"""
原生插件编译器
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from ..types.plugin import PluginConfig
from .contracts import PluginCompileResult


class PluginCompiler:
    """将旧插件 JSON 编译为原生运行描述"""

    SUPPORTED_PLUGIN_IDS = {"xfpeiyin.Mr.Wang", "bot.n.cn", "doubao.com"}

    def compile(self, config: PluginConfig) -> PluginCompileResult:
        if config.pluginId not in self.SUPPORTED_PLUGIN_IDS:
            return PluginCompileResult(
                compile_status="failed",
                compile_error=f"当前原生编译器暂不支持插件：{config.pluginId}",
                capabilities={"supports_import": False},
            )

        handlers = {
            "xfpeiyin.Mr.Wang": self._compile_xunfei,
            "bot.n.cn": self._compile_nami,
            "doubao.com": self._compile_doubao,
        }
        return handlers[config.pluginId](config)

    def _base_capabilities(self, plugin_kind: str, required_vars: List[str], extra_fields: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        capabilities = {
            "plugin_kind": plugin_kind,
            "supports_synthesis": True,
            "supports_voices": True,
            "supports_locales": True,
            "required_user_vars": required_vars,
            "extra_fields": [field["key"] for field in extra_fields],
        }
        ui_schema = {
            "sections": [
                {
                    "key": "user_vars",
                    "title": "插件参数",
                    "fields": extra_fields,
                }
            ]
        }
        return capabilities, ui_schema

    def _compile_xunfei(self, config: PluginConfig) -> PluginCompileResult:
        voices = self._parse_simple_voice_map(config.code)
        special_symbols_map = self._parse_special_symbols_map(config.code)
        fields = [
            {"key": "customVoice", "label": "自定义声音代号", "type": "text", "required": False},
            {"key": "emoValue", "label": "情绪强度", "type": "number", "default": 0, "required": False},
            {"key": "soundEffect", "label": "音效代码", "type": "text", "required": False},
        ]
        capabilities, ui_schema = self._base_capabilities("xunfei", [], fields)
        return PluginCompileResult(
            capabilities=capabilities,
            ui_schema=ui_schema,
            runtime_meta={
                "voices": voices,
                "special_symbols_map": special_symbols_map,
                "capabilities": capabilities,
            },
        )

    def _compile_nami(self, config: PluginConfig) -> PluginCompileResult:
        capabilities, ui_schema = self._base_capabilities("nami", [], [])
        return PluginCompileResult(capabilities=capabilities, ui_schema=ui_schema, runtime_meta={"capabilities": capabilities})

    def _compile_doubao(self, config: PluginConfig) -> PluginCompileResult:
        fields = [
            {"key": "cookie", "label": "豆包 Cookie", "type": "textarea", "required": True},
            {"key": "bv", "label": "自定义 BV 号", "type": "text", "required": False},
        ]
        capabilities, ui_schema = self._base_capabilities("doubao", ["cookie"], fields)
        return PluginCompileResult(capabilities=capabilities, ui_schema=ui_schema, runtime_meta={"capabilities": capabilities})

    def _parse_simple_voice_map(self, code: str) -> List[Dict[str, str]]:
        pattern = re.compile(r"'(?P<code>[^']+)':\s*'(?P<name>[^']+)'")
        results: List[Dict[str, str]] = []
        for match in pattern.finditer(code):
            voice_code = match.group("code")
            voice_name = match.group("name")
            if voice_code in {"name", "id", "author", "description", "version"}:
                continue
            if voice_code.startswith("http"):
                continue
            if re.fullmatch(r"\d+(?:_\d+)?|custom", voice_code):
                results.append({"code": voice_code, "name": voice_name})
        deduped: List[Dict[str, str]] = []
        seen = set()
        for item in results:
            if item["code"] in seen:
                continue
            deduped.append(item)
            seen.add(item["code"])
        return deduped

    def _parse_special_symbols_map(self, code: str) -> Dict[str, str]:
        match = re.search(r"specialSymbolsMap'\s*:\s*\{(?P<body>[\s\S]*?)\}\s*,", code)
        if not match:
            return {}
        body = match.group("body")
        result: Dict[str, str] = {}
        for key, value in re.findall(r"'([^']+)':\s*'([^']+)'", body):
            result[key] = value
        return result
