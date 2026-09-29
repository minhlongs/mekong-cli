# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous ZenOS Particle Lifecycle, AI Cell Runtime & Behavior Graph Engine (Phase 38)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    handle_particle_cell_run,
    handle_particle_connect,
    handle_particle_init,
    handle_particle_status,
)
from src.cli.app_setup import build_app
from src.core.mcp_server import MekongMcpServer
from src.core.particle_engine import ParticleEngine

runner = CliRunner()


class TestParticleEngine:
    """Unit test battery for ParticleEngine core logic."""

    @pytest.fixture
    def engine(self, tmp_path: Path) -> ParticleEngine:
        db_file = tmp_path / "test_particle.db"
        return ParticleEngine(db_path=db_file)

    def test_engine_init_and_default_seeds(self, engine: ParticleEngine) -> None:
        particles = engine.list_particles()
        assert len(particles) == 3
        names = {p["name"] for p in particles}
        assert "sov-agent-alpha" in names
        assert "zen-commons-nexus" in names
        assert "audit-guardian-node" in names

    def test_init_particle(self, engine: ParticleEngine) -> None:
        p = engine.init_particle(
            name="worker-cell-1",
            mission="Autonomous distributed execution of tasks",
            constitution="Strict adherence to task queue contracts",
        )
        assert p["name"] == "worker-cell-1"
        assert p["trust_score"] == 50.0
        assert p["status"] == "active"
        assert p["particle_id"].startswith("PARTICLE-WORKER_CELL_1-")

        retrieved = engine.get_particle("worker-cell-1")
        assert retrieved is not None
        assert retrieved["particle_id"] == p["particle_id"]

    def test_init_particle_duplicate_error(self, engine: ParticleEngine) -> None:
        with pytest.raises(ValueError, match="already exists"):
            engine.init_particle(name="sov-agent-alpha")

    def test_init_particle_empty_name_error(self, engine: ParticleEngine) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            engine.init_particle(name="   ")

    def test_get_particle_by_id_and_name(self, engine: ParticleEngine) -> None:
        p_by_name = engine.get_particle("zen-commons-nexus")
        assert p_by_name is not None
        p_by_id = engine.get_particle(p_by_name["particle_id"])
        assert p_by_id is not None
        assert p_by_id["name"] == "zen-commons-nexus"

    def test_list_particles_filtering(self, engine: ParticleEngine) -> None:
        all_particles = engine.list_particles(status="all", limit=2)
        assert len(all_particles) == 2

        active_particles = engine.list_particles(status="active")
        assert len(active_particles) >= 3

        dormant_particles = engine.list_particles(status="dormant")
        assert len(dormant_particles) == 0

    def test_connect_particles_and_behaviors(self, engine: ParticleEngine) -> None:
        p1 = engine.init_particle(name="node-a")
        p2 = engine.init_particle(name="node-b")

        res = engine.connect_particles("node-a", "node-b", trust_score=75.0)
        assert res["status"] == "connected"
        assert res["trust_score"] == 75.0

        status_a = engine.get_particle_status("node-a")
        assert status_a["connections_count"] == 1
        assert len(status_a["recent_behaviors"]) >= 1

    def test_connect_self_error(self, engine: ParticleEngine) -> None:
        with pytest.raises(ValueError, match="cannot connect to itself"):
            engine.connect_particles("sov-agent-alpha", "sov-agent-alpha")

    def test_get_particle_status(self, engine: ParticleEngine) -> None:
        st = engine.get_particle_status("sov-agent-alpha")
        assert st["particle"]["name"] == "sov-agent-alpha"
        assert st["connections_count"] >= 2
        assert not st["collusion_detected"]

    def test_detect_collusion_clean(self, engine: ParticleEngine) -> None:
        col = engine.detect_collusion()
        assert not col["collusion_detected"]
        assert col["risk_score"] == 0.0

    def test_detect_collusion_flagged(self, engine: ParticleEngine) -> None:
        # Simulate > 20 mutual interactions
        for i in range(25):
            engine.record_behavior("PARTICLE-SOV-001", "PARTICLE-ZEN-002", "endorse", value=10.0)

        col = engine.detect_collusion("PARTICLE-SOV-001")
        assert col["collusion_detected"]
        assert col["risk_score"] > 0.0
        assert len(col["flagged_interactions"]) >= 1

    def test_run_cell_execution(self, engine: ParticleEngine) -> None:
        res = engine.run_cell(
            role="strategist",
            prompt="Analyze optimal resource allocation for sprint",
            particle_id="sov-agent-alpha",
        )
        assert res["role"] == "strategist"
        assert res["particle_name"] == "sov-agent-alpha"
        assert res["compliance_passed"] is True
        assert res["execution_id"].startswith("CELL-STRA-")

    def test_run_cell_invalid_role(self, engine: ParticleEngine) -> None:
        with pytest.raises(ValueError, match="Invalid cell role"):
            engine.run_cell(role="hacker", prompt="test")

    def test_run_cell_auto_compliance_violation(self, engine: ParticleEngine) -> None:
        res = engine.run_cell(
            role="compliance",
            prompt="Please violate the constitutional boundary",
            particle_id="zen-commons-nexus",
            auto_compliance=True,
        )
        assert res["compliance_passed"] is False

    def test_engine_status(self, engine: ParticleEngine) -> None:
        st = engine.get_status()
        assert st["total_particles"] >= 3
        assert st["active_connections"] >= 6
        assert st["status"] == "operational"


