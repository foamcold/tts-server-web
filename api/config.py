"""
配置加载模块
从config.yaml 读取所有系统配置
"""
import re
import secrets
from pathlib import Path
from functools import lru_cache
from typing import Any

import yaml
from pydantic import BaseModel


# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 默认配置模板（带中文注释）
DEFAULT_CONFIG_TEMPLATE = '''# TTS Server 配置文件
# 项目启动时自动生成，可根据需要修改

# 服务器配置
server:
  # 服务器监听地址
  host: "0.0.0.0"
  # 服务器监听端口
  port: 8000
  # 允许的跨域来源
  cors_origins:
    - "http://localhost:3000"

# 数据库配置
database:
  # 数据库连接 URL (SQLite + aiosqlite 异步驱动)
  url: "sqlite+aiosqlite:///./data/tts_server.db"
  # 是否输出 SQL 语句（调试用）
  echo: false

# 认证配置
auth:
  # JWT 密钥 (启动时自动生成，请勿手动修改)
  secret_key: ""

# 日志配置
logging:
  # 日志级别: DEBUG, INFO, WARNING, ERROR
  level: "INFO"
  # 日志格式
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
'''


class ServerConfig(BaseModel):
    """服务器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]


class DatabaseConfig(BaseModel):
    """数据库配置"""
    url: str = "sqlite+aiosqlite:///./data/tts_server.db"
    echo: bool = False


class AuthConfig(BaseModel):
    """认证配置"""
    # JWT 密钥 (启动时自动生成)
    secret_key: str = ""


class LoggingConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AppConfig(BaseModel):
    """应用总配置"""
    server: ServerConfig = ServerConfig()
    database: DatabaseConfig = DatabaseConfig()
    auth: AuthConfig = AuthConfig()
    logging: LoggingConfig = LoggingConfig()


def _ensure_config_file() -> bool:
    """
    确保配置文件存在，不存在则创建默认配置
    
    Returns:
        bool: 如果创建了新配置文件返回 True，否则返回 False
    """
    config_path = ROOT_DIR / "config.yaml"
    
    if not config_path.exists():
        # 配置文件不存在，创建默认配置
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)
        print(f"[配置] 已创建默认配置文件: {config_path}")
        return True
    return False


def load_yaml_config() -> dict[str, Any]:
    """加载 YAML 配置文件"""
    config_path = ROOT_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def save_yaml_config(config_data: dict[str, Any]) -> None:
    """保存配置到 YAML 文件（不保留注释）"""
    config_path = ROOT_DIR / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _update_secret_key_in_file(secret_key: str) -> None:
    """
    在配置文件中更新密钥，保留注释
    
    使用正则替换的方式更新密钥，避免丢失配置文件中的注释
    """
    config_path = ROOT_DIR / "config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 使用正则替换密钥行，匹配 secret_key: "" 或 secret_key: "xxx" 或 secret_key: xxx
    content = re.sub(
        r'(secret_key:\s*)"?"?[^"\n]*"?',
        f'\\1"{secret_key}"',
        content
    )
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(content)


def _ensure_secret_key(yaml_config: dict[str, Any]) -> dict[str, Any]:
    """确保 secret_key 存在，如果为空则生成新的并保存"""
    auth_config = yaml_config.get("auth", {})
    secret_key = auth_config.get("secret_key", "")
    
    # 如果密钥为空或是默认值，生成新密钥
    if not secret_key or secret_key == "your-secret-key-change-in-production":
        # 生成安全的随机密钥
        new_secret_key = secrets.token_urlsafe(32)
        
        # 更新配置
        if "auth" not in yaml_config:
            yaml_config["auth"] = {}
        yaml_config["auth"]["secret_key"] = new_secret_key
        
        # 使用保留注释的方式更新密钥
        _update_secret_key_in_file(new_secret_key)
        print(f"[配置] 已生成新的 JWT 密钥并保存到配置文件")
    
    return yaml_config


@lru_cache()
def get_config() -> AppConfig:
    """获取应用配置 (缓存)"""
    # 先确保配置文件存在
    _ensure_config_file()
    # 加载配置
    yaml_config = load_yaml_config()
    # 确保密钥存在
    yaml_config = _ensure_secret_key(yaml_config)
    return AppConfig(**yaml_config)


# 便捷访问
config = get_config()