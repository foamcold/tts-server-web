"""
TTS Server Web 启动脚本
读取 config.yaml 中的服务器配置启动 uvicorn
"""
import uvicorn

from api.config import config


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )
