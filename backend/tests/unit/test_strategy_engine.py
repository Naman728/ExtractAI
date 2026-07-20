"""Unit tests for Strategy Engine scoring and selection."""

from datetime import UTC, datetime

from app.strategy.engine import StrategyEngine
from app.strategy.registry import StrategyRegistry
from app.strategy.strategies.dynamic_browser import DynamicBrowserStrategy
from app.strategy.strategies.json_ld import JSONLDStrategy
from app.strategy.strategies.metadata import MetadataStrategy
from app.strategy.strategies.static_html import StaticHTMLStrategy
from app.website_intelligence.profile import WebsiteProfile
from app.website_intelligence.types import ConfidentValue


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


def test_registry_discovers_enabled_strategies() -> None:
    registry = StrategyRegistry()
    registry.discover()
    enabled_ids = {s.id() for s in registry.enabled()}
    assert "static_html" in enabled_ids
    assert "dynamic_browser" in enabled_ids
    assert "json_ld" in enabled_ids
    assert "metadata" in enabled_ids
    assert "browser_agent" in enabled_ids
    assert "llm" not in enabled_ids  # reserved disabled


def test_static_wins_for_static_page() -> None:
    registry = StrategyRegistry()
    for cls in (StaticHTMLStrategy, DynamicBrowserStrategy, JSONLDStrategy, MetadataStrategy):
        registry.register(cls())
    engine = StrategyEngine(registry=registry)
    plan, ranking, _ = engine.decide(_base_profile())
    assert ranking.chosen_strategy_id == "static_html"
    assert plan.fetch_engine == "requests_http"


def test_dynamic_wins_for_csr() -> None:
    registry = StrategyRegistry()
    for cls in (StaticHTMLStrategy, DynamicBrowserStrategy, JSONLDStrategy, MetadataStrategy):
        registry.register(cls())
    engine = StrategyEngine(registry=registry)
    profile = _base_profile(
        rendering_mode=_cv("csr_heavy"),
        javascript_required=_cv(True),
        estimated_complexity=_cv(75.0),
    )
    plan, ranking, _ = engine.decide(profile)
    assert ranking.chosen_strategy_id == "dynamic_browser"
    assert plan.fetch_engine == "playwright"


def test_json_ld_wins_when_rich_schema() -> None:
    registry = StrategyRegistry()
    for cls in (StaticHTMLStrategy, DynamicBrowserStrategy, JSONLDStrategy, MetadataStrategy):
        registry.register(cls())
    engine = StrategyEngine(registry=registry)
    profile = _base_profile(
        has_json_ld=_cv(True),
        schema_org_types=_cv(["Product", "Offer", "Organization"]),
        open_graph=_cv({"og:title": "x"}),
    )
    plan, ranking, _ = engine.decide(profile)
    assert ranking.chosen_strategy_id == "json_ld"
    assert plan.extractor == "json_ld_parser"
