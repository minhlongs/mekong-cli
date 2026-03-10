"""Tests for company_report.py — /company report backend."""

import json
import tempfile
from pathlib import Path

import pytest

from src.core.company_report import (
    generate_report,
)
from src.core.mcu_gate import MCUGate


def _setup_base(tmpdir: str, tasks=None, ledger=None) -> Path:
    base = Path(tmpdir)
    mekong = base / ".mekong"
    mekong.mkdir(parents=True)

    company = {"company_name": "TestCorp", "product_type": "saas"}
    (mekong / "company.json").write_text(json.dumps(company))

    if tasks is not None:
        (mekong / "memory.json").write_text(json.dumps(tasks))

    if ledger is not None:
        (mekong / "mcu_ledger.json").write_text(json.dumps(ledger))

    return base


SAMPLE_TASKS = [
    {"agent": "cto", "status": "success", "mcu": 5},
    {"agent": "cto", "status": "success", "mcu": 3},
    {"agent": "cto", "status": "failed", "mcu": 1},
    {"agent": "cmo", "status": "success", "mcu": 1},
    {"agent": "cmo", "status": "success", "mcu": 1},
    {"agent": "cs", "status": "success", "mcu": 1},
]


class TestBriefReport:
    def test_brief_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("brief", base_dir=tmpdir)
            assert report["type"] == "brief"
            assert report["company_name"] == "TestCorp"
            assert report["tasks_done"] == 6
            assert report["mcu_used"] == 12

    def test_brief_success_rate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("brief", base_dir=tmpdir)
            assert report["success_rate"] == pytest.approx(83.3, abs=0.1)

    def test_brief_most_active(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("brief", base_dir=tmpdir)
            assert report["most_active_agent"] == "cto"

    def test_brief_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=[])
            report = generate_report("brief", base_dir=tmpdir)
            assert report["tasks_done"] == 0
            assert report["success_rate"] == 0


class TestRevenueReport:
    def test_revenue_from_gate(self):
        gate = MCUGate(":memory:")
        gate.seed_balance("t1", 100, reason="init")
        gate.seed_balance("t1", 500, reason="topup")
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir)
            report = generate_report("revenue", base_dir=tmpdir, mcu_gate=gate, tenant_id="t1")
            assert report["total_mcu_sold"] == 600
            assert report["seed_count"] == 2
            assert report["mcu_revenue"] > 0

    def test_revenue_from_file(self):
        ledger = [
            {"type": "seed", "amount": 200},
            {"type": "confirm", "amount": -5},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, ledger=ledger)
            report = generate_report("revenue", base_dir=tmpdir)
            assert report["total_mcu_sold"] == 200


class TestUsageReport:
    def test_usage_by_agent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("usage", base_dir=tmpdir)
            assert report["by_agent"]["cto"]["tasks"] == 3
            assert report["by_agent"]["cto"]["mcu"] == 9
            assert report["total_mcu"] == 12

    def test_usage_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=[])
            report = generate_report("usage", base_dir=tmpdir)
            assert report["total_mcu"] == 0


class TestAgentsReport:
    def test_agents_performance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("agents", base_dir=tmpdir)
            assert report["agents"]["cto"]["tasks"] == 3
            assert report["agents"]["cto"]["success_rate"] == pytest.approx(66.7, abs=0.1)

    def test_agents_alerts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("agents", base_dir=tmpdir)
            alerts = report["alerts"]
            assert any("cto" in a for a in alerts)  # 66.7% < 90%

    def test_agents_no_alerts_when_all_good(self):
        tasks = [{"agent": "cto", "status": "success", "mcu": 3} for _ in range(10)]
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=tasks)
            report = generate_report("agents", base_dir=tmpdir)
            assert report["alerts"] == []


class TestHealthReport:
    def test_health_basic(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=SAMPLE_TASKS)
            report = generate_report("health", base_dir=tmpdir)
            assert report["total_tasks"] == 6
            assert report["errors"] == 1
            assert report["error_rate"] == pytest.approx(16.7, abs=0.1)

    def test_health_mcu_gate_stats(self):
        gate = MCUGate(":memory:")
        gate.seed_balance("t1", 100)
        lock = gate.check_and_lock("t1", "m1", 5)
        gate.confirm(lock.lock_id)
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=[])
            report = generate_report("health", base_dir=tmpdir, mcu_gate=gate, tenant_id="t1")
            assert report["mcu_gate"]["locks"] == 1
            assert report["mcu_gate"]["confirms"] == 0  # seed is "seed" type, not "confirm"


class TestReportGeneral:
    def test_invalid_type_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir)
            with pytest.raises(ValueError, match="Unknown report type"):
                generate_report("invalid", base_dir=tmpdir)

    def test_auto_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=[])
            generate_report("brief", base_dir=tmpdir)
            reports = list((Path(tmpdir) / ".mekong" / "reports").glob("*.json"))
            assert len(reports) == 1

    def test_generated_at_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            _setup_base(tmpdir, tasks=[])
            report = generate_report("brief", base_dir=tmpdir)
            assert "generated_at" in report

    def test_no_company_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(tmpdir, ".mekong").mkdir()
            report = generate_report("brief", base_dir=tmpdir)
            assert report["company_name"] == "Unknown"
