"""
原生插件注册表
"""

from __future__ import annotations

from .adapters.base import NativePluginAdapter
from .adapters.doubao import DoubaoAdapter
from .adapters.nami import NamiAdapter
from .adapters.xunfei import XunfeiAdapter


ADAPTERS = {
    "xfpeiyin.Mr.Wang": XunfeiAdapter,
    "bot.n.cn": NamiAdapter,
    "doubao.com": DoubaoAdapter,
}


def get_adapter_class(plugin_id: str) -> type[NativePluginAdapter] | None:
    return ADAPTERS.get(plugin_id)

