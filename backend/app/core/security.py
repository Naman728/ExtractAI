"""Security utilities: password hashing and JWT tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str,
    *,
    extra_claims: dict[str, Any] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived JWT access token."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
        "jti": str(uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> tuple[str, str, datetime]:
    """
    Create a refresh token.

    Returns:
        (raw_token, jti, expires_at)
    """
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    jti = str(uuid4())
    payload = {
        "sub": subject,
        "exp": expires_at,
        "iat": datetime.now(UTC),
        "type": "refresh",
        "jti": jti,
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, expires_at


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def hash_token(raw: str) -> str:
    """Hash a token for at-rest storage (refresh tokens, API keys)."""
    return pwd_context.hash(raw)


def verify_token_hash(raw: str, hashed: str) -> bool:
    """Verify a raw token against a stored hash."""
    return pwd_context.verify(raw, hashed)


class TokenError(Exception):
    """Raised when a token is invalid or expired."""


def require_token_type(payload: dict[str, Any], expected: str) -> None:
    """Ensure JWT payload has the expected type claim."""
    if payload.get("type") != expected:
        raise TokenError(f"Expected token type '{expected}'")
    if "sub" not in payload:
        raise TokenError("Token missing subject")


def safe_decode_access_token(token: str) -> dict[str, Any]:
    """Decode an access token or raise TokenError."""
    try:
        payload = decode_token(token)
        require_token_type(payload, "access")
        return payload
    except (JWTError, TokenError) as exc:
        raise TokenError(str(exc)) from exc
