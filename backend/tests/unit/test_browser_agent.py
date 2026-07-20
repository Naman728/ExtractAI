"""Tests for officials parsing and browser_agent strategy gating."""

from datetime import UTC, datetime

from app.scrapers.workflows.officials import classify_level, parse_officials_from_text
from app.scrapers.workflows.registry import resolve_workflow
from app.strategy.strategies.browser_agent import BrowserAgentStrategy
from app.website_intelligence.profile import WebsiteProfile
from app.website_intelligence.types import ConfidentValue


def _cv(value, confidence: float = 0.9):
    return ConfidentValue(value=value, confidence=confidence, evidence=["test"])


def _profile(**overrides) -> WebsiteProfile:
    data = dict(
        url="https://www.ballotready.org/",
        final_url="https://www.ballotready.org/",
        normalized_url="https://www.ballotready.org/",
        profile_version="1.0.0",
        probed_at=datetime.now(UTC),
        status_code=_cv(200),
        content_type=_cv("text/html"),
        charset=_cv("utf-8"),
        server=_cv("Vercel"),
        response_time_ms=_cv(100.0),
        estimated_page_size_bytes=_cv(1000),
        redirect_chain=_cv([]),
        redirect_count=_cv(0),
        framework=_cv("nextjs"),
        cms=_cv(None),
        rendering_mode=_cv("ssr"),
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
        canonical_url=_cv("https://www.ballotready.org/"),
        favicon=_cv(None),
        title=_cv("BallotReady"),
        has_json_ld=_cv(False),
        schema_org_types=_cv([]),
        open_graph=_cv({}),
        twitter_cards=_cv({}),
        robots=_cv({}),
        sitemap_urls=_cv([]),
        rss_urls=_cv([]),
        discovered_apis=_cv([]),
        discovered_graphql=_cv([]),
        discovered_assets=_cv([]),
        downloads=_cv([]),
        social_links=_cv([]),
        forms_detected=_cv(1),
        estimated_complexity=_cv(40.0),
        overall_confidence=0.8,
        security_headers=_cv({}),
        diagnostics={},
    )
    data.update(overrides)
    return WebsiteProfile(**data)


def test_classify_level():
    assert classify_level("U.S. Senate - Georgia") == "federal"
    assert classify_level("Georgia Governor") == "state"
    assert classify_level("Dougherty County Sheriff") == "local"


def test_parse_officials_from_text():
    body = """
Your civic center
English
All
Federal
State
Local
Jon Ossoff
U.S. Senate - Georgia
Brian Kemp
Georgia Governor
Terron Hayes
Dougherty County Sheriff

Please select an office holder from the menu to get started
"""
    parsed = parse_officials_from_text(body)
    assert parsed["total"] == 3
    assert parsed["counts"]["federal"] == 1
    assert parsed["counts"]["state"] == 1
    assert parsed["counts"]["local"] == 1
    assert parsed["federal"][0]["name"] == "Jon Ossoff"


def test_resolve_ballotready_workflow():
    wf = resolve_workflow(
        "https://www.ballotready.org/",
        {"address": "Albany, GA 31705"},
    )
    assert wf.id() == "ballotready_officials"


def test_resolve_general_browser_for_query():
    wf = resolve_workflow("https://example.com/search", {"query": "headphones"})
    assert wf.id() == "general_browser"


def test_resolve_general_browser_for_topics():
    wf = resolve_workflow(
        "https://en.wikipedia.org/",
        {"topics": '["Artificial intelligence", "FastAPI"]', "query": "Artificial intelligence"},
    )
    assert wf.id() == "general_browser"


def test_normalize_topics_json():
    from app.scrapers.workflows.input_normalize import all_search_targets, normalize_agent_inputs

    n = normalize_agent_inputs(
        {"topics": '["Artificial intelligence", "Machine learning", "FastAPI"]'}
    )
    assert n["query"] == "Artificial intelligence"
    targets = all_search_targets(n)
    assert targets[0] == "Artificial intelligence"
    assert "FastAPI" in targets


def test_browser_agent_requires_inputs():
    strategy = BrowserAgentStrategy()
    bare = _profile()
    assert strategy.can_handle(bare) is False

    with_inputs = _profile(diagnostics={"job_inputs": {"address": "Albany, GA"}})
    assert strategy.can_handle(with_inputs) is True
    plan = strategy.build_execution_plan(with_inputs)
    assert plan.fetch_engine == "browser_agent"
    assert plan.options["inputs"]["address"] == "Albany, GA"
