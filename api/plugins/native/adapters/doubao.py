"""
豆包原生适配器
"""

from __future__ import annotations

import base64
import json
import random
from typing import Any, Dict, List

import aiohttp

from ...runtime.audio import AudioUtils
from ...types.plugin import PluginAudioResult, PluginLocale, PluginVoice
from ..utils import read_json, write_json
from .base import NativePluginAdapter


class DoubaoAdapter(NativePluginAdapter):
    VOICE_RECOMMEND_URL = (
        "https://www.doubao.com/alice/user_voice/recommend?language=zh&browser_language=zh-CN&mode=0"
        "&language=zh&browser_language=zh-CN&device_platform=web&aid=586861&real_aid=586861"
        "&pkg_type=release_version&device_id={device_id}&tea_uuid={device_id}&web_id={device_id}"
        "&is_new_user=0&region=CN&sys_region=CN&use-olympus-account=1&samantha_web=1&version=1.20.1"
        "&version_code=20800&pc_version=1.20.1"
    )
    WS_URL = (
        "wss://ws-samantha.doubao.com/samantha/audio/tts?format=aac&speaker={speaker}"
        "&speech_rate={rate}&pitch={pitch}{common}"
    )
    COMMON_QUERY = (
        "&mode=0&language=zh&browser_language=zh-CN&device_platform=web&aid=586861&real_aid=586861"
        "&pkg_type=release_version&device_id={device_id}&tea_uuid={device_id}&web_id={device_id}&is_new_user=0"
        "&region=CN&sys_region=CN&use-olympus-account=1&samantha_web=1&version=1.20.1&version_code=20800&pc_version=1.20.1"
    )
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 Edg/133.0.0.0"

    def _device_id(self) -> str:
        return f"{random.randint(100000000, 999999999)}{random.randint(100000000, 999999999)}"

    def _cookie(self) -> str:
        cookie = str(self.context.merged_vars.get("cookie") or "")
        if not cookie:
            raise ValueError("未设置豆包Cookie，请从官网获取")
        return cookie

    async def load_data(self) -> None:
        cookie = self._cookie()
        device_id = self._device_id()
        all_voices: List[Dict[str, Any]] = []
        locales: List[str] = []
        async with self.create_client() as client:
            for voice_type, tab in [(1, ""), (10, "female"), (10, "male"), (10, "characters"), (10, "accent")]:
                file_name = self.cache_dir / f"voices_{voice_type}_{tab or 'default'}.json"
                payload = read_json(file_name)
                if payload is None:
                    response = await client.post(
                        self.VOICE_RECOMMEND_URL.format(device_id=device_id),
                        content=json.dumps({"page_index": 1, "page_size": 200, "recommend_type": voice_type, "tab_key": tab}, ensure_ascii=False),
                        headers={"Cookie": cookie, "User-Agent": self.UA},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    write_json(file_name, payload)
                if payload.get("code") != 0:
                    raise ValueError(f"加载发音人失败：{payload.get('msg', '未知错误')}")
                for item in payload.get("data", {}).get("ugc_voice_list", []):
                    if not any(existing["style_id"] == item["style_id"] for existing in all_voices):
                        all_voices.append(item)
                    language_code = item.get("language_code") or "zh-CN"
                    if language_code not in locales:
                        locales.append(language_code)
        self.context.runtime_meta["voices_data"] = all_voices
        self.context.runtime_meta["locales"] = locales

    async def get_locales(self) -> List[PluginLocale]:
        if not self.context.runtime_meta.get("locales"):
            await self.load_data()
        return [PluginLocale(code=code, name=code) for code in self.context.runtime_meta.get("locales", ["zh-CN"])]

    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        if not self.context.runtime_meta.get("voices_data"):
            await self.load_data()
        result: List[PluginVoice] = []
        for item in self.context.runtime_meta.get("voices_data", []):
            item_locale = item.get("language_code") or "zh-CN"
            if locale and item_locale != locale:
                continue
            tags = "|".join(tag.get("tag_value", "") for tag in item.get("tag_list", []))
            name = f"{item.get('name', item['style_id'])} ({tags})" if tags else item.get("name", item["style_id"])
            result.append(PluginVoice(id=item["style_id"], name=name, locale=item_locale, extra={"icon_url": item.get("icon", {}).get("url", "")}))
        return result

    def _get_voice_gender(self, voice: str) -> str:
        voices = self.context.runtime_meta.get("voices_data", [])
        for item in voices:
            if item.get("style_id") == voice:
                name = item.get("name", "")
                if "男" in name:
                    return "male"
                if "女" in name:
                    return "female"
                for tag in item.get("tag_list", []):
                    value = tag.get("tag_value", "")
                    if "男" in value:
                        return "male"
                    if "女" in value:
                        return "female"
        return "female" if "female" in voice else "male"

    async def _get_volc_audio(self, text: str, voice: str, custom_bv: str = "") -> bytes:
        voice_map = {
            "en_male_adam": "tts.other.BV700_V2_streaming",
            "en_male_bob": "tts.other.BV701_V2_streaming",
            "en_female_sarah": "tts.other.BV703_V2_streaming",
            "zh_male_rap": "tts.other.BV021_streaming",
            "zh_male_zhubo": "tts.other.BV107_streaming",
            "zh_female_zhubo": "tts.other.BV100_streaming",
            "zh_female_sichuan": "tts.other.BV005_streaming",
            "zh_male_xiaoming": "tts.other.BV119_streaming",
            "zh_female_qingxin": "tts.other.BV104_streaming",
            "zh_female_story": "tts.other.BV064_streaming",
            "jp_male_satoshi": "tts.other.BV524_streaming",
            "jp_female_mai": "tts.other.BV520_streaming",
            "kr_male_gye": "tts.other.BV083_streaming",
            "es_male_george": "tts.other.BV065_streaming",
            "pt_female_alice": "tts.other.BV530_streaming",
            "de_female_sophie": "tts.other.BV068_streaming",
            "fr_male_enzo": "tts.other.BV078_streaming",
            "id_female_noor": "tts.other.BV092_streaming",
        }
        current_voice = voice
        if voice == "custom":
            if not custom_bv:
                raise ValueError("火山custom类型需设置BV号")
            current_voice = f"tts.other.BV{custom_bv}_streaming" if not custom_bv.startswith("tts.other.") else custom_bv
        elif voice.startswith("BV") and not voice.startswith("tts.other."):
            current_voice = f"tts.other.{voice}"
        elif not voice.startswith("tts.other.BV"):
            current_voice = voice_map.get(voice, voice)
        async with self.create_client() as client:
            response = await client.post(
                "https://translate.volcengine.com/crx/tts/v1/",
                json={"text": text, "speaker": current_voice},
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise ValueError(f"火山错误：code={base_resp.get('status_code')}，msg={base_resp.get('status_message')}" )
        return base64.b64decode(data["audio"]["data"])

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
        if not self.context.runtime_meta.get("voices_data"):
            await self.load_data()
        cookie = self._cookie()
        custom_bv = str((kwargs.get("bv") or self.context.merged_vars.get("bv") or "")).strip()
        if voice == "custom" or voice.startswith("BV") or voice.startswith("tts.other.BV"):
            audio = await self._get_volc_audio(text, voice, custom_bv)
            return PluginAudioResult(audio=audio, contentType="audio/mpeg", sampleRate=AudioUtils.getAudioSampleRate(audio))

        device_id = self._device_id()
        ws_url = self.WS_URL.format(
            speaker=voice,
            rate=(rate * 2) - 100,
            pitch=pitch - 50,
            common=self.COMMON_QUERY.format(device_id=device_id),
        )
        headers = {
            "Cookie": cookie,
            "Origin": "chrome-extension://capohkkfagimodmlpnahjoijgoocdjhd",
            "User-Agent": self.UA,
        }
        chunks: List[bytes] = []
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.ws_connect(ws_url) as ws:
                    await ws.send_str(json.dumps({"event": "text", "podcast_extra": {"role": ""}, "text": text}, ensure_ascii=False))
                    await ws.send_str('{"event":"finish"}')
                    async for message in ws:
                        if message.type == aiohttp.WSMsgType.BINARY:
                            chunks.append(message.data)
                        elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                            break
        except Exception:
            fallback_voice = "tts.other.BV008_streaming" if self._get_voice_gender(voice) == "male" else "tts.other.BV405_streaming"
            audio = await self._get_volc_audio(text, fallback_voice, custom_bv)
            return PluginAudioResult(audio=audio, contentType="audio/mpeg", sampleRate=AudioUtils.getAudioSampleRate(audio))

        if not chunks:
            fallback_voice = "tts.other.BV008_streaming" if self._get_voice_gender(voice) == "male" else "tts.other.BV405_streaming"
            audio = await self._get_volc_audio(text, fallback_voice, custom_bv)
            return PluginAudioResult(audio=audio, contentType="audio/aac", sampleRate=AudioUtils.getAudioSampleRate(audio))

        audio = b"".join(chunks)
        return PluginAudioResult(audio=audio, contentType="audio/aac", sampleRate=24000)

