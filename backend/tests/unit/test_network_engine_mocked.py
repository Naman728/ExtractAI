"""Mocked Playwright / convention network discovery tests."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from app.network.engine import NetworkDiscoveryEngine
from app.network.types import CapturedRequestMeta
from app.website_intelligence.profile import WebsiteProfile
from app.website_intelligence.types import ConfidentValue


def _cv(value, confidence: float = 0.9):
    return ConfidentValue(value=value, confidence=confidence, evidence=["test"])


def _profile(**overrides) -> WebsiteProfile:
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
        response_time_ms=_cv(100.0),
        estimated_page_size_bytes=_cv(2000),
        redirect_chain=_cv([]),
        redirect_count=_cv(0),
        framework=_cv("nextjs"),
        cms=_cv(None),
        rendering_mode=_cv("hybrid"),
        javascript_required=_cv(True),
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
        robots=_cv({"available": True, "disallows": [], "allows": ["/"]}),
        sitemap_urls=_cv([]),
        rss_urls=_cv([]),
        discovered_apis=_cv([]),
        discovered_graphql=_cv([]),
        discovered_assets=_cv([]),
        social_links=_cv([]),
        downloads=_cv([]),
        forms_detected=_cv(0),
        security_headers=_cv({}),
        estimated_complexity=_cv(40.0),
        overall_confidence=0.75,
        diagnostics={},
    )
    data.update(overrides)
    return WebsiteProfile(**data)


def test_discovery_engine_with_mocked_playwright_and_conventions() -> None:
    engine = NetworkDiscoveryEngine()
    html = """
    <html><body>
    <script>fetch('/api/v1/products');</script>
    <script id="__NEXT_DATA__" type="application/json">
    {"buildId":"b1","page":"/"}
    </script>
    </body></html>
    """
    pw_metas = [
        CapturedRequestMeta(
            url="https://example.com/api/v1/products",
            method="GET",
            status_code=200,
            content_type="application/json",
            resource_type="fetch",
            source="playwright",
        ),
        CapturedRequestMeta(
            url="https://example.com/logo.png",
            method="GET",
            status_code=200,
            content_type="image/png",
            resource_type="image",
            source="playwright",
        ),
    ]
    convention_metas = [
        CapturedRequestMeta(
            url="https://example.com/wp-json/",
            method="GET",
            status_code=200,
            content_type="application/json",
            source="convention",
        )
    ]

    with (
        patch.object(engine, "_fetch_html", return_value=html),
        patch.object(engine._playwright, "capture", return_value=pw_metas),
        patch.object(engine._conventions, "probe", return_value=convention_metas),
        patch("app.utils.url.assert_public_url", side_effect=lambda u: u),
    ):
        profile = engine.discover(
            _profile(),
            website_profile_id="00000000-0000-0000-0000-000000000001",
            use_playwright=True,
        )

    assert profile.captured_request_count >= 2
    types = {e.endpoint_type for e in profile.endpoints}
    assert "rest" in types or "next_data" in types or "json_feed" in types
    assert profile.recommendation.preferred_data_source in {
        "html",
        "rest_api",
        "json_feed",
        "graphql",
    }
    assert "discovery_total_ms" in profile.timings
    assert profile.diagnostics.get("playwright_used") is True
