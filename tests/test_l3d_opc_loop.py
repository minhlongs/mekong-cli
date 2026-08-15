"""Tests for OPC Business Loop (signal/revenue/metrics/loop)."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.opc_loop import KILL_CYCLES, MetricsStore, OpcLoop, RevenueLedger, SignalInbox


class _StubLLM:
    """LLM stub — deterministic, no network (rule: tests không gọi gateway)."""

    def text(self, model, prompt, system=None, max_tokens=4096):  # noqa: ANN001
        return "STUB ADVISORY: deterministic"

    def chat(self, model, messages, max_tokens=4096, timeout=None):  # noqa: ANN001
        return {"choices": [{"message": {"content": "STUB"}}]}


def _patch_llm():
    """Patch LLMClient trong module llm (nơi các hàm import) — deterministic."""
    from src.mk7.core import llm as llm_mod

    llm_mod.LLMClient = _StubLLM


def _fresh_loop(tmpdir: str, products: list[str] | None = None) -> OpcLoop:
    from src.mk7.core import opc_loop as m

    old_dir = m.OPC_DIR
    m.OPC_DIR = Path(tmpdir)
    m._state_dir = lambda: Path(tmpdir)  # noqa: E731 — patch cả state_dir
    _patch_llm()
    loop = OpcLoop()
    for p in products or []:
        if p not in loop.state.active_products:
            loop.state.active_products.append(p)
    loop.state.save()
    m.OPC_DIR = old_dir
    m.OPC_DIR = Path(tmpdir)
    return OpcLoop()


def test_signal_inbox():
    with tempfile.TemporaryDirectory() as td:
        loop = _fresh_loop(td)
        loop.signals.add("sophia", "lead", "khách hỏi mua")
        sigs = loop.signals.list("sophia")
        assert len(sigs) == 1
        assert sigs[0][1]["kind"] == "lead"


def test_revenue_requires_human():
    with tempfile.TemporaryDirectory() as td:
        loop = _fresh_loop(td)
        try:
            loop.revenue.record("sophia", 100)
            assert False, "must require confirmed_by"
        except ValueError:
            pass
        loop.revenue.record("sophia", 100, confirmed_by="founder")
        assert loop.revenue.total_for("sophia") == 100.0


def test_loop_kill_rule():
    with tempfile.TemporaryDirectory() as td:
        loop = _fresh_loop(td, ["dead-product"])
        # run kill_cycles cycles với $0 revenue
        for _ in range(KILL_CYCLES):
            r = loop.run_cycle(dry_run=True)
        assert "dead-product" in r["decide"]["kill"]
        assert "dead-product" in loop.state.archived_products


def test_loop_keeps_revenue_product():
    with tempfile.TemporaryDirectory() as td:
        loop = _fresh_loop(td, ["money-maker"])
        loop.revenue.record("money-maker", 500, confirmed_by="founder")
        r = loop.run_cycle(dry_run=True)
        assert "money-maker" in r["decide"]["keep"]
        assert r["decide"]["kill"] == []
        assert r["learn"]["money-maker"]["revenue"] == 500.0


def test_metrics_cycles_increment():
    with tempfile.TemporaryDirectory() as td:
        loop = _fresh_loop(td, ["p1"])
        loop.run_cycle(dry_run=True)
        loop.run_cycle(dry_run=True)
        assert loop.metrics.get("p1").get("cycles", 0) >= 2


def test_dedupe_active_products():
    with tempfile.TemporaryDirectory() as td:
        loop = _fresh_loop(td)
        loop.state.active_products = ["a", "a", "b"]
        loop.state.save()
        loop.run_cycle(dry_run=True)
        assert loop.state.active_products == ["a", "b"]


if __name__ == "__main__":
    import traceback

    failed = total = 0
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
