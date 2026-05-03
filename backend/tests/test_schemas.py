"""Validate shared dataclasses (problems, sessions, tutor responses)."""
import pytest
from app.models.schemas import (
    Problem,
    SessionState,
    TutorAction,
    TutorTurn,
)


def test_problem_minimal():
    p = Problem(
        id="m_g7_001",
        subject="math",
        grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7",
        knowledge_points=["一元一次方程"],
    )
    assert p.subject == "math"


def test_tutor_action_enum_strict():
    with pytest.raises(ValueError):
        TutorAction(name="bogus_tool", arguments={})


def test_session_state_appends_turn():
    s = SessionState(problem_id="m_g7_001", student_grade="junior_1", history=[])
    s.history.append(
        TutorTurn(
            role="tutor",
            action=TutorAction(name="ask_question", arguments={"question": "你怎么想?", "expected_thinking_direction": "reframe"}),
        )
    )
    assert len(s.history) == 1
