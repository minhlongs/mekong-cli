# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Public Investment, Capital Allocation & Medium-Term Planning Suite (Phase 118)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

pubinvestment_app = typer.Typer(
    name="pubinvestment",
    help="Vietnamese Public Investment, Capital Allocation & Medium-Term Planning Suite.",
)
console = Console()


@pubinvestment_app.callback(invoke_without_command=True)
def pubinvestment_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động quản lý đầu tư công, phân bổ kế hoạch vốn và giải ngân Kho bạc Nhà nước."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    telemetry = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    reg = telemetry["regulatory_framework"]
    prj = telemetry["projects"]
    cap = telemetry["capital_and_disbursement"]
    btn = telemetry["bottlenecks"]

    rate_color = "green" if cap["national_disbursement_rate_pct"] >= 80 else ("yellow" if cap["national_disbursement_rate_pct"] >= 50 else "red")

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN LÝ ĐẦU TƯ CÔNG, KẾ HOẠCH VỐN & GIẢI NGÂN KBNN QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:               [bold]{reg['law']}[/]\n"
            f"  Nghị định hướng dẫn thi hành:[bold yellow]{reg['decree_guideline']}[/] | Quản lý thanh toán vốn: [bold yellow]{reg['decree_payment']}[/]\n\n"
            f"  Dự án đầu tư công đăng ký:   [bold]{prj['total']}[/] dự án ([bold red]{prj['national_special']}[/] QTQG, [bold magenta]{prj['group_a']}[/] Nhóm A, [bold blue]{prj['group_b']}[/] Nhóm B, [bold cyan]{prj['group_c']}[/] Nhóm C)\n"
            f"  - Tổng mức đầu tư cam kết:   [bold yellow]{prj['total_committed_vnd']:,.0f} VND[/]\n\n"
            f"  Kế hoạch vốn giao trong năm: [bold]{cap['total_annual_allocated_vnd']:,.0f} VND[/]\n"
            f"  Số vốn đã giải ngân (KBNN):  [bold green]{cap['total_disbursed_vnd']:,.0f} VND[/]\n"
            f"  - Tỷ lệ giải ngân toàn quốc: [bold {rate_color}]{cap['national_disbursement_rate_pct']}%[/]\n\n"
            f"  Điểm nghẽn tiến độ ghi nhận: [bold]{btn['total_reported']}[/] vướng mắc ([bold red]{btn['critical_unresolved']}[/] điểm nghẽn nghiêm trọng)",
            title="[bold blue]Vietnam Public Investment Management & Capital Disbursement Telemetry[/]",
            border_style="blue",
        )
    )


@pubinvestment_app.command("project")
def project_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Mã dự án đầu tư công (e.g. PRJ-METRO-02)"),
    name: str = typer.Option(..., "--name", "-n", help="Tên dự án đầu tư công"),
    sector: str = typer.Option("TRANSPORT_ENERGY_INDUSTRY", "--sector", help="Lĩnh vực (TRANSPORT_ENERGY_INDUSTRY, AGRICULTURE_IRRIGATION_URBAN, HEALTH_EDUCATION_CULTURE, OTHER_INFRASTRUCTURE)"),
    capital: float = typer.Option(..., "--capital", help="Tổng mức đầu tư dự án (VND)"),
    source: str = typer.Option("CENTRAL_BUDGET", "--source", help="Nguồn vốn (CENTRAL_BUDGET, LOCAL_BUDGET, ODA_CONCESSIONAL, GOVERNMENT_BONDS, STATE_DEVELOPMENT)"),
    agency: str = typer.Option(..., "--agency", help="Cơ quan chủ quản / Chủ đầu tư"),
    location: str = typer.Option(..., "--location", help="Địa điểm thực hiện dự án (Tỉnh/Thành phố)"),
    start_year: int = typer.Option(2026, "--start", help="Năm khởi công dự kiến"),
    end_year: int = typer.Option(2030, "--end", help="Năm hoàn thành dự kiến"),
    resettlement: int = typer.Option(0, "--resettlement", help="Số người dân thuộc diện di dân tái định cư"),
    sensitive: bool = typer.Option(False, "--sensitive", help="Dự án có ảnh hưởng lớn đến môi trường hoặc an ninh quốc phòng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký dự án đầu tư công và xác định thẩm quyền quyết định chủ trương đầu tư (Điều 6-10 & 17-18)."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    try:
        res = engine.register_project(
            project_code=code,
            project_name=name,
            sector=sector,
            total_investment_vnd=capital,
            capital_source=source,
            managing_agency=agency,
            implementation_location=location,
            start_year=start_year,
            end_year=end_year,
            resettlement_people=resettlement,
            is_nationally_sensitive=sensitive,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi đăng ký dự án đầu tư công:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐĂNG KÝ DỰ ÁN ĐẦU TƯ CÔNG THÀNH CÔNG[/]\n\n"
            f"  Mã dự án (ID):             [bold yellow]{res['project_id']}[/] ({res['project_code']})\n"
            f"  Tên dự án:                 [bold]{res['project_name']}[/]\n"
            f"  Lĩnh vực:                  [bold]{res['sector']}[/] | Địa điểm: [bold]{res['implementation_location']}[/]\n"
            f"  Tổng mức đầu tư:           [bold cyan]{res['total_investment_vnd']:,.0f} VND[/] ({res['capital_source']})\n"
            f"  Phân loại dự án:           [bold red]{res['classification']} — {res['classification_name']}[/]\n"
            f"  Thời gian thực hiện:       [bold]{res['duration']}[/]\n\n"
            f"  Cơ quan quyết định CTĐT:   [bold green]{res['competent_authority']}[/]\n"
            f"  Hồ sơ nghiên cứu bắt buộc: [bold]{res['study_type_required']}[/]",
            title="[bold blue]Public Investment Project Registered (Law 39/2019/QH14)[/]",
            border_style="green",
        )
    )


