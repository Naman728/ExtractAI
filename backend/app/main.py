"""FastAPI application factory."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.constants import REQUEST_ID_HEADER
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger
from app.observability import set_trace_id

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    settings = get_settings()
    logger.info("app.startup", app=settings.app_name, env=settings.app_env)
    # Ensure local storage root exists
    from app.storage import create_storage_backend

    create_storage_backend()
    yield
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Guest-Key",
            "X-Guest-Jobs-Remaining",
            REQUEST_ID_HEADER,
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "Retry-After",
        ],
    )

    from app.middleware.rate_limit import RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        set_trace_id(request_id)
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL",
                    "message": "An unexpected error occurred",
                    "details": {},
                }
            },
        )

    app.include_router(api_router, prefix=settings.api_prefix)
    # Health also at root for probes
    from app.api.v1.health import router as health_router

    app.include_router(health_router)
    return app


app = create_app()
