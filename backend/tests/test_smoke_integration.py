"""Live API smoke test — runs ONE problem end-to-end with real Claude+DeepSeek.

Skipped automatically if API keys are absent (see conftest.py).
"""
import pytest
from app.core.llm_router import LLMRouter
from app.core.socratic_tutor import SocraticTutor
from app.core.student_simulator import StudentSimulator
from app.models.schemas import Problem
from eval.run_eval import run_one


@pytest.mark.integration
@pytest.mark.asyncio
async def test_smoke_single_problem():
    router = LLMRouter()
    tutor = SocraticTutor(router)
    sim = StudentSimulator(router, capability="average")
    problem = Problem(
        id="smoke", subject="math", grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7", knowledge_points=["一元一次方程"],
    )
    report = await run_one(tutor=tutor, simulator=sim, problem=problem, max_turns=15)
    assert report["leak_detected"] is False, "Tutor leaked the answer!"
    assert isinstance(report["turns"], int)
