"""
音频缓存模型
存储音频缓存索引信息，实际音频文件存储在文件系统
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class AudioCache(Base):
    """音频缓存索引表"""
    __tablename__ = "audio_caches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 缓存键（SHA256哈希，用于快速查找）
    cache_key: Mapped[str] = mapped_column(
        String(64), 
        unique=True, 
        index=True, 
        comment="缓存键（SHA256哈希）"
    )
    
    # 原始文本（用于调试和查看）
    text: Mapped[str] = mapped_column(Text, comment="原始文本")
    
    # 文本哈希（用于快速比对）
    text_hash: Mapped[str] = mapped_column(String(64), comment="文本SHA256哈希")
    
    # 合成参数
    plugin_id: Mapped[str] = mapped_column(String(100), comment="插件ID")
    voice: Mapped[str] = mapped_column(String(100), comment="发音人代码")
    locale: Mapped[str] = mapped_column(String(20), default="zh-CN", comment="语言区域")
    speed: Mapped[int] = mapped_column(Integer, default=50, comment="语速 0-100")
    volume: Mapped[int] = mapped_column(Integer, default=50, comment="音量 0-100")
    pitch: Mapped[int] = mapped_column(Integer, default=50, comment="音调 0-100")
    format: Mapped[str] = mapped_column(String(10), default="mp3", comment="音频格式")
    
    # 文件信息
    file_path: Mapped[str] = mapped_column(
        String(255), 
        comment="音频文件相对路径（相对于/data/cache）"
    )
    audio_size: Mapped[int] = mapped_column(Integer, default=0, comment="音频大小（字节）")
    
    # 统计信息
    hit_count: Mapped[int] = mapped_column(Integer, default=0, comment="命中次数")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        comment="创建时间"
    )
    last_accessed_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        comment="最后访问时间"
    )

    # 复合索引：用于清理过期缓存
    __table_args__ = (
        Index('idx_created_at', 'created_at'),
        Index('idx_last_accessed_at', 'last_accessed_at'),
    )

    def __repr__(self) -> str:
        return f"<AudioCache(id={self.id}, cache_key={self.cache_key[:16]}..., voice={self.voice})>"
