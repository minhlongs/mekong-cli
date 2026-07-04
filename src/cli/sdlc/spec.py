"""
src/cli/sdlc/spec.py — `mekong spec` sub-app.

Commands:
  mekong spec new <feature>   Scaffold SPEC_OUTPUT.md and print agent prompt.

The agent (planner) reads CLAUDE.spec.md then fills in .mekong/SPEC_OUTPUT.md.
This command scaffolds the output file and prints the prompt — it does NOT
invoke the agent automatically (MVP: manual invocation).
"""

from __future__ import annotations


import typer
from rich.console import Console

from src.cli.sdlc.agent_dispatch import (
    print_agent_instructions,
    resolve_context,
    scaffold_output,
)

spec_app = typer.Typer(
    name="spec",
    help="Specification phase: convert a feature request into requirements.",
    add_completion=False,
)

console = Console()

_PHASE = "spec"
_AGENT = "planner"
_CONTRACT = "CLAUDE.spec.md"
_TEMPLATE = "SPEC_OUTPUT.template.md"
_OUTPUT = "SPEC_OUTPUT.md"


@spec_app.command("new")
def spec_new(
    feature: str = typer.Argument(..., help="Feature slug, e.g. auth-mfa"),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite existing SPEC_OUTPUT.md (default: yes — idempotent)",
    ),
    scaffold_only: bool = typer.Option(
        False,
        "--scaffold-only",
        help="Only write the blank template, skip agent prompt",
    ),
) -> None:
    """
    Start the spec phase for <feature>.

    Scaffolds .mekong/SPEC_OUTPUT.md from the blank template, then prints
    the agent prompt for the planner agent to fill it in.
    """
    mekong_root, out_dir, phases_dir = resolve_context(feature)

    contract_path = phases_dir / _CONTRACT
    if not contract_path.exists():
        console.print(
            f"[red]Contract not found:[/red] {contract_path}\n"
            "Ensure .mekong/phases/CLAUDE.spec.md exists."
        )
        raise typer.Exit(code=1)

    out_path = scaffold_output(
        template_name=_TEMPLATE,
        output_filename=_OUTPUT,
        feature=feature,
        mekong_root=mekong_root,
        overwrite=overwrite,
    )

    console.print(f"[green]Scaffolded:[/green] {out_path}")

    if scaffold_only:
        console.print(
            f"[dim]--scaffold-only set. Open {out_path} and fill manually.[/dim]"
        )
        return

    print_agent_instructions(
        phase=_PHASE,
        feature=feature,
        contract_path=contract_path,
        output_path=out_path,
        agent_name=_AGENT,
        prior_output_path=None,
    )

    console.print(
        f"[dim]Next:[/dim] After the agent fills {_OUTPUT}, run "
        f"[bold cyan]mekong design new {feature}[/bold cyan]"
    )
