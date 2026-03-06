"""
插件管理器模块
"""

from __future__ import annotations

import logging
import threading
from typing import Dict, List, Optional

from .engine import PluginEngine
from .types.plugin import PluginAudioResult, PluginConfig, PluginLocale, PluginVoice

logger = logging.getLogger(__name__)


class PluginManager:
    """原生插件管理器"""

    _instance: Optional["PluginManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PluginManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._engines: Dict[str, PluginEngine] = {}
        self._configs: Dict[str, PluginConfig] = {}
        self._engine_lock = threading.RLock()
        self._initialized = True

    def register(self, config: PluginConfig) -> bool:
        with self._engine_lock:
            if config.pluginId in self._engines:
                self.unregister(config.pluginId)
            engine = PluginEngine(config)
            if not engine.load():
                logger.error("插件加载失败: %s, %s", config.pluginId, engine.get_error())
                return False
            self._engines[config.pluginId] = engine
            self._configs[config.pluginId] = config
            return True

    def unregister(self, plugin_id: str) -> bool:
        with self._engine_lock:
            engine = self._engines.pop(plugin_id, None)
            self._configs.pop(plugin_id, None)
            if engine is None:
                return False
            engine.unload()
            return True

    def get_engine(self, plugin_id: str) -> Optional[PluginEngine]:
        return self._engines.get(plugin_id)

    def get_config(self, plugin_id: str) -> Optional[PluginConfig]:
        return self._configs.get(plugin_id)

    async def synthesize(
        self,
        plugin_id: str,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 50,
        pitch: int = 50,
        volume: int = 50,
        **kwargs,
    ) -> PluginAudioResult:
        engine = self.get_engine(plugin_id)
        if engine is None:
            return PluginAudioResult(error=f"插件不存在: {plugin_id}")
        return await engine.get_audio(text, voice, locale, rate, pitch, volume, **kwargs)

    async def get_locales(self, plugin_id: str) -> List[PluginLocale]:
        engine = self.get_engine(plugin_id)
        if engine is None:
            return []
        return await engine.get_locales()

    async def get_voices(self, plugin_id: str, locale: str = "") -> List[PluginVoice]:
        engine = self.get_engine(plugin_id)
        if engine is None:
            return []
        return await engine.get_voices(locale)

    def list_plugins(self) -> List[str]:
        return list(self._engines.keys())

    def is_registered(self, plugin_id: str) -> bool:
        return plugin_id in self._engines

    def clear(self) -> int:
        count = len(self._engines)
        for plugin_id in list(self._engines.keys()):
            self.unregister(plugin_id)
        return count


class PluginRuntime:
    """兼容旧命名"""


class LegacyPluginEngine:
    """兼容旧命名"""


def get_plugin_manager() -> PluginManager:
    return PluginManager()
