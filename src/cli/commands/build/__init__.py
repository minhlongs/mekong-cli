# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Build CLI — ``mekong build from-plan``."""

from __future__ import annotations

from pathlib import Path
import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.cli.commands.build import i18n as i18n_mod

app = typer.Typer(
    name="build",
    help="Generate build task list from spec",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()
DEFAULT_LOCALE = "en"

_DOMAIN_RE = re.compile(r"`([^`]+)`", re.MULTILINE)
_METADATA_PREFIXES = (
    "company:", "product type:", "generated:", "scenario:",
    "budget:", "mekong", "auto-generated",
)
_TASK_PHASES = ["research", "implement", "test", "review"]


def _extract_domains(spec_text: str) -> list[str]:
    """Extract domain/feature keywords from SPEC_OUTPUT.md body."""
    domains: list[str] = []
    for match in _DOMAIN_RE.finditer(spec_text):
        candidate = (match.group(1) or "").strip()
        lower = candidate.lower()
        if not candidate or candidate.startswith("#") or candidate == "---":
            continue
        if lower.startswith(_METADATA_PREFIXES) or len(candidate) < 10:
            continue
        if candidate not in domains:
            domains.append(candidate)
    return domains


def _scaffold_tasks(domains: list[str]) -> str:
    """Return .mekong/TASKS.todo content (checklist format)."""
    lines: list[str] = [
        "# Build Tasks\n",
        "Auto-extracted from `.mekong/SPEC_OUTPUT.md` domain outlines.\n",
        "---\n\n",
    ]
    task_no = 0
    for domain in domains:
        for phase in _TASK_PHASES:
            task_no += 1
            lines.append(f"- [ ] {task_no:03d}. [{phase}] {domain}")
        lines.append("")
    lines.append("---\n")
    lines.append(f"_Total tasks: {task_no}_ | _Domains: {len(domains)}_\n")
    return "\n".join(lines)


def _dry_run_preview(domains: list[str]) -> str:
    """Return a human-readable preview of what TASKS.todo would contain."""
    lines: list[str] = [
        "[bold]Would generate:[/]\n",
        "[cyan].mekong/TASKS.todo[/] with the following tasks:\n",
    ]
    task_no = 0
    for domain in domains:
        for phase in _TASK_PHASES:
            task_no += 1
            lines.append(f"  [dim]{task_no:03d}.[/] [{phase}] {domain}")
    lines.append(f"\n[dim]Total: {task_no} tasks across {len(domains)} domains.[/]")
    return "\n".join(lines)


@app.command("from-plan")
def from_plan_cmd(
    output_dir: Path = typer.Option(
        Path("."), "--dir", "-d", exists=False, file_okay=False, dir_okay=True, help="Project root (default: CWD).",
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print preview without writing files."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing .mekong/TASKS.todo."),
    lang: str = typer.Option(DEFAULT_LOCALE, "--lang", help="Output language: en | vi."),
) -> None:
    """Generate .mekong/TASKS.todo from .mekong/SPEC_OUTPUT.md."""
    path = output_dir.resolve()
    spec_path = path / ".mekong" / "SPEC_OUTPUT.md"

    if not spec_path.exists():
        console.print(f'[red]{i18n_mod.t(lang, "no_spec")}[/]')
        console.print(f'[dim]{i18n_mod.t(lang, "no_spec_hint", "Run `mekong plan from-init` first.")}[/]')
        raise typer.Exit(code=1)

    spec_text = spec_path.read_text(encoding="utf-8")
    domains = _extract_domains(spec_text)

    if not domains:
        console.print(f'[yellow]{i18n_mod.t(lang, "no_domains")}[/]')
        console.print(f'[dim]{i18n_mod.t(lang, "no_domains_hint", "The spec may not contain backtick-quoted or bullet-prefixed outlines.")}[/]')
        raise typer.Exit(code=1)

    tasks_path = path / ".mekong" / "TASKS.todo"
    if dry_run:
        console.print(_dry_run_preview(domains))
        raise typer.Exit(code=0)

    if not force and tasks_path.exists():
        console.print(f'[yellow]{i18n_mod.t(lang, "already_exists")}[/]')
        raise typer.Exit(code=1)

    tasks_path.write_text(_scaffold_tasks(domains), encoding="utf-8")

    task_count = len(domains) * len(_TASK_PHASES)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    table.add_row("spec", str(spec_path.relative_to(path)))
    table.add_row("tasks_file", str(tasks_path.relative_to(path)))
    table.add_row("domains", str(len(domains)))
    table.add_row("total_tasks", str(task_count))

    console.print(Panel(
        table, title=i18n_mod.t(lang, "tasks_generated", "Build Tasks Generated"),
        border_style="green", expand=False,
    ))
