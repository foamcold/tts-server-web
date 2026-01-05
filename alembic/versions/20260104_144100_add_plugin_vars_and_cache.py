"""增加插件变量和缓存字段

Revision ID: a1b2c3d4e5f6
Revises: 6255554d5ddd
Create Date: 2026-01-04 14:41:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6255554d5ddd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级迁移：添加插件变量和缓存相关字段"""
    # 添加默认变量字段
    op.add_column('plugins', sa.Column('def_vars', sa.JSON(), nullable=True, comment='插件默认变量'))
    
    # 注意：原有的 user_vars 是 Text 类型，需要先删除再创建为 JSON 类型
    # 如果数据库中已有数据，需要先备份数据
    op.drop_column('plugins', 'user_vars')
    op.add_column('plugins', sa.Column('user_vars', sa.JSON(), nullable=True, comment='用户自定义变量'))
    
    # 添加缓存相关字段
    op.add_column('plugins', sa.Column('cached_locales', sa.JSON(), nullable=True, comment='缓存的语言列表'))
    op.add_column('plugins', sa.Column('cached_voices', sa.JSON(), nullable=True, comment='缓存的声音列表'))
    op.add_column('plugins', sa.Column('last_cache_time', sa.DateTime(), nullable=True, comment='最后缓存时间'))


def downgrade() -> None:
    """降级迁移：删除插件变量和缓存相关字段"""
    # 删除缓存相关字段
    op.drop_column('plugins', 'last_cache_time')
    op.drop_column('plugins', 'cached_voices')
    op.drop_column('plugins', 'cached_locales')
    
    # 将user_vars 恢复为 Text 类型
    op.drop_column('plugins', 'user_vars')
    op.add_column('plugins', sa.Column('user_vars', sa.Text(), nullable=True, server_default='{}', comment='用户变量 JSON'))
    
    # 删除默认变量字段
    op.drop_column('plugins', 'def_vars')
