# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plan CLI — ``mekong plan from-init``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import shutil

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import typer

from src.cli.commands.plan import i18n as i18n_mod
from src.cli.commands.plan.domain_data import _DOMAIN_OUTLINES, _PHASES, _domain_outlines
from src.cli.commands.plan.generators import (
    _generate_plan_md, _generate_spec, _load_company, _slug, _write_artifacts,
)
from src.cli.commands.plan.spec_templates import render_data_model, render_quickstart, render_research

app = typer.Typer(name="plan", help="Generate plan from company init", no_args_is_help=True, add_completion=False, rich_markup_mode="rich")
console = Console()
DEFAULT_LOCALE = "en"


@app.command("from-init")
def from_init_cmd(
    output_dir: Path = typer.Option(Path("."), "--dir", "-d", exists=False, file_okay=False, dir_okay=True, help="Project root (default: CWD)."),
    lang: str = typer.Option(DEFAULT_LOCALE, "--lang", help="Output language: en | vi."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing SPEC_OUTPUT.md and plans/."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview spec path and planned plan directory without writing files."),
) -> None:
    """Generate spec and plan from .mekong/company.json."""
    path = output_dir.resolve()
    company = _load_company(path)
    if company is None:
        msg = i18n_mod.t(lang, "no_company", ".mekong/company.json not found. Run `mekong company init` first.")
        console.print(f"[yellow]{msg}[/]")
        raise typer.Exit(code=1)

    if lang not in ("en", "vi"):
        console.print(f'[red]{i18n_mod.t(lang, "invalid_lang", f"Invalid --lang: {lang}. Use en | vi.")}[/]')
        raise typer.Exit(code=1)

    product_type = company.get("product_type", "saas")
    outlines = _domain_outlines(product_type, lang)
    if not outlines:
        console.print(f'[yellow]{i18n_mod.t(lang, "no_domains_hint", f"No domain outline for product_type {product_type!r}. Using generic.")}[/]')
        outlines = ["Core platform features"]

    spec_path, plans_root = path / ".mekong" / "SPEC_OUTPUT.md", path / "plans"
    if dry_run:
        slug = _slug(company.get("company_name", "project"))
        plan_dir_preview = plans_root / f"{slug}-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        console.print(
            "[bold yellow][DRY RUN][/] Preview only — nothing written.\n\n"
            f"  company:    [cyan]{company.get('company_name', '?')}[/]\n"
            f"  product:    [cyan]{product_type}[/]\n"
            f"  spec_path:  [cyan]{spec_path}[/]\n"
            f"  plan_dir:   [cyan]{plan_dir_preview}[/]\n"
            f"  domains:    [cyan]{len(outlines)}[/]\n\n"
            "[dim]Run without --dry-run to generate spec + plan.[/]"
        )
        raise typer.Exit(code=0)

    if not force and spec_path.exists():
        console.print(f'[yellow]{i18n_mod.t(lang, "spec_exists", f"SPEC_OUTPUT.md already exists at {spec_path}. Use --force to overwrite.")}[/]')
        raise typer.Exit(code=1)
    if not force and plans_root.exists() and any(plans_root.iterdir()):
        console.print(f'[yellow]{i18n_mod.t(lang, "plans_exist", "plans/ directory already has content. Use --force to overwrite.")}[/]')
        raise typer.Exit(code=1)

    if force and plans_root.exists():
        for item in plans_root.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)

    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(_generate_spec(company, outlines, lang), encoding="utf-8")
    _, plan_dir = _generate_plan_md(company, outlines, lang)
    _write_artifacts(plan_dir, company, lang)

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("key", style="cyan", no_wrap=True)
    table.add_column("value", style="green")
    for k, v in [
        ("company", company.get("company_name", "?")), ("product", product_type),
        ("spec", str(spec_path.relative_to(path))), ("plan_dir", str(plan_dir)), ("domains", str(len(outlines))),
    ]:
        table.add_row(k, v)
    console.print(Panel(table, title=i18n_mod.t(lang, "plan_generated_title", "Plan Generated"), border_style="green", expand=False))


__all__ = [
    "DEFAULT_LOCALE", "_DOMAIN_OUTLINES", "_PHASES", "_domain_outlines", "_generate_plan_md",
    "_generate_spec", "_load_company", "_slug", "_write_artifacts", "app", "console",
    "from_init_cmd", "render_data_model", "render_quickstart", "render_research",
]
