"""CLI Commands for MARPOL Air Emission (CII/ECA), Charter Party, Towage Tariffs & Customs STS Manifest (Phases 295-298)."""

from datetime import datetime
import typer

from src.core.maritime_air_charter_towage_sts_engine import (
    BunkerSulphurLog,  # noqa: F401
    CharterPartyFinancialEngine,
    CiiRating,
    CustomsStsManifestEngine,
    FuelType,
    LighterVesselAllocation,
    MarpolAirCiiEngine,
    OffHireReason,
    PortZoneArea,  # noqa: F401
    StsOperationType,
    StsPermitRecord,
    TimeCharterOffHireInput,
    TowageDrydockTariffEngine,
    TowageServiceInput,
    TowageTugPower,
    VesselCiiAssessmentInput,
    VoyageLaytimeStatement,  # noqa: F401
)

marpol_air_app = typer.Typer(help="MARPOL Annex VI CII & SEEMP Tracker Engine (Phase 295)")
charter_party_app = typer.Typer(help="Charter Party Financials Off-Hire & Laytime Engine (Phase 296)")
towage_drydock_app = typer.Typer(help="Towage Tariffs (TT 39/2023) & Drydock Budget Engine (Phase 297)")
sts_manifest_app = typer.Typer(help="Customs STS Permit & Split Manifest Handling Engine (Phase 298)")


@marpol_air_app.command("evaluate-cii")
def evaluate_cii(
    vessel: str = typer.Option("MV MEKONG GREEN", "--vessel", "-v", help="Tên tàu biển"),
    imo: str = typer.Option("9876543", "--imo", help="Số IMO"),
    dwt: float = typer.Option(50000.0, "--dwt", help="Trọng tải toàn phần (DWT)"),
    dist: float = typer.Option(50000.0, "--dist", "-d", help="Khoảng cách đã chạy (NM)"),
    fuel_mt: float = typer.Option(6500.0, "--fuel", "-f", help="Lượng dầu VLSFO tiêu thụ (Tấn)"),
    hist: str = typer.Option("C,C", "--hist", help="Lịch sử hạng CII (Mỗi hạng cách nhau dấu phẩy)"),
):
    """Đánh giá và cấp hạng CII (Carbon Intensity Indicator) theo MARPOL Annex VI."""
    hist_ratings = []
    if hist:
        for r in hist.split(","):
            try:
                hist_ratings.append(CiiRating(r.strip().upper()))
            except ValueError:
                pass
    req = VesselCiiAssessmentInput(
        vessel_name=vessel, imo_number=imo, dwt=dwt, distance_traveled_nm=dist,
        fuel_consumption_mt={FuelType.VLSFO: fuel_mt}, historical_ratings=hist_ratings,
        year=datetime.now().year,
    )
    result = MarpolAirCiiEngine.evaluate(req)
    typer.echo("=" * 80)
    typer.echo("MARPOL ANNEX VI: ĐÁNH GIÁ CHỈ SỐ CII & KẾ HOẠCH SEEMP")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {result.vessel_name} | IMO: {result.imo_number} | Năm: {result.year}")
    typer.echo(f"Tổng phát thải: {result.total_co2_emissions_mt:,.1f} tấn CO2 | CII tính toán: {result.attained_cii:.2f} gCO2/dwt.nm")
    typer.echo(f"HẠNG CII (Rating): {result.rating.value} | Cảnh báo SEEMP: {'CÓ' if result.requires_seemp_corrective_action_plan else 'KHÔNG'}")
    typer.echo(f"Chi tiết: {result.seemp_reason}\nMã tra cứu: {result.verification_hash}\n" + "=" * 80)


@charter_party_app.command("off-hire")
def calculate_off_hire(
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", "-v", help="Tên tàu biển"),
    charter_id: str = typer.Option("CP-TC-2026", "--cid", "-c", help="Mã hợp đồng Time Charter"),
    hire: float = typer.Option(24000.0, "--hire", help="Mức thuê tàu theo ngày (USD/Ngày)"),
    hours: float = typer.Option(24.0, "--hours", "-h", help="Số giờ Off-Hire"),
    reason: str = typer.Option("ENGINE_BREAKDOWN", "--reason", "-r", help="Lý do Off-Hire"),
    bunker_mt: float = typer.Option(10.0, "--bunker", help="Dầu máy chính tiêu hao trong off-hire (MT)"),
    bunker_price: float = typer.Option(600.0, "--price", help="Giá dầu (USD/MT)"),
):
    """Tính toán khoản tiền bị trừ (Off-Hire & Bunker) trong quá trình thuê tàu chuyến/định hạn."""
    try:
        r_enum = OffHireReason(reason.upper())
    except ValueError:
        r_enum = OffHireReason.ENGINE_BREAKDOWN
    req = TimeCharterOffHireInput(
        charter_id=charter_id, vessel_name=vessel, daily_hire_rate_usd=hire, off_hire_hours=hours,
        reason=r_enum, bunker_consumed_mt=bunker_mt, bunker_price_usd_per_mt=bunker_price,
    )
    res = CharterPartyFinancialEngine.calculate_off_hire(req)
    typer.echo("=" * 80)
    typer.echo("BÁO CÁO OFF-HIRE & BÙ TRỪ TÀI CHÍNH (TIME CHARTER)")
    typer.echo("=" * 80)
    typer.echo(f"Hợp đồng: {res.charter_id} | Tàu: {res.vessel_name}")
    typer.echo(f"Thời gian Off-Hire: {res.off_hire_days:.2f} ngày | Lý do: {res.reason.value}")
    typer.echo(f"Tiền thuê bị khấu trừ: ${res.hire_deduction_usd:,.2f} | Hoàn trả nhiên liệu: ${res.bunker_deduction_usd:,.2f}")
    typer.echo(f"TỔNG SỐ TIỀN BỊ TRỪ: ${res.total_deduction_usd:,.2f}\nBiên lai đối soát: {res.settlement_token}\n" + "=" * 80)


