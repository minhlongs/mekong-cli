# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for the Vietnam business-funnel commands.

Reaches the existing library code in ``src/commands/zalo_oa.py``,
``src/commands/thue_dnvn.py``, ``src/commands/ke_toan.py``, and
``src/commands/sophia_video.py`` — which
already have unit tests — and exposes them as Typer sub-apps so the
``mekong`` binary can dispatch::

    mekong zalo-oa   send|broadcast|followers|caption|post
    mekong thue       tncn|tndn|gtgt
    mekong ke-toan    create|xml|journal|summary
    mekong tools video render|status|list|voices|avatars|templates|cost

Import paths used by ``src/cli/app_setup.py``::

    from src.cli.funnel_commands import ke_toan_app, thue_app, zalo_app, sophia_app
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional
from typing import Any

import typer

from src.commands.ke_toan import create_invoice
from src.commands.sophia_video import app as sophia_app
from src.commands.thue_dnvn import (
    calculate_gtgt,
    calculate_tncn,
    calculate_tndn,
)

__all__ = ["ke_toan_app", "sophia_app", "thue_app", "zalo_app"]

# ---------------------------------------------------------------------------
# Zalo OA
# ---------------------------------------------------------------------------

zalo_app = typer.Typer(
    name="zalo-oa",
    help="Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


def _zalo_client() -> Any:
    """Lazy factory mirroring src/commands/zalo_oa.py::_get_client()."""
    from integrations.zalo import ZaloOAClient

    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    app_id = os.getenv("ZALO_APP_ID", "")
    if not token:
        typer.echo("❌ Thiếu ZALO_OA_ACCESS_TOKEN. Đặt trong .env.", err=True)
        raise typer.Exit(code=1)
    return ZaloOAClient(access_token=token, app_id=app_id)


@zalo_app.command(name="send")
def zalo_send(
    user_id: str = typer.Argument(..., help="Zalo user ID"),
    message: str = typer.Argument(..., help="Nội dung tin nhắn"),
) -> None:
    """Gửi tin nhắn cá nhân qua Zalo OA."""
    client = _zalo_client()
    result = client.send_message(user_id, message)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="broadcast")
def zalo_broadcast(
    message: str = typer.Argument(..., help="Nội dung broadcast"),
) -> None:
    """Broadcast đến tất cả followers."""
    client = _zalo_client()
    result = client.broadcast(message)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="followers")
def zalo_followers(
    offset: int = typer.Option(0, "--offset", help="Vị trí bắt đầu"),
    count: int = typer.Option(50, "--count", help="Số lượng tối đa"),
) -> None:
    """Xem danh sách followers."""
    client = _zalo_client()
    result = client.get_followers(offset=offset, count=count)
    total = result.get("data", {}).get("total", 0)
    typer.echo(f"Tổng followers: {total:,}")
    for uid in result.get("data", {}).get("followers", []):
        typer.echo(f"  - {uid.get('user_id', '')} | {uid.get('display_name', '')}")


@zalo_app.command(name="caption")
def zalo_caption(
    product: str = typer.Argument(..., help="Tên sản phẩm/dịch vụ"),
    tone: str = typer.Option(
        "than_thien",
        "--tone",
        help="Giọng văn: than_thien | chuyen_nghiep | vui_ve",
    ),
) -> None:
    """Tạo caption marketing tự động (offline, không cần token)."""
    from integrations.zalo import generate_vn_caption

    typer.echo(generate_vn_caption(product=product, tone=tone))


@zalo_app.command(name="post")
def zalo_post(
    title: str = typer.Argument(..., help="Tiêu đề bài viết"),
    content: str = typer.Argument(..., help="Nội dung bài viết"),
    cover: str = typer.Option("", "--cover", help="URL ảnh bìa"),
) -> None:
    """Đăng bài viết lên Zalo OA."""
    client = _zalo_client()
    result = client.post_article(title=title, content=content, cover_image=cover)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Thuế VN
# ---------------------------------------------------------------------------

