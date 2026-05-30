"""Photo draft workflow: stage temp image, create draft, finalize or discard."""
from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from app.core.ocr import image_to_problem, solve_problem, categorize_problem

_TMP_IMAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "photo_drafts"
_MISTAKE_IMAGE_DIR = Path(__file__).resolve().parents[2] / "data" / "mistake_images"
_drafts: dict[str, "PhotoDraft"] = {}


@dataclass
class PhotoDraft:
    id: str
    subject: str
    grade: str
    statement: str
    reference_answer: str
    raw_ocr: str
    needs_confirmation: bool
    category: str
    temp_image_path: str


def _write_temp_image(image_bytes: bytes, suffix: str) -> Path:
    _TMP_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    path = _TMP_IMAGE_DIR / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(image_bytes)
    return path


def _build_permanent_image_path(source_path: Path) -> Path:
    today = date.today()
    target_dir = _MISTAKE_IMAGE_DIR / f"{today.year}" / f"{today.month:02d}"
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / source_path.name


async def create_photo_draft(
    image_bytes: bytes,
    filename: str,
    subject: str,
    grade: str,
) -> PhotoDraft:
    suffix = Path(filename).suffix or ".jpg"
    temp_path = _write_temp_image(image_bytes, suffix)
    result = await image_to_problem(image_bytes, subject=subject, grade=grade)
    category = await categorize_problem(result["statement"], subject, grade, result["raw_ocr"])
    draft = PhotoDraft(
        id=uuid.uuid4().hex,
        subject=subject,
        grade=grade,
        statement=result["statement"],
        reference_answer=result["reference_answer"],
        raw_ocr=result["raw_ocr"],
        needs_confirmation=bool(result.get("needs_confirmation", False)),
        category=category,
        temp_image_path=str(temp_path),
    )
    _drafts[draft.id] = draft
    return draft


def get_photo_draft(draft_id: str) -> PhotoDraft:
    try:
        return _drafts[draft_id]
    except KeyError as exc:
        raise ValueError("Photo draft not found") from exc


async def build_finalized_photo_payload(draft_id: str, statement: str) -> dict[str, str | bool]:
    draft = get_photo_draft(draft_id)
    final_statement = statement.strip() or draft.statement
    if final_statement != draft.statement:
        solved = await solve_problem(final_statement, draft.subject, draft.grade)
        if solved.get("needs_confirmation") or not solved.get("reference_answer"):
            return {
                "subject": draft.subject,
                "grade": draft.grade,
                "statement": final_statement,
                "answer": "",
                "category": draft.category,
                "needs_confirmation": True,
                "raw_ocr": draft.raw_ocr,
            }
        category = await categorize_problem(final_statement, draft.subject, draft.grade, draft.raw_ocr)
        return {
            "subject": draft.subject,
            "grade": draft.grade,
            "statement": final_statement,
            "answer": str(solved["reference_answer"]).strip(),
            "category": category,
            "needs_confirmation": False,
            "raw_ocr": draft.raw_ocr,
        }
    return {
        "subject": draft.subject,
        "grade": draft.grade,
        "statement": draft.statement,
        "answer": draft.reference_answer,
        "category": draft.category,
        "needs_confirmation": draft.needs_confirmation,
        "raw_ocr": draft.raw_ocr,
    }


def move_draft_image_to_mistake_store(draft_id: str) -> str:
    draft = get_photo_draft(draft_id)
    source = Path(draft.temp_image_path)
    if not source.exists():
        raise FileNotFoundError(
            f"Temp image for draft {draft_id!r} not found at {source}; "
            "it may have already been moved or deleted."
        )
    target = _build_permanent_image_path(source)
    shutil.move(str(source), str(target))
    return str(target.relative_to(Path(__file__).resolve().parents[2]))


def discard_photo_draft(draft_id: str) -> None:
    draft = _drafts.pop(draft_id, None)
    if draft is None:
        return
    path = Path(draft.temp_image_path)
    if path.exists():
        path.unlink()
