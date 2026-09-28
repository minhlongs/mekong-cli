# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_evals.py — Test suite for Continuous Learning & Recipe Evolution Engine.

Verifies:
1. SQLite telemetry storage, schema creation, safe write-through in src/core/evals_bridge.py
2. Statistical metrics calculation (success rate, p95 duration, token/credit tracking)
3. Failure pattern categorization, clustering, and automated recommendations
4. SelfImprover lifecycle: recipe deprecation, auto-generation, and recipe evolution
5. Evolution journal persistence and stats
6. CLI commands: mekong eval-agent and mekong evolve (table + JSON modes)
7. MCP tools over stdio JSON-RPC in fallback and standard FastMCP modes:
   - mekong_eval_query
   - mekong_recipe_evolve
   - mekong_mission_metrics
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Generator
from unittest.mock import patch

import pytest

from src.core.evals_bridge import (
    classify_failure_reason,
    clear_evals,
    cluster_failures,
    generate_recommendations,
    get_evals_db_path,
    query_evals,
    record_mission_eval,
)
from src.core.memory_canonical import MemoryEntry, MemoryStore
from src.core.recipe_gen import RecipeGenerator
from src.core.self_improve import JournalEntry, SelfImprover

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
        run_env = self.env.copy()
        run_env["PYTHONUNBUFFERED"] = "1"
        run_env["PYTHONIOENCODING"] = "utf-8"
        run_env["PYTHONPATH"] = str(PROJECT_ROOT)

        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=run_env,
            cwd=str(PROJECT_ROOT),
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)

    def write_message(self, msg: dict[str, Any] | str) -> None:
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("JSON-RPC client process not running")
        line = json.dumps(msg, separators=(",", ":")) + "\n" if isinstance(msg, dict) else (msg if msg.endswith("\n") else msg + "\n")
        self.proc.stdin.write(line)
        self.proc.stdin.flush()

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.write_message(msg)

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

        self.write_message(msg)

        deadline = time.time() + timeout
        while time.time() < deadline:
            remaining = max(0.05, deadline - time.time())
            events = self.selector.select(timeout=remaining)
            for key, _ in events:
                line = self.proc.stdout.readline()
                if not line:
                    continue
                stripped = line.strip()
                if not stripped or not stripped.startswith("{"):
                    continue
                try:
                    resp = json.loads(stripped)
                    if isinstance(resp, dict) and resp.get("id") == req_id:
                        return resp
                except json.JSONDecodeError:
                    continue

        raise TimeoutError(f"Request {method} (id={req_id}) timed out after {timeout}s")


