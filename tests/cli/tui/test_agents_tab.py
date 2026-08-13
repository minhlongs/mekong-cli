"""AgentsTab + tmux controller tests."""

from __future__ import annotations

import pytest

from src.cli.tui.command_center import CommandCenter
from src.cli.tui.tmux_controller import AGENTS, _ssh


def test_agent_registry():
    assert set(AGENTS.keys()) == {"claude", "opencode"}
    assert AGENTS["claude"]["session"] == "mk-claude"


def test_ssh_cmd_builds_with_path():
    stdout, _ = _ssh("echo HI", timeout=15)
    assert "HI" in stdout


@pytest.mark.asyncio
async def test_agents_tab_mounts_and_selects():
    app = CommandCenter()
    async with app.run_test() as pilot:
        await pilot.click("#tab-agents")
        await pilot.pause(0.3)
        hint = app.query_one("#agent-hint")
        assert "select" in str(hint.renderable).lower() or "selected" in str(hint.renderable).lower()
        await pilot.press("2")
        await pilot.pause()
        assert "opencode" in str(hint.renderable)
