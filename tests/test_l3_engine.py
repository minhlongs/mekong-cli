"""Tests for L3 port: compaction, maxSteps, plugins."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["MEKONG_CONFIG_DIR"] = tempfile.mkdtemp()

from src.mk7.core.compaction import CompactionResult, Compactor
from src.mk7.core.dispatch import dispatch_node
from src.mk7.core.graph import Node
from src.mk7.core.plugins import HookRegistry, PluginBlocked, PluginLoader


class _FakeClient:
    def __init__(self, reply: str = "SUMMARY"):
        self.reply = reply

    def text(self, model, prompt, system=None, max_tokens=4096):
        return self.reply


# ── COMPACTION ──────────────────────────────────────────────

def test_compactor_skips_small_context():
    c = Compactor(client=_FakeClient(), threshold_chars=10000)
    result = c.compact({"n1": "small"})
    assert not result.compacted


def test_compactor_triggers_on_large_context():
    c = Compactor(client=_FakeClient(reply="compact summary here"), threshold_chars=100)
    result = c.compact({"n1": "x" * 500})
    assert result.compacted
    assert "compact summary here" in result.summary


def test_compactor_excludes_key():
    c = Compactor(client=_FakeClient(reply="s"), threshold_chars=100)
    result = c.compact({"current": "y" * 500, "other": "z" * 500}, exclude_key="current")
    assert result.compacted
    # summarize called with the OTHER block only


def test_compactor_fallback_truncates():
    class _Fail:
        def text(self, model, prompt, system=None, max_tokens=4096):
            raise RuntimeError("model down")

    c = Compactor(client=_Fail(), threshold_chars=100, max_summary_chars=50)
    result = c.compact({"n1": "z" * 500})
    assert result.compacted
    assert len(result.summary) <= 50


def test_compactor_should_flag():
    c = Compactor(client=_FakeClient(), threshold_chars=50)
    assert c.should_compact({"a": "x" * 100})
    assert not c.should_compact({"a": "x"})


# ── MAXSTEPS ────────────────────────────────────────────────

def test_dispatch_max_steps_caps_tools():
    class _Client:
        def text(self, model, prompt, system=None, max_tokens=4096):
            return '{"tool": "bash-test", "command": "echo 1"}{"tool": "bash-test", "command": "echo 2"}{"tool": "bash-test", "command": "echo 3"}'

    node = Node(id="n1", task="test", agent="eng")
    result = dispatch_node(node, {}, client=_Client(), max_steps=2)
    assert len(result["tools"]) == 2  # capped at 2 rounds


def test_dispatch_no_cap_all_tools():
    class _Client:
        def text(self, model, prompt, system=None, max_tokens=4096):
            return '{"tool": "bash-test", "command": "echo 1"}{"tool": "bash-test", "command": "echo 2"}'

    node = Node(id="n1", task="test", agent="eng")
    result = dispatch_node(node, {}, client=_Client(), max_steps=0)
    assert len(result["tools"]) == 2


# ── PLUGINS ─────────────────────────────────────────────────

def test_plugin_blocked_before_hook():
    hooks = HookRegistry()

    def blocker(tool, args):
        if tool == "bash":
            raise PluginBlocked("no bash allowed")

    hooks.on_before("blocker", blocker)
    try:
        hooks.run_before("bash", {"command": "ls"})
        assert False
    except PluginBlocked:
        pass
    modified = hooks.run_before("read", {"path": "/x"})
    assert modified["path"] == "/x"


def test_plugin_before_modifies_args():
    hooks = HookRegistry()

    def modifier(tool, args):
        if tool == "write":
            return {**args, "content": "REWRITTEN"}
        return None

    hooks.on_before("modifier", modifier)
    modified = hooks.run_before("write", {"path": "a.txt", "content": "orig"})
    assert modified["content"] == "REWRITTEN"


def test_plugin_after_never_breaks():
    hooks = HookRegistry()

    def bad(tool, args, result):
        raise RuntimeError("after hook crash")

    hooks.on_after("bad", bad)
    hooks.run_after("read", {}, {"ok": True})  # must not raise


def test_plugin_loader_empty_dir():
    loader = PluginLoader(Path(tempfile.mkdtemp()))
    assert loader.load_all() == []


def test_plugin_loader_loads_module():
    with tempfile.TemporaryDirectory() as td:
        plugin = Path(td) / "my_plugin.py"
        plugin.write_text(
            "def register(hooks):\n"
            "    def h(tool, args):\n"
            "        return args\n"
            "    hooks.on_before('my_plugin', h)\n"
        )
        loader = PluginLoader(Path(td))
        loaded = loader.load_all()
        assert "my_plugin" in loaded


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
