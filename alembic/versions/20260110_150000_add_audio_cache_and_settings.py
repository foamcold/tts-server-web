"""添加音频缓存和系统设置表

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-10 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级迁移：添加音频缓存和系统设置表"""
    
    # 创建音频缓存索引表
    op.create_table(
        'audio_caches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cache_key', sa.String(64), nullable=False, comment='缓存键（SHA256哈希）'),
        sa.Column('text', sa.Text(), nullable=False, comment='原始文本'),
        sa.Column('text_hash', sa.String(64), nullable=False, comment='文本SHA256哈希'),
        sa.Column('plugin_id', sa.String(100), nullable=False, comment='插件ID'),
        sa.Column('voice', sa.String(100), nullable=False, comment='发音人代码'),
        sa.Column('locale', sa.String(20), nullable=False, server_default='zh-CN', comment='语言区域'),
        sa.Column('speed', sa.Integer(), nullable=False, server_default='50', comment='语速 0-100'),
        sa.Column('volume', sa.Integer(), nullable=False, server_default='50', comment='音量 0-100'),
        sa.Column('pitch', sa.Integer(), nullable=False, server_default='50', comment='音调 0-100'),
        sa.Column('format', sa.String(10), nullable=False, server_default='mp3', comment='音频格式'),
        sa.Column('file_path', sa.String(255), nullable=False, comment='音频文件相对路径'),
        sa.Column('audio_size', sa.Integer(), nullable=False, server_default='0', comment='音频大小（字节）'),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0', comment='命中次数'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='创建时间'),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='最后访问时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_audio_caches_cache_key', 'audio_caches', ['cache_key'], unique=True)
    op.create_index('idx_created_at', 'audio_caches', ['created_at'])
    op.create_index('idx_last_accessed_at', 'audio_caches', ['last_accessed_at'])
    
    # 创建系统设置表
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(100), nullable=False, comment='设置键'),
        sa.Column('value', sa.JSON(), nullable=True, comment='设置值'),
        sa.Column('description', sa.String(500), nullable=False, server_default='', comment='设置描述'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=True)
    
    # 插入默认设置
    op.execute("""
        INSERT INTO system_settings (key, value, description) VALUES 
        ('cache.audio.enabled', 'true', '是否启用音频缓存'),
        ('cache.audio.max_age_days', '7', '缓存过期天数'),
        ('cache.audio.max_count', '1000', '最大缓存数量')
    """)


def downgrade() -> None:
    """降级迁移：删除音频缓存和系统设置表"""
    
    # 删除音频缓存表索引
    op.drop_index('idx_last_accessed_at', table_name='audio_caches')
    op.drop_index('idx_created_at', table_name='audio_caches')
    op.drop_index('ix_audio_caches_cache_key', table_name='audio_caches')
    
    # 删除音频缓存表
    op.drop_table('audio_caches')
    
    # 删除系统设置表索引
    op.drop_index('ix_system_settings_key', table_name='system_settings')
    
    # 删除系统设置表
    op.drop_table('system_settings')
