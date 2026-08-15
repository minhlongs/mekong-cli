"""Tests for L2 port: extended tools (grep/glob/edit/apply_patch/webfetch/question) + MCP client."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.tools import ToolError, run_tool, _apply_patch_body, _ask_question


# ── extended tools ──────────────────────────────────────────

def test_grep_finds_text():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "a.py"
        f.write_text("def hello():\n    return 1\n")
        r = run_tool(f"grep hello {td}")
        assert r["ok"]
        assert "hello" in r["output"]


def test_grep_no_match():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "a.py"
        f.write_text("x = 1\n")
        r = run_tool(f"grep zzzz {td}")
        assert r["ok"]
        assert "(no matches)" in r["output"]


def test_glob_finds_files():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "one.ts").write_text("")
        (Path(td) / "two.ts").write_text("")
        r = run_tool(f"glob {td}/*.ts")
        assert r["ok"]
        assert "one.ts" in r["output"]
        assert "two.ts" in r["output"]


def test_edit_replace():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "x.py"
        f.write_text("print('old')\n")
        r = run_tool(f'edit {f} --old old --new new')
        assert r["ok"]
        assert "print('new')" in f.read_text()


def test_edit_missing_old_text():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "x.py"
        f.write_text("abc\n")
        r = run_tool(f'edit {f} --old zzz --new yyy')
        assert not r["ok"]
        assert "not found" in r["error"]


def test_apply_patch_add_and_update():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "sub" / "new.txt"
        patch = (
            f"*** Add File: {target}\nhello world\n"
            f"*** Update File: {target}\nhello world\n---\nHELLO WORLD\n"
        )
        summary = _apply_patch_body(patch)
        assert target.exists()
        assert target.read_text().strip() == "HELLO WORLD"
        assert "added" in summary and "updated" in summary


def test_apply_patch_delete():
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "gone.txt"
        f.write_text("bye")
        summary = _apply_patch_body(f"*** Delete File: {f}\n")
        assert not f.exists()
        assert "deleted" in summary


def test_webfetch_bad_url():
    try:
        run_tool("webfetch not-a-url")
        assert False
    except ToolError:
        pass


def test_question_aborted_on_eof():
    # monkeypatch input to raise EOFError -> returns aborted
    import builtins

    real_input = builtins.input
    builtins.input = lambda *a, **k: (_ for _ in ()).throw(EOFError())
    try:
        ans = _ask_question("Are you sure?", ["yes", "no"])
        assert "aborted" in ans
    finally:
        builtins.input = real_input


def test_tool_not_allowed():
    from src.mk7.core.gates import GateNotAllowed

    try:
        run_tool("curl http://evil.com")
        assert False
    except GateNotAllowed:
        pass


# ── MCP client (fake server) ────────────────────────────────

FAKE_MCP_SERVER = r"""
import json, sys
for line in sys.stdin:
    msg = json.loads(line)
    method = msg.get("method")
    if method == "initialize":
        reply = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"serverInfo": {"name": "fake"}}}
    elif method == "notifications/initialized":
        continue
    elif method == "tools/list":
        reply = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"tools": [{"name": "echo", "description": "echo text", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}}
    elif method == "tools/call":
        args = msg.get("params", {}).get("arguments", {})
        reply = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {"content": [{"type": "text", "text": "echo:" + str(args.get("text", ""))}]}}
    else:
        reply = {"jsonrpc": "2.0", "id": msg.get("id"), "result": {}}
    sys.stdout.write(json.dumps(reply) + "\n")
    sys.stdout.flush()
"""


def test_mcp_initialize_and_list():
    import sys as _sys

    from src.mk7.core.mcp import McpClient, McpServer

    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "fake_mcp.py"
        script.write_text(FAKE_MCP_SERVER)
        server = McpServer(name="fake", command=[_sys.executable, str(script)], cwd=td)
        with McpClient(server) as client:
            client.initialize()
            tools = client.list_tools()
            assert len(tools) == 1
            assert tools[0].name == "echo"


def test_mcp_call_tool():
    import sys as _sys

    from src.mk7.core.mcp import McpClient, McpServer

    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "fake_mcp.py"
        script.write_text(FAKE_MCP_SERVER)
        server = McpServer(name="fake", command=[_sys.executable, str(script)], cwd=td)
        with McpClient(server) as client:
            client.initialize()
            result = client.call_tool("echo", {"text": "hi"})
            assert result["ok"]
            assert "echo:hi" in result["output"]


if __name__ == "__main__":
    import traceback

    failed = 0
    total = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            total += 1
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)
