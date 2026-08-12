"""`mekong idea` — autonomous Plan→Execute→Verify→Reflect autopilot.

Usage:
    mekong idea "build me a /pricing page that pulls from Polar"
    mekong idea "add /idea autopilot" --max-iter 20 --deploy
    mekong idea resume <run-id>
    mekong idea list
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mekong.autopilot import IdeaLoop, RunOptions

idea_app = typer.Typer(
    help="🤖 /idea autopilot — autonomous Plan→Execute→Verify→Reflect.",
    no_args_is_help=True,
)
console = Console()
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / ".mekong" / "idea"


@idea_app.command("run")
def run_cmd(
    idea: str = typer.Argument(..., help="The idea, in plain English/Vietnamese."),
    max_iter: int = typer.Option(12, "--max-iter", help="Hard cap on Plan→Execute→Verify cycles."),
    max_tokens: int = typer.Option(800_000, "--max-tokens"),
    max_mcu: int = typer.Option(50, "--max-mcu", help="Cap on LLM calls (1 MCU = 1 turn)."),
    worktree: bool = typer.Option(True, "--worktree/--in-place", help="Run in a git worktree (safer)."),
    deploy: bool = typer.Option(False, "--deploy", help="Run scripts/deploy-dashboard.sh after green tests."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Plan only — no writes, no shell."),
    model: str | None = typer.Option(None, "--model", "-m", help="Override LLM_MODEL just for this run."),
    temp: float = typer.Option(0.4, "--temp"),
    unsafe_bash: bool = typer.Option(False, "--unsafe-bash", help="Disable bash safelist."),
    cf_filter: bool = typer.Option(False, "--cf-filter", help="Chỉ generate Cloudflare-focused ideas (Workers, Pages, Wrangler)."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """🚀 Start a new autopilot run."""
    if worktree and not dry_run:
        wt = _ensure_worktree(idea)
        console.print(f"[dim]→ working in worktree:[/dim] {wt}")
        os.chdir(wt)

    console.print(Panel.fit(
        f"[bold]/idea autopilot[/bold]\n[dim]idea:[/dim] {idea}\n"
        f"[dim]caps:[/dim] {max_iter} iter · {max_tokens:,} tok · {max_mcu} MCU\n"
        f"[dim]model:[/dim] {model or os.environ.get('LLM_MODEL', '(env)')}\n"
        f"[dim]deploy:[/dim] {deploy}  [dim]dry-run:[/dim] {dry_run}"
        + (f"\n[dim]cf-filter:[/dim] [cyan]{cf_filter}[/cyan]" if cf_filter else ""),
        border_style="cyan",
    ))

    if not yes and not dry_run:
        if not typer.confirm("Start autonomous run?", default=True):
            raise typer.Exit(0)

    opts = RunOptions(
        idea=idea, max_iter=max_iter, max_tokens=max_tokens, max_mcu=max_mcu,
        worktree=worktree, deploy=deploy, dry_run=dry_run,
        model=model, temperature=temp, unsafe_bash=unsafe_bash,
        cf_filter=cf_filter,
    )
    loop = IdeaLoop(opts)
    console.print(f"[dim]run id:[/dim] [bold]{loop.run_id}[/bold]")
    console.print(f"[dim]audit:[/dim] {loop.audit_path}\n")

    result = loop.run()

    style = "green" if result.ok else "red"
    console.print(Panel(
        f"[bold]{'✓ DONE' if result.ok else '✘ STOPPED'}[/bold]  {result.reason}\n"
        f"[dim]iterations:[/dim] {result.iterations}\n"
        f"[dim]files:[/dim] {len(result.files_touched)}\n"
        f"[dim]audit:[/dim] {result.audit_log}",
        border_style=style,
    ))
    if result.files_touched:
        console.print("\n[bold]Files touched:[/bold]")
        for f in result.files_touched:
            console.print(f"  · {f}")
    raise typer.Exit(0 if result.ok else 1)


@idea_app.command("list")
def list_cmd() -> None:
    """📋 List past runs."""
    if not RUNS_DIR.exists():
        console.print("[dim]no runs yet[/dim]")
        return
    runs = sorted(RUNS_DIR.iterdir(), reverse=True)
    table = Table(title=f"/idea runs · {len(runs)}", show_lines=False)
    table.add_column("run_id", style="bold")
    table.add_column("ok", width=4)
    table.add_column("iter", justify="right")
    table.add_column("reason")
    for d in runs[:50]:
        rp = d / "result.json"
        if not rp.exists():
            table.add_row(d.name, "—", "—", "(no result.json — interrupted?)")
            continue
        r = json.loads(rp.read_text(encoding="utf-8"))
        ok = "[green]✓[/green]" if r.get("ok") else "[red]✘[/red]"
        table.add_row(d.name, ok, str(r.get("iterations", "?")), str(r.get("reason", ""))[:60])
    console.print(table)


@idea_app.command("show")
def show_cmd(run_id: str = typer.Argument(...)) -> None:
    """🔍 Show details of a run (plan, audit tail, files)."""
    d = RUNS_DIR / run_id
    if not d.exists():
        console.print(f"[red]✘ unknown run: {run_id}[/red]")
        raise typer.Exit(1)
    rp = d / "result.json"
    if rp.exists():
        console.print(Panel(rp.read_text(encoding="utf-8"), title="result.json", border_style="cyan"))
    al = d / "audit.jsonl"
    if al.exists():
        lines = al.read_text(encoding="utf-8").splitlines()
        console.print(f"\n[bold]Audit (last 20 of {len(lines)}):[/bold]")
        for line in lines[-20:]:
            console.print(f"  {line}")


@idea_app.command("kill")
def kill_cmd(run_id: str = typer.Argument(...)) -> None:
    """🛑 Mark a run as aborted (cooperative — sends SIGTERM if process is found)."""
    d = RUNS_DIR / run_id
    if not d.exists():
        console.print(f"[red]✘ unknown run: {run_id}[/red]")
        raise typer.Exit(1)
    sf = d / "safety.json"
    if sf.exists():
        s = json.loads(sf.read_text(encoding="utf-8"))
        s["aborted"] = True
        sf.write_text(json.dumps(s, indent=2), encoding="utf-8")
        console.print(f"[yellow]marked aborted:[/yellow] {sf}")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _slug(idea: str) -> str:
    s = "".join(c if c.isalnum() else "-" for c in idea.lower())[:40].strip("-")
    return s or "idea"


def _ensure_worktree(idea: str) -> Path:
    """Create a sibling git worktree to isolate autopilot writes."""
    slug = _slug(idea)
    wt = (REPO_ROOT.parent / f"mekong-idea-{slug}").resolve()
    if wt.exists():
        return wt
    branch = f"idea/{slug}"
    subprocess.run(["git", "worktree", "add", "-b", branch, str(wt)], cwd=REPO_ROOT, check=True)
    return wt
