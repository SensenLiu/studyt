"""Route tests for branchable photo-draft endpoints and image retrieval."""
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest

import app.api.routes as routes
from app.api.main import app
from app.models.schemas import TutorAction


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_photo_draft_returns_branching_payload(client, monkeypatch):
    async def fake_create_photo_draft(image_bytes: bytes, filename: str, subject: str, grade: str):
        return SimpleNamespace(
            id="draft-1",
            statement="某数加 5 等于 12，求该数。",
            raw_ocr="某数加 5 等于 12，求该数。",
            needs_confirmation=False,
            category="一元一次方程",
        )

    monkeypatch.setattr(routes, "create_photo_draft", fake_create_photo_draft)

    response = client.post(
        "/api/photo-drafts?subject=math&grade=junior_1",
        files={"file": ("problem.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "draft_id": "draft-1",
        "statement": "某数加 5 等于 12，求该数。",
        "raw_ocr": "某数加 5 等于 12，求该数。",
        "needs_confirmation": False,
        "category": "一元一次方程",
    }


def test_create_photo_draft_returns_422_for_validation_errors(client, monkeypatch):
    async def fake_create_photo_draft(image_bytes: bytes, filename: str, subject: str, grade: str):
        raise ValueError("题目识别或求解结果还不够确定，请先确认题目内容")

    monkeypatch.setattr(routes, "create_photo_draft", fake_create_photo_draft)

    response = client.post(
        "/api/photo-drafts?subject=math&grade=junior_1",
        files={"file": ("problem.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "题目识别或求解结果还不够确定，请先确认题目内容"


def test_create_photo_draft_returns_502_for_unexpected_errors(client, monkeypatch):
    async def fake_create_photo_draft(image_bytes: bytes, filename: str, subject: str, grade: str):
        raise RuntimeError("Insufficient Balance")

    monkeypatch.setattr(routes, "create_photo_draft", fake_create_photo_draft)

    response = client.post(
        "/api/photo-drafts?subject=math&grade=junior_1",
        files={"file": ("problem.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Photo draft failed: Insufficient Balance"


def test_save_photo_draft_persists_image_and_category(client, monkeypatch):
    async def fake_build_finalized_photo_payload(draft_id: str, statement: str):
        return {
            "subject": "math",
            "grade": "junior_1",
            "statement": "某数加 5 等于 12，求该数。",
            "answer": "7",
            "category": "一元一次方程",
            "needs_confirmation": False,
            "raw_ocr": "某数加 5 等于 12，求该数。",
        }

    monkeypatch.setattr(routes, "build_finalized_photo_payload", fake_build_finalized_photo_payload)
    monkeypatch.setattr(routes, "move_draft_image_to_mistake_store", lambda draft_id: "data/mistake_images/2026/05/a.jpg")
    monkeypatch.setattr(routes, "discard_photo_draft", lambda draft_id: None)
    monkeypatch.setattr(routes, "add_mistake", lambda **kwargs: 42)
    monkeypatch.setattr(
        routes,
        "get_mistake",
        lambda mistake_id: {
            "id": 42,
            "subject": "math",
            "grade": "junior_1",
            "statement": "某数加 5 等于 12，求该数。",
            "answer": "7",
            "source": "photo",
            "added_date": "2026-05-23",
            "next_review": "2026-05-24",
            "review_count": 0,
            "note": "",
            "image_path": "data/mistake_images/2026/05/a.jpg",
            "category": "一元一次方程",
            "ocr_text": "某数加 5 等于 12，求该数。",
        },
    )

    response = client.post(
        "/api/photo-drafts/draft-1/save-mistake",
        json={"statement": "某数加 5 等于 12，求该数。"},
    )

    assert response.status_code == 200
    assert response.json()["image_path"].endswith("a.jpg")
    assert response.json()["category"] == "一元一次方程"


def test_get_mistake_image_returns_file(client, monkeypatch, tmp_path):
    image_path = tmp_path / "a.jpg"
    image_path.write_bytes(b"jpg")
    monkeypatch.setattr(
        routes,
        "get_mistake",
        lambda mistake_id: {
            "id": mistake_id,
            "image_path": str(image_path),
        },
    )

    response = client.get("/api/mistakes/7/image")

    assert response.status_code == 200
    assert response.content == b"jpg"


def test_start_session_from_photo_draft_rejects_needs_confirmation(client, monkeypatch):
    """422 when payload has needs_confirmation=True."""
    async def fake_build(draft_id: str, statement: str):
        return {
            "subject": "math",
            "grade": "junior_1",
            "statement": "题目",
            "answer": "",
            "category": "未分类",
            "needs_confirmation": True,
            "raw_ocr": "题目",
        }

    monkeypatch.setattr(routes, "build_finalized_photo_payload", fake_build)

    response = client.post(
        "/api/photo-drafts/draft-x/start-session",
        json={"statement": "题目"},
    )

    assert response.status_code == 422


def test_save_photo_draft_rejects_needs_confirmation(client, monkeypatch):
    """422 when payload has needs_confirmation=True."""
    async def fake_build(draft_id: str, statement: str):
        return {
            "subject": "math",
            "grade": "junior_1",
            "statement": "题目",
            "answer": "",
            "category": "未分类",
            "needs_confirmation": True,
            "raw_ocr": "题目",
        }

    monkeypatch.setattr(routes, "build_finalized_photo_payload", fake_build)

    response = client.post(
        "/api/photo-drafts/draft-x/save-mistake",
        json={"statement": "题目"},
    )

    assert response.status_code == 422


def test_get_mistake_image_returns_404_when_no_image(client, monkeypatch):
    """404 when mistake exists but has no image_path."""
    monkeypatch.setattr(
        routes,
        "get_mistake",
        lambda mistake_id: {"id": mistake_id, "image_path": ""},
    )

    response = client.get("/api/mistakes/99/image")

    assert response.status_code == 404


def test_delete_mistake_removes_image_file(client, monkeypatch, tmp_path):
    """Deleting a mistake with an image_path also removes the file."""
    image_file = tmp_path / "photo.jpg"
    image_file.write_bytes(b"image data")

    monkeypatch.setattr(
        routes,
        "delete_mistake",
        lambda mistake_id: {"id": mistake_id, "image_path": str(image_file)},
    )

    response = client.delete("/api/mistakes/5")

    assert response.status_code == 200
    assert not image_file.exists()


def test_mistake_from_photo_uses_photo_draft_wrapper(client, monkeypatch):
    async def fake_create_photo_draft(image_bytes: bytes, filename: str, subject: str, grade: str):
        assert subject == "physics"
        assert grade == "junior_2"
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

    discarded: list[str] = []

    monkeypatch.setattr(routes, "create_photo_draft", fake_create_photo_draft)
    monkeypatch.setattr(routes, "build_finalized_photo_payload", fake_build_finalized_photo_payload)
    monkeypatch.setattr(routes, "move_draft_image_to_mistake_store", lambda draft_id: "data/mistake_images/2026/05/p1.jpg")
    monkeypatch.setattr(routes, "discard_photo_draft", lambda draft_id: discarded.append(draft_id))
    monkeypatch.setattr(routes, "add_mistake", lambda **kwargs: 88)
    monkeypatch.setattr(
        routes,
        "get_mistake",
        lambda mistake_id: {
            "id": mistake_id,
            "subject": "physics",
            "grade": "junior_2",
            "statement": "质量为 2kg 的物体受到 10N 拉力，求加速度。",
            "answer": "5m/s²",
            "source": "photo",
            "added_date": "2026-05-23",
            "next_review": "2026-05-24",
            "review_count": 0,
            "note": "",
            "image_path": "data/mistake_images/2026/05/p1.jpg",
            "category": "牛顿第二定律",
            "ocr_text": "质量为 2kg 的物体受到 10N 拉力，求加速度。",
        },
    )

    response = client.post(
        "/api/mistakes/from-photo?subject=physics&grade=junior_2",
        files={"file": ("problem.jpg", b"fake-image", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["image_path"].endswith("p1.jpg")
    assert response.json()["category"] == "牛顿第二定律"
    assert discarded == ["draft-compat"]
