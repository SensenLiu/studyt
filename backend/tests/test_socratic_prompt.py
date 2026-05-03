"""Verify the system prompt encodes hard constraints and adapts to grade/subject."""
from app.core.socratic_prompt import build_socratic_prompt


def test_prompt_contains_no_answer_clause():
    p = build_socratic_prompt(
        subject="math",
        grade="junior_1",
        problem_statement="x + 5 = 12, x = ?",
        reference_answer="7",
    )
    assert "绝不直接告诉学生答案" in p
    assert "工具调用" in p
    assert "x + 5 = 12" in p


def test_prompt_does_not_echo_reference_answer_into_visible_section():
    """Reference answer must be marked as internal-only, not student-visible."""
    p = build_socratic_prompt(
        subject="math",
        grade="primary_5",
        problem_statement="What is 3 × 4 ?",
        reference_answer="12",
    )
    # We require the answer to be wrapped with an internal-only marker
    assert "（内部参考，禁止告知学生）" in p


def test_prompt_grade_branch():
    p1 = build_socratic_prompt(
        subject="math", grade="primary_5", problem_statement="x", reference_answer="y"
    )
    p2 = build_socratic_prompt(
        subject="math", grade="senior_2", problem_statement="x", reference_answer="y"
    )
    assert "小学" in p1
    assert "高中" in p2
