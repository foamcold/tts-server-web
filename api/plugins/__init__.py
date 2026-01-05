"""
插件系统模块

提供 JavaScript 插件的加载、执行和管理功能。

主要组件：
- PluginEngine: 插件引擎，负责加载和执行 JavaScript 插件
- PluginManager: 插件管理器，管理多个插件实例
- TtsrvRuntime: ttsrv 运行时对象，提供给插件调用的 API
- RhinoCompatLayer: Rhino 语法兼容层
- PluginConfig, PluginVoice, PluginLocale, PluginAudioResult: 类型定义

使用示例：# 方式1：使用 PluginManager（推荐）
    from api.plugins import PluginManager, PluginConfig, get_plugin_manager
    
    manager = get_plugin_manager()  # 获取单例实例
    config = PluginConfig(
        pluginId="my-plugin",
        code="...",  # JavaScript 代码
        userVars={"key": "value"}
    )
    
    manager.register(config)
    result = await manager.synthesize("my-plugin", "你好", "voice1")
    if result.is_success():
        audio_data = result.audio
    
    manager.unregister("my-plugin")
    
    # 方式2：直接使用 PluginEngine
    from api.plugins import PluginEngine, PluginConfig
    
    config = PluginConfig(pluginId="my-plugin", code="...")
    engine = PluginEngine(config)
    engine.load()
    result = await engine.get_audio("你好", "voice1", "zh-CN")
    engine.unload()
"""

# 核心引擎
from .engine import PluginEngine

# 插件管理器
from .js_engine import (
    PluginManager,
    PluginRuntime,
    LegacyPluginEngine,
    get_plugin_manager,
)

# 运行时
from .runtime.ttsrv import TtsrvRuntime

# 类型定义
from .types.plugin import (
    PluginConfig,
    PluginVoice,
    PluginLocale,
    PluginAudioResult,
    PluginMetadata,
    PluginStatus,
    PluginExecutionContext,
    TTSRequest,
    VoiceGender,
)

# 兼容层
from .compat.rhino import RhinoCompatLayer, preprocess_rhino_code

__all__ = [
    # 核心引擎
    'PluginEngine',
    # 插件管理器
    'PluginManager',
    'PluginRuntime',
    'LegacyPluginEngine',
    'get_plugin_manager',
    
    # 运行时
    'TtsrvRuntime',
    
    # 类型定义
    'PluginConfig',
    'PluginVoice',
    'PluginLocale',
    'PluginAudioResult',
    'PluginMetadata',
    'PluginStatus',
    'PluginExecutionContext',
    'TTSRequest',
    'VoiceGender',
    
    # 兼容层
    'RhinoCompatLayer',
    'preprocess_rhino_code',
]