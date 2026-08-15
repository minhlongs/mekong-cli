"""Mekong CLI 7 — `chat` command: Textual chat TUI + `--raw` one-shot."""

from __future__ import annotations

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.markdown import Markdown

from src.cli.tui.chat_config import resolve_model
from src.cli.tui.omni_client import OmniClient

console = Console()


def cc_cmd(
    model: Optional[str] = typer.Option(None, "--model", help="Model alias or raw id"),
    project: Optional[str] = typer.Option(None, "--project", help="Project context (system prompt hint)"),
) -> None:
    """Command center: 4-tab TUI — Chat | OPC | Agents | OmniRoute."""
    from src.cli.tui.command_center import CommandCenter

    CommandCenter(model=model, project=project).run()


def chat_cmd(
    prompt: Optional[str] = typer.Argument(None, help="Prompt; empty = interactive TUI"),
    raw: bool = typer.Option(False, "--raw", help="One-shot mode: print response, no TUI"),
    model: Optional[str] = typer.Option(None, "--model", help="Model alias or raw id"),
    project: Optional[str] = typer.Option(None, "--project", help="Project context (system prompt hint)"),
) -> None:
    """Chat with OmniRoute models — interactive Textual TUI or --raw one-shot."""
    resolved = resolve_model(model)
    if raw:
        if not prompt:
            console.print("[red]--raw requires a prompt[/red]")
            raise typer.Exit(1)
        _raw_chat(prompt, resolved, project)
        return
    from src.cli.tui.chat_tui import ChatTUI  # lazy: --raw works without textual

    ChatTUI(model=resolved, project=project).run()


def _raw_chat(prompt: str, model: str, project: str | None) -> None:
    messages: list[dict[str, str]] = []
    if project:
        messages.append(
            {"role": "system", "content": f"Project context: {project}. Answer concisely."}
        )
    messages.append({"role": "user", "content": prompt})

    async def _run() -> None:
        client = OmniClient()
        collected: list[str] = []
        reasoning: list[str] = []

        async def on_delta(chunk) -> None:
            if chunk.text:
                collected.append(chunk.text)
            if chunk.reasoning_text:
                reasoning.append(chunk.reasoning_text)

        final = await client.stream_chat(model, messages, on_delta)
        actual = final.actual_model or model
        if actual != model:
            console.print(f"[yellow]⚠ actual model: {actual}[/yellow]")
        text = "".join(collected)
        if not text.strip():
            console.print("[red]empty response[/red]")
            raise typer.Exit(1)
        console.print(Markdown(text))

    try:
        asyncio.run(_run())
    except RuntimeError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1) from exc
