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
