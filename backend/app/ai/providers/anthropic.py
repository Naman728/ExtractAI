"""Anthropic Claude Messages API provider."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.ai.providers.base import LLMMessage, LLMProvider, LLMResponse

_COST_TABLE: dict[str, tuple[float, float]] = {
    "claude-3-5-haiku-latest": (0.80, 4.00),
    "claude-3-5-sonnet-latest": (3.00, 15.00),
    "claude-3-haiku-20240307": (0.25, 1.25),
}


def _estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    inp, out = _COST_TABLE.get(model, (0.80, 4.00))
    return (prompt_tokens * inp + completion_tokens * out) / 1_000_000


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-latest",
        *,
        base_url: str = "https://api.anthropic.com",
        timeout_seconds: float = 60.0,
        api_version: str = "2023-06-01",
    ) -> None:
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicProvider")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._api_version = api_version

    def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        response_format_json: bool = True,
    ) -> LLMResponse:
        system = "\n\n".join(m.content for m in messages if m.role == "system")
        if response_format_json:
            system = (
                (system + "\n\n") if system else ""
            ) + "Respond with a single valid JSON object only. No markdown."

        api_messages = [
            {"role": "user" if m.role == "user" else "assistant", "content": m.content}
            for m in messages
            if m.role != "system"
        ]
        if not api_messages:
            api_messages = [{"role": "user", "content": "Analyze the provided data."}]

        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": api_messages,
        }
        if system:
            payload["system"] = system

        started = time.perf_counter()
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(
                f"{self._base_url}/v1/messages",
                headers={
                    "x-api-key": self._api_key,
                    "anthropic-version": self._api_version,
                    "content-type": "application/json",
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.perf_counter() - started) * 1000)

        blocks = data.get("content") or []
        text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("output_tokens") or 0)

        return LLMResponse(
            text=text,
            model=data.get("model") or self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            raw=data,
            estimated_cost_usd=_estimate_cost(self._model, prompt_tokens, completion_tokens),
        )
