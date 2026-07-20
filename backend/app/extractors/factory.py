"""Extraction engine factory."""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.extractors.base import ExtractionEngine
from app.extractors.basic import BasicExtractionEngine
from app.extractors.llm import LLMExtractionEngine


def create_extraction_engine(settings: Settings | None = None) -> ExtractionEngine:
    cfg = settings or get_settings()
    if cfg.extractor_type == "basic":
        return BasicExtractionEngine()
    if cfg.extractor_type == "llm":
        return LLMExtractionEngine()
    raise ValueError(f"Unknown extractor type: {cfg.extractor_type}")
