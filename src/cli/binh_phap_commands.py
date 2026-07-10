"""
Binh Phap CLI Commands — 3D Topology Engine + Standards.
"""

import json
import typer
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.binh_phap.dag import CHAPTER_NODE_COUNT, load_dag
from src.binh_phap.executor import Executor, ExecutionState
from src.binh_phap.immortal_loop import main as run_immortal_loop
from src.binh_phap.topology import (
    TopologyEngine,
    CHAPTER_COMMANDS,
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


_dag = typer.Typer(help="DAG: run and inspect the 13-chapter chain")


@_dag.command("status")
def dag_status(
    state_path: str = typer.Option(".mekong/binh-phap-state.json"),
    json_output: bool = typer.Option(False, "--json", "-j"),
) -> None:
    """Show execution status of every chapter."""
    dag = load_dag()
    state = ExecutionState.load(Path(state_path))
    failed = dict(state.failed)

    if json_output:
        rows = []
        for ch in range(1, CHAPTER_NODE_COUNT + 1):
            node = dag.chapters.get(ch)
            res = state.results.get(ch)
            rows.append(
                {
                    "chapter": ch,
                    "name": node.name if node else "?",
                    "status": res.status if res else "pending",
                    "error": res.error if res else "",
                }
            )
        console.print_json(
            json.dumps({"completed": sorted(state.completed), "chapters": rows})
        )
        return

    table = Table(title="Binh Phap DAG Status")
    table.add_column("#", justify="right")
    table.add_column("Chapter")
    table.add_column("Agent")
    table.add_column("Status")
    table.add_column("Error")
    for ch in range(1, CHAPTER_NODE_COUNT + 1):
        node = dag.chapters.get(ch)
        if not node:
            continue
        res = state.results.get(ch)
        if ch in state.completed:
            st = "[green]✓ done[/]"
            err = ""
        elif ch in failed:
            st = "[red]✗ failed[/]"
            err = failed[ch][:40]
        elif ch in dag.human_only:
            st = "[yellow]⏸ human[/]"
            err = ""
        else:
            st = "[dim]… pending[/]"
            err = ""
        table.add_row(str(ch), node.name, node.primary_agent, st, err)
    console.print(table)
    console.print(f"\n[bold]Completed:[/] {len(state.completed)}/{CHAPTER_NODE_COUNT}")


@_dag.command("run")
def dag_run(
    chapter: Optional[int] = typer.Argument(None, help="Start chapter"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    state_path: str = typer.Option(".mekong/binh-phap-state.json"),
) -> None:
    """Run the DAG from the beginning (or a specific chapter)."""
    exec_ = Executor(
        dag=load_dag(),
        state_path=Path(state_path),
        dry_run=dry_run,
    )
    start = chapter
    if start is None:
        # resume hint: pick next pending
        st = ExecutionState.load(Path(state_path))
        if st.completed and max(st.completed) < CHAPTER_NODE_COUNT:
            start = max(st.completed) + 1
    console.print(f"[bold]Running DAG (start={start or 'first pending'}, dry={dry_run})[/]\n")
    results = exec_.run(start_chapter=start)
    for ch in sorted(results):
        r = results[ch]
        icon = {"success": "✓", "failed": "✗", "skipped": "→"}.get(r.status, "?")
        line = f"  Ch {ch:2d} {icon} {r.status}"
        if r.error:
            line += f"  ({r.error[:50]})"
        console.print(line)
    n = sum(1 for r in results.values() if r.status == "success")
    console.print(f"\n[bold]Result:[/] {n} succeeded out of {len(results)} executed")


@_dag.command("resume")
def dag_resume(
    dry_run: bool = typer.Option(False, "--dry-run"),
    state_path: str = typer.Option(".mekong/binh-phap-state.json"),
) -> None:
    """Resume execution from last persisted completed chapter."""
    exec_ = Executor(
        dag=load_dag(),
        state_path=Path(state_path),
        dry_run=dry_run,
    )
    console.print("[bold]Resuming from persisted state…[/]\n")
    results = exec_.resume()
    for ch in sorted(results):
        r = results[ch]
        icon = {"success": "✓", "failed": "✗", "skipped": "→"}.get(r.status, "?")
        console.print(f"  Ch {ch:2d} {icon} {r.status}")
    n = sum(1 for r in results.values() if r.status == "success")
    console.print(f"\n[bold]Resumed:[/] {n} succeeded" + (f" / {len(results)} executed" if results else ""))


@_dag.command("validate")
def dag_validate(
    os_path: Optional[str] = typer.Option(None, "--os-path", help="Custom OS manifest path"),
) -> None:
    """Validate OS manifest + DAG integrity (chapters, agents, edges)."""
    errors: list[str] = []
    try:
        dag = load_dag(os_path)
    except Exception as exc:  # pylint: disable=broad-except
        console.print(f"[red]Load failed:[/] {exc}")
        raise typer.Exit(1)  # noqa: TRY200
    for i in range(1, CHAPTER_NODE_COUNT + 1):
        if i not in dag.chapters:
            errors.append(f"Chapter {i} missing from manifest")
    for ch_num, node in dag.chapters.items():
        if not node.primary_agent:
            errors.append(f"Chapter {ch_num} has no primary_agent")
    for ch, pres in dag.edges.items():
        for p in pres:
            if p not in dag.chapters:
                errors.append(f"Edge from ch{p} → {ch} references unknown chapter")
    if errors:
        console.print("[red]Validation errors:[/]")
        for e in errors:
            console.print(f"  ✗ {e}")
        raise typer.Exit(1)
    console.print(
        f"[green]DAG valid — {len(dag.chapters)} chapters, "
        f"human_only: {sorted(dag.human_only)}[/]"
    )
    console.print(f"Execution order: {dag.topological_order()}")


app.add_typer(
    _dag,
    name="dag",
    help="13-chapter DAG execution chain",
)

# D5: chain subcommands — end-to-end chapter runner
chain_app = typer.Typer(help="Run Binh Phap chain end-to-end")

@chain_app.command("next")
def chain_next(
 state_path: str = typer.Option(".mekong/binh-phap-state.json"),
) -> None:
 """Show next runnable chapter (deps satisfied, not human-only)."""
 from src.binh_phap.executor import ExecutionState
 dag = load_dag()
 state = ExecutionState.load(Path(state_path))
 ready = [
 ch for ch in dag.topological_order()
 if ch not in state.completed
 and ch not in dag.human_only
 and set(dag.predecessors(ch)).issubset(state.completed)
 ]
 if not ready:
  console.print("[yellow]No runnable chapters — all done or blocked[/]")
  return
 node = dag.chapters.get(ready[0])
 console.print(
  f"[bold]Next:[/] Ch {ready[0]} — {node.name if node else '?'} "
  f"via {node.primary_agent if node else '?'}"
 )

@chain_app.command("reset")
def chain_reset(
 state_path: str = typer.Option(".mekong/binh-phap-state.json"),
 dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
 """Reset state file to start fresh."""
 p = Path(state_path)
 if dry_run:
  console.print(f"[dry-run] Would delete {p}")
  return
 if p.exists():
  p.unlink()
  console.print(f"[green]State reset — {p} deleted[/]")
 else:
  console.print(f"[dim]No state file at {p}[/]")

app.add_typer(
 chain_app,
 name="chain",
 help="End-to-end Binh Phap chain",
)

@app.command()
def daemon(
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show actions without executing"),
    cycles: int = typer.Option(0, help="Max cycles (0=infinite)"),
    interval: int = typer.Option(10, help="Seconds between cycles"),
) -> None:
    """CTO Daemon: Autonomous 3D topology dispatch loop for M1 Max."""
    from src.binh_phap.cto_daemon import run_daemon
    run_daemon(dry_run=dry_run, max_cycles=cycles, interval_seconds=interval)
