# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Insurance Business, Actuarial Solvency & Underwriting (Phase 77)."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands._insurance_actuarial import (
    claim_cmd,
    register_insurance_actuarial,
    reserve_cmd,
    solvency_cmd,
)
from src.cli.commands._insurance_queries import (
    list_cmd,
    register_insurance_queries,
    status_cmd,
)

console = Console()
insurance_app = typer.Typer(
    name="insurance",
    help="Insurance — Vietnamese Insurance Business, Actuarial Solvency & Underwriting",
    add_completion=False,
)


@insurance_app.callback(invoke_without_command=True)
def insurance_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Kinh doanh Bảo hiểm, An toàn Vốn & Trích lập Dự phòng."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ KINH DOANH BẢO HIỂM & BIÊN KHẢ NĂNG THANH TOÁN (LUẬT KDBH 2022)[/]\n\n"
            f"  Khung pháp lý:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Cơ quan quản lý:     [bold]{status_data['regulatory_authority']}[/]\n"
            f"  Doanh nghiệp BH:     [bold cyan]{m['active_insurers']} doanh nghiệp bảo hiểm đang hoạt động[/]\n"
            f"  Hợp đồng hiệu lực:   [bold green]{m['in_force_policies']:,} đơn bảo hiểm[/] (Tổng STBH: [bold green]{m['total_sum_insured_vnd']:,.0f} VND[/])\n"
            f"  Tổng doanh thu phí:  [bold cyan]{m['total_written_premium_vnd']:,.0f} VND[/]\n"
            f"  Hồ sơ bồi thường:    [bold]{m['total_claims_processed']:,} vụ tổn thất[/] (Đã chi trả: [bold red]{m['total_claims_settled_vnd']:,.0f} VND[/])\n"
            f"  Tỷ lệ bồi thường:    [bold yellow]{m['loss_ratio_percent']}[/] (Loss Ratio)\n"
            f"  An toàn vốn (CAR):   [bold green]{m['capital_compliant_insurers']}/{m['solvency_audits_count']} đợt kiểm tra đạt chuẩn biên thanh toán[/]\n"
            f"  Dự phòng nghiệp vụ:  [bold green]{m['total_technical_reserves_vnd']:,.0f} VND[/]",
            title="[bold blue]Vietnam Insurance & Actuarial Solvency Telemetry[/]",
            border_style="green",
        )
    )


