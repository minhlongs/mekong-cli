"""ChatTUI smoke tests using Textual Pilot (headless)."""

from __future__ import annotations

import pytest

from src.cli.tui.chat_config import MODELS
from src.cli.tui.chat_tui import ChatTUI


def _all_text(scroll) -> str:
    out: list[str] = []
    for node in scroll._nodes:  # type: ignore[attr-defined]
        content = getattr(node, "_markdown", None)
        if content is None:
            content = getattr(node, "renderable", None)
        if content is not None:
            out.append(str(content))
    return "\n".join(out)


@pytest.mark.asyncio
async def test_app_starts_and_commands():
    app = ChatTUI()
    async with app.run_test() as pilot:
        assert app.TITLE == "mk chat"
        input_widget = app.query_one("#chat-input")
        assert input_widget is not None
        await pilot.pause()
        # /help shows command list
        await pilot.press("/", "h", "e", "l", "p", "enter")
        await pilot.pause()
        scroll = app.query_one("#chat-scroll")
        assert "/help" in _all_text(scroll)
        # /clear works without error
        await pilot.press("/", "c", "l", "e", "a", "r", "enter")
        await pilot.pause()
        assert len(app.history) == 0


@pytest.mark.asyncio
async def test_model_switch_command():
    app = ChatTUI()
    async with app.run_test() as pilot:
        await pilot.press("/", "m", "o", "d", "e", "l", " ", "m", "i", "n", "i", "m", "a", "x", "enter")
        await pilot.pause()
        assert app.model == MODELS["minimax"]
        await pilot.press("/", "m", "o", "d", "e", "l", " ", "k", "i", "m", "i", "enter")
        await pilot.pause()
        assert app.model == MODELS["kimi"]


@pytest.mark.asyncio
async def test_unknown_command_notice():
    app = ChatTUI()
    async with app.run_test() as pilot:
        await pilot.press("/", "z", "z", "z", "enter")
        await pilot.pause()
        scroll = app.query_one("#chat-scroll")
        assert "unknown command" in _all_text(scroll)
