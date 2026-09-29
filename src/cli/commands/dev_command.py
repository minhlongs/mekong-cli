# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/commands/dev_command.py — CLI command surface for Developer & Code Quality Suite.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.dev_engine import get_dev_engine

console = Console()
dev_app = typer.Typer(
    name="dev",
    help="💻 Developer Command Suite: Audit, debug, scaffold, PR review, and refactor",
    no_args_is_help=False,
)


@dev_app.callback(invoke_without_command=True)
def dev_main(
    ctx: typer.Context,
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON developer workbench summary",
    ),
) -> None:
    """💻 Developer Workbench Overview: Branch, uncommitted state, debt count, and environment."""
    if ctx.invoked_subcommand is not None:
        return

    engine = get_dev_engine()
    status = engine.get_status()

    if json_output:
        print(json.dumps(status.to_dict(), indent=2))
        return

    dirty_badge = f"[bold red]{status.uncommitted_files} uncommitted[/bold red]" if status.uncommitted_files > 0 else "[bold green]clean[/bold green]"
    debt_badge = f"[yellow]{status.debt_markers}[/yellow]" if status.debt_markers > 0 else "[green]0[/green]"

    body = (
        f"[bold cyan]💻 DEVELOPER WORKBENCH[/bold cyan]\n"
        f"[dim]Git Branch:[/dim]        [bold]{status.active_branch}[/bold] ({dirty_badge})\n"
        f"[dim]Last Commit:[/dim]       [dim]{status.last_commit_hash}[/dim] — {status.last_commit_subject}\n"
        f"[dim]Debt Markers:[/dim]      {debt_badge} (TODO/FIXME/HACK)\n"
        f"[dim]Python Runtime:[/dim]    {status.python_version} (env: [cyan]{status.virtualenv}[/cyan])"
    )
    console.print(Panel(body, title="Engineering Workspace", border_style="cyan", box=ROUNDED))

    # Available commands quick guide
    table = Table(title="Available Developer Commands", box=ROUNDED)
    table.add_column("Command", style="cyan")
    table.add_column("Purpose")

    table.add_row("mekong dev audit", "Perform static AST and security audit across codebase")
    table.add_row("mekong dev scaffold <name>", "Scaffold a new module, service, or API with tests")
    table.add_row("mekong dev review", "Review working tree git diff for safety & standards")
    table.add_row("mekong dev refactor <file>", "Analyze complexity and get refactoring recommendations")

    console.print(table)


@dev_app.command(name="audit")
def dev_audit(
    path: Optional[str] = typer.Argument(
        None,
        help="Optional path or file to audit (defaults to project root)",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        "-s",
        help="Filter findings by severity: high, medium, low",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON audit report",
    ),
) -> None:
    """🛡️ Perform static AST and security audit across the codebase."""
    engine = get_dev_engine()
    report = engine.audit_codebase(target_path=path)

    findings = report.findings
    if severity:
        findings = [f for f in findings if f.severity.lower() == severity.lower()]

    if json_output:
        res = report.to_dict()
        res["findings"] = [f.to_dict() for f in findings]
        print(json.dumps(res, indent=2))
        return

    grade_style = "bold green" if report.grade in ("A", "B") else "bold yellow"
    header_text = (
        f"[bold]Quality Score:[/bold] [{grade_style}]{report.quality_score}/100 (Grade: {report.grade})[/{grade_style}]\n"
        f"[dim]Files Scanned:[/dim] {report.total_files_scanned}  |  "
        f"[bold red]High:[/bold red] {report.high_count}  |  "
        f"[bold yellow]Medium:[/bold yellow] {report.medium_count}  |  "
        f"[dim]Low:[/dim] {report.low_count}"
    )
    console.print(Panel(header_text, title="Codebase Audit Summary", border_style="cyan", box=ROUNDED))

    if findings:
        table = Table(title=f"Audit Findings ({len(findings)} issues)", box=ROUNDED)
        table.add_column("Location", style="dim")
        table.add_column("Sev", justify="center")
        table.add_column("Issue & Recommendation")

        for f in findings[:25]:
            sev_style = "bold red" if f.severity == "high" else ("yellow" if f.severity == "medium" else "dim")
            table.add_row(
                f"{f.file_path}:{f.line_number}",
                f"[{sev_style}]{f.severity.upper()}[/{sev_style}]",
                f"[bold]{f.message}[/bold]\n[dim]Action: {f.recommendation}[/dim]",
            )
        console.print(table)
    else:
        console.print("[bold green]✓ Zero audit issues found! Codebase is in excellent condition.[/bold green]")


