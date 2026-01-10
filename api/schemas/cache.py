"""
缓存相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AudioCacheResponse(BaseModel):
    """音频缓存响应"""
    id: int
    cache_key: str
    text: str = Field(description="原始文本（可能被截断）")
    plugin_id: str
    voice: str
    locale: str
    speed: int
    volume: int
    pitch: int
    format: str
    audio_size: int = Field(description="音频大小（字节）")
    hit_count: int = Field(description="命中次数")
    created_at: datetime
    last_accessed_at: datetime

    class Config:
        from_attributes = True


class CacheStatsResponse(BaseModel):
    """缓存统计响应"""
    enabled: bool = Field(description="缓存是否启用")
    total_count: int = Field(description="缓存总数")
    total_size_bytes: int = Field(description="缓存总大小（字节）")
    total_size_mb: float = Field(description="缓存总大小（MB）")
    total_hits: int = Field(description="总命中次数")
    oldest_cache_date: Optional[datetime] = Field(None, description="最早缓存时间")
    newest_cache_date: Optional[datetime] = Field(None, description="最新缓存时间")
    # 设置信息
    max_age_days: int = Field(description="最大缓存天数")
    max_count: int = Field(description="最大缓存数量")


class CacheCleanupResponse(BaseModel):
    """缓存清理响应"""
    deleted_count: int = Field(description="删除的缓存数量")
    deleted_size_bytes: int = Field(description="删除的缓存大小（字节）")
    remaining_count: int = Field(description="剩余缓存数量")
    message: str


class CacheClearResponse(BaseModel):
    """缓存清空响应"""
    deleted_count: int = Field(description="删除的缓存数量")
    deleted_size_bytes: int = Field(description="删除的缓存大小（字节）")
    message: str
