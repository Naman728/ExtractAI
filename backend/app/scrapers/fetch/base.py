"""Fetch engine ports — Strategy Pattern for page acquisition."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class FetchResult:
    url: str
    final_url: str
    status_code: int
    html: str
    raw_bytes: bytes
    headers: dict[str, str] = field(default_factory=dict)
    elapsed_ms: float = 0.0
    error_code: str | None = None
    error_message: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


class FetchEngine(ABC):
    """Acquires HTML for a URL. Selected by ExecutionPlan.fetch_engine."""

    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, url: str, *, options: dict[str, Any] | None = None) -> FetchResult:
        raise NotImplementedError
