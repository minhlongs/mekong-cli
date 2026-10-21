"""CLI Commands for MARPOL Sewage, STCW Medical, Port Stevedoring Tariffs & Bonded Warehouse Suite (Phases 291-294)."""

import typer

from src.core.maritime_sewage_medical_stevedoring_bonded_engine import (
    BondedWarehouseEngine,
    BondedWarehouseInput,
    CargoHazardCategory,
    CargoStatus,
    ContainerSize,
    DepartmentRole,
    HandlingOperation,
    MedicalAssessmentInput,
    PortZone,
    SeafarerMedicalEngine,
    SewageDischargeEngine,
    SewageDischargeInput,
    SewageTreatmentType,
    StevedoringTariffEngine,
    StevedoringTariffInput,
)

sewage_app = typer.Typer(help="MARPOL Annex IV Sewage Discharge & STP Engine (Phase 291)")
medical_app = typer.Typer(help="STCW Manila & MLC 2006 Seafarer Medical Fitness Engine (Phase 292)")
stevedore_app = typer.Typer(help="Circular 39/2023/TT-BGTVT Port Stevedoring Tariffs Engine (Phase 293)")
bonded_app = typer.Typer(help="Customs Bonded Warehouse (Kho Ngoại Quan) Dwell Engine (Phase 294)")


def _parse_enum(enum_cls, val: str, default):
    try:
        return enum_cls(val.upper())
    except ValueError:
        return default


@sewage_app.command("evaluate")
def evaluate_sewage_discharge(
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", "-v", help="Tên tàu biển"),
    imo: str = typer.Option("9876543", "--imo", help="Số IMO tàu biển"),
    treatment: str = typer.Option("COMMINUTED_AND_DISINFECTED", "--treatment", "-t", help="Loại xử lý nước thải"),
    dist: float = typer.Option(4.5, "--dist", "-d", help="Khoảng cách tới bờ biển gần nhất (NM)"),
    speed: float = typer.Option(11.2, "--speed", "-s", help="Tốc độ tàu (hải lý/giờ)"),
    port_waters: bool = typer.Option(False, "--port-waters", help="Tàu đang trong vùng nước cảng biển"),
    special_area: bool = typer.Option(False, "--special-area", help="Vùng biển đặc quyền (Special Area)"),
    passenger: bool = typer.Option(False, "--passenger", help="Là tàu chở khách"),
):
    """Đánh giá tuân thủ quy định xả nước thải theo MARPOL Annex IV & MEPC.227(64)."""
    treat_enum = _parse_enum(SewageTreatmentType, treatment, SewageTreatmentType.COMMINUTED_AND_DISINFECTED)
    sample = SewageDischargeInput(
        vessel_name=vessel, imo_number=imo, distance_to_shore_nm=dist, vessel_speed_knots=speed,
        treatment_type=treat_enum, is_in_port_waters=port_waters, is_special_area=special_area,
        is_passenger_ship=passenger,
    )
    result = SewageDischargeEngine.evaluate(sample)
    typer.echo("=" * 80)
    typer.echo("QUẢN LÝ XẢ NƯỚC THẢI TÀU BIỂN (MARPOL ANNEX IV & MEPC.227(64))")
    typer.echo("=" * 80)
    typer.echo(f"Tàu: {vessel} | IMO: {imo} | Hệ thống xử lý: {treat_enum.value}")
    typer.echo(f"Khoảng cách đến bờ: {dist:.1f} NM | Tốc độ hành trình: {speed:.1f} kts")
    typer.echo(f"Kết luận kiểm định: {result.verdict.value}")
    typer.echo(f"Được phép xả thải: {'CÓ' if result.is_discharge_permitted else 'KHÔNG (PHẢI LƯU GIỮ TRÊN TÀU)'}")
    typer.echo(f"Yêu cầu tối thiểu: Khoảng cách >= {result.required_min_distance_nm:.1f} NM | Tốc độ >= {result.required_min_speed_knots:.1f} kts")
    typer.echo(f"Ghi chú: {result.remarks}\nMã xác thực SHA-256: {result.verification_token}\n" + "=" * 80)