@towage_drydock_app.command("calc-towage")
def calculate_towage(
    vessel: str = typer.Option("MV EVERGREEN", "--vessel", "-v", help="Tên tàu biển"),
    gt: float = typer.Option(60000.0, "--gt", help="Dung tích toàn phần (GT)"),
    tug_power: str = typer.Option("HP_3000_TO_3999", "--power", help="Công suất tàu kéo"),
    qty: int = typer.Option(2, "--qty", "-q", help="Số lượng tàu kéo"),
    hours: float = typer.Option(2.0, "--hours", "-h", help="Thời gian lai dắt (Giờ)"),
    intl: bool = typer.Option(True, "--intl", help="Tàu ngoại (True = USD, False = VND)"),
    night: bool = typer.Option(False, "--night", help="Ngoài giờ hành chính / Lễ (+30%)"),
):
    """Tính cước dịch vụ tàu kéo hỗ trợ cập cầu/rời cầu (Thông tư 39/2023/TT-BGTVT)."""
    try:
        power_enum = TowageTugPower(tug_power.upper())
    except ValueError:
        power_enum = TowageTugPower.HP_3000_TO_3999
    req = TowageServiceInput(
        vessel_name=vessel, vessel_gt=gt, tug_power=power_enum, tug_quantity=qty,
        operation_hours=hours, is_international=intl, is_holiday_or_night=night,
    )
    res = TowageDrydockTariffEngine.calculate_towage(req)
    typer.echo("=" * 80)
    typer.echo("TÍNH CƯỚC TÀU KÉO CẢNG BIỂN (THÔNG TƯ 39/2023/TT-BGTVT)")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {res.vessel_name} (GT: {res.vessel_gt}) | Loại tàu kéo: {power_enum.value} | Số lượng: {res.tug_quantity} | Thời gian: {res.operation_hours}h")
    typer.echo(f"Đơn giá cơ bản: {res.base_rate_per_tug_hour:,.2f} {res.currency} / tàu kéo / giờ")
    if res.surcharge_rate > 0:
        typer.echo(f"Phụ thu: +{res.surcharge_rate * 100:.0f}% (Làm đêm/Lễ)")
    typer.echo(f"TỔNG CƯỚC: {res.total_towage_charge:,.2f} {res.currency}\n" + "=" * 80)


@sts_manifest_app.command("split")
def split_sts_manifest(
    vessel: str = typer.Option("MV MOTHER SHIP", "--vessel", "-v", help="Tên tàu mẹ"),
    permit: str = typer.Option("STS-2026-HQ-09", "--permit", "-p", help="Số giấy phép STS Hải quan"),
    total_wt: float = typer.Option(50000.0, "--total", "-t", help="Tổng lượng hàng trên tàu mẹ (MT)"),
    child1: str = typer.Option("BARGE-1", "--c1", help="Tên tàu con 1"),
    wt1: float = typer.Option(15000.0, "--w1", help="Khối lượng tàu con 1 nhận (MT)"),
    child2: str = typer.Option("BARGE-2", "--c2", help="Tên tàu con 2"),
    wt2: float = typer.Option(10000.0, "--w2", help="Khối lượng tàu con 2 nhận (MT)"),
):
    """Xử lý Tách Bản khai (Split Manifest) cho luồng hàng Ship-to-Ship truyền Hải quan."""
    p_rec = StsPermitRecord(
        permit_number=permit, mother_vessel_name=vessel, mother_imo="9000001",
        operation_type=StsOperationType.LIGHTERAGE_DISCHARGE, anchor_location_zone="Hon Gai STS",
        total_cargo_weight_mt=total_wt, total_packages=0, valid_from="2026-10-08", valid_until="2026-10-15",
    )
    allocs = [
        LighterVesselAllocation(child1, "CALL1", wt1, 0, "HQ-KV1"),
        LighterVesselAllocation(child2, "CALL2", wt2, 0, "HQ-KV2"),
    ]
    res = CustomsStsManifestEngine.split_manifest(p_rec, allocs)
    typer.echo("=" * 80)
    typer.echo("HẢI QUAN: TÁCH BẢN KHAI CHUYỂN TẢI STS (SPLIT MANIFEST)")
    typer.echo("=" * 80)
    typer.echo(f"Tàu mẹ: {res.mother_vessel_name} | Giấy phép STS: {res.permit_number}")
    typer.echo(f"Tổng hàng gốc: {res.total_mother_weight_mt:,.2f} MT | Tổng đã sang mạn: {res.total_transferred_weight_mt:,.2f} MT")
    for s in res.sub_manifests:
        typer.echo(f" [->] Tàu con: {s['lighter_vessel']} nhận {s['weight_mt']:,.2f} MT (Số Manifest con: {s['sub_manifest_id']})")
    typer.echo("-" * 80)
    typer.echo(f"Trạng thái: {'CÂN BẰNG' if res.is_balanced else 'LỖI PHÂN BỔ'} | Tồn tàu mẹ: {res.remaining_weight_on_mother_mt:,.2f} MT")
    typer.echo(f"Ghi chú rủi ro: {res.discrepancy_remarks}\n" + "=" * 80)