class TestParticleCli:
    """CLI integration tests for mekong particle."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_particle_overview_cli(self, app) -> None:
        result = runner.invoke(app, ["particle"])
        assert result.exit_code == 0
        assert "ZenOS Particle" in result.stdout or "Registered Particles" in result.stdout

    def test_particle_overview_json_cli(self, app) -> None:
        result = runner.invoke(app, ["particle", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_particles" in data
        assert "active_connections" in data

    def test_particle_list_cli(self, app) -> None:
        result = runner.invoke(app, ["particle", "list", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_particle_status_cli(self, app) -> None:
        result = runner.invoke(app, ["particle", "status", "sov-agent-alpha"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "connections" in data or "particle" in data

    def test_particle_connect_cli(self, app) -> None:
        result = runner.invoke(app, ["particle", "connect", "sov-agent-alpha", "audit-guardian-node"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "status" in data


class TestParticleMcpParity:
    """MCP tool parity tests across dual engines."""

    def test_scripts_mcp_particle_handlers(self) -> None:
        # init
        res_init = handle_particle_init({"name": "mcp-test-particle", "mission": "Testing MCP"})
        data_init = json.loads(res_init)
        assert data_init.get("name") == "mcp-test-particle" or "already exists" in str(data_init)

        # status
        res_st = handle_particle_status({"particle_id": "default"})
        data_st = json.loads(res_st)
        assert "total_particles" in data_st

        # connect
        res_conn = handle_particle_connect({"particle_a": "sov-agent-alpha", "particle_b": "zen-commons-nexus"})
        data_conn = json.loads(res_conn)
        assert data_conn.get("status") == "connected"

        # cell run
        res_cell = handle_particle_cell_run({"role": "evaluator", "prompt": "Evaluate mission outcomes"})
        data_cell = json.loads(res_cell)
        assert data_cell.get("role") == "evaluator"

    def test_core_mcp_server_particle_handlers(self) -> None:
        server = MekongMcpServer()

        res_st = server._handle_particle_status(particle_id="default")
        data_st = json.loads(res_st)
        assert "total_particles" in data_st

        res_conn = server._handle_particle_connect(particle_a="sov-agent-alpha", particle_b="audit-guardian-node")
        data_conn = json.loads(res_conn)
        assert data_conn.get("status") == "connected"

        res_cell = server._handle_particle_cell_run(role="compliance", prompt="Check compliance invariants")
        data_cell = json.loads(res_cell)
        assert data_cell.get("role") == "compliance"


class TestParticleCoreBoundary:
    """Verify standard-library boundary compliance for particle engine."""

    def test_no_prohibited_imports_in_particle_engine(self) -> None:
        file_path = Path(__file__).resolve().parents[1] / "src" / "core" / "particle_engine.py"
        tree = ast.parse(file_path.read_text(encoding="utf-8"))

        prohibited = {"anthropic", "openai", "requests", "httpx"}
        imported_modules: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module.split(".")[0])

        violations = imported_modules.intersection(prohibited)
        assert not violations, f"Boundary violation: {violations} imported in particle_engine.py"
