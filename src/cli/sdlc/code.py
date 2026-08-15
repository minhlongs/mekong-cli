"""
src/cli/sdlc/code.py — `mekong code` sub-app.

Commands:
  mekong code <feature>   Load DESIGN_OUTPUT.md, scaffold TASKS.todo,
                          print fullstack-developer agent prompt.

The agent (fullstack-developer) reads CLAUDE.code.md + DESIGN_OUTPUT.md
then fills in .mekong/TASKS.todo.
"""

from __future__ import annotations

import typer
from rich.console import Console

from src.cli.sdlc.agent_dispatch import (
    load_prior_output,
    print_agent_instructions,
    resolve_context,
    scaffold_output,
)

code_app = typer.Typer(
    name="code",
    help="Code phase: convert architecture design into a task backlog.",
    add_completion=False,
)

console = Console()

_PHASE = "code"
_AGENT = "fullstack-developer"
_CONTRACT = "CLAUDE.code.md"
_PRIOR_OUTPUT = "DESIGN_OUTPUT.md"
_TEMPLATE = "TASKS.todo.template"
_OUTPUT = "TASKS.todo"


@code_app.command("new")
def code_cmd(
    feature: str = typer.Argument(..., help="Feature slug, e.g. auth-mfa"),
    skip_prior_check: bool = typer.Option(
        False,
        "--skip-prior-check",
        help="Skip check for DESIGN_OUTPUT.md (solo fast-path)",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite existing TASKS.todo (default: yes — idempotent)",
    ),
) -> None:
    """
    Start the code phase for <feature>.

    Loads DESIGN_OUTPUT.md, scaffolds TASKS.todo, then prints the agent
    prompt for the fullstack-developer agent to fill it in.
    """
    mekong_root, out_dir, phases_dir = resolve_context(feature)

    contract_path = phases_dir / _CONTRACT
    if not contract_path.exists():
        console.print(
            f"[red]Contract not found:[/red] {contract_path}\n"
            "Ensure .mekong/phases/CLAUDE.code.md exists."
        )
        raise typer.Exit(code=1)

    prior_content = load_prior_output(
        filename=_PRIOR_OUTPUT,
        feature=feature,
        mekong_root=mekong_root,
        required=not skip_prior_check,
    )

    if prior_content:
        console.print(f"[green]Loaded:[/green] {out_dir / _PRIOR_OUTPUT}")

    out_path = scaffold_output(
        template_name=_TEMPLATE,
        output_filename=_OUTPUT,
        feature=feature,
        mekong_root=mekong_root,
        overwrite=overwrite,
    )

    console.print(f"[green]Scaffolded:[/green] {out_path}")

    print_agent_instructions(
        phase=_PHASE,
        feature=feature,
        contract_path=contract_path,
        output_path=out_path,
        agent_name=_AGENT,
        prior_output_path=out_dir / _PRIOR_OUTPUT if prior_content else None,
    )

    console.print(
        f"[dim]Next:[/dim] After the agent fills {_OUTPUT}, run "
        f"[bold cyan]mekong deploy new {feature}[/bold cyan]"
    )
