"""Session API routes: start a tutoring session and exchange turns."""
from __future__ import annotations
import random
import uuid
from pathlib import Path
from typing import Any

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.asr import transcribe
from app.core.ocr import image_to_problem
from app.core.mistake_book import (
    add_mistake, list_mistakes, mark_reviewed, delete_mistake, due_count
)
from app.core.llm_router import LLMRouter
from app.core.socratic_tutor import SocraticTutor
from app.models.schemas import (
    Grade, Problem, SessionState, Subject, TutorAction,
)

router = APIRouter()

# In-memory session store: session_id → (tutor, session, problem)
_sessions: dict[str, tuple[SocraticTutor, SessionState, Problem]] = {}

# Question bank loaded once at startup
_QBANK_PATH = Path(__file__).resolve().parents[2] / "tests" / "data" / "eval_questions.yaml"
_QBANK: list[dict] = yaml.safe_load(_QBANK_PATH.read_text(encoding="utf-8"))


def _action_to_display(action: TutorAction) -> str:
    args = action.arguments
    match action.name:
        case "ask_question":
            return args["question"]
        case "acknowledge_correct_step":
            base = args["what_student_got_right"]
            nq = args.get("next_question")
            return f"{base}\n\n{nq}" if nq else base
        case "hint":
            return f"💡 提示（等级 {args['level']}）：{args['hint_text']}"
        case "redirect_thinking":
            return args["redirect_question"]
        case "summarize_at_end":
            concepts = "、".join(args.get("related_concepts", []))
            return f"🎉 你自己解出来了！\n\n方法：{args['method_used']}\n知识点：{concepts}"
        case _:
            return str(args)


class StartRequest(BaseModel):
    subject: Subject
    grade: Grade
    statement: str
    reference_answer: str
    knowledge_points: list[str] = []


class TurnResponse(BaseModel):
    tool: str
    display_text: str
    completed: bool
    leak_detected: bool


class StartResponse(BaseModel):
    session_id: str
    turn: TurnResponse


class TurnRequest(BaseModel):
    session_id: str
    message: str


class QuestionItem(BaseModel):
    id: str
    subject: str
    grade: str
    statement: str
    reference_answer: str
    knowledge_points: list[str]


@router.get("/api/questions/random", response_model=QuestionItem)
async def random_question(
    subject: str | None = None,
    grade: str | None = None,
) -> Any:
    """Return a random question filtered by subject and/or grade."""
    pool = _QBANK
    if subject:
        pool = [q for q in pool if q["subject"] == subject]
    if grade:
        pool = [q for q in pool if q["grade"] == grade]
    if not pool:
        raise HTTPException(status_code=404, detail="没有符合条件的题目")
    q = random.choice(pool)
    return QuestionItem(**{k: q[k] for k in QuestionItem.model_fields if k in q})


@router.post("/api/session/start", response_model=StartResponse)
async def start_session(req: StartRequest) -> Any:
    problem = Problem(
        id=str(uuid.uuid4()),
        subject=req.subject,
        grade=req.grade,
        statement=req.statement,
        reference_answer=req.reference_answer,
        knowledge_points=req.knowledge_points,
    )
    router_llm = LLMRouter()
    tutor = SocraticTutor(router_llm)
    session = tutor.start_session(problem)
    turn = await tutor.take_turn(session, student_message="（开始）")
    session_id = str(uuid.uuid4())
    _sessions[session_id] = (tutor, session, problem)
    return StartResponse(
        session_id=session_id,
        turn=TurnResponse(
            tool=turn.action.name,
            display_text=_action_to_display(turn.action),
            completed=session.completed,
            leak_detected=session.leak_detected,
        ),
    )


class AsrResponse(BaseModel):
    text: str


class OcrResponse(BaseModel):
    statement: str
    reference_answer: str
    raw_ocr: str


@router.post("/api/ocr", response_model=OcrResponse)
async def ocr_image(file: UploadFile = File(...)) -> Any:
    """Receive an image file, OCR it, return extracted problem + answer."""
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")
    try:
        result = await image_to_problem(image_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR failed: {e}")
    return OcrResponse(**result)


@router.post("/api/asr", response_model=AsrResponse)
async def asr(file: UploadFile = File(...)) -> Any:
    """Receive an audio file, return transcribed text via Aliyun NLS."""
    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")
    try:
        text = await transcribe(audio_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ASR failed: {e}")
    return AsrResponse(text=text)


@router.post("/api/session/turn", response_model=TurnResponse)
async def take_turn(req: TurnRequest) -> Any:
    entry = _sessions.get(req.session_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Session not found")
    tutor, session, problem = entry
    if session.completed:
        raise HTTPException(status_code=400, detail="Session already completed")
    turn = await tutor.take_turn(session, student_message=req.message)
    # Auto-add to mistake book if session ends with too many hints (struggling)
    if session.completed and session.hint_count >= 3:
        add_mistake(
            subject=problem.subject,
            grade=problem.grade,
            statement=problem.statement,
            answer=problem.reference_answer,
            source="session",
            note=f"用了 {session.hint_count} 次提示",
        )
    return TurnResponse(
        tool=turn.action.name,
        display_text=_action_to_display(turn.action),
        completed=session.completed,
        leak_detected=session.leak_detected,
    )


# ── Mistake book endpoints ──────────────────────────────────────────────────

class MistakeIn(BaseModel):
    subject: str
    grade: str
    statement: str
    answer: str
    source: str = "manual"
    note: str = ""


class MistakeOut(BaseModel):
    id: int
    subject: str
    grade: str
    statement: str
    answer: str
    source: str
    added_date: str
    next_review: str
    review_count: int
    note: str


class DueCountOut(BaseModel):
    due: int


@router.get("/api/mistakes", response_model=list[MistakeOut])
async def get_mistakes(due_only: bool = False) -> Any:
    return list_mistakes(due_only=due_only)


@router.get("/api/mistakes/due-count", response_model=DueCountOut)
async def get_due_count() -> Any:
    return DueCountOut(due=due_count())


@router.post("/api/mistakes", response_model=MistakeOut)
async def create_mistake(m: MistakeIn) -> Any:
    mid = add_mistake(m.subject, m.grade, m.statement, m.answer, m.source, m.note)
    return list_mistakes()[0] if mid else {}


@router.post("/api/mistakes/from-session/add-from-session")
async def add_from_session(session_id: str) -> Any:
    """Manually add the current session's problem to mistake book."""
    entry = _sessions.get(session_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _, session, problem = entry
    mid = add_mistake(
        subject=problem.subject,
        grade=problem.grade,
        statement=problem.statement,
        answer=problem.reference_answer,
        source="manual",
    )
    return {"id": mid, "message": "已加入错题集"}


@router.post("/api/mistakes/from-photo", response_model=MistakeOut)
async def mistake_from_photo(
    grade: str,
    file: UploadFile = File(...),
) -> Any:
    """OCR a photo and add it directly to mistake book."""
    image_bytes = await file.read()
    try:
        result = await image_to_problem(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OCR failed: {e}")
    mid = add_mistake(
        subject="math",
        grade=grade,
        statement=result["statement"],
        answer=result["reference_answer"],
        source="photo",
    )
    rows = list_mistakes()
    return next(r for r in rows if r["id"] == mid)


@router.put("/api/mistakes/{mistake_id}/reviewed", response_model=MistakeOut)
async def reviewed(mistake_id: int) -> Any:
    try:
        return mark_reviewed(mistake_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/api/mistakes/{mistake_id}")
async def remove_mistake(mistake_id: int) -> Any:
    delete_mistake(mistake_id)
    return {"message": "已删除"}
