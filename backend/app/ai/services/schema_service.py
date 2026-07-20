"""Schema validation / normalization for AI understanding payloads."""

from __future__ import annotations

from typing import Any

from app.ai.models.website_profile import WebsiteUnderstanding


class SchemaService:
    """Validate and coerce AI outputs into WebsiteUnderstanding."""

    def parse(self, payload: dict[str, Any] | WebsiteUnderstanding) -> WebsiteUnderstanding:
        if isinstance(payload, WebsiteUnderstanding):
            return payload
        return WebsiteUnderstanding.model_validate(payload)

    def to_storage(self, understanding: WebsiteUnderstanding) -> dict[str, Any]:
        return understanding.model_dump(mode="json")

    def empty(self, *, status: str = "skipped", reason: str | None = None) -> WebsiteUnderstanding:
        u = WebsiteUnderstanding(status=status)
        if reason:
            u.observability.error = reason
            u.extras["reason"] = reason
        return u
