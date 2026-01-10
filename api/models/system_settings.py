"""
系统设置模型
存储系统级别的配置项
"""
from datetime import datetime
from typing import Any
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SystemSettings(Base):
    """系统设置表"""
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # 设置键（唯一索引）
    key: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        index=True, 
        comment="设置键"
    )
    
    # 设置值（JSON格式，支持各种类型）
    value: Mapped[Any] = mapped_column(JSON, comment="设置值")
    
    # 设置描述
    description: Mapped[str] = mapped_column(
        String(500), 
        default="", 
        comment="设置描述"
    )
    
    # 更新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
        comment="更新时间"
    )

    def __repr__(self) -> str:
        return f"<SystemSettings(key={self.key}, value={self.value})>"


# 预定义的设置键常量
class SettingsKeys:
    """系统设置键常量"""
    # 音频缓存设置
    CACHE_AUDIO_ENABLED = "cache.audio.enabled"
    CACHE_AUDIO_MAX_AGE_DAYS = "cache.audio.max_age_days"
    CACHE_AUDIO_MAX_COUNT = "cache.audio.max_count"
    # API 鉴权设置
    API_AUTH_ENABLED = "api.auth.enabled"


# 默认设置值
DEFAULT_SETTINGS = {
    SettingsKeys.CACHE_AUDIO_ENABLED: {
        "value": True,
        "description": "是否启用音频缓存"
    },
    SettingsKeys.CACHE_AUDIO_MAX_AGE_DAYS: {
        "value": 7,
        "description": "缓存过期天数"
    },
    SettingsKeys.CACHE_AUDIO_MAX_COUNT: {
        "value": 1000,
        "description": "最大缓存数量"
    },
    SettingsKeys.API_AUTH_ENABLED: {
        "value": False,
        "description": "是否启用 API 鉴权（需要 API Key 才能调用公开 API）"
    },
}
