"""Verify SocraticTutor: starts session, takes a turn, parses tool call, blocks leaks."""
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.core.socratic_tutor import SocraticTutor
from app.models.schemas import Problem


def _mock_completion(tool_name: str, args: dict):
    """Build a fake OpenAI ChatCompletion response with a tool call."""
    msg = MagicMock()
    msg.content = None
    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function = MagicMock(name=tool_name, arguments=json.dumps(args))
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(args)
    msg.tool_calls = [tc]
    choice = MagicMock(message=msg, finish_reason="tool_calls")
    return MagicMock(choices=[choice])


@pytest.fixture
def problem():
    return Problem(
        id="m_g7_001",
        subject="math",
        grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7",
        knowledge_points=["一元一次方程"],
    )


@pytest.mark.asyncio
async def test_tutor_parses_ask_question_tool_call(problem):
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=_mock_completion(
            "ask_question",
            {"question": "题目要求什么？", "expected_thinking_direction": "reframe"},
        )
    )
    tutor = SocraticTutor(router)
    session = tutor.start_session(problem)
    turn = await tutor.take_turn(session, student_message="（开始）")
    assert turn.action.name == "ask_question"
    assert "题目要求什么" in turn.action.arguments["question"]
    assert len(session.history) == 2  # student + tutor


@pytest.mark.asyncio
async def test_tutor_blocks_leaked_answer(problem):
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=_mock_completion(
            "ask_question",
            # tutor accidentally puts the answer in the question
            {"question": "答案是 7，对吗？", "expected_thinking_direction": "x"},
        )
    )
    tutor = SocraticTutor(router)
    session = tutor.start_session(problem)
    turn = await tutor.take_turn(session, student_message="hi")
    # Tutor must have flagged the leak and replaced with a safe fallback hint
    assert session.leak_detected is True
    assert "7" not in turn.action.arguments.get("question", "") and \
           "7" not in turn.action.arguments.get("hint_text", "")


@pytest.mark.asyncio
async def test_tutor_marks_session_completed_on_summarize(problem):
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=_mock_completion(
            "summarize_at_end",
            {"method_used": "解一元一次方程", "related_concepts": ["移项", "等式性质"]},
        )
    )
    tutor = SocraticTutor(router)
    session = tutor.start_session(problem)
    await tutor.take_turn(session, student_message="所以是 7")
    assert session.completed is True
