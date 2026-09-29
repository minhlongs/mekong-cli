# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Cross-Border E-Commerce, Platform Tax Invoicing & Marketplace Compliance (Phase 61)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
ecom_app = typer.Typer(
    name="ecom",
    help="E-Commerce — Vietnamese Cross-Border E-Commerce, Overseas Supplier Tax & Marketplace Compliance",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def _format_usd(amount: float) -> str:
    return f"${amount:,.2f} USD"


@ecom_app.callback(invoke_without_command=True)
def ecom_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Thương mại Điện tử, Thuế Nhà thầu Nước ngoài (NCCNN) & Sàn Giao dịch TMĐT."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ THƯƠNG MẠI ĐIỆN TỬ & NỀN TẢNG SỐ XUYÊN BIÊN GIỚI[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Sàn & Website TMĐT:  [bold]{metrics['registered_platforms']} nền tảng[/]\n"
            f"  Kê khai thuế NCCNN:  [bold cyan]{metrics['fct_tax_declarations_count']} kỳ[/] (Doanh thu: [bold]{_format_vnd(metrics['total_fct_declared_revenue_vnd'])}[/] | Thuế FCT: [bold green]{_format_vnd(metrics['total_fct_tax_collected_vnd'])}[/])\n"
            f"  Đơn hàng đã quyết toán:[bold]{metrics['total_marketplace_orders_settled']} đơn[/] (GMV: [bold yellow]{_format_vnd(metrics['total_marketplace_gmv_vnd'])}[/] | Phí sàn: [bold green]{_format_vnd(metrics['total_platform_fees_earned_vnd'])}[/])\n"
            f"  Bưu kiện xuyên biên giới: [bold]{metrics['total_cross_border_parcels']} bưu kiện[/] (Miễn thuế $\\le 1$ tr: [bold green]{metrics['exempt_parcels_count']}[/] | Thuế NK: [bold red]{_format_vnd(metrics['total_parcel_import_duty_vnd'])}[/])",
            title="[bold blue]Vietnam E-Commerce & Cross-Border Digital Platform Hub[/]",
            border_style="green",
        )
    )


