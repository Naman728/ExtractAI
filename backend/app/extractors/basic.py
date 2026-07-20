"""Basic extraction engine — plugin runtime wired in Phase 4."""

from __future__ import annotations

from app.extractors.base import ExtractionEngine, ExtractionResult, ExtractionTask


class BasicExtractionEngine(ExtractionEngine):
    """Deterministic HTML extraction via plugin registry (Phase 4)."""

    name = "basic"

    def extract(self, html: str, task: ExtractionTask) -> ExtractionResult:
        if not html:
            return ExtractionResult(payload={}, confidence=0.0, diagnostics={"empty": True})
        # Phase 2: interface only. Plugin runtime lands in Phase 4.
        return ExtractionResult(
            payload={},
            confidence=0.0,
            diagnostics={
                "engine": self.name,
                "url": task.url,
                "status": "awaiting_phase_4_plugins",
            },
        )
