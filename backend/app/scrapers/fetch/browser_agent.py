"""Browser agent fetch engine — multi-step interactive extraction via workflows."""

from __future__ import annotations

import time
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.scrapers.fetch.base import FetchEngine, FetchResult
from app.scrapers.workflows import run_workflow
from app.scrapers.workflows.input_normalize import normalize_agent_inputs
from app.utils.url import assert_public_url

logger = get_logger(__name__)


class BrowserAgentFetchEngine(FetchEngine):
    """
    Runs a named or auto-detected workflow with arbitrary `inputs`.

    options:
      - inputs: dict[str, str]  (address, query, topics, zip, …)
      - workflow: optional workflow id
      - timeout_ms: int

    Routing:
      - No inputs → do not use this engine (strategy picks static/API/dynamic)
      - With inputs → general browser agent (same logic for every website)
      - Known hosts (e.g. BallotReady) → optional specialized fast-path
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

    def id(self) -> str:
        return "browser_agent"

    def fetch(self, url: str, *, options: dict[str, Any] | None = None) -> FetchResult:
        opts = options or {}
        safe = assert_public_url(url)
        inputs = normalize_agent_inputs(opts.get("inputs") or {})
        workflow_id = opts.get("workflow")
        timeout_ms = int(opts.get("timeout_ms", max(self._settings.playwright_timeout_ms, 60_000)))
        start = time.perf_counter()

        if not inputs:
            return FetchResult(
                url=safe,
                final_url=safe,
                status_code=0,
                html="",
                raw_bytes=b"",
                elapsed_ms=(time.perf_counter() - start) * 1000,
                error_code="VALIDATION",
                error_message="browser_agent requires non-empty inputs",
                diagnostics={"engine": self.id()},
            )

        result = run_workflow(
            safe,
            inputs,
            workflow_id=workflow_id,
            timeout_ms=timeout_ms,
        )
        elapsed = (time.perf_counter() - start) * 1000
        html = result.html or ""
        logger.info(
            "fetch.browser_agent",
            success=result.success,
            workflow=(result.structured or {}).get("workflow"),
            final_url=result.final_url,
            ms=round(elapsed, 1),
        )
        return FetchResult(
            url=safe,
            final_url=result.final_url or safe,
            status_code=200 if result.success or html else 0,
            html=html,
            raw_bytes=html.encode("utf-8", errors="replace"),
            elapsed_ms=elapsed,
            error_code=result.error_code,
            error_message=result.error_message,
            diagnostics={
                "engine": self.id(),
                "workflow": (result.structured or {}).get("workflow"),
                "steps": result.steps,
                "structured": result.structured,
                "workflow_diagnostics": result.diagnostics,
            },
        )
