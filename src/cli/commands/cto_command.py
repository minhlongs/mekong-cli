# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""src/cli/commands/cto_command.py — CLI command surface for CTO Architecture & Review Suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.cto_engine import ADRRecord, CodeReviewReport, EngineeringScorecard, get_cto_engine

console = Console()
cto_app = typer.Typer(
    name="cto",
    help="🏛️ CTO Command Suite: Architecture decisions, code review, scorecard, health, and roadmap",
    no_args_is_help=False,
)
_GRADE_COLORS = {"A+": "bold green", "A": "green", "B": "cyan", "C": "yellow", "D": "red"}


@cto_app.callback(invoke_without_command=True)
def cto_main(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON executive summary")) -> None:
    """🏛️ CTO Executive Overview: Health status, engineering scorecard, and strategic priorities."""
    if ctx.invoked_subcommand is not None:
        return
    summary = get_cto_engine().executive_summary()
    if json_output:
        print(json.dumps(summary, indent=2))
        return
    sc, health = summary["scorecard"], summary["health"]
    grade_style = _GRADE_COLORS.get(sc["grade"], "white")
    tree_status = "[green]Clean[/green]" if health["git_clean"] else f"[yellow]{health['uncommitted_files']} uncommitted files[/yellow]"
    header_text = (
        f"[bold cyan]🏛️ CTO EXECUTIVE BRIEFING — {summary['date']}[/bold cyan]\n"
        f"[dim]Engineering Health Grade:[/dim] [{grade_style}]{sc['grade']} ({sc['composite_score']}/100)[/{grade_style}]  |  "
        f"[dim]Branch:[/dim] [cyan]{health['repo_branch']}[/cyan]\n"
        f"[dim]Working Tree:[/dim]            {tree_status}  |  [dim]Python:[/dim] {health['python_version']}\n"
        f"[dim]Total Initiatives:[/dim]        [bold]{summary['initiatives_count']}[/bold]"
    )
    console.print(Panel(header_text, title="Engineering Leadership", border_style="cyan", box=ROUNDED))
    m = sc["metrics"]
    table = Table(title="Engineering Scorecard Metrics", box=ROUNDED)
    table.add_column("Category", style="cyan")
    table.add_column("Score", justify="center", style="bold")
    table.add_column("Details")
    table.add_row("Automated Tests", f"{m['test_score']}/30", f"{m['test_files_count']} test files detected")
    table.add_row("Git Cadence & Hygiene", f"{m['git_score']}/25", f"{m['git_commits_count']} commits, {m['uncommitted_files_count']} uncommitted")
    table.add_row("Security & Code Quality", f"{m['security_score']}/25", f"{m['total_findings']} code smell / security findings")
    table.add_row("Modularity & Standards", f"{m['modularity_score']}/20", "Standard packaging and src structure")
    console.print(table)
    if summary["top_priorities"]:
        console.print(Panel("\n".join(f"  • [bold green]{p}[/bold green]" for p in summary["top_priorities"]), title="🎯 CTO Execution Priorities", border_style="green", box=ROUNDED))


@cto_app.command(name="architect")
def cto_architect(
    title: str = typer.Argument(..., help="Title or subject of the Architecture Decision Record"),
    context: str = typer.Option("", "--context", "-c", help="Problem context and rationale for architectural decision"),
    decision: str = typer.Option("", "--decision", "-d", help="Chosen architectural decision and design pattern"),
    export: bool = typer.Option(False, "--export", "-e", help="Export ADR markdown to reports/cto/architect/ADR-XXX.md"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON ADR record"),
) -> None:
    """📐 Generate and document an Architecture Decision Record (ADR)."""
    record = get_cto_engine().generate_adr(title=title, context=context, decision=decision, export=export)
    if json_output:
        print(json.dumps(record.to_dict(), indent=2))
        return
    console.print(Panel(
        f"[bold cyan]ADR-{record.number:03d}: {record.title}[/bold cyan]\n"
        f"[dim]Status:[/dim] [green]{record.status}[/green]  |  [dim]Date:[/dim] {record.date}\n\n"
        f"[bold]Context:[/bold]\n{record.context}\n\n[bold]Decision:[/bold]\n{record.decision}\n\n"
        f"[bold]Consequences:[/bold]\n{record.consequences}",
        title="Architecture Decision Record", border_style="cyan", box=ROUNDED,
    ))
    if export:
        console.print(f"[dim]Exported ADR to reports/cto/architect/ADR-{record.number:03d}.md[/dim]")


@cto_app.command(name="review")
def cto_review(
    target_path: Optional[str] = typer.Argument(None, help="Optional relative path or file to review (defaults to entire repo)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON code review report"),
) -> None:
    """🔍 Conduct automated code quality, anti-pattern, and security review."""
    report = get_cto_engine().run_code_review(target_path=target_path)
    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return
    status_str = "[bold green]PASSED[/bold green]" if report.passed else "[bold red]ACTION REQUIRED[/bold red]"
    console.print(Panel(
        f"[bold]Code Review Status:[/bold] {status_str}\n[dim]Files Scanned:[/dim] {report.files_scanned}  |  [dim]Total Findings:[/dim] {report.total_findings}\n"
        f"[dim]Severity Breakdown:[/dim] [red]{report.severity_counts['CRITICAL']} Critical[/red]  |  [yellow]{report.severity_counts['HIGH']} High[/yellow]  |  [blue]{report.severity_counts['MEDIUM']} Medium[/blue]  |  [dim]{report.severity_counts['LOW']} Low[/dim]",
        title="CTO Code & Security Review", border_style="cyan", box=ROUNDED,
    ))
    if report.findings:
        table = Table(title="Review Findings", box=ROUNDED)
        table.add_column("Severity", justify="center", width=10)
        table.add_column("Rule ID", style="dim", width=18)
        table.add_column("Location", style="cyan", width=32)
        table.add_column("Finding & Recommendation")
        for f in report.findings[:20]:
            sev_style = "bold red" if f.severity.value in ("CRITICAL", "HIGH") else "yellow"
            table.add_row(f"[{sev_style}]{f.severity.value}[/{sev_style}]", f.rule_id, f"{f.file}:{f.line}", f"{f.message}\n[dim]Fix: {f.recommendation}[/dim]")
        console.print(table)


@cto_app.command(name="scorecard")
def cto_scorecard(
    export_path: Optional[str] = typer.Option(None, "--export", "-e", help="Export scorecard JSON to specified file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON scorecard"),
) -> None:
    """📊 Calculate composite engineering health scorecard and grade."""
    scorecard = get_cto_engine().compute_scorecard()
    if export_path:
        p = Path(export_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(scorecard.to_dict(), indent=2), encoding="utf-8")
    if json_output:
        print(json.dumps(scorecard.to_dict(), indent=2))
        return
    grade_style = _GRADE_COLORS.get(scorecard.grade, "white")
    console.print(Panel(
        f"[bold]Engineering Health Score:[/bold] [{grade_style}]{scorecard.composite_score}/100 (Grade {scorecard.grade})[/{grade_style}]\n\n" + "\n".join(f"  • {r}" for r in scorecard.recommendations),
        title="Engineering Scorecard", border_style="green", box=ROUNDED,
    ))


@cto_app.command(name="health")
def cto_health(json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON health report")) -> None:
    """🏥 Inspect developer environment, runtime, git, and tooling health."""
    health = get_cto_engine().check_health()
    if json_output:
        print(json.dumps(health.to_dict(), indent=2))
        return
    table = Table(title="CTO Developer Stack Health", box=ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Value / Details")
    table.add_row("Git Working Tree", "[green]✓ CLEAN[/green]" if health.git_clean else "[yellow]DIRTY[/yellow]", f"Branch: {health.repo_branch} ({health.uncommitted_files} uncommitted files)")
    table.add_row("Python Runtime", "[green]✓ OK[/green]", f"Python {health.python_version} ({'Virtualenv Active' if health.virtualenv_active else 'System Python'})")
    table.add_row("Test Runner", "[green]✓ READY[/green]" if health.test_runner_available else "[dim]NOT INSTALLED[/dim]", "pytest framework")
    table.add_row("Linter / Formatter", "[green]✓ READY[/green]" if health.linter_available else "[dim]NOT INSTALLED[/dim]", "ruff static analyzer")
    console.print(table)


@cto_app.command(name="roadmap")
def cto_roadmap(json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON roadmap")) -> None:
    """🗺️ Generate 3-horizon technical roadmap (Now, Next, Later)."""
    roadmap = get_cto_engine().generate_roadmap()
    if json_output:
        print(json.dumps(roadmap.to_dict(), indent=2))
        return
    console.print(Panel("[bold cyan]🗺️ CTO TECHNICAL ROADMAP (3 HORIZONS)[/bold cyan]", box=ROUNDED))
    for horizon, title, style in [
        ("now", "🔥 Horizon 1: NOW (Immediate Blockers & Debt)", "bold red"),
        ("next", "⚡ Horizon 2: NEXT (Architecture & Scaling)", "bold yellow"),
        ("later", "🚀 Horizon 3: LATER (Platform & Swarm Expansion)", "bold green"),
    ]:
        items = roadmap.horizons.get(horizon, [])
        console.print(Panel("\n".join(f"  • {it}" for it in items) if items else "  • No open initiatives", title=title, border_style=style, box=ROUNDED))


def register_cto_command(app: typer.Typer) -> None:
    """Register the 'cto' command group onto the main Typer application."""
    app.add_typer(cto_app, name="cto")


__all__ = ["ADRRecord", "CodeReviewReport", "EngineeringScorecard", "cto_app", "register_cto_command"]
