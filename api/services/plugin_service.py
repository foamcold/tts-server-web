"""
插件服务

管理插件的CRUD 操作和运行时管理。
集成 PluginManager 和 PluginEngine 实现语音合成功能。
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.plugin import Plugin
from ..schemas.plugin import PluginCreate, PluginUpdate
from ..plugins import (
    PluginManager,
    PluginConfig,
    PluginAudioResult,
    PluginVoice,
    PluginLocale,
    get_plugin_manager,
)

logger = logging.getLogger(__name__)

# 默认缓存有效期（秒）
# 设置为 0 禁用缓存，每次请求都从插件引擎获取最新的声音列表
DEFAULT_CACHE_TTL = 0


class PluginService:
    """
    插件服务类
    提供插件的 CRUD 操作和运行时管理功能，包括：
    - 插件的增删改查
    - 插件的加载/卸载
    - 语音合成
    - 声音/语言列表（带缓存）
    """

    def __init__(self, db: AsyncSession):
        """
        初始化插件服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self._manager = get_plugin_manager()
        self._cache_ttl = DEFAULT_CACHE_TTL

    #==================== CRUD 操作 ====================

    async def get_plugins(self) -> List[Plugin]:
        """获取所有插件"""
        stmt = select(Plugin).order_by(Plugin.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_enabled_plugins(self) -> List[Plugin]:
        """获取所有启用的插件"""
        stmt = select(Plugin).where(Plugin.is_enabled == True).order_by(Plugin.order)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_plugin_by_id(self, plugin_id: int) -> Optional[Plugin]:
        """通过数据库 ID 获取插件"""
        stmt = select(Plugin).where(Plugin.id == plugin_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_plugin_by_plugin_id(self, plugin_id: str) -> Optional[Plugin]:
        """通过插件标识获取插件"""
        stmt = select(Plugin).where(Plugin.plugin_id == plugin_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_plugin(self, data: PluginCreate) -> Plugin:
        """创建插件"""
        # 获取最大排序值
        stmt = select(func.max(Plugin.order))
        result = await self.db.execute(stmt)
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
        self.db.add(plugin)
        await self.db.flush()
        await self.db.refresh(plugin)
        return plugin

    async def update_plugin(self, plugin_db_id: int, data: PluginUpdate) -> Optional[Plugin]:
        """更新插件"""
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plugin, key, value)
        
        # 如果更新了代码或用户变量，需要重新加载插件
        if 'code' in update_data or 'user_vars' in update_data:
            # 清除缓存
            plugin.cached_locales = None
            plugin.cached_voices = None
            plugin.last_cache_time = None
            # 重新加载插件
            await self.reload_plugin(plugin_db_id)
        
        await self.db.flush()
        await self.db.refresh(plugin)
        return plugin

    async def delete_plugin(self, plugin_db_id: int) -> bool:
        """删除插件"""
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return False
        
        # 先卸载插件
        await self.unload_plugin(plugin_db_id)
        
        await self.db.delete(plugin)
        return True

    async def import_plugin(self, json_data: str) -> Plugin:
        """从 JSON 导入插件"""
        data = json.loads(json_data)
        
        # 处理数组格式
        if isinstance(data, list):
            data = data[0]
        
        plugin_data = PluginCreate(
            plugin_id=data.get('pluginId', data.get('id', '')),
            name=data.get('name', ''),
            author=data.get('author', ''),
            version=data.get('version',1),
            code=data.get('code', ''),
            icon_url=data.get('iconUrl', ''),
            is_enabled=data.get('isEnabled', True),
            user_vars=data.get('userVars', {}),)
        
        # 检查是否已存在
        existing = await self.get_plugin_by_plugin_id(plugin_data.plugin_id)
        if existing:
            # 更新现有插件
            return await self.update_plugin(existing.id, PluginUpdate(
                name=plugin_data.name,
                author=plugin_data.author,
                version=plugin_data.version,
                code=plugin_data.code,
                icon_url=plugin_data.icon_url,
            ))
        
        return await self.create_plugin(plugin_data)

    def export_plugin(self, plugin: Plugin) -> str:
        """导出插件为 JSON"""
        return json.dumps([{
            'isEnabled': plugin.is_enabled,
            'version': plugin.version,
            'name': plugin.name,
            'pluginId': plugin.plugin_id,
            'author': plugin.author,
            'iconUrl': plugin.icon_url,
            'code': plugin.code,
            'userVars': plugin.user_vars or {},
        }], ensure_ascii=False, indent=2)

    # ==================== 运行时管理 ====================

    async def load_plugin(self, plugin_db_id: int) -> bool:
        """
        加载插件到运行时
        
        Args:
            plugin_db_id: 插件数据库 ID
            
        Returns:
            加载成功返回 True，否则返回 False
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            logger.warning(f"加载失败，插件不存在: db_id={plugin_db_id}")
            return False
        
        if not plugin.is_enabled:
            logger.warning(f"加载失败，插件未启用: {plugin.plugin_id}")
            return False
        
        config = self._to_plugin_config(plugin)
        result = self._manager.register(config)
        
        if result:
            logger.info(f"插件加载成功: {plugin.plugin_id}")
        else:
            logger.error(f"插件加载失败: {plugin.plugin_id}")
        
        return result

    async def unload_plugin(self, plugin_db_id: int) -> bool:
        """
        从运行时卸载插件
        
        Args:
            plugin_db_id: 插件数据库 ID
            
        Returns:
            卸载成功返回 True，否则返回 False
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return False
        
        result = self._manager.unregister(plugin.plugin_id)
        
        if result:
            logger.info(f"插件卸载成功: {plugin.plugin_id}")
        return result

    async def reload_plugin(self, plugin_db_id: int) -> bool:
        """
        重新加载插件
        
        Args:
            plugin_db_id: 插件数据库 ID
            
        Returns:
            重新加载成功返回 True
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return False
        
        # 先卸载（如果已加载）
        if self._manager.is_registered(plugin.plugin_id):
            self._manager.unregister(plugin.plugin_id)
        
        # 如果插件启用，重新加载
        if plugin.is_enabled:
            return await self.load_plugin(plugin_db_id)
        
        return True

    async def ensure_plugin_loaded(self, plugin_db_id: int) -> bool:
        """
        确保插件已加载
        
        如果插件未加载，则自动加载。
        
        Args:
            plugin_db_id: 插件数据库 ID
            
        Returns:
            插件已加载或加载成功返回 True
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return False
        
        if not self._manager.is_registered(plugin.plugin_id):
            return await self.load_plugin(plugin_db_id)
        
        return True

    # ==================== 语音合成 ====================

    async def synthesize(self,
        plugin_db_id: int,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 0,
        pitch: int = 0,
        volume: int = 0,
        **kwargs
    ) -> PluginAudioResult:
        """
        使用指定插件合成音频
        
        Args:
            plugin_db_id: 插件数据库 ID
            text: 要合成的文本
            voice: 声音 ID
            locale: 语言区域代码，默认 "zh-CN"
            rate: 语速（-100 到 100），0 为默认
            pitch: 音调（-100 到 100），0 为默认
            volume: 音量（0 到 100），0 为默认
            **kwargs: 其他参数
            
        Returns:PluginAudioResult 对象，包含音频数据或错误信息
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return PluginAudioResult(error="插件不存在")
        
        if not plugin.is_enabled:
            return PluginAudioResult(error="插件未启用")
        
        # 确保插件已加载
        if not await self.ensure_plugin_loaded(plugin_db_id):
            return PluginAudioResult(error="插件加载失败")
        
        # 执行合成
        logger.debug(f"[DEBUG] PluginService.synthesize 开始调用_manager.synthesize")
        logger.debug(f"[DEBUG] 参数: plugin_id={plugin.plugin_id}, text_len={len(text)}, voice={voice}, locale={locale}")
        
        result = await self._manager.synthesize(
            plugin.plugin_id,
            text,
            voice,
            locale=locale,
            rate=rate,
            pitch=pitch,
            volume=volume,
            **kwargs
        )
        
        logger.debug(f"[DEBUG] PluginService.synthesize 结果: is_success={result.is_success()}, error={result.error}")
        if result.is_success():
            logger.debug(f"[DEBUG] 音频大小: {len(result.audio) if result.audio else 0} 字节")
        
        return result

    async def get_audio(
        self,
        plugin_db_id: int,
        text: str,
        locale: str,
        voice: str,
        speed: int,
        volume: int,
        pitch: int,
        extra_data: Dict = None
    ) -> bytes:
        """
        通过插件获取音频（兼容旧接口）
        
        Args:
            plugin_db_id: 插件数据库 ID
            text: 要合成的文本
            locale: 语言区域代码
            voice: 声音 ID
            speed: 语速
            volume: 音量
            pitch: 音调
            extra_data: 额外数据
            
        Returns:
            音频二进制数据
        Raises:
            ValueError: 插件不存在、未启用或合成失败
        """
        logger.debug(f"[DEBUG] PluginService.get_audio 开始: plugin_db_id={plugin_db_id}, text_len={len(text)}, voice={voice}")
        
        result = await self.synthesize(
            plugin_db_id=plugin_db_id,
            text=text,
            voice=voice,
            locale=locale,
            rate=speed,
            pitch=pitch,
            volume=volume,
            **(extra_data or {})
        )
        
        logger.debug(f"[DEBUG] PluginService.get_audio 结果: is_success={result.is_success()}, error={result.error}")
        
        if not result.is_success():
            logger.error(f"[DEBUG] PluginService.get_audio 失败: {result.error}")
            raise ValueError(result.error or "音频合成失败")
        
        logger.debug(f"[DEBUG] PluginService.get_audio 成功: 音频大小={len(result.audio)} 字节")
        return result.audio

    # ==================== 声音/语言列表（带缓存） ====================

    async def get_voices(
        self,
        plugin_db_id: int,
        locale: str = "",
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取插件支持的声音列表（带缓存）
        
        Args:
            plugin_db_id: 插件数据库 ID
            locale: 语言区域代码，为空获取所有声音
            use_cache: 是否使用缓存
            
        Returns:
            声音列表，每个元素包含 id、name、locale 等字段
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            logger.warning(f"获取声音列表失败，插件不存在: {plugin_db_id}")
            return []
        
        # 检查缓存是否有效
        if use_cache and self._is_cache_valid(plugin):
            voices = plugin.cached_voices or []
            if locale:
                voices = [v for v in voices if v.get('locale') == locale]
            logger.debug(f"使用缓存的声音列表: {plugin.plugin_id}")
            return voices
        
        # 确保插件已加载
        if not await self.ensure_plugin_loaded(plugin_db_id):
            return []
        
        # 获取声音列表
        voices = await self._manager.get_voices(plugin.plugin_id, locale)
        voice_dicts = [
            {
                'id': v.id,
                'name': v.name,
                'locale': v.locale,
                'gender': v.gender,
                'extra': v.extra,
            }
            for v in voices
        ]
        
        # 如果没有指定 locale，更新缓存
        if not locale:
            await self._update_voices_cache(plugin, voice_dicts)
        
        return voice_dicts

    async def get_locales(
        self,
        plugin_db_id: int,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取插件支持的语言列表（带缓存）
        
        Args:
            plugin_db_id: 插件数据库 ID
            use_cache: 是否使用缓存
            
        Returns:
            语言列表，每个元素包含 code、name 字段
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            logger.warning(f"获取语言列表失败，插件不存在: {plugin_db_id}")
            return []
        
        # 检查缓存是否有效
        if use_cache and self._is_cache_valid(plugin) and plugin.cached_locales:
            logger.debug(f"使用缓存的语言列表: {plugin.plugin_id}")
            return plugin.cached_locales
        
        # 确保插件已加载
        if not await self.ensure_plugin_loaded(plugin_db_id):
            return []
        
        # 获取语言列表
        locales = await self._manager.get_locales(plugin.plugin_id)
        locale_dicts = [
            {
                'code': loc.code,
                'name': loc.name,
            }
            for loc in locales
        ]
        
        # 更新缓存
        await self._update_locales_cache(plugin, locale_dicts)
        
        return locale_dicts

    async def get_plugin_voices(self, plugin_db_id: int) -> Dict[str, Any]:
        """
        获取插件声音列表（兼容旧接口）
        
        返回格式与旧版接口兼容，包含 locales 和 voices 字段。
        
        Args:
            plugin_db_id: 插件数据库 ID
            
        Returns:
            包含 locales 和 voices 的字典
            
        Raises:
            ValueError: 插件不存在
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            raise ValueError("插件不存在")
        
        logger.info(f"获取插件声音列表: plugin_id={plugin_db_id}, plugin_name={plugin.name}")
        
        # 获取语言列表
        locales = await self.get_locales(plugin_db_id)
        locale_codes = [loc['code'] for loc in locales]
        
        # 获取每个语言的声音列表
        voices = {}
        for locale_code in locale_codes:
            locale_voices = await self.get_voices(plugin_db_id, locale=locale_code)
            voices[locale_code] = [
                {'code': v['id'], 'name': v['name']}
                for v in locale_voices
            ]
        
        # 记录调试日志：每个语言下有多少个发音人
        voice_counts = {lang: len(v_list) for lang, v_list in voices.items()}
        logger.info(f"成功获取所有声音列表: {len(locale_codes)} 个语言, 详情: {voice_counts}")
        
        return {'locales': locale_codes, 'voices': voices}

    async def refresh_cache(self, plugin_db_id: int) -> bool:
        """
        刷新插件的声音/语言缓存
        
        Args:
            plugin_db_id: 插件数据库 ID
            
        Returns:刷新成功返回 True
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return False
        
        # 清除缓存
        plugin.cached_locales = None
        plugin.cached_voices = None
        plugin.last_cache_time = None
        
        await self.db.flush()
        
        # 重新获取（不使用缓存）
        await self.get_locales(plugin_db_id, use_cache=False)
        await self.get_voices(plugin_db_id, use_cache=False)
        
        logger.info(f"已刷新插件缓存: {plugin.plugin_id}")
        return True

    # ==================== 用户变量管理 ====================

    async def update_user_vars(
        self,
        plugin_db_id: int,
        user_vars: Dict[str, Any]
    ) -> bool:
        """
        更新插件的用户变量
        
        Args:
            plugin_db_id: 插件数据库 ID
            user_vars: 用户变量字典
            
        Returns:
            更新成功返回 True
        """
        plugin = await self.get_plugin_by_id(plugin_db_id)
        if not plugin:
            return False
        
        plugin.user_vars = user_vars
        
        # 如果插件已加载，需要重新加载以应用新变量
        if self._manager.is_registered(plugin.plugin_id):
            await self.reload_plugin(plugin_db_id)
        
        await self.db.flush()
        logger.info(f"已更新插件用户变量: {plugin.plugin_id}")
        return True

    # ==================== 批量操作 ====================

    async def load_all_enabled(self) -> int:
        """
        加载所有启用的插件
        
        Returns:
            成功加载的插件数量
        """
        plugins = await self.get_enabled_plugins()
        count = 0
        
        for plugin in plugins:
            try:
                if await self.load_plugin(plugin.id):
                    count += 1
            except Exception as e:
                logger.error(f"加载插件失败: {plugin.plugin_id},错误: {e}")
        
        logger.info(f"批量加载插件完成，共{count}/{len(plugins)} 个")
        return count

    async def unload_all(self) -> int:
        """
        卸载所有插件
        
        Returns:
            卸载的插件数量
        """
        count = self._manager.unregister_all()
        logger.info(f"批量卸载插件完成，共 {count} 个")
        return count

    # ==================== 状态查询 ====================

    def is_plugin_loaded(self, plugin_id: str) -> bool:
        """
        检查插件是否已加载
        
        Args:
            plugin_id: 插件标识符（不是数据库 ID）
            
        Returns:
            已加载返回 True
        """
        return self._manager.is_registered(plugin_id)

    def get_loaded_plugin_count(self) -> int:
        """
        获取已加载的插件数量
        
        Returns:
            已加载的插件数量
        """
        return self._manager.get_plugin_count()

    def list_loaded_plugins(self) -> List[str]:
        """
        列出所有已加载的插件 ID
        
        Returns:
            插件 ID 列表
        """
        return self._manager.list_plugins()

    # ==================== 私有方法 ====================

    def _to_plugin_config(self, plugin: Plugin) -> PluginConfig:
        """
        将数据库模型转换为 PluginConfig
        
        Args:
            plugin: 插件数据库模型
            
        Returns:
            PluginConfig 配置对象
        """
        return PluginConfig(
            isEnabled=plugin.is_enabled,
            version=plugin.version,
            name=plugin.name,
            pluginId=plugin.plugin_id,
            author=plugin.author,
            iconUrl=plugin.icon_url or "",
            code=plugin.code,
            defVars=plugin.def_vars,
            userVars=plugin.user_vars,
        )

    def _is_cache_valid(self, plugin: Plugin) -> bool:
        """
        检查插件缓存是否有效
        
        Args:
            plugin: 插件数据库模型
            
        Returns:
            缓存有效返回 True
        """
        if not plugin.last_cache_time:
            return False
        
        cache_age = datetime.utcnow() - plugin.last_cache_time
        return cache_age.total_seconds() < self._cache_ttl

    async def _update_locales_cache(
        self,
        plugin: Plugin,
        locales: List[Dict[str, Any]]
    ) -> None:
        """
        更新语言列表缓存
        
        Args:
            plugin: 插件数据库模型
            locales: 语言列表
        """
        plugin.cached_locales = locales
        plugin.last_cache_time = datetime.utcnow()
        await self.db.flush()
        logger.debug(f"已更新语言缓存: {plugin.plugin_id}")

    async def _update_voices_cache(
        self,
        plugin: Plugin,
        voices: List[Dict[str, Any]]
    ) -> None:
        """
        更新声音列表缓存
        
        Args:
            plugin: 插件数据库模型
            voices: 声音列表
        """
        plugin.cached_voices = voices
        plugin.last_cache_time = datetime.utcnow()
        await self.db.flush()
        logger.debug(f"已更新声音缓存: {plugin.plugin_id}")