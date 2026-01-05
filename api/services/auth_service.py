"""
认证服务
"""
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..schemas.auth import UserCreate
from ..utils.auth import hash_password, verify_password


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

    async def create_user(self, user_data: UserCreate, is_admin: bool = False) -> User:
        """创建用户"""
        user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            is_admin=is_admin,
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