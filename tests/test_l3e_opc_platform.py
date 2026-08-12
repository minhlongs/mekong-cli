"""Tests cho OPC Platform modules: finance/analytics/sales/support/marketing/profile."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mk7.core.analytics import Analytics
from src.mk7.core.finance import Finance
from src.mk7.core.marketing import Marketing
from src.mk7.core.opc_loop import OpcLoop
from src.mk7.core.profile import (DEFAULT_PROFILE, active_profile, init_profile,
                                  list_profiles, set_active_profile, state_dir)
from src.mk7.core.sales import SalesPipeline
from src.mk7.core.support import SupportDesk


def _patch_state_dir(tmpdir: str):
    """Patch _state_dir của opc_loop để dùng tmpdir — tránh đụng state thật."""
    from src.mk7.core import opc_loop as m

    m._state_dir = lambda: Path(tmpdir)  # noqa: E731


# ── Finance ──────────────────────────────────────────────────

def test_cost_requires_human():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        f = Finance()
        try:
            f.costs.record("p", 5)
            assert False
        except ValueError:
            pass
        e = f.costs.record("p", 5, rate=50, by="founder")
        assert e.total_usd == 250.0


def test_finance_profit_mrr():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        f = Finance()
        f.costs.record("p", 2, rate=50, by="founder")          # cost 100
        f.revenue.record("p", 500, kind="subscription", confirmed_by="founder")
        assert f.profit("p") == 400.0
        assert f.mrr("p") == 500.0
        assert f.mrr() == 500.0


# ── Analytics ────────────────────────────────────────────────

def test_analytics_board():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        loop = OpcLoop()
        loop.state.active_products = ["p"]
        loop.state.save()
        a = Analytics()
        board = a.board()
        assert board["kpi"]["active_products"] == 1
        assert board["kpi"]["mrr"] == 0.0
        assert isinstance(board["kpi"]["conversion"], (int, float, type(None)))


# ── Sales ────────────────────────────────────────────────────

def test_sales_pipeline():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        s = SalesPipeline()
        s.leads = {"L1": {"id": "L1", "product": "p", "stage": "new", "note": "x", "ts": 0}}
        s._save()
        lead = s.advance("L1", "proposal")
        assert lead["stage"] == "proposal"
        proposal = s.draft_proposal("L1")
        assert "Proposal draft" in proposal


def test_sales_close_records_revenue():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        s = SalesPipeline()
        s.leads = {"L1": {"id": "L1", "product": "p", "stage": "new", "note": "x", "ts": 0}}
        s._save()
        s.close("L1", 100, by="founder")
        from src.mk7.core.opc_loop import RevenueLedger

        assert RevenueLedger().total_for("p") == 100.0


# ── Support ──────────────────────────────────────────────────

def test_support_ticket():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        d = SupportDesk()
        d.tickets = {"T1": {"id": "T1", "product": "p", "status": "open", "note": "bug", "ts": 0}}
        d._save()
        resp = d.draft_response("T1")
        assert "Response draft" in resp
        d.resolve("T1", by="founder")
        assert d.tickets["T1"]["status"] == "resolved"


# ── Marketing ────────────────────────────────────────────────

def test_marketing_draft():
    with tempfile.TemporaryDirectory() as td:
        _patch_state_dir(td)
        m = Marketing()
        draft = m.draft("p", angle="cho solo founder")
        assert "Campaign draft — p" in draft
        assert "cho solo founder" in draft


# ── Profile ──────────────────────────────────────────────────

def test_profile_switch():
    with tempfile.TemporaryDirectory() as td:
        from src.mk7.core import profile as pr

        old_dir = pr.PROFILES_DIR
        old_file = pr.PROFILE_FILE
        pr.PROFILES_DIR = Path(td) / "profiles"
        pr.PROFILE_FILE = Path(td) / "profile.json"
        try:
            init_profile("demo")
            set_active_profile("demo")
            assert active_profile() == "demo"
            assert "demo" in list_profiles()
            sd = state_dir()
            assert sd.name == "opc" and "demo" in str(sd)
            set_active_profile(DEFAULT_PROFILE)
            assert state_dir().name == "opc"
        finally:
            pr.PROFILES_DIR = old_dir
            pr.PROFILE_FILE = old_file


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
