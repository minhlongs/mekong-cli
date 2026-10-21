"""CLI Commands for Maritime COLREGs, General Average, Container VGM & Marine Insurance (Phases 319-322)."""

import json
from typing import List
import typer

from src.core.maritime_colregs_ga_vgm_insurance_engine import (
    ColregsNavigationEngine, ColregsTargetInput, ContainerVgmComplianceEngine,
    ContainerVgmInput, GaContributoryItem, GaInterestParty,
    GeneralAverageAdjustmentEngine, ItcHullsClaimEngine, ItcHullsClaimInput, VgmMethod,
)

colregs_app = typer.Typer(help="COLREGs 1972 Collision Avoidance & CPA/TCPA Evaluator (Phase 319)")
ga_app = typer.Typer(help="York-Antwerp Rules 2016 General Average Adjustment (Phase 320)")
vgm_app = typer.Typer(help="SOLAS VI/2 Container Verified Gross Mass Verification (Phase 321)")
insurance_app = typer.Typer(help="ITC-Hulls 1/10/83 Marine Insurance Claims Settlement (Phase 322)")

_BAR = "======================================================="


def _print_header(title: str, color: str) -> None:
    typer.secho(f"\n{_BAR}", fg=color, bold=True)
    typer.secho(f" {title}", fg=color, bold=True)
    typer.secho(_BAR, fg=color)


