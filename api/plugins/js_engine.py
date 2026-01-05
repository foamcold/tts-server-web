"""
插件管理器模块

提供 PluginManager 类用于管理多个插件实例，
以及向后兼容的 PluginRuntime 类。

此模块是新PluginEngine 的高级包装器，提供：
- 多插件实例管理
- 线程安全的注册/注销
- 便捷的合成接口
"""

import threading
from typing import Dict, Optional, List, Any
import logging

from .engine import PluginEngine
from .types.plugin import (
    PluginConfig,
    PluginAudioResult,
    PluginVoice,
    PluginLocale,
)

logger = logging.getLogger(__name__)


class PluginManager:
    """
    插件管理器，管理多个插件实例
    
    提供插件的注册、注销、查询和合成等高级功能。
    使用线程锁确保线程安全。
    
    示例:
        manager = PluginManager()
        config = PluginConfig(pluginId="test", code="...")
        manager.register(config)
        
        # 合成音频
        result = await manager.synthesize("test", "你好", "voice1")
        
        # 获取声音列表
        voices = await manager.get_voices("test")
        manager.unregister("test")
    """
    
    # 单例模式支持
    _instance: Optional['PluginManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'PluginManager':
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化插件管理器"""
        # 避免重复初始化
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._engines: Dict[str, PluginEngine] = {}
        self._configs: Dict[str, PluginConfig] = {}
        self._engine_lock = threading.RLock()
        self._initialized = True
        logger.info("PluginManager 初始化完成")
    
    def register(self, config: PluginConfig) -> bool:
        """
        注册插件
        
        创建并加载插件引擎实例。如果插件已存在，
        会先注销再重新注册。
        
        Args:
            config: 插件配置对象
            
        Returns:
            注册成功返回 True，失败返回 False
        """
        plugin_id = config.pluginId
        if not plugin_id:
            logger.error("插件ID 不能为空")
            return False
        
        with self._engine_lock:
            # 如果已存在，先注销
            if plugin_id in self._engines:
                logger.info(f"插件已存在，重新注册: {plugin_id}")
                self._unregister_unsafe(plugin_id)
            
            try:
                # 创建并加载引擎
                engine = PluginEngine(config)
                if not engine.load():
                    logger.error(f"插件加载失败: {plugin_id}, 错误: {engine.get_error()}")
                    return False
                
                self._engines[plugin_id] = engine
                self._configs[plugin_id] = config
                logger.info(f"插件注册成功: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"插件注册异常: {plugin_id}, 错误: {e}")
                return False
    
    def unregister(self, plugin_id: str) -> bool:
        """
        注销插件
        卸载并移除插件引擎实例。
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            注销成功返回 True，插件不存在返回 False
        """
        with self._engine_lock:
            return self._unregister_unsafe(plugin_id)
    
    def _unregister_unsafe(self, plugin_id: str) -> bool:
        """
        注销插件（内部方法，不加锁）
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            注销成功返回 True
        """
        if plugin_id not in self._engines:
            logger.warning(f"插件不存在: {plugin_id}")
            return False
        
        try:
            engine = self._engines.pop(plugin_id)
            self._configs.pop(plugin_id, None)
            engine.unload()
            logger.info(f"插件注销成功: {plugin_id}")
            return True
        except Exception as e:
            logger.error(f"插件注销异常: {plugin_id}, 错误: {e}")
            return False
    
    def get_engine(self, plugin_id: str) -> Optional[PluginEngine]:
        """
        获取插件引擎实例
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            插件引擎实例，不存在返回 None
        """
        with self._engine_lock:
            return self._engines.get(plugin_id)
    
    def get_config(self, plugin_id: str) -> Optional[PluginConfig]:
        """
        获取插件配置
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            插件配置对象，不存在返回 None
        """
        with self._engine_lock:
            return self._configs.get(plugin_id)
    
    async def synthesize(
        self,
        plugin_id: str,
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
            plugin_id: 插件唯一标识符
            text: 要合成的文本
            voice: 声音 ID
            locale: 语言区域代码，默认 "zh-CN"
            rate: 语速（-100 到 100），0 为默认
            pitch: 音调（-100 到 100），0 为默认
            volume: 音量（0 到 100），0 为默认
            **kwargs: 其他参数
            
        Returns:
            PluginAudioResult 对象
        """
        engine = self.get_engine(plugin_id)
        if not engine:
            return PluginAudioResult(error=f"插件不存在: {plugin_id}")
        
        if not engine.is_loaded():
            return PluginAudioResult(error=f"插件未加载: {plugin_id}")
        
        return await engine.get_audio(
            text=text,
            voice=voice,
            locale=locale,
            rate=rate,
            pitch=pitch,
            volume=volume,
            **kwargs
        )
    
    async def get_locales(self, plugin_id: str) -> List[PluginLocale]:
        """
        获取插件支持的语言列表
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            PluginLocale 对象列表，插件不存在返回空列表
        """
        engine = self.get_engine(plugin_id)
        if not engine:
            logger.warning(f"获取语言列表失败，插件不存在: {plugin_id}")
            return []
        
        return await engine.get_locales()
    
    async def get_voices(
        self,
        plugin_id: str,
        locale: str = ""
    ) -> List[PluginVoice]:
        """
        获取插件支持的声音列表
        
        Args:
            plugin_id: 插件唯一标识符
            locale: 语言区域代码，为空获取所有声音
            
        Returns:
            PluginVoice 对象列表，插件不存在返回空列表
        """
        engine = self.get_engine(plugin_id)
        if not engine:
            logger.warning(f"获取声音列表失败，插件不存在: {plugin_id}")
            return []
        
        return await engine.get_voices(locale)
    
    def list_plugins(self) -> List[str]:
        """
        列出所有已注册的插件ID
        
        Returns:
            插件 ID 列表
        """
        with self._engine_lock:
            return list(self._engines.keys())
    
    def list_plugin_configs(self) -> List[PluginConfig]:
        """
        列出所有已注册的插件配置
        
        Returns:
            插件配置列表
        """
        with self._engine_lock:
            return list(self._configs.values())
    
    def is_registered(self, plugin_id: str) -> bool:
        """
        检查插件是否已注册
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            已注册返回 True
        """
        with self._engine_lock:
            return plugin_id in self._engines
    
    def is_loaded(self, plugin_id: str) -> bool:
        """
        检查插件是否已加载
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            已加载返回 True
        """
        engine = self.get_engine(plugin_id)
        return engine.is_loaded() if engine else False
    
    def get_plugin_count(self) -> int:
        """
        获取已注册的插件数量
        
        Returns:
            插件数量
        """
        with self._engine_lock:
            return len(self._engines)
    
    def unregister_all(self) -> int:
        """
        注销所有插件
        
        Returns:
            注销的插件数量
        """
        with self._engine_lock:
            count = 0
            plugin_ids = list(self._engines.keys())
            for plugin_id in plugin_ids:
                if self._unregister_unsafe(plugin_id):
                    count += 1
            logger.info(f"批量注销插件完成，共{count} 个")
            return count
    
    def reload(self, plugin_id: str) -> bool:
        """
        重新加载插件
        
        Args:
            plugin_id: 插件唯一标识符
            
        Returns:
            重新加载成功返回 True
        """
        with self._engine_lock:
            config = self._configs.get(plugin_id)
            if not config:
                logger.warning(f"重新加载失败，插件配置不存在: {plugin_id}")
                return False
            
            # 先注销
            self._unregister_unsafe(plugin_id)
            
            # 重新注册
            try:
                engine =PluginEngine(config)
                if not engine.load():
                    logger.error(f"插件重新加载失败: {plugin_id}")
                    return False
                
                self._engines[plugin_id] = engine
                self._configs[plugin_id] = config
                logger.info(f"插件重新加载成功: {plugin_id}")
                return True
                
            except Exception as e:
                logger.error(f"插件重新加载异常: {plugin_id}, 错误: {e}")
                return False


# ==================== 向后兼容 ====================


class PluginRuntime:
    """
    插件运行时环境（向后兼容类）
    
    此类保持与旧版 API 的兼容性，内部使用新的 PluginEngine。
    建议新代码直接使用 PluginEngine 或 PluginManager。
    @deprecated: 建议使用 PluginEngine 或 PluginManager
    """

    def __init__(self, plugin_id: str, user_vars: Dict[str, Any] = None):
        """
        初始化插件运行时
        
        Args:
            plugin_id: 插件唯一标识符
            user_vars: 用户变量字典
        """
        self.plugin_id = plugin_id
        self.user_vars = user_vars or {}
        self._engine: Optional[PluginEngine] = None
        self._code: Optional[str] = None
        logger.debug(f"PluginRuntime 初始化（兼容模式）: {plugin_id}")
    
    def load_plugin(self, code: str):
        """
        加载插件代码
        
        Args:
            code: JavaScript 插件代码
        """
        self._code = code
        config = PluginConfig(
            pluginId=self.plugin_id,
            code=code,
            userVars=self.user_vars
        )
        self._engine = PluginEngine(config)
        if not self._engine.load():
            error = self._engine.get_error()
            raise RuntimeError(f"插件加载失败: {error}")
    def get_locales(self) -> list:
        """
        获取支持的语言列表
        
        Returns:
            语言代码列表
        """
        if not self._engine or not self._engine.is_loaded():
            return ['zh-CN']
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        locales = loop.run_until_complete(self._engine.get_locales())
        return [loc.code for loc in locales]
    
    def get_voices(self, locale: str) -> dict:
        """
        获取声音列表
        
        Args:
            locale: 语言区域代码
            
        Returns:
            声音字典{id: name, ...}
        """
        if not self._engine or not self._engine.is_loaded():
            return {}
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        voices = loop.run_until_complete(self._engine.get_voices(locale))
        return {v.id: v.name for v in voices}
    
    def get_audio(
        self,
        text: str,
        locale: str,
        voice: str,
        speed: int,
        volume: int,
        pitch: int
    ) -> bytes:
        """
        获取音频数据
        
        Args:
            text: 要合成的文本
            locale: 语言区域代码
            voice: 声音 ID
            speed: 语速
            volume: 音量
            pitch: 音调
            
        Returns:
            音频二进制数据
        Raises:
            RuntimeError: 插件执行失败
        """
        if not self._engine or not self._engine.is_loaded():
            raise RuntimeError("插件未加载")
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self._engine.get_audio(
                text=text,
                voice=voice,
                locale=locale,
                rate=speed,
                pitch=pitch,
                volume=volume
            )
        )
        
        if result.error:
            raise RuntimeError(f"插件执行失败: {result.error}")
        
        return result.audio
    
    def get_user_vars(self) -> Dict[str, Any]:
        """
        获取更新后的用户变量
        
        Returns:
            用户变量字典
        """
        if self._engine:
            return self._engine.get_user_vars()
        return self.user_vars


