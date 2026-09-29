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

__all__ = ["bhxh_app", "ke_toan_app", "sophia_app", "thue_app", "vietqr_app", "zalo_app"]

# ---------------------------------------------------------------------------
# Zalo OA
# ---------------------------------------------------------------------------

zalo_app = typer.Typer(
    name="zalo-oa",
    help="Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài",
    no_args_is_help=False,
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


@zalo_app.callback(invoke_without_command=True)
def zalo_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.zalo_engine import ZaloEngine

    engine = ZaloEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            f"[bold green]HỆ THỐNG ZALO OFFICIAL ACCOUNT (OA) & CSKH TỰ ĐỘNG[/]\n"
            f"  Trạng thái:            [bold cyan]{status_data['status'].upper()}[/]\n"
            f"  Tổng số người theo dõi:[bold]{status_data['total_followers']}[/]\n"
            f"  Tin nhắn đã gửi:       [yellow]{status_data['total_messages_sent']}[/]\n"
            f"  Chiến dịch broadcast:  [green]{status_data['total_broadcasts']}[/]\n"
            f"  Caption đã khởi tạo:   [bold magenta]{status_data['total_captions_generated']}[/]\n"
            f"  Chế độ tích hợp:       [bold]{status_data['integration_mode']}[/]",
            title="[bold blue]Zalo OA Marketing & CSKH[/]",
            border_style="green",
        )
    )


