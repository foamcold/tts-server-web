"""
插件引擎核心模块

负责加载、执行和管理 JavaScript 插件。
使用 py_mini_racer (V8 引擎) 执行 JavaScript 代码，
并通过 ttsrv 运行时对象提供 API给插件调用。
"""

from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import asyncio
import json
import logging
import base64
import traceback

import quickjs

from .runtime.ttsrv import TtsrvRuntime
from .runtime.filesystem import FileSystem
from .runtime.crypto import createSymmetricCrypto,SymmetricCrypto
from .types.plugin import PluginConfig, PluginVoice, PluginLocale, PluginAudioResult
from .compat.rhino import RhinoCompatLayer

logger = logging.getLogger(__name__)


class PluginEngine:
    """
    插件引擎，负责加载和执行 JavaScript 插件
    
    使用 py_mini_racer (V8 引擎) 执行插件代码，
    通过注入ttsrv 对象提供运行时 API。
    
    主要功能：
    - 加载和卸载插件
    - 执行PluginJS.getAudio获取音频
    - 执行 PluginJS.getLocales/getVoices 获取配置
    - 处理 Rhino 语法兼容
    示例:
        config = PluginConfig(pluginId="test", code="...")
        engine = PluginEngine(config)
        engine.load()
        result = await engine.get_audio("你好", "voice1", "zh-CN")
        engine.unload()
    """
    
    # 默认执行超时时间（秒）
    DEFAULT_TIMEOUT = 30.0
    
    def __init__(self, plugin_config: PluginConfig):
        """
        初始化插件引擎
        
        Args:
            plugin_config: 插件配置对象，包含插件代码和元数据
        """
        self._config = plugin_config
        self._runtime = TtsrvRuntime(
            plugin_id=plugin_config.pluginId,
            user_vars=plugin_config.userVars,
            def_vars=plugin_config.defVars
        )
        self._fs = FileSystem(base_dir=f"data/plugins/{plugin_config.pluginId}")
        self._ctx: Optional[quickjs.Context] = None  # type: ignore[valid-type]
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._loaded = False
        self._error: Optional[str] = None
        # 加密对象存储
        self._crypto_objects: Dict[str, SymmetricCrypto] = {}
        self._crypto_counter = 0
        logger.debug(f"PluginEngine 初始化: plugin_id={plugin_config.pluginId}")
    
    def load(self) -> bool:
        """
        加载插件，初始化 JavaScript 上下文
        
        执行以下步骤：
        1. 创建 MiniRacer 上下文
        2. 使用 RhinoCompatLayer 预处理代码
        3. 注入 ttsrv 运行时对象
        4. 执行插件代码
        Returns:
            加载成功返回 True，失败返回 False
        """
        if self._loaded:
            logger.warning(f"插件已加载: {self._config.pluginId}")
            return True
        
        try:
            # 创建 JavaScript 上下文
            self._ctx = quickjs.Context()
            
            # 注入运行时 API
            self._inject_runtime(self._ctx)
            
            # 预处理代码（Rhino 兼容）
            processed_code = RhinoCompatLayer.preprocess_code(self._config.code)
            
            # 检测使用的 Rhino 特性（用于调试）
            rhino_features = RhinoCompatLayer.detect_rhino_features(self._config.code)
            if rhino_features:
                logger.info(f"检测到 Rhino 特性: {rhino_features}")
            
            # 执行插件代码
            self._ctx.eval(processed_code)
            
            # 注入时区校正函数（覆盖插件中可能有问题的实现）
            # 某些插件（如纳米AI）的 getISO8601Time() 函数使用本地时间方法
            # 但硬编码了 +08:00 偏移，在非北京时区服务器上会导致时间错误
            self._ctx.eval('''
//========== 时区校正函数 ==========
//覆盖插件中可能有问题的 getISO8601Time() 实现
// 确保无论服务器在哪个时区运行，都能返回正确的北京时间
function getISO8601Time() {
    const now = new Date();
    // 将当前时间转换为北京时间(UTC+8)
    const beijingOffset = 8 * 60 * 60 * 1000;
    const utcTime = now.getTime() + now.getTimezoneOffset() * 60 * 1000;
    const beijingTime = new Date(utcTime + beijingOffset);
    
    const year = beijingTime.getFullYear();
    const month = String(beijingTime.getMonth() + 1).padStart(2, '0');
    const day = String(beijingTime.getDate()).padStart(2, '0');
    const hours = String(beijingTime.getHours()).padStart(2, '0');
    const minutes = String(beijingTime.getMinutes()).padStart(2, '0');
    const seconds = String(beijingTime.getSeconds()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}+08:00`;
}
//========== 时区校正函数结束 ==========
''')
            
            # 调用 onLoadData（如果存在），添加异常捕获
            self._ctx.eval('''
                try {
                    if (typeof EditorJS !== "undefined" && typeof EditorJS.onLoadData === "function") {
                        console.log("[DEBUG] 调用 EditorJS.onLoadData()");
                        EditorJS.onLoadData();
                    }
                    if (typeof PluginJS !== "undefined" && typeof PluginJS.onLoad === "function") {
                        console.log("[DEBUG] 调用 PluginJS.onLoad()");
                        PluginJS.onLoad();
                    }
                } catch (e) {
                    console.error("[ERROR] 插件初始化回调失败: " + e.message + "\\nStack: " + e.stack);
                    // 不抛出异常，允许插件继续加载，防止整个系统崩溃
                }
            ''')
            
            self._loaded = True
            self._error = None
            logger.info(f"插件加载成功: {self._config.pluginId}")
            return True
            
        except Exception as e:
            self._error = str(e)
            logger.error(f"插件加载失败: {self._config.pluginId}, 错误: {e}")
            self._cleanup()
            return False
    
    def unload(self) -> None:
        """
        卸载插件，释放资源
        
        清理 JavaScript 上下文和线程池资源。
        """
        if not self._loaded:
            return
        
        try:
            # 调用 onUnload（如果存在）
            if self._ctx:
                try:
                    self._ctx.eval('''
                        if (typeof PluginJS !== "undefined" && typeof PluginJS.onUnload === "function") {
                            PluginJS.onUnload();
                        }
                    ''')
                except Exception:
                    pass  # 忽略卸载回调错误
        finally:
            self._cleanup()
            logger.info(f"插件已卸载: {self._config.pluginId}")
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._ctx = None
        self._loaded = False
    
    def _inject_runtime(self, ctx: quickjs.Context) -> None:  # type: ignore[valid-type]
        """
        注入运行时到 JavaScript 上下文
        
        Args:
            ctx: quickjs.Context 上下文实例
        """
        # 注入 Python 回调函数
        ctx.add_callable('__py_httpGet', self._js_http_get)
        ctx.add_callable('__py_httpPost', self._js_http_post)
        ctx.add_callable('__py_md5Encode', self._js_md5_encode)
        ctx.add_callable('__py_md5Encode16', self._js_md5_encode16)
        ctx.add_callable('__py_base64Encode', self._js_base64_encode)
        ctx.add_callable('__py_base64Decode', self._js_base64_decode)
        ctx.add_callable('__py_base64DecodeToString', self._js_base64_decode_to_string)
        ctx.add_callable('__py_hexEncode', self._js_hex_encode)
        ctx.add_callable('__py_hexDecode', self._js_hex_decode)
        ctx.add_callable('__py_log', self._js_log)
        ctx.add_callable('__py_toast', self._js_toast)
        ctx.add_callable('__py_sleep', self._js_sleep)
        ctx.add_callable('__py_randomUUID', self._js_random_uuid)
        ctx.add_callable('__py_timeFormat', self._js_time_format)
        ctx.add_callable('__py_setVar', self._js_set_var)
        ctx.add_callable('__py_getVar', self._js_get_var)
        ctx.add_callable('__py_removeVar', self._js_remove_var)
        ctx.add_callable('__py_getAudioSampleRate', self._js_get_audio_sample_rate)
        # 文件系统
        ctx.add_callable('__py_fsExists', self._js_fs_exists)
        ctx.add_callable('__py_fsReadText', self._js_fs_read_text)
        ctx.add_callable('__py_fsWriteFile', self._js_fs_write_file)
        ctx.add_callable('__py_fsReadFile', self._js_fs_read_file)
        ctx.add_callable('__py_fsRm', self._js_fs_rm)
        ctx.add_callable('__py_fsRename', self._js_fs_rename)
        ctx.add_callable('__py_fsMkdir', self._js_fs_mkdir)
        ctx.add_callable('__py_fsCopy', self._js_fs_copy)
        ctx.add_callable('__py_fsIsFile', self._js_fs_is_file)
        # Base64 编解码函数（浏览器标准 API 兼容）
        # atob 返回的是"二进制字符串"，每个字符的码点对应一个字节值（0-255）
        # 使用 latin-1（ISO-8859-1）编码，因为它是 1:1 映射字节到字符
        ctx.add_callable('__py_atob', lambda s: base64.b64decode(s).decode('latin-1'))
        ctx.add_callable('__py_btoa', lambda s: base64.b64encode(s.encode('latin-1')).decode('ascii'))
        # Base64 直接解码为字节数组（避免二进制字符串中空字符导致的截断问题）
        ctx.add_callable('__py_base64ToByteArray', self._js_base64_to_byte_array)
        # 字节数组直接编码为 Base64（避免通过二进制字符串中间转换导致的截断问题）
        ctx.add_callable('__py_arrayToBase64', self._js_array_to_base64)
        # 字符串和字节转换
        ctx.add_callable('__py_strToBytes', lambda s: self._js_str_to_bytes(s))
        ctx.add_callable('__py_bytesToStr', lambda b, e="utf-8": self._js_bytes_to_str(b, e))
        # 对称加密
        ctx.add_callable('__py_createSymmetricCrypto', lambda t, k, iv="null": self._js_create_symmetric_crypto(t, k, iv))
        ctx.add_callable('__py_cryptoEncryptBase64', lambda cid, d: self._js_crypto_encrypt_base64(cid, d))
        ctx.add_callable('__py_cryptoDecryptBase64', lambda cid, d: self._js_crypto_decrypt_base64(cid, d))
        ctx.add_callable('__py_cryptoDecryptBase64Str', lambda cid, d: self._js_crypto_decrypt_base64_str(cid, d))
        # 定义 JavaScript 端的ttsrv 代理对象
        ttsrv_js = '''
//========== ttsrv 运行时对象 ==========

// Base64 编解码函数（浏览器标准 API）
function atob(base64Str) {
    return __py_atob(base64Str);
}

function btoa(str) {
    return __py_btoa(str);
}

// 创建模拟 OkHttp ResponseBody 的对象
function __createResponseBody(bodyStr, bodyBytesBase64) {
    return {
        _bodyStr: bodyStr,
        _bodyBytesBase64: bodyBytesBase64,
        
        // 返回字符串内容
        string: function() {
            return this._bodyStr;
        },
        
        // 返回字节数组
        bytes: function() {
            // 将 Base64 解码为字节数组
            // 注意：使用 __py_base64ToByteArray 直接在Python 端解码，
            // 避免 atob() 返回的二进制字符串中空字符(null)导致的截断问题
            if (!this._bodyBytesBase64) {
                return [];
            }
            var bytesJson = __py_base64ToByteArray(this._bodyBytesBase64);
            return JSON.parse(bytesJson);
        },
        
        // 返回原始 Base64 编码的字节数据（避免中间转换导致的数据截断）
        bytesBase64: function() {
            return this._bodyBytesBase64 || '';
        },
        
        // 返回字节流（简化实现，返回字节数组）
        byteStream: function() {
            return this.bytes();
        }
    };
}

// 创建模拟 OkHttp Response 的对象
function __createResponse(rawResult) {
if (!rawResult) return null;
var _code = rawResult.code || 0;
var _message = rawResult.message || '';
var _headers = rawResult.headers || {};
var _body = __createResponseBody(rawResult.body || '', rawResult.bodyBytes || '');

return {
        // 返回 HTTP 状态码
        code: function() {
            return _code;
        },
        
        // 返回状态消息
        message: function() {
            return _message;
        },
        
        // 返回状态消息（别名）
        status: function() {
            return _message;
        },
        
        // 返回响应头
        headers: function() {
            return _headers;
        },
        
        // 返回 ResponseBody 对象
        body: function() {
            return _body;
        },
        
        // 兼容性方法：直接返回响应文本
        text: function() {
            return _body.string();
        },
        
        // 检查请求是否成功
        isSuccessful: function() {
            return _code >= 200 && _code < 300;
        }
    };
}

var ttsrv = {
    // HTTP 方法
    httpGet: function(url, headers) {
        var headersJson = JSON.stringify(headers || {});
        var result = __py_httpGet(url, headersJson);
        if (!result) return null;
        var rawResult = JSON.parse(result);
        return __createResponse(rawResult);
    },
    httpPost: function(url, body, headers) {
        var headersJson = JSON.stringify(headers || {});
        var result = __py_httpPost(url, body || "", headersJson);
        var rawResult = JSON.parse(result);
        return __createResponse(rawResult);
    },
    
    // 加密/编码方法
    md5Encode: function(data) {
        return __py_md5Encode(data);
    },
    md5Encode16: function(data) {
        return __py_md5Encode16(data);
    },
    base64Encode: function(data) {
        return __py_base64Encode(data);
    },
    base64Decode: function(data) {
        return __py_base64Decode(data);
    },
    base64DecodeToString: function(data, encoding) {
        return __py_base64DecodeToString(data, encoding || "utf-8");
    },
    hexEncodeToString: function(data) {
        // data 应该是数组或类数组
        var arr = Array.isArray(data) ? data : Array.from(data);
        return __py_hexEncode(JSON.stringify(arr));
    },
    hexDecodeToByteArray: function(hexStr) {
        var result = __py_hexDecode(hexStr);
        return JSON.parse(result);
    },
    
    // 字符串/字节转换
    strToBytes: function(str) {
        return JSON.parse(__py_strToBytes(str));
    },
    
    bytesToStr: function(bytes, encoding) {
        return __py_bytesToStr(JSON.stringify(Array.from(bytes)), encoding || "utf-8");
    },
    
    // 对称加密
    createSymmetricCrypto: function(transformation, key, iv) {
        var keyJson = JSON.stringify(Array.from(key));
        var ivJson = iv ? JSON.stringify(Array.from(iv)) : "null";
        var cryptoId = __py_createSymmetricCrypto(transformation, keyJson, ivJson);
        // 内部辅助函数：将数据转换为字节数组 JSON
        function toDataJson(data) {
            if (typeof data === 'string') {
                // 将字符串转换为 UTF-8 字节数组
                var bytes = [];
                for (var i = 0; i < data.length; i++) {
                    var code = data.charCodeAt(i);
                    if (code < 128) {
                        bytes.push(code);
                    } else if (code < 2048) {
                        bytes.push(192 | (code >> 6));
                        bytes.push(128 | (code & 63));
                    } else {
                        bytes.push(224 | (code >> 12));
                        bytes.push(128 | ((code >> 6) & 63));
                        bytes.push(128 | (code & 63));
                    }
                }
                return JSON.stringify(bytes);
            } else {
                return JSON.stringify(Array.from(data));
            }
        }
        
        return {
            // 加密数据返回 Base64 字符串
            encryptBase64: function(data) {
                return __py_cryptoEncryptBase64(cryptoId, toDataJson(data));
            },
            // 加密数据返回字节数组（与 hutool SymmetricCrypto.encrypt兼容）
            encrypt: function(data) {
                // 先加密为Base64，再解码为字节数组
                var base64Result = __py_cryptoEncryptBase64(cryptoId, toDataJson(data));
                // 使用 Base64 解码
                var binary = atob(base64Result);
                var len = binary.length;
                var bytes = new Array(len);
                for (var i = 0; i < len; i++) {
                    // 使用 & 0xFF 确保结果在0-255 范围内
                    bytes[i] = binary.charCodeAt(i) & 0xFF;
                }
                return bytes;
            },
            
            // 加密数据返回Hex 字符串（与 hutool SymmetricCrypto.encryptHex 兼容）
            encryptHex: function(data) {
                // 先加密为 Base64，再转换为 Hex
                var base64Result = __py_cryptoEncryptBase64(cryptoId, toDataJson(data));
                var binary = atob(base64Result);
                var hex = '';
                for (var i = 0; i < binary.length; i++) {
                    // 使用 & 0xFF 确保结果在 0-255 范围内
                    var byte = binary.charCodeAt(i) & 0xFF;
                    hex += ('0' + byte.toString(16)).slice(-2);
                }
                return hex;
            },
            
            // 解密Base64 编码的密文，返回字节数组
            decryptBase64: function(base64Str) {
                return JSON.parse(__py_cryptoDecryptBase64(cryptoId, base64Str));
            },
            
            // 解密 Base64 编码的密文，返回解密后的字符串
            decryptBase64Str: function(base64Str) {
                return __py_cryptoDecryptBase64Str(cryptoId, base64Str);
            },
            
            // 解密 Base64 编码的密文，返回解密后的字符串
            // （与 hutool SymmetricCrypto.decryptStr 兼容，功能等同于 decryptBase64Str）
            decryptStr: function(base64Str) {
                return __py_cryptoDecryptBase64Str(cryptoId, base64Str);
            },
            
            // 解密字节数组（与 hutool SymmetricCrypto.decrypt 兼容）
            // data为 Base64 字符串时，返回解密后的字节数组
            decrypt: function(data) {
                // 如果传入的是 Base64 字符串，直接解密
                if (typeof data === 'string') {
                    return JSON.parse(__py_cryptoDecryptBase64(cryptoId, data));
                }
                // 如果传入的是字节数组，先编码为 Base64再解密
                var binary = '';
                for (var i = 0; i < data.length; i++) {
                    binary += String.fromCharCode(data[i]);
                }
                var base64Str = btoa(binary);
                return JSON.parse(__py_cryptoDecryptBase64(cryptoId, base64Str));
            }
        };
    },
    
    // 工具方法
    log: function(message) {
        __py_log(String(message));
    },
    toast: function(message) {
        __py_toast(String(message));
    },
    sleep: function(ms) {
        __py_sleep(ms);
    },
    randomUUID: function() {
        return __py_randomUUID();
    },
    timeFormat: function(timestamp, format) {
        return __py_timeFormat(timestamp ||0, format || "%Y-%m-%d %H:%M:%S");
    },
    // 变量管理
    setVar: function(key, value) {
        __py_setVar(key, JSON.stringify(value));
    },
    getVar: function(key, defaultValue) {
        var result = __py_getVar(key);
        if (result === null || result === undefined || result === "") {
            return defaultValue;
        }
        try {
            return JSON.parse(result);
        } catch (e) {
            return result;
        }
    },
    removeVar: function(key) {
        return __py_removeVar(key);
    },
    
    // 音频工具
    getAudioSampleRate: function(audioData) {
        // audioData 应该是Base64 字符串或字节数组
        if (typeof audioData === "string") {
            return __py_getAudioSampleRate(audioData);
        } else {
            // 转换为 Base64
            var base64 = ttsrv.base64Encode(audioData);
            return __py_getAudioSampleRate(base64);
        }
    },
    
    // tts 数据对象（用于存储临时数据）
    tts: {
        data: {}
    }
};

var http = {
    get: function(url, headers) {
        return ttsrv.httpGet(url, headers);
    },
    post: function(url, body, headers) {
        return ttsrv.httpPost(url, body, headers);
    }
};

var fs = {
    exists: function(path) {
        return __py_fsExists(path);
    },
    readText: function(path, encoding) {
        return __py_fsReadText(path, encoding || "utf-8");
    },
    readFile: function(path) {
        var bytesJson = __py_fsReadFile(path);
        var bytes = JSON.parse(bytesJson);
        return new Uint8Array(bytes);
    },
    writeFile: function(path, body, encoding) {
        if (typeof body === 'string') {
            return __py_fsWriteFile(path, body, "string", encoding || "utf-8");
        } else if (body instanceof Uint8Array || Array.isArray(body)) {
            var bytesJson = JSON.stringify(Array.from(body));
            return __py_fsWriteFile(path, bytesJson, "bytes", "");
        }
        return false;
    },
    rm: function(path, recursive) {
        return __py_fsRm(path, !!recursive);
    },
    rename: function(path, newPath) {
        return __py_fsRename(path, newPath);
    },
    mkdir: function(path, recursive) {
        return __py_fsMkdir(path, !!recursive);
    },
    copy: function(path, newPath, overwrite) {
        return __py_fsCopy(path, newPath, !!overwrite);
    },
    isFile: function(path) {
        return __py_fsIsFile(path);
    }
};

// 控制台兼容
var console = {
    log: function() {
        var args = Array.prototype.slice.call(arguments);
        ttsrv.log(args.map(String).join(" "));
    },
    error: function() {
        var args = Array.prototype.slice.call(arguments);
        ttsrv.log("[ERROR] " + args.map(String).join(" "));
    },
    warn: function() {
        var args = Array.prototype.slice.call(arguments);
        ttsrv.log("[WARN] " + args.map(String).join(" "));
    },
    info: function() {
        var args = Array.prototype.slice.call(arguments);
        ttsrv.log("[INFO] " + args.map(String).join(" "));
    },
    debug: function() {
        var args = Array.prototype.slice.call(arguments);
        ttsrv.log("[DEBUG] " + args.map(String).join(" "));
    }
};

// 模拟 require 方法，特别是针对 crypto 模块
function require(moduleName) {
    if (moduleName === 'crypto') {
        return {
            MD5: function(data) {
                var hash = ttsrv.md5Encode(data);
                return {
                    toString: function() {
                        return hash;
                    }
                };
            }
        };
    }
    throw new Error("Cannot find module '" + moduleName + "'");
}
//========== ttsrv 运行时对象结束 ==========
'''
        ctx.eval(ttsrv_js)
        # 设置用户变量
        merged_vars = self._config.get_merged_vars()
        if merged_vars:
            vars_json = json.dumps(merged_vars)
            ctx.eval(f'ttsrv.tts.data = {vars_json};')
    
    #==================== JavaScript 回调实现 ====================
    
    def _js_http_get(self, url: str, headers_json: str) -> str:
        """JavaScript httpGet 回调"""
        try:
            logger.info(f"js_http_get: {url}")
            headers = json.loads(headers_json) if headers_json else {}
            response = self._runtime.httpGet(url, headers)
            
            if response is None:
                return ""
            
            raw_bytes = response.body().bytes()
            body_bytes_base64 = base64.b64encode(raw_bytes).decode('ascii')
            
            result = {
                'code': response.code(),
                'message': response.message(),
                'headers': response.headers(),
                'body': response.body().string(),
                'bodyBytes': body_bytes_base64
            }
            return json.dumps(result)
        except Exception as e:
            logger.error(f"httpGet 失败: {e}")
            return json.dumps({
                'code':0,
                'message': str(e),
                'headers': {},
                'body': '',
                'bodyBytes': ''
            })
    
    def _js_http_post(self, url: str, body: str, headers_json: str) -> str:
        """JavaScript httpPost 回调"""
        try:
            headers = json.loads(headers_json) if headers_json else {}
            response = self._runtime.httpPost(url, body, headers)
            return json.dumps({
                'code': response.code(),
                'message': response.message(),
                'headers': response.headers(),
                'body': response.body().string(),
                'bodyBytes': base64.b64encode(response.body().bytes()).decode('ascii')
            })
        except Exception as e:
            logger.error(f"httpPost 失败: {e}")
            return json.dumps({
                'code': 0,
                'message': str(e),
                'headers': {},
                'body': '',
                'bodyBytes': ''
            })
    
    def _js_md5_encode(self, data: str) -> str:
        """JavaScript md5Encode 回调"""
        return self._runtime.md5Encode(data)
    
    def _js_md5_encode16(self, data: str) -> str:
        """JavaScript md5Encode16 回调"""
        return self._runtime.md5Encode16(data)
    
    def _js_base64_encode(self, data: str) -> str:
        """JavaScript base64Encode 回调"""
        return self._runtime.base64Encode(data)
    
    def _js_base64_decode(self, data: str) -> str:
        """JavaScript base64Decode 回调，返回 Base64 编码的结果"""
        try:
            decoded = self._runtime.base64Decode(data)
            # 返回为Base64 字符串，JavaScript 端再处理
            return base64.b64encode(decoded).decode('ascii')
        except Exception as e:
            logger.error(f"base64Decode 失败: {e}")
            return ''
    
    def _js_base64_decode_to_string(self, data: str, encoding: str) -> str:
        """JavaScript base64DecodeToString 回调"""
        return self._runtime.base64DecodeToString(data, encoding)
    
    def _js_hex_encode(self, data_json: str) -> str:
        """JavaScript hexEncodeToString 回调"""
        try:
            data = json.loads(data_json)
            # 处理 JavaScript 有符号字节
            byte_data = self._convert_js_bytes(data)
            return self._runtime.hexEncodeToString(byte_data)
        except Exception as e:
            logger.error(f"hexEncode 失败: {e}")
            return ''
    
    def _js_hex_decode(self, hex_str: str) -> str:
        """JavaScript hexDecodeToByteArray 回调"""
        try:
            decoded = self._runtime.hexDecodeToByteArray(hex_str)
            return json.dumps(list(decoded))
        except Exception as e:
            logger.error(f"hexDecode 失败: {e}")
            return '[]'
    
    def _js_log(self, message: str) -> None:
        """JavaScript log 回调"""
        self._runtime.log(message)
    
    def _js_toast(self, message: str) -> None:
        """JavaScript toast 回调"""
        self._runtime.toast(message)
    
    def _js_sleep(self, ms: int) -> None:
        """JavaScript sleep 回调"""
        self._runtime.sleep(ms)
    
    def _js_random_uuid(self) -> str:
        """JavaScript randomUUID 回调"""
        return self._runtime.randomUUID()
    
    def _js_time_format(self, timestamp: int, format_str: str) -> str:
        """JavaScript timeFormat 回调"""
        ts = timestamp if timestamp > 0 else None
        return self._runtime.timeFormat(ts, format_str)
    
    def _js_set_var(self, key: str, value_json: str) -> None:
        """JavaScript setVar 回调"""
        try:
            value = json.loads(value_json)
            self._runtime.setVar(key, value)
        except json.JSONDecodeError:
            self._runtime.setVar(key, value_json)
    
    def _js_get_var(self, key: str) -> str:
        """JavaScript getVar 回调"""
        value = self._runtime.getVar(key)
        if value is None:
            return ''
        try:
            return json.dumps(value)
        except (TypeError, ValueError):
            return str(value)
    
    def _js_remove_var(self, key: str) -> bool:
        """JavaScript removeVar 回调"""
        return self._runtime.removeVar(key)
    
    def _js_get_audio_sample_rate(self, audio_base64: str) -> int:
        """JavaScript getAudioSampleRate 回调"""
        try:
            audio_data = base64.b64decode(audio_base64)
            return self._runtime.getAudioSampleRate(audio_data)
        except Exception as e:
            logger.error(f"getAudioSampleRate 失败: {e}")
            return 22050  # 默认采样率
    
    #==================== 文件系统回调 ====================

    def _js_fs_exists(self, path: str) -> bool:
        """检查文件是否存在"""
        return self._fs.exists(path)

    def _js_fs_read_text(self, path: str, encoding: str = 'utf-8') -> str:
        """读取文本文件"""
        try:
            return self._fs.readText(path, encoding)
        except Exception as e:
            logger.error(f"fs.readText 失败: {path}, {e}")
            return ""

    def _js_fs_write_file(self, path: str, body: str, body_type: str, encoding: str = 'utf-8') -> bool:
        """写入文件"""
        try:
            if body_type == "string":
                return self._fs.writeText(path, body, encoding)
            else:
                bytes_data = self._convert_js_bytes(json.loads(body))
                return self._fs.writeBytes(path, bytes_data)
        except Exception as e:
            logger.error(f"fs.writeFile 失败: {path}, {e}")
            return False

    def _js_fs_read_file(self, path: str) -> str:
        """读取二进制文件"""
        try:
            data = self._fs.readBytes(path)
            return json.dumps(list(data))
        except Exception as e:
            logger.error(f"fs.readFile 失败: {path}, {e}")
            return "[]"

    def _js_fs_rm(self, path: str, recursive: bool) -> bool:
        """删除文件或目录"""
        try:
            return self._fs.delete(path)
        except Exception as e:
            logger.error(f"fs.rm 失败: {path}, {e}")
            return False

    def _js_fs_rename(self, path: str, new_path: str) -> bool:
        """重命名文件"""
        try:
            return self._fs.move(path, new_path)
        except Exception as e:
            logger.error(f"fs.rename 失败: {path}, {e}")
            return False

    def _js_fs_mkdir(self, path: str, recursive: bool) -> bool:
        """创建目录"""
        try:
            if recursive:
                return self._fs.mkdirs(path)
            else:
                return self._fs.mkdir(path)
        except Exception as e:
            logger.error(f"fs.mkdir 失败: {path}, {e}")
            return False

    def _js_fs_copy(self, path: str, new_path: str, overwrite: bool) -> bool:
        """复制文件"""
        try:
            # FileSystem.copy 目前不支持 overwrite 参数，需要的话可以后续扩展
            return self._fs.copy(path, new_path)
        except Exception as e:
            logger.error(f"fs.copy 失败: {path}, {e}")
            return False

    def _js_fs_is_file(self, path: str) -> bool:
        """是否为文件"""
        return self._fs.isFile(path)

    def _js_base64_to_byte_array(self, base64_str: str) -> str:
        """
        将 Base64 字符串直接解码为字节数组（JSON 格式）
        
        这个方法用于绕过 QuickJS 的 atob() 函数在处理二进制字符串时
遇到 \\x00 空字符导致截断的问题。直接在 Python 端解码 Base64
        并返回字节数组的 JSON 表示。
        
        Args:
            base64_str: Base64 编码的字符串
            
        Returns:
            字节数组的 JSON 字符串，如 "[82, 73, 70, 70, ...]"
        """
        try:
            if not base64_str:
                logger.debug("[DEBUG] _js_base64_to_byte_array: 输入为空")
                return '[]'
            
            logger.debug(f"[DEBUG] _js_base64_to_byte_array: 输入 Base64 长度 = {len(base64_str)}")
            decoded_bytes = base64.b64decode(base64_str)
            logger.debug(f"[DEBUG] _js_base64_to_byte_array: 解码后字节数 = {len(decoded_bytes)}")
            
            result = json.dumps(list(decoded_bytes))
            logger.debug(f"[DEBUG] _js_base64_to_byte_array: 输出 JSON 长度 = {len(result)}")
            return result
        except Exception as e:
            logger.error(f"base64ToByteArray 失败: {e}")
            logger.error(f"base64ToByteArray 堆栈: {traceback.format_exc()}")
            return '[]'
    
    def _js_array_to_base64(self, array_json: str) -> str:
        """
        将字节数组直接编码为 Base64 字符串
        
        这个方法用于绕过 QuickJS 的 btoa() 函数在处理二进制字符串时
        遇到 \\x00 空字符导致截断的问题。直接在Python 端将字节数组
        编码为 Base64。
        
        Args:
            array_json: 字节数组的 JSON 字符串，如 "[82, 73, 70, 70, ...]"
            
        Returns:
            Base64 编码的字符串
        """
        try:
            if not array_json:
                logger.debug("[DEBUG] _js_array_to_base64: 输入为空")
                return ''
            
            logger.debug(f"[DEBUG] _js_array_to_base64: 输入 JSON 长度 = {len(array_json)}")
            
            # 解析 JSON 数组
            byte_list = json.loads(array_json)
            logger.debug(f"[DEBUG] _js_array_to_base64: 解析得到 {len(byte_list)} 个元素")
            
            # 转换为 bytes（处理有符号字节）
            byte_data = self._convert_js_bytes(byte_list)
            logger.debug(f"[DEBUG] _js_array_to_base64: 转换后字节数 = {len(byte_data)}")
            
            # Base64 编码
            result = base64.b64encode(byte_data).decode('ascii')
            logger.debug(f"[DEBUG] _js_array_to_base64: Base64 编码后长度 = {len(result)}")
            
            return result
        except Exception as e:
            logger.error(f"arrayToBase64 失败: {e}")
            logger.error(f"arrayToBase64 堆栈: {traceback.format_exc()}")
            return ''
    
    #==================== 字符串/字节转换====================
    
    def _convert_js_bytes(self, js_bytes: list) -> bytes:
        """
        将 JavaScript 字节数组转换为 Python bytes
        
        JavaScript 中的字节数组可能包含有符号值（-128 到 127），
        需要转换为无符号值（0 到 255）才能在 Python 中使用。
        
        Args:
            js_bytes: JavaScript 传来的字节数组（可能包含负数）
            
        Returns:
            Python bytes 对象
        """
        # 将有符号字节或任何整数转换为无符号字节（0 到 255）
        # 使用 & 0xFF 确保所有值都在 0-255 范围内
        unsigned_bytes = []
        for b in js_bytes:
            # 确保 b 是整数
            if isinstance(b, float):
                b = int(b)
            # 使用位与操作确保在 0-255 范围内
            unsigned_bytes.append(b & 0xFF)
        return bytes(unsigned_bytes)
    
    def _js_str_to_bytes(self, s: str) -> str:
        """将字符串转换为字节数组（JSON格式）"""
        try:
            return json.dumps(list(s.encode('utf-8')))
        except Exception as e:
            logger.error(f"strToBytes 失败: {e}")
            return '[]'
    
    def _js_bytes_to_str(self, bytes_json: str, encoding: str = 'utf-8') -> str:
        """
        将字节数组转换为字符串
        
        JavaScript 中的有符号字节（-128 到 127）需要转换为无符号字节（0 到 255）
        """
        try:
            bytes_list = json.loads(bytes_json)
            logger.debug(f"[DEBUG] bytesToStr 输入: 长度={len(bytes_list)}, 前10个值={bytes_list[:10] if len(bytes_list) > 10 else bytes_list}")
            
            # 检查是否有超范围的值
            out_of_range = [b for b in bytes_list if not isinstance(b, (int, float)) or b < -128 or b > 255]
            if out_of_range:
                logger.warning(f"[DEBUG] bytesToStr 发现超范围值: {out_of_range[:5]}...")
            
            # 使用辅助方法处理有符号字节
            byte_data = self._convert_js_bytes(bytes_list)
            result = byte_data.decode(encoding)
            logger.debug(f"[DEBUG] bytesToStr 结果: 长度={len(result)}")
            return result
        except Exception as e:
            logger.error(f"bytesToStr 失败: {e}")
            logger.error(f"bytesToStr 堆栈: {traceback.format_exc()}")
            return ''
    
    # ==================== 对称加密 ====================
    
    def _js_create_symmetric_crypto(self, transformation: str, key_json: str, iv_json: str = "null") -> str:
        """
        创建对称加密对象并返回 ID
        
        Args:
            transformation: 转换模式，如 "AES/CBC/PKCS5Padding"
            key_json: 密钥字节数组的 JSON 字符串
            iv_json: 初始化向量字节数组的 JSON 字符串，"null" 表示不使用
        Returns:
            加密对象 ID
        """
        try:
            # 解析密钥（处理 JavaScript 有符号字节）
            key_bytes = self._convert_js_bytes(json.loads(key_json))
            
            # 解析 IV（处理 JavaScript 有符号字节）
            iv_bytes = None
            if iv_json and iv_json != "null":
                iv_bytes = self._convert_js_bytes(json.loads(iv_json))
            
            # 创建加密对象
            crypto = createSymmetricCrypto(transformation, key_bytes, iv_bytes)
            
            # 存储并返回 ID
            self._crypto_counter += 1
            crypto_id = f"crypto_{self._crypto_counter}"
            self._crypto_objects[crypto_id] = crypto
            
            logger.debug(f"创建加密对象: {crypto_id}, 模式: {transformation}")
            return crypto_id
            
        except Exception as e:
            logger.error(f"createSymmetricCrypto 失败: {e}")
            return ""
    
    def _js_crypto_encrypt_base64(self, crypto_id: str, data_json: str) -> str:
        """
        使用加密对象加密数据并返回 Base64 编码结果
        
        Args:
            crypto_id: 加密对象 ID
            data_json: 要加密的字节数组的 JSON 字符串
            
        Returns:
            Base64 编码的加密结果
        """
        try:
            crypto = self._crypto_objects.get(crypto_id)
            if not crypto:
                logger.error(f"加密对象不存在: {crypto_id}")
                return ""
            
            # 处理 JavaScript 有符号字节
            data_bytes = self._convert_js_bytes(json.loads(data_json))
            encrypted_base64 = crypto.encryptBase64(data_bytes)
            return encrypted_base64
            
        except Exception as e:
            logger.error(f"cryptoEncryptBase64 失败: {e}")
            return ""
    
    def _js_crypto_decrypt_base64(self, crypto_id: str, base64_str: str) -> str:
        """
        使用加密对象解密 Base64 编码的数据
        
        Args:
            crypto_id: 加密对象 ID
            base64_str: Base64 编码的加密数据
            
        Returns:
            解密后的字节数组的 JSON 字符串
        """
        try:
            logger.debug(f"[DEBUG] cryptoDecryptBase64 调用: crypto_id={crypto_id}")
            logger.debug(f"[DEBUG] 输入 base64_str 长度: {len(base64_str) if base64_str else 0}")
            
            crypto = self._crypto_objects.get(crypto_id)
            if not crypto:
                logger.error(f"加密对象不存在: {crypto_id}")
                return '[]'
            
            decrypted_bytes = crypto.decryptBase64(base64_str)
            result = json.dumps(list(decrypted_bytes))
            
            logger.debug(f"[DEBUG] cryptoDecryptBase64 解密成功，结果字节数: {len(decrypted_bytes)}")
            return result
            
        except Exception as e:
            logger.error(f"cryptoDecryptBase64 失败: {e}")
            logger.error(f"cryptoDecryptBase64堆栈: {traceback.format_exc()}")
            return '[]'
    
    def _js_crypto_decrypt_base64_str(self, crypto_id: str, base64_str: str) -> str:
        """
        使用加密对象解密 Base64 编码的数据并返回字符串
        
        Args:
            crypto_id: 加密对象 ID
            base64_str: Base64 编码的加密数据
            
        Returns:
            解密后的字符串
        """
        try:
            logger.debug(f"[DEBUG] cryptoDecryptBase64Str 调用: crypto_id={crypto_id}")
            logger.debug(f"[DEBUG] 输入 base64_str 长度: {len(base64_str) if base64_str else 0}")
            if base64_str:
                preview = base64_str[:100] if len(base64_str) > 100 else base64_str
                logger.debug(f"[DEBUG] 输入 base64_str 前100字符: {preview}")
            
            crypto = self._crypto_objects.get(crypto_id)
            if not crypto:
                logger.error(f"加密对象不存在: {crypto_id}")
                return ""
            
            decrypted_bytes = crypto.decryptBase64(base64_str)
            result = decrypted_bytes.decode('utf-8')
            
            logger.debug(f"[DEBUG] cryptoDecryptBase64Str 解密成功，结果长度: {len(result)}")
            if result:
                preview = result[:200] if len(result) > 200 else result
                logger.debug(f"[DEBUG] 解密结果前200字符: {preview}")
            
            return result
            
        except Exception as e:
            logger.error(f"cryptoDecryptBase64Str 失败: {e}")
            logger.error(f"cryptoDecryptBase64Str 堆栈: {traceback.format_exc()}")
            return ""
    
    # ==================== 插件 API ====================
    
    async def get_audio(
        self,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 0,
        pitch: int = 0,
        volume: int = 0,
        **kwargs
    ) ->PluginAudioResult:
        """
        调用插件的 getAudio 方法获取音频
        
        Args:
            text: 要合成的文本
            voice: 声音 ID
            locale: 语言区域代码，默认 "zh-CN"
            rate: 语速（-100 到 100），0 为默认
            pitch: 音调（-100 到 100），0 为默认
            volume: 音量（0 到 100），0 为默认
            **kwargs: 其他参数
            
        Returns:
            PluginAudioResult 对象，包含音频数据或错误信息
        """
        if not self._loaded:
            return PluginAudioResult(error="插件未加载")
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._get_audio_sync,
            text, voice, locale, rate, pitch, volume, kwargs
        )
    
    def _get_audio_sync(
        self,
        text: str,
        voice: str,
        locale: str,
        rate: int,
        pitch: int,
        volume: int,
        kwargs: Dict[str, Any]
    ) -> PluginAudioResult:
        """同步获取音频（在线程池中执行）"""
        try:
            logger.debug(f"[DEBUG] _get_audio_sync 开始: text={text[:50] if len(text) > 50 else text}, voice={voice}, locale={locale}")
            
            # 构造JavaScript调用代码
            js_code = f'''
(function() {{
    try {{
        if (typeof PluginJS === "undefined" || typeof PluginJS.getAudio !== "function") {{
            return JSON.stringify({{error: "PluginJS.getAudio 未定义"}});
        }}
        
        var result = PluginJS.getAudio(
            {json.dumps(text)},
            {json.dumps(locale)},
            {json.dumps(voice)},
            {rate},
            {volume},
            {pitch}
        );
        
        if (!result) {{
            return JSON.stringify({{error: "getAudio 返回空结果"}});
        }}
        
        // 处理不同的返回格式
            if (typeof result === "object") {{
                // 首先检查是否是数组（字节数组）
                if (Array.isArray(result)) {{
                // 直接返回字节数组的情况
                // 使用 __py_arrayToBase64 直接在Python 端转换，避免 btoa 的截断问题
                console.log('[DEBUG _get_audio_sync] 检测到数组类型结果，长度: ' + result.length);
                var base64 = __py_arrayToBase64(JSON.stringify(result));
                console.log('[DEBUG _get_audio_sync] __py_arrayToBase64 转换后Base64 长度: ' + (base64 ? base64.length : 0));
                return JSON.stringify({{
                    audio: base64,
                    contentType: "audio/mpeg"
                }});
            }} else if (typeof result.body === 'function') {{
                // JsResponse 格式 - result.body 是一个函数，需要调用它获取 ResponseBody 对象
                console.log('[DEBUG _get_audio_sync] 进入 typeof result.body === function 分支');
                var responseBody = result.body();
                console.log('[DEBUG _get_audio_sync] responseBody: ' + (responseBody ? 'exists' : 'null'));
                console.log('[DEBUG _get_audio_sync] typeof responseBody.bytesBase64: ' + (responseBody ? typeof responseBody.bytesBase64 : 'N/A'));
                if (responseBody && typeof responseBody.bytesBase64 === 'function') {{
                    console.log('[DEBUG _get_audio_sync]调用 responseBody.bytesBase64()');
                    // 优先使用 bytesBase64() 避免数据截断
                    var base64 = responseBody.bytesBase64();
                    console.log('[DEBUG _get_audio_sync] bytesBase64() 结果长度: ' + (base64 ? base64.length : 0));
                    if (base64 && base64.length > 100) {{
                        console.log('[DEBUG _get_audio_sync] bytesBase64 前50字符: ' + base64.substring(0, 50));
}}
                    if (base64) {{
                        var contentType = "audio/mpeg";
                        if (typeof result.headers === 'function') {{
                            var headers = result.headers();
                            if (headers && headers["content-type"]) {{
                                contentType = headers["content-type"];
                            }}
                        }}
                        return JSON.stringify({{
                            audio: base64,
                            contentType: contentType
                        }});
                    }}
                }}
                if (responseBody && typeof responseBody.bytes === 'function') {{
                    // 备用方案使用 bytes()
                    var bytes = responseBody.bytes();
                    if (bytes) {{
                        // 转换为 Base64
                        var base64 = "";
                        if (typeof bytes === "string") {{
                            base64 = bytes;
                        }} else if (Array.isArray(bytes) || bytes instanceof Uint8Array) {{
                            var binary = "";
                            var len = bytes.length;
                            for (var i = 0; i < len; i++) {{
                                // 处理有符号字节
                                var byte = bytes[i];
                                if (byte < 0) byte = byte + 256;
                                binary += String.fromCharCode(byte & 0xFF);
                            }}
                            base64 = btoa(binary);
                        }}
                        var contentType = "audio/mpeg";
                        if (typeof result.headers === 'function') {{
                            var headers = result.headers();
                            if (headers && headers["content-type"]) {{
                                contentType = headers["content-type"];
                            }}
                        }}
                        return JSON.stringify({{
                            audio: base64,
                            contentType: contentType
                        }});
                    }}
                }}
            }} else if (result.bodyBytes) {{
                // 已经有bodyBytes 的情况
                return JSON.stringify({{
                    audio: result.bodyBytes,
                    contentType: result.headers ? result.headers["content-type"] || "audio/mpeg" : "audio/mpeg"
                }});
            }} else if (result.audio) {{
                // 直接包含 audio 字段
                return JSON.stringify(result);
            }} else if (result.error) {{
                return JSON.stringify({{error: result.error}});
            }}
        }} else if (typeof result === "string") {{
            // 可能是 Base64 编码的音频
            return JSON.stringify({{audio: result, contentType: "audio/mpeg"}});
        }}
        
        // 添加更多调试信息
        var resultType = typeof result;
        var resultInfo = "type=" + resultType;
        if (result && typeof result === "object") {{
            resultInfo += ", keys=" + Object.keys(result).join(",");
            resultInfo += ", isArray=" + Array.isArray(result);
        }}
        return JSON.stringify({{error: "无法解析 getAudio 返回值: " + resultInfo}});
        
    }} catch (e) {{
        return JSON.stringify({{error: "JavaScript 执行错误: " + e.toString()}});
    }}
}})();
'''
            result_json = self._ctx.eval(js_code)
            
            # 添加调试日志
            logger.debug(f"[DEBUG] _get_audio_sync JS执行原始结果长度: {len(result_json) if result_json else 0}")
            if result_json:
                preview = result_json[:500] if len(result_json) > 500 else result_json
                logger.debug(f"[DEBUG] _get_audio_sync JS执行结果预览: {preview}")
            
            result = json.loads(result_json)
            
            if isinstance(result, dict):
                logger.debug(f"[DEBUG] _get_audio_sync 解析后的结果 keys: {list(result.keys())}")
                if'error' in result:
                    logger.error(f"[DEBUG] _get_audio_sync 插件返回错误: {result['error']}")
                else:
                    logger.debug(f"[DEBUG] _get_audio_sync 解析后的结果类型: {type(result)}")
            
            if'error' in result:
                return PluginAudioResult(error=result['error'])
            # 解码 Base64 音频数据
            audio_base64 = result.get('audio', '')
            if not audio_base64:
                logger.error(f"[DEBUG] _get_audio_sync 音频数据为空")
                return PluginAudioResult(error="音频数据为空")
            
            logger.debug(f"[DEBUG] _get_audio_sync 音频 Base64 长度: {len(audio_base64)}")
            
            try:
                audio_bytes = base64.b64decode(audio_base64)
                logger.debug(f"[DEBUG] _get_audio_sync Base64 解码成功，音频字节数: {len(audio_bytes)}")
            except Exception as e:
                logger.error(f"[DEBUG] _get_audio_sync Base64 解码失败: {e}")
                return PluginAudioResult(error=f"Base64 解码失败: {e}")
            
            content_type = result.get('contentType', 'audio/mpeg')
            sample_rate = self._runtime.getAudioSampleRate(audio_bytes)
            
            logger.info(f"[DEBUG] _get_audio_sync 成功: audio_size={len(audio_bytes)}, contentType={content_type}, sampleRate={sample_rate}")
            
            return PluginAudioResult(
                audio=audio_bytes,
                contentType=content_type,
                sampleRate=sample_rate
            )
            
        except Exception as e:
            logger.error(f"getAudio 执行失败: {e}")
            logger.error(f"getAudio 堆栈: {traceback.format_exc()}")
            return PluginAudioResult(error=str(e))
    
    async def get_locales(self) -> List[PluginLocale]:
        """
        获取插件支持的语言列表
        
        调用 EditorJS.getLocales() 或 PluginJS.getLocales()
        
        Returns:
            PluginLocale 对象列表
        """
        if not self._loaded:
            return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self._get_locales_sync)
    
    def _get_locales_sync(self) -> List[PluginLocale]:
        """同步获取语言列表"""
        try:
            js_code = '''
(function() {
    var locales = [];
    
    //尝试 EditorJS
    if (typeof EditorJS !== "undefined" && typeof EditorJS.getLocales === "function") {
        var result = EditorJS.getLocales();
        if (Array.isArray(result)) {
            locales = result;
        }
    }
    
    // 尝试 PluginJS
    if (locales.length === 0 && typeof PluginJS !== "undefined" && typeof PluginJS.getLocales === "function") {
        var result = PluginJS.getLocales();
        if (Array.isArray(result)) {
            locales = result;
        }
    }
    
    // 返回默认值
    if (locales.length === 0) {
        locales = ["zh-CN"];
    }
    
    return JSON.stringify(locales);
})();
'''
            result_json = self._ctx.eval(js_code)
            locale_codes = json.loads(result_json)
            
            # 语言代码到名称的映射
            locale_names = {
                'zh-CN': '中文（简体）',
                'zh-TW': '中文（繁体）',
                'en-US': 'English (US)',
                'en-GB': 'English (UK)',
                'ja-JP': '日本語',
                'ko-KR': '한국어',
                'fr-FR': 'Français',
                'de-DE': 'Deutsch',
                'es-ES': 'Español',
                'ru-RU': 'Русский',}
            
            return [
                PluginLocale(
                    code=code,
                    name=locale_names.get(code, code)
                )
                for code in locale_codes
            ]
            
        except Exception as e:
            logger.error(f"getLocales 执行失败: {e}")
            return [PluginLocale(code='zh-CN', name='中文（简体）')]
    
    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        """
        获取插件支持的声音列表
        
        调用 EditorJS.getVoices(locale) 或 PluginJS.getVoices(locale)
        
        Args:
            locale: 语言区域代码，为空则获取所有声音
            
        Returns:
            PluginVoice 对象列表
        """
        if not self._loaded:
            return []
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._get_voices_sync,
            locale
        )
    
    def _get_voices_sync(self, locale: str) -> List[PluginVoice]:
        """同步获取声音列表"""
        try:
            js_code = f'''
(function() {{
    var voices = [];
    var locale = {json.dumps(locale)};
    
    // 尝试 EditorJS
    if (typeof EditorJS !== "undefined" && typeof EditorJS.getVoices === "function") {{
        var result = EditorJS.getVoices(locale);
        if (result && typeof result === "object") {{
            // 可能是对象格式 {{id: name, ...}}
            if (!Array.isArray(result)) {{
                for (var id in result) {{
                    var v = result[id];
                    if (v && typeof v === "object") {{
                        voices.push({{
                            id: id,
                            name: v.name || id,
                            locale: v.locale || locale || "zh-CN",
                            gender: v.gender || "",
                            extra: v.extra || null
                        }});
                    }} else {{
                        voices.push({{id: id, name: v, locale: locale || "zh-CN"}});
                    }}
                }}
            }} else {{
                voices = result;
            }}
        }}
    }}
    
    // 尝试 PluginJS
    if (voices.length === 0 && typeof PluginJS !== "undefined" && typeof PluginJS.getVoices === "function") {{
        var result = PluginJS.getVoices(locale);
        if (result && typeof result === "object") {{
            if (!Array.isArray(result)) {{
                for (var id in result) {{
                    var v = result[id];
                    if (v && typeof v === "object") {{
                        voices.push({{
                            id: id,
                            name: v.name || id,
                            locale: v.locale || locale || "zh-CN",
                            gender: v.gender || "",
                            extra: v.extra || null
                        }});
                    }} else {{
                        voices.push({{id: id, name: v, locale: locale || "zh-CN"}});
                    }}
                }}
            }} else {{
                voices = result;
            }}
        }}
    }}
    
    return JSON.stringify(voices);
}})();
'''
            result_json = self._ctx.eval(js_code)
            voices_data = json.loads(result_json)
            
            return [
                PluginVoice(
                    id=v.get('id', ''),
                    name=v.get('name', v.get('id', '')),
                    locale=v.get('locale', locale or'zh-CN'),
                    gender=v.get('gender', ''),
                    extra=v.get('extra')
                )
                for v in voices_data
                if v.get('id')
            ]
            
        except Exception as e:
            logger.error(f"getVoices 执行失败: {e}")
            return []
    
    def is_loaded(self) -> bool:
        """
        检查插件是否已加载
        
        Returns:
            如果插件已成功加载返回 True
        """
        return self._loaded
    
    def get_error(self) -> Optional[str]:
        """
        获取最近的错误信息
        
        Returns:
            错误消息，如果没有错误返回 None
        """
        return self._error
    
    def get_user_vars(self) -> Dict[str, Any]:
        """
        获取当前用户变量
        
        Returns:
            用户变量字典的副本
        """
        return self._runtime.getUserVars()
    
    def get_config(self) -> PluginConfig:
        """
        获取插件配置
        
        Returns:
            插件配置对象
        """
        return self._config
    
    def __enter__(self):
        """上下文管理器入口"""
        self.load()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.unload()
        return False
    
    def __del__(self):
        """析构函数，确保资源释放"""
        try:
            if self._loaded:
                self.unload()
            if self._executor:
                self._executor.shutdown(wait=False)
        except Exception:
            pass


# 导出
__all__ = ['PluginEngine']