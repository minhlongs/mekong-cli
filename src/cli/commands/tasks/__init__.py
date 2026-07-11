"""Tasks generation -- `mekong tasks new <feature>`.

Generates a TDD-ordered task list from the SDD tasks template.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.sdlc.agent_dispatch import _mekong_root, _output_dir
from src.core.spec_templates import write_artifact

console = Console()

tasks_app = typer.Typer(
    name="tasks",
    help="SDD: generate TDD task list from spec",
    no_args_is_help=True,
    add_completion=False,
)


@tasks_app.command("new")
def tasks_new(
    feature: str = typer.Argument(..., help="Feature slug, e.g. add-auth"),
    feature_dir_mode: bool = typer.Option(
        None,
        "--feature-dir/--no-feature-dir",
        help="Write to .mekong/features/<feature>/ (default: env MEKONG_FEATURE_DIR=1)",
    ),
) -> None:
    """Generate a TDD-ordered task list for a feature."""
    use_feature_dir = (
        feature_dir_mode
        if feature_dir_mode is not None
        else os.environ.get("MEKONG_FEATURE_DIR") == "1"
    )

    mekong_root = _mekong_root()
    out_dir = _output_dir(feature, mekong_root)
    out_path = out_dir / "tasks.md"

    context: dict[str, Any] = {
        "title": feature,
        "test_task_1": f"[P] Write unit tests for {feature} core logic",
        "test_task_2": f"[P] Write integration tests for {feature} handlers",
        "test_task_3": f"[P] Write edge-case tests for {feature} error paths",
        "impl_task_1": f"Implement {feature} core module",
        "impl_task_2": f"Add {feature} CLI entry point",
        "impl_task_3": f"Wire {feature} into existing pipeline",
        "integ_task_1": f"Run full test suite for {feature}",
        "integ_task_2": f"Verify {feature} end-to-end flow",
    }

    written = write_artifact(out_path, "tasks", context)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    table.add_row("feature", feature)
    table.add_row("output", str(written.relative_to(Path.cwd())))

    console.print(
        Panel(table, title="[bold green]Tasks Generated[/]", border_style="green", expand=False)
    )
