"""Solo a16z business-plan flow — `mekong plan-a16z ...`.

Guided 14-section / 61-card founder workflow. Prompts and section graph come
from `.claude-skills/solo-a16z-plan/framework.json`. State persists to
`.mekong/solo-a16z/<slug>.json`. LLM calls go through
`src.core.llm_client.get_client()`.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()
plan_a16z_app = typer.Typer(
    help="🏯 Solo a16z business-plan — 14 sections, 61 prompt cards, contrarian-thesis-first.",
    no_args_is_help=True,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_PATH = REPO_ROOT / ".claude-skills" / "solo-a16z-plan" / "framework.json"
STATE_DIR = REPO_ROOT / ".mekong" / "solo-a16z"
DEFAULT_PROJECT = "default"


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def _load_framework() -> list[dict[str, Any]]:
    if not FRAMEWORK_PATH.exists():
        console.print(
            f"[red]✘ framework.json not found at {FRAMEWORK_PATH}[/red]\n"
            f"[dim]The skill folder may be missing. Re-install the solo-a16z-plan skill.[/dim]"
        )
        raise typer.Exit(1)
    return json.loads(FRAMEWORK_PATH.read_text(encoding="utf-8"))


def _state_path(project: str) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in project) or DEFAULT_PROJECT
    return STATE_DIR / f"{safe}.json"


def _load_state(project: str) -> dict[str, Any]:
    p = _state_path(project)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"project": project, "seed": "", "results": {}, "completed": {}, "updated_at": None}


def _save_state(project: str, state: dict[str, Any]) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    p = _state_path(project)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _key(section_id: str, idx: int) -> str:
    return f"{section_id}.{idx}"


def _resolve_card(framework: list[dict[str, Any]], target: str) -> tuple[dict[str, Any], int, str] | None:
    """Resolve `section.idx` or `section_id`+index lookup. Returns (section, idx, key) or None."""
    if "." not in target:
        return None
    sec_id, idx_str = target.rsplit(".", 1)
    try:
        idx = int(idx_str)
    except ValueError:
        return None
    for sec in framework:
        if sec["id"] == sec_id and 0 <= idx < len(sec["cards"]):
            return sec, idx, _key(sec_id, idx)
    return None


def _resolve_ref(state: dict[str, Any], framework: list[dict[str, Any]], ref: str | None) -> str:
    """Resolve an input_ref string ("seed" or "section.idx,section.idx") to LLM context."""
    if not ref:
        return ""
    parts = [p.strip() for p in ref.split(",")]
    out: list[str] = []
    for p in parts:
        if p == "seed":
            out.append("--- IDEA ---\n" + (state.get("seed") or "(seed not set)"))
            continue
        if "." not in p:
            continue
        sec_id, idx_str = p.rsplit(".", 1)
        try:
            idx = int(idx_str)
        except ValueError:
            continue
        sec = next((s for s in framework if s["id"] == sec_id), None)
        if not sec or idx >= len(sec["cards"]):
            continue
        card = sec["cards"][idx]
        val = state.get("results", {}).get(_key(sec_id, idx), "")
        out.append(f"--- {card['field']} ---\n{val or '(not yet completed)'}")
    return "\n\n".join(out)


def _build_prompt(state: dict[str, Any], framework: list[dict[str, Any]], card: dict[str, Any]) -> str:
    if card.get("is_input"):
        return ""
    ctx = _resolve_ref(state, framework, card.get("input_ref"))
    if not ctx:
        return card.get("prompt", "")
    return f"{card['prompt']}\n\n{ctx}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@plan_a16z_app.command("init")
def init_cmd(
    seed: str = typer.Argument(..., help="One-paragraph idea — what you're building, for whom, why you."),
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p", help="Project slug for multi-plan setups."),
) -> None:
    """🌱 Initialize a new plan with a seed idea (or overwrite the existing seed)."""
    state = _load_state(project)
    state["seed"] = seed
    _save_state(project, state)
    console.print(Panel.fit(
        f"[bold]Seed saved[/bold]\n[dim]project:[/dim] {project}\n[dim]chars:[/dim] {len(seed)}",
        border_style="green",
    ))
    console.print("[dim]Next:[/dim] [bold]mekong plan-a16z list[/bold]")


@plan_a16z_app.command("list")
def list_cmd(
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
    section: str | None = typer.Option(None, "--section", "-s", help="Show only one section by id (e.g. 'idea_maze')."),
) -> None:
    """📋 List sections and cards with completion status."""
    framework = _load_framework()
    state = _load_state(project)
    seed_set = bool(state.get("seed"))
    results = state.get("results", {})
    completed = state.get("completed", {})

    total = sum(len(s["cards"]) for s in framework)
    done = sum(1 for s in framework for i, _ in enumerate(s["cards"]) if completed.get(_key(s["id"], i)))
    console.print(f"\n[bold]Solo a16z Plan[/bold] · project=[cyan]{project}[/cyan] · "
                  f"seed=[{'green' if seed_set else 'red'}]{'set' if seed_set else 'missing'}[/] · "
                  f"progress=[bold]{done}/{total}[/bold]\n")

    for sec in framework:
        if section and sec["id"] != section:
            continue
        table = Table(title=sec["title"], title_style="bold", show_lines=False, expand=True)
        table.add_column("#", width=4, style="dim")
        table.add_column("✓", width=2)
        table.add_column("Card", style="bold")
        table.add_column("Key", style="dim")
        table.add_column("Chars", justify="right", width=7)
        for i, c in enumerate(sec["cards"]):
            k = _key(sec["id"], i)
            mark = "[green]✓[/green]" if completed.get(k) else "·"
            chars = len(results.get(k, ""))
            table.add_row(str(i), mark, c["field"], k, str(chars) if chars else "—")
        console.print(table)
        console.print()


@plan_a16z_app.command("show")
def show_cmd(
    target: str = typer.Argument(..., help="Card key, e.g. 'idea_maze.0' or 'problem.3'."),
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
    prompt_only: bool = typer.Option(False, "--prompt", help="Print only the resolved prompt (for piping)."),
) -> None:
    """🔍 Show a single card's prompt (with refs resolved) and current result."""
    framework = _load_framework()
    state = _load_state(project)
    found = _resolve_card(framework, target)
    if not found:
        console.print(f"[red]✘ unknown card: {target}[/red]  Try [bold]mekong plan-a16z list[/bold]")
        raise typer.Exit(1)
    sec, idx, key = found
    card = sec["cards"][idx]
    prompt = _build_prompt(state, framework, card)
    if prompt_only:
        sys.stdout.write(prompt)
        return
    console.print(Panel.fit(
        f"[bold]{card['field']}[/bold]\n[dim]{card['purpose']}[/dim]\n"
        f"[dim]section:[/dim] {sec['title']}\n[dim]key:[/dim] {key}\n"
        f"[dim]input_ref:[/dim] {card.get('input_ref') or '—'}",
        border_style="cyan",
    ))
    console.print("\n[bold]Prompt[/bold]")
    console.print(Panel(prompt, border_style="dim"))
    existing = state.get("results", {}).get(key, "")
    if existing:
        console.print("\n[bold green]Result[/bold green]")
        console.print(Panel(Markdown(existing), border_style="green"))


