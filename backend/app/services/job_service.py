"""Job lifecycle service (create/list/get/delete/retry). Pipeline runs in workers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import JobStatus
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.engines.versions import current_version_pins
from app.models.guest_session import GuestSession
from app.models.job import Job, JobEvent
from app.models.user import User
from app.observability import metrics, set_job_id
from app.repositories.job_repository import JobRepository
from app.schemas import JobEventResponse, JobEventsResponse, JobListResponse, JobResponse
from app.services.quota_service import QuotaService
from app.utils.url import assert_public_url

logger = get_logger(__name__)


def job_to_response(job: Job) -> JobResponse:
    meta = job.meta or {}
    inputs = meta.get("inputs") if isinstance(meta.get("inputs"), dict) else {}
    workflow = meta.get("workflow")
    batch_raw = meta.get("batch_id")
    batch_id = None
    if batch_raw:
        try:
            from uuid import UUID as _UUID

            batch_id = _UUID(str(batch_raw))
        except Exception:
            batch_id = None
    return JobResponse.model_validate(job).model_copy(
        update={
            "inputs": {str(k): str(v) for k, v in inputs.items()},
            "workflow": str(workflow) if workflow else None,
            "batch_id": batch_id,
        }
    )


class JobService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._jobs = JobRepository(session)
        self._quota = QuotaService(session, self._settings)

    async def create_job(
        self,
        url: str,
        *,
        user: User | None = None,
        guest_key: str | None = None,
        inputs: dict[str, str] | None = None,
        workflow: str | None = None,
        follow_pagination: bool | None = None,
        max_pages: int | None = None,
    ) -> tuple[JobResponse, GuestSession | None]:
        normalized = assert_public_url(str(url))
        pins = current_version_pins()
        guest: GuestSession | None = None

        clean_inputs = {
            str(k): str(v).strip()
            for k, v in (inputs or {}).items()
            if v is not None and str(v).strip()
        }

        crawl: dict[str, object] = {}
        if follow_pagination is not None:
            crawl["follow_pagination"] = follow_pagination
        if max_pages is not None:
            crawl["max_pages"] = int(max_pages)

        if user is None:
            guest = await self._quota.resolve_or_create_guest(guest_key)
            await self._quota.assert_guest_can_create_job(guest)

        job = Job(
            user_id=user.id if user else None,
            guest_session_id=guest.id if guest else None,
            url=str(url),
            normalized_url=normalized,
            status=JobStatus.PENDING.value,
            extractor_type=self._settings.extractor_type,
            pipeline_version=pins.pipeline_version,
            strategy_version=pins.strategy_version,
            plugin_set_version=pins.plugin_set_version,
            schema_version=pins.schema_version,
            profile_version=pins.profile_version,
            discovery_version=pins.discovery_version,
            meta={
                "inputs": clean_inputs,
                "workflow": workflow,
                "crawl": crawl,
            },
        )
        job = await self._jobs.create(job)

        if guest is not None:
            guest = await self._quota.consume_guest_job(guest)

        await self._jobs.add_event(
            JobEvent(
                job_id=job.id,
                stage="created",
                level="info",
                message="Job created and queued",
                details={
                    "normalized_url": normalized,
                    "inputs": list(clean_inputs.keys()),
                    "workflow": workflow,
                },
                created_at=datetime.now(UTC),
            )
        )

        # Commit before enqueue so workers never race an uncommitted insert.
        await self._session.commit()
        await self._session.refresh(job)
        if guest is not None:
            await self._session.refresh(guest)

        self._enqueue(job.id)
        metrics.incr("jobs.created", auth="user" if user else "guest")
        logger.info(
            "job.created",
            job_id=str(job.id),
            url=normalized,
            inputs=list(clean_inputs.keys()),
        )
        return job_to_response(job), guest

    async def list_jobs(
        self,
        user: User,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> JobListResponse:
        if page < 1 or page_size < 1 or page_size > 100:
            raise ValidationAppError("Invalid pagination parameters")
        items, total = await self._jobs.list_for_user(user.id, page=page, page_size=page_size)
        return JobListResponse(
            items=[job_to_response(j) for j in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_job(
        self,
        job_id: UUID,
        *,
        user: User | None = None,
        guest_key: str | None = None,
    ) -> JobResponse:
        job = await self._require_accessible_job(job_id, user=user, guest_key=guest_key)
        return job_to_response(job)

    async def get_job_events(
        self,
        job_id: UUID,
        *,
        user: User | None = None,
        guest_key: str | None = None,
        limit: int = 40,
    ) -> JobEventsResponse:
        job = await self._require_accessible_job(job_id, user=user, guest_key=guest_key)
        logs = await self._jobs.list_pipeline_logs(job.id, limit=limit)
        # Repository returns newest-first; expose chronological (oldest-first).
        events = [
            JobEventResponse.model_validate(log) for log in reversed(logs)
        ]
        return JobEventsResponse(
            job_id=job.id,
            status=job.status,
            progress_pct=job.progress_pct or 0,
            current_stage=job.current_stage,
            events=events,
        )

    async def delete_job(self, job_id: UUID, *, user: User) -> None:
        job = await self._jobs.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")
        if job.user_id != user.id:
            raise ForbiddenError("You do not own this job")
        await self._jobs.soft_delete(job)
        metrics.incr("jobs.deleted")
        logger.info("job.deleted", job_id=str(job_id))

    async def retry_job(self, job_id: UUID, *, user: User) -> JobResponse:
        job = await self._jobs.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")
        if job.user_id != user.id:
            raise ForbiddenError("You do not own this job")
        if job.status not in {JobStatus.FAILED.value, JobStatus.COMPLETED.value}:
            raise ValidationAppError("Only failed or completed jobs can be retried")
        if job.retry_count >= job.max_retries:
            raise ValidationAppError("Maximum retries exceeded")

        job.status = JobStatus.PENDING.value
        job.retry_count += 1
        job.error_code = None
        job.error_message = None
        job.progress_pct = 0
        job.current_stage = "queued"
        job.started_at = None
        job.finished_at = None
        job.duration_ms = None
        await self._jobs.save(job)
        await self._jobs.add_event(
            JobEvent(
                job_id=job.id,
                stage="retry",
                level="info",
                message=f"Job retry #{job.retry_count} queued",
                details={},
                created_at=datetime.now(UTC),
            )
        )
        await self._session.commit()
        await self._session.refresh(job)
        self._enqueue(job.id)
        metrics.incr("jobs.retried")
        return job_to_response(job)

    async def _require_accessible_job(
        self,
        job_id: UUID,
        *,
        user: User | None,
        guest_key: str | None,
    ) -> Job:
        job = await self._jobs.get_by_id(job_id)
        if not job:
            raise NotFoundError("Job not found")

        if user and job.user_id == user.id:
            return job

        if guest_key and job.guest_session_id is not None:
            guest = await self._quota._guests.get_by_key(guest_key)
            if guest and guest.id == job.guest_session_id:
                return job

        if user is None and guest_key is None:
            raise ForbiddenError("Authentication or guest key required")

        raise ForbiddenError("You do not have access to this job")

    def _enqueue(self, job_id: UUID) -> None:
        """
        Run extraction asynchronously.

        Uses Celery when settings.use_celery is true; otherwise a daemon thread.
        """
        set_job_id(str(job_id))
        import threading

        from app.workers.tasks import run_extraction_pipeline

        use_celery = self._settings.use_celery
        if use_celery:
            try:
                run_extraction_pipeline.delay(str(job_id))
                logger.info("job.enqueued_celery", job_id=str(job_id))
                return
            except Exception as exc:
                logger.warning("job.celery_unavailable", job_id=str(job_id), error=str(exc))

        threading.Thread(
            target=lambda: run_extraction_pipeline.apply(args=(str(job_id),)),
            daemon=True,
            name=f"extract-{job_id}",
        ).start()
        logger.info("job.enqueued_thread", job_id=str(job_id))
