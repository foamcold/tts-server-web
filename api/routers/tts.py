"""
TTS 配置路由
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.tts import (
    TtsGroupCreate, TtsGroupUpdate, TtsGroupResponse, TtsGroupWithConfigs,
    TtsConfigCreate, TtsConfigUpdate, TtsConfigResponse,
    TtsConfigBatchMove, TtsConfigBatchEnable, TtsReorder,
)
from ..schemas.auth import MessageResponse
from ..services.tts_service import TtsService
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/tts-configs", tags=["TTS 配置管理"])


#============分组 API ============

@router.get("/groups", response_model=List[TtsGroupWithConfigs])
async def get_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有 TTS 分组及配置"""
    service = TtsService(db)
    return await service.get_groups_with_configs()


@router.post("/groups", response_model=TtsGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: TtsGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 TTS 分组"""
    service = TtsService(db)
    return await service.create_group(data)


@router.put("/groups/{group_id}", response_model=TtsGroupResponse)
async def update_group(
    group_id: int,
    data: TtsGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 TTS 分组"""
    service = TtsService(db)
    group = await service.update_group(group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="分组不存在")
    return group


@router.delete("/groups/{group_id}", response_model=MessageResponse)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除 TTS 分组"""
    service = TtsService(db)
    if not await service.delete_group(group_id):
        raise HTTPException(status_code=404, detail="分组不存在")
    return MessageResponse(message="删除成功")


@router.post("/groups/reorder", response_model=MessageResponse)
async def reorder_groups(
    data: TtsReorder,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新排序分组"""
    service = TtsService(db)
    await service.reorder_groups(data.items)
    return MessageResponse(message="排序更新成功")


# ============ 配置 API ============

@router.get("/configs/{config_id}", response_model=TtsConfigResponse)
async def get_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个 TTS 配置"""
    service = TtsService(db)
    config = await service.get_config_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.post("/configs", response_model=TtsConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    data: TtsConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建 TTS 配置"""
    service = TtsService(db)
    # 验证分组存在
    group = await service.get_group_by_id(data.group_id)
    if not group:
        raise HTTPException(status_code=400, detail="分组不存在")
    return await service.create_config(data)


@router.put("/configs/{config_id}", response_model=TtsConfigResponse)
async def update_config(
    config_id: int,
    data: TtsConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 TTS 配置"""
    service = TtsService(db)
    config = await service.update_config(config_id, data)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return config


@router.delete("/configs/{config_id}", response_model=MessageResponse)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除 TTS 配置"""
    service = TtsService(db)
    if not await service.delete_config(config_id):
        raise HTTPException(status_code=404, detail="配置不存在")
    return MessageResponse(message="删除成功")


@router.post("/configs/batch/move", response_model=MessageResponse)
async def batch_move_configs(
    data: TtsConfigBatchMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量移动配置"""
    service = TtsService(db)
    count = await service.batch_move_configs(data.config_ids, data.target_group_id)
    return MessageResponse(message=f"已移动 {count} 个配置")


@router.post("/configs/batch/enable", response_model=MessageResponse)
async def batch_enable_configs(
    data: TtsConfigBatchEnable,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量启用/禁用配置"""
    service = TtsService(db)
    count = await service.batch_enable_configs(data.config_ids, data.is_enabled)
    action = "启用" if data.is_enabled else "禁用"
    return MessageResponse(message=f"已{action} {count} 个配置")


@router.post("/configs/reorder", response_model=MessageResponse)
async def reorder_configs(
    data: TtsReorder,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新排序配置"""
    service = TtsService(db)
    await service.reorder_configs(data.items)
    return MessageResponse(message="排序更新成功")