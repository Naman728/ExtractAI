"""Ollama local LLM provider."""

from __future__ import annotations

import time
from typing import Any

import httpx

from app.ai.providers.base import LLMMessage, LLMProvider, LLMResponse


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(
        self,
        model: str = "llama3.2",
        *,
        base_url: str = "http://127.0.0.1:11434",
        timeout_seconds: float = 120.0,
        api_key: str | None = None,  # unused; accepted for factory uniformity
    ) -> None:
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
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if response_format_json:
            payload["format"] = "json"

        started = time.perf_counter()
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(f"{self._base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
        latency_ms = int((time.perf_counter() - started) * 1000)

        text = ((data.get("message") or {}).get("content")) or ""
        prompt_tokens = int(data.get("prompt_eval_count") or 0)
        completion_tokens = int(data.get("eval_count") or 0)

        return LLMResponse(
            text=text,
            model=data.get("model") or self._model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            raw=data,
            estimated_cost_usd=0.0,
        )

    def healthcheck(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{self._base_url}/api/tags")
                return r.status_code == 200
        except Exception:
            return False
