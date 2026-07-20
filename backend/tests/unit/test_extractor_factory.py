"""Unit tests for extraction engine factory."""

import pytest

from app.core.config import Settings
from app.extractors.basic import BasicExtractionEngine
from app.extractors.factory import create_extraction_engine
from app.extractors.llm import LLMExtractionEngine


def test_basic_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(
        jwt_secret_key="x" * 32,
        extractor_type="basic",
    )
    engine = create_extraction_engine(settings)
    assert isinstance(engine, BasicExtractionEngine)


def test_llm_factory_returns_stub() -> None:
    settings = Settings(
        jwt_secret_key="x" * 32,
        extractor_type="llm",
    )
    engine = create_extraction_engine(settings)
    assert isinstance(engine, LLMExtractionEngine)
    with pytest.raises(NotImplementedError):
        engine.extract("<html></html>", task=__import__("app.extractors.base", fromlist=["ExtractionTask"]).ExtractionTask(url="https://example.com", job_id="1"))
