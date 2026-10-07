# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Vietnam Seaport Operations, Trade Finance L/C, Pharma Cold Chain & Freight Carbon CLI (Phases 179 - 182).

Provides CLI commands for:
- Phase 179: Seaport Terminal Tariffs (TT 39/2023), DEM/DET Escalations & SOLAS VGM
- Phase 180: Cross-Border Trade Finance L/C Strict Compliance (UCP 600 / ISBP 745) & Usance Discounting
- Phase 181: Pharma Cold Chain Integrity, Arrhenius MKT & GDP Quarantine Holds (TT 02/2018)
- Phase 182: Multimodal Freight Carbon Accounting & Scope 3 Decarbonization (ISO 14083 / GLEC v3.0)
"""

from __future__ import annotations

import json
from typing import List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.port_supply_chain_engine import (
    SeaportTerminalOpsEngine,
    TradeFinanceLCEngine,
    ColdChainPharmaGDPEngine,
    FreightCarbonAccountingEngine,
    PortArea,
    ContainerType,
    CargoStatus,
    PharmaStorageClass,
    FreightTransportMode,
    TemperatureExcursionEvent,
)

port_app = typer.Typer(
    name="port",
    help="PORT — Vietnam Seaport Terminal Operations, DEM/DET & SOLAS VGM Suite (Phase 179)",
    no_args_is_help=False,
)

tradefinance_app = typer.Typer(
    name="tradefinance",
    help="TRADEFINANCE — L/C UCP 600, Pharma Cold Chain & Green Freight Carbon Suite (Phases 180-182)",
    no_args_is_help=False,
)

console = Console()


# =====================================================================
# SEAPORT OPERATIONS & TERMINAL COMMANDS (PHASE 179)
# =====================================================================

@port_app.callback(invoke_without_command=True)
def port_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Quản trị Cảng biển, Biểu phí THC, DEM/DET & Cân VGM."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Seaport Terminal Operations & SOLAS VGM Suite (Phase 179)",
            "statutory_basis": [
                "Circular 39/2023/TT-BGTVT (Vietnam Seaport Tariffs & Container Stevedoring)",
                "Vietnam Maritime Code 2015 Article 168 (Statutory Maritime Lien for Unpaid Demurrage)",
                "IMO SOLAS Chapter VI Regulation 2 & MSC.1/Circ.1475 (Verified Gross Mass)",
                "Decree 58/2017/ND-CP (Maritime Transport & Seaport Administration)",
            ],
            "commands": ["tariff", "dem-det", "vgm"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Seaport Terminal Operations & Maritime Suite (Phase 179)[/bold cyan]\n"
            "[dim]Kiểm soát chi phí bốc dỡ cảng biển, lũy tiến phạt lưu bãi/lưu vỏ và cân tải trọng SOLAS.[/dim]\n\n"
            "• [bold green]tariff[/bold green]   : Biểu phí bốc dỡ container (Lạch Huyện, Đà Nẵng, Cái Mép, Cát Lái - TT 39/2023).\n"
            "• [bold yellow]dem-det[/bold yellow]  : Lũy tiến phí lưu bãi/vỏ (Tier 1-3) & cảnh báo quyền cầm giữ hàng (Điều 168 BLLHH).\n"
            "• [bold blue]vgm[/bold blue]      : Xác thực dung sai cân SOLAS VGM (+/-5% hoặc 500kg) & cấp lệnh hạ bãi Gate-in.",
            title="⚓ [bold]QUẢN TRỊ CẢNG BIỂN & SOLAS VGM[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@port_app.command("tariff")
def port_tariff(
    area: str = typer.Option("AREA_III_SOUTH", "--area", "-a", help="Cụm cảng (AREA_I_NORTH, AREA_II_CENTRAL, AREA_III_SOUTH)"),
    container_type: str = typer.Option("DRY_40FT", "--container", "-c", help="Loại container (DRY_20FT, DRY_40FT, DRY_45FT, REEFER_20FT, REEFER_40FT, OOG_FLATRACK, DG_CONTAINER)"),
    status: str = typer.Option("LADEN", "--status", "-s", help="Trạng thái hàng (LADEN: có hàng, EMPTY: vỏ rỗng)"),
    reefer_hours: float = typer.Option(0.0, "--reefer-hours", "-r", help="Số giờ cắm điện lạnh container reefer"),
    imo: bool = typer.Option(False, "--imo", help="Hàng nguy hiểm IMO/DG (+50% phụ phí)"),
    oog: bool = typer.Option(False, "--oog", help="Hàng quá khổ quá tải OOG (+100% phụ phí)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi phí xếp dỡ cảng biển và phụ phí theo Thông tư 39/2023/TT-BGTVT."""
    try:
        area_enum = PortArea[area.upper()]
    except KeyError:
        area_enum = PortArea.AREA_III_SOUTH

    try:
        c_type_enum = ContainerType[container_type.upper()]
    except KeyError:
        c_type_enum = ContainerType.DRY_40FT

    try:
        status_enum = CargoStatus[status.upper()]
    except KeyError:
        status_enum = CargoStatus.LADEN

    res = SeaportTerminalOpsEngine.calculate_port_tariff(
        port_area=area_enum,
        container_type=c_type_enum,
        cargo_status=status_enum,
        reefer_plug_hours=reefer_hours,
        is_imo_dangerous=imo,
        is_oog=oog,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="⚓ BIỂU PHÍ BỐC DỠ CẢNG BIỂN (THÔNG TƯ 39/2023/TT-BGTVT)", box=box.ROUNDED)
    table.add_column("Hạng mục Phí", style="cyan", justify="left")
    table.add_column("Chi tiết / Mức tính", style="magenta", justify="right")

    table.add_row("Khu vực Cảng biển", area_enum.value)
    table.add_row("Loại Container & Trạng thái", f"{c_type_enum.value} ({status_enum.value})")
    table.add_row("Phí xếp dỡ cơ bản (THC)", f"{res.base_thc_vnd:,.0f} VND")
    if res.reefer_power_vnd > 0:
        table.add_row(f"Điện lạnh Reefer ({reefer_hours:.1f}h)", f"{res.reefer_power_vnd:,.0f} VND")
    if res.surcharge_vnd > 0:
        table.add_row("Phụ phí Đặc thù (IMO / OOG)", f"{res.surcharge_vnd:,.0f} VND")
    table.add_section()
    table.add_row("[bold green]TỔNG CỘNG CHI PHÍ[/bold green]", f"[bold green]{res.total_port_charge_vnd:,.0f} VND[/bold green]")

    console.print(table)


