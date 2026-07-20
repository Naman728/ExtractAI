"""Network Intelligence domain types — discovery only (no API extraction)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EndpointType = Literal[
    "rest",
    "graphql",
    "json_feed",
    "xml_feed",
    "static_asset",
    "media",
    "websocket",
    "sse",
    "next_data",
    "unknown",
]

DataSourceKind = Literal["html", "rest_api", "graphql", "json_feed", "xml_feed"]


class CapturedRequestMeta(BaseModel):
    """Network request metadata (bodies not stored by default)."""

    url: str
    method: str = "GET"
    status_code: int | None = None
    content_type: str | None = None
    resource_type: str | None = None
    duration_ms: float | None = None
    transfer_size: int | None = None
    source: str = "probe"  # probe | playwright | html_script | convention
    request_headers_redacted: dict[str, str] = Field(default_factory=dict)
    response_headers_redacted: dict[str, str] = Field(default_factory=dict)


class EndpointClassification(BaseModel):
    endpoint_type: EndpointType
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class ApiEndpointProfile(BaseModel):
    """Profile for a single discovered public endpoint."""

    url: str
    method: str = "GET"
    endpoint_type: EndpointType = "unknown"
    parameters: list[str] = Field(default_factory=list)
    content_type: str | None = None
    authentication_required: bool = False
    returns_json: bool = False
    returns_html: bool = False
    returns_xml: bool = False
    rate_limit_indicators: list[str] = Field(default_factory=list)
    pagination_support: bool = False
    estimated_value: float = Field(ge=0.0, le=100.0, description="Usefulness 0–100")
    confidence: float = Field(ge=0.0, le=1.0)
    framework_hint: str | None = None
    classification_evidence: list[str] = Field(default_factory=list)
    status_code: int | None = None
    source: str = "discovery"


class DataSourceRecommendation(BaseModel):
    preferred_data_source: DataSourceKind
    fallback_sources: list[DataSourceKind] = Field(default_factory=list)
    estimated_speed: str  # fast | medium | slow
    estimated_reliability: float = Field(ge=0.0, le=1.0)
    reasoning: list[str] = Field(default_factory=list)
    top_endpoints: list[str] = Field(default_factory=list)


class NetworkProfile(BaseModel):
    """Complete network intelligence output for a site."""

    website_profile_id: str
    strategy_analysis_id: str | None = None
    final_url: str
    discovered_at: datetime
    discovery_version: str
    endpoints: list[ApiEndpointProfile] = Field(default_factory=list)
    rest_endpoints: list[ApiEndpointProfile] = Field(default_factory=list)
    graphql_endpoints: list[ApiEndpointProfile] = Field(default_factory=list)
    json_feeds: list[ApiEndpointProfile] = Field(default_factory=list)
    xml_feeds: list[ApiEndpointProfile] = Field(default_factory=list)
    xhr_candidates: list[ApiEndpointProfile] = Field(default_factory=list)
    nextjs_signals: list[str] = Field(default_factory=list)
    shopify_signals: list[str] = Field(default_factory=list)
    wordpress_signals: list[str] = Field(default_factory=list)
    websocket_detected: bool = False
    sse_detected: bool = False
    recommendation: DataSourceRecommendation
    timings: dict[str, float] = Field(default_factory=dict)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    captured_request_count: int = 0


class NetworkAnalyzeRequest(BaseModel):
    website_profile_id: str
    strategy_analysis_id: str | None = None


class NetworkAnalyzeResponse(BaseModel):
    id: str
    network_profile: NetworkProfile
    execution_recommendation: DataSourceRecommendation
    metrics: dict[str, Any] = Field(default_factory=dict)
