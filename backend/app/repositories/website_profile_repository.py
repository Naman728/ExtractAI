"""Website profile persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.website_profile import WebsiteProfileRecord


class WebsiteProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, record: WebsiteProfileRecord) -> WebsiteProfileRecord:
        self._session.add(record)
        await self._session.flush()
        await self._session.refresh(record)
        return record

    async def get_by_id(self, profile_id: uuid.UUID) -> WebsiteProfileRecord | None:
        return await self._session.get(WebsiteProfileRecord, profile_id)

    async def list_recent(
        self,
        *,
        user_id: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[WebsiteProfileRecord]:
        stmt = select(WebsiteProfileRecord).order_by(WebsiteProfileRecord.probed_at.desc()).limit(limit)
        if user_id is not None:
            stmt = stmt.where(WebsiteProfileRecord.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
