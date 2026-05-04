"""Abstract LLM access for guidance and classify roles (both via DeepSeek for now).

Claude gateway config is retained in .env for future use but routing is
temporarily unified to DeepSeek while the Claude gateway tool-use issue is
resolved.
"""
from __future__ import annotations
import os
from typing import Any, Literal
from openai import AsyncOpenAI

Role = Literal["guidance", "classify"]


class LLMRouter:
    """Both roles use DeepSeek (OpenAI-compatible). Claude gateway config kept for later."""

    def __init__(self) -> None:
        self.deepseek = AsyncOpenAI(
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=os.environ["DEEPSEEK_API_KEY"],
        )
        self.guidance_model = os.environ.get("GUIDANCE_MODEL", os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"))
        self.classify_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

    async def chat(
        self,
        role: Role,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict | None = None,
        **kwargs: Any,
    ):
        if role == "guidance":
            model = self.guidance_model
        elif role == "classify":
            model = self.classify_model
        else:
            raise ValueError(f"unknown role: {role}")

        params: dict[str, Any] = dict(model=model, messages=messages, **kwargs)
        if tools is not None:
            params["tools"] = tools
        if tool_choice is not None:
            params["tool_choice"] = tool_choice
        return await self.deepseek.chat.completions.create(**params)
