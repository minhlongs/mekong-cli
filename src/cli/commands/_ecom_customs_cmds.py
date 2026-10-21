# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phase 175: Cross-Border E-Commerce Customs Management & Platform Withholding CLI commands."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.ecom_inspect_engine import (
    CrossBorderEcomEngine,
    EcomOrderItem,
    EcomPlatform,
)

console = Console()

ecom_app = typer.Typer(
    name="ecom",
    help="ECOM — Cross-Border E-Commerce Customs Management & Platform Withholding (Phase 175)",
    no_args_is_help=False,
)


@ecom_app.callback(invoke_without_command=True)
def ecom_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Quản lý Hải quan TMĐT Xuyên biên giới & Khấu trừ thuế tại nguồn."""
    if ctx.invoked_subcommand is not None:
        return
    if json_mode:
        data = {
            "suite": "Mekong Cross-Border E-Commerce Customs Suite (Phase 175)",
            "statutory_basis": [
                "Draft Decree on Customs Management for Cross-Border E-Commerce",
                "Repeal of Decision 78/2010/QD-TTg (VAT exemption elimination)",
                "Decree 134/2016/ND-CP Article 29 (1,000,000 VND Duty De Minimis)",
                "Circular 80/2021/TT-BTC & Decree 91/2022/ND-CP (Platform Withholding)",
            ],
            "commands": ["tax", "split-check", "platform-info"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Cross-Border E-Commerce Customs Suite (Phase 175)[/bold cyan]\n"
            "[dim]Khấu trừ thuế tại sàn TMĐT, kiểm soát định giá và chống gian lận chia nhỏ đơn hàng.[/dim]\n\n"
            "• [bold green]tax[/bold green]          : Tính trị giá hải quan, miễn thuế NK <1M, thuế GTGT bỏ QĐ 78 & nộp thay.\n"
            "• [bold yellow]split-check[/bold yellow]  : Phát hiện rủi ro chia nhỏ đơn hàng (anti-structuring) trong 72h.\n"
            "• [bold blue]platform-info[/bold blue]: Nghĩa vụ khấu trừ của các sàn (Shopee, Lazada, TikTok, Temu, Taobao).",
            title="📦 [bold]TMĐT XUYÊN BIÊN GIỚI[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@ecom_app.command("tax")
def ecom_tax(
    order_id: str = typer.Argument(..., help="Mã đơn hàng TMĐT"),
    price_vnd: float = typer.Argument(..., help="Đơn giá sản phẩm (VND)"),
    qty: int = typer.Option(1, "--qty", "-q", help="Số lượng"),
    freight_vnd: float = typer.Option(0.0, "--freight", "-f", help="Cước vận chuyển quốc tế (VND)"),
    insurance_vnd: float = typer.Option(0.0, "--insurance", "-i", help="Bảo hiểm quốc tế (VND)"),
    discount_vnd: float = typer.Option(0.0, "--discount", "-d", help="Chiết khấu trực tiếp của người bán (VND)"),
    voucher_vnd: float = typer.Option(0.0, "--voucher", "-v", help="Trợ giá voucher từ sàn (Không được trừ)"),
    duty_rate: float = typer.Option(10.0, "--duty-rate", help="Thuế suất thuế nhập khẩu (%)"),
    sct_rate: float = typer.Option(0.0, "--sct-rate", help="Thuế suất Tiêu thụ đặc biệt (%)"),
    vat_rate: float = typer.Option(10.0, "--vat-rate", help="Thuế suất GTGT (%)"),
    platform: str = typer.Option("SHOPEE", "--platform", "-p", help="Sàn TMĐT (SHOPEE, LAZADA, TIKTOK_SHOP, AMAZON, TEMU, TAOBAO)"),
    buyer_id: str = typer.Option("BUYER-VN-01", "--buyer", "-b", help="Mã định danh người mua"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính thuế nhập khẩu, GTGT và nghĩa vụ khấu trừ của sàn TMĐT."""
    plat_enum = EcomPlatform.__members__.get(platform.upper(), EcomPlatform.OTHER)
    item = EcomOrderItem(
        item_id=f"ITEM-{order_id}",
        product_name=f"Product for {order_id}",
        hs_code="9503.00.00",
        unit_price_vnd=price_vnd,
        quantity=qty,
        seller_id="SELLER-INTL-01",
        platform=plat_enum,
        direct_seller_discount_vnd=discount_vnd,
        platform_subsidy_voucher_vnd=voucher_vnd,
        import_duty_rate=duty_rate,
        sct_rate=sct_rate,
        vat_rate=vat_rate,
    )
    result = CrossBorderEcomEngine.calculate_customs_tax(
        order_id=order_id,
        platform=plat_enum,
        buyer_id=buyer_id,
        items=[item],
        intl_freight_vnd=freight_vnd,
        intl_insurance_vnd=insurance_vnd,
    )
    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"📦 Khai Thuế TMĐT — Đơn hàng: {order_id}", box=box.ROUNDED)
    table.add_column("Chỉ số / Khoản mục", style="cyan")
    table.add_column("Giá trị (VND)", justify="right", style="bold")
    table.add_column("Ghi chú luật định", style="dim")
    table.add_row("Tổng tiền hàng khai báo", f"{result.declared_items_value_vnd:,.0f} đ", "Giá mua sản phẩm")
    table.add_row("Cước & Bảo hiểm quốc tế", f"{result.intl_freight_insurance_vnd:,.0f} đ", "Khoản cộng trị giá tính thuế")
    table.add_row("Chiết khấu người bán (Trừ)", f"-{result.direct_discount_allowed_vnd:,.0f} đ", "Được khấu trừ hợp lệ")
    if result.platform_voucher_disallowed_vnd > 0:
        table.add_row("Voucher trợ giá sàn", f"{result.platform_voucher_disallowed_vnd:,.0f} đ", "Không được khấu trừ")
    table.add_row("Trị giá Hải quan (Vc)", f"{result.customs_value_vnd:,.0f} đ", "Căn cứ tính thuế")
    duty_note = "[green]Miễn thuế (<= 1M)[/green]" if result.is_de_minimis_duty_free else f"Thuế suất {duty_rate}%"
    table.add_row("Thuế Nhập khẩu", f"{result.import_duty_vnd:,.0f} đ", duty_note)
    if result.sct_vnd > 0:
        table.add_row("Thuế TTĐB", f"{result.sct_vnd:,.0f} đ", f"Thuế suất {sct_rate}%")
    table.add_row("Thuế GTGT", f"{result.vat_vnd:,.0f} đ", f"Thuế suất {vat_rate}% (Bỏ QĐ 78, thu từ 0đ)")
    table.add_row("Tổng nghĩa vụ thuế", f"{result.total_tax_liability_vnd:,.0f} đ", "Tổng số nộp NSNN")
    table.add_row("Sàn khấu trừ nộp thay", f"[bold yellow]{result.platform_withholding_payable_vnd:,.0f} đ[/bold yellow]", f"Trách nhiệm sàn {plat_enum.value} (TT 80/2021)")
    console.print(table)


