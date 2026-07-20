"""Batch repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.batch import ExtractionBatch, ExtractionBatchItem


class BatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, batch: ExtractionBatch) -> ExtractionBatch:
        self._session.add(batch)
        await self._session.flush()
        await self._session.refresh(batch)
        return batch

    async def get_by_id(self, batch_id: UUID) -> ExtractionBatch | None:
        result = await self._session.execute(
            select(ExtractionBatch)
            .where(ExtractionBatch.id == batch_id)
            .options(selectinload(ExtractionBatch.items))
        )
        return result.scalar_one_or_none()

    async def save(self, batch: ExtractionBatch) -> ExtractionBatch:
        await self._session.flush()
        await self._session.refresh(batch)
        return batch

    async def get_item_by_job_id(self, job_id: UUID) -> ExtractionBatchItem | None:
        result = await self._session.execute(
            select(ExtractionBatchItem).where(ExtractionBatchItem.job_id == job_id)
        )
        return result.scalar_one_or_none()
