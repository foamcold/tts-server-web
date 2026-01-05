"""
替换规则服务
"""
import re
import json
from typing import Optional, List

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.replace_rule import ReplaceRule
from ..schemas.rules import (
    ReplaceRuleCreate, ReplaceRuleUpdate, ReplaceRuleTest, ReplaceRuleTestResponse
)


class ReplaceRuleService:
    """替换规则服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, group_id: Optional[int] = None) -> List[ReplaceRule]:
        """获取所有规则"""
        stmt = select(ReplaceRule)
        if group_id is not None:
            stmt = stmt.where(ReplaceRule.group_id == group_id)
        stmt = stmt.order_by(ReplaceRule.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_enabled(self) -> List[ReplaceRule]:
        """获取所有启用的规则"""
        stmt = select(ReplaceRule).where(
            ReplaceRule.is_enabled == True
        ).order_by(ReplaceRule.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, rule_id: int) -> Optional[ReplaceRule]:
        """通过 ID 获取规则"""
        stmt = select(ReplaceRule).where(ReplaceRule.id == rule_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: ReplaceRuleCreate) -> ReplaceRule:
        """创建规则"""
        # 验证正则表达式
        if data.is_regex:
            try:
                re.compile(data.pattern)
            except re.error as e:
                raise ValueError(f"无效的正则表达式: {e}")
        
        # 获取最大排序值
        stmt = select(func.max(ReplaceRule.order))
        result = await self.db.execute(stmt)
        max_order = result.scalar() or 0

        rule = ReplaceRule(
            name=data.name,
            pattern=data.pattern,
            replacement=data.replacement,
            pattern_type=1 if data.is_regex else 0,
            is_enabled=data.is_enabled,
            group_id=data.group_id,
            order=max_order + 1,
        )
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def update(self, rule_id: int, data: ReplaceRuleUpdate) -> Optional[ReplaceRule]:
        """更新规则"""
        rule = await self.get_by_id(rule_id)
        if not rule:
            return None

        update_data = data.model_dump(exclude_unset=True)
        
        # 验证正则表达式
        if 'pattern' in update_data or 'is_regex' in update_data:
            pattern = update_data.get('pattern', rule.pattern)
            is_regex = update_data.get('is_regex', rule.pattern_type == 1)
            if is_regex:
                try:
                    re.compile(pattern)
                except re.error as e:
                    raise ValueError(f"无效的正则表达式: {e}")
        
        if 'is_regex' in update_data:
            rule.pattern_type = 1 if update_data.pop('is_regex') else 0

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
                          group_id: Optional[int] = None) -> int:
        """批量更新"""
        update_data = {}
        if is_enabled is not None:
            update_data['is_enabled'] = is_enabled
        if group_id is not None:
            update_data['group_id'] = group_id
        
        if not update_data:
            return 0
        
        stmt = update(ReplaceRule).where(
            ReplaceRule.id.in_(ids)
        ).values(**update_data)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def batch_delete(self, ids: List[int]) -> int:
        """批量删除"""
        stmt = delete(ReplaceRule).where(ReplaceRule.id.in_(ids))
        result = await self.db.execute(stmt)
        return result.rowcount

    async def reorder(self, rule_ids: List[int]) -> bool:
        """重新排序"""
        for i, rule_id in enumerate(rule_ids):
            stmt = update(ReplaceRule).where(
                ReplaceRule.id == rule_id
            ).values(order=i)
            await self.db.execute(stmt)
        return True

    async def import_rules(self, json_data: str) -> List[ReplaceRule]:
        """导入规则"""
        data = json.loads(json_data)
        if not isinstance(data, list):
            data = [data]
        
        rules = []
        for item in data:
            rule_data = ReplaceRuleCreate(
                name=item.get('name', ''),
                pattern=item.get('pattern', ''),
                replacement=item.get('replacement', ''),
                is_regex=item.get('isRegex', item.get('is_regex', False)),
                is_enabled=item.get('isEnabled', item.get('is_enabled', True)),
                group_id=item.get('groupId', item.get('group_id', 0)),
            )
            rule = await self.create(rule_data)
            rules.append(rule)
        
        return rules

    def export_rules(self, rules: List[ReplaceRule]) -> str:
        """导出规则"""
        return json.dumps([{
            'name': rule.name,
            'pattern': rule.pattern,
            'replacement': rule.replacement,
            'isRegex': rule.pattern_type == 1,
            'isEnabled': rule.is_enabled,
            'groupId': rule.group_id,
        } for rule in rules], ensure_ascii=False, indent=2)

    def test_rule(self, data: ReplaceRuleTest) -> ReplaceRuleTestResponse:
        """测试规则"""
        match_count = 0
        result = data.text
        
        try:
            if data.is_regex:
                pattern = re.compile(data.pattern)
                matches = pattern.findall(data.text)
                match_count = len(matches)
                result = pattern.sub(data.replacement, data.text)
            else:
                match_count = data.text.count(data.pattern)
                result = data.text.replace(data.pattern, data.replacement)
        except re.error as e:
            raise ValueError(f"正则表达式错误: {e}")
        
        return ReplaceRuleTestResponse(
            original=data.text,
            result=result,
            match_count=match_count,
        )