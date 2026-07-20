"""Heuristic / offline provider — no external API calls.

Used when LLM_PROVIDER=none or keys are missing. Produces structured
understanding from extraction signals so demos still work.
"""

from __future__ import annotations

import json
import time

from app.ai.providers.base import LLMMessage, LLMProvider, LLMResponse


class HeuristicProvider(LLMProvider):
    """Deterministic JSON completion used as a safe fallback."""

    name = "heuristic"

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format_json: bool = True,
    ) -> LLMResponse:
        started = time.perf_counter()
        # The understanding service interprets heuristically when this provider
        # is selected; return a minimal marker so callers know to use the
        # offline path.
        text = json.dumps({"_heuristic": True, "note": "use offline understanding path"})
        latency_ms = int((time.perf_counter() - started) * 1000)
        return LLMResponse(
            text=text,
            model="heuristic-v1",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            latency_ms=latency_ms,
            estimated_cost_usd=0.0,
        )
