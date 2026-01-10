"""移除插件缓存字段，缓存迁移到前端浏览器

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-10 12:55:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级迁移：删除插件缓存相关字段，缓存功能迁移到前端浏览器"""
    # 删除缓存相关字段
    op.drop_column('plugins', 'cached_locales')
    op.drop_column('plugins', 'cached_voices')
    op.drop_column('plugins', 'last_cache_time')


def downgrade() -> None:
    """降级迁移：恢复插件缓存相关字段"""
    # 恢复缓存相关字段
    op.add_column('plugins', sa.Column('cached_locales', sa.JSON(), nullable=True, comment='缓存的语言列表'))
    op.add_column('plugins', sa.Column('cached_voices', sa.JSON(), nullable=True, comment='缓存的声音列表'))
    op.add_column('plugins', sa.Column('last_cache_time', sa.DateTime(), nullable=True, comment='最后缓存时间'))
