"""FastAPI dependency injection."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import GUEST_HEADER
from app.core.database import get_db_session
from app.core.exceptions import UnauthorizedError
from app.core.security import safe_decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.job_service import JobService
from app.services.quota_service import QuotaService
from app.storage import StorageBackend, create_storage_backend

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


async def get_storage() -> StorageBackend:
    return create_storage_backend()


StorageDep = Annotated[StorageBackend, Depends(get_storage)]


async def get_auth_service(session: DbSession) -> AuthService:
    return AuthService(session)


async def get_job_service(session: DbSession) -> JobService:
    return JobService(session)


async def get_quota_service(session: DbSession) -> QuotaService:
    return QuotaService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
JobServiceDep = Annotated[JobService, Depends(get_job_service)]
QuotaServiceDep = Annotated[QuotaService, Depends(get_quota_service)]


async def get_current_user_optional(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User | None:
    """Return the user when a valid Bearer token is present.

    Expired / malformed tokens are treated as anonymous (guest) so public
    extraction endpoints keep working after a stale login session.
    """
    if credentials is None:
        return None
    try:
        payload = safe_decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except Exception:
        return None

    user = await UserRepository(session).get_by_id(user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        return None
    return user


async def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Authentication required")
    try:
        payload = safe_decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except Exception as exc:
        raise UnauthorizedError("Invalid access token") from exc

    user = await UserRepository(session).get_by_id(user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise UnauthorizedError("User not found or inactive")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


async def get_guest_key(
    x_guest_key: Annotated[str | None, Header(alias=GUEST_HEADER)] = None,
) -> str | None:
    return x_guest_key


GuestKey = Annotated[str | None, Depends(get_guest_key)]


def client_meta(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return user_agent, ip
