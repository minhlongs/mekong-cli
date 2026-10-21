# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SDD spec generation -- ``mekong specify run`` & ``mekong specify new``."""

from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.sdlc.agent_dispatch import _mekong_root
from src.core.spec_templates import write_artifact

console = Console()

specify_app = typer.Typer(
    name="specify",
    help="SDD: generate feature specs from templates (spec-kit style)",
    no_args_is_help=True,
    add_completion=False,
)

_FALLBACK_TEMPLATE = (
    "# Feature Specification\n\n## Feature Name\n\n{description}\n\n"
    "## Description\n\n{description}\n\n---\n\n## Requirements\n\n"
    "### Functional Requirements\n\nImplement {description} core functionality.\n\n"
    "### Non-Functional Requirements\n\n"
    "- Performance: response time < 200ms under normal load\n"
    "- Reliability: graceful error handling; no crashes on bad input\n"
    "- Security: input validation on all public entry points\n"
    "- Observability: structured logs for every request/response cycle\n\n---\n\n"
    "## User Stories\n\nAs a user, I want to {description} so that I can achieve my goals.\n\n---\n\n"
    "## Acceptance Criteria\n\n"
    "- {description} is discoverable and usable\n"
    "- Outputs written to expected paths\n"
    "- No regressions in existing functionality\n\n---\n\n"
    "## Out of Scope\n\nExternal integrations, legacy system support.\n\n---\n\n"
    "*Generated: {timestamp}*\n"
)


def _slugify(text: str) -> str:
    """Lowercase, hyphen-safe slug from description."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "feature"


def _next_nnn(specs_dir: Path) -> int:
    """Return next auto-increment NNN by scanning specs/NNN-* dirs."""
    if not specs_dir.is_dir():
        return 1
    existing = [int(d.name.split("-")[0]) for d in specs_dir.iterdir() if d.is_dir() and d.name[0:3].isdigit()]
    return max(existing, default=0) + 1


def _print_spec_panel(rows: list[tuple[str, str]]) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    for k, v in rows:
        table.add_row(k, v)
    console.print(Panel(table, title="[bold green]Spec Generated[/]", border_style="green", expand=False))


@specify_app.command("run")
def specify_run(
    description: str = typer.Argument(..., help="Feature description (used as title and slug seed)."),
    output_dir: Path = typer.Option(Path("specs"), "--output-dir", "-o", help="Base directory for spec outputs."),
) -> None:
    """Generate an SDD feature spec (spec-kit style)."""
    slug = _slugify(description)
    nnn = _next_nnn(output_dir.resolve())
    spec_dir = output_dir.resolve() / f"{nnn:03d}-{slug}"
    spec_dir.mkdir(parents=True, exist_ok=True)
    out_path = spec_dir / "spec.md"

    context: dict[str, Any] = {
        "feature_name": description,
        "description": description,
        "requirements": f"Implement {description} core functionality.",
        "user_stories": f"As a user, I want to {description.lower()} so that I can achieve my goals.",
        "acceptance_criteria": (
            f"- {description} is discoverable and usable\n"
            f"- Outputs written to expected paths\n"
            f"- No regressions in existing functionality"
        ),
        "out_of_scope": "External integrations, legacy system support.",
    }

    try:
        written = write_artifact(out_path, "spec", context)
    except Exception:
        fallback = _FALLBACK_TEMPLATE.format(description=description, timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))
        out_path.write_text(fallback, encoding="utf-8")
        written = out_path.resolve()

    try:
        rel = written.relative_to(Path.cwd())
    except ValueError:
        rel = written

    _print_spec_panel([("number", f"{nnn:03d}"), ("slug", slug), ("output", str(rel))])


@specify_app.command("new")
def specify_new(
    feature: str = typer.Argument(..., help="Feature slug, e.g. add-auth"),
    feature_dir_mode: bool = typer.Option(None, "--feature-dir/--no-feature-dir", help="Write to .mekong/features/<feature>/ (default: env MEKONG_FEATURE_DIR=1)"),
    title: str = typer.Option("", "--title", help="Feature title for the spec header (defaults to feature slug)."),
    description: str = typer.Option("", "--description", help="Short description of the feature."),
) -> None:
    """Generate a feature spec from the SDD spec template."""
    use_feature_dir = feature_dir_mode if feature_dir_mode is not None else os.environ.get("MEKONG_FEATURE_DIR") == "1"
    mekong_root = _mekong_root()

    if use_feature_dir:
        features_base = mekong_root / "features"
        num = _next_nnn(features_base)
        feature_dir = features_base / f"{num:03d}-{feature}"
        feature_dir.mkdir(parents=True, exist_ok=True)
        out_path = feature_dir / "SPEC.md"
    else:
        out_path = mekong_root / "SPEC.md"

    context: dict[str, Any] = {
        "title": title or feature, "description": description or feature,
        "feature_1": feature, "feature_2": f"{feature} helper", "feature_3": f"{feature} integration",
        "requirement_f_1": f"Implement core {feature} functionality", "requirement_f_2": f"Add {feature} CLI entry point",
        "requirement_nf_1": "Response time < 200ms", "user_1": "operator", "user_story_1": f"Use {feature}",
        "capability_1": f"access {feature} functionality", "value_1": f"streamline {feature} workflow",
        "ac_1_1": f"{feature} command is discoverable", "ac_1_2": "Output is written to expected path",
        "user_2": "developer", "user_story_2": f"Integrate {feature}", "capability_2": f"build on top of {feature}",
        "value_2": "extend platform capabilities", "ac_2_1": f"{feature} API is stable",
        "out_of_scope_1": "External integrations", "dependency_1": "mekong-cli core", "open_question_1": "Edge cases for empty input",
    }

    written = write_artifact(out_path, "spec", context)
    _print_spec_panel([("feature", feature), ("output", str(written.relative_to(Path.cwd())))])
