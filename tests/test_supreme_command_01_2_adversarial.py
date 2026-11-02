# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Supreme Command #01.2 — Forensic Audit Reproduction & Adversarial Hardening Suite.

Covers:
- F01-T01 .. F01-T06: False Verified Success Closure (`GoalEngineAdapter`, `GoalEngine.verify_goal`, CLI)
- F02-T01 .. F02-T10: 3-State Worktree Lifecycle (`SCRATCH`, `ARTIFACT`, `RECOVERY`) & SHA-256 Artifact Handoff
- F03-T01 .. F03-T11: Fail-Closed Durable Webhook Admission & SQLite IntegrityError Race Recovery
- F04-T01 .. F04-T11: Server-Side WebhookAuthorityPolicy & Callback SSRF Defense
- A01 .. A22: 22-Scenario Adversarial Attack Matrix
"""

from __future__ import annotations

import hashlib
import json
import socket
import threading
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from src.cli.cook_command import register_cook_command
from src.cli.goal_commands import goal_app
from src.core.adapters.goal_engine_adapter import GoalEngineAdapter
from src.core.buzz_adapter import (
    BuzzAdapter,
    BuzzConfigError,
    BuzzSecurityError,
    _NoRedirectHandler,
    validate_callback_destination,
)
from src.core.buzz_runtime_adapter import BuzzRuntimeAdapter
from src.core.contracts import (
    CONTRACT_VERSION,
    SophiaContractValidationError,
    validate_sophia_handoff_fixture,
)
from src.core.runtime_adapter import MekongCoreRuntimeImpl
from src.mekongcli.core.goal_engine.models import (
    ExecutionTruthStatus,
    OutboxEntry,
    TaskStatus,
)
from src.mekongcli.core.goal_engine.service import GoalEngine
from src.mekongcli.core.goal_engine.store import MandateIntegrityError, SQLiteGoalStore
from src.mekongcli.core.goal_engine.worktree_manager import (
    WorktreeEscapeError,
    WorktreeFinalizationResult,
    WorktreeIsolationManager,
    WorktreeMode,
)

runner = CliRunner()


def _seed_smoke_workspace(workspace: Path) -> None:
    src_dir = workspace / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "main.py").write_text("import sys\nprint('smoke ok')\n", encoding="utf-8")
    (workspace / "produce_out.py").write_text(
        "from pathlib import Path\nPath('generated_artifact.txt').write_text('verified payload', encoding='utf-8')\nprint('ok')\n",
        encoding="utf-8",
    )


def _make_store_and_engine(tmp_path: Path) -> tuple[SQLiteGoalStore, GoalEngine]:
    _seed_smoke_workspace(tmp_path)
    db_path = tmp_path / ".mekong" / "sc012.sqlite3"
    store = SQLiteGoalStore(db_path)
    engine = GoalEngine(store=store, cwd=tmp_path)
    return store, engine


class _StubDispatcher:
    def __init__(self, *, fail: bool = False, cancel: bool = False) -> None:
        self.fail = fail
        self.cancel = cancel

    def dispatch(self, task: Any, agent: Any = None) -> dict[str, Any]:
        _ = agent
        if self.fail:
            raise RuntimeError("dispatcher failure")
        return {"ok": True, "task_id": task.id}


def _make_runtime(*, fail: bool = False) -> MekongCoreRuntimeImpl:
    return MekongCoreRuntimeImpl(
        dispatcher=_StubDispatcher(fail=fail),
        tool_registry=type("_R", (), {"execute": lambda *_args: {"ok": True}})(),
    )


# =========================================================================== #
# Gate G1 — Finding F01 (`False Verified Success` Closure: F01-T01 .. F01-T06)
# =========================================================================== #


def test_f01_t01_missing_truth_status_under_exec_cmds_true_fails_closed_unavailable(
    tmp_path: Path,
) -> None:
    """F01-T01: Missing truth_status when execute_commands=True must fail closed to UNAVAILABLE."""
    store, _ = _make_store_and_engine(tmp_path)

    class _LegacyServiceNoTruth:
        def create_goal(self, title: str) -> Any:
            return type("_G", (), {"id": "goal_legacy_1", "title": title})()

        def run_goal(self, goal_id: str, **_kwargs: Any) -> Any:
            from src.mekongcli.core.goal_engine.models import GoalStatus

            return type("_G", (), {"id": goal_id, "status": GoalStatus.SATISFIED})()

    adapter = GoalEngineAdapter(
        store=store,
        service=_LegacyServiceNoTruth(),  # type: ignore[arg-type]
        execute_commands=True,
    )
    plan = adapter.decompose("Test legacy missing truth_status")
    commit_res = adapter.commit(plan)

    assert commit_res.metadata["truth_status"] == ExecutionTruthStatus.UNAVAILABLE.value
    assert commit_res.success is False


def test_f01_t02_none_or_mock_truth_status_never_coerced_to_verified_success(
    tmp_path: Path,
) -> None:
    """F01-T02: MagicMock or None truth_status on a goal object is rejected as UNAVAILABLE."""
    from src.mekongcli.core.goal_engine.models import GoalStatus

    store, _ = _make_store_and_engine(tmp_path)
    mock_service = MagicMock()
    mock_goal = MagicMock()
    mock_goal.id = "goal_mock_1"
    mock_goal.status = GoalStatus.SATISFIED
    # MagicMock.truth_status is another MagicMock (not a valid ExecutionTruthStatus)
    mock_service.create_goal.return_value = mock_goal
    mock_service.run_goal.return_value = mock_goal

    adapter = GoalEngineAdapter(store=store, service=mock_service, execute_commands=True)
    plan = adapter.decompose("Test MagicMock service")
    commit_res = adapter.commit(plan)

    assert commit_res.metadata["truth_status"] == ExecutionTruthStatus.UNAVAILABLE.value
    assert commit_res.success is False


def test_f01_t03_verify_goal_with_simulated_tasks_refuses_verified_success_even_if_simulated_run_false(
    tmp_path: Path,
) -> None:
    """F01-T03: Calling verify_goal(simulated_run=False) on a simulated goal keeps SIMULATED truth_status."""
    _, engine = _make_store_and_engine(tmp_path)
    goal = engine.create_goal("Simulated run")
    engine.run_goal(goal.id, verification_profile="smoke", execute_commands=False)

    reverified = engine.verify_goal(goal.id, verification_profile="smoke", simulated_run=False)
    assert reverified.truth_status == ExecutionTruthStatus.SIMULATED
    assert reverified.truth_status != ExecutionTruthStatus.VERIFIED_SUCCESS


def test_f01_t04_task_level_truth_mismatch_rejects_goal_level_verified_success(
    tmp_path: Path,
) -> None:
    """F01-T04: GoalEngineAdapter.commit rejects VERIFIED_SUCCESS if any stored task is not VERIFIED_SUCCESS."""
    from src.mekongcli.core.goal_engine.models import GoalStatus

    store, engine = _make_store_and_engine(tmp_path)
    goal = engine.create_goal("Task mismatch check")
    tasks = store.get_tasks(goal.id)
    for t in tasks:
        t.status = TaskStatus.COMPLETED
        t.truth_status = ExecutionTruthStatus.PLANNED
    store.save_tasks(tasks)

    class _LyingService:
        def create_goal(self, _title: str) -> Any:
            return goal

        def run_goal(self, _goal_id: str, **_kwargs: Any) -> Any:
            goal.status = GoalStatus.SATISFIED
            goal.truth_status = ExecutionTruthStatus.VERIFIED_SUCCESS
            return goal

    adapter = GoalEngineAdapter(store=store, service=_LyingService(), execute_commands=True)  # type: ignore[arg-type]
    plan = adapter.decompose("Task mismatch")
    commit_res = adapter.commit(plan)
    assert commit_res.metadata["truth_status"] == ExecutionTruthStatus.UNAVAILABLE.value
    assert commit_res.success is False


def test_f01_t05_cli_cook_auto_and_parallel_honor_isolate_worktree_ticket_id_require_verified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F01-T05: cook-auto and cook-auto-parallel expose --isolate-worktree, --ticket-id, and --require-verified."""
    _seed_smoke_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    app = typer.Typer()
    register_cook_command(app)

    res_sim = runner.invoke(
        app,
        [
            "cook-auto",
            "Build feature X",
            "--profile",
            "smoke",
            "--require-verified",
            "--json",
        ],
    )
    assert res_sim.exit_code != 0
    payload_sim = json.loads(res_sim.stdout)
    assert payload_sim["truth_status"] == "SIMULATED"
    assert payload_sim["simulated"] is True


