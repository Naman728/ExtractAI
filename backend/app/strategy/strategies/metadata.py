"""Metadata (Open Graph / Twitter Cards) strategy."""

from __future__ import annotations

from app.core.config import get_settings
from app.strategy.base import ExtractionStrategy
from app.strategy.scoring import clamp, complexity, has_json_ld, has_rich_metadata
from app.strategy.types import ExecutionPlan, StrategyScore
from app.website_intelligence.profile import WebsiteProfile


class MetadataStrategy(ExtractionStrategy):
    def id(self) -> str:
        return "metadata"

    def name(self) -> str:
        return "Structured Metadata"

    def priority(self) -> int:
        return 60

    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, profile: WebsiteProfile) -> bool:
        return has_rich_metadata(profile) or bool(profile.title.value)

    def score(self, profile: WebsiteProfile) -> StrategyScore:
        breakdown: dict[str, float] = {}
        score = 45.0
        warnings: list[str] = []
        advantages = ["Fast", "Good for link unfurling", "Stable meta tags"]
        disadvantages = ["Shallow content", "Not ideal for deep entity extraction"]

        og_count = len(profile.open_graph.value or {})
        tw_count = len(profile.twitter_cards.value or {})
        if og_count:
            score += min(25, og_count * 4)
            breakdown["open_graph"] = float(min(25, og_count * 4))
            advantages.append(f"{og_count} Open Graph tags")
        if tw_count:
            score += min(15, tw_count * 3)
            breakdown["twitter"] = float(min(15, tw_count * 3))
        if profile.title.value:
            score += 5
            breakdown["title"] = 5
        if has_json_ld(profile):
            score -= 12
            breakdown["prefer_jsonld"] = -12
            warnings.append("JSON-LD available — prefer JSON-LD strategy when deeper entities matter")

        if not has_rich_metadata(profile):
            score -= 15
            breakdown["thin_meta"] = -15
            warnings.append("Limited OG/Twitter metadata")

        score = clamp(score)
        conf = 0.85 if og_count >= 3 else 0.65

        return StrategyScore(
            strategy_id=self.id(),
            strategy_name=self.name(),
            suitability_score=round(score, 1),
            confidence=round(conf, 3),
            estimated_runtime_ms=500 + int(profile.response_time_ms.value or 50),
            estimated_cost=5.0,
            reason=f"Metadata strategy scored {score:.0f} (og={og_count}, twitter={tw_count})",
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
            cleaner="meta_only",
            extractor="metadata_parser",
            normalizer="normalization_engine_v1",
            validator="validation_engine_v1",
            storage="local_storage",
            estimated_duration_ms=700 + int(profile.response_time_ms.value or 0),
            complexity=max(5.0, complexity(profile) * 0.25),
            confidence=0.85,
            warnings=[],
            fallback_strategy="static_html",
            future_alternatives=["json_ld"],
            pipeline_stages=[
                "fetch_static",
                "parse_meta",
                "normalize",
                "validate",
                "persist",
            ],
            options={
                "open_graph_keys": list((profile.open_graph.value or {}).keys())[:20],
                "twitter_keys": list((profile.twitter_cards.value or {}).keys())[:20],
            },
            strategy_version=self.version(),
            pipeline_version=settings.pipeline_version,
        )
