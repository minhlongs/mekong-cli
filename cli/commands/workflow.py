"""🌐 mekong workflow — FABRIC catalog browser (list, show, domains).

Single source of truth: `src.command_fabric.catalog` (`.claude/commands/*.md`).

Bilingual VI+EN per row: column headers use `name / tên`; help strings per
subcommand carry both scripts so non-technical operators can discover skills.

Delegates domain inference + table rendering to `_workflow_catalog_helpers`
to keep this file thin and testable.
"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cli.commands._workflow_catalog_helpers import (
    _DOMAIN_BY_ID,
    _DOMAIN_ORDER,
    _DOMAIN_SCOPES,
    _DOMAIN_RULES,
    build_command_catalog,
    get_domain_groups,
    infer_domain,
    render_domain_table,
    render_summary,
)

console = Console()
workflow_app = typer.Typer(
    help=(
        "🌐 FABRIC Workflow Catalog — browse the 300+ skills registry.\n"
        " Liên kết kiểm tra / xem chi tiết kỹ năng theo domain.\n"
        " Subcommands / Lệnh con: list, show, domains"
    ),
    no_args_is_help=True,
    rich_markup_mode="rich",
)


@workflow_app.command("list")
def workflow_list(
    domain: str | None = typer.Option(
        None,
        "--domain",
        "-d",
        help="Filter / Lọc theo domain id (engineering, business, ...) / VD: engineering, business.",
        show_default=False,
    ),
    compact: bool = typer.Option(
        False,
        "--compact",
        help="Compact: hide descriptions / Ẩn mô tả.",
    ),
) -> None:
    """List / Liệt kê kỹ năng theo domain."""
    try:
        records: list = list(build_command_catalog())
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]✘ Failed / Lỗi khi load catalog: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    grouped = get_domain_groups(records)
    domain_count, total = len(grouped), len(records)

    console.print(
        Panel.fit(
            "[bold]🌐 FABRIC Catalog[/bold]\n"
            "[dim].claude/commands/*.md → registry → mekong <cmd>[/dim]",
            title="Catalog Overview / Tổng quan Catalog",
            border_style="cyan",
        )
    )

    if domain:
        d = domain.strip().lower()
        if d not in grouped:
            console.print(
                f"[yellow]⚠️ Domain not found / Không tìm thấy domain:[/yellow] "
                f"[bold]{domain}[/bold]\n"
                f"[dim]Available / Có sẵn:[/dim] [cyan]{', '.join(_DOMAIN_ORDER)}[/cyan] "
                f"[/cyan]general[/cyan]"
            )
            raise typer.Exit(code=1)
        label, _ = _DOMAIN_BY_ID.get(d, ("📦 General / Khác", ""))
        render_domain_table(grouped[d], title=f"{label} ({len(grouped[d])})", compact=compact)
        console.print(
            f"\n[dim]⊗ {total} total / tổng | {domain_count} domain(s) / lĩnh vực[/dim]"
        )
        return

    for domain_id in _DOMAIN_ORDER:
        recs = grouped.get(domain_id)
        if not recs:
            continue
        label, _ = _DOMAIN_BY_ID[domain_id]
        render_domain_table(recs, title=f"{label} — {len(recs)} skills / kỹ năng", compact=compact)

    if "general" in grouped:
        render_domain_table(
            grouped["general"],
            title="📦 General / Khác — uncategorized / chưa phân loại",
            compact=compact,
        )

    console.print()
    console.print(Panel(render_summary(total, domain_count), border_style="dim", padding=(0, 2)))
    console.print(
        "\n[dim]Tip / Mẹo:[/dim] [bold]mekong workflow show <name> / <tên>[/bold]"
        " — details of one skill / chi tiết một kỹ năng"
    )


@workflow_app.command("show")
def workflow_show(
    name: str = typer.Argument(
        ...,
        help="Skill / workflow name (e.g. cook, analyze, binh-phap) / Tên kỹ năng.",
        show_default=False,
    ),
) -> None:
    """Show detail / Hiển thị chi tiết của một skill."""
    try:
        records: list = list(build_command_catalog())
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]✘ Failed / Lỗi: {exc}[/red]")
        raise typer.Exit(code=1) from exc

    by_name = {rec.name: rec for rec in records}
    rec = by_name.get(name)
    if rec is None:
        matches = [n for n in by_name if name.lower() in n.lower()][:6]
        hint = (
            f"[dim]Did you mean / Có phải bạn muốn:[/dim] "
            f"[cyan]{', '.join(matches)}[/cyan]\n"
            if matches
            else ""
        )
        console.print(
            f"[red]✘ Unknown / Không rõ:[/red] [bold]{name}[/bold]\n"
            f"{hint}"
            "[dim]Run / Chạy[/dim] [bold]mekong workflow list[/bold] "
            "[dim]to browse / để duyệt.[/dim]"
        )
        raise typer.Exit(code=1)

    domain_id = infer_domain(rec.name, rec.description, rec.layer)
    domain_label, _ = _DOMAIN_BY_ID.get(domain_id, ("📦 General / Khác", ""))

    meta = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    meta.add_column("Field / Trường", style="bold cyan", no_wrap=True)
    meta.add_column("Value / Giá trị")
    meta.add_row("name / tên", f"[bold]{rec.name}[/bold]")
    meta.add_row("source / nguồn", rec.source)
    meta.add_row("description / mô tả", rec.description or "—")
    meta.add_row("domain / lĩnh vực", f"{domain_label} [dim](id: {domain_id})[/dim]")
    if rec.layer:
        meta.add_row("layer / tầng", rec.layer)
    console.print(Panel(meta, title=f"📄 {rec.name}", border_style="cyan", padding=(1, 2)))

    if rec.execution:
        console.print("\n[bold]⚙️ Execution / Cách chạy[/bold]")
        console.print(Panel(rec.execution, border_style="dim", padding=(0, 2)))

    meta2 = Table(
        title="Metadata",
        title_style="bold",
        header_style="bold cyan",
        expand=True,
        show_lines=False,
    )
    meta2.add_column("Key / Khóa", style="bold", no_wrap=True, min_width=20)
    meta2.add_column("Value / Giá trị", style="dim")
    if rec.argument_hint:
        meta2.add_row("argument_hint / gợi ý đối số", rec.argument_hint)
    if rec.allowed_tools:
        meta2.add_row(
            "allowed_tools / công cụ cho phép",
            ", ".join(rec.allowed_tools) if rec.allowed_tools else "—",
        )
    if rec.contract:
        meta2.add_row("contract / hợp đồng", rec.contract)
    if rec.portability_targets:
        meta2.add_row(
            "portability / cổng chạy",
            ", ".join(rec.portability_targets[:12])
            + (" …" if len(rec.portability_targets) > 12 else ""),
        )
    console.print(meta2)


@workflow_app.command("domains")
def workflow_domains() -> None:
    """Show available domain ids / Hiển thị danh sách domain."""
    table = Table(
        title="🌐 Domains / Lĩnh vực",
        title_style="bold",
        header_style="bold cyan",
        expand=True,
    )
    table.add_column("ID", style="bold", no_wrap=True)
    table.add_column("Label (VI + EN)", style="bold")
    table.add_column("Scope / Phạm vi", style="dim")
    for domain_id in _DOMAIN_ORDER + ["general"]:
        label, _ = _DOMAIN_BY_ID.get(domain_id, ("📦 General / Khác", ""))
        table.add_row(domain_id, label, _DOMAIN_SCOPES.get(domain_id, ""))
    console.print(table)
