"""
TTS 配置服务
"""
from typing import Optional, List

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.tts_group import TtsGroup
from ..models.tts_config import TtsConfig
from ..schemas.tts import (
    TtsGroupCreate, TtsGroupUpdate,
    TtsConfigCreate, TtsConfigUpdate,ReorderItem,
)


class TtsService:
    """TTS 配置服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    #============分组操作 ============

    async def get_groups(self) -> List[TtsGroup]:
        """获取所有分组 (按排序)"""
        stmt = select(TtsGroup).order_by(TtsGroup.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_groups_with_configs(self) -> List[TtsGroup]:
        """获取所有分组及其配置"""
        stmt = (
            select(TtsGroup)
            .options(selectinload(TtsGroup.configs))
            .order_by(TtsGroup.order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_group_by_id(self, group_id: int) -> Optional[TtsGroup]:
        """通过 ID 获取分组"""
        stmt = select(TtsGroup).where(TtsGroup.id == group_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_group(self, data: TtsGroupCreate) -> TtsGroup:
        """创建分组"""
        # 获取最大排序值
        stmt = select(func.max(TtsGroup.order))
        result = await self.db.execute(stmt)
        max_order = result.scalar() or 0

        group = TtsGroup(
            name=data.name,
            is_expanded=data.is_expanded,
            audio_params=data.audio_params,
            order=max_order + 1,
        )
        self.db.add(group)
        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def update_group(self, group_id: int, data: TtsGroupUpdate) -> Optional[TtsGroup]:
        """更新分组"""
        group = await self.get_group_by_id(group_id)
        if not group:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(group, key, value)
        
        await self.db.flush()
        await self.db.refresh(group)
        return group

    async def delete_group(self, group_id: int) -> bool:
        """删除分组 (级联删除配置)"""
        group = await self.get_group_by_id(group_id)
        if not group:
            return False
        
        await self.db.delete(group)
        return True

    async def reorder_groups(self, items: List[ReorderItem]) -> bool:
        """重新排序分组"""
        for item in items:
            stmt = (
                update(TtsGroup)
                .where(TtsGroup.id == item.id)
                .values(order=item.order)
            )
            await self.db.execute(stmt)
        return True

    # ============ 配置操作 ============

    async def get_configs_by_group(self, group_id: int) -> List[TtsConfig]:
        """获取分组下的所有配置"""
        stmt = (
            select(TtsConfig)
            .where(TtsConfig.group_id == group_id).order_by(TtsConfig.order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_config_by_id(self, config_id: int) -> Optional[TtsConfig]:
        """通过 ID 获取配置"""
        stmt = select(TtsConfig).where(TtsConfig.id == config_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_enabled_configs(self) -> List[TtsConfig]:
        """获取所有启用的配置"""
        stmt = (
            select(TtsConfig)
            .where(TtsConfig.is_enabled == True)
            .order_by(TtsConfig.order)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_config(self, data: TtsConfigCreate) -> TtsConfig:
        """创建配置"""
        # 获取分组内最大排序值
        stmt = select(func.max(TtsConfig.order)).where(
            TtsConfig.group_id == data.group_id
        )
        result = await self.db.execute(stmt)
        max_order = result.scalar() or 0
        
        config = TtsConfig(
            **data.model_dump(),
            order=max_order + 1,
        )
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def update_config(self, config_id: int, data: TtsConfigUpdate) -> Optional[TtsConfig]:
        """更新配置"""
        config = await self.get_config_by_id(config_id)
        if not config:
            return None
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)
        
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def delete_config(self, config_id: int) -> bool:
        """删除配置"""
        config = await self.get_config_by_id(config_id)
        if not config:
            return False
        
        await self.db.delete(config)
        return True

    async def batch_move_configs(self, config_ids: List[int], target_group_id: int) -> int:
        """批量移动配置到目标分组"""
        stmt = (
            update(TtsConfig)
            .where(TtsConfig.id.in_(config_ids))
            .values(group_id=target_group_id)
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def batch_enable_configs(self, config_ids: List[int], is_enabled: bool) -> int:
        """批量启用/禁用配置"""
        stmt = (
            update(TtsConfig)
            .where(TtsConfig.id.in_(config_ids))
            .values(is_enabled=is_enabled)
        )
        result = await self.db.execute(stmt)
        return result.rowcount

    async def reorder_configs(self, items: List[ReorderItem]) -> bool:
        """重新排序配置"""
        for item in items:
            stmt = (
                update(TtsConfig)
                .where(TtsConfig.id == item.id)
                .values(order=item.order)
            )
            await self.db.execute(stmt)
        return True