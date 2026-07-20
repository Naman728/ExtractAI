"""WebsiteProfile domain model — intelligence output consumed by Strategy Engine later."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

from app.website_intelligence.types import (
    ApiHint,
    ConfidentValue,
    DiscoveredAsset,
    GraphqlHint,
    RedirectHop,
    SocialLink,
    TechnologyHit,
)

RenderingMode = Literal["static", "csr_heavy", "ssr", "hybrid", "unknown"]
BotProtection = Literal["none", "cloudflare", "captcha", "waf_unknown"]


class WebsiteProfile(BaseModel):
    """
    Complete intelligence profile for a target URL.

    Every substantive signal is a ConfidentValue (or includes confidence).
    This object is the Strategy Engine's primary input in later phases.
    """

    url: str
    final_url: str
    normalized_url: str
    profile_version: str
    probed_at: datetime

    # HTTP / transport
    status_code: ConfidentValue[int]
    content_type: ConfidentValue[str | None]
    charset: ConfidentValue[str | None]
    server: ConfidentValue[str | None]
    response_time_ms: ConfidentValue[float]
    estimated_page_size_bytes: ConfidentValue[int]
    redirect_chain: ConfidentValue[list[RedirectHop]]
    redirect_count: ConfidentValue[int]

    # Stack
    framework: ConfidentValue[str | None]
    cms: ConfidentValue[str | None]
    rendering_mode: ConfidentValue[RenderingMode]
    javascript_required: ConfidentValue[bool]
    technologies: ConfidentValue[list[TechnologyHit]]

    # Protection / access
    bot_protection: ConfidentValue[BotProtection]
    cloudflare: ConfidentValue[bool]
    captcha: ConfidentValue[bool]
    auth_required: ConfidentValue[bool]
    auth_signals: ConfidentValue[list[str]]
    cookies_present: ConfidentValue[bool]
    cookie_names: ConfidentValue[list[str]]

    # Locale / document
    language: ConfidentValue[str | None]
    canonical_url: ConfidentValue[str | None]
    favicon: ConfidentValue[str | None]
    title: ConfidentValue[str | None]

    # Structured metadata presence
    has_json_ld: ConfidentValue[bool]
    schema_org_types: ConfidentValue[list[str]]
    open_graph: ConfidentValue[dict[str, str]]
    twitter_cards: ConfidentValue[dict[str, str]]

    # Discovery summaries (full discovery lives in DiscoveryBundle)
    robots: ConfidentValue[dict[str, Any]]
    sitemap_urls: ConfidentValue[list[str]]
    rss_urls: ConfidentValue[list[str]]
    discovered_apis: ConfidentValue[list[ApiHint]]
    discovered_graphql: ConfidentValue[list[GraphqlHint]]
    discovered_assets: ConfidentValue[list[DiscoveredAsset]]
    social_links: ConfidentValue[list[SocialLink]]
    downloads: ConfidentValue[list[DiscoveredAsset]]
    forms_detected: ConfidentValue[int]
    security_headers: ConfidentValue[dict[str, str]]

    # Scoring
    estimated_complexity: ConfidentValue[float] = Field(
        description="0–100 complexity estimate for strategy costing"
    )
    overall_confidence: float = Field(ge=0.0, le=1.0)

    # Free-form diagnostics for operators
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class IntelligenceReport(BaseModel):
    """Human/strategy-facing summary derived from a WebsiteProfile."""

    website_type: str
    framework: str | None
    cms: str | None
    strategy_recommendation: str
    javascript_required: bool
    cloudflare: bool
    captcha: bool
    complexity_score: float
    suggested_fetch_strategy: str
    suggested_extractor: str
    warnings: list[str] = Field(default_factory=list)
    potential_issues: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    id: str
    profile: WebsiteProfile
    report: IntelligenceReport
    discovery: dict[str, Any]