@pytest.fixture
def temp_evals_db() -> Generator[Path, None, None]:
    """Temporary SQLite database for isolated evals testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "evals.db"
        old_env = os.environ.get("MEKONG_EVALS_DB_PATH")
        os.environ["MEKONG_EVALS_DB_PATH"] = str(db_path)
        yield db_path
        if old_env is not None:
            os.environ["MEKONG_EVALS_DB_PATH"] = old_env
        else:
            os.environ.pop("MEKONG_EVALS_DB_PATH", None)


@pytest.fixture
def mcp_fallback_client(temp_evals_db: Path) -> Generator[JsonRpcStdioClient, None, None]:
    cmd = [sys.executable, str(MCP_SERVER_SCRIPT), "--mode", "core", "--fallback"]
    env = os.environ.copy()
    env["MEKONG_FORCE_MCP_FALLBACK"] = "1"
    env["MEKONG_EVALS_DB_PATH"] = str(temp_evals_db)
    client = JsonRpcStdioClient(cmd, env=env)
    client.start()
    init_resp = client.call(
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test-runner", "version": "1.0"},
        },
    )
    assert "result" in init_resp
    client.notify("notifications/initialized")
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def mcp_standard_client(temp_evals_db: Path) -> Generator[JsonRpcStdioClient, None, None]:
    cmd = [sys.executable, str(MCP_SERVER_SCRIPT), "--mode", "core"]
    env = os.environ.copy()
    env.pop("MEKONG_FORCE_MCP_FALLBACK", None)
    env["MEKONG_EVALS_DB_PATH"] = str(temp_evals_db)
    client = JsonRpcStdioClient(cmd, env=env)
    client.start()
    init_resp = client.call(
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "test-runner-std", "version": "1.0"},
        },
    )
    assert "result" in init_resp
    client.notify("notifications/initialized")
    try:
        yield client
    finally:
        client.close()


# =============================================================================
# Unit Tests: Evals Bridge
# =============================================================================


class TestEvalsBridge:
    def test_record_and_query_single_eval(self, temp_evals_db: Path) -> None:
        ok = record_mission_eval(
            mission_id="m-001",
            agent_id="developer",
            goal="Implement auth middleware",
            duration_ms=1250,
            credits_used=1.5,
            success=True,
            tool_calls_count=4,
            tokens_used=4200,
            db_path=temp_evals_db,
        )
        assert ok is True

        res = query_evals(agent_id="all", window_days=7, db_path=temp_evals_db)
        assert res["ok"] is True
        assert res["total_missions"] == 1
        assert res["successful_missions"] == 1
        assert res["failed_missions"] == 0
        assert res["success_rate_pct"] == 100.0
        assert res["p95_duration_ms"] == 1250
        assert res["avg_duration_ms"] == 1250.0
        assert res["avg_credits"] == 1.5
        assert res["total_tokens"] == 4200
        assert len(res["recent_missions"]) == 1
        assert res["recent_missions"][0]["mission_id"] == "m-001"

    def test_record_multiple_evals_and_p95_calculation(self, temp_evals_db: Path) -> None:
        durations = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
        for i, dur in enumerate(durations):
            record_mission_eval(
                mission_id=f"m-{i:03d}",
                agent_id="developer" if i % 2 == 0 else "tester",
                goal=f"Task {i}",
                duration_ms=dur,
                credits_used=2.0,
                success=(i != 9),  # 9 successes, 1 failure
                failure_reason="Timeout waiting for network" if i == 9 else "",
                tool_calls_count=2,
                tokens_used=1000,
                db_path=temp_evals_db,
            )

        res = query_evals(agent_id="all", window_days=7, db_path=temp_evals_db)
        assert res["total_missions"] == 10
        assert res["successful_missions"] == 9
        assert res["failed_missions"] == 1
        assert res["success_rate_pct"] == 90.0
        assert res["p95_duration_ms"] == 1000
        assert res["avg_duration_ms"] == 550.0
        assert res["total_credits"] == 20.0
        assert res["total_tokens"] == 10000

        # Filter by agent
        res_dev = query_evals(agent_id="developer", window_days=7, db_path=temp_evals_db)
        assert res_dev["total_missions"] == 5
        assert res_dev["agent_id"] == "developer"

    def test_failure_classification_categories(self) -> None:
        assert classify_failure_reason("Request timed out after 30s") == "Timeout"
        assert classify_failure_reason("SyntaxError: invalid syntax on line 12") == "Syntax / Type Error"
        assert classify_failure_reason("ModuleNotFoundError: No module named 'src.core'") == "Missing Dependency / File"
        assert classify_failure_reason("Unauthorized: Governance permission denied") == "Permission / Governance"
        assert classify_failure_reason("Token limit exceeded: context budget > 40k") == "Context Budget Exceeded"
        assert classify_failure_reason("Rate limit reached 429 Too Many Requests") == "Rate Limiting"
        assert classify_failure_reason("MCP Tool failure in tool call execution") == "Tool Failure"
        assert classify_failure_reason("AssertionError: expected True but got False") == "Verification / Test Failure"
        assert classify_failure_reason("Unexpected internal error") == "General Execution Error"
        assert classify_failure_reason("") == "Unknown"

    def test_cluster_failures_and_recommendations(self, temp_evals_db: Path) -> None:
        # Record 4 timeouts, 2 syntax errors, 1 missing module
        for i in range(4):
            record_mission_eval(
                mission_id=f"fail-to-{i}",
                agent_id="ops",
                goal="Deploy container",
                success=False,
                failure_reason=f"Network deadline timed out step {i}",
                db_path=temp_evals_db,
            )
        for i in range(2):
            record_mission_eval(
                mission_id=f"fail-se-{i}",
                agent_id="dev",
                goal="Parse AST",
                success=False,
                failure_reason="SyntaxError invalid token",
                db_path=temp_evals_db,
            )
        record_mission_eval(
            mission_id="fail-mf-1",
            agent_id="dev",
            goal="Import service",
            success=False,
            failure_reason="FileNotFoundError: config.json not found",
            db_path=temp_evals_db,
        )

        res = query_evals(agent_id="all", window_days=7, db_path=temp_evals_db)
        clusters = res["failure_clusters"]
        assert len(clusters) == 3
        assert clusters[0]["category"] == "Timeout"
        assert clusters[0]["count"] == 4
        assert clusters[0]["percentage"] == round((4 / 7) * 100, 1)

        recommendations = res["recommendations"]
        assert any("timeout" in r.lower() for r in recommendations)
        assert any("syntax" in r.lower() for r in recommendations)

    def test_clear_evals(self, temp_evals_db: Path) -> None:
        record_mission_eval(mission_id="m-test", agent_id="dev", goal="test", db_path=temp_evals_db)
        assert query_evals(db_path=temp_evals_db)["total_missions"] == 1
        clear_evals(db_path=temp_evals_db)
        assert query_evals(db_path=temp_evals_db)["total_missions"] == 0


# =============================================================================
# Unit Tests: SelfImprover & Recipe Evolution
# =============================================================================


class TestSelfImprover:
    @pytest.fixture(autouse=True)
    def restore_memory(self) -> Generator[None, None, None]:
        import src.core.memory_canonical as _mc
        import src.core.self_improve as _si
        from tests.conftest import _pre_gateway_originals

        _real = _pre_gateway_originals.get("src.core.memory_canonical.MemoryStore")
        if _real is not None:
            with patch.object(_mc, "MemoryStore", _real), patch.object(_si, "MemoryStore", _real):
                yield
        else:
            yield

    def _get_real_memory_store(self, store_path: str) -> Any:
        from tests.conftest import _pre_gateway_originals

        real_cls = _pre_gateway_originals.get("src.core.memory_canonical.MemoryStore")
        if real_cls is not None:
            return real_cls(store_path=store_path)
        from src.core.memory_canonical import MemoryStore

        return MemoryStore(store_path=store_path)

    def test_deprecate_bad_recipes(self, temp_evals_db: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mem_path = Path(tmp_dir) / "memory.yaml"
            journal_path = Path(tmp_dir) / "journal.yaml"
            store = self._get_real_memory_store(store_path=str(mem_path))
            generator = RecipeGenerator()

            # Record 6 runs of 'flaky-recipe': 5 failed, 1 success (success rate 16.7% < 20%)
            for i in range(5):
                store.record(MemoryEntry(goal="Flaky goal", status="failed", recipe_used="flaky-recipe"))
            store.record(MemoryEntry(goal="Flaky goal", status="success", recipe_used="flaky-recipe"))

            # Record 5 runs of 'good-recipe': 5 success (100%)
            for i in range(5):
                store.record(MemoryEntry(goal="Good goal", status="success", recipe_used="good-recipe"))

            improver = SelfImprover(
                memory_store=store,
                recipe_generator=generator,
                journal_path=str(journal_path),
                evals_db_path=temp_evals_db,
            )

            deprecated = improver.deprecate_bad_recipes()
            assert "flaky-recipe" in deprecated
            assert "good-recipe" not in deprecated

    def test_suggest_new_recipes(self, temp_evals_db: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            mem_path = Path(tmp_dir) / "memory.yaml"
            store = self._get_real_memory_store(store_path=str(mem_path))
            improver = SelfImprover(
                memory_store=store,
                recipe_generator=RecipeGenerator(),
                evals_db_path=temp_evals_db,
            )

            store.record(MemoryEntry(goal="Generate invoice PDF", status="success", recipe_used=""))
            store.record(MemoryEntry(goal="Failed goal", status="failed", recipe_used=""))

            suggestions = improver.suggest_new_recipes()
            assert "Generate invoice PDF" in suggestions
            assert "Failed goal" not in suggestions

    def test_evolve_recipe_specific(self, temp_evals_db: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            auto_dir = Path(tmp_dir) / "recipes" / "auto"
            auto_dir.mkdir(parents=True)
            journal_path = Path(tmp_dir) / "journal.yaml"

            # Create unhardened recipe
            recipe_file = auto_dir / "checkout-service.md"
            recipe_file.write_text(
                "# Checkout Service\n\n## Steps\n### Step 1: Process Payment\nCharge card\n",
                encoding="utf-8",
            )

            # Record timeout failure in evals
            record_mission_eval(
                mission_id="m-timeout-1",
                agent_id="dev",
                goal="Checkout",
                success=False,
                failure_reason="Timeout payment gateway timeout",
                db_path=temp_evals_db,
            )

            gen = RecipeGenerator()
            gen.AUTO_DIR = str(auto_dir)

            improver = SelfImprover(
                recipe_generator=gen,
                journal_path=str(journal_path),
                evals_db_path=temp_evals_db,
            )

            entry = improver.evolve_recipe("checkout-service")
            assert entry is not None
            assert entry.action == "evolved"
            assert entry.target == "checkout-service"

            evolved_text = recipe_file.read_text(encoding="utf-8")
            assert "### Step 0: Pre-flight Check & Task Partitioning" in evolved_text
            assert "### Step Final: Post-execution Verification" in evolved_text
            assert "<!-- evolved: v2" in evolved_text

            # Idempotency check: second evolution without force returns None
            second_entry = improver.evolve_recipe("checkout-service", force=False)
            assert second_entry is None

    def test_journal_persistence_and_stats(self, temp_evals_db: Path) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            journal_path = Path(tmp_dir) / "journal.yaml"
            improver = SelfImprover(
                journal_path=str(journal_path),
                evals_db_path=temp_evals_db,
            )

            improver._record(JournalEntry(action="generated", target="recipe-a", reason="new"))
            improver._record(JournalEntry(action="deprecated", target="recipe-b", reason="broken"))
            improver._record(JournalEntry(action="evolved", target="recipe-c", reason="timeout fix"))

            stats = improver.get_evolution_stats()
            assert stats["total_generated"] == 1
            assert stats["total_deprecated"] == 1
            assert stats["total_evolved"] == 1
            assert stats["journal_size"] == 3

            # Reload fresh instance
            fresh = SelfImprover(journal_path=str(journal_path), evals_db_path=temp_evals_db)
            assert len(fresh.get_journal()) == 3


# =============================================================================
# CLI Command Tests: eval-agent & evolve
# =============================================================================


class TestCliCommands:
    def test_eval_agent_cli_no_data(self, temp_evals_db: Path) -> None:
        cmd = [sys.executable, "-m", "src.main", "eval-agent", "--json"]
        env = os.environ.copy()
        env["MEKONG_EVALS_DB_PATH"] = str(temp_evals_db)
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))
        assert res.returncode == 1
        data = json.loads(res.stdout)
        assert data.get("total_missions") == 0

    def test_eval_agent_cli_with_data(self, temp_evals_db: Path) -> None:
        record_mission_eval(
            mission_id="cli-eval-1",
            agent_id="ceo",
            goal="Weekly planning",
            duration_ms=450,
            credits_used=0.8,
            success=True,
            tool_calls_count=1,
            tokens_used=1200,
            db_path=temp_evals_db,
        )
        cmd = [sys.executable, "-m", "src.main", "eval-agent", "--json"]
        env = os.environ.copy()
        env["MEKONG_EVALS_DB_PATH"] = str(temp_evals_db)
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))
        assert res.returncode == 0
        data = json.loads(res.stdout)
        assert data["total_missions"] == 1
        assert data["successful_missions"] == 1
        assert data["success_rate_pct"] == 100.0

    def test_evolve_cli(self, temp_evals_db: Path) -> None:
        cmd = [sys.executable, "-m", "src.main", "evolve"]
        env = os.environ.copy()
        env["MEKONG_EVALS_DB_PATH"] = str(temp_evals_db)
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(PROJECT_ROOT))
        assert res.returncode == 0
        assert "Evolution Engine" in res.stdout
        assert "Evolution Statistics" in res.stdout


# =============================================================================
# MCP Server Tests: Fallback and Standard Modes
# =============================================================================


class TestMcpEvalsTools:
    def test_tools_list_exposes_continuous_learning_tools_fallback(
        self, mcp_fallback_client: JsonRpcStdioClient
    ) -> None:
        resp = mcp_fallback_client.call("tools/list")
        assert "result" in resp
        tool_names = {t["name"] for t in resp["result"]["tools"]}
        assert "mekong_eval_query" in tool_names
        assert "mekong_recipe_evolve" in tool_names
        assert "mekong_mission_metrics" in tool_names

    def test_tools_list_exposes_continuous_learning_tools_standard(
        self, mcp_standard_client: JsonRpcStdioClient
    ) -> None:
        resp = mcp_standard_client.call("tools/list")
        assert "result" in resp
        tool_names = {t["name"] for t in resp["result"]["tools"]}
        assert "mekong_eval_query" in tool_names
        assert "mekong_recipe_evolve" in tool_names
        assert "mekong_mission_metrics" in tool_names

    def test_tool_call_eval_query(
        self,
        mcp_fallback_client: JsonRpcStdioClient,
        mcp_standard_client: JsonRpcStdioClient,
        temp_evals_db: Path,
    ) -> None:
        record_mission_eval(
            mission_id="m-mcp-1",
            agent_id="dev",
            goal="Build API",
            duration_ms=500,
            credits_used=1.0,
            success=True,
            db_path=temp_evals_db,
        )

        # Fallback call
        resp_fb = mcp_fallback_client.call(
            "tools/call",
            {"name": "mekong_eval_query", "arguments": {"agent_id": "all", "days": 7}},
        )
        assert "result" in resp_fb
        data_fb = json.loads(resp_fb["result"]["content"][0]["text"])
        assert data_fb["ok"] is True
        assert data_fb["total_missions"] == 1
        assert data_fb["successful_missions"] == 1

        # Standard FastMCP call
        resp_std = mcp_standard_client.call(
            "tools/call",
            {"name": "mekong_eval_query", "arguments": {"agent_id": "all", "days": 7}},
        )
        assert "result" in resp_std
        data_std = json.loads(resp_std["result"]["content"][0]["text"])
        assert data_std["ok"] is True
        assert data_std["total_missions"] == 1

    def test_tool_call_recipe_evolve(
        self,
        mcp_fallback_client: JsonRpcStdioClient,
        mcp_standard_client: JsonRpcStdioClient,
    ) -> None:
        test_recipe_path = PROJECT_ROOT / "recipes" / "auto" / "auto-test-recipe.md"
        try:
            # Fallback call
            resp_fb = mcp_fallback_client.call(
                "tools/call",
                {"name": "mekong_recipe_evolve", "arguments": {"recipe_name": "auto-test-recipe", "goal": "Run test suite"}},
            )
            assert "result" in resp_fb
            data_fb = json.loads(resp_fb["result"]["content"][0]["text"])
            assert data_fb["ok"] is True
            assert "evolved" in data_fb

            # Standard FastMCP call
            resp_std = mcp_standard_client.call(
                "tools/call",
                {"name": "mekong_recipe_evolve", "arguments": {"recipe_name": ""}},
            )
            assert "result" in resp_std
            data_std = json.loads(resp_std["result"]["content"][0]["text"])
            assert data_std["ok"] is True
            assert "stats" in data_std
        finally:
            if test_recipe_path.exists():
                test_recipe_path.unlink()
            auto_dir = PROJECT_ROOT / "recipes" / "auto"
            for f in auto_dir.glob("*test*.md"):
                try:
                    f.unlink()
                except Exception:
                    pass
            if auto_dir.exists() and not any(auto_dir.iterdir()):
                shutil.rmtree(auto_dir.parent if not any(auto_dir.parent.iterdir()) else auto_dir, ignore_errors=True)


    def test_tool_call_mission_metrics(
        self,
        mcp_fallback_client: JsonRpcStdioClient,
        mcp_standard_client: JsonRpcStdioClient,
        temp_evals_db: Path,
    ) -> None:
        record_mission_eval(
            mission_id="m-met-1",
            agent_id="tester",
            goal="Run chaos tests",
            duration_ms=750,
            credits_used=2.5,
            success=False,
            failure_reason="Chaos injection timeout",
            db_path=temp_evals_db,
        )

        resp_fb = mcp_fallback_client.call(
            "tools/call",
            {"name": "mekong_mission_metrics", "arguments": {"agent_id": "all"}},
        )
        assert "result" in resp_fb
        data_fb = json.loads(resp_fb["result"]["content"][0]["text"])
        assert data_fb["ok"] is True
        assert data_fb["total_missions"] == 1
        assert data_fb["failed_missions"] == 1
        assert data_fb["top_cluster"] == "Timeout"

        resp_std = mcp_standard_client.call(
            "tools/call",
            {"name": "mekong_mission_metrics", "arguments": {"agent_id": "all"}},
        )
        assert "result" in resp_std
        data_std = json.loads(resp_std["result"]["content"][0]["text"])
        assert data_std["ok"] is True
        assert data_std["total_missions"] == 1

    def test_tool_call_invalid_inputs(
        self,
        mcp_fallback_client: JsonRpcStdioClient,
    ) -> None:
        # Invalid days in eval_query
        resp = mcp_fallback_client.call(
            "tools/call",
            {"name": "mekong_eval_query", "arguments": {"days": "not-an-int"}},
        )
        assert "result" in resp
        data = json.loads(resp["result"]["content"][0]["text"])
        assert data.get("ok") is False
        assert data.get("code") == "INVALID_DAYS_PARAMETER"

        # Invalid limit in eval_query
        resp_lim = mcp_fallback_client.call(
            "tools/call",
            {"name": "mekong_eval_query", "arguments": {"limit": "invalid"}},
        )
        data_lim = json.loads(resp_lim["result"]["content"][0]["text"])
        assert data_lim.get("ok") is False
        assert data_lim.get("code") == "INVALID_LIMIT_PARAMETER"
