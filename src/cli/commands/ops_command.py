# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/ops_command.py — CLI command surface for Operations, SRE & Incident Response Suite.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.ops_engine import get_ops_engine

console = Console()
ops_app = typer.Typer(
    name="ops",
    help="🛡️ Operations Suite: SRE morning check, health sweep, incidents & DR readiness",
    no_args_is_help=False,
)

incident_app = typer.Typer(
    name="incident",
    help="🚨 Incident response, triage, resolution & blameless post-mortems",
    no_args_is_help=False,
)
ops_app.add_typer(incident_app, name="incident")


@ops_app.callback(invoke_without_command=True)
def ops_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON operational status overview",
    ),
) -> None:
    """🛡️ Operations Overview: Health score, active incidents, DR readiness, and alerts."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_ops_engine()
    status = engine.get_status()

    if json_output:
        print(json.dumps(status, indent=2))
        return

    score = status["health_score"]
    overall_status = status["overall_status"]
    score_color = "green" if score >= 85 else ("yellow" if score >= 60 else "red")
    badge = f"[{score_color}]{overall_status} ({score}/100)[/{score_color}]"

    open_incidents = status["open_incidents"]
    critical = status["critical_incidents"]
    inc_badge = f"[bold red]{open_incidents} active ({critical} critical)[/bold red]" if open_incidents > 0 else "[bold green]0 active[/bold green]"

    dr_status = status["dr_status"]
    dr_color = "green" if dr_status == "READY" else ("yellow" if dr_status == "ACCEPTABLE" else "red")
    dr_badge = f"[{dr_color}]{dr_status} ({status['dr_readiness_score']}/100)[/{dr_color}]"

    body = (
        f"[bold cyan]🛡️ OPERATIONS & SRE CONTROL PLANE[/bold cyan]\n"
        f"[dim]System Health:[/dim]      {badge}\n"
        f"[dim]Active Incidents:[/dim]   {inc_badge}\n"
        f"[dim]DR Readiness:[/dim]       {dr_badge}\n"
        f"[dim]Active Warnings:[/dim]    {status['warnings_count']}"
    )

    if status["warnings"]:
        body += "\n\n[bold yellow]Warnings:[/bold yellow]\n" + "\n".join([f"  • {w}" for w in status["warnings"][:3]])

    console.print(Panel(body, title="Ops Layer Dashboard", border_style="cyan", box=ROUNDED))


@ops_app.command(name="sweep")
def ops_sweep(
    save: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save full markdown health report to reports/health-sweep/",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Custom output directory for saved health reports",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output health sweep result as machine-readable JSON",
    ),
) -> None:
    """🔍 Run full system health audit across runtime, storage, databases, git & configs."""
    engine = get_ops_engine()
    report = engine.health_sweep(save_report=save, output_dir=output_dir)

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    table = Table(
        title=f"Health Sweep Audit (Score: {report.score}/100 — {report.overall_status})",
        box=ROUNDED,
        border_style="cyan",
    )
    table.add_column("Category", style="cyan", width=14)
    table.add_column("Check Name", style="bold")
    table.add_column("Status", justify="center", width=10)
    table.add_column("Details", style="dim")

    for c in report.checks:
        stat = c["status"]
        if stat == "PASS":
            stat_str = "[bold green]PASS[/bold green]"
        elif stat == "WARN":
            stat_str = "[bold yellow]WARN[/bold yellow]"
        else:
            stat_str = "[bold red]FAIL[/bold red]"

        table.add_row(c["category"].upper(), c["name"], stat_str, c["details"])

    console.print(table)

    if report.warnings:
        console.print("\n[bold yellow]Active Warnings:[/bold yellow]")
        for w in report.warnings:
            console.print(f"  [yellow]• {w}[/yellow]")

    if report.report_file:
        console.print(f"\n[green]Saved health report to:[/green] [dim]{report.report_file}[/dim]")


@ops_app.command(name="morning")
def ops_morning(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output SRE morning check as JSON",
    ),
) -> None:
    """🌅 SRE morning status check: active incidents, system health, and operational readiness."""
    engine = get_ops_engine()
    report = engine.morning_check()

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    status_color = "green" if report.system_status == "READY" else ("yellow" if report.system_status == "ATTENTION_REQUIRED" else "red")
    panel_content = (
        f"[bold {status_color}]Status: {report.system_status}[/bold {status_color}]\n"
        f"[dim]Health Score:[/dim]         [bold]{report.health_score}/100[/bold]\n"
        f"[dim]Open Incidents:[/dim]       {report.open_incidents_count} ({report.sev1_sev2_count} critical)\n"
        f"[dim]Disk Free:[/dim]            {report.disk_free_gb} GB\n"
        f"[dim]Git Clean:[/dim]            {'Yes' if report.git_clean else 'No'}\n\n"
        f"[bold]Checklist Items:[/bold]"
    )
    console.print(Panel(panel_content, title="SRE Morning Readiness Check", border_style="cyan", box=ROUNDED))

    table = Table(box=ROUNDED, border_style="dim")
    table.add_column("Check", style="bold")
    table.add_column("Result", justify="center")
    table.add_column("Details", style="dim")

    for item in report.items:
        res = item["status"]
        res_str = "[green]OK[/green]" if res == "PASS" else (f"[yellow]{res}[/yellow]" if res in {"WARN", "INFO"} else f"[red]{res}[/red]")
        table.add_row(item["name"], res_str, item["details"])

    console.print(table)


@incident_app.command(name="create")
def incident_create(
    title: str = typer.Argument(..., help="Title / brief description of the incident"),
    severity: str = typer.Option("SEV3", "--severity", "-s", help="Severity level: SEV1, SEV2, SEV3, SEV4"),
    service: str = typer.Option("core", "--service", help="Affected service or subsystem"),
    summary: str = typer.Option("", "--summary", help="Detailed incident summary / symptoms"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output incident record as JSON"),
) -> None:
    """🚨 Create and track a new SRE incident."""
    engine = get_ops_engine()
    rec = engine.create_incident(title=title, severity=severity, service=service, summary=summary)

    if json_output:
        print(json.dumps(rec.to_dict(), indent=2))
        return

    sev_color = "red" if rec.severity in {"SEV1", "SEV2"} else "yellow"
    console.print(
        Panel(
            f"[bold {sev_color}]Incident {rec.id} Created ({rec.severity})[/bold {sev_color}]\n"
            f"[dim]Title:[/dim]   {rec.title}\n"
            f"[dim]Service:[/dim] {rec.service}\n"
            f"[dim]Status:[/dim]  [bold yellow]{rec.status}[/bold yellow]\n"
            f"[dim]Time:[/dim]    {rec.created_at}",
            title="Incident Raised",
            border_style="red" if rec.severity in {"SEV1", "SEV2"} else "yellow",
            box=ROUNDED,
        )
    )


@incident_app.command(name="list")
def incident_list(
    status: str = typer.Option("ALL", "--status", "-s", help="Filter by status (OPEN, RESOLVED, ALL)"),
    severity: str = typer.Option("ALL", "--severity", help="Filter by severity (SEV1, SEV2, SEV3, SEV4, ALL)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output incident list as JSON"),
) -> None:
    """📋 List tracked incidents with status and severity filters."""
    engine = get_ops_engine()
    incidents = engine.list_incidents(status=status, severity=severity)

    if json_output:
        print(json.dumps([i.to_dict() for i in incidents], indent=2))
        return

    if not incidents:
        console.print("[dim]No incidents matching the specified criteria.[/dim]")
        return

    table = Table(title=f"SRE Incidents ({len(incidents)} total)", box=ROUNDED, border_style="red")
    table.add_column("ID", style="bold cyan")
    table.add_column("Severity", justify="center")
    table.add_column("Service", style="magenta")
    table.add_column("Status", justify="center")
    table.add_column("Title")
    table.add_column("Created At", style="dim")

    for i in incidents:
        sev_color = "red" if i.severity in {"SEV1", "SEV2"} else "yellow"
        stat_color = "green" if i.status == "RESOLVED" else "yellow"
        table.add_row(
            i.id,
            f"[{sev_color}]{i.severity}[/{sev_color}]",
            i.service,
            f"[{stat_color}]{i.status}[/{stat_color}]",
            i.title,
            i.created_at[:19].replace("T", " "),
        )

    console.print(table)


@incident_app.command(name="resolve")
def incident_resolve(
    incident_id: str = typer.Argument(..., help="ID of the incident to resolve"),
    mitigation: str = typer.Option(
        "Mitigation applied and service restored.",
        "--mitigation",
        "-m",
        help="Mitigation actions taken",
    ),
    root_cause: str = typer.Option(
        "Root cause identified and corrective measures scheduled.",
        "--root-cause",
        "-r",
        help="Identified root cause",
    ),
    postmortem: bool = typer.Option(
        False,
        "--postmortem",
        "-p",
        help="Generate and display blameless post-mortem",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output resolution result as JSON",
    ),
) -> None:
    """✅ Mark an incident as RESOLVED with mitigation and root cause notes."""
    engine = get_ops_engine()
    rec = engine.update_incident(
        incident_id=incident_id,
        status="RESOLVED",
        mitigation=mitigation,
        root_cause=root_cause,
    )

    if not rec:
        console.print(f"[bold red]Error:[/bold red] Incident '{incident_id}' not found.")
        raise typer.Exit(code=1)

    pm_report = None
    if postmortem:
        pm_report = engine.generate_postmortem(incident_id=incident_id, save_to_file=False)

    if json_output:
        out = rec.to_dict()
        if pm_report:
            out["postmortem"] = pm_report.to_dict()
        print(json.dumps(out, indent=2))
        return

    console.print(
        Panel(
            f"[bold green]Incident {rec.id} RESOLVED[/bold green]\n"
            f"[dim]Title:[/dim]        {rec.title}\n"
            f"[dim]Mitigation:[/dim]   {rec.mitigation}\n"
            f"[dim]Root Cause:[/dim]   {rec.root_cause}\n"
            f"[dim]Resolved At:[/dim]  {rec.resolved_at}",
            title="Incident Resolved",
            border_style="green",
            box=ROUNDED,
        )
    )

    if pm_report:
        console.print("\n[bold cyan]Blameless Postmortem Summary:[/bold cyan]")
        console.print(pm_report.markdown_report)


@incident_app.command(name="postmortem")
def incident_postmortem(
    incident_id: str = typer.Argument(..., help="ID of the incident to postmortem"),
    save: bool = typer.Option(
        False,
        "--save",
        "-s",
        help="Save markdown post-mortem to reports/postmortems/",
    ),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Custom output directory for post-mortem files",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output post-mortem report as JSON",
    ),
) -> None:
    """📝 Generate blameless SRE post-mortem for an incident."""
    engine = get_ops_engine()
    try:
        pm = engine.generate_postmortem(incident_id=incident_id, save_to_file=save, output_dir=output_dir)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        print(json.dumps(pm.to_dict(), indent=2))
        return

    console.print(pm.markdown_report)
    if pm.report_file:
        console.print(f"\n[green]Saved post-mortem to:[/green] [dim]{pm.report_file}[/dim]")


@ops_app.command(name="dr")
def ops_dr(
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output disaster recovery audit as JSON",
    ),
) -> None:
    """💾 Disaster Recovery (DR) & Backup Readiness Audit."""
    engine = get_ops_engine()
    report = engine.dr_audit()

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    dr_color = "green" if report.status == "READY" else ("yellow" if report.status == "ACCEPTABLE" else "red")
    body = (
        f"[bold {dr_color}]DR Readiness: {report.status} ({report.readiness_score}/100)[/bold {dr_color}]\n"
        f"[dim]RTO Target:[/dim]         <{report.rto_target_minutes} minutes\n"
        f"[dim]RPO Target:[/dim]         <{report.rpo_target_minutes} minutes\n"
        f"[dim]Integrity Status:[/dim]   [green]{report.integrity_status}[/green]\n"
        f"[dim]Notes:[/dim]              {report.notes}\n\n"
        f"[bold]Detected Backups & State Artifacts:[/bold]\n"
    )
    for b in report.backups_found:
        body += f"  • {b}\n"

    body += "\n[bold]Recovery Procedure Steps:[/bold]\n"
    for s in report.steps:
        body += f"  {s}\n"

    console.print(Panel(body, title="Disaster Recovery Readiness Plan", border_style="cyan", box=ROUNDED))


def register_ops_command(app: typer.Typer) -> None:
    """Register the 'ops' command group onto the main Typer application."""
    app.add_typer(ops_app, name="ops")

