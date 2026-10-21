"""CLI Commands for MARPOL Garbage, STCW Rest, Port Wharfage & CFS E-Seal Suite (Phases 287-290)."""

import typer

from src.core.maritime_garbage_stcw_wharfage_cfs_engine import (
    BerthType,
    CfsCargoOperation,
    CfsEsealEngine,
    CfsEsealSupervisionInput,
    GarbageCategory,
    GarbageDischargeEngine,
    GarbageDischargeInput,
    PortWharfArea,
    PortWharfageEngine,
    RestPeriod,
    SeaAreaZone,
    SeafarerRestEngine,
    SeafarerRestInput,
    VesselTradeType,
    WharfageCalculationInput,
)

garbage_app = typer.Typer(help="MARPOL Annex V Garbage Discharge & GRB Engine (Phase 287)")
resthours_app = typer.Typer(help="STCW Manila & MLC 2006 Seafarer Rest Hours Engine (Phase 288)")
wharfage_app = typer.Typer(help="Circular 39/2023/TT-BGTVT Port Wharfage Tariffs Engine (Phase 289)")
cfseseal_app = typer.Typer(help="Customs CFS Deconsolidation & E-Seal Tracking Engine (Phase 290)")


def _parse_enum(enum_cls, val: str, default):
    try:
        return enum_cls(val.upper())
    except ValueError:
        return default


@garbage_app.command("evaluate")
def evaluate_garbage_discharge(
    vessel: str = typer.Option("MV MEKONG HORIZON", "--vessel", "-v", help="Tên tàu biển"),
    imo: str = typer.Option("9845123", "--imo", help="Số IMO tàu biển"),
    category: str = typer.Option("FOOD_WASTE_COMMINUTED", "--category", "-c", help="Phân loại rác thải"),
    zone: str = typer.Option("OUTSIDE_SPECIAL_AREA", "--zone", "-z", help="Vùng biển hành trình"),
    dist: float = typer.Option(4.5, "--dist", "-d", help="Khoảng cách tới bờ biển gần nhất (NM)"),
    speed: float = typer.Option(11.2, "--speed", "-s", help="Tốc độ tàu (hải lý/giờ)"),
    vol: float = typer.Option(0.35, "--vol", help="Khối lượng rác thải ước tính (m3)"),
    port_available: bool = typer.Option(True, "--port-available", help="Có cơ sở tiếp nhận tại cảng không"),
    depth: float = typer.Option(65.0, "--depth", help="Độ sâu đáy biển (mét)"),
):
    """Đánh giá tuân thủ quy định xả rác theo MARPOL Annex V & MEPC.295(71)."""
    cat_enum = _parse_enum(GarbageCategory, category, GarbageCategory.FOOD_WASTE_COMMINUTED)
    zone_enum = _parse_enum(SeaAreaZone, zone, SeaAreaZone.OUTSIDE_SPECIAL_AREA)
    sample = GarbageDischargeInput(
        vessel_name=vessel, imo_number=imo, garbage_category=cat_enum, zone=zone_enum,
        distance_from_land_nm=dist, vessel_speed_knots=speed, estimated_volume_m3=vol,
        is_special_area_port_available=port_available, water_depth_meters=depth,
    )
    result = GarbageDischargeEngine.evaluate(sample)
    typer.echo("=" * 80)
    typer.echo("QUẢN LÝ RÁC THẢI TÀU BIỂN (MARPOL ANNEX V & MEPC.295(71))")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {vessel} | IMO: {imo} | Loại rác thải: {cat_enum.value} | Vùng biển: {zone_enum.value}")
    typer.echo(f"Khoảng cách đến bờ: {dist:.1f} NM | Tốc độ tàu: {speed:.1f} kts")
    typer.echo(f"Kết luận kiểm định: {result.verdict.value}")
    typer.echo(f"Được phép xả qua mạn: {'CÓ' if result.is_discharge_permitted else 'KHÔNG (LƯU GIỮ TRÊN TÀU)'}")
    typer.echo(f"Khoảng cách tối thiểu bắt buộc: {result.required_min_distance_nm:.1f} NM | Mã nhật ký rác (GRB): {result.grb_log_code}")
    typer.echo(f"Ghi chú kiểm tra: {result.remarks}\nMã băm xác thực: {result.verification_token}")
    typer.echo("=" * 80)


