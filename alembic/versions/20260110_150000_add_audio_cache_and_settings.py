"""Add audio cache and system settings tables.

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-10 15:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6g7h8"
down_revision: Union[str, None] = "b2c3d4e5f6g7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return any(index.get("name") == index_name for index in inspector.get_indexes(table_name))


def _ensure_audio_caches_table() -> None:
    if _table_exists("audio_caches"):
        return

    op.create_table(
        "audio_caches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False, comment="cache key"),
        sa.Column("text", sa.Text(), nullable=False, comment="raw text"),
        sa.Column("text_hash", sa.String(64), nullable=False, comment="text sha256"),
        sa.Column("plugin_id", sa.String(100), nullable=False, comment="plugin id"),
        sa.Column("voice", sa.String(100), nullable=False, comment="voice code"),
        sa.Column("locale", sa.String(20), nullable=False, server_default="zh-CN", comment="locale"),
        sa.Column("speed", sa.Integer(), nullable=False, server_default="50", comment="speed"),
        sa.Column("volume", sa.Integer(), nullable=False, server_default="50", comment="volume"),
        sa.Column("pitch", sa.Integer(), nullable=False, server_default="50", comment="pitch"),
        sa.Column("format", sa.String(10), nullable=False, server_default="mp3", comment="audio format"),
        sa.Column("file_path", sa.String(255), nullable=False, comment="relative file path"),
        sa.Column("audio_size", sa.Integer(), nullable=False, server_default="0", comment="audio size bytes"),
        sa.Column("hit_count", sa.Integer(), nullable=False, server_default="0", comment="hit count"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="created at"),
        sa.Column("last_accessed_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="last accessed at"),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_system_settings_table() -> None:
    if _table_exists("system_settings"):
        return

    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("key", sa.String(100), nullable=False, comment="setting key"),
        sa.Column("value", sa.JSON(), nullable=True, comment="setting value"),
        sa.Column("description", sa.String(500), nullable=False, server_default="", comment="setting description"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), comment="updated at"),
        sa.PrimaryKeyConstraint("id"),
    )


def _ensure_default_settings() -> None:
    op.execute(
        """
        INSERT INTO system_settings (key, value, description)
        SELECT 'cache.audio.enabled', 'true', 'enable audio cache'
        WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE key = 'cache.audio.enabled')
        """
    )
    op.execute(
        """
        INSERT INTO system_settings (key, value, description)
        SELECT 'cache.audio.max_age_days', '7', 'cache max age days'
        WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE key = 'cache.audio.max_age_days')
        """
    )
    op.execute(
        """
        INSERT INTO system_settings (key, value, description)
        SELECT 'cache.audio.max_count', '1000', 'cache max count'
        WHERE NOT EXISTS (SELECT 1 FROM system_settings WHERE key = 'cache.audio.max_count')
        """
    )


def upgrade() -> None:
    _ensure_audio_caches_table()

    if not _index_exists("audio_caches", "ix_audio_caches_cache_key"):
        op.create_index("ix_audio_caches_cache_key", "audio_caches", ["cache_key"], unique=True)
    if not _index_exists("audio_caches", "idx_created_at"):
        op.create_index("idx_created_at", "audio_caches", ["created_at"])
    if not _index_exists("audio_caches", "idx_last_accessed_at"):
        op.create_index("idx_last_accessed_at", "audio_caches", ["last_accessed_at"])

    _ensure_system_settings_table()

    if not _index_exists("system_settings", "ix_system_settings_key"):
        op.create_index("ix_system_settings_key", "system_settings", ["key"], unique=True)

    _ensure_default_settings()


def downgrade() -> None:
    if _table_exists("audio_caches"):
        if _index_exists("audio_caches", "idx_last_accessed_at"):
            op.drop_index("idx_last_accessed_at", table_name="audio_caches")
        if _index_exists("audio_caches", "idx_created_at"):
            op.drop_index("idx_created_at", table_name="audio_caches")
        if _index_exists("audio_caches", "ix_audio_caches_cache_key"):
            op.drop_index("ix_audio_caches_cache_key", table_name="audio_caches")
        op.drop_table("audio_caches")

    if _table_exists("system_settings"):
        if _index_exists("system_settings", "ix_system_settings_key"):
            op.drop_index("ix_system_settings_key", table_name="system_settings")
        op.drop_table("system_settings")
