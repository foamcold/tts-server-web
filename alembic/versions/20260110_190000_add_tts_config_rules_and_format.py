"""Add apply_rules and audio_format fields to tts_configs.

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-10 19:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6g7h8i9j0"
down_revision: Union[str, None] = "d4e5f6g7h8i9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    if not _has_column("tts_configs", "apply_rules"):
        op.add_column(
            "tts_configs",
            sa.Column("apply_rules", sa.Boolean(), nullable=False, server_default="1", comment="apply replace rules"),
        )

    if not _has_column("tts_configs", "audio_format"):
        op.add_column(
            "tts_configs",
            sa.Column("audio_format", sa.String(10), nullable=False, server_default="mp3", comment="audio format"),
        )


def downgrade() -> None:
    if _has_column("tts_configs", "audio_format"):
        op.drop_column("tts_configs", "audio_format")
    if _has_column("tts_configs", "apply_rules"):
        op.drop_column("tts_configs", "apply_rules")
