"""Discovery bundle — structured findings from the Discovery Engine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.website_intelligence.types import ApiHint, DiscoveredAsset, GraphqlHint


class DiscoveryBundle(BaseModel):
    """Output of Discovery Engine — feeds Strategy Engine later."""

    discovery_version: str
    robots_raw: str | None = None
    robots: dict[str, Any] = Field(default_factory=dict)
    sitemap_urls: list[str] = Field(default_factory=list)
    rss_urls: list[str] = Field(default_factory=list)
    json_ld_blocks: list[Any] = Field(default_factory=list)
    open_graph: dict[str, str] = Field(default_factory=dict)
    twitter_cards: dict[str, str] = Field(default_factory=dict)
    schema_org_types: list[str] = Field(default_factory=list)
    manifest_url: str | None = None
    favicon_url: str | None = None
    rest_candidates: list[ApiHint] = Field(default_factory=list)
    graphql_candidates: list[GraphqlHint] = Field(default_factory=list)
    json_endpoints: list[ApiHint] = Field(default_factory=list)
    downloads: list[DiscoveredAsset] = Field(default_factory=list)
    media: list[DiscoveredAsset] = Field(default_factory=list)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
