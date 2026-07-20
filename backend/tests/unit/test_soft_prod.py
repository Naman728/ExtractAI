"""Soft-prod cascade / rate-limit helpers."""

from types import SimpleNamespace

from app.engines.pipeline import ExtractionPipeline


def test_fetch_needs_browser_retry_on_403() -> None:
    fetched = SimpleNamespace(error_code="HTTP_403", status_code=403, html="")
    assert ExtractionPipeline._fetch_needs_browser_retry(fetched) is True


def test_fetch_needs_browser_retry_ok_html() -> None:
    fetched = SimpleNamespace(
        error_code=None,
        status_code=200,
        html="<html><body><h1>Hello Unsplash</h1></body></html>",
    )
    assert ExtractionPipeline._fetch_needs_browser_retry(fetched) is False


def test_unsplash_profile_forces_playwright() -> None:
    from app.scrapers.site_profiles import resolve_site_profile

    p = resolve_site_profile("https://unsplash.com/")
    assert p.id == "unsplash"
    assert p.force_engine == "playwright"