thue_app = typer.Typer(
    name="thue",
    help="Thuế VN — TNCN lũy tiến, TNDN, GTGT (offline, không cần API)",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


@thue_app.callback(invoke_without_command=True)
def thue_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Hệ thống tính thuế Việt Nam — TNCN lũy tiến, TNDN, GTGT."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.thue_engine import ThueEngine

    engine = ThueEngine()
    status_data = engine.get_status()

    if json_mode:
        import json

        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(
        Panel(
            f"[bold green]Hệ Thống Thuế Việt Nam (TNCN, TNDN, GTGT)[/]\n\n"
            f"  Tổng số lượt tính:       [cyan]{status_data['total_calculations']}[/]\n"
            f"  Tổng tiền thuế mô phỏng: [yellow]{status_data['total_tax_simulated']:,.0f} đ[/]\n"
            f"  Hồ sơ thuế mẫu:          [magenta]{status_data['total_profiles']}[/]\n"
            f"  Giảm trừ bản thân:       [bold]11.000.000 đ/tháng[/]\n"
            f"  Giảm trừ người PT:       [bold]4.400.000 đ/người/tháng[/]\n"
            f"  Thuế TNDN tiêu chuẩn:    [bold]20%[/] (Ưu đãi SME: [bold green]17%[/])",
            title="[bold blue]Thuế Doanh Nghiệp & Cá Nhân VN[/]",
            border_style="green",
        )
    )

    table = Table(title="Lịch Sử Tính Thuế Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã Tính", style="dim", width=18)
    table.add_column("Loại Thuế", style="cyan", width=10)
    table.add_column("Số Tiền Gốc", justify="right", width=16)
    table.add_column("Tiền Thuế", justify="right", width=16)
    table.add_column("Thuế Suất", justify="right", width=10)

    for c in status_data.get("recent_calculations", []):
        table.add_row(
            c["calc_id"],
            c["tax_type"].upper(),
            f"{c['gross_amount']:,.0f} đ",
            f"{c['tax_amount']:,.0f} đ",
            f"{c['effective_rate']:.1f}%",
        )

    console.print(table)


@thue_app.command(name="tncn")
def thue_tncn(
    monthly_income: int = typer.Argument(..., help="Thu nhập gộp/tháng (VND)"),
    dependents: int = typer.Option(0, "--dependents", "-d", help="Số người phụ thuộc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính thuế TNCN lũy tiến (Điều 22, Luật thuế TNCN)."""
    from src.core.thue_engine import ThueEngine

    engine = ThueEngine()
    result = engine.calculate_tncn(monthly_income, dependents=dependents)

    if json_mode:
        import json

        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    try:
        typer.echo(calculate_tncn(monthly_income, dependents=dependents).to_summary())
    except Exception:
        typer.echo(
            f"=== TÍNH THUẾ TNCN ===\n"
            f"Thu nhập gộp:      {result['formatted']['gross']}/tháng\n"
            f"Giảm trừ bản thân: {result['personal_deduction']:,.0f} đ\n"
            f"Giảm trừ PT:       {result['dependent_deduction']:,.0f} đ\n"
            f"Thu nhập tính thuế:{result['formatted']['taxable']}\n"
            f"Tiền thuế TNCN:    {result['formatted']['tax']}\n"
            f"Thu nhập thực nhận:{result['formatted']['net']}\n"
            f"Thuế suất thực tế: {result['effective_rate_pct']:.1f}%\n"
        )


@thue_app.command(name="tndn")
def thue_tndn(
    annual_revenue: int = typer.Argument(..., help="Doanh thu năm (VND)"),
    profit: Optional[int] = typer.Option(None, "--profit", "-p", help="Lợi nhuận tính thuế (VND)"),
    sme: bool = typer.Option(True, "--sme/--no-sme", help="Áp dụng ưu đãi SME 17% nếu ≤ 3 tỷ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính thuế TNDN (20% tiêu chuẩn, 17% SME ≤ 3 tỷ/năm)."""
    from src.core.thue_engine import ThueEngine

    engine = ThueEngine()
    result = engine.calculate_tndn(annual_revenue, profit=profit, is_sme=sme)

    if json_mode:
        import json

        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    try:
        typer.echo(calculate_tndn(annual_revenue).to_summary())
    except Exception:
        typer.echo(
            f"=== TÍNH THUẾ TNDN ===\n"
            f"Doanh thu:       {result['formatted']['revenue']}\n"
            f"Lợi nhuận ước tính: {result['formatted']['profit']}\n"
            f"Thuế suất:       {result['applied_rate_pct']}%\n"
            f"Tiền thuế TNDN:  {result['formatted']['tax']}\n"
            f"Lợi nhuận ròng:  {result['formatted']['net_profit']}\n"
        )


@thue_app.command(name="gtgt")
def thue_gtgt(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    rate: int = typer.Option(10, "--rate", "-r", help="Thuế suất GTGT (0/5/8/10)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính thuế GTGT."""
    from src.core.thue_engine import ThueEngine

    engine = ThueEngine()
    result = engine.calculate_gtgt(amount, rate=rate)

    if json_mode:
        import json

        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    typer.echo(
        f"Cơ sở: {result['formatted']['subtotal']}\n"
        f"Thuế GTGT ({result['vat_rate_pct']}%): {result['formatted']['vat']}\n"
        f"Tổng cộng: {result['formatted']['total']}\n\n"
        f"⚠️  Tra cứu tại thuedientu.gdt.gov.vn để xác nhận."
    )


@thue_app.command(name="status")
def thue_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem tổng quan tình trạng tính thuế và số liệu mô phỏng."""
    from src.core.thue_engine import ThueEngine

    engine = ThueEngine()
    data = engine.get_status()

    if json_mode:
        import json

        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            f"Tổng số lượt tính: [cyan]{data['total_calculations']}[/]\n"
            f"Tổng tiền thuế mô phỏng: [yellow]{data['total_tax_simulated']:,.0f} đ[/]\n"
            f"Hồ sơ người nộp thuế: [magenta]{data['total_profiles']}[/]",
            title="[bold green]Trạng Thái Thuế VN[/]",
            border_style="green",
        )
    )


@thue_app.command(name="list")
def thue_list(
    tax_type: str = typer.Option("all", "--type", "-t", help="Lọc loại thuế (tncn, tndn, gtgt, all)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Liệt kê các phép tính thuế đã thực hiện."""
    from src.core.thue_engine import ThueEngine

    engine = ThueEngine()
    records = engine.list_calculations(tax_type=tax_type, limit=limit)

    if json_mode:
        import json

        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title=f"Lịch Sử Tính Thuế ({tax_type.upper()})", show_header=True, header_style="bold magenta")
    table.add_column("Mã Tính", style="dim", width=18)
    table.add_column("Loại", style="cyan", width=8)
    table.add_column("Số Tiền", justify="right", width=16)
    table.add_column("Tiền Thuế", justify="right", width=16)
    table.add_column("Thuế Suất", justify="right", width=10)
    table.add_column("Thời Gian", style="dim")

    for r in records:
        table.add_row(
            r["calc_id"],
            r["tax_type"].upper(),
            f"{r['gross_amount']:,.0f} đ",
            f"{r['tax_amount']:,.0f} đ",
            f"{r['effective_rate']:.1f}%",
            r["created_at"][:19],
        )

    console.print(table)



# ---------------------------------------------------------------------------
# Kế Toán VN
# ---------------------------------------------------------------------------

ke_toan_app = typer.Typer(
    name="ke-toan",
    help="Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)


@ke_toan_app.command(name="create")
def ke_toan_create(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
) -> None:
    """Tạo hóa đơn đơn giản và in summary."""
    invoice = create_invoice(
        amount=amount,
        vat_rate=vat_rate,
        buyer=buyer,
        seller=seller,
        seller_tax_code=seller_tax_code,
        description=description,
    )
    typer.echo(invoice.to_summary())


@ke_toan_app.command(name="xml")
def ke_toan_xml(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
) -> None:
    """Xuất XML hóa đơn theo schema TT78/2021."""
    invoice = create_invoice(
        amount=amount,
        vat_rate=vat_rate,
        buyer=buyer,
        seller=seller,
        seller_tax_code=seller_tax_code,
        description=description,
    )
    typer.echo(invoice.to_xml())


@ke_toan_app.command(name="journal")
def ke_toan_journal(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
) -> None:
    """Xuất bút toán kế toán VAS (JSON)."""
    invoice = create_invoice(
        amount=amount,
        vat_rate=vat_rate,
        buyer=buyer,
        seller=seller,
        seller_tax_code=seller_tax_code,
        description=description,
    )
    typer.echo(json.dumps(invoice.to_journal_entry(), ensure_ascii=False, indent=2))


@ke_toan_app.command(name="summary")
def ke_toan_summary(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
) -> None:
    """In summary hóa đơn (dạng text dễ đọc)."""
    invoice = create_invoice(
        amount=amount,
        vat_rate=vat_rate,
        buyer=buyer,
        seller=seller,
        seller_tax_code=seller_tax_code,
        description=description,
    )
    typer.echo(invoice.to_summary())
