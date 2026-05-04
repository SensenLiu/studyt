"""Sanity-check the 30 eval problems load and have required fields."""
from pathlib import Path
import yaml
from app.models.schemas import Problem


DATA = Path(__file__).parent / "data" / "eval_questions.yaml"


def test_thirty_problems():
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    assert len(raw) == 30


def test_problems_validate_against_schema():
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    for item in raw:
        Problem(**item)  # raises if invalid


def test_grade_coverage():
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    grades = {p["grade"] for p in raw}
    # Must cover at least primary, junior, senior bands
    assert any(g.startswith("primary") for g in grades)
    assert any(g.startswith("junior") for g in grades)
    assert any(g.startswith("senior") for g in grades)


def test_subject_split():
    raw = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    math = sum(1 for p in raw if p["subject"] == "math")
    physics = sum(1 for p in raw if p["subject"] == "physics")
    assert math >= 20
    assert physics >= 5
