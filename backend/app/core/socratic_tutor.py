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
        # Tools that legitimately echo the student's own answer; no scan needed
        if action.name in ("summarize_at_end", "acknowledge_correct_step"):
            return action
        # Only hint_text is a direct-delivery field that must never reveal the answer.
        # Questions and redirects may mention answer values in Socratic context
        # (e.g. "你是怎么得到X的？" or intermediate calc steps); scanning them
        # produces too many false positives with no meaningful safety benefit.
        hint_text = action.arguments.get("hint_text", "")
        if hint_text and detect_answer_leak(hint_text, reference_answer):
            session.leak_detected = True
            return _SAFE_FALLBACK
        return action
