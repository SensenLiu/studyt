"""OpenAI-format function-calling schemas for the 5 Socratic actions.

Design principle: the LLM must always reply via one of these tools — never
plain text. This keeps answer-leakage risk low and makes responses parseable.
"""
from __future__ import annotations

SOCRATIC_TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "ask_question",
            "description": (
                "Ask the student a probing question to advance their thinking. "
                "Primary teaching action. Keep ≤ 2 sentences. NEVER reveal the answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Question shown to the student. ≤ 2 sentences.",
                    },
                    "expected_thinking_direction": {
                        "type": "string",
                        "description": "Internal note: thinking process you hope to trigger.",
                    },
                },
                "required": ["question", "expected_thinking_direction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "acknowledge_correct_step",
            "description": (
                "Affirm a specific correct step from the student before moving on. "
                "Use sparingly — never praise empty effort."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "what_student_got_right": {"type": "string"},
                    "next_question": {
                        "type": "string",
                        "description": "Optional follow-up question to push thinking forward.",
                    },
                },
                "required": ["what_student_got_right"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hint",
            "description": (
                "Provide a hint at increasing intensity. "
                "Level 1 = lightest nudge (mention concept), "
                "Level 2 = guide direction, "
                "Level 3 = strong hint (last resort, after ≥3 student failures). "
                "NEVER state the final answer."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {"type": "integer", "enum": [1, 2, 3]},
                    "hint_text": {"type": "string"},
                },
                "required": ["level", "hint_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "redirect_thinking",
            "description": (
                "Use when student is on the wrong track. "
                "DO NOT say 'you are wrong' — pose a probing question that exposes the flaw."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "why_student_is_off": {"type": "string"},
                    "redirect_question": {
                        "type": "string",
                        "description": "Probing question, NOT a correction statement.",
                    },
                },
                "required": ["why_student_is_off", "redirect_question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_at_end",
            "description": (
                "Use ONLY after the student has independently arrived at the correct "
                "final answer. Summarize the method and connect to broader concepts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "method_used": {"type": "string"},
                    "related_concepts": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["method_used", "related_concepts"],
            },
        },
    },
]

TOOL_NAMES = {t["function"]["name"] for t in SOCRATIC_TOOLS}
