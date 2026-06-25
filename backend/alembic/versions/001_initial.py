"""Initial tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "prompt_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "prompt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("labels", postgresql.JSON, default=[]),
        sa.Column("is_active", sa.Boolean, default=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "golden_examples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "prompt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("input_text", sa.Text, nullable=False),
        sa.Column("expected_output", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "eval_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "prompt_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_versions.id"),
            nullable=False,
        ),
        sa.Column("locale", sa.String(10), nullable=False),
        sa.Column("input_text", sa.Text, nullable=False),
        sa.Column("llm_output", sa.Text, nullable=False),
        sa.Column("quality_score", sa.Float, nullable=False),
        sa.Column("quality_reasoning", sa.Text, nullable=False),
        sa.Column("hallucination_score", sa.Float, nullable=False),
        sa.Column("hallucination_reasoning", sa.Text, nullable=False),
        sa.Column("moderation_passed", sa.Boolean, nullable=False),
        sa.Column("moderation_reasoning", sa.Text, nullable=False),
        sa.Column("world_readiness_passed", sa.Boolean, nullable=False),
        sa.Column("world_readiness_details", postgresql.JSON, default={}),
        sa.Column("overall_passed", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )

    op.create_table(
        "ci_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "prompt_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompts.id"),
            nullable=False,
        ),
        sa.Column(
            "candidate_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "baseline_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("prompt_versions.id"),
            nullable=True,
        ),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("regressions", postgresql.JSON, default=[]),
        sa.Column("details", postgresql.JSON, default={}),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ci_runs")
    op.drop_table("eval_runs")
    op.drop_table("golden_examples")
    op.drop_table("prompt_versions")
    op.drop_table("prompts")