@resthours_app.command("verify")
def verify_seafarer_rest(
    name: str = typer.Option("Nguyễn Văn A", "--name", "-n", help="Họ và tên thuyền viên"),
    rank: str = typer.Option("Đại phó (Chief Officer)", "--rank", "-r", help="Chức danh thuyền viên"),
    p1: float = typer.Option(4.0, "--p1", help="Thời lượng khoảng nghỉ 1 trong 24h (giờ)"),
    p2: float = typer.Option(7.0, "--p2", help="Thời lượng khoảng nghỉ 2 trong 24h (giờ)"),
    past_6d: float = typer.Option(72.0, "--past-6d", help="Tổng giờ nghỉ trong 6 ngày liền kề trước đó (giờ)"),
    interval: float = typer.Option(10.5, "--interval", help="Khoảng thời gian giãn cách giữa 2 lần nghỉ (giờ)"),
    emergency: bool = typer.Option(False, "--emergency", help="Có tình huống khẩn cấp / báo động diễn tập không"),
):
    """Kiểm tra tuân thủ giờ nghỉ ngơi thuyền viên theo STCW Bảng A-VIII/1 & MLC 2006."""
    rest_list = [RestPeriod(start_hour=0.0, duration_hours=p1)]
    if p2 > 0:
        rest_list.append(RestPeriod(start_hour=12.0, duration_hours=p2))
    sample = SeafarerRestInput(
        seafarer_name=name, rank=rank, rest_periods_24h=rest_list,
        total_rest_hours_past_6d=past_6d, interval_between_rests_hours=interval,
        is_emergency_drill_or_sar=emergency,
    )
    result = SeafarerRestEngine.evaluate(sample)
    typer.echo("=" * 80)
    typer.echo("KIỂM SOÁT THỜI GIAN NGHỈ NGƠI THUYỀN VIÊN (STCW 2010 & MLC 2006)")
    typer.echo("=" * 80)
    typer.echo(f"Thuyền viên: {name} | Chức danh: {rank}")
    typer.echo(f"Tổng giờ nghỉ trong 24h: {result.total_rest_24h:.1f} h (Tối thiểu luật định: 10.0 h)")
    typer.echo(f"Khoảng nghỉ liên tục dài nhất: {result.longest_continuous_rest:.1f} h (Tối thiểu: 6.0 h)")
    typer.echo(f"Số khoảng nghỉ trong 24h: {result.period_count_24h} (Tối đa: 2 khoảng) | Trượt 7 ngày: {result.total_rest_7d:.1f} h")
    typer.echo(f"Trạng thái tuân thủ: {result.compliance_status.value}")
    typer.echo(f"Đạt yêu cầu: {'ĐẠT (COMPLIANT)' if result.is_compliant else 'VI PHẠM (NON-COMPLIANT)'}")
    if result.compensation_rest_due_hours > 0:
        typer.echo(f"Giờ nghỉ bù phải bố trí ngay: {result.compensation_rest_due_hours:.1f} h")
    typer.echo(f"Chi tiết đánh giá: {result.audit_remarks}\n" + "=" * 80)


@wharfage_app.command("calculate")
def calculate_port_wharfage(
    gt: float = typer.Option(32000.0, "--gt", help="Dung tích toàn phần (GT) của tàu"),
    trade: str = typer.Option("INTERNATIONAL", "--trade", "-t", help="Tuyến vận tải: INTERNATIONAL hoặc DOMESTIC"),
    area: str = typer.Option("AREA_III_SOUTH", "--area", "-a", help="Vùng cảng: AREA_I_NORTH, AREA_II_CENTRAL, AREA_III_SOUTH"),
    berth: str = typer.Option("CONTAINER_BERTH", "--berth", "-b", help="Loại cầu bến cảng"),
    sched_h: float = typer.Option(36.0, "--sched-h", help="Thời gian làm hàng theo kế hoạch (giờ)"),
    actual_h: float = typer.Option(40.0, "--actual-h", help="Thời gian cập cầu thực tế (giờ)"),
    holiday: bool = typer.Option(False, "--holiday", help="Cập cầu vào ngày lễ, Tết"),
    fx: float = typer.Option(25000.0, "--fx", help="Tỷ giá USD/VND"),
):
    """Tính toán cước sử dụng cầu bến, phao neo theo Thông tư 39/2023/TT-BGTVT."""
    trade_enum = _parse_enum(VesselTradeType, trade, VesselTradeType.INTERNATIONAL)
    area_enum = _parse_enum(PortWharfArea, area, PortWharfArea.AREA_III_SOUTH)
    berth_enum = _parse_enum(BerthType, berth, BerthType.CONTAINER_BERTH)
    sample = WharfageCalculationInput(
        gross_tonnage=gt, trade_type=trade_enum, port_area=area_enum, berth_type=berth_enum,
        scheduled_hours=sched_h, actual_hours=actual_h, is_holiday=holiday, vnd_exchange_rate=fx,
    )
    result = PortWharfageEngine.calculate(sample)
    typer.echo("=" * 80)
    typer.echo("TÍNH CƯỚC SỬ DỤNG CẦU BẾN CẢNG BIỂN (THÔNG TƯ 39/2023/TT-BGTVT)")
    typer.echo("=" * 80)
    typer.echo(f"Dung tích tàu: {gt:,.0f} GT | Loại bến: {berth_enum.value} | Khu vực: {area_enum.value}")
    typer.echo(f"Thời gian cập bến thực tế: {actual_h:.1f} h (Kế hoạch: {sched_h:.1f} h | Overstay: {result.overstay_hours:.1f} h)")
    typer.echo(f"Đơn giá cơ sở: {result.base_rate_per_gt_hour:.6f} /GT/h | Cước cơ sở: ${result.base_berthage_fee_usd:,.2f} USD")
    if result.overstay_surcharge_usd > 0:
        typer.echo(f"Phụ phí nằm cầu quá hạn (+50%): ${result.overstay_surcharge_usd:,.2f} USD")
    if result.holiday_surcharge_usd > 0:
        typer.echo(f"Phụ phí ngày lễ/Tết (+30%): ${result.holiday_surcharge_usd:,.2f} USD")
    typer.echo("-" * 80)
    typer.echo(f"TỔNG CƯỚC CẦU BẾN PHẢI THU: ${result.total_wharfage_fee_usd:,.2f} USD ({result.total_wharfage_fee_vnd:,.0f} VND)")
    typer.echo(f"Mô tả hóa đơn: {result.invoice_description}\n" + "=" * 80)


