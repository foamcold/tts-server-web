"""
插件管理路由

提供插件的CRUD 操作和运行时管理 API。
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.plugin import (
    PluginCreate,
    PluginUpdate,
    PluginResponse,
    PluginImport,
    PluginExport,
    PluginVoicesResponse,
    PluginAudioRequest,
    PluginRuntimeStatus,
    PluginRuntimeStats,PluginLocaleResponse,
    PluginVoiceDetail,
    UserVarsUpdate,
)
from ..schemas.auth import MessageResponse
from ..services.plugin_service import PluginService
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/plugins", tags=["插件管理"])


#==================== CRUD 操作 ====================

@router.get("", response_model=List[PluginResponse])
async def get_plugins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有插件"""
    service = PluginService(db)
    return await service.get_plugins()


@router.get("/enabled", response_model=List[PluginResponse])
async def get_enabled_plugins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取所有启用的插件"""
    service = PluginService(db)
    return await service.get_enabled_plugins()


@router.get("/{plugin_id}", response_model=PluginResponse)
async def get_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取单个插件"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return plugin


@router.post("", response_model=PluginResponse, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    data: PluginCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建插件"""
    service = PluginService(db)
    # 检查插件ID是否已存在
    existing = await service.get_plugin_by_plugin_id(data.plugin_id)
    if existing:
        raise HTTPException(status_code=400, detail="插件ID已存在")
    return await service.create_plugin(data)


@router.put("/{plugin_id}", response_model=PluginResponse)
async def update_plugin(
    plugin_id: int,
    data: PluginUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新插件"""
    service = PluginService(db)
    plugin = await service.update_plugin(plugin_id, data)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    return plugin


@router.delete("/{plugin_id}", response_model=MessageResponse)
async def delete_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除插件"""
    service = PluginService(db)
    if not await service.delete_plugin(plugin_id):
        raise HTTPException(status_code=404, detail="插件不存在")
    return MessageResponse(message="删除成功")


# ==================== 导入导出 ====================

@router.post("/import", response_model=PluginResponse)
async def import_plugin(
    data: PluginImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导入插件 (JSON 格式)"""
    service = PluginService(db)
    try:
        return await service.import_plugin(data.json_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"导入失败: {str(e)}")


@router.get("/{plugin_id}/export", response_model=PluginExport)
async def export_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出插件为 JSON"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    returnPluginExport(json_data=service.export_plugin(plugin))


# ==================== 运行时管理 ====================

@router.get("/runtime/stats", response_model=PluginRuntimeStats)
async def get_runtime_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取插件运行时统计信息"""
    service = PluginService(db)
    return PluginRuntimeStats(
        loaded_count=service.get_loaded_plugin_count(),
        loaded_plugins=service.list_loaded_plugins(),)


@router.get("/{plugin_id}/runtime/status", response_model=PluginRuntimeStatus)
async def get_plugin_runtime_status(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取插件运行时状态"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    return PluginRuntimeStatus(
        plugin_id=plugin.plugin_id,
        is_loaded=service.is_plugin_loaded(plugin.plugin_id),
        name=plugin.name,
    )


@router.post("/{plugin_id}/load", response_model=MessageResponse)
async def load_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """加载插件到运行时"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if await service.load_plugin(plugin_id):
        return MessageResponse(message=f"插件 {plugin.name} 加载成功")
    else:
        raise HTTPException(status_code=400, detail="插件加载失败")


@router.post("/{plugin_id}/unload", response_model=MessageResponse)
async def unload_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """从运行时卸载插件"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if await service.unload_plugin(plugin_id):
        return MessageResponse(message=f"插件 {plugin.name} 已卸载")
    else:
        raise HTTPException(status_code=400, detail="插件卸载失败")


@router.post("/{plugin_id}/reload", response_model=MessageResponse)
async def reload_plugin(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """重新加载插件"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if await service.reload_plugin(plugin_id):
        return MessageResponse(message=f"插件 {plugin.name} 已重新加载")
    else:
        raise HTTPException(status_code=400, detail="插件重新加载失败")


@router.post("/runtime/load-all", response_model=MessageResponse)
async def load_all_plugins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """加载所有启用的插件"""
    service = PluginService(db)
    count = await service.load_all_enabled()
    return MessageResponse(message=f"已加载 {count} 个插件")


@router.post("/runtime/unload-all", response_model=MessageResponse)
async def unload_all_plugins(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """卸载所有插件"""
    service = PluginService(db)
    count = await service.unload_all()
    return MessageResponse(message=f"已卸载 {count} 个插件")


# ==================== 声音/语言列表 ====================

@router.get("/{plugin_id}/voices", response_model=PluginVoicesResponse)
async def get_plugin_voices(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取插件声音列表（兼容旧接口）"""
    service = PluginService(db)
    try:
        return await service.get_plugin_voices(plugin_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{plugin_id}/locales", response_model=List[PluginLocaleResponse])
async def get_plugin_locales(
    plugin_id: int,
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取插件支持的语言列表"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    locales = await service.get_locales(plugin_id, use_cache=use_cache)
    return [PluginLocaleResponse(**loc) for loc in locales]


@router.get("/{plugin_id}/voices/detail", response_model=List[PluginVoiceDetail])
async def get_plugin_voices_detail(
    plugin_id: int,
    locale: str = "",
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取插件声音列表（详细信息）"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    voices = await service.get_voices(plugin_id, locale=locale, use_cache=use_cache)
    return [PluginVoiceDetail(**v) for v in voices]


@router.post("/{plugin_id}/cache/refresh", response_model=MessageResponse)
async def refresh_plugin_cache(
    plugin_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刷新插件的声音/语言缓存"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if await service.refresh_cache(plugin_id):
        return MessageResponse(message="缓存已刷新")
    else:
        raise HTTPException(status_code=400, detail="缓存刷新失败")


# ==================== 用户变量管理 ====================

@router.put("/{plugin_id}/user-vars", response_model=MessageResponse)
async def update_plugin_user_vars(
    plugin_id: int,
    data: UserVarsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新插件的用户变量"""
    service = PluginService(db)
    plugin = await service.get_plugin_by_id(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="插件不存在")
    
    if await service.update_user_vars(plugin_id, data.user_vars):
        return MessageResponse(message="用户变量已更新")
    else:
        raise HTTPException(status_code=400, detail="用户变量更新失败")


# ==================== 语音合成 ====================

@router.post("/{plugin_id}/audio")
async def get_plugin_audio(
    plugin_id: int,
    data: PluginAudioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """通过插件获取音频"""
    service = PluginService(db)
    try:
        audio_data = await service.get_audio(
            plugin_id,
            data.text,
            data.locale,
            data.voice,
            data.speed,
            data.volume,
            data.pitch,
            data.extra_data,
        )
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=audio.mp3"},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/synthesize")
async def synthesize_audio(
    plugin_id: int,
    data: PluginAudioRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    通过插件合成音频（新接口）
    
    返回音频数据和元信息。
    """
    service = PluginService(db)
    result = await service.synthesize(
        plugin_db_id=plugin_id,
        text=data.text,
        voice=data.voice,
        locale=data.locale,
        rate=data.speed,
        pitch=data.pitch,
        volume=data.volume,
        **data.extra_data,
    )
    
    if not result.is_success():
        raise HTTPException(status_code=400, detail=result.error or "合成失败")
    
    return Response(
        content=result.audio,
        media_type=result.contentType,
        headers={
            "Content-Disposition": "attachment; filename=audio.mp3",
            "X-Sample-Rate": str(result.sampleRate),
        },
    )