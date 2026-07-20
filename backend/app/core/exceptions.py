"""Domain and HTTP-mappable application exceptions."""

from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "INTERNAL",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, code="NOT_FOUND", status_code=404, **kwargs)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", **kwargs: Any) -> None:
        super().__init__(message, code="UNAUTHORIZED", status_code=401, **kwargs)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", **kwargs: Any) -> None:
        super().__init__(message, code="FORBIDDEN", status_code=403, **kwargs)


class ValidationAppError(AppError):
    def __init__(self, message: str = "Validation failed", **kwargs: Any) -> None:
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, **kwargs)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict", **kwargs: Any) -> None:
        super().__init__(message, code="CONFLICT", status_code=409, **kwargs)


class QuotaExceededError(AppError):
    def __init__(self, message: str = "Guest job quota exceeded", **kwargs: Any) -> None:
        super().__init__(message, code="QUOTA_EXCEEDED", status_code=429, **kwargs)


class InvalidUrlError(AppError):
    def __init__(self, message: str = "Invalid URL", **kwargs: Any) -> None:
        super().__init__(message, code="INVALID_URL", status_code=400, **kwargs)


class SsrfBlockedError(AppError):
    def __init__(self, message: str = "URL blocked by SSRF protection", **kwargs: Any) -> None:
        super().__init__(message, code="SSRF_BLOCKED", status_code=400, **kwargs)


class RateLimitError(AppError):
    def __init__(self, message: str = "Rate limit exceeded", **kwargs: Any) -> None:
        super().__init__(message, code="RATE_LIMITED", status_code=429, **kwargs)
