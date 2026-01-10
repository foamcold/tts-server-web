"""
TTS 合成服务
"""
import io
import asyncio
import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.tts_config import TtsConfig
from ..schemas.synthesizer import SynthesizeRequest, AudioFormat
from ..services.text_processor import TextProcessor
from ..services.plugin_service import PluginService
from ..services.audio_cache_service import AudioCacheService
from ..config import config

logger = logging.getLogger(__name__)


class SynthesizerService:
    """TTS 合成服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.text_processor = TextProcessor(db)
        self.plugin_service = PluginService(db)
        self.cache_service = AudioCacheService(db)

    async def get_default_config(self) -> Optional[TtsConfig]:
        """获取默认 TTS 配置"""
        stmt = select(TtsConfig).where(
            TtsConfig.is_enabled == True
        ).order_by(TtsConfig.order).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_config_by_id(self, config_id: int) -> Optional[TtsConfig]:
        """获取指定 TTS 配置"""
        stmt = select(TtsConfig).where(TtsConfig.id == config_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def synthesize(self, request: SynthesizeRequest) -> bytes:
        """
        合成语音
        返回音频二进制数据
        优先从缓存获取，未命中则调用插件合成并缓存
        """
        # 处理文本（注意：apply_rules 可能被配置覆盖，所以先在后面处理）
        text = request.text
        
        # 确定使用的配置
        tts_config = None
        plugin_db_id = request.plugin_id  # 前端传入的是数据库整数 ID
        voice = request.voice
        locale = request.locale
        speed = request.speed
        volume = request.volume
        pitch = request.pitch
        apply_rules = request.apply_rules
        audio_format = request.format
        
        if request.config_id:
            tts_config = await self.get_config_by_id(request.config_id)
            if tts_config:
                # TtsConfig.plugin_id 是字符串标识符，需要转换为数据库 ID
                if not plugin_db_id and tts_config.plugin_id:
                    plugin_record = await self.plugin_service.get_plugin_by_plugin_id(tts_config.plugin_id)
                    if plugin_record:
                        plugin_db_id = plugin_record.id
                    else:
                        raise ValueError(f"配置关联的插件不存在: {tts_config.plugin_id}")
                voice = voice or tts_config.voice
                locale = locale or tts_config.locale
                # 使用配置中的参数（配置模式下完全使用配置的参数）
                speed = tts_config.speed
                volume = tts_config.volume
                pitch = tts_config.pitch
                # 使用配置中的应用规则和音频格式设置
                apply_rules = getattr(tts_config, 'apply_rules', True)
                audio_format_str = getattr(tts_config, 'audio_format', None)
                if audio_format_str:
                    try:
                        audio_format = AudioFormat(audio_format_str)
                    except ValueError:
                        pass  # 保持请求中的默认格式
        
        if not plugin_db_id:
            # 使用默认配置
            tts_config = await self.get_default_config()
            if not tts_config:
                raise ValueError("没有可用的 TTS 配置")
            # TtsConfig.plugin_id 是字符串标识符，需要转换为数据库 ID
            if tts_config.plugin_id:
                plugin_record = await self.plugin_service.get_plugin_by_plugin_id(tts_config.plugin_id)
                if plugin_record:
                    plugin_db_id = plugin_record.id
                else:
                    raise ValueError(f"配置关联的插件不存在: {tts_config.plugin_id}")
            voice = voice or tts_config.voice
            locale = locale or tts_config.locale
            speed = tts_config.speed
            volume = tts_config.volume
            pitch = tts_config.pitch
        
        if not voice:
            raise ValueError("未指定声音")
        
        # 现在处理文本（apply_rules 可能已被配置覆盖）
        if apply_rules:
            text = await self.text_processor.process_text(text)
        
        if not text.strip():
            raise ValueError("处理后的文本为空")
        
        # 确定最终的音频格式
        final_audio_format = audio_format.value if hasattr(audio_format, 'value') else str(audio_format)
        
        # 尝试从缓存获取
        cache_result = await self.cache_service.get_cache(
            text=text,
            plugin_id=str(plugin_db_id),
            voice=voice,
            locale=locale,
            speed=speed,
            volume=volume,
            pitch=pitch,
            audio_format=final_audio_format
        )
        
        if cache_result:
            audio_data, cache_record = cache_result
            logger.info(f"缓存命中: voice={voice}, text_len={len(text)}, hit_count={cache_record.hit_count}")
            return audio_data
        
        # 缓存未命中，调用插件合成
        logger.debug(f"[DEBUG] SynthesizerService.synthesize 准备调用插件")
        logger.debug(f"[DEBUG] 参数: plugin_db_id={plugin_db_id}, text_len={len(text)}, voice={voice}, locale={locale}")
        logger.debug(f"[DEBUG] 参数: speed={speed}, volume={volume}, pitch={pitch}")
        
        try:
            audio_data = await self.plugin_service.get_audio(
                plugin_db_id,
                text,
                locale,
                voice,
                speed,
                volume,
                pitch,)
            
            logger.debug(f"[DEBUG] SynthesizerService.synthesize 插件返回成功，音频大小: {len(audio_data)} 字节")
        except Exception as e:
            logger.error(f"[DEBUG] SynthesizerService.synthesize 插件调用失败: {e}")
            import traceback
            logger.error(f"[DEBUG] 堆栈: {traceback.format_exc()}")
            raise
        
        # 格式转换 (如果需要)
        if audio_format != AudioFormat.MP3:
            audio_data = await self._convert_format(audio_data, audio_format)
        
        # 保存到缓存
        await self.cache_service.save_cache(
            text=text,
            plugin_id=str(plugin_db_id),
            voice=voice,
            locale=locale,
            speed=speed,
            volume=volume,
            pitch=pitch,
            audio_format=final_audio_format,
            audio_data=audio_data
        )
        
        return audio_data

    async def synthesize_with_rules(self, text: str, default_config_id: Optional[int] = None) -> bytes:
        """
        使用朗读规则合成
        根据朗读规则分割文本，不同部分使用不同配置
        """
        await self.text_processor.load_rules()
        
        # 应用替换规则
        processed_text = self.text_processor.apply_replace_rules(text)
        
        # 根据朗读规则分割
        segments = await self.text_processor.split_by_speech_rules(processed_text)
        
        # 合成每个片段
        audio_parts: List[bytes] = []
        
        for segment_text, config_id, _tag in segments:
            if not segment_text.strip():
                continue
            
            effective_config_id = config_id or default_config_id
            
            request = SynthesizeRequest(
                text=segment_text,
                config_id=effective_config_id,
                apply_rules=False,  # 已经处理过了
            )
            
            try:
                audio_data = await self.synthesize(request)
                audio_parts.append(audio_data)
            except Exception as e:
                print(f"合成片段失败: {e}")
                continue
        
        if not audio_parts:
            raise ValueError("没有成功合成任何片段")
        
        # 合并音频
        return await self._merge_audio(audio_parts)

    async def synthesize_long_text(
        self, 
        text: str, 
        config_id: Optional[int] = None,
        max_segment_length: int = 500
    ) -> bytes:
        """
        合成长文本
        自动分割并合并
        """
        await self.text_processor.load_rules()
        
        # 处理文本
        processed_text = self.text_processor.apply_replace_rules(text)
        
        # 分割为句子
        sentences = self.text_processor.split_sentences(processed_text, max_segment_length)
        
        # 并发合成 (限制并发数)
        semaphore = asyncio.Semaphore(3)
        async def synthesize_sentence(sentence: str) -> Optional[bytes]:
            async with semaphore:
                try:
                    request = SynthesizeRequest(
                        text=sentence,
                        config_id=config_id,
                        apply_rules=False,
                    )
                    return await self.synthesize(request)
                except Exception as e:
                    print(f"合成失败: {e}")
                    return None
        
        tasks = [synthesize_sentence(s) for s in sentences if s.strip()]
        results = await asyncio.gather(*tasks)
        
        audio_parts = [r for r in results if r is not None]
        
        if not audio_parts:
            raise ValueError("合成失败")
        
        return await self._merge_audio(audio_parts)

    async def _convert_format(self, audio_data: bytes, target_format: AudioFormat) -> bytes:
        """
        转换音频格式
        使用 pydub 进行转换（可选依赖）
        """
        try:
            import pydub  # type: ignore[import-not-found]
            AudioSegment = pydub.AudioSegment
            
            audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
            
            output = io.BytesIO()
            audio.export(output, format=target_format.value)
            return output.getvalue()
        except ImportError:
            # 如果没有 pydub，返回原始数据
            logger.warning("pydub 未安装，无法转换音频格式，返回原始 MP3 数据")
            return audio_data
        except Exception as e:
            logger.warning(f"格式转换失败: {e}")
            return audio_data

    async def _merge_audio(self, audio_parts: List[bytes]) -> bytes:
        """
        合并多个音频文件
        使用 pydub 进行合并（可选依赖）
        """
        if len(audio_parts) == 1:
            return audio_parts[0]
        
        try:
            import pydub  # type: ignore[import-not-found]
            AudioSegment = pydub.AudioSegment
            
            combined = AudioSegment.empty()
            
            for part in audio_parts:
                try:
                    segment = AudioSegment.from_mp3(io.BytesIO(part))
                    combined += segment
                except Exception:
                    continue
            
            output = io.BytesIO()
            combined.export(output, format="mp3")
            return output.getvalue()
        except ImportError:
            # 如果没有 pydub，简单拼接 (注意：这可能不能正确播放)
            logger.warning("pydub 未安装，使用简单拼接合并音频（可能无法正确播放）")
            return b''.join(audio_parts)