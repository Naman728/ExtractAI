"""Static HTML fetch strategy."""

from __future__ import annotations

from app.core.config import get_settings
from app.strategy.base import ExtractionStrategy
from app.strategy.scoring import (
    clamp,
    cloudflare_blocked,
    complexity,
    has_json_ld,
    js_required,
    rendering_mode,
)
from app.strategy.types import ExecutionPlan, StrategyScore
from app.website_intelligence.profile import WebsiteProfile


class StaticHTMLStrategy(ExtractionStrategy):
    def id(self) -> str:
        return "static_html"

    def name(self) -> str:
        return "Static HTML"

    def priority(self) -> int:
        return 40

    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, profile: WebsiteProfile) -> bool:
        if profile.status_code.value == 0:
            return False
        if profile.captcha.value:
            return False
        return True

    def score(self, profile: WebsiteProfile) -> StrategyScore:
        breakdown: dict[str, float] = {}
        score = 55.0
        warnings: list[str] = []
        advantages = ["Low cost", "Fast", "No browser overhead"]
        disadvantages: list[str] = []

        mode = rendering_mode(profile)
        if mode == "static":
            score += 30
            breakdown["static_mode"] = 30
            advantages.append("Page renders as static HTML")
        elif mode == "ssr":
            score += 22
            breakdown["ssr_mode"] = 22
            advantages.append("SSR HTML likely sufficient")
        elif mode == "hybrid":
            score += 8
            breakdown["hybrid_mode"] = 8
            warnings.append("Hybrid page — some content may need JS")
        elif mode == "csr_heavy":
            score -= 35
            breakdown["csr_penalty"] = -35
            disadvantages.append("CSR-heavy — static fetch may miss content")
            warnings.append("JavaScript-heavy page reduces static suitability")

        if js_required(profile):
            score -= 25
            breakdown["js_required"] = -25
            disadvantages.append("JS required for primary content")

        if cloudflare_blocked(profile):
            score -= 20
            breakdown["cloudflare"] = -20
            warnings.append("Cloudflare challenge may block simple HTTP fetch")

        if has_json_ld(profile):
            score -= 5  # Prefer JSON-LD strategy slightly when present
            breakdown["prefer_jsonld"] = -5

        cx = complexity(profile)
        if cx > 70:
            score -= 10
            breakdown["high_complexity"] = -10

        score = clamp(score)
        conf = min(0.95, 0.55 + (score / 200) + (0.15 if mode in {"static", "ssr"} else 0))

        return StrategyScore(
            strategy_id=self.id(),
            strategy_name=self.name(),
            suitability_score=round(score, 1),
            confidence=round(conf, 3),
            estimated_runtime_ms=800 + int(profile.response_time_ms.value or 200),
            estimated_cost=12.0,
            reason=(
                f"Static HTML scored {score:.0f} for rendering_mode={mode}, "
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
            fetch_engine="requests_http",
            cleaner="html_cleaner_v1",
            extractor="basic_extraction_engine",
            normalizer="normalization_engine_v1",
            validator="validation_engine_v1",
            storage="local_storage",
            estimated_duration_ms=1500 + int(profile.response_time_ms.value or 0),
            complexity=complexity(profile),
            confidence=0.8 if not js_required(profile) else 0.55,
            warnings=(
                ["JS required — static plan may yield incomplete content"]
                if js_required(profile)
                else []
            ),
            fallback_strategy="dynamic_browser",
            future_alternatives=["rest_api", "llm"],
            pipeline_stages=[
                "fetch_static",
                "clean_html",
                "extract_basic",
                "normalize",
                "validate",
                "persist",
            ],
            options={"follow_redirects": True, "max_bytes": settings.max_html_bytes},
            strategy_version=self.version(),
            pipeline_version=settings.pipeline_version,
        )
