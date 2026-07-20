"""JSON-LD / Schema.org strategy."""

from __future__ import annotations

from app.core.config import get_settings
from app.strategy.base import ExtractionStrategy
from app.strategy.scoring import clamp, complexity, has_json_ld
from app.strategy.types import ExecutionPlan, StrategyScore
from app.website_intelligence.profile import WebsiteProfile


class JSONLDStrategy(ExtractionStrategy):
    def id(self) -> str:
        return "json_ld"

    def name(self) -> str:
        return "JSON-LD"

    def priority(self) -> int:
        return 70

    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, profile: WebsiteProfile) -> bool:
        return has_json_ld(profile) or bool(profile.schema_org_types.value)

    def score(self, profile: WebsiteProfile) -> StrategyScore:
        breakdown: dict[str, float] = {}
        score = 50.0
        warnings: list[str] = []
        advantages = ["Structured data", "High fidelity entities", "Cheap vs browser"]
        disadvantages: list[str] = []

        types = profile.schema_org_types.value or []
        if has_json_ld(profile):
            score += 30
            breakdown["json_ld_present"] = 30
        if types:
            score += min(20, 5 * len(types))
            breakdown["schema_types"] = float(min(20, 5 * len(types)))
            advantages.append(f"Schema types: {', '.join(types[:5])}")
        else:
            warnings.append("JSON-LD present but no @type detected")
            score -= 5
            breakdown["missing_types"] = -5

        if profile.javascript_required.value and not has_json_ld(profile):
            # can_handle would usually be false, but keep safe
            score -= 20
            breakdown["js_without_ld"] = -20

        # Prefer over static when rich LD exists
        if has_json_ld(profile) and types:
            score += 8
            breakdown["rich_ld_bonus"] = 8

        score = clamp(score)
        conf = min(0.97, 0.7 + 0.05 * len(types))

        return StrategyScore(
            strategy_id=self.id(),
            strategy_name=self.name(),
            suitability_score=round(score, 1),
            confidence=round(conf, 3),
            estimated_runtime_ms=600 + int(profile.response_time_ms.value or 100),
            estimated_cost=8.0,
            reason=f"JSON-LD strategy scored {score:.0f} with types={types[:5]}",
            warnings=warnings,
            advantages=advantages,
            disadvantages=disadvantages or ["Limited to embedded structured data"],
            can_handle=True,
            score_breakdown=breakdown,
        )

    def build_execution_plan(self, profile: WebsiteProfile) -> ExecutionPlan:
        settings = get_settings()
        return ExecutionPlan(
            strategy=self.name(),
            strategy_id=self.id(),
            fetch_engine="requests_http",
            cleaner="noop_or_light",
            extractor="json_ld_parser",
            normalizer="normalization_engine_v1",
            validator="validation_engine_v1",
            storage="local_storage",
            estimated_duration_ms=900 + int(profile.response_time_ms.value or 0),
            complexity=max(10.0, complexity(profile) * 0.4),
            confidence=0.9,
            warnings=[],
            fallback_strategy="metadata",
            future_alternatives=["static_html", "llm"],
            pipeline_stages=[
                "fetch_static",
                "parse_json_ld",
                "normalize",
                "validate",
                "persist",
            ],
            options={"schema_types": profile.schema_org_types.value},
            strategy_version=self.version(),
            pipeline_version=settings.pipeline_version,
        )
