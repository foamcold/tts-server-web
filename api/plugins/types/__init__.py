"""
插件类型定义模块

提供插件系统中使用的所有数据类型定义
"""

from api.plugins.types.plugin import (
    PluginConfig,
    PluginLocale,
    PluginVoice,
    PluginAudioResult,
    PluginMetadata,
    PluginExecutionContext,
)

__all__ = [
    "PluginConfig",
    "PluginLocale",
    "PluginVoice",
    "PluginAudioResult",
    "PluginMetadata",
    "PluginExecutionContext",
]