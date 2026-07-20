"""LLM extraction engine — reserved for future AI integration."""

from __future__ import annotations

from app.extractors.base import ExtractionEngine, ExtractionResult, ExtractionTask


class LLMExtractionEngine(ExtractionEngine):
    """
    Future LLM-powered extraction.

    Implements the same interface as BasicExtractionEngine.
    Not wired until EXTRACTOR_TYPE=llm and a provider adapter is configured.
    """

    name = "llm"

    def extract(self, html: str, task: ExtractionTask) -> ExtractionResult:
        raise NotImplementedError(
            "LLMExtractionEngine is reserved for future AI support. "
            "Use BasicExtractionEngine (EXTRACTOR_TYPE=basic)."
        )
