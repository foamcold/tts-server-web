"""
TTS 合成路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.synthesizer import (
    SynthesizeRequest, TextPreviewRequest, AudioFormat
)
from ..services.synthesizer_service import SynthesizerService
from ..services.text_processor import TextProcessor
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/synthesize", tags=["语音合成"])


@router.post("")
async def synthesize(
    request: SynthesizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """合成语音"""
    service = SynthesizerService(db)
    try:
        audio_data = await service.synthesize(request)
        
        # 确定Content-Type
        content_types = {
            AudioFormat.MP3: "audio/mpeg",
            AudioFormat.WAV: "audio/wav",
            AudioFormat.OGG: "audio/ogg",
            AudioFormat.FLAC: "audio/flac",}
        
        return Response(
            content=audio_data,
            media_type=content_types.get(request.format, "audio/mpeg"),
            headers={
                "Content-Disposition": f"attachment; filename=audio.{request.format.value}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


@router.post("/long")
async def synthesize_long_text(
    request: SynthesizeRequest,
    max_segment: int = Query(default=500, ge=100, le=2000, description="最大分段长度"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """合成长文本 (自动分段)"""
    service = SynthesizerService(db)
    try:
        audio_data = await service.synthesize_long_text(
            request.text,
            request.config_id,
            max_segment,)
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=audio.mp3"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


@router.post("/with-rules")
async def synthesize_with_rules(
    request: SynthesizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """使用朗读规则合成 (不同部分可使用不同配置)"""
    service = SynthesizerService(db)
    try:
        audio_data = await service.synthesize_with_rules(
            request.text,
            request.config_id,
        )
        
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=audio.mp3"}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"合成失败: {str(e)}")


@router.post("/preview-text")
async def preview_text(
    request: TextPreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """预览处理后的文本 (应用替换规则)"""
    processor = TextProcessor(db)
    processed = await processor.process_text(
        request.text,
        apply_replace=request.apply_replace_rules,
    )
    return {"original": request.text, "processed": processed}

