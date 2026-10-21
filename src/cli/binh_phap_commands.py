# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap CLI Commands — 3D Topology Engine + Standards."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.binh_phap.dag import CHAPTER_NODE_COUNT, load_dag
from src.core.binh_phap.executor import ExecutionState, Executor
from src.core.binh_phap.immortal_loop import main as run_immortal_loop
from src.core.binh_phap.topology import CHAPTER_COMMANDS, CycleLesson, TopologyEngine

console = Console()
app = typer.Typer(help="Binh Phap: 3D Topology Engine + Standards")
_dag = typer.Typer(help="DAG: run and inspect the 13-chapter chain")
chain_app = typer.Typer(help="Run Binh Phap chain end-to-end")


@app.command()
def dispatch(auto: bool = typer.Option(False, help="Auto-dispatch without confirmation")) -> None:
    """Show next command to dispatch based on 3D topology state."""
    result = TopologyEngine().dispatch_next()
    action = result.get("action", "unknown")
    if action == "execute":
        approval = "APPROVAL REQUIRED" if result["needs_approval"] else "auto"
        console.print(Panel(f"[bold]/{result['command']}[/bold]  (Chapter {result['chapter']})\nDimension: {result['dimension']}  |  LLM: {result['llm']}  |  Gate: {approval}", title="Next Dispatch", style="green"))
    elif action == "execute_parallel":
        console.print(Panel(f"[bold]Battle Group: {result['group']}[/bold]\nCommands: {', '.join('/' + c for c in result['commands'])}\nDimension: horizontal (parallel)", title="Parallel Dispatch", style="cyan"))
    elif action == "execute_loop":
        console.print(Panel(f"[bold]Diagonal Cycle #{result['cycle']}[/bold]\nLoop: {' → '.join('/' + c for c in result['commands'])}\nLessons: {result.get('previous_lessons', ['(first cycle)'])}", title="Diagonal Loop", style="magenta"))
    elif action == "stop":
        console.print(Panel(f"[bold red]STOPPED[/bold red]: {result['reason']}\nRecommendation: {result.get('recommendation', '')}", title="Dispatch Halted", style="red"))
    elif action == "pause":
        console.print(Panel(f"Cycle {result.get('cycle', 0)} paused.\nRecent lessons: {result.get('lessons', [])}", title="Diagonal Paused", style="yellow"))
    else:
        console.print(json.dumps(result, indent=2))


@app.command()
def status() -> None:
    """Show current topology state — dimension, cycle, groups."""
    engine = TopologyEngine()
    state, history = engine.state, engine.state.get("cycle_history", [])
    table = Table(title="Binh Phap Topology State")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    rows = [
        ("Dimension", state.get("current_dimension", "vertical")), ("Cycle", str(state.get("cycle_number", 0))),
        ("Next Command", f"/{state.get('next_command', 'swot')}"), ("Auto Dispatch", str(state.get("auto_dispatch", False))),
        ("Target MRR", f"${state.get('target_mrr', 1000)}"), ("Failures", str(engine.consecutive_failures)),
    ] + [(f"Group {n}", g.status.value) for n, g in engine.groups.items()] + [("Cycles Completed", str(len(history)))]
    if history:
        rows += [("Last MRR", f"${history[-1]['result']['mrr']}"), ("Last Customers", str(history[-1]["result"]["customers"]))]
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)


@app.command()
def chapters() -> None:
    """Show all 13 chapters with their mapped commands."""
    names = {1: "Calculations", 2: "Waging War", 3: "Strategic Attack", 4: "Disposition", 5: "Momentum", 6: "Void & Substance", 7: "Maneuvering", 8: "Nine Variations", 9: "The March", 10: "Terrain", 11: "Nine Situations", 12: "Fire Attack", 13: "Intelligence"}
    table = Table(title="13 Chapters → Commands")
    for col, kw in [("Ch.", {"style": "bold", "width": 4}), ("Name", {"style": "cyan", "width": 18}), ("Commands", {"style": "green"})]:
        table.add_column(col, **kw)
    for ch in range(1, 14):
        table.add_row(str(ch), names.get(ch, ""), ", ".join("/" + c for c in CHAPTER_COMMANDS.get(ch, [])))
    console.print(table)


@app.command()
def learn(mrr: float = typer.Argument(..., help="Current MRR"), customers: int = typer.Argument(..., help="Customer count"), lesson: str = typer.Argument(..., help="Lesson learned")) -> None:
    """Record a lesson from the current diagonal cycle."""
    engine = TopologyEngine()
    cycle_num = engine.state.get("cycle_number", 1)
    engine.record_cycle_lesson(CycleLesson(cycle=cycle_num, mrr=mrr, customers=customers, lessons=[lesson], adaptations=[]))
    console.print(f"[green]Lesson recorded for cycle {cycle_num}[/green]\nMRR: ${mrr} | Customers: {customers}")


app.command("immortal")(run_immortal_loop)
app.command("monitor")(run_immortal_loop)


