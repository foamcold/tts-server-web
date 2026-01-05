"""
TTS 合成请求 Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class AudioFormat(str, Enum):
    """音频格式"""
    MP3 = "mp3"
    WAV = "wav"
    OGG = "ogg"
    FLAC = "flac"


class SynthesizeRequest(BaseModel):
    """合成请求"""
    text: str = Field(..., min_length=1, max_length=10000, description="要合成的文本")
    config_id: Optional[int] = Field(None, description="TTS 配置 ID，不传则使用默认配置")
    plugin_id: Optional[int] = Field(None, description="指定插件 ID，优先于配置")
    locale: str = Field(default="zh-CN", description="语言")
    voice: Optional[str] = Field(None, description="声音代码")
    speed: int = Field(default=50, ge=0, le=100, description="语速(0-100)")
    volume: int = Field(default=50, ge=0, le=100, description="音量 (0-100)")
    pitch: int = Field(default=50, ge=0, le=100, description="音调 (0-100)")
    format: AudioFormat = Field(default=AudioFormat.MP3, description="输出格式")
    apply_rules: bool = Field(default=True, description="是否应用替换规则")

class SynthesizeResponse(BaseModel):
    """合成响应 (用于返回信息而非直接音频)"""
    success: bool
    message: str
    audio_url: Optional[str] = None
    duration_ms: Optional[int] = None
    char_count: int = 0


class BatchSynthesizeItem(BaseModel):
    """批量合成项"""
    text: str
    config_id: Optional[int] = None
    voice: Optional[str] = None


class BatchSynthesizeRequest(BaseModel):
    """批量合成请求"""
    items: List[BatchSynthesizeItem] = Field(..., min_length=1, max_length=100)
    format: AudioFormat = Field(default=AudioFormat.MP3)
    apply_rules: bool = Field(default=True)


class TextPreviewRequest(BaseModel):
    """文本预览请求 (应用规则后的文本)"""
    text: str = Field(..., min_length=1)
    apply_replace_rules: bool = Field(default=True)
    apply_speech_rules: bool = Field(default=True)