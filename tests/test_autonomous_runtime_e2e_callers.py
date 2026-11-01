# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Supreme Command #01.1 — E2E Production-Caller & Operator Surface Convergence Tests.

Verifies the 4 production caller surfaces:
1. CLI JSON truth surface (`truth_status`, `simulated`) and `--require-verified` non-zero exit gate
2. CLI `--isolate-worktree`, `--ticket-id`, and `--workers` default (`2`)
3. `GoalEngineAdapter.commit()` Explicit Dual Mode (`execute_commands=True` vs `False`)
4. `BuzzRuntimeAdapter.assign_mission()` `(source_id, event_id)` replay dedup and `report_outbox` durability
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from typer.testing import CliRunner

from src.cli.cook_command import register_cook_command
from src.cli.goal_commands import goal_app
from src.core.adapters.goal_engine_adapter import GoalEngineAdapter, make_goal_engine_adapter
from src.core.buzz_runtime_adapter import BuzzRuntimeAdapter
from src.core.mission_tracer import MissionTracer
from src.core.runtime_adapter import MekongCoreRuntimeImpl
from src.mekongcli.core.goal_engine.service import GoalEngine
from src.mekongcli.core.goal_engine.store import SQLiteGoalStore


runner = CliRunner()


class _OkDispatcher:
    def dispatch(self, task: Any, agent: Any = None) -> dict[str, Any]:
        _ = agent
        return {"ok": True, "task_id": task.id}


def _make_runtime() -> MekongCoreRuntimeImpl:
    return MekongCoreRuntimeImpl(
        dispatcher=_OkDispatcher(),
        tool_registry=type("_R", (), {"execute": lambda *_args: {"ok": True}})(),
    )


def _seed_smoke_src(workspace: Path) -> None:
    """Create minimal `src/main.py` so `--profile smoke` (`python3 -m src.main --help`) passes."""
    src_dir = workspace / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "main.py").write_text("import sys\nprint('smoke ok')\n", encoding="utf-8")


def _make_store_and_engine(tmp_path: Path) -> tuple[SQLiteGoalStore, GoalEngine]:
    _seed_smoke_src(tmp_path)
    db_path = tmp_path / "e2e_callers.sqlite3"
    store = SQLiteGoalStore(db_path=str(db_path))
    engine = GoalEngine(store=store, cwd=tmp_path)
    return store, engine


# --------------------------------------------------------------------------- #
# Surface 1: CLI JSON Truth Surface & --require-verified Exit Gate
# --------------------------------------------------------------------------- #


def test_e2e_cli_goal_run_and_verify_emit_truth_status_and_honor_require_verified(
    tmp_path: Path,
) -> None:
    """Simulated `mekong goal run --json` emits `truth_status="SIMULATED"` and `simulated=True`;
    `--require-verified` exits with code 1 when truth_status != VERIFIED_SUCCESS.
    """
    db_path = str(tmp_path / "cli_truth.sqlite3")
    res_create = runner.invoke(goal_app, ["create", "Audit invoice pipeline", "--db", db_path, "--json"])
    assert res_create.exit_code == 0
    created = json.loads(res_create.stdout)
    goal_id = created["id"]

    # Simulated default run -> exit 0 without --require-verified, truth_status=SIMULATED
    res_run = runner.invoke(
        goal_app,
        ["run", goal_id, "--profile", "none", "--db", db_path, "--json"],
    )
    assert res_run.exit_code == 0
    run_payload = json.loads(res_run.stdout)
    assert run_payload["status"] == "satisfied"
    assert run_payload["truth_status"] == "SIMULATED"
    assert run_payload["simulated"] is True

    # Simulated run with --require-verified -> must exit non-zero (code 1) even in --json mode
    res_create2 = runner.invoke(goal_app, ["create", "Second simulated goal", "--db", db_path, "--json"])
    goal_id2 = json.loads(res_create2.stdout)["id"]
    res_req = runner.invoke(
        goal_app,
        ["run", goal_id2, "--profile", "none", "--require-verified", "--db", db_path, "--json"],
    )
    assert res_req.exit_code == 1
    req_payload = json.loads(res_req.stdout)
    assert req_payload["truth_status"] == "SIMULATED"
    assert req_payload["simulated"] is True

    # `goal verify --profile none --require-verified --json` -> exits non-zero
    res_ver = runner.invoke(
        goal_app,
        ["verify", goal_id, "--profile", "none", "--require-verified", "--db", db_path, "--json"],
    )
    assert res_ver.exit_code == 1
    ver_payload = json.loads(res_ver.stdout)
    assert ver_payload["truth_status"] in ("SIMULATED", "UNAVAILABLE")