class LegacyPluginEngine:
    """
    旧版插件引擎（向后兼容类）
    
    保持与旧版 API 的兼容性。
    新代码应使用 PluginManager 或 PluginEngine。
    
    @deprecated: 建议使用 PluginManager 或 PluginEngine
    """
    
    _instances: Dict[str,PluginRuntime] = {}

    @classmethod
    def get_runtime(
        cls,
        plugin_id: str,
        code: str,
        user_vars: Dict[str, Any] = None
    ) -> PluginRuntime:
        """
        获取或创建插件运行时
        
        Args:
            plugin_id: 插件 ID
            code: 插件代码
            user_vars: 用户变量
            
        Returns:
            PluginRuntime 实例
        """
        runtime = PluginRuntime(plugin_id, user_vars)
        runtime.load_plugin(code)
        return runtime

    @classmethod
    async def execute_async(
        cls,
        plugin_id: str,
        code: str,
        user_vars: Dict[str, Any],
        method: str,
        *args
    ) -> Any:
        """
        异步执行插件方法
        
        Args:
            plugin_id: 插件 ID
            code: 插件代码
            user_vars: 用户变量
            method: 方法名
            *args: 方法参数
            
        Returns:
            方法返回值
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        executor = ThreadPoolExecutor(max_workers=1)
        loop = asyncio.get_event_loop()
        def run():
            runtime = cls.get_runtime(plugin_id, code, user_vars)
            if method =='getLocales':
                return runtime.get_locales()
            elif method == 'getVoices':
                return runtime.get_voices(*args)
            elif method == 'getAudio':
                return runtime.get_audio(*args)
            else:
                raise ValueError(f"未知方法: {method}")
        
        return await loop.run_in_executor(executor, run)


# 获取全局插件管理器实例
def get_plugin_manager() -> PluginManager:
    """
    获取全局插件管理器实例
    
    Returns:
        PluginManager 单例实例
    """
    return PluginManager()


# 导出
__all__ = [
    'PluginManager',
    'PluginRuntime',
    'LegacyPluginEngine',
    'get_plugin_manager',
]