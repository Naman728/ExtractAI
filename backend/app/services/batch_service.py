"""Batch extraction service — fan-out addresses to child jobs."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import BatchStatus, JobStatus
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.logging import get_logger
from app.engines.versions import current_version_pins
from app.models.batch import ExtractionBatch, ExtractionBatchItem
from app.models.guest_session import GuestSession
from app.models.job import Job, JobEvent
from app.models.user import User
from app.observability import metrics
from app.repositories.batch_repository import BatchRepository
from app.repositories.job_repository import JobRepository
from app.schemas import (
    BatchItemResponse,
    BatchResponse,
    BatchResultsResponse,
)
from app.services.job_service import JobService
from app.services.quota_service import QuotaService
from app.utils.url import assert_public_url

logger = get_logger(__name__)


def normalize_addresses(addresses: list[str]) -> list[str]:
    """
    Deduplicate while preserving order.

    - Does NOT split on commas (addresses contain them).
    - If a single element looks like a JSON array string, expand it.
    - Strips wrapping quotes / brackets from paste accidents.
    """
    import json
    import re

    expanded: list[str] = []
    for raw in addresses:
        text = str(raw).strip()
        if not text:
            continue
        # Single blob that is a JSON array
        if text.startswith("[") and len(addresses) == 1:
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    expanded.extend(str(v) for v in parsed)
                    continue
            except json.JSONDecodeError:
                pass
        # Multi-line blob accidentally sent as one item
        if "\n" in text:
            expanded.extend(text.splitlines())
            continue
        expanded.append(text)

    seen: set[str] = set()
    out: list[str] = []
    for raw in expanded:
        addr = " ".join(str(raw).split()).strip()
        addr = re.sub(r"^\[+\s*", "", addr)
        addr = re.sub(r"\s*\]+$", "", addr)
        addr = addr.strip().strip("\"'")
        addr = " ".join(addr.split()).strip()
        if not addr:
            continue
        key = addr.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(addr)
    return out


class BatchService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._batches = BatchRepository(session)
        self._jobs = JobRepository(session)
        self._quota = QuotaService(session, self._settings)
        self._job_service = JobService(session, self._settings)

    async def create_batch(
        self,
        url: str,
        addresses: list[str],
        *,
        workflow: str | None = None,
        extra_inputs: dict[str, str] | None = None,
        user: User | None = None,
        guest_key: str | None = None,
    ) -> tuple[BatchResponse, GuestSession | None]:
        normalized_url = assert_public_url(str(url))
        addrs = normalize_addresses(addresses)
        if not addrs:
            raise ValidationAppError("Provide at least one non-empty address")

        max_allowed = self._settings.batch_max_addresses
        guest_max = self._settings.batch_guest_max_addresses
        if len(addrs) > max_allowed:
            raise ValidationAppError(
                f"Too many addresses (max {max_allowed})",
                details={"count": len(addrs), "max": max_allowed},
            )

        guest: GuestSession | None = None
        if user is None:
            if len(addrs) > guest_max:
                raise ValidationAppError(
                    f"Guests can submit at most {guest_max} addresses per batch. Register for larger batches.",
                    details={"count": len(addrs), "guest_max": guest_max},
                )
            guest = await self._quota.resolve_or_create_guest(guest_key)
            await self._quota.assert_guest_can_create_jobs(guest, len(addrs))

        wf = workflow
        if not wf and "ballotready" in normalized_url.lower():
            wf = "ballotready_officials"

        now = datetime.now(UTC)
        batch = ExtractionBatch(
            user_id=user.id if user else None,
            guest_session_id=guest.id if guest else None,
            url=str(url),
            workflow=wf,
            status=BatchStatus.PENDING.value,
            total_items=len(addrs),
            completed_items=0,
            failed_items=0,
            meta={"extra_inputs": extra_inputs or {}},
        )
        batch = await self._batches.create(batch)

        pins = current_version_pins()
        job_ids: list[UUID] = []

        for idx, address in enumerate(addrs):
            inputs = {**(extra_inputs or {}), "address": address}
            job = Job(
                user_id=user.id if user else None,
                guest_session_id=guest.id if guest else None,
                url=str(url),
                normalized_url=normalized_url,
                status=JobStatus.PENDING.value,
                extractor_type=self._settings.extractor_type,
                pipeline_version=pins.pipeline_version,
                strategy_version=pins.strategy_version,
                plugin_set_version=pins.plugin_set_version,
                schema_version=pins.schema_version,
                profile_version=pins.profile_version,
                discovery_version=pins.discovery_version,
                meta={
                    "inputs": inputs,
                    "workflow": wf,
                    "batch_id": str(batch.id),
                    "batch_position": idx,
                },
            )
            job = await self._jobs.create(job)
            job_ids.append(job.id)

            item = ExtractionBatchItem(
                batch_id=batch.id,
                position=idx,
                address=address,
                job_id=job.id,
                status=JobStatus.PENDING.value,
                result_summary={},
                created_at=now,
                updated_at=now,
            )
            self._session.add(item)

            await self._jobs.add_event(
                JobEvent(
                    job_id=job.id,
                    stage="created",
                    level="info",
                    message=f"Batch job created ({idx + 1}/{len(addrs)})",
                    details={"batch_id": str(batch.id), "address": address},
                    created_at=now,
                )
            )

        if guest is not None:
            guest = await self._quota.consume_guest_jobs(guest, len(addrs))

        batch.status = BatchStatus.RUNNING.value
        await self._batches.save(batch)
        await self._session.commit()

        # Enqueue after commit
        for jid in job_ids:
            self._job_service._enqueue(jid)

        metrics.incr("batches.created")
        logger.info(
            "batch.created",
            batch_id=str(batch.id),
            total=len(addrs),
            url=normalized_url,
        )

        refreshed = await self._batches.get_by_id(batch.id)
        assert refreshed is not None
        return self._to_response(refreshed), guest

    async def get_batch(
        self,
        batch_id: UUID,
        *,
        user: User | None = None,
        guest_key: str | None = None,
    ) -> BatchResponse:
        batch = await self._require_accessible(batch_id, user=user, guest_key=guest_key)
        await self._refresh_progress(batch)
        batch = await self._batches.get_by_id(batch_id)
        assert batch is not None
        return self._to_response(batch)

    async def get_results(
        self,
        batch_id: UUID,
        *,
        user: User | None = None,
        guest_key: str | None = None,
    ) -> BatchResultsResponse:
        batch = await self._require_accessible(batch_id, user=user, guest_key=guest_key)
        await self._refresh_progress(batch)
        batch = await self._batches.get_by_id(batch_id)
        assert batch is not None

        return BatchResultsResponse(
            batch_id=batch.id,
            url=batch.url,
            status=batch.status,
            total_items=batch.total_items,
            completed_items=batch.completed_items,
            failed_items=batch.failed_items,
            results=[self._item_result_payload(i) for i in batch.items],
        )

    def _item_result_payload(self, item: ExtractionBatchItem) -> dict:
        summary = item.result_summary or {}
        return {
            "address": item.address,
            "position": item.position,
            "status": item.status,
            "job_id": str(item.job_id) if item.job_id else None,
            "error_message": item.error_message,
            "officials": summary.get("officials")
            or {
                "federal": [],
                "state": [],
                "local": [],
                "unknown": [],
                "counts": {},
                "total": 0,
            },
            "address_normalized": summary.get("address_normalized"),
            "title": summary.get("title"),
        }

    async def _refresh_progress(self, batch: ExtractionBatch) -> None:
        """Sync item statuses from child jobs and roll up batch counters."""
        from app.models.extracted_data import ExtractedData
        from sqlalchemy import select

        completed = failed = 0
        now = datetime.now(UTC)
        for item in batch.items:
            if not item.job_id:
                continue
            job = await self._jobs.get_by_id(item.job_id)
            if not job:
                continue
            item.status = job.status
            item.updated_at = now
            if job.status == JobStatus.FAILED.value:
                failed += 1
                item.error_message = job.error_message
            elif job.status == JobStatus.COMPLETED.value:
                completed += 1
                if not (item.result_summary or {}).get("officials"):
                    result = await self._session.execute(
                        select(ExtractedData).where(ExtractedData.job_id == job.id)
                    )
                    data = result.scalar_one_or_none()
                    if data and data.normalized_payload:
                        payload = data.normalized_payload
                        officials = payload.get("officials") or {}
                        agent = payload.get("agent") or {}
                        item.result_summary = {
                            "title": payload.get("title"),
                            "officials": officials,
                            "address_normalized": agent.get("address_normalized"),
                            "strategy": job.strategy_used,
                        }
            elif job.status in {JobStatus.PENDING.value, JobStatus.RUNNING.value}:
                pass

        batch.completed_items = completed
        batch.failed_items = failed
        done = completed + failed
        if done >= batch.total_items and batch.total_items > 0:
            if failed == 0:
                batch.status = BatchStatus.COMPLETED.value
            elif completed == 0:
                batch.status = BatchStatus.FAILED.value
            else:
                batch.status = BatchStatus.PARTIAL.value
        elif done > 0:
            batch.status = BatchStatus.RUNNING.value
        await self._batches.save(batch)
        await self._session.commit()

    async def _require_accessible(
        self,
        batch_id: UUID,
        *,
        user: User | None,
        guest_key: str | None,
    ) -> ExtractionBatch:
        batch = await self._batches.get_by_id(batch_id)
        if not batch:
            raise NotFoundError("Batch not found")

        if user and batch.user_id == user.id:
            return batch

        if guest_key and batch.guest_session_id is not None:
            guest = await self._quota._guests.get_by_key(guest_key)
            if guest and guest.id == batch.guest_session_id:
                return batch

        if user is None and guest_key is None:
            raise ForbiddenError("Authentication or guest key required")

        raise ForbiddenError("You do not have access to this batch")

    def _to_response(self, batch: ExtractionBatch) -> BatchResponse:
        done = batch.completed_items + batch.failed_items
        progress = int((done / batch.total_items) * 100) if batch.total_items else 0
        items = []
        for item in batch.items or []:
            summary = item.result_summary or {}
            officials = summary.get("officials") or {}
            items.append(
                BatchItemResponse(
                    id=item.id,
                    position=item.position,
                    address=item.address,
                    job_id=item.job_id,
                    status=item.status,
                    error_message=item.error_message,
                    officials_total=int(officials.get("total") or 0),
                    officials_counts=officials.get("counts")
                    if isinstance(officials.get("counts"), dict)
                    else {},
                    result_summary=summary,
                )
            )
        return BatchResponse(
            id=batch.id,
            url=batch.url,
            workflow=batch.workflow,
            status=batch.status,
            total_items=batch.total_items,
            completed_items=batch.completed_items,
            failed_items=batch.failed_items,
            progress_pct=progress,
            created_at=batch.created_at,
            updated_at=batch.updated_at,
            items=items,
        )
