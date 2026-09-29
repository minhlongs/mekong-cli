# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/consensus_command.py — Multi-Agent Consensus Protocol & Debate Mesh CLI.

Coordinates structured multi-agent debate, quorum voting (majority, supermajority,
unanimous, and weighted roles), synthetic consensus resolution, and cryptographic
ballot logging.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.consensus_bridge import get_consensus_bridge

console = Console()
consensus_app = typer.Typer(name="consensus", help="🗳️ Multi-Agent Consensus Protocol & Swarm Debate")


@consensus_app.command(name="vote")
def consensus_vote(
    proposal: str = typer.Argument(
        ...,
        help="The technical, strategic, or governance proposal to vote upon",
    ),
    agents: Optional[str] = typer.Option(
        None,
        "--agents",
        "-a",
        help="Comma-separated list of agent roles (e.g. cto,sre,cfo,pm,ceo)",
    ),
    quorum: str = typer.Option(
        "majority",
        "--quorum",
        "-q",
        help="Quorum rule: majority, supermajority, unanimous, or weighted",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON ballot result",
    ),
) -> None:
    """Execute a multi-agent quorum vote on a proposal."""
    bridge = get_consensus_bridge()
    agent_list = [a.strip() for a in agents.split(",")] if agents else None

    ballot = bridge.create_vote(proposal=proposal, agents=agent_list, quorum=quorum)

    if json_output:
        print(json.dumps(ballot.to_dict(), indent=2))
        return

    status_color = "green" if ballot.passed else "red"
    status_label = "PASSED" if ballot.passed else "REJECTED"

    console.print(
        Panel(
            f"[bold cyan]Proposal:[/bold cyan] {ballot.proposal}\n"
            f"[bold {status_color}]Result: {status_label}[/bold {status_color}] | [dim]Quorum Rule:[/dim] {ballot.quorum_type}\n"
            f"[dim]Tally:[/dim] [green]{ballot.yes_votes} Yes[/green] / [red]{ballot.no_votes} No[/red] / [yellow]{ballot.abstain_votes} Abstain[/yellow] "
            f"([dim]Weighted: {ballot.weighted_yes}/{ballot.weighted_total}[/dim])\n"
            f"[dim]Ballot ID:[/dim] {ballot.ballot_id}\n"
            f"[dim]SHA-256 Ledger Hash:[/dim] {ballot.ballot_hash}",
            title="Consensus Vote Outcome",
            border_style=status_color,
        )
    )

    table = Table(title="Agent Ballots & Justifications", box=ROUNDED)
    table.add_column("Agent", style="cyan")
    table.add_column("Vote", style="bold")
    table.add_column("Weight", justify="right")
    table.add_column("Justification")

    for v in ballot.votes:
        v_color = "green" if v.vote == "yes" else ("red" if v.vote == "no" else "yellow")
        table.add_row(
            v.agent_id.upper(),
            f"[{v_color}]{v.vote.upper()}[/{v_color}]",
            str(v.weight),
            v.justification,
        )

    console.print(table)


@consensus_app.command(name="debate")
def consensus_debate(
    topic: str = typer.Argument(
        ...,
        help="The technical or strategic topic to debate",
    ),
    proponent: str = typer.Option(
        "cto",
        "--proponent",
        "-p",
        help="Proponent agent role (e.g. cto, cmo)",
    ),
    opponent: str = typer.Option(
        "sre",
        "--opponent",
        "-o",
        help="Opponent agent role (e.g. sre, cfo)",
    ),
    moderator: str = typer.Option(
        "ceo",
        "--moderator",
        "-m",
        help="Moderator agent role (default: ceo)",
    ),
    rounds: int = typer.Option(
        2,
        "--rounds",
        "-r",
        help="Number of debate rounds (1-5)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON debate transcript",
    ),
) -> None:
    """Conduct a structured multi-round debate with synthetic consensus resolution."""
    bridge = get_consensus_bridge()
    session = bridge.conduct_debate(
        topic=topic,
        proponent=proponent,
        opponent=opponent,
        moderator=moderator,
        rounds=rounds,
    )

    if json_output:
        print(json.dumps(session.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold cyan]Topic:[/bold cyan] {session.topic}\n"
            f"[dim]Participants:[/dim] [green]{proponent.upper()} (Pro)[/green] vs [red]{opponent.upper()} (Con)[/red] | [dim]Moderator:[/dim] [magenta]{moderator.upper()}[/magenta]\n"
            f"[dim]Rounds:[/dim] {session.rounds} | [dim]Consensus Score:[/dim] [bold green]{session.consensus_score}/100[/bold green]",
            title="Multi-Agent Debate Session",
            border_style="cyan",
        )
    )

    for turn in session.turns:
        if turn.stance == "pro":
            style = "green"
            title = f"Round {turn.round_number}: {turn.speaker.upper()} ({turn.role})"
        elif turn.stance == "con":
            style = "yellow"
            title = f"Round {turn.round_number}: {turn.speaker.upper()} ({turn.role})"
        else:
            style = "magenta"
            title = f"Synthesis: {turn.speaker.upper()} ({turn.role})"

        console.print(Panel(turn.argument, title=title, border_style=style))

    console.print(
        Panel(
            f"[bold]Recommended Action:[/bold]\n{session.recommended_action}\n\n"
            f"[dim]Session ID:[/dim] {session.session_id}",
            title="Consensus Synthesis & Directive",
            border_style="green",
        )
    )


@consensus_app.command(name="history")
def consensus_history(
    limit: int = typer.Option(
        10,
        "--limit",
        "-l",
        help="Maximum number of historical records to display",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON history",
    ),
) -> None:
    """View recent consensus ballots and debate sessions from local ledger."""
    bridge = get_consensus_bridge()
    ballots = bridge.list_ballots(limit=limit)
    debates = bridge.list_debates(limit=limit)

    if json_output:
        res = {
            "ballots": [b.to_dict() for b in ballots],
            "debates": [d.to_dict() for d in debates],
        }
        print(json.dumps(res, indent=2))
        return

    b_table = Table(title="Recent Consensus Ballots", box=ROUNDED)
    b_table.add_column("Ballot ID", style="dim")
    b_table.add_column("Proposal", style="bold")
    b_table.add_column("Quorum")
    b_table.add_column("Status")
    b_table.add_column("Ledger Hash", style="dim")

    for b in ballots:
        status_color = "green" if b.passed else "red"
        status_text = f"[{status_color}]{'PASSED' if b.passed else 'REJECTED'}[/{status_color}]"
        b_table.add_row(
            b.ballot_id,
            b.proposal[:45] + ("..." if len(b.proposal) > 45 else ""),
            b.quorum_type,
            status_text,
            b.ballot_hash[:16] + "...",
        )

    console.print(b_table)

    d_table = Table(title="Recent Debate Sessions", box=ROUNDED)
    d_table.add_column("Session ID", style="dim")
    d_table.add_column("Topic", style="bold")
    d_table.add_column("Pro vs Con")
    d_table.add_column("Score", justify="right")
    d_table.add_column("Recommendation")

    for d in debates:
        d_table.add_row(
            d.session_id,
            d.topic[:40] + ("..." if len(d.topic) > 40 else ""),
            f"{d.proponent.upper()} vs {d.opponent.upper()}",
            f"{d.consensus_score:.1f}",
            d.recommended_action[:50] + ("..." if len(d.recommended_action) > 50 else ""),
        )

    console.print(d_table)


def register_consensus_command(app: typer.Typer) -> None:
    """Register the 'consensus' command group onto the main Typer application."""
    app.add_typer(consensus_app, name="consensus")
