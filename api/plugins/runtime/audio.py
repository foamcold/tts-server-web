"""
音频处理运行时模块

提供音频格式检测、采样率获取等功能
"""

import struct
from typing import Optional, Tuple


class AudioUtils:
    """音频处理工具类"""
    
    # 默认采样率
    DEFAULT_SAMPLE_RATE = 22050
    
    # 音频格式魔数
    MAGIC_RIFF = b'RIFF'
    MAGIC_WAVE = b'WAVE'
    MAGIC_OGG = b'OggS'
    MAGIC_FTYP = b'ftyp'  # MP4/M4A
    MAGIC_FLAC = b'fLaC'
    # MP3 帧同步字节
    MP3_SYNC_BYTE = 0xFF
    
    # MP3 采样率表(MPEG Audio Version ID, Layer, 采样率索引)
    # Version: 0=MPEG2.5, 1=reserved, 2=MPEG2, 3=MPEG1
    MP3_SAMPLE_RATES = {
        # MPEG1 采样率
        3: {0: 44100, 1: 48000, 2: 32000, 3: 0},
        # MPEG2 采样率
        2: {0: 22050, 1: 24000, 2: 16000, 3: 0},
        # MPEG2.5 采样率
        0: {0: 11025, 1: 12000, 2: 8000, 3: 0},
    }
    
    @staticmethod
    def detectAudioFormat(data: bytes) -> str:
        """
        检测音频格式
        
        Args:
            data: 音频数据（至少需要前12字节）
            
        Returns:
            格式字符串: 'wav', 'mp3', 'ogg', 'flac', 'm4a', 'unknown'
        """
        if not data or len(data) < 4:
            return 'unknown'
        
        # 检测 WAV 格式 (RIFF....WAVE)
        if len(data) >= 12:
            if data[:4] == AudioUtils.MAGIC_RIFF and data[8:12] == AudioUtils.MAGIC_WAVE:
                return 'wav'
        
        # 检测 OGG 格式
        if data[:4] == AudioUtils.MAGIC_OGG:
            return 'ogg'
        
        # 检测 FLAC 格式
        if data[:4] == AudioUtils.MAGIC_FLAC:
            return 'flac'
        
        # 检测 MP4/M4A 格式 (....ftyp)
        if len(data) >= 8:
            if data[4:8] == AudioUtils.MAGIC_FTYP:
                return 'm4a'
        
        # 检测 MP3 格式 (帧同步)
        if AudioUtils._isMp3Frame(data):
            return 'mp3'
        
        # 检测 ID3 标签开头的 MP3
        if len(data) >= 3 and data[:3] == b'ID3':
            return 'mp3'
        
        return 'unknown'
    
    @staticmethod
    def _isMp3Frame(data: bytes) -> bool:
        """
        检测是否为 MP3 帧
        
        Args:
            data: 音频数据
            
        Returns:
            是否为 MP3 帧
        """
        if len(data) < 4:
            return False
        
        # MP3 帧同步: 11个1位(0xFF 0xE0 或更高)
        if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
            # 验证版本和层不是保留值
            version = (data[1] >> 3) & 0x03
            layer = (data[1] >> 1) & 0x03
            
            # version=1 是保留值，layer=0 是保留值
            if version != 1 and layer != 0:
                return True
        
        return False
    
    @staticmethod
    def getAudioSampleRate(data: bytes) -> int:
        """
        从音频数据中获取采样率
        
        Args:
            data: 音频数据
            
        Returns:
            采样率（Hz），解析失败返回默认值
        """
        if not data:
            return AudioUtils.DEFAULT_SAMPLE_RATE
        
        # 检测格式
        audio_format = AudioUtils.detectAudioFormat(data)
        
        try:
            if audio_format == 'wav':
                return AudioUtils._getWavSampleRate(data)
            elif audio_format == 'mp3':
                return AudioUtils._getMp3SampleRate(data)
            elif audio_format == 'ogg':
                return AudioUtils._getOggSampleRate(data)
            elif audio_format == 'flac':
                return AudioUtils._getFlacSampleRate(data)
            else:
                return AudioUtils.DEFAULT_SAMPLE_RATE
        except Exception:
            return AudioUtils.DEFAULT_SAMPLE_RATE
    
    @staticmethod
    def _getWavSampleRate(data: bytes) -> int:
        """
        解析 WAV 文件采样率
        
        WAV 文件头结构:
        - 偏移 0-3: "RIFF"
        - 偏移 4-7: 文件大小
        - 偏移 8-11: "WAVE"
        - 偏移 12-15: "fmt " chunk标识
        - 偏移 16-19: fmt chunk大小
        - 偏移 20-21: 音频格式
        - 偏移 22-23: 通道数
        - 偏移 24-27: 采样率(little-endian uint32)
        
        Args:
            data: WAV 音频数据
            
        Returns:
            采样率
        """
        if len(data) < 28:
            return AudioUtils.DEFAULT_SAMPLE_RATE
        
        # 验证 RIFF/WAVE 头
        if data[:4] != AudioUtils.MAGIC_RIFF or data[8:12] != AudioUtils.MAGIC_WAVE:
            return AudioUtils.DEFAULT_SAMPLE_RATE
        
        # 查找 fmt chunk
        offset = 12
        while offset + 8 <= len(data):
            chunk_id = data[offset:offset + 4]
            chunk_size = struct.unpack('<I', data[offset + 4:offset + 8])[0]
            
            if chunk_id == b'fmt ':
                # fmt chunk 找到，采样率在 chunk 数据的偏移 4处
                if offset + 12 <= len(data):
                    sample_rate = struct.unpack('<I', data[offset + 12:offset + 16])[0]
                    # 验证采样率合理性
                    if 1000 <= sample_rate <= 192000:
                        return sample_rate
                break
            
            # 移动到下一个chunk
            offset += 8 + chunk_size
            # chunk 大小必须是偶数对齐
            if chunk_size % 2 != 0:
                offset += 1
        
        return AudioUtils.DEFAULT_SAMPLE_RATE
    
    @staticmethod
    def _getMp3SampleRate(data: bytes) -> int:
        """
        解析 MP3 文件采样率
        
        Args:
            data: MP3 音频数据
            
        Returns:
            采样率
        """
        #跳过 ID3 标签
        offset = 0
        if len(data) >= 10 and data[:3] == b'ID3':
            # ID3v2 标签大小在偏移 6-9，使用同步安全整数
            size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | \
                   ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
            offset = 10 + size
        
        # 查找 MP3 帧同步
        max_search = min(len(data), offset + 8192)  # 最多搜索 8KB
        while offset + 4 <= max_search:
            if data[offset] == 0xFF and (data[offset + 1] & 0xE0) == 0xE0:
                # 找到帧同步
                header = data[offset:offset + 4]
                # 解析帧头
                version = (header[1] >> 3) & 0x03
                layer = (header[1] >> 1) & 0x03
                sample_rate_index = (header[2] >> 2) & 0x03
                
                # 验证版本和层
                if version == 1 or layer == 0:
                    offset += 1
                    continue
                
                # 获取采样率
                if version in AudioUtils.MP3_SAMPLE_RATES:
                    sample_rate = AudioUtils.MP3_SAMPLE_RATES[version].get(sample_rate_index, 0)
                    if sample_rate > 0:
                        return sample_rate
                
                offset += 1
            else:
                offset += 1
        
        return AudioUtils.DEFAULT_SAMPLE_RATE
    
    @staticmethod
    def _getOggSampleRate(data: bytes) -> int:
        """
        解析 OGG 文件采样率（Vorbis）
        
        Args:
            data: OGG 音频数据
            
        Returns:
            采样率
        """
        if len(data) < 100:
            return AudioUtils.DEFAULT_SAMPLE_RATE
        
        # OGG Vorbis 标识头在第一个 OGG 页面中
        # 查找 vorbis 标识
        try:
            # 在前200 字节中查找 vorbis 标识
            vorbis_pos = data[:200].find(b'\x01vorbis')
            if vorbis_pos >= 0:
                # Vorbis 标识头结构:
                # 偏移 0: 包类型 (0x01)
                # 偏移 1-6: "vorbis"
                # 偏移 7-10: vorbis 版本
                # 偏移 11: 通道数
                # 偏移 12-15: 采样率 (little-endian uint32)
                sample_rate_offset = vorbis_pos + 12
                if sample_rate_offset + 4 <= len(data):
                    sample_rate = struct.unpack('<I', data[sample_rate_offset:sample_rate_offset + 4])[0]
                    if 1000 <= sample_rate <= 192000:
                        return sample_rate
        except Exception:
            pass
        
        return AudioUtils.DEFAULT_SAMPLE_RATE
    
    @staticmethod
    def _getFlacSampleRate(data: bytes) -> int:
        """
        解析 FLAC 文件采样率
        
        Args:
            data: FLAC 音频数据
            
        Returns:
            采样率
        """
        if len(data) < 22:
            return AudioUtils.DEFAULT_SAMPLE_RATE
        
        # FLAC 结构:
        # 偏移 0-3: "fLaC"
        # 偏移 4: 元数据块头(1字节类型 + 3字节大小)
        # STREAMINFO 块 (类型0) 结构:
        # - 最小/最大块大小 (各2字节)
        # - 最小/最大帧大小 (各3字节)
        # - 采样率 (20位), 通道数-1 (3位), 采样位深-1 (5位), 总采样数 (36位)
        
        try:
            if data[:4] != AudioUtils.MAGIC_FLAC:
                return AudioUtils.DEFAULT_SAMPLE_RATE
            
            # 检查第一个元数据块类型是否为 STREAMINFO (0)
            block_type = data[4] & 0x7F
            if block_type != 0:
                return AudioUtils.DEFAULT_SAMPLE_RATE
            
            # STREAMINFO 数据从偏移 8 开始
            # 采样率在偏移 8+4+6 = 18 处，占用 20 位
            # 字节 18-19 包含采样率的高 16 位，字节 20 的高 4 位是采样率的低 4 位
            if len(data) >= 21:
                sample_rate = (data[18] << 12) | (data[19] << 4) | (data[20] >> 4)
                if 1000 <= sample_rate <= 192000:
                    return sample_rate
        except Exception:
            pass
        
        return AudioUtils.DEFAULT_SAMPLE_RATE
    @staticmethod
    def getAudioDuration(data: bytes) -> Optional[float]:
        """
        获取音频时长（秒）
        
        注意: 这是一个简化实现，仅支持 WAV 格式的精确时长计算
        
        Args:
            data: 音频数据
            
        Returns:
            时长（秒），无法计算时返回 None
        """
        if not data:
            return None
        
        audio_format = AudioUtils.detectAudioFormat(data)
        
        try:
            if audio_format == 'wav':
                return AudioUtils._getWavDuration(data)
            else:
                # 其他格式暂不支持精确时长计算
                return None
        except Exception:
            return None
    
    @staticmethod
    def _getWavDuration(data: bytes) -> Optional[float]:
        """
        计算 WAV 文件时长
        
        Args:
            data: WAV 音频数据
            
        Returns:
            时长（秒）
        """
        if len(data) < 44:
            return None
        
        #验证 RIFF/WAVE 头
        if data[:4] != AudioUtils.MAGIC_RIFF or data[8:12] != AudioUtils.MAGIC_WAVE:
            return None
        
        # 查找 fmt 和 data chunk
        sample_rate = 0
        byte_rate = 0
        data_size = 0
        
        offset = 12
        while offset + 8 <= len(data):
            chunk_id = data[offset:offset + 4]
            chunk_size = struct.unpack('<I', data[offset + 4:offset + 8])[0]
            
            if chunk_id == b'fmt ':
                if offset + 20 <= len(data):
                    sample_rate = struct.unpack('<I', data[offset + 12:offset + 16])[0]
                    byte_rate = struct.unpack('<I', data[offset + 16:offset + 20])[0]
            elif chunk_id == b'data':
                data_size = chunk_size
                break
            
            offset += 8 + chunk_size
            if chunk_size % 2 != 0:
                offset += 1
        
        if byte_rate > 0 and data_size > 0:
            return data_size / byte_rate
        
        return None
    
    @staticmethod
    def getAudioInfo(data: bytes) -> dict:
        """
        获取音频信息摘要
        
        Args:
            data: 音频数据
            
        Returns:
            包含格式、采样率、时长等信息的字典
        """
        audio_format = AudioUtils.detectAudioFormat(data)
        sample_rate = AudioUtils.getAudioSampleRate(data)
        duration = AudioUtils.getAudioDuration(data)
        
        return {
            'format': audio_format,
            'sample_rate': sample_rate,
            'duration': duration,
            'size': len(data) if data else 0,}