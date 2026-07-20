"""Redis sliding-window rate limiter for API soft-production."""

from __future__ import annotations

import time
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_SKIP_PREFIXES = (
    "/health",
    "/ready",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def _client_key(request: Request) -> str:
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer ") and len(auth) > 20:
        # Bucket by token prefix — avoids sharing one IP bucket across users on NAT
        return f"auth:{auth[7:23]}"
    guest = request.headers.get("x-guest-key") or ""
    if guest:
        return f"guest:{guest[:48]}"
    forwarded = request.headers.get("x-forwarded-for") or ""
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "unknown")
    return f"ip:{ip}"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce per-minute request budgets via Redis. Fails open if Redis is down."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._redis: Any | None = None
        self._redis_failed = False

    def _client(self) -> Any | None:
        if self._redis_failed:
            return None
        if self._redis is not None:
            return self._redis
        try:
            import redis

            settings = get_settings()
            self._redis = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
            self._redis.ping()
            return self._redis
        except Exception as exc:
            self._redis_failed = True
            logger.warning("rate_limit.redis_unavailable", error=str(exc))
            return None

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        path = request.url.path
        if request.method == "OPTIONS" or any(path == p or path.startswith(p + "/") for p in _SKIP_PREFIXES):
            return await call_next(request)

        # Only gate write-ish / expensive API traffic
        api_prefix = get_settings().api_prefix.rstrip("/")
        if not path.startswith(api_prefix):
            return await call_next(request)

        settings = get_settings()
        auth = request.headers.get("authorization") or ""
        limit = (
            settings.rate_limit_auth_per_minute
            if auth.lower().startswith("bearer ")
            else settings.rate_limit_guest_per_minute
        )
        key = f"rl:{_client_key(request)}:{int(time.time() // 60)}"

        client = self._client()
        count = 0
        if client is not None:
            try:
                count = int(client.incr(key))
                if count == 1:
                    client.expire(key, 70)
            except Exception as exc:
                logger.warning("rate_limit.incr_failed", error=str(exc))
                return await call_next(request)

            if count > limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMITED",
                            "message": f"Rate limit exceeded ({limit}/minute). Retry shortly.",
                            "details": {"limit_per_minute": limit},
                        }
                    },
                    headers={"Retry-After": "60"},
                )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        if client is not None and count:
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
