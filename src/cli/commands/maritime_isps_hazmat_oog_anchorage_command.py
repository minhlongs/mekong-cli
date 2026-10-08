"""CLI Commands for ISPS Security, Hazmat Waste, OOG Stevedoring & Anchorage Booking Suite.

Phases 299-302 Simplest Viable Maritime Operational Suite.
"""

import typer
from typing import List

from src.core.maritime_isps_hazmat_oog_anchorage_engine import (
    SecurityLevel,
    DeclarationOfSecurity,
    MaritimeIspsEngine,
    WasteType,
    HazmatWasteManifest,
    HazmatWasteEngine,
    OogCargoDimensions,
    OogStevedoringEngine,
    AnchorageBooking,
    AnchorageBookingEngine,
)

# Typer Command Groups
isps_app = typer.Typer(help="ISPS Code Port Security & DoS Engine (Phase 299)")
hazmat_app = typer.Typer(help="Hazmat Waste Port Clearance Engine (Phase 300)")
oog_stevedore_app = typer.Typer(help="OOG Stevedoring & Overtime Tariffs Engine (Phase 301)")
anchorage_app = typer.Typer(help="Anchorage Zone Capacity Booking Engine (Phase 302)")


# ------------------------------------------------------------------------------
# Phase 299: ISPS Security Command
# ------------------------------------------------------------------------------
@isps_app.command("check-clearance")
def check_isps_clearance(
    vessel: str = typer.Option("MV MEKONG SECURE", "--vessel", "-v", help="Tên tàu biển"),
    port_level: str = typer.Option("LEVEL_1", "--port", "-p", help="Cấp độ an ninh cảng (LEVEL_1/2/3)"),
    vessel_level: str = typer.Option("LEVEL_1", "--ship", "-s", help="Cấp độ an ninh tàu (LEVEL_1/2/3)"),
    current_time: str = typer.Option("2026-10-09", "--time", "-t", help="Thời điểm kiểm tra (YYYY-MM-DD)")
):
    """Kiểm tra sự đồng bộ Cấp độ An ninh (ISPS Code) giữa Tàu và Cảng trước làm hàng."""
    try:
        p_lvl = SecurityLevel(port_level.upper())
        s_lvl = SecurityLevel(vessel_level.upper())
    except ValueError:
        p_lvl = SecurityLevel.LEVEL_1
        s_lvl = SecurityLevel.LEVEL_1

    dos = DeclarationOfSecurity(
        dos_id="DOS-2026-99",
        vessel_name=vessel,
        port_facility="Cat Lai Terminal",
        ship_security_officer="SSO",
        port_facility_security_officer="PFSO",
        port_security_level=p_lvl,
        vessel_security_level=s_lvl,
        valid_from="2026-10-01",
        valid_until="2026-10-31"
    )
    res = MaritimeIspsEngine.evaluate_dos_clearance(dos, current_time)

    typer.echo("================================================================================")
    typer.echo("ISPS CODE: KIỂM TRA ĐỒNG BỘ CẤP ĐỘ AN NINH TÀU & CẢNG")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} | Thời điểm check: {current_time}")
    typer.echo(f"Giấy chứng nhận (DoS): {dos.dos_id}")
    typer.echo(f"  + Cấp độ tại Cảng: {p_lvl.value}")
    typer.echo(f"  + Cấp độ của Tàu: {s_lvl.value}")
    typer.echo("-" * 80)
    typer.echo(f"Trạng thái cấp phép (Clearance): {'ĐƯỢC PHÉP (CLEARED)' if res.is_cleared else 'BỊ TỪ CHỐI (DENIED)'}")
    typer.echo(f"Ghi chú: {res.remarks}")
    typer.echo(f"Mã tra cứu SHA-256: {res.security_hash}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 300: Hazmat Waste Command
# ------------------------------------------------------------------------------
@hazmat_app.command("port-clearance")
def check_hazmat_clearance(
    vessel: str = typer.Option("MV CHEMICAL", "--vessel", "-v", help="Tên tàu biển"),
    qty: float = typer.Option(5.0, "--qty", "-q", help="Khối lượng rác nguy hại (m3)"),
    receipt: str = typer.Option("", "--receipt", "-r", help="Chứng chỉ Disposal Receipt (Điền OK nếu có)")
):
    """Kiểm tra chứng nhận thu gom rác nguy hại (Hazmat/Medical) để cấp Port Clearance."""
    manifest = HazmatWasteManifest(
        manifest_id="HW-099",
        vessel_name=vessel,
        waste_type=WasteType.IMDG_CHEMICAL,
        quantity_cubic_meters=qty,
        disposal_receipt_id=receipt if receipt else None
    )
    res = HazmatWasteEngine.evaluate_port_clearance([manifest], vessel)

    typer.echo("================================================================================")
    typer.echo("KIỂM SOÁT PORT CLEARANCE DO MÔI TRƯỜNG & RÁC THẢI NGUY HẠI")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} | Khối lượng rác: {qty} m3")
    typer.echo(f"Receipt ID đối tác xử lý: {receipt if receipt else 'CHƯA CÓ / THIẾU'}")
    typer.echo("-" * 80)
    typer.echo(f"Cho phép rời cảng: {'CÓ (CLEARED)' if res.is_cleared_for_departure else 'KHÔNG (DENIED)'}")
    typer.echo(res.remarks)
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 301: OOG Stevedoring Command
# ------------------------------------------------------------------------------
@oog_stevedore_app.command("calc")
def calculate_oog_tariff(
    teu: int = typer.Option(1, "--teu", help="Kích thước cont (1 = 20ft, 2 = 40ft)"),
    w: int = typer.Option(0, "--width", help="Quá khổ chiều rộng (cm)"),
    h: int = typer.Option(0, "--height", help="Quá khổ chiều cao (cm)"),
    l: int = typer.Option(0, "--length", help="Quá khổ chiều dài (cm)"),
    wt: float = typer.Option(20.0, "--weight", help="Trọng lượng (Tấn)"),
    overtime: bool = typer.Option(False, "--overtime", help="Làm ngoài giờ / Lễ")
):
    """Tính cước bốc dỡ cho hàng Siêu Trường / Siêu Trọng (Out-of-Gauge)."""
    dim = OogCargoDimensions(
        container_size_teu=teu,
        over_width_cm=w,
        over_height_cm=h,
        over_length_cm=l,
        gross_weight_mt=wt
    )
    res = OogStevedoringEngine.calculate_tariff(dim, overtime)

    typer.echo("================================================================================")
    typer.echo("CƯỚC BỐC DỠ HÀNG QUÁ KHỔ (OUT-OF-GAUGE TARIFFS)")
    typer.echo("================================================================================")
    typer.echo(f"Kích thước quy đổi: {teu} TEU | Trọng lượng: {wt} Tấn")
    typer.echo(f"Đơn giá cơ bản: {res.base_rate_usd:,.2f} USD")
    typer.echo(f"Hệ số nhân OOG (Lố khổ/Nặng): x{res.oog_multiplier:.2f}")
    if overtime:
        typer.echo(f"Hệ số ngoài giờ: x{res.overtime_multiplier:.2f}")
    typer.echo("-" * 80)
    typer.echo(f"TỔNG CƯỚC THU: {res.final_charge_usd:,.2f} USD")
    typer.echo(f"Ghi chú: {res.remarks}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 302: Anchorage Booking Command
# ------------------------------------------------------------------------------
@anchorage_app.command("book")
def book_anchorage_slot(
    zone: str = typer.Option("Vung Tau OPL", "--zone", help="Khu neo đậu"),
    cap: float = typer.Option(100000.0, "--cap", help="Sức chứa GRT tĩnh của khu neo"),
    vessel: str = typer.Option("MV NEW ARRIVAL", "--vessel", "-v", help="Tên tàu cần book"),
    grt: float = typer.Option(30000.0, "--grt", help="Dung tích GRT của tàu mới"),
    start: str = typer.Option("2026-10-09 10:00", "--start", help="Giờ đến dự kiến (YYYY-MM-DD HH:MM)"),
    end: str = typer.Option("2026-10-09 18:00", "--end", help="Giờ rời dự kiến (YYYY-MM-DD HH:MM)")
):
    """Đăng ký slot tại Phao neo dựa trên tổng dung tích GRT khu vực."""
    existing = [
        AnchorageBooking("B1", "SHIP A", 50000, "2026-10-09 08:00", "2026-10-09 15:00"),
        AnchorageBooking("B2", "SHIP B", 40000, "2026-10-09 13:00", "2026-10-09 20:00")
    ]
    new_book = AnchorageBooking("B3", vessel, grt, start, end)
    res = AnchorageBookingEngine.evaluate_booking(zone, cap, existing, new_book)

    typer.echo("================================================================================")
    typer.echo("QUẢN LÝ SỨC CHỨA KHU NEO ĐẬU (ANCHORAGE BOOKING)")
    typer.echo("================================================================================")
    typer.echo(f"Khu vực: {zone} | Sức chứa an toàn: {cap:,.0f} GRT")
    typer.echo(f"Yêu cầu từ: {vessel} ({grt:,.0f} GRT) trong khung {start} -> {end}")
    typer.echo("-" * 80)
    typer.echo(f"Trạng thái phê duyệt: {'CHẤP NHẬN' if res.is_accepted else 'TỪ CHỐI (VƯỢT TẢI)'}")
    typer.echo(res.remarks)
    typer.echo("================================================================================")