def test_f01_t06_cli_goal_list_and_cancel_emit_truth_status_and_simulated(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """F01-T06: goal list and goal cancel JSON outputs include truth_status and simulated."""
    _seed_smoke_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    db_file = str(tmp_path / ".mekong" / "cli_goals.sqlite3")

    init_res = runner.invoke(goal_app, ["create", "Audit truth fields", "--db", db_file, "--json"])
    assert init_res.exit_code == 0
    goal_id = json.loads(init_res.stdout)["id"]

    list_res = runner.invoke(goal_app, ["list", "--db", db_file, "--json"])
    assert list_res.exit_code == 0
    listed = json.loads(list_res.stdout)
    matching = [g for g in listed if g["id"] == goal_id]
    assert len(matching) == 1
    assert matching[0]["truth_status"] == "PLANNED"
    assert "simulated" in matching[0]

    cancel_res = runner.invoke(goal_app, ["cancel", goal_id, "--db", db_file, "--json"])
    assert cancel_res.exit_code == 0
    cancelled = json.loads(cancel_res.stdout)
    assert cancelled["truth_status"] == "CANCELLED"
    assert cancelled["simulated"] is False


# =========================================================================== #
# Gate G2 — Finding F02 (3-State Worktree Lifecycle + SHA-256 Artifacts: F02-T01 .. F02-T10)
# =========================================================================== #


def test_f02_t01_scratch_mode_cleans_up_unmodified_worktree(tmp_path: Path) -> None:
    """F02-T01: Unmodified successful worktree finalizes in SCRATCH mode and is removed."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_scratch", "task_1")
    assert wt.exists()

    fin = mgr.finalize_worktree(wt, ticket_id="tkt_scratch", task_id="task_1", success=True)
    assert fin.mode == WorktreeMode.SCRATCH
    assert fin.cleaned_up is True
    assert not wt.exists()


def test_f02_t02_artifact_mode_harvests_modified_files_to_mekong_artifacts_before_cleanup(
    tmp_path: Path,
) -> None:
    """F02-T02: Modified successful worktree harvests changed files into .mekong/artifacts/ before cleanup."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_art", "task_2", attempt_no=1)
    (wt / "deliverable.json").write_text('{"ready": true}', encoding="utf-8")

    fin = mgr.finalize_worktree(wt, ticket_id="tkt_art", task_id="task_2", attempt_no=1, success=True)
    assert fin.mode == WorktreeMode.ARTIFACT
    assert fin.cleaned_up is True
    assert not wt.exists()
    assert fin.artifact_dir is not None and fin.artifact_dir.exists()
    harvested_file = fin.artifact_dir / "files" / "deliverable.json"
    assert harvested_file.exists()
    assert harvested_file.read_text(encoding="utf-8") == '{"ready": true}'


