# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""tests/test_antigravity_bootstrap_parallel.py — Comprehensive Test Battery for Phase 153.

Autonomous Parallel Project Bootstrap Engine E2E Verification Battery.
Validates:
1. TestBootstrapParallelBoundary:
   AST static analysis of src/core/bootstrap_parallel_engine.py (0 vendor SDKs,
   0 third-party HTTP/network libs, 0 UI/CLI libs, strict stdlib only).
2. TestTopologicalDagResolution:
   Kahn's algorithm DAG ordering, 2-node / 3-node cycle detection, self-loops,
   and missing/unknown dependency handling.
3. TestParallelExecutionEngine:
   Concurrency scaling (workers=1 vs workers=4), thread ID tracking,
   and zero-mutation dry-run mode.
4. TestAtomicRollbackOnFailure:
   Injected task failures across early, middle, and late stages, clean zero-orphan
   rollback, user pre-existing file restoration, and git repository cleanup.
5. TestTemplatesAndProfiles:
   Template presets (default, vas, fintech, agent) and profiles (smoke, standard, full),
   validating generated code structure and test integrity.
6. TestCliBootstrapCommands:
   CliRunner tests for bootstrap-auto-parallel, bootstrap-auto, and bootstrap-auto-fast
   in console and --json modes, plus CLI argument validation bounds.
7. TestDualMcpBootstrapTools:
   FastMCP app tool registration and invocation + fallback JSON-RPC stdio tool execution
   with bare alias parity.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.bootstrap_parallel_engine import (
    CORE_6_AGENTS,
    FULL_25_AGENTS,
    BootstrapContext,
    BootstrapResult,
    BootstrapTask,
    CyclicDependencyError,
    TaskStatus,
    TaskTiming,
    build_bootstrap_dag,
    execute_bootstrap_parallel,
    execute_tasks_parallel,
    get_bootstrap_status,
    resolve_dag_dependencies,
    rollback_context,
)
from src.core.mcp_server import MekongMcpServer
from scripts.mcp_server import (
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
    handle_bootstrap_auto_parallel,
    handle_bootstrap_status,
)

runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[1]
ENGINE_SOURCE_PATH = REPO_ROOT / "src" / "core" / "bootstrap_parallel_engine.py"


# =============================================================================
# 1. TestBootstrapParallelBoundary (AST Static Analysis)
# =============================================================================