@plan_a16z_app.command("run")
def run_cmd(
    target: str = typer.Argument(..., help="Card key, e.g. 'idea_maze.0'."),
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
    model: str | None = typer.Option(None, "--model", "-m", help="Override LLM_MODEL just for this call."),
    temperature: float = typer.Option(0.7, "--temp"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation."),
) -> None:
    """⚡ Run one card through the LLM and store the result."""
    framework = _load_framework()
    state = _load_state(project)
    found = _resolve_card(framework, target)
    if not found:
        console.print(f"[red]✘ unknown card: {target}[/red]")
        raise typer.Exit(1)
    sec, idx, key = found
    card = sec["cards"][idx]
    if card.get("is_input"):
        console.print(f"[yellow]'{key}' is the seed card. Use[/yellow] [bold]mekong plan-a16z init[/bold]")
        raise typer.Exit(1)
    prompt = _build_prompt(state, framework, card)
    console.print(f"[dim]→ {sec['title']} / {card['field']}[/dim]")
    if not yes and not typer.confirm("Run this card now?", default=True):
        raise typer.Exit(0)

    try:
        from core.llm_client import get_client  # type: ignore
    except Exception:
        try:
            from src.core.llm_client import get_client  # type: ignore
        except Exception as e:
            console.print(f"[red]✘ cannot import LLM client: {e}[/red]")
            raise typer.Exit(1) from e

    client = get_client()
    kw: dict[str, Any] = {"temperature": temperature}
    if model:
        kw["model"] = model

    with Progress(SpinnerColumn(), TextColumn("[bold]calling LLM…[/bold]"), transient=True) as p:
        p.add_task("run", total=None)
        out = client.generate(prompt, **kw)

    state.setdefault("results", {})[key] = out
    state.setdefault("completed", {})[key] = True
    _save_state(project, state)

    console.print(Panel(Markdown(out), title=card["field"], border_style="green"))
    console.print(f"[dim]✓ saved → {_state_path(project).relative_to(REPO_ROOT)}[/dim]")


@plan_a16z_app.command("run-section")
def run_section_cmd(
    section_id: str = typer.Argument(..., help="Section id, e.g. 'customer' or 'distribution'."),
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
    model: str | None = typer.Option(None, "--model", "-m"),
    skip_done: bool = typer.Option(True, "--skip-done/--rerun"),
) -> None:
    """⚡⚡ Run every card in a section sequentially (each one feeds the next)."""
    framework = _load_framework()
    state = _load_state(project)
    sec = next((s for s in framework if s["id"] == section_id), None)
    if not sec:
        console.print(f"[red]✘ unknown section: {section_id}[/red]")
        raise typer.Exit(1)
    if sec["id"] == "seed":
        console.print("[yellow]Use[/yellow] [bold]mekong plan-a16z init[/bold] [yellow]for the seed.[/yellow]")
        raise typer.Exit(1)

    try:
        from core.llm_client import get_client  # type: ignore
    except Exception:
        from src.core.llm_client import get_client  # type: ignore
    client = get_client()
    kw: dict[str, Any] = {}
    if model:
        kw["model"] = model

    for i, card in enumerate(sec["cards"]):
        key = _key(sec["id"], i)
        if skip_done and state.get("completed", {}).get(key):
            console.print(f"[dim]· skip {key}[/dim]")
            continue
        prompt = _build_prompt(state, framework, card)
        console.print(f"[bold]→ {card['field']}[/bold]")
        with Progress(SpinnerColumn(), TextColumn(f"[dim]{card['field']}[/dim]"), transient=True) as p:
            p.add_task("x", total=None)
            out = client.generate(prompt, **kw)
        state.setdefault("results", {})[key] = out
        state.setdefault("completed", {})[key] = True
        _save_state(project, state)
        console.print(f"[green]✓[/green] {key}  [dim]({len(out)} chars)[/dim]")


@plan_a16z_app.command("set")
def set_cmd(
    target: str = typer.Argument(..., help="Card key, e.g. 'customer.3'."),
    text: str = typer.Argument(..., help="Result text. Use '-' to read from stdin."),
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
) -> None:
    """✏️ Manually set a card result (paste from ChatGPT/Claude, or pipe via `-`)."""
    framework = _load_framework()
    state = _load_state(project)
    found = _resolve_card(framework, target)
    if not found:
        console.print(f"[red]✘ unknown card: {target}[/red]")
        raise typer.Exit(1)
    _, _, key = found
    if text == "-":
        text = sys.stdin.read()
    state.setdefault("results", {})[key] = text
    state.setdefault("completed", {})[key] = bool(text.strip())
    _save_state(project, state)
    console.print(f"[green]✓[/green] {key} ← {len(text)} chars")


@plan_a16z_app.command("export")
def export_cmd(
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
    fmt: str = typer.Option("md", "--format", "-f", help="md | json"),
    out: Path | None = typer.Option(None, "--out", "-o", help="Output file (defaults to stdout)."),
) -> None:
    """📄 Export the plan as Markdown or JSON."""
    framework = _load_framework()
    state = _load_state(project)
    if fmt == "json":
        text = json.dumps(state, ensure_ascii=False, indent=2)
    elif fmt == "md":
        lines = ["# Business Plan — Solo a16z Edition\n",
                 f"> Project: `{project}`  ·  Updated: {state.get('updated_at') or '—'}\n", "---\n"]
        if state.get("seed"):
            lines.append("## 0. Seed\n\n" + state["seed"] + "\n\n---\n")
        for sec in framework:
            if sec["id"] == "seed":
                continue
            lines.append(f"## {sec['title']}\n\n_{sec['subtitle']}_\n")
            for i, card in enumerate(sec["cards"]):
                key = _key(sec["id"], i)
                v = state.get("results", {}).get(key, "")
                done = "✓" if state.get("completed", {}).get(key) else "○"
                lines.append(f"### {done} {card['field']}\n\n*{card['purpose']}*\n")
                lines.append((v or "_(not yet completed)_") + "\n")
            lines.append("---\n")
        text = "\n".join(lines)
    else:
        console.print(f"[red]✘ unknown format: {fmt} (md|json)[/red]")
        raise typer.Exit(1)
    if out:
        out.write_text(text, encoding="utf-8")
        console.print(f"[green]✓[/green] wrote {out}")
    else:
        sys.stdout.write(text)


@plan_a16z_app.command("dashboard")
def dashboard_cmd(
    project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p"),
    port: int = typer.Option(3000, "--port"),
) -> None:
    """🌐 Open the dashboard route in your browser (requires `apps/dashboard` running)."""
    import webbrowser
    url = f"http://localhost:{port}/solo-a16z?project={project}"
    console.print(f"[dim]→ {url}[/dim]")
    webbrowser.open(url)


@plan_a16z_app.command("status")
def status_cmd(project: str = typer.Option(DEFAULT_PROJECT, "--project", "-p")) -> None:
    """📊 One-line status: progress + state file path."""
    framework = _load_framework()
    state = _load_state(project)
    total = sum(len(s["cards"]) for s in framework)
    done = sum(1 for s in framework for i, _ in enumerate(s["cards"])
               if state.get("completed", {}).get(_key(s["id"], i)))
    console.print(
        f"[bold]{project}[/bold] · {done}/{total} cards · seed={'✓' if state.get('seed') else '✗'} · "
        f"file=[dim]{_state_path(project).relative_to(REPO_ROOT)}[/dim]"
    )
