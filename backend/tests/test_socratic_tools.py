"""Sanity-check the 5 Socratic tool schemas (OpenAI tools format)."""
from app.core.socratic_tools import SOCRATIC_TOOLS, TOOL_NAMES


def test_five_tools_present():
    assert TOOL_NAMES == {
        "ask_question",
        "acknowledge_correct_step",
        "hint",
        "redirect_thinking",
        "summarize_at_end",
    }


def test_each_tool_has_function_schema():
    for t in SOCRATIC_TOOLS:
        assert t["type"] == "function"
        assert "name" in t["function"]
        assert "description" in t["function"]
        assert t["function"]["parameters"]["type"] == "object"


def test_hint_tool_constrains_level_to_1_3():
    hint = next(t for t in SOCRATIC_TOOLS if t["function"]["name"] == "hint")
    level = hint["function"]["parameters"]["properties"]["level"]
    assert level["enum"] == [1, 2, 3]
