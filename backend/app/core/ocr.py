"""Aliyun OCR + DeepSeek to extract problem statement and answer from an image."""
from __future__ import annotations
import io
import json
import os

from alibabacloud_ocr_api20210707.client import Client
from alibabacloud_ocr_api20210707 import models as ocr_models
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from openai import AsyncOpenAI


def _ocr_client() -> Client:
    config = open_api_models.Config(
        access_key_id=os.environ["ALIYUN_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIYUN_ACCESS_KEY_SECRET"],
        endpoint="ocr-api.cn-hangzhou.aliyuncs.com",
    )
    return Client(config)


def _extract_text(body) -> str:
    """Extract plain text from RecognizeGeneral response body."""
    data_str = body.data if hasattr(body, "data") else str(body.to_map().get("Data", ""))
    try:
        data = json.loads(data_str)
    except Exception:
        return data_str

    # Try word list first (preserves structure better)
    words = data.get("prism_wordsInfo", [])
    if words:
        return " ".join(w.get("word", "") for w in words if w.get("word"))
    # Fallback to content field
    return data.get("content", "")


async def image_to_problem(image_bytes: bytes) -> dict[str, str]:
    """
    Given raw image bytes:
    1. Run Aliyun OCR to extract text
    2. Ask DeepSeek to parse out statement + reference_answer
    Returns {"statement": ..., "reference_answer": ..., "raw_ocr": ...}
    """
    # Step 1: OCR via stream upload
    import asyncio
    client = _ocr_client()
    req = ocr_models.RecognizeGeneralRequest()
    req.body = io.BytesIO(image_bytes)
    runtime = util_models.RuntimeOptions()
    resp = await asyncio.get_event_loop().run_in_executor(
        None, lambda: client.recognize_general_with_options(req, runtime)
    )
    raw_text = _extract_text(resp.body)

    if not raw_text.strip():
        raise ValueError("OCR 未能识别到文字，请确保图片清晰")

    # Step 2: DeepSeek parses OCR text into structured fields
    ds = AsyncOpenAI(
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        api_key=os.environ["DEEPSEEK_API_KEY"],
    )
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    prompt = f"""以下是从题目图片中 OCR 识别出的文字：

{raw_text}

请从中提取：
1. 题目内容（statement）：完整的题目描述，去掉题号、页码等无关内容
2. 参考答案（reference_answer）：如果图片中有答案则提取，没有则填"未提供"

以 JSON 格式返回，只返回 JSON，不要其他内容：
{{"statement": "...", "reference_answer": "..."}}"""

    completion = await ds.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
        temperature=0,
    )
    content = completion.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    result = json.loads(content.strip())
    return {
        "statement": result.get("statement", "").strip(),
        "reference_answer": result.get("reference_answer", "未提供").strip(),
        "raw_ocr": raw_text,
    }
