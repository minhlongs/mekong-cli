# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Vietnam E-Commerce, Specialized Inspection, Hazardous Chemicals & CBAM CLI Commands (Phases 175 - 178).

Provides CLI commands for:
- Phase 175: Cross-Border E-Commerce Customs Management & Platform Withholding
- Phase 176: Hazardous Chemicals Import Declaration via NSW & Dangerous Goods Segregation
- Phase 177: Specialized Food Safety & Quarantine Inspection
- Phase 178: EU CBAM & EUDR Green Supply Chain Export Compliance
"""

from __future__ import annotations

import json
from typing import List, Optional, Tuple
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.ecom_inspect_engine import (
    CrossBorderEcomEngine,
    HazardousChemicalNSWEngine,
    SpecializedInspectionEngine,
    CBAMEUDRComplianceEngine,
    EcomPlatform,
    EcomOrderItem,
    ChemicalItem,
    ChemicalAnnex,
    FoodInspectionMethod,
    FoodSafetyConsignmentRecord,
    QuarantineType,
    CBAMSector,
    CBAMEmissionsInput,
)

ecom_app = typer.Typer(
    name="ecom",
    help="ECOM — Cross-Border E-Commerce Customs Management & Platform Withholding (Phase 175)",
    no_args_is_help=False,
)

inspect_app = typer.Typer(
    name="inspect",
    help="INSPECT — Specialized Inspection, Hazardous Chemicals & EU CBAM/EUDR Suite (Phases 176-178)",
    no_args_is_help=False,
)

console = Console()


# =====================================================================
# E-COMMERCE CLI COMMANDS (PHASE 175)
# =====================================================================

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
    try:
        plat_enum = EcomPlatform[platform.upper()]
    except KeyError:
        plat_enum = EcomPlatform.OTHER

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
    table.add_row(
        "Thuế Nhập khẩu",
        f"{result.import_duty_vnd:,.0f} đ",
        "[green]Miễn thuế (<= 1M)[/green]" if result.is_de_minimis_duty_free else f"Thuế suất {duty_rate}%",
    )
    if result.sct_vnd > 0:
        table.add_row("Thuế TTĐB", f"{result.sct_vnd:,.0f} đ", f"Thuế suất {sct_rate}%")
    table.add_row("Thuế GTGT", f"{result.vat_vnd:,.0f} đ", f"Thuế suất {vat_rate}% (Bỏ QĐ 78, thu từ 0đ)")
    table.add_row("Tổng nghĩa vụ thuế", f"{result.total_tax_liability_vnd:,.0f} đ", "Tổng số nộp NSNN")
    table.add_row(
        "Sàn khấu trừ nộp thay",
        f"[bold yellow]{result.platform_withholding_payable_vnd:,.0f} đ[/bold yellow]",
        f"Trách nhiệm sàn {plat_enum.value} (TT 80/2021)",
    )

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


# =====================================================================
# SPECIALIZED INSPECTION, CHEMICALS & CBAM CLI (PHASES 176 - 178)
# =====================================================================

@inspect_app.callback(invoke_without_command=True)
def inspect_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Kiểm tra Chuyên ngành, Khai báo Hóa chất NSW & EU CBAM/EUDR."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Specialized Inspection, Chemicals & CBAM Suite (Phases 176-178)",
            "statutory_basis": [
                "Decree 113/2017/ND-CP & Decree 82/2022/ND-CP (Hazardous Chemicals)",
                "IMDG Code 41-22 & IATA DGR (Dangerous Goods Segregation)",
                "Decree 15/2018/ND-CP (Imported Food Safety Inspection Tiers)",
                "Circular 25/2016/TT-BNNPTNT & Circular 33/2014/TT-BNNPTNT (Quarantine)",
                "EU Regulation 2023/956 (CBAM) & EU Regulation 2023/1115 (EUDR)",
            ],
            "commands": ["chemical", "dg-segregation", "food-tier", "quarantine", "cbam", "eudr"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Specialized Inspection, Chemicals & CBAM Suite (Phases 176-178)[/bold cyan]\n"
            "[dim]Kiểm tra chuyên ngành ATTP, khai báo hóa chất một cửa quốc gia, phân cách hàng nguy hiểm và tuân thủ CBAM/EUDR.[/dim]\n\n"
            "• [bold yellow]chemical[/bold yellow]       : Kiểm tra phân loại Hóa chất NĐ 113/82 (PL I-V) & cấp token VNSW.\n"
            "• [bold red]dg-segregation[/bold red] : Ma trận phân cách hàng nguy hiểm IMDG/IATA (9 nhóm).\n"
            "• [bold green]food-tier[/bold green]      : Chuyển đổi phương thức kiểm tra ATTP NĐ 15/2018 (Chặt -> Thường -> Giảm).\n"
            "• [bold blue]quarantine[/bold blue]     : Kiểm tra thời hạn hiệu lực giấy kiểm dịch động vật / thực vật.\n"
            "• [bold magenta]cbam[/bold magenta]           : Tính phát thải tích hợp và nghĩa vụ tài chính CBAM xuất khẩu EU.\n"
            "• [bold green]eudr[/bold green]           : Thẩm định chuỗi cung ứng không phá rừng EUDR (Polygon GPS & Cut-off 2020).",
            title="🔬 [bold]KIỂM TRA CHUYÊN NGÀNH & HÓA CHẤT & CBAM[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@inspect_app.command("chemical")
def inspect_chemical(
    cas: str = typer.Argument(..., help="Mã định danh hóa chất CAS"),
    qty_kg: float = typer.Argument(..., help="Khối lượng nhập khẩu (kg)"),
    name: str = typer.Option("Chemical Compound", "--name", "-n", help="Tên hóa chất"),
    hs: str = typer.Option("2807.00.00", "--hs", help="Mã HS"),
    annexes_str: str = typer.Option("ANNEX_V", "--annexes", "-a", help="Các phụ lục thuộc NĐ 113/82 (phân tách dấu phẩy)"),
    moit_license: Optional[str] = typer.Option(None, "--license", "-l", help="Số giấy phép BCT (nếu thuộc PL II)"),
    vnsw_id: Optional[str] = typer.Option(None, "--vnsw", help="Mã hồ sơ khai báo NSW"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá điều kiện nhập khẩu hóa chất theo Nghị định 113/2017 & 82/2022."""
    annex_enums: List[ChemicalAnnex] = []
    for a in annexes_str.split(","):
        a_clean = a.strip().upper()
        if not a_clean.startswith("ANNEX_"):
            a_clean = f"ANNEX_{a_clean}"
        for member in ChemicalAnnex:
            if member.value == a_clean or member.name == a_clean:
                annex_enums.append(member)
                break

    item = ChemicalItem(
        cas_number=cas,
        chemical_name=name,
        hs_code=hs,
        quantity_kg=qty_kg,
        annexes=annex_enums,
        moit_license_number=moit_license,
        vnsw_declaration_id=vnsw_id,
    )

    result = HazardousChemicalNSWEngine.evaluate_chemical_compliance(item)

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"🧪 Khai Báo Hóa Chất NSW — CAS: {cas}", box=box.ROUNDED)
    table.add_column("Chỉ số kiểm tra", style="cyan")
    table.add_column("Kết quả", style="bold")
    table.add_column("Chi tiết luật định", style="dim")

    table.add_row("Tên hóa chất / Khối lượng", f"{name} ({qty_kg:,.1f} kg)", f"HS: {hs}")
    table.add_row(
        "Hóa chất Cấm (Phụ lục III)",
        "[bold red]CẤM NHẬP KHẨU[/bold red]" if result.is_banned else "[green]Không thuộc PL Cấm[/green]",
        "Nghị định 113/2017/NĐ-CP",
    )
    table.add_row(
        "Hóa chất Hạn chế (Phụ lục II)",
        f"{'Bắt buộc Giấy phép BCT' if result.requires_moit_license else 'Không thuộc PL II'}",
        f"Giấy phép: {moit_license or 'Chưa có'}",
    )
    table.add_row("Kế hoạch / Biện pháp PC Sự cố", result.accident_document_type, "Đánh giá theo ngưỡng tồn trữ")
    table.add_row(
        "Khai báo Cổng Một cửa (VNSW)",
        f"[green]{result.nsw_token}[/green]" if result.nsw_token else ("Miễn khai (<10kg)" if result.is_nsw_exempt else "Chưa khai báo"),
        "Hệ thống NSW vnsw.gov.vn",
    )
    table.add_row("Trạng thái Hải quan", f"[bold]{result.customs_status}[/bold]", result.action_required)

    console.print(table)


