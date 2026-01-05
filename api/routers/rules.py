"""
规则管理路由
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.rules import (
    ReplaceRuleCreate, ReplaceRuleUpdate, ReplaceRuleResponse,
    ReplaceRuleBatchUpdate, ReplaceRuleImport, ReplaceRuleTest, ReplaceRuleTestResponse,
    SpeechRuleCreate, SpeechRuleUpdate, SpeechRuleResponse, SpeechRuleBatchUpdate,
)
from ..schemas.auth import MessageResponse
from ..services.replace_rule_service import ReplaceRuleService
from ..services.speech_rule_service import SpeechRuleService
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(tags=["规则管理"])


#============替换规则 ============

@router.get("/replace-rules", response_model=List[ReplaceRuleResponse])
async def get_replace_rules(
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有替换规则"""
    service = ReplaceRuleService(db)
    rules = await service.get_all(group_id)
    # 将数据库模型转换为响应 Schema，处理字段映射
    return [
        ReplaceRuleResponse(
            id=r.id,
            name=r.name,
            pattern=r.pattern,
            replacement=r.replacement,
            is_regex=r.pattern_type == 1,
            is_enabled=r.is_enabled,
            group_id=r.group_id,
            order=r.order,
            created_at=r.created_at,
            updated_at=r.updated_at,
        ) for r in rules
    ]


@router.get("/replace-rules/{rule_id}", response_model=ReplaceRuleResponse)
async def get_replace_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个替换规则"""
    service = ReplaceRuleService(db)
    rule = await service.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    
    return ReplaceRuleResponse(
        id=rule.id,
        name=rule.name,
        pattern=rule.pattern,
        replacement=rule.replacement,
        is_regex=rule.pattern_type == 1,
        is_enabled=rule.is_enabled,
        group_id=rule.group_id,
        order=rule.order,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.post("/replace-rules", response_model=ReplaceRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_replace_rule(
    data: ReplaceRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建替换规则"""
    service = ReplaceRuleService(db)
    try:
        rule = await service.create(data)
        return ReplaceRuleResponse(
            id=rule.id,
            name=rule.name,
            pattern=rule.pattern,
            replacement=rule.replacement,
            is_regex=rule.pattern_type == 1,
            is_enabled=rule.is_enabled,
            group_id=rule.group_id,
            order=rule.order,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/replace-rules/{rule_id}", response_model=ReplaceRuleResponse)
async def update_replace_rule(
    rule_id: int,
    data: ReplaceRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新替换规则"""
    service = ReplaceRuleService(db)
    try:
        rule = await service.update(rule_id, data)
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        
        return ReplaceRuleResponse(
            id=rule.id,
            name=rule.name,
            pattern=rule.pattern,
            replacement=rule.replacement,
            is_regex=rule.pattern_type == 1,
            is_enabled=rule.is_enabled,
            group_id=rule.group_id,
            order=rule.order,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/replace-rules/{rule_id}", response_model=MessageResponse)
async def delete_replace_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除替换规则"""
    service = ReplaceRuleService(db)
    if not await service.delete(rule_id):
        raise HTTPException(status_code=404, detail="规则不存在")
    return MessageResponse(message="删除成功")


@router.post("/replace-rules/batch-update", response_model=MessageResponse)
async def batch_update_replace_rules(
    data: ReplaceRuleBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量更新替换规则"""
    service = ReplaceRuleService(db)
    count = await service.batch_update(data.ids, data.is_enabled, data.group_id)
    return MessageResponse(message=f"更新了{count} 条规则")


@router.post("/replace-rules/batch-delete", response_model=MessageResponse)
async def batch_delete_replace_rules(
    ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除替换规则"""
    service = ReplaceRuleService(db)
    count = await service.batch_delete(ids)
    return MessageResponse(message=f"删除了 {count} 条规则")


@router.post("/replace-rules/reorder", response_model=MessageResponse)
async def reorder_replace_rules(
    rule_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新排序替换规则"""
    service = ReplaceRuleService(db)
    await service.reorder(rule_ids)
    return MessageResponse(message="排序成功")


@router.post("/replace-rules/import", response_model=List[ReplaceRuleResponse])
async def import_replace_rules(
    data: ReplaceRuleImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导入替换规则"""
    service = ReplaceRuleService(db)
    try:
        rules = await service.import_rules(data.json_data)
        return [
            ReplaceRuleResponse(
                id=r.id,
                name=r.name,
                pattern=r.pattern,
                replacement=r.replacement,
                is_regex=r.pattern_type == 1,
                is_enabled=r.is_enabled,
                group_id=r.group_id,
                order=r.order,
                created_at=r.created_at,
                updated_at=r.updated_at,
            ) for r in rules
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.get("/replace-rules/export/all")
async def export_replace_rules(
    group_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出替换规则"""
    service = ReplaceRuleService(db)
    rules = await service.get_all(group_id)
    return {"json_data": service.export_rules(rules)}


@router.post("/replace-rules/test", response_model=ReplaceRuleTestResponse)
async def test_replace_rule(
    data: ReplaceRuleTest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """测试替换规则"""
    service = ReplaceRuleService(db)
    try:
        return service.test_rule(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ 朗读规则 ============

@router.get("/speech-rules", response_model=List[SpeechRuleResponse])
async def get_speech_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有朗读规则"""
    service = SpeechRuleService(db)
    return await service.get_all()


@router.get("/speech-rules/{rule_id}", response_model=SpeechRuleResponse)
async def get_speech_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个朗读规则"""
    service = SpeechRuleService(db)
    rule = await service.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule


@router.post("/speech-rules", response_model=SpeechRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_speech_rule(
    data: SpeechRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建朗读规则"""
    service = SpeechRuleService(db)
    try:
        return await service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/speech-rules/{rule_id}", response_model=SpeechRuleResponse)
async def update_speech_rule(
    rule_id: int,
    data: SpeechRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新朗读规则"""
    service = SpeechRuleService(db)
    try:
        rule = await service.update(rule_id, data)
        if not rule:
            raise HTTPException(status_code=404, detail="规则不存在")
        return rule
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/speech-rules/{rule_id}", response_model=MessageResponse)
async def delete_speech_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除朗读规则"""
    service = SpeechRuleService(db)
    if not await service.delete(rule_id):
        raise HTTPException(status_code=404, detail="规则不存在")
    return MessageResponse(message="删除成功")


@router.post("/speech-rules/batch-update", response_model=MessageResponse)
async def batch_update_speech_rules(
    data: SpeechRuleBatchUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量更新朗读规则"""
    service = SpeechRuleService(db)
    count = await service.batch_update(data.ids, data.is_enabled, data.target_config_id)
    return MessageResponse(message=f"更新了 {count} 条规则")


@router.post("/speech-rules/batch-delete", response_model=MessageResponse)
async def batch_delete_speech_rules(
    ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量删除朗读规则"""
    service = SpeechRuleService(db)
    count = await service.batch_delete(ids)
    return MessageResponse(message=f"删除了 {count} 条规则")


@router.post("/speech-rules/reorder", response_model=MessageResponse)
async def reorder_speech_rules(
    rule_ids: List[int],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新排序朗读规则"""
    service = SpeechRuleService(db)
    await service.reorder(rule_ids)
    return MessageResponse(message="排序成功")