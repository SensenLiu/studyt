"""Shared dataclasses used across the Socratic engine."""
from __future__ import annotations
from typing import Literal, Any
from pydantic import BaseModel, Field, field_validator

Subject = Literal["math", "physics"]
Grade = Literal[
    "primary_4", "primary_5", "primary_6",
    "junior_1", "junior_2", "junior_3",
    "senior_1", "senior_2", "senior_3",
]

VALID_TOOLS = {
    "ask_question",
    "acknowledge_correct_step",
    "hint",
    "redirect_thinking",
    "summarize_at_end",
}


class Problem(BaseModel):
    id: str
    subject: Subject
    grade: Grade
    statement: str
    reference_answer: str
    knowledge_points: list[str] = Field(default_factory=list)
    expected_steps: int = 3  # rough difficulty proxy


class TutorAction(BaseModel):
    name: str
    arguments: dict[str, Any]

    @field_validator("name")
    @classmethod
    def _validate_name(cls, v: str) -> str:
        if v not in VALID_TOOLS:
            raise ValueError(f"unknown tool: {v}")
        return v


class TutorTurn(BaseModel):
    role: Literal["tutor", "student"]
    action: TutorAction | None = None
    text: str | None = None  # student message; tutor turns must use action


class SessionState(BaseModel):
    problem_id: str
    student_grade: Grade
    history: list[TutorTurn] = Field(default_factory=list)
    completed: bool = False
    leak_detected: bool = False
    hint_count: int = 0
