"""Extend strategy_decisions for profile-linked candidate rows.

Revision ID: 003_strategy
Revises: 002_intelligence
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_strategy"
down_revision: Union[str, None] = "002_intelligence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "strategy_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "website_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("website_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chosen_strategy", sa.String(64), nullable=False),
        sa.Column("chosen_strategy_id", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("decision_time_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("execution_plan", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("ranking", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("candidates", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("reasoning", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("warnings", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("pipeline_version", sa.String(32), nullable=False),
        sa.Column("strategy_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_strategy_analyses_website_profile_id", "strategy_analyses", ["website_profile_id"])
    op.create_index("ix_strategy_analyses_chosen_strategy_id", "strategy_analyses", ["chosen_strategy_id"])

    op.alter_column(
        "strategy_decisions",
        "job_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=True,
    )
    op.add_column(
        "strategy_decisions",
        sa.Column("strategy_analysis_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "strategy_decisions",
        sa.Column("website_profile_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "strategy_decisions",
        sa.Column("execution_plan", postgresql.JSONB(), nullable=True),
    )
    op.create_foreign_key(
        "fk_strategy_decisions_analysis",
        "strategy_decisions",
        "strategy_analyses",
        ["strategy_analysis_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_strategy_decisions_profile",
        "strategy_decisions",
        "website_profiles",
        ["website_profile_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_strategy_decisions_analysis_id", "strategy_decisions", ["strategy_analysis_id"])


def downgrade() -> None:
    op.drop_index("ix_strategy_decisions_analysis_id", table_name="strategy_decisions")
    op.drop_constraint("fk_strategy_decisions_profile", "strategy_decisions", type_="foreignkey")
    op.drop_constraint("fk_strategy_decisions_analysis", "strategy_decisions", type_="foreignkey")
    op.drop_column("strategy_decisions", "execution_plan")
    op.drop_column("strategy_decisions", "website_profile_id")
    op.drop_column("strategy_decisions", "strategy_analysis_id")
    op.alter_column(
        "strategy_decisions",
        "job_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.drop_index("ix_strategy_analyses_chosen_strategy_id", table_name="strategy_analyses")
    op.drop_index("ix_strategy_analyses_website_profile_id", table_name="strategy_analyses")
    op.drop_table("strategy_analyses")
