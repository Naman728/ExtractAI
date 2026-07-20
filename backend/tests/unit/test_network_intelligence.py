"""Unit tests for Network Intelligence classifier, profiler, ranker."""

from __future__ import annotations

from app.network.classifier import ApiClassifier
from app.network.html_analyzer import HtmlScriptAnalyzer
from app.network.profiler import ApiProfiler
from app.network.ranker import DataSourceRanker
from app.network.types import ApiEndpointProfile, CapturedRequestMeta


def test_classifier_wordpress_rest() -> None:
    clf = ApiClassifier()
    meta = CapturedRequestMeta(
        url="https://example.com/wp-json/wp/v2/posts",
        method="GET",
        status_code=200,
        content_type="application/json",
    )
    result = clf.classify(meta)
    assert result.endpoint_type == "rest"
    assert result.confidence >= 0.9
    assert "wordpress_rest" in result.evidence


def test_classifier_graphql() -> None:
    clf = ApiClassifier()
    meta = CapturedRequestMeta(url="https://shop.example/graphql", method="POST")
    result = clf.classify(meta)
    assert result.endpoint_type == "graphql"


def test_classifier_shopify_json() -> None:
    clf = ApiClassifier()
    meta = CapturedRequestMeta(
        url="https://store.myshopify.com/products.json",
        content_type="application/json",
        status_code=200,
    )
    result = clf.classify(meta)
    assert result.endpoint_type == "json_feed"
    assert "shopify_json" in result.evidence


def test_classifier_static_asset() -> None:
    clf = ApiClassifier()
    meta = CapturedRequestMeta(url="https://cdn.example.com/app.js", content_type="application/javascript")
    assert clf.classify(meta).endpoint_type == "static_asset"


def test_profiler_auth_on_401() -> None:
    clf = ApiClassifier()
    profiler = ApiProfiler()
    meta = CapturedRequestMeta(
        url="https://api.example.com/v1/items",
        status_code=401,
        content_type="application/json",
    )
    profile = profiler.profile(meta, clf.classify(meta))
    assert profile.authentication_required is True
    assert profile.estimated_value < 60


def test_html_analyzer_next_data() -> None:
    html = """
    <html><head>
    <script id="__NEXT_DATA__" type="application/json">
    {"buildId":"abc123","page":"/","props":{}}
    </script>
    </head><body></body></html>
    """
    metas, signals = HtmlScriptAnalyzer().analyze(html, "https://example.com/")
    assert any("__NEXT_DATA__" in s for s in signals["nextjs"])
    assert any("/_next/data/abc123/" in m.url for m in metas)


def test_ranker_prefers_json_feed() -> None:
    endpoints = [
        ApiEndpointProfile(
            url="https://example.com/feed.json",
            endpoint_type="json_feed",
            estimated_value=90,
            confidence=0.9,
            returns_json=True,
            status_code=200,
        ),
        ApiEndpointProfile(
            url="https://example.com/style.css",
            endpoint_type="static_asset",
            estimated_value=5,
            confidence=0.95,
        ),
    ]
    rec = DataSourceRanker().recommend(endpoints)
    assert rec.preferred_data_source == "json_feed"
    assert "html" in rec.fallback_sources


def test_ranker_defaults_to_html() -> None:
    rec = DataSourceRanker().recommend([])
    assert rec.preferred_data_source == "html"
