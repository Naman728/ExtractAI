"""Website understanding profile — top-level AI output."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.ai.models.entities import EntityBundle
from app.ai.models.knowledge_graph import KnowledgeGraph


class WebsiteCategory(str, Enum):
    GOVERNMENT = "Government"
    ECOMMERCE = "E-commerce"
    UNIVERSITY = "University"
    HEALTHCARE = "Healthcare"
    NEWS = "News"
    BLOG = "Blog"
    CORPORATE = "Corporate"
    SAAS = "SaaS"
    DOCUMENTATION = "Documentation"
    MARKETPLACE = "Marketplace"
    PORTFOLIO = "Portfolio"
    NONPROFIT = "Nonprofit"
    FINANCIAL = "Financial"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    DEVELOPER = "Developer"
    OTHER = "Other"


class BusinessProfile(BaseModel):
    organization_name: str | None = None
    description: str | None = None
    industry: str | None = None
    main_products: list[str] = Field(default_factory=list)
    main_services: list[str] = Field(default_factory=list)
    target_audience: str | None = None
    value_proposition: str | None = None


class AIObservability(BaseModel):
    provider: str
    model: str | None = None
    latency_ms: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    prompt_version: str = "1.0.0"
    cache_hit: bool = False
    chunked: bool = False
    error: str | None = None


class WebsiteUnderstanding(BaseModel):
    """Full AI Understanding Engine output."""

    summary: str = ""
    category: WebsiteCategory = WebsiteCategory.OTHER
    category_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    business_profile: BusinessProfile = Field(default_factory=BusinessProfile)
    entities: EntityBundle = Field(default_factory=EntityBundle)
    knowledge_graph: KnowledgeGraph = Field(default_factory=KnowledgeGraph)
    semantic_tags: list[str] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    observability: AIObservability = Field(
        default_factory=lambda: AIObservability(provider="none")
    )
    content_hash: str | None = None
    understanding_version: str = "1.0.0"
    status: str = "completed"  # pending | running | completed | failed | skipped
    extras: dict[str, Any] = Field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")
