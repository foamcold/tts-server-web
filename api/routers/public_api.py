"""
公开 API 路由
提供 TTS 合成、阅读 APP 兼容、代理等接口
"""
import time
import logging
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

from ..database import get_db
from ..schemas.synthesizer import SynthesizeRequest, AudioFormat
from ..schemas.auth import ApiAuthStatusResponse
from ..services.synthesizer_service import SynthesizerService
from ..services.settings_service import SettingsService
from ..services.auth_service import AuthService
from ..config import config
from ..utils.deps import get_current_user_optional
from ..models.user import User

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter(tags=["公开 API"])


@router.get("/tts")
async def public_tts(
    text: str = Query(..., min_length=1, max_length=1000, description="要合成的文本"),
    voice: str = Query(default="", description="声音代码"),
    speed: int = Query(default=50, ge=0, le=100, description="语速 (0-100)"),
    rate: int = Query(default=None, ge=0, le=100, description="语速别名，同 speed"),
    pitch: int = Query(default=50, ge=0, le=100, description="音调 (0-100)"),
    volume: int = Query(default=50, ge=0, le=100, description="音量 (0-100)"),
    plugin_id: int = Query(default=None, description="插件 ID"),
    config_id: int = Query(default=None, description="TTS 配置 ID"),
    format: str = Query(default="mp3", description="音频格式"),
    api_key: str = Query(default="", description="API 密钥"),
    db: AsyncSession = Depends(get_db),
):
    """
    公开 TTS API (可能需要 API Key，取决于系统设置)
    兼容常见 TTS API 格式，也兼容阅读 Legado 等客户端
    
    参数说明:
    - text: 要合成的文本
    - voice: 声音代码
    - speed/rate: 语速，rate 是 speed 的别名（兼容阅读 APP）
    - pitch: 音调
    - volume: 音量
    - plugin_id: 指定使用的插件 ID
    - config_id: 指定使用的 TTS 配置 ID
    - format: 音频格式 (mp3/wav/ogg/flac)
    - api_key: API 密钥（当系统开启 API 鉴权时必需）
    """
    # 检查是否需要 API Key 验证
    settings_service = SettingsService(db)
    auth_enabled = await settings_service.get_api_auth_enabled()
    
    if auth_enabled:
        # API 鉴权已开启，需要验证 API Key
        if not api_key:
            raise HTTPException(status_code=401, detail="需要提供 API Key")
        
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_api_key(api_key)
        if not user:
            raise HTTPException(status_code=401, detail="无效的 API Key")
    
    service = SynthesizerService(db)
    try:
        # 确定音频格式
        audio_format = AudioFormat.MP3
        if format in ["mp3", "wav", "ogg", "flac"]:
            audio_format = AudioFormat(format)
        
        # rate 是 speed 的别名（兼容阅读 APP 的 speakSpeed 变量）
        actual_speed = rate if rate is not None else speed
        
        # 确定 Content-Type
        content_types = {
            AudioFormat.MP3: "audio/mpeg",
            AudioFormat.WAV: "audio/x-wav",
            AudioFormat.OGG: "audio/ogg",
            AudioFormat.FLAC: "audio/flac",
        }
        
        request = SynthesizeRequest(
            text=text,
            voice=voice if voice else None,
            speed=actual_speed,
            pitch=pitch,
            volume=volume,
            plugin_id=plugin_id,
            config_id=config_id,
            format=audio_format,
        )
        
        audio_data = await service.synthesize(request)
        
        return Response(
            content=audio_data,
            media_type=content_types.get(audio_format, "audio/mpeg"),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/legado")
async def get_legado_config(
    api: str = Query(..., description="TTS API 地址"),
    name: str = Query(..., description="配置显示名称"),
    plugin_id: int = Query(..., description="插件 ID"),
    voice: str = Query(default="", description="声音代码"),
    pitch: str = Query(default="50", description="音调"),
    format: str = Query(default="mp3", description="音频格式 (mp3/wav/ogg)"),
    api_key: str = Query(default="", description="API 密钥（当系统开启 API 鉴权时需要）"),
):
    """
    生成阅读 Legado APP 的 httpTTS 配置 JSON
    
    参考 tts-server-android 的实现：
    - 返回标准的 Legado httpTTS 配置格式
    - URL 中包含阅读 APP 的模板变量
    
    阅读 APP 模板变量说明：
    - {{speakText}}: 要朗读的文本
    - {{speakSpeed}}: 语速 (-50 到 50)
    - {{java.encodeURI(speakText)}}: URL 编码后的文本
    
    rate 计算公式：{{speakSpeed * 2}}
    - speakSpeed 范围: -50 ~ 50
    - 转换后 rate 范围: -100 ~ 100
    - 实际使用时需要在插件中处理负值情况
    """
    current_time = int(time.time() * 1000)
    
    # 根据音频格式确定 contentType
    content_type_map = {
        "mp3": "audio/mpeg",
        "wav": "audio/x-wav",
        "ogg": "audio/ogg",
    }
    content_type = content_type_map.get(format, "audio/mpeg")
    
    # 构建 TTS URL，使用阅读 APP 的模板变量语法
    # 参考: LegadoUtils.kt 第27-28行
    tts_url = f"{api}?plugin_id={plugin_id}&text={{{{java.encodeURI(speakText)}}}}&rate={{{{speakSpeed * 2}}}}&pitch={pitch}&voice={voice}&format={format}"
    
    # 如果提供了 api_key，添加到 URL 中
    if api_key:
        tts_url += f"&api_key={api_key}"
    
    # 返回标准的 Legado httpTTS 配置 JSON
    # 参考: LegadoUtils.kt LegadoJson 数据类
    legado_config = {
        "contentType": content_type,
        "header": "",
        "id": current_time,
        "lastUpdateTime": current_time,
        "name": name,
        "url": tts_url,
        "concurrentRate": "100",
    }
    
    # 调试日志：输出生成的 Legado JSON 配置
    logger.info(f"=== Legado JSON 响应 ===")
    logger.info(f"请求参数: api={api}, name={name}, plugin_id={plugin_id}, voice={voice}, pitch={pitch}, format={format}, api_key={'***' if api_key else ''}")
    logger.info(f"生成的 TTS URL: {tts_url}")
    logger.info(f"完整 JSON: {legado_config}")
    
    return JSONResponse(content=legado_config)


# ============ 通用代理接口 ============

@router.api_route("/proxy/{path:path}", methods=["GET", "POST"])
async def proxy(
    path: str,
    request: Request,
):
    """
    通用代理接口
    用于转发请求到其他服务
    """
    # 安全检查 - 检查是否有配置代理白名单
    proxy_allowed_domains = getattr(config, 'proxy_allowed_domains', None)
    if not proxy_allowed_domains:
        raise HTTPException(status_code=403, detail="代理功能未启用")
    
    # 从路径中提取目标URL
    target_url = path
    if not target_url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="无效的目标 URL")
    
    # 检查域名是否允许
    parsed = urlparse(target_url)
    if parsed.netloc not in proxy_allowed_domains:
        raise HTTPException(status_code=403, detail="目标域名不在允许列表中")
    
    # 转发请求
    async with aiohttp.ClientSession() as session:
        if request.method == "GET":
            async with session.get(target_url, params=dict(request.query_params)) as resp:
                content = await resp.read()
                return Response(
                    content=content,
                    status_code=resp.status,
                    media_type=resp.content_type,
                )
        elif request.method == "POST":
            body = await request.body()
            async with session.post(target_url, data=body) as resp:
                content = await resp.read()
                return Response(
                    content=content,
                    status_code=resp.status,
                    media_type=resp.content_type,
                )
        else:
            raise HTTPException(status_code=405, detail="不支持的请求方法")


# ============ 系统信息接口 ============

@router.get("/info")
async def get_server_info():
    """获取服务器信息"""
    return {
        "name": "TTS Server Web",
        "version": "1.0.0",
        "endpoints": {
            "tts": "/api/tts",
            "legado": "/api/legado",
            "synthesize": "/api/synthesize",
        },
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


@router.get("/auth-status", response_model=ApiAuthStatusResponse)
async def get_auth_status(
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    获取 API 鉴权状态
    
    返回：
    - auth_enabled: 是否开启 API 鉴权
    - api_key: 当前用户的 API Key（仅当用户已登录时返回）
    """
    settings_service = SettingsService(db)
    auth_enabled = await settings_service.get_api_auth_enabled()
    
    api_key = None
    if current_user:
        # 确保用户有 API Key
        auth_service = AuthService(db)
        api_key = await auth_service.ensure_user_has_api_key(current_user)
    
    return ApiAuthStatusResponse(
        auth_enabled=auth_enabled,
        api_key=api_key,
    )
