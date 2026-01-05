"""
ttsrv 运行时对象
为 JavaScript 插件提供主要API，模拟 Android 项目中的 ttsrv 全局对象
"""

import uuid
import time
import logging
import threading
from typing import Any, Optional, Dict, Union

from .http import HttpClient, JsResponse
from .crypto import (
    md5Encode as _md5Encode,
    md5Encode16 as _md5Encode16,
    base64Encode as _base64Encode,
    base64Decode as _base64Decode,
    base64DecodeToString as _base64DecodeToString,
    hexEncodeToString as _hexEncodeToString,
    hexDecodeToByteArray as _hexDecodeToByteArray,
    createSymmetricCrypto as _createSymmetricCrypto,SymmetricCrypto,
)
from .filesystem import FileSystem
from .audio import AudioUtils

logger = logging.getLogger(__name__)


class TtsrvRuntime:
    """
    ttsrv 运行时对象，暴露给 JavaScript 插件
    整合所有运行时模块，提供统一的 API：
    - HTTP 请求
    - 加密/编码
    - 文件系统操作
    - 音频处理
    - 工具方法
    - 变量管理
    """
    
    def __init__(
        self,
        plugin_id: str,
        user_vars: Optional[Dict[str, Any]] = None,
        def_vars: Optional[Dict[str, Any]] = None
    ):
        """
        初始化 ttsrv 运行时
        
        Args:
            plugin_id: 插件 ID，用于隔离文件系统
            user_vars: 用户变量初始值
            def_vars: 默认变量（来自插件定义）
        """
        self._plugin_id = plugin_id
        
        # 初始化变量存储（线程安全）
        self._vars_lock = threading.Lock()
        # 默认变量（只读）
        self._def_vars = def_vars or {}
        # 用户变量（可读写）
        self._user_vars = user_vars.copy() if user_vars else {}
        
        # 初始化 HTTP 客户端
        self._http = HttpClient()
        
        # 初始化文件系统（每个插件独立目录）
        self._fs = FileSystem(f"data/plugins/{plugin_id}")
        
        # 音频工具
        self._audio = AudioUtils()
        
        logger.debug(f"TtsrvRuntime 初始化完成: plugin_id={plugin_id}")
    
    #==================== HTTP 方法 ====================
    
    def httpGet(self, url: str, headers: Optional[Dict[str, str]] = None) -> JsResponse:
        """
        发送 HTTP GET 请求
        
        Args:
            url: 请求 URL
            headers: 可选的请求头字典
            
        Returns:
            JsResponse 对象，包含状态码、响应头和响应体
        """
        return self._http.httpGet(url, headers)
    
    def httpPost(
        self,
        url: str,
        body: str,
        headers: Optional[Dict[str, str]] = None
    ) -> JsResponse:
        """
        发送 HTTP POST 请求
        
        Args:
            url: 请求 URL
            body: 请求体内容（字符串）
            headers: 可选的请求头字典
            
        Returns:
            JsResponse 对象
        """
        return self._http.httpPost(url, body, headers)
    
    def httpPostMultipart(
        self,
        url: str,
        files: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> JsResponse:
        """
        发送Multipart POST 请求
        
        Args:
            url: 请求 URL
            files: 文件字典
            headers: 可选的请求头字典
            
        Returns:
            JsResponse 对象
        """
        return self._http.httpPostMultipart(url, files, headers)
    
    # ==================== 加密方法 ====================
    
    def md5Encode(self, data: Union[str, bytes]) -> str:
        """
        计算 MD5 哈希值（32位小写）
        
        Args:
            data: 要计算哈希的数据
            
        Returns:
            32位小写 MD5 哈希字符串
        """
        return _md5Encode(data)
    
    def md5Encode16(self, data: Union[str, bytes]) -> str:
        """
        计算 MD5 哈希值（16位小写，取中间16位）
        
        Args:
            data: 要计算哈希的数据
            
        Returns:
            16位小写 MD5 哈希字符串
        """
        return _md5Encode16(data)
    
    def base64Encode(self, data: Union[str, bytes]) -> str:
        """
        Base64 编码
        
        Args:
            data: 要编码的数据
            
        Returns:
            Base64 编码后的字符串
        """
        return _base64Encode(data)
    
    def base64Decode(self, data: str) -> bytes:
        """
        Base64 解码
        
        Args:
            data: Base64 编码的字符串
            
        Returns:
            解码后的字节
        """
        return _base64Decode(data)
    
    def base64DecodeToString(self, data: str, encoding: str = 'utf-8') -> str:
        """
        Base64 解码为字符串
        
        Args:
            data: Base64 编码的字符串
            encoding: 字符编码，默认为 utf-8
            
        Returns:
            解码后的字符串
        """
        return _base64DecodeToString(data, encoding)
    
    def hexEncodeToString(self, data: bytes) -> str:
        """
        字节转十六进制字符串
        
        Args:
            data: 要转换的字节数据
            
        Returns:
            小写十六进制字符串
        """
        return _hexEncodeToString(data)
    
    def hexDecodeToByteArray(self, hex_str: str) -> bytes:
        """
        十六进制字符串转字节
        
        Args:
            hex_str: 十六进制字符串
            
        Returns:
            字节数据
        """
        return _hexDecodeToByteArray(hex_str)
    
    def createSymmetricCrypto(
        self,
        transformation: str,
        key: bytes,
        iv: Optional[bytes] = None
    ) -> SymmetricCrypto:
        """
        创建对称加密实例
        
        Args:
            transformation: 转换模式，格式为 "算法/模式/填充"
                           支持: AES/ECB/PKCS5Padding, AES/CBC/PKCS5Padding,
                                 DES/ECB/PKCS5Padding, DES/CBC/PKCS5Padding
            key: 加密密钥
            iv: 初始化向量（CBC 模式必需）
            
        Returns:
            SymmetricCrypto 实例
        """
        return _createSymmetricCrypto(transformation, key, iv)
    
    # ==================== 文件系统 ====================
    
    @property
    def fs(self) -> FileSystem:
        """
        获取文件系统实例
        
        Returns:
            FileSystem 实例，用于文件操作
        """
        return self._fs
    
    # ==================== 音频方法 ====================
    
    def getAudioSampleRate(self, data: bytes) -> int:
        """
        从音频数据中获取采样率
        
        Args:
            data: 音频数据
            
        Returns:
            采样率（Hz），解析失败返回默认值 22050
        """
        return AudioUtils.getAudioSampleRate(data)
    
    # ==================== 工具方法 ====================
    
    def randomUUID(self) -> str:
        """
        生成随机 UUID
        
        Returns:
            UUID 字符串（小写，无连字符）
        """
        return str(uuid.uuid4()).replace('-', '')
    
    def timeFormat(self, timestamp: Optional[int] = None, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: Unix 时间戳（毫秒），None 表示当前时间
            format_str: 格式化字符串，默认为 '%Y-%m-%d %H:%M:%S'
            
        Returns:
            格式化后的时间字符串
        """
        if timestamp is None:
            ts = time.time()
        else:
            # 将毫秒转换为秒
            ts = timestamp / 1000.0
        
        return time.strftime(format_str, time.localtime(ts))
    
    def log(self, message: str) -> None:
        """
        日志输出（调试用）
        
        Args:
            message: 日志消息
        """
        logger.info(f"[Plugin:{self._plugin_id}] {message}")
    
    def toast(self, message: str) -> None:
        """
        消息提示（仅记录日志，Web 环境无Toast）
        
        Args:
            message: 提示消息
        """
        logger.info(f"[Plugin:{self._plugin_id}] Toast: {message}")
    
    def sleep(self, ms: int) -> None:
        """
        休眠指定毫秒数
        
        Args:
            ms: 休眠时间（毫秒）
        """
        time.sleep(ms / 1000.0)
    
    # ==================== 变量管理 ====================
    
    def setVar(self, key: str, value: Any) -> None:
        """
        设置用户变量
        
        Args:
            key: 变量名
            value: 变量值
        """
        with self._vars_lock:
            self._user_vars[key] = value
    
    def getVar(self, key: str, default: Any = None) -> Any:
        """
        获取用户变量
        
        首先从用户变量中查找，如果不存在则从默认变量中查找。
        
        Args:
            key: 变量名
            default: 默认值（当变量不存在时返回）
            
        Returns:
            变量值
        """
        with self._vars_lock:
            # 优先从用户变量获取
            if key in self._user_vars:
                return self._user_vars[key]
            # 再从默认变量获取
            if key in self._def_vars:
                return self._def_vars[key]
            return default
    
    def removeVar(self, key: str) -> bool:
        """
        删除用户变量
        
        Args:
            key: 变量名
            
        Returns:
            如果变量存在并被删除返回 True，否则返回 False
        """
        with self._vars_lock:
            if key in self._user_vars:
                del self._user_vars[key]
                return True
            return False
    
    # ==================== 内部方法 ====================
    
    def getUserVars(self) -> Dict[str, Any]:
        """
        获取所有用户变量（用于持久化）
        
        Returns:
            用户变量字典的副本
        """
        with self._vars_lock:
            return self._user_vars.copy()
    
    def getPluginId(self) -> str:
        """
        获取插件 ID
        
        Returns:
            插件 ID
        """
        return self._plugin_id


# 导出
__all__ = ['TtsrvRuntime']