@inspect_app.command("dg-segregation")
def inspect_dg_segregation(
    un_a: str = typer.Argument(..., help="Số UN chất A (ví dụ UN1203)"),
    class_a: float = typer.Argument(..., help="Nhóm nguy hiểm chất A (ví dụ 3.0)"),
    un_b: str = typer.Argument(..., help="Số UN chất B (ví dụ UN1479)"),
    class_b: float = typer.Argument(..., help="Nhóm nguy hiểm chất B (ví dụ 5.1)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu ma trận phân cách hàng nguy hiểm theo IMDG Code 41-22 & IATA DGR."""
    result = HazardousChemicalNSWEngine.check_dg_segregation(
        un_a=un_a,
        dg_class_a=class_a,
        un_b=un_b,
        dg_class_b=class_b,
    )

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = "green" if result.is_coloading_permitted else "red"
    content = (
        f"• Chất A: [bold]{result.un_a}[/bold] (Class {result.dg_class_a})\n"
        f"• Chất B: [bold]{result.un_b}[/bold] (Class {result.dg_class_b})\n"
        f"• Cấp phân cách IMDG: [bold]{result.segregation_requirement}[/bold]\n"
        f"• Khoảng cách tối thiểu: [bold]{result.min_distance_meters} mét[/bold]\n"
        f"• Cho phép đóng chung container: [bold]{'CÓ' if result.min_distance_meters == 0 else 'KHÔNG'}[/bold]\n\n"
        f"[bold]Quy định luật định:[/bold]\n{result.statutory_rule}"
    )

    console.print(
        Panel(
            content,
            title="⚠️ Ma Trận Phân Cách Hàng Nguy Hiểm (IMDG Code 41-22)",
            border_style=style,
            box=box.ROUNDED,
        )
    )


@inspect_app.command("food-tier")
def inspect_food_tier(
    consignor_id: str = typer.Argument(..., help="Mã nhà sản xuất / xuất khẩu nước ngoài"),
    current_method: str = typer.Option("NORMAL", "--current", "-c", help="Phương thức hiện tại (REDUCED, NORMAL, TIGHTENED)"),
    passes: int = typer.Option(0, "--passes", "-p", help="Số lô liên tiếp đạt yêu cầu"),
    has_iso_haccp: bool = typer.Option(False, "--haccp", help="Có chứng nhận GMP, HACCP, ISO 22000, IFS, BRC"),
    cert_days: int = typer.Option(0, "--cert-days", help="Thời hạn hiệu lực chứng nhận ATTP (ngày)"),
    failed_last: bool = typer.Option(False, "--failed", help="Lô gần nhất không đạt chỉ tiêu ATTP"),
    warning: bool = typer.Option(False, "--warning", help="Có cảnh báo an toàn từ Bộ Y tế / NN&PTNT / Công Thương"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá phương thức kiểm tra ATTP nhập khẩu theo Nghị định 15/2018/NĐ-CP."""
    try:
        meth_enum = FoodInspectionMethod[current_method.upper()]
    except KeyError:
        meth_enum = FoodInspectionMethod.NORMAL

    record = FoodSafetyConsignmentRecord(
        consignor_id=consignor_id,
        product_hs="1905.90.00",
        current_method=meth_enum,
        consecutive_passes=passes,
        has_iso22000_or_haccp=has_iso_haccp,
        cert_valid_days=cert_days,
        failed_last_batch=failed_last,
        official_warning_issued=warning,
    )

    result = SpecializedInspectionEngine.evaluate_food_inspection_tier(record)

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"🍎 Kiểm Tra Chuyên Ngành ATTP — Doanh nghiệp: {consignor_id}", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Trạng thái", style="bold")
    table.add_column("Căn cứ Nghị định 15/2018/NĐ-CP", style="dim")

    table.add_row(
        "Phương thức áp dụng",
        f"[bold]{result.assigned_method.value}[/bold]",
        "Kiểm tra Giảm / Thông thường / Chặt",
    )
    table.add_row("Tỷ lệ lấy mẫu kiểm nghiệm", f"{result.sample_inspection_rate_pct:.0f}%", "Kiểm tra thực tế mẫu")
    table.add_row("Yêu cầu thử nghiệm Lab", "CÓ (Bắt buộc)" if result.requires_lab_testing else "KHÔNG (Chỉ xét hồ sơ)", "100% chỉ tiêu ATTP")
    table.add_row("Lý do áp dụng", result.transition_reason, "Điều 16, 17, 18")
    table.add_row("Điều kiện chuyển bậc tiếp theo", result.next_milestone, "Chuỗi 3 lô liên tiếp đạt")

    console.print(table)


@inspect_app.command("quarantine")
def inspect_quarantine(
    cert_id: str = typer.Argument(..., help="Số giấy chứng nhận kiểm dịch"),
    q_type: str = typer.Argument(..., help="Loại kiểm dịch (ANIMAL_LIVE, ANIMAL_CONSUMPTION, ANIMAL_PROCESSED, PLANT_PHYTOSANITARY)"),
    issue_date: str = typer.Argument(..., help="Ngày cấp giấy kiểm dịch (YYYY-MM-DD)"),
    inspect_date: str = typer.Argument(..., help="Ngày làm thủ tục hải quan (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra thời hạn hiệu lực giấy chứng nhận kiểm dịch động thực vật."""
    type_map = {
        "ANIMAL_LIVE": QuarantineType.ANIMAL_LIVE,
        "ANIMAL_CONSUMPTION": QuarantineType.ANIMAL_CONSUMPTION,
        "ANIMAL_FOOD": QuarantineType.ANIMAL_CONSUMPTION,
        "ANIMAL_PROCESSED": QuarantineType.ANIMAL_PROCESSED,
        "PLANT_PHYTOSANITARY": QuarantineType.PLANT_PHYTOSANITARY,
        "PLANT_PHYTO": QuarantineType.PLANT_PHYTOSANITARY,
    }
    target_type = type_map.get(q_type.upper(), QuarantineType.PLANT_PHYTOSANITARY)

    result = SpecializedInspectionEngine.verify_quarantine_validity(
        certificate_id=cert_id,
        quarantine_type=target_type,
        issue_date_str=issue_date,
        inspection_date_str=inspect_date,
    )

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = "green" if result.is_valid else "red"
    content = (
        f"• Số giấy kiểm dịch: [bold]{result.certificate_id}[/bold]\n"
        f"• Loại hình kiểm dịch: {result.quarantine_type.value}\n"
        f"• Ngày cấp: {result.issue_date} | Ngày làm thủ tục: {result.inspection_date}\n"
        f"• Thời hạn tối đa: {result.max_validity_days} ngày\n"
        f"• Thời gian đã trôi qua: {result.elapsed_days} ngày\n"
        f"• Số ngày còn lại: [bold]{result.remaining_days} ngày[/bold]\n\n"
        f"[bold]Kết luận kiểm dịch:[/bold]\n{result.action}"
    )

    console.print(
        Panel(
            content,
            title="🌿 Thời Hiệu Giấy Chứng Nhận Kiểm Dịch (TT 25/2016 & TT 33/2014)",
            border_style=style,
            box=box.ROUNDED,
        )
    )


@inspect_app.command("cbam")
def inspect_cbam(
    sector: str = typer.Argument(..., help="Lĩnh vực CBAM (IRON_STEEL, ALUMINIUM, CEMENT, FERTILIZERS, HYDROGEN)"),
    export_vol: float = typer.Argument(..., help="Sản lượng xuất khẩu vào EU (tấn)"),
    prod_vol: float = typer.Argument(..., help="Tổng sản lượng toàn cơ sở (tấn)"),
    scope1: float = typer.Argument(..., help="Phát thải trực tiếp Scope 1 (tCO2e)"),
    elec_mwh: float = typer.Argument(..., help="Điện năng tiêu thụ (MWh)"),
    grid_ef: float = typer.Option(0.722, "--grid-ef", help="Hệ số phát thải lưới điện (tCO2/MWh)"),
    ets_price: float = typer.Option(75.0, "--ets-price", help="Giá hạn ngạch EU ETS (EUR/tCO2e)"),
    vn_price: float = typer.Option(0.0, "--vn-price", help="Giá carbon hiệu dụng đã trả tại Việt Nam (EUR/tCO2e)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính phát thải tích hợp và nghĩa vụ tài chính chứng chỉ EU CBAM."""
    sec_map = {
        "IRON_STEEL": CBAMSector.IRON_AND_STEEL,
        "STEEL": CBAMSector.IRON_AND_STEEL,
        "ALUMINIUM": CBAMSector.ALUMINIUM,
        "CEMENT": CBAMSector.CEMENT,
        "FERTILIZERS": CBAMSector.FERTILIZERS,
        "HYDROGEN": CBAMSector.HYDROGEN,
    }
    sec_enum = sec_map.get(sector.upper(), CBAMSector.IRON_AND_STEEL)

    inp = CBAMEmissionsInput(
        sector=sec_enum,
        export_volume_tonnes=export_vol,
        total_production_volume_tonnes=prod_vol,
        direct_emissions_scope1_tco2e=scope1,
        electricity_consumed_mwh=elec_mwh,
        grid_emission_factor_tco2_mwh=grid_ef,
        eu_ets_allowance_price_eur=ets_price,
        vn_carbon_effective_price_eur=vn_price,
    )

    result = CBAMEUDRComplianceEngine.calculate_cbam_liability(inp)

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"🌱 Tính Toán Nghĩa Vụ EU CBAM — Ngành: {sec_enum.value}", box=box.ROUNDED)
    table.add_column("Chỉ số phát thải & tài chính", style="cyan")
    table.add_column("Giá trị", style="bold", justify="right")
    table.add_column("Căn cứ EU Reg 2023/956", style="dim")

    table.add_row("Khối lượng xuất khẩu sang EU", f"{result.export_volume_tonnes:,.1f} tấn", "Sản lượng chịu CBAM")
    table.add_row("Phát thải trực tiếp (Scope 1)", f"{result.direct_emissions_tco2e:,.2f} tCO2e", "Đốt nhiên liệu, nung hóa chất")
    table.add_row("Phát thải gián tiếp (Scope 2)", f"{result.indirect_emissions_tco2e:,.2f} tCO2e", f"Điện {elec_mwh:,.0f} MWh × {grid_ef} EF")
    table.add_row("Cường độ tích hợp (SE)", f"{result.specific_embedded_emissions_per_tonne:.4f} tCO2e/tấn", "Phát thải trên 1 tấn SP")
    table.add_row("Tổng phát thải tích hợp XK", f"{result.total_embedded_emissions_tco2e:,.2f} tCO2e", "SE × Khối lượng XK")
    table.add_row("Chênh lệch giá carbon EU - VN", f"€{result.net_carbon_price_spread_eur:,.2f} / tCO2e", f"EU €{ets_price} - VN €{vn_price}")
    table.add_row(
        "Nghĩa vụ chứng chỉ CBAM",
        f"[bold magenta]€{result.total_cbam_liability_eur:,.2f} EUR[/bold magenta]",
        "Nộp từ giai đoạn chính thức 2026+",
    )

    console.print(table)


@inspect_app.command("eudr")
def inspect_eudr(
    plot_id: str = typer.Argument(..., help="Mã định danh thửa đất trồng"),
    hs: str = typer.Argument(..., help="Mã HS mặt hàng (Gỗ 44, Cao su 40, Cà phê 0901)"),
    area: float = typer.Argument(..., help="Diện tích thửa đất (hecta)"),
    coords: str = typer.Option(..., "--coords", "-c", help="Tọa độ thửa đất (định dạng: lat,lon;lat,lon;...)"),
    deforest_free: bool = typer.Option(True, "--deforest-free", help="Không phá rừng sau ngày 31/12/2020"),
    land_title: bool = typer.Option(True, "--land-title", help="Có sổ đỏ / giấy chứng nhận quyền sử dụng đất"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định chuỗi cung ứng không phá rừng theo Quy định EUDR 2023/1115."""
    coord_list: List[Tuple[float, float]] = []
    for pair in coords.split(";"):
        if "," in pair:
            parts = pair.split(",")
            coord_list.append((float(parts[0].strip()), float(parts[1].strip())))

    result = CBAMEUDRComplianceEngine.verify_eudr_compliance(
        plot_id=plot_id,
        commodity_hs=hs,
        area_hectares=area,
        coordinates=coord_list,
        deforestation_free_post_2020=deforest_free,
        legal_land_title_certified=land_title,
    )

    if json_mode:
        console.print_json(json.dumps(result.to_dict(), ensure_ascii=False))
        return

    style = "green" if result.is_compliant else "red"
    reasons = "\n".join([f"• [red]{r}[/red]" for r in result.rejection_reasons]) if result.rejection_reasons else "• [green]Thỏa mãn 100% 3 cổng thẩm định EUDR[/green]"

    content = (
        f"• Thửa đất: [bold]{result.plot_id}[/bold] | Mã HS: {result.commodity_hs}\n"
        f"• Diện tích: {result.area_hectares} ha | Số đỉnh tọa độ: {len(result.coordinates)}\n"
        f"• Rừng không bị tàn phá sau 31/12/2020: {'ĐẠT' if result.deforestation_free_post_2020 else 'VI PHẠM'}\n"
        f"• Pháp lý quyền sử dụng đất: {'HỢP LỆ' if result.legal_land_title_certified else 'THIẾU SỔ ĐỎ'}\n"
        f"• Trạng thái thẩm định: [bold]{result.validation_status}[/bold]\n\n"
        f"[bold]Đánh giá chi tiết:[/bold]\n{reasons}"
    )

    console.print(
        Panel(
            content,
            title="🌲 Thẩm Định Chuỗi Cung Ứng Không Phá Rừng (EUDR 2023/1115)",
            border_style=style,
            box=box.ROUNDED,
        )
    )
