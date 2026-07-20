"""Scrape / extraction job runner used by Celery workers."""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from app.ai.cache.store import UnderstandingCache
from app.ai.services.understanding_service import UnderstandingService
from app.core.config import Settings, get_settings
from app.core.constants import JobStatus
from app.core.logging import get_logger
from app.engines.pipeline import ExtractionPipeline, PipelineResult
from app.models.extracted_data import ExtractedData
from app.models.job import Job, JobEvent
from app.models.performance_metric import PerformanceMetric
from app.models.pipeline_log import PipelineLog
from app.models.strategy_decision import StrategyDecision
from app.models.website_profile import WebsiteProfileRecord
from app.observability import metrics

logger = get_logger(__name__)


class ScrapeService:
    """Runs ExtractionPipeline for a job and persists all artifacts."""

    def __init__(self, session_factory: sessionmaker[Session], settings: Settings | None = None) -> None:
        self._session_factory = session_factory
        self._settings = settings or get_settings()
        self._pipeline = ExtractionPipeline(self._settings)

    def run_job(self, job_id: str) -> dict:
        with self._session_factory() as session:
            job = session.get(Job, UUID(job_id))
            if job is None:
                logger.warning("scrape.job_missing", job_id=job_id)
                return {"status": "missing"}

            job.status = JobStatus.RUNNING.value
            job.started_at = datetime.now(UTC)
            job.current_stage = "intelligence"
            job.progress_pct = 5
            session.add(
                JobEvent(
                    job_id=job.id,
                    stage="running",
                    level="info",
                    message="Extraction pipeline started",
                    details={},
                    created_at=datetime.now(UTC),
                )
            )
            session.commit()

            try:
                self._set_stage(session, job, "intelligence", 10)
                meta = job.meta or {}
                inputs = meta.get("inputs") if isinstance(meta.get("inputs"), dict) else {}
                workflow = meta.get("workflow")
                crawl = meta.get("crawl") if isinstance(meta.get("crawl"), dict) else {}

                def on_progress(stage: str, progress: int, message: str, details: dict) -> None:
                    """Persist real-time stage/progress so the orchestra reflects live work."""
                    try:
                        job.current_stage = stage
                        job.progress_pct = max(job.progress_pct or 0, int(progress))
                        session.add(
                            PipelineLog(
                                job_id=job.id,
                                stage=stage,
                                level="info",
                                message=message,
                                details=details or {},
                                created_at=datetime.now(UTC),
                            )
                        )
                        session.commit()
                    except Exception:
                        session.rollback()

                result = self._pipeline.run(
                    job.url,
                    job_id=str(job.id),
                    inputs=inputs,
                    workflow=str(workflow) if workflow else None,
                    crawl=crawl,
                    on_progress=on_progress,
                )
                self._persist_success(session, job, result)
                metrics.incr("jobs.completed")

                # AI Understanding runs AFTER extraction (never replaces it).
                if result.success and self._settings.ai_understanding_enabled:
                    if self._settings.ai_understanding_async:
                        self._enqueue_understanding(str(job.id))
                    else:
                        self.run_understanding(str(job.id))

                return {"status": "completed", "job_id": job_id}
            except Exception as exc:
                logger.exception("scrape.failed", job_id=job_id)
                job.status = JobStatus.FAILED.value
                job.finished_at = datetime.now(UTC)
                job.error_code = "INTERNAL"
                job.error_message = str(exc)[:2000]
                job.current_stage = "failed"
                if job.started_at:
                    start = job.started_at if job.started_at.tzinfo else job.started_at.replace(tzinfo=UTC)
                    job.duration_ms = int((job.finished_at - start).total_seconds() * 1000)
                session.add(
                    JobEvent(
                        job_id=job.id,
                        stage="failed",
                        level="error",
                        message=job.error_message or "failed",
                        details={"error_code": job.error_code},
                        created_at=datetime.now(UTC),
                    )
                )
                self._sync_batch_item(session, job, None)
                session.commit()
                metrics.incr("jobs.failed")
                return {"status": "failed", "job_id": job_id}

    def _enqueue_understanding(self, job_id: str) -> None:
        """Schedule AI understanding without blocking the API or extraction completion."""
        use_celery = self._settings.use_celery
        if use_celery:
            try:
                from app.workers.tasks import run_ai_understanding

                run_ai_understanding.delay(job_id)
                return
            except Exception as exc:
                logger.warning("ai.enqueue.celery_failed", error=str(exc))

        threading.Thread(
            target=lambda: self.run_understanding(job_id),
            daemon=True,
            name=f"ai-understand-{job_id}",
        ).start()

    def run_understanding(self, job_id: str) -> dict:
        """Run AI Understanding Engine for an already-extracted job."""
        with self._session_factory() as session:
            job = session.get(Job, UUID(job_id))
            if job is None:
                return {"status": "missing"}
            data = session.query(ExtractedData).filter_by(job_id=job.id).one_or_none()
            if data is None:
                return {"status": "no_data"}

            data.ai_status = "running"
            session.add(
                JobEvent(
                    job_id=job.id,
                    stage="understanding",
                    level="info",
                    message="AI Understanding Engine started",
                    details={},
                    created_at=datetime.now(UTC),
                )
            )
            session.commit()

            try:
                # Dedicated sessions for cache — never share the job session.
                cache = UnderstandingCache(session_factory=self._session_factory)
                service = UnderstandingService(self._settings, cache=cache)
                understanding = service.understand(
                    data.normalized_payload or {},
                    url=job.url,
                )
                data.ai_understanding = understanding.to_api_dict()
                data.ai_status = understanding.status
                session.add(
                    JobEvent(
                        job_id=job.id,
                        stage="understanding",
                        level="info" if understanding.status == "completed" else "warning",
                        message=f"AI Understanding {understanding.status}",
                        details={
                            "provider": understanding.observability.provider,
                            "cache_hit": understanding.observability.cache_hit,
                            "latency_ms": understanding.observability.latency_ms,
                            "category": understanding.category.value
                            if hasattr(understanding.category, "value")
                            else str(understanding.category),
                        },
                        created_at=datetime.now(UTC),
                    )
                )
                session.commit()
                return {"status": understanding.status, "job_id": job_id}
            except Exception as exc:
                logger.exception("ai.understanding.persist_failed", job_id=job_id)
                try:
                    session.rollback()
                except Exception:
                    pass
                data = session.query(ExtractedData).filter_by(job_id=UUID(job_id)).one_or_none()
                if data is not None:
                    data.ai_status = "failed"
                    data.ai_understanding = {
                        "status": "failed",
                        "summary": "",
                        "observability": {"provider": "unknown", "error": str(exc)[:500]},
                    }
                    try:
                        session.commit()
                    except Exception:
                        session.rollback()
                return {"status": "failed", "job_id": job_id}

    def _set_stage(self, session: Session, job: Job, stage: str, progress: int) -> None:
        job.current_stage = stage
        job.progress_pct = progress
        session.add(
            PipelineLog(
                job_id=job.id,
                stage=stage,
                level="info",
                message=f"Entered stage {stage}",
                details={},
                created_at=datetime.now(UTC),
            )
        )
        session.commit()

    def _persist_success(self, session: Session, job: Job, result: PipelineResult) -> None:
        finished = datetime.now(UTC)
        job.finished_at = finished
        if job.started_at:
            start = job.started_at if job.started_at.tzinfo else job.started_at.replace(tzinfo=UTC)
            job.duration_ms = int((finished - start).total_seconds() * 1000)

        if result.profile:
            existing_profile = (
                session.query(WebsiteProfileRecord).filter_by(job_id=job.id).one_or_none()
            )
            profile_payload = {
                "url": result.profile.url,
                "normalized_url": result.profile.normalized_url,
                "profile": result.profile.model_dump(mode="json"),
                "report": {},
                "discovery": result.discovery,
                "profile_version": result.profile.profile_version,
                "discovery_version": result.discovery.get("discovery_version"),
                "schema_version": self._settings.schema_version,
                "overall_confidence": result.profile.overall_confidence,
                "probed_at": result.profile.probed_at,
            }
            if existing_profile:
                for k, v in profile_payload.items():
                    setattr(existing_profile, k, v)
            else:
                session.add(WebsiteProfileRecord(job_id=job.id, **profile_payload))
            session.flush()

        if result.plan:
            job.strategy_used = result.plan.strategy_id
            job.selected_strategy = result.plan.strategy_id
            session.add(
                StrategyDecision(
                    job_id=job.id,
                    strategy_name=result.plan.strategy_id,
                    strategy_version=result.plan.strategy_version,
                    score=result.plan.confidence * 100,
                    score_breakdown={},
                    decision="selected",
                    attempt_order=0,
                    duration_ms=int(result.timings.strategy_ms),
                    outcome="selected",
                    execution_plan=result.plan.model_dump(mode="json"),
                    created_at=datetime.now(UTC),
                )
            )

        summary = {
            "title": (result.normalized_payload or {}).get("title"),
            "sections": {
                k: (
                    int(v.get("total") or 0)
                    if isinstance(v, dict) and "total" in v
                    else (len(v) if isinstance(v, (list, dict)) else (1 if v else 0))
                )
                for k, v in (result.normalized_payload or {}).items()
            },
            "strategy": result.plan.strategy_id if result.plan else None,
            "pagination": result.pagination or {},
            "timings": {
                "intelligence_ms": result.timings.intelligence_ms,
                "strategy_ms": result.timings.strategy_ms,
                "fetch_ms": result.timings.fetch_ms,
                "clean_ms": result.timings.clean_ms,
                "plugins_ms": result.timings.plugins_ms,
                "normalize_ms": result.timings.normalize_ms,
                "validate_ms": result.timings.validate_ms,
                "total_ms": result.timings.total_ms,
            },
            "plugin_timings": result.timings.plugin_timings,
        }

        import json

        payload_bytes = len(json.dumps(result.normalized_payload or {}).encode())
        job.output_size_bytes = payload_bytes
        job.overall_confidence = float(
            (result.validation_report or {}).get("overall_confidence") or 0
        )
        job.meta = {
            **(job.meta or {}),
            "raw_html_path": result.raw_storage_path,
            "clean_html_path": result.clean_storage_path,
            "strategy_ranking": result.strategy_ranking,
            "inputs": (job.meta or {}).get("inputs") or {},
            "workflow": (job.meta or {}).get("workflow"),
            "crawl": (job.meta or {}).get("crawl") or {},
            "pagination": result.pagination or {},
        }

        ai_pending = bool(result.success and self._settings.ai_understanding_enabled)

        if result.success:
            job.status = JobStatus.COMPLETED.value
            job.progress_pct = 100
            job.current_stage = "completed"
            job.error_code = result.error_code
            job.error_message = result.error_message
        else:
            job.status = JobStatus.FAILED.value
            job.progress_pct = 100
            job.current_stage = "failed"
            job.error_code = result.error_code or "EXTRACT_FAILED"
            job.error_message = result.error_message or "Extraction failed"

        existing = session.query(ExtractedData).filter_by(job_id=job.id).one_or_none()
        ai_status = "pending" if ai_pending else ("skipped" if result.success else None)
        if existing:
            existing.payload = result.raw_payload
            existing.normalized_payload = result.normalized_payload
            existing.summary = summary
            existing.validation_report = result.validation_report
            existing.section_confidence = result.section_confidence
            existing.storage_path = result.clean_storage_path
            existing.content_hash = result.content_hash
            existing.schema_version = self._settings.schema_version
            if ai_pending:
                existing.ai_status = ai_status
                existing.ai_understanding = None
            elif result.success:
                existing.ai_status = "skipped"
        else:
            session.add(
                ExtractedData(
                    job_id=job.id,
                    payload=result.raw_payload,
                    normalized_payload=result.normalized_payload,
                    summary=summary,
                    validation_report=result.validation_report,
                    section_confidence=result.section_confidence,
                    storage_path=result.clean_storage_path,
                    content_hash=result.content_hash,
                    schema_version=self._settings.schema_version,
                    ai_status=ai_status,
                    ai_understanding=None,
                )
            )

        existing_perf = session.query(PerformanceMetric).filter_by(job_id=job.id).one_or_none()
        perf_data = dict(
            ttfb_ms=int(result.timings.fetch_ms),
            load_event_ms=int(result.timings.total_ms),
            total_requests=max(1, int(getattr(result, "pages_fetched", 1) or 1)),
            total_transfer_bytes=len(result.raw_html.encode("utf-8", errors="replace")),
            extras={
                "timings": summary["timings"],
                "plugin_timings": result.timings.plugin_timings,
            },
        )
        if existing_perf:
            for k, v in perf_data.items():
                setattr(existing_perf, k, v)
        else:
            session.add(PerformanceMetric(job_id=job.id, **perf_data))
        session.add(
            JobEvent(
                job_id=job.id,
                stage=job.current_stage,
                level="info" if result.success else "error",
                message="Pipeline finished",
                details={"success": result.success, "error_code": job.error_code},
                created_at=datetime.now(UTC),
            )
        )
        self._sync_batch_item(session, job, result)
        session.commit()

    def _sync_batch_item(self, session: Session, job: Job, result: PipelineResult | None) -> None:
        """Update parent batch item summary when this job belongs to a batch."""
        from app.core.constants import BatchStatus
        from app.models.batch import ExtractionBatch, ExtractionBatchItem

        item = session.query(ExtractionBatchItem).filter_by(job_id=job.id).one_or_none()
        if item is None:
            return
        now = datetime.now(UTC)
        item.status = job.status
        item.updated_at = now
        item.error_message = job.error_message
        if result and result.success:
            payload = result.normalized_payload or {}
            agent = payload.get("agent") or {}
            item.result_summary = {
                "title": payload.get("title"),
                "officials": payload.get("officials") or {},
                "address_normalized": agent.get("address_normalized"),
                "strategy": job.strategy_used,
            }
        batch = session.get(ExtractionBatch, item.batch_id)
        if batch is None:
            return
        items = session.query(ExtractionBatchItem).filter_by(batch_id=batch.id).all()
        completed = sum(1 for i in items if i.status == JobStatus.COMPLETED.value)
        failed = sum(1 for i in items if i.status == JobStatus.FAILED.value)
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
