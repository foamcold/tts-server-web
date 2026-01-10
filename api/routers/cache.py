"""
缓存管理路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.cache import CacheStatsResponse, CacheCleanupResponse, CacheClearResponse
from ..services.audio_cache_service import AudioCacheService
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/cache", tags=["缓存管理"])


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取缓存统计信息"""
    service = AudioCacheService(db)
    stats = await service.get_stats()
    return CacheStatsResponse(**stats)


@router.post("/cleanup", response_model=CacheCleanupResponse)
async def cleanup_cache(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手动触发缓存清理"""
    # 只有管理员可以清理缓存
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以清理缓存")
    
    service = AudioCacheService(db)
    result = await service.cleanup()
    return CacheCleanupResponse(**result)


@router.delete("", response_model=CacheClearResponse)
async def clear_cache(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """清空所有缓存"""
    # 只有管理员可以清空缓存
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="只有管理员可以清空缓存")
    
    service = AudioCacheService(db)
    result = await service.clear_all()
    return CacheClearResponse(**result)
