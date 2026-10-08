"""CLI Commands for MLC Crew, Bunkering, Shore Power, and Customs VASSCM.

Phases 303-306 Simplest Viable Maritime Operational Suite.
"""

import typer
from typing import List

from src.core.maritime_mlc_bunkering_shorepower_customs_engine import (
    CrewRole, CrewMember, MlcCrewEngine,
    BdnInput, BunkeringEngine,
    ShorePowerConnection, ShorePowerEngine,
    ManifestItem, CustomsVasscmEngine
)

# Typer Command Groups
mlc_crew_app = typer.Typer(help="MLC 2006 Crew Clearance & IMO FAL 5 Engine (Phase 303)")
bunkering_app = typer.Typer(help="Bunkering BDN Calculation & Tax Engine (Phase 304)")
shore_power_app = typer.Typer(help="Shore Power (Cold Ironing) Billing Engine (Phase 305)")
vasscm_customs_app = typer.Typer(help="Customs VASSCM Simple Data Adapter (Phase 306)")

# ------------------------------------------------------------------------------
# Phase 303: MLC Crew Clearance Command
# ------------------------------------------------------------------------------
@mlc_crew_app.command("crew-clear")
def check_crew_clearance(
    vessel: str = typer.Option("MV OCEAN", "--vessel", "-v", help="Tên tàu biển"),
    date: str = typer.Option("2026-10-08", "--date", "-d", help="Ngày kiểm tra (YYYY-MM-DD)")
):
    """Kiểm tra hợp đồng và chứng nhận y tế của Thuyền viên (MLC 2006) để cấp IMO FAL 5."""
    crew_list = [
        CrewMember("C1", "Nguyễn Văn A", CrewRole.CAPTAIN, "VN", "2026-12-31", True),
        CrewMember("C2", "Trần Thị B", CrewRole.OFFICER, "VN", "2027-01-15", True),
        CrewMember("C3", "Lê Văn C", CrewRole.RATING, "VN", "2025-10-01", True), # Hết hạn y tế
    ]
    res = MlcCrewEngine.evaluate_clearance(vessel, crew_list, date)

    typer.echo("================================================================================")
    typer.echo("MLC 2006: KIỂM SOÁT THUYỀN VIÊN & CẤP PHÉP IMO FAL FORM 5")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} | Ngày kiểm tra: {date}")
    typer.echo(f"Tổng số thuyền viên: {res.total_crew}")
    typer.echo("-" * 80)
    typer.echo(f"Trạng thái: {'ĐẠT (CLEARED)' if res.is_cleared else 'KHÔNG ĐẠT (DENIED)'}")
    typer.echo(f"Ghi chú: {res.remarks}")
    if not res.is_cleared:
        typer.echo(f"Thuyền viên không hợp lệ (ID): {', '.join(res.unfit_crew_ids)}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 304: Bunkering Volume & Tax Command
# ------------------------------------------------------------------------------
@bunkering_app.command("calc-bdn")
def calculate_bdn(
    vessel: str = typer.Option("MV TANKER", "--vessel", "-v", help="Tên tàu nhận dầu"),
    bdn: str = typer.Option("BDN-2026-123", "--bdn", help="Mã BDN"),
    vol: float = typer.Option(1500.0, "--vol", help="Thể tích thực (m3)"),
    den: float = typer.Option(991.0, "--den", help="Tỷ trọng (kg/m3)"),
    temp: float = typer.Option(30.0, "--temp", help="Nhiệt độ (C)"),
    tax: float = typer.Option(1000.0, "--tax", help="Thuế BVMT (VND/MT)")
):
    """Tính toán chuyển đổi Thể tích sang Khối lượng (MT) từ BDN và tính thuế BVMT."""
    bdn_input = BdnInput(
        bdn_id=bdn, vessel_name=vessel, fuel_type="VLSFO",
        volume_cubic_meters=vol, density_kg_m3=den, temperature_celsius=temp,
        env_tax_rate_vnd_per_mt=tax
    )
    res = BunkeringEngine.calculate_bunker_delivery(bdn_input)

    typer.echo("================================================================================")
    typer.echo("CUNG ỨNG DẦU (BUNKERING): TÍNH TOÁN MT & THUẾ BVMT (ASTM BASE)")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} | BDN: {bdn}")
    typer.echo(f"Input: Thể tích = {vol} m3 | Tỷ trọng = {den} | Nhiệt độ = {temp}C")
    typer.echo("-" * 80)
    typer.echo(f"Khối lượng quy đổi: {res.metric_tons:,.2f} MT")
    typer.echo(f"Thuế BVMT phải nộp: {res.env_tax_vnd:,.0f} VND")
    typer.echo(f"Chi tiết: {res.remarks}")
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 305: Shore Power Command
# ------------------------------------------------------------------------------
@shore_power_app.command("calc-power")
def calculate_shore_power(
    vessel: str = typer.Option("MV GREEN", "--vessel", "-v", help="Tên tàu điện"),
    conn: str = typer.Option("SP-K10", "--conn", help="Mã kết nối"),
    start: float = typer.Option(100.0, "--start", help="Chỉ số điện đầu (kWh)"),
    stop: float = typer.Option(500.0, "--stop", help="Chỉ số điện cuối (kWh)"),
    rate: float = typer.Option(0.3, "--rate", help="Đơn giá (USD/kWh)")
):
    """Tính cước sử dụng Điện bờ (Shore Power / Cold Ironing)."""
    sp_input = ShorePowerConnection(conn, vessel, start, stop, rate, connection_fee_usd=50.0)
    res = ShorePowerEngine.calculate_billing(sp_input)

    typer.echo("================================================================================")
    typer.echo("ĐIỆN BỜ (SHORE POWER / COLD IRONING): TÍNH CƯỚC SỬ DỤNG")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} | Điểm kết nối (Conn ID): {conn}")
    typer.echo(f"Chỉ số điện: {start} -> {stop} (kWh) | Đơn giá: ${rate}/kWh")
    typer.echo("-" * 80)
    typer.echo(f"Tổng tiêu thụ: {res.total_kwh:,.1f} kWh")
    typer.echo(f"Tiền điện: ${res.energy_cost_usd:,.2f}")
    typer.echo(f"TỔNG THANH TOÁN (Cộng phí nối): ${res.total_invoice_usd:,.2f}")
    typer.echo(res.remarks)
    typer.echo("================================================================================")


