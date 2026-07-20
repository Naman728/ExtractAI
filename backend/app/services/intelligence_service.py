"""Website Intelligence application service."""

from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.models.user import User
from app.models.website_profile import WebsiteProfileRecord
from app.observability import metrics
from app.repositories.website_profile_repository import WebsiteProfileRepository
from app.services.quota_service import QuotaService
from app.website_intelligence.engine import WebsiteIntelligenceEngine
from app.website_intelligence.profile import AnalyzeResponse, IntelligenceReport, WebsiteProfile

logger = get_logger(__name__)


class IntelligenceService:
    """Runs Website Intelligence Engine and persists versioned profiles."""

    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._profiles = WebsiteProfileRepository(session)
        self._quota = QuotaService(session, self._settings)
        self._engine = WebsiteIntelligenceEngine(self._settings)

    async def analyze(
        self,
        url: str,
        *,
        user: User | None = None,
        guest_key: str | None = None,
    ) -> tuple[AnalyzeResponse, object | None]:
        guest = None
        if user is None:
            guest = await self._quota.resolve_or_create_guest(guest_key)

        # Engine is sync/httpx — run in thread to keep event loop free
        profile, report, discovery = await asyncio.to_thread(self._engine.analyze, str(url))

        record = WebsiteProfileRecord(
            job_id=None,
            user_id=user.id if user else None,
            guest_session_id=guest.id if guest else None,
            url=profile.url,
            normalized_url=profile.normalized_url,
            profile=profile.model_dump(mode="json"),
            report=report.model_dump(mode="json"),
            discovery=discovery.model_dump(mode="json"),
            profile_version=profile.profile_version,
            discovery_version=discovery.discovery_version,
            schema_version=self._settings.schema_version,
            overall_confidence=profile.overall_confidence,
            probed_at=profile.probed_at,
        )
        record = await self._profiles.create(record)
        await self._session.commit()
        await self._session.refresh(record)

        metrics.incr("intelligence.analyzed")
        logger.info(
            "intelligence.persisted",
            profile_id=str(record.id),
            url=profile.normalized_url,
            strategy=report.suggested_fetch_strategy,
        )

        response = AnalyzeResponse(
            id=str(record.id),
            profile=profile,
            report=report,
            discovery=discovery.model_dump(mode="json"),
        )
        return response, guest

    async def get_analysis(self, profile_id: UUID) -> AnalyzeResponse:
        record = await self._profiles.get_by_id(profile_id)
        if not record:
            raise NotFoundError("Intelligence profile not found")
        return AnalyzeResponse(
            id=str(record.id),
            profile=WebsiteProfile.model_validate(record.profile),
            report=IntelligenceReport.model_validate(record.report),
            discovery=record.discovery or {},
        )
