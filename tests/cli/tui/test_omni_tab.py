"""OmniRoute poller tests (mock ssh where possible)."""

from __future__ import annotations

import pytest

from src.cli.tui.omni_poller import OmniPoll, _ssh


def test_omni_poll_dataclass_defaults():
    p = OmniPoll()
    assert p.health == "?"
    assert p.quota == "?"
    assert p.recent == ""


def test_ssh_returns_stdout():
    out = _ssh("echo POLL_OK", timeout=15)
    assert "POLL_OK" in out


@pytest.mark.asyncio
async def test_omni_tab_mounts():
    from src.cli.tui.command_center import CommandCenter

    app = CommandCenter()
    async with app.run_test() as pilot:
        await pilot.click("#tab-omni")
        await pilot.pause(0.5)
        status = app.query_one("#omni-status")
        text = str(status.renderable)
        assert ("poll" in text.lower()) or ("●" in text) or ("quota" in text.lower())
