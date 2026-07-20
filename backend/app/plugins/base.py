"""Extraction plugin protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup


@dataclass(slots=True)
class PluginContext:
    url: str
    final_url: str
    html: str
    soup: BeautifulSoup
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PluginResult:
    name: str
    section: str
    data: Any
    confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


class ExtractionPlugin(ABC):
    """One responsibility per plugin. Auto-registered via PluginRegistry."""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def section(self) -> str: ...

    def version(self) -> str:
        return "1.0.0"

    def priority(self) -> int:
        return 50

    def requires(self) -> list[str]:
        return []

    def is_enabled(self) -> bool:
        return True

    @abstractmethod
    def extract(self, ctx: PluginContext) -> PluginResult: ...