@pubinvestment_app.command("classify")
def classify_cmd(
    sector: str = typer.Option("TRANSPORT_ENERGY_INDUSTRY", "--sector", help="Lĩnh vực đầu tư"),
    capital: float = typer.Option(..., "--capital", "-c", help="Tổng mức đầu tư dự án (VND)"),
    resettlement: int = typer.Option(0, "--resettlement", help="Số người di dân tái định cư"),
    sensitive: bool = typer.Option(False, "--sensitive", help="Có ảnh hưởng quốc phòng / an ninh / môi trường nhạy cảm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu tiêu chí phân loại dự án (QTQG, Nhóm A, B, C) và cấp có thẩm quyền phê duyệt."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    try:
        res = PublicInvestmentEngine.classify_project(
            sector=sector,
            total_investment_vnd=capital,
            resettlement_people=resettlement,
            is_nationally_sensitive=sensitive,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi phân loại dự án:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]KẾT QUẢ PHÂN LOẠI DỰ ÁN ĐẦU TƯ CÔNG[/]\n\n"
            f"  Phân loại dự án:           [bold red]{res['classification']} — {res['classification_name']}[/]\n"
            f"  Căn cứ pháp lý:            [bold]{res['statutory_basis']}[/]\n"
            f"  Thẩm quyền quyết định CTĐT:[bold green]{res['competent_deciding_authority']}[/]\n"
            f"  Thẩm quyền quyết định ĐT:  [bold]{res['approving_authority']}[/]\n"
            f"  Yêu cầu lập báo cáo:       [bold yellow]{res['study_type_required']}[/]",
            title="[bold blue]Project Classification Assessment[/]",
            border_style="blue",
        )
    )


@pubinvestment_app.command("plan")
def plan_cmd(
    project_id: str = typer.Argument(..., help="Mã dự án (PRJ-...)"),
    type: str = typer.Option("ANNUAL", "--type", help="Loại kế hoạch vốn (ANNUAL, MEDIUM_TERM)"),
    year: int = typer.Option(2026, "--year", help="Năm kế hoạch tài chính"),
    capital: float = typer.Option(..., "--capital", help="Số vốn phân bổ giao kế hoạch (VND)"),
    approver: str = typer.Option("Thủ tướng Chính phủ", "--approver", help="Cơ quan giao kế hoạch vốn"),
    decision: str = typer.Option("Quyết định số 168/QĐ-TTg", "--decision", help="Số quyết định giao vốn"),
    priority: int = typer.Option(5, "--priority", help="Thứ tự ưu tiên phân bổ Điều 51 (1: Thu hồi tạm ứng, 2: Nợ XDCB, 3: ODA, 4: Chuyển tiếp, 5: Khởi công mới)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Giao kế hoạch vốn đầu tư công trung hạn hoặc hằng năm theo thứ tự ưu tiên Điều 51."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    try:
        res = engine.allocate_capital_plan(
            project_id=project_id,
            plan_type=type,
            fiscal_year=year,
            allocated_capital_vnd=capital,
            approved_by=approver,
            decision_number=decision,
            priority_tier=priority,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi phân bổ kế hoạch vốn:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]PHÂN BỔ KẾ HOẠCH VỐN ĐẦU TƯ CÔNG THÀNH CÔNG[/]\n\n"
            f"  Mã kế hoạch vốn:           [bold yellow]{res['plan_id']}[/]\n"
            f"  Dự án:                     [bold]{res['project_name']}[/] ({res['project_id']})\n"
            f"  Loại kế hoạch:             [bold]{res['plan_type']}[/] (Năm: [bold]{res['fiscal_year']}[/])\n"
            f"  Số vốn phân bổ:            [bold cyan]{res['allocated_capital_vnd']:,.0f} VND[/]\n"
            f"  Thứ tự ưu tiên:            [bold]{res['priority_description']}[/]\n"
            f"  Cơ quan phê duyệt:         [bold]{res['approved_by']}[/] (Số QĐ: {res['decision_number']})",
            title="[bold blue]Capital Plan Allocated[/]",
            border_style="green",
        )
    )


