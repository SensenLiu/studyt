# Study Assistant — Project Memory & Handoff

> **For any new Claude Code session opening this project: read this file first.** It tells you exactly where we are, what's decided, and what to do next.

**Last updated**: 2026-05-03 (mid M0 scaffolding)

---

## TL;DR — Resume Here

We are building an MVP K-12 Socratic AI tutor app (mobile, Flutter + Python backend). Product design and detailed M0 implementation plan are **both already approved by the user** and saved to disk. We were about to dispatch the first implementer subagent for Task 1 of M0 when the third-party Claude gateway (`new-api`) started returning 500 panics on every Agent dispatch, blocking the Subagent-Driven workflow.

**Next step:** Either retry Subagent-Driven mode (if gateway recovered) OR fall back to **inline execution** of the M0 plan (user's stated preference is Subagent-Driven, but they're OK with inline as a pragmatic fallback if dispatch keeps failing). Start at **Task 1 of `docs/superpowers/plans/2026-05-03-m0-socratic-tutor.md`**.

---

## Project Background

A mobile learning-assistant app for Chinese K-12 students (中小学生). Three product features were originally proposed by the user:

1. **引导式答疑** — Socratic-style guided Q&A (no direct answers)
2. **错题本+回顾** — Zero-friction error notebook + spaced-repetition review
3. **长期跟踪+个性化方案** — Long-term tracking and personalized study plans (deferred beyond MVP)

**MVP scope:** Features 1 + 2, math + physics, K-9 priority (full K-12 covered), no parent/teacher portal, internal Demo only, target tester is the user's own children.

**Differentiation:** Anti-pattern to 作业帮/小猿搜题 (which give answers directly, now under regulatory pressure in China). Mirrors Khan Academy's Khanmigo (true Socratic) plus Anki's FSRS (proper spaced repetition).

**Full product spec & rationale:** `/home/lss/.claude/plans/ai-1-skill-skill-2-kind-widget.md` — read this for context, market research summary, decision history.

---

## Confirmed Decisions (lock these in — do NOT re-litigate)

| Dimension | Decision |
|---|---|
| Product nature | MVP prototype/Demo |
| MVP scope | Features 1 + 2 |
| Target users | All K-12, K-9 priority |
| Subjects | Math + Physics |
| Parent/teacher portal | Not built |
| Mobile framework | Flutter (one codebase iOS+Android) |
| Backend | Python FastAPI + PostgreSQL + Redis |
| LLM strategy | Dual: Claude (guidance) + DeepSeek/Qwen (classify/cheap) |
| Claude access | **3rd-party OpenAI-compatible gateway** (e.g. AiHubMix, OpenRouter — NOT direct Anthropic API) |
| OCR | Aliyun OCR (含数学公式) |
| Knowledge graph | Course-standard skeleton + open datasets (Math23K etc.) |
| Test users | User's own children (1-2 kids) |
| Deployment | Internal Demo only |

---

## Where We Are Right Now

**Phase**: M0 implementation (Socratic engine validation), Task 1 not yet started.

**What's on disk:**
- `/home/lss/.claude/plans/ai-1-skill-skill-2-kind-widget.md` — approved product spec
- `docs/superpowers/plans/2026-05-03-m0-socratic-tutor.md` — approved M0 implementation plan (12 tasks, ~60 atomic TDD steps)
- `.gitignore`, `README.md` (placeholder) — committed in initial commit `a26c0bd`
- Empty directory tree: `backend/app/{core,models,safety}/`, `backend/tests/data/`, `backend/eval/reports/`, `app/lib/`

**What's NOT done:**
- All of Tasks 1–12 in the M0 plan
- No Python venv, no deps installed
- No `.env` (user needs to fill keys when at Task 11+)

---

## Workflow Status

User wanted **Subagent-Driven Development** (`superpowers:subagent-driven-development`). Standard flow per task = implementer → spec reviewer → code-quality reviewer.

**Blocker hit on 2026-05-03**: Every `Agent` tool dispatch fails with:
```
API Error: 500 Panic detected, error: runtime error: invalid memory address or nil pointer dereference
```
The error originates in the `new-api` server (third-party Claude gateway). Same error also seen on a research agent earlier the same day. WebSearch and WebFetch also flaky.

**Implication**: If the gateway is still broken when you resume:
- Try **one** Agent dispatch first — if it 500s again, fall back to inline execution (`superpowers:executing-plans` or just doing it yourself in the main session)
- Communicate the change of mode to the user
- TDD discipline + per-task commits remain non-negotiable regardless of mode

