"""
认证路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    MessageResponse,
    ChangePasswordRequest,
)
from ..services.auth_service import AuthService
from ..utils.auth import create_access_token, verify_password
from ..utils.deps import get_current_user
from ..models.user import User

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=MessageResponse)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """用户注册"""
    auth_service = AuthService(db)
    
    # 检查用户是否已存在
    if await auth_service.user_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 第一个用户设为管理员
    user_count = await auth_service.get_user_count()
    is_admin = user_count == 0
    
    await auth_service.create_user(user_data, is_admin=is_admin)
    
    return MessageResponse(message="注册成功")


@router.post("/login", response_model=Token)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """用户登录"""
    auth_service = AuthService(db)
    
    user = await auth_service.authenticate_user(
        user_data.username,
        user_data.password,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )
    
    # 创建 Token
    access_token = create_access_token(
        data={"user_id": user.id, "username": user.username}
    )
    
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户信息"""
    return current_user


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    auth_service = AuthService(db)
    
    # 验证当前密码
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误",
        )
    
    # 更新密码
    await auth_service.update_password(current_user, data.new_password)
    
    return MessageResponse(message="密码修改成功")