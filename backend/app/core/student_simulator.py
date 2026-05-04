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
