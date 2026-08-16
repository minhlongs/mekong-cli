"""Cross-artifact analysis -- `mekong analyze check <feature>`.

Read-only consistency validation across spec.md, plan.md, tasks.md.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel

from src.cli.sdlc.agent_dispatch import _mekong_root, _output_dir

console = Console()

analyze_app = typer.Typer(
    name="analyze",
    help="Cross-artifact consistency check (spec vs plan vs tasks)",
    no_args_is_help=True,
    add_completion=False,
)


def _find_feature_dir(feature: str, mekong_root: Path) -> Path | None:
    """Locate output directory for a feature slug."""
    features_base = mekong_root / "features"
    if features_base.is_dir():
        for sub in sorted(features_base.iterdir()):
            if sub.is_dir() and feature in sub.name:
                return sub
    # Fallback: flat .mekong/
    if (mekong_root / "SPEC.md").exists():
        return mekong_root
    return None


def _check_has_feature(content: str, feature: str) -> bool:
    """Heuristic: does this markdown mention the feature slug?"""
    return feature.lower() in content.lower()


@analyze_app.command("check")
def analyze_check(
    feature: str = typer.Argument(..., help="Feature slug to analyze"),
) -> None:
    """Validate consistency across spec, plan, and tasks for a feature."""
    mekong_root = _mekong_root()
    feature_dir = _find_feature_dir(feature, mekong_root)

    if feature_dir is None:
        console.print(f"[red]No output found for feature:[/red] {feature}")
        raise typer.Exit(code=1)

    issues: list[str] = []

    # Load artifacts
    spec_path = feature_dir / "SPEC.md"
    tasks_path = feature_dir / "tasks.md"
    plan_path = feature_dir / "plan.md"

    spec_content = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    tasks_content = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else ""
    plan_content = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""

    # Build report
    lines: list[str] = [
        f"# Cross-Artifact Analysis: {feature}",
        "",
        f"**Feature dir:** `{feature_dir}`",
        "",
        "## Artifact Check",
        "",
    ]

    # Check spec
    if spec_content:
        lines.append("- [x] `SPEC.md` exists")
        lines.append(f"- [x] Mentions feature: `{_check_has_feature(spec_content, feature)}`")
    else:
        lines.append("- [ ] `SPEC.md` missing -- run `mekong specify new` first")
        issues.append("SPEC.md missing")

    # Check tasks
    if tasks_content:
        lines.append("- [x] `tasks.md` exists")
        lines.append(f"- [x] Mentions feature: `{_check_has_feature(tasks_content, feature)}`")
        # Count tasks
        task_items = re.findall(r"^- \[(?:\]|P)\] (.+)$", tasks_content, re.MULTILINE)
        lines.append(f"- Task count: {len(task_items)}")
    else:
        lines.append("- [ ] `tasks.md` missing -- run `mekong tasks new` first")
        issues.append("tasks.md missing")

    # Check plan
    if plan_content:
        lines.append("- [x] `plan.md` exists")
        lines.append(f"- [x] Mentions feature: `{_check_has_feature(plan_content, feature)}`")
    else:
        lines.append("- [ ] `plan.md` missing -- run `mekong plan from-init` first")
        issues.append("plan.md missing")

    lines.append("")
    lines.append("## Summary")
    lines.append("")

    if issues:
        lines.append(f"**{len(issues)} issue(s) found:**")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("**[green]All artifacts present and consistent.[/green]**")

    output = "\n".join(lines)

    panel = Panel(
        output,
        title=f"[bold cyan]Analysis: {feature}[/bold cyan]",
        border_style="cyan",
        expand=False,
    )
    console.print(panel)
