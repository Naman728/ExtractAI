"""Workflow protocol for browser_agent multi-step extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowResult:
    """Outcome of an interactive browser workflow."""

    success: bool
    final_url: str
    html: str
    title: str = ""
    structured: dict[str, Any] = field(default_factory=dict)
    steps: list[dict[str, Any]] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)


class BrowserWorkflow(ABC):
    """One named multi-step interaction recipe (BallotReady, generic form, …)."""

    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def can_handle(self, url: str, inputs: dict[str, str]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run(
        self,
        url: str,
        inputs: dict[str, str],
        *,
        timeout_ms: int = 60_000,
    ) -> WorkflowResult:
        raise NotImplementedError