@ecom_app.command("fct")
def fct_cmd(
    supplier: str = typer.Argument(..., help="Tên nhà cung cấp nước ngoài (VD: Google Asia Pacific, Meta Ireland, Netflix, TikTok Pte)"),
    etax_code: str = typer.Argument(..., help="Mã số thuế NCCNN tại Việt Nam (10 hoặc 13 số được cấp qua etaxvn.gdt.gov.vn)"),
    category: str = typer.Argument(..., help="Nhóm dịch vụ (DIGITAL_SERVICES, ONLINE_ADVERTISING, CLOUD_SAAS, STREAMING_MEDIA)"),
    revenue_usd: float = typer.Option(0.0, "--usd", help="Doanh thu dịch vụ kỹ thuật số bằng USD"),
    revenue_vnd: float = typer.Option(0.0, "--vnd", help="Doanh thu dịch vụ kỹ thuật số bằng VND"),
    quarter: str = typer.Option("Q1-2026", "--quarter", "-q", help="Kỳ tính thuế (VD: Q1-2026)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính thuế Nhà thầu Nước ngoài (FCT - VAT & CIT) cho dịch vụ kỹ thuật số xuyên biên giới."""
    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    result = engine.calculate_foreign_contractor_tax(
        foreign_supplier_name=supplier,
        supplier_etax_code=etax_code,
        service_category=category,
        revenue_usd=revenue_usd,
        revenue_vnd=revenue_vnd,
        quarter=quarter,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    s = result["foreign_supplier"]
    f = result["financials"]
    t = result["tax_breakdown_vnd"]

    console.print(
        Panel(
            f"[bold green]TỜ KHAI THUẾ NHÀ THẦU NƯỚC NGOÀI (NCCNN) — DỊCH VỤ SỐ XUYÊN BIÊN GIỚI[/]\n\n"
            f"  Mã hồ sơ kê khai:    [bold]{result['declaration_id']}[/]\n"
            f"  Nhà cung cấp:        [bold yellow]{s['name']}[/] (Mã thuế: [bold cyan]{s['etax_code']}[/])\n"
            f"  Cổng kê khai:        [bold]{s['portal']}[/]\n"
            f"  Nhóm dịch vụ:        [bold]{result['service_classification']['category']}[/] (Kỳ: [bold]{f['reporting_quarter']}[/])\n\n"
            f"  [bold]Doanh thu tính thuế:[/] [bold]{_format_vnd(f['declared_revenue_vnd'])}[/] ({_format_usd(f['equivalent_revenue_usd'])})\n"
            f"  ├─ Thuế GTGT ({t['vat_rate_pct']}%):      [bold cyan]{_format_vnd(t['vat_amount_vnd'])}[/]\n"
            f"  ├─ Thuế TNDN ({t['cit_rate_pct']}%):      [bold cyan]{_format_vnd(t['cit_amount_vnd'])}[/]\n"
            f"  └─ [bold red]Tổng nghĩa vụ FCT:[/]   [bold red]{_format_vnd(t['total_fct_liability_vnd'])}[/] (Tỷ lệ thực: {t['effective_tax_rate_pct']}%)",
            title=f"[bold blue]FCT Tax Assessment — {s['name']}[/]",
            border_style="green",
        )
    )


@ecom_app.command("audit")
def audit_cmd(
    name: str = typer.Argument(..., help="Tên sàn hoặc website thương mại điện tử (VD: Tiki, Sendo, BachHoaXanh)"),
    domain: str = typer.Argument(..., help="Tên miền website/ứng dụng (VD: https://tiki.vn)"),
    platform_type: str = typer.Option("MARKETPLACE", "--type", "-t", help="Loại nền tảng (SALES_WEBSITE, MARKETPLACE, SOCIAL_COMMERCE, PROMOTION_APP)"),
    tax_id: str = typer.Option("0109999999", "--tax-id", help="Mã số thuế doanh nghiệp thiết lập"),
    regulations: bool = typer.Option(True, "--regulations/--no-regulations", help="Có quy chế hoạt động được duyệt"),
    dispute: bool = typer.Option(True, "--dispute/--no-dispute", help="Có cơ chế tiếp nhận & giải quyết khiếu nại"),
    kyc: bool = typer.Option(True, "--kyc/--no-kyc", help="Có quy trình định danh người bán (KYC)"),
    retention: bool = typer.Option(True, "--retention/--no-retention", help="Lưu trữ lịch sử giao dịch tối thiểu 3 năm"),
    tax_reporting: bool = typer.Option(True, "--tax-reporting/--no-tax-reporting", help="Có module cung cấp thông tin cho Tổng cục Thuế"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện cấp phép và tuân thủ pháp luật sàn/website TMĐT theo Nghị định 52/2013 & 85/2021."""
    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    result = engine.audit_platform_compliance(
        platform_name=name,
        domain_url=domain,
        platform_type=platform_type,
        enterprise_tax_id=tax_id,
        has_operating_regulations=regulations,
        has_dispute_mechanism=dispute,
        has_seller_kyc=kyc,
        has_data_retention_3yr=retention,
        has_tax_reporting_system=tax_reporting,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    p = result["platform_profile"]
    proc = result["licensing_procedure"]
    e = result["compliance_evaluation"]

    status_color = "green" if e["compliance_status"] == "COMPLIANT_APPROVED" else ("yellow" if e["compliance_status"] == "CONDITIONAL_APPROVAL" else "red")

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ THẨM ĐỊNH TUÂN THỦ NỀN TẢNG THƯƠNG MẠI ĐIỆN TỬ[/]\n\n"
            f"  Tên nền tảng:        [bold yellow]{p['platform_name']}[/] ({p['domain_url']})\n"
            f"  Mô hình TMĐT:        [bold]{p['type_description']}[/] (Mã: [bold]{p['platform_type']}[/])\n"
            f"  Thủ tục hành chính:  [bold cyan]{proc['statutory_procedure']}[/] tại [bold]{proc['competent_authority']}[/] ({proc['online_portal']})\n"
            f"  Cung cấp dữ liệu TCT:[bold]{'Bắt buộc định kỳ hàng quý' if proc['quarterly_tax_reporting_required'] else 'Không bắt buộc'}[/]\n\n"
            f"  Điểm tuân thủ:       [bold {status_color}]{e['compliance_score']}/100[/]\n"
            f"  Trạng thái:          [bold {status_color}]{e['compliance_status']}[/]\n"
            f"  Tồn tại ({len(e['identified_gaps'])}):     {', '.join(e['identified_gaps']) if e['identified_gaps'] else '[green]Đạt 100% tiêu chí[/]'}",
            title=f"[bold blue]E-Commerce Licensing Audit — {p['platform_name']}[/]",
            border_style=status_color,
        )
    )


@ecom_app.command("order")
def order_cmd(
    order_code: str = typer.Argument(..., help="Mã đơn hàng giao dịch sàn (VD: 240929-SHOPEE-9988)"),
    platform: str = typer.Argument(..., help="Mã sàn TMĐT (VD: SHOPEE_VN, LAZADA_VN, TIKTOK_SHOP)"),
    seller: str = typer.Argument(..., help="Mã định danh người bán / Shop ID"),
    buyer: str = typer.Argument(..., help="Mã định danh người mua / User ID"),
    gmv: float = typer.Argument(..., help="Tổng giá trị hàng hóa gốc (Gross GMV VND)"),
    commission: float = typer.Option(6.0, "--commission", "-c", help="Tỷ lệ hoa hồng sàn (Take-rate %)"),
    payment_fee: float = typer.Option(2.5, "--pay-fee", help="Tỷ lệ phí xử lý thanh toán (%)"),
    shop_voucher: float = typer.Option(0.0, "--shop-voucher", help="Giảm giá voucher của người bán (VND)"),
    platform_voucher: float = typer.Option(0.0, "--plat-voucher", help="Trợ giá voucher của sàn (VND)"),
    shipping: float = typer.Option(30000.0, "--shipping", help="Phí vận chuyển (VND)"),
    vat_rate: int = typer.Option(10, "--vat", help="Thuế suất GTGT hóa đơn (0, 5, 8, 10%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Quyết toán tài chính đơn hàng sàn TMĐT, tính thực nhận của shop & xuất hóa đơn điện tử."""
    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    result = engine.process_marketplace_order_settlement(
        order_code=order_code,
        platform_id=platform,
        seller_id=seller,
        buyer_id=buyer,
        gmv_gross_vnd=gmv,
        platform_commission_pct=commission,
        payment_fee_pct=payment_fee,
        shop_voucher_vnd=shop_voucher,
        platform_voucher_vnd=platform_voucher,
        shipping_fee_vnd=shipping,
        vat_rate_pct=vat_rate,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    f = result["financial_settlement_vnd"]
    inv = result["electronic_invoice"]

    console.print(
        Panel(
            f"[bold green]QUYẾT TOÁN ĐƠN HÀNG SÀN TMĐT & HÓA ĐƠN ĐIỆN TỬ[/]\n\n"
            f"  Mã đơn hàng:         [bold yellow]{result['order_code']}[/] (ID: {result['order_id']})\n"
            f"  Sàn giao dịch:       [bold]{result['parties']['platform_id']}[/] | Shop: [bold]{result['parties']['seller_id']}[/]\n\n"
            f"  [bold]Dòng tiền quyết toán:[/\n"
            f"  ├─ Giá trị hàng hóa (GMV):   [bold]{_format_vnd(f['gmv_gross_goods_vnd'])}[/]\n"
            f"  ├─ Phí vận chuyển:           [bold]{_format_vnd(f['shipping_fee_vnd'])}[/]\n"
            f"  ├─ Người mua thanh toán:     [bold green]{_format_vnd(f['buyer_total_payment_vnd'])}[/]\n"
            f"  ├─ Hoa hồng sàn ({commission}%):       [bold red]-{_format_vnd(f['platform_commission_fee_vnd'])}[/]\n"
            f"  ├─ Phí thanh toán ({payment_fee}%):      [bold red]-{_format_vnd(f['payment_gateway_fee_vnd'])}[/]\n"
            f"  └─ [bold green]Người bán thực nhận:[/]   [bold green]{_format_vnd(f['seller_net_payout_vnd'])}[/]\n\n"
            f"  [bold]Hóa đơn điện tử (NĐ 123/2020):[/]\n"
            f"  Số HĐ: [bold cyan]{inv['invoice_number']}[/] (Trước thuế: {_format_vnd(inv['pre_tax_amount_vnd'])}, Thuế {inv['vat_rate_pct']}%: {_format_vnd(inv['vat_amount_vnd'])})",
            title=f"[bold blue]Marketplace Settlement — {result['order_code']}[/]",
            border_style="green",
        )
    )


@ecom_app.command("parcel")
def parcel_cmd(
    tracking_no: str = typer.Argument(..., help="Mã vận đơn chuyển phát nhanh quốc tế (VD: VN123456789HK, SPX123456)"),
    country: str = typer.Argument(..., help="Quốc gia gửi hàng (VD: China, Korea, Japan, US)"),
    consignee: str = typer.Argument(..., help="Tên người nhận tại Việt Nam"),
    item: str = typer.Argument(..., help="Mô tả hàng hóa trong bưu kiện (VD: Quần áo, Tai nghe không dây, Linh kiện)"),
    value_usd: float = typer.Option(0.0, "--usd", help="Trị giá hải quan bưu kiện bằng USD"),
    value_vnd: float = typer.Option(0.0, "--vnd", help="Trị giá hải quan bưu kiện bằng VND"),
    duty_pct: float = typer.Option(10.0, "--duty", help="Thuế suất thuế nhập khẩu (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định nghĩa vụ thuế bưu kiện chuyển phát nhanh TMĐT xuyên biên giới (ngưỡng miễn thuế $\\le 1$ tr)."""
    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    result = engine.evaluate_cross_border_parcel(
        tracking_no=tracking_no,
        shipper_country=country,
        consignee_name=consignee,
        item_description=item,
        customs_value_usd=value_usd,
        customs_value_vnd=value_vnd,
        import_duty_pct=duty_pct,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    s = result["shipment_profile"]
    v = result["valuation_and_taxation"]

    status_color = "green" if v["is_tax_exempt"] else "yellow"

    console.print(
        Panel(
            f"[bold green]KẾT QUẢ PHÂN LUỒNG THUẾ BƯU KIỆN TMĐT XUYÊN BIÊN GIỚI[/]\n\n"
            f"  Mã vận đơn:          [bold yellow]{result['tracking_no']}[/]\n"
            f"  Quốc gia xuất xứ:    [bold]{s['shipper_country']}[/] ➔ Người nhận: [bold]{s['consignee_name']}[/]\n"
            f"  Mô tả kiện hàng:     [bold]{s['item_description']}[/]\n\n"
            f"  Trị giá hải quan:    [bold]{_format_vnd(v['customs_value_vnd'])}[/] ({_format_usd(v['customs_value_usd'])})\n"
            f"  Miễn thuế (<= 1 tr):  [bold {status_color}]{'ĐƯỢC MIỄN THUẾ' if v['is_tax_exempt'] else 'PHẢI NỘP THUẾ'}[/]\n"
            f"  ├─ Thuế Nhập khẩu:   [bold]{_format_vnd(v['import_duty_vnd'])}[/]\n"
            f"  ├─ Thuế GTGT (10%):  [bold]{_format_vnd(v['import_vat_vnd'])}[/]\n"
            f"  └─ [bold]Tổng thuế phải nộp:[/] [bold {status_color}]{_format_vnd(v['total_tax_payable_vnd'])}[/]\n\n"
            f"  Trạng thái thông quan: [bold {status_color}]{v['clearance_status']}[/]",
            title=f"[bold blue]Cross-Border Express Parcel — {result['tracking_no']}[/]",
            border_style=status_color,
        )
    )


@ecom_app.command("list")
def list_cmd(
    item_type: str = typer.Option("platforms", "--type", "-t", help="Loại bản ghi: 'platforms', 'fct', 'orders', 'parcels'"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục sàn TMĐT, tờ khai thuế FCT, đơn hàng hoặc bưu kiện xuyên biên giới."""
    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    clean_type = item_type.lower().strip()

    if clean_type in ("fct", "tax", "declarations"):
        records = engine.list_fct_declarations(limit=limit)
        title = "Tờ khai thuế Nhà thầu Nước ngoài (FCT)"
        payload = {"ok": True, "type": "fct", "total": len(records), "declarations": list(records)}
    elif clean_type in ("order", "orders", "settlements"):
        records = engine.list_marketplace_orders(limit=limit)
        title = "Đơn hàng Sàn Thương mại Điện tử"
        payload = {"ok": True, "type": "orders", "total": len(records), "orders": list(records)}
    elif clean_type in ("parcel", "parcels", "express"):
        records = engine.list_cross_border_parcels(limit=limit)
        title = "Bưu kiện Chuyển phát nhanh Xuyên biên giới"
        payload = {"ok": True, "type": "parcels", "total": len(records), "parcels": list(records)}
    else:
        records = engine.list_platform_registrations(limit=limit)
        title = "Nền tảng Sàn & Website TMĐT Đăng ký"
        payload = {"ok": True, "type": "platforms", "total": len(records), "platforms": list(records)}

    if json_mode:
        typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục {title} ({len(records)} bản ghi)")
    if clean_type in ("fct", "tax", "declarations"):
        table.add_column("Mã hồ sơ", style="cyan")
        table.add_column("Nhà cung cấp", style="bold")
        table.add_column("Dịch vụ", style="yellow")
        table.add_column("Doanh thu", style="green")
        table.add_column("Thuế FCT", style="red")
        table.add_column("Kỳ", style="magenta")
        for r in records:
            table.add_row(
                r.get("declaration_id", ""),
                r.get("foreign_supplier_name", ""),
                r.get("service_category", ""),
                _format_vnd(r.get("revenue_vnd", 0)),
                _format_vnd(r.get("total_fct_vnd", 0)),
                r.get("quarter", ""),
            )
    elif clean_type in ("order", "orders", "settlements"):
        table.add_column("Mã đơn hàng", style="cyan")
        table.add_column("Sàn", style="bold")
        table.add_column("Shop", style="yellow")
        table.add_column("GMV", style="green")
        table.add_column("Phí sàn", style="red")
        table.add_column("Shop thực nhận", style="bold green")
        for r in records:
            table.add_row(
                r.get("order_code", ""),
                r.get("platform_id", ""),
                r.get("seller_id", ""),
                _format_vnd(r.get("gmv_gross_vnd", 0)),
                _format_vnd(r.get("platform_fee_vnd", 0)),
                _format_vnd(r.get("seller_payout_vnd", 0)),
            )
    else:
        table.add_column("Mã ĐK", style="cyan")
        table.add_column("Tên nền tảng", style="bold")
        table.add_column("Loại hình", style="yellow")
        table.add_column("MST", style="magenta")
        table.add_column("Điểm", style="green")
        table.add_column("Trạng thái", style="blue")
        for r in records:
            table.add_row(
                r.get("registration_id", ""),
                r.get("platform_name", ""),
                r.get("platform_type", ""),
                r.get("enterprise_tax_id", ""),
                str(r.get("compliance_score", 0)),
                r.get("status", ""),
            )

    console.print(table)


@ecom_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số điều hành TMĐT và nghĩa vụ thuế số xuyên biên giới."""
    from src.core.ecommerce_engine import EcommerceEngine

    engine = EcommerceEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]CHỈ SỐ ĐIỀU HÀNH THƯƠNG MẠI ĐIỆN TỬ VIỆT NAM (E-COMMERCE)[/]\n\n"
            f"  Sàn & Website đã đăng ký:       [bold]{m['registered_platforms']}[/]\n"
            f"  Số kỳ kê khai thuế NCCNN:       [bold cyan]{m['fct_tax_declarations_count']}[/]\n"
            f"  Tổng doanh thu NCCNN kê khai:   [bold green]{_format_vnd(m['total_fct_declared_revenue_vnd'])}[/]\n"
            f"  Tổng thuế FCT đã thu:           [bold red]{_format_vnd(m['total_fct_tax_collected_vnd'])}[/]\n"
            f"  Đơn hàng sàn TMĐT đã quyết toán:[bold]{m['total_marketplace_orders_settled']}[/]\n"
            f"  Tổng GMV giao dịch qua sàn:     [bold yellow]{_format_vnd(m['total_marketplace_gmv_vnd'])}[/]\n"
            f"  Tổng doanh thu phí sàn:         [bold green]{_format_vnd(m['total_platform_fees_earned_vnd'])}[/]\n"
            f"  Bưu kiện chuyển phát nhanh:     [bold]{m['total_cross_border_parcels']}[/] (Miễn thuế: [bold green]{m['exempt_parcels_count']}[/])",
            title="[bold blue]E-Commerce Operational Telemetry[/]",
            border_style="green",
        )
    )