@colregs_app.command("assess")
def assess_colregs_collision(
    own_name: str = typer.Option("MEKONG_PRIDE", "--own", "-o", help="Tên tàu mình"),
    own_course: float = typer.Option(0.0, "--own-course", help="Hướng đi tàu mình (độ)"),
    own_speed: float = typer.Option(14.0, "--own-speed", help="Tốc độ tàu mình (knots)"),
    target_name: str = typer.Option("TARGET_VESSEL", "--target", "-t", help="Tên tàu mục tiêu"),
    bearing: float = typer.Option(45.0, "--bearing", "-b", help="Phương vị tới tàu mục tiêu (độ)"),
    distance: float = typer.Option(5.0, "--dist", "-d", help="Khoảng cách tới mục tiêu (NM)"),
    target_course: float = typer.Option(270.0, "--target-course", help="Hướng đi mục tiêu (độ)"),
    target_speed: float = typer.Option(12.0, "--target-speed", help="Tốc độ mục tiêu (knots)"),
    safe_cpa: float = typer.Option(1.5, "--safe-cpa", help="Khoảng cách CPA an toàn tối thiểu (NM)"),
    safe_tcpa: float = typer.Option(20.0, "--safe-tcpa", help="Thời gian TCPA cảnh báo tối đa (phút)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Đánh giá nguy cơ va chạm và tình huống điều động theo COLREGs 1972."""
    inp = ColregsTargetInput(own_name, own_course, own_speed, target_name, bearing, distance, target_course, target_speed, safe_cpa, safe_tcpa)
    res = ColregsNavigationEngine.evaluate_encounter(inp)
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    _print_header("COLREGs 1972 COLLISION RISK ASSESSMENT (Phase 319)", typer.colors.CYAN)
    typer.echo(
        f"Tàu ta: {res.own_vessel_name} (Hướng: {own_course:.1f}°, Tốc độ: {own_speed:.1f} kts)\n"
        f"Mục tiêu: {res.target_vessel_name} (Phương vị: {bearing:.1f}°, Khoảng cách: {distance:.1f} NM)\n"
        f"Góc mạn tương đối (Relative Bearing): {res.relative_bearing_deg:.1f}°\n"
        f"CPA: {res.cpa_distance_nm:.2f} NM | TCPA: {res.tcpa_minutes:.1f} phút"
    )
    if res.risk_of_collision:
        typer.secho(f"\n[!] CẢNH BÁO: CÓ NGUY CƠ ĐÂM VA (CPA < {safe_cpa:.1f} NM)!", fg=typer.colors.RED, bold=True)
    else:
        typer.secho("\n[+] AN TOÀN: Không có nguy cơ va chạm nguy hiểm.", fg=typer.colors.GREEN, bold=True)
    typer.echo(f"Tình huống (Situation): {res.situation.value}\nNghĩa vụ điều động: {res.action_obligation.value}")
    typer.secho(f"\nKhuyến cáo hành hải:\n{res.recommended_maneuver}", fg=typer.colors.YELLOW, bold=True)
    typer.echo(f"Mã kiểm toán SHA-256: {res.audit_hash}\n{_BAR}\n")


@ga_app.command("calculate")
def calculate_general_average(
    incident: str = typer.Option("GA-SGN-2026", "--incident", "-i", help="Mã vụ việc tổn thất chung"),
    vessel_val: float = typer.Option(10000000.0, "--vessel-val", help="Giá trị nguyên vẹn của tàu (USD)"),
    vessel_dmg: float = typer.Option(200000.0, "--vessel-dmg", help="Tổn thất riêng của tàu (USD)"),
    vessel_sacrifice: float = typer.Option(100000.0, "--vessel-sac", help="Hy sinh máy/thân tàu vì GA (USD)"),
    vessel_salvage: float = typer.Option(150000.0, "--vessel-salvage", help="Chi phí cứu nạn/ghé cảng lánh nạn (USD)"),
    cargo_val: float = typer.Option(5000000.0, "--cargo-val", help="Tổng giá trị hàng hóa CIF (USD)"),
    cargo_sacrifice: float = typer.Option(300000.0, "--cargo-sac", help="Giá trị hàng bị ném xuống biển cứu tàu (USD)"),
    freight_val: float = typer.Option(250000.0, "--freight-val", help="Giá trị cước phí chịu rủi ro (USD)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán phân bổ tổn thất chung (General Average) theo York-Antwerp Rules 2016."""
    items: List[GaContributoryItem] = [
        GaContributoryItem("VESSEL", GaInterestParty.SHIPOWNER, "Vessel / Shipowner Interest", vessel_val, vessel_dmg, vessel_sacrifice, vessel_salvage),
        GaContributoryItem("CARGO", GaInterestParty.CARGO_OWNER, "Total Cargo CIF Interest", cargo_val, 0.0, cargo_sacrifice, 0.0),
        GaContributoryItem("FREIGHT", GaInterestParty.CHARTERER, "Freight at Risk", freight_val, 0.0, 0.0, 0.0),
    ]
    res = GeneralAverageAdjustmentEngine.calculate_adjustment(incident, items)
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    _print_header("YORK-ANTWERP RULES 2016 GENERAL AVERAGE ADJUSTMENT", typer.colors.MAGENTA)
    typer.echo(
        f"Vụ việc tổn thất chung: {res.incident_ref}\n"
        f"Tổng giá trị chịu phân bổ (Contributory Value): ${res.total_contributory_value_usd:,.2f} USD\n"
        f"Tổng quỹ thiệt hại & chi phí GA: ${res.total_ga_loss_usd:,.2f} USD"
    )
    typer.secho(f"Tỷ lệ đóng góp GA Rate: {res.ga_contribution_rate_pct:.4f}%\n", fg=typer.colors.YELLOW, bold=True)
    typer.echo(f"Bảng phân bổ công nợ & bù trừ tài chính (GA Balance Sheet):\n{'Bên liên quan':<25} | {'Giá trị chịu PB':<16} | {'Phải đóng góp':<16} | {'Được bù hoàn':<16} | {'Thu/Chi ròng'}\n" + "-" * 100)
    for s in res.settlements:
        net_str = f"+${s.net_balance_usd:,.2f}" if s.net_balance_usd >= 0 else f"-${abs(s.net_balance_usd):,.2f}"
        typer.echo(f"{s.name:<25} | ${s.contributory_value_usd:>14,.2f} | ${s.contribution_payable_usd:>14,.2f} | ${s.ga_allowance_receivable_usd:>14,.2f} | {net_str:>14}")
    typer.echo("-" * 100 + f"\nGhi chú: {res.remarks}\nMã kiểm toán SHA-256: {res.audit_hash}\n{_BAR}\n")


@vgm_app.command("verify")
def verify_container_vgm(
    container_no: str = typer.Option("MSKU1234567", "--container", "-c", help="Số container (11 ký tự)"),
    booking_no: str = typer.Option("BKG-VGM-2026", "--booking", "-b", help="Mã Booking hàng hải"),
    method: str = typer.Option("METHOD_1", "--method", "-m", help="Phương pháp cân VGM (METHOD_1 hoặc METHOD_2)"),
    tare: float = typer.Option(3850.0, "--tare", help="Trọng lượng vỏ container rỗng Tare (kg)"),
    mgw: float = typer.Option(30480.0, "--mgw", help="Trọng lượng tối đa cho phép Max Gross Weight (kg)"),
    vgm: float = typer.Option(24500.0, "--vgm", help="Trọng lượng VGM khai báo trong chứng từ (kg)"),
    terminal_weight: float = typer.Option(24650.0, "--terminal-weight", "-w", help="Trọng lượng thực cân tại cổng cảng (kg)"),
    has_cert: bool = typer.Option(True, "--cert/--no-cert", help="Có chứng chỉ/phiếu cân hợp lệ hay không"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Kiểm tra tuân thủ khối lượng toàn bộ container theo SOLAS VI/2 & TT 41/2016/TT-BGTVT."""
    m_enum = VgmMethod(method.upper()) if method.upper() in VgmMethod._value2member_map_ else VgmMethod.METHOD_1
    res = ContainerVgmComplianceEngine.verify_vgm(ContainerVgmInput(container_no, booking_no, m_enum, tare, mgw, vgm, terminal_weight, has_cert))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    _print_header("SOLAS VI/2 CONTAINER VGM VERIFICATION (Phase 321)", typer.colors.BLUE)
    typer.echo(
        f"Container: {res.container_no} | Booking: {res.booking_no} | Phương pháp: {res.vgm_method}\n"
        f"Khối lượng VGM khai báo: {res.declared_vgm_kg:,.1f} kg | Khối lượng thực tế cảng cân: {res.terminal_scale_weight_kg:,.1f} kg\n"
        f"Độ lệch trọng lượng: {res.weight_variance_kg:+,.1f} kg ({res.weight_variance_pct:.2f}%)\n"
        f"Tải trọng tối đa cho phép (Payload): {res.max_payload_kg:,.1f} kg | Trọng lượng vỏ Tare: {res.tare_weight_kg:,.1f} kg"
    )
    if res.is_loading_permitted:
        typer.secho("\n[PASS] ĐỦ ĐIỀU KIỆN XẾP HÀNG LÊN TÀU (LOADING PERMITTED)", fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("\n[FAIL] CẤM XẾP HÀNG LÊN TÀU (NO VGM, NO LOAD VIOLATION)!", fg=typer.colors.RED, bold=True)
        for r in res.rejection_reasons:
            typer.echo(f" - {r}")
    typer.echo(f"\nKết luận: {res.remarks}\nMã kiểm toán SHA-256: {res.audit_hash}\n{_BAR}\n")


@insurance_app.command("settle")
def settle_itc_hulls_claim(
    claim_id: str = typer.Option("CLM-HULL-2026-01", "--claim-id", "-c", help="Mã hồ sơ bồi thường"),
    vessel: str = typer.Option("M/V MEKONG EXPRESS", "--vessel", "-v", help="Tên tàu được bảo hiểm"),
    insured_val: float = typer.Option(5000000.0, "--insured-val", help="Giá trị bảo hiểm thỏa thuận trong đơn (USD)"),
    repairs: float = typer.Option(350000.0, "--repair", "-r", help="Chi phí sửa chữa thân tàu (USD)"),
    salvage: float = typer.Option(20000.0, "--salvage", "-s", help="Chi phí cứu nạn trục vớt (USD)"),
    third_party: float = typer.Option(180000.0, "--third-party", help="Trách nhiệm đâm va gây thiệt hại cho bên thứ 3 (USD)"),
    deductible: float = typer.Option(25000.0, "--deductible", "-d", help="Mức khấu trừ hợp đồng bảo hiểm thân tàu (USD)"),
    sue_labour: float = typer.Option(10000.0, "--sue-labour", help="Chi phí đề phòng hạn chế tổn thất Sue & Labour (USD)"),
    is_atl: bool = typer.Option(False, "--atl", help="Tàu bị tổn thất toàn bộ thực tế (chìm/mất tích)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
):
    """Tính toán thanh toán bồi thường bảo hiểm thân tàu theo ITC-Hulls 1/10/83."""
    res = ItcHullsClaimEngine.calculate_claim_settlement(ItcHullsClaimInput(claim_id, vessel, insured_val, repairs, salvage, third_party, deductible, sue_labour, is_atl))
    if as_json:
        typer.echo(json.dumps(res.to_dict(), indent=2, ensure_ascii=False))
        return

    _print_header("ITC-HULLS 1/10/83 MARINE INSURANCE CLAIM SETTLEMENT", typer.colors.GREEN)
    typer.echo(
        f"Mã yêu cầu bồi thường: {res.claim_id} | Tàu: {res.vessel_name}\n"
        f"Giá trị bảo hiểm (Insured Value): ${res.agreed_insured_value_usd:,.2f} USD\n"
        f"Phân loại tổn thất: {res.loss_classification.value}"
    )
    typer.secho(f"\nTổng số tiền Bảo hiểm Thân tàu chi trả: ${res.hull_insurer_payout_usd:,.2f} USD", fg=typer.colors.YELLOW, bold=True)
    typer.echo(
        f" - Khấu trừ đã áp dụng (Deductible): ${res.deductible_applied_usd:,.2f} USD\n"
        f" - Bồi thường 3/4 Trách nhiệm đâm va (3/4 RDC): ${res.rdc_hull_3_4_payout_usd:,.2f} USD\n"
        f" - Trách nhiệm 1/4 RDC chuyển giao Hội P&I: ${res.rdc_pni_1_4_liability_usd:,.2f} USD\n"
        f" - Bồi hoàn chi phí Sue & Labour: ${res.sue_and_labour_payout_usd:,.2f} USD\n\n"
        f"Nhận định giải quyết bồi thường:\n{res.remarks}\n"
        f"Mã kiểm toán SHA-256: {res.audit_hash}\n{_BAR}\n"
    )