@insurance_app.command("license")
def license_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp xin cấp phép bảo hiểm (vd: 'Tổng Công ty Bảo hiểm Quân đội')"),
    tax_id: str = typer.Argument(..., help="Mã số thuế doanh nghiệp"),
    license_type: str = typer.Option("NON_LIFE_INSURANCE", "--type", "-t", help="Loại giấy phép: NON_LIFE_INSURANCE, NON_LIFE_SPECIALTY, LIFE_INSURANCE, LIFE_UNIT_LINKED, REINSURANCE, INSURANCE_BROKERAGE"),
    capital: float = typer.Option(400_000_000_000.0, "--capital", "-c", help="Vốn điều lệ thực góp (VND)"),
    rep: str = typer.Option("Nguyễn Văn Hùng", "--rep", "-r", help="Người đại diện theo pháp luật"),
    office: str = typer.Option("Hà Nội", "--office", "-o", help="Địa chỉ trụ sở chính"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm tra vốn điều lệ và cấp Giấy phép thành lập doanh nghiệp bảo hiểm theo Luật Kinh doanh bảo hiểm 2022."""
    from src.core.insurance_engine import InsuranceEngine

    result = InsuranceEngine().issue_insurer_license(
        enterprise_name=name, tax_id=tax_id, license_type=license_type,
        charter_capital_vnd=capital, legal_representative=rep, head_office=office,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Giấy Phép Thành Lập & Hoạt Động Bảo Hiểm — {prof['enterprise_name']}")
    table.add_column("Chỉ tiêu thẩm định giấy phép", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")
    for k, v in [
        ("Số giấy phép hoạt động", prof["license_number"]), ("Tên doanh nghiệp bảo hiểm", prof["enterprise_name"]),
        ("Mã số thuế", prof["tax_id"]), ("Loại hình nghiệp vụ", prof["license_name_vi"]),
        ("Vốn điều lệ thực góp", f"{prof['charter_capital_vnd']:,.0f} VND"),
        ("Mức vốn tối thiểu quy định", f"{prof['min_required_capital_vnd']:,.0f} VND"),
        ("Người đại diện pháp luật", prof["legal_representative"]), ("Trụ sở chính", prof["head_office"]),
        ("Cơ quan cấp phép", prof["licensing_authority"]), ("Trạng thái hoạt động", prof["status"]),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@insurance_app.command("policy")
def policy_cmd(
    holder: str = typer.Argument(..., help="Tên bên mua bảo hiểm (Tổ chức / Cá nhân)"),
    line: str = typer.Argument("MOTOR_VEHICLE", help="Nghiệp vụ: MOTOR_VEHICLE, FIRE_EXPLOSION, CARGO_MARINE, HEALTH_ACCIDENT, LIFE_TERM, LIFE_ENDOWMENT, LIFE_UNIT_LINKED"),
    sum_insured: float = typer.Option(1_000_000_000.0, "--sum-insured", "-s", help="Số tiền bảo hiểm (STBH - VND)"),
    premium: float = typer.Option(15_000_000.0, "--premium", "-p", help="Phí bảo hiểm định kỳ/trọn gói (VND)"),
    deductible: float = typer.Option(1_000_000.0, "--deductible", "-d", help="Mức khấu trừ / miễn thường (VND)"),
    months: int = typer.Option(12, "--months", "-m", help="Thời hạn hợp đồng (tháng)"),
    date: str = typer.Option("2026-10-01", "--date", help="Ngày hiệu lực hợp đồng (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định rủi ro và phát hành Giấy chứng nhận bảo hiểm / Hợp đồng bảo hiểm."""
    from src.core.insurance_engine import InsuranceEngine

    result = InsuranceEngine().underwrite_policy(
        policyholder_name=holder, product_line=line, sum_insured_vnd=sum_insured,
        premium_vnd=premium, deductible_vnd=deductible, term_months=months, start_date=date,
    )
    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["policy_profile"]
    table = Table(title=f"Hợp Đồng / Giấy Chứng Nhận Bảo Hiểm — Mã {prof['policy_id']}")
    table.add_column("Điều khoản hợp đồng bảo hiểm", style="cyan")
    table.add_column("Chi tiết hợp đồng", justify="right", style="bold")
    for k, v in [
        ("Số hợp đồng bảo hiểm", prof["policy_id"]), ("Bên mua bảo hiểm", prof["policyholder_name"]),
        ("Nghiệp vụ bảo hiểm", prof["product_name_vi"]), ("Phân loại danh mục", prof["category"]),
        ("Số tiền bảo hiểm (STBH)", f"[bold green]{prof['sum_insured_vnd']:,.0f} VND[/bold green]"),
        ("Phí bảo hiểm nộp", f"[bold cyan]{prof['premium_vnd']:,.0f} VND[/bold cyan]"),
        ("Mức khấu trừ tổn thất", f"{prof['deductible_vnd']:,.0f} VND / vụ"),
        ("Thời hạn hợp đồng", f"{prof['term_months']} tháng (Từ {prof['start_date']} đến {prof['end_date']})"),
        ("Thời gian cân nhắc (Free-look)", f"{prof['free_look_days']} ngày"),
        ("Trạng thái hiệu lực", f"[bold green]{prof['status']}[/bold green]"),
    ]:
        table.add_row(k, v)
    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


register_insurance_actuarial(insurance_app)
register_insurance_queries(insurance_app)

__all__ = ["insurance_app", "insurance_main", "license_cmd", "policy_cmd", "solvency_cmd", "claim_cmd", "reserve_cmd", "list_cmd", "status_cmd"]