@zalo_app.command(name="send")
def zalo_send(
    user_id: str = typer.Argument(..., help="Zalo user ID"),
    message: str = typer.Argument(..., help="Nội dung tin nhắn"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Gửi tin nhắn cá nhân qua Zalo OA."""
    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    if mock:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        result = engine.send_message(user_id=user_id, text=message)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    client = _zalo_client()
    result = client.send_message(user_id, message)
    from src.core.zalo_engine import ZaloEngine

    ZaloEngine().send_message(user_id=user_id, text=message)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="broadcast")
def zalo_broadcast(
    message: str = typer.Argument(..., help="Nội dung broadcast"),
    title: str = typer.Option("Thông báo Zalo OA", "--title", "-t", help="Tiêu đề thông báo"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Broadcast đến tất cả followers."""
    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    if mock:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        result = engine.broadcast_campaign(title=title, text=message)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    client = _zalo_client()
    result = client.broadcast(message)
    from src.core.zalo_engine import ZaloEngine

    ZaloEngine().broadcast_campaign(title=title, text=message)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="followers")
def zalo_followers(
    offset: int = typer.Option(0, "--offset", help="Vị trí bắt đầu"),
    count: int = typer.Option(50, "--count", help="Số lượng tối đa"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem danh sách followers."""
    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    if mock:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        followers = engine.list_followers(limit=count)
        if json_mode:
            typer.echo(json.dumps({"total": len(followers), "followers": followers}, ensure_ascii=False, indent=2))
            return
        typer.echo(f"Tổng followers: {len(followers):,}")
        for uid in followers:
            typer.echo(f"  - {uid.get('user_id', '')} | {uid.get('name', '')} ({uid.get('segment', '')})")
        return

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
        help="Giọng văn: than_thien | chuyen_nghiep | vui_ve | sang_tao | khuyen_mai | binh_phap",
    ),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tạo caption marketing tự động (offline, không cần token)."""
    from src.core.zalo_engine import ZaloEngine

    engine = ZaloEngine()
    cap_data = engine.generate_caption(topic=product, tone=tone)

    if json_mode:
        typer.echo(json.dumps(cap_data, ensure_ascii=False, indent=2))
        return

    from integrations.zalo import generate_vn_caption

    typer.echo(generate_vn_caption(product=product, tone=tone))


@zalo_app.command(name="post")
def zalo_post(
    title: str = typer.Argument(..., help="Tiêu đề bài viết"),
    content: str = typer.Argument(..., help="Nội dung bài viết"),
    cover: str = typer.Option("", "--cover", help="URL ảnh bìa"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Đăng bài viết lên Zalo OA."""
    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    if mock:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        result = engine.create_post(title=title, content=content)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    client = _zalo_client()
    result = client.post_article(title=title, content=content, cover_image=cover)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="status")
def zalo_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem trạng thái hệ thống Zalo OA và số liệu marketing."""
    from src.core.zalo_engine import ZaloEngine

    engine = ZaloEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI ZALO OFFICIAL ACCOUNT[/]\n"
            f"Tổng followers:     [bold]{data['total_followers']}[/]\n"
            f"Tin nhắn CSKH:      [yellow]{data['total_messages_sent']}[/]\n"
            f"Broadcast đã gửi:   [green]{data['total_broadcasts']}[/]\n"
            f"Caption tiếp thị:   [bold magenta]{data['total_captions_generated']}[/]",
            title="[bold blue]Zalo OA Telemetry[/]",
            border_style="green",
        )
    )


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
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


@ke_toan_app.callback(invoke_without_command=True)
def ke_toan_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Kế toán VN — hóa đơn TT78/2021, bút toán VAS, XML."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    console.print(
        Panel(
            f"[bold green]HỆ THỐNG KẾ TOÁN VAS & HÓA ĐƠN ĐIỆN TỬ TT78[/]\n"
            f"  Trạng thái:            [bold cyan]{status_data['status'].upper()}[/]\n"
            f"  Tổng số hóa đơn:       [bold]{status_data['total_invoices']}[/]\n"
            f"  Tổng doanh thu:        [yellow]{status_data['total_revenue']:,.0f} đ[/]\n"
            f"  Thuế GTGT đầu ra:      [green]{status_data['total_vat_output']:,.0f} đ[/]\n"
            f"  Tổng tiền thanh toán:  [bold magenta]{status_data['total_gross_invoiced']:,.0f} đ[/]\n"
            f"  Bút toán VAS ghi sổ:   [bold]{status_data['total_journal_entries']}[/]\n"
            f"  Doanh số phát sinh:    [cyan]{status_data['total_ledger_turnover']:,.0f} đ[/]\n"
            f"  Danh mục tài khoản:    [bold]{status_data['total_accounts']} tài khoản VAS[/]",
            title="[bold blue]Kế Toán Doanh Nghiệp VN[/]",
            border_style="green",
        )
    )

    table = Table(title="Hóa Đơn Điện Tử Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã Hóa Đơn", style="dim", width=18)
    table.add_column("Người Mua", style="cyan", width=20)
    table.add_column("Tiền Hàng", justify="right", width=16)
    table.add_column("Thuế GTGT", justify="right", width=16)
    table.add_column("Tổng Cộng", justify="right", width=16)

    for inv in status_data.get("recent_invoices", []):
        table.add_row(
            inv["invoice_id"],
            inv["buyer_name"],
            f"{inv['subtotal']:,.0f} đ",
            f"{inv['vat_amount']:,.0f} đ",
            f"{inv['total_amount']:,.0f} đ",
        )

    console.print(table)


@ke_toan_app.command(name="create")
def ke_toan_create(
    amount: int = typer.Argument(..., help="Số tiền trước thuế (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT (0/5/8/10)"),
    buyer: str = typer.Option(..., "--buyer", help="Tên người mua"),
    seller: str = typer.Option("Doanh Nghiệp", "--seller", help="Tên người bán"),
    seller_tax_code: str = typer.Option("0000000000", "--mst", help="Mã số thuế người bán"),
    description: str = typer.Option("Hàng hóa/Dịch vụ", "--desc", help="Mô tả hàng hóa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tạo hóa đơn đơn giản và in summary."""
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()
    inv_data = engine.create_invoice(
        amount=amount,
        vat_rate=vat_rate,
        buyer=buyer,
        seller=seller,
        seller_tax_code=seller_tax_code,
        description=description,
    )

    if json_mode:
        typer.echo(json.dumps(inv_data, indent=2, ensure_ascii=False))
        return

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
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xuất bút toán kế toán VAS (JSON)."""
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()
    inv_data = engine.create_invoice(
        amount=amount,
        vat_rate=vat_rate,
        buyer=buyer,
        seller=seller,
        seller_tax_code=seller_tax_code,
        description=description,
        save=False,
    )
    jrn = engine.create_vas_journal(inv_data, save=True)

    if json_mode:
        typer.echo(json.dumps(jrn, indent=2, ensure_ascii=False))
        return

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


@ke_toan_app.command(name="status")
def ke_toan_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem trạng thái hệ thống kế toán và sổ sách phát sinh."""
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG KẾ TOÁN VAS[/]\n"
            f"Tổng số hóa đơn:       [bold]{data['total_invoices']}[/]\n"
            f"Tổng doanh thu:        [yellow]{data['total_revenue']:,.0f} đ[/]\n"
            f"Thuế GTGT đầu ra:      [green]{data['total_vat_output']:,.0f} đ[/]\n"
            f"Tổng tiền thanh toán:  [bold magenta]{data['total_gross_invoiced']:,.0f} đ[/]\n"
            f"Bút toán VAS ghi sổ:   [bold]{data['total_journal_entries']}[/]\n"
            f"Doanh số phát sinh:    [cyan]{data['total_ledger_turnover']:,.0f} đ[/]\n"
            f"Danh mục tài khoản:    [bold]{data['total_accounts']} tài khoản VAS[/]",
            title="[bold blue]Hệ Thống Kế Toán[/]",
            border_style="green",
        )
    )


@ke_toan_app.command(name="list")
def ke_toan_list(
    list_type: str = typer.Option("all", "--type", "-t", help="Lọc loại (invoice, journal, all)"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Liệt kê danh sách hóa đơn hoặc bút toán VAS đã ghi sổ."""
    from src.core.ke_toan_engine import KeToanEngine

    engine = KeToanEngine()

    if list_type == "journal":
        records = engine.list_journal_entries(limit=limit)
    elif list_type == "invoice":
        records = engine.list_invoices(limit=limit)
    else:
        records = {
            "invoices": engine.list_invoices(limit=limit),
            "journal_entries": engine.list_journal_entries(limit=limit),
        }

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    if list_type in ("invoice", "all"):
        invs = records if list_type == "invoice" else records["invoices"]
        table = Table(title="Danh Sách Hóa Đơn Điện Tử", show_header=True, header_style="bold magenta")
        table.add_column("Mã Hóa Đơn", style="dim", width=18)
        table.add_column("Người Mua", style="cyan", width=20)
        table.add_column("Tiền Hàng", justify="right", width=16)
        table.add_column("Thuế GTGT", justify="right", width=16)
        table.add_column("Tổng Tiền", justify="right", width=16)
        table.add_column("Ngày Lập", style="dim")

        for r in invs:
            table.add_row(
                r["invoice_id"],
                r["buyer_name"],
                f"{r['subtotal']:,.0f} đ",
                f"{r['vat_amount']:,.0f} đ",
                f"{r['total_amount']:,.0f} đ",
                r["invoice_date"],
            )
        console.print(table)


# ---------------------------------------------------------------------------
# Bảo hiểm xã hội VN (BHXH, BHYT, BHTN)
# ---------------------------------------------------------------------------

bhxh_app = typer.Typer(
    name="bhxh",
    help="Bảo hiểm xã hội VN — BHXH, BHYT, BHTN, hồ sơ D02-LT (NĐ 73/2024 & NĐ 74/2024)",
    no_args_is_help=False,
    add_completion=False,
    rich_markup_mode="rich",
)


@bhxh_app.callback(invoke_without_command=True)
def bhxh_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Hệ thống trích nộp Bảo hiểm Xã hội, BHYT, BHTN và kê khai D02-LT."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.bhxh_engine import BhxhEngine

    engine = BhxhEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    regs = status_data["statutory_regulations"]
    console.print(
        Panel(
            f"[bold green]Hệ Thống Bảo Hiểm Xã Hội Việt Nam (BHXH - BHYT - BHTN)[/]\n\n"
            f"  Căn cứ pháp lý:          [cyan]{regs['decree']}[/]\n"
            f"  Mức lương cơ sở:         [yellow]{regs['base_salary_vnd']:,.0f} đ/tháng[/]\n"
            f"  Mức trần đóng BHXH/BHYT: [magenta]{regs['ceiling_bhxh_bhyt_vnd']:,.0f} đ/tháng[/]\n"
            f"  Tỷ lệ Người lao động:    [bold]10.5%[/] (BHXH 8%, BHYT 1.5%, BHTN 1%)\n"
            f"  Tỷ lệ Doanh nghiệp:      [bold green]21.5%[/] (BHXH 17.5%, BHYT 3%, BHTN 1%)\n"
            f"  Tổng trích nộp bắt buộc: [bold red]32.0%[/]\n"
            f"  Nhân sự đăng ký:         [cyan]{status_data['total_employees']}[/] (Hoạt động: {status_data['active_employees']})\n"
            f"  Hồ sơ kê khai D02-LT:    [bold blue]{status_data['total_declarations']}[/]\n"
            f"  Tổng quỹ trích nộp:      [yellow]{status_data['total_contributions_simulated']:,.0f} đ[/]",
            title="[bold blue]BHXH & Lao Động Doanh Nghiệp VN[/]",
            border_style="green",
        )
    )

    table = Table(title="Lịch Sử Tính Đóng BHXH Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã Tính", style="dim", width=16)
    table.add_column("Lương Gốc", justify="right", width=14)
    table.add_column("NLĐ Đóng (10.5%)", justify="right", width=16)
    table.add_column("DN Đóng (21.5%)", justify="right", width=16)
    table.add_column("Tổng Trích Nộp", justify="right", width=16)
    table.add_column("Lương Thực Lĩnh", justify="right", width=16)

    for c in status_data.get("recent_calculations", []):
        table.add_row(
            c["calc_id"],
            f"{c['salary_gross']:,.0f} đ",
            f"{c['nl_total']:,.0f} đ",
            f"{c['dn_total']:,.0f} đ",
            f"{c['total_contribution']:,.0f} đ",
            f"{c['salary_gross'] - c['nl_total']:,.0f} đ",
        )
    console.print(table)


@bhxh_app.command(name="calc")
def bhxh_calc(
    salary: float = typer.Argument(..., help="Mức tiền lương đóng bảo hiểm (Gross)"),
    region: int = typer.Option(1, "--region", "-r", help="Vùng lương tối thiểu (1, 2, 3, 4)"),
    kpcd: bool = typer.Option(False, "--kpcd", help="Bao gồm kinh phí công đoàn 2%"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tính chi tiết tỷ lệ trích nộp BHXH, BHYT, BHTN cho NLĐ và Doanh nghiệp."""
    from src.core.bhxh_engine import BhxhEngine, format_vnd

    engine = BhxhEngine()
    res = engine.calculate_contribution(salary=salary, region=region, include_kpcd=kpcd)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    capped_str = " (Đã chạm mức trần 46.800.000 đ)" if res["is_capped"] else ""
    console.print(
        Panel(
            f"[bold]Mức lương tính bảo hiểm:[/] [yellow]{format_vnd(res['salary_gross'])}[/]{capped_str}\n"
            f"[bold]Vùng áp dụng:[/] Vùng {res['region']}\n"
            f"[bold]NLĐ trích nộp (10.5%):[/] [cyan]{format_vnd(res['employee']['total'])}[/]\n"
            f"[bold]DN trích nộp ({'23.5%' if kpcd else '21.5%'}):[/] [magenta]{format_vnd(res['employer']['total'])}[/]\n"
            f"[bold green]Tổng quỹ bảo hiểm nộp về CQ BHXH:[/] [bold green]{format_vnd(res['total_contribution'])}[/]\n"
            f"[bold blue]Lương thực lĩnh sau bảo hiểm:[/] [bold blue]{format_vnd(res['net_salary_estimated'])}[/]",
            title=f"[bold green]Chi Tiết Trích Nộp BHXH — {res['calc_id']}[/]",
            border_style="green",
        )
    )

    table = Table(title="Bảng Tỷ Lệ Trích Nộp Theo Quy Định", show_header=True, header_style="bold cyan")
    table.add_column("Khoản Trích Nộp", style="bold", width=22)
    table.add_column("NLĐ Đóng", justify="right", width=18)
    table.add_column("NSDLĐ Đóng", justify="right", width=18)
    table.add_column("Tổng Tỷ Lệ", justify="right", width=16)

    table.add_row("BHXH (Hưu trí / Ốm đau)", f"8.0% ({format_vnd(res['employee']['bhxh_8pct'])})", f"17.5% ({format_vnd(res['employer']['bhxh_17_5pct'])})", "25.5%")
    table.add_row("BHYT (Y tế)", f"1.5% ({format_vnd(res['employee']['bhyt_1_5pct'])})", f"3.0% ({format_vnd(res['employer']['bhyt_3pct'])})", "4.5%")
    table.add_row("BHTN (Thất nghiệp)", f"1.0% ({format_vnd(res['employee']['bhtn_1pct'])})", f"1.0% ({format_vnd(res['employer']['bhtn_1pct'])})", "2.0%")
    if kpcd:
        table.add_row("KPCĐ (Công đoàn)", "0.0%", f"2.0% ({format_vnd(res['employer']['kpcd_2pct'])})", "2.0%")
    table.add_row("[bold]TỔNG CỘNG[/]", f"[bold cyan]{format_vnd(res['employee']['total'])}[/]", f"[bold magenta]{format_vnd(res['employer']['total'])}[/]", f"[bold green]{format_vnd(res['total_contribution'])}[/]")
    console.print(table)


@bhxh_app.command(name="employees")
def bhxh_employees(
    status: str = typer.Option("all", "--status", "-s", help="Lọc theo trạng thái (active, all)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem danh sách nhân sự tham gia đóng BHXH trong doanh nghiệp."""
    from src.core.bhxh_engine import BhxhEngine, format_vnd

    engine = BhxhEngine()
    emps = engine.list_employees(status=status)

    if json_mode:
        typer.echo(json.dumps({"total": len(emps), "employees": emps}, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Danh Sách Nhân Sự Tham Gia BHXH", show_header=True, header_style="bold magenta")
    table.add_column("Mã NV", style="dim", width=12)
    table.add_column("Họ Và Tên", style="bold cyan", width=22)
    table.add_column("Mã Số BHXH", style="dim", width=14)
    table.add_column("Lương Đóng BHXH", justify="right", width=18)
    table.add_column("Vùng", justify="center", width=8)
    table.add_column("Phòng Ban", width=16)
    table.add_column("Trạng Thái", justify="center", width=12)

    for e in emps:
        table.add_row(
            e["employee_id"],
            e["full_name"],
            e["bhxh_code"],
            format_vnd(e["salary_insurance"]),
            str(e["region"]),
            e["department"],
            f"[green]{e['status']}[/]" if e["status"] == "active" else e["status"],
        )
    console.print(table)


@bhxh_app.command(name="declaration")
def bhxh_declaration(
    change_type: str = typer.Argument(..., help="Loại biến động: bao_tang | bao_giam | dieu_chinh_luong"),
    employee_id: str = typer.Argument(..., help="Mã nhân viên (e.g. EMP-001)"),
    month: str = typer.Option("", "--month", "-m", help="Tháng hiệu lực (MM/YYYY)"),
    new_salary: float = typer.Option(0.0, "--new-salary", help="Mức lương mới nếu điều chỉnh"),
    note: str = typer.Option("", "--note", help="Ghi chú hồ sơ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Lập hồ sơ điện tử Mẫu D02-LT (Báo tăng / Báo giảm / Điều chỉnh lương đóng BHXH)."""
    from src.core.bhxh_engine import BhxhEngine

    engine = BhxhEngine()
    res = engine.create_declaration_d02lt(
        change_type=change_type,
        employee_id=employee_id,
        effective_month=month,
        new_salary=new_salary,
        note=note,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    console.print(
        Panel(
            f"[bold green]Hồ Sơ Điện Tử Mẫu D02-LT Đã Khởi Tạo[/]\n\n"
            f"  Mã hồ sơ:       [bold]{res['declaration_id']}[/]\n"
            f"  Quy chuẩn:      {res['standard']}\n"
            f"  Nghiệp vụ:      [cyan]{res['change_type']}[/]\n"
            f"  Mã nhân viên:   [yellow]{res['employee_id']}[/] ({res['full_name']})\n"
            f"  Kỳ hiệu lực:    [magenta]{res['effective_month']}[/]\n"
            f"  Lương cũ:       {res['old_salary']:,.0f} đ\n"
            f"  Lương mới:      [bold green]{res['new_salary']:,.0f} đ[/]\n"
            f"  Trạng thái:     [bold blue]{res['status']}[/]\n"
            f"  Ghi chú:        {res['note']}",
            title="[bold blue]Hồ Sơ Kê Khai BHXH D02-LT[/]",
            border_style="green",
        )
    )


@bhxh_app.command(name="status")
def bhxh_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Kiểm tra trạng thái tuân thủ BHXH và các mốc quy định pháp lý."""
    from src.core.bhxh_engine import BhxhEngine

    engine = BhxhEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    regs = status_data["statutory_regulations"]
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG BHXH VIỆT NAM[/]\n\n"
            f"Trạng thái:             [bold green]{status_data['status'].upper()}[/]\n"
            f"Nghị định áp dụng:      [cyan]{regs['decree']}[/]\n"
            f"Mức lương cơ sở:        [yellow]{regs['base_salary_vnd']:,.0f} đ[/]\n"
            f"Trần đóng BHXH/BHYT:    [magenta]{regs['ceiling_bhxh_bhyt_vnd']:,.0f} đ[/]\n"
            f"Tổng nhân sự:           [bold]{status_data['total_employees']}[/] (Hoạt động: {status_data['active_employees']})\n"
            f"Số lượt tính đóng:      [cyan]{status_data['total_calculations']}[/]\n"
            f"Hồ sơ D02-LT đã lập:    [bold blue]{status_data['total_declarations']}[/]\n"
            f"Tổng quỹ bảo hiểm:      [bold green]{status_data['total_contributions_simulated']:,.0f} đ[/]",
            title="[bold blue]BHXH Telemetry[/]",
            border_style="green",
        )
    )


# ---------------------------------------------------------------------------
# VietQR / Napas 247 Instant Payments
# ---------------------------------------------------------------------------

vietqr_app = typer.Typer(
    name="vietqr",
    help="VietQR / Napas 247 — thanh toán chuyển khoản, tạo mã QR EMVCo, đối soát",
    add_completion=False,
)


@vietqr_app.callback(invoke_without_command=True)
def vietqr_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan VietQR dạng JSON"),
) -> None:
    """VietQR / Napas 247 — thanh toán chuyển khoản, tạo mã QR EMVCo, đối soát."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.vietqr_engine import VietQrEngine

    engine = VietQrEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    acc = status_data["default_account"]
    console.print(
        Panel(
            f"[bold green]CỔNG THANH TOÁN VIETQR & NAPAS 247 TỰ ĐỘNG[/]\n"
            f"  Trạng thái:            [bold green]{status_data['status'].upper()}[/]\n"
            f"  Cổng thanh toán:       [cyan]{status_data['gateway']}[/]\n"
            f"  Quy chuẩn áp dụng:     {', '.join(status_data['statutory_standards'])}\n"
            f"  Tài khoản mặc định:    [yellow]{acc['account_number']}[/] — [bold]{acc['bank']}[/] ({acc['account_holder']})\n"
            f"  Số mã QR đã tạo:       [bold]{status_data['total_qr_generated']}[/]\n"
            f"  Giao dịch đối soát:    [bold cyan]{status_data['total_transactions_recorded']}[/]\n"
            f"  Tổng tiền đã nhận:     [bold green]{status_data['total_volume_received_vnd']:,.0f} đ[/]\n"
            f"  Ngân hàng liên kết:    [bold]{status_data['supported_banks_count']} ngân hàng Napas 247[/]",
            title="[bold blue]Hệ Thống Thanh Toán VietQR[/]",
            border_style="green",
        )
    )

    table = Table(title="Giao Dịch Thanh Toán Gần Nhất", show_header=True, header_style="bold magenta")
    table.add_column("Mã GD", style="dim", width=14)
    table.add_column("Mã Ngân Hàng", style="cyan", width=16)
    table.add_column("Số Tiền", justify="right", width=16)
    table.add_column("Nội Dung Chuyển Khoản", width=26)
    table.add_column("Trạng Thái", justify="center", width=12)

    for tx in status_data.get("recent_transactions", []):
        table.add_row(
            tx["transaction_id"],
            tx["bank_tx_id"],
            f"{tx['amount_vnd']:,.0f} đ",
            tx["memo"],
            f"[green]{tx['status']}[/]",
        )

    console.print(table)


@vietqr_app.command(name="generate")
def vietqr_generate(
    amount: int = typer.Argument(0, help="Số tiền thanh toán (VND, 0 = động/người chuyển nhập)"),
    memo: str = typer.Option("", "--memo", "-m", help="Nội dung chuyển khoản (e.g. MK-INV-1001)"),
    bank: str = typer.Option("MB", "--bank", "-b", help="Mã ngân hàng (MB, VCB, CTG, BIDV, TCB, ACB, TPB)"),
    account: str = typer.Option("", "--account", "-a", help="Số tài khoản thụ hưởng"),
    name: str = typer.Option("", "--name", "-n", help="Tên chủ tài khoản thụ hưởng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu QR dạng JSON"),
) -> None:
    """Tạo mã thanh toán VietQR chuẩn EMVCo và QuickLink Napas 247."""
    from src.core.vietqr_engine import VietQrEngine

    engine = VietQrEngine()
    res = engine.generate_qr(
        bank=bank,
        account_number=account,
        account_name=name,
        amount_vnd=amount,
        memo=memo,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    amount_str = f"{res['amount_vnd']:,.0f} đ" if res["amount_vnd"] > 0 else "Người chuyển tự nhập số tiền"

    console.print(
        Panel(
            f"[bold green]MÃ THANH TOÁN VIETQR ĐÃ TẠO THÀNH CÔNG[/]\n\n"
            f"  Mã QR:          [bold]{res['qr_id']}[/]\n"
            f"  Ngân hàng:      [bold cyan]{res['bank_full']}[/] (BIN: {res['bank_bin']})\n"
            f"  Số tài khoản:   [bold yellow]{res['account_number']}[/]\n"
            f"  Chủ tài khoản:  [bold]{res['account_holder']}[/]\n"
            f"  Số tiền:        [bold magenta]{amount_str}[/]\n"
            f"  Nội dung:       [bold green]{res['memo'] or '(Không có)'}[/]\n\n"
            f"[bold cyan]QuickLink URL (Hiển thị ảnh QR):[/]\n{res['quicklink_url']}\n\n"
            f"[bold dim]Chuỗi EMVCo Payload:[/] [dim]{res['emvco_payload'][:60]}...[/dim]",
            title="[bold blue]VietQR Napas 247 Instant Transfer[/]",
            border_style="green",
        )
    )


@vietqr_app.command(name="banks")
def vietqr_banks(
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách ngân hàng dạng JSON"),
) -> None:
    """Tra cứu danh sách các ngân hàng liên kết Napas 247 và mã BIN."""
    from src.core.vietqr_engine import VietQrEngine

    engine = VietQrEngine()
    banks = engine.list_banks()

    if json_mode:
        typer.echo(json.dumps({"total": len(banks), "banks": banks}, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Danh Sách Ngân Hàng Napas 247 Hỗ Trợ VietQR", show_header=True, header_style="bold magenta")
    table.add_column("Mã BIN", style="dim", width=10)
    table.add_column("Ký Hiệu", style="bold cyan", width=10)
    table.add_column("Tên Ngân Hàng", width=45)

    for b in banks:
        table.add_row(b["bin"], b["short_name"], b["full_name"])

    console.print(table)


@vietqr_app.command(name="transactions")
def vietqr_transactions(
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng giao dịch hiển thị"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất danh sách giao dịch dạng JSON"),
) -> None:
    """Xem lịch sử các giao dịch chuyển khoản ngân hàng đã đối soát."""
    from src.core.vietqr_engine import VietQrEngine

    engine = VietQrEngine()
    txs = engine.list_transactions(limit=limit)

    if json_mode:
        typer.echo(json.dumps({"total": len(txs), "transactions": txs}, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Lịch Sử Giao Dịch Chuyển Khoản Ngân Hàng", show_header=True, header_style="bold cyan")
    table.add_column("Mã GD", style="dim", width=14)
    table.add_column("Mã GD Ngân Hàng", style="bold", width=18)
    table.add_column("Số Tiền", justify="right", width=16)
    table.add_column("Nội Dung Chuyển Khoản", width=24)
    table.add_column("Trạng Thái", justify="center", width=12)
    table.add_column("Thời Gian", style="dim", width=22)

    for tx in txs:
        table.add_row(
            tx["transaction_id"],
            tx["bank_tx_id"],
            f"{tx['amount_vnd']:,.0f} đ",
            tx["memo"],
            f"[green]{tx['status']}[/]",
            tx["received_at"][:19],
        )

    console.print(table)


@vietqr_app.command(name="record")
def vietqr_record(
    tx_id: str = typer.Argument(..., help="Mã giao dịch ngân hàng (e.g. FT26090123)"),
    amount: int = typer.Argument(..., help="Số tiền thanh toán đã nhận (VND)"),
    memo: str = typer.Option("", "--memo", "-m", help="Nội dung giao dịch"),
    order_id: str = typer.Option("", "--order", help="Mã đơn hàng liên kết"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả ghi nhận dạng JSON"),
) -> None:
    """Ghi nhận đối soát giao dịch chuyển khoản ngân hàng (idempotent)."""
    from src.core.vietqr_engine import VietQrEngine

    engine = VietQrEngine()
    res = engine.record_transaction(
        bank_tx_id=tx_id,
        amount_vnd=amount,
        memo=memo,
        matched_order_id=order_id or None,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    dup_str = " [yellow](Giao dịch đã tồn tại - Bỏ qua trùng lặp)[/]" if res.get("is_duplicate") else ""
    console.print(
        Panel(
            f"[bold green]GHI NHẬN ĐỐI SOÁT GIAO DỊCH THÀNH CÔNG[/]{dup_str}\n\n"
            f"  Mã hệ thống:      [bold]{res['transaction_id']}[/]\n"
            f"  Mã GD ngân hàng:  [bold cyan]{res['bank_tx_id']}[/]\n"
            f"  Số tiền nhận:     [bold green]{res['amount_vnd']:,.0f} đ[/]\n"
            f"  Nội dung:         [yellow]{res['memo']}[/]\n"
            f"  Đơn hàng:         {res.get('matched_order_id') or '(Không có)'}\n"
            f"  Trạng thái:       [bold green]{res['status'].upper()}[/]",
            title="[bold blue]Đối Soát Giao Dịch VietQR[/]",
            border_style="green",
        )
    )


@vietqr_app.command(name="status")
def vietqr_status(
    json_mode: bool = typer.Option(False, "--json", help="Xuất trạng thái dạng JSON"),
) -> None:
    """Kiểm tra trạng thái hệ thống VietQR và số liệu thanh toán."""
    from src.core.vietqr_engine import VietQrEngine

    engine = VietQrEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    acc = status_data["default_account"]
    console.print(
        Panel(
            f"[bold green]TRẠNG THÁI HỆ THỐNG VIETQR / NAPAS 247[/]\n\n"
            f"Trạng thái:             [bold green]{status_data['status'].upper()}[/]\n"
            f"Cổng xử lý:             {status_data['gateway']}\n"
            f"Tài khoản thụ hưởng:    {acc['account_number']} ({acc['bank']})\n"
            f"Số mã QR đã tạo:        [bold]{status_data['total_qr_generated']}[/]\n"
            f"Giao dịch đối soát:     [cyan]{status_data['total_transactions_recorded']}[/]\n"
            f"Tổng dòng tiền nhận:    [bold green]{status_data['total_volume_received_vnd']:,.0f} đ[/]\n"
            f"Ngân hàng hỗ trợ:       {status_data['supported_banks_count']} ngân hàng",
            title="[bold blue]VietQR Gateway Telemetry[/]",
            border_style="green",
        )
    )
