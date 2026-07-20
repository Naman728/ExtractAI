"""Strategy Engine considers HTML / REST / GraphQL / JSON as possible sources."""

from __future__ import annotations

from datetime import UTC, datetime

from app.strategy.data_sources import enrich_data_sources
from app.strategy.engine import StrategyEngine
from app.strategy.types import ExecutionPlan
from app.website_intelligence.profile import WebsiteProfile
from app.website_intelligence.types import ApiHint, ConfidentValue, GraphqlHint


def _cv(value, confidence: float = 0.9):
    return ConfidentValue(value=value, confidence=confidence, evidence=["test"])


def _base_profile(**overrides) -> WebsiteProfile:
    data = dict(
        url="https://example.com",
        final_url="https://example.com/",
        normalized_url="https://example.com/",
        profile_version="1.0.0",
        probed_at=datetime.now(UTC),
        status_code=_cv(200),
        content_type=_cv("text/html"),
        charset=_cv("utf-8"),
        server=_cv("nginx"),
        response_time_ms=_cv(120.0),
        estimated_page_size_bytes=_cv(5000),
        redirect_chain=_cv([]),
        redirect_count=_cv(0),
        framework=_cv(None),
        cms=_cv(None),
        rendering_mode=_cv("static"),
        javascript_required=_cv(False),
        technologies=_cv([]),
        bot_protection=_cv("none"),
        cloudflare=_cv(False),
        captcha=_cv(False),
        auth_required=_cv(False),
        auth_signals=_cv([]),
        cookies_present=_cv(False),
        cookie_names=_cv([]),
        language=_cv("en"),
        canonical_url=_cv("https://example.com/"),
        favicon=_cv(None),
        title=_cv("Example"),
        has_json_ld=_cv(False),
        schema_org_types=_cv([]),
        open_graph=_cv({}),
        twitter_cards=_cv({}),
        robots=_cv({"available": True}),
        sitemap_urls=_cv([]),
        rss_urls=_cv([]),
        discovered_apis=_cv([]),
        discovered_graphql=_cv([]),
        discovered_assets=_cv([]),
        social_links=_cv([]),
        downloads=_cv([]),
        forms_detected=_cv(0),
        security_headers=_cv({}),
        estimated_complexity=_cv(20.0),
        overall_confidence=0.8,
        diagnostics={},
    )
    data.update(overrides)
    return WebsiteProfile(**data)


def test_enrich_adds_rest_and_graphql_fallbacks() -> None:
    plan = ExecutionPlan(
        strategy="Static HTML",
        strategy_id="static_html",
        fetch_engine="requests_http",
        cleaner="html_cleaner_v1",
        extractor="basic_extraction_engine",
        normalizer="normalization_engine_v1",
        validator="validation_engine_v1",
        storage="local_storage",
        estimated_duration_ms=1000,
        complexity=20,
        confidence=0.8,
        strategy_version="1.0.0",
        pipeline_version="1.0.0",
    )
    profile = _base_profile(
        discovered_apis=_cv(
            [ApiHint(url="https://example.com/api/v1/items", source="test", confidence=0.7)]
        ),
        discovered_graphql=_cv(
            [GraphqlHint(url="https://example.com/graphql", source="test", confidence=0.6)]
        ),
    )
    enriched = enrich_data_sources(plan, profile)
    assert enriched.preferred_data_source == "html"
    assert "rest_api" in enriched.fallback_sources
    assert "graphql" in enriched.fallback_sources
    assert "rest_api" in enriched.future_alternatives
    assert "graphql" in enriched.future_alternatives


def test_strategy_engine_populates_data_source_fields() -> None:
    engine = StrategyEngine()
    plan, ranking, _ = engine.decide(_base_profile())
    assert plan.preferred_data_source == "html"
    assert "html" in plan.fallback_sources
    assert plan.data_source_reasoning
    assert ranking.chosen_strategy_id
