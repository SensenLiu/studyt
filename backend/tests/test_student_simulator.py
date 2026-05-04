"""Student simulator drives end-to-end eval; uses cheap LLM with persona prompt."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.core.student_simulator import StudentSimulator
from app.models.schemas import Problem


def _text_completion(text: str):
    msg = MagicMock(content=text, tool_calls=None)
    return MagicMock(choices=[MagicMock(message=msg)])


@pytest.mark.asyncio
async def test_simulator_responds_with_text():
    router = MagicMock()
    router.chat = AsyncMock(return_value=_text_completion("我觉得已知是 5 和 12"))
    sim = StudentSimulator(router, capability="average")
    problem = Problem(
        id="x", subject="math", grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7", knowledge_points=[],
    )
    reply = await sim.respond(problem=problem, tutor_question="题目要求什么？", history=[])
    assert "5" in reply or "12" in reply
    # router should have been called with role='classify' (cheap tier)
    assert router.chat.call_args.kwargs["role"] == "classify"
