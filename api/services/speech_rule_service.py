"""
朗读规则服务
"""
import re
from typing import Optional, List

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.speech_rule import SpeechRule
from ..schemas.rules import SpeechRuleCreate, SpeechRuleUpdate


class SpeechRuleService:
    """朗读规则服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> List[SpeechRule]:
        """获取所有规则"""
        stmt = select(SpeechRule).order_by(SpeechRule.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_enabled(self) -> List[SpeechRule]:
        """获取所有启用的规则"""
        stmt = select(SpeechRule).where(
            SpeechRule.is_enabled == True
        ).order_by(SpeechRule.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, rule_id: int) -> Optional[SpeechRule]:
        """通过 ID 获取规则"""
        stmt = select(SpeechRule).where(SpeechRule.id == rule_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: SpeechRuleCreate) -> SpeechRule:
        """创建规则"""
        # 验证正则表达式
        if data.is_regex:
            try:
                re.compile(data.pattern)
            except re.error as e:
                raise ValueError(f"无效的正则表达式: {e}")
        
        # 获取最大排序值
        stmt = select(func.max(SpeechRule.order))
        result = await self.db.execute(stmt)
        max_order = result.scalar() or 0

        rule = SpeechRule(
            name=data.name,
            pattern=data.pattern,
            target_config_id=data.target_config_id,
            is_regex=data.is_regex,
            is_enabled=data.is_enabled,
            order=max_order + 1,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def update(self, rule_id: int, data: SpeechRuleUpdate) -> Optional[SpeechRule]:
        """更新规则"""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        
        # 验证正则表达式
        if 'pattern' in update_data or 'is_regex' in update_data:
            pattern = update_data.get('pattern', rule.pattern)
            is_regex = update_data.get('is_regex', rule.is_regex)
            if is_regex:
                try:
                    re.compile(pattern)
                except re.error as e:
                    raise ValueError(f"无效的正则表达式: {e}")
        
        for key, value in update_data.items():
            setattr(rule, key, value)
        
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def delete(self, rule_id: int) -> bool:
        """删除规则"""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return False
        
        await self.db.delete(rule)
        return True

    async def batch_update(self, ids: List[int], is_enabled: Optional[bool] = None,
                          target_config_id: Optional[int] = None) -> int:
        """批量更新"""
        update_data = {}
        if is_enabled is not None:
            update_data['is_enabled'] = is_enabled
        if target_config_id is not None:
            update_data['target_config_id'] = target_config_id
        
        if not update_data:
            return 0
        
        stmt = update(SpeechRule).where(
            SpeechRule.id.in_(ids)
        ).values(**update_data)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def batch_delete(self, ids: List[int]) -> int:
        """批量删除"""
        stmt = delete(SpeechRule).where(SpeechRule.id.in_(ids))
        result = await self.db.execute(stmt)
        return result.rowcount

    async def reorder(self, rule_ids: List[int]) -> bool:
        """重新排序"""
        for i, rule_id in enumerate(rule_ids):
            stmt = update(SpeechRule).where(
                SpeechRule.id == rule_id
            ).values(order=i)
            await self.db.execute(stmt)
        return True