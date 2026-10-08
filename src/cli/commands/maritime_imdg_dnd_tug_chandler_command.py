"""CLI Commands for IMDG Segregation, Container D&D, Tugboat Dispatch & Ship Chandler.

Phases 307-310 Simplest Viable Maritime Operational Suite.
"""

import typer
from typing import List

from src.core.maritime_imdg_dnd_tug_chandler_engine import (
    ImdgClass, SegregationLevel, ImdgSegregationEngine,
    ContainerType, DndCalculationInput, ContainerDndEngine,
    TugboatAsset, TugboatDispatchEngine,
    ChandlerItem, ShipChandlerEngine
)

# Typer Command Groups
imdg_app = typer.Typer(help="IMDG Code General Segregation Table 7.2.4 (Phase 307)")
dnd_app = typer.Typer(help="Container Demurrage & Detention Tiered Calculator (Phase 308)")
tug_dispatch_app = typer.Typer(help="Tugboat Quota & Port Dispatch Assigner (Phase 309)")
chandler_app = typer.Typer(help="Ship Chandler Provision Multi-Currency Quotation (Phase 310)")


# ------------------------------------------------------------------------------
# Phase 307: IMDG Segregation Command
# ------------------------------------------------------------------------------
@imdg_app.command("check-segregation")
def check_imdg_segregation(
    class_a: str = typer.Option("3", "--ca", help="Nhóm nguy hại Class A (ví dụ: 3, 5.1, 8, 1.1)"),
    class_b: str = typer.Option("5.1", "--cb", help="Nhóm nguy hại Class B (ví dụ: 3, 5.1, 8, 1.1)"),
    acid_base: bool = typer.Option(False, "--acid-base", help="Xung đột Axít vs Kiềm (cho Class 8)")
):
    """Kiểm tra quy chuẩn phân cách an toàn hàng nguy hiểm theo Bảng 7.2.4 IMDG Code."""
    res = ImdgSegregationEngine.evaluate_segregation(class_a, class_b, acid_base)

    typer.echo("================================================================================")
    typer.echo("IMDG CODE: MA TRẬN PHÂN CÁCH HÀNG NGUY HIỂM (BẢNG 7.2.4)")
    typer.echo("================================================================================")
    typer.echo(f"Cặp chất kiểm tra: Class {res.class_a} <---> Class {res.class_b}")
    typer.echo(f"Mức độ phân cách: Cấp {res.segregation_level} ({res.segregation_label})")
    typer.echo("-" * 80)
    typer.echo(f"Cho phép xếp gần: {'CÓ (COMPATIBLE)' if res.is_compatible else 'KHÔNG (INCOMPATIBLE - CẦN CÁCH LY)'}")
    typer.echo(f"Chi tiết quy định: {res.remarks}")
    typer.echo(f"Mã tra cứu: {res.audit_hash}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 308: Container D&D Command
# ------------------------------------------------------------------------------
@dnd_app.command("calc")
def calculate_dnd(
    container: str = typer.Option("TEMU1234567", "--cont", "-c", help="Số container"),
    cont_type: str = typer.Option("DRY_20GP", "--type", "-t", help="Loại cont (DRY_20GP, DRY_40GP, REEFER_20RF, REEFER_40HR)"),
    free_days: int = typer.Option(7, "--free", "-f", help="Số ngày miễn phí (Free days)"),
    used_days: int = typer.Option(12, "--used", "-u", help="Số ngày thực tế sử dụng"),
    is_detention: bool = typer.Option(False, "--detention", help="Tính phí Detention (mặc định Demurrage)")
):
    """Tính cước lưu bãi (Demurrage) hoặc lưu cont (Detention) biểu giá bậc thang."""
    try:
        c_type = ContainerType(cont_type.upper())
    except ValueError:
        c_type = ContainerType.DRY_20GP

    req = DndCalculationInput(
        container_no=container,
        container_type=c_type,
        free_days_allowed=free_days,
        actual_days_used=used_days,
        is_detention=is_detention
    )
    res = ContainerDndEngine.calculate_dnd(req)

    typer.echo("================================================================================")
    typer.echo(f"TÍNH PHÍ CONTAINER BẬC THANG: {res.charge_type}")
    typer.echo("================================================================================")
    typer.echo(f"Container: {res.container_no} ({c_type.value})")
    typer.echo(f"Thời gian: {used_days} ngày thực tế / {free_days} ngày miễn phí -> Quá hạn: {res.overdue_days} ngày")
    typer.echo("-" * 80)
    typer.echo(f"Tiền cước chưa thuế: ${res.subtotal_usd:,.2f} USD")
    typer.echo(f"Thuế GTGT (VAT 8%): ${res.vat_usd:,.2f} USD")
    typer.echo(f"TỔNG THANH TOÁN: ${res.total_amount_usd:,.2f} USD")
    typer.echo(f"Ghi chú: {res.remarks}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 309: Tugboat Dispatch Command
# ------------------------------------------------------------------------------
@tug_dispatch_app.command("dispatch")
def dispatch_tugboat(
    vessel: str = typer.Option("MV MEKONG PHOENIX", "--vessel", "-v", help="Tên tàu biển cập cảng"),
    loa: float = typer.Option(165.0, "--loa", help="Chiều dài lớn nhất LOA (m)"),
    grt: float = typer.Option(25000.0, "--grt", help="Dung tích toàn phần GRT")
):
    """Kiểm tra định mức Cảng vụ & tự động điều động tàu lai từ đội tàu trực ca."""
    fleet = [
        TugboatAsset("T1", "TÀU KÉO SÀI GÒN 01", bhp=4000, bollard_pull_mt=50.0, is_idle=True),
        TugboatAsset("T2", "TÀU KÉO SÀI GÒN 02", bhp=3600, bollard_pull_mt=45.0, is_idle=True),
        TugboatAsset("T3", "TÀU KÉO TÂN CẢNG 09", bhp=2500, bollard_pull_mt=30.0, is_idle=True),
        TugboatAsset("T4", "TÀU KÉO VŨNG TÀU 05", bhp=1200, bollard_pull_mt=15.0, is_idle=False),
    ]
    res = TugboatDispatchEngine.evaluate_and_dispatch(vessel, loa, grt, fleet)

    typer.echo("================================================================================")
    typer.echo("ĐỊNH MỨC CẢNG VỤ & ĐIỀU ĐỘNG TÀU LAI DẮT (TUGBOAT DISPATCH)")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} | LOA: {loa}m | GRT: {grt:,.0f}")
    typer.echo(f"Quy chuẩn yêu cầu: {res.required_tug_count} tàu lai (Công suất >= {res.required_min_bhp} BHP)")
    typer.echo("-" * 80)
    typer.echo(f"Trạng thái điều phối: {'THÀNH CÔNG' if res.is_dispatched else 'KHÔNG ĐỦ TÀU KHẢ DỤNG'}")
    if res.assigned_tugs:
        typer.echo(f"Tàu lai được chỉ định: {', '.join(res.assigned_tugs)}")
    typer.echo(f"Dự toán cước lai dắt: {res.estimated_cost_vnd:,.0f} VND")
    typer.echo(f"Ghi chú: {res.remarks}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 310: Ship Chandler Provision Command
# ------------------------------------------------------------------------------
@chandler_app.command("quote")
def quote_provision(
    vessel: str = typer.Option("MV OCEAN TRADER", "--vessel", "-v", help="Tên tàu đặt hàng"),
    rfq: str = typer.Option("RFQ-2026-99", "--rfq", help="Mã yêu cầu báo giá RFQ"),
    margin: float = typer.Option(0.25, "--margin", "-m", help="Tỷ lệ biên lợi nhuận mong muốn (0.25 = 25%)"),
    launch_fee: float = typer.Option(150.0, "--launch", help="Phí cano ra phao neo (USD)")
):
    """Lập báo giá cung ứng vật tư, thực phẩm tàu biển đa ngoại tệ (USD & VND)."""
    items = [
        ChandlerItem("IMPA-150101", "Thịt bò đông lạnh (Ribeye)", "KG", 80.0, 14.5),
        ChandlerItem("IMPA-150402", "Rau củ tươi Đà Lạt", "KG", 150.0, 2.0),
        ChandlerItem("IMPA-170201", "Gia vị & đồ khô nhà bếp", "LOT", 1.0, 250.0),
        ChandlerItem("IMPA-232115", "Vật tư vệ sinh boong tàu", "PKG", 5.0, 45.0)
    ]
    res = ShipChandlerEngine.calculate_quotation(
        rfq_id=rfq,
        vessel_name=vessel,
        items=items,
        markup_ratio=margin,
        launch_boat_fee_usd=launch_fee,
        exchange_rate_usd_vnd=25400.0
    )

    typer.echo("================================================================================")
    typer.echo("BÁO GIÁ CUNG ỨNG TÀU BIỂN (SHIP CHANDLER PROVISION QUOTATION)")
    typer.echo("================================================================================")
    typer.echo(f"Đơn hàng: {rfq} | Tàu: {vessel} | Số mặt hàng: {res.line_items_count}")
    typer.echo(f"Tổng giá vốn hàng hóa + Vận chuyển ca-nô: ${res.total_cost_usd:,.2f} USD")
    typer.echo("-" * 80)
    typer.echo(f"GIÁ BÁO CHÍNH THỨC (USD): ${res.total_revenue_usd:,.2f} USD")
    typer.echo(f"GIÁ BÁO QUY ĐỔI (VND): {res.total_revenue_vnd:,.0f} VND (Tỷ giá: {res.exchange_rate:,.0f})")
    typer.echo(f"Lợi nhuận gộp dự kiến: ${res.gross_profit_usd:,.2f} USD (Biên LN: {res.margin_percentage:.1f}%)")
    typer.echo("================================================================================")
