"""Command center smoke tests (Textual Pilot headless)."""

from __future__ import annotations

import pytest

from src.cli.tui.command_center import CommandCenter


@pytest.mark.asyncio
async def test_command_center_mounts_four_tabs():
    app = CommandCenter()
    async with app.run_test() as pilot:
        assert app.TITLE == "mk command center"
        tabs = app.query("TabPane")
        ids = sorted(str(t.id) for t in tabs)
        assert ids == ["tab-agents", "tab-chat", "tab-omni", "tab-opc"]
        await pilot.pause()


@pytest.mark.asyncio
async def test_command_center_chat_input_in_chat_tab():
    app = CommandCenter()
    async with app.run_test() as pilot:
        await pilot.pause()
        input_widget = app.query_one("#chat-input")
        assert input_widget is not None
        await pilot.press("/", "q", "u", "i", "t")
        await pilot.pause()


@pytest.mark.asyncio
async def test_opc_tab_connects_or_shows_error():
    # If a server is reachable on 18790 → connected banner; else error banner.
    app = CommandCenter()
    async with app.run_test() as pilot:
        await pilot.click("#tab-opc")
        await pilot.pause(0.5)
        summary = app.query_one("#opc-summary-text")
        text = str(summary.renderable)
        assert ("connected" in text) or ("WS error" in text) or ("connecting" in text)