class TestBootstrapParallelBoundary:
    """AST static analysis verifying standard library boundary isolation."""

    def test_ast_static_analysis_zero_vendor_sdks(self) -> None:
        """Assert zero vendor SDK imports (anthropic, openai) in bootstrap engine."""
        tree = ast.parse(ENGINE_SOURCE_PATH.read_text(encoding="utf-8"))
        vendor_sdks = {"anthropic", "openai"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_pkg = alias.name.split(".")[0]
                    assert top_pkg not in vendor_sdks, (
                        f"Forbidden vendor SDK imported: '{alias.name}' at line {node.lineno}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_pkg = node.module.split(".")[0]
                    assert top_pkg not in vendor_sdks, (
                        f"Forbidden vendor SDK imported: '{node.module}' at line {node.lineno}"
                    )

    def test_ast_static_analysis_zero_third_party_http_libs(self) -> None:
        """Assert zero third-party HTTP/network/web imports in core bootstrap engine."""
        tree = ast.parse(ENGINE_SOURCE_PATH.read_text(encoding="utf-8"))
        forbidden_http = {
            "requests",
            "httpx",
            "aiohttp",
            "fastapi",
            "starlette",
            "websockets",
            "urllib3",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_pkg = alias.name.split(".")[0]
                    assert top_pkg not in forbidden_http, (
                        f"Forbidden HTTP/web library imported: '{alias.name}' at line {node.lineno}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_pkg = node.module.split(".")[0]
                    assert top_pkg not in forbidden_http, (
                        f"Forbidden HTTP/web library imported: '{node.module}' at line {node.lineno}"
                    )

    def test_ast_static_analysis_zero_ui_and_cli_libs(self) -> None:
        """Assert zero UI, CLI, or schema framework imports (rich, typer, pydantic) in core."""
        tree = ast.parse(ENGINE_SOURCE_PATH.read_text(encoding="utf-8"))
        forbidden_frameworks = {"rich", "typer", "pydantic"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_pkg = alias.name.split(".")[0]
                    assert top_pkg not in forbidden_frameworks, (
                        f"Forbidden CLI/UI framework imported in core: '{alias.name}' at line {node.lineno}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_pkg = node.module.split(".")[0]
                    assert top_pkg not in forbidden_frameworks, (
                        f"Forbidden CLI/UI framework imported in core: '{node.module}' at line {node.lineno}"
                    )

    def test_ast_static_analysis_stdlib_allowlist(self) -> None:
        """Verify all imported modules in bootstrap engine belong strictly to Python stdlib."""
        tree = ast.parse(ENGINE_SOURCE_PATH.read_text(encoding="utf-8"))
        allowed_stdlib = {
            "__future__",
            "concurrent",
            "dataclasses",
            "enum",
            "hashlib",
            "json",
            "logging",
            "os",
            "pathlib",
            "shutil",
            "stat",
            "subprocess",
            "sys",
            "tempfile",
            "threading",
            "time",
            "typing",
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top_pkg = alias.name.split(".")[0]
                    assert top_pkg in allowed_stdlib, (
                        f"Unrecognized non-stdlib import: '{top_pkg}' in {ENGINE_SOURCE_PATH}"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top_pkg = node.module.split(".")[0]
                    assert top_pkg in allowed_stdlib, (
                        f"Unrecognized non-stdlib import: '{top_pkg}' in {ENGINE_SOURCE_PATH}"
                    )


# =============================================================================
# 2. TestTopologicalDagResolution (Kahn's Algorithm & Cycles)
# =============================================================================


class TestTopologicalDagResolution:
    """Test topological sorting, dependency resolution, cycle detection, and error handling."""

    def test_kahn_topological_sort_linear(self) -> None:
        """Verify linear dependency chain order (A -> B -> C)."""
        tasks = [
            BootstrapTask(id="c", name="Task C", dependencies=["b"]),
            BootstrapTask(id="a", name="Task A", dependencies=[]),
            BootstrapTask(id="b", name="Task B", dependencies=["a"]),
        ]
        sorted_order = resolve_dag_dependencies(tasks)
        assert sorted_order == ["a", "b", "c"]

    def test_kahn_topological_sort_branching(self) -> None:
        """Verify branching DAG ordering (A -> B, A -> C, (B, C) -> D)."""
        tasks = [
            BootstrapTask(id="d", name="Task D", dependencies=["b", "c"]),
            BootstrapTask(id="b", name="Task B", dependencies=["a"]),
            BootstrapTask(id="c", name="Task C", dependencies=["a"]),
            BootstrapTask(id="a", name="Task A", dependencies=[]),
        ]
        order = resolve_dag_dependencies(tasks)
        assert order[0] == "a"
        assert order[-1] == "d"
        assert set(order[1:3]) == {"b", "c"}

    def test_cycle_detection_two_node(self) -> None:
        """Detect two-node circular dependency (A -> B -> A)."""
        tasks = [
            BootstrapTask(id="a", name="Task A", dependencies=["b"]),
            BootstrapTask(id="b", name="Task B", dependencies=["a"]),
        ]
        with pytest.raises(CyclicDependencyError) as exc_info:
            resolve_dag_dependencies(tasks)
        assert "Cyclic dependency detected" in str(exc_info.value)
        assert "a" in str(exc_info.value)
        assert "b" in str(exc_info.value)

    def test_cycle_detection_three_node(self) -> None:
        """Detect three-node circular dependency (A -> B -> C -> A)."""
        tasks = [
            BootstrapTask(id="a", name="Task A", dependencies=["c"]),
            BootstrapTask(id="b", name="Task B", dependencies=["a"]),
            BootstrapTask(id="c", name="Task C", dependencies=["b"]),
        ]
        with pytest.raises(CyclicDependencyError) as exc_info:
            resolve_dag_dependencies(tasks)
        assert "Cyclic dependency detected" in str(exc_info.value)

    def test_cycle_detection_self_loop(self) -> None:
        """Detect self-loop dependency (A -> A)."""
        tasks = [
            BootstrapTask(id="a", name="Task A", dependencies=["a"]),
        ]
        with pytest.raises(CyclicDependencyError) as exc_info:
            resolve_dag_dependencies(tasks)
        assert "Cyclic dependency detected" in str(exc_info.value)

    def test_missing_dependency_raises_value_error(self) -> None:
        """Raise ValueError when a task references a non-existent dependency."""
        tasks = [
            BootstrapTask(id="a", name="Task A", dependencies=["non_existent_task"]),
        ]
        with pytest.raises(ValueError) as exc_info:
            resolve_dag_dependencies(tasks)
        assert "references unknown dependency 'non_existent_task'" in str(exc_info.value)

    def test_standard_bootstrap_dag_is_acyclic(self, tmp_path: Path) -> None:
        """Verify the built-in bootstrap DAG is topologically valid and acyclic."""
        ctx = BootstrapContext(target_path=tmp_path)
        dag = build_bootstrap_dag(ctx)
        order = resolve_dag_dependencies(dag)
        assert len(order) == len(dag)
        assert order[0] == "validate_workspace"
        assert order[1] == "snapshot_prestate"
        assert order[-1] == "finalize_telemetry"


# =============================================================================
# 3. TestParallelExecutionEngine (Concurrency, Scaling, Dry-Run)
# =============================================================================


class TestParallelExecutionEngine:
    """Test parallel worker execution, concurrency scaling, thread tracking, and dry-run."""

    def test_concurrency_scaling_workers_1_vs_4(self, tmp_path: Path) -> None:
        """Verify engine executes successfully across both workers=1 and workers=4."""
        target_single = tmp_path / "single_worker"
        target_multi = tmp_path / "multi_worker"

        res_single = execute_bootstrap_parallel(
            goal="Single worker bootstrap",
            target_path=target_single,
            workers=1,
            profile="smoke",
            template="default",
        )
        assert res_single.ok is True
        assert res_single.rolled_back is False
        assert len(res_single.created_files) > 0

        res_multi = execute_bootstrap_parallel(
            goal="Multi worker bootstrap",
            target_path=target_multi,
            workers=4,
            profile="smoke",
            template="default",
        )
        assert res_multi.ok is True
        assert res_multi.rolled_back is False
        assert len(res_multi.created_files) > 0

    def test_thread_id_tracking_in_task_timings(self, tmp_path: Path) -> None:
        """Verify that every executed task records worker thread identity and duration."""
        target = tmp_path / "thread_tracking"
        res = execute_bootstrap_parallel(
            goal="Thread tracking test",
            target_path=target,
            workers=4,
            profile="smoke",
        )
        assert res.ok is True
        assert len(res.task_timings) >= 10

        worker_ids = set()
        for tid, timing in res.task_timings.items():
            assert timing.task_id == tid
            assert timing.duration_ms >= 0.0
            assert timing.worker_id != ""
            worker_ids.add(timing.worker_id)
            if timing.status == TaskStatus.COMPLETED:
                assert timing.end_time >= timing.start_time

        # With 4 workers and multiple concurrent tasks, thread IDs are captured
        assert len(worker_ids) >= 1

    def test_dry_run_mode_zero_filesystem_mutations(self, tmp_path: Path) -> None:
        """Verify dry-run mode previews execution with ZERO disk mutations."""
        target = tmp_path / "dry_run_target"
        target.mkdir(parents=True, exist_ok=True)

        res = execute_bootstrap_parallel(
            goal="Dry run test",
            target_path=target,
            workers=4,
            profile="standard",
            template="default",
            dry_run=True,
        )
        assert res.ok is True
        assert res.dry_run is True
        assert res.rolled_back is False
        assert len(res.created_files) > 0

        # Assert no files or subdirectories were actually created on disk
        disk_items = list(target.iterdir())
        assert len(disk_items) == 0, f"Expected 0 items on disk in dry-run mode, found: {disk_items}"


# =============================================================================
# 4. TestAtomicRollbackOnFailure (Rollback & Restoration)
# =============================================================================


class TestAtomicRollbackOnFailure:
    """Test atomic checkpoint rollback upon injected failures across pipeline stages."""

    def test_direct_rollback_context_cleans_created_files_and_dirs(self, tmp_path: Path) -> None:
        """Verify direct rollback_context unlinks created files and prunes empty directories."""
        target = tmp_path / "rollback_test"
        target.mkdir()

        ctx = BootstrapContext(target_path=target)
        ctx.write_file("file1.txt", "content1")
        ctx.write_file("sub/file2.txt", "content2")
        ctx.register_dir("sub")

        assert (target / "file1.txt").is_file()
        assert (target / "sub" / "file2.txt").is_file()

        reverted = rollback_context(ctx)
        assert "file1.txt" in reverted
        assert "sub/file2.txt" in reverted
        assert not (target / "file1.txt").exists()
        assert not (target / "sub" / "file2.txt").exists()
        assert not (target / "sub").exists()

    def test_injected_early_task_failure_rollback(self, tmp_path: Path) -> None:
        """Verify clean zero-orphan rollback when an early task fails."""
        target = tmp_path / "early_fail_target"

        def failing_early_action(context: BootstrapContext) -> None:
            raise RuntimeError("Injected early stage failure")

        custom_tasks = [
            BootstrapTask(id="step1", name="Step 1", action=lambda ctx: ctx.write_file("step1.txt", "hello")),
            BootstrapTask(id="step2_fail", name="Step 2 Fail", dependencies=["step1"], action=failing_early_action),
            BootstrapTask(id="step3", name="Step 3", dependencies=["step2_fail"], action=lambda ctx: ctx.write_file("step3.txt", "world")),
        ]

        ctx = BootstrapContext(target_path=target)
        success = execute_tasks_parallel(custom_tasks, ctx)
        assert success is False
        rollback_context(ctx)

        assert not (target / "step1.txt").exists()
        assert not (target / "step3.txt").exists()

    def test_injected_late_task_failure_via_execute_bootstrap_parallel(self, tmp_path: Path) -> None:
        """Verify execute_bootstrap_parallel automatically triggers rollback on verification failure."""
        target = tmp_path / "late_fail_target"

        with patch(
            "src.core.bootstrap_parallel_engine.task_verify_integrity",
            side_effect=RuntimeError("Injected late integrity verification error"),
        ):
            res = execute_bootstrap_parallel(
                goal="Late failure test",
                target_path=target,
                workers=2,
                profile="smoke",
            )

        assert res.ok is False
        assert res.rolled_back is True
        assert "Injected late integrity verification error" in str(res.error)

        # Confirm target directory has zero created project files leftover
        assert not (target / "GEMINI.md").exists()
        assert not (target / "AGENTS.md").exists()
        assert not (target / "HARNESS.md").exists()
        assert not (target / "src").exists()

    def test_user_file_content_restoration_on_rollback(self, tmp_path: Path) -> None:
        """Verify pre-existing user files are restored to original content upon rollback."""
        target = tmp_path / "restore_target"
        target.mkdir()

        unrelated_file = target / "user_notes.txt"
        unrelated_file.write_text("Important notes", encoding="utf-8")

        overwritten_file = target / "GEMINI.md"
        overwritten_file.write_text("Original user GEMINI configuration", encoding="utf-8")

        ctx = BootstrapContext(target_path=target, force=True)
        ctx.write_file("GEMINI.md", "Overwritten new engine GEMINI content")
        ctx.write_file("new_artifact.txt", "Newly created artifact")

        assert overwritten_file.read_text(encoding="utf-8") == "Overwritten new engine GEMINI content"
        assert (target / "new_artifact.txt").is_file()

        rollback_context(ctx)

        # Unrelated file remains untouched
        assert unrelated_file.read_text(encoding="utf-8") == "Important notes"
        # Overwritten file restored to exact original content
        assert overwritten_file.read_text(encoding="utf-8") == "Original user GEMINI configuration"
        # Newly created file removed
        assert not (target / "new_artifact.txt").exists()

    def test_git_repo_cleanup_on_rollback(self, tmp_path: Path) -> None:
        """Verify git directory created by engine is cleaned up on rollback without removing user files."""
        target = tmp_path / "git_target"
        target.mkdir()

        user_doc = target / "README.md"
        user_doc.write_text("Existing readme", encoding="utf-8")

        ctx = BootstrapContext(target_path=target)
        git_dir = target / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("[core]\n", encoding="utf-8")
        ctx.metadata["git_dir_created_by_us"] = True
        ctx.write_file("scaffold_file.py", "x = 1")

        rollback_context(ctx)

        assert not git_dir.exists()
        assert not (target / "scaffold_file.py").exists()
        assert user_doc.read_text(encoding="utf-8") == "Existing readme"


# =============================================================================
# 5. TestTemplatesAndProfiles (Presets, Profiles & Test Integrity)
# =============================================================================


class TestTemplatesAndProfiles:
    """Test domain template presets (default, vas, fintech, agent) and profiles (smoke, standard, full)."""

    def test_template_default(self, tmp_path: Path) -> None:
        """Verify default template scaffolds standard main.py and test_main.py."""
        target = tmp_path / "tpl_default"
        res = execute_bootstrap_parallel(
            goal="Default template test",
            target_path=target,
            template="default",
            profile="smoke",
        )
        assert res.ok is True
        assert (target / "src" / "main.py").is_file()
        assert (target / "tests" / "test_main.py").is_file()

        main_py = (target / "src" / "main.py").read_text(encoding="utf-8")
        assert "Hello from Mekong CLI Project" in main_py

    def test_template_vas(self, tmp_path: Path) -> None:
        """Verify VAS template scaffolds VasLedger, TT78 invoice validator, and chart of accounts."""
        target = tmp_path / "tpl_vas"
        res = execute_bootstrap_parallel(
            goal="VAS template test",
            target_path=target,
            template="vas",
            profile="smoke",
        )
        assert res.ok is True
        assert (target / "src" / "vas" / "accounting.py").is_file()
        assert (target / "src" / "vas" / "tt78_invoice.py").is_file()
        assert (target / "src" / "vas" / "chart_of_accounts.json").is_file()
        assert (target / "tests" / "test_vas.py").is_file()

        coa = json.loads((target / "src" / "vas" / "chart_of_accounts.json").read_text(encoding="utf-8"))
        assert "accounts" in coa
        assert "111" in coa["accounts"]

    def test_template_fintech(self, tmp_path: Path) -> None:
        """Verify fintech template scaffolds VietQR, NAPAS 24/7 reconciliation, and PCI masking."""
        target = tmp_path / "tpl_fintech"
        res = execute_bootstrap_parallel(
            goal="Fintech template test",
            target_path=target,
            template="fintech",
            profile="smoke",
        )
        assert res.ok is True
        assert (target / "src" / "fintech" / "vietqr.py").is_file()
        assert (target / "src" / "fintech" / "napas247.py").is_file()
        assert (target / "src" / "fintech" / "pci_tokens.py").is_file()
        assert (target / "tests" / "test_fintech.py").is_file()

        vietqr_code = (target / "src" / "fintech" / "vietqr.py").read_text(encoding="utf-8")
        assert "generate_vietqr_payload" in vietqr_code

    def test_template_agent(self, tmp_path: Path) -> None:
        """Verify agent template scaffolds AgentSwarm, MemoryMesh, and AgiLoop."""
        target = tmp_path / "tpl_agent"
        res = execute_bootstrap_parallel(
            goal="Agent template test",
            target_path=target,
            template="agent",
            profile="smoke",
        )
        assert res.ok is True
        assert (target / "src" / "agents" / "swarm.py").is_file()
        assert (target / "src" / "agents" / "memory_mesh.py").is_file()
        assert (target / "src" / "agents" / "agi_loop.py").is_file()
        assert (target / "tests" / "test_agent.py").is_file()

        swarm_code = (target / "src" / "agents" / "swarm.py").read_text(encoding="utf-8")
        assert "class AgentSwarm" in swarm_code

    def test_invalid_template_raises_value_error(self, tmp_path: Path) -> None:
        """Assert ValueError for unsupported template name."""
        with pytest.raises(ValueError) as exc_info:
            execute_bootstrap_parallel(target_path=tmp_path, template="invalid_xyz")
        assert "Unknown template 'invalid_xyz'" in str(exc_info.value)

    def test_profile_smoke_scaffolds_6_agents(self, tmp_path: Path) -> None:
        """Verify smoke profile scaffolds minimal 6 core subagents."""
        target = tmp_path / "prof_smoke"
        res = execute_bootstrap_parallel(
            goal="Smoke profile test",
            target_path=target,
            profile="smoke",
        )
        assert res.ok is True
        reg_file = target / ".agents" / "subagents" / "registry.json"
        assert reg_file.is_file()
        reg = json.loads(reg_file.read_text(encoding="utf-8"))
        assert reg["total_agents"] == len(CORE_6_AGENTS)
        agent_ids = [ag["id"] for ag in reg["agents"]]
        assert "ceo" in agent_ids
        assert "cto" in agent_ids

    def test_profile_standard_and_full_scaffolds_25_agents(self, tmp_path: Path) -> None:
        """Verify standard and full profiles scaffold all 25 subagents."""
        target = tmp_path / "prof_standard"
        res = execute_bootstrap_parallel(
            goal="Standard profile test",
            target_path=target,
            profile="standard",
        )
        assert res.ok is True
        reg_file = target / ".agents" / "subagents" / "registry.json"
        reg = json.loads(reg_file.read_text(encoding="utf-8"))
        assert reg["total_agents"] == len(FULL_25_AGENTS)
        assert (target / "dna" / "core-dna.json").is_file()

    def test_invalid_profile_raises_value_error(self, tmp_path: Path) -> None:
        """Assert ValueError for unsupported profile name."""
        with pytest.raises(ValueError) as exc_info:
            execute_bootstrap_parallel(target_path=tmp_path, profile="unsupported_profile")
        assert "Unknown profile 'unsupported_profile'" in str(exc_info.value)


# =============================================================================
# 6. TestCliBootstrapCommands (CliRunner, Aliases & Bounds)
# =============================================================================


class TestCliBootstrapCommands:
    """Test Typer CLI surface for bootstrap-auto-parallel, bootstrap-auto, and bootstrap-auto-fast."""

    @pytest.fixture
    def app(self):
        return build_app()

    def test_cli_bootstrap_auto_parallel_help(self, app) -> None:
        """Verify bootstrap-auto-parallel --help displays options and documentation."""
        res = runner.invoke(app, ["bootstrap-auto-parallel", "--help"])
        assert res.exit_code == 0
        assert "Autonomous Parallel Bootstrap" in res.stdout
        assert "--workers" in res.stdout
        assert "--profile" in res.stdout
        assert "--template" in res.stdout
        assert "--dry-run" in res.stdout
        assert "--json" in res.stdout

    def test_cli_bootstrap_auto_parallel_console_dry_run(self, app, tmp_path: Path) -> None:
        """Verify console execution in dry-run mode prints Rich cards and exits 0."""
        target = tmp_path / "cli_console"
        res = runner.invoke(
            app,
            [
                "bootstrap-auto-parallel",
                "Scaffold Console Test",
                "--target",
                str(target),
                "--workers",
                "2",
                "--profile",
                "smoke",
                "--dry-run",
            ],
        )
        assert res.exit_code == 0
        assert "Mekong Autonomous Parallel Bootstrap Engine" in res.stdout
        assert "Parallel Task Execution Summary" in res.stdout
        assert "Bootstrap Complete" in res.stdout

    def test_cli_bootstrap_auto_parallel_json_mode(self, app, tmp_path: Path) -> None:
        """Verify --json mode outputs machine-readable JSON structure matching spec."""
        target = tmp_path / "cli_json"
        res = runner.invoke(
            app,
            [
                "bootstrap-auto-parallel",
                "Scaffold JSON Test",
                "--target",
                str(target),
                "--workers",
                "2",
                "--profile",
                "smoke",
                "--dry-run",
                "--json",
            ],
        )
        assert res.exit_code == 0
        payload = json.loads(res.stdout)
        assert payload["ok"] is True
        assert payload["status"] == "completed"
        assert payload["goal"] == "Scaffold JSON Test"
        assert payload["workers"] == 2
        assert payload["profile"] == "smoke"
        assert "tasks" in payload
        assert "checkpoint" in payload

    def test_cli_companion_alias_bootstrap_auto(self, app, tmp_path: Path) -> None:
        """Verify companion alias bootstrap-auto executes cleanly in --json mode."""
        target = tmp_path / "cli_auto"
        res = runner.invoke(
            app,
            [
                "bootstrap-auto",
                "Auto Companion Goal",
                "--target",
                str(target),
                "--profile",
                "smoke",
                "--dry-run",
                "--json",
            ],
        )
        assert res.exit_code == 0
        payload = json.loads(res.stdout)
        assert payload["ok"] is True
        assert payload["status"] == "completed"

    def test_cli_companion_alias_bootstrap_auto_fast(self, app, tmp_path: Path) -> None:
        """Verify companion alias bootstrap-auto-fast defaults to 8 workers and smoke profile."""
        target = tmp_path / "cli_auto_fast"
        res = runner.invoke(
            app,
            [
                "bootstrap-auto-fast",
                "Fast Companion Goal",
                "--target",
                str(target),
                "--dry-run",
                "--json",
            ],
        )
        assert res.exit_code == 0
        payload = json.loads(res.stdout)
        assert payload["ok"] is True
        assert payload["workers"] == 8
        assert payload["profile"] == "smoke"

    def test_cli_validation_worker_count_bounds(self, app) -> None:
        """Verify worker count boundary enforcement (< 1 or > 32)."""
        res_zero = runner.invoke(app, ["bootstrap-auto-parallel", "--workers", "0", "--dry-run"])
        assert res_zero.exit_code != 0
        assert "Invalid worker count" in res_zero.stdout

        res_excess = runner.invoke(app, ["bootstrap-auto-parallel", "--workers", "40", "--dry-run"])
        assert res_excess.exit_code != 0
        assert "Invalid worker count" in res_excess.stdout

    def test_cli_validation_invalid_profile(self, app) -> None:
        """Verify CLI error on unknown profile."""
        res = runner.invoke(app, ["bootstrap-auto-parallel", "--profile", "unknown_profile", "--dry-run"])
        assert res.exit_code != 0
        assert "Unknown profile 'unknown_profile'" in res.stdout

    def test_cli_validation_invalid_template(self, app) -> None:
        """Verify CLI error on unknown template."""
        res = runner.invoke(app, ["bootstrap-auto-parallel", "--template", "unknown_tpl", "--dry-run"])
        assert res.exit_code != 0
        assert "Unknown template 'unknown_tpl'" in res.stdout


# =============================================================================
# 7. TestDualMcpBootstrapTools (FastMCP & JSON-RPC Parity)
# =============================================================================


class TestDualMcpBootstrapTools:
    """Test FastMCP app tools and pure-Python JSON-RPC stdio fallback tool handlers."""

    def test_scripts_mcp_handle_bootstrap_auto_parallel(self) -> None:
        """Verify scripts/mcp_server.py handler executes and returns JSON payload."""
        raw_res = handle_bootstrap_auto_parallel({
            "goal": "MCP Parallel Test",
            "workers": 2,
            "profile": "smoke",
            "template": "default",
            "dry_run": True,
        })
        payload = json.loads(raw_res)
        assert payload.get("ok") is True
        assert payload.get("status") == "completed"
        assert payload.get("workers") == 2
        assert payload.get("profile") == "smoke"

    def test_scripts_mcp_handle_bootstrap_status(self) -> None:
        """Verify scripts/mcp_server.py status handler returns engine telemetry."""
        raw_res = handle_bootstrap_status({})
        payload = json.loads(raw_res)
        assert payload.get("ok") is True
        assert payload.get("engine") == "ParallelBootstrapEngine"
        assert "status" in payload

    def test_scripts_mcp_core_handlers_and_tools_spec(self) -> None:
        """Verify registration of both prefixed and bare aliases in CORE_HANDLERS and CORE_TOOLS_SPEC."""
        assert "mekong_bootstrap_auto_parallel" in CORE_HANDLERS
        assert "bootstrap_auto_parallel" in CORE_HANDLERS
        assert "mekong_bootstrap_status" in CORE_HANDLERS
        assert "bootstrap_status" in CORE_HANDLERS

        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_bootstrap_auto_parallel" in tool_names
        assert "bootstrap_auto_parallel" in tool_names
        assert "mekong_bootstrap_status" in tool_names
        assert "bootstrap_status" in tool_names

    def test_src_core_mcp_server_handlers_and_aliases(self) -> None:
        """Verify MekongMcpServer internal handlers and method aliases."""
        server = MekongMcpServer()
        res_raw = server._handle_bootstrap_auto_parallel(
            goal="Core MCP Test",
            workers=2,
            profile="smoke",
            dry_run=True,
        )
        res_data = json.loads(res_raw)
        assert res_data.get("ok") is True

        status_raw = server._handle_bootstrap_status()
        status_data = json.loads(status_raw)
        assert status_data.get("ok") is True

        # Verify alias equality
        assert server._handle_mekong_bootstrap_auto_parallel == server._handle_bootstrap_auto_parallel
        assert server._handle_bootstrap_auto_parallel == server._handle_bootstrap_auto_parallel
        assert server._handle_mekong_bootstrap_status == server._handle_bootstrap_status
        assert server._handle_bootstrap_status == server._handle_bootstrap_status

    def test_fastmcp_app_tool_registrations(self) -> None:
        """Verify FastMCP application registers bootstrap tools with valid parameter schemas."""
        server = MekongMcpServer()
        app = server.create_app()
        tools = app._tool_manager._tools

        assert "mekong_bootstrap_auto_parallel" in tools
        assert "mekong_bootstrap_status" in tools

        bootstrap_tool = tools["mekong_bootstrap_auto_parallel"]
        props = bootstrap_tool.parameters.get("properties", {})
        assert "goal" in props
        assert "workers" in props
        assert "profile" in props
        assert "template" in props
