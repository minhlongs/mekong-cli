"""SDD Phase 2: Tasks runner -- `mekong tasks run <feature>`.

Generates a TDD-ordered task list from `.specify/templates/tasks-template.md`.
Finds the matching spec file in `specs/`, renders with task context, writes
`specs/NNN-<slug>/tasks.md`.

TDD ordering: test tasks first ([P] parallel-safe), then impl tasks, then
integration tasks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

tasks_app = typer.Typer(
    name="tasks",
    help="SDD: generate TDD-ordered task list from spec",
    no_args_is_help=True,
    add_completion=False,
)


def _find_spec_dir(specs_base: Path, slug: str) -> Optional[Path]:
    """Find the spec directory matching *slug* under *specs_base/*.

    Matches ``NNN-<slug>`` dirs where the slug portion is a prefix match.
    Returns the first match, or None.
    """
    if not specs_base.is_dir():
        return None
    for entry in sorted(specs_base.iterdir()):
        if not entry.is_dir():
            continue
        parts = entry.name.split("-", 1)
        if len(parts) == 2 and parts[1] == slug:
            return entry
    # Fallback: try exact match on slug-after-NNN-
    for entry in sorted(specs_base.iterdir()):
        if not entry.is_dir():
            continue
        parts = entry.name.split("-", 1)
        if len(parts) == 2 and slug in parts[1]:
            return entry
    return None


def _load_template() -> str:
    """Load tasks-template.md, falling back to an inline template."""
    inline = (
        "# Tasks: {title}\n\n"
        "## Task List (TDD order)\n\n"
        "<!-- [P] = parallel-safe (no shared state); no marker = sequential -->\n\n"
        "### Tests (Prerequisites)\n\n"
        "- [ ] **[P]** {test_task_1}\n"
        "- [ ] **[P]** {test_task_2}\n"
        "- [ ] **[P]** {test_task_3}\n\n"
        "### Implementation\n\n"
        "- [ ] {impl_task_1}\n"
        "- [ ] {impl_task_2}\n"
        "- [ ] {impl_task_3}\n\n"
        "### Integration\n\n"
        "- [ ] {integ_task_1}\n"
        "- [ ] {integ_task_2}\n\n"
        "---\n- TDD ordering enforced: tests before implementation\n"
        "- `[P]` = parallel-safe (no shared state with sibling tasks)\n"
        "- Execute in order; `[P]` tasks within the same group can run concurrently\n\n"
        "> Generated at: {timestamp}\n> Template: `.specify/templates/tasks-template.md`\n"
    )
    from src.core.spec_templates import load_template
    return load_template("tasks") or inline


@tasks_app.command("run")
def tasks_run(
    feature_slug: str = typer.Argument(
        ..., help="Feature slug, e.g. add-auth"
    ),
    spec_dir: Path = typer.Option(
        Path("specs"),
        "--spec-dir",
        "-d",
        help="Base directory containing NNN-<slug> spec dirs.",
    ),
) -> None:
    """Generate a TDD-ordered task list for a feature spec.

    Finds the matching ``specs/NNN-<slug>/`` directory, renders the tasks
    template with TDD ordering (test tasks first, [P] = parallel-safe),
    and writes ``specs/NNN-<slug>/tasks.md``.

    TDD ORDER:
      1. Test tasks (all marked [P])
      2. Implementation tasks
      3. Integration tasks
    """
    resolved = spec_dir.resolve()
    spec_section = _find_spec_dir(resolved, feature_slug)
    if spec_section is None:
        console.print(
            f"[red]No spec directory found for slug '{feature_slug}' "
            f"under {resolved}[/red]"
        )
        raise typer.Exit(code=1)

    tasks_path = spec_section / "tasks.md"
    if tasks_path.exists():
        console.print(
            f"[yellow]Overwriting existing {tasks_path}[/yellow]"
        )

    tmpl = _load_template()
    context = {
        "title": feature_slug,
        "test_task_1": (
            f"[P] Write unit tests for {feature_slug} core logic"
        ),
        "test_task_2": (
            f"[P] Write integration tests for {feature_slug} handlers"
        ),
        "test_task_3": (
            f"[P] Write edge-case tests for {feature_slug} error paths"
        ),
        "impl_task_1": f"Implement {feature_slug} core module",
        "impl_task_2": f"Add {feature_slug} CLI entry point",
        "impl_task_3": f"Wire {feature_slug} into existing pipeline",
        "integ_task_1": f"Run full test suite for {feature_slug}",
        "integ_task_2": f"Verify {feature_slug} end-to-end flow",
    }

    # Try template rendering first, fallback to manual substitution
    rendered = _safe_format(tmpl, context)
    tasks_path.write_text(rendered, encoding="utf-8")

    try:
        rel = tasks_path.relative_to(Path.cwd())
    except ValueError:
        rel = tasks_path

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    table.add_row("feature", feature_slug)
    table.add_row("output", str(rel))
    table.add_row("order", "TDD: tests -> impl -> integration")

    console.print(
        Panel(
            table,
            title="[bold green]Tasks Generated[/]",
            border_style="green",
            expand=False,
        )
    )


def _safe_format(template: str, context: dict[str, str]) -> str:
    """Safe str.format_map that logs missing keys but continues rendering."""
    try:
        return template.format_map(context)
    except KeyError as exc:
        console.print(
            f"[yellow]Template key not provided: {exc} "
            f"(-- leaving placeholder unreplaced)[/yellow]"
        )
        # Re-render, replacing only known keys
        result = template
        for key, value in context.items():
            result = result.replace("{" + key + "}", value)
        return result
