"""Pytest config: load .env so live integration tests can be opt-in."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

import pytest


def pytest_collection_modifyitems(config, items):
    """Skip @pytest.mark.integration unless live smoke is explicitly enabled."""
    skip_integration = pytest.mark.skip(
        reason="Live integration tests require RUN_LIVE_INTEGRATION=1 and configured API keys"
    )
    live_opt_in = os.environ.get("RUN_LIVE_INTEGRATION") == "1"
    has_keys = bool(os.environ.get("CLAUDE_GATEWAY_API_KEY")) and bool(
        os.environ.get("DEEPSEEK_API_KEY")
    )
    if live_opt_in and has_keys:
        return
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
