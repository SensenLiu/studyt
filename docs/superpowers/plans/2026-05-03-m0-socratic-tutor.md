# M0: Socratic Tutor Engine — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build & validate (in pure backend, no frontend) a Socratic-style tutoring engine that guides students to solve K-12 math/physics problems WITHOUT leaking the answer. Pass acceptance: ≥ 25/30 problems solved by a simulated "student LLM" with zero answer-leakage.

**Architecture:** A `SocraticTutor` orchestrates an LLM (Claude via 3rd-party gateway, OpenAI-compatible API) constrained by Tool Use to call only Socratic-action tools (`ask_question`, `hint`, etc.). A `LeakDetector` post-processes every response to catch answer reveals. A `StudentSimulator` (DeepSeek) plays the role of student to drive end-to-end evaluation against 30 curated problems.

**Tech Stack:** Python 3.11+, `openai` SDK (used for both Claude-gateway and DeepSeek), `pydantic` (schemas), `pytest` + `pytest-asyncio`, `pyyaml`, `python-dotenv`, `uv` (env manager).

---

## File Structure (M0 only)

```
study_assitant/
├── .gitignore
├── README.md
├── backend/
│   ├── pyproject.toml
│   ├── .env.example
│   ├── README.md
│   ├── app/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── llm_router.py          # Claude + DeepSeek abstraction
│   │   │   ├── socratic_tools.py      # 5 tool JSON-schemas
│   │   │   ├── socratic_prompt.py     # system prompt builder
│   │   │   ├── leak_detector.py       # answer-leak detection
│   │   │   ├── student_simulator.py   # LLM-based student
│   │   │   └── socratic_tutor.py      # main engine
│   │   └── models/
│   │       ├── __init__.py
│   │       └── schemas.py             # Pydantic dataclasses
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_llm_router.py
│   │   ├── test_socratic_tools.py
│   │   ├── test_socratic_prompt.py
│   │   ├── test_leak_detector.py
│   │   ├── test_socratic_tutor.py
│   │   ├── test_student_simulator.py
│   │   └── data/
│   │       └── eval_questions.yaml    # 30 problems
│   └── eval/
│       ├── __init__.py
│       ├── run_eval.py                # acceptance runner
│       └── reports/                   # generated .md / .json
└── docs/
    ├── socratic-prompt-spec.md        # prompt+tool design rationale (optional, deferred)
    └── superpowers/plans/<this-file>
```

---

