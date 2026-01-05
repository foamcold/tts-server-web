"""
TTS 配置模型
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Boolean, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .tts_group import TtsGroup


class TtsConfig(Base):
    """TTS 配置表"""
    __tablename__ = "tts_configs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("tts_groups.id"), comment="所属分组 ID")
    
    # 基本信息
    name: Mapped[str] = mapped_column(String(100), comment="配置名称")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    order: Mapped[int] = mapped_column(Integer, default=0, comment="排序顺序")
    
    # TTS 来源类型: plugin, local, http
    source_type: Mapped[str] = mapped_column(String(20), comment="来源类型")
    
    # 插件来源配置
    plugin_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, comment="插件 ID")
    
    # 语音配置
    locale: Mapped[str] = mapped_column(String(20), default="zh-CN", comment="语言区域")
    voice: Mapped[str] = mapped_column(String(100), default="", comment="声音代码")
    voice_name: Mapped[str] = mapped_column(String(100), default="", comment="声音名称")
    
    # 音频参数
    speed: Mapped[int] = mapped_column(Integer, default=50, comment="语速0-100")
    volume: Mapped[int] = mapped_column(Integer, default=50, comment="音量 0-100")
    pitch: Mapped[int] = mapped_column(Integer, default=50, comment="音调 0-100")
    
    # 朗读规则
    speech_rule_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="朗读规则 ID")
    speech_rule_tag: Mapped[str] = mapped_column(String(50), default="", comment="朗读规则标签")
    speech_rule_tag_name: Mapped[str] = mapped_column(String(50), default="", comment="朗读规则标签名称")
    
    # 扩展数据
    extra_data: Mapped[dict] = mapped_column(JSON, default=dict, comment="扩展数据 JSON")
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    group: Mapped["TtsGroup"] = relationship("TtsGroup", back_populates="configs")