"""
加密运行时模块
提供 MD5、Base64、Hex 编解码以及对称加密（AES/DES）功能
"""

import hashlib
import base64
from typing import Union, Optional

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.backends import default_backend


def md5Encode(data: Union[str, bytes]) -> str:
    """
    计算 MD5 哈希值（32位小写）
    
    Args:
        data: 要计算哈希的数据，可以是字符串或字节
        
    Returns:
        32位小写 MD5 哈希字符串
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.md5(data).hexdigest()


def md5Encode16(data: Union[str, bytes]) -> str:
    """
    计算 MD5 哈希值（16位小写，取中间16位）
    
    Args:
        data: 要计算哈希的数据，可以是字符串或字节
        
    Returns:
        16位小写 MD5 哈希字符串（32位哈希的第9-24位）
    """
    full_hash = md5Encode(data)
    # 取中间16位：索引 8到 24
    return full_hash[8:24]


def base64Encode(data: Union[str, bytes]) -> str:
    """
    Base64 编码
    
    Args:
        data: 要编码的数据，可以是字符串或字节
        
    Returns:
        Base64 编码后的字符串
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')


def base64Decode(data: str) -> bytes:
    """
    Base64 解码
    
    Args:
        data: Base64 编码的字符串
        
    Returns:
        解码后的字节
    """
    return base64.b64decode(data)


def base64DecodeToString(data: str, encoding: str = 'utf-8') -> str:
    """
    Base64 解码为字符串
    
    Args:
        data: Base64 编码的字符串
        encoding: 字符编码，默认为 utf-8
        
    Returns:
        解码后的字符串
    """
    return base64Decode(data).decode(encoding)


def hexEncodeToString(data: bytes) -> str:
    """
    字节转十六进制字符串
    
    Args:
        data: 要转换的字节数据
        
    Returns:
        小写十六进制字符串
    """
    return data.hex()


def hexDecodeToByteArray(hex_str: str) -> bytes:
    """
    十六进制字符串转字节
    
    Args:
        hex_str: 十六进制字符串
        
    Returns:
        字节数据
    """
    return bytes.fromhex(hex_str)


