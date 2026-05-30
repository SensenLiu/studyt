from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

import app.api.routes as routes
from app.api.main import app
from app.models.schemas import TutorAction


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class _FakeTutor:
    def __init__(self, llm, captured_problems: list) -> None:
        self._captured_problems = captured_problems

    def start_session(self, problem):
        self._captured_problems.append(problem)
        return SimpleNamespace(completed=False, leak_detected=False, hint_count=0)

    async def take_turn(self, session, student_message: str):
        return SimpleNamespace(
            action=TutorAction(
                name="ask_question",
                arguments={
                    "question": "先看看题目里有哪些已知条件？",
                    "expected_thinking_direction": "reframe",
                },
            )
        )


def test_random_question_hides_reference_answer(client: TestClient):
    response = client.get("/api/questions/random?subject=math&grade=junior_1")

    assert response.status_code == 200
    data = response.json()
    assert "reference_answer" not in data


def test_ocr_endpoint_hides_reference_answer_and_surfaces_confirmation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    async def fake_image_to_problem(_: bytes, *, subject: str = "math", grade: str = "junior_1") -> dict[str, object]:
        return {
            "statement": "某数加 5 等于 12，求该数。",
            "reference_answer": "7",
            "raw_ocr": "某数加 5 等于 12，求该数。",
            "needs_confirmation": True,
            "answer_source": "solved",
        }

    monkeypatch.setattr(routes, "image_to_problem", fake_image_to_problem)

    response = client.post(
        "/api/ocr",
        files={"file": ("problem.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data == {
        "statement": "某数加 5 等于 12，求该数。",
        "raw_ocr": "某数加 5 等于 12，求该数。",
        "needs_confirmation": True,
    }


def test_start_session_accepts_missing_answer_and_derives_internal_answer(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    captured_problems = []

    async def fake_solve_problem(statement: str, subject: str, grade: str) -> dict[str, object]:
        assert statement == "某数加 5 等于 12，求该数。"
        assert subject == "math"
        assert grade == "junior_1"
        return {"reference_answer": "7", "needs_confirmation": False}

    monkeypatch.setattr(routes, "solve_problem", fake_solve_problem, raising=False)
    monkeypatch.setattr(routes, "LLMRouter", lambda: object())
    monkeypatch.setattr(routes, "SocraticTutor", lambda llm: _FakeTutor(llm, captured_problems))

    response = client.post(
        "/api/session/start",
        json={
            "subject": "math",
            "grade": "junior_1",
            "statement": "某数加 5 等于 12，求该数。",
            "knowledge_points": ["一元一次方程"],
        },
    )

    assert response.status_code == 200
    assert captured_problems[0].reference_answer == "7"


def test_start_session_rejects_when_internal_solver_needs_confirmation(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    async def fake_solve_problem(statement: str, subject: str, grade: str) -> dict[str, object]:
        return {"reference_answer": "", "needs_confirmation": True}

    monkeypatch.setattr(routes, "solve_problem", fake_solve_problem, raising=False)

    response = client.post(
        "/api/session/start",
        json={
            "subject": "math",
            "grade": "junior_1",
            "statement": "某数加 5 等于 12，求该数。",
            "knowledge_points": [],
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "题目识别或求解结果还不够确定，请先确认题目内容"


def test_mistake_from_photo_uses_subject_query_param(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    captured_create = {}
    captured_add = {}
    discarded = []

    async def fake_create_photo_draft(
        _: bytes, filename: str, subject: str, grade: str
    ):
        captured_create.update(filename=filename, subject=subject, grade=grade)
        return SimpleNamespace(
            id="draft-compat",
            statement="质量为 2kg 的物体受到 10N 拉力，求加速度。",
            raw_ocr="质量为 2kg 的物体受到 10N 拉力，求加速度。",
            needs_confirmation=False,
            category="牛顿第二定律",
        )

    async def fake_build_finalized_photo_payload(draft_id: str, statement: str):
        assert draft_id == "draft-compat"
        return {
            "subject": "physics",
            "grade": "junior_2",
            "statement": "质量为 2kg 的物体受到 10N 拉力，求加速度。",
            "answer": "5m/s²",
            "category": "牛顿第二定律",
            "needs_confirmation": False,
            "raw_ocr": "质量为 2kg 的物体受到 10N 拉力，求加速度。",
        }

    def fake_add_mistake(
        subject: str,
        grade: str,
        statement: str,
        answer: str,
        source: str = "session",
        note: str = "",
        image_path: str = "",
        category: str = "",
        ocr_text: str = "",
    ) -> int:
        captured_add.update(
            subject=subject,
            grade=grade,
            statement=statement,
            answer=answer,
            source=source,
            note=note,
            image_path=image_path,
            category=category,
            ocr_text=ocr_text,
        )
        return 99

    def fake_get_mistake(mistake_id: int):
        return {
            "id": mistake_id,
            "subject": captured_add["subject"],
            "grade": captured_add["grade"],
            "statement": captured_add["statement"],
            "answer": captured_add["answer"],
            "source": captured_add["source"],
            "added_date": "2026-05-15",
            "next_review": "2026-05-16",
            "review_count": 0,
            "note": captured_add["note"],
            "image_path": captured_add["image_path"],
            "category": captured_add["category"],
        }

    monkeypatch.setattr(routes, "create_photo_draft", fake_create_photo_draft)
    monkeypatch.setattr(routes, "build_finalized_photo_payload", fake_build_finalized_photo_payload)
    monkeypatch.setattr(routes, "move_draft_image_to_mistake_store", lambda draft_id: "data/mistake_images/2026/05/p1.jpg")
    monkeypatch.setattr(routes, "discard_photo_draft", lambda draft_id: discarded.append(draft_id))
    monkeypatch.setattr(routes, "add_mistake", fake_add_mistake)
    monkeypatch.setattr(routes, "get_mistake", fake_get_mistake)

    response = client.post(
        "/api/mistakes/from-photo?subject=physics&grade=junior_2",
        files={"file": ("physics-problem.png", b"fake-image", "image/png")},
    )

    assert response.status_code == 200
    assert captured_create["subject"] == "physics"
    assert captured_create["grade"] == "junior_2"
    assert captured_add["subject"] == "physics"
    assert captured_add["answer"] == "5m/s²"
    assert captured_add["category"] == "牛顿第二定律"
    assert discarded == ["draft-compat"]
