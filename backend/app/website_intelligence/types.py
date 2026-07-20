"""Shared typed field with confidence for intelligence signals."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ConfidentValue(BaseModel, Generic[T]):
    """Any profile field wrapped with an explicit confidence score (0.0–1.0)."""

    value: T
    confidence: float = Field(ge=0.0, le=1.0, description="Detector confidence 0–1")
    evidence: list[str] = Field(default_factory=list)


class TechnologyHit(BaseModel):
    name: str
    category: str  # framework | cms | server | library | hosting | other
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class RedirectHop(BaseModel):
    url: str
    status_code: int


class ApiHint(BaseModel):
    url: str
    method: str = "GET"
    source: str
    confidence: float = Field(ge=0.0, le=1.0)
    content_type: str | None = None


class GraphqlHint(BaseModel):
    url: str
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class DiscoveredAsset(BaseModel):
    url: str
    kind: str  # favicon | manifest | download | media | feed | sitemap | other
    confidence: float = Field(ge=0.0, le=1.0)


class SocialLink(BaseModel):
    platform: str
    url: str
    confidence: float = Field(ge=0.0, le=1.0)
