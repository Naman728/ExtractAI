"""Extend website_profiles for standalone intelligence analyzes.

Revision ID: 002_intelligence
Revises: 001_initial
Create Date: 2026-07-16
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_intelligence"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("website_profiles", "job_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)

    op.add_column("website_profiles", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "website_profiles", sa.Column("guest_session_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column(
        "website_profiles",
        sa.Column("url", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "website_profiles",
        sa.Column("normalized_url", sa.Text(), nullable=False, server_default=""),
    )
    op.add_column(
        "website_profiles",
        sa.Column("report", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "website_profiles",
        sa.Column("discovery", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column("website_profiles", sa.Column("discovery_version", sa.String(length=32), nullable=True))
    op.add_column(
        "website_profiles",
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("website_profiles", sa.Column("overall_confidence", sa.Float(), nullable=True))
    op.add_column(
        "website_profiles",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "website_profiles",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_foreign_key(
        "fk_website_profiles_user_id",
        "website_profiles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_website_profiles_guest_session_id",
        "website_profiles",
        "guest_sessions",
        ["guest_session_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_website_profiles_user_id", "website_profiles", ["user_id"])
    op.create_index("ix_website_profiles_guest_session_id", "website_profiles", ["guest_session_id"])
    op.create_index("ix_website_profiles_normalized_url", "website_profiles", ["normalized_url"])

    # Drop server defaults used only for backfill
    op.alter_column("website_profiles", "url", server_default=None)
    op.alter_column("website_profiles", "normalized_url", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_website_profiles_normalized_url", table_name="website_profiles")
    op.drop_index("ix_website_profiles_guest_session_id", table_name="website_profiles")
    op.drop_index("ix_website_profiles_user_id", table_name="website_profiles")
    op.drop_constraint("fk_website_profiles_guest_session_id", "website_profiles", type_="foreignkey")
    op.drop_constraint("fk_website_profiles_user_id", "website_profiles", type_="foreignkey")
    for col in (
        "updated_at",
        "created_at",
        "overall_confidence",
        "schema_version",
        "discovery_version",
        "discovery",
        "report",
        "normalized_url",
        "url",
        "guest_session_id",
        "user_id",
    ):
        op.drop_column("website_profiles", col)
    op.alter_column("website_profiles", "job_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
