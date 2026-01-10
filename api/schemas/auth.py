"""
认证相关 Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token 数据"""
    user_id: int
    username: str


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    is_active: bool
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str


class ApiKeyResponse(BaseModel):
    """API Key 响应"""
    api_key: str = Field(..., description="API 密钥")

    class Config:
        from_attributes = True


class ApiAuthStatusResponse(BaseModel):
    """API 鉴权状态响应"""
    auth_enabled: bool = Field(..., description="是否启用 API 鉴权")
    api_key: str | None = Field(default=None, description="当前用户的 API Key（需登录）")