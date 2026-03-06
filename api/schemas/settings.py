"""
系统设置 Schema
"""
from typing import Any, Literal
from pydantic import BaseModel, Field


class CacheSettingsResponse(BaseModel):
    """缓存设置响应"""

    cache_audio_enabled: bool = Field(description="是否启用音频缓存")
    cache_audio_max_age_days: int = Field(description="缓存过期天数")
    cache_audio_max_count: int = Field(description="最大缓存数量")


class CacheSettingsUpdate(BaseModel):
    """缓存设置更新"""

    cache_audio_enabled: bool = Field(default=True, description="是否启用音频缓存")
    cache_audio_max_age_days: int = Field(default=7, ge=1, le=365, description="缓存过期天数（1-365）")
    cache_audio_max_count: int = Field(default=1000, ge=100, le=100000, description="最大缓存数量（100-100000）")


class UpstreamSettingsResponse(BaseModel):
    """上游连接设置响应"""

    connection_mode: Literal["concurrent", "queue", "replace"] = Field(description="上游连接方式")
    timeout_seconds: int = Field(description="上游连接超时时间（秒）")
    retry_count: int = Field(description="上游失败重试次数")


class UpstreamSettingsUpdate(BaseModel):
    """上游连接设置更新"""

    connection_mode: Literal["concurrent", "queue", "replace"] = Field(description="上游连接方式")
    timeout_seconds: int = Field(default=30, ge=1, le=300, description="上游连接超时时间（1-300 秒）")
    retry_count: int = Field(default=1, ge=0, le=5, description="上游失败重试次数（0-5）")


class SettingsResponse(BaseModel):
    """通用设置响应"""

    key: str
    value: Any
    description: str


class MessageResponse(BaseModel):
    """消息响应"""

    message: str


class ApiAuthSettingsResponse(BaseModel):
    """API 鉴权设置响应"""

    api_auth_enabled: bool = Field(description="是否启用 API 鉴权")


class ApiAuthSettingsUpdate(BaseModel):
    """API 鉴权设置更新"""

    api_auth_enabled: bool = Field(description="是否启用 API 鉴权")
