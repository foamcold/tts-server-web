"""
系统设置路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.settings import CacheSettingsResponse, CacheSettingsUpdate, MessageResponse
from ..services.settings_service import SettingsService
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/settings", tags=["系统设置"])


@router.get("/cache", response_model=CacheSettingsResponse)
async def get_cache_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取缓存设置"""
    service = SettingsService(db)
    settings = await service.get_cache_settings()
    return CacheSettingsResponse(**settings)


@router.put("/cache", response_model=CacheSettingsResponse)
async def update_cache_settings(
    data: CacheSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新缓存设置"""
    # 只有管理员可以修改设置
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以修改系统设置")
    
    service = SettingsService(db)
    settings = await service.update_cache_settings(
        enabled=data.cache_audio_enabled,
        max_age_days=data.cache_audio_max_age_days,
        max_count=data.cache_audio_max_count,
    )
    return CacheSettingsResponse(**settings)
