"""add user api_key field

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-01-10 18:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加用户 api_key 字段"""
    # 添加 api_key 字段到 users 表
    op.add_column('users', sa.Column('api_key', sa.String(64), nullable=True, comment='API 密钥，用户注册时自动生成'))
    
    # 创建唯一索引
    op.create_index('ix_users_api_key', 'users', ['api_key'], unique=True)


def downgrade() -> None:
    """移除用户 api_key 字段"""
    # 删除索引
    op.drop_index('ix_users_api_key', table_name='users')
    
    # 删除字段
    op.drop_column('users', 'api_key')
