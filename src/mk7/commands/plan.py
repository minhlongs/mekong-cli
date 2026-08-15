"""Mekong CLI 7 — plan command: create plan.md + phase files."""

from __future__ import annotations

import datetime
import re

import typer
from rich.console import Console

from ..core.llm import LLMClient
from ..core.models import resolve

console = Console()

PLANS_DIR = None  # resolved per-cwd below


def _plan_root() -> str:
    import os

    return os.path.join(os.getcwd(), "plans")


def plan_cmd(
    task: str = typer.Argument(..., help="Feature/task to plan"),
    hard: bool = typer.Option(False, "--hard", help="Use opus for deeper planning"),
) -> None:
    """Create a phased implementation plan (plan.md + phase files)."""
    import os

    from pathlib import Path

    client = LLMClient()
    model = resolve("opus" if hard else "sonnet")

    console.print(f"[bold]Planning ({model.id}):[/] {task}")
    prompt = (
        f"Create a phased implementation plan for: {task}\n\n"
        "Working directory is the operator's repo. Structure:\n"
        "- Phase 01..0N: each with name, files to touch, task description, acceptance criteria\n"
        "- Verify + Review phases\n\n"
        'Return ONLY JSON: {"title": "...", "phases": [{"name": "...", "files": ["..."], "task": "...", "acceptance": "..."}]}'
    )
    raw = client.text(model.id, prompt, max_tokens=4096)
    try:
        data = json_loads(raw)
    except Exception:
        console.print("[red]Model did not return valid plan JSON.[/]")
        console.print(raw[:500])
        raise typer.Exit(1)

    title = data.get("title", task)
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
    date = datetime.date.today().strftime("%y%m%d")
    plan_dir = Path(_plan_root()) / f"{date}-{slug}"
    plan_dir.mkdir(parents=True, exist_ok=True)

    overview = [f"# {title}", "", f"**Ngày:** {date} · **Priority:** MEDIUM · **Status:** pending", ""]
    phases = data.get("phases", [])
    for i, ph in enumerate(phases, 1):
        overview.append(f"- [ ] **Phase {i:02d}** — {ph.get('name', '')} — [phase-{i:02d}.md](phase-{i:02d}.md)")
        phase_md = [
            f"# Phase {i:02d} — {ph.get('name', '')}",
            "",
            f"**Date:** {date} · **Status:** pending",
            "",
            "## Task",
            ph.get("task", ""),
            "",
            "## Files",
            "",
        ]
        for f in ph.get("files", []):
            phase_md.append(f"- {f}")
        phase_md += ["", "## Acceptance criteria", "", ph.get("acceptance", ""), ""]
        (plan_dir / f"phase-{i:02d}.md").write_text("\n".join(phase_md))

    overview.append("")
    (plan_dir / "plan.md").write_text("\n".join(overview))

    console.print(f"[bold green]✔ Plan created: {plan_dir}[/]")
    console.print(f"  {len(phases)} phases — {plan_dir / 'plan.md'}")


def json_loads(raw: str) -> dict:
    import json

    # Strip code fences if the model wrapped JSON.
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    return json.loads(cleaned)
