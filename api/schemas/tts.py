"""
TTS 配置 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


#============ TTS 配置组============

class TtsGroupBase(BaseModel):
    """TTS 分组基础"""
    name: str = Field(..., min_length=1, max_length=100, description="分组名称")
    is_expanded: bool = Field(default=True, description="是否展开")
    audio_params: Dict[str, Any] = Field(default_factory=dict, description="音频参数")


class TtsGroupCreate(TtsGroupBase):
    """创建 TTS 分组"""
    pass


class TtsGroupUpdate(BaseModel):
    """更新 TTS 分组"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_expanded: Optional[bool] = None
    order: Optional[int] = None
    audio_params: Optional[Dict[str, Any]] = None


class TtsGroupResponse(TtsGroupBase):
    """TTS 分组响应"""
    id: int
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ TTS 配置 ============

class TtsConfigBase(BaseModel):
    """TTS 配置基础"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    is_enabled: bool = Field(default=True, description="是否启用")
    source_type: str = Field(..., description="来源类型: plugin, local, http")
    plugin_id: Optional[str] = Field(None, description="插件 ID")
    locale: str = Field(default="zh-CN", description="语言区域")
    voice: str = Field(default="", description="声音代码")
    voice_name: str = Field(default="", description="声音名称")
    speed: int = Field(default=50, ge=0, le=100, description="语速")
    volume: int = Field(default=50, ge=0, le=100, description="音量")
    pitch: int = Field(default=50, ge=0, le=100, description="音调")
    apply_rules: bool = Field(default=True, description="是否应用替换规则")
    audio_format: str = Field(default="mp3", description="音频格式: mp3, wav, ogg")
    speech_rule_id: Optional[int] = Field(None, description="朗读规则 ID")
    speech_rule_tag: str = Field(default="", description="朗读规则标签")
    speech_rule_tag_name: str = Field(default="", description="朗读规则标签名称")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")


class TtsConfigCreate(TtsConfigBase):
    """创建 TTS 配置"""
    group_id: int = Field(..., description="所属分组 ID")


class TtsConfigUpdate(BaseModel):
    """更新 TTS 配置"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_enabled: Optional[bool] = None
    order: Optional[int] = None
    group_id: Optional[int] = None
    source_type: Optional[str] = None
    plugin_id: Optional[str] = None
    locale: Optional[str] = None
    voice: Optional[str] = None
    voice_name: Optional[str] = None
    speed: Optional[int] = Field(None, ge=0, le=100)
    volume: Optional[int] = Field(None, ge=0, le=100)
    pitch: Optional[int] = Field(None, ge=0, le=100)
    apply_rules: Optional[bool] = None
    audio_format: Optional[str] = None
    speech_rule_id: Optional[int] = None
    speech_rule_tag: Optional[str] = None
    speech_rule_tag_name: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None


class TtsConfigResponse(TtsConfigBase):
    """TTS 配置响应"""
    id: int
    group_id: int
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ 分组带配置列表 ============

class TtsGroupWithConfigs(TtsGroupResponse):
    """TTS 分组及其配置列表"""
    configs: List[TtsConfigResponse] = []


# ============ 批量操作 ============

class TtsConfigBatchMove(BaseModel):
    """批量移动配置"""
    config_ids: List[int] = Field(..., description="配置 ID 列表")
    target_group_id: int = Field(..., description="目标分组 ID")


class TtsConfigBatchEnable(BaseModel):
    """批量启用/禁用配置"""
    config_ids: List[int] = Field(..., description="配置 ID 列表")
    is_enabled: bool = Field(..., description="是否启用")


class ReorderItem(BaseModel):
    """排序项"""
    id: int
    order: int


class TtsReorder(BaseModel):
    """重新排序请求"""
    items: List[ReorderItem]