"""Shared constants and enums."""

from enum import StrEnum


class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class ExportFormat(StrEnum):
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


class ExportStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    FAILED = "failed"
    EXPIRED = "expired"


class SnapshotKind(StrEnum):
    SCREENSHOT_DESKTOP = "screenshot_desktop"
    SCREENSHOT_MOBILE = "screenshot_mobile"
    DOM = "dom"
    HTML_RENDERED = "html_rendered"
    HTML_RAW = "html_raw"
    CONSOLE = "console"
    HAR = "har"


class StrategyDecisionOutcome(StrEnum):
    SELECTED = "selected"
    SKIPPED = "skipped"
    FAILED = "failed"
    CASCADE_FALLBACK = "cascade_fallback"
    SUCCEEDED = "succeeded"


class PluginStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    INCOMPATIBLE = "incompatible"


GUEST_HEADER = "X-Guest-Key"
REQUEST_ID_HEADER = "X-Request-Id"

ALLOWED_URL_SCHEMES = frozenset({"http", "https"})
