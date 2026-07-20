"""Authentication service."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationAppError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    require_token_type,
    verify_password,
    verify_token_hash,
)
from app.models.email_verification import EmailVerificationToken
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.models.user_settings import UserSettings
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas import TokenPair, UserResponse
from app.services.mail_service import MailService

logger = get_logger(__name__)


def _hash_verify_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._users = UserRepository(session)
        self._tokens = RefreshTokenRepository(session)
        self._mail = MailService(self._settings)

    async def register(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> tuple[UserResponse, dict]:
        existing = await self._users.get_by_email(email)
        if existing:
            raise ConflictError("Email already registered", details={"email": email})

        user = User(
            email=email.lower().strip(),
            password_hash=hash_password(password),
            full_name=full_name,
            email_verified=False,
        )
        user = await self._users.create(user)
        self._session.add(UserSettings(user_id=user.id))
        await self._session.flush()

        email_meta = await self._create_and_send_verification(user)
        if not email_meta.get("email_sent"):
            # Soft-fail message — account exists but sign-in stays locked until mail works + verify
            email_meta["message"] = (
                "Account created, but we could not send the verification email. "
                "Confirm Brevo sender/API key, then use Resend on the sign-in page."
            )
        logger.info("auth.register", user_id=str(user.id), email_sent=email_meta.get("email_sent"))
        # No tokens until email is verified via Gmail link
        return UserResponse.model_validate(user), email_meta

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[UserResponse, TokenPair]:
        user = await self._users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is disabled")
        if self._settings.email_verification_required and not user.email_verified:
            raise UnauthorizedError(
                "Verify your email before signing in. Check your Gmail for the ExtractAI link.",
                details={"code": "EMAIL_NOT_VERIFIED", "email": user.email},
            )

        tokens = await self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)
        logger.info("auth.login", user_id=str(user.id))
        return UserResponse.model_validate(user), tokens

    async def verify_email(self, raw_token: str) -> UserResponse:
        token = (raw_token or "").strip()
        if not token:
            raise ValidationAppError("Verification token is required")

        token_hash = _hash_verify_token(token)
        result = await self._session.execute(
            select(EmailVerificationToken).where(EmailVerificationToken.token_hash == token_hash)
        )
        record = result.scalar_one_or_none()
        if record is None:
            raise ValidationAppError("Invalid or expired verification link")
        if record.used_at is not None:
            user = await self._users.get_by_id(record.user_id)
            if user and user.email_verified:
                return UserResponse.model_validate(user)
            raise ValidationAppError("Verification link already used")

        expires = record.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(UTC):
            raise ValidationAppError("Verification link expired — request a new one")

        user = await self._users.get_by_id(record.user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User not found")

        user.email_verified = True
        record.used_at = datetime.now(UTC)
        await self._session.flush()
        logger.info("auth.email_verified", user_id=str(user.id))
        return UserResponse.model_validate(user)

    async def resend_verification(self, user_id: UUID) -> dict:
        user = await self._users.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            raise UnauthorizedError("User not found")
        if user.email_verified:
            return {
                "email_sent": False,
                "already_verified": True,
                "message": "Email already verified — you can sign in.",
            }
        return await self._create_and_send_verification(user)

    async def resend_verification_by_email(self, email: str) -> dict:
        """Public resend (no login) — for users blocked until Gmail verify."""
        user = await self._users.get_by_email(email)
        # Always return a generic message to avoid account enumeration
        generic = {
            "email_sent": True,
            "message": "If that account exists and is unverified, a new link was sent to Gmail.",
        }
        if not user or user.deleted_at is not None or user.email_verified:
            return generic
        meta = await self._create_and_send_verification(user)
        out: dict = {
            "email_sent": bool(meta.get("email_sent")),
            "message": (
                "Verification email sent — check your Gmail inbox (and Spam)."
                if meta.get("email_sent")
                else "Could not send email. Check Brevo API key / verified sender."
            ),
        }
        if meta.get("verification_url"):
            out["verification_url"] = meta["verification_url"]
            out["message"] = str(meta.get("message") or out["message"])
        return out

    async def _create_and_send_verification(self, user: User) -> dict:
        existing = await self._session.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.user_id == user.id,
                EmailVerificationToken.used_at.is_(None),
            )
        )
        now = datetime.now(UTC)
        for row in existing.scalars().all():
            row.used_at = now

        raw = secrets.token_urlsafe(32)
        record = EmailVerificationToken(
            user_id=user.id,
            token_hash=_hash_verify_token(raw),
            expires_at=now + timedelta(hours=self._settings.email_verification_expire_hours),
            created_at=now,
        )
        self._session.add(record)
        await self._session.flush()

        base = self._settings.frontend_public_url.rstrip("/")
        verify_url = f"{base}/verify-email?token={raw}"
        sent = await self._mail.send_verification_email(
            to_email=user.email,
            verify_url=verify_url,
            full_name=user.full_name,
        )
        meta: dict = {
            "email_sent": sent,
            "already_verified": False,
            "verification_required": True,
            "message": (
                "We emailed a one-time verification link to your Gmail. "
                "Open it, then sign in. Also check Spam / Promotions."
                if sent
                else "Could not send verification email. Check Brevo settings."
            ),
        }
        # Local/dev: always expose the link so signup works when Gmail rate-limits
        # Brevo's shared *.brevosend.com domain (common on free plans).
        if self._settings.is_development:
            meta["verification_url"] = verify_url
            if sent:
                meta["message"] = (
                    "Verification email requested. If it does not appear in Gmail "
                    "(Spam/Promotions), use the on-screen link below — Gmail often "
                    "delays mail from Brevo's shared sending domain."
                )
        return meta

    async def refresh(
        self,
        refresh_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        try:
            payload = decode_token(refresh_token)
            require_token_type(payload, "refresh")
        except (JWTError, Exception) as exc:
            raise UnauthorizedError("Invalid refresh token") from exc

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise UnauthorizedError("Invalid refresh token")

        stored = await self._tokens.get_by_jti(jti)
        if not stored or stored.revoked_at is not None:
            raise UnauthorizedError("Refresh token revoked")
        if stored.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise UnauthorizedError("Refresh token expired")
        if not verify_token_hash(refresh_token, stored.token_hash):
            raise UnauthorizedError("Invalid refresh token")

        user = await self._users.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found")

        await self._tokens.revoke(stored)
        return await self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
            require_token_type(payload, "refresh")
            jti = payload.get("jti")
            if not jti:
                return
            stored = await self._tokens.get_by_jti(jti)
            if stored and stored.revoked_at is None:
                await self._tokens.revoke(stored)
        except Exception:
            return

    async def get_user(self, user_id: UUID) -> UserResponse:
        user = await self._users.get_by_id(user_id)
        if not user or user.deleted_at is not None:
            raise UnauthorizedError("User not found")
        return UserResponse.model_validate(user)

    async def _issue_tokens(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        access = create_access_token(
            str(user.id),
            extra_claims={"email": user.email, "email_verified": user.email_verified},
        )
        raw_refresh, jti, expires_at = create_refresh_token(str(user.id))
        record = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh),
            jti=jti,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=datetime.now(UTC),
        )
        await self._tokens.create(record)
        return TokenPair(access_token=access, refresh_token=raw_refresh)
