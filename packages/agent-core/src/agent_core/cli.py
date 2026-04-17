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
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory
from agent_core.tools.file_system import write_file

app = typer.Typer(add_completion=False, no_args_is_help=True, invoke_without_command=True)


@app.callback()
def _root(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit."),
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
        None,
        "--signal/--no-signal",
        help="Prompt for good/bad feedback after run. Default: env AGENT_CORE_PROMPT_SIGNAL=1.",
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

    enabled = signal if signal is not None else os.environ.get("AGENT_CORE_PROMPT_SIGNAL") == "1"
    _maybe_prompt_signal(llm, enabled)


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
