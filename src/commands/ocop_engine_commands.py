# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""OCOP Engine subcommands (eval, products, listing, compliance, status)."""

from __future__ import annotations

import json
import sys

from rich.panel import Panel
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.ocop_commands"]


def ocop_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan OCOP dạng JSON"),
) -> None:
    """OCOP: AI-powered agricultural export tools & star rating."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.ocop_engine import OcopEngine

    f = _facade()
    engine = OcopEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    f.console.print(
        Panel(
            f"[bold green]CHƯƠNG TRÌNH OCOP QUỐC GIA — MỖI XÃ MỘT SẢN PHẨM[/]\n"
            f"  Quyết định căn cứ:     [cyan]{', '.join(status_data['governing_decrees'])}[/]\n"
            f"  Trạng thái:            [bold green]{status_data['status'].upper()}[/]\n"
            f"  Tổng sản phẩm:         [bold]{status_data['total_products']}[/]\n"
            f"  Hạng 5 Sao (Quốc gia): [bold yellow]{status_data['star_breakdown']['5_stars_national_export']}[/]\n"
            f"  Hạng 4 Sao (Cấp tỉnh): [bold blue]{status_data['star_breakdown']['4_stars_provincial_high']}[/]\n"
            f"  Hạng 3 Sao:            [bold]{status_data['star_breakdown']['3_stars_regional']}[/]\n"
            f"  Đánh giá phân hạng:    [bold cyan]{status_data['total_evaluations_run']}[/]\n"
            f"  Listing xuất khẩu B2B: [bold magenta]{status_data['total_export_listings']}[/]",
            title="[bold green]OCOP Export Platform[/]",
            border_style="green",
        )
    )

    table = Table(title="Sản Phẩm OCOP Tiêu Biểu Sẵn Sàng Xuất Khẩu", show_header=True, header_style="bold cyan")
    table.add_column("Mã SP", style="dim", width=14)
    table.add_column("Tên Sản Phẩm", style="bold green", width=28)
    table.add_column("Sao", justify="center", width=8)
    table.add_column("Mã HS", justify="center", width=10)
    table.add_column("Xuất Xứ", width=18)
    table.add_column("Thị Trường", width=20)

    for p in engine.list_products(min_stars=4)[:5]:
        table.add_row(
            p["product_id"],
            p["name"],
            "⭐" * p["star_rating"],
            p["hs_code"],
            p["origin_province"],
            ", ".join(p["primary_markets"][:3]),
        )
    f.console.print(table)


def ocop_eval(
    product: str = typer.Argument(..., help="Tên sản phẩm nông nghiệp OCOP"),
    part_a: float = typer.Option(30.0, "--part-a", help="Điểm phần A - Tổ chức sản xuất & cộng đồng (tối đa 35)"),
    part_b: float = typer.Option(22.0, "--part-b", help="Điểm phần B - Tiếp thị & thương mại hóa (tối đa 25)"),
    part_c: float = typer.Option(38.0, "--part-c", help="Điểm phần C - Chất lượng & quy chuẩn sản phẩm (tối đa 40)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả đánh giá dạng JSON"),
) -> None:
    """Đánh giá phân hạng sao OCOP (1 đến 5 sao) theo Quyết định 148/QĐ-TTg."""
    from src.core.ocop_engine import OcopEngine

    f = _facade()
    engine = OcopEngine()
    res = engine.evaluate_star_rating(
        product_name=product,
        part_a_community=part_a,
        part_b_marketing=part_b,
        part_c_quality=part_c,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    stars_icon = "⭐" * res["star_rating"]
    f.console.print(
        Panel(
            f"[bold]Sản phẩm đánh giá:[/]   [bold green]{res['product_name']}[/]\n"
            f"[bold]Mã hồ sơ:[/]            {res['eval_id']}\n"
            f"[bold]Căn cứ pháp lý:[/]      {res['decree']}\n"
            f"[bold]Phần A (Sản xuất):[/]   [cyan]{res['scores']['part_a_community_max35']}/35.0[/]\n"
            f"[bold]Phần B (Tiếp thị):[/]   [cyan]{res['scores']['part_b_marketing_max25']}/25.0[/]\n"
            f"[bold]Phần C (Chất lượng):[/] [cyan]{res['scores']['part_c_quality_max40']}/40.0[/]\n"
            f"[bold]Tổng điểm đạt được:[/]  [bold yellow]{res['scores']['total_score_max100']}/100.0[/]\n"
            f"[bold]Phân hạng OCOP:[/]      [bold yellow]{stars_icon} ({res['star_rating']} Sao)[/]\n"
            f"[bold]Danh hiệu:[/]           [bold]{res['grade_title']}[/]\n"
            f"[bold]Tiềm năng xuất khẩu:[/] [bold magenta]{res['export_potential']}[/]",
            title="[bold green]Kết Quả Đánh Giá Phân Hạng OCOP[/]",
            border_style="green",
        )
    )


def ocop_products(
    min_stars: int = typer.Option(1, "--min-stars", "-s", help="Lọc số sao tối thiểu (1-5)"),
    province: str = typer.Option("all", "--province", "-p", help="Lọc theo tỉnh thành xuất xứ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu sản phẩm dạng JSON"),
) -> None:
    """Tra cứu danh mục sản phẩm OCOP, mã HS và tiêu chuẩn chất lượng."""
    from src.core.ocop_engine import OcopEngine

    f = _facade()
    engine = OcopEngine()
    prods = engine.list_products(min_stars=min_stars, province=province)

    if json_mode:
        typer.echo(json.dumps({"total": len(prods), "products": prods}, indent=2, ensure_ascii=False))
        return

    table = Table(title="Danh Mục Sản Phẩm OCOP Xuất Khẩu", show_header=True, header_style="bold magenta")
    table.add_column("Mã SP", style="dim", width=14)
    table.add_column("Tên Sản Phẩm", style="bold green", width=26)
    table.add_column("Ngành Hàng", width=20)
    table.add_column("Tỉnh Thành", width=14)
    table.add_column("Sao", justify="center", width=8)
    table.add_column("Mã HS", justify="center", width=10)
    table.add_column("Chứng Nhận", width=22)

    for p in prods:
        table.add_row(
            p["product_id"],
            p["name"],
            p["category"],
            p["origin_province"],
            "⭐" * p["star_rating"],
            p["hs_code"],
            ", ".join(p["certifications"]),
        )
    f.console.print(table)
