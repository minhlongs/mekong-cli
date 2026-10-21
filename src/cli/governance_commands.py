# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Governance CLI — ZenOS Commons kickoff surface."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.governance.proposals import GovernanceProposalSystem, Proposal
from src.governance.voting import VoteType

console = Console()
governance_app = typer.Typer(name="governance", help="Governance: propose, vote, and tally Commons amendments", no_args_is_help=False, add_completion=False, rich_markup_mode="rich")
_INSTANCE: Optional[GovernanceProposalSystem] = None
_TIER_SPECS = {
    "soft": {"threshold": "50%", "quorum": 3, "description": "Simple majority (>50%) for operational tweaks"},
    "operational": {"threshold": "66.7%", "quorum": 5, "description": "Two-thirds supermajority for service contracts"},
    "foundational": {"threshold": "75.0%", "quorum": 7, "description": "Three-fourths supermajority for constitutional boundaries"},
}


def _get_backend() -> GovernanceProposalSystem:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = GovernanceProposalSystem()
    return _INSTANCE


@governance_app.callback(invoke_without_command=True)
def governance_main(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", "-j", help="Output machine-readable JSON governance overview")) -> None:
    if ctx.invoked_subcommand is not None:
        return
    proposals = _get_backend().list_proposals()
    if json_output:
        typer.echo(json.dumps({"status": "HEALTHY", "tier_specs": _TIER_SPECS, "total_proposals": len(proposals), "proposals": [p.to_dict() for p in proposals]}, indent=2))
        return
    from rich.box import ROUNDED
    grid = Table.grid(expand=True, padding=(0, 2))
    grid.add_column(justify="left")
    grid.add_column(justify="left")
    grid.add_row(f"🏛️ [bold]Total Proposals:[/bold] [bold cyan]{len(proposals)}[/bold cyan]", "⚡ [bold]Status:[/bold] [bold green]HEALTHY[/bold green]")
    grid.add_row("📜 [bold]Tiers:[/bold] Soft (50%) | Operational (66.7%) | Foundational (75%)", "🗳️ [bold]Quorums:[/bold] Soft (3) | Oper (5) | Found (7)")
    console.print(Panel(grid, title="[bold green]🏛️ ZenOS Commons Constitutional Governance[/bold green]", subtitle="[dim]Consensus & Amendment Ledger[/dim]", border_style="green", box=ROUNDED))
    if proposals:
        table = Table(title="Active & Recent Proposals", box=ROUNDED)
        for col in ("ID", "Tier", "Status", "Title", "Proposer", "Sponsors"):
            table.add_column(col, style="cyan" if col == "ID" else None)
        for p in proposals[:10]:
            tc = {"soft": "blue", "operational": "yellow", "foundational": "red"}.get(p.tier, "white")
            table.add_row(p.id, f"[{tc}]{p.tier.upper()}[/{tc}]", p.status, p.title[:40] + ("…" if len(p.title) > 40 else ""), p.proposer, str(len(p.co_sponsors)))
        console.print(table)


@governance_app.command("status")
def governance_status(json_output: bool = typer.Option(False, "--json", "-j", help="JSON output")) -> None:
    proposals = _get_backend().list_proposals()
    if json_output:
        typer.echo(json.dumps({"status": "HEALTHY", "total_proposals": len(proposals), "tier_specifications": {"soft": {"threshold_percent": 50.0, "quorum_min": 3}, "operational": {"threshold_percent": 66.7, "quorum_min": 5}, "foundational": {"threshold_percent": 75.0, "quorum_min": 7}}}, indent=2))
        return
    console.print(f"[bold green]Governance Status:[/bold green] HEALTHY | Total proposals: {len(proposals)}")


@governance_app.command("propose")
def governance_propose(
    title: str = typer.Argument(..., help="Proposal title"), description: str = typer.Argument(..., help="Description / rationale"),
    text: str = typer.Argument(..., help="Proposed amendment text"), proposer: str = typer.Option("founder", "--from", "-f", help="Member ID proposing"),
    tier: str = typer.Option("soft", "--tier", "-t", help="Tier: soft | operational | foundational"),
    co_sponsor: list[str] = typer.Option([], "--co-sponsor", help="Co-sponsor member IDs"), json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    ts, senate = _timestamp(), _get_backend()
    try:
        proposal = senate.propose(title=title, description=description, text=text, proposer=proposer, tier=tier, co_sponsors=co_sponsor)
    except ValueError as exc:
        _bad(str(exc))
    _emit(_to_display(senate.submit(proposal.id)), "Proposal Submitted", "green", json_output, ts)


@governance_app.command("vote")
def governance_vote(
    proposal_id: str = typer.Argument(..., help="Proposal ID"), voter: str = typer.Option("founder", "--from", "-f", help="Voter ID"),
    choice: str = typer.Option("yes", "--choice", "-c", help="yes | no | abstain"), window_hours: int = typer.Option(168, "--window", help="Voting window (hours)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    _timestamp()
    senate = _get_backend()
    try:
        vtype = _parse_vote_type(choice)
    except ValueError as exc:
        _bad(str(exc))
    try:
        proposal, voting_system = senate.start_vote(proposal_id)
    except ValueError as exc:
        _not_found(proposal_id, str(exc))
    voting_system.config.time_window_hours = window_hours
    try:
        vote = voting_system.cast_vote(voter_id=voter, proposal_id=proposal_id, vote_type=vtype)
    except Exception as exc:
        _bad(str(exc))
    typer.echo(json.dumps({"proposal_id": proposal_id, "voter": voter, "choice": vtype.value, "weight": vote.weight, "timestamp": vote.timestamp.isoformat()}, indent=2)) if json_output else console.print(Panel(f"Proposal: {proposal.title}\nID: {proposal.id}\nVoter: {voter}\nChoice: [bold]{vtype.value.upper()}[/bold]  (weight: {vote.weight:.3f})\n", title="Vote Recorded", border_style="green"))


@governance_app.command("tally")
def governance_tally(proposal_id: str = typer.Argument(..., help="Proposal ID"), json_output: bool = typer.Option(False, "--json", "-j", help="JSON output")) -> None:
    ts = _timestamp()
    try:
        proposal, results = _get_backend().tally(proposal_id)
    except ValueError as exc:
        _not_found(proposal_id, str(exc))
    typer.echo(json.dumps(proposal.to_dict(), indent=2)) if json_output else _render_tally(proposal, results, ts)


@governance_app.command("list")
def governance_list(status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"), json_output: bool = typer.Option(False, "--json", "-j", help="JSON output")) -> None:
    _timestamp()
    proposals = _get_backend().list_proposals(status=status)
    if json_output:
        typer.echo(json.dumps([p.to_dict() for p in proposals], indent=2))
        return
    if not proposals:
        console.print("[dim]No proposals found.[/dim]")
        return
    table = Table(title="Governance Proposals", show_lines=False)
    for col in ("ID", "Tier", "Status", "Title", "Proposer", "Sponsors", "Submitted"):
        table.add_column(col)
    for p in proposals:
        tc = {"soft": "blue", "operational": "yellow", "foundational": "red"}.get(p.tier, "white")
        table.add_row(p.id, f"[{tc}]{p.tier.upper()}[/{tc}]", p.status, p.title[:40] + ("…" if len(p.title) > 40 else ""), p.proposer, str(len(p.co_sponsors)), p.submitted_at.isoformat() if p.submitted_at else "—")
    console.print(table)


def _render_tally(proposal: Proposal, results, ts: str) -> None:
    console.print(Panel(
        f"[bold]Proposal:[/bold] {proposal.title}\n[bold]ID:[/bold] {proposal.id}  [bold]Tier:[/bold] {proposal.tier.upper()}\n\n"
        f"[bold]Votes:[/bold]\n  YES:      {results.yes_weight:>7.3f}\n  NO:       {results.no_weight:>7.3f}\n"
        f"  ABSTAIN:  {results.abstain_weight:>7.3f}\n  RECUSE:   {results.recuse_weight:>7.3f}\n\n"
        f"[bold]Participants:[/bold] {results.total_participants}\n[bold]Quorum:[/bold] {'YES' if results.quorum_met else 'NO'}  [bold]Threshold:[/bold] {'YES' if results.threshold_met else 'NO'}\n\n"
        f"[bold]Result:[/bold] [{'green' if results.passed else 'red'}]{'PASSED' if results.passed else 'FAILED'}[/]",
        title="Tally", border_style="green" if results.passed else "red",
    ))


def _emit(proposal: Proposal, title: str, style: str, json_output: bool, ts: str) -> None:
    typer.echo(json.dumps(proposal.to_dict(), indent=2)) if json_output else console.print(Panel(f"[bold]{proposal.title}[/bold]\nID: {proposal.id}\nTier: {proposal.tier.upper()}  Status: {proposal.status}\n", title=title, border_style=style))


def _to_display(proposal: Proposal) -> Proposal:
    return proposal


def _parse_vote_type(text: str) -> "VoteType":
    mapping = {"yes": VoteType.YES, "no": VoteType.NO, "abstain": VoteType.ABSTAIN, "recuse": VoteType.RECUSE}
    if text.strip().lower() not in mapping:
        raise ValueError(f"choice must be one of {sorted(mapping)}; got {text!r}")
    return mapping[text.strip().lower()]


def _bad(reason: str) -> None:
    console.print(f"[red]Error:[/red] {reason}")
    raise typer.Exit(1)


def _not_found(proposal_id: str, reason: str) -> None:
    console.print(f"[red]Not found:[/red] {proposal_id} ({reason})")
    raise typer.Exit(1)


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def register(root: typer.Typer) -> None:
    root.add_typer(governance_app, name="governance", help="ZenOS Commons governance (propose / vote / tally / list)")
