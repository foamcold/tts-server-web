"""
插件类型定义

定义插件系统中使用的所有数据结构，包括插件配置、
语言设置、声音定义、音频结果等。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum


class PluginStatus(str, Enum):
    """插件状态枚举"""
    IDLE = "idle"           # 空闲
    LOADING = "loading"     # 加载中
    RUNNING = "running"     # 运行中
    ERROR = "error"         # 错误
    DISABLED = "disabled"   # 已禁用


class VoiceGender(str, Enum):
    """声音性别枚举"""
    MALE = "male"# 男声
    FEMALE = "female"       # 女声
    NEUTRAL = "neutral"     # 中性


@dataclass
class PluginConfig:
    """
    插件配置（对应 JSON 中的插件定义）
    
    此类表示从插件 JSON 文件解析的配置信息，
    包含插件的元数据和执行代码。
    
    Attributes:
        isEnabled: 是否启用插件
        version: 插件版本号
        name: 插件名称
        pluginId: 插件唯一标识符
        author: 插件作者
        iconUrl: 插件图标 URL
        code: 插件 JavaScript 代码
        defVars: 默认变量定义
        userVars: 用户自定义变量"""
    isEnabled: bool = True
    version: int = 2
    name: str = ""
    pluginId: str = ""
    author: str = ""
    iconUrl: str = ""
    code: str = ""
    defVars: Optional[Dict[str, Any]] = None
    userVars: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.defVars is None:
            self.defVars = {}
        if self.userVars is None:
            self.userVars = {}

    def get_merged_vars(self) -> Dict[str, Any]:
        """
        获取合并后的变量（用户变量覆盖默认变量）
        
        Returns:
            合并后的变量字典
        """
        merged = dict(self.defVars or {})
        merged.update(self.userVars or {})
        return merged


@dataclass
class PluginLocale:
    """
    语言/区域设置
    
    表示 TTS 引擎支持的语言区域信息。
    Attributes:
        code: 语言代码，如 "zh-CN"、"en-US"
        name: 语言显示名称，如 "中文（简体）"、"English (US)"
    """
    code: str           # 如 "zh-CN"
    name: str           # 如 "中文（简体）"

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


@dataclass
class PluginVoice:
    """
    声音定义
    
    表示 TTS 引擎支持的声音配置，包含声音的
    基本信息和额外参数。
    
    Attributes:
        id: 声音唯一标识符
        name: 声音显示名称
        locale: 声音对应的语言区域代码
        gender: 声音性别
        extra: 额外参数，如音调、语速等
    """
    id: str
    name: str
    locale: str
    gender: str = ""
    extra: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理"""
        if self.extra is None:
            self.extra = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            声音信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "locale": self.locale,
            "gender": self.gender,
            "extra": self.extra,
        }


@dataclass
class PluginAudioResult:
    """
    getAudio 返回结果
    
    表示 TTS 合成的音频结果，包含音频数据
    和相关元信息。
    
    Attributes:
        audio: 音频二进制数据
        contentType: 音频MIME 类型
        sampleRate: 采样率（Hz）
        error: 错误信息（如果有）
    """
    audio: Optional[bytes] = None
    contentType: str = "audio/wav"
    sampleRate: int = 22050
    error: Optional[str] = None

    def is_success(self) -> bool:
        """
        检查是否成功获取音频
        
        Returns:
            如果音频数据存在且无错误返回 True
        """
        return self.audio is not None and self.error is None

    def get_audio_size(self) -> int:
        """
        获取音频数据大小
        
        Returns:
            音频数据字节数
        """
        return len(self.audio) if self.audio else 0


@dataclass
class PluginMetadata:
    """
    插件元数据
    
    存储插件的扩展信息，用于管理和展示。Attributes:
        pluginId: 插件唯一标识符
        name: 插件名称
        author: 插件作者
        version: 插件版本号
        description: 插件描述
        homepage: 插件主页 URL
        iconUrl: 插件图标 URL
        supportedLocales: 支持的语言列表
        tags: 插件标签
    """
    pluginId: str
    name: str
    author: str = ""
    version: int = 2
    description: str = ""
    homepage: str = ""
    iconUrl: str = ""
    supportedLocales: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class PluginExecutionContext:
    """
    插件执行上下文
    
    包含插件执行时所需的全部上下文信息。Attributes:
        plugin_id: 插件 ID
        code: 要执行的 JavaScript 代码
        vars: 变量字典
        timeout: 执行超时时间（秒）
        max_memory: 最大内存限制（MB）
        enable_network: 是否允许网络访问
        enable_filesystem: 是否允许文件系统访问
    """
    plugin_id: str
    code: str
    vars: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    max_memory: int = 128
    enable_network: bool = True
    enable_filesystem: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            上下文信息字典
        """
        return {
            "plugin_id": self.plugin_id,
            "vars": self.vars,
            "timeout": self.timeout,
            "max_memory": self.max_memory,
            "enable_network": self.enable_network,
            "enable_filesystem": self.enable_filesystem,
        }


@dataclass
class TTSRequest:
    """
    TTS 合成请求
    
    包含 TTS 合成所需的全部参数。
    
    Attributes:
        text: 要合成的文本
        voice: 声音 ID
        locale: 语言区域代码
        rate: 语速（0.5-2.0）
        pitch: 音调（0.5-2.0）
        volume: 音量（0.0-1.0）
        extra: 额外参数
    """
    text: str
    voice: str
    locale: str = "zh-CN"
    rate: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    extra: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理，验证参数范围"""
        # 限制 rate 范围
        self.rate = max(0.5, min(2.0, self.rate))
        # 限制 pitch 范围
        self.pitch = max(0.5, min(2.0, self.pitch))
        # 限制 volume 范围
        self.volume = max(0.0, min(1.0, self.volume))
        if self.extra is None:
            self.extra = {}

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        
        Returns:
            请求参数字典
        """
        return {
            "text": self.text,
            "voice": self.voice,
            "locale": self.locale,
            "rate": self.rate,
            "pitch": self.pitch,
            "volume": self.volume,
            "extra": self.extra,
        }