"""Add users.api_key field.

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-10 18:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6g7h8i9"
down_revision: Union[str, None] = "c3d4e5f6g7h8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(column.get("name") == column_name for column in inspector.get_columns(table_name))


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def upgrade() -> None:
    if not _has_column("users", "api_key"):
        op.add_column("users", sa.Column("api_key", sa.String(64), nullable=True, comment="user api key"))
    if not _index_exists("users", "ix_users_api_key"):
        op.create_index("ix_users_api_key", "users", ["api_key"], unique=True)


def downgrade() -> None:
    if _index_exists("users", "ix_users_api_key"):
        op.drop_index("ix_users_api_key", table_name="users")
    if _has_column("users", "api_key"):
        op.drop_column("users", "api_key")
