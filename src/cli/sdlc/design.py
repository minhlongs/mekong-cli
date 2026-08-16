# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/cli/sdlc/design.py — `mekong design` sub-app.

Commands:
  mekong design <feature>   Load SPEC_OUTPUT.md, scaffold DESIGN_OUTPUT.md,
                            print architect agent prompt.

The agent (architect) reads CLAUDE.design.md + SPEC_OUTPUT.md then fills
in .mekong/DESIGN_OUTPUT.md.
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

design_app = typer.Typer(
    name="design",
    help="Design phase: convert spec requirements into architecture decisions.",
    add_completion=False,
)

console = Console()

_PHASE = "design"
_AGENT = "architect"
_CONTRACT = "CLAUDE.design.md"
_PRIOR_OUTPUT = "SPEC_OUTPUT.md"
_TEMPLATE = "DESIGN_OUTPUT.template.md"
_OUTPUT = "DESIGN_OUTPUT.md"


@design_app.command("new")
def design_cmd(
    feature: str = typer.Argument(..., help="Feature slug, e.g. auth-mfa"),
    skip_prior_check: bool = typer.Option(
        False,
        "--skip-prior-check",
        help="Skip check for SPEC_OUTPUT.md (solo fast-path)",
    ),
    overwrite: bool = typer.Option(
        True,
        "--overwrite/--no-overwrite",
        help="Overwrite existing DESIGN_OUTPUT.md (default: yes — idempotent)",
    ),
) -> None:
    """
    Start the design phase for <feature>.

    Loads SPEC_OUTPUT.md, scaffolds DESIGN_OUTPUT.md, then prints the
    agent prompt for the architect agent to fill it in.
    """
    mekong_root, out_dir, phases_dir = resolve_context(feature)

    contract_path = phases_dir / _CONTRACT
    if not contract_path.exists():
        console.print(
            f"[red]Contract not found:[/red] {contract_path}\n"
            "Ensure .mekong/phases/CLAUDE.design.md exists."
        )
        raise typer.Exit(code=1)

    # Load prior output (guard: spec must exist unless skipped)
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
        f"[bold cyan]mekong code new {feature}[/bold cyan]"
    )
