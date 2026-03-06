"""
数据库连接模块
使用 SQLAlchemy 2.0 异步引擎
"""
from collections.abc import AsyncGenerator

from sqlalchemy import text

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from .config import config, ROOT_DIR


# 确保数据目录存在
data_dir = ROOT_DIR / "data"
data_dir.mkdir(exist_ok=True)

# 创建异步引擎
engine = create_async_engine(
    config.database.url,
    echo=config.database.echo,
)

# 创建异步会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """SQLAlchemy 模型基类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话 (依赖注入)"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库 (创建所有表)"""
    # 导入所有模型以确保表被注册到metadata
    from .models import (
        User, Plugin, TtsGroup, TtsConfig,
        ReplaceRuleGroup, ReplaceRule, SpeechRule,
        AudioCache, SystemSettings
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _sync_plugin_columns(conn)


async def _sync_plugin_columns(conn):
    """为 SQLite 开发环境补齐插件新增字段"""
    dialect = conn.dialect.name
    if dialect != "sqlite":
        return

    result = await conn.execute(text("PRAGMA table_info(plugins)"))
    columns = {row[1] for row in result.fetchall()}
    additions = {
        "engine_type": "ALTER TABLE plugins ADD COLUMN engine_type VARCHAR(50) DEFAULT 'native'",
        "compile_status": "ALTER TABLE plugins ADD COLUMN compile_status VARCHAR(50) DEFAULT 'pending'",
        "compile_error": "ALTER TABLE plugins ADD COLUMN compile_error TEXT DEFAULT ''",
        "capabilities": "ALTER TABLE plugins ADD COLUMN capabilities JSON",
        "ui_schema": "ALTER TABLE plugins ADD COLUMN ui_schema JSON",
        "runtime_meta": "ALTER TABLE plugins ADD COLUMN runtime_meta JSON",
        "raw_json": "ALTER TABLE plugins ADD COLUMN raw_json TEXT DEFAULT ''",
        "compiled_at": "ALTER TABLE plugins ADD COLUMN compiled_at DATETIME",
    }
    for column_name, sql in additions.items():
        if column_name not in columns:
            await conn.execute(text(sql))