# ------------------------------------------------------------------------------
# Phase 306: Customs VASSCM Adapter Command
# ------------------------------------------------------------------------------
@vasscm_customs_app.command("export-vasscm")
def generate_vasscm(
    vessel: str = typer.Option("MV LOGISTICS", "--vessel", "-v", help="Tên tàu"),
    voyage: str = typer.Option("V001", "--voy", help="Chuyến tàu"),
    port: str = typer.Option("VNVUT", "--port", help="Cảng dỡ hàng (UNLOCODE)"),
    qty: int = typer.Option(2, "--qty", help="Số lượng container mô phỏng")
):
    """Tạo JSON Payload truyền nhận VASSCM (Hải quan) thay vì dùng EDIFACT truyền thống."""
    items = []
    for i in range(qty):
        items.append(ManifestItem(f"BL-{i}", f"CONT{i}123", f"SEAL{i}", 20000.0, "8504"))
        
    res = CustomsVasscmEngine.generate_vasscm_payload(vessel, voyage, port, items)

    typer.echo("================================================================================")
    typer.echo("HẢI QUAN: XUẤT JSON PAYLOAD VASSCM (BỎ QUA EDIFACT)")
    typer.echo("================================================================================")
    typer.echo(f"Tàu: {vessel} (Voyage: {voyage}) | Cảng đích: {port}")
    typer.echo(f"Trạng thái Payload: {'HỢP LỆ' if res.is_valid else 'LỖI'}")
    typer.echo(res.remarks)
    typer.echo("-" * 80)
    typer.echo("PAYLOAD CẮT NHỎ (Preview):")
    preview = res.json_payload[:250] + ("..." if len(res.json_payload) > 250 else "")
    typer.echo(preview)
    typer.echo("================================================================================")

