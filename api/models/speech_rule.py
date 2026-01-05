"""
朗读规则模型
"""
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SpeechRule(Base):
    """朗读规则表"""
    __tablename__ = "speech_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, comment="规则唯一标识")
    name: Mapped[str] = mapped_column(String(100), comment="规则名称")
    author: Mapped[str] = mapped_column(String(100), default="", comment="作者")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")
    
    # JavaScript 代码
    code: Mapped[str] = mapped_column(Text, comment="JavaScript 代码")
    
    # 标签列表
    tags: Mapped[dict] = mapped_column(JSON, default=dict, comment="标签 JSON: {tag: name}")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)