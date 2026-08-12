"""Mekong CLI 7 — ask / text commands."""

from __future__ import annotations

import typer
from rich.console import Console

from ..core.llm import LLMClient
from ..core.models import resolve

console = Console()


def ask_cmd(
    question: str = typer.Argument(..., help="Question to ask"),
    model: str = typer.Option("fable", "--model", "-m", help="Model role or id"),
) -> None:
    """Ask the model a single question."""
    client = LLMClient()
    entry = resolve(model)
    console.print(f"[dim]{entry.id} →[/]")
    reply = client.text(entry.id, question)
    console.print(reply)


def strategist_cmd(
    question: str = typer.Argument(..., help="Strategy question"),
) -> None:
    """Ask the strategist (qwen3.8-max via strategist combo)."""
    from ..core.agents import run_strategist

    console.print("[dim]strategist (qwen3.8-max) →[/]")
    console.print(run_strategist(question))
