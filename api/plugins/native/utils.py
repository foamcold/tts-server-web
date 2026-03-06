"""
原生插件通用工具
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

import httpx


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def md5_hex(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def b64_to_bytes(value: str) -> bytes:
    return base64.b64decode(value)


async def fetch_json(
    client: httpx.AsyncClient,
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Any = None,
    json_data: Any = None,
) -> Dict[str, Any]:
    response = await client.request(method, url, headers=headers, data=data, json=json_data)
    response.raise_for_status()
    return response.json()