@cfseseal_app.command("supervise")
def supervise_cfs_eseal(
    container: str = typer.Option("TCNU8923410", "--container", "-c", help="Số hiệu container"),
    eseal: str = typer.Option("ESEAL-VN-2026-9921", "--eseal", "-e", help="Mã niêm phong điện tử E-Seal"),
    op: str = typer.Option("LCL_DECONSOLIDATION", "--op", help="Nghiệp vụ kho CFS"),
    days: int = typer.Option(45, "--days", "-d", help="Số ngày hàng lưu giữ tại kho CFS"),
    extended: bool = typer.Option(False, "--extended", help="Đã được Hải quan gia hạn lưu kho"),
    cable_ok: bool = typer.Option(True, "--cable-ok", help="Tình trạng dây cáp niêm phong nguyên vẹn"),
    tamper: bool = typer.Option(False, "--tamper", help="Cảnh báo can thiệp mở khóa trái phép"),
    dev_m: float = typer.Option(0.0, "--dev-m", help="Độ lệch khỏi tuyến đường giám sát (mét)"),
    gps_lost_m: float = typer.Option(0.0, "--gps-lost-m", help="Thời gian mất tín hiệu GPS (phút)"),
):
    """Giám sát hàng hóa CFS và niêm phong định vị điện tử Hải quan (E-Seal)."""
    op_enum = _parse_enum(CfsCargoOperation, op, CfsCargoOperation.LCL_DECONSOLIDATION)
    sample = CfsEsealSupervisionInput(
        container_no=container, eseal_id=eseal, operation=op_enum, storage_days=days,
        is_extension_approved=extended, is_cable_intact=cable_ok,
        is_tamper_detected=tamper, route_deviation_meters=dev_m, gps_lost_minutes=gps_lost_m,
    )
    result = CfsEsealEngine.evaluate(sample)
    typer.echo("=" * 80)
    typer.echo("GIÁM SÁT KHO HÀNG CFS & ĐỊNH VỊ NIÊM PHONG ĐIỆN TỬ E-SEAL HẢI QUAN")
    typer.echo("=" * 80)
    typer.echo(f"Container: {container} | Mã E-Seal: {eseal} | Nghiệp vụ CFS: {op_enum.value}")
    typer.echo(f"Thời gian lưu kho: {days} ngày / Hạn tối đa: {result.max_permitted_storage_days} ngày (Còn lại: {result.remaining_storage_days} ngày)")
    typer.echo(f"Trạng thái giám sát Hải quan: {result.customs_status.value}")
    typer.echo(f"Đủ điều kiện thông quan/giải phóng hàng: {'CÓ (CLEARED)' if result.is_cleared_for_release else 'KHÔNG (GIỮ LẠI ĐIỀU TRA)'}")
    typer.echo(f"Mã định danh giám sát: {result.supervision_token}\nTóm tắt nghiệp vụ: {result.status_summary}")
    typer.echo("=" * 80)
