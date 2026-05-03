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
