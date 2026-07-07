"""Governance CLI — ZenOS Commons kickoff surface.

Follows patterns from:
- `src/cli/constitution_command.py` (rich + typer, JSON + human modes)
- `src/commands/core_commands.py` (flat command registration)
"""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.governance.proposals import (
    GovernanceProposalSystem,
    Proposal,
)
from src.governance.voting import VoteType

console = Console()
governance_app = typer.Typer(
    name="governance",
    help="Governance: propose, vote, and tally Commons amendments",
)


# Optionally lazily-bound backend; provides deterministic behavior even
# when no live principals are registered (kickoff scaffold mode).
_INSTANCE: Optional[GovernanceProposalSystem] = None


def _get_backend() -> GovernanceProposalSystem:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = GovernanceProposalSystem()
    return _INSTANCE


@governance_app.command("propose")
def governance_propose(
    title: str = typer.Argument(..., help="Proposal title"),
    description: str = typer.Argument(..., help="Description / rationale"),
    text: str = typer.Argument(..., help="Proposed amendment text"),
    proposer: str = typer.Option("founder", "--from", "-f", help="Member ID proposing"),
    tier: str = typer.Option(
        "soft",
        "--tier",
        "-t",
        help="Tier: soft | operational | foundational",
    ),
    co_sponsor: list[str] = typer.Option(
        [], "--co-sponsor", help="Co-sponsor member IDs (repeatable)"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Draft + submit a new constitutional amendment proposal.

    Kicks off a DRAFT → SUBMITTED transition. Start voting later with
    `mekong governance vote <id>`.
    """
    ts = _timestamp()
    senate = _get_backend()
    try:
        proposal = senate.propose(
            title=title,
            description=description,
            text=text,
            proposer=proposer,
            tier=tier,
            co_sponsors=co_sponsor,
        )
    except ValueError as exc:
        _bad(str(exc))

    # Auto-submit — during kickoff there's no multi-stakeholder review gate.
    proposal = _to_display(senate.submit(proposal.id))
    _emit(proposal, "Proposal Submitted", "green", json_output, ts)


@governance_app.command("vote")
def governance_vote(
    proposal_id: str = typer.Argument(..., help="Proposal ID"),
    voter: str = typer.Option("founder", "--from", "-f", help="Voter ID"),
    choice: str = typer.Option("yes", "--choice", "-c", help="yes | no | abstain"),
    window_hours: int = typer.Option(168, "--window", help="Voting window (hours)"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Start voting on a proposal and record a single vote."""
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

    # Build override VotingSystem with the requested window in case the
    # existing voting window inside the facade doesn't match.
    voting_system.config.time_window_hours = window_hours
    try:
        vote = voting_system.cast_vote(
            voter_id=voter,
            proposal_id=proposal_id,
            vote_type=vtype,
        )
    except Exception as exc:  # pylint: disable=broad-except
        _bad(str(exc))

    if json_output:
        typer.echo(
            __import__("json").dumps(
                {
                    "proposal_id": proposal_id,
                    "voter": voter,
                    "choice": vtype.value,
                    "weight": vote.weight,
                    "timestamp": vote.timestamp.isoformat(),
                },
                indent=2,
            )
        )
    else:
        console.print(
            Panel(
                f"Proposal: {proposal.title}\n"
                f"ID: {proposal.id}\n"
                f"Voter: {voter}\n"
                f"Choice: [bold]{vtype.value.upper()}[/bold]  (weight: {vote.weight:.3f})\n",
                title="Vote Recorded",
                border_style="green",
            )
        )


@governance_app.command("tally")
def governance_tally(
    proposal_id: str = typer.Argument(..., help="Proposal ID"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """Tally votes and finalize a proposal."""
    ts = _timestamp()
    senate = _get_backend()
    try:
        proposal, results = senate.tally(proposal_id)
    except ValueError as exc:
        _not_found(proposal_id, str(exc))

    if json_output:
        typer.echo(__import__("json").dumps(proposal.to_dict(), indent=2))
    else:
        _render_tally(proposal, results, ts)


@governance_app.command("list")
def governance_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
) -> None:
    """List all Commons governance proposals."""
    _timestamp()
    senate = _get_backend()
    proposals = senate.list_proposals(status=status)

    if json_output:
        typer.echo(__import__("json").dumps([p.to_dict() for p in proposals], indent=2))
        return

    if not proposals:
        console.print("[dim]No proposals found.[/dim]")
        return

    table = Table(title="Governance Proposals", show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Tier", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Title", no_wrap=True)
    table.add_column("Proposer", style="dim")
    table.add_column("Sponsors", justify="right")
    table.add_column("Submitted", justify="right")

    for p in proposals:
        tier_color = {"soft": "blue", "operational": "yellow", "foundational": "red"}.get(
            p.tier, "white"
        )
        table.add_row(
            p.id,
            f"[{tier_color}]{p.tier.upper()}[/{tier_color}]",
            p.status,
            p.title[:40] + ("…" if len(p.title) > 40 else ""),
            p.proposer,
            str(len(p.co_sponsors)),
            (p.submitted_at.isoformat() if p.submitted_at else "—"),
        )
    console.print(table)


# ---- display helpers ----

def _render_tally(proposal: Proposal, results, ts: str) -> None:
    panel = Panel(
        f"[bold]Proposal:[/bold] {proposal.title}\n"
        f"[bold]ID:[/bold] {proposal.id}  [bold]Tier:[/bold] {proposal.tier.upper()}\n\n"
        f"[bold]Votes:[/bold]\n"
        f"  YES:      {results.yes_weight:>7.3f}\n"
        f"  NO:       {results.no_weight:>7.3f}\n"
        f"  ABSTAIN:  {results.abstain_weight:>7.3f}\n"
        f"  RECUSE:   {results.recuse_weight:>7.3f}\n\n"
        f"[bold]Participants:[/bold] {results.total_participants}\n"
        f"[bold]Quorum:[/bold] {'YES' if results.quorum_met else 'NO'}  "
        f"[bold]Threshold:[/bold] {'YES' if results.threshold_met else 'NO'}\n\n"
        f"[bold]Result:[/bold] [{('green' if results.passed else 'red')}]"
        f"{'PASSED' if results.passed else 'FAILED'}[/]",
        title="Tally",
        border_style="green" if results.passed else "red",
    )
    console.print(panel)


def _emit(proposal: Proposal, title: str, style: str, json_output: bool, ts: str) -> None:
    if json_output:
        typer.echo(__import__("json").dumps(proposal.to_dict(), indent=2))
    else:
        console.print(
            Panel(
                f"[bold]{proposal.title}[/bold]\nID: {proposal.id}\n"
                f"Tier: {proposal.tier.upper()}  Status: {proposal.status}\n",
                title=title,
                border_style=style,
            )
        )


def _to_display(proposal: Proposal) -> Proposal:
    return proposal


def _parse_vote_type(text: str) -> "VoteType":
    mapping = {
        "yes": VoteType.YES,
        "no": VoteType.NO,
        "abstain": VoteType.ABSTAIN,
        "recuse": VoteType.RECUSE,
    }
    key = text.strip().lower()
    if key not in mapping:
        raise ValueError(
            f"choice must be one of {sorted(mapping)}; got {text!r}"
        )
    return mapping[key]


def _bad(reason: str) -> None:
    console.print(f"[red]Error:[/red] {reason}")
    raise typer.Exit(1)


def _not_found(proposal_id: str, reason: str) -> None:
    console.print(f"[red]Not found:[/red] {proposal_id} ({reason})")
    raise typer.Exit(1)


def _timestamp() -> str:
    return __import__("datetime").datetime.now().isoformat(timespec="seconds")


def register(root: typer.Typer) -> None:
    """Register `governance` sub-app onto a root Typer.

    Registration pattern mirrors:
    - `src/cli/cook_command.register_cook_command(root)`
    - `src/cli/commands/company_init.register(root)` (was package import)
    """
    root.add_typer(
        governance_app,
        name="governance",
        help="ZenOS Commons governance (propose / vote / tally / list)",
    )
