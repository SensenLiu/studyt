from __future__ import annotations

from pathlib import Path

import pytest

from app.core import photo_intake


@pytest.mark.asyncio
async def test_create_photo_draft_stages_image_and_category(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_intake, "_TMP_IMAGE_DIR", tmp_path / "tmp")

    async def fake_image_to_problem(image_bytes: bytes, *, subject: str, grade: str):
        return {
            "statement": "某数加 5 等于 12，求该数。",
            "reference_answer": "7",
            "raw_ocr": "某数加 5 等于 12，求该数。",
            "needs_confirmation": False,
            "answer_source": "solved",
        }

    async def fake_categorize_problem(statement: str, subject: str, grade: str, raw_ocr: str = "") -> str:
        return "一元一次方程"

    monkeypatch.setattr(photo_intake, "image_to_problem", fake_image_to_problem)
    monkeypatch.setattr(photo_intake, "categorize_problem", fake_categorize_problem)

    draft = await photo_intake.create_photo_draft(
        image_bytes=b"fake-image",
        filename="problem.jpg",
        subject="math",
        grade="junior_1",
    )

    assert draft.statement == "某数加 5 等于 12，求该数。"
    assert draft.category == "一元一次方程"
    assert Path(draft.temp_image_path).exists()


@pytest.mark.asyncio
async def test_build_finalized_photo_payload_returns_draft_data_when_statement_unchanged(
    tmp_path, monkeypatch
):
    """When the caller passes an empty / identical statement, the payload must
    come verbatim from the draft (no re-solve, no re-categorize call)."""
    monkeypatch.setattr(photo_intake, "_TMP_IMAGE_DIR", tmp_path / "tmp")

    async def fake_image_to_problem(image_bytes: bytes, *, subject: str, grade: str):
        return {
            "statement": "某数加 5 等于 12，求该数。",
            "reference_answer": "7",
            "raw_ocr": "某数加 5 等于 12，求该数。",
            "needs_confirmation": False,
            "answer_source": "extracted",
        }

    async def fake_categorize_problem(statement: str, subject: str, grade: str, raw_ocr: str = "") -> str:
        return "一元一次方程"

    async def should_not_be_called(*args, **kwargs):
        raise AssertionError("solve_problem must not be called when statement is unchanged")

    monkeypatch.setattr(photo_intake, "image_to_problem", fake_image_to_problem)
    monkeypatch.setattr(photo_intake, "categorize_problem", fake_categorize_problem)
    monkeypatch.setattr(photo_intake, "solve_problem", should_not_be_called)

    draft = await photo_intake.create_photo_draft(
        image_bytes=b"fake-image",
        filename="problem.jpg",
        subject="math",
        grade="junior_1",
    )

    # Pass the same statement back (simulating user confirming without edits)
    payload = await photo_intake.build_finalized_photo_payload(
        draft_id=draft.id,
        statement=draft.statement,
    )

    assert payload["statement"] == "某数加 5 等于 12，求该数。"
    assert payload["answer"] == "7"
    assert payload["category"] == "一元一次方程"
    assert payload["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_build_finalized_photo_payload_re_solves_when_statement_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(photo_intake, "_TMP_IMAGE_DIR", tmp_path / "tmp")
    monkeypatch.setattr(photo_intake, "_MISTAKE_IMAGE_DIR", tmp_path / "mistake_images")

    async def fake_image_to_problem(image_bytes: bytes, *, subject: str, grade: str):
        return {
            "statement": "原始 OCR 题目",
            "reference_answer": "未提供",
            "raw_ocr": "原始 OCR 题目",
            "needs_confirmation": False,
            "answer_source": "solved",
        }

    async def fake_categorize_problem(statement: str, subject: str, grade: str, raw_ocr: str = "") -> str:
        return "一元一次方程"

    async def fake_solve_problem(statement: str, subject: str, grade: str):
        return {"reference_answer": "7", "needs_confirmation": False}

    monkeypatch.setattr(photo_intake, "image_to_problem", fake_image_to_problem)
    monkeypatch.setattr(photo_intake, "categorize_problem", fake_categorize_problem)
    monkeypatch.setattr(photo_intake, "solve_problem", fake_solve_problem)

    draft = await photo_intake.create_photo_draft(
        image_bytes=b"fake-image",
        filename="problem.jpg",
        subject="math",
        grade="junior_1",
    )

    payload = await photo_intake.build_finalized_photo_payload(
        draft_id=draft.id,
        statement="某数加 5 等于 12，求该数。",
    )

    assert payload["statement"] == "某数加 5 等于 12，求该数。"
    assert payload["answer"] == "7"
    assert payload["category"] == "一元一次方程"
