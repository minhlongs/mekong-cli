"""Tests for gate registry + tool whitelist executor."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.gates import GATE_EXIT_CODE, GateDecision, GateNotAllowed, GateRegistry
from src.mk7.core.tools import ensure_shell_safe, run_tool


def test_default_gates_present():
    r = GateRegistry()
    for kw in ("deploy", "rm", "git push --force", "chi-tien", "xoa-data"):
        assert kw in r.gates


def test_deploy_blocks():
    r = GateRegistry()
    d = r.evaluate("deploy the service to production")
    assert d.blocked
    assert d.gate_key == "deploy"
    assert d.exit_code == GATE_EXIT_CODE


def test_rm_blocks():
    r = GateRegistry()
    d = r.evaluate("cleanup old files")
    assert not d.blocked
    d2 = r.evaluate("rm -rf build dir")
    assert d2.blocked
    assert d2.gate_key == "rm"


def test_chi_tien_blocks():
    r = GateRegistry()
    d = r.evaluate("chi tien 10$ ad campaign")
    assert d.blocked
    assert d.gate_key == "spend_money"


def test_hard_gate_never_overridable():
    r = GateRegistry(extra_gates={"code_review_required": ("code_review_required", "x")})
    d = r.evaluate("merge feature", hard_flags=["code_review_required"])
    assert d.blocked
    assert d.hard
    assert d.exit_code == GATE_EXIT_CODE


def test_safe_task_not_blocked():
    r = GateRegistry()
    d = r.evaluate("fix typo in readme")
    assert not d.blocked


def test_ensure_tool_allowed_whitelist():
    from src.mk7.core.tools import ensure_tool_allowed

    ensure_tool_allowed("bash-test ls -la")
    ensure_tool_allowed("write /tmp/x content")
    try:
        ensure_tool_allowed("curl http://evil")
        assert False
    except GateNotAllowed:
        pass
    try:
        ensure_tool_allowed("python3 -c evil")
        assert False
    except GateNotAllowed:
        pass


def test_ensure_shell_safe_forbids_destructive():
    for bad in ("rm -rf /", "git push --force main", "sudo rm", "dd if=/dev/zero"):
        try:
            ensure_shell_safe(bad)
            assert False, f"should forbid: {bad}"
        except GateNotAllowed:
            pass
    ensure_shell_safe("ls -la")  # safe


def test_run_tool_write_read():
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "sub" / "f.txt"
        w = run_tool(f'write {target} hello')
        assert w["ok"]
        assert target.exists()
        c = run_tool(f"cat {target}")
        assert c["ok"]
        assert "hello" in c["output"]


def test_run_tool_bash_test():
    r = run_tool("bash-test echo hello")
    assert r["ok"]
    assert "hello" in r["output"]


def test_run_tool_bash_test_forbidden():
    try:
        run_tool("bash-test rm -rf /tmp/x")
        assert False
    except GateNotAllowed:
        pass


def test_run_tool_unknown():
    try:
        run_tool("definitely-not-a-tool foo")
        assert False, "should raise GateNotAllowed"
    except GateNotAllowed:
        pass


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
    total = sum(1 for n in globals() if n.startswith("test_"))
    print(f"\n{total - failed}/{total} passed")
    sys.exit(1 if failed else 0)
