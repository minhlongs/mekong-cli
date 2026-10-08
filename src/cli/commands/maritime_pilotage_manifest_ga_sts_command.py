"""Typer CLI Commands for Maritime Pilotage Exemption, e-Manifest MLETR, General Average & STS Transshipment.

Phases 235-238:
- Phase 235: mekong pilotagezone check / tariff
- Phase 236: mekong emanifest check / reconcile / token
- Phase 237: mekong generalaverage adjust
- Phase 238: mekong ststransfer energy / evaluate
"""

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.maritime_pilotage_manifest_ga_sts_engine import (
    MaritimePilotageEngine,
    PilotageZoneType,
    VesselTradeClass,
    CargoManifestMletrEngine,
    GeneralAverageAdjustingEngine,
    ShipToShipTransferEngine,
)

console = Console()

pilotagezone_app = typer.Typer(
    name="pilotagezone",
    help="Vùng hoa tiêu bắt buộc, miễn hoa tiêu thuyền trưởng & biểu giá hoa tiêu TT 39/2023 (Phase 235).",
)
emanifest_app = typer.Typer(
    name="emanifest",
    help="Khai báo trước bản lược khai hàng hóa điện tử, e-B/L MLETR & đối soát số lượng dỡ hàng (Phase 236).",
)
generalaverage_app = typer.Typer(
    name="generalaverage",
    help="Phân bổ tổn thất chung (GA), Quy tắc York-Antwerp 2016 & tiền đặt cọc Average Guarantee (Phase 237).",
)
ststransfer_app = typer.Typer(
    name="ststransfer",
    help="Chuyển tải dầu giữa hai tàu (STS), tính năng lượng va chạm & tiêu chuẩn an toàn MARPOL (Phase 238).",
)


# ==============================================================================
# PHASE 235: MARITIME PILOTAGE COMMANDS
# ==============================================================================

