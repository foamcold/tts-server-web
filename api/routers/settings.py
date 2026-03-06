"""
系统设置路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.user import User
from ..schemas.settings import (
    ApiAuthSettingsResponse,
    ApiAuthSettingsUpdate,
    CacheSettingsResponse,
    CacheSettingsUpdate,
    UpstreamSettingsResponse,
    UpstreamSettingsUpdate,
)
from ..services.settings_service import SettingsService
from ..utils.deps import get_current_user

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

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以修改系统设置")

    service = SettingsService(db)
    settings = await service.update_cache_settings(
        enabled=data.cache_audio_enabled,
        max_age_days=data.cache_audio_max_age_days,
        max_count=data.cache_audio_max_count,
    )
    return CacheSettingsResponse(**settings)


@router.get("/upstream", response_model=UpstreamSettingsResponse)
async def get_upstream_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取上游连接设置"""

    service = SettingsService(db)
    settings = await service.get_upstream_settings()
    return UpstreamSettingsResponse(**settings)


@router.put("/upstream", response_model=UpstreamSettingsResponse)
async def update_upstream_settings(
    data: UpstreamSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新上游连接设置"""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以修改系统设置")

    service = SettingsService(db)
    settings = await service.update_upstream_settings(
        connection_mode=data.connection_mode,
        timeout_seconds=data.timeout_seconds,
        retry_count=data.retry_count,
    )
    return UpstreamSettingsResponse(**settings)


@router.get("/api-auth", response_model=ApiAuthSettingsResponse)
async def get_api_auth_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取 API 鉴权设置"""

    service = SettingsService(db)
    enabled = await service.get_api_auth_enabled()
    return ApiAuthSettingsResponse(api_auth_enabled=enabled)


@router.put("/api-auth", response_model=ApiAuthSettingsResponse)
async def update_api_auth_settings(
    data: ApiAuthSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新 API 鉴权设置"""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以修改系统设置")

    service = SettingsService(db)
    await service.set_api_auth_enabled(data.api_auth_enabled)
    return ApiAuthSettingsResponse(api_auth_enabled=data.api_auth_enabled)
