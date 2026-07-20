"""OpenAI chat completions provider (HTTP, no SDK required)."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.ai.providers.base import LLMMessage, LLMProvider, LLMResponse

# Approximate USD per 1M tokens (input, output) — used for observability only.
_COST_TABLE: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = _COST_TABLE.get(model, (0.15, 0.60))
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        *,
        base_url: str = "https://api.openai.com/v1",
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIProvider")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format_json: bool = True,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}

        started = time.perf_counter()
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.perf_counter() - started) * 1000)

        choice = (data.get("choices") or [{}])[0]
        text = ((choice.get("message") or {}).get("content")) or ""
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        model = data.get("model") or self._model

        return LLMResponse(
            text=text,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            raw=data,
            estimated_cost_usd=_estimate_cost(self._model, prompt_tokens, completion_tokens),
        )