@pilotagezone_app.command(name="check")
def check_pilotage(
    gt: float = typer.Option(2500.0, "--gt", help="Tổng dung tích tàu Gross Tonnage (GT)"),
    trade: str = typer.Option("domestic", "--trade", "-t", help="Tuyến vận tải: domestic hoặc international"),
    hazardous: bool = typer.Option(False, "--hazardous", "-h", help="Chở hàng nguy hiểm/dầu khí dạng rời"),
    has_cert: bool = typer.Option(True, "--cert", help="Thuyền trưởng có Giấy chứng nhận khả năng chuyên môn hoa tiêu"),
    calls_12m: int = typer.Option(12, "--calls", help="Số lượt cập cảng trong 12 tháng qua"),
    zone: str = typer.Option("compulsory_inshore", "--zone", "-z", help="Vùng hoa tiêu: compulsory_inshore, compulsory_estuary, optional_anchorage"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra điều kiện bắt buộc hoặc miễn hoa tiêu hàng hải theo Bộ luật Hàng hải 2015."""
    trade_enum = VesselTradeClass.INTERNATIONAL if trade.lower().startswith("inter") else VesselTradeClass.DOMESTIC
    zone_enum = PilotageZoneType.OPTIONAL_ANCHORAGE if "optional" in zone.lower() else (
        PilotageZoneType.COMPULSORY_ESTUARY if "estuary" in zone.lower() else PilotageZoneType.COMPULSORY_INSHORE
    )

    res = MaritimePilotageEngine.check_pilotage_exemption(
        gross_tonnage=gt,
        trade_class=trade_enum,
        is_hazardous_bulk=hazardous,
        master_has_exemption_cert=has_cert,
        port_calls_last_12m=calls_12m,
        zone_type=zone_enum,
    )

    data = {
        "is_exempt": res.is_exempt,
        "requires_pilot": res.requires_pilot,
        "exemption_reason": res.exemption_reason,
        "statutory_notes": res.statutory_notes,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_exempt else "yellow"
    table = Table(title="[bold blue]Kết quả Kiểm tra Miễn Hoa tiêu Hàng hải (BLLHH Điều 248)[/bold blue]")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style=color)
    table.add_row("Miễn hoa tiêu", "CÓ (Đủ điều kiện miễn)" if res.is_exempt else "KHÔNG (Bắt buộc hoa tiêu)")
    table.add_row("Bắt buộc bố trí hoa tiêu", "CÓ" if res.requires_pilot else "KHÔNG")
    table.add_row("Lý do pháp định", res.exemption_reason)
    console.print(table)


@pilotagezone_app.command(name="tariff")
def calculate_pilotage_tariff(
    gt: float = typer.Option(15000.0, "--gt", help="Tổng dung tích tàu Gross Tonnage"),
    trade: str = typer.Option("international", "--trade", "-t", help="Tuyến vận tải: domestic hoặc international"),
    distance: float = typer.Option(15.0, "--distance", "-d", help="Cự ly dẫn tàu (hải lý NM)"),
    wait_hours: float = typer.Option(2.5, "--wait", "-w", help="Thời gian hoa tiêu chờ tại tàu (giờ)"),
    cancel_hours: Optional[float] = typer.Option(None, "--cancel", help="Thời gian báo hủy trước giờ đón (giờ)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Tính giá dịch vụ hoa tiêu hàng hải & phí chờ theo Thông tư 39/2023/TT-BGTVT."""
    trade_enum = VesselTradeClass.INTERNATIONAL if trade.lower().startswith("inter") else VesselTradeClass.DOMESTIC

    res = MaritimePilotageEngine.calculate_pilotage_tariff(
        gross_tonnage=gt,
        trade_class=trade_enum,
        distance_nautical_miles=distance,
        idle_wait_hours=wait_hours,
        cancellation_notice_hours=cancel_hours,
    )

    data = {
        "base_tariff": res.base_tariff,
        "wait_hours": res.wait_hours,
        "standby_detention_fee": res.standby_detention_fee,
        "cancellation_penalty": res.cancellation_penalty,
        "total_tariff": res.total_tariff,
        "currency": res.currency,
        "audit_hash": res.audit_hash,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold green]Biểu giá Dịch vụ Hoa tiêu Hàng hải (TT 39/2023)[/bold green]")
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị", style="magenta")
    table.add_row("Giá hoa tiêu cơ sở", f"{res.base_tariff:,.2f} {res.currency}")
    table.add_row("Phí hoa tiêu chờ tàu", f"{res.standby_detention_fee:,.2f} {res.currency} ({res.wait_hours}h)")
    table.add_row("Phạt hủy dịch vụ muộn", f"{res.cancellation_penalty:,.2f} {res.currency}")
    table.add_row("[bold]Tổng giá hoa tiêu[/bold]", f"[bold green]{res.total_tariff:,.2f} {res.currency}[/bold green]")
    table.add_row("Mã băm kiểm toán", res.audit_hash)
    console.print(table)


# ==============================================================================
# PHASE 236: E-MANIFEST & MLETR COMMANDS
# ==============================================================================

@emanifest_app.command(name="check")
def check_manifest(
    hours_prior: float = typer.Option(26.0, "--hours", "-h", help="Thời gian nộp trước giờ dự kiến đến cảng (giờ)"),
    short_sea: bool = typer.Option(False, "--short-sea", "-s", help="Tuyến vận tải biển ngắn (< 500 NM)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Kiểm tra thời hạn khai bản lược khai hàng hóa điện tử trước khi tàu đến cảng."""
    res = CargoManifestMletrEngine.check_advance_manifest(
        hours_before_arrival=hours_prior,
        is_short_sea_shipping=short_sea,
    )
    data = {
        "is_compliant": res.is_compliant,
        "status": res.status.value,
        "hours_prior": res.hours_prior,
        "required_hours": res.required_hours,
        "statutory_notes": res.statutory_notes,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_compliant else "red"
    console.print(Panel(
        f"[bold {color}]Trạng thái: {res.status.value.upper()}[/bold {color}]\n"
        f"Thời gian nộp: {res.hours_prior:.1f}h (Yêu cầu: >= {res.required_hours:.1f}h)\n"
        + "\n".join(f"- {n}" for n in res.statutory_notes),
        title="Kiểm tra e-Manifest Quốc gia Một cửa (NĐ 58/2017)",
    ))


@emanifest_app.command(name="reconcile")
def reconcile_tally(
    manifest_qty: float = typer.Option(5000.0, "--manifest", "-m", help="Số lượng hàng ghi trên e-Manifest (tấn/kiện)"),
    tally_qty: float = typer.Option(4980.0, "--tally", "-t", help="Số lượng hàng thực tế kiểm đếm dỡ xuống (tấn/kiện)"),
    tolerance: float = typer.Option(0.5, "--tolerance", help="Dung sai miễn khai sửa đổi hải quan (%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Đối soát số lượng kiểm đếm dỡ hàng so với bản lược khai hàng hải (TT 39/2018/TT-BTC)."""
    res = CargoManifestMletrEngine.reconcile_manifest_vs_tally(
        manifest_qty=manifest_qty,
        tally_qty=tally_qty,
        customs_tolerance_pct=tolerance,
    )
    data = {
        "is_matched": res.is_matched,
        "manifest_qty": res.manifest_qty,
        "tally_qty": res.tally_qty,
        "discrepancy_qty": res.discrepancy_qty,
        "discrepancy_pct": res.discrepancy_pct,
        "discrepancy_type": res.discrepancy_type.value,
        "requires_customs_amendment": res.requires_customs_amendment,
        "statutory_warning": res.statutory_warning,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold cyan]Đối soát Kiểm đếm Dỡ hàng Hải quan[/bold cyan]")
    table.add_column("Chỉ tiêu", style="cyan")
    table.add_column("Giá trị", style="white")
    table.add_row("Khối lượng Manifest", f"{res.manifest_qty:,.2f}")
    table.add_row("Khối lượng Kiểm đếm (Tally)", f"{res.tally_qty:,.2f}")
    table.add_row("Chênh lệch", f"{res.discrepancy_qty:,.2f} ({res.discrepancy_pct:.2f}%) [{res.discrepancy_type.value}]")
    table.add_row("Cần khai báo sửa đổi", "[bold red]CÓ[/bold red]" if res.requires_customs_amendment else "[bold green]KHÔNG[/bold green]")
    console.print(table)


@emanifest_app.command(name="token")
def issue_mletr_ebl(
    bl: str = typer.Option("BL-MEKONG-2026-001", "--bl", help="Số vận đơn B/L"),
    carrier: str = typer.Option("Mekong Shipping Line", "--carrier", help="Hãng tàu vận chuyển"),
    shipper: str = typer.Option("Saigon Export Corp", "--shipper", help="Người gửi hàng"),
    consignee: str = typer.Option("To Order", "--consignee", help="Người nhận hàng theo lệnh"),
    holder: str = typer.Option("Vietcombank Hochiminh Branch", "--holder", help="Người nắm giữ quyền kiểm soát hiện tại"),
    prev_hash: str = typer.Option("0" * 64, "--prev", help="Băm khối trước đó"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Phát hành hoặc chuyển quyền kiểm soát vận đơn điện tử e-B/L theo UNCITRAL MLETR."""
    rec = CargoManifestMletrEngine.issue_or_transfer_mletr_ebl(
        bl_number=bl,
        carrier=carrier,
        shipper=shipper,
        consignee=consignee,
        new_holder=holder,
        previous_token=prev_hash,
    )
    data = {
        "bl_number": rec.bl_number,
        "carrier": rec.carrier,
        "shipper": rec.shipper,
        "consignee": rec.consignee,
        "current_holder": rec.current_holder,
        "is_valid_transfer": rec.is_valid_transfer,
        "mletr_token": rec.mletr_token,
        "previous_hash": rec.previous_hash,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    console.print(Panel(
        f"[bold green]e-B/L MLETR Token đã xác thực thành công[/bold green]\n"
        f"Vận đơn: {rec.bl_number}\n"
        f"Chủ thể kiểm soát: {rec.current_holder}\n"
        f"Chữ ký số kiểm soát: [yellow]{rec.mletr_token}[/yellow]",
        title="UNCITRAL MLETR Electronic Bill of Lading",
    ))


# ==============================================================================
# PHASE 237: GENERAL AVERAGE (GA) COMMANDS
# ==============================================================================

@generalaverage_app.command(name="adjust")
def adjust_general_average(
    ship_sound: float = typer.Option(20000000.0, "--ship", help="Giá trị nguyên vẹn của tàu ($)"),
    ship_damage: float = typer.Option(500000.0, "--ship-damage", help="Tổn thất riêng của tàu ($)"),
    cargo_cif: float = typer.Option(30000000.0, "--cargo", help="Giá trị CIF hàng hóa ($)"),
    cargo_loss: float = typer.Option(200000.0, "--cargo-loss", help="Tổn thất riêng hàng hóa ($)"),
    freight: float = typer.Option(1000000.0, "--freight", help="Cước vận chuyển chịu rủi ro ($)"),
    ga_sacrifice: float = typer.Option(800000.0, "--sacrifice", help="Hy sinh tổn thất chung ($)"),
    ga_cash: float = typer.Option(400000.0, "--cash", help="Chi phí chi bằng tiền mặt ($)"),
    days: int = typer.Option(180, "--days", help="Số ngày tính lãi suất YAR 2016 Rule XXI"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Tính toán phân bổ tổn thất chung (General Average) theo Quy tắc York-Antwerp 2016."""
    cv = GeneralAverageAdjustingEngine.calculate_contributory_values(
        ship_sound_value=ship_sound,
        ship_non_ga_damage=ship_damage,
        cargo_cif_value=cargo_cif,
        cargo_damage_loss=cargo_loss,
        cargo_landing_charges=0.0,
        freight_at_risk=freight,
        freight_post_ga_expenses=0.0,
    )

    res = GeneralAverageAdjustingEngine.adjust_general_average(
        ga_sacrifices=ga_sacrifice,
        ga_cash_disbursements=ga_cash,
        contributory_values=cv,
        adjustment_days=days,
    )

    data = {
        "contributory_values": {
            "ship": cv.ship_value,
            "cargo": cv.cargo_value,
            "freight": cv.freight_value,
            "total": cv.total_contributory_value,
        },
        "ga_rate_pct": res.ga_rate_pct,
        "ship_contribution": res.ship_contribution,
        "cargo_contribution": res.cargo_contribution,
        "freight_contribution": res.freight_contribution,
        "cash_deposit_required": res.cash_deposit_required,
        "commission_allowance": res.commission_allowance,
        "interest_allowance": res.interest_allowance,
        "adjustment_hash": res.adjustment_hash,
    }

    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold red]Bản Tính Phân Bổ Tổn Thất Chung (York-Antwerp Rules 2016)[/bold red]")
    table.add_column("Hạng mục", style="cyan")
    table.add_column("Giá trị ($)", style="yellow")
    table.add_row("Tổng giá trị đóng góp (CV)", f"${cv.total_contributory_value:,.2f}")
    table.add_row("Tỷ lệ đóng góp GA", f"{res.ga_rate_pct:.4f}%")
    table.add_row("Đóng góp của Tàu", f"${res.ship_contribution:,.2f}")
    table.add_row("Đóng góp của Hàng", f"${res.cargo_contribution:,.2f}")
    table.add_row("Đóng góp của Cước", f"${res.freight_contribution:,.2f}")
    table.add_row("Hoa hồng chi tiền (2% Rule XX)", f"${res.commission_allowance:,.2f}")
    table.add_row("Lãi suất 7%/năm (Rule XXI)", f"${res.interest_allowance:,.2f}")
    table.add_row("[bold]Tiền bảo đảm đặt cọc (Average Guarantee)[/bold]", f"[bold green]${res.cash_deposit_required:,.2f}[/bold green]")
    table.add_row("Mã chứng thư GA", res.adjustment_hash)
    console.print(table)


# ==============================================================================
# PHASE 238: SHIP-TO-SHIP (STS) COMMANDS
# ==============================================================================

@ststransfer_app.command(name="energy")
def calculate_sts_energy(
    displacement: float = typer.Option(80000.0, "--displacement", "-m", help="Lượng giãn nước tàu cặp mạn (tấn)"),
    draft: float = typer.Option(12.5, "--draft", "-d", help="Mớn nước tàu cặp mạn (mét)"),
    beam: float = typer.Option(32.2, "--beam", "-b", help="Chiều rộng tàu (mét)"),
    velocity: float = typer.Option(0.15, "--velocity", "-v", help="Vận tốc tiếp cận (m/s)"),
    fender_energy: float = typer.Option(350.0, "--fender-energy", help="Năng lượng hấp thụ định mức của đệm khí (kNm)"),
    standoff: float = typer.Option(3.5, "--standoff", help="Khoảng cách cách ly đệm va (mét)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Tính toán động năng tiếp cận va chạm cặp mạn STS & kiểm tra thông số đệm khí Yokohoma."""
    res = ShipToShipTransferEngine.calculate_berthing_energy(
        displacement_tonnes=displacement,
        draft_meters=draft,
        beam_meters=beam,
        approach_velocity_mps=velocity,
        fender_rated_energy_kNm=fender_energy,
        fender_standoff_distance_meters=standoff,
    )
    data = {
        "berthing_energy_kNm": res.berthing_energy_kNm,
        "virtual_mass_tonnes": res.virtual_mass_tonnes,
        "fender_standoff_meters": res.fender_standoff_meters,
        "is_fender_adequate": res.is_fender_adequate,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    table = Table(title="[bold yellow]Kiểm tra Động năng Cặp mạn STS (OCIMF/PIANC)[/bold yellow]")
    table.add_column("Thông số", style="cyan")
    table.add_column("Giá trị", style="white")
    table.add_row("Khối lượng ảo (Virtual Mass)", f"{res.virtual_mass_tonnes:,.2f} tấn")
    table.add_row("Năng lượng tiếp cận (Berthing Energy)", f"{res.berthing_energy_kNm:,.2f} kNm")
    table.add_row("Khoảng cách đệm cách ly", f"{res.fender_standoff_meters:.2f} m (Chuẩn >= 3.0m)")
    table.add_row("Đệm khí đạt chuẩn an toàn", "[bold green]ĐẠT[/bold green]" if res.is_fender_adequate else "[bold red]KHÔNG ĐẠT[/bold red]")
    console.print(table)


@ststransfer_app.command(name="evaluate")
def evaluate_sts_safety(
    wind: float = typer.Option(8.5, "--wind", "-w", help="Tốc độ gió (m/s)"),
    wave: float = typer.Option(1.0, "--wave", help="Chiều cao sóng có nghĩa Hs (mét)"),
    lightning: Optional[float] = typer.Option(None, "--lightning", help="Khoảng cách sét/dông bão (NM)"),
    o2: float = typer.Option(5.0, "--o2", help="Hàm lượng oxy khí trơ hầm hàng (%)"),
    resistance: float = typer.Option(500.0, "--ohm", help="Điện trở dây tiếp địa chống tĩnh điện (Ohms)"),
    boom: float = typer.Option(450.0, "--boom", help="Chiều dài phao quây dầu dự phòng (mét)"),
    loa_a: float = typer.Option(220.0, "--loa-a", help="Chiều dài tàu A (mét)"),
    loa_b: float = typer.Option(180.0, "--loa-b", help="Chiều dài tàu B (mét)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
):
    """Đánh giá ngưỡng an toàn khí tượng, khí trơ & phao quây dầu cho chuyển tải hàng rời/dầu STS."""
    res = ShipToShipTransferEngine.evaluate_sts_safety(
        wind_speed_mps=wind,
        significant_wave_height_meters=wave,
        lightning_distance_nm=lightning,
        inert_gas_oxygen_pct=o2,
        bonding_resistance_ohms=resistance,
        oil_boom_circumference_meters=boom,
        vessel_a_loa_meters=loa_a,
        vessel_b_loa_meters=loa_b,
    )
    data = {
        "is_safe_to_operate": res.is_safe_to_operate,
        "weather_abort": res.weather_abort,
        "inert_gas_safe": res.inert_gas_safe,
        "electrical_bonding_safe": res.electrical_bonding_safe,
        "boom_circumference_adequate": res.boom_circumference_adequate,
        "violations": res.violations,
        "sts_clearance_hash": res.sts_clearance_hash,
    }
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    color = "green" if res.is_safe_to_operate else "red"
    console.print(Panel(
        f"[bold {color}]Kết luận: {'CHO PHÉP HOẠT ĐỘNG STS' if res.is_safe_to_operate else 'ĐÌNH CHỈ / KHÔNG AN TOÀN'}[/bold {color}]\n"
        f"Ngưỡng thời tiết: {'ĐẠT' if not res.weather_abort else 'VƯỢT GIỚI HẠN (DỪNG)'}\n"
        f"Khí trơ O2 <= 8%: {'ĐẠT' if res.inert_gas_safe else 'KHÔNG ĐẠT'}\n"
        f"Tiếp địa chống tĩnh điện: {'ĐẠT' if res.electrical_bonding_safe else 'KHÔNG ĐẠT'}\n"
        f"Phao quây dầu dự phòng: {'ĐẠT' if res.boom_circumference_adequate else 'KHÔNG ĐẠT'}\n"
        + ("\n[bold red]Cảnh báo vi phạm:[/bold red]\n" + "\n".join(f"- {v}" for v in res.violations) if res.violations else ""),
        title="Đánh giá An toàn Chuyển tải Hàng hóa Giữa hai Tàu (NĐ 58/2017 & MARPOL Annex I)",
    ))
