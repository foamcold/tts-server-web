"""
插件兼容层模块

提供与 Android tts-server 项目使用的 Rhino JavaScript 引擎的兼容支持。
主要处理 V8 (py_mini_racer) 与 Rhino 之间的语法差异。
"""

from api.plugins.compat.rhino import (
    RhinoCompatLayer,
    preprocess_rhino_code,
    remove_java_imports,
    convert_java_types,
)

__all__ = [
    "RhinoCompatLayer",
    "preprocess_rhino_code",
    "remove_java_imports",
    "convert_java_types",
]