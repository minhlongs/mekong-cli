"""Tests for SubsystemHealth metrics — Sprint 2.2."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.telemetry_models import SubsystemHealth, SubsystemHealthReport


class TestSubsystemHealth:
    def test_default_values(self) -> None:
        h = SubsystemHealth(subsystem="memory")
        assert h.activation_count == 0
        assert h.success_contribution == 0.0
        assert h.avg_latency_ms == 0.0
        assert h.error_count == 0

    def test_record_activation(self) -> None:
        h = SubsystemHealth(subsystem="planning")
        h.record_activation(latency_ms=50.0, success=True)
        assert h.activation_count == 1
        assert h.avg_latency_ms == 50.0
        assert h.error_count == 0
        assert h.last_activated is not None

    def test_record_multiple_activations(self) -> None:
        h = SubsystemHealth(subsystem="execution")
        h.record_activation(latency_ms=100.0, success=True)
        h.record_activation(latency_ms=200.0, success=True)
        assert h.activation_count == 2
        assert h.avg_latency_ms == pytest.approx(150.0)

    def test_record_failure(self) -> None:
        h = SubsystemHealth(subsystem="self_healing")
        h.record_activation(latency_ms=30.0, success=False)
        assert h.error_count == 1
        assert h.activation_count == 1

    def test_success_rate(self) -> None:
        h = SubsystemHealth(subsystem="memory")
        h.record_activation(10.0, True)
        h.record_activation(10.0, True)
        h.record_activation(10.0, False)
        assert h.success_rate == pytest.approx(2 / 3)

    def test_success_rate_zero(self) -> None:
        h = SubsystemHealth(subsystem="empty")
        assert h.success_rate == 0.0

    def test_to_dict(self) -> None:
        h = SubsystemHealth(subsystem="telemetry")
        h.record_activation(25.0, True)
        data = h.to_dict()
        assert data["subsystem"] == "telemetry"
        assert data["activation_count"] == 1
        assert "success_rate" in data
        assert data["last_activated"] is not None


class TestSubsystemHealthReport:
    def test_empty_report(self) -> None:
        r = SubsystemHealthReport()
        assert r.total_activations == 0
        assert r.active_count == 0
        assert r.coverage == 0.0

    def test_add_subsystem(self) -> None:
        r = SubsystemHealthReport()
        h = SubsystemHealth(subsystem="memory", activation_count=5)
        r.add_subsystem(h)
        assert len(r.subsystems) == 1
        assert r.get_subsystem("memory") is not None

    def test_update_existing(self) -> None:
        r = SubsystemHealthReport()
        r.add_subsystem(SubsystemHealth(subsystem="memory", activation_count=1))
        r.add_subsystem(SubsystemHealth(subsystem="memory", activation_count=10))
        assert len(r.subsystems) == 1
        assert r.get_subsystem("memory").activation_count == 10

    def test_coverage(self) -> None:
        r = SubsystemHealthReport()
        r.add_subsystem(SubsystemHealth(subsystem="a", activation_count=1))
        r.add_subsystem(SubsystemHealth(subsystem="b", activation_count=0))
        assert r.coverage == pytest.approx(0.5)

    def test_get_nonexistent(self) -> None:
        r = SubsystemHealthReport()
        assert r.get_subsystem("nope") is None

    def test_to_dict(self) -> None:
        r = SubsystemHealthReport()
        r.add_subsystem(SubsystemHealth(subsystem="planning", activation_count=3))
        data = r.to_dict()
        assert "timestamp" in data
        assert data["active_count"] == 1
        assert len(data["subsystems"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
