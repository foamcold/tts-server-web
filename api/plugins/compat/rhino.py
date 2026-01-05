"""
Rhino JavaScript语法兼容层

处理 py_mini_racer (V8) 与 Rhino (Android tts-server 项目使用) 的语法差异。
主要转换以下 Rhino 特有语法：
1. Java.type() 调用
2. importPackage/importClass 语句
3. Java风格的类型转换
4. Java String 相关操作
"""

import re
from typing import Callable, List, Tuple, Optional


class RhinoCompatLayer:
    """
    Rhino JavaScript 语法兼容层
    
    将 Rhino 特有的Java 互操作语法转换为纯 JavaScript 代码，
    使其能够在 V8 引擎（py_mini_racer）中执行。
    """
    
    # Java 包导入语句模式
    IMPORT_PACKAGE_PATTERN = re.compile(
        r'importPackage\s*\(\s*([^\)]+)\s*\)\s*;?',
        re.MULTILINE
    )
    
    # Java 类导入语句模式
    IMPORT_CLASS_PATTERN = re.compile(
        r'importClass\s*\(\s*([^\)]+)\s*\)\s*;?',
        re.MULTILINE
    )
    
    # Java.type() 调用模式
    JAVA_TYPE_PATTERN = re.compile(
        r'Java\.type\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    
    # new java.lang.String() 模式
    JAVA_STRING_NEW_PATTERN = re.compile(
        r'new\s+java\.lang\.String\s*\(\s*([^,\)]+)\s*,\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    
    # Java 字节数组字面量模式 (如 [B@xxx)
    JAVA_BYTE_ARRAY_PATTERN = re.compile(
        r'\[B@[a-fA-F0-9]+',
        re.MULTILINE
    )
    
    # Java String.getBytes() 调用模式
    GET_BYTES_PATTERN = re.compile(
        r'\.getBytes\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )
    
    # Packages.xxx引用模式
    PACKAGES_PATTERN = re.compile(
        r'Packages\.([a-zA-Z0-9_.]+)',
        re.MULTILINE
    )
    
    @classmethod
    def preprocess_code(cls, code: str) -> str:
        """
        预处理 JavaScript 代码，转换 Rhino 特有语法
        Args:
            code: 原始 JavaScript 代码
            
        Returns:
            转换后的 JavaScript 代码
        """
        if not code:
            return code
        
        # 按顺序应用所有转换
        transformations: List[Callable[[str], str]] = [
            cls._remove_import_package,
            cls._remove_import_class,
            cls._convert_java_type,
            cls._convert_java_string_new,
            cls._convert_get_bytes,
            cls._remove_packages_reference,
            cls._add_compatibility_shims,
        ]
        
        result = code
        for transform in transformations:
            result = transform(result)
        
        return result
    
    @classmethod
    def _remove_import_package(cls, code: str) -> str:
        """
        移除 importPackage 语句
        
        Rhino 允许使用 importPackage(java.xxx) 导入 Java 包，
        在 V8 中需要移除这些语句。
        """
        return cls.IMPORT_PACKAGE_PATTERN.sub('// [移除] importPackage', code)
    
    @classmethod
    def _remove_import_class(cls, code: str) -> str:
        """
        移除 importClass 语句Rhino 允许使用 importClass(java.xxx.ClassName) 导入 Java 类，
        在 V8 中需要移除这些语句。
        """
        return cls.IMPORT_CLASS_PATTERN.sub('// [移除] importClass', code)
    
    @classmethod
    def _convert_java_type(cls, code: str) -> str:
        """
        转换 Java.type() 调用
        
        Java.type("java.lang.String") 等调用需要替换为 JavaScript 等价物
        或模拟对象。
        """
        def replace_java_type(match: re.Match) -> str:
            java_class = match.group(1)
            
            # 常见 Java 类型的JavaScript 等价映射
            type_mapping = {
                'java.lang.String': 'String',
                'java.lang.Integer': 'Number',
                'java.lang.Long': 'Number',
                'java.lang.Double': 'Number',
                'java.lang.Float': 'Number',
                'java.lang.Boolean': 'Boolean',
                'java.lang.Object': 'Object',
                'java.util.ArrayList': 'Array',
                'java.util.HashMap': 'Object',
                'java.util.Map': 'Object',
                'java.util.List': 'Array',}
            
            if java_class in type_mapping:
                return type_mapping[java_class]
            
            # 对于未知类型，返回一个空对象构造函数
            return f'(function() {{ return Object; }})()'
        
        return cls.JAVA_TYPE_PATTERN.sub(replace_java_type, code)
    
    @classmethod
    def _convert_java_string_new(cls, code: str) -> str:
        """
        转换 new java.lang.String(bytes, charset) 调用
        
        Rhino 中可以直接使用 Java 的 String 构造函数处理字节数组，
        需要转换为 JavaScript 的 TextDecoder。
        """
        def replace_java_string(match: re.Match) -> str:
            bytes_var = match.group(1).strip()
            charset = match.group(2).strip()
            
            # 使用 TextDecoder 处理编码转换
            # 注意：某些编码名称可能需要映射
            charset_mapping = {
                'UTF-8': 'utf-8',
                'UTF8': 'utf-8',
                'GBK': 'gbk',
                'GB2312': 'gb2312',
                'GB18030': 'gb18030',
                'ISO-8859-1': 'iso-8859-1',
                'ASCII': 'ascii',
            }
            
            js_charset = charset_mapping.get(charset.upper(), charset.lower())
            
            # 返回使用 TextDecoder 的等价代码
            return f'new TextDecoder("{js_charset}").decode(new Uint8Array({bytes_var}))'
        
        return cls.JAVA_STRING_NEW_PATTERN.sub(replace_java_string, code)
    
    @classmethod
    def _convert_get_bytes(cls, code: str) -> str:
        """
        转换 String.getBytes(charset) 调用
        
        Java 的 getBytes() 方法需要转换为 JavaScript 的 TextEncoder。
        """
        def replace_get_bytes(match: re.Match) -> str:
            charset = match.group(1).strip()
            charset_mapping = {
                'UTF-8': 'utf-8',
                'UTF8': 'utf-8',}
            
            js_charset = charset_mapping.get(charset.upper(), charset.lower())
            
            # 返回使用自定义 getBytes 函数的调用
            # 实际的 getBytes 函数将在兼容性shim 中定义
            return f'.split("").map(c => c.charCodeAt(0))'
        
        return cls.GET_BYTES_PATTERN.sub(replace_get_bytes, code)
    
    @classmethod
    def _remove_packages_reference(cls, code: str) -> str:
        """
        移除 Packages.xxx 引用
        
        Rhino 中可以使用 Packages.java.xxx 访问 Java 类，
        在 V8 中需要替换为空对象或模拟。
        """
        def replace_packages(match: re.Match) -> str:
            package_path = match.group(1)
            # 返回一个占位符对象
            return f'({{/* Packages.{package_path} */}})'
        
        return cls.PACKAGES_PATTERN.sub(replace_packages, code)
    
    @classmethod
    def _add_compatibility_shims(cls, code: str) -> str:
        """
        添加兼容性垫片代码
        
        在代码开头添加必要的兼容性函数和对象定义。
        """
        # 检查是否需要添加垫片
        needs_shim = any([
            'Java.' in code,
            'importPackage' in code,
            'importClass' in code,
            'Packages.' in code,
            'getBytes' in code,])
        
        if not needs_shim:
            return code
        
        shim_code = '''
//========== Rhino 兼容性垫片 ==========
(function() {
    // 模拟 Java 对象
    if (typeof Java === 'undefined') {
        globalThis.Java = {
            type: function(className) {
                // 返回基本类型的 JavaScript 等价物
                var mapping = {
                    'java.lang.String': String,
                    'java.lang.Integer': Number,
                    'java.lang.Long': Number,
                    'java.lang.Double': Number,
                    'java.lang.Float': Number,
                    'java.lang.Boolean': Boolean,
                    'java.lang.Object': Object,
                    'java.util.ArrayList': Array,
                    'java.util.HashMap': Object
                };
                return mapping[className] || Object;
            }
        };
    }
    
    // 模拟 importPackage 函数（空操作）
    if (typeof importPackage === 'undefined') {
        globalThis.importPackage = function() {};
    }
    
    // 模拟 importClass 函数（空操作）
    if (typeof importClass === 'undefined') {
        globalThis.importClass = function() {};
    }
    
    // 模拟 Packages 对象
    if (typeof Packages === 'undefined') {
        globalThis.Packages = new Proxy({}, {
            get: function(target, prop) {
                return new Proxy({}, {
                    get: function() { return function() {}; }
                });
            }
        });
    }
    
    // 为 String 原型添加 getBytes 方法（如果不存在）
    if (!String.prototype.getBytes) {
        String.prototype.getBytes = function(charset) {
            charset = charset || 'UTF-8';
            // 简单实现：返回 UTF-8 编码的字节数组
            var bytes = [];
            for (var i = 0; i < this.length; i++) {
                var code = this.charCodeAt(i);
                if (code < 0x80) {
                    bytes.push(code);
                } else if (code < 0x800) {
                    bytes.push(0xc0 | (code >> 6));
                    bytes.push(0x80 | (code & 0x3f));
                } else if (code < 0x10000) {
                    bytes.push(0xe0 | (code >> 12));
                    bytes.push(0x80 | ((code >> 6) & 0x3f));
                    bytes.push(0x80 | (code & 0x3f));
                }
            }
            return bytes;
        };
    }
})();
// ========== 垫片代码结束 ==========

'''
        return shim_code + code
    
    @staticmethod
    def wrap_java_string(s: str) -> str:
        """
        模拟 Java String 的方法调用
        
        将 Python 字符串包装为具有 Java String 类似方法的对象。
        Args:
            s: Python 字符串
            
        Returns:
            包装后的字符串（目前直接返回原字符串）
        """
        return s
    
    @classmethod
    def detect_rhino_features(cls, code: str) -> List[str]:
        """
        检测代码中使用的 Rhino 特有功能
        
        Args:
            code: JavaScript 代码
            
        Returns:
            检测到的 Rhino 特性列表
        """
        features = []
        
        if cls.IMPORT_PACKAGE_PATTERN.search(code):
            features.append('importPackage')
        
        if cls.IMPORT_CLASS_PATTERN.search(code):
            features.append('importClass')
        
        if cls.JAVA_TYPE_PATTERN.search(code):
            features.append('Java.type')
        
        if cls.JAVA_STRING_NEW_PATTERN.search(code):
            features.append('new java.lang.String')
        
        if cls.GET_BYTES_PATTERN.search(code):
            features.append('String.getBytes')
        
        if cls.PACKAGES_PATTERN.search(code):
            features.append('Packages')
        
        return features


def preprocess_rhino_code(code: str) -> str:
    """
    预处理 Rhino JavaScript 代码的便捷函数
    
    Args:
        code: 原始 JavaScript 代码
        
    Returns:
        转换后的 JavaScript 代码
    """
    return RhinoCompatLayer.preprocess_code(code)


def remove_java_imports(code: str) -> str:
    """
    移除 Java 导入语句的便捷函数
    
    Args:
        code: 原始 JavaScript 代码
        
    Returns:
        移除导入语句后的代码
    """
    code = RhinoCompatLayer._remove_import_package(code)
    code = RhinoCompatLayer._remove_import_class(code)
    return code


def convert_java_types(code: str) -> str:
    """
    转换 Java 类型引用的便捷函数
    
    Args:
        code: 原始 JavaScript 代码
        
    Returns:
        转换类型引用后的代码
    """
    code = RhinoCompatLayer._convert_java_type(code)
    code = RhinoCompatLayer._convert_java_string_new(code)
    code = RhinoCompatLayer._convert_get_bytes(code)
    return code