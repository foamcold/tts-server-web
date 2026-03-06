"""
上游请求控制器
按插件维度控制并发、排队、替换旧请求，并统一处理超时与重试
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict

import aiohttp
import httpx

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class UpstreamSettings:
    """上游连接设置"""

    mode: str = "concurrent"
    timeout_seconds: int = 30
    retry_count: int = 1


class UpstreamRequestReplacedError(RuntimeError):
    """请求被同插件新请求替换"""


class UpstreamController:
    """上游请求控制器"""

    def __init__(self) -> None:
        self._settings = UpstreamSettings()
        self._queue_locks: Dict[str, asyncio.Lock] = {}
        self._replace_locks: Dict[str, asyncio.Lock] = {}
        self._active_tasks: Dict[str, asyncio.Task[Any]] = {}
        self._task_meta: Dict[asyncio.Task[Any], Dict[str, Any]] = {}

    def update_settings(self, settings: UpstreamSettings) -> None:
        """更新当前生效的上游设置"""

        self._settings = settings

    def get_settings(self) -> UpstreamSettings:
        """读取当前生效的上游设置"""

        return self._settings

    async def run(
        self,
        plugin_id: str,
        operation_name: str,
        coroutine_factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """按当前策略运行上游操作"""

        mode = self._settings.mode
        if mode == "queue":
            lock = self._queue_locks.setdefault(plugin_id, asyncio.Lock())
            async with lock:
                return await self._run_with_retry(plugin_id, operation_name, coroutine_factory)

        if mode == "replace":
            return await self._run_replace(plugin_id, operation_name, coroutine_factory)

        return await self._run_with_retry(plugin_id, operation_name, coroutine_factory)

    async def _run_replace(
        self,
        plugin_id: str,
        operation_name: str,
        coroutine_factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """替换旧请求模式"""

        current_task = asyncio.current_task()
        if current_task is None:
            return await self._run_with_retry(plugin_id, operation_name, coroutine_factory)

        replace_lock = self._replace_locks.setdefault(plugin_id, asyncio.Lock())
        async with replace_lock:
            previous_task = self._active_tasks.get(plugin_id)
            if previous_task is not None and not previous_task.done():
                meta = self._task_meta.get(previous_task)
                if meta is not None:
                    meta["replaced"] = True
                previous_task.cancel()
                logger.info("插件上游请求已被新请求替换: plugin_id=%s, operation=%s", plugin_id, operation_name)

            self._active_tasks[plugin_id] = current_task
            self._task_meta[current_task] = {
                "plugin_id": plugin_id,
                "operation_name": operation_name,
                "replaced": False,
            }

        try:
            return await self._run_with_retry(plugin_id, operation_name, coroutine_factory)
        except asyncio.CancelledError as exc:
            meta = self._task_meta.get(current_task, {})
            if meta.get("replaced"):
                raise UpstreamRequestReplacedError("同插件有新请求到达，当前请求已被替换") from exc
            raise
        finally:
            async with replace_lock:
                if self._active_tasks.get(plugin_id) is current_task:
                    self._active_tasks.pop(plugin_id, None)
                self._task_meta.pop(current_task, None)

    async def _run_with_retry(
        self,
        plugin_id: str,
        operation_name: str,
        coroutine_factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """统一处理超时与重试"""

        last_error: Exception | None = None
        max_attempts = max(1, self._settings.retry_count + 1)

        for attempt in range(1, max_attempts + 1):
            try:
                async with asyncio.timeout(self._settings.timeout_seconds):
                    return await coroutine_factory()
            except UpstreamRequestReplacedError:
                raise
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError as exc:
                last_error = RuntimeError(
                    f"上游{operation_name}超时，已超过 {self._settings.timeout_seconds} 秒"
                )
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code if exc.response is not None else 0
                if not self._should_retry_status(status_code) or attempt >= max_attempts:
                    raise RuntimeError(f"上游{operation_name}失败，HTTP {status_code}") from exc
                last_error = RuntimeError(f"上游{operation_name}失败，HTTP {status_code}，正在重试")
            except (httpx.TimeoutException, httpx.TransportError, aiohttp.ClientError, OSError) as exc:
                last_error = RuntimeError(f"上游{operation_name}连接失败：{exc}")
            except Exception:
                raise

            logger.warning(
                "上游操作失败，准备重试: plugin_id=%s, operation=%s, attempt=%s/%s, error=%s",
                plugin_id,
                operation_name,
                attempt,
                max_attempts,
                last_error,
            )
            if attempt >= max_attempts:
                break

        if last_error is not None:
            raise last_error
        raise RuntimeError(f"上游{operation_name}失败")

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        """仅对明确可重试的状态码重试"""

        return status_code == 429 or 500 <= status_code < 600


_upstream_controller = UpstreamController()


def get_upstream_controller() -> UpstreamController:
    """获取全局上游请求控制器"""

    return _upstream_controller
