"""
数据库模型索引
"""
from .user import User
from .plugin import Plugin
from .tts_group import TtsGroup
from .tts_config import TtsConfig
from .replace_rule import ReplaceRuleGroup, ReplaceRule
from .speech_rule import SpeechRule
from .audio_cache import AudioCache
from .system_settings import SystemSettings, SettingsKeys, DEFAULT_SETTINGS

__all__ = [
    "User",
    "Plugin",
    "TtsGroup",
    "TtsConfig",
    "ReplaceRuleGroup",
    "ReplaceRule",
    "SpeechRule",
    "AudioCache",
    "SystemSettings",
    "SettingsKeys",
    "DEFAULT_SETTINGS",
]