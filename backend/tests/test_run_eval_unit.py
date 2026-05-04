"""Unit-test the runner's single-problem driver with mocked tutor & student."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.schemas import Problem, SessionState, TutorAction, TutorTurn
from eval.run_eval import run_one


@pytest.fixture
def problem():
    return Problem(
        id="m_g7_001", subject="math", grade="junior_1",
        statement="x+5=12", reference_answer="7", knowledge_points=[],
    )


@pytest.mark.asyncio
async def test_run_one_terminates_on_summarize(problem):
    tutor = MagicMock()
    sim = MagicMock()

    summarize_action = TutorAction(
        name="summarize_at_end",
        arguments={"method_used": "x", "related_concepts": []},
    )
    summarize_turn = TutorTurn(role="tutor", action=summarize_action)
    final_session = SessionState(
        problem_id="m_g7_001", student_grade="junior_1", completed=True,
        leak_detected=False, hint_count=0,
    )
    tutor.start_session = MagicMock(return_value=final_session)
    tutor.take_turn = AsyncMock(return_value=summarize_turn)
    sim.respond = AsyncMock(return_value="是 7")

    report = await run_one(tutor=tutor, simulator=sim, problem=problem, max_turns=10)
    assert report["completed"] is True
    assert report["leak_detected"] is False


@pytest.mark.asyncio
async def test_run_one_caps_at_max_turns(problem):
    tutor = MagicMock()
    sim = MagicMock()
    ask_action = TutorAction(
        name="ask_question",
        arguments={"question": "?", "expected_thinking_direction": "x"},
    )
    ask_turn = TutorTurn(role="tutor", action=ask_action)
    state = SessionState(problem_id="m_g7_001", student_grade="junior_1")
    tutor.start_session = MagicMock(return_value=state)
    tutor.take_turn = AsyncMock(return_value=ask_turn)
    sim.respond = AsyncMock(return_value="嗯…")

    report = await run_one(tutor=tutor, simulator=sim, problem=problem, max_turns=5)
    assert report["completed"] is False
    assert report["turns"] == 5