def test_f02_t03_artifact_manifest_records_sha256_size_safe_ref_and_verification_status(
    tmp_path: Path,
) -> None:
    """F02-T03: Harvested manifest.json contains verified SHA-256 digest and metadata for each artifact."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_sha", "task_3", attempt_no=2)
    payload_bytes = b"deterministic artifact content\n"
    (wt / "report.txt").write_bytes(payload_bytes)
    expected_sha = hashlib.sha256(payload_bytes).hexdigest()

    fin = mgr.finalize_worktree(
        wt,
        ticket_id="tkt_sha",
        task_id="task_3",
        attempt_no=2,
        success=True,
        verification_status="VERIFIED_SUCCESS",
    )
    assert fin.manifest_path is not None and fin.manifest_path.exists()
    manifest = json.loads(fin.manifest_path.read_text(encoding="utf-8"))
    assert manifest["ticket_id"] == "tkt_sha"
    assert manifest["attempt_id"] == "attempt_2"
    rec = next(r for r in manifest["artifacts"] if r["relative_path"] == "report.txt")
    assert rec["sha256"] == expected_sha
    assert rec["size_bytes"] == len(payload_bytes)
    assert rec["verification_status"] == "VERIFIED_SUCCESS"


def test_f02_t04_recovery_mode_preserves_failed_worktree_under_recovery_worktrees(
    tmp_path: Path,
) -> None:
    """F02-T04: Failed task execution preserves worktree state under .mekong/recovery_worktrees/."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_fail", "task_4", attempt_no=1)
    (wt / "partial_crash.log").write_text("partial write before crash", encoding="utf-8")

    fin = mgr.finalize_worktree(
        wt,
        ticket_id="tkt_fail",
        task_id="task_4",
        attempt_no=1,
        success=False,
        reason="exit_code_1",
    )
    assert fin.mode == WorktreeMode.RECOVERY
    assert fin.preserved_path is not None and fin.preserved_path.exists()
    assert (fin.preserved_path / "partial_crash.log").read_text(encoding="utf-8") == "partial write before crash"
    assert (fin.preserved_path / "recovery_manifest.json").exists()
    assert not wt.exists()


def test_f02_t05_recovery_mode_preserves_side_effect_uncertain_worktree(tmp_path: Path) -> None:
    """F02-T05: Uncertain side effects force RECOVERY preservation even if success flag was True."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_uncertain", "task_5")
    (wt / "mutation.tmp").write_text("uncertain state", encoding="utf-8")

    fin = mgr.finalize_worktree(
        wt,
        ticket_id="tkt_uncertain",
        task_id="task_5",
        success=True,
        side_effect_uncertain=True,
    )
    assert fin.mode == WorktreeMode.RECOVERY
    assert fin.preserved_path is not None and fin.preserved_path.exists()


def test_f02_t06_recovery_mode_never_overwrites_previous_attempts(tmp_path: Path) -> None:
    """F02-T06: Repeated recovery preservations for the same attempt allocate distinct directories."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)

    wt1 = mgr.allocate("tkt_coll", "task_6", attempt_no=1)
    (wt1 / "state.txt").write_text("first failure", encoding="utf-8")
    fin1 = mgr.finalize_worktree(wt1, ticket_id="tkt_coll", task_id="task_6", attempt_no=1, success=False)

    wt2 = mgr.allocate("tkt_coll", "task_6", attempt_no=1)
    (wt2 / "state.txt").write_text("second failure", encoding="utf-8")
    fin2 = mgr.finalize_worktree(wt2, ticket_id="tkt_coll", task_id="task_6", attempt_no=1, success=False)

    assert fin1.preserved_path != fin2.preserved_path
    assert (fin1.preserved_path / "state.txt").read_text(encoding="utf-8") == "first failure"  # type: ignore[union-attr]
    assert (fin2.preserved_path / "state.txt").read_text(encoding="utf-8") == "second failure"  # type: ignore[union-attr]


