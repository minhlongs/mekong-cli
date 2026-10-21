"""CLI command group (`mekong pilot`) for invited pilot operators and partners."""

from __future__ import annotations

import json
from pathlib import Path
import typer
from rich.console import Console

from src.core.pilot_client import PilotClient, PilotClientError

console = Console()
pilot_app = typer.Typer(
    name="pilot",
    help="Invited Pilot operations: issue/redeem invites, run LLM-only missions, submit 48h feedback, and view KPIs.",
    no_args_is_help=True,
)


def _build_client(state_file: str | None, offline: bool) -> PilotClient:
    return PilotClient(
        state_path=Path(state_file) if state_file else None,
        offline=offline,
    )


@pilot_app.command("issue-invite")
def issue_invite_cmd(
    partner: str = typer.Option("Pilot Partner", "--partner", "-p", help="Partner organization label"),
    state_file: str | None = typer.Option(None, "--state-file", help="Optional local state JSON path"),
    offline: bool = typer.Option(False, "--offline", help="Run against local synthetic state"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Issue a single-use SHA-256 hashed invite code (capped at 5 partners)."""
    client = _build_client(state_file, offline)
    try:
        result = client.issue_invite(partner_label=partner)
    except PilotClientError as exc:
        console.print(f"[red]Error ({exc.code}): {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_out:
        typer.echo(json.dumps(result))
        return
    console.print(f"[green]Issued pilot invite for {partner}:[/green] [bold]{result['invite_code']}[/bold]")


@pilot_app.command("redeem")
def redeem_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Partner tenant name"),
    code: str = typer.Option(..., "--code", "-c", help="Pilot invite code"),
    state_file: str | None = typer.Option(None, "--state-file", help="Optional local state JSON path"),
    offline: bool = typer.Option(False, "--offline", help="Run against local synthetic state"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Redeem a single-use pilot invite code and provision a 10-credit tenant."""
    client = _build_client(state_file, offline)
    try:
        result = client.redeem_invite(name=name, invite_code=code)
    except PilotClientError as exc:
        console.print(f"[red]Error ({exc.code}): {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_out:
        typer.echo(json.dumps(result))
        return
    console.print(
        f"[green]Redeemed invite for {result['name']}[/green] (tenant_id={result['tenant_id']}, credits={result['credits']})"
    )


@pilot_app.command("submit")
def submit_cmd(
    goal: str = typer.Argument(..., help="Synthetic-data mission goal"),
    mode: str = typer.Option("llm", "--mode", "-m", help="Step execution mode (must be 'llm' in pilot)"),
    state_file: str | None = typer.Option(None, "--state-file", help="Optional local state JSON path"),
    offline: bool = typer.Option(False, "--offline", help="Run against local synthetic state"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Submit a synthetic-data LLM-only mission to the pilot queue."""
    client = _build_client(state_file, offline)
    try:
        result = client.submit_mission(goal=goal, mode=mode)
    except PilotClientError as exc:
        console.print(f"[red]Error ({exc.code}): {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_out:
        typer.echo(json.dumps(result))
        return
    console.print(f"[green]Submitted mission {result['id']}[/green] — status: [bold]{result['status']}[/bold]")


@pilot_app.command("feedback")
def feedback_cmd(
    mission_id: str = typer.Argument(..., help="Mission UUID"),
    rating: int = typer.Option(5, "--rating", "-r", help="Partner rating from 1 to 5"),
    comment: str = typer.Option("", "--comment", "-c", help="Optional partner feedback comment"),
    state_file: str | None = typer.Option(None, "--state-file", help="Optional local state JSON path"),
    offline: bool = typer.Option(False, "--offline", help="Run against local synthetic state"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Submit 1–5 star partner feedback within the 48-hour pilot SLA window."""
    client = _build_client(state_file, offline)
    try:
        result = client.submit_feedback(mission_id=mission_id, rating=rating, comment=comment)
    except PilotClientError as exc:
        console.print(f"[red]Error ({exc.code}): {exc}[/red]")
        raise typer.Exit(code=1) from exc

    if json_out:
        typer.echo(json.dumps(result))
        return
    console.print(
        f"[green]Recorded {result['rating']}/5 feedback for mission {mission_id}[/green] (within_48h={result['within_48h']})"
    )


@pilot_app.command("kpis")
def kpis_cmd(
    state_file: str | None = typer.Option(None, "--state-file", help="Optional local state JSON path"),
    offline: bool = typer.Option(False, "--offline", help="Run against local synthetic state"),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON output"),
) -> None:
    """Display operator KPI summary (5 partners, 5 missions/partner/week, 48h feedback SLA)."""
    client = _build_client(state_file, offline)
    result = client.get_kpis()
    if json_out:
        typer.echo(json.dumps(result))
        return
    totals = result["totals"]
    console.print(
        f"[bold cyan]Pilot KPIs:[/bold cyan] partners={totals['redeemed_partners']}/5 | "
        f"missions={totals['missions_completed']}/{totals['missions_submitted']} | "
        f"feedback={totals['feedback_count']} (avg={totals['average_rating']})"
    )
