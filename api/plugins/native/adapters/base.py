"""
原生插件适配器基类
"""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from ....services.upstream_controller import get_upstream_controller
from ...types.plugin import PluginAudioResult, PluginLocale, PluginVoice
from ..contracts import PluginRuntimeContext
from ..utils import ensure_dir


class NativePluginAdapter:
    """原生插件适配器基类"""

    def __init__(self, context: PluginRuntimeContext):
        self.context = context
        self.base_dir = ensure_dir(context.base_dir)
        self.cache_dir = ensure_dir(self.base_dir / "cache")

    async def load_data(self) -> None:
        return None

    async def get_locales(self) -> List[PluginLocale]:
        return [PluginLocale(code="zh-CN", name="中文")]

    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        return []

    async def synthesize(
        self,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 50,
        pitch: int = 50,
        volume: int = 50,
        **kwargs: Any,
    ) -> PluginAudioResult:
        return PluginAudioResult(error="插件未实现语音合成")

    async def on_voice_changed(self, locale: str, voice: str) -> Dict[str, Any]:
        return {}

    def get_capabilities(self) -> Dict[str, Any]:
        return self.context.runtime_meta.get("capabilities", {})

    def create_client(self, timeout: float | None = None) -> httpx.AsyncClient:
        controller = get_upstream_controller()
        effective_timeout = timeout or float(controller.get_settings().timeout_seconds)
        return httpx.AsyncClient(timeout=effective_timeout, follow_redirects=True)
