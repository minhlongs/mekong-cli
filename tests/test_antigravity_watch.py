# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Self-Repair & File-Watcher Daemon (Phase 13).

Covers:
1. FileSystemWatcher: change detection, SHA-256 hash calculation, ignore filters, debouncing.
2. DiagnosticsEngine: AST syntax verification, error details (line, column), clustering, test execution.
3. SelfRepairManager: heuristic syntax auto-fixing, CheckpointStore rollback, repair tracking.
4. AutonomousWatchDaemon: lifecycle management, event batch processing, gateway event broadcasting.
5. CLI Command Surface: mekong watch options (--status, --repair, --stop, --json).
6. Native MCP Tools: mekong_watch_status and mekong_self_repair dual-engine parity.
7. AST Core Boundary Compliance: standard library only, zero vendor SDKs.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from src.core.watcher_bridge import (
    AutonomousWatchDaemon,
    ChangeType,
    DiagnosticResult,
    DiagnosticsEngine,
    FileChangeEvent,
    FileSystemWatcher,
    RepairAction,
    SelfRepairManager,
    WatcherConfig,
    WatcherState,
    compute_file_hash,
    get_watch_daemon,
    matches_patterns,
)


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for watching and repairing."""
    tmp_dir = Path(tempfile.mkdtemp(prefix="mekong_watch_test_"))
    yield tmp_dir
    shutil.rmtree(str(tmp_dir), ignore_errors=True)


class TestFileSystemWatcher:
    """Tests for FileSystemWatcher polling, hashing, ignoring, and debouncing."""

    def test_compute_file_hash_and_matching(self, temp_workspace: Path):
        f = temp_workspace / "sample.py"
        f.write_text("print('hello world')", encoding="utf-8")
        h1 = compute_file_hash(f)
        assert len(h1) == 64
        assert compute_file_hash(temp_workspace / "nonexistent.py") == ""

        # Test ignore pattern matching
        assert matches_patterns("foo/__pycache__/bar.pyc", ["*/__pycache__/*", "*.pyc"])
        assert matches_patterns(".git/HEAD", [".git/*"])
        assert not matches_patterns("src/core/main.py", [".git/*", "*.pyc"])

    def test_scan_once_lifecycle(self, temp_workspace: Path):
        config = WatcherConfig(
            watch_paths=[str(temp_workspace)],
            poll_interval=0.1,
            debounce_ms=50,
        )
        watcher = FileSystemWatcher(config)

        # Baseline scan seeds known files, should return no events
        initial_events = watcher.scan_once()
        assert initial_events == []

        # Create a new file
        test_file = temp_workspace / "module_a.py"
        test_file.write_text("def a(): return 1\n", encoding="utf-8")

        created_events = watcher.scan_once()
        assert len(created_events) == 1
        assert created_events[0].change_type == ChangeType.CREATED.value
        assert Path(created_events[0].file_path).name == "module_a.py"
        assert len(created_events[0].hash) == 64

        # Modify the file
        time.sleep(0.05)
        test_file.write_text("def a(): return 2\n", encoding="utf-8")
        mod_events = watcher.scan_once()
        assert len(mod_events) == 1
        assert mod_events[0].change_type == ChangeType.MODIFIED.value

        # Delete the file
        test_file.unlink()
        del_events = watcher.scan_once()
        assert len(del_events) == 1
        assert del_events[0].change_type == ChangeType.DELETED.value

    def test_ignore_patterns_filtered(self, temp_workspace: Path):
        config = WatcherConfig(
            watch_paths=[str(temp_workspace)],
            poll_interval=0.1,
            debounce_ms=50,
        )
        watcher = FileSystemWatcher(config)
        watcher.scan_once()

        # Create an ignored directory and file
        pycache = temp_workspace / "__pycache__"
        pycache.mkdir()
        ignored_file = pycache / "cached.pyc"
        ignored_file.write_text("byte code", encoding="utf-8")

        events = watcher.scan_once()
        assert len(events) == 0

    def test_background_thread_and_debounce(self, temp_workspace: Path):
        config = WatcherConfig(
            watch_paths=[str(temp_workspace)],
            poll_interval=0.05,
            debounce_ms=100,
        )
        watcher = FileSystemWatcher(config)
        emitted_batches: list[list[FileChangeEvent]] = []

        watcher.add_change_listener(lambda batch: emitted_batches.append(batch))
        watcher.scan_once()
        watcher.start(daemon=True)
        time.sleep(0.05)

        # Perform multiple rapid file writes
        f1 = temp_workspace / "batch1.py"
        f2 = temp_workspace / "batch2.py"
        f1.write_text("x = 1\n", encoding="utf-8")
        f2.write_text("y = 2\n", encoding="utf-8")

        # Wait for debounce duration to settle
        time.sleep(0.35)
        watcher.stop()
        assert not watcher.is_running()

        assert len(emitted_batches) >= 1
        all_emitted_paths = [Path(e.file_path).name for b in emitted_batches for e in b]
        assert "batch1.py" in all_emitted_paths
        assert "batch2.py" in all_emitted_paths


class TestDiagnosticsEngine:
    """Tests for AST syntax analysis and error clustering."""

    def test_validate_valid_and_invalid_source(self):
        engine = DiagnosticsEngine()

        # Valid source
        res_valid = engine.validate_source("def hello():\n    return 'world'\n", filename="hello.py")
        assert res_valid.is_valid
        assert res_valid.error_type is None
        assert res_valid.severity == "info"

        # Invalid source (missing closing paren and colon)
        res_invalid = engine.validate_source("def broken(\n", filename="broken.py")
        assert not res_valid == res_invalid
        assert not res_invalid.is_valid
        assert res_invalid.error_type == "SyntaxError"
        assert res_invalid.line_number is not None
        assert res_invalid.severity == "error"
        assert res_invalid.matched_cluster_id is not None
        assert res_invalid.matched_cluster_id.startswith("cluster_")

    def test_validate_file_on_disk(self, temp_workspace: Path):
        engine = DiagnosticsEngine(project_root=temp_workspace)

        py_file = temp_workspace / "valid.py"
        py_file.write_text("val = 42\n", encoding="utf-8")
        res = engine.validate_file(py_file)
        assert res.is_valid

        # Nonexistent file
        res_none = engine.validate_file(temp_workspace / "missing.py")
        assert not res_none.is_valid
        assert res_none.error_type == "FileNotFoundError"

        # Non-python file
        txt_file = temp_workspace / "notes.txt"
        txt_file.write_text("just some text", encoding="utf-8")
        res_txt = engine.validate_file(txt_file)
        assert res_txt.is_valid

    def test_run_tests_for_file(self, temp_workspace: Path):
        engine = DiagnosticsEngine(project_root=temp_workspace)
        test_file = temp_workspace / "test_mini.py"
        test_file.write_text("def test_ok(): assert True\n", encoding="utf-8")

        res = engine.run_tests_for_file(test_file, timeout=5.0)
        assert "ok" in res
        assert "returncode" in res


class TestSelfRepairManager:
    """Tests for heuristic AST auto-fix and CheckpointStore rollback."""

    def test_auto_fix_missing_colon(self, temp_workspace: Path):
        engine = DiagnosticsEngine(project_root=temp_workspace)
        repair_mgr = SelfRepairManager(project_root=temp_workspace)

        corrupt_file = temp_workspace / "missing_colon.py"
        corrupt_file.write_text("def greet()\n    return 'hi'\n", encoding="utf-8")

        diag = engine.validate_file(corrupt_file)
        assert not diag.is_valid

        action = repair_mgr.auto_fix_syntax(corrupt_file, diag)
        assert action.status == "success"
        assert action.strategy == "syntax_auto_fix"

        # File should now be valid AST
        diag_after = engine.validate_file(corrupt_file)
        assert diag_after.is_valid
        assert "def greet():\n" in corrupt_file.read_text(encoding="utf-8")

    def test_auto_fix_unclosed_paren(self, temp_workspace: Path):
        engine = DiagnosticsEngine(project_root=temp_workspace)
        repair_mgr = SelfRepairManager(project_root=temp_workspace)

        corrupt_file = temp_workspace / "unclosed.py"
        corrupt_file.write_text("msg = str(123\n", encoding="utf-8")

        diag = engine.validate_file(corrupt_file)
        assert not diag.is_valid

        action = repair_mgr.auto_fix_syntax(corrupt_file, diag)
        assert action.status == "success"
        assert action.strategy == "syntax_auto_fix"

        diag_after = engine.validate_file(corrupt_file)
        assert diag_after.is_valid

    def test_checkpoint_rollback_on_unfixable_code(self, temp_workspace: Path):
        from src.core.pev_swarm_bridge import CheckpointStore

        db_path = temp_workspace / ".mekong" / "pev_checkpoints.db"
        real_store = CheckpointStore(db_path=db_path)

        with real_store._connect() as conn:
            conn.execute(
                """
                INSERT INTO missions (mission_id, goal, status, cycle, max_cycles, plan_json, created_at, updated_at)
                VALUES ('m1', 'test goal', 'in_progress', 1, 3, '{}', 'now', 'now')
                """
            )
            conn.execute(
                """
                INSERT INTO checkpoints (checkpoint_id, mission_id, task_id, cycle, phase, label, task_states, created_at)
                VALUES ('cp_test_001', 'm1', 't1', 1, 'verify', 'snapshot', '{}', 'now')
                """
            )
            conn.execute(
                """
                INSERT INTO file_snapshots (checkpoint_id, relative_path, sha256, content_type, content, size_bytes, created_at)
                VALUES ('cp_test_001', 'garbled.py', 'abcdef1234567890', 'text/plain', 'def clean_code():\n    return ''pristine''\n', 40, 'now')
                """
            )

        engine = DiagnosticsEngine(project_root=temp_workspace)
        repair_mgr = SelfRepairManager(project_root=temp_workspace, checkpoint_store=real_store)

        corrupt_file = temp_workspace / "garbled.py"
        corrupt_file.write_text("&&& INVALID PYTHON ### ^^^", encoding="utf-8")

        diag = engine.validate_file(corrupt_file)
        assert not diag.is_valid

        # diagnose_and_repair tries heuristic first, fails, then rolls back from checkpoint
        action = repair_mgr.diagnose_and_repair(corrupt_file, diag)
        assert action.status == "success"
        assert action.strategy == "checkpoint_rollback"
        assert "Restored from checkpoint cp_test_001" in action.details

        # Verify file content was restored
        assert "clean_code" in corrupt_file.read_text(encoding="utf-8")
        assert engine.validate_file(corrupt_file).is_valid


class TestAutonomousWatchDaemon:
    """Tests for daemon lifecycle and event handling."""

    def test_daemon_lifecycle_and_status(self, temp_workspace: Path):
        config = WatcherConfig(
            watch_paths=[str(temp_workspace)],
            poll_interval=0.1,
            debounce_ms=50,
            auto_repair=True,
            stream_gateway=True,
        )
        daemon = AutonomousWatchDaemon(config=config, project_root=temp_workspace)

        assert not daemon.is_running()
        daemon.start(daemon=True)
        assert daemon.is_running()

        status = daemon.get_status()
        assert status["is_active"]
        assert status["uptime_seconds"] >= 0.0

        daemon.stop()
        assert not daemon.is_running()

    def test_process_file_batch_with_auto_repair(self, temp_workspace: Path):
        config = WatcherConfig(
            watch_paths=[str(temp_workspace)],
            auto_repair=True,
        )
        daemon = AutonomousWatchDaemon(config=config, project_root=temp_workspace)

        broken_file = temp_workspace / "broken_batch.py"
        broken_file.write_text("if True\n    pass\n", encoding="utf-8")

        event = FileChangeEvent(
            file_path=str(broken_file),
            change_type=ChangeType.CREATED.value,
            timestamp=time.time(),
            hash=compute_file_hash(broken_file),
            size_bytes=broken_file.stat().st_size,
        )

        results = daemon.process_file_batch([event])
        assert len(results) == 1
        item = results[0]
        assert "diagnostic" in item
        assert item["repair"] is not None
        assert item["repair"]["status"] == "success"

        # Telemetry should be updated
        st = daemon.get_status()
        assert st["events_detected"] >= 1
        assert st["errors_diagnosed"] >= 1
        assert st["repairs_attempted"] >= 1
        assert st["repairs_succeeded"] >= 1

    def test_trigger_self_repair_manual(self, temp_workspace: Path):
        daemon = AutonomousWatchDaemon(project_root=temp_workspace)
        test_file = temp_workspace / "manual_fix.py"
        test_file.write_text("class MyService\n    pass\n", encoding="utf-8")

        res = daemon.trigger_self_repair(str(test_file), mode="auto")
        assert res["repair"]["status"] == "success"
        assert res["repair"]["strategy"] == "syntax_auto_fix"


class TestWatchCLICommand:
    """Tests for Typer CLI mekong watch integration."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_watch_help(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["watch", "--help"])
        assert result.exit_code == 0
        assert "Autonomous Watcher" in result.output
        assert "--auto-repair" in result.output
        assert "--status" in result.output

    def test_watch_status_json(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["watch", "--status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "running" in data
        assert "state" in data

    def test_watch_stop_when_not_running(self, runner: CliRunner):
        from src.cli.app_setup import build_app
        app = build_app()
        result = runner.invoke(app, ["watch", "--stop", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is False

    def test_watch_repair_flag_json(self, runner: CliRunner, temp_workspace: Path):
        from src.cli.app_setup import build_app
        test_file = temp_workspace / "cli_repair.py"
        test_file.write_text("def run()\n    return 0\n", encoding="utf-8")

        app = build_app()
        result = runner.invoke(app, ["watch", "--repair", str(test_file), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "diagnostic" in data
        assert "repair" in data
        assert data["repair"]["status"] == "success"


class TestWatchMCPTools:
    """Tests for native MCP tools mekong_watch_status and mekong_self_repair."""

    def test_mcp_watch_status_handler(self):
        from scripts.mcp_server import handle_watch_status
        raw = handle_watch_status({})
        data = json.loads(raw)
        assert data["ok"] is True
        assert "status" in data
        assert "data" in data

    def test_mcp_self_repair_handler(self, temp_workspace: Path):
        from scripts.mcp_server import handle_self_repair

        # Missing argument
        err_raw = handle_self_repair({})
        err_data = json.loads(err_raw)
        assert err_data["ok"] is False
        assert "Missing required argument" in err_data["error"]

        # Valid repair target
        sample_file = temp_workspace / "mcp_fix.py"
        sample_file.write_text("while True\n    break\n", encoding="utf-8")

        ok_raw = handle_self_repair({"file_path": str(sample_file)})
        ok_data = json.loads(ok_raw)
        assert ok_data["ok"] is True
        assert "repair" in ok_data["data"]

    def test_mcp_server_method_parity(self, temp_workspace: Path):
        from src.core.mcp_server import MekongMcpServer
        server = MekongMcpServer()

        # Test _handle_watch_status
        raw_status = server._handle_watch_status()
        status_data = json.loads(raw_status)
        assert status_data["ok"] is True

        # Test _handle_self_repair
        target = temp_workspace / "parity_fix.py"
        target.write_text("def ok(): return 1\n", encoding="utf-8")
        raw_repair = server._handle_self_repair(file_path=str(target))
        repair_data = json.loads(raw_repair)
        assert repair_data["ok"] is True


class TestASTCoreBoundary:
    """Verify src/core/watcher_bridge.py adheres to standard library only."""

    def test_no_external_vendor_or_http_imports_in_watcher(self):
        bridge_file = Path("src/core/watcher_bridge.py")
        assert bridge_file.exists()

        tree = ast.parse(bridge_file.read_text(encoding="utf-8"), filename=str(bridge_file))
        forbidden_modules = {"anthropic", "openai", "requests", "httpx", "watchdog", "rich", "typer", "fastapi"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".")[0]
                    assert root_name not in forbidden_modules, f"Forbidden import found: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_name = node.module.split(".")[0]
                    assert root_name not in forbidden_modules, f"Forbidden import from found: {node.module}"
