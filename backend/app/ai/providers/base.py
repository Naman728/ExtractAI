"""LLM provider abstract interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMMessage:
    role: str  # system | user | assistant
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    raw: dict[str, Any] = field(default_factory=dict)
    estimated_cost_usd: float = 0.0


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    name: str = "base"

    @abstractmethod
    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format_json: bool = True,
    ) -> LLMResponse:
        """Run a chat completion and return text (+ usage metadata)."""

    def healthcheck(self) -> bool:
        return True
