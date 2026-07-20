"""Dynamic browser (Playwright) strategy — plan only, no browser execution here."""

from __future__ import annotations

from app.core.config import get_settings
from app.strategy.base import ExtractionStrategy
from app.strategy.scoring import (
    clamp,
    captcha_present,
    cloudflare_blocked,
    complexity,
    js_required,
    rendering_mode,
)
from app.strategy.types import ExecutionPlan, StrategyScore
from app.website_intelligence.profile import WebsiteProfile


class DynamicBrowserStrategy(ExtractionStrategy):
    def id(self) -> str:
        return "dynamic_browser"

    def name(self) -> str:
        return "Dynamic Browser"

    def priority(self) -> int:
        return 30

    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, profile: WebsiteProfile) -> bool:
        return profile.status_code.value != 0

    def score(self, profile: WebsiteProfile) -> StrategyScore:
        breakdown: dict[str, float] = {}
        score = 40.0
        warnings: list[str] = []
        advantages = ["Renders JavaScript", "Captures network signals later", "Handles SPA shells"]
        disadvantages = ["Higher cost", "Slower", "More fragile under bot protection"]

        mode = rendering_mode(profile)
        if mode == "csr_heavy":
            score += 40
            breakdown["csr_boost"] = 40
            advantages.append("Optimal for CSR-heavy pages")
        elif mode == "hybrid":
            score += 20
            breakdown["hybrid_boost"] = 20
        elif mode in {"static", "ssr"}:
            score -= 15
            breakdown["static_demote"] = -15
            disadvantages.append("Overkill for static/SSR pages")

        if js_required(profile):
            score += 25
            breakdown["js_required"] = 25

        if cloudflare_blocked(profile):
            score += 10
            breakdown["cloudflare_need"] = 10
            warnings.append("Cloudflare present — browser may still be challenged")

        if captcha_present(profile):
            score -= 30
            breakdown["captcha"] = -30
            warnings.append("CAPTCHA detected — browser plan may fail without human/solver")
            disadvantages.append("CAPTCHA blocks automated browser")

        cx = complexity(profile)
        if cx >= 60:
            score += 8
            breakdown["complexity"] = 8

        score = clamp(score)
        conf = min(0.92, 0.5 + (score / 200) + (0.2 if js_required(profile) else 0))

        return StrategyScore(
            strategy_id=self.id(),
            strategy_name=self.name(),
            suitability_score=round(score, 1),
            confidence=round(conf, 3),
            estimated_runtime_ms=5000 + int(cx * 40),
            estimated_cost=65.0,
            reason=(
                f"Dynamic browser scored {score:.0f} for rendering_mode={mode}, "
                f"js_required={js_required(profile)}"
            ),
            warnings=warnings,
            advantages=advantages,
            disadvantages=disadvantages,
            can_handle=True,
            score_breakdown=breakdown,
        )

    def build_execution_plan(self, profile: WebsiteProfile) -> ExecutionPlan:
        settings = get_settings()
        return ExecutionPlan(
            strategy=self.name(),
            strategy_id=self.id(),
            fetch_engine="playwright",
            cleaner="html_cleaner_v1",
            extractor="basic_extraction_engine",
            normalizer="normalization_engine_v1",
            validator="validation_engine_v1",
            storage="local_storage",
            estimated_duration_ms=6000 + int(complexity(profile) * 50),
            complexity=complexity(profile),
            confidence=0.75 if js_required(profile) else 0.6,
            warnings=(
                ["CAPTCHA may block execution"]
                if captcha_present(profile)
                else []
            ),
            fallback_strategy="static_html",
            future_alternatives=["remote_browser", "browser_agent"],
            pipeline_stages=[
                "launch_browser",
                "navigate",
                "wait_network",
                "capture_dom",
                "clean_html",
                "extract_basic",
                "normalize",
                "validate",
                "persist",
            ],
            options={
                "headless": True,
                "timeout_ms": settings.playwright_timeout_ms,
                "capture_network": True,
                "capture_screenshots": True,
            },
            strategy_version=self.version(),
            pipeline_version=settings.pipeline_version,
        )
