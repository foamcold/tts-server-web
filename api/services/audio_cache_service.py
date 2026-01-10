"""
音频缓存服务
管理音频缓存的存储、读取和清理
"""
import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete

from ..models.audio_cache import AudioCache
from ..config import ROOT_DIR
from .settings_service import SettingsService

logger = logging.getLogger(__name__)

# 缓存目录
CACHE_DIR = ROOT_DIR / "data" / "cache"


class AudioCacheService:
    """音频缓存服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.settings_service = SettingsService(db)
        # 确保缓存目录存在
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_cache_key(
        text: str,
        plugin_id: str,
        voice: str,
        locale: str,
        speed: int,
        volume: int,
        pitch: int,
        audio_format: str
    ) -> str:
        """
        生成缓存键
        
        Args:
            text: 原始文本
            plugin_id: 插件ID
            voice: 发音人代码
            locale: 语言区域
            speed: 语速
            volume: 音量
            pitch: 音调
            audio_format: 音频格式
            
        Returns:
            SHA256 哈希字符串
        """
        params = {
            "text": text,
            "plugin_id": plugin_id,
            "voice": voice,
            "locale": locale,
            "speed": speed,
            "volume": volume,
            "pitch": pitch,
            "format": audio_format
        }
        param_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(param_str.encode()).hexdigest()

    @staticmethod
    def _get_file_path(cache_key: str, audio_format: str) -> str:
        """
        获取缓存文件相对路径
        按缓存键前两个字符分层存储
        
        Args:
            cache_key: 缓存键
            audio_format: 音频格式
            
        Returns:
            相对于 CACHE_DIR 的文件路径
        """
        subdir = cache_key[:2]
        filename = f"{cache_key}.{audio_format}"
        return f"{subdir}/{filename}"

    @staticmethod
    def _get_absolute_path(relative_path: str) -> Path:
        """获取绝对路径"""
        return CACHE_DIR / relative_path

    async def get_cache(
        self,
        text: str,
        plugin_id: str,
        voice: str,
        locale: str,
        speed: int,
        volume: int,
        pitch: int,
        audio_format: str
    ) -> Optional[Tuple[bytes, AudioCache]]:
        """
        获取缓存的音频数据
        
        Args:
            text: 原始文本
            plugin_id: 插件ID
            voice: 发音人代码
            locale: 语言区域
            speed: 语速
            volume: 音量
            pitch: 音调
            audio_format: 音频格式
            
        Returns:
            (音频数据, 缓存记录) 或 None
        """
        # 检查缓存是否启用
        settings = await self.settings_service.get_cache_settings()
        if not settings["cache_audio_enabled"]:
            return None
        
        cache_key = self.generate_cache_key(
            text, plugin_id, voice, locale, speed, volume, pitch, audio_format
        )
        
        # 查询缓存记录
        stmt = select(AudioCache).where(AudioCache.cache_key == cache_key)
        result = await self.db.execute(stmt)
        cache = result.scalar_one_or_none()
        
        if not cache:
            return None
        
        # 检查文件是否存在
        file_path = self._get_absolute_path(cache.file_path)
        if not file_path.exists():
            logger.warning(f"缓存文件不存在，删除缓存记录: {cache.file_path}")
            await self.db.delete(cache)
            await self.db.flush()
            return None
        
        # 读取音频数据
        try:
            audio_data = file_path.read_bytes()
        except Exception as e:
            logger.error(f"读取缓存文件失败: {e}")
            return None
        
        # 更新访问统计
        cache.hit_count += 1
        cache.last_accessed_at = datetime.utcnow()
        await self.db.flush()
        
        logger.debug(f"缓存命中: cache_key={cache_key[:16]}..., hit_count={cache.hit_count}")
        
        return audio_data, cache

    async def save_cache(
        self,
        text: str,
        plugin_id: str,
        voice: str,
        locale: str,
        speed: int,
        volume: int,
        pitch: int,
        audio_format: str,
        audio_data: bytes
    ) -> Optional[AudioCache]:
        """
        保存音频到缓存
        
        Args:
            text: 原始文本
            plugin_id: 插件ID
            voice: 发音人代码
            locale: 语言区域
            speed: 语速
            volume: 音量
            pitch: 音调
            audio_format: 音频格式
            audio_data: 音频二进制数据
            
        Returns:
            缓存记录或 None
        """
        # 检查缓存是否启用
        settings = await self.settings_service.get_cache_settings()
        if not settings["cache_audio_enabled"]:
            return None
        
        cache_key = self.generate_cache_key(
            text, plugin_id, voice, locale, speed, volume, pitch, audio_format
        )
        
        # 检查是否已存在
        stmt = select(AudioCache).where(AudioCache.cache_key == cache_key)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.debug(f"缓存已存在: cache_key={cache_key[:16]}...")
            return existing
        
        # 生成文件路径
        relative_path = self._get_file_path(cache_key, audio_format)
        absolute_path = self._get_absolute_path(relative_path)
        
        # 确保目录存在
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        try:
            absolute_path.write_bytes(audio_data)
        except Exception as e:
            logger.error(f"写入缓存文件失败: {e}")
            return None
        
        # 创建缓存记录
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        cache = AudioCache(
            cache_key=cache_key,
            text=text[:1000],  # 只保存前1000字符用于调试
            text_hash=text_hash,
            plugin_id=plugin_id,
            voice=voice,
            locale=locale,
            speed=speed,
            volume=volume,
            pitch=pitch,
            format=audio_format,
            file_path=relative_path,
            audio_size=len(audio_data),
            hit_count=0,
        )
        
        self.db.add(cache)
        await self.db.flush()
        
        logger.info(f"音频已缓存: cache_key={cache_key[:16]}..., size={len(audio_data)} bytes")
        
        # 触发清理检查
        await self._check_and_cleanup()
        
        return cache

    async def _check_and_cleanup(self) -> None:
        """检查并执行清理（如果需要）"""
        settings = await self.settings_service.get_cache_settings()
        max_count = settings["cache_audio_max_count"]
        max_age_days = settings["cache_audio_max_age_days"]
        
        # 获取当前缓存数量
        count_stmt = select(func.count(AudioCache.id))
        result = await self.db.execute(count_stmt)
        current_count = result.scalar() or 0
        
        # 如果超过数量限制，触发清理
        if current_count > max_count:
            await self.cleanup()

    async def cleanup(self) -> dict:
        """
        清理过期和超量缓存
        
        Returns:
            清理结果统计
        """
        settings = await self.settings_service.get_cache_settings()
        max_count = settings["cache_audio_max_count"]
        max_age_days = settings["cache_audio_max_age_days"]
        
        deleted_count = 0
        deleted_size = 0
        
        # 1. 清理过期缓存
        expire_date = datetime.utcnow() - timedelta(days=max_age_days)
        stmt = select(AudioCache).where(AudioCache.created_at < expire_date)
        result = await self.db.execute(stmt)
        expired_caches = result.scalars().all()
        
        for cache in expired_caches:
            deleted_size += cache.audio_size
            # 删除文件
            file_path = self._get_absolute_path(cache.file_path)
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception as e:
                logger.warning(f"删除缓存文件失败: {e}")
            
            await self.db.delete(cache)
            deleted_count += 1
        
        logger.info(f"清理过期缓存: 删除 {deleted_count} 条")
        
        # 2. 清理超量缓存（按创建时间删除最旧的）
        count_stmt = select(func.count(AudioCache.id))
        result = await self.db.execute(count_stmt)
        current_count = result.scalar() or 0
        
        if current_count > max_count:
            excess_count = current_count - max_count
            
            # 获取最旧的记录
            stmt = select(AudioCache).order_by(AudioCache.created_at.asc()).limit(excess_count)
            result = await self.db.execute(stmt)
            old_caches = result.scalars().all()
            
            for cache in old_caches:
                deleted_size += cache.audio_size
                # 删除文件
                file_path = self._get_absolute_path(cache.file_path)
                try:
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    logger.warning(f"删除缓存文件失败: {e}")
                
                await self.db.delete(cache)
                deleted_count += 1
            
            logger.info(f"清理超量缓存: 删除 {excess_count} 条")
        
        await self.db.flush()
        
        # 获取剩余数量
        result = await self.db.execute(count_stmt)
        remaining_count = result.scalar() or 0
        
        return {
            "deleted_count": deleted_count,
            "deleted_size_bytes": deleted_size,
            "remaining_count": remaining_count,
            "message": f"清理完成，删除 {deleted_count} 条缓存"
        }

    async def clear_all(self) -> dict:
        """
        清空所有缓存
        
        Returns:
            清理结果统计
        """
        # 统计
        count_stmt = select(func.count(AudioCache.id))
        size_stmt = select(func.sum(AudioCache.audio_size))
        
        count_result = await self.db.execute(count_stmt)
        size_result = await self.db.execute(size_stmt)
        
        deleted_count = count_result.scalar() or 0
        deleted_size = size_result.scalar() or 0
        
        # 删除所有记录
        await self.db.execute(delete(AudioCache))
        await self.db.flush()
        
        # 删除所有文件
        try:
            import shutil
            if CACHE_DIR.exists():
                for item in CACHE_DIR.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        except Exception as e:
            logger.error(f"清空缓存目录失败: {e}")
        
        logger.info(f"已清空所有缓存: {deleted_count} 条, {deleted_size} bytes")
        
        return {
            "deleted_count": deleted_count,
            "deleted_size_bytes": deleted_size,
            "message": f"已清空 {deleted_count} 条缓存"
        }

    async def get_stats(self) -> dict:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        settings = await self.settings_service.get_cache_settings()
        
        # 总数量
        count_stmt = select(func.count(AudioCache.id))
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0
        
        # 总大小
        size_stmt = select(func.sum(AudioCache.audio_size))
        size_result = await self.db.execute(size_stmt)
        total_size = size_result.scalar() or 0
        
        # 总命中次数
        hits_stmt = select(func.sum(AudioCache.hit_count))
        hits_result = await self.db.execute(hits_stmt)
        total_hits = hits_result.scalar() or 0
        
        # 最早和最新缓存时间
        oldest_stmt = select(func.min(AudioCache.created_at))
        newest_stmt = select(func.max(AudioCache.created_at))
        
        oldest_result = await self.db.execute(oldest_stmt)
        newest_result = await self.db.execute(newest_stmt)
        
        oldest_date = oldest_result.scalar()
        newest_date = newest_result.scalar()
        
        return {
            "enabled": settings["cache_audio_enabled"],
            "total_count": total_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_hits": total_hits,
            "oldest_cache_date": oldest_date,
            "newest_cache_date": newest_date,
            "max_age_days": settings["cache_audio_max_age_days"],
            "max_count": settings["cache_audio_max_count"],
        }
