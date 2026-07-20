"""Persisted Strategy Engine analysis (standalone from jobs)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class StrategyAnalysis(Base):
    """One Strategy Engine decision run against a WebsiteProfile."""

    __tablename__ = "strategy_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    website_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("website_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chosen_strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    chosen_strategy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    decision_time_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    execution_plan: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    ranking: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    candidates: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    reasoning: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    pipeline_version: Mapped[str] = mapped_column(String(32), nullable=False)
    strategy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
