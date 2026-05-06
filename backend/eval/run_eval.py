"""M0 acceptance evaluation runner.

Usage:
    python -m eval.run_eval --output eval/reports/m0_<date>.json [--max-turns 30]

Reads tests/data/eval_questions.yaml, drives Tutor↔StudentSimulator for each
problem, writes per-problem & aggregate stats. Prints PASS/FAIL on the
≥25/30 acceptance threshold.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from app.core.llm_router import LLMRouter
from app.core.socratic_tutor import SocraticTutor
from app.core.student_simulator import StudentSimulator
from app.models.schemas import Problem


DATA_PATH = Path(__file__).resolve().parents[1] / "tests" / "data" / "eval_questions.yaml"
ACCEPTANCE_THRESHOLD = 25


async def run_one(
    *, tutor, simulator, problem: Problem, max_turns: int = 30
) -> dict[str, Any]:
    session = tutor.start_session(problem)
    student_msg = "（开始解题）"
    turns_taken = 0
    for turn_idx in range(max_turns):
        tutor_turn = await tutor.take_turn(session, student_message=student_msg)
        turns_taken += 1
        if session.completed:
            break
        # Render tutor's tool call into a natural-language prompt for the student
        action = tutor_turn.action
        if action is None:
            question_text = ""
        elif action.name == "ask_question":
            question_text = action.arguments["question"]
        elif action.name == "acknowledge_correct_step":
            question_text = action.arguments.get("next_question") or "继续呢？"
        elif action.name == "hint":
            question_text = action.arguments["hint_text"]
        elif action.name == "redirect_thinking":
            question_text = action.arguments["redirect_question"]
        else:
            question_text = "继续。"

        student_msg = await simulator.respond(
            problem=problem, tutor_question=question_text, history=[]
        )

    return {
        "problem_id": problem.id,
        "subject": problem.subject,
        "grade": problem.grade,
        "completed": session.completed,
        "leak_detected": session.leak_detected,
        "turns": turns_taken,
        "hint_count": session.hint_count,
    }


async def run_all(*, max_turns: int = 30) -> dict[str, Any]:
    raw = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8"))
    problems = [Problem(**item) for item in raw]
    router = LLMRouter()
    tutor = SocraticTutor(router)
    simulator = StudentSimulator(router, capability="average")

    results = []
    for p in problems:
        try:
            r = await run_one(
                tutor=tutor, simulator=simulator, problem=p, max_turns=max_turns
            )
        except Exception as exc:  # noqa: BLE001
            r = {"problem_id": p.id, "error": repr(exc), "completed": False, "leak_detected": False, "turns": 0, "hint_count": 0}
        print(f"[{p.id}] completed={r['completed']} leak={r['leak_detected']} turns={r.get('turns')}")
        results.append(r)

    completed = sum(1 for r in results if r.get("completed"))
    leaks = sum(1 for r in results if r.get("leak_detected"))
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total": len(results),
        "completed": completed,
        "leaks": leaks,
        "passed_threshold": completed >= ACCEPTANCE_THRESHOLD and leaks == 0,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--max-turns", type=int, default=30)
    args = parser.parse_args()

    summary = asyncio.run(run_all(max_turns=args.max_turns))
    Path(args.output).write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== M0 Acceptance ===")
    print(f"Total:     {summary['total']}")
    print(f"Completed: {summary['completed']} (need ≥ {ACCEPTANCE_THRESHOLD})")
    print(f"Leaks:     {summary['leaks']} (need 0)")
    print(f"Result:    {'PASS ✅' if summary['passed_threshold'] else 'FAIL ❌'}")
    return 0 if summary["passed_threshold"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