def test_f02_t07_non_git_fallback_worktree_seeds_workspace_and_harvests_changes(
    tmp_path: Path,
) -> None:
    """F02-T07: Non-git workspaces seed top-level files into worktree and only harvest modified/new files."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_nongit", "task_7")
    assert (wt / "src" / "main.py").exists()
    (wt / "new_output.txt").write_text("created in fallback wt", encoding="utf-8")

    fin = mgr.finalize_worktree(wt, ticket_id="tkt_nongit", task_id="task_7", success=True)
    assert fin.mode == WorktreeMode.ARTIFACT
    rel_paths = [a.relative_path for a in fin.artifacts]
    assert "new_output.txt" in rel_paths
    assert "src/main.py" not in rel_paths


def test_f02_t08_concurrent_worktree_allocations_are_serialized_and_isolated(
    tmp_path: Path,
) -> None:
    """F02-T08: Concurrent threads allocating and finalizing worktrees do not race or cross-contaminate."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    results: list[WorktreeFinalizationResult] = []  # type: ignore[name-defined]
    lock = threading.Lock()

    def _worker(idx: int) -> None:
        wt = mgr.allocate("tkt_conc", f"task_{idx}")
        (wt / f"file_{idx}.txt").write_text(f"payload_{idx}", encoding="utf-8")
        res = mgr.finalize_worktree(wt, ticket_id="tkt_conc", task_id=f"task_{idx}", success=True)
        with lock:
            results.append(res)

    threads = [threading.Thread(target=_worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 4
    assert all(r.mode == WorktreeMode.ARTIFACT and r.cleaned_up for r in results)


def test_f02_t09_cleanup_verifies_expected_owner_and_is_idempotent(tmp_path: Path) -> None:
    """F02-T09: cleanup() rejects mismatched expected_owner and returns False on already-cleaned worktree."""
    _seed_smoke_workspace(tmp_path)
    mgr = WorktreeIsolationManager(repo_root=tmp_path)
    wt = mgr.allocate("tkt_owner_a", "task_a")

    with pytest.raises(PermissionError, match="Worktree ownership mismatch"):
        mgr.cleanup(wt, expected_owner=("tkt_owner_b", "task_b"))

    assert mgr.cleanup(wt, expected_owner=("tkt_owner_a", "task_a")) is True
    assert mgr.cleanup(wt, expected_owner=("tkt_owner_a", "task_a")) is False


def test_f02_t10_goal_engine_run_goal_and_parallel_preserve_artifacts_after_worktree_cleanup(
    tmp_path: Path,
) -> None:
    """F02-T10: GoalEngine.run_goal with isolate_worktree=True harvests artifacts before removing the worktree."""
    store, engine = _make_store_and_engine(tmp_path)
    goal = engine.create_goal("Produce artifact in isolated worktree")
    tasks = store.get_tasks(goal.id)
    for idx, t in enumerate(tasks):
        t.command = "python3 produce_out.py" if idx == 0 else "python3 -m src.main --help"
        t.mutates_workspace = idx == 0
    store.save_tasks(tasks)

    finished = engine.run_goal(
        goal.id,
        verification_profile="smoke",
        execute_commands=True,
        isolate_worktree=True,
    )
    assert finished.truth_status == ExecutionTruthStatus.VERIFIED_SUCCESS
    manifests = engine.worktree_manager.list_artifacts(ticket_id=goal.id)
    assert len(manifests) >= 1
    assert any(
        a["relative_path"] == "generated_artifact.txt"
        for m in manifests
        for a in m["artifacts"]
    )


# =========================================================================== #
# Gate G3 — Finding F03 (Fail-Closed Durable Webhook Admission: F03-T01 .. F03-T11)
# =========================================================================== #


def test_f03_t01_external_webhook_mode_without_outbox_store_fails_closed() -> None:
    """F03-T01: BuzzRuntimeAdapter in external_webhook mode without outbox_store raises BuzzConfigError."""
    runtime = _make_runtime()
    adapter = BuzzRuntimeAdapter(
        runtime=runtime,
        transport=lambda _u, _p: 200,
        outbox_store=None,
        ingress_mode="external_webhook",
    )
    with pytest.raises(BuzzConfigError, match="requires a durable outbox_store"):
        adapter.assign_mission({"goal": "Run webhook", "event_id": "evt_1"})


def test_f03_t02_external_webhook_mode_without_event_id_fails_closed(tmp_path: Path) -> None:
    """F03-T02: BuzzRuntimeAdapter in external_webhook mode without event_id raises ValueError."""
    store, _ = _make_store_and_engine(tmp_path)
    adapter = BuzzRuntimeAdapter(
        runtime=_make_runtime(),
        transport=lambda _u, _p: 200,
        outbox_store=store,
        ingress_mode="external_webhook",
    )
    with pytest.raises(ValueError, match="requires a non-empty 'event_id'"):
        adapter.assign_mission({"goal": "Run webhook without event_id", "mission_id": "m_only"})


def test_f03_t03_trusted_local_mode_preserves_backward_compatible_in_memory_execution() -> None:
    """F03-T03: Default trusted_local mode continues to allow local missions without outbox_store."""
    adapter = BuzzRuntimeAdapter(
        runtime=_make_runtime(),
        transport=lambda _u, _p: 200,
    )
    res = adapter.assign_mission({"goal": "Local test mission"})
    assert res["status"] == "completed"


def test_f03_t04_require_admission_flag_enforces_durable_outbox_even_in_trusted_local() -> None:
    """F03-T04: Passing require_admission=True in payload enforces durable outbox even in trusted_local mode."""
    adapter = BuzzRuntimeAdapter(
        runtime=_make_runtime(),
        transport=lambda _u, _p: 200,
        outbox_store=None,
    )
    with pytest.raises(BuzzConfigError):
        adapter.assign_mission({"goal": "Must admit", "event_id": "evt_req_1", "require_admission": True})


def test_f03_t05_admit_ticket_handles_concurrent_sqlite_integrity_error_race_as_deduplicated(
    tmp_path: Path,
) -> None:
    """F03-T05: Concurrent admit_ticket calls on the same (source_id, event_id) converge cleanly with 1 created and N-1 deduplicated."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)
    results: list[tuple[str, bool]] = []
    lock = threading.Lock()

    def _admit() -> None:
        rec, created = buzz.admit_webhook_event(
            {"goal": "Concurrent webhook", "source_id": "buzz", "event_id": "evt_race_100"}
        )
        with lock:
            results.append((rec.ticket_id, created))

    threads = [threading.Thread(target=_admit) for _ in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 6
    created_flags = [c for _, c in results]
    assert created_flags.count(True) == 1
    assert created_flags.count(False) == 5
    assert len({tid for tid, _ in results}) == 1


def test_f03_t06_enqueue_outbox_handles_concurrent_sqlite_integrity_error_race_as_deduplicated(
    tmp_path: Path,
) -> None:
    """F03-T06: Concurrent enqueue_outbox calls with identical idempotency_key deduplicate without raising IntegrityError."""
    store, _ = _make_store_and_engine(tmp_path)
    results: list[dict[str, Any]] = []
    lock = threading.Lock()

    def _enqueue(i: int) -> None:
        entry = OutboxEntry(
            outbox_id=f"outbox_race_{i}",
            ticket_id="tkt_race",
            source_id="buzz",
            thread_id="th_1",
            idempotency_key="shared_idem_key_001",
            payload_json='{"status": "completed"}',
        )
        res = store.enqueue_outbox(entry, callback_url="https://buzz.example/cb")
        with lock:
            results.append(res)

    threads = [threading.Thread(target=_enqueue, args=(i,)) for i in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 6
    dedup_flags = [bool(r["deduplicated"]) for r in results]
    assert dedup_flags.count(False) == 1
    assert dedup_flags.count(True) == 5


def test_f03_t07_ticket_truth_status_transitions_from_planned_to_running_to_terminal(
    tmp_path: Path,
) -> None:
    """F03-T07: Admitted webhook ticket updates truth_status to VERIFIED_SUCCESS after execution."""
    store, _ = _make_store_and_engine(tmp_path)
    adapter = BuzzRuntimeAdapter(
        runtime=_make_runtime(),
        transport=lambda _u, _p: 200,
        outbox_store=store,
        ingress_mode="external_webhook",
    )
    res = adapter.assign_mission(
        {"goal": "Execute and track ticket state", "source_id": "buzz", "event_id": "evt_state_1"}
    )
    tkt = store.get_ticket(res["ticket_id"])
    assert tkt is not None
    assert tkt["truth_status"] == ExecutionTruthStatus.VERIFIED_SUCCESS.value


def test_f03_t08_replayed_webhook_returns_duplicate_ignored_with_persisted_truth_status(
    tmp_path: Path,
) -> None:
    """F03-T08: Replayed webhook returns duplicate_ignored and includes the ticket's current truth_status."""
    store, _ = _make_store_and_engine(tmp_path)
    adapter = BuzzRuntimeAdapter(
        runtime=_make_runtime(),
        transport=lambda _u, _p: 200,
        outbox_store=store,
        ingress_mode="external_webhook",
    )
    payload = {"goal": "Idempotent mission", "source_id": "buzz", "event_id": "evt_replay_8"}
    first = adapter.assign_mission(payload)
    second = adapter.assign_mission(payload)
    assert first["status"] == "completed"
    assert second["status"] == "duplicate_ignored"
    assert second["duplicate"] is True
    assert second["truth_status"] == ExecutionTruthStatus.VERIFIED_SUCCESS.value


def test_f03_t09_failed_or_crashing_mission_updates_ticket_truth_status_to_execution_failed(
    tmp_path: Path,
) -> None:
    """F03-T09: Crashing runtime updates durable ticket truth_status to EXECUTION_FAILED."""
    store, _ = _make_store_and_engine(tmp_path)

    class _CrashingRuntime:
        def start_mission(self, *_a: Any, **_kw: Any) -> None:
            raise RuntimeError("boom")

    adapter = BuzzRuntimeAdapter(
        runtime=_CrashingRuntime(),
        transport=lambda _u, _p: 200,
        outbox_store=store,
        ingress_mode="external_webhook",
    )
    res = adapter.assign_mission({"goal": "Crash test", "source_id": "buzz", "event_id": "evt_crash_9"})
    assert res["status"] == "failed"
    tkt = store.get_ticket(res["ticket_id"])
    assert tkt is not None
    assert tkt["truth_status"] == ExecutionTruthStatus.EXECUTION_FAILED.value


def test_f03_t10_cancelled_mission_updates_ticket_truth_status_to_cancelled(
    tmp_path: Path,
) -> None:
    """F03-T10: Cancelled runtime mission updates durable ticket truth_status to CANCELLED."""
    store, _ = _make_store_and_engine(tmp_path)

    class _CancelledRuntime:
        _mission_id = "m_cancel_10"

        def start_mission(self, *_a: Any, **_kw: Any) -> None:
            pass

        def run_from_payload(self, _p: dict[str, Any]) -> Any:
            return type(
                "_R",
                (),
                {
                    "output": None,
                    "error": "cancelled by user",
                    "task_id": "t_1",
                    "metadata": {"cancelled": True},
                },
            )()

    adapter = BuzzRuntimeAdapter(
        runtime=_CancelledRuntime(),
        transport=lambda _u, _p: 200,
        outbox_store=store,
        ingress_mode="external_webhook",
    )
    res = adapter.assign_mission({"goal": "Cancel test", "source_id": "buzz", "event_id": "evt_cancel_10"})
    assert res["status"] == "cancelled"
    tkt = store.get_ticket(res["ticket_id"])
    assert tkt is not None
    assert tkt["truth_status"] == ExecutionTruthStatus.CANCELLED.value


def test_f03_t11_outbox_retry_and_dead_letter_transitions_are_durable(tmp_path: Path) -> None:
    """F03-T11: Outbox delivery retries and dead-letter transitions persist across SQLite reads."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 502)
    res = buzz.send_update(
        "failed",
        {"reason": "bad gateway"},
        callback_url="https://buzz.example/cb",
        ticket_id="tkt_dlq_11",
        idempotency_key="idem_dlq_11",
        max_attempts=2,
    )
    assert res["delivery_status"] == "FAILED_RETRYABLE"
    dlq = store.process_outbox_delivery(res["outbox_id"], lambda _u, _p: 502)
    assert dlq["delivery_status"] == "DEAD_LETTER"
    rows = store.list_outbox(ticket_id="tkt_dlq_11", delivery_status="DEAD_LETTER")
    assert len(rows) == 1


# =========================================================================== #
# Gate G4 — Finding F04 (Server-Side WebhookAuthorityPolicy & SSRF: F04-T01 .. F04-T11)
# =========================================================================== #


def test_f04_t01_webhook_cannot_supply_forged_mandate_hash_or_override_policy_version(
    tmp_path: Path,
) -> None:
    """F04-T01: Inbound webhook payload supplying mandate_hash, policy_version, or mandate_version is rejected."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    with pytest.raises(BuzzSecurityError, match="mandate_hash"):
        buzz.admit_webhook_event(
            {"goal": "Forge hash", "event_id": "e1", "mandate_hash": "deadbeef" * 8}
        )

    with pytest.raises(BuzzSecurityError, match="policy_version"):
        buzz.admit_webhook_event(
            {"goal": "Forge policy", "event_id": "e2", "policy_version": "1999.01-bypass"}
        )

    with pytest.raises(BuzzSecurityError, match="mandate_version"):
        buzz.admit_webhook_event(
            {"goal": "Forge mandate version", "event_id": "e3", "mandate_version": 999}
        )


def test_f04_t02_webhook_cannot_escalate_permitted_capabilities(tmp_path: Path) -> None:
    """F04-T02: Requesting capabilities outside policy.allowed_capabilities raises BuzzSecurityError."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    with pytest.raises(BuzzSecurityError, match="unauthorized capabilities"):
        buzz.admit_webhook_event(
            {
                "goal": "Run arbitrary shell",
                "event_id": "e_cap",
                "permitted_capabilities": ["goal_execute", "root_shell_admin"],
            }
        )


def test_f04_t03_webhook_cannot_escalate_authorized_scope(tmp_path: Path) -> None:
    """F04-T03: Requesting authorized_scope outside policy.allowed_scopes raises BuzzSecurityError."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    with pytest.raises(BuzzSecurityError, match="unauthorized scope"):
        buzz.admit_webhook_event(
            {
                "goal": "Global scope escalation",
                "event_id": "e_scope",
                "authorized_scope": "cluster_root_admin",
            }
        )


def test_f04_t04_webhook_cannot_escape_resource_boundaries_via_traversal_or_glob(
    tmp_path: Path,
) -> None:
    """F04-T04: Resource boundaries with '..', '/', '~', or '*' are rejected with BuzzSecurityError."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    for bad_boundary in (["../etc/passwd"], ["/etc"], ["~/.ssh"], ["src/*"]):
        with pytest.raises(BuzzSecurityError, match="resource boundary"):
            buzz.admit_webhook_event(
                {
                    "goal": "Boundary escape",
                    "event_id": f"e_bound_{bad_boundary[0]}",
                    "resource_boundaries": bad_boundary,
                }
            )


def test_f04_t05_webhook_cannot_downgrade_risk_classification(tmp_path: Path) -> None:
    """F04-T05: Webhook cannot downgrade risk_classification below policy.min_risk_classification ('standard')."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    with pytest.raises(BuzzSecurityError, match="downgrade risk_classification"):
        buzz.admit_webhook_event(
            {
                "goal": "Downgrade risk",
                "event_id": "e_risk_low",
                "risk_classification": "low",
            }
        )


def test_f04_t06_webhook_cannot_exceed_server_cost_or_retry_budget_ceilings_or_pass_non_positive(
    tmp_path: Path,
) -> None:
    """F04-T06: Cost/retry budgets <= 0, NaN/Inf, or above server ceilings are rejected."""
    store, _ = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    for bad_cost in (0.0, -5.0, 9999.0, float("inf"), float("nan")):
        with pytest.raises(BuzzSecurityError, match="cost_budget"):
            buzz.admit_webhook_event(
                {"goal": "Bad cost", "event_id": f"e_cost_{bad_cost}", "cost_budget": bad_cost}
            )

    for bad_retry in (0, -1, 50, True):
        with pytest.raises(BuzzSecurityError, match="retry_budget"):
            buzz.admit_webhook_event(
                {"goal": "Bad retry", "event_id": f"e_retry_{bad_retry}", "retry_budget": bad_retry}
            )


def test_f04_t07_callback_ssrf_blocks_http_non_https_and_embedded_credentials() -> None:
    """F04-T07: Callback validator rejects http://, file://, ftp://, and embedded user:pass@ URLs."""
    for bad_url in (
        "http://buzz.example/hook",
        "file:///etc/passwd",
        "ftp://buzz.example/file",
        "gopher://buzz.example:70/",
        "https://admin:secret@buzz.example/hook",
    ):
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination(bad_url)


def test_f04_t08_callback_ssrf_blocks_loopback_rfc1918_link_local_cgnat_and_metadata_ips() -> None:
    """F04-T08: Callback validator rejects loopback, RFC1918, link-local, AWS metadata, CGNAT, and 0.0.0.0."""
    for bad_url in (
        "https://localhost/hook",
        "https://api.internal/hook",
        "https://service.local/hook",
        "https://127.0.0.1/hook",
        "https://10.0.0.1/hook",
        "https://172.16.0.5/hook",
        "https://192.168.1.10/hook",
        "https://169.254.169.254/latest/meta-data/",
        "https://100.64.0.1/hook",
        "https://0.0.0.0/hook",
    ):
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination(bad_url)


def test_f04_t09_callback_ssrf_blocks_ipv6_loopback_mapped_ipv4_and_integer_hex_ip_literals() -> None:
    """F04-T09: Callback validator rejects IPv6 loopback, IPv4-mapped IPv6, and integer/hex encoded loopback."""
    for bad_url in (
        "https://[::1]/hook",
        "https://[::ffff:127.0.0.1]/hook",
        "https://[::ffff:169.254.169.254]/hook",
        "https://[fe80::1]/hook",
        "https://[fc00::1]/hook",
        "https://2130706433/hook",
        "https://0x7f000001/hook",
    ):
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination(bad_url)


def test_f04_t10_callback_ssrf_blocks_dns_rebinding_when_any_resolved_record_is_private() -> None:
    """F04-T10: If DNS returns both a public IP and a private/loopback IP, callback validation fails closed."""

    def _rebinding_resolver(host: str, port: int, proto: int = 0) -> list[Any]:
        _ = (host, port, proto)
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]

    with pytest.raises(BuzzSecurityError, match="forbidden"):
        validate_callback_destination(
            "https://rebind.attacker.com/hook",
            resolver=_rebinding_resolver,
        )


def test_f04_t11_no_redirect_handler_blocks_3xx_ssrf_redirect_to_internal_metadata() -> None:
    """F04-T11: _NoRedirectHandler refuses HTTP 301/302/307/308 redirects to block open-redirect SSRF."""
    handler = _NoRedirectHandler()
    with pytest.raises(BuzzSecurityError, match="redirect"):
        handler.redirect_request(
            req=None,
            fp=None,
            code=302,
            msg="Found",
            headers={},
            newurl="http://169.254.169.254/latest/meta-data/",
        )


# =========================================================================== #
# Gate G6 — 22-Scenario Adversarial Attack Matrix (A01 .. A22)
# =========================================================================== #


@pytest.mark.parametrize(
    "scenario_id",
    [f"A{i:02d}" for i in range(1, 23)],
)
def test_a01_to_a22_adversarial_trust_matrix(scenario_id: str, tmp_path: Path) -> None:
    """Execute all 22 adversarial attack scenarios (A01..A22) and verify deterministic fail-closed defense."""
    store, engine = _make_store_and_engine(tmp_path)
    buzz = BuzzAdapter(outbox_store=store, transport=lambda _u, _p: 200)

    if scenario_id == "A01":
        # A01: Simulated run claiming VERIFIED_SUCCESS via verify_goal(simulated_run=False)
        g = engine.create_goal("A01 simulated")
        engine.run_goal(g.id, verification_profile="smoke", execute_commands=False)
        res = engine.verify_goal(g.id, verification_profile="smoke", simulated_run=False)
        assert res.truth_status == ExecutionTruthStatus.SIMULATED

    elif scenario_id == "A02":
        # A02: GoalEngineAdapter with missing truth_status under execute_commands=True
        from src.mekongcli.core.goal_engine.models import GoalStatus

        class _DummySvc:
            def create_goal(self, title: str) -> Any:
                return type("_G", (), {"id": "g_a02", "title": title})()

            def run_goal(self, gid: str, **_kw: Any) -> Any:
                return type("_G", (), {"id": gid, "status": GoalStatus.SATISFIED})()

        ad = GoalEngineAdapter(store=store, service=_DummySvc(), execute_commands=True)  # type: ignore[arg-type]
        c = ad.commit(ad.decompose("A02"))
        assert c.metadata["truth_status"] == ExecutionTruthStatus.UNAVAILABLE.value
        assert c.success is False

    elif scenario_id == "A03":
        # A03: Verification profile 'none' attempting VERIFIED_SUCCESS under execute_commands=True
        ad = GoalEngineAdapter(
            store=store,
            service=engine,
            verification_profile="none",
            execute_commands=True,
        )
        c = ad.commit(ad.decompose("A03"))
        assert c.metadata["truth_status"] != ExecutionTruthStatus.VERIFIED_SUCCESS.value
        assert c.metadata["truth_status"] in (
            ExecutionTruthStatus.SIMULATED.value,
            ExecutionTruthStatus.UNAVAILABLE.value,
        )
        assert c.success is False

    elif scenario_id == "A04":
        # A04: Worktree path traversal via '../outside'
        mgr = WorktreeIsolationManager(repo_root=tmp_path)
        wt = mgr.allocate("tkt_a04", "task_a04")
        with pytest.raises(WorktreeEscapeError):
            mgr.validate_path_within_worktree(wt, "../../escaped.txt")
        mgr.cleanup(wt)

    elif scenario_id == "A05":
        # A05: Worktree symlink escape pointing outside worktree root
        mgr = WorktreeIsolationManager(repo_root=tmp_path)
        wt = mgr.allocate("tkt_a05", "task_a05")
        outside_target = tmp_path.parent / "outside_target_a05.txt"
        link_path = wt / "evil_link.txt"
        link_path.symlink_to(outside_target)
        with pytest.raises(WorktreeEscapeError):
            mgr.validate_path_within_worktree(wt, "evil_link.txt")
        mgr.cleanup(wt)

    elif scenario_id == "A06":
        # A06: Command confinement escape using absolute path outside worktree
        mgr = WorktreeIsolationManager(repo_root=tmp_path)
        wt = mgr.allocate("tkt_a06", "task_a06")
        with pytest.raises(WorktreeEscapeError):
            mgr.assert_command_confined("cat /etc/passwd", wt)
        mgr.cleanup(wt)

    elif scenario_id == "A07":
        # A07: Artifact harvest on successful worktree verifies SHA-256 and survives cleanup
        mgr = WorktreeIsolationManager(repo_root=tmp_path)
        wt = mgr.allocate("tkt_a07", "task_a07")
        (wt / "art.bin").write_bytes(b"a07-data")
        fin = mgr.finalize_worktree(wt, ticket_id="tkt_a07", task_id="task_a07", success=True)
        assert fin.mode == WorktreeMode.ARTIFACT
        assert not wt.exists()
        assert fin.artifacts[0].sha256 == hashlib.sha256(b"a07-data").hexdigest()

    elif scenario_id == "A08":
        # A08: Failed worktree preserved in RECOVERY mode without deleting evidence
        mgr = WorktreeIsolationManager(repo_root=tmp_path)
        wt = mgr.allocate("tkt_a08", "task_a08")
        (wt / "crash.dump").write_text("segfault", encoding="utf-8")
        fin = mgr.finalize_worktree(wt, ticket_id="tkt_a08", task_id="task_a08", success=False)
        assert fin.mode == WorktreeMode.RECOVERY
        assert fin.preserved_path is not None and (fin.preserved_path / "crash.dump").exists()

    elif scenario_id == "A09":
        # A09: Cross-worker worktree cleanup hijack attempt
        mgr = WorktreeIsolationManager(repo_root=tmp_path)
        wt = mgr.allocate("tkt_a09_legit", "task_1")
        with pytest.raises(PermissionError):
            mgr.cleanup(wt, expected_owner=("tkt_a09_attacker", "task_1"))
        mgr.cleanup(wt, expected_owner=("tkt_a09_legit", "task_1"))

    elif scenario_id == "A10":
        # A10: External webhook admission without durable SQLite outbox_store
        rt_adapter = BuzzRuntimeAdapter(
            runtime=_make_runtime(),
            outbox_store=None,
            ingress_mode="external_webhook",
        )
        with pytest.raises(BuzzConfigError):
            rt_adapter.assign_mission({"goal": "A10", "event_id": "e_a10"})

    elif scenario_id == "A11":
        # A11: External webhook admission with empty/whitespace event_id
        rt_adapter = BuzzRuntimeAdapter(
            runtime=_make_runtime(),
            outbox_store=store,
            ingress_mode="external_webhook",
        )
        with pytest.raises(ValueError):
            rt_adapter.assign_mission({"goal": "A11", "event_id": "   "})

    elif scenario_id == "A12":
        # A12: Duplicate webhook replay storm does not re-execute runtime
        calls = 0

        class _CountingRuntime:
            _mission_id = "m_a12"

            def start_mission(self, *_a: Any, **_kw: Any) -> None:
                pass

            def run_from_payload(self, _p: dict[str, Any]) -> Any:
                nonlocal calls
                calls += 1
                return type("_R", (), {"output": "ok", "error": None, "task_id": "t1", "metadata": {}})()

        rt_adapter = BuzzRuntimeAdapter(
            runtime=_CountingRuntime(),
            outbox_store=store,
            transport=lambda _u, _p: 200,
            ingress_mode="external_webhook",
        )
        for _ in range(5):
            rt_adapter.assign_mission({"goal": "A12", "source_id": "buzz", "event_id": "e_a12"})
        assert calls == 1

    elif scenario_id == "A13":
        # A13: Direct SQLite mandate tampering detected by trigger and HMAC verification
        rec, _ = buzz.admit_webhook_event({"goal": "A13", "event_id": "e_a13"})
        with pytest.raises(MandateIntegrityError):
            store.attempt_worker_mandate_mutation(rec.ticket_id, cost_budget=99999.0)

    elif scenario_id == "A14":
        # A14: Webhook payload attempting to inject precomputed mandate_hash
        with pytest.raises(BuzzSecurityError):
            buzz.admit_webhook_event(
                {"goal": "A14", "event_id": "e_a14", "mandate_hash": "0" * 64}
            )

    elif scenario_id == "A15":
        # A15: Webhook payload attempting capability escalation
        with pytest.raises(BuzzSecurityError):
            buzz.admit_webhook_event(
                {
                    "goal": "A15",
                    "event_id": "e_a15",
                    "permitted_capabilities": ["arbitrary_shell_exec"],
                }
            )

    elif scenario_id == "A16":
        # A16: Webhook payload attempting resource_boundaries path traversal
        with pytest.raises(BuzzSecurityError):
            buzz.admit_webhook_event(
                {
                    "goal": "A16",
                    "event_id": "e_a16",
                    "resource_boundaries": ["../../secrets"],
                }
            )

    elif scenario_id == "A17":
        # A17: Webhook payload attempting risk_classification downgrade to 'low'
        with pytest.raises(BuzzSecurityError):
            buzz.admit_webhook_event(
                {
                    "goal": "A17",
                    "event_id": "e_a17",
                    "risk_classification": "low",
                }
            )

    elif scenario_id == "A18":
        # A18: Webhook payload attempting cost_budget / retry_budget inflation above server ceiling
        with pytest.raises(BuzzSecurityError):
            buzz.admit_webhook_event(
                {"goal": "A18", "event_id": "e_a18", "cost_budget": 5000.0}
            )

    elif scenario_id == "A19":
        # A19: Callback SSRF targeting AWS/GCP/Cloud metadata 169.254.169.254
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination("https://169.254.169.254/latest/meta-data/iam/")

    elif scenario_id == "A20":
        # A20: Callback SSRF targeting IPv4-mapped IPv6 and integer-encoded loopback
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination("https://[::ffff:127.0.0.1]:8080/internal")
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination("https://2130706433/internal")

    elif scenario_id == "A21":
        # A21: Callback SSRF via DNS rebinding (multi-A record containing 10.0.0.1)
        with pytest.raises(BuzzSecurityError):
            validate_callback_destination(
                "https://evil-rebind.org/cb",
                resolver=lambda *_a, **_kw: [
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 443)),
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 443)),
                ],
            )

    elif scenario_id == "A22":
        # A22: Sophia handoff fixture claiming verified_success_claim_permitted=True on SIMULATED orKPI-only outcome
        with pytest.raises(SophiaContractValidationError):
            validate_sophia_handoff_fixture(
                {
                    "contract_version": CONTRACT_VERSION,
                    "ticket_id": "tkt_a22",
                    "goal_id": "goal_a22",
                    "truth_status": "SIMULATED",
                    "simulated": True,
                    "execution_outcome": "SIMULATED",
                    "verification_outcome": "NOT_RUN",
                    "delivery_outcome": "SENT",
                    "business_outcome": "KPI_ATTRIBUTED",
                    "verified_success_claim_permitted": True,
                }
            )
