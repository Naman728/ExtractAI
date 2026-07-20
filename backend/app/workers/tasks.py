"""Celery tasks — full extraction pipeline."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.observability import set_job_id
from app.services.scrape_service import ScrapeService
from app.workers.celery_app import celery_app

configure_logging()
logger = get_logger(__name__)

_settings = get_settings()
_sync_engine = create_engine(_settings.database_url_sync, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(bind=_sync_engine, autoflush=False, expire_on_commit=False)


@celery_app.task(name="app.workers.tasks.run_extraction_pipeline", bind=True, max_retries=2)
def run_extraction_pipeline(self, job_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Execute the full traditional extraction pipeline for a job."""
    set_job_id(job_id)
    logger.info("pipeline.task_start", job_id=job_id)
    service = ScrapeService(SyncSessionLocal, _settings)
    try:
        return service.run_job(job_id)
    except Exception as exc:
        logger.exception("pipeline.task_error", job_id=job_id)
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="app.workers.tasks.run_ai_understanding", bind=True, max_retries=1)
def run_ai_understanding(self, job_id: str) -> dict:  # type: ignore[no-untyped-def]
    """Run AI Understanding Engine after extraction (async, non-blocking)."""
    set_job_id(job_id)
    logger.info("ai.understanding.task_start", job_id=job_id)
    service = ScrapeService(SyncSessionLocal, _settings)
    try:
        return service.run_understanding(job_id)
    except Exception as exc:
        logger.exception("ai.understanding.task_error", job_id=job_id)
        raise self.retry(exc=exc, countdown=10) from exc