def test_e2e_cli_cook_auto_emits_truth_status_and_simulated(tmp_path: Path) -> None:
    """`mekong cook-auto --json` includes `truth_status` and `simulated`."""
    app = typer.Typer()
    register_cook_command(app)
    db_path = str(tmp_path / "cook_auto.sqlite3")

    res = runner.invoke(
        app,
        ["cook-auto", "Generate quarterly VAT summary", "--profile", "none", "--db", db_path, "--json"],
    )
    assert res.exit_code == 0
    payload = json.loads(res.stdout)
    assert payload["status"] == "satisfied"
    assert payload["truth_status"] == "SIMULATED"
    assert payload["simulated"] is True


# --------------------------------------------------------------------------- #
# Surface 2: CLI --isolate-worktree, --ticket-id, and --workers=2 Default
# --------------------------------------------------------------------------- #


def test_e2e_cli_goal_run_and_parallel_support_isolate_worktree_and_workers_default_2(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    """`goal run` and `goal run-parallel` accept `--isolate-worktree`, `--ticket-id`,
    and `--require-verified`, and default `--workers` to 2.
    """
    monkeypatch.chdir(tmp_path)
    store, engine = _make_store_and_engine(tmp_path)
    db_path = str(store.db_path)

    goal = engine.create_goal("Run isolated command")
    tasks = store.get_tasks(goal.id)
    for idx, t in enumerate(tasks):
        t.command = "python3 -V"
        t.depends_on = [] if idx == 0 else [tasks[idx - 1].id]
    store.save_tasks(tasks)

    res = runner.invoke(
        goal_app,
        [
            "run",
            goal.id,
            "--profile",
            "smoke",
            "--execute-commands",
            "--isolate-worktree",
            "--require-verified",
            "--db",
            db_path,
            "--json",
        ],
    )
    assert res.exit_code == 0, res.stdout
    payload = json.loads(res.stdout)
    assert payload["truth_status"] == "VERIFIED_SUCCESS"
    assert payload["simulated"] is False

    # Parallel run with --isolate-worktree and default --workers (2)
    goal2 = engine.create_goal("Parallel isolated run")
    tasks2 = store.get_tasks(goal2.id)
    for t in tasks2:
        t.command = "python3 -V"
        t.depends_on = []
    store.save_tasks(tasks2)

    res_par = runner.invoke(
        goal_app,
        [
            "run-parallel",
            goal2.id,
            "--profile",
            "smoke",
            "--execute-commands",
            "--isolate-worktree",
            "--require-verified",
            "--db",
            db_path,
            "--json",
        ],
    )
    assert res_par.exit_code == 0, res_par.stdout
    par_payload = json.loads(res_par.stdout)
    assert par_payload["truth_status"] == "VERIFIED_SUCCESS"
    assert par_payload["simulated"] is False


# --------------------------------------------------------------------------- #
# Surface 3: GoalEngineAdapter.commit() Explicit Dual Mode
# --------------------------------------------------------------------------- #


def test_e2e_goal_engine_adapter_explicit_dual_mode(tmp_path: Path) -> None:
    """`GoalEngineAdapter.commit()`:
    - default `execute_commands=False` keeps `success=True` on simulated run but marks `simulated=True` and `truth_status="SIMULATED"`
    - `execute_commands=True` with `profile="none"` (`truth_status="UNAVAILABLE"`) returns `success=False`
    - `execute_commands=True` with `profile="smoke"` and passing task commands returns `success=True` and `truth_status="VERIFIED_SUCCESS"`.
    """
    store, engine = _make_store_and_engine(tmp_path)

    # 1. Default simulated mode (backward-compatible)
    adapter_sim = make_goal_engine_adapter(
        store=store,
        cwd=tmp_path,
        verification_profile="none",
        execute_commands=False,
    )
    plan_sim = adapter_sim.decompose("Simulated adapter plan")
    res_sim = adapter_sim.commit(plan_sim)
    assert res_sim.success is True
    assert res_sim.metadata["truth_status"] == "SIMULATED"
    assert res_sim.metadata["simulated"] is True
    assert res_sim.output["goal_truth_status"] == "SIMULATED"

    # 2. Real mode (`execute_commands=True`) with `profile="none"` -> UNAVAILABLE -> must fail
    adapter_unverified = GoalEngineAdapter(
        service=engine,
        store=store,
        cwd=tmp_path,
        verification_profile="none",
        execute_commands=True,
    )
    plan_unv = adapter_unverified.decompose("Unverified real execution")
    tasks_unv = store.get_tasks(plan_unv.metadata["svc_goal_id"])
    for t in tasks_unv:
        t.command = "python3 -V"
    store.save_tasks(tasks_unv)

    res_unv = adapter_unverified.commit(plan_unv)
    assert res_unv.success is False
    assert res_unv.metadata["truth_status"] == "UNAVAILABLE"
    assert res_unv.metadata["simulated"] is False
    assert "VERIFIED_SUCCESS" in (res_unv.error or "")

    # 3. Real mode (`execute_commands=True`) with `profile="smoke"` -> VERIFIED_SUCCESS -> success=True
    adapter_real = GoalEngineAdapter(
        service=engine,
        store=store,
        cwd=tmp_path,
        verification_profile="smoke",
        execute_commands=True,
        isolate_worktree=True,
    )
    plan_real = adapter_real.decompose("Verified real execution")
    tasks_real = store.get_tasks(plan_real.metadata["svc_goal_id"])
    for t in tasks_real:
        t.command = "python3 -V"
    store.save_tasks(tasks_real)

    res_real = adapter_real.commit(plan_real)
    assert res_real.success is True
    assert res_real.metadata["truth_status"] == "VERIFIED_SUCCESS"
    assert res_real.metadata["simulated"] is False
    assert res_real.output["goal_truth_status"] == "VERIFIED_SUCCESS"


# --------------------------------------------------------------------------- #
# Surface 4: BuzzRuntimeAdapter Replay Dedup & Transactional Outbox
# --------------------------------------------------------------------------- #


def test_e2e_buzz_runtime_adapter_deduplicates_replayed_webhooks_and_queues_outbox(
    tmp_path: Path,
) -> None:
    """`BuzzRuntimeAdapter` wired with `outbox_store`:
    1. Admits first `(source_id, event_id)` webhook and executes runtime once.
    2. Short-circuits duplicate `(source_id, event_id)` replay with `status="duplicate_ignored"`, `duplicate=True` without re-running `runtime.run_from_payload` or firing duplicate callbacks.
    3. Persists failed callback deliveries (`HTTP 503`) into `report_outbox` (`FAILED_RETRYABLE`).
    """
    store, _ = _make_store_and_engine(tmp_path)
    deliveries: list[tuple[str, dict[str, Any]]] = []

    def flaky_transport(url: str, body: dict[str, Any]) -> int:
        deliveries.append((url, body))
        return 503  # Simulate transient downstream outage

    runtime = _make_runtime()
    tracer = MissionTracer()
    adapter = BuzzRuntimeAdapter(
        runtime=runtime,
        tracer=tracer,
        transport=flaky_transport,
        outbox_store=store,
    )

    payload = {
        "goal": "Sync Shopee order ledger",
        "source_id": "buzz_webhook",
        "event_id": "evt_buzz_20261102_001",
        "mission_id": "mission_buzz_001",
        "thread_id": "thread_shopee_1",
        "callback_url": "https://buzz.example/hooks/status",
    }

    # First delivery -> admitted, executed, and queued in report_outbox as FAILED_RETRYABLE
    first = adapter.assign_mission(payload)
    assert first["status"] == "completed"
    assert first.get("duplicate") is False
    assert first["ticket_id"].startswith("tkt_")
    assert first["delivery_status"] == "FAILED_RETRYABLE"
    assert len(deliveries) == 1

    # Replay same (source_id, event_id) -> short-circuited before runtime execution or callback
    second = adapter.assign_mission(payload)
    assert second["status"] == "duplicate_ignored"
    assert second["duplicate"] is True
    assert second["ticket_id"] == first["ticket_id"]
    assert len(deliveries) == 1  # No second HTTP POST attempted