@dev_app.command(name="scaffold")
def dev_scaffold(
    name: str = typer.Argument(
        ...,
        help="Name of the component or module to scaffold",
    ),
    module_type: str = typer.Option(
        "service",
        "--type",
        "-t",
        help="Type of module: 'service', 'api', 'agent', 'util'",
    ),
    directory: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Custom target directory for the module",
    ),
    with_test: bool = typer.Option(
        True,
        "--test/--no-test",
        help="Generate corresponding unit test file",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Simulate file creation without writing to disk",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON scaffolding report",
    ),
) -> None:
    """⚡ Scaffold a new structured Python module, service, API, or agent with unit tests."""
    engine = get_dev_engine()
    res = engine.scaffold_module(
        name=name,
        module_type=module_type,
        target_dir=directory,
        with_test=with_test,
        dry_run=dry_run,
    )

    if json_output:
        print(json.dumps(res.to_dict(), indent=2))
        return

    action_label = "Simulated Scaffolding (Dry Run)" if dry_run else "Scaffolded Successfully"
    color = "yellow" if dry_run else "green"
    file_list = "\n".join(f"  • {f}" for f in res.files_created)

    console.print(
        Panel(
            f"[bold {color}]✓ {action_label}[/bold {color}]\n"
            f"[dim]Component:[/dim]  [bold]{res.module_name}[/bold] ({res.module_type})\n\n"
            f"[bold]Files Created:[/bold]\n{file_list}",
            title="Module Scaffolder",
            border_style=color,
            box=ROUNDED,
        )
    )


@dev_app.command(name="review")
def dev_review(
    cached: bool = typer.Option(
        False,
        "--cached",
        help="Review staged/cached git changes instead of working tree",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON review report",
    ),
) -> None:
    """🔍 Review working tree git diff for safety, technical debt, and quality hazards."""
    engine = get_dev_engine()
    diff = engine._run_git(["diff", "--cached" if cached else "HEAD"])
    report = engine.review_diff(diff_text=diff)

    if json_output:
        print(json.dumps(report.to_dict(), indent=2))
        return

    status_color = "green" if report.status == "approved" else ("red" if report.status == "changes_requested" else "dim")

    console.print(
        Panel(
            f"[bold]Review Status:[/bold] [{status_color}]{report.status.upper()}[/{status_color}]\n"
            f"[dim]Changes:[/dim] {report.diff_summary}\n\n"
            f"[bold]Recommendations:[/bold]\n" + "\n".join(f"  • {r}" for r in report.recommendations),
            title="Pull Request Diff Review",
            border_style=status_color,
            box=ROUNDED,
        )
    )

    if report.findings:
        table = Table(title="Diff Findings", box=ROUNDED)
        table.add_column("Issue Detected", style="yellow")
        for finding in report.findings:
            table.add_row(finding)
        console.print(table)


@dev_app.command(name="refactor")
def dev_refactor(
    file_path: str = typer.Argument(
        ...,
        help="Path to Python file to analyze for refactoring",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output machine-readable JSON refactoring recommendations",
    ),
) -> None:
    """🔨 Analyze code complexity, method sizes, and generate refactoring advice."""
    engine = get_dev_engine()
    advice = engine.analyze_refactor(target_file=file_path)

    if json_output:
        print(json.dumps(advice.to_dict(), indent=2))
        return

    risk_style = "green" if advice.complexity_risk == "low" else ("yellow" if advice.complexity_risk == "moderate" else "bold red")

    console.print(
        Panel(
            f"[bold cyan]REFACTOR ANALYSIS — {advice.target_file}[/bold cyan]\n"
            f"[dim]Total Lines:[/dim]       {advice.total_lines}\n"
            f"[dim]Complexity Risk:[/dim]   [{risk_style}]{advice.complexity_risk.upper()}[/{risk_style}]\n\n"
            f"[bold]Suggested Actions:[/bold]\n" + "\n".join(f"  • {a}" for a in advice.suggested_actions),
            title="Refactoring Advisor",
            border_style="cyan",
            box=ROUNDED,
        )
    )

    if advice.anti_patterns_found:
        table = Table(title="Detected Anti-Patterns", box=ROUNDED)
        table.add_column("Anti-Pattern", style="yellow")
        for ap in advice.anti_patterns_found:
            table.add_row(ap)
        console.print(table)


def register_dev_command(app: typer.Typer) -> None:
    """Register the 'dev' command group onto the main Typer application."""
    app.add_typer(dev_app, name="dev")
