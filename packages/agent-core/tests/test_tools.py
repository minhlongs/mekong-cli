"""Tests for the tool registry."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx

from agent_core.tools.browser import browse_website
from agent_core.tools.execute import execute_command


def test_write_and_read_file_roundtrip(tmp_outputs: Path):
    import importlib

    import agent_core.tools.file_system as fs

    importlib.reload(fs)
    msg = fs.write_file("hello.txt", "world")
    assert "hello.txt" in msg
    assert fs.read_file("hello.txt") == "world"


def test_write_file_rejects_path_traversal(tmp_outputs: Path):
    import importlib

    import agent_core.tools.file_system as fs

    importlib.reload(fs)
    with pytest.raises(ValueError):
        fs.write_file("../escape.txt", "nope")


def test_write_file_rejects_sibling_prefix_bypass(tmp_outputs: Path):
    import importlib

    import agent_core.tools.file_system as fs

    importlib.reload(fs)
    sibling = tmp_outputs.parent / (tmp_outputs.name + "-evil")
    with pytest.raises(ValueError):
        fs.write_file(f"../{sibling.name}/x.txt", "nope")


def test_execute_command_rejects_cwd_outside_sandbox(tmp_outputs: Path):
    from agent_core.tools.execute import execute_command

    out = execute_command("echo hi", cwd="/")
    assert out.startswith("Lỗi:")


def test_read_file_returns_message_when_missing(tmp_outputs: Path):
    import importlib

    import agent_core.tools.file_system as fs

    importlib.reload(fs)
    out = fs.read_file("does-not-exist.txt")
    assert "không tồn tại" in out


@respx.mock
def test_browse_website_extracts_text():
    respx.get("https://example.com").mock(
        return_value=httpx.Response(
            200, text="<html><body><h1>Hi</h1><p>Content</p></body></html>"
        )
    )
    text = browse_website("https://example.com")
    assert "Hi" in text and "Content" in text
    assert "<h1>" not in text


@respx.mock
def test_browse_website_returns_error_on_http_failure():
    respx.get("https://example.com").mock(side_effect=httpx.ConnectError("boom"))
    out = browse_website("https://example.com")
    assert out.startswith("Lỗi khi truy cập")


def test_execute_command_success(tmp_outputs: Path):
    out = execute_command("echo hello", cwd=tmp_outputs)
    assert "hello" in out


def test_execute_command_nonzero_exit(tmp_outputs: Path):
    out = execute_command("false", cwd=tmp_outputs)
    assert out.startswith("[exit 1]")


def test_execute_command_rejects_empty():
    assert execute_command("") == "Lỗi: lệnh rỗng"
