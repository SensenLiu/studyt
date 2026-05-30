"""Tests for extended mistake book: image_path, category, ocr_text persistence."""
from pathlib import Path

from app.core import mistake_book


def test_add_mistake_persists_image_and_category(tmp_path, monkeypatch):
    db_path = tmp_path / "mistakes.db"
    monkeypatch.setattr(mistake_book, "_DB_PATH", db_path)
    mistake_book.init_db()

    mid = mistake_book.add_mistake(
        subject="math",
        grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        answer="7",
        source="photo",
        note="OCR 保存",
        image_path="backend/data/mistake_images/2026/05/test.jpg",
        category="一元一次方程",
        ocr_text="某数加 5 等于 12，求该数。",
    )

    row = mistake_book.get_mistake(mid)
    assert row["image_path"].endswith("test.jpg")
    assert row["category"] == "一元一次方程"
    assert row["ocr_text"] == "某数加 5 等于 12，求该数。"


def test_delete_mistake_returns_deleted_row(tmp_path, monkeypatch):
    db_path = tmp_path / "mistakes.db"
    monkeypatch.setattr(mistake_book, "_DB_PATH", db_path)
    mistake_book.init_db()

    mid = mistake_book.add_mistake(
        subject="physics",
        grade="junior_2",
        statement="质量为 2kg 的物体受到 10N 拉力，求加速度。",
        answer="5m/s²",
        source="photo",
        image_path="backend/data/mistake_images/2026/05/p1.jpg",
        category="牛顿第二定律",
        ocr_text="质量为 2kg 的物体受到 10N 拉力，求加速度。",
    )

    deleted = mistake_book.delete_mistake(mid)

    assert deleted["id"] == mid
    assert deleted["image_path"].endswith("p1.jpg")
    assert mistake_book.get_mistake(mid) is None
