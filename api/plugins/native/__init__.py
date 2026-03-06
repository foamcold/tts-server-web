"""
原生插件系统
"""

from .compiler import PluginCompiler
from .contracts import PluginCompileResult, PluginExecutable, PluginRuntimeContext
from .registry import get_adapter_class

__all__ = [
    "PluginCompiler",
    "PluginCompileResult",
    "PluginExecutable",
    "PluginRuntimeContext",
    "get_adapter_class",
]
