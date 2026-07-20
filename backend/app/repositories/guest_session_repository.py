"""Guest session repository."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.guest_session import GuestSession


class GuestSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key(self, guest_key: str) -> GuestSession | None:
        result = await self._session.execute(
            select(GuestSession).where(GuestSession.guest_key == guest_key)
        )
        return result.scalar_one_or_none()

    async def create(self, session: GuestSession) -> GuestSession:
        self._session.add(session)
        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def save(self, session: GuestSession) -> GuestSession:
        await self._session.flush()
        await self._session.refresh(session)
        return session

    async def increment_usage(self, session: GuestSession, *, count: int = 1) -> GuestSession:
        session.jobs_used += max(1, count)
        await self._session.flush()
        await self._session.refresh(session)
        return session

    def is_expired(self, session: GuestSession) -> bool:
        expires = session.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        return expires < datetime.now(UTC)
