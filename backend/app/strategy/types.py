"""Strategy Engine domain types — scoring and execution plans (no extraction)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

DataSourceKind = Literal["html", "rest_api", "graphql", "json_feed", "xml_feed"]


class StrategyScore(BaseModel):
    """Scored evaluation of a single strategy against a WebsiteProfile."""

    strategy_id: str
    strategy_name: str
    suitability_score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    estimated_runtime_ms: int = Field(ge=0)
    estimated_cost: float = Field(ge=0.0, description="Relative cost units 0–100")
    reason: str
    warnings: list[str] = Field(default_factory=list)
    advantages: list[str] = Field(default_factory=list)
    disadvantages: list[str] = Field(default_factory=list)
    can_handle: bool = True
    reject_reason: str | None = None
    score_breakdown: dict[str, float] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """
    Declarative plan for a future extraction pipeline.

    Consumed later by the pipeline conductor — this phase only produces the plan.
    """

    strategy: str
    strategy_id: str
    fetch_engine: str
    cleaner: str
    extractor: str
    normalizer: str
    validator: str
    storage: str
    estimated_duration_ms: int
    complexity: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    fallback_strategy: str | None = None
    future_alternatives: list[str] = Field(default_factory=list)
    pipeline_stages: list[str] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)
    strategy_version: str
    pipeline_version: str
    # Network Intelligence — preferred execution sources (discovery ranks; HTML still extracts)
    preferred_data_source: DataSourceKind = "html"
    fallback_sources: list[DataSourceKind] = Field(default_factory=lambda: ["html"])
    estimated_speed: str = "medium"
    estimated_reliability: float = Field(default=0.7, ge=0.0, le=1.0)
    data_source_reasoning: list[str] = Field(default_factory=list)


class StrategyRanking(BaseModel):
    """Ordered list of candidate evaluations."""

    scores: list[StrategyScore]
    chosen_strategy_id: str
    chosen_strategy_name: str
    decision_time_ms: float
    decided_at: datetime


class StrategyAnalyzeRequest(BaseModel):
    website_profile_id: str


class StrategyAnalyzeResponse(BaseModel):
    id: str
    website_profile_id: str
    execution_plan: ExecutionPlan
    ranking: StrategyRanking
    reasoning: list[str]
    warnings: list[str]
    confidence: float
    pipeline_version: str
    strategy_version: str
