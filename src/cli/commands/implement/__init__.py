"""Implement runner -- `mekong implement run <feature>`.

Wraps goal execution with spec context from prior SDD phases.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.cli.sdlc.agent_dispatch import (
    _mekong_root,
    _output_dir,
    print_agent_instructions,
)

console = Console()

implement_app = typer.Typer(
    name="implement",
    help="SDD: execute implementation from task list",
    no_args_is_help=True,
    add_completion=False,
)


@implement_app.command("run")
def implement_run(
    feature: str = typer.Argument(..., help="Feature slug, e.g. add-auth"),
    agent_name: str = typer.Option(
        "fullstack-developer",
        "--agent",
        help="Agent to dispatch for implementation",
    ),
) -> None:
    """Execute implementation for a feature using prior task context."""
    mekong_root = _mekong_root()
    out_dir = _output_dir(feature, mekong_root)

    contract_path = out_dir / "SPEC.md"
    output_path = out_dir / "IMPLEMENT.md"
    prior_path = out_dir / "tasks.md"

    prior_output_path: Optional[Path] = None
    if prior_path.exists():
        prior_output_path = prior_path

    print_agent_instructions(
        phase="implement",
        feature=feature,
        contract_path=contract_path,
        output_path=output_path,
        agent_name=agent_name,
        prior_output_path=prior_output_path,
    )
