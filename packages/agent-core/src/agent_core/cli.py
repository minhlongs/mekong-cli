"""Typer CLI — `agent-core run "<goal>"` orchestrates CEO → Developer."""

from __future__ import annotations

import json
import logging
import os
import sys

import typer

from agent_core import __version__
from agent_core.agents.ceo import CEOAgent
from agent_core.agents.developer import DeveloperAgent
from agent_core.feedback_loop import FeedbackLoop, list_recent_sessions
from agent_core.forest_client import fetch_forest_status
from agent_core.formatters import (
    breakdown_from_signals,
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
    try:
        if source == "all":
            by_model = llm.get_signals_breakdown(hours=window)
        else:
            # Fetch recent signals and tabulate locally — mekongd /breakdown
            # has no source-filter parameter yet.
            recent = llm.get_recent_signals(limit=500)
            by_model = breakdown_from_signals(recent, source=source)
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
def status_cmd() -> None:
    """In ra snapshot ops: memory root, retention, số row theo agent_id, lần chạy cuối."""
    memory = SeedMemory()
    typer.echo(
        format_status(
            agent_rows=memory.agent_counts(),
            last_session_at=memory.last_created_at("feedback_session"),
            retention_env=os.environ.get("AGENT_CORE_SESSION_RETENTION"),
            memory_root=str(memory.root),
        )
    )


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


if __name__ == "__main__":  # pragma: no cover
    app()
