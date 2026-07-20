"""Unit tests for technology detection and robots parsing."""

from app.discovery.robots import parse_robots
from app.website_intelligence.detectors.technology import detect_technologies
from app.website_intelligence.report import build_intelligence_report, estimate_complexity
from app.website_intelligence.engine import WebsiteIntelligenceEngine


def test_detect_nextjs() -> None:
    html = '<script id="__NEXT_DATA__" type="application/json">{}</script><div id="__next"></div>'
    fw, cms, techs = detect_technologies(html, {}, {})
    assert fw.value == "nextjs"
    assert fw.confidence >= 0.9
    assert any(t.name == "react" for t in techs.value)


def test_detect_wordpress() -> None:
    html = '<link rel="stylesheet" href="/wp-content/themes/x/style.css">'
    fw, cms, techs = detect_technologies(html, {}, {})
    assert cms.value == "wordpress"
    assert cms.confidence >= 0.9


def test_parse_robots() -> None:
    text = """
User-agent: *
Disallow: /admin
Allow: /
Sitemap: https://example.com/sitemap.xml
"""
    parsed = parse_robots(text)
    assert parsed["available"] is True
    assert "https://example.com/sitemap.xml" in parsed["sitemaps"]
    assert "/admin" in parsed["disallows"]


def test_complexity_increases_with_js() -> None:
    low, _ = estimate_complexity({"js_required": False, "rendering_mode": "static", "tech_count": 1})
    high, _ = estimate_complexity(
        {"js_required": True, "cloudflare": True, "captcha": True, "rendering_mode": "csr_heavy", "tech_count": 5}
    )
    assert high > low


def test_report_suggests_playwright_for_csr() -> None:
    engine = WebsiteIntelligenceEngine()
    # Use internal error profile path style via building from a static analyze of unreachable
    # Instead construct via detectors path: analyze example.com may network — skip if offline.
    # Unit-level: build report from a minimal profile using engine._error_profile then mutate
    profile = engine._error_profile("https://example.com", "test", 10.0)
    profile.javascript_required.value = True
    profile.javascript_required.confidence = 0.9
    profile.rendering_mode.value = "csr_heavy"
    profile.overall_confidence = 0.7
    profile.estimated_complexity.value = 70
    report = build_intelligence_report(profile)
    assert report.suggested_fetch_strategy == "playwright_rendering"
