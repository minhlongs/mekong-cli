"""Typer CLI — `agent-core run "<goal>"` orchestrates CEO → Developer."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

import typer

from agent_core import __version__
from agent_core.agents.ceo import CEOAgent
from agent_core.agents.developer import DeveloperAgent
from agent_core.evals import (
    EvalRunSummary,
    dataset_hash,
    detect_regression,
    load_dataset,
    run_dataset,
)
from agent_core.experiments import bucket
from agent_core.feedback_loop import FeedbackLoop, list_recent_sessions
from agent_core.forest_client import fetch_forest_status
from agent_core.formatters import (
    format_breakdown,
    format_cost_by_model,
    format_forest_status,
    format_history,
    format_recent_notes,
    format_status,
)
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory
from agent_core.orchestrator import SoloCompanyOrchestrator
from agent_core.tools.file_system import write_file


class _OfflineLLM:
    """Deterministic stub — returns '[offline] <prompt>' without any network call.

    Used by ``agent-core eval`` when the dataset fixture is designed for offline
    testing (expect_substring contains 'offline' or '[offline]').
    """

    def chat(self, messages: list, system: str | None = None, max_tokens: int = 1024) -> str:
        prompt = ""
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user":
                prompt = m.get("content", "")
                break
        return f"[offline] {prompt}"

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback()
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    if version:
        typer.echo(f"agent-core {__version__}")
        raise typer.Exit(code=0)
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit(code=0)


@app.command("run")
def run_cmd(
    goal: str = typer.Argument(..., help="Mục tiêu bạn muốn giao cho công ty AI."),
    mekongd_url: str = typer.Option(
        None, "--mekongd-url", help="Override mekongd base URL (default: env MEKONGD_URL)."
    ),
    model: str = typer.Option(None, "--model", help="Override LLM model."),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    signal: bool = typer.Option(
        False,
        "--signal",
        help="Prompt good/bad after run. Default off; env AGENT_CORE_PROMPT_SIGNAL=1 also enables.",
    ),
) -> None:
    """CEO plans → Developer executes the first actionable step."""
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)
    kwargs: dict = {}
    if mekongd_url:
        kwargs["base_url"] = mekongd_url
    if model:
        kwargs["model"] = model
    llm = LLMClient(**kwargs)
    memory = SeedMemory()
    ceo = CEOAgent(llm=llm, memory=memory)
    dev = DeveloperAgent(llm=llm, memory=memory)

    typer.echo("CEO đang lập kế hoạch...")
    plan = ceo.plan(goal)
    typer.echo(f"\n--- Kế hoạch ---\n{plan}\n")

    typer.echo("Developer đang thực thi bước đầu tiên...")
    result = dev.execute(
        task=f"Thực hiện bước đầu tiên trong kế hoạch: {goal}",
        plan_context=plan,
    )
    typer.echo(f"\n--- Kết quả ---\n{result}\n")

    artifact = _maybe_write_artifact(result)
    if artifact:
        typer.echo(f"Đã lưu artifact vào: {artifact}")

    enabled = signal or os.environ.get("AGENT_CORE_PROMPT_SIGNAL") == "1"
    _maybe_prompt_signal(llm, enabled)


@app.command("report")
def report_cmd(
    mekongd_url: str = typer.Option(
        None, "--mekongd-url", help="Override mekongd base URL (default: env MEKONGD_URL)."
    ),
    hours: int = typer.Option(
        0, "--hours", help="Limit breakdown to last N hours (0 = all time)."
    ),
    notes: int = typer.Option(
        0, "--notes", help="Append last N signal notes to output (0 = none)."
    ),
    cost: bool = typer.Option(
        False, "--cost", help="Append cloud cost breakdown by model."
    ),
    source: str = typer.Option(
        "all",
        "--source",
        help="Filter signals by origin: all | auto (worker) | user (feedback endpoint).",
    ),
) -> None:
    """Show good/bad signal breakdown by model as a human-friendly table."""
    if source not in {"all", "auto", "user"}:
        typer.echo(
            f"--source must be one of all|auto|user, got {source!r}", err=True
        )
        raise typer.Exit(code=2)
    kwargs: dict = {"base_url": mekongd_url} if mekongd_url else {}
    llm = LLMClient(**kwargs)
    window = hours if hours > 0 else None
    server_source = source if source in ("auto", "user") else None
    try:
        by_model = llm.get_signals_breakdown(hours=window, source=server_source)
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Lỗi khi gọi mekongd: {e}", err=True)
        raise typer.Exit(code=2) from e
    src_label = "" if source == "all" else f" [source={source}]"
    label = f" (last {hours}h)" if window else ""
    typer.echo(f"Signal breakdown{label}{src_label}:")
    typer.echo(format_breakdown(by_model))
    if notes > 0:
        try:
            recent = llm.get_recent_signals(limit=notes)
        except Exception as e:  # noqa: BLE001
            typer.echo(f"Lỗi khi lấy notes: {e}", err=True)
            return
        typer.echo(format_recent_notes(recent))
    if cost:
        try:
            by_cost = llm.get_cost_by_model(hours=window)
        except Exception as e:  # noqa: BLE001
            typer.echo(f"Lỗi khi lấy cost: {e}", err=True)
            return
        typer.echo(format_cost_by_model(by_cost, window))


@app.command("orchestrate")
def orchestrate_cmd(
    goal: str = typer.Argument(..., help="Mục tiêu giao cho công ty AI."),
    mekongd_url: str = typer.Option(
        None, "--mekongd-url", help="Override mekongd base URL (default: env MEKONGD_URL)."
    ),
    model: str = typer.Option(None, "--model", help="Override LLM model."),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    rounds: int = typer.Option(
        1,
        "--rounds",
        "-r",
        help="Số vòng feedback loop (>=2 bật Ops+Analyst+retry). 1 = single pass.",
    ),
) -> None:
    """CEO → Developer → Tester → Reviewer [→ Ops + Analyst retry if rounds>1]."""
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)
    kwargs: dict = {}
    if mekongd_url:
        kwargs["base_url"] = mekongd_url
    if model:
        kwargs["model"] = model
    llm = LLMClient(**kwargs)
    memory = SeedMemory()

    if rounds <= 1:
        orch = SoloCompanyOrchestrator(llm=llm, memory=memory)
        typer.echo("Orchestrator khởi động: CEO → Developer → Tester → Reviewer")
        report = orch.process_goal(goal)
        _print_report(report)
        artifact = _maybe_write_artifact(report.artifact)
        if artifact:
            typer.echo(f"\nĐã lưu artifact vào: {artifact}")
        return

    loop = FeedbackLoop(llm=llm, memory=memory)
    typer.echo(
        f"FeedbackLoop khởi động: tối đa {rounds} vòng "
        "(CEO → Dev → Tester → Reviewer → Ops → Analyst)"
    )
    session = loop.process_goal(goal, max_rounds=rounds)
    for round_ in session.rounds:
        typer.echo(f"\n===== Vòng {round_.round_index} =====")
        _print_report(round_.report)
        typer.echo(
            f"Ops: healthy={round_.ops['healthy']} "
            f"severity={round_.ops['severity']} alerts={round_.ops['alerts']}"
        )
        typer.echo(
            f"Analyst: trend={round_.analyst['trend']} "
            f"summary={round_.analyst['summary']}"
        )
        for rec in round_.analyst["recommendations"]:
            typer.echo(f"  • {rec}")
    artifact = _maybe_write_artifact(session.final.artifact)
    if artifact:
        typer.echo(f"\nĐã lưu artifact vào: {artifact}")


def _print_report(report) -> None:
    typer.echo(f"--- Kế hoạch (CEO) ---\n{report.plan}\n")
    typer.echo(f"--- Artifact (Developer) ---\n{report.artifact[:2000]}\n")
    typer.echo(
        f"--- Tester ({report.test['status'].upper()}) ---\n"
        f"{report.test['summary']}"
    )
    for issue in report.test["issues"]:
        typer.echo(f"  - {issue}")
    typer.echo(
        f"--- Reviewer ({report.review['verdict'].upper()} "
        f"score={report.review['score']}/10) ---"
    )
    for note in report.review["notes"]:
        typer.echo(f"  - {note}")


@app.command("history")
def history_cmd(
    limit: int = typer.Option(
        10, "--limit", "-n", help="Số round gần nhất hiển thị (mặc định 10)."
    ),
    as_json: bool = typer.Option(
        False, "--json", help="In ra JSON thô thay vì bảng."
    ),
) -> None:
    """Hiển thị các vòng feedback đã persist trong SeedMemory."""
    memory = SeedMemory()
    rows = list_recent_sessions(memory, limit=max(1, limit))
    if as_json:
        typer.echo(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    typer.echo(format_history(rows))


@app.command("forest-status")
def forest_status_cmd(
    url: str = typer.Option(
        "http://localhost:8000",
        "--url",
        "-u",
        help="Base URL của agent-forest gateway (mặc định localhost:8000).",
    ),
    timeout: float = typer.Option(
        5.0, "--timeout", help="Timeout HTTP tính bằng giây (mặc định 5)."
    ),
    as_json: bool = typer.Option(
        False, "--json", help="In ra JSON thô (cho monitoring/script) thay vì bảng."
    ),
) -> None:
    """Gọi /healthz + /metrics trên agent-forest gateway và in snapshot."""
    data = fetch_forest_status(url, timeout=timeout)
    if as_json:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return
    typer.echo(format_forest_status(data))


@app.command("status")
def status_cmd(
    as_json: bool = typer.Option(
        False, "--json", help="In JSON thô (cho monitoring/script) thay vì bảng text."
    ),
) -> None:
    """In ra snapshot ops: memory root, retention, số row theo agent_id, lần chạy cuối."""
    memory = SeedMemory()
    agent_rows = memory.agent_counts()
    last_session_at = memory.last_created_at("feedback_session")
    retention_env = os.environ.get("AGENT_CORE_SESSION_RETENTION")
    if as_json:
        payload = {
            "memory_root": str(memory.root),
            "retention_env": retention_env,
            "last_session_at": last_session_at,
            "agent_rows": agent_rows,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    typer.echo(
        format_status(
            agent_rows=agent_rows,
            last_session_at=last_session_at,
            retention_env=retention_env,
            memory_root=str(memory.root),
        )
    )


@app.command("doctor")
def doctor_cmd(
    mekongd_url: str | None = typer.Option(
        None, "--mekongd-url", help="Override mekongd base URL (default: env MEKONGD_URL)."
    ),
    forest_url: str = typer.Option(
        "http://localhost:8000",
        "--forest-url",
        help="Base URL của agent-forest gateway (mặc định localhost:8000).",
    ),
    timeout: float = typer.Option(3.0, "--timeout", help="HTTP timeout giây (mặc định 3)."),
    as_json: bool = typer.Option(
        False, "--json", help="In JSON thô (cho monitoring/script) thay vì bảng text."
    ),
) -> None:
    """Self-check env + memory + mekongd/forest connectivity.

    Holistic operator triage: dumps env flags, memory stats, pings both
    services /healthz, prints package + Python versions in one shot.
    Never raises — returns exit 0 even on probe failures (informational only).
    """
    import httpx

    memory = SeedMemory()
    counts = memory.agent_counts()
    total_rows = sum(counts.values())
    mekongd_target = mekongd_url or os.environ.get("MEKONGD_URL") or "(unset)"
    retention_env = os.environ.get("AGENT_CORE_SESSION_RETENTION", "(unset)")
    outputs_env = os.environ.get("AGENT_CORE_OUTPUTS", "(unset)")
    prompt_env = os.environ.get("AGENT_CORE_PROMPT_SIGNAL", "(unset)")

    def _ping(url: str) -> str:
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.get(f"{url.rstrip('/')}/healthz")
            return f"OK (HTTP {resp.status_code})"
        except Exception as exc:  # noqa: BLE001 — informational probe
            return f"FAIL ({type(exc).__name__})"

    mekongd_status = _ping(mekongd_url or os.environ.get("MEKONGD_URL") or "") \
        if (mekongd_url or os.environ.get("MEKONGD_URL")) else "(skipped — no URL)"
    forest_status = _ping(forest_url)

    if as_json:
        payload = {
            "env": {
                "MEKONGD_URL": mekongd_target,
                "AGENT_CORE_SESSION_RETENTION": retention_env,
                "AGENT_CORE_OUTPUTS": outputs_env,
                "AGENT_CORE_PROMPT_SIGNAL": prompt_env,
            },
            "memory": {
                "root": str(memory.root),
                "agents": len(counts),
                "total_rows": total_rows,
            },
            "connectivity": {
                "mekongd": mekongd_status,
                "agent_forest": forest_status,
            },
            "package": {
                "agent_core": __version__,
                "python": sys.version.split()[0],
            },
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    lines = [
        "agent-core doctor",
        "",
        "[env]",
        f"  MEKONGD_URL                  : {mekongd_target}",
        f"  AGENT_CORE_SESSION_RETENTION : {retention_env}",
        f"  AGENT_CORE_OUTPUTS           : {outputs_env}",
        f"  AGENT_CORE_PROMPT_SIGNAL     : {prompt_env}",
        "",
        "[memory]",
        f"  root      : {memory.root}",
        f"  agents    : {len(counts)}",
        f"  total rows: {total_rows}",
        "",
        "[connectivity]",
        f"  mekongd /healthz     : {mekongd_status}",
        f"  agent-forest /healthz: {forest_status}",
        "",
        "[package]",
        f"  agent-core: {__version__}",
        f"  python    : {sys.version.split()[0]}",
    ]
    typer.echo("\n".join(lines))


@app.command("prune")
def prune_cmd(
    keep: int = typer.Option(
        100, "--keep", "-k", help="Số row mới nhất giữ lại (>=0). Mặc định 100."
    ),
    prune_all: bool = typer.Option(
        False,
        "--all",
        help="Áp dụng cho MỌI agent_id (CEO, Developer, Tester, ...). "
        "Mặc định chỉ xoá feedback_session.",
    ),
) -> None:
    """Xoá các row cũ trong SeedMemory, giữ lại N row mới nhất.

    Mặc định chỉ áp dụng cho agent_id=feedback_session. Dùng ``--all`` để
    gom cả các agent role khác (memory của CEO/Developer/Tester/Reviewer
    cũng grow unbounded nếu không được prune).
    """
    if keep < 0:
        typer.echo("keep phải >= 0", err=True)
        raise typer.Exit(code=2)
    memory = SeedMemory()
    if not prune_all:
        deleted = memory.prune_agent("feedback_session", keep_last_n=keep)
        typer.echo(f"Đã xoá {deleted} row cũ của feedback_session, giữ lại {keep} gần nhất.")
        return
    counts = memory.agent_counts()
    if not counts:
        typer.echo("Memory đang trống, không có gì để xoá.")
        return
    total = 0
    for agent_id in counts:
        total += memory.prune_agent(agent_id, keep_last_n=keep)
    typer.echo(
        f"Đã xoá {total} row cũ trên {len(counts)} agent_id, giữ lại {keep} gần nhất mỗi agent."
    )


@app.command("signal")
def signal_cmd(
    kind: str = typer.Argument(..., help="good|bad — operator feedback on last response."),
    note: str = typer.Argument("", help="Optional free-text note (≤500 chars)."),
    mekongd_url: str = typer.Option(
        None, "--mekongd-url", help="Override mekongd base URL (default: env MEKONGD_URL)."
    ),
) -> None:
    """Send a Pillar 3 feedback signal to mekongd /v1/signals."""
    kwargs: dict = {"base_url": mekongd_url} if mekongd_url else {}
    llm = LLMClient(**kwargs)
    try:
        resp = llm.send_signal(kind, note)
    except ValueError as e:
        typer.echo(f"Lỗi: {e}", err=True)
        raise typer.Exit(code=2) from e
    typer.echo(f"Đã gửi signal: {resp}")


def _maybe_prompt_signal(llm: LLMClient, enabled: bool) -> None:
    """Prompt operator for good/bad feedback → mekongd/v1/signals. No-op unless TTY + enabled."""
    if not enabled or not sys.stdin.isatty():
        return
    choice = typer.prompt("Feedback? [g]ood/[b]ad/[s]kip", default="s").strip().lower()
    if not choice or choice[0] not in ("g", "b"):
        return
    kind = "good" if choice[0] == "g" else "bad"
    try:
        llm.send_signal(kind)
        typer.echo(f"Đã gửi signal: {kind}")
    except Exception as e:  # noqa: BLE001
        typer.echo(f"Cảnh báo: gửi signal thất bại ({e}) — bỏ qua.", err=True)


def _maybe_write_artifact(developer_response: str) -> str | None:
    """If the developer replied with {file_path, content} JSON, persist it."""
    start = developer_response.find("{")
    end = developer_response.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        payload = json.loads(developer_response[start : end + 1])
    except json.JSONDecodeError:
        return None
    path = payload.get("file_path")
    content = payload.get("content")
    if not path or content is None:
        return None
    return write_file(path, content)


@app.command("eval")
def eval_cmd(  # noqa: B008
    dataset: Path = typer.Option(  # noqa: B008
        ..., "--dataset", "-d", help="Path to JSON dataset file.", exists=True
    ),
    baseline_run_id: int = typer.Option(  # noqa: B008
        0, "--baseline", help="Run ID to compare against (0 = use latest run for dataset)."
    ),
    as_json: bool = typer.Option(False, "--json", help="Emit structured JSON output for CI."),  # noqa: B008
    offline: bool = typer.Option(  # noqa: B008
        False,
        "--offline",
        help="Use built-in offline stub LLM instead of mekongd (for fixture-based CI testing).",
    ),
    mekongd_url: str = typer.Option(  # noqa: B008
        None, "--mekongd-url", help="Override mekongd base URL (default: env MEKONGD_URL)."
    ),
    threshold: float = typer.Option(  # noqa: B008
        0.05, "--threshold", help="Regression threshold as fraction (default 0.05 = 5%)."
    ),
) -> None:
    """Run offline eval harness against a fixed dataset and detect regressions.

    Exits with code 1 when regressions are detected; 0 when clean.
    """
    with open(dataset, encoding="utf-8") as fh:
        dataset_dict: dict = json.load(fh)

    dataset_name: str = dataset_dict.get("name", dataset.stem)
    d_hash = dataset_hash(dataset_dict)
    cases = load_dataset(dataset)

    llm: object
    if offline:
        llm = _OfflineLLM()
    else:
        kwargs: dict = {"base_url": mekongd_url} if mekongd_url else {}
        llm = LLMClient(**kwargs)

    summary: EvalRunSummary = run_dataset(cases, llm)
    summary.dataset_name = dataset_name

    memory = SeedMemory()

    # Resolve baseline
    baseline_record: dict | None = None
    if baseline_run_id > 0:
        runs = memory.recent_eval_runs(dataset_name, limit=100)
        for r in runs:
            if r["id"] == baseline_run_id:
                baseline_record = r
                break
        if baseline_record is None:
            typer.echo(
                f"Cảnh báo: baseline run_id={baseline_run_id} không tìm thấy — bỏ qua so sánh.",
                err=True,
            )
    else:
        prev_runs = memory.recent_eval_runs(dataset_name, limit=1)
        if prev_runs:
            baseline_record = prev_runs[0]

    # Record current run
    run_id = memory.record_eval_run(
        dataset_name=dataset_name,
        dataset_hash=d_hash,
        score=summary.total_score,
        passed=summary.passed_count,
        total=summary.total_count,
        details=summary.as_record(),
    )

    regressions = detect_regression(summary, baseline_record, threshold_pct=threshold)

    if as_json:
        out = {
            "run_id": run_id,
            "dataset": dataset_name,
            "score_pct": round(summary.score_pct, 4),
            "passed": summary.passed_count,
            "total": summary.total_count,
            "regressions": regressions,
            "cases": [
                {
                    "id": r.case_id,
                    "passed": r.passed,
                    "score": r.score,
                }
                for r in summary.details
            ],
        }
        typer.echo(json.dumps(out, ensure_ascii=False))
        if regressions:
            raise typer.Exit(code=1)
        return

    # Human-readable table
    typer.echo(f"\nEval: {dataset_name}  (run_id={run_id}  hash={d_hash[:12]})")
    typer.echo(f"{'Case':<20} {'Score':>6} {'Pass':>5}")
    typer.echo("-" * 35)
    for r in summary.details:
        mark = "OK" if r.passed else "FAIL"
        typer.echo(f"{r.case_id:<20} {r.score:>6.2f} {mark:>5}")
    typer.echo("-" * 35)
    typer.echo(
        f"{'TOTAL':<20} {summary.total_score:>6.2f} {summary.passed_count}/{summary.total_count}"
    )
    typer.echo(f"Score: {summary.score_pct:.1%}")

    if regressions:
        typer.echo("\n" + "\n".join(regressions), err=True)
        raise typer.Exit(code=1)


@app.command("experiment")
def experiment_cmd(
    user: str = typer.Option(..., "--user", help="User identifier."),
    name: str = typer.Option(..., "--name", help="Experiment name."),
    variants: str = typer.Option(
        "control,treatment",
        "--variants",
        help="Comma-separated variant names (equal weight).",
    ),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output."),
) -> None:
    """Assign user to a variant of an experiment (deterministic hash-based)."""
    variant_list = [v.strip() for v in variants.split(",") if v.strip()]
    try:
        assignment = bucket(user, name, variant_list)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=2) from exc
    if json_out:
        typer.echo(
            json.dumps({"user": user, "experiment": name, "variant": assignment})
        )
    else:
        typer.echo(assignment)


if __name__ == "__main__":  # pragma: no cover
    app()
