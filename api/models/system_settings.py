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

    key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="设置键",
    )

    value: Mapped[Any] = mapped_column(JSON, comment="设置值")

    description: Mapped[str] = mapped_column(
        String(500),
        default="",
        comment="设置描述",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )

    def __repr__(self) -> str:
        return f"<SystemSettings(key={self.key}, value={self.value})>"


class SettingsKeys:
    """系统设置键常量"""

    CACHE_AUDIO_ENABLED = "cache.audio.enabled"
    CACHE_AUDIO_MAX_AGE_DAYS = "cache.audio.max_age_days"
    CACHE_AUDIO_MAX_COUNT = "cache.audio.max_count"
    API_AUTH_ENABLED = "api.auth.enabled"

    UPSTREAM_CONNECTION_MODE = "upstream.connection.mode"
    UPSTREAM_TIMEOUT_SECONDS = "upstream.connection.timeout_seconds"
    UPSTREAM_RETRY_COUNT = "upstream.connection.retry_count"


DEFAULT_SETTINGS = {
    SettingsKeys.CACHE_AUDIO_ENABLED: {
        "value": True,
        "description": "是否启用音频缓存",
    },
    SettingsKeys.CACHE_AUDIO_MAX_AGE_DAYS: {
        "value": 7,
        "description": "缓存过期天数",
    },
    SettingsKeys.CACHE_AUDIO_MAX_COUNT: {
        "value": 1000,
        "description": "最大缓存数量",
    },
    SettingsKeys.API_AUTH_ENABLED: {
        "value": False,
        "description": "是否启用 API 鉴权（启用后公开 API 需要 API Key）",
    },
    SettingsKeys.UPSTREAM_CONNECTION_MODE: {
        "value": "concurrent",
        "description": "上游连接方式：并发、排队、替换旧请求",
    },
    SettingsKeys.UPSTREAM_TIMEOUT_SECONDS: {
        "value": 30,
        "description": "上游连接超时时间（秒）",
    },
    SettingsKeys.UPSTREAM_RETRY_COUNT: {
        "value": 1,
        "description": "上游失败后的重试次数",
    },
}
