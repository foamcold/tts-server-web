"""
认证服务
"""
import hashlib
import secrets
import base64
from datetime import datetime
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..schemas.auth import UserCreate
from ..utils.auth import hash_password, verify_password


def generate_api_key(username: str, password_hash: str, created_at: datetime) -> str:
    """
    基于用户信息生成 API Key
    
    算法：将用户名、密码哈希、创建时间戳和随机盐组合后，
    使用 SHA256 生成确定性但难以预测的密钥
    
    Args:
        username: 用户名
        password_hash: 密码哈希
        created_at: 创建时间
        
    Returns:
        格式为 tts-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx 的 API Key
    """
    # 添加随机盐增加不可预测性
    salt = secrets.token_hex(16)
    
    # 组合原始数据
    raw_data = f"{username}:{password_hash}:{created_at.isoformat()}:{salt}"
    
    # 生成 SHA256 哈希
    hash_bytes = hashlib.sha256(raw_data.encode()).digest()
    
    # 转换为 URL 安全的 Base64 编码，取前32个字符
    api_key = base64.urlsafe_b64encode(hash_bytes).decode()[:32]
    
    # 添加前缀便于识别
    return f"tts-{api_key}"


class AuthService:
    """认证服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """通过ID 获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """
        通过 API Key 获取用户
        
        Args:
            api_key: API 密钥
            
        Returns:
            用户对象，不存在则返回 None
        """
        stmt = select(User).where(User.api_key == api_key, User.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate, is_admin: bool = False) -> User:
        """
        创建用户
        
        用户创建时自动生成 API Key
        """
        password_hash = hash_password(user_data.password)
        created_at = datetime.utcnow()
        
        # 生成 API Key
        api_key = generate_api_key(user_data.username, password_hash, created_at)
        
        user = User(
            username=user_data.username,
            password_hash=password_hash,
            api_key=api_key,
            is_admin=is_admin,
            created_at=created_at,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """验证用户"""
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def user_exists(self, username: str) -> bool:
        """检查用户是否存在"""
        user = await self.get_user_by_username(username)
        return user is not None

    async def get_user_count(self) -> int:
        """获取用户总数"""
        stmt = select(func.count(User.id))
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def update_password(self, user: User, new_password: str) -> User:
        """更新用户密码"""
        user.password_hash = hash_password(new_password)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def regenerate_api_key(self, user: User) -> str:
        """
        重新生成用户的 API Key
        
        Args:
            user: 用户对象
            
        Returns:
            新的 API Key
        """
        # 使用当前时间作为新的时间戳来生成不同的 key
        new_api_key = generate_api_key(
            user.username,
            user.password_hash,
            datetime.utcnow()
        )
        user.api_key = new_api_key
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return new_api_key

    async def validate_api_key(self, api_key: str) -> bool:
        """
        验证 API Key 是否有效
        
        Args:
            api_key: API 密钥
            
        Returns:
            是否有效
        """
        user = await self.get_user_by_api_key(api_key)
        return user is not None

    async def ensure_user_has_api_key(self, user: User) -> str:
        """
        确保用户有 API Key，如果没有则生成一个
        
        Args:
            user: 用户对象
            
        Returns:
            用户的 API Key
        """
        if not user.api_key:
            return await self.regenerate_api_key(user)
        return user.api_key