from __future__ import annotations

from types import SimpleNamespace

import tests.conftest as conftest


class FakeItem:
    def __init__(self, *, integration: bool) -> None:
        self.keywords = {"integration": True} if integration else {}
        self.markers: list[object] = []

    def add_marker(self, marker: object) -> None:
        self.markers.append(marker)


def test_integration_tests_are_skipped_without_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("CLAUDE_GATEWAY_API_KEY", "test-claude-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.delenv("RUN_LIVE_INTEGRATION", raising=False)

    item = FakeItem(integration=True)

    conftest.pytest_collection_modifyitems(SimpleNamespace(), [item])

    assert any(getattr(marker, "name", "") == "skip" for marker in item.markers)



def test_integration_tests_run_when_explicitly_enabled(monkeypatch):
    monkeypatch.setenv("CLAUDE_GATEWAY_API_KEY", "test-claude-key")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-deepseek-key")
    monkeypatch.setenv("RUN_LIVE_INTEGRATION", "1")

    item = FakeItem(integration=True)

    conftest.pytest_collection_modifyitems(SimpleNamespace(), [item])

    assert item.markers == []