class SymmetricCrypto:
    """
    对称加密类，支持 AES/DES 加解密
    
    支持的转换模式：
    - AES/ECB/PKCS5Padding
    - AES/CBC/PKCS5Padding
    - DES/ECB/PKCS5Padding
    - DES/CBC/PKCS5Padding
    
    注意：PKCS5Padding 在 Python cryptography 库中等同于 PKCS7
    """
    
    # 支持的算法和块大小映射
    ALGORITHM_BLOCK_SIZES = {
        'AES': 128,  # 128 位= 16 字节
        'DES': 64,   # 64 位 = 8 字节
    }
    
    def __init__(self, transformation: str, key: bytes, iv: Optional[bytes] = None):
        """
        初始化对称加密实例
        
        Args:
            transformation: 转换模式，格式为 "算法/模式/填充"支持: AES/ECB/PKCS5Padding, AES/CBC/PKCS5Padding,DES/ECB/PKCS5Padding, DES/CBC/PKCS5Padding
            key: 加密密钥
            iv: 初始化向量，CBC模式必需，ECB 模式忽略
            
        Raises:
            ValueError: 当转换模式不支持或参数无效时
        """
        self.transformation = transformation
        self.key = key
        self.iv = iv
        
        # 解析转换模式
        parts = transformation.split('/')
        if len(parts) != 3:
            raise ValueError(f"无效的转换模式格式: {transformation}，应为 '算法/模式/填充'")
        
        self.algorithm_name = parts[0].upper()
        self.mode_name = parts[1].upper()
        self.padding_name = parts[2].upper()
        
        # 验证算法
        if self.algorithm_name not in self.ALGORITHM_BLOCK_SIZES:
            raise ValueError(f"不支持的算法: {self.algorithm_name}，支持: {list(self.ALGORITHM_BLOCK_SIZES.keys())}")
        
        # 验证模式
        if self.mode_name not in ('ECB', 'CBC'):
            raise ValueError(f"不支持的模式: {self.mode_name}，支持: ECB, CBC")
        
        # 验证填充
        if self.padding_name not in ('PKCS5PADDING', 'PKCS7PADDING'):
            raise ValueError(f"不支持的填充: {self.padding_name}，支持: PKCS5Padding, PKCS7Padding")
        
        # CBC 模式需要IV
        if self.mode_name == 'CBC' and iv is None:
            raise ValueError("CBC 模式需要初始化向量 (iv)")
        
        # 获取块大小
        self.block_size = self.ALGORITHM_BLOCK_SIZES[self.algorithm_name]
        
        # 创建算法实例
        if self.algorithm_name == 'AES':
            self._algorithm = algorithms.AES(key)
        else:  # DES
            #注意：cryptography 库不直接支持 DES，使用 TripleDES 模拟
            # 对于 8 字节密钥，将其重复 3 次使用 TripleDES
            if len(key) == 8:
                self._algorithm = algorithms.TripleDES(key * 3)
            elif len(key) == 16:
                self._algorithm = algorithms.TripleDES(key + key[:8])
            elif len(key) == 24:
                self._algorithm = algorithms.TripleDES(key)
            else:
                raise ValueError(f"DES 密钥长度无效: {len(key)}，应为 8、16 或 24 字节")
    def _get_cipher(self) -> Cipher:
        """创建加密器实例"""
        if self.mode_name == 'ECB':
            mode = modes.ECB()
        else:  # CBC
            mode = modes.CBC(self.iv)
        
        return Cipher(self._algorithm, mode, backend=default_backend())
    
    def _pad(self, data: bytes) -> bytes:
        """PKCS7 填充"""
        padder = sym_padding.PKCS7(self.block_size).padder()
        return padder.update(data) + padder.finalize()
    
    def _unpad(self, data: bytes) -> bytes:
        """移除 PKCS7 填充"""
        unpadder = sym_padding.PKCS7(self.block_size).unpadder()
        return unpadder.update(data) + unpadder.finalize()
    
    def encrypt(self, data: bytes) -> bytes:
        """
        加密数据
        
        Args:
            data: 要加密的字节数据
            
        Returns:
            加密后的字节数据
        """
        # 填充数据
        padded_data = self._pad(data)
        
        # 创建加密器并加密
        cipher = self._get_cipher()
        encryptor = cipher.encryptor()
        return encryptor.update(padded_data) + encryptor.finalize()
    
    def decrypt(self, data: bytes) -> bytes:
        """
        解密数据
        
        Args:
            data: 要解密的字节数据
            
        Returns:
            解密后的字节数据
        """
        # 创建解密器并解密
        cipher = self._get_cipher()
        decryptor = cipher.decryptor()
        decrypted_padded = decryptor.update(data) + decryptor.finalize()
        
        # 移除填充
        return self._unpad(decrypted_padded)
    
    def encryptBase64(self, data: bytes) -> str:
        """
        加密并返回 Base64 编码结果
        
        Args:
            data: 要加密的字节数据
            
        Returns:
            Base64 编码的加密结果
        """
        encrypted = self.encrypt(data)
        return base64Encode(encrypted)
    
    def decryptBase64(self, data: str) -> bytes:
        """
        解密Base64 编码的数据
        
        Args:
            data: Base64 编码的加密数据
            
        Returns:
            解密后的字节数据
        """
        encrypted = base64Decode(data)
        return self.decrypt(encrypted)


def createSymmetricCrypto(
    transformation: str,
    key: bytes,
    iv: Optional[bytes] = None
) -> SymmetricCrypto:
    """
    创建对称加密实例
    
    这是一个工厂函数，用于创建 SymmetricCrypto 实例。
    
    Args:
        transformation: 转换模式，格式为 "算法/模式/填充"
                       支持: AES/ECB/PKCS5Padding, AES/CBC/PKCS5Padding,
                             DES/ECB/PKCS5Padding, DES/CBC/PKCS5Padding
        key: 加密密钥- AES: 16、24 或 32 字节
             - DES: 8、16 或 24 字节
        iv: 初始化向量
            - CBC 模式必需
            - ECB 模式忽略
            - AES: 16 字节
            - DES: 8 字节
            
    Returns:
        SymmetricCrypto 实例
        
    Raises:
        ValueError: 当参数无效时
    Example:
        # AES-CBC 加密
        crypto = createSymmetricCrypto(
            "AES/CBC/PKCS5Padding",
            key=b"0123456789abcdef",# 16 字节密钥
            iv=b"fedcba9876543210"    # 16 字节 IV
        )
        encrypted = crypto.encrypt(b"Hello, World!")
        decrypted = crypto.decrypt(encrypted)
        
        # AES-ECB 加密（不需要 IV）
        crypto = createSymmetricCrypto(
            "AES/ECB/PKCS5Padding",
            key=b"0123456789abcdef"
        )
        encrypted = crypto.encryptBase64(b"Hello, World!")
    """
    return SymmetricCrypto(transformation, key, iv)


# 导出所有公共接口
__all__ = [
    'md5Encode',
    'md5Encode16',
    'base64Encode',
    'base64Decode',
    'base64DecodeToString',
    'hexEncodeToString',
    'hexDecodeToByteArray',
    'SymmetricCrypto',
    'createSymmetricCrypto',
]