@medical_app.command("verify")
def verify_seafarer_medical(
    name: str = typer.Option("NGUYEN VAN HUNG", "--name", "-n", help="Họ và tên thuyền viên"),
    sid: str = typer.Option("VN123456", "--sid", help="Số hộ chiếu hoặc Sổ thuyền viên"),
    age: int = typer.Option(28, "--age", "-a", help="Tuổi thuyền viên"),
    dept: str = typer.Option("DECK_WATCHKEEPING", "--dept", help="Bộ phận công tác"),
    vision_right: float = typer.Option(1.0, "--vr", help="Thị lực mắt phải"),
    vision_left: float = typer.Option(0.8, "--vl", help="Thị lực mắt trái"),
    vision_both: float = typer.Option(1.0, "--vb", help="Thị lực hai mắt"),
    color_pass: bool = typer.Option(True, "--color-pass", help="Đạt kiểm tra sắc giác Ishihara"),
    whisper_m: float = typer.Option(4.0, "--whisper", help="Khoảng cách nghe tiếng nói thầm (mét)"),
    normal_m: float = typer.Option(6.0, "--normal", help="Khoảng cách nghe tiếng nói thường (mét)"),
    cardio: bool = typer.Option(False, "--cardio", help="Có bệnh tim mạch nặng"),
    epilepsy: bool = typer.Option(False, "--epilepsy", help="Có tiền sử động kinh/co giật"),
    diabetes: bool = typer.Option(False, "--diabetes", help="Có đái tháo đường không kiểm soát"),
    lenses: bool = typer.Option(False, "--lenses", help="Yêu cầu đeo kính điều chỉnh"),
):
    """Kiểm tra và cấp chứng nhận sức khỏe thuyền viên theo STCW I/9 & Thông tư 22/2017/TT-BYT."""
    dept_enum = _parse_enum(DepartmentRole, dept, DepartmentRole.DECK_WATCHKEEPING)
    cand = MedicalAssessmentInput(
        seafarer_name=name, passport_or_sid=sid, age=age, department=dept_enum,
        visual_acuity_right=vision_right, visual_acuity_left=vision_left, visual_acuity_both_eyes=vision_both,
        is_color_vision_passed=color_pass, hearing_whisper_m=whisper_m, hearing_normal_m=normal_m,
        has_severe_cardiovascular=cardio, has_epilepsy_or_seizures=epilepsy,
        has_uncontrolled_diabetes=diabetes, requires_corrective_lenses=lenses,
    )
    result = SeafarerMedicalEngine.evaluate(cand)
    typer.echo("=" * 80)
    typer.echo("GIÁM ĐỊNH SỨC KHỎE THUYỀN VIÊN (STCW MANILA I/9 & TT 22/2017/TT-BYT)")
    typer.echo("=" * 80)
    typer.echo(f"Thuyền viên: {name} | Hộ chiếu/SID: {sid} | Tuổi: {age} | Bộ phận: {dept_enum.value}")
    typer.echo(f"Kết luận giám định: {result.verdict.value} | Thời hạn hiệu lực GKSK: {result.certificate_validity_months} tháng")
    typer.echo(f"Trạng thái thị giác: {result.visual_status} | Thính giác: {result.hearing_status}")
    if result.restrictions:
        typer.echo(f"Điều kiện hạn chế: {'; '.join(result.restrictions)}")
    if result.disqualifications:
        typer.echo(f"Lý do không đủ điều kiện: {'; '.join(result.disqualifications)}")
    typer.echo(f"Mã xác thực chứng chỉ SHA-256: {result.verification_token}\n" + "=" * 80)


