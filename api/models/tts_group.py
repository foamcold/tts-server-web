"""
TTS 配置组模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, List
from sqlalchemy import String, Boolean, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .tts_config import TtsConfig


class TtsGroup(Base):
    """TTS 配置组表"""
    __tablename__ = "tts_groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), comment="分组名称")
    is_expanded: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否展开")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")
    audio_params: Mapped[dict] = mapped_column(JSON, default=dict, comment="音频参数")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联的TTS配置
    configs: Mapped[List["TtsConfig"]] = relationship("TtsConfig", back_populates="group", cascade="all, delete-orphan")