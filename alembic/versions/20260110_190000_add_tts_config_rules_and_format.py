"""为 tts_configs 表添加 apply_rules 和 audio_format 字段

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i9
Create Date: 2026-01-10 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 apply_rules 字段（是否应用替换规则，默认 True）
    op.add_column(
        'tts_configs',
        sa.Column('apply_rules', sa.Boolean(), nullable=False, server_default='1', comment='是否应用替换规则')
    )
    
    # 添加 audio_format 字段（音频格式，默认 mp3）
    op.add_column(
        'tts_configs',
        sa.Column('audio_format', sa.String(10), nullable=False, server_default='mp3', comment='音频格式')
    )


def downgrade() -> None:
    op.drop_column('tts_configs', 'audio_format')
    op.drop_column('tts_configs', 'apply_rules')
