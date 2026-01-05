"""
替换规则和朗读规则Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


#============替换规则 ============

class ReplaceRuleBase(BaseModel):
    """替换规则基础"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    pattern: str = Field(..., min_length=1, description="匹配模式")
    replacement: str = Field(default="", description="替换内容")
    is_regex: bool = Field(default=False, description="是否为正则表达式")
    is_enabled: bool = Field(default=True, description="是否启用")
    group_id: int = Field(default=0, description="分组 ID")


class ReplaceRuleCreate(ReplaceRuleBase):
    """创建替换规则"""
    pass


class ReplaceRuleUpdate(BaseModel):
    """更新替换规则"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    pattern: Optional[str] = None
    replacement: Optional[str] = None
    is_regex: Optional[bool] = None
    is_enabled: Optional[bool] = None
    order: Optional[int] = None
    group_id: Optional[int] = None


class ReplaceRuleResponse(ReplaceRuleBase):
    """替换规则响应"""
    id: int
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReplaceRuleBatchUpdate(BaseModel):
    """批量更新替换规则"""
    ids: List[int]
    is_enabled: Optional[bool] = None
    group_id: Optional[int] = None


class ReplaceRuleImport(BaseModel):
    """导入替换规则"""
    json_data: str


class ReplaceRuleTest(BaseModel):
    """测试替换规则"""
    text: str = Field(..., min_length=1)
    pattern: str = Field(..., min_length=1)
    replacement: str = Field(default="")
    is_regex: bool = Field(default=False)


class ReplaceRuleTestResponse(BaseModel):
    """测试替换规则响应"""
    original: str
    result: str
    match_count: int


# ============ 朗读规则 ============

class SpeechRuleBase(BaseModel):
    """朗读规则基础"""
    name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    pattern: str = Field(..., min_length=1, description="匹配模式")
    target_config_id: int = Field(..., description="目标TTS 配置 ID")
    is_regex: bool = Field(default=True, description="是否为正则表达式")
    is_enabled: bool = Field(default=True, description="是否启用")


class SpeechRuleCreate(SpeechRuleBase):
    """创建朗读规则"""
    pass


class SpeechRuleUpdate(BaseModel):
    """更新朗读规则"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    pattern: Optional[str] = None
    target_config_id: Optional[int] = None
    is_regex: Optional[bool] = None
    is_enabled: Optional[bool] = None
    order: Optional[int] = None


class SpeechRuleResponse(SpeechRuleBase):
    """朗读规则响应"""
    id: int
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SpeechRuleBatchUpdate(BaseModel):
    """批量更新朗读规则"""
    ids: List[int]
    is_enabled: Optional[bool] = None
    target_config_id: Optional[int] = None