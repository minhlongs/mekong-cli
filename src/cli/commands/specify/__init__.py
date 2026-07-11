"""SDD spec generation -- ``mekong specify new``.

Generates a feature spec from the SDD spec template.
Outputs to .mekong/features/<feature>/SPEC.md when MEKONG_FEATURE_DIR=1,
otherwise overwrites .mekong/SPEC.md.
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

specify_app = typer.Typer(
    name="specify",
    help="SDD: generate feature spec from template",
    no_args_is_help=True,
    add_completion=False,
)


def _next_feature_number(features_dir: Path) -> int:
    """Return the next auto-increment number for a features/ subdirectory."""
    if not features_dir.is_dir():
        return 1
    existing = [
        int(d.name.split("-")[0])
        for d in features_dir.iterdir()
        if d.is_dir() and d.name[0:3].isdigit()
    ]
    return max(existing, default=0) + 1


@specify_app.command("new")
def specify_new(
    feature: str = typer.Argument(..., help="Feature slug, e.g. add-auth"),
    feature_dir_mode: bool = typer.Option(
        None,
        "--feature-dir/--no-feature-dir",
        help="Write to .mekong/features/<feature>/ (default: env MEKONG_FEATURE_DIR=1)",
    ),
    title: str = typer.Option(
        "",
        "--title",
        help="Feature title for the spec header (defaults to feature slug).",
    ),
    description: str = typer.Option(
        "",
        "--description",
        help="Short description of the feature.",
    ),
) -> None:
    """Generate a feature spec from the SDD spec template.

    Writes SPEC.md to .mekong/ (default) or .mekong/features/<feature>/.
    """
    use_feature_dir = (
        feature_dir_mode
        if feature_dir_mode is not None
        else os.environ.get("MEKONG_FEATURE_DIR") == "1"
    )

    mekong_root = _mekong_root()

    if use_feature_dir:
        features_base = mekong_root / "features"
        num = _next_feature_number(features_base)
        feature_dir = features_base / f"{num:03d}-{feature}"
        feature_dir.mkdir(parents=True, exist_ok=True)
        out_path = feature_dir / "SPEC.md"
    else:
        out_path = mekong_root / "SPEC.md"

    context: dict[str, Any] = {
        "title": title or feature,
        "description": description or feature,
        "feature_1": feature,
        "feature_2": f"{feature} helper",
        "feature_3": f"{feature} integration",
        "requirement_f_1": f"Implement core {feature} functionality",
        "requirement_f_2": f"Add {feature} CLI entry point",
        "requirement_nf_1": "Response time < 200ms",
        "user_1": "operator",
        "user_story_1": f"Use {feature}",
        "capability_1": f"access {feature} functionality",
        "value_1": f"streamline {feature} workflow",
        "ac_1_1": f"{feature} command is discoverable",
        "ac_1_2": f"Output is written to expected path",
        "user_2": "developer",
        "user_story_2": f"Integrate {feature}",
        "capability_2": f"build on top of {feature}",
        "value_2": "extend platform capabilities",
        "ac_2_1": f"{feature} API is stable",
        "out_of_scope_1": "External integrations",
        "dependency_1": "mekong-cli core",
        "open_question_1": "Edge cases for empty input",
    }

    written = write_artifact(out_path, "spec", context)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    table.add_row("feature", feature)
    table.add_row("output", str(written.relative_to(Path.cwd())))

    console.print(
        Panel(table, title="[bold green]Spec Generated[/]", border_style="green", expand=False)
    )
