"""
文件系统运行时模块
提供安全的文件操作 API，供JavaScript插件调用
"""

from pathlib import Path
from typing import List
import shutil


class FileSystem:
    """
    插件文件系统，提供安全的文件操作
    所有路径操作都限制在指定的基础目录内，防止路径遍历攻击。
    """
    
    def __init__(self, base_dir: str = "data/plugins"):
        """
        初始化文件系统，设置基础目录
        
        Args:
            base_dir: 插件数据的基础目录，默认为 data/plugins
        """
        self._base_dir = Path(base_dir).resolve()
        # 自动创建基础目录
        self._base_dir.mkdir(parents=True, exist_ok=True)
    
    def _safe_path(self, path: str) -> Path:
        """
        验证并返回安全的路径，防止路径遍历攻击
        
        Args:
            path: 相对路径字符串
            
        Returns:
            解析后的绝对路径
        Raises:
            ValueError: 当路径尝试访问基础目录外的位置时
        """
        # 规范化路径，移除 . 和 ..
        # 首先将输入路径与基础目录组合
        target_path = (self._base_dir / path).resolve()
        
        # 验证目标路径是否在基础目录内
        try:
            target_path.relative_to(self._base_dir)
        except ValueError:
            raise ValueError(f"路径遍历攻击检测:禁止访问基础目录外的路径 '{path}'")
        
        return target_path
    
    def exists(self, path: str) -> bool:
        """
        检查文件或目录是否存在
        
        Args:
            path: 相对于基础目录的路径
            
        Returns:
            如果文件或目录存在返回 True，否则返回 False
        """
        try:
            safe_path = self._safe_path(path)
            return safe_path.exists()
        except ValueError:
            return False
        except OSError:
            return False
    
    def readText(self, path: str, encoding: str = 'utf-8') -> str:
        """
        读取文本文件内容
        
        Args:
            path: 相对于基础目录的文件路径
            encoding: 文件编码，默认为 utf-8
            
        Returns:
            文件的文本内容
            
        Raises:
            ValueError: 路径不安全时
            FileNotFoundError: 文件不存在时
            IOError: 读取失败时
        """
        safe_path = self._safe_path(path)
        
        if not safe_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        if not safe_path.is_file():
            raise IOError(f"路径不是文件: {path}")
        
        try:
            return safe_path.read_text(encoding=encoding)
        except PermissionError:
            raise IOError(f"没有权限读取文件: {path}")
        except UnicodeDecodeError as e:
            raise IOError(f"文件编码错误: {path}, {str(e)}")
    
    def readBytes(self, path: str) -> bytes:
        """
        读取文件字节内容
        
        Args:
            path: 相对于基础目录的文件路径
            
        Returns:
            文件的字节内容
            
        Raises:
            ValueError: 路径不安全时
            FileNotFoundError: 文件不存在时
            IOError: 读取失败时
        """
        safe_path = self._safe_path(path)
        
        if not safe_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        if not safe_path.is_file():
            raise IOError(f"路径不是文件: {path}")
        
        try:
            return safe_path.read_bytes()
        except PermissionError:
            raise IOError(f"没有权限读取文件: {path}")
    
    def writeText(self, path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        写入文本文件
        
        Args:
            path: 相对于基础目录的文件路径
            content: 要写入的文本内容
            encoding: 文件编码，默认为 utf-8
            
        Returns:
            写入成功返回 True
            
        Raises:
            ValueError: 路径不安全时
            IOError: 写入失败时
        """
        safe_path = self._safe_path(path)
        
        try:
            # 确保父目录存在
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_text(content, encoding=encoding)
            return True
        except PermissionError:
            raise IOError(f"没有权限写入文件: {path}")
        except OSError as e:
            raise IOError(f"写入文件失败: {path}, {str(e)}")
    
    def writeBytes(self, path: str, content: bytes) -> bool:
        """
        写入字节文件
        
        Args:
            path: 相对于基础目录的文件路径
            content: 要写入的字节内容
            
        Returns:
            写入成功返回 True
            
        Raises:
            ValueError: 路径不安全时
            IOError: 写入失败时
        """
        safe_path = self._safe_path(path)
        
        try:
            # 确保父目录存在
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            safe_path.write_bytes(content)
            return True
        except PermissionError:
            raise IOError(f"没有权限写入文件: {path}")
        except OSError as e:
            raise IOError(f"写入文件失败: {path}, {str(e)}")
    
    def listFiles(self, path: str = "") -> List[str]:
        """
        列出目录下的文件和子目录
        
        Args:
            path: 相对于基础目录的目录路径，默认为基础目录根
            
        Returns:
            文件和目录名称列表
            
        Raises:
            ValueError: 路径不安全时
            FileNotFoundError: 目录不存在时
            IOError: 读取失败时
        """
        if path == "" or path == ".":
            safe_path = self._base_dir
        else:
            safe_path = self._safe_path(path)
        
        if not safe_path.exists():
            raise FileNotFoundError(f"目录不存在: {path}")
        
        if not safe_path.is_dir():
            raise IOError(f"路径不是目录: {path}")
        
        try:
            return [item.name for item in safe_path.iterdir()]
        except PermissionError:
            raise IOError(f"没有权限读取目录: {path}")
    
    def mkdir(self, path: str) -> bool:
        """
        创建目录（单层）
        
        Args:
            path: 相对于基础目录的目录路径
            
        Returns:
            创建成功返回 True，目录已存在也返回 True
            
        Raises:
            ValueError: 路径不安全时
            IOError: 创建失败时
        """
        safe_path = self._safe_path(path)
        
        try:
            safe_path.mkdir(exist_ok=True)
            return True
        except FileExistsError:
            # 路径存在但是文件而非目录
            if safe_path.is_file():
                raise IOError(f"路径已存在且为文件: {path}")
            return True
        except PermissionError:
            raise IOError(f"没有权限创建目录: {path}")
        except OSError as e:
            raise IOError(f"创建目录失败: {path}, {str(e)}")
    
    def mkdirs(self, path: str) -> bool:
        """
        递归创建目录（包括所有父目录）
        
        Args:
            path: 相对于基础目录的目录路径
            
        Returns:
            创建成功返回 True，目录已存在也返回 True
            
        Raises:
            ValueError: 路径不安全时
            IOError: 创建失败时
        """
        safe_path = self._safe_path(path)
        
        try:
            safe_path.mkdir(parents=True, exist_ok=True)
            return True
        except FileExistsError:
            # 路径存在但是文件而非目录
            if safe_path.is_file():
                raise IOError(f"路径已存在且为文件: {path}")
            return True
        except PermissionError:
            raise IOError(f"没有权限创建目录: {path}")
        except OSError as e:
            raise IOError(f"创建目录失败: {path}, {str(e)}")
    
    def delete(self, path: str) -> bool:
        """
        删除文件或目录
        
        如果是目录，会递归删除所有内容。
        
        Args:
            path: 相对于基础目录的路径
            
        Returns:
            删除成功返回 True，路径不存在返回 False
            
        Raises:
            ValueError: 路径不安全时
            IOError: 删除失败时
        """
        safe_path = self._safe_path(path)
        
        if not safe_path.exists():
            return False
        
        try:
            if safe_path.is_file():
                safe_path.unlink()
            else:
                shutil.rmtree(safe_path)
            return True
        except PermissionError:
            raise IOError(f"没有权限删除: {path}")
        except OSError as e:
            raise IOError(f"删除失败: {path}, {str(e)}")
    
    def copy(self, src: str, dst: str) -> bool:
        """
        复制文件
        
        Args:
            src: 源文件路径（相对于基础目录）
            dst: 目标文件路径（相对于基础目录）
            
        Returns:
            复制成功返回 True
            
        Raises:
            ValueError: 路径不安全时
            FileNotFoundError: 源文件不存在时
            IOError: 复制失败时
        """
        safe_src = self._safe_path(src)
        safe_dst = self._safe_path(dst)
        
        if not safe_src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        if not safe_src.is_file():
            raise IOError(f"源路径不是文件: {src}")
        
        try:
            # 确保目标父目录存在
            safe_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(safe_src, safe_dst)
            return True
        except PermissionError:
            raise IOError(f"没有权限复制文件: {src} -> {dst}")
        except OSError as e:
            raise IOError(f"复制文件失败: {src} -> {dst}, {str(e)}")
    
    def move(self, src: str, dst: str) -> bool:
        """
        移动文件
        
        Args:
            src: 源文件路径（相对于基础目录）
            dst: 目标文件路径（相对于基础目录）
            
        Returns:
            移动成功返回 TrueRaises:
            ValueError: 路径不安全时
            FileNotFoundError: 源文件不存在时
            IOError: 移动失败时
        """
        safe_src = self._safe_path(src)
        safe_dst = self._safe_path(dst)
        
        if not safe_src.exists():
            raise FileNotFoundError(f"源文件不存在: {src}")
        
        try:
            # 确保目标父目录存在
            safe_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(safe_src), str(safe_dst))
            return True
        except PermissionError:
            raise IOError(f"没有权限移动文件: {src} -> {dst}")
        except OSError as e:
            raise IOError(f"移动文件失败: {src} -> {dst}, {str(e)}")
    
    def getBasePath(self) -> str:
        """
        获取基础目录的绝对路径
        
        Returns:
            基础目录的绝对路径字符串
        """
        return str(self._base_dir)
    
    def getAbsolutePath(self, path: str) -> str:
        """
        获取指定路径的绝对路径
        
        Args:
            path: 相对于基础目录的路径
            
        Returns:
            绝对路径字符串
            
        Raises:
            ValueError: 路径不安全时
        """
        safe_path = self._safe_path(path)
        return str(safe_path)
    
    def isFile(self, path: str) -> bool:
        """
        检查路径是否为文件
        
        Args:
            path: 相对于基础目录的路径
            
        Returns:
            如果是文件返回 True，否则返回 False
        """
        try:
            safe_path = self._safe_path(path)
            return safe_path.is_file()
        except ValueError:
            return False
        except OSError:
            return False
    
    def isDirectory(self, path: str) -> bool:
        """
        检查路径是否为目录
        
        Args:
            path: 相对于基础目录的路径
            
        Returns:
            如果是目录返回 True，否则返回 False
        """
        try:
            safe_path = self._safe_path(path)
            return safe_path.is_dir()
        except ValueError:
            return False
        except OSError:
            return False
    
    def getFileSize(self, path: str) -> int:
        """
        获取文件大小
        
        Args:
            path: 相对于基础目录的文件路径
            
        Returns:
            文件大小（字节）
            
        Raises:
            ValueError: 路径不安全时
            FileNotFoundError: 文件不存在时
            IOError: 获取失败时
        """
        safe_path = self._safe_path(path)
        
        if not safe_path.exists():
            raise FileNotFoundError(f"文件不存在: {path}")
        
        if not safe_path.is_file():
            raise IOError(f"路径不是文件: {path}")
        
        try:
            return safe_path.stat().st_size
        except PermissionError:
            raise IOError(f"没有权限访问文件: {path}")


# 导出所有公共接口
__all__ = ['FileSystem']