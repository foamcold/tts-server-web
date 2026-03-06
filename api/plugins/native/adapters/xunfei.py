"""
讯飞配音原生适配器
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List
from urllib.parse import quote

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from ...runtime.audio import AudioUtils
from ...types.plugin import PluginAudioResult, PluginLocale, PluginVoice
from .base import NativePluginAdapter


class XunfeiAdapter(NativePluginAdapter):
    AES_KEY = b'G%.g7"Y&Nf^40Ee<'
    DEFAULT_HEADERS = {
        "content-type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://peiyin.xunfei.cn/",
        "Origin": "https://peiyin.xunfei.cn",
    }

    async def get_locales(self) -> List[PluginLocale]:
        return [PluginLocale(code="zh-CN", name="中文")]

    async def get_voices(self, locale: str = "") -> List[PluginVoice]:
        voices = self.context.runtime_meta.get("voices", [])
        result: List[PluginVoice] = []
        for item in voices:
            result.append(PluginVoice(id=item["code"], name=item["name"], locale="zh-CN"))
        return result

    def _process_text(self, text: str) -> str:
        mapping = self.context.runtime_meta.get("special_symbols_map", {})
        return "".join(mapping.get(char, char) for char in text)

    def _encrypt(self, payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        padder = padding.PKCS7(128).padder()
        padded = padder.update(raw) + padder.finalize()
        cipher = Cipher(algorithms.AES(self.AES_KEY), modes.ECB())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        import base64
        return json.dumps({"req": base64.b64encode(encrypted).decode("utf-8")}, ensure_ascii=False)

    def _decrypt(self, body_text: str) -> Dict[str, Any]:
        body = json.loads(body_text)
        import base64
        encrypted = base64.b64decode(body["body"])
        cipher = Cipher(algorithms.AES(self.AES_KEY), modes.ECB())
        decryptor = cipher.decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        raw = unpadder.update(padded) + unpadder.finalize()
        return json.loads(raw.decode("utf-8"))

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
        merged_vars = self.context.merged_vars
        runtime_data = kwargs.copy()
        runtime_data.update(merged_vars)
        processed_text = self._process_text(text)

        if voice == "custom":
            custom_voice = str(runtime_data.get("customVoice") or "")
            if not custom_voice:
                return PluginAudioResult(error="自定义声音代号为空")
            parts = custom_voice.split("_", 1)
            vid = parts[0]
            emo = parts[1] if len(parts) > 1 else ""
        else:
            vid = voice.split("_")[0]
            emo = ""
            if "_" in voice:
                emo = voice.split("_", 1)[1]

        x_speed = rate * 4 - 200
        x_volume = int(volume * 0.4 - 20)
        pitch_tag = f"[te{pitch}]" if pitch else ""
        emo_value = runtime_data.get("emoValue", 0)
        emo_tag = f"[em{emo}:{emo_value}]" if emo else ""
        sound_effect = runtime_data.get("soundEffect")
        effect_tag = f"[e{sound_effect}]" if sound_effect and str(sound_effect) != "0" else ""
        final_text = f"{effect_tag}{pitch_tag}{emo_tag}{processed_text}"

        sign_request = self._encrypt({"synth_text_hash_code": hashlib.md5(final_text.encode("utf-8")).hexdigest()})
        async with self.create_client() as client:
            response = await client.post(
                "https://peiyin.xunfei.cn/web-server/1.0/works_synth_sign",
                content=sign_request.encode("utf-8"),
                headers=self.DEFAULT_HEADERS,
            )
            response.raise_for_status()
            sign_data = self._decrypt(response.text)
            audio_url = (
                "https://peiyin.xunfei.cn/synth?"
                f"ts={sign_data['time_stamp']}&sign={sign_data['sign_text']}&sid=&vid={vid}"
                f"&volume={x_volume}&speed={x_speed}&content={quote(final_text)}&listen=0"
            )
            audio_response = await client.get(audio_url)
            audio_response.raise_for_status()
            audio = audio_response.content
        return PluginAudioResult(
            audio=audio,
            contentType="audio/mpeg",
            sampleRate=AudioUtils.getAudioSampleRate(audio),
        )
