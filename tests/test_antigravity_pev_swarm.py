# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Comprehensive test suite for Autonomous PEV & Swarm Orchestration integration (R4).

Validates:
1. PEVSwarmBridge core lifecycle (Plan -> Execute -> Verify) with SQLite persistence
2. Subagent payload generation, context budgets (16k-30k), and HARNESS.md ceilings (<=40k)
3. Checkpoint capture, retrieval, atomic file restoration, and boundary confinement
4. Error resilience: corrupted checkpoints, invalid parameters, and missing goals
5. CLI commands in live, dry-run, and structured JSON modes:
   - mekong cook-auto <goal> [--max-cycles] [--dry-run] [--checkpoint-id]
   - mekong swarm run <goal> [--agents] [--dry-run]
   - mekong goal checkpoint <goal-id> and mekong goal rollback <goal-id> <checkpoint-id>
6. MCP PEV tools over stdio JSON-RPC in standard and fallback modes:
   - mekong_pev_plan, mekong_pev_checkpoint, mekong_pev_rollback, mekong_swarm_status
7. Standard library boundary compliance and non-regression of health checks
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Generator

import pytest

from src.core.pev_swarm_bridge import (
    CheckpointRecord,
    CheckpointStore,
    MissionStatus,
    PEVSwarmBridge,
    PevPhase,
    PevPlan,
    PevTask,
    ROLE_CONTEXT_BUDGETS,
    ROLE_TOOL_ALLOWLISTS,
    TaskStatus,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MCP_SERVER_SCRIPT = SCRIPTS_DIR / "mcp_server.py"

PROTOCOL_VERSION = "2024-11-05"
TIMEOUT_SECONDS = 6.0


# =============================================================================
# Helper: Stdio JSON-RPC Client for MCP Testing
# =============================================================================


class JsonRpcStdioClient:
    """Non-blocking stdio JSON-RPC process manager with timeout protection."""

    def __init__(self, cmd: list[str], env: dict[str, str] | None = None) -> None:
        self.cmd = cmd
        self.env = env or os.environ.copy()
        self.proc: subprocess.Popen[str] | None = None
        self.selector: selectors.DefaultSelector | None = None
        self._seq = 0

    def start(self) -> None:
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=self.env,
            cwd=str(PROJECT_ROOT),
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)

    def close(self) -> None:
        if self.selector:
            try:
                self.selector.close()
            except Exception:
                pass
            self.selector = None

        if self.proc:
            try:
                if self.proc.stdin and not self.proc.stdin.closed:
                    self.proc.stdin.close()
                self.proc.terminate()
                self.proc.wait(timeout=2.0)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            self.proc = None

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float = TIMEOUT_SECONDS) -> dict[str, Any]:
        if not self.proc or not self.proc.stdin or not self.selector:
            raise RuntimeError("JSON-RPC client process not running")

        self._seq += 1
        req_id = self._seq
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": req_id, "method": method}
        if params is not None:
            msg["params"] = params

        payload = json.dumps(msg) + "\n"
        self.proc.stdin.write(payload)
        self.proc.stdin.flush()

        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.05, deadline - time.time())
            events = self.selector.select(timeout=remaining)
            for key, _ in events:
                line = key.fileobj.readline()
                if not line:
                    continue
                clean = line.strip()
                if not clean:
                    continue
                try:
                    resp = json.loads(clean)
                    if isinstance(resp, dict) and resp.get("id") == req_id:
                        return resp
                except json.JSONDecodeError:
                    continue

        raise TimeoutError(f"Method '{method}' timed out waiting for id {req_id} after {timeout}s")


@pytest.fixture
def mcp_fallback_client() -> Generator[JsonRpcStdioClient, None, None]:
    env = os.environ.copy()
    env["MEKONG_FORCE_MCP_FALLBACK"] = "1"
    client = JsonRpcStdioClient([sys.executable, str(MCP_SERVER_SCRIPT), "--fallback"], env=env)
    client.start()
    init_resp = client.call("initialize", {"capabilities": {}, "protocolVersion": PROTOCOL_VERSION})
    assert "result" in init_resp
    yield client
    client.close()


# =============================================================================
# Milestone 1 Tests: PEVSwarmBridge & CheckpointStore Core Invariants
# =============================================================================


