"""Add plugin vars and cache fields.

Revision ID: a1b2c3d4e5f6
Revises: 6255554d5ddd
Create Date: 2026-01-04 14:41:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "6255554d5ddd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_column_map(table_name: str) -> dict[str, dict]:
    inspector = sa.inspect(op.get_bind())
    columns = inspector.get_columns(table_name)
    return {column["name"]: column for column in columns}


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in _get_column_map(table_name)


def _is_text_column(table_name: str, column_name: str) -> bool:
    column = _get_column_map(table_name).get(column_name)
    if column is None:
        return False
    return "TEXT" in str(column.get("type", "")).upper()


def upgrade() -> None:
    """Upgrade migration with idempotent checks."""

    if not _has_column("plugins", "def_vars"):
        op.add_column("plugins", sa.Column("def_vars", sa.JSON(), nullable=True, comment="plugin default vars"))

    if _has_column("plugins", "user_vars") and _is_text_column("plugins", "user_vars"):
        op.drop_column("plugins", "user_vars")
        op.add_column("plugins", sa.Column("user_vars", sa.JSON(), nullable=True, comment="plugin user vars"))
    elif not _has_column("plugins", "user_vars"):
        op.add_column("plugins", sa.Column("user_vars", sa.JSON(), nullable=True, comment="plugin user vars"))

    if not _has_column("plugins", "cached_locales"):
        op.add_column("plugins", sa.Column("cached_locales", sa.JSON(), nullable=True, comment="cached locales"))
    if not _has_column("plugins", "cached_voices"):
        op.add_column("plugins", sa.Column("cached_voices", sa.JSON(), nullable=True, comment="cached voices"))
    if not _has_column("plugins", "last_cache_time"):
        op.add_column("plugins", sa.Column("last_cache_time", sa.DateTime(), nullable=True, comment="last cache time"))


def downgrade() -> None:
    """Downgrade migration with idempotent checks."""

    if _has_column("plugins", "last_cache_time"):
        op.drop_column("plugins", "last_cache_time")
    if _has_column("plugins", "cached_voices"):
        op.drop_column("plugins", "cached_voices")
    if _has_column("plugins", "cached_locales"):
        op.drop_column("plugins", "cached_locales")

    if _has_column("plugins", "user_vars"):
        op.drop_column("plugins", "user_vars")
    if not _has_column("plugins", "user_vars"):
        op.add_column("plugins", sa.Column("user_vars", sa.Text(), nullable=True, server_default="{}", comment="user vars json"))

    if _has_column("plugins", "def_vars"):
        op.drop_column("plugins", "def_vars")
