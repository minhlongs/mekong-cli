# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Solvency audit, claim settlement, and technical reserve subcommands for Insurance CLI."""

from __future__ import annotations

import json
import typing

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def register_insurance_actuarial(insurance_app: typer.Typer) -> None:
    """Register solvency, claim, and reserve commands onto insurance_app."""
    insurance_app.command("solvency")(solvency_cmd)
    insurance_app.command("claim")(claim_cmd)
    insurance_app.command("reserve")(reserve_cmd)


def solvency_cmd(
    insurer: str = typer.Argument(..., help="Tên doanh nghiệp bảo hiểm"),
    actual_margin: float = typer.Option(..., "--actual-margin", "-a", help="Biên khả năng thanh toán thực tế (VND)"),
    net_premium: float = typer.Option(2_000_000_000_000.0, "--net-premium", help="Phí bảo hiểm thuần giữ lại trong năm (VND)"),
    avg_claims: float = typer.Option(1_000_000_000_000.0, "--avg-claims", help="Bồi thường bình quân 3 năm liền kề (VND)"),
    math_reserve: float = typer.Option(0.0, "--math-reserve", help="Dự phòng toán học đối với bảo hiểm nhân thọ (VND)"),
    sum_at_risk: float = typer.Option(0.0, "--sum-at-risk", help="Số tiền bảo hiểm chịu rủi ro đối với nhân thọ (VND)"),
    is_life: bool = typer.Option(False, "--life/--non-life", help="Doanh nghiệp bảo hiểm nhân thọ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra biên khả năng thanh toán tối thiểu và tỷ lệ an toàn vốn (CAR) theo Nghị định 46/2023/NĐ-CP."""
    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    result = engine.audit_solvency_margin(
        insurer_name=insurer,
        actual_solvency_margin_vnd=actual_margin,
        net_premium_retained_vnd=net_premium,
        avg_annual_claims_vnd=avg_claims,
        mathematical_reserve_vnd=math_reserve,
        sum_at_risk_vnd=sum_at_risk,
        is_life=is_life,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["solvency_profile"]
    status_color = "green" if prof["is_solvent"] else "red"

    table = Table(title=f"Kiểm Tra Biên Khả Năng Thanh Toán & CAR — {prof['insurer_name']}")
    table.add_column("Chỉ tiêu an toàn vốn & thanh toán", style="cyan")
    table.add_column("Kết quả thẩm định", justify="right", style="bold")

    table.add_row("Mã hồ sơ audit", prof["audit_id"])
    table.add_row("Tên doanh nghiệp", prof["insurer_name"])
    table.add_row("Loại hình bảo hiểm", prof["business_type"])
    table.add_row("Biên thanh toán thực tế", f"{prof['actual_margin_vnd']:,.0f} VND")
    table.add_row("Biên thanh toán tối thiểu quy định", f"{prof['minimum_margin_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ an toàn vốn (CAR)", prof["capital_adequacy_percent"], style=f"bold {status_color}")
    table.add_row("Đánh giá an toàn tài chính", prof["solvency_rating_vi"], style=f"bold {status_color}")
    table.add_row("Kết luận & Xử lý luật định", prof["regulatory_verdict"])

    console.print(table)
    console.print(f"[dim]Tiêu chuẩn áp dụng: {result['statutory_reference']}[/dim]")


def claim_cmd(
    policy_id: str = typer.Argument(..., help="Số hợp đồng bảo hiểm phát sinh tổn thất"),
    incident: str = typer.Argument(..., help="Mô tả sự kiện bảo hiểm / vụ việc tổn thất"),
    claimed_amount: float = typer.Argument(..., help="Số tiền khiếu nại bồi thường (VND)"),
    verified: bool = typer.Option(True, "--verified/--unverified", help="Hồ sơ chứng từ giám định tổn thất hợp lệ"),
    approved: bool = typer.Option(True, "--approved/--rejected", help="Duyệt bồi thường bảo hiểm"),
    deductible: typing.Optional[float] = typer.Option(None, "--deductible", "-d", help="Mức khấu trừ ghi đè (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Xử lý giám định tổn thất, khấu trừ miễn thường và chi trả bồi thường bảo hiểm."""
    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    result = engine.settle_claim(
        policy_id=policy_id,
        incident_description=incident,
        claimed_amount_vnd=claimed_amount,
        damage_proof_verified=verified,
        is_approved=approved,
        custom_deductible_vnd=deductible,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["claim_profile"]
    status_color = "green" if prof["is_approved"] and prof["damage_proof_verified"] else "red"

    table = Table(title=f"Quyết Định Giải Quyết Bồi Thường — Hồ Sơ {prof['claim_id']}")
    table.add_column("Hạng mục giám định & bồi thường", style="cyan")
    table.add_column("Thông số bồi thường", justify="right", style="bold")

    table.add_row("Mã hồ sơ bồi thường", prof["claim_id"])
    table.add_row("Số hợp đồng bảo hiểm", prof["policy_id"])
    table.add_row("Mô tả sự kiện bảo hiểm", prof["incident_description"])
    table.add_row("Số tiền yêu cầu bồi thường", f"{prof['claimed_amount_vnd']:,.0f} VND")
    table.add_row("Mức khấu trừ áp dụng", f"{prof['deductible_vnd']:,.0f} VND")
    table.add_row("Số tiền thực tế chi trả", f"{prof['net_settled_amount_vnd']:,.0f} VND", style=f"bold {status_color}")
    table.add_row("Chứng từ tổn thất", "HỢP LỆ ĐẦY ĐỦ" if prof["damage_proof_verified"] else "CHƯA HỢP LỆ")
    table.add_row("Trạng thái chi trả", prof["settlement_status"], style=f"bold {status_color}")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


def reserve_cmd(
    insurer: str = typer.Argument(..., help="Tên doanh nghiệp bảo hiểm"),
    line: str = typer.Argument("MOTOR_VEHICLE", help="Nghiệp vụ: MOTOR_VEHICLE, FIRE_EXPLOSION, CARGO_MARINE, HEALTH_ACCIDENT, LIFE_TERM"),
    written_premium: float = typer.Option(50_000_000_000.0, "--written-premium", "-w", help="Phí bảo hiểm gốc thu trong kỳ (VND)"),
    unearned_ratio: float = typer.Option(0.50, "--unearned-ratio", "-u", help="Hệ số phí chưa được hưởng (0.0 đến 1.0)"),
    outstanding_claims: float = typer.Option(10_000_000_000.0, "--outstanding-claims", "-o", help="Dự phòng bồi thường khiếu nại chưa giải quyết (OCR - VND)"),
    ibnr_rate: float = typer.Option(0.05, "--ibnr-rate", help="Tỷ lệ dự phòng IBNR (mặc định 5% phí gốc)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán và trích lập dự phòng nghiệp vụ kỹ thuật (UPR, OCR, IBNR) theo chuẩn Bộ Tài chính."""
    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    result = engine.calculate_technical_reserves(
        insurer_name=insurer,
        product_line=line,
        written_premium_vnd=written_premium,
        unearned_ratio=unearned_ratio,
        outstanding_claims_vnd=outstanding_claims,
        ibnr_rate=ibnr_rate,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["reserve_profile"]
    table = Table(title=f"Báo Cáo Trích Lập Dự Phòng Nghiệp Vụ — {prof['insurer_name']}")
    table.add_column("Khoản mục dự phòng nghiệp vụ", style="cyan")
    table.add_column("Số tiền trích lập (VND)", justify="right", style="bold")

    table.add_row("Mã bảng tính dự phòng", prof["reserve_id"])
    table.add_row("Doanh nghiệp bảo hiểm", prof["insurer_name"])
    table.add_row("Nghiệp vụ áp dụng", prof["product_line"])
    table.add_row("Phí bảo hiểm gốc", f"{prof['written_premium_vnd']:,.0f} VND")
    table.add_row("Dự phòng phí chưa được hưởng (UPR)", f"{prof['unearned_premium_reserve_vnd']:,.0f} VND")
    table.add_row("Dự phòng bồi thường khiếu nại (OCR)", f"{prof['outstanding_claim_reserve_vnd']:,.0f} VND")
    table.add_row("Dự phòng phát sinh chưa khiếu nại (IBNR)", f"{prof['ibnr_reserve_vnd']:,.0f} VND")
    table.add_row("TỔNG DỰ PHÒNG KỸ THUẬT", f"{prof['total_reserves_vnd']:,.0f} VND", style="bold green")

    console.print(table)
    console.print(f"[dim]Tiêu chuẩn trích lập: {result['statutory_reference']}[/dim]")