@port_app.command("dem-det")
def port_dem_det(
    container_id: str = typer.Option("TCLU8291045", "--id", help="Số hiệu container ISO"),
    container_type: str = typer.Option("DRY_40FT", "--type", "-t", help="Loại container (DRY_20FT, DRY_40FT, DRY_45FT)"),
    days_incurred: int = typer.Option(8, "--days", "-d", help="Tổng số ngày lưu bãi/lưu vỏ thực tế"),
    free_days: int = typer.Option(5, "--free-days", "-f", help="Số ngày miễn phí (Free time) theo hãng tàu"),
    cif_value_usd: float = typer.Option(25000.0, "--cif-usd", help="Trị giá CIF lô hàng (USD) để xét quyền cầm giữ hàng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán phí lũy tiến Demurrage/Detention (DEM/DET) & đánh giá quyền cầm giữ hàng (Điều 168 BLLHH 2015)."""
    try:
        c_type_enum = ContainerType[container_type.upper()]
    except KeyError:
        c_type_enum = ContainerType.DRY_40FT

    res = SeaportTerminalOpsEngine.calculate_dem_det(
        container_id=container_id,
        container_type=c_type_enum,
        days_incurred=days_incurred,
        free_days_allowed=free_days,
        cargo_cif_value_usd=cif_value_usd,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="⚠️ QUẢN TRỊ DEM/DET & QUYỀN CẦM GIỮ HÀNG HẢI", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")

    table.add_row("Số hiệu Container", res.container_id)
    table.add_row("Hạn Miễn phí (Free Time)", f"{res.free_days_allowed} ngày")
    table.add_row("Thời gian Thực tế", f"{res.days_incurred} ngày")
    table.add_row("Số ngày Quá hạn (Overdue)", f"{res.overdue_days} ngày")
    table.add_row("Giai đoạn Lũy tiến", res.stage.value)
    table.add_row("Đơn giá phạt hiện tại", f"${res.daily_rate_usd:,.2f} USD/ngày")
    table.add_section()
    table.add_row("[bold red]Tổng Phạt Quá Hạn (USD)[/bold red]", f"[bold red]${res.total_penalty_usd:,.2f} USD[/bold red]")
    table.add_row("Quy đổi tương đương (VND)", f"{res.total_penalty_vnd:,.0f} VND")
    table.add_row("Cảnh báo Cầm giữ hàng (Điều 168)", "[bold red]CÓ CẢNH BÁO[/bold red]" if res.carrier_lien_warning else "[bold green]AN TOÀN[/bold green]")

    console.print(table)
    if res.carrier_lien_warning:
        console.print(Panel(f"[bold red]CẢNH BÁO PHÁP LÝ:[/bold red] {res.lien_rationale}", border_style="red"))


@port_app.command("vgm")
def port_vgm(
    container_id: str = typer.Option("MSKU1092834", "--id", help="Số hiệu container ISO"),
    declared_kg: float = typer.Option(24500.0, "--declared", "-w", help="Khối lượng VGM khai báo (kg)"),
    measured_kg: float = typer.Option(24850.0, "--measured", "-m", help="Khối lượng cân thực tế tại bàn cân cảng (kg)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xác thực sai số khối lượng toàn bộ SOLAS VGM theo quy chuẩn IMO MSC.1/Circ.1475."""
    res = SeaportTerminalOpsEngine.verify_solas_vgm(
        container_id=container_id,
        declared_vgm_kg=declared_kg,
        verified_scale_kg=measured_kg,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="⚖️ XÁC THỰC TẢI TRỌNG SOLAS VGM (IMO CHAPTER VI REG 2)", box=box.ROUNDED)
    table.add_column("Chỉ số Kiểm tra", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")

    table.add_row("Số hiệu Container", res.container_id)
    table.add_row("VGM Khai báo (Shipper Declared)", f"{res.declared_vgm_kg:,.1f} kg")
    table.add_row("VGM Thực tế (Terminal Weighbridge)", f"{res.verified_scale_kg:,.1f} kg")
    table.add_row("Chênh lệch Tuyệt đối", f"{res.variance_kg:,.1f} kg ({res.variance_pct:.2f}%)")
    table.add_row("Dung sai Tối đa Cho phép (min 5%, 500kg)", f"{res.max_allowable_variance_kg:,.1f} kg")
    table.add_section()
    table.add_row("Trạng thái Tuân thủ", "[bold green]HỢP LỆ (COMPLIANT)[/bold green]" if res.is_compliant else "[bold red]VI PHẠM (NON-COMPLIANT)[/bold red]")
    table.add_row("Lệnh Cấp Phép Hạ Bãi / Xếp Tàu", f"[bold]{res.gate_in_status}[/bold]")

    console.print(table)
    if not res.is_compliant:
        console.print(Panel(f"[bold red]TỪ CHỐI XẾP TÀU (NO VGM, NO LOAD):[/bold red]\n{res.rejection_reason}\nƯớc tính phí phạt cân lại: {res.penalty_estimate_vnd:,.0f} VND", border_style="red"))


# =====================================================================
# TRADE FINANCE & COLD CHAIN / CARBON COMMANDS (PHASES 180-182)
# =====================================================================

@tradefinance_app.callback(invoke_without_command=True)
def tradefinance_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Tài trợ Thương mại L/C UCP 600, Chuỗi lạnh Dược phẩm & Khí nhà kính Vận tải."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Trade Finance, Cold Chain & Logistics Carbon Suite (Phases 180-182)",
            "statutory_basis": [
                "ICC Uniform Customs and Practice for Documentary Credits (UCP 600)",
                "International Standard Banking Practice (ISBP 745)",
                "Circular 02/2018/TT-BYT & Circular 36/2018/TT-BYT (GDP & GSP for Pharmaceuticals)",
                "WHO Technical Report Series No. 961 Annex 9 & USP-NF <1079> (Mean Kinetic Temperature)",
                "ISO 14083:2023 & GLEC Framework v3.0 (Logistics GHG Emissions)",
                "Decree 06/2022/ND-CP (Greenhouse Gas Mitigation & Carbon Market)",
            ],
            "commands": ["lc-exam", "lc-discount", "mkt", "coldchain", "carbon", "modal-shift"],
        }
        console.print_json(json.dumps(data, ensure_ascii=False))
        return

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_row(
        Panel(
            "[bold cyan]Mekong Trade Finance, Cold Chain & Green Freight Suite (Phases 180-182)[/bold cyan]\n"
            "[dim]Kiểm tra L/C theo UCP 600, bảo đảm chuỗi lạnh GDP Dược phẩm và kiểm kê carbon ISO 14083.[/dim]\n\n"
            "• [bold green]lc-exam[/bold green]     : Kiểm tra tuân thủ nghiêm ngặt L/C theo UCP 600 & thời hạn 5 ngày ngân hàng.\n"
            "• [bold green]lc-discount[/bold green] : Tính chiết khấu hối phiếu L/C trả chậm (ACT/360) & trừ phí sai biệt.\n"
            "• [bold yellow]mkt[/bold yellow]         : Tính Nhiệt độ Động học Trung bình (MKT) Arrhenius cho vaccine/dược phẩm.\n"
            "• [bold yellow]coldchain[/bold yellow]   : Đánh giá sự cố nhiệt độ & lệnh Biệt trữ Đảm bảo Chất lượng (TT 02/2018).\n"
            "• [bold blue]carbon[/bold blue]      : Kiểm kê khí nhà kính vận tải đa phương thức theo chuẩn quốc tế ISO 14083.\n"
            "• [bold blue]modal-shift[/bold blue] : Tối ưu hóa chuyển đổi phương thức xanh (Đường bộ → Xà lan Cái Mép).",
            title="💳 [bold]TÀI TRỢ THƯƠNG MẠI, CHUỖI LẠNH & DECARBONIZATION[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )
    console.print(grid)


@tradefinance_app.command("lc-exam")
def tradefinance_lc_exam(
    lc_ref: str = typer.Option("LC-2026-VCB-9182", "--ref", help="Số tham chiếu L/C"),
    pres_date: str = typer.Option("2026-10-06", "--pres-date", help="Ngày xuất trình chứng từ (YYYY-MM-DD)"),
    ship_date: str = typer.Option("2026-10-01", "--ship-date", help="Ngày giao hàng trễ nhất cho phép (YYYY-MM-DD)"),
    exp_date: str = typer.Option("2026-10-25", "--exp-date", help="Ngày hết hạn của L/C (YYYY-MM-DD)"),
    bl_date: str = typer.Option("2026-09-28", "--bl-date", help="Ngày phát hành vận đơn B/L on board (YYYY-MM-DD)"),
    inv_amount: float = typer.Option(150000.0, "--inv-amount", help="Số tiền trên Hóa đơn Thương mại (USD)"),
    lc_amount: float = typer.Option(150000.0, "--lc-amount", help="Giá trị tối đa của L/C (USD)"),
    exact_desc: bool = typer.Option(True, "--exact-desc", help="Mô tả hàng hóa trên hóa đơn khớp từng chữ với L/C (Điều 18c)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra tuân thủ chứng từ L/C theo chuẩn quốc tế ICC UCP 600 & ISBP 745."""
    res = TradeFinanceLCEngine.examine_presentation(
        lc_reference=lc_ref,
        presentation_date_iso=pres_date,
        latest_shipment_date_iso=ship_date,
        expiry_date_iso=exp_date,
        bl_onboard_date_iso=bl_date,
        invoice_amount_usd=inv_amount,
        lc_credit_amount_usd=lc_amount,
        is_goods_description_exact_match=exact_desc,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"💳 KIỂM TRA CHỨNG TỪ L/C UCP 600 ({res.lc_reference})", box=box.ROUNDED)
    table.add_column("Hạng mục Kiểm tra", style="cyan")
    table.add_column("Chi tiết", style="magenta", justify="right")

    table.add_row("Ngày xuất trình chứng từ", res.presentation_date)
    table.add_row("Hạn chót kiểm tra (5 ngày LVNH)", res.examination_deadline_date)
    table.add_row("Kết quả kiểm tra", "[bold green]CHỨNG TỪ HỢP LỆ (CLEAN)[/bold green]" if res.is_clean else "[bold red]PHÁT HIỆN BẤT HỢP LỆ (DISCREPANT)[/bold red]")
    table.add_row("Hành động yêu cầu", res.action_required)
    table.add_row("Khấu trừ phí bất hợp lệ", f"${res.discrepancy_fee_usd:,.2f} USD")

    console.print(table)

    if not res.is_clean:
        disc_table = Table(title="CHI TIẾT CÁC ĐIỂM BẤT HỢP LỆ (DISCREPANCIES)", box=box.SIMPLE)
        disc_table.add_column("Điều khoản UCP 600", style="yellow")
        disc_table.add_column("Chứng từ", style="cyan")
        disc_table.add_column("Nội dung Bất hợp lệ", style="red")

        for d in res.discrepancies:
            disc_table.add_row(d.rule_article, d.document_type.value, d.description)
        console.print(disc_table)


@tradefinance_app.command("lc-discount")
def tradefinance_lc_discount(
    lc_ref: str = typer.Option("LC-2026-VCB-9182", "--ref", help="Số tham chiếu L/C"),
    draft_amount: float = typer.Option(200000.0, "--draft", help="Trị giá hối phiếu L/C trả chậm (USD)"),
    tenor: int = typer.Option(90, "--tenor", "-t", help="Thời hạn trả chậm (ngày)"),
    sofr: float = typer.Option(5.25, "--sofr", help="Lãi suất tham chiếu Term SOFR (%/năm)"),
    margin: float = typer.Option(1.75, "--margin", help="Biên độ ngân hàng (%/năm)"),
    discrepancy_fee: float = typer.Option(85.0, "--fee", help="Phí chứng từ bất hợp lệ bị khấu trừ (USD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán tiền chiết khấu hối phiếu L/C trả chậm (Usance Discounting ACT/360)."""
    res = TradeFinanceLCEngine.calculate_usance_discount(
        lc_reference=lc_ref,
        draft_amount_usd=draft_amount,
        tenor_days=tenor,
        benchmark_rate_pct=sofr,
        spread_margin_pct=margin,
        discrepancy_fee_usd=discrepancy_fee,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title=f"💰 TÍNH CHIẾT KHẤU HỐI PHIẾU L/C ({res.lc_reference})", box=box.ROUNDED)
    table.add_column("Chỉ số Chiết khấu", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")

    table.add_row("Trị giá Hối phiếu", f"${res.draft_amount_usd:,.2f} USD")
    table.add_row("Thời hạn thanh toán", f"{res.tenor_days} ngày (ACT/360)")
    table.add_row("Lãi suất All-in", f"{res.all_in_discount_rate_pct:.2f}% (SOFR {res.benchmark_rate_pct:.2f}% + Spread {res.spread_margin_pct:.2f}%)")
    table.add_row("Tiền lãi chiết khấu khấu trừ", f"${res.discount_charge_usd:,.2f} USD")
    table.add_row("Phí sai biệt chứng từ", f"${res.discrepancy_deduction_usd:,.2f} USD")
    table.add_section()
    table.add_row("[bold green]Thực nhận ròng (USD)[/bold green]", f"[bold green]${res.net_proceeds_usd:,.2f} USD[/bold green]")
    table.add_row("Quy đổi tương đương (VND)", f"{res.net_proceeds_vnd:,.0f} VND (Tỷ giá: {res.fx_rate_usd_vnd:,.0f})")

    console.print(table)


@tradefinance_app.command("mkt")
def tradefinance_mkt(
    batch_id: str = typer.Option("VAX-2026-0914", "--batch", help="Mã số lô hàng sinh phẩm / vaccine"),
    temps: str = typer.Option("4.2,4.5,5.1,5.8,6.2,4.8,3.9,4.4", "--temps", "-t", help="Dữ liệu nhiệt độ đo định kỳ (°C), phân cách dấu phẩy"),
    storage_class: str = typer.Option("COLD_CHAIN", "--class", "-c", help="Loại bảo quản (COLD_CHAIN: +2 to +8°C, DEEP_FROZEN, CONTROLLED_ROOM_TEMP)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán Nhiệt độ Động học Trung bình (Arrhenius MKT) theo chuẩn Dược điển USP <1079>."""
    temp_list = [float(x.strip()) for x in temps.split(",") if x.strip()]
    try:
        class_enum = PharmaStorageClass[storage_class.upper()]
    except KeyError:
        class_enum = PharmaStorageClass.COLD_CHAIN

    res = ColdChainPharmaGDPEngine.calculate_mkt(
        batch_id=batch_id,
        temperatures_celsius=temp_list,
        storage_class=class_enum,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="❄️ PHÂN TÍCH NHIỆT ĐỘ ĐỘNG HỌC MKT (USP <1079> & TT 02/2018)", box=box.ROUNDED)
    table.add_column("Thông số", style="cyan")
    table.add_column("Giá trị", style="magenta", justify="right")

    table.add_row("Mã số Lô hàng", res.batch_id)
    table.add_row("Số lượng mẫu đo", f"{res.sample_count} điểm")
    table.add_row("Nhiệt độ Thấp nhất / Cao nhất", f"{res.min_temp_c:.1f}°C / {res.max_temp_c:.1f}°C")
    table.add_row("Trung bình số học (Arithmetic)", f"{res.arithmetic_mean_c:.2f}°C")
    table.add_row("Năng lượng kích hoạt (Arrhenius ΔH)", f"{res.activation_energy_kj_mol} kJ/mol")
    table.add_section()
    table.add_row("[bold cyan]Nhiệt độ Động học (MKT)[/bold cyan]", f"[bold cyan]{res.mkt_celsius:.2f}°C[/bold cyan]")
    table.add_row("Quyết định Đảm bảo Chất lượng", f"[bold]{res.disposition.value}[/bold]")

    console.print(table)


@tradefinance_app.command("coldchain")
def tradefinance_coldchain(
    shipment_id: str = typer.Option("SHP-COLD-8812", "--id", help="Mã lô hàng vận tải lạnh"),
    transit_hours: float = typer.Option(48.0, "--transit-hours", help="Tổng thời gian vận chuyển (giờ)"),
    excursion_hours: float = typer.Option(0.0, "--excursion-hours", help="Tổng số giờ nhiệt độ vượt ngưỡng cho phép"),
    peak_temp: float = typer.Option(6.5, "--peak-temp", help="Nhiệt độ đỉnh cao nhất ghi nhận (°C)"),
    min_temp: float = typer.Option(2.5, "--min-temp", help="Nhiệt độ thấp nhất ghi nhận (°C)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá toàn vẹn chuỗi lạnh Dược phẩm và lệnh Biệt trữ theo Thông tư 02/2018/TT-BYT."""
    events: List[TemperatureExcursionEvent] = []
    if excursion_hours > 0:
        delta = max(0.0, peak_temp - 8.0)
        events.append(
            TemperatureExcursionEvent(
                start_time_iso="2026-10-05T12:00:00",
                duration_hours=excursion_hours,
                peak_temp_c=peak_temp,
                delta_over_limit_c=delta,
            )
        )
    if min_temp < 0.0:
        events.append(
            TemperatureExcursionEvent(
                start_time_iso="2026-10-05T18:00:00",
                duration_hours=1.0,
                peak_temp_c=min_temp,
                delta_over_limit_c=abs(min_temp),
            )
        )

    res = ColdChainPharmaGDPEngine.assess_cold_chain_excursions(
        shipment_id=shipment_id,
        storage_class=PharmaStorageClass.COLD_CHAIN,
        total_transit_hours=transit_hours,
        excursion_events=events,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="🏥 GIÁM SÁT CHUỖI LẠNH GDP DƯỢC PHẨM (TT 02/2018/TT-BYT)", box=box.ROUNDED)
    table.add_column("Chỉ số Đánh giá", style="cyan")
    table.add_column("Kết quả", style="magenta", justify="right")

    table.add_row("Mã Chuyến hàng", res.shipment_id)
    table.add_row("Thời gian Vận chuyển", f"{res.total_transit_hours:.1f} giờ")
    table.add_row("Thời gian Vượt ngưỡng", f"{res.cumulative_excursion_hours:.1f} giờ")
    table.add_row("Tải nhiệt tích lũy (Degree-Hours)", f"{res.severity_degree_hours:.1f} °C·h")
    table.add_row("Sự cố đông đá (Freeze Breach < 0°C)", "[bold red]CÓ BIẾN CỐ[/bold red]" if res.freeze_violation else "[bold green]KHÔNG[/bold green]")
    table.add_section()
    table.add_row("Trạng thái Xuất xưởng", f"[bold]{res.disposition.value}[/bold]")

    console.print(table)
    if res.quarantine_hold_rationale:
        console.print(Panel(f"[bold red]CĂN CỨ BIỆT TRỮ / ĐIỀU TRA:[/bold red] {res.quarantine_hold_rationale}", border_style="red"))


@tradefinance_app.command("carbon")
def tradefinance_carbon(
    route_id: str = typer.Option("RT-SGN-HPH", "--route", help="Mã lộ trình vận tải"),
    weight_tonnes: float = typer.Option(24.0, "--weight", "-w", help="Khối lượng hàng hóa (tấn)"),
    ocean_km: float = typer.Option(1500.0, "--ocean-km", help="Khoảng cách tàu biển container (km)"),
    barge_km: float = typer.Option(120.0, "--barge-km", help="Khoảng cách xà lan thủy nội địa (km)"),
    truck_km: float = typer.Option(60.0, "--truck-km", help="Khoảng cách xe đầu kéo container (km)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm kê phát thải KNK vận tải đa phương thức theo chuẩn ISO 14083 / GLEC v3.0."""
    legs = []
    if ocean_km > 0:
        legs.append(("Chặng Đường biển Feeder", FreightTransportMode.FEEDER_VESSEL, ocean_km))
    if barge_km > 0:
        legs.append(("Chặng Xà lan Mekong", FreightTransportMode.INLAND_WATERWAY_BARGE, barge_km))
    if truck_km > 0:
        legs.append(("Chặng Xe tải Kéo Cảng", FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4, truck_km))

    res = FreightCarbonAccountingEngine.calculate_multimodal_emissions(
        route_id=route_id,
        cargo_weight_tonnes=weight_tonnes,
        legs_data=legs,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="🌱 KIỂM KÊ KHÍ NHÀ KÍNH VẬN TẢI (ISO 14083 & GLEC v3.0)", box=box.ROUNDED)
    table.add_column("Chặng Vận tải / Phương thức", style="cyan")
    table.add_column("Cự ly", style="yellow", justify="right")
    table.add_column("Phát thải CO2e", style="magenta", justify="right")

    for leg in res.legs:
        table.add_row(f"{leg.leg_name} ({leg.mode.value})", f"{leg.distance_km:.1f} km", f"{leg.emissions_kg_co2e:,.1f} kg")

    table.add_section()
    table.add_row("[bold green]TỔNG PHÁT THẢI (WTW)[/bold green]", f"{res.total_distance_km:.1f} km", f"[bold green]{res.total_emissions_t_co2e:.3f} tCO2e[/bold green]")
    table.add_row("Cường độ Carbon Trung bình", "", f"{res.average_intensity_g_per_tkm:.1f} gCO2e/t·km")
    table.add_row("Chi phí Bù trừ Tín chỉ (NĐ 06/2022)", "", f"{res.offset_cost_vnd:,.0f} VND")

    console.print(table)


@tradefinance_app.command("modal-shift")
def tradefinance_modal_shift(
    origin: str = typer.Option("Bình Dương", "--from", help="Điểm xuất phát"),
    destination: str = typer.Option("Cái Mép", "--to", help="Điểm đến"),
    weight_tonnes: float = typer.Option(100.0, "--weight", "-w", help="Khối lượng hàng hóa (tấn)"),
    road_km: float = typer.Option(95.0, "--road-km", help="Cự ly đường bộ toàn tuyến (km)"),
    barge_km: float = typer.Option(85.0, "--barge-km", help="Cự ly xà lan đường thủy (km)"),
    drayage_km: float = typer.Option(15.0, "--drayage-km", help="Cự ly trung chuyển đầu cuối (km)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tối ưu hóa chuyển đổi xanh: Đánh giá tỷ lệ giảm CO2e khi chuyển từ Đường bộ sang Xà lan."""
    intermodal_legs = [
        ("Trung chuyển đường bộ", FreightTransportMode.DIESEL_HEAVY_TRUCK_EURO4, drayage_km),
        ("Vận chuyển xà lan", FreightTransportMode.INLAND_WATERWAY_BARGE, barge_km),
    ]

    res = FreightCarbonAccountingEngine.evaluate_modal_shift(
        origin=origin,
        destination=destination,
        cargo_weight_tonnes=weight_tonnes,
        road_distance_km=road_km,
        intermodal_legs=intermodal_legs,
    )

    if json_mode:
        console.print_json(json.dumps(res.to_dict(), ensure_ascii=False))
        return

    table = Table(title="🔄 TỐI ƯU HÓA CHUYỂN ĐỔI PHƯƠNG THỨC XANH (MODAL SHIFT)", box=box.ROUNDED)
    table.add_column("Phương thức So sánh", style="cyan")
    table.add_column("Phát thải / Chuyến", style="magenta", justify="right")

    table.add_row("Đường bộ Thuần túy (Truck Baseline)", f"{res.baseline_road_emissions_t_co2e:.3f} tCO2e")
    table.add_row("Đa phương thức (Đường bộ + Xà lan)", f"{res.intermodal_emissions_t_co2e:.3f} tCO2e")
    table.add_section()
    table.add_row("[bold green]Lượng Giảm Phát thải[/bold green]", f"[bold green]{res.emissions_saved_t_co2e:.3f} tCO2e ({res.reduction_percentage:.1f}%)[/bold green]")
    table.add_row("Tiết kiệm Chi phí Tín chỉ Carbon/năm", f"{res.annual_cost_savings_offset_vnd:,.0f} VND")

    console.print(table)
    console.print(Panel(f"[bold green]KHUYẾN NGHỊ DECARBONIZATION:[/bold green] {res.green_recommendation}", border_style="green"))
