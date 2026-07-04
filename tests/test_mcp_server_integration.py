"""Integration tests for MCP server — real subprocess with JSON-RPC over stdio.

Spawns the MCP server as a subprocess and tests the actual MCP protocol
handshake, tool listing, and tool invocation.
"""

from __future__ import annotations

import json
import os
import selectors
import subprocess
import sys
import time
from pathlib import Path

import pytest

MODULE = "src.core.mcp_server"
PROTOCOL_VERSION = "2024-11-05"
SERVER_TIMEOUT = 15.0


@pytest.fixture(scope="module")
def mcp_proc():
    """Spawn MCP server subprocess with stdio transport.

    Yields (write, read, proc) helpers.
    """
    proc = subprocess.Popen(
        [sys.executable, "-m", MODULE],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={**os.environ, "PYTHONPATH": str(Path.cwd())},
        cwd=Path.cwd(),
        text=True,
    )

    sel = selectors.DefaultSelector()
    assert proc.stdout is not None
    sel.register(proc.stdout, selectors.EVENT_READ)

    def write(msg: dict) -> None:
        assert proc.stdin is not None
        proc.stdin.write(json.dumps(msg, separators=(",", ":")) + "\n")
        proc.stdin.flush()

    def read(timeout: float = SERVER_TIMEOUT) -> dict | None:
        if sel.select(timeout=timeout):
            line = proc.stdout.readline()
            if not line:
                return None
            return json.loads(line.strip())
        return None

    yield write, read, proc

    sel.close()
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def _handshake(write, read_):
    """Perform MCP initialize handshake. Returns True on success."""
    write({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"},
        },
    })
    resp = read_()
    if resp is None:
        return False
    write({"jsonrpc": "2.0", "method": "notifications/initialized"})
    time.sleep(0.3)
    return True


# ═══════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.integration
def test_initialize_handshake(mcp_proc):
    """Initialize returns server info with protocol version."""
    write, read_, _ = mcp_proc
    write({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"},
        },
    })
    resp = read_()
    assert resp is not None
    assert resp.get("id") == 1
    assert "result" in resp
    assert resp["result"].get("protocolVersion") == PROTOCOL_VERSION
    assert "serverInfo" in resp["result"]
    assert "capabilities" in resp["result"]


@pytest.mark.integration
def test_tools_list_returns_25_tools(mcp_proc):
    """tools/list returns all registered tools."""
    write, read_, _ = mcp_proc
    assert _handshake(write, read_)

    write({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    resp = read_()
    assert resp is not None
    assert resp.get("id") == 2
    tools = resp.get("result", {}).get("tools", [])
    assert len(tools) >= 20
    tool_names = {t["name"] for t in tools}
    for name in ("cc_memory_search", "cc_tasks_create", "cc_plan_start", "cc_ssj"):
        assert name in tool_names, f"Missing tool: {name}"


@pytest.mark.integration
def test_cc_ssj_diagnostics(mcp_proc):
    """cc_ssj diagnostics returns system information."""
    write, read_, _ = mcp_proc
    assert _handshake(write, read_)

    write({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "cc_ssj", "arguments": {"action": "diagnostics"}},
    })
    resp = read_()
    assert resp is not None
    assert resp.get("id") == 3
    result = resp.get("result", {})
    content = result.get("content", [])
    assert len(content) > 0
    text = content[0].get("text", "")
    assert "python" in text.lower() or "platform" in text.lower(), (
        f"Expected diagnostics content, got: {text[:200]}"
    )


@pytest.mark.integration
def test_cc_tasks_create_list_done(mcp_proc):
    """Full task lifecycle via MCP protocol."""
    write, read_, _ = mcp_proc
    assert _handshake(write, read_)
    next_id = 10

    def call(name: str, args: dict) -> dict:
        nonlocal next_id
        rid = next_id
        next_id += 1
        write({
            "jsonrpc": "2.0",
            "id": rid,
            "method": "tools/call",
            "params": {"name": name, "arguments": args},
        })
        resp = read_()
        assert resp is not None, f"No response for {name}({args})"
        assert resp.get("id") == rid
        r = resp.get("result", {})
        texts = [c.get("text", "") for c in r.get("content", [])]
        return json.loads(texts[0]) if texts else {}

    # Create
    result = call("cc_tasks_create", {"subject": "Integration test task"})
    assert result.get("ok") is True
    task = result.get("data", {}).get("task", {})
    task_id = task.get("task_id", "")
    assert task_id

    # List
    result = call("cc_tasks_list", {"status": ""})
    assert result.get("ok") is True
    assert len(result.get("data", {}).get("tasks", [])) >= 1

    # Done
    result = call("cc_tasks_done", {"task_id": task_id})
    assert result.get("ok") is True

    # Delete
    result = call("cc_tasks_delete", {"task_id": task_id})
    assert result.get("ok") is True
