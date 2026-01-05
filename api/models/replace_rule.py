"""
替换规则模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    pass


class ReplaceRuleGroup(Base):
    """替换规则分组表"""
    __tablename__ = "replace_rule_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="分组名称")
    is_expanded: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否展开")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联的规则
    rules: Mapped[List["ReplaceRule"]] = relationship("ReplaceRule", back_populates="group", cascade="all, delete-orphan")


class ReplaceRule(Base):
    """替换规则表"""
    __tablename__ = "replace_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("replace_rule_groups.id"), comment="所属分组 ID")
    
    name: Mapped[str] = mapped_column(String(100), comment="规则名称")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")
    # 匹配模式: 0=普通文本, 1=正则表达式
    pattern_type: Mapped[int] = mapped_column(Integer, default=0, comment="匹配模式")
    pattern: Mapped[str] = mapped_column(Text, comment="匹配模式")
    replacement: Mapped[str] = mapped_column(Text, default="", comment="替换文本")
    
    # 执行时机: 0=TTS前, 1=TTS后
    execution: Mapped[int] = mapped_column(Integer, default=0, comment="执行时机")
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    group: Mapped["ReplaceRuleGroup"] = relationship("ReplaceRuleGroup", back_populates="rules")