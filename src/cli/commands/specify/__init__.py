"""SDD spec generation -- ``mekong specify run`` & ``mekong specify new``."""

from __future__ import annotations

import os
import re
from datetime import UTC
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

_FALLBACK_TEMPLATE = """\
# Feature Specification

## Feature Name

{description}

## Description

{description}

---

## Requirements

### Functional Requirements

Implement {description} core functionality.

### Non-Functional Requirements

- Performance: response time < 200ms under normal load
- Reliability: graceful error handling; no crashes on bad input
- Security: input validation on all public entry points
- Observability: structured logs for every request/response cycle

---

## User Stories

As a user, I want to {description} so that I can achieve my goals.

---

## Acceptance Criteria

- {description} is discoverable and usable
- Outputs written to expected paths
- No regressions in existing functionality

---

## Out of Scope

External integrations, legacy system support.

---

*Generated: {timestamp}*
"""


def _slugify(text: str) -> str:
    """Lowercase, hyphen-safe slug from description."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "feature"


def _next_nnn(specs_dir: Path) -> int:
    """Return next auto-increment NNN by scanning specs/NNN-* dirs."""
    if not specs_dir.is_dir():
        return 1
    existing = [
        int(d.name.split("-")[0])
        for d in specs_dir.iterdir()
        if d.is_dir() and d.name[0:3].isdigit()
    ]
    return max(existing, default=0) + 1


@specify_app.command("run")
def specify_run(
    description: str = typer.Argument(
        ...,
        help="Feature description (used as title and slug seed).",
    ),
    output_dir: Path = typer.Option(
        Path("specs"),
        "--output-dir",
        "-o",
        help="Base directory for spec outputs.",
    ),
) -> None:
    """Generate an SDD feature spec (spec-kit style).

    Writes to ``specs/NNN-<slug>/spec.md`` where NNN is auto-incremented.
    """
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
        from datetime import datetime
        fallback = _FALLBACK_TEMPLATE.format(
            description=description,
            timestamp=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        out_path.write_text(fallback, encoding="utf-8")
        written = out_path.resolve()

    try:
        rel = written.relative_to(Path.cwd())
    except ValueError:
        rel = written

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    table.add_row("number", f"{nnn:03d}")
    table.add_row("slug", slug)
    table.add_row("output", str(rel))
    console.print(
        Panel(
            table,
            title="[bold green]Spec Generated[/]",
            border_style="green",
            expand=False,
        )
    )


# -----------------------------------------------------------------------
# Legacy ``mekong specify new`` (kept for backward compatibility)
# -----------------------------------------------------------------------


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
        existing = [
            int(d.name.split("-")[0])
            for d in features_base.iterdir()
            if d.is_dir() and d.name[0:3].isdigit()
        ]
        num = max(existing, default=0) + 1
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
        "ac_1_2": "Output is written to expected path",
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
        Panel(
            table,
            title="[bold green]Spec Generated[/]",
            border_style="green",
            expand=False,
        )
    )
