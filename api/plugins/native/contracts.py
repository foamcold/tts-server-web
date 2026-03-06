"""
原生插件协议定义
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from ..types.plugin import PluginAudioResult, PluginConfig, PluginLocale, PluginVoice


@dataclass
class PluginCompileResult:
    """插件编译结果"""

    engine_type: str = "native"
    compile_status: str = "success"
    compile_error: str = ""
    capabilities: Dict[str, Any] = field(default_factory=dict)
    ui_schema: Dict[str, Any] = field(default_factory=dict)
    runtime_meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginRuntimeContext:
    """插件运行上下文"""

    plugin_id: str
    config: PluginConfig
    runtime_meta: Dict[str, Any]
    base_dir: Path

    @property
    def merged_vars(self) -> Dict[str, Any]:
        return self.config.get_merged_vars()


class PluginExecutable(Protocol):
    """原生插件执行器协议"""

    async def load_data(self) -> None:
        ...

    async def get_locales(self) -> List[PluginLocale]:
        ...

    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        ...

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
        ...

    async def on_voice_changed(self, locale: str, voice: str) -> Dict[str, Any]:
        ...

    def get_capabilities(self) -> Dict[str, Any]:
        ...

