"""Job repository."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobEvent
from app.models.pipeline_log import PipelineLog


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, job: Job) -> Job:
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Job | None:
        result = await self._session.execute(
            select(Job).where(Job.id == job_id, Job.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Job], int]:
        base = select(Job).where(Job.user_id == user_id, Job.deleted_at.is_(None))
        count_result = await self._session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(count_result.scalar_one())
        result = await self._session.execute(
            base.order_by(Job.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def soft_delete(self, job: Job) -> None:
        job.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def list_pipeline_logs(
        self, job_id: uuid.UUID, *, limit: int = 40
    ) -> list[PipelineLog]:
        result = await self._session.execute(
            select(PipelineLog)
            .where(PipelineLog.job_id == job_id)
            .order_by(PipelineLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_event(self, event: JobEvent) -> JobEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def save(self, job: Job) -> Job:
        await self._session.flush()
        await self._session.refresh(job)
        return job
