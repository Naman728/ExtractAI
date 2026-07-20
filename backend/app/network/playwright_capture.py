"""Optional Playwright network traffic capture (metadata only)."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.network.headers import redact_headers
from app.network.types import CapturedRequestMeta
from app.utils.url import assert_public_url

logger = get_logger(__name__)


class PlaywrightNetworkCapture:
    """
    Observe XHR/Fetch/document requests during a normal page load.

    Stores metadata only — response bodies are never persisted.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def capture(self, url: str, *, timeout_ms: int | None = None) -> list[CapturedRequestMeta]:
        safe = assert_public_url(url)
        timeout = timeout_ms or min(self._settings.playwright_timeout_ms, 20_000)
        captured: list[CapturedRequestMeta] = []
        started: dict[str, float] = {}

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.info("network.playwright_unavailable")
            return []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (compatible; ExtractAI-Network/1.0; "
                        "+https://extractai.local)"
                    ),
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()
                page.set_default_timeout(timeout)

                def on_request(request: Any) -> None:
                    started[request.url] = time.perf_counter()

                def on_response(response: Any) -> None:
                    req = response.request
                    resource = req.resource_type
                    # Focus on data-bearing traffic; keep a few documents for context
                    if resource not in {
                        "xhr",
                        "fetch",
                        "document",
                        "websocket",
                        "eventsource",
                        "other",
                    }:
                        # Still keep JSON-looking scripts/styles skipped
                        if resource in {"stylesheet", "image", "font", "media"}:
                            return
                    duration = None
                    if req.url in started:
                        duration = (time.perf_counter() - started[req.url]) * 1000
                    headers = {k.lower(): v for k, v in response.headers.items()}
                    captured.append(
                        CapturedRequestMeta(
                            url=response.url,
                            method=req.method,
                            status_code=response.status,
                            content_type=headers.get("content-type"),
                            resource_type=resource,
                            duration_ms=duration,
                            source="playwright",
                            request_headers_redacted=redact_headers(
                                {k.lower(): v for k, v in req.headers.items()}
                            ),
                            response_headers_redacted=redact_headers(headers),
                        )
                    )

                page.on("request", on_request)
                page.on("response", on_response)
                page.goto(safe, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=min(timeout, 8000))
                except Exception:
                    pass
                browser.close()
        except Exception as exc:
            logger.warning("network.playwright_capture_failed", error=str(exc))
            return captured

        # Cap volume
        return captured[:200]