@ecom_app.command("split-check")
def ecom_split_check(
    buyer_id: str = typer.Argument(..., help="Mã định danh người mua"),
    values: str = typer.Option(..., "--values", "-v", help="Danh sách trị giá các đơn hàng (VND, phân tách dấu phẩy)"),
    phone: str = typer.Option("0901234567", "--phone", "-p", help="Số điện thoại nhận hàng"),
    address: str = typer.Option("123 Le Loi, Q1, HCM", "--address", "-a", help="Địa chỉ giao hàng"),
    hours: float = typer.Option(72.0, "--hours", "-h", help="Khung thời gian quét (giờ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra dấu hiệu chia nhỏ đơn hàng (anti-structuring) dưới 1,000,000 VND."""
    val_list = [float(x.strip()) for x in values.split(",") if x.strip()]
    orders = [{"customs_value_vnd": v, "phone": phone, "address": address} for v in val_list]
    result = CrossBorderEcomEngine.evaluate_split_consignment_risk(
        buyer_id=buyer_id,
        orders=orders,
        window_hours=hours,
    )
    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    panel_style = "red" if result.is_split_fraud_detected else ("yellow" if result.recommended_channel == "YELLOW" else "green")
    content = (
        f"• Người mua: [bold]{result.buyer_id}[/bold] | SĐT: {result.recipient_phone}\n"
        f"• Số lượng đơn hàng: [bold]{result.order_count}[/bold] đơn trong {result.window_hours:.0f} giờ\n"
        f"• Tổng trị giá cộng dồn: [bold]{result.total_aggregate_value_vnd:,.0f} đ[/bold]\n"
        f"• Điểm trùng khớp thực thể (Sim): {result.similarity_score:.2f}\n"
        f"• Điểm rủi ro chia nhỏ (R_split): [bold]{result.risk_score:.2f}[/bold]\n"
        f"• Phân luồng đề xuất: [bold]{result.recommended_channel}[/bold]\n\n"
        f"[bold]Kết luận & Hành động:[/bold]\n{result.recommended_action}"
    )
    console.print(
        Panel(
            content,
            title=f"🛡️ Radar Chống Gian Lận Chia Nhỏ Đơn Hàng ({'PHÁT HIỆN GIAN LẬN' if result.is_split_fraud_detected else 'HỢP LỆ'})",
            border_style=panel_style,
            box=box.ROUNDED,
        )
    )
