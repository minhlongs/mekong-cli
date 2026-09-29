# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/support_command.py — CLI command surface for Customer Success, Onboarding & Support Suite.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.support_engine import get_support_engine

console = Console()
support_app = typer.Typer(
    name="support",
    help="🤝 Customer Success Suite: Guided onboarding, NPS feedback, bug reports & smart triage",
    no_args_is_help=False,
)


@support_app.callback(invoke_without_command=True)
def support_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON customer success overview",
    ),
) -> None:
    """🤝 Customer Success Overview: Onboarding progress, NPS score, open bugs, and channels."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_support_engine()
    status = engine.get_status()

    if json_output:
        print(json.dumps(status, indent=2))
        return

    progress = status["onboarding_progress_pct"]
    prog_color = "green" if progress >= 80 else ("yellow" if progress >= 40 else "cyan")
    step_str = f"Step {status['onboarding_step']}/5" if status['onboarding_step'] else "All Complete (5/5)"

    nps = status["nps_score"]
    nps_color = "green" if nps >= 50 else ("yellow" if nps >= 0 else "red")
    nps_badge = f"[{nps_color}]{nps:+0.1f}[/{nps_color}] ({status['nps_total_responses']} reviews)"

    bugs_badge = f"[bold red]{status['open_bugs_count']} open[/bold red]" if status['open_bugs_count'] > 0 else "[bold green]0 open[/bold green]"

    body = (
        f"[bold cyan]🤝 CUSTOMER SUCCESS & SUPPORT CONTROL PLANE[/bold cyan]\n"
        f"[dim]Onboarding Progress:[/dim]   [{prog_color}]{progress}%[/{prog_color}] — {step_str}\n"
        f"[dim]Net Promoter Score:[/dim]    {nps_badge}\n"
        f"[dim]Open Bug Reports:[/dim]      {bugs_badge}\n\n"
        f"[bold]Support Channels:[/bold]\n"
        f"  • [cyan]GitHub Issues:[/cyan]      {status['channels']['github_issues']}\n"
        f"  • [cyan]Email Desk:[/cyan]         {status['channels']['email_support']}\n"
        f"  • [cyan]Billing Support:[/cyan]    {status['channels']['billing_support']}"
    )

    console.print(Panel(body, title="Customer Success Dashboard", border_style="cyan", box=ROUNDED))


@support_app.command(name="onboard")
def support_onboard(
    step: Optional[int] = typer.Option(
        None,
        "--step",
        "-s",
        help="Mark a specific onboarding step as completed (1 to 5)",
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Reset all onboarding steps to uncompleted",
    ),
    notes: str = typer.Option(
        "",
        "--notes",
        "-n",
        help="Optional notes or confirmation for the completed milestone",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output onboarding status as machine-readable JSON",
    ),
) -> None:
    """🚀 Track and update project onboarding milestones (Steps 1 through 5)."""
    engine = get_support_engine()

    if reset:
        res = engine.reset_onboarding()
    elif step is not None:
        try:
            res = engine.complete_onboarding_step(step_index=step, notes=notes)
        except ValueError as e:
            console.print(f"[bold red]Error:[/bold red] {e}")
            raise typer.Exit(code=1)
    else:
        res = engine.get_onboarding_status()

    if json_output:
        print(json.dumps(res.to_dict(), indent=2))
        return

    table = Table(
        title=f"Project Onboarding Progress ({res.progress_pct}% — {res.completed_count}/{res.total_count} Completed)",
        box=ROUNDED,
        border_style="cyan",
    )
    table.add_column("Step", justify="center", width=6)
    table.add_column("Status", justify="center", width=12)
    table.add_column("Milestone Description", style="bold")
    table.add_column("Completed At", style="dim", width=20)

    for s in res.steps:
        stat_str = "[bold green]COMPLETE[/bold green]" if s["completed"] else "[dim yellow]PENDING[/dim yellow]"
        comp_at = s["completed_at"][:19].replace("T", " ") if s["completed_at"] else "-"
        table.add_row(str(s["step"]), stat_str, s["title"], comp_at)

    console.print(table)


@support_app.command(name="feedback")
def support_feedback(
    nps: Optional[int] = typer.Option(
        None,
        "--nps",
        help="Rate Mekong CLI from 0 (not likely) to 10 (extremely likely)",
    ),
    text: str = typer.Option(
        "",
        "--text",
        "-t",
        help="Feedback comments, feature requests, or suggestions",
    ),
    category: str = typer.Option(
        "general",
        "--category",
        "-c",
        help="Category (product, pricing, performance, support)",
    ),
    report: bool = typer.Option(
        False,
        "--report",
        "-r",
        help="Show aggregated Net Promoter Score summary",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output feedback record or NPS summary as JSON",
    ),
) -> None:
    """⭐ Submit customer feedback / NPS rating or view the satisfaction report."""
    engine = get_support_engine()

    if report or (nps is None and not text):
        summary = engine.get_nps_summary()
        if json_output:
            print(json.dumps(summary.to_dict(), indent=2))
            return

        body = (
            f"[bold cyan]⭐ NET PROMOTER SCORE (NPS) SUMMARY[/bold cyan]\n"
            f"[dim]Overall NPS Score:[/dim]     [bold]{summary.nps_score:+0.1f}[/bold]\n"
            f"[dim]Total Responses:[/dim]       {summary.total_responses}\n"
            f"[dim]Promoters (9-10):[/dim]     [green]{summary.promoters}[/green]\n"
            f"[dim]Passives (7-8):[/dim]       [yellow]{summary.passives}[/yellow]\n"
            f"[dim]Detractors (0-6):[/dim]     [red]{summary.detractors}[/red]"
        )
        console.print(Panel(body, title="Customer Satisfaction", border_style="cyan", box=ROUNDED))
        return

    try:
        fb = engine.submit_feedback(nps_score=nps, feedback_text=text, category=category)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(fb.to_dict(), indent=2))
        return

    nps_str = f"Rating: {fb.nps_score}/10" if fb.nps_score is not None else "No rating"
    console.print(
        Panel(
            f"[bold green]Thank you for your feedback![/bold green]\n"
            f"[dim]ID:[/dim]       {fb.id}\n"
            f"[dim]Score:[/dim]    {nps_str}\n"
            f"[dim]Category:[/dim] {fb.category}\n"
            f"[dim]Notes:[/dim]    {fb.feedback_text or '(none)'}",
            title="Feedback Submitted",
            border_style="green",
            box=ROUNDED,
        )
    )


@support_app.command(name="bug")
def support_bug(
    title: str = typer.Argument(..., help="Short summary of the bug"),
    severity: str = typer.Option(
        "medium",
        "--severity",
        "-s",
        help="Bug severity (low, medium, high, critical)",
    ),
    desc: str = typer.Option(
        "",
        "--desc",
        "-d",
        help="Detailed description of unexpected behavior",
    ),
    steps: str = typer.Option(
        "",
        "--steps",
        help="Reproduction steps",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output bug report as JSON",
    ),
) -> None:
    """🐛 Report a bug or regression in Mekong CLI."""
    engine = get_support_engine()
    bug = engine.submit_bug(title=title, severity=severity, description=desc, steps=steps)

    if json_output:
        print(json.dumps(bug.to_dict(), indent=2))
        return

    sev_color = "red" if bug.severity in {"high", "critical"} else "yellow"
    console.print(
        Panel(
            f"[bold {sev_color}]Bug Report {bug.id} Filed ({bug.severity.upper()})[/bold {sev_color}]\n"
            f"[dim]Title:[/dim]       {bug.title}\n"
            f"[dim]Description:[/dim] {bug.description or '(none)'}\n"
            f"[dim]Steps:[/dim]       {bug.steps or '(none)'}\n"
            f"[dim]Status:[/dim]      [bold yellow]{bug.status.upper()}[/bold yellow]",
            title="Bug Tracked",
            border_style="red" if bug.severity in {"high", "critical"} else "yellow",
            box=ROUNDED,
        )
    )


@support_app.command(name="triage")
def support_triage(
    issue_text: str = typer.Argument(..., help="Error message or problem description to triage"),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output triage recommendations as JSON",
    ),
) -> None:
    """🧠 Smart AI/heuristic triage for system errors and common configuration problems."""
    engine = get_support_engine()
    triage = engine.triage_issue(issue_description=issue_text)

    if json_output:
        print(json.dumps(triage.to_dict(), indent=2))
        return

    urg_color = "red" if triage.urgency in {"critical", "high"} else ("yellow" if triage.urgency == "medium" else "green")
    body = (
        f"[bold]Issue:[/bold]               {triage.issue_text}\n"
        f"[bold]Category:[/bold]            {triage.category.upper()}\n"
        f"[bold]Urgency:[/bold]             [{urg_color}]{triage.urgency.upper()}[/{urg_color}]\n\n"
        f"[bold cyan]Recommended Action:[/bold cyan]\n"
        f"  {triage.recommended_action}\n\n"
        f"[bold cyan]Escalation Channel:[/bold cyan]\n"
        f"  {triage.escalation_channel}"
    )

    console.print(Panel(body, title="Smart Issue Triage Result", border_style="cyan", box=ROUNDED))


@support_app.command(name="contact")
def support_contact(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output contact links as JSON",
    ),
) -> None:
    """📞 List official Mekong CLI support channels and documentation."""
    engine = get_support_engine()
    channels = engine.get_support_channels()

    if json_output:
        print(json.dumps(channels, indent=2))
        return

    table = Table(title="Mekong CLI Support Channels", box=ROUNDED, border_style="cyan")
    table.add_column("Channel", style="bold cyan")
    table.add_column("Destination", style="bold")

    for k, v in channels.items():
        table.add_row(k.replace("_", " ").title(), v)

    console.print(table)


def register_support_command(app: typer.Typer) -> None:
    """Register the 'support' command group onto the main Typer application."""
    app.add_typer(support_app, name="support")
