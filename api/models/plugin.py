"""
插件模型
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import String, Boolean, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Plugin(Base):
    """插件表"""
    __tablename__ = "plugins"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plugin_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="插件唯一标识")
    name: Mapped[str] = mapped_column(String(100), comment="插件名称")
    author: Mapped[str] = mapped_column(String(100), default="", comment="作者")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    code: Mapped[str] = mapped_column(Text, comment="JavaScript代码")
    icon_url: Mapped[str] = mapped_column(String(500), default="", comment="图标 URL")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")
    
    # 插件变量
    def_vars: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None, comment="插件默认变量"
    )
    user_vars: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, default=None, comment="用户自定义变量"
    )
    
    # 注意：缓存字段已迁移到前端浏览器，使用 React Query 内存缓存
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