---

## How to Resume (concrete steps)

1. Read this file (you just did) ✓
2. Read the M0 plan: `docs/superpowers/plans/2026-05-03-m0-socratic-tutor.md`
3. Skim the product spec only if you need broader context: `/home/lss/.claude/plans/ai-1-skill-skill-2-kind-widget.md`
4. `git log --oneline` to see commit history
5. `git status` should be clean
6. Try a tiny `Agent` dispatch (e.g. trivial 'echo hello' general-purpose agent) to test gateway health
7. Based on result:
   - **Gateway healthy** → continue Subagent-Driven mode, start at Task 1 of M0 plan, follow the implementer / spec-reviewer / code-quality-reviewer pattern
   - **Gateway still 500ing** → tell user, switch to inline execution, start at Task 1 anyway

---

## Reading Order (for orientation)

1. **This file** (`CLAUDE.md`) — top-level context
2. `docs/superpowers/plans/2026-05-03-m0-socratic-tutor.md` — what to build next
3. `/home/lss/.claude/plans/ai-1-skill-skill-2-kind-widget.md` — full product spec (only if needed)

---

## Repository Layout (current and target)

```
study_assitant/                    ← project root, working dir
├── CLAUDE.md                       ← THIS FILE
├── README.md                       ← top-level (placeholder; Task 1 fills)
├── .gitignore                      ← present
│
├── docs/
│   └── superpowers/plans/2026-05-03-m0-socratic-tutor.md   ← M0 implementation plan
│
├── backend/                        ← Python FastAPI; ALL M0 code lives here
│   ├── app/{core,models,safety}/   (empty dirs exist)
│   ├── tests/data/                 (empty)
│   ├── eval/reports/               (empty)
│   └── (pyproject.toml, .env.example, conftest.py, etc. → built in Task 1)
│
└── app/                            ← Flutter; placeholder until M1
    └── lib/                        (empty)
```

---

## Critical Implementation Constraints (apply to every task)

1. **TDD always**: write failing test → run to confirm fail → implement → run to confirm pass → commit. Never skip.
2. **No placeholders**: code must be complete. No `TODO` / `pass # later`.
3. **Per-task commit**: one logical commit per plan task (or per logical step within); never one giant blob.
4. **Tool-use enforced for tutor**: `tool_choice='required'` whenever calling Claude for guidance role. Never let it produce free-form text answers.
5. **Leak guard hard rule**: every tutor response is post-processed by `LeakDetector`. If it flags, replace with safe fallback hint and set `session.leak_detected=True`. The 30-question eval acceptance requires `leaks==0`.
6. **OpenAI-compat for both LLMs**: use the `openai` Python SDK with custom `base_url` for both Claude (via gateway) and DeepSeek. Don't use the Anthropic SDK directly.

---

## Things You Should NOT Do (without asking)

- Do not change the dual-LLM strategy or swap out gateways
- Do not expand MVP scope to include Feature 3, parent portal, more subjects, etc.
- Do not start frontend / Flutter work — that's M1
- Do not change `requires-python = ">=3.11"` in pyproject.toml without checking with user
- Do not skip the leak detector or weaken its tests
- Do not create a worktree (user is solo; YAGNI)
- Do not drop tests to make things pass faster
- Do not commit `.env` (it's git-ignored, but be vigilant)

---

## Open Items the User Will Need to Provide Eventually

When you reach Task 11 (live API smoke test) or Task 12 (acceptance run), the user must populate `backend/.env` with real keys:
- `CLAUDE_GATEWAY_BASE_URL` + `CLAUDE_GATEWAY_API_KEY` + `CLAUDE_MODEL`
- `DEEPSEEK_BASE_URL` + `DEEPSEEK_API_KEY` + `DEEPSEEK_MODEL`

Tasks 1–10 do NOT need real keys (tests are mock-based). Don't block on key availability for those.

---

## Conversation Log (high-level events)

- **Brainstorming completed**: 4 critical product questions answered, market research compiled (no live web access today — used training-knowledge fallback), 4 follow-up detail questions answered → product spec written and approved
- **M0 plan completed**: 12 TDD tasks authored to `docs/superpowers/plans/2026-05-03-m0-socratic-tutor.md`, self-reviewed, approved
- **Subagent dispatch failed**: gateway returning 500 panics consistently; switched to writing this handoff doc on user's request
- **Pending on resume**: kick off Task 1 of M0 plan
