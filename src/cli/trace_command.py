"""
Vibe Coding Factory — Trace Command.

Provides `mekong trace` to display session lineage and
`mekong trace --demo` to show a sample lineage tree.
"""

from __future__ import annotations

import logging
import os

import typer
from rich.console import Console
from rich.tree import Tree

from factory.lineage import LineageTracker

logger = logging.getLogger(__name__)
console = Console()


def register_trace_command(app: typer.Typer) -> None:
    """Register the `trace` command on the given Typer app."""

    @app.command()
    def trace(
        demo: bool = typer.Option(False, "--demo", help="Show demo lineage tree."),
        session_id: str = typer.Option(
            "", "--session", "-s", help="Session ID to trace (default: current)."
        ),
    ) -> None:
        """Hien thi lineage cua session hien tai hoac demo tree."""
        if demo:
            _show_demo_tree()
            return

        sid = session_id or os.getenv("MEKONG_SESSION_ID", "")
        if not sid:
            console.print(
                "[yellow]Chua co session ID. Dung --session <id> hoac --demo.[/yellow]"
            )
            raise typer.Exit(0)

        tracker = LineageTracker(session_id=sid)
        data = tracker.get_session()
        steps = data.get("steps", [])

        if not steps:
            console.print(f"[dim]Khong co lineage cho session: {sid}[/dim]")
            raise typer.Exit(0)

        _render_lineage_tree(sid, steps)


def _render_lineage_tree(session_id: str, steps: list[dict]) -> None:
    """Render a rich Tree from lineage steps."""
    root = Tree(f"[bold cyan]Session: {session_id}[/bold cyan]")
    nodes: dict[str, Tree] = {}
    roots: list[dict] = []

    for step in steps:
        if not step.get("triggered_by"):
            roots.append(step)

    def add_step(parent_tree: Tree, step: dict) -> None:
        label = (
            f"[green]{step['layer']}[/green]/"
            f"[bold]{step['command']}[/bold] "
            f"[dim]({step['id']})[/dim]"
        )
        node = parent_tree.add(label)
        nodes[step["id"]] = node
        # Add children
        for child in steps:
            if child.get("triggered_by") == step["id"]:
                add_step(node, child)

    for step in roots:
        add_step(root, step)

    console.print(root)


def _show_demo_tree() -> None:
    """Render a hardcoded demo lineage tree."""
    root = Tree("[bold cyan]Demo Session: abc-123[/bold cyan]")

    founder_node = root.add("[green]founder[/green]/[bold]okr[/bold] [dim](a1b2)[/dim]")
    biz_node = founder_node.add(
        "[green]business[/green]/[bold]sales[/bold] [dim](c3d4)[/dim]"
    )
    prod_node = biz_node.add(
        "[green]product[/green]/[bold]roadmap[/bold] [dim](e5f6)[/dim]"
    )
    eng_node = prod_node.add(
        "[green]engineering[/green]/[bold]cook[/bold] [dim](g7h8)[/dim]"
    )
    eng_node.add(
        "[green]ops[/green]/[bold]deploy[/bold] [dim](i9j0)[/dim]"
    )
    founder_node.add(
        "[green]business[/green]/[bold]marketing[/bold] [dim](k1l2)[/dim]"
    )

    console.print("\n[bold]Demo Lineage Tree — Founder → Business → Product → Eng → Ops[/bold]")
    console.print(root)
    console.print(
        "\n[dim]Dung `mekong trace --session <id>` de xem session thuc te.[/dim]"
    )
