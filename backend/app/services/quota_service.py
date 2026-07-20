"""Guest quota service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import QuotaExceededError, ValidationAppError
from app.core.logging import get_logger
from app.models.guest_session import GuestSession
from app.repositories.guest_session_repository import GuestSessionRepository
from app.schemas import GuestSessionResponse

logger = get_logger(__name__)


class QuotaService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._guests = GuestSessionRepository(session)

    async def resolve_or_create_guest(self, guest_key: str | None) -> GuestSession:
        """Return an existing guest session or create a new one."""
        if guest_key:
            existing = await self._guests.get_by_key(guest_key)
            if existing:
                if self._guests.is_expired(existing):
                    raise ValidationAppError(
                        "Guest session expired. Start a new session.",
                        code="GUEST_EXPIRED",
                    )
                # Keep existing sessions aligned with current configured limit
                if existing.jobs_limit != self._settings.guest_job_limit:
                    existing.jobs_limit = self._settings.guest_job_limit
                    await self._guests.save(existing)
                return existing

        session = GuestSession(
            guest_key=guest_key or str(uuid4()),
            jobs_used=0,
            jobs_limit=self._settings.guest_job_limit,
            expires_at=datetime.now(UTC)
            + timedelta(days=self._settings.guest_session_expire_days),
        )
        created = await self._guests.create(session)
        logger.info("guest.created", guest_key=created.guest_key)
        return created

    async def assert_guest_can_create_jobs(self, guest: GuestSession, count: int) -> None:
        if count < 1:
            raise ValidationAppError("Batch must include at least one address")
        if self._guests.is_expired(guest):
            raise ValidationAppError("Guest session expired", code="GUEST_EXPIRED")
        limit = max(guest.jobs_limit, self._settings.guest_job_limit)
        if guest.jobs_used + count > limit:
            raise QuotaExceededError(
                "Guest job quota exceeded for this batch. Register to continue.",
                details={
                    "jobs_used": guest.jobs_used,
                    "jobs_limit": limit,
                    "requested": count,
                    "remaining": max(0, limit - guest.jobs_used),
                },
            )

    async def consume_guest_jobs(self, guest: GuestSession, count: int) -> GuestSession:
        await self.assert_guest_can_create_jobs(guest, count)
        updated = await self._guests.increment_usage(guest, count=count)
        logger.info(
            "guest.quota_consumed_batch",
            guest_key=updated.guest_key,
            count=count,
            jobs_used=updated.jobs_used,
            jobs_limit=updated.jobs_limit,
        )
        return updated

    async def assert_guest_can_create_job(self, guest: GuestSession) -> None:
        await self.assert_guest_can_create_jobs(guest, 1)

    async def consume_guest_job(self, guest: GuestSession) -> GuestSession:
        return await self.consume_guest_jobs(guest, 1)

    def to_response(self, guest: GuestSession) -> GuestSessionResponse:
        limit = max(guest.jobs_limit, self._settings.guest_job_limit)
        return GuestSessionResponse(
            guest_key=guest.guest_key,
            jobs_used=guest.jobs_used,
            jobs_limit=limit,
            remaining=max(0, limit - guest.jobs_used),
        )
