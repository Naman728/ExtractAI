"""Extraction engine ports — Basic now, LLM later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExtractionTask:
    """Describes what to extract for a given job/page."""

    url: str
    job_id: str
    sections: list[str] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExtractionResult:
    """Raw plugin-merged extraction draft before normalization."""

    payload: dict[str, Any]
    confidence: float = 0.0
    diagnostics: dict[str, Any] = field(default_factory=dict)


class ExtractionEngine(ABC):
    """Abstract extraction engine. Implementations: Basic, LLM (future)."""

    name: str

    @abstractmethod
    def extract(self, html: str, task: ExtractionTask) -> ExtractionResult:
        raise NotImplementedError
