"""
原生插件引擎
"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import Any, List, Optional

from .native import PluginRuntimeContext, get_adapter_class
from .types.plugin import PluginAudioResult, PluginConfig, PluginLocale, PluginVoice

logger = logging.getLogger(__name__)


class PluginEngine:
    """原生插件引擎"""

    DEFAULT_TIMEOUT = 30.0

    def __init__(self, plugin_config: PluginConfig):
        self._config = plugin_config
        self._loaded = False
        self._error: Optional[str] = None
        self._adapter = None

    def load(self) -> bool:
        adapter_class = get_adapter_class(self._config.pluginId)
        if adapter_class is None:
            self._error = f"暂不支持的原生插件: {self._config.pluginId}"
            return False
        runtime_meta = copy.deepcopy(getattr(self._config, "runtimeMeta", {}) or {})
        context = PluginRuntimeContext(
            plugin_id=self._config.pluginId,
            config=self._config,
            runtime_meta=runtime_meta,
            base_dir=Path("data") / "plugins" / self._config.pluginId,
        )
        self._adapter = adapter_class(context)
        self._loaded = True
        self._error = None
        return True

    def unload(self) -> None:
        self._loaded = False
        self._adapter = None

    def is_loaded(self) -> bool:
        return self._loaded and self._adapter is not None

    def get_error(self) -> Optional[str]:
        return self._error

    async def get_audio(
        self,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 50,
        pitch: int = 50,
        volume: int = 50,
        **kwargs: Any,
    ) -> PluginAudioResult:
        if not self.is_loaded():
            return PluginAudioResult(error=self._error or "插件未加载")
        try:
            return await self._adapter.synthesize(text, voice, locale, rate, pitch, volume, **kwargs)
        except Exception as exc:
            logger.exception("插件合成失败: %s", self._config.pluginId)
            return PluginAudioResult(error=str(exc))

    async def get_locales(self) -> List[PluginLocale]:
        if not self.is_loaded():
            return []
        await self._adapter.load_data()
        return await self._adapter.get_locales()

    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        if not self.is_loaded():
            return []
        await self._adapter.load_data()
        return await self._adapter.get_voices(locale)

    async def on_voice_changed(self, locale: str, voice: str) -> dict[str, Any]:
        if not self.is_loaded():
            return {}
        return await self._adapter.on_voice_changed(locale, voice)

    def get_capabilities(self) -> dict[str, Any]:
        if not self.is_loaded():
            return {}
        return self._adapter.get_capabilities()
