"""
Binh Phap CLI Commands — 3D Topology Engine + Standards.
"""

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.binh_phap.immortal_loop import main as run_immortal_loop
from src.binh_phap.topology import (
    TopologyEngine,
    CHAPTER_COMMANDS,
    DIAGONAL_LOOP,
    CycleLesson,
)

console = Console()
app = typer.Typer(help="Binh Phap: 3D Topology Engine + Standards")


@app.command()
def dispatch(
    auto: bool = typer.Option(False, help="Auto-dispatch without confirmation"),
) -> None:
    """Show next command to dispatch based on 3D topology state."""
    engine = TopologyEngine()
    result = engine.dispatch_next()
    action = result.get("action", "unknown")

    if action == "execute":
        cmd = result["command"]
        ch = result["chapter"]
        llm = result["llm"]
        approval = "APPROVAL REQUIRED" if result["needs_approval"] else "auto"
        console.print(Panel(
            f"[bold]/{cmd}[/bold]  (Chapter {ch})\n"
            f"Dimension: {result['dimension']}  |  LLM: {llm}  |  Gate: {approval}",
            title="Next Dispatch",
            style="green",
        ))
    elif action == "execute_parallel":
        cmds = result["commands"]
        console.print(Panel(
            f"[bold]Battle Group: {result['group']}[/bold]\n"
            f"Commands: {', '.join('/' + c for c in cmds)}\n"
            f"Dimension: horizontal (parallel)",
            title="Parallel Dispatch",
            style="cyan",
        ))
    elif action == "execute_loop":
        cycle = result["cycle"]
        cmds = result["commands"]
        console.print(Panel(
            f"[bold]Diagonal Cycle #{cycle}[/bold]\n"
            f"Loop: {' → '.join('/' + c for c in cmds)}\n"
            f"Lessons: {result.get('previous_lessons', ['(first cycle)'])}",
            title="Diagonal Loop",
            style="magenta",
        ))
    elif action == "stop":
        console.print(Panel(
            f"[bold red]STOPPED[/bold red]: {result['reason']}\n"
            f"Recommendation: {result.get('recommendation', '')}",
            title="Dispatch Halted",
            style="red",
        ))
    elif action == "pause":
        console.print(Panel(
            f"Cycle {result.get('cycle', 0)} paused.\n"
            f"Recent lessons: {result.get('lessons', [])}",
            title="Diagonal Paused",
            style="yellow",
        ))
    else:
        console.print(json.dumps(result, indent=2))


@app.command()
def status() -> None:
    """Show current topology state — dimension, cycle, groups."""
    engine = TopologyEngine()
    state = engine.state

    table = Table(title="Binh Phap Topology State")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Dimension", state.get("current_dimension", "vertical"))
    table.add_row("Cycle", str(state.get("cycle_number", 0)))
    table.add_row("Next Command", f"/{state.get('next_command', 'swot')}")
    table.add_row("Auto Dispatch", str(state.get("auto_dispatch", False)))
    table.add_row("Target MRR", f"${state.get('target_mrr', 1000)}")
    table.add_row("Failures", str(engine.consecutive_failures))

    # Battle group status
    for name, group in engine.groups.items():
        table.add_row(f"Group {name}", group.status.value)

    # Cycle history count
    history = state.get("cycle_history", [])
    table.add_row("Cycles Completed", str(len(history)))
    if history:
        last = history[-1]
        table.add_row("Last MRR", f"${last['result']['mrr']}")
        table.add_row("Last Customers", str(last["result"]["customers"]))

    console.print(table)


@app.command()
def chapters() -> None:
    """Show all 13 chapters with their mapped commands."""
    chapter_names = {
        1: "Calculations", 2: "Waging War", 3: "Strategic Attack",
        4: "Disposition", 5: "Momentum", 6: "Void & Substance",
        7: "Maneuvering", 8: "Nine Variations", 9: "The March",
        10: "Terrain", 11: "Nine Situations", 12: "Fire Attack",
        13: "Intelligence",
    }
    table = Table(title="13 Chapters → Commands")
    table.add_column("Ch.", style="bold", width=4)
    table.add_column("Name", style="cyan", width=18)
    table.add_column("Commands", style="green")

    for ch in range(1, 14):
        cmds = CHAPTER_COMMANDS.get(ch, [])
        table.add_row(str(ch), chapter_names.get(ch, ""), ", ".join("/" + c for c in cmds))

    console.print(table)


@app.command()
def learn(
    mrr: float = typer.Argument(..., help="Current MRR after this cycle"),
    customers: int = typer.Argument(..., help="Current customer count"),
    lesson: str = typer.Argument(..., help="What we learned this cycle"),
) -> None:
    """Record a lesson from the current diagonal cycle."""
    engine = TopologyEngine()
    cycle_num = engine.state.get("cycle_number", 1)
    engine.record_cycle_lesson(CycleLesson(
        cycle=cycle_num,
        mrr=mrr,
        customers=customers,
        lessons=[lesson],
        adaptations=[],
    ))
    console.print(f"[green]Lesson recorded for cycle {cycle_num}[/green]")
    console.print(f"MRR: ${mrr} | Customers: {customers}")


@app.command()
def immortal() -> None:
    """The Immortal Loop: Infinite Supervisor for Standards."""
    run_immortal_loop()


@app.command()
def monitor() -> None:
    """Alias for immortal."""
    run_immortal_loop()
