"""
HTTP 运行时模块
模拟 OkHttp 的 Response 对象，供JavaScript 插件调用
"""
import httpx
import logging
from typing import Optional, Dict, Any, Iterator

logger = logging.getLogger(__name__)


class ResponseBody:
    """
    模拟 OkHttp ResponseBody
    提供多种方式读取响应内容
    """

    def __init__(self, content: bytes, encoding: str = 'utf-8'):
        """
        初始化ResponseBody

        Args:
            content: 响应的原始字节内容
            encoding: 字符编码，默认 utf-8
        """
        self._content = content
        self._encoding = encoding

    def string(self) -> str:
        """
        返回响应文本

        Returns:
            解码后的字符串内容
        """
        return self._content.decode(self._encoding, errors='replace')

    def bytes(self) -> bytes:
        """
        返回响应字节

        Returns:
            原始字节内容
        """
        return self._content

    def byteStream(self) -> Iterator[bytes]:
        """
        返回字节流迭代器
        用于大文件的流式读取

        Returns:
            字节块迭代器，每块8KB
        """
        chunk_size = 8192  # 8KB 每块
        offset = 0
        while offset < len(self._content):
            yield self._content[offset:offset + chunk_size]
            offset += chunk_size


class JsResponse:
    """
    模拟 OkHttp Response
    用于 JavaScript 插件调用，提供与 OkHttp 兼容的 API
    """

    def __init__(self, status_code: int, message: str, headers: Dict[str, str], body: bytes, encoding: str = 'utf-8'):
        """
        初始化 JsResponse

        Args:
            status_code: HTTP 状态码
            message: 状态消息
            headers: 响应头字典
            body: 响应体字节内容
            encoding: 字符编码
        """
        self._status_code = status_code
        self._message = message
        self._headers = headers
        self._body = ResponseBody(body, encoding)

    def code(self) -> int:
        """
        返回 HTTP 状态码

        Returns:
            状态码，如 200, 404, 500 等
        """
        return self._status_code

    def message(self) -> str:
        """
        返回状态消息

        Returns:
            状态消息，如 "OK", "Not Found" 等
        """
        return self._message

    def body(self) -> ResponseBody:
        """
        返回 ResponseBody 对象

        Returns:
            ResponseBody 实例，可用于读取响应内容
        """
        return self._body

    def headers(self) -> Dict[str, str]:
        """
        返回响应头字典

        Returns:
            包含所有响应头的字典
        """
        return self._headers

    def isSuccessful(self) -> bool:
        """
        检查请求是否成功

        Returns:
            如果状态码在 200-299 范围内返回 True
        """
        return 200 <= self._status_code < 300


