"""Network Intelligence schema — profiles, endpoints, execution sources.

Revision ID: 004_network
Revises: 003_strategy
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_network"
down_revision: Union[str, None] = "003_strategy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "network_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "website_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("website_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "strategy_analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("strategy_analyses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("final_url", sa.Text(), nullable=False),
        sa.Column("discovery_version", sa.String(32), nullable=False),
        sa.Column("profile", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "recommendation",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("timings", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "diagnostics",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("endpoints_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("useful_endpoints", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_endpoints", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("websocket_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sse_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("discovery_time_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("classification_time_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_network_profiles_website_profile_id", "network_profiles", ["website_profile_id"])
    op.create_index(
        "ix_network_profiles_strategy_analysis_id",
        "network_profiles",
        ["strategy_analysis_id"],
    )

    op.create_table(
        "api_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "network_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("network_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("method", sa.String(16), nullable=False, server_default="GET"),
        sa.Column("endpoint_type", sa.String(32), nullable=False, server_default="unknown"),
        sa.Column("content_type", sa.String(255), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column(
            "authentication_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("returns_json", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("returns_html", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("returns_xml", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "pagination_support",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("estimated_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("framework_hint", sa.String(64), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="discovery"),
        sa.Column(
            "parameters",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "rate_limit_indicators",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "classification_evidence",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "profile_json",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_api_endpoints_network_profile_id", "api_endpoints", ["network_profile_id"])
    op.create_index("ix_api_endpoints_endpoint_type", "api_endpoints", ["endpoint_type"])

    op.create_table(
        "execution_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "network_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("network_profiles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "strategy_analysis_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("strategy_analyses.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("preferred_data_source", sa.String(32), nullable=False, server_default="html"),
        sa.Column(
            "fallback_sources",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("estimated_speed", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("estimated_reliability", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column(
            "reasoning",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "top_endpoints",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "is_applied_to_plan",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_execution_sources_network_profile_id",
        "execution_sources",
        ["network_profile_id"],
    )
    op.create_index(
        "ix_execution_sources_strategy_analysis_id",
        "execution_sources",
        ["strategy_analysis_id"],
    )

    # Allow standalone network analysis without a job
    op.alter_column("network_requests", "job_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.add_column(
        "network_requests",
        sa.Column(
            "network_profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("network_profiles.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_network_requests_network_profile_id",
        "network_requests",
        ["network_profile_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_network_requests_network_profile_id", table_name="network_requests")
    op.drop_column("network_requests", "network_profile_id")
    op.alter_column(
        "network_requests",
        "job_id",
        existing_type=postgresql.UUID(as_uuid=True),
        nullable=False,
    )

    op.drop_index("ix_execution_sources_strategy_analysis_id", table_name="execution_sources")
    op.drop_index("ix_execution_sources_network_profile_id", table_name="execution_sources")
    op.drop_table("execution_sources")

    op.drop_index("ix_api_endpoints_endpoint_type", table_name="api_endpoints")
    op.drop_index("ix_api_endpoints_network_profile_id", table_name="api_endpoints")
    op.drop_table("api_endpoints")

    op.drop_index("ix_network_profiles_strategy_analysis_id", table_name="network_profiles")
    op.drop_index("ix_network_profiles_website_profile_id", table_name="network_profiles")
    op.drop_table("network_profiles")