@pubinvestment_app.command("disburse")
def disburse_cmd(
    project_id: str = typer.Argument(..., help="Mã dự án (PRJ-...)"),
    amount: float = typer.Option(..., "--amount", "-a", help="Số tiền thanh toán giải ngân (VND)"),
    year: int = typer.Option(2026, "--year", help="Năm ngân sách thực hiện giải ngân"),
    treasury: str = typer.Option("Kho bạc Nhà nước TP. Hà Nội", "--treasury", help="Kho bạc Nhà nước kiểm soát thanh toán"),
    voucher: str = typer.Option(..., "--voucher", help="Số giấy rút vốn / lệnh chi tiền KBNN"),
    contractor: str = typer.Option(..., "--contractor", help="Đơn vị nhà thầu / bên thụ hưởng thanh toán"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Ghi chú nội dung thanh toán khối lượng hoàn thành"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ghi nhận chứng từ giải ngân vốn qua Kho bạc Nhà nước theo Nghị định 99/2021/NĐ-CP."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    try:
        res = engine.record_disbursement(
            project_id=project_id,
            fiscal_year=year,
            disbursed_amount_vnd=amount,
            treasury_office=treasury,
            payment_voucher_number=voucher,
            recipient_contractor=contractor,
            notes=notes,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi ghi nhận giải ngân KBNN:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    rate_color = "green" if res["disbursement_rate_pct"] >= 80 else ("yellow" if res["disbursement_rate_pct"] >= 50 else "red")
    console.print(
        Panel(
            f"[bold green]GHI NHẬN GIẢI NGÂN VỐN KHO BẠC NHÀ NƯỚC THÀNH CÔNG[/]\n\n"
            f"  Mã giải ngân:              [bold yellow]{res['disbursement_id']}[/]\n"
            f"  Dự án:                     [bold]{res['project_name']}[/]\n"
            f"  Số tiền giải ngân đợt này: [bold cyan]{res['disbursed_amount_vnd']:,.0f} VND[/]\n"
            f"  Tổng giải ngân năm {res['fiscal_year']}:   [bold]{res['total_disbursed_year_vnd']:,.0f} VND[/] / [bold]{res['allocated_capital_year_vnd']:,.0f} VND[/]\n"
            f"  Tỷ lệ giải ngân năm:       [bold {rate_color}]{res['disbursement_rate_pct']}%[/]\n"
            f"  Kho bạc thực hiện:         [bold]{res['treasury_office']}[/] (Chứng từ: [bold]{res['payment_voucher_number']}[/])\n"
            f"  Nhà thầu thụ hưởng:        [bold]{res['recipient_contractor']}[/]",
            title="[bold blue]State Treasury Disbursement Recorded[/]",
            border_style="green",
        )
    )


@pubinvestment_app.command("bottleneck")
def bottleneck_cmd(
    project_id: str = typer.Argument(..., help="Mã dự án gặp khó khăn vướng mắc (PRJ-...)"),
    type: str = typer.Option("LAND_CLEARANCE", "--type", help="Loại điểm nghẽn (LAND_CLEARANCE, BIDDING_PROCEDURE, MATERIAL_PRICE_SPIKE, ODA_DONOR_APPROVAL, ENVIRONMENT_PERMIT, CONTRACTOR_CAPACITY)"),
    severity: str = typer.Option("HIGH", "--severity", help="Mức độ nghiêm trọng (LOW, MEDIUM, HIGH, CRITICAL)"),
    delay: int = typer.Option(6, "--delay", help="Dự kiến số tháng chậm tiến độ"),
    measures: str = typer.Option(..., "--measures", "-m", help="Biện pháp tháo gỡ khó khăn, thúc đẩy giải ngân"),
    party: str = typer.Option(..., "--party", help="Cơ quan / Đơn vị chịu trách nhiệm xử lý"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Ghi nhận và phân tích điểm nghẽn tiến độ dự án theo Nghị định 40/2020/NĐ-CP."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    try:
        res = engine.assess_bottleneck(
            project_id=project_id,
            bottleneck_type=type,
            severity_level=severity,
            estimated_delay_months=delay,
            mitigation_measures=measures,
            responsible_party=party,
        )
    except Exception as exc:
        console.print(f"[bold red]Lỗi ghi nhận điểm nghẽn dự án:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    sev_color = "red" if res["severity_level"] in ("HIGH", "CRITICAL") else "yellow"
    console.print(
        Panel(
            f"[bold {sev_color}]GHI NHẬN ĐIỂM NGHẼN TIẾN ĐỘ DỰ ÁN ĐẦU TƯ CÔNG[/]\n\n"
            f"  Mã cảnh báo (ID):          [bold yellow]{res['assessment_id']}[/]\n"
            f"  Dự án:                     [bold]{res['project_name']}[/]\n"
            f"  Loại điểm nghẽn:           [bold]{res['bottleneck_type']}[/]\n"
            f"  Mức độ nghiêm trọng:       [bold {sev_color}]{res['severity_level']}[/]\n"
            f"  Dự kiến chậm tiến độ:      [bold red]{res['estimated_delay_months']} tháng[/]\n"
            f"  Giải pháp tháo gỡ:         [bold]{res['mitigation_measures']}[/]\n"
            f"  Đơn vị chủ trì xử lý:      [bold green]{res['responsible_party']}[/]",
            title="[bold blue]Project Bottleneck Assessment[/]",
            border_style=sev_color,
        )
    )


@pubinvestment_app.command("list")
def list_cmd(
    type: str = typer.Option("all", "--type", help="Loại bản ghi (all, projects, plans, disbursements, bottlenecks)"),
    limit: int = typer.Option(20, "--limit", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Liệt kê danh sách dự án đầu tư công, kế hoạch vốn, đợt giải ngân và điểm nghẽn."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    records = engine.list_records(category=type, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "projects" in records and records["projects"]:
        table = Table(title="Danh Sách Dự Án Đầu Tư Công (Luật 39/2019/QH14)")
        table.add_column("Mã Dự Án", style="cyan")
        table.add_column("Tên Dự Án", style="bold")
        table.add_column("Lĩnh Vực", style="white")
        table.add_column("Phân Loại", style="magenta")
        table.add_column("Tổng Mức ĐT", style="yellow")
        table.add_column("Chủ Đầu Tư", style="green")
        for p in records["projects"]:
            table.add_row(
                p["project_code"],
                p["project_name"][:35],
                p["sector"],
                p["classification"],
                f"{p['total_investment_vnd']:,.0f} VND",
                p["managing_agency"][:25],
            )
        console.print(table)

    if "plans" in records and records["plans"]:
        table = Table(title="Kế Hoạch Vốn Đầu Tư Công Phân Bổ")
        table.add_column("Mã Kế Hoạch", style="cyan")
        table.add_column("Mã Dự Án", style="white")
        table.add_column("Loại Kế Hoạch", style="bold")
        table.add_column("Năm NS", style="yellow")
        table.add_column("Vốn Giao", style="green")
        table.add_column("Số Quyết Định", style="blue")
        for pl in records["plans"]:
            table.add_row(
                pl["plan_id"],
                pl["project_id"],
                pl["plan_type"],
                str(pl["fiscal_year"]),
                f"{pl['allocated_capital_vnd']:,.0f} VND",
                pl["decision_number"],
            )
        console.print(table)


@pubinvestment_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Báo cáo chỉ số telemetry và tốc độ giải ngân vốn đầu tư công toàn quốc."""
    from src.core.pubinvestment_engine import PublicInvestmentEngine

    engine = PublicInvestmentEngine()
    status = engine.get_telemetry_status()

    if json_mode:
        typer.echo(json.dumps(status, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]Public Investment Subsystem Status:[/] {status['status']}")
    console.print(f"Tổng số dự án: {status['projects']['total']} (QTQG: {status['projects']['national_special']}, Nhóm A: {status['projects']['group_a']}, Nhóm B: {status['projects']['group_b']}, Nhóm C: {status['projects']['group_c']})")
    console.print(f"Tổng vốn cam kết: {status['projects']['total_committed_vnd']:,.0f} VND")
    console.print(f"Vốn kế hoạch năm: {status['capital_and_disbursement']['total_annual_allocated_vnd']:,.0f} VND")
    console.print(f"Đã giải ngân: {status['capital_and_disbursement']['total_disbursed_vnd']:,.0f} VND ({status['capital_and_disbursement']['national_disbursement_rate_pct']}%)")
    console.print(f"Điểm nghẽn nghiêm trọng chưa xử lý: {status['bottlenecks']['critical_unresolved']}")