class TestPEVSwarmBridgeCore:
    """Validate core bridge logic, plan decomposition, budgets, and atomic SQLite checkpoints."""

    def test_plan_goal_decomposition(self, tmp_path: Path) -> None:
        db_file = tmp_path / "test_pev.db"
        bridge = PEVSwarmBridge(db_path=db_file)

        plan = bridge.plan("Implement user authentication with JWT tokens")
        assert isinstance(plan, PevPlan)
        assert plan.goal == "Implement user authentication with JWT tokens"
        assert len(plan.tasks) == 3

        # Check canonical 3 phases
        t1, t2, t3 = plan.tasks
        assert t1.phase == PevPhase.PLAN
        assert t1.role == "pm"
        assert t1.context_budget == ROLE_CONTEXT_BUDGETS["pm"]
        assert t1.context_budget <= 40000

        assert t2.phase == PevPhase.EXECUTE
        assert t2.role == "eng"
        assert t2.context_budget == ROLE_CONTEXT_BUDGETS["eng"]
        assert t2.context_budget <= 40000

        assert t3.phase == PevPhase.VERIFY
        assert t3.role == "tester"
        assert t3.context_budget == ROLE_CONTEXT_BUDGETS["tester"]
        assert t3.context_budget <= 40000

        # Check subagent assignments payload
        assignments = plan.subagent_assignments
        assert "pm" in assignments
        assert "eng" in assignments
        assert "tester" in assignments

        for role, data in assignments.items():
            assert data["ok"] is True
            assert "define_subagent" in data
            assert "invoke_subagent" in data
            assert "context_engineering" in data
            assert data["context_engineering"]["token_ceiling"] <= 40000
            assert set(data["context_engineering"]["tool_allowlist"]).issubset(
                {"Read", "Write", "Edit", "Bash", "Task"}
            )

    def test_checkpoint_capture_and_retrieval(self, tmp_path: Path) -> None:
        db_file = tmp_path / "test_cp.db"
        bridge = PEVSwarmBridge(db_path=db_file)

        dummy_file = tmp_path / "app.py"
        dummy_file.write_text("print('hello world')", encoding="utf-8")

        cp_id = bridge.store.capture_checkpoint(
            mission_id="m_test_001",
            label="initial_state",
            files=[dummy_file],
            test_results={"tests_passed": 5, "tests_failed": 0},
            project_root=tmp_path,
        )

        assert cp_id.startswith("cp_")
        record = bridge.store.get_checkpoint(cp_id)
        assert isinstance(record, CheckpointRecord)
        assert record.checkpoint_id == cp_id
        assert record.mission_id == "m_test_001"
        assert record.label == "initial_state"
        assert len(record.file_snapshots) == 1
        assert record.file_snapshots[0].relative_path == "app.py"
        assert record.test_results.get("tests_passed") == 5

    def test_checkpoint_rollback_atomic_restoration(self, tmp_path: Path) -> None:
        db_file = tmp_path / "test_rollback.db"
        bridge = PEVSwarmBridge(db_path=db_file)

        # 1. Create original file
        code_file = tmp_path / "logic.py"
        code_file.write_text("def solve(): return 42\n", encoding="utf-8")

        # 2. Capture checkpoint 1
        cp_id_1 = bridge.store.capture_checkpoint(
            mission_id="m_test_rollback",
            label="working_version",
            files=[code_file],
            project_root=tmp_path,
        )

        # 3. Mutate file and add extraneous file in checkpoint 2
        code_file.write_text("def solve(): return 'corrupted'\n", encoding="utf-8")
        extra_file = tmp_path / "extraneous.tmp"
        extra_file.write_text("temporary data", encoding="utf-8")

        # Capture checkpoint 2 containing the extraneous file
        bridge.store.capture_checkpoint(
            mission_id="m_test_rollback",
            label="broken_state",
            files=[code_file, extra_file],
            project_root=tmp_path,
        )

        # 4. Rollback to checkpoint 1
        res = bridge.store.rollback_to_checkpoint(cp_id_1, project_root=tmp_path)
        assert res["ok"] is True
        assert "logic.py" in res["restored_files"]
        assert "extraneous.tmp" in res["removed_files"]

        # 5. Verify file contents restored and extra file removed
        assert code_file.read_text(encoding="utf-8") == "def solve(): return 42\n"
        assert not extra_file.exists()

    def test_checkpoint_path_traversal_confinement(self, tmp_path: Path) -> None:
        db_file = tmp_path / "test_confinement.db"
        bridge = PEVSwarmBridge(db_path=db_file)

        # 1. Create a checkpoint with a traversal path injection
        cp_id = "cp_traversal_attack"
        now = "2026-09-28T00:00:00Z"
        with bridge.store._connect() as conn:
            conn.execute(
                """
                INSERT INTO missions (mission_id, goal, status, cycle, max_cycles, plan_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("m_attack", "Attack", "created", 1, 3, "{}", now, now),
            )
            conn.execute(
                """
                INSERT INTO checkpoints (checkpoint_id, mission_id, task_id, cycle, phase, label, task_states, test_results, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cp_id, "m_attack", None, 1, "plan", "attack", "{}", "{}", now),
            )
            # Inject snapshot with ../ relative path attempting to overwrite outside project root
            conn.execute(
                """
                INSERT INTO file_snapshots (checkpoint_id, relative_path, sha256, content_type, content, size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (cp_id, "../../etc_passwd_sim.txt", "abc", "utf-8", "attack_payload", 14, now),
            )

        # 2. Attempt rollback
        res = bridge.store.rollback_to_checkpoint(cp_id, project_root=tmp_path)
        assert res["ok"] is True
        # Traversal file must be rejected and not restored
        assert "../../etc_passwd_sim.txt" not in res["restored_files"]
        assert not (tmp_path.parent / "etc_passwd_sim.txt").exists()

    def test_corrupted_data_and_invalid_checkpoint_error_handling(self, tmp_path: Path) -> None:
        db_file = tmp_path / "test_corrupt.db"
        bridge = PEVSwarmBridge(db_path=db_file)

        # Non-existent checkpoint
        res = bridge.store.rollback_to_checkpoint("cp_does_not_exist", project_root=tmp_path)
        assert res["ok"] is False
        assert "not found" in res["error"].lower()

        # Corrupted checkpoint payload in database
        with bridge.store._connect() as conn:
            conn.execute(
                """
                INSERT INTO missions (mission_id, goal, status, cycle, max_cycles, plan_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("m_corrupt", "Corrupt", "created", 1, 3, "{}", "2026-09-28T00:00:00Z", "2026-09-28T00:00:00Z"),
            )
            conn.execute(
                """
                INSERT INTO checkpoints (
                    checkpoint_id, mission_id, task_id, cycle, phase, label,
                    task_states, test_results, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "cp_corrupted_json",
                    "m_corrupt",
                    None,
                    1,
                    "plan",
                    "bad_json",
                    "{INVALID_JSON",
                    "{}",
                    "2026-09-28T00:00:00Z",
                ),
            )

        res_corrupt = bridge.store.rollback_to_checkpoint("cp_corrupted_json", project_root=tmp_path)
        assert res_corrupt["ok"] is False
        assert "corrupted" in res_corrupt["error"].lower()


# =============================================================================
# Milestone 2 Tests: CLI Commands & Rich Formatting
# =============================================================================


class TestPEVCliCommands:
    """Validate cook-auto, swarm run, goal checkpoint, and goal rollback CLI commands."""

    def test_cook_auto_dry_run_console(self) -> None:
        res = subprocess.run(
            [sys.executable, "-m", "src.main", "cook-auto", "Implement notification system", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0
        assert "Cook Auto Preview (Dry Run)" in res.stdout
        assert "PEV Swarm Delegation Hierarchy" in res.stdout
        assert "Subagent Context Budgets & Guardrails" in res.stdout
        assert "Verification Gates & Acceptance Rubrics" in res.stdout

    def test_cook_auto_dry_run_json(self) -> None:
        res = subprocess.run(
            [sys.executable, "-m", "src.main", "cook-auto", "Implement notification system", "--dry-run", "--json"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0
        data = json.loads(res.stdout)
        assert data.get("ok") is True
        assert data.get("status") == "dry_run"
        assert "plan" in data
        assert len(data["plan"]["tasks"]) == 3

    def test_cook_auto_invalid_checkpoint_error(self) -> None:
        res = subprocess.run(
            [sys.executable, "-m", "src.main", "cook-auto", "Test", "--checkpoint-id", "cp_missing_xyz", "--dry-run", "--json"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 1
        data = json.loads(res.stdout)
        assert data.get("ok") is False
        assert data.get("code") == "CHECKPOINT_NOT_FOUND"

    def test_swarm_run_dry_run(self) -> None:
        res = subprocess.run(
            [sys.executable, "-m", "src.main", "swarm", "run", "Audit architecture and security", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0
        assert "Swarm Run Preview (Dry Run)" in res.stdout
        assert "Multi-Agent Swarm Delegation Tree" in res.stdout

    def test_swarm_run_custom_agents_and_json(self) -> None:
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.main",
                "swarm",
                "run",
                "Build payment gateway",
                "--agents",
                "cto,eng,tester",
                "--dry-run",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0
        data = json.loads(res.stdout)
        assert data.get("ok") is True
        assert data.get("dry_run") is True
        assert data.get("agents") == ["cto", "eng", "tester"]
        assert len(data.get("tasks", [])) == 3

    def test_swarm_run_unknown_role_validation(self) -> None:
        res = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.main",
                "swarm",
                "run",
                "Build feature",
                "--agents",
                "cto,unknown_ninja_role",
                "--dry-run",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 1
        data = json.loads(res.stdout)
        assert data.get("ok") is False
        assert data.get("code") == "UNKNOWN_AGENT_ROLE"

    def test_goal_checkpoint_and_rollback_cli_lifecycle(self, tmp_path: Path) -> None:
        # Create goal
        create_res = subprocess.run(
            [sys.executable, "-m", "src.main", "goal", "create", "E2E Checkpoint Mission", "--json"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert create_res.returncode == 0
        goal_data = json.loads(create_res.stdout)
        goal_id = goal_data["id"]

        # Capture checkpoint
        cp_res = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.main",
                "goal",
                "checkpoint",
                goal_id,
                "--label",
                "cli_test_checkpoint",
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert cp_res.returncode == 0
        cp_data = json.loads(cp_res.stdout)
        assert cp_data.get("ok") is True
        assert cp_data.get("status") == "captured"
        cp_id = cp_data["checkpoint_id"]

        # Rollback checkpoint
        rb_res = subprocess.run(
            [sys.executable, "-m", "src.main", "goal", "rollback", goal_id, cp_id, "--json"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert rb_res.returncode == 0
        rb_data = json.loads(rb_res.stdout)
        assert rb_data.get("ok") is True
        assert rb_data.get("status") == "rolled_back"
        assert rb_data.get("checkpoint_id") == cp_id


# =============================================================================
# Milestone 3 Tests: MCP Native PEV Swarm Tools over Stdio JSON-RPC
# =============================================================================


class TestPEVMcpTools:
    """Validate native MCP PEV tools over stdio transport."""

    def test_tools_list_exposes_4_pev_tools(self, mcp_fallback_client: JsonRpcStdioClient) -> None:
        resp = mcp_fallback_client.call("tools/list")
        assert "result" in resp
        tool_names = {t["name"] for t in resp["result"]["tools"]}

        assert "mekong_pev_plan" in tool_names
        assert "mekong_pev_checkpoint" in tool_names
        assert "mekong_pev_rollback" in tool_names
        assert "mekong_swarm_status" in tool_names

    def test_tool_call_mekong_pev_plan(self, mcp_fallback_client: JsonRpcStdioClient) -> None:
        resp = mcp_fallback_client.call(
            "tools/call",
            {"name": "mekong_pev_plan", "arguments": {"goal": "Build robust checkout system"}},
        )
        assert "result" in resp
        content = json.loads(resp["result"]["content"][0]["text"])
        assert content.get("ok") is True
        assert "plan" in content
        assert len(content["plan"]["tasks"]) == 3

    def test_tool_call_mekong_pev_checkpoint_and_rollback(self, mcp_fallback_client: JsonRpcStdioClient) -> None:
        # Checkpoint
        resp_cp = mcp_fallback_client.call(
            "tools/call",
            {
                "name": "mekong_pev_checkpoint",
                "arguments": {
                    "mission_id": "m_mcp_e2e",
                    "label": "mcp_snapshot",
                    "files": ["scripts/mcp_server.py"],
                },
            },
        )
        assert "result" in resp_cp
        cp_content = json.loads(resp_cp["result"]["content"][0]["text"])
        assert cp_content.get("ok") is True
        cp_id = cp_content["checkpoint_id"]

        # Rollback
        resp_rb = mcp_fallback_client.call(
            "tools/call",
            {"name": "mekong_pev_rollback", "arguments": {"checkpoint_id": cp_id}},
        )
        assert "result" in resp_rb
        rb_content = json.loads(resp_rb["result"]["content"][0]["text"])
        assert rb_content.get("ok") is True
        assert "scripts/mcp_server.py" in rb_content.get("restored_files", [])

    def test_tool_call_mekong_swarm_status(self, mcp_fallback_client: JsonRpcStdioClient) -> None:
        resp = mcp_fallback_client.call("tools/call", {"name": "mekong_swarm_status", "arguments": {}})
        assert "result" in resp
        status_content = json.loads(resp["result"]["content"][0]["text"])
        assert status_content.get("ok") is True


# =============================================================================
# Milestone 4 Tests: Integrity & Non-Regression
# =============================================================================


class TestPEVIntegrityAndBoundary:
    """Validate boundary neutrality and full healthcheck."""

    def test_core_boundary_invariants(self) -> None:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_core_boundary.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0, f"Core boundary violation: {res.stdout}\n{res.stderr}"

    def test_antigravity_healthcheck_clean(self) -> None:
        res = subprocess.run(
            [sys.executable, "scripts/antigravity_healthcheck.py"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert res.returncode == 0, f"Healthcheck failure: {res.stdout}\n{res.stderr}"
        assert "Status: HEALTHY (exit 0)" in res.stdout
