"""Session API routes: start a tutoring session and exchange turns."""
from __future__ import annotations
import uuid
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.asr import transcribe
from app.core.llm_router import LLMRouter
from app.core.socratic_tutor import SocraticTutor
from app.models.schemas import (
    Grade, Problem, SessionState, Subject, TutorAction,
)

router = APIRouter()

# In-memory session store: session_id → (tutor, session, problem)
_sessions: dict[str, tuple[SocraticTutor, SessionState, Problem]] = {}


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
    return TurnResponse(
        tool=turn.action.name,
        display_text=_action_to_display(turn.action),
        completed=session.completed,
        leak_detected=session.leak_detected,
    )
