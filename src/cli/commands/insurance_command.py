# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Insurance Business, Actuarial Solvency & Underwriting (Phase 77)."""

from __future__ import annotations

import json
import typing
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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

    engine = InsuranceEngine()
    result = engine.issue_insurer_license(
        enterprise_name=name,
        tax_id=tax_id,
        license_type=license_type,
        charter_capital_vnd=capital,
        legal_representative=rep,
        head_office=office,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["license_profile"]
    table = Table(title=f"Giấy Phép Thành Lập & Hoạt Động Bảo Hiểm — {prof['enterprise_name']}")
    table.add_column("Chỉ tiêu thẩm định giấy phép", style="cyan")
    table.add_column("Thông số ghi nhận", justify="right", style="bold green")

    table.add_row("Số giấy phép hoạt động", prof["license_number"])
    table.add_row("Tên doanh nghiệp bảo hiểm", prof["enterprise_name"])
    table.add_row("Mã số thuế", prof["tax_id"])
    table.add_row("Loại hình nghiệp vụ", prof["license_name_vi"])
    table.add_row("Vốn điều lệ thực góp", f"{prof['charter_capital_vnd']:,.0f} VND")
    table.add_row("Mức vốn tối thiểu quy định", f"{prof['min_required_capital_vnd']:,.0f} VND")
    table.add_row("Người đại diện pháp luật", prof["legal_representative"])
    table.add_row("Trụ sở chính", prof["head_office"])
    table.add_row("Cơ quan cấp phép", prof["licensing_authority"])
    table.add_row("Trạng thái hoạt động", prof["status"])

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

    engine = InsuranceEngine()
    result = engine.underwrite_policy(
        policyholder_name=holder,
        product_line=line,
        sum_insured_vnd=sum_insured,
        premium_vnd=premium,
        deductible_vnd=deductible,
        term_months=months,
        start_date=date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    prof = result["policy_profile"]
    table = Table(title=f"Hợp Đồng / Giấy Chứng Nhận Bảo Hiểm — Mã {prof['policy_id']}")
    table.add_column("Điều khoản hợp đồng bảo hiểm", style="cyan")
    table.add_column("Chi tiết hợp đồng", justify="right", style="bold")

    table.add_row("Số hợp đồng bảo hiểm", prof["policy_id"])
    table.add_row("Bên mua bảo hiểm", prof["policyholder_name"])
    table.add_row("Nghiệp vụ bảo hiểm", prof["product_name_vi"])
    table.add_row("Phân loại danh mục", prof["category"])
    table.add_row("Số tiền bảo hiểm (STBH)", f"{prof['sum_insured_vnd']:,.0f} VND", style="bold green")
    table.add_row("Phí bảo hiểm nộp", f"{prof['premium_vnd']:,.0f} VND", style="bold cyan")
    table.add_row("Mức khấu trừ tổn thất", f"{prof['deductible_vnd']:,.0f} VND / vụ")
    table.add_row("Thời hạn hợp đồng", f"{prof['term_months']} tháng (Từ {prof['start_date']} đến {prof['end_date']})")
    table.add_row("Thời gian cân nhắc (Free-look)", f"{prof['free_look_days']} ngày")
    table.add_row("Trạng thái hiệu lực", prof["status"], style="bold green")

    console.print(table)
    console.print(f"[dim]Căn cứ pháp lý: {result['statutory_reference']}[/dim]")


@insurance_app.command("solvency")
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


@insurance_app.command("claim")
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


@insurance_app.command("reserve")
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


@insurance_app.command("list")
def list_cmd(
    resource: str = typer.Argument("licenses", help="Tài nguyên: 'licenses', 'policies', 'solvency', 'claims', 'reserves'"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu danh mục giấy phép doanh nghiệp BH, hợp đồng, an toàn vốn, khiếu nại bồi thường, dự phòng."""
    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    res_type = resource.lower().strip()

    if res_type in ("licenses", "license"):
        items = engine.list_licenses(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giấy Phép Doanh Nghiệp Bảo Hiểm")
        table.add_column("Số Giấy Phép", style="cyan")
        table.add_column("Tên Doanh Nghiệp BH", style="bold")
        table.add_column("Mã Số Thuế")
        table.add_column("Loại Hình")
        table.add_column("Vốn Điều Lệ", justify="right")
        table.add_column("Đại Diện")
        for item in items.data:
            table.add_row(
                item["license_number"],
                item["enterprise_name"],
                item["tax_id"],
                item["license_type"],
                f"{item['charter_capital_vnd']:,.0f} VND",
                item["legal_representative"],
            )
        console.print(table)

    elif res_type in ("policies", "policy"):
        items = engine.list_policies(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Hợp Đồng Bảo Hiểm Đang Hiệu Lực")
        table.add_column("Mã Hợp Đồng", style="cyan")
        table.add_column("Bên Mua Bảo Hiểm", style="bold")
        table.add_column("Nghiệp Vụ")
        table.add_column("STBH", justify="right", style="bold green")
        table.add_column("Phí Bảo Hiểm", justify="right", style="cyan")
        table.add_column("Khấu Trừ", justify="right")
        table.add_column("Thời Hạn", justify="center")
        for item in items.data:
            table.add_row(
                item["policy_id"],
                item["policyholder_name"],
                item["product_line"],
                f"{item['sum_insured_vnd']:,.0f} VND",
                f"{item['premium_vnd']:,.0f} VND",
                f"{item['deductible_vnd']:,.0f} VND",
                f"{item['term_months']}T",
            )
        console.print(table)

    elif res_type in ("solvency", "solvency_audits"):
        items = engine.list_solvency_audits(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Kiểm Tra Biên Khả Năng Thanh Toán (CAR)")
        table.add_column("Mã Audit", style="cyan")
        table.add_column("Doanh Nghiệp BH", style="bold")
        table.add_column("Biên Thực Tế", justify="right")
        table.add_column("Biên Tối Thiểu", justify="right")
        table.add_column("Tỷ Lệ CAR", justify="center", style="bold")
        table.add_column("Trạng Thái", justify="center")
        for item in items.data:
            st_color = "green" if item["capital_adequacy_ratio"] >= 1.0 else "red"
            table.add_row(
                item["audit_id"],
                item["insurer_name"],
                f"{item['actual_margin_vnd']:,.0f} VND",
                f"{item['minimum_margin_vnd']:,.0f} VND",
                f"[{st_color}]{item['capital_adequacy_ratio'] * 100:.2f}%[/]",
                f"[{st_color}]{item['solvency_status']}[/]",
            )
        console.print(table)

    elif res_type in ("claims", "claim"):
        items = engine.list_claims(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Giải Quyết Khiếu Nại Bồi Thường")
        table.add_column("Mã Claim", style="cyan")
        table.add_column("Mã Hợp Đồng")
        table.add_column("Mô Tả Tổn Thất", style="bold")
        table.add_column("Yêu Cầu", justify="right")
        table.add_column("Chi Trả Thực Tế", justify="right", style="bold green")
        table.add_column("Trạng Thái", justify="center")
        for item in items.data:
            table.add_row(
                item["claim_id"],
                item["policy_id"],
                item["incident_description"],
                f"{item['claimed_amount_vnd']:,.0f} VND",
                f"{item['net_settled_amount_vnd']:,.0f} VND",
                item["settlement_status"],
            )
        console.print(table)

    elif res_type in ("reserves", "reserve"):
        items = engine.list_reserves(limit=limit)
        if json_mode:
            typer.echo(json.dumps(items.data, indent=2, ensure_ascii=False))
            return
        table = Table(title="Danh Sách Trích Lập Dự Phòng Nghiệp Vụ Kỹ Thuật")
        table.add_column("Mã Reserve", style="cyan")
        table.add_column("Doanh Nghiệp BH", style="bold")
        table.add_column("Nghiệp Vụ")
        table.add_column("UPR", justify="right")
        table.add_column("OCR", justify="right")
        table.add_column("IBNR", justify="right")
        table.add_column("Tổng Dự Phòng", justify="right", style="bold green")
        for item in items.data:
            table.add_row(
                item["reserve_id"],
                item["insurer_name"],
                item["product_line"],
                f"{item['unearned_premium_reserve_vnd']:,.0f} VND",
                f"{item['outstanding_claim_reserve_vnd']:,.0f} VND",
                f"{item['ibnr_reserve_vnd']:,.0f} VND",
                f"{item['total_reserves_vnd']:,.0f} VND",
            )
        console.print(table)

    else:
        typer.echo(f"Tài nguyên không hợp lệ: '{resource}'. Hỗ trợ: 'licenses', 'policies', 'solvency', 'claims', 'reserves'")


@insurance_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Tra cứu trạng thái telemetry tổng thể của thị trường kinh doanh bảo hiểm và an toàn vốn."""
    from src.core.insurance_engine import InsuranceEngine

    engine = InsuranceEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    m = status_data["metrics"]
    table = Table(title="Báo Cáo Telemetry Thị Trường Bảo Hiểm Việt Nam")
    table.add_column("Chỉ số an toàn vốn & thị trường bảo hiểm", style="cyan")
    table.add_column("Giá trị", justify="right", style="bold green")

    table.add_row("Doanh nghiệp bảo hiểm đang hoạt động", str(m["active_insurers"]))
    table.add_row("Số lượng đơn bảo hiểm đang hiệu lực", f"{m['in_force_policies']:,} đơn")
    table.add_row("Tổng số tiền bảo hiểm cam kết (STBH)", f"{m['total_sum_insured_vnd']:,.0f} VND")
    table.add_row("Tổng doanh thu phí bảo hiểm", f"{m['total_written_premium_vnd']:,.0f} VND")
    table.add_row("Tổng số hồ sơ bồi thường đã tiếp nhận", f"{m['total_claims_processed']:,} vụ")
    table.add_row("Tổng số tiền bồi thường đã chi trả", f"{m['total_claims_settled_vnd']:,.0f} VND")
    table.add_row("Tỷ lệ bồi thường thị trường (Loss Ratio)", m["loss_ratio_percent"])
    table.add_row("Đợt kiểm tra an toàn vốn biên thanh toán", str(m["solvency_audits_count"]))
    table.add_row("Số doanh nghiệp đạt chuẩn an toàn vốn", str(m["capital_compliant_insurers"]))
    table.add_row("Tổng quỹ dự phòng nghiệp vụ kỹ thuật", f"{m['total_technical_reserves_vnd']:,.0f} VND")

    console.print(table)
