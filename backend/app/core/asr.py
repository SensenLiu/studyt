"""Aliyun NLS one-sentence ASR via REST API."""
from __future__ import annotations
import json
import os
import time

import httpx
from aliyunsdkcore.client import AcsClient
from aliyunsdknls_cloud_meta.request.v20180518.CreateTokenRequest import CreateTokenRequest

_TOKEN_CACHE: dict[str, object] = {"token": None, "expires_at": 0.0}

_NLS_ASR_URL = "https://nls-gateway-cn-shanghai.aliyuncs.com/stream/v1/asr"


def _get_token_sync() -> str:
    now = time.time()
    if _TOKEN_CACHE["token"] and now < float(_TOKEN_CACHE["expires_at"]) - 60:
        return str(_TOKEN_CACHE["token"])

    ak_id = os.environ["ALIYUN_ACCESS_KEY_ID"]
    ak_secret = os.environ["ALIYUN_ACCESS_KEY_SECRET"]

    client = AcsClient(ak_id, ak_secret, "cn-shanghai")
    req = CreateTokenRequest()
    req.set_accept_format("JSON")
    req.set_endpoint("nls-meta.cn-shanghai.aliyuncs.com")
    resp = client.do_action_with_exception(req)
    data = json.loads(resp)

    token = data["Token"]["Id"]
    expires_at = float(data["Token"]["ExpireTime"])
    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expires_at"] = expires_at
    return token


async def transcribe(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    """Send audio bytes to Aliyun NLS one-sentence ASR, return transcript."""
    import asyncio
    token = await asyncio.get_event_loop().run_in_executor(None, _get_token_sync)
    appkey = os.environ["ALIYUN_NLS_APPKEY"]

    headers = {
        "X-NLS-Token": token,
        "Content-Type": "application/octet-stream",
    }
    params = {
        "appkey": appkey,
        "format": "ogg-opus",   # browsers record webm/opus; NLS accepts ogg-opus
        "sample_rate": str(sample_rate),
        "enable_punctuation_prediction": "true",
        "enable_inverse_text_normalization": "true",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            _NLS_ASR_URL,
            headers=headers,
            params=params,
            content=audio_bytes,
        )

    if resp.status_code != 200:
        raise RuntimeError(f"NLS HTTP {resp.status_code}: {resp.text[:200]}")

    data = resp.json()
    if data.get("status") != 20000000:
        raise RuntimeError(f"NLS error {data.get('status')}: {data.get('message')}")
    return data.get("result", "")
