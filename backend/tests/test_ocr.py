from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.core import ocr


class _FakeAsyncOpenAI:
    def __init__(self, responses: list[str]) -> None:
        self._responses = responses
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create)
        )

    async def _create(self, **kwargs):
        content = self._responses.pop(0)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
        )


class _FakeOcrClient:
    def __init__(self, raw_text: str) -> None:
        self._raw_text = raw_text

    def recognize_general_with_options(self, req, runtime):
        return SimpleNamespace(
            body=SimpleNamespace(data=json.dumps({"content": self._raw_text}))
        )


@pytest.mark.asyncio
async def test_image_to_problem_solves_answer_when_ocr_does_not_provide_one(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        ocr,
        "_ocr_client",
        lambda: _FakeOcrClient("某数加 5 等于 12，求该数。"),
    )
    fake_client = _FakeAsyncOpenAI(
        [
            '{"statement": "某数加 5 等于 12，求该数。", "reference_answer": "未提供"}',
            '{"reference_answer": "7", "needs_confirmation": false}',
        ]
    )
    monkeypatch.setattr(ocr, "_deepseek_client", lambda: fake_client)

    result = await ocr.image_to_problem(b"fake-image")

    assert result["statement"] == "某数加 5 等于 12，求该数。"
    assert result["reference_answer"] == "7"
    assert result.get("answer_source") == "solved"
    assert result.get("needs_confirmation") is False


@pytest.mark.asyncio
async def test_image_to_problem_marks_confirmation_when_solver_is_uncertain(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        ocr,
        "_ocr_client",
        lambda: _FakeOcrClient("已知直角三角形两边长，求第三边。"),
    )
    fake_client = _FakeAsyncOpenAI(
        [
            '{"statement": "已知直角三角形两边长，求第三边。", "reference_answer": "未提供"}',
            '{"reference_answer": "", "needs_confirmation": true}',
        ]
    )
    monkeypatch.setattr(ocr, "_deepseek_client", lambda: fake_client)

    result = await ocr.image_to_problem(b"fake-image")

    assert result["statement"] == "已知直角三角形两边长，求第三边。"
    assert result["reference_answer"] == ""
    assert result.get("needs_confirmation") is True
    assert result.get("answer_source") == "solved"
