# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""OCOP Export, Listing, Compliance, and Status commands."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import typer


def _facade():
    return sys.modules["src.commands.ocop_commands"]


def ocop_listing(
    product_id: str = typer.Argument(..., help="Mã sản phẩm (e.g. OCOP-ST25) hoặc tên sản phẩm"),
    market: str = typer.Option("EU", "--market", "-m", help="Thị trường xuất khẩu mục tiêu (EU, US, Japan, China, Middle East)"),
    platform: str = typer.Option("alibaba", "--platform", help="Sàn thương mại điện tử B2B (alibaba, amazon, shopee)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu listing dạng JSON"),
) -> None:
    """Tạo listing B2B thương mại điện tử xuất khẩu và rà soát FTA."""
    from src.core.ocop_engine import OcopEngine

    f = _facade()
    res = OcopEngine().generate_b2b_listing(product_id=product_id, target_market=market, platform=platform)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    f.console.print(
        Panel(
            f"[bold]Mã listing:[/]        {res['listing_id']}\n"
            f"[bold]Sản phẩm:[/]          [bold green]{res['product_name']}[/] (Mã HS: [cyan]{res['hs_code']}[/])\n"
            f"[bold]Phân hạng OCOP:[/]    {'⭐' * res['star_rating']} ({res['star_rating']} Sao)\n"
            f"[bold]Thị trường mục tiêu:[/] [bold magenta]{res['target_market']}[/] (Hiệp định: {res['compliance_summary']['fta']})\n"
            f"[bold]Sàn thương mại:[/]     [bold cyan]{res['platform'].upper()}[/]\n"
            f"[bold]Ưu đãi thuế quan:[/]   [green]{res['compliance_summary']['tariff_rate']}[/]\n"
            f"[bold]Chứng nhận bắt buộc:[/] {', '.join(res['compliance_summary']['certifications_required'])}\n\n"
            f"[bold cyan]Tiêu đề Listing (EN):[/]\n{res['title_en']}\n\n"
            f"[bold cyan]Mô tả sản phẩm (EN):[/]\n{res['description_en']}",
            title="[bold green]Listing Xuất Khẩu B2B Quốc Tế[/]",
            border_style="green",
        )
    )


def ocop_compliance(
    market: str = typer.Argument(..., help="Thị trường xuất khẩu (EU, US, Japan, China, Middle East)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất quy định xuất khẩu dạng JSON"),
) -> None:
    """Kiểm tra điều kiện kỹ thuật, thuế quan và chứng chỉ xuất khẩu nông sản."""
    from src.core.ocop_engine import OcopEngine

    f = _facade()
    res = OcopEngine().get_market_compliance(market)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    f.console.print(
        Panel(
            f"[bold]Thị trường mục tiêu:[/]   [bold magenta]{res['market']}[/]\n"
            f"[bold]Hiệp định thương mại:[/]  [cyan]{res['free_trade_agreement']}[/]\n"
            f"[bold]Ưu đãi thuế quan:[/]      [green]{res['tariff_preference']}[/]\n"
            f"[bold]Chứng nhận bắt buộc:[/]   [yellow]{', '.join(res['mandatory_certifications'])}[/]\n"
            f"[bold]Quy chuẩn bao bì/nhãn:[/] {res['packaging_rules']}",
            title=f"[bold green]Quy Chuẩn Xuất Khẩu — {res['market']}[/]",
            border_style="green",
        )
    )


def ocop_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dạng JSON"),
) -> None:
    """Kiểm tra trạng thái hệ thống OCOP và năng lực xuất khẩu."""
    from src.core.ocop_engine import OcopEngine

    f = _facade()
    status_data = OcopEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    f.console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG OCOP VIỆT NAM[/]\n\n"
            f"Trạng thái:               [bold green]{status_data['status'].upper()}[/]\n"
            f"Chương trình:             {status_data['program']}\n"
            f"Tổng sản phẩm đăng ký:    [bold]{status_data['total_products']}[/]\n"
            f"  - 5 Sao (Quốc gia):     [bold yellow]{status_data['star_breakdown']['5_stars_national_export']}[/]\n"
            f"  - 4 Sao (Cấp tỉnh):     [bold blue]{status_data['star_breakdown']['4_stars_provincial_high']}[/]\n"
            f"  - 3 Sao (Cơ sở):        [bold]{status_data['star_breakdown']['3_stars_regional']}[/]\n"
            f"Tổng số lượt đánh giá:    [cyan]{status_data['total_evaluations_run']}[/]\n"
            f"Listing B2B đã khởi tạo:  [magenta]{status_data['total_export_listings']}[/]\n"
            f"Thị trường hỗ trợ:        {', '.join(status_data['supported_target_markets'])}",
            title="[bold green]OCOP System Status[/]",
            border_style="green",
        )
    )


def analyze(
    file: str = typer.Argument(..., help="Product image or JSON file to analyze"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path (default: stdout)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed analysis"),
):
    """Analyze a product image/JSON for export-ready features."""
    f = _facade()
    file_path = Path(file)
    if not file_path.exists():
        f.console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)

    suffix = file_path.suffix.lower()
    if suffix not in (".json", ".jpg", ".jpeg", ".png", ".webp"):
        f.console.print(
            f"[red]Error: Unsupported file type '{suffix}'[/red]\n"
            "[dim]Supported: .json, .jpg, .jpeg, .png, .webp[/dim]"
        )
        raise typer.Exit(1)

    f.console.print(Panel(f"[bold cyan]Analyzing:[/bold cyan] {file_path.name}", title="🌾 OCOP Product Analysis", border_style="green"))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=f.console) as progress:
        task = progress.add_task("Loading product data...", total=None)
        if suffix == ".json":
            try:
                product_data = json.loads(file_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                f.console.print(f"[red]Error: Invalid JSON — {e}[/red]")
                raise typer.Exit(1)
        else:
            product_data = {"image_path": str(file_path.resolve()), "type": "image"}

        progress.update(task, description="Sending to AI Agent for analysis...")
        analysis = f._generate_analysis(product_data, file_path)
        progress.update(task, description="Analysis complete!")

    f._display_analysis(analysis, verbose)
    if output:
        Path(output).write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
        f.console.print(f"\n[green]✓ Results saved to {output}[/green]")
