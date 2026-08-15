"""Tests for L3 wiring: compaction in dispatch, session in auto, LSP tools."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.dispatch import build_node_prompt
from src.mk7.core.graph import Node
from src.mk7.core.lsp import find_references, go_to_definition
from src.mk7.core.tools import run_tool


# ── prompt / compaction wiring ──────────────────────────────

def test_build_node_prompt_compact_block():
    node = Node(id="n2", task="task b", agent="eng")
    prompt = build_node_prompt(node, {"n1": "big context"}, compact_context="SUMMARY HERE")
    assert "SUMMARY HERE" in prompt
    assert "[Compacted prior context]" in prompt


def test_build_node_prompt_plain():
    node = Node(id="n1", task="task a", agent="eng")
    prompt = build_node_prompt(node, {}, compact_context="")
    assert "(no upstream context)" in prompt
    assert "Compacted" not in prompt


def test_build_node_prompt_skills():
    node = Node(id="n1", task="t", agent="eng")
    prompt = build_node_prompt(node, {}, skills_context="SKILL CONTENT")
    assert "SKILL CONTENT" in prompt


# ── LSP ─────────────────────────────────────────────────────

def test_go_to_definition_python():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "mod.py").write_text("def hello():\n    pass\n\nx = 1\n")
        hits = go_to_definition("hello", td)
        assert len(hits) >= 1
        assert hits[0]["line"] == 1  # rg line numbers are 1-based


def test_find_references():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.py").write_text("def helper():\n    pass\n\nhelper()\n")
        hits = find_references("helper", td)
        assert len(hits) >= 2  # definition + call


def test_lsp_tool_interface():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "mod.py").write_text("class MyClass:\n    pass\n")
        r = run_tool(f"lsp MyClass def {td}")
        assert r["ok"]
        assert "MyClass" in r["output"]


def test_lsp_tool_no_symbol():
    from src.mk7.core.tools import ToolError

    try:
        run_tool("lsp")
        assert False
    except ToolError:
        pass


def test_lsp_tool_no_match():
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "a.py").write_text("x = 1\n")
        r = run_tool(f"lsp NothingHere def {td}")
        assert r["ok"]
        assert "no def found" in r["output"]


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