class HttpClient:
    """
    HTTP 客户端
    使用 httpx 实现，提供给 ttsrv 运行时使用
    支持同步调用，供 JavaScript 引擎使用
    """

    def __init__(self, timeout: float = 30.0, follow_redirects: bool = True):
        """
        初始化 HTTP 客户端

        Args:
            timeout: 请求超时时间（秒），默认 30 秒
            follow_redirects: 是否自动跟随重定向，默认True
        """
        self._timeout = timeout
        self._follow_redirects = follow_redirects

    def _create_client(self) -> httpx.Client:
        """
        创建 httpx 客户端实例

        Returns:
            配置好的 httpx.Client 实例
        """
        return httpx.Client(
            timeout=self._timeout,
            follow_redirects=self._follow_redirects
        )

    def _get_status_message(self, status_code: int) -> str:
        """
        根据状态码获取标准状态消息

        Args:
            status_code: HTTP 状态码

        Returns:
            对应的状态消息
        """
        messages = {
            200: "OK",
            201: "Created",
            204: "No Content",
            301: "Moved Permanently",
            302: "Found",
            304: "Not Modified",
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            500: "Internal Server Error",
            502: "Bad Gateway",
            503: "Service Unavailable",
        }
        return messages.get(status_code, "Unknown")

    def _make_response(self, response: httpx.Response) -> JsResponse:
        """
        将 httpx.Response 转换为 JsResponse

        Args:
            response: httpx 响应对象

        Returns:
            JsResponse 实例
        """
        # 获取编码
        encoding = response.encoding or 'utf-8'

        # 转换响应头为普通字典
        headers = dict(response.headers)

        return JsResponse(
            status_code=response.status_code,
            message=self._get_status_message(response.status_code),
            headers=headers,
            body=response.content,
            encoding=encoding
        )

    def httpGet(self, url: str, headers: Optional[Dict[str, str]] = None) -> JsResponse:
        """
        发送 HTTP GET 请求

        Args:
            url: 请求URL
            headers: 可选的请求头字典

        Returns:
            JsResponse 对象

        Raises:
            Exception: 当请求失败时抛出异常
        """
        try:
            with self._create_client() as client:
                logger.debug(f"HTTP GET: {url}, headers: {headers}")
                response = client.get(url, headers=headers or {})
                logger.debug(f"HTTP GET Response [{response.status_code}]: {response.text[:1000]}")
                return self._make_response(response)
        except httpx.TimeoutException:
            # 超时时返回一个错误响应
            return JsResponse(
                status_code=408,
                message="Request Timeout",
                headers={},
                body=b"Request timed out"
            )
        except httpx.RequestError as e:
            # 其他请求错误
            return JsResponse(
                status_code=0,
                message="Request Error",
                headers={},
                body=str(e).encode('utf-8')
            )

    def httpPost(self, url: str, body: str, headers: Optional[Dict[str, str]] = None) -> JsResponse:
        """
        发送 HTTP POST 请求

        Args:
            url: 请求 URL
            body: 请求体内容（字符串）
            headers: 可选的请求头字典

        Returns:
            JsResponse 对象

        Raises:
            Exception: 当请求失败时抛出异常
        """
        try:
            with self._create_client() as client:
                logger.debug(f"HTTP POST: {url}, body: {body[:500]}, headers: {headers}")
                response = client.post(url, content=body, headers=headers or {})
                logger.debug(f"HTTP POST Response [{response.status_code}]: {response.text[:1000]}")
                return self._make_response(response)
        except httpx.TimeoutException:
            return JsResponse(
                status_code=408,
                message="Request Timeout",
                headers={},
                body=b"Request timed out"
            )
        except httpx.RequestError as e:
            return JsResponse(
                status_code=0,
                message="Request Error",
                headers={},
                body=str(e).encode('utf-8')
            )

    def httpPostMultipart(
        self,
        url: str,
        files: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> JsResponse:
        """
        发送Multipart POST 请求

        Args:
            url: 请求 URL
            files: 文件字典，格式为:-简单格式: {"field_name": file_content}
                   - 完整格式: {"field_name": ("filename", file_content, "content_type")}
            headers: 可选的请求头字典

        Returns:
            JsResponse 对象

        示例:
            # 简单格式
            client.httpPostMultipart(url, {"file": open("test.txt", "rb").read()})

            # 完整格式
            client.httpPostMultipart(url, {
                "file": ("test.txt", file_content, "text/plain"),
                "data": ("data.json", json_content, "application/json")
            })
        """
        try:
            # 处理文件参数
            httpx_files = {}
            for field_name, file_data in files.items():
                if isinstance(file_data, tuple):
                    # 完整格式: (filename, content, content_type)
                    if len(file_data) >= 3:
                        httpx_files[field_name] = (file_data[0], file_data[1], file_data[2])
                    elif len(file_data) == 2:
                        httpx_files[field_name] = (file_data[0], file_data[1])
                    else:
                        httpx_files[field_name] = file_data[0]
                else:
                    # 简单格式: 直接是内容
                    httpx_files[field_name] = file_data

            with self._create_client() as client:
                response = client.post(url, files=httpx_files, headers=headers or {})
                return self._make_response(response)
        except httpx.TimeoutException:
            return JsResponse(
                status_code=408,
                message="Request Timeout",
                headers={},
                body=b"Request timed out"
            )
        except httpx.RequestError as e:
            return JsResponse(
                status_code=0,
                message="Request Error",
                headers={},
                body=str(e).encode('utf-8')
            )