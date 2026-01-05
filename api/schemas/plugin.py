"""
插件 Schema
"""
import json
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class PluginBase(BaseModel):
    """插件基础"""
    plugin_id: str = Field(..., min_length=1, max_length=100, description="插件唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="插件名称")
    author: str = Field(default="", max_length=100, description="作者")
    version: int = Field(default=1, ge=1, description="版本号")
    code: str = Field(..., description="JavaScript 代码")
    icon_url: str = Field(default="", description="图标 URL")
    is_enabled: bool = Field(default=True, description="是否启用")
    user_vars: Dict[str, Any] = Field(default_factory=dict, description="用户变量")


class PluginCreate(PluginBase):
    """创建插件"""
    pass


class PluginUpdate(BaseModel):
    """更新插件"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    author: Optional[str] = None
    version: Optional[int] = Field(None, ge=1)
    code: Optional[str] = None
    icon_url: Optional[str] = None
    is_enabled: Optional[bool] = None
    order: Optional[int] = None
    user_vars: Optional[Dict[str, Any]] = None


class PluginResponse(PluginBase):
    """插件响应"""
    id: int
    order: int
    created_at: datetime
    updated_at: datetime

    @field_validator('user_vars', mode='before')
    @classmethod
    def parse_user_vars(cls, v: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """将 JSON 字符串反序列化为字典"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v if v is not None else {}

    class Config:
        from_attributes = True


class PluginImport(BaseModel):
    """导入插件(JSON格式)"""
    json_data: str = Field(..., description="插件 JSON 数据")


class PluginExport(BaseModel):
    """导出插件响应"""
    json_data: str


#============插件执行相关 ============

class PluginVoice(BaseModel):
    """插件声音"""
    code: str = Field(..., description="声音代码")
    name: str = Field(..., description="声音名称")
    icon_url: Optional[str] = Field(None, description="图标 URL")


class PluginVoicesResponse(BaseModel):
    """插件声音列表响应"""
    locales: List[str] = Field(..., description="支持的语言列表")
    voices: Dict[str, List[PluginVoice]] = Field(..., description="声音列表 {locale: voices}")


class PluginAudioRequest(BaseModel):
    """插件音频请求"""
    text: str = Field(..., description="要合成的文本")
    locale: str = Field(default="zh-CN", description="语言")
    voice: str = Field(..., description="声音代码")
    speed: int = Field(default=50, ge=0, le=100, description="语速")
    volume: int = Field(default=50, ge=0, le=100, description="音量")
    pitch: int = Field(default=50, ge=0, le=100, description="音调")
    extra_data: Dict[str, Any] = Field(default_factory=dict, description="扩展数据")


# ============运行时管理相关 ============

class PluginRuntimeStatus(BaseModel):
    """插件运行时状态"""
    plugin_id: str = Field(..., description="插件标识")
    is_loaded: bool = Field(..., description="是否已加载")
    name: str = Field(default="", description="插件名称")


class PluginRuntimeStats(BaseModel):
    """插件运行时统计"""
    loaded_count: int = Field(..., description="已加载插件数量")
    loaded_plugins: List[str] = Field(..., description="已加载的插件ID列表")


class PluginLocaleResponse(BaseModel):
    """语言响应"""
    code: str = Field(..., description="语言代码")
    name: str = Field(..., description="语言名称")


class PluginVoiceDetail(BaseModel):
    """声音详情"""
    id: str = Field(..., description="声音ID")
    name: str = Field(..., description="声音名称")
    locale: str = Field(..., description="语言代码")
    gender: str = Field(default="", description="性别")
    extra: Optional[Dict[str, Any]] = Field(None, description="额外信息")


class UserVarsUpdate(BaseModel):
    """用户变量更新请求"""
    user_vars: Dict[str, Any] = Field(..., description="用户变量")