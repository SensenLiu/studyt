"""Mistake book: SQLite-backed wrong-answer collection with spaced review."""
from __future__ import annotations
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "mistakes.db"
_DB_PATH.parent.mkdir(exist_ok=True)

# Review intervals in days: review_count → days until next review
_INTERVALS = {0: 1, 1: 3, 2: 7, 3: 14, 4: 30}


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _ensure_columns(c: sqlite3.Connection) -> None:
    cols = {row["name"] for row in c.execute("PRAGMA table_info(mistakes)").fetchall()}
    additions = {
        "image_path": "TEXT DEFAULT ''",
        "category": "TEXT DEFAULT ''",
        "ocr_text": "TEXT DEFAULT ''",
    }
    for name, ddl in additions.items():
        if name not in cols:
            c.execute(f"ALTER TABLE mistakes ADD COLUMN {name} {ddl}")


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS mistakes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                subject      TEXT NOT NULL,
                grade        TEXT NOT NULL,
                statement    TEXT NOT NULL,
                answer       TEXT NOT NULL,
                source       TEXT DEFAULT 'session',
                added_date   TEXT NOT NULL,
                next_review  TEXT NOT NULL,
                review_count INTEGER DEFAULT 0,
                note         TEXT DEFAULT ''
            )
            """
        )
        _ensure_columns(c)


def add_mistake(
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
    today = date.today().isoformat()
    next_review = (date.today() + timedelta(days=_INTERVALS[0])).isoformat()
    with _conn() as c:
        cur = c.execute(
            """
            INSERT INTO mistakes (
                subject, grade, statement, answer, source,
                added_date, next_review, review_count, note,
                image_path, category, ocr_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?)
            """,
            (
                subject, grade, statement, answer, source,
                today, next_review, note,
                image_path, category, ocr_text,
            ),
        )
        return cur.lastrowid


def get_mistake(mistake_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM mistakes WHERE id = ?", (mistake_id,)).fetchone()
    return dict(row) if row else None


def list_mistakes(due_only: bool = False) -> list[dict]:
    today = date.today().isoformat()
    with _conn() as c:
        if due_only:
            rows = c.execute(
                "SELECT * FROM mistakes WHERE next_review <= ? ORDER BY next_review",
                (today,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT * FROM mistakes ORDER BY added_date DESC"
            ).fetchall()
    return [dict(r) for r in rows]


def mark_reviewed(mistake_id: int) -> dict:
    with _conn() as c:
        row = c.execute(
            "SELECT review_count FROM mistakes WHERE id = ?", (mistake_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Mistake {mistake_id} not found")
        count = row["review_count"] + 1
        days = _INTERVALS.get(count, 30)
        next_review = (date.today() + timedelta(days=days)).isoformat()
        c.execute(
            "UPDATE mistakes SET review_count = ?, next_review = ? WHERE id = ?",
            (count, next_review, mistake_id),
        )
        updated = c.execute(
            "SELECT * FROM mistakes WHERE id = ?", (mistake_id,)
        ).fetchone()
        return dict(updated)


def delete_mistake(mistake_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM mistakes WHERE id = ?", (mistake_id,)).fetchone()
        if row is None:
            return None
        c.execute("DELETE FROM mistakes WHERE id = ?", (mistake_id,))
    return dict(row)


def due_count() -> int:
    today = date.today().isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT COUNT(*) as n FROM mistakes WHERE next_review <= ?", (today,)
        ).fetchone()
        return row["n"]


init_db()
