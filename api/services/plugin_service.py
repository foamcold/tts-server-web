"""
插件服务
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.plugin import Plugin
from ..plugins import PluginAudioResult, PluginConfig, get_plugin_manager
from ..plugins.native import PluginCompiler
from ..schemas.plugin import PluginCreate, PluginUpdate
from .settings_service import SettingsService
from .upstream_controller import get_upstream_controller

logger = logging.getLogger(__name__)


class PluginService:
    """插件服务类"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._manager = get_plugin_manager()
        self._compiler = PluginCompiler()
        self._settings_service = SettingsService(db)
        self._upstream_controller = get_upstream_controller()

    async def get_plugins(self) -> List[Plugin]:
        result = await self.db.execute(select(Plugin).order_by(Plugin.order))
        return list(result.scalars().all())

    async def get_enabled_plugins(self) -> List[Plugin]:
        result = await self.db.execute(select(Plugin).where(Plugin.is_enabled == True).order_by(Plugin.order))
        return list(result.scalars().all())

    async def get_plugin_by_id(self, plugin_id: int) -> Optional[Plugin]:
        result = await self.db.execute(select(Plugin).where(Plugin.id == plugin_id))
        return result.scalar_one_or_none()

    async def get_plugin_by_plugin_id(self, plugin_id: str) -> Optional[Plugin]:
        result = await self.db.execute(select(Plugin).where(Plugin.plugin_id == plugin_id))
        return result.scalar_one_or_none()

    def _normalize_import_payload(self, raw_json: str) -> Dict[str, Any]:
        payload = json.loads(raw_json)
        if isinstance(payload, list):
            payload = payload[0]
        return payload

    def _compile_plugin_data(self, plugin_data: PluginCreate):
        config = PluginConfig(
            isEnabled=plugin_data.is_enabled,
            version=plugin_data.version,
            name=plugin_data.name,
            pluginId=plugin_data.plugin_id,
            author=plugin_data.author,
            iconUrl=plugin_data.icon_url,
            code=plugin_data.code,
            defVars=getattr(plugin_data, "def_vars", {}) or {},
            userVars=plugin_data.user_vars,
        )
        return self._compiler.compile(config)

    def _apply_compile_result(self, plugin: Plugin, compile_result, raw_json: str, def_vars: Optional[Dict[str, Any]]) -> None:
        plugin.engine_type = compile_result.engine_type
        plugin.compile_status = compile_result.compile_status
        plugin.compile_error = compile_result.compile_error
        plugin.capabilities = compile_result.capabilities
        plugin.ui_schema = compile_result.ui_schema
        plugin.runtime_meta = compile_result.runtime_meta
        plugin.raw_json = raw_json
        plugin.def_vars = def_vars or {}
        plugin.compiled_at = datetime.utcnow() if compile_result.compile_status == "success" else None

    def _build_export_payload(self, plugin: Plugin) -> Dict[str, Any]:
        return {
            "isEnabled": plugin.is_enabled,
            "version": plugin.version,
            "name": plugin.name,
            "pluginId": plugin.plugin_id,
            "author": plugin.author,
            "code": plugin.code,
            "iconUrl": plugin.icon_url,
            "defVars": plugin.def_vars or {},
            "userVars": plugin.user_vars or {},
        }

    async def _sync_upstream_settings(self) -> None:
        """在执行插件请求前同步上游连接设置到控制器"""

        runtime_settings = await self._settings_service.get_upstream_runtime_settings()
        self._upstream_controller.update_settings(runtime_settings)

    async def create_plugin(self, data: PluginCreate, raw_json: Optional[str] = None, def_vars: Optional[Dict[str, Any]] = None) -> Plugin:
        result = await self.db.execute(select(func.max(Plugin.order)))
        max_order = result.scalar() or 0
        plugin = Plugin(
            plugin_id=data.plugin_id,
            name=data.name,
            author=data.author,
            version=data.version,
            code=data.code,
            icon_url=data.icon_url,
            is_enabled=data.is_enabled,
            user_vars=data.user_vars,
            order=max_order + 1,
        )
        compile_result = self._compile_plugin_data(data)
        self._apply_compile_result(plugin, compile_result, raw_json or "", def_vars if def_vars is not None else data.def_vars)
        self.db.add(plugin)
        await self.db.flush()
        await self.db.refresh(plugin)
        if plugin.is_enabled and plugin.compile_status == "success":
            await self.load_plugin(plugin.id)
        return plugin

    async def update_plugin(self, plugin_db_id: int, data: PluginUpdate) -> Optional[Plugin]:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plugin, key, value)
        if {"code", "user_vars", "name", "author", "version", "icon_url", "def_vars"} & set(update_data.keys()):
            plugin_create = PluginCreate(
                plugin_id=plugin.plugin_id,
                name=plugin.name,
                author=plugin.author,
                version=plugin.version,
                code=plugin.code,
                icon_url=plugin.icon_url,
                is_enabled=plugin.is_enabled,
                user_vars=plugin.user_vars or {},
                def_vars=plugin.def_vars or {},
            )
            compile_result = self._compile_plugin_data(plugin_create)
            self._apply_compile_result(plugin, compile_result, plugin.raw_json or "", plugin.def_vars)
        await self.db.flush()
        await self.db.refresh(plugin)
        await self.reload_plugin(plugin.id)
        return plugin

    async def delete_plugin(self, plugin_db_id: int) -> bool:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return False
        await self.unload_plugin(plugin_db_id)
        await self.db.delete(plugin)
        await self.db.flush()
        return True

    async def import_plugin(self, raw_json: str) -> Plugin:
        payload = self._normalize_import_payload(raw_json)
        plugin_data = PluginCreate(
            plugin_id=payload.get("pluginId", ""),
            name=payload.get("name", ""),
            author=payload.get("author", ""),
            version=payload.get("version", 1),
            code=payload.get("code", ""),
            icon_url=payload.get("iconUrl", ""),
            is_enabled=payload.get("isEnabled", True),
            user_vars=payload.get("userVars", {}) or {},
            def_vars=payload.get("defVars", {}) or {},
        )
        existing = await self.get_plugin_by_plugin_id(plugin_data.plugin_id)
        if existing:
            return await self.update_plugin(existing.id, PluginUpdate(**plugin_data.model_dump()))
        return await self.create_plugin(plugin_data, raw_json=raw_json, def_vars=plugin_data.def_vars)

    async def export_plugin(self, plugin_db_id: int) -> Optional[Dict[str, Any]]:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return None
        return self._build_export_payload(plugin)

    def _build_plugin_config(self, plugin: Plugin) -> PluginConfig:
        return PluginConfig(
            isEnabled=plugin.is_enabled,
            version=plugin.version,
            name=plugin.name,
            pluginId=plugin.plugin_id,
            author=plugin.author,
            iconUrl=plugin.icon_url,
            code=plugin.code,
            defVars=plugin.def_vars or {},
            userVars=plugin.user_vars or {},
            runtimeMeta=plugin.runtime_meta or {},
        )

    async def load_plugin(self, plugin_db_id: int) -> bool:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return False
        if plugin.compile_status != "success":
            logger.warning("跳过加载编译失败的插件: %s", plugin.plugin_id)
            return False
        return self._manager.register(self._build_plugin_config(plugin))

    async def unload_plugin(self, plugin_db_id: int) -> bool:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return False
        return self._manager.unregister(plugin.plugin_id)

    async def reload_plugin(self, plugin_db_id: int) -> bool:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return False
        self._manager.unregister(plugin.plugin_id)
        if plugin.is_enabled and plugin.compile_status == "success":
            return await self.load_plugin(plugin_db_id)
        return True

    async def load_all_enabled(self) -> int:
        count = 0
        for plugin in await self.get_enabled_plugins():
            if await self.load_plugin(plugin.id):
                count += 1
        return count

    async def unload_all(self) -> int:
        return self._manager.clear()

    async def synthesize(
        self,
        plugin_db_id: int,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 50,
        pitch: int = 50,
        volume: int = 50,
        **kwargs: Any,
    ) -> PluginAudioResult:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return PluginAudioResult(error="插件不存在")
        if plugin.compile_status != "success":
            return PluginAudioResult(error=plugin.compile_error or "插件尚未编译成功")
        if not self._manager.is_registered(plugin.plugin_id):
            await self.load_plugin(plugin.id)

        await self._sync_upstream_settings()
        return await self._upstream_controller.run(
            plugin.plugin_id,
            "语音合成",
            lambda: self._manager.synthesize(plugin.plugin_id, text, voice, locale, rate, pitch, volume, **kwargs),
        )

    async def get_audio(
        self,
        plugin_db_id: int,
        text: str,
        locale: str,
        voice: str,
        speed: int,
        volume: int,
        pitch: int,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        result = await self.synthesize(plugin_db_id, text, voice, locale, speed, pitch, volume, **(extra_data or {}))
        if not result.is_success():
            raise ValueError(result.error or "合成失败")
        return result.audio or b""

    async def get_locales(self, plugin_db_id: int) -> List[Dict[str, Any]]:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return []
        if not self._manager.is_registered(plugin.plugin_id):
            await self.load_plugin(plugin.id)

        await self._sync_upstream_settings()
        locales = await self._upstream_controller.run(
            plugin.plugin_id,
            "语言列表加载",
            lambda: self._manager.get_locales(plugin.plugin_id),
        )
        return [{"code": item.code, "name": item.name} for item in locales]

    async def get_voices(self, plugin_db_id: int, locale: str = "") -> List[Dict[str, Any]]:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return []
        if not self._manager.is_registered(plugin.plugin_id):
            await self.load_plugin(plugin.id)

        await self._sync_upstream_settings()
        voices = await self._upstream_controller.run(
            plugin.plugin_id,
            "发音人加载",
            lambda: self._manager.get_voices(plugin.plugin_id, locale),
        )
        return [
            {
                "id": voice.id,
                "name": voice.name,
                "locale": voice.locale,
                "gender": voice.gender,
                "extra": voice.extra or {},
            }
            for voice in voices
        ]

    async def get_plugin_voices(self, plugin_db_id: int) -> Dict[str, Any]:
        locales = await self.get_locales(plugin_db_id)
        voices = await self.get_voices(plugin_db_id)
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        all_voices: List[Dict[str, Any]] = []
        for voice in voices:
            item = {
                "code": voice["id"],
                "name": voice["name"],
                "icon_url": voice.get("extra", {}).get("icon_url", ""),
            }
            grouped.setdefault(voice["locale"], []).append(item)
            all_voices.append(item)
        response = {
            "locales": [item["code"] for item in locales],
            "voices": grouped,
            "allVoices": all_voices,
        }
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin:
            response["capabilities"] = plugin.capabilities or {}
            response["ui_schema"] = plugin.ui_schema or {}
        return response

    async def update_user_vars(self, plugin_db_id: int, user_vars: Dict[str, Any]) -> bool:
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if plugin is None:
            return False
        plugin.user_vars = user_vars
        await self.db.flush()
        await self.reload_plugin(plugin_db_id)
        return True

    def is_plugin_loaded(self, plugin_id: str) -> bool:
        return self._manager.is_registered(plugin_id)
