"""
纳米 AI 原生适配器
"""

from __future__ import annotations

import time
from typing import Any, Dict, List
from urllib.parse import quote

from ...runtime.audio import AudioUtils
from ...types.plugin import PluginAudioResult, PluginLocale, PluginVoice
from ..utils import md5_hex, read_json, write_json
from .base import NativePluginAdapter


class NamiAdapter(NativePluginAdapter):
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

    def _generate_mid(self) -> str:
        import random

        def hash_text(value: str) -> int:
            hash_mask_1 = 268435455
            hash_mask_2 = 266338304
            total = 0
            for char in reversed(value):
                code = ord(char)
                total = ((total << 6) & hash_mask_1) + code + (code << 14)
                current = total & hash_mask_2
                if current != 0:
                    total ^= current >> 21
            return total

        lang = "zh-CN"
        app_name = "chrome"
        referrer = "https://bot.n.cn/chat"
        platform = "Win32"
        joined = "".join([app_name, str(1.0), lang, platform, self.UA, "1920", "x", "1080", "24", referrer])
        joined += "".join(str((1 - index) ^ (len(joined) + index)) for index in range(2))
        rt = f"{hash_text('https://bot.n.cn')}{hash_text(joined)}{int(time.time() * 1000 + random.random() * 1000)}"
        return rt.replace(".", "e")[:32]

    def _headers(self) -> Dict[str, str]:
        device = "Web"
        version = "1.2"
        time_text = time.strftime("%Y-%m-%dT%H:%M:%S+08:00", time.localtime())
        access_token = self._generate_mid()
        zm_ua = md5_hex(self.UA)
        return {
            "device-platform": device,
            "timestamp": time_text,
            "access-token": access_token,
            "zm-token": md5_hex(f"{device}{time_text}{version}{access_token}{zm_ua}"),
            "zm-ver": version,
            "zm-ua": zm_ua,
            "User-Agent": self.UA,
        }

    async def load_data(self) -> None:
        cache_file = self.cache_dir / "robots.json"
        data = read_json(cache_file)
        if data is None:
            async with self.create_client() as client:
                response = await client.get("https://bot.n.cn/api/robot/platform", headers=self._headers())
                response.raise_for_status()
                data = response.json()
            write_json(cache_file, data)
        voices = []
        seen_ids = set()
        for item in data.get("data", {}).get("list", []):
            voice_id = item.get("tag", "")
            if not voice_id or voice_id in seen_ids:
                continue
            seen_ids.add(voice_id)
            voices.append({
                "id": voice_id,
                "name": item.get("title", voice_id),
                "icon_url": item.get("icon", ""),
                "locale": "zh-CN",
            })
        self.context.runtime_meta["voices"] = voices

    async def get_locales(self) -> List[PluginLocale]:
        return [PluginLocale(code="zh-CN", name="中文")]

    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        if not self.context.runtime_meta.get("voices"):
            await self.load_data()
        return [
            PluginVoice(id=item["id"], name=item["name"], locale=item["locale"], extra={"icon_url": item["icon_url"]})
            for item in self.context.runtime_meta.get("voices", [])
        ]

    async def synthesize(
        self,
        text: str,
        voice: str,
        locale: str = "zh-CN",
        rate: int = 50,
        pitch: int = 50,
        volume: int = 50,
        **kwargs: Any,
    ) -> PluginAudioResult:
        url = f"https://bot.n.cn/api/tts/v1?roleid={quote(voice or 'DeepSeek')}"
        headers = self._headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        form = f"&text={quote(text)}&audio_type=mp3&format=stream"
        async with self.create_client() as client:
            response = await client.post(url, data=form.encode("utf-8"), headers=headers)
            response.raise_for_status()
            audio = response.content
        return PluginAudioResult(audio=audio, contentType="audio/mpeg", sampleRate=AudioUtils.getAudioSampleRate(audio))