@stevedore_app.command("calculate")
def calculate_stevedoring_tariff(
    zone: str = typer.Option("ZONE_III_DEEPWATER", "--zone", "-z", help="Khu vực cảng biển"),
    size: str = typer.Option("CONT_40FT", "--size", "-s", help="Kích cỡ container"),
    status: str = typer.Option("LADEN", "--status", help="Tình trạng (LADEN = có hàng, EMPTY = rỗng)"),
    op: str = typer.Option("VESSEL_TO_CY", "--op", help="Phương án bốc dỡ"),
    hazard: str = typer.Option("NORMAL_GENERAL", "--hazard", help="Phân loại nguy hiểm"),
    qty: int = typer.Option(10, "--qty", "-q", help="Số lượng container"),
    intl: bool = typer.Option(True, "--intl", help="Tàu vận tải quốc tế (True = USD, False = VND)"),
):
    """Tính cước bốc dỡ container theo Thông tư 39/2023/TT-BGTVT & Thông tư 12/2024/TT-BGTVT."""
    zone_enum = _parse_enum(PortZone, zone, PortZone.ZONE_III_DEEPWATER)
    size_enum = _parse_enum(ContainerSize, size, ContainerSize.CONT_40FT)
    status_enum = _parse_enum(CargoStatus, status, CargoStatus.LADEN)
    op_enum = _parse_enum(HandlingOperation, op, HandlingOperation.VESSEL_TO_CY)
    hazard_enum = _parse_enum(CargoHazardCategory, hazard, CargoHazardCategory.NORMAL_GENERAL)
    req = StevedoringTariffInput(
        port_zone=zone_enum, container_size=size_enum, cargo_status=status_enum,
        handling_operation=op_enum, hazard_category=hazard_enum, quantity=qty,
        is_international_vessel=intl,
    )
    result = StevedoringTariffEngine.calculate(req)
    typer.echo("=" * 80)
    typer.echo("CƯỚC DỊCH VỤ BỐC DỠ CONTAINER CẢNG BIỂN (THÔNG TƯ 39/2023/TT-BGTVT)")
    typer.echo("=" * 80)
    typer.echo(f"Khu vực cảng: {zone_enum.value} | Phương án: {op_enum.value}")
    typer.echo(f"Loại container: {size_enum.value} ({status_enum.value}) | Số lượng: {qty}")
    typer.echo(f"Phân loại hàng: {hazard_enum.value} (Phụ thu: {result.hazard_surcharge_rate * 100:.0f}%)")
    typer.echo(f"Đơn giá bốc dỡ: {result.rate_per_container:,.2f} {result.currency}/cont")
    typer.echo(f"TỔNG CƯỚC BỐC DỠ: {result.total_charge:,.2f} {result.currency}")
    typer.echo(f"Mã hóa đơn điện tử SHA-256: {result.invoice_hash}\n" + "=" * 80)


@bonded_app.command("supervise")
def supervise_bonded_warehouse(
    dec_no: str = typer.Option("C11-20251001-9876", "--dec-no", help="Số tờ khai nhập kho ngoại quan"),
    entry_date: str = typer.Option("2025-10-08", "--entry-date", help="Ngày đưa hàng vào kho ngoại quan (YYYY-MM-DD)"),
    check_date: str = typer.Option("2026-10-08", "--check-date", help="Ngày kiểm tra hiện tại (YYYY-MM-DD)"),
    extended: bool = typer.Option(False, "--extended", help="Đã được Cục trưởng Hải quan gia hạn 12 tháng"),
    warehouse: str = typer.Option("TAN_CANG_BONDED_WH", "--wh", help="Tên kho ngoại quan"),
    cif_val: float = typer.Option(85000.0, "--val", help="Trị giá CIF lô hàng (USD)"),
):
    """Giám sát thời hạn lưu kho ngoại quan và xử lý quá hạn theo Luật Hải quan 2014 Điều 61 & 63."""
    record = BondedWarehouseInput(
        declaration_number=dec_no, entry_date_str=entry_date, check_date_str=check_date,
        is_extension_granted=extended, warehouse_name=warehouse, cif_value_usd=cif_val,
    )
    result = BondedWarehouseEngine.supervise(record)
    typer.echo("=" * 80)
    typer.echo("GIÁM SÁT THỜI HẠN LƯU KHO NGOẠI QUAN (LUẬT HẢI QUAN 2014 & NĐ 08/2015)")
    typer.echo("=" * 80)
    typer.echo(f"Tờ khai: {dec_no} | Kho ngoại quan: {warehouse} | Nhập kho: {entry_date} | Kiểm tra: {check_date}")
    typer.echo(f"Số ngày lưu kho thực tế: {result.days_in_storage} ngày (Hạn cho phép: {result.allowed_max_days} ngày)")
    typer.echo(f"Trạng thái hải quan: {result.status.value} | Còn lại: {result.remaining_days} ngày | Quá hạn: {result.overstay_days} ngày")
    typer.echo(f"Buộc tịch thu/tiêu hủy: {'CÓ (ĐIỀU 63 LUẬT HẢI QUAN)' if result.is_seizure_mandated else 'KHÔNG'}")
    typer.echo(f"Biện pháp xử lý: {result.recommended_action}\nMã kiểm toán SHA-256: {result.audit_token}\n" + "=" * 80)
