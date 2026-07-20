"""Per-host scrape presets for hard / modern public sites."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote_plus, urlparse


@dataclass(frozen=True)
class SiteProfile:
    """Hints that make extraction more reliable for a given host family."""

    id: str
    hosts: tuple[str, ...]
    # Preferred fetch cascade (first success with useful content wins)
    engines: tuple[str, ...] = ("playwright", "requests_http")
    force_engine: str | None = "playwright"
    follow_pagination: bool = True
    max_pages: int = 3
    scroll_rounds: int = 4
    scroll_pause_ms: int = 600
    wait_ms: int = 1500
    timeout_ms: int = 45_000
    # Optional search URL template; {q} = url-encoded query
    search_url: str | None = None
    notes: str = ""
    extra_options: dict[str, Any] = field(default_factory=dict)


_PROFILES: tuple[SiteProfile, ...] = (
    SiteProfile(
        id="amazon",
        hosts=("amazon.com", "www.amazon.com", "smile.amazon.com"),
        engines=("requests_http", "playwright"),
        force_engine="requests_http",
        follow_pagination=True,
        max_pages=3,
        scroll_rounds=2,
        search_url="https://www.amazon.com/s?k={q}",
        notes="SERP HTML is often server-rendered; Playwright as fallback.",
    ),
    SiteProfile(
        id="walmart",
        hosts=("walmart.com", "www.walmart.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        follow_pagination=True,
        max_pages=2,
        scroll_rounds=5,
        search_url="https://www.walmart.com/search?q={q}",
        notes="Heavy bot protection — may still CAPTCHA.",
    ),
    SiteProfile(
        id="nike",
        hosts=("nike.com", "www.nike.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        follow_pagination=False,
        max_pages=1,
        scroll_rounds=6,
        search_url="https://www.nike.com/w?q={q}",
        notes="CSR product grids need scroll.",
    ),
    SiteProfile(
        id="zara",
        hosts=("zara.com", "www.zara.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        scroll_rounds=5,
        search_url="https://www.zara.com/us/en/search?searchTerm={q}",
        notes="WAF-heavy; Playwright + browser UA is best effort.",
    ),
    SiteProfile(
        id="booking",
        hosts=("booking.com", "www.booking.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        scroll_rounds=3,
        search_url="https://www.booking.com/searchresults.html?ss={q}",
        notes="Homepage shell loads; full hotel search needs dates (pass in query).",
    ),
    SiteProfile(
        id="airbnb",
        hosts=("airbnb.com", "www.airbnb.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        follow_pagination=False,
        scroll_rounds=8,
        scroll_pause_ms=800,
        search_url="https://www.airbnb.com/s/{q}/homes",
        notes="Infinite-scroll style; scroll rounds load more cards.",
    ),
    SiteProfile(
        id="expedia",
        hosts=("expedia.com", "www.expedia.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        scroll_rounds=2,
        search_url="https://www.expedia.com/Hotel-Search?destination={q}",
        notes="Frequently CAPTCHA-gated.",
    ),
    SiteProfile(
        id="tripadvisor",
        hosts=("tripadvisor.com", "www.tripadvisor.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        scroll_rounds=4,
        search_url="https://www.tripadvisor.com/Search?q={q}",
        notes="Often 403 on datacenter IPs.",
    ),
    SiteProfile(
        id="imdb",
        hosts=("imdb.com", "www.imdb.com"),
        engines=("playwright", "requests_http", "browser_agent"),
        force_engine="playwright",
        follow_pagination=False,
        scroll_rounds=2,
        search_url="https://www.imdb.com/find/?q={q}",
        notes="Prefer find URL; agent fallback with inputs.query.",
    ),
    SiteProfile(
        id="figma",
        hosts=("figma.com", "www.figma.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        follow_pagination=False,
        scroll_rounds=10,
        scroll_pause_ms=700,
        search_url="https://www.figma.com/community/search?resource_type=mixed&sort_by=relevancy&query={q}",
        notes="CloudFront/WAF may block; scroll for community cards.",
    ),
    SiteProfile(
        id="unsplash",
        hosts=("unsplash.com", "www.unsplash.com"),
        engines=("playwright", "requests_http"),
        force_engine="playwright",
        follow_pagination=False,
        max_pages=1,
        scroll_rounds=6,
        scroll_pause_ms=700,
        wait_ms=1200,
        search_url="https://unsplash.com/s/photos/{q}",
        notes="Blocks bare HTTP often — prefer Playwright + scroll for image grid.",
    ),
    SiteProfile(
        id="books_toscrape",
        hosts=("books.toscrape.com",),
        engines=("requests_http",),
        force_engine="requests_http",
        follow_pagination=True,
        max_pages=5,
        scroll_rounds=0,
        notes="Ideal catalog demo.",
    ),
)

_DEFAULT = SiteProfile(
    id="generic",
    hosts=(),
    engines=("playwright", "requests_http"),
    force_engine=None,
    follow_pagination=True,
    max_pages=3,
    scroll_rounds=3,
    wait_ms=800,
    notes="Generic modern-site defaults; cascade retries Playwright on 403.",
)


def list_profiles() -> list[SiteProfile]:
    return list(_PROFILES)


def resolve_site_profile(url: str) -> SiteProfile:
    host = (urlparse(url).hostname or "").lower()
    if host.startswith("www."):
        bare = host[4:]
    else:
        bare = host
    for profile in _PROFILES:
        for h in profile.hosts:
            h_l = h.lower()
            if host == h_l or bare == h_l or host.endswith("." + h_l) or bare.endswith("." + h_l):
                return profile
    return _DEFAULT


def build_search_url(profile: SiteProfile, query: str) -> str | None:
    if not profile.search_url or not query.strip():
        return None
    return profile.search_url.format(q=quote_plus(query.strip()))


def profile_to_crawl(profile: SiteProfile, *, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    crawl: dict[str, Any] = {
        "follow_pagination": profile.follow_pagination,
        "max_pages": profile.max_pages,
        "force_engine": profile.force_engine,
        "scroll_rounds": profile.scroll_rounds,
        "scroll_pause_ms": profile.scroll_pause_ms,
        "wait_ms": profile.wait_ms,
        "timeout_ms": profile.timeout_ms,
        "browser_headers": True,
        "site_profile": profile.id,
        **(profile.extra_options or {}),
    }
    if overrides:
        crawl.update({k: v for k, v in overrides.items() if v is not None})
    return crawl
