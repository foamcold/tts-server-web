"""
系统设置服务
管理系统级别的配置项
"""
import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.system_settings import SystemSettings, SettingsKeys, DEFAULT_SETTINGS

logger = logging.getLogger(__name__)


class SettingsService:
    """系统设置服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_setting(self, key: str) -> Optional[Any]:
        """
        获取单个设置值
        
        Args:
            key: 设置键
            
        Returns:
            设置值，不存在则返回默认值或 None
        """
        stmt = select(SystemSettings).where(SystemSettings.key == key)
        result = await self.db.execute(stmt)
        setting = result.scalar_one_or_none()
        
        if setting:
            return setting.value
        
        # 返回默认值
        if key in DEFAULT_SETTINGS:
            return DEFAULT_SETTINGS[key]["value"]
        
        return None

    async def set_setting(self, key: str, value: Any, description: str = "") -> SystemSettings:
        """
        设置单个配置值
        
        Args:
            key: 设置键
            value: 设置值
            description: 设置描述
            
        Returns:
            更新后的设置对象
        """
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
                description=description or DEFAULT_SETTINGS.get(key, {}).get("description", "")
            )
            self.db.add(setting)
        
        await self.db.flush()
        return setting

    async def get_cache_settings(self) -> dict:
        """
        获取缓存相关设置
        
        Returns:
            缓存设置字典
        """
        enabled = await self.get_setting(SettingsKeys.CACHE_AUDIO_ENABLED)
        max_age_days = await self.get_setting(SettingsKeys.CACHE_AUDIO_MAX_AGE_DAYS)
        max_count = await self.get_setting(SettingsKeys.CACHE_AUDIO_MAX_COUNT)
        
        return {
            "cache_audio_enabled": enabled if enabled is not None else True,
            "cache_audio_max_age_days": max_age_days if max_age_days is not None else 7,
            "cache_audio_max_count": max_count if max_count is not None else 1000,
        }

    async def update_cache_settings(
        self,
        enabled: bool,
        max_age_days: int,
        max_count: int
    ) -> dict:
        """
        更新缓存设置
        
        Args:
            enabled: 是否启用缓存
            max_age_days: 缓存过期天数
            max_count: 最大缓存数量
            
        Returns:
            更新后的设置字典
        """
        await self.set_setting(
            SettingsKeys.CACHE_AUDIO_ENABLED,
            enabled,
            "是否启用音频缓存"
        )
        await self.set_setting(
            SettingsKeys.CACHE_AUDIO_MAX_AGE_DAYS,
            max_age_days,
            "缓存过期天数"
        )
        await self.set_setting(
            SettingsKeys.CACHE_AUDIO_MAX_COUNT,
            max_count,
            "最大缓存数量"
        )
        
        logger.info(f"缓存设置已更新: enabled={enabled}, max_age_days={max_age_days}, max_count={max_count}")
        
        return await self.get_cache_settings()

    async def init_default_settings(self) -> None:
        """
        初始化默认设置
        如果设置不存在则创建
        """
        for key, config in DEFAULT_SETTINGS.items():
            existing = await self.get_setting(key)
            if existing is None:
                await self.set_setting(key, config["value"], config["description"])
                logger.info(f"初始化默认设置: {key} = {config['value']}")
