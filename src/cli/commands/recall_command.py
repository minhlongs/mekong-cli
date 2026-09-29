# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/recall_command.py — Federated Memory & Semantic Recall CLI.

Provides commands for associative cross-mission recall, knowledge graph queries,
and memory mesh indexing.
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

from src.core.memory_federation import get_memory_federation_engine

console = Console()
memory_mesh_app = typer.Typer(name="memory-mesh", help="🕸️ Federated Memory Mesh & Knowledge Graph")


def register_recall_command(app: typer.Typer) -> None:
    """Register 'recall' command onto main Typer application."""

    @app.command(name="recall")
    def recall(
        query: str = typer.Argument(
            ...,
            help="Search query for cross-mission associative memory recall",
        ),
        domain: str = typer.Option(
            "all",
            "--domain",
            "-d",
            help="Federated domain: episodic, decisions, entities, patterns, or all",
        ),
        limit: int = typer.Option(
            5,
            "--limit",
            "-l",
            help="Maximum number of memory results to return",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output machine-readable JSON search results",
        ),
    ) -> None:
        """🧠 Semantic Associative Recall: Search cross-mission logs, decisions, and patterns."""
        engine = get_memory_federation_engine()
        items = engine.query(query_text=query, domain=domain, limit=limit)

        if json_output:
            print(json.dumps([item.to_dict() for item in items], indent=2))
            return

        if not items:
            console.print(f"[dim]No associative memory items found for query: '{query}' in domain '{domain}'.[/dim]")
            return

        console.print(
            Panel(
                f"[bold cyan]Query:[/bold cyan] {query}\n"
                f"[dim]Domain:[/dim] {domain} | [dim]Hits Found:[/dim] {len(items)}",
                title="Semantic Associative Recall",
                border_style="cyan",
            )
        )

        table = Table(title="Relevant Memory Artifacts", box=ROUNDED)
        table.add_column("Domain", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Title", style="bold")
        table.add_column("Content Snippet")

        for item in items:
            dom_colors = {
                "episodic": "blue",
                "decisions": "green",
                "entities": "magenta",
                "patterns": "yellow",
            }
            d_color = dom_colors.get(item.domain, "white")
            snippet = item.content[:60] + ("..." if len(item.content) > 60 else "")
            table.add_row(
                f"[{d_color}]{item.domain.upper()}[/{d_color}]",
                f"{item.relevance_score:.2f}",
                item.title,
                snippet,
            )

        console.print(table)


@memory_mesh_app.command(name="index")
def mesh_index(
    project_dir: Optional[str] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Root path of the project to index into memory mesh",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON index stats",
    ),
) -> None:
    """Index codebase entities, historical ballots, and execution patterns into memory mesh."""
    engine = get_memory_federation_engine()
    p_path = Path(project_dir).resolve() if project_dir else None
    stats = engine.index_all(project_root=p_path)

    if json_output:
        print(json.dumps(stats.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold green]✓ Memory Mesh Indexing Complete[/bold green]\n"
            f"[dim]Total Indexed Items:[/dim] {stats.total_items}\n"
            f"[dim]Knowledge Nodes:[/dim] {stats.total_nodes} | [dim]Edges:[/dim] {stats.total_edges}\n"
            f"[dim]Database:[/dim] {stats.db_path}",
            title="Memory Federation Engine",
            border_style="green",
        )
    )


@memory_mesh_app.command(name="stats")
def mesh_stats(
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON memory stats",
    ),
) -> None:
    """Display health and telemetry metrics of the federated memory subsystem."""
    engine = get_memory_federation_engine()
    stats = engine.get_stats()

    if json_output:
        print(json.dumps(stats.to_dict(), indent=2))
        return

    console.print(
        Panel(
            f"[bold cyan]Federated Memory Statistics[/bold cyan]\n"
            f"[dim]Total Items:[/dim] {stats.total_items}\n"
            f"[dim]Knowledge Graph Nodes:[/dim] {stats.total_nodes}\n"
            f"[dim]Knowledge Graph Edges:[/dim] {stats.total_edges}\n"
            f"[dim]Database:[/dim] {stats.db_path}",
            title="Memory Mesh Telemetry",
            border_style="cyan",
        )
    )

    table = Table(title="Items by Domain", box=ROUNDED)
    table.add_column("Domain", style="cyan")
    table.add_column("Count", justify="right", style="bold")

    for dom, count in stats.items_by_domain.items():
        table.add_row(dom.upper(), str(count))

    console.print(table)


@memory_mesh_app.command(name="graph")
def mesh_graph(
    entity: str = typer.Argument(
        ...,
        help="Entity name, symbol, or file path to inspect in knowledge graph",
    ),
    depth: int = typer.Option(
        2,
        "--depth",
        "-d",
        help="Traversal depth (1-4)",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON graph structure",
    ),
) -> None:
    """Traverse and display relational knowledge graph around an entity."""
    engine = get_memory_federation_engine()
    graph = engine.query_knowledge_graph(entity=entity, depth=depth)

    if json_output:
        print(json.dumps(graph, indent=2))
        return

    console.print(
        Panel(
            f"[bold cyan]Knowledge Graph Query:[/bold cyan] {entity}\n"
            f"[dim]Depth:[/dim] {depth} | [dim]Discovered Nodes:[/dim] {graph['total_nodes']} | [dim]Edges:[/dim] {graph['total_edges']}",
            title="Knowledge Graph Traversal",
            border_style="cyan",
        )
    )

    if graph["edges"]:
        table = Table(title="Discovered Relationships", box=ROUNDED)
        table.add_column("Source", style="cyan")
        table.add_column("Relation", style="bold yellow")
        table.add_column("Target", style="green")

        for edge in graph["edges"][:20]:
            table.add_row(edge["source_id"], edge["relation"], edge["target_id"])

        console.print(table)


def register_memory_mesh_command(app: typer.Typer) -> None:
    """Register 'memory-mesh' command group onto main Typer application."""
    app.add_typer(memory_mesh_app, name="memory-mesh")
