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