@_dag.command("status")
def dag_status(state_path: str = typer.Option(".mekong/binh-phap-state.json"), json_output: bool = typer.Option(False, "--json", "-j")) -> None:
    dag, state = load_dag(), ExecutionState.load(Path(state_path))
    failed = dict(state.failed)
    if json_output:
        rows = [{"chapter": ch, "name": dag.chapters[ch].name if ch in dag.chapters else "?", "status": state.results[ch].status if ch in state.results else "pending", "error": state.results[ch].error if ch in state.results else ""} for ch in range(1, CHAPTER_NODE_COUNT + 1)]
        console.print_json(json.dumps({"completed": sorted(state.completed), "chapters": rows}))
        return
    table = Table(title="Binh Phap DAG Status")
    for col in ("#", "Chapter", "Agent", "Status", "Error"):
        table.add_column(col, justify="right" if col == "#" else "left")
    for ch in range(1, CHAPTER_NODE_COUNT + 1):
        if node := dag.chapters.get(ch):
            st, err = ("[green]✓ done[/]", "") if ch in state.completed else (("[red]✗ failed[/]", failed[ch][:40]) if ch in failed else (("[yellow]⏸ human[/]", "") if ch in dag.human_only else ("[dim]… pending[/]", "")))
            table.add_row(str(ch), node.name, node.primary_agent, st, err)
    console.print(table)
    console.print(f"\n[bold]Completed:[/] {len(state.completed)}/{CHAPTER_NODE_COUNT}")


@_dag.command("run")
def dag_run(chapter: Optional[int] = typer.Argument(None, help="Start chapter"), dry_run: bool = typer.Option(False, "--dry-run"), state_path: str = typer.Option(".mekong/binh-phap-state.json")) -> None:
    exec_, st = Executor(dag=load_dag(), state_path=Path(state_path), dry_run=dry_run), ExecutionState.load(Path(state_path))
    start = chapter if chapter is not None else (max(st.completed) + 1 if st.completed and max(st.completed) < CHAPTER_NODE_COUNT else None)
    console.print(f"[bold]Running DAG (start={start or 'first pending'}, dry={dry_run})[/]\n")
    results, icons = exec_.run(start_chapter=start), {"success": "✓", "failed": "✗", "skipped": "→"}
    for ch, r in sorted(results.items()):
        console.print(f"  Ch {ch:2d} {icons.get(r.status, '?')} {r.status}" + (f"  ({r.error[:50]})" if r.error else ""))
    console.print(f"\n[bold]Result:[/] {sum(1 for r in results.values() if r.status == 'success')} succeeded out of {len(results)} executed")


@_dag.command("resume")
def dag_resume(dry_run: bool = typer.Option(False, "--dry-run"), state_path: str = typer.Option(".mekong/binh-phap-state.json")) -> None:
    console.print("[bold]Resuming from persisted state…[/]\n")
    results, icons = Executor(dag=load_dag(), state_path=Path(state_path), dry_run=dry_run).resume(), {"success": "✓", "failed": "✗", "skipped": "→"}
    for ch, r in sorted(results.items()):
        console.print(f"  Ch {ch:2d} {icons.get(r.status, '?')} {r.status}")
    console.print(f"\n[bold]Resumed:[/] {sum(1 for r in results.values() if r.status == 'success')} succeeded" + (f" / {len(results)} executed" if results else ""))


@_dag.command("validate")
def dag_validate(os_path: Optional[str] = typer.Option(None, "--os-path", help="Custom OS manifest path")) -> None:
    try:
        dag = load_dag(os_path)
    except Exception as exc:
        console.print(f"[red]Load failed:[/] {exc}")
        raise typer.Exit(1)
    errors = [f"Chapter {i} missing from manifest" for i in range(1, CHAPTER_NODE_COUNT + 1) if i not in dag.chapters]
    errors += [f"Chapter {ch} has no primary_agent" for ch, node in dag.chapters.items() if not node.primary_agent]
    errors += [f"Edge from ch{p} → {ch} references unknown chapter" for ch, pres in dag.edges.items() for p in pres if p not in dag.chapters]
    if errors:
        console.print("[red]Validation errors:[/]\n" + "\n".join(f"  ✗ {e}" for e in errors))
        raise typer.Exit(1)
    console.print(f"[green]DAG valid — {len(dag.chapters)} chapters, human_only: {sorted(dag.human_only)}[/]\nExecution order: {dag.topological_order()}")


@chain_app.command("next")
def chain_next(state_path: str = typer.Option(".mekong/binh-phap-state.json")) -> None:
    dag, state = load_dag(), ExecutionState.load(Path(state_path))
    ready = [ch for ch in dag.topological_order() if ch not in state.completed and ch not in dag.human_only and set(dag.predecessors(ch)).issubset(state.completed)]
    if not ready:
        console.print("[yellow]No runnable chapters — all done or blocked[/]")
        return
    node = dag.chapters.get(ready[0])
    console.print(f"[bold]Next:[/] Ch {ready[0]} — {node.name if node else '?'} via {node.primary_agent if node else '?'}")


@chain_app.command("reset")
def chain_reset(state_path: str = typer.Option(".mekong/binh-phap-state.json"), dry_run: bool = typer.Option(False, "--dry-run")) -> None:
    p = Path(state_path)
    if dry_run:
        console.print(f"[dry-run] Would delete {p}")
    elif p.exists():
        p.unlink()
        console.print(f"[green]State reset — {p} deleted[/]")
    else:
        console.print(f"[dim]No state file at {p}[/]")


app.add_typer(_dag, name="dag", help="13-chapter DAG execution chain")
app.add_typer(chain_app, name="chain", help="End-to-end Binh Phap chain")


@app.command()
def daemon(dry_run: bool = typer.Option(False, "--dry-run", "-n"), cycles: int = typer.Option(0), interval: int = typer.Option(10)) -> None:
    from src.core.binh_phap.cto_daemon import run_daemon
    run_daemon(dry_run=dry_run, max_cycles=cycles, interval_seconds=interval)
