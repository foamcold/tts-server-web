"""
系统设置服务
管理系统级别的配置项
"""
import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.system_settings import DEFAULT_SETTINGS, SettingsKeys, SystemSettings
from .upstream_controller import UpstreamSettings

logger = logging.getLogger(__name__)


class SettingsService:
    """系统设置服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_setting(self, key: str) -> Optional[Any]:
        """获取单个设置值"""

        stmt = select(SystemSettings).where(SystemSettings.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            return setting.value

        if key in DEFAULT_SETTINGS:
            return DEFAULT_SETTINGS[key]["value"]

        return None

    async def set_setting(self, key: str, value: Any, description: str = "") -> SystemSettings:
        """设置单个配置值"""

        stmt = select(SystemSettings).where(SystemSettings.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SystemSettings(
                key=key,
                value=value,
                description=description or DEFAULT_SETTINGS.get(key, {}).get("description", ""),
            )
            self.db.add(setting)

        await self.db.flush()
        return setting

    async def get_cache_settings(self) -> dict:
        """获取缓存相关设置"""

        enabled = await self.get_setting(SettingsKeys.CACHE_AUDIO_ENABLED)
        max_age_days = await self.get_setting(SettingsKeys.CACHE_AUDIO_MAX_AGE_DAYS)
        max_count = await self.get_setting(SettingsKeys.CACHE_AUDIO_MAX_COUNT)

        return {
            "cache_audio_enabled": enabled if enabled is not None else True,
            "cache_audio_max_age_days": max_age_days if max_age_days is not None else 7,
            "cache_audio_max_count": max_count if max_count is not None else 1000,
        }

    async def update_cache_settings(self, enabled: bool, max_age_days: int, max_count: int) -> dict:
        """更新缓存设置"""

        await self.set_setting(SettingsKeys.CACHE_AUDIO_ENABLED, enabled, "是否启用音频缓存")
        await self.set_setting(SettingsKeys.CACHE_AUDIO_MAX_AGE_DAYS, max_age_days, "缓存过期天数")
        await self.set_setting(SettingsKeys.CACHE_AUDIO_MAX_COUNT, max_count, "最大缓存数量")

        logger.info("缓存设置已更新: enabled=%s, max_age_days=%s, max_count=%s", enabled, max_age_days, max_count)
        return await self.get_cache_settings()

    async def get_upstream_settings(self) -> dict:
        """获取上游连接设置"""

        connection_mode = await self.get_setting(SettingsKeys.UPSTREAM_CONNECTION_MODE)
        timeout_seconds = await self.get_setting(SettingsKeys.UPSTREAM_TIMEOUT_SECONDS)
        retry_count = await self.get_setting(SettingsKeys.UPSTREAM_RETRY_COUNT)

        return {
            "connection_mode": connection_mode if connection_mode in {"concurrent", "queue", "replace"} else "concurrent",
            "timeout_seconds": int(timeout_seconds) if timeout_seconds is not None else 30,
            "retry_count": int(retry_count) if retry_count is not None else 1,
        }

    async def get_upstream_runtime_settings(self) -> UpstreamSettings:
        """获取控制器使用的上游连接设置"""

        settings = await self.get_upstream_settings()
        return UpstreamSettings(
            mode=settings["connection_mode"],
            timeout_seconds=settings["timeout_seconds"],
            retry_count=settings["retry_count"],
        )

    async def update_upstream_settings(self, connection_mode: str, timeout_seconds: int, retry_count: int) -> dict:
        """更新上游连接设置"""

        await self.set_setting(SettingsKeys.UPSTREAM_CONNECTION_MODE, connection_mode, "上游连接方式")
        await self.set_setting(SettingsKeys.UPSTREAM_TIMEOUT_SECONDS, timeout_seconds, "上游连接超时时间（秒）")
        await self.set_setting(SettingsKeys.UPSTREAM_RETRY_COUNT, retry_count, "上游失败后的重试次数")

        logger.info(
            "上游连接设置已更新: mode=%s, timeout_seconds=%s, retry_count=%s",
            connection_mode,
            timeout_seconds,
            retry_count,
        )
        return await self.get_upstream_settings()

    async def init_default_settings(self) -> None:
        """初始化默认设置"""

        for key, config in DEFAULT_SETTINGS.items():
            existing = await self.get_setting(key)
            if existing is None:
                await self.set_setting(key, config["value"], config["description"])
                logger.info("初始化默认设置: %s = %s", key, config["value"])

    async def get_api_auth_enabled(self) -> bool:
        """获取 API 鉴权开关状态"""

        value = await self.get_setting(SettingsKeys.API_AUTH_ENABLED)
        return bool(value) if value is not None else False

    async def set_api_auth_enabled(self, enabled: bool) -> None:
        """设置 API 鉴权开关状态"""

        await self.set_setting(
            SettingsKeys.API_AUTH_ENABLED,
            enabled,
            "是否启用 API 鉴权（启用后公开 API 需要 API Key）",
        )
        logger.info("API 鉴权设置已更新: enabled=%s", enabled)
