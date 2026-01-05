"""
TTS Server Web - FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import config
from .database import init_db


# 配置日志
logging.basicConfig(
    level=getattr(logging, config.logging.level),
    format=config.logging.format,
)
logger = logging.getLogger(__name__)

# 抑制 aiosqlite 的DEBUG 日志，避免输出过多
logging.getLogger("aiosqlite").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("正在初始化数据库...")
    await init_db()
    logger.info("数据库初始化完成")
    logger.info(f"TTS Server Web 启动成功，监听 {config.server.host}:{config.server.port}")
    yield
    # 关闭时
    logger.info("TTS Server Web 正在关闭...")


# 检查是否存在前端静态文件（生产环境）
static_dir = Path(__file__).parent.parent / "dist"
has_frontend = static_dir.exists() and (static_dir / "index.html").exists()

# 创建 FastAPI 应用
app = FastAPI(
    title="TTS Server Web",
    description="TTS 语音合成服务器 Web 版",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置 CORS - 支持所有来源以兼容阅读APP等客户端
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境可根据需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 仅在开发环境（无前端静态文件）时显示 API 信息
if not has_frontend:
    @app.get("/")
    async def root():
        """根路径 - API 信息（开发环境）"""
        return {
            "name": "TTS Server Web",
            "version": "1.0.0",
            "status": "running",
        }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy"}


# 注册路由
from .routers import auth, tts, plugins, synthesizer, rules, public_api

app.include_router(auth.router, prefix="/api")
app.include_router(tts.router, prefix="/api")  # TTS 配置管理: /api/tts-configs/...
app.include_router(plugins.router, prefix="/api")
app.include_router(synthesizer.router, prefix="/api")
app.include_router(rules.router, prefix="/api")
app.include_router(public_api.router, prefix="/api")  # 公开 API: /api/tts, /api/legado, /api/info, /api/health, /api/proxy


# 静态文件托管（生产环境）
if has_frontend:
    # 挂载静态资源目录（_next、images 等）
    next_static = static_dir / "_next"
    if next_static.exists():
        app.mount("/_next", StaticFiles(directory=str(next_static)), name="next-static")
    
    # 挂载其他静态资源
    for item in static_dir.iterdir():
        if item.is_dir() and item.name not in ("_next",):
            app.mount(f"/{item.name}", StaticFiles(directory=str(item)), name=f"static-{item.name}")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA 路由回退 - 返回对应的 HTML 文件或 index.html"""
        # 尝试匹配具体的 HTML 文件
        html_file = static_dir / f"{full_path}.html"
        if html_file.exists():
            return FileResponse(html_file)
        
        # 尝试匹配目录下的 index.html
        dir_index = static_dir / full_path / "index.html"
        if dir_index.exists():
            return FileResponse(dir_index)
        
        # 尝试匹配静态文件
        static_file = static_dir / full_path
        if static_file.exists() and static_file.is_file():
            return FileResponse(static_file)
        
        # 回退到根 index.html
        return FileResponse(static_dir / "index.html")
    
    logger.info(f"已启用静态文件托管: {static_dir}")