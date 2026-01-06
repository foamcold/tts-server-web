"""
TTS Server Web API 开发模式启动脚本
启用热重载，适用于开发调试
"""
import uvicorn

from api.config import config


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,  # 开发模式启用热重载
        reload_dirs=["api"],  # 监听 api 目录的文件变化
    )
