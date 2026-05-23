"""Aliyun OCR + DeepSeek to extract problem statement and answer from an image."""
from __future__ import annotations
import io
import json
import os
from typing import Any

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


def _deepseek_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        api_key=os.environ["DEEPSEEK_API_KEY"],
    )


async def _chat_json(prompt: str, *, max_tokens: int = 500) -> dict[str, Any]:
    ds = _deepseek_client()
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    completion = await ds.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0,
    )
    content = completion.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    return json.loads(content.strip())


async def solve_problem(statement: str, subject: str, grade: str) -> dict[str, Any]:
    prompt = f"""你是一名中国 K-12 {subject} 老师。下面是一道 {grade} 题目：

{statement}

请先自行求解，再只返回 JSON，不要解释：
{{"reference_answer": "最终答案", "needs_confirmation": false}}

如果题目信息不完整、歧义明显、无法可靠求解，则返回：
{{"reference_answer": "", "needs_confirmation": true}}"""
    result = await _chat_json(prompt)
    return {
        "reference_answer": str(result.get("reference_answer", "")).strip(),
        "needs_confirmation": bool(result.get("needs_confirmation", False)),
    }


async def image_to_problem(
    image_bytes: bytes,
    *,
    subject: str = "math",
    grade: str = "junior_1",
) -> dict[str, Any]:
    """
    Given raw image bytes:
    1. Run Aliyun OCR to extract text
    2. Ask DeepSeek to parse out statement + reference_answer
    3. If no answer is present, ask DeepSeek to solve it internally
    Returns internal data including answer and confirmation state.
    """
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

    parsed = await _chat_json(
        f"""以下是从题目图片中 OCR 识别出的文字：

{raw_text}

请从中提取：
1. 题目内容（statement）：完整的题目描述，去掉题号、页码等无关内容
2. 参考答案（reference_answer）：如果图片中有答案则提取，没有则填\"未提供\"

以 JSON 格式返回，只返回 JSON，不要其他内容：
{{"statement": "...", "reference_answer": "..."}}"""
    )
    statement = str(parsed.get("statement", "")).strip()
    reference_answer = str(parsed.get("reference_answer", "未提供")).strip()
    needs_confirmation = len(statement) < 8
    answer_source = "extracted"

    if reference_answer in {"", "未提供"}:
        solved = await solve_problem(statement, subject, grade)
        reference_answer = solved["reference_answer"]
        needs_confirmation = needs_confirmation or bool(solved.get("needs_confirmation")) or not reference_answer
        answer_source = "solved"

    return {
        "statement": statement,
        "reference_answer": reference_answer,
        "raw_ocr": raw_text,
        "needs_confirmation": needs_confirmation,
        "answer_source": answer_source,
    }
