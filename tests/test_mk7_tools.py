"""Tests for mk7 tool-call parsing (agents.py)."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.agents import _parse_tool_calls


def test_single_object():
    text = '{"tool": "bash", "command": "echo hi"}'
    calls = _parse_tool_calls(text)
    assert calls is not None and len(calls) == 1
    assert calls[0]["tool"] == "bash"


def test_concatenated_objects():
    text = '{"tool": "write", "path": "a.txt", "content": "x"}{"tool": "cat", "path": "a.txt"}'
    calls = _parse_tool_calls(text)
    assert calls is not None and len(calls) == 2
    assert calls[0]["tool"] == "write"
    assert calls[1]["tool"] == "cat"


def test_array():
    text = '[{"tool": "bash", "command": "pwd"}, {"tool": "write", "path": "b.txt", "content": "y"}]'
    calls = _parse_tool_calls(text)
    assert calls is not None and len(calls) == 2


def test_whitespace_between_objects():
    text = '{"tool": "write", "path": "c.txt", "content": "z"}\n\n{"tool": "bash", "command": "ls"}'
    calls = _parse_tool_calls(text)
    assert calls is not None and len(calls) == 2


def test_prose_returns_none():
    assert _parse_tool_calls("Here is the file content: hello world") is None
    assert _parse_tool_calls("") is None
    assert _parse_tool_calls("plain text without json") is None


def test_execute_write_and_bash():
    import json as _json

    from src.mk7.core.agents import _execute_tool_calls

    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "sum.py"
        cmd = f'python3 -c "import sys; sys.path.insert(0, \'{td}\'); from sum import add; print(add(2,3))"'
        call1 = _json.dumps({"tool": "write", "path": str(target), "content": "def add(a,b): return a+b\n"})
        call2 = _json.dumps({"tool": "bash", "command": cmd})
        reply = call1 + call2
        result = _execute_tool_calls(reply)
        assert target.exists()
        assert "[write]" in result
        assert "[bash]" in result
        assert "5" in result


def test_write_creates_parent_dirs():
    import json as _json

    from src.mk7.core.agents import _execute_tool_calls

    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "nested" / "deep" / "file.txt"
        call = _json.dumps({"tool": "write", "path": str(target), "content": "hello"})
        result = _execute_tool_calls(call)
        assert target.exists()
        assert target.read_text() == "hello"
        assert "[write]" in result


def test_json_then_prose():
    text = '{"tool": "bash", "command": "echo hi"}\nRESULT: Done'
    calls = _parse_tool_calls(text)
    assert calls is not None and len(calls) == 1
    assert calls[0]["tool"] == "bash"


def test_prose_between_objects_breaks_but_keeps_parsed():
    text = '{"tool": "write", "path": "d.txt", "content": "w"}\nnote here\n{"tool": "bash", "command": "ls"}'
    calls = _parse_tool_calls(text)
    assert calls is not None and len(calls) == 1
    assert calls[0]["tool"] == "write"


if __name__ == "__main__":
    import traceback

    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception:
                failed += 1
                print(f"FAIL {name}")
                traceback.print_exc()
    print(f"\n{6 - failed}/6 passed")
    sys.exit(1 if failed else 0)
