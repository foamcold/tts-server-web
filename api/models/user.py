"""
用户模型
"""
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="用户名")
    password_hash: Mapped[str] = mapped_column(String(255), comment="密码哈希 (argon2id)")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否激活")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否管理员")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")