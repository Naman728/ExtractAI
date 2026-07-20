"""Browser Agent strategy — interactive multi-step extraction with job inputs."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.strategy.base import ExtractionStrategy
from app.strategy.scoring import clamp, complexity
from app.strategy.types import ExecutionPlan, StrategyScore
from app.website_intelligence.profile import WebsiteProfile


def _job_inputs(profile: WebsiteProfile) -> dict[str, Any]:
    diag = profile.diagnostics or {}
    raw = diag.get("job_inputs") or {}
    return raw if isinstance(raw, dict) else {}


def _workflow(profile: WebsiteProfile) -> str | None:
    diag = profile.diagnostics or {}
    wf = diag.get("workflow")
    return str(wf) if wf else None


class BrowserAgentStrategy(ExtractionStrategy):
    """
    Selected when the job provides interactive `inputs` (query, address, topics, …).

    Routing rule (Browserbase-style):
      - No inputs → StrategyEngine picks static / JSON-LD / dynamic / API (normal extract)
      - With inputs → this strategy → general browser agent for ANY website
      - Known hosts (BallotReady) → optional specialized workflow inside the agent
    """

    def id(self) -> str:
        return "browser_agent"

    def name(self) -> str:
        return "Browser Agent"

    def priority(self) -> int:
        return 95

    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, profile: WebsiteProfile) -> bool:
        inputs = _job_inputs(profile)
        if not inputs:
            return False
        return (profile.status_code.value or 0) != 0

    def score(self, profile: WebsiteProfile) -> StrategyScore:
        inputs = _job_inputs(profile)
        breakdown: dict[str, float] = {"inputs_present": 50.0}
        score = 50.0
        advantages = [
            "Multi-step browser interaction",
            "Session-preserving extraction",
            "Arbitrary inputs (address, query, zip, …)",
        ]
        disadvantages = ["Slower", "UI-fragile", "Requires Playwright"]

        score += min(30.0, 8.0 * len(inputs))
        breakdown["input_keys"] = float(min(30.0, 8.0 * len(inputs)))

        if inputs.get("address"):
            score += 15
            breakdown["address"] = 15
            advantages.append("Address/location workflow ready")

        host = (profile.final_url or profile.url or "").lower()
        if "ballotready" in host or "civicengine" in host:
            score += 20
            breakdown["ballotready"] = 20
            advantages.append("BallotReady officials workflow available")

        if (profile.forms_detected.value or 0) >= 1:
            score += 5
            breakdown["forms"] = 5

        score = clamp(score)
        return StrategyScore(
            strategy_id=self.id(),
            strategy_name=self.name(),
            suitability_score=round(score, 1),
            confidence=0.9,
            estimated_runtime_ms=12_000 + int(complexity(profile) * 80),
            estimated_cost=70.0,
            reason=f"Browser agent selected for inputs={list(inputs.keys())}",
            warnings=[],
            advantages=advantages,
            disadvantages=disadvantages,
            can_handle=True,
            score_breakdown=breakdown,
        )

    def build_execution_plan(self, profile: WebsiteProfile) -> ExecutionPlan:
        settings = get_settings()
        inputs = _job_inputs(profile)
        workflow = _workflow(profile)
        return ExecutionPlan(
            strategy=self.name(),
            strategy_id=self.id(),
            fetch_engine="browser_agent",
            cleaner="html_cleaner_v1",
            extractor="basic_extraction_engine",
            normalizer="normalization_engine_v1",
            validator="validation_engine_v1",
            storage="local_storage",
            estimated_duration_ms=15_000 + int(complexity(profile) * 50),
            complexity=max(complexity(profile), 40.0),
            confidence=0.9,
            warnings=[],
            fallback_strategy="dynamic_browser",
            future_alternatives=["rest_api", "graphql"],
            pipeline_stages=[
                "launch_browser",
                "apply_inputs",
                "interact",
                "wait_results",
                "capture_dom",
                "structured_extract",
                "clean_html",
                "plugins",
                "normalize",
                "validate",
                "persist",
            ],
            options={
                "headless": True,
                "timeout_ms": max(settings.playwright_timeout_ms, 60_000),
                "inputs": inputs,
                "workflow": workflow,
            },
            strategy_version=self.version(),
            pipeline_version=settings.pipeline_version,
        )