## Task 1: Project Scaffolding & Dependencies

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/README.md`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

- [ ] **Step 1: Write `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.env
*.egg-info/
dist/
build/
backend/eval/reports/*.md
backend/eval/reports/*.json
!backend/eval/reports/.gitkeep
.DS_Store
```

- [ ] **Step 2: Write `README.md`** (top-level)

```markdown
# Study Assistant — K-12 Socratic AI Tutor

MVP. See `/home/lss/.claude/plans/ai-1-skill-skill-2-kind-widget.md` for the product spec, `docs/superpowers/plans/` for implementation plans.

## Status
- M0 (Socratic engine validation): in progress

## Layout
- `backend/` — FastAPI + Socratic engine (Python)
- `app/`     — Flutter mobile app (placeholder; M1+)
- `docs/`    — design & plans
```

- [ ] **Step 3: Write `backend/pyproject.toml`**

```toml
[project]
name = "study-assistant-backend"
version = "0.1.0"
description = "Socratic AI tutor backend for K-12 math/physics."
requires-python = ">=3.11"
dependencies = [
    "openai>=1.50",
    "pydantic>=2.7",
    "python-dotenv>=1.0",
    "pyyaml>=6.0",
    "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.2",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["app*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: Write `backend/.env.example`**

```
# Claude via 3rd-party OpenAI-compatible gateway (e.g. AiHubMix, OpenRouter)
CLAUDE_GATEWAY_BASE_URL=https://api.example-gateway.com/v1
CLAUDE_GATEWAY_API_KEY=sk-xxx
CLAUDE_MODEL=claude-sonnet-4-5

# DeepSeek (native OpenAI-compatible)
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_MODEL=deepseek-chat
```

- [ ] **Step 5: Write `backend/README.md`**

```markdown
# Backend

## Setup
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # fill in real keys
```

## Run tests
```bash
pytest -v
```

## Run M0 acceptance eval
```bash
python -m eval.run_eval --output eval/reports/m0_$(date +%Y%m%d).json
```
```

- [ ] **Step 6: Write empty package init files**

Create empty files:
- `backend/app/__init__.py`
- `backend/app/core/__init__.py`
- `backend/app/models/__init__.py`
- `backend/tests/__init__.py`

Each with content: `# (intentionally empty)`

- [ ] **Step 7: Write `backend/tests/conftest.py`**

```python
"""Pytest config: load .env so integration tests can call real APIs when present."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.integration tests when keys missing."""
    skip_integration = pytest.mark.skip(reason="Live API keys not configured")
    has_keys = bool(os.environ.get("CLAUDE_GATEWAY_API_KEY")) and bool(
        os.environ.get("DEEPSEEK_API_KEY")
    )
    if has_keys:
        return
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
```

- [ ] **Step 8: Set up venv and verify install**

Run:
```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest --collect-only
```
Expected: `collected 0 items` (no tests yet, but pytest itself works).

- [ ] **Step 9: Initial commit**

```bash
cd /home/lss/study_assitant
git add -A
git commit -m "chore: scaffold backend project structure for M0 socratic tutor"
```

---

## Task 2: Pydantic Schemas (shared types)

**Files:**
- Create: `backend/app/models/schemas.py`
- Create: `backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test `tests/test_schemas.py`**

```python
"""Validate shared dataclasses (problems, sessions, tutor responses)."""
import pytest
from app.models.schemas import (
    Problem,
    SessionState,
    TutorAction,
    TutorTurn,
)


def test_problem_minimal():
    p = Problem(
        id="m_g7_001",
        subject="math",
        grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7",
        knowledge_points=["一元一次方程"],
    )
    assert p.subject == "math"


def test_tutor_action_enum_strict():
    with pytest.raises(ValueError):
        TutorAction(name="bogus_tool", arguments={})


def test_session_state_appends_turn():
    s = SessionState(problem_id="m_g7_001", student_grade="junior_1", history=[])
    s.history.append(
        TutorTurn(
            role="tutor",
            action=TutorAction(name="ask_question", arguments={"question": "你怎么想?", "expected_thinking_direction": "reframe"}),
        )
    )
    assert len(s.history) == 1
```

- [ ] **Step 2: Run test, confirm failure**

```bash
cd backend && pytest tests/test_schemas.py -v
```
Expected: ImportError / ModuleNotFoundError on `app.models.schemas`.

- [ ] **Step 3: Implement `app/models/schemas.py`**

```python
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
```

- [ ] **Step 4: Run test, verify pass**

```bash
pytest tests/test_schemas.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/schemas.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add Problem/Session/TutorAction pydantic models"
```

---

## Task 3: LLM Router

**Files:**
- Create: `backend/app/core/llm_router.py`
- Create: `backend/tests/test_llm_router.py`

- [ ] **Step 1: Write failing test (mock-based, no live API)**

```python
"""Verify routing logic: 'guidance' → Claude client; 'classify' → DeepSeek."""
import os
from unittest.mock import AsyncMock, patch
import pytest
from app.core.llm_router import LLMRouter


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("CLAUDE_GATEWAY_BASE_URL", "https://gw.test/v1")
    monkeypatch.setenv("CLAUDE_GATEWAY_API_KEY", "k1")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-test")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://ds.test/v1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "k2")
    monkeypatch.setenv("DEEPSEEK_MODEL", "ds-test")


@pytest.mark.asyncio
async def test_router_guidance_uses_claude():
    router = LLMRouter()
    fake = AsyncMock(return_value="claude-resp")
    router.claude.chat.completions.create = fake  # type: ignore[assignment]
    await router.chat(role="guidance", messages=[{"role": "user", "content": "hi"}])
    fake.assert_awaited_once()
    assert fake.call_args.kwargs["model"] == "claude-test"


@pytest.mark.asyncio
async def test_router_classify_uses_deepseek():
    router = LLMRouter()
    fake = AsyncMock(return_value="ds-resp")
    router.deepseek.chat.completions.create = fake  # type: ignore[assignment]
    await router.chat(role="classify", messages=[{"role": "user", "content": "hi"}])
    fake.assert_awaited_once()
    assert fake.call_args.kwargs["model"] == "ds-test"


@pytest.mark.asyncio
async def test_router_unknown_role_raises():
    router = LLMRouter()
    with pytest.raises(ValueError):
        await router.chat(role="bogus", messages=[])
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_llm_router.py -v
```
Expected: ImportError on `app.core.llm_router`.

- [ ] **Step 3: Implement `app/core/llm_router.py`**

```python
"""Abstract LLM access for guidance (Claude via 3rd-party gateway) and classify (DeepSeek)."""
from __future__ import annotations
import os
from typing import Any, Literal
from openai import AsyncOpenAI

Role = Literal["guidance", "classify"]


class LLMRouter:
    """Both upstreams expose OpenAI-compatible chat-completions API."""

    def __init__(self) -> None:
        self.claude = AsyncOpenAI(
            base_url=os.environ["CLAUDE_GATEWAY_BASE_URL"],
            api_key=os.environ["CLAUDE_GATEWAY_API_KEY"],
        )
        self.deepseek = AsyncOpenAI(
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=os.environ["DEEPSEEK_API_KEY"],
        )
        self.claude_model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")
        self.deepseek_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    async def chat(
        self,
        role: Role,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict | None = None,
        **kwargs: Any,
    ):
        if role == "guidance":
            client, model = self.claude, self.claude_model
        elif role == "classify":
            client, model = self.deepseek, self.deepseek_model
        else:
            raise ValueError(f"unknown role: {role}")

        params: dict[str, Any] = dict(model=model, messages=messages, **kwargs)
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        return await client.chat.completions.create(**params)
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_llm_router.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/llm_router.py backend/tests/test_llm_router.py
git commit -m "feat(llm): add LLMRouter abstracting Claude(gateway)+DeepSeek"
```

---

## Task 4: Socratic Tool Schemas

**Files:**
- Create: `backend/app/core/socratic_tools.py`
- Create: `backend/tests/test_socratic_tools.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_socratic_tools.py -v
```

- [ ] **Step 3: Implement `app/core/socratic_tools.py`**

```python
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
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_socratic_tools.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/socratic_tools.py backend/tests/test_socratic_tools.py
git commit -m "feat(socratic): define 5 Socratic action tool schemas"
```

---

## Task 5: System Prompt Builder

**Files:**
- Create: `backend/app/core/socratic_prompt.py`
- Create: `backend/tests/test_socratic_prompt.py`

- [ ] **Step 1: Write failing test**

```python
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
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_socratic_prompt.py -v
```

- [ ] **Step 3: Implement `app/core/socratic_prompt.py`**

```python
"""System prompt builder for the Socratic tutor."""
from __future__ import annotations
from app.models.schemas import Grade, Subject

_GRADE_BAND = {
    "primary_4": "小学", "primary_5": "小学", "primary_6": "小学",
    "junior_1": "初中", "junior_2": "初中", "junior_3": "初中",
    "senior_1": "高中", "senior_2": "高中", "senior_3": "高中",
}

_SUBJECT_CN = {"math": "数学", "physics": "物理"}

_TEMPLATE = """你是一名优秀的中{band}{subject_cn}老师，使用苏格拉底教学法引导学生独立思考。

# 学生信息
- 年级：{grade}（{band}）

# 当前题目
{problem_statement}

# 参考答案（内部参考，禁止告知学生）
{reference_answer}

# 核心原则（必须严格遵守）
1. **绝不直接告诉学生答案** —— 这是底线，违反即视为失败
2. 每次回复必须使用工具调用之一（ask_question / acknowledge_correct_step / hint / redirect_thinking / summarize_at_end），禁止纯文本回复
3. 单次提问 ≤ 2 句话；语言简洁，符合{band}学生水平
4. 学生答对一步 → 用 acknowledge_correct_step 推进
5. 学生答错或方向偏了 → 用 redirect_thinking 反问，不直接说"错了"
6. 学生卡住 → 按梯度使用 hint(level=1→2→3)；level=3 是最后兜底，仍不可直接说答案
7. 学生独立得出最终答案后，调用 summarize_at_end 收尾，归纳方法与关联知识点

# 引导思路（推荐五步）
1. 题目要求是什么？（从问题反推目标）
2. 已知条件有哪些？
3. 还需要什么条件 / 能从已知推出什么中间条件？
4. 这让你联想到什么知识点 / 公式？
5. 怎么把这些组合起来得到答案？

每一步只问一个核心问题，让学生回答后再推进。

# 失败兜底
若学生在同一卡点 ≥ 3 次仍未突破，将 hint level 升至 3，给出关键启示但仍不可直接说答案。

# 成功标准
你的 KPI 是"学生靠自己解出"，不是"你讲解清楚"。请克制讲解冲动。
"""


def build_socratic_prompt(
    subject: Subject,
    grade: Grade,
    problem_statement: str,
    reference_answer: str,
) -> str:
    return _TEMPLATE.format(
        band=_GRADE_BAND[grade],
        subject_cn=_SUBJECT_CN[subject],
        grade=grade,
        problem_statement=problem_statement,
        reference_answer=reference_answer,
    )
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_socratic_prompt.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/socratic_prompt.py backend/tests/test_socratic_prompt.py
git commit -m "feat(socratic): add grade/subject-aware system prompt builder"
```

---

## Task 6: Leak Detector

**Files:**
- Create: `backend/app/core/leak_detector.py`
- Create: `backend/tests/test_leak_detector.py`

- [ ] **Step 1: Write failing test**

```python
from app.core.leak_detector import detect_answer_leak, normalize


def test_normalize_strips_punct_and_lowercases():
    assert normalize("X = 7 . ") == "x=7"
    assert normalize("结果是 12 ") == "结果是12"


def test_exact_numeric_leak_detected():
    assert detect_answer_leak(response_text="所以答案是 7。", reference_answer="7")


def test_no_leak_when_only_method_mentioned():
    assert not detect_answer_leak(
        response_text="你能先写出方程吗？",
        reference_answer="x=7",
    )


def test_chinese_numeral_leak_detected():
    assert detect_answer_leak(
        response_text="所以 x 等于 三", reference_answer="x=3"
    )


def test_substring_inside_word_not_false_positive():
    # reference is "12", text contains "120" — should NOT count as leak
    assert not detect_answer_leak(
        response_text="如果有 120 个苹果……", reference_answer="12"
    )


def test_multi_value_reference_all_must_appear_for_leak():
    # reference "x=2, y=3" leaks only if both numbers in vicinity
    assert detect_answer_leak(
        response_text="解出 x=2 然后 y=3",
        reference_answer="x=2,y=3",
    )
    assert not detect_answer_leak(
        response_text="想想 x 的值",
        reference_answer="x=2,y=3",
    )
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_leak_detector.py -v
```

- [ ] **Step 3: Implement `app/core/leak_detector.py`**

```python
"""Answer-leak detector: regex-based, fast, runs on every tutor turn.

Strategy:
1. Normalize both reference answer and response (strip punctuation, lowercase, unify Chinese numerals).
2. Split reference into atomic value tokens (e.g. "x=2,y=3" → ["x=2","y=3"] → numbers ["2","3"]).
3. A leak is declared if EVERY non-trivial numeric/symbolic token from the reference appears in the response as a standalone token (word-boundary check).

This is intentionally conservative: false positives (over-flagging) are
acceptable for M0 — we'd rather refuse a legit response than leak. We can
loosen later if too noisy.
"""
from __future__ import annotations
import re
import unicodedata

_CN_NUMS = {"零": "0", "一": "1", "二": "2", "三": "3", "四": "4",
            "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower()
    # convert Chinese digits
    for cn, ar in _CN_NUMS.items():
        s = s.replace(cn, ar)
    # remove whitespace and common punctuation
    s = re.sub(r"[\s,，。．、:：;；!！?？]+", "", s)
    return s


_TOKEN_RE = re.compile(r"[a-z]?=?-?\d+(?:\.\d+)?")


def _atomic_tokens(reference: str) -> list[str]:
    norm = normalize(reference)
    tokens = _TOKEN_RE.findall(norm)
    if not tokens:
        # fallback: take normalized whole string as single token
        return [norm] if norm else []
    return tokens


def detect_answer_leak(response_text: str, reference_answer: str) -> bool:
    tokens = _atomic_tokens(reference_answer)
    if not tokens:
        return False
    norm_resp = normalize(response_text)
    # require word-ish boundaries for plain numbers to avoid "12" matching "120"
    for tok in tokens:
        # build a regex for boundary: digit-only tokens need \D-or-edge boundary
        if re.fullmatch(r"\d+(?:\.\d+)?", tok):
            pat = rf"(?<!\d){re.escape(tok)}(?!\d)"
        else:
            pat = re.escape(tok)
        if not re.search(pat, norm_resp):
            return False
    return True
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_leak_detector.py -v
```

If any test fails (boundary handling is finicky), iterate on the regex pattern in `detect_answer_leak` until all 6 tests pass before continuing.

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/leak_detector.py backend/tests/test_leak_detector.py
git commit -m "feat(safety): add answer-leak detector (regex + Chinese numeral handling)"
```

---

## Task 7: Socratic Tutor Core Engine

**Files:**
- Create: `backend/app/core/socratic_tutor.py`
- Create: `backend/tests/test_socratic_tutor.py`

- [ ] **Step 1: Write failing test (mock-based)**

```python
"""Verify SocraticTutor: starts session, takes a turn, parses tool call, blocks leaks."""
import json
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.core.socratic_tutor import SocraticTutor
from app.models.schemas import Problem


def _mock_completion(tool_name: str, args: dict):
    """Build a fake OpenAI ChatCompletion response with a tool call."""
    msg = MagicMock()
    msg.content = None
    tc = MagicMock()
    tc.id = "call_1"
    tc.type = "function"
    tc.function = MagicMock(name=tool_name, arguments=json.dumps(args))
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(args)
    msg.tool_calls = [tc]
    choice = MagicMock(message=msg, finish_reason="tool_calls")
    return MagicMock(choices=[choice])


@pytest.fixture
def problem():
    return Problem(
        id="m_g7_001",
        subject="math",
        grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7",
        knowledge_points=["一元一次方程"],
    )


@pytest.mark.asyncio
async def test_tutor_parses_ask_question_tool_call(problem):
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=_mock_completion(
            "ask_question",
            {"question": "题目要求什么？", "expected_thinking_direction": "reframe"},
        )
    )
    tutor = SocraticTutor(router)
    session = tutor.start_session(problem)
    turn = await tutor.take_turn(session, student_message="（开始）")
    assert turn.action.name == "ask_question"
    assert "题目要求什么" in turn.action.arguments["question"]
    assert len(session.history) == 2  # student + tutor


@pytest.mark.asyncio
async def test_tutor_blocks_leaked_answer(problem):
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=_mock_completion(
            "ask_question",
            # tutor accidentally puts the answer in the question
            {"question": "答案是 7，对吗？", "expected_thinking_direction": "x"},
        )
    )
    tutor = SocraticTutor(router)
    session = tutor.start_session(problem)
    turn = await tutor.take_turn(session, student_message="hi")
    # Tutor must have flagged the leak and replaced with a safe fallback hint
    assert session.leak_detected is True
    assert "7" not in turn.action.arguments.get("question", "") and \
           "7" not in turn.action.arguments.get("hint_text", "")


@pytest.mark.asyncio
async def test_tutor_marks_session_completed_on_summarize(problem):
    router = MagicMock()
    router.chat = AsyncMock(
        return_value=_mock_completion(
            "summarize_at_end",
            {"method_used": "解一元一次方程", "related_concepts": ["移项", "等式性质"]},
        )
    )
    tutor = SocraticTutor(router)
    session = tutor.start_session(problem)
    await tutor.take_turn(session, student_message="所以是 7")
    assert session.completed is True
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_socratic_tutor.py -v
```

- [ ] **Step 3: Implement `app/core/socratic_tutor.py`**

```python
"""Socratic tutor engine: orchestrates LLM with tool-use constraints + leak guard."""
from __future__ import annotations
import json
from app.core.llm_router import LLMRouter
from app.core.socratic_prompt import build_socratic_prompt
from app.core.socratic_tools import SOCRATIC_TOOLS
from app.core.leak_detector import detect_answer_leak
from app.models.schemas import Problem, SessionState, TutorAction, TutorTurn


_SAFE_FALLBACK = TutorAction(
    name="hint",
    arguments={
        "level": 1,
        "hint_text": "我们先一步一步来——题目里有哪些已知条件？",
    },
)


class SocraticTutor:
    def __init__(self, llm: LLMRouter) -> None:
        self.llm = llm
        self._problems: dict[str, Problem] = {}

    def start_session(self, problem: Problem) -> SessionState:
        self._problems[problem.id] = problem
        return SessionState(problem_id=problem.id, student_grade=problem.grade)

    async def take_turn(
        self, session: SessionState, student_message: str
    ) -> TutorTurn:
        problem = self._problems[session.problem_id]
        # Append student turn first
        session.history.append(TutorTurn(role="student", text=student_message))

        # Build OpenAI-format messages from session history
        messages: list[dict] = [
            {
                "role": "system",
                "content": build_socratic_prompt(
                    subject=problem.subject,
                    grade=problem.grade,
                    problem_statement=problem.statement,
                    reference_answer=problem.reference_answer,
                ),
            }
        ]
        for turn in session.history:
            if turn.role == "student":
                messages.append({"role": "user", "content": turn.text or ""})
            else:  # tutor
                # Render tutor's prior tool call back as assistant tool_call message
                assert turn.action is not None
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": f"call_{len(messages)}",
                                "type": "function",
                                "function": {
                                    "name": turn.action.name,
                                    "arguments": json.dumps(
                                        turn.action.arguments, ensure_ascii=False
                                    ),
                                },
                            }
                        ],
                    }
                )
                # tool result placeholder (we don't actually run tools server-side;
                # OpenAI protocol requires a tool message after tool_calls)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": f"call_{len(messages) - 1}",
                        "content": "ok",
                    }
                )

        completion = await self.llm.chat(
            role="guidance",
            messages=messages,
            tools=SOCRATIC_TOOLS,
            tool_choice="required",  # force tool use
        )

        action = self._parse_tool_call(completion)
        action = self._guard_against_leak(action, problem.reference_answer, session)

        if action.name == "hint":
            session.hint_count += 1
        if action.name == "summarize_at_end":
            session.completed = True

        turn = TutorTurn(role="tutor", action=action)
        session.history.append(turn)
        return turn

    @staticmethod
    def _parse_tool_call(completion) -> TutorAction:
        msg = completion.choices[0].message
        if not getattr(msg, "tool_calls", None):
            # Should not happen with tool_choice='required'; treat as fallback
            return _SAFE_FALLBACK
        tc = msg.tool_calls[0]
        try:
            args = json.loads(tc.function.arguments)
        except (TypeError, ValueError):
            return _SAFE_FALLBACK
        try:
            return TutorAction(name=tc.function.name, arguments=args)
        except ValueError:
            return _SAFE_FALLBACK

    @staticmethod
    def _guard_against_leak(
        action: TutorAction, reference_answer: str, session: SessionState
    ) -> TutorAction:
        # Concatenate all string args for scanning
        text_blob = " ".join(
            v for v in action.arguments.values() if isinstance(v, str)
        )
        if detect_answer_leak(text_blob, reference_answer):
            session.leak_detected = True
            return _SAFE_FALLBACK
        return action
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_socratic_tutor.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/socratic_tutor.py backend/tests/test_socratic_tutor.py
git commit -m "feat(socratic): add SocraticTutor engine with tool-use + leak guard"
```

---

## Task 8: Student Simulator

**Files:**
- Create: `backend/app/core/student_simulator.py`
- Create: `backend/tests/test_student_simulator.py`

- [ ] **Step 1: Write failing test**

```python
"""Student simulator drives end-to-end eval; uses cheap LLM with persona prompt."""
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.core.student_simulator import StudentSimulator
from app.models.schemas import Problem


def _text_completion(text: str):
    msg = MagicMock(content=text, tool_calls=None)
    return MagicMock(choices=[MagicMock(message=msg)])


@pytest.mark.asyncio
async def test_simulator_responds_with_text():
    router = MagicMock()
    router.chat = AsyncMock(return_value=_text_completion("我觉得已知是 5 和 12"))
    sim = StudentSimulator(router, capability="average")
    problem = Problem(
        id="x", subject="math", grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7", knowledge_points=[],
    )
    reply = await sim.respond(problem=problem, tutor_question="题目要求什么？", history=[])
    assert "5" in reply or "12" in reply
    # router should have been called with role='classify' (cheap tier)
    assert router.chat.call_args.kwargs["role"] == "classify"
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_student_simulator.py -v
```

- [ ] **Step 3: Implement `app/core/student_simulator.py`**

```python
"""LLM-based student simulator for offline evaluation of the Socratic engine."""
from __future__ import annotations
from typing import Literal
from app.core.llm_router import LLMRouter
from app.models.schemas import Problem

Capability = Literal["novice", "average", "skilled"]

_PERSONA_TEMPLATE = """你正在扮演一位{capability_cn}{grade}学生。
你的任务：和老师对话，**只回答老师的当前问题**，不主动跑题，不展示过强或过弱能力。

# 题目（你正在做这道题）
{problem}

# 行为准则
- 实话实说：不会就说不会，会一点就只答会的那部分
- 一次只回答一个问题，不要预先把所有解法说出来
- 中文回答，简短自然，像真实学生说话
- 不要用专业术语装懂；不要套用你训练数据里的标准解法直接抄
- 如果老师问的是开放性提问，给出你脑海里第一反应（即使不完整）"""

_CAPABILITY_CN = {"novice": "基础较弱的", "average": "中等水平的", "skilled": "学得不错的"}


class StudentSimulator:
    def __init__(self, llm: LLMRouter, capability: Capability = "average") -> None:
        self.llm = llm
        self.capability = capability

    async def respond(
        self,
        problem: Problem,
        tutor_question: str,
        history: list[dict],
    ) -> str:
        sys = _PERSONA_TEMPLATE.format(
            capability_cn=_CAPABILITY_CN[self.capability],
            grade=problem.grade,
            problem=problem.statement,
        )
        messages = [{"role": "system", "content": sys}]
        messages.extend(history)
        messages.append({"role": "user", "content": f"老师问你：{tutor_question}"})

        completion = await self.llm.chat(role="classify", messages=messages)
        return completion.choices[0].message.content or ""
```

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_student_simulator.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/student_simulator.py backend/tests/test_student_simulator.py
git commit -m "feat(eval): add StudentSimulator (DeepSeek-backed persona)"
```

---

## Task 9: Evaluation Question Set (30 problems)

**Files:**
- Create: `backend/tests/data/eval_questions.yaml`
- Create: `backend/tests/test_eval_data.py`

- [ ] **Step 1: Write failing test (validates data integrity)**

```python
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
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_eval_data.py -v
```

- [ ] **Step 3: Author `backend/tests/data/eval_questions.yaml`**

Author 30 questions hand-picked to cover the curriculum bands. Distribution:
- 数学小学（primary_5/6）: 8 题（含整数运算、分数、应用题、几何周长面积）
- 数学初中（junior_1/2/3）: 12 题（一元一次方程、二元一次方程组、勾股定理、二次函数、相似三角形）
- 数学高中（senior_1/2）: 5 题（函数、三角、数列基础）
- 物理初中（junior_2/3）: 5 题（受力分析、欧姆定律、密度、机械能）

Format example (full file template — author needs to expand to 30):

```yaml
- id: m_p5_001
  subject: math
  grade: primary_5
  statement: "一个长方形的长是 8 cm，宽是 5 cm，求它的周长。"
  reference_answer: "26 cm"
  knowledge_points: ["长方形周长公式"]
  expected_steps: 2

- id: m_p5_002
  subject: math
  grade: primary_5
  statement: "小明有 24 颗糖，分给 3 个朋友每人相同数量，每人得到几颗？"
  reference_answer: "8"
  knowledge_points: ["平均分"]
  expected_steps: 1

- id: m_p6_001
  subject: math
  grade: primary_6
  statement: "一个数的 3/4 是 18，这个数是多少？"
  reference_answer: "24"
  knowledge_points: ["分数除法"]
  expected_steps: 2

- id: m_j1_001
  subject: math
  grade: junior_1
  statement: "解方程：2x + 3 = 11"
  reference_answer: "x=4"
  knowledge_points: ["一元一次方程", "移项"]
  expected_steps: 2

- id: m_j2_001
  subject: math
  grade: junior_2
  statement: "已知直角三角形两直角边分别为 3 和 4，求斜边长。"
  reference_answer: "5"
  knowledge_points: ["勾股定理"]
  expected_steps: 2

- id: m_j2_002
  subject: math
  grade: junior_2
  statement: "解方程组：x+y=10, x-y=4"
  reference_answer: "x=7,y=3"
  knowledge_points: ["二元一次方程组", "加减消元"]
  expected_steps: 3

- id: m_j3_001
  subject: math
  grade: junior_3
  statement: "二次函数 y = x² - 4x + 3 的对称轴方程是什么？"
  reference_answer: "x=2"
  knowledge_points: ["二次函数", "对称轴"]
  expected_steps: 2

- id: m_s1_001
  subject: math
  grade: senior_1
  statement: "已知 sin θ = 1/2，θ 在第一象限，求 cos θ。"
  reference_answer: "√3/2"
  knowledge_points: ["三角恒等式", "sin²+cos²=1"]
  expected_steps: 2

- id: p_j2_001
  subject: physics
  grade: junior_2
  statement: "一个物体重 49 N，求它的质量（g=9.8 N/kg）。"
  reference_answer: "5 kg"
  knowledge_points: ["重力公式 G=mg"]
  expected_steps: 1

- id: p_j3_001
  subject: physics
  grade: junior_3
  statement: "电阻 R=10Ω，电流 I=0.2A，求电压。"
  reference_answer: "2 V"
  knowledge_points: ["欧姆定律 U=IR"]
  expected_steps: 1

# ... (continue to 30 total — author the remaining 20 with similar shape)
```

The plan executor must author all 30 entries before proceeding. Coverage targets above are non-negotiable.

- [ ] **Step 4: Run, verify pass**

```bash
pytest tests/test_eval_data.py -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/tests/data/eval_questions.yaml backend/tests/test_eval_data.py
git commit -m "feat(eval): curate 30-problem M0 evaluation dataset"
```

---

## Task 10: Evaluation Runner

**Files:**
- Create: `backend/eval/__init__.py` (empty)
- Create: `backend/eval/run_eval.py`
- Create: `backend/eval/reports/.gitkeep`
- Create: `backend/tests/test_run_eval_unit.py` (unit-tests core runner functions, not live API)

- [ ] **Step 1: Write failing test for the runner's per-problem function**

```python
"""Unit-test the runner's single-problem driver with mocked tutor & student."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.models.schemas import Problem, SessionState, TutorAction, TutorTurn
from eval.run_eval import run_one


@pytest.fixture
def problem():
    return Problem(
        id="m_g7_001", subject="math", grade="junior_1",
        statement="x+5=12", reference_answer="7", knowledge_points=[],
    )


@pytest.mark.asyncio
async def test_run_one_terminates_on_summarize(problem):
    tutor = MagicMock()
    sim = MagicMock()

    summarize_action = TutorAction(
        name="summarize_at_end",
        arguments={"method_used": "x", "related_concepts": []},
    )
    summarize_turn = TutorTurn(role="tutor", action=summarize_action)
    final_session = SessionState(
        problem_id="m_g7_001", student_grade="junior_1", completed=True,
        leak_detected=False, hint_count=0,
    )
    tutor.start_session = MagicMock(return_value=final_session)
    tutor.take_turn = AsyncMock(return_value=summarize_turn)
    sim.respond = AsyncMock(return_value="是 7")

    report = await run_one(tutor=tutor, simulator=sim, problem=problem, max_turns=10)
    assert report["completed"] is True
    assert report["leak_detected"] is False


@pytest.mark.asyncio
async def test_run_one_caps_at_max_turns(problem):
    tutor = MagicMock()
    sim = MagicMock()
    ask_action = TutorAction(
        name="ask_question",
        arguments={"question": "?", "expected_thinking_direction": "x"},
    )
    ask_turn = TutorTurn(role="tutor", action=ask_action)
    state = SessionState(problem_id="m_g7_001", student_grade="junior_1")
    tutor.start_session = MagicMock(return_value=state)
    tutor.take_turn = AsyncMock(return_value=ask_turn)
    sim.respond = AsyncMock(return_value="嗯…")

    report = await run_one(tutor=tutor, simulator=sim, problem=problem, max_turns=5)
    assert report["completed"] is False
    assert report["turns"] == 5
```

- [ ] **Step 2: Run, confirm failure**

```bash
pytest tests/test_run_eval_unit.py -v
```

- [ ] **Step 3: Implement `eval/run_eval.py`**

```python
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
    for turn_idx in range(max_turns):
        tutor_turn = await tutor.take_turn(session, student_message=student_msg)
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
        "turns": len(session.history) // 2,
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
```

- [ ] **Step 4: Create empty placeholders**

- `backend/eval/__init__.py` (content: `# eval package`)
- `backend/eval/reports/.gitkeep` (empty)

- [ ] **Step 5: Run unit tests, verify pass**

```bash
pytest tests/test_run_eval_unit.py -v
```

- [ ] **Step 6: Commit**

```bash
git add backend/eval/ backend/tests/test_run_eval_unit.py
git commit -m "feat(eval): add M0 acceptance runner with mockable per-problem driver"
```

---

## Task 11: Smoke-test against live APIs (1 problem)

**Files:**
- Create: `backend/tests/test_smoke_integration.py`

- [ ] **Step 1: Write integration smoke test**

```python
"""Live API smoke test — runs ONE problem end-to-end with real Claude+DeepSeek.

Skipped automatically if API keys are absent (see conftest.py).
"""
import pytest
from app.core.llm_router import LLMRouter
from app.core.socratic_tutor import SocraticTutor
from app.core.student_simulator import StudentSimulator
from app.models.schemas import Problem
from eval.run_eval import run_one


@pytest.mark.integration
@pytest.mark.asyncio
async def test_smoke_single_problem():
    router = LLMRouter()
    tutor = SocraticTutor(router)
    sim = StudentSimulator(router, capability="average")
    problem = Problem(
        id="smoke", subject="math", grade="junior_1",
        statement="某数加 5 等于 12，求该数。",
        reference_answer="7", knowledge_points=["一元一次方程"],
    )
    report = await run_one(tutor=tutor, simulator=sim, problem=problem, max_turns=15)
    # We don't assert completion (the LLM might still fail) — only that nothing crashed
    # AND no leak occurred.
    assert report["leak_detected"] is False, "Tutor leaked the answer!"
    assert isinstance(report["turns"], int)
```

- [ ] **Step 2: Run smoke test (requires real keys in `.env`)**

```bash
pytest tests/test_smoke_integration.py -v
```

Expected: with keys present → PASS or SKIP-with-noted-issue (we expect the leak guard to keep `leak_detected=False`); without keys → SKIPPED.

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_smoke_integration.py
git commit -m "test(eval): add live-API smoke test for tutor pipeline"
```

---

## Task 12: M0 Acceptance Run + Iterate

- [ ] **Step 1: Run full eval suite against live APIs**

```bash
cd backend
mkdir -p eval/reports
python -m eval.run_eval --output eval/reports/m0_$(date +%Y%m%d_%H%M).json
```

Capture the printed summary. Expected at first run: results vary; iteration usually needed.

- [ ] **Step 2: Triage failures**

For each problem where `completed=False` or `leak_detected=True`:
- Open the saved JSON, look at the per-problem entry
- (Optional but helpful) re-run that single problem with `--max-turns` higher and add print-debugging in `take_turn` to dump the LLM's tool args each round
- Categorize the failure:
  - **Leak**: prompt isn't strict enough → strengthen prohibition wording in `socratic_prompt.py`
  - **Got stuck (no progress)**: hint laddering broken → check `hint` description in `socratic_tools.py`
  - **Student-sim too dumb / too smart**: tweak `_PERSONA_TEMPLATE` in `student_simulator.py`

- [ ] **Step 3: Iterate prompts**

Make targeted edits, commit each (so we can bisect what helped):
```bash
git add -p
git commit -m "tune(prompt): strengthen no-leak clause for senior physics"
```
Re-run eval after each batch.

- [ ] **Step 4: Final acceptance check**

When the latest report shows:
- `completed >= 25`
- `leaks == 0`

Save the final report and tag the commit:
```bash
git tag m0-acceptance
git log --oneline | head
```

- [ ] **Step 5: Update top-level README & approved plan with M0 status**

Edit `/home/lss/study_assitant/README.md` to mark M0 as ✅ done with link to the latest report.

```bash
git add README.md
git commit -m "docs: mark M0 acceptance achieved (X/30, 0 leaks)"
```

---

## Risks (during M0 execution)

| Risk | Sign | Mitigation |
|---|---|---|
| Claude via gateway returns no `tool_calls` field | Tutor falls back to safe hint every turn → no progress | Add fallback: if `finish_reason='stop'`, append a system reminder and retry once with `tool_choice='required'` |
| OpenAI tool-call protocol mismatch on gateway | Errors at runtime | Test with a single live call early (Task 11 smoke) before authoring 30 questions |
| Student simulator too capable → solves immediately, hides tutor flaws | Many problems pass with `turns < 3` | Lower capability to "novice"; add to persona "你只回答问到的，不主动解题" |
| Eval runs cost too much | Budget alarm | Cap `max_turns=20`; cache responses; only re-run failures |
| Chinese-numeral leak detector overflags | Many `leak_detected=True` even on legit responses | Inspect a few cases; tighten `_atomic_tokens` to require ≥2-character tokens for non-numeric leaks |

---

## Out of Scope for M0 (deferred)

- FastAPI HTTP layer — no API endpoints yet (M1)
- OCR + 题目结构化 — students paste problem text directly into eval YAML (M1)
- Persistence — sessions live in process memory only (M2)
- FSRS scheduler — error notebook logic (M2)
- Flutter app — entirely M1+
- Knowledge graph beyond inline `knowledge_points` strings (M2)

---

## Self-Review Checklist (executor: do this BEFORE Task 12)

- [ ] All 11 prior tasks have green tests
- [ ] No `TODO` / `XXX` left in committed code (`grep -RIn "TODO\|XXX" backend/app backend/eval`)
- [ ] All 5 Socratic tool names appear in 4 places consistently: `socratic_tools.py`, `schemas.py::VALID_TOOLS`, `socratic_tutor.py` action handling, `run_eval.py` action→student-question rendering
- [ ] `.env.example` is complete — fresh clone can fill in keys and run
- [ ] `eval_questions.yaml` has exactly 30 entries, validated by `test_eval_data.py`
