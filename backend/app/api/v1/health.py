"""Health and readiness probes."""

from fastapi import APIRouter
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.api.deps import AppSettings, DbSession
from app.engines.versions import current_version_pins
from app.schemas import HealthResponse, ReadyResponse
from app.services.mail_service import MailService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: AppSettings) -> HealthResponse:
    pins = current_version_pins()
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        version=pins.pipeline_version,
    )


@router.get("/health/mail")
async def health_mail(settings: AppSettings) -> dict:
    """Safe mail config probe (no secrets) — used to debug signup delivery."""
    mail = MailService(settings)
    return {
        "enabled": mail.enabled,
        "transport": mail._transport(),
        "sender_configured": bool(mail._sender_email()),
        "smtp_configured": mail._smtp_ready(),
        "gmail_smtp_configured": mail._smtp_ready(),  # back-compat
        "brevo_configured": bool((settings.brevo_api_key or "").strip()),
        "frontend_public_url": settings.frontend_public_url,
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
    }


@router.get("/ready", response_model=ReadyResponse)
async def ready(session: DbSession, settings: AppSettings) -> ReadyResponse:
    db_status = "ok"
    redis_status = "ok"

    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    try:
        client = redis_from_url(settings.redis_url)
        await client.ping()
        await client.aclose()
    except Exception:
        redis_status = "error"

    status = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return ReadyResponse(status=status, database=db_status, redis=redis_status)
