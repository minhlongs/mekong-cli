# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Vietnamese Labor Code 2019, Foreign Work Permits & Safety Compliance (Phase 56)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
labor_app = typer.Typer(
    name="labor",
    help="Labor — Vietnamese Labor Code 2019, foreign work permits, overtime & internal labor regulations",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


@labor_app.callback(invoke_without_command=True)
def labor_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản trị Pháp luật Lao động, Giấy phép Lao động Nước ngoài & An toàn Lao động."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG PHÁP LUẬT LAO ĐỘNG & QUẢN LÝ LAO ĐỘNG NƯỚC NGOÀI[/]\n\n"
            f"  Khung pháp lý:         [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Tiêu chuẩn tham chiếu: [bold cyan]{status_data['standards']}[/]\n"
            f"  Lao động nước ngoài:   [bold]{metrics['total_foreign_workers_assessed']} chuyên gia/nhà quản lý[/] (Miễn GPLĐ: [bold green]{metrics['total_exempt_workers']}[/])\n"
            f"  Hồ sơ đề nghị GPLĐ:    [bold]{metrics['total_work_permit_applications']} bộ hồ sơ[/]\n"
            f"  Rà soát Nội quy LĐ:    [bold]{metrics['total_enterprises_audited']} doanh nghiệp[/] (Đạt chuẩn Sở: [bold green]{metrics['compliant_enterprises']}[/])",
            title="[bold blue]Vietnam Labor & Foreign Work Permit Dashboard[/]",
            border_style="green",
        )
    )


@labor_app.command("permit")
def evaluate_permit_cmd(
    worker_name: str = typer.Argument(..., help="Họ và tên người lao động nước ngoài"),
    nationality: str = typer.Argument(..., help="Quốc tịch (VD: Japan, Korea, USA, Germany, China)"),
    position: str = typer.Argument(..., help="Vị trí công việc (EXPERT, EXECUTIVE_DIRECTOR, MANAGING_DIRECTOR, TECHNICAL_WORKER)"),
    job_title: str = typer.Argument(..., help="Chức danh công việc cụ thể (VD: Giám đốc Kỹ thuật)"),
    degree: str = typer.Option("BACHELOR", "--degree", "-d", help="Trình độ đào tạo / bằng cấp"),
    exp: float = typer.Option(3.0, "--exp", "-e", help="Số năm kinh nghiệm phù hợp"),
    capital: float = typer.Option(0.0, "--capital", help="Vốn góp đầu tư tại Việt Nam (VND)"),
    wto: bool = typer.Option(False, "--wto", help="Di chuyển nội bộ 11 ngành dịch vụ WTO"),
    married_vn: bool = typer.Option(False, "--married-vn", help="Kết hôn với công dân Việt Nam"),
    passport: str = typer.Option("PASS-DEFAULT", "--passport", help="Số hộ chiếu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thẩm định điều kiện cấp Giấy phép lao động (GPLĐ) hoặc Xác nhận Miễn GPLĐ (Nghị định 70/2023/NĐ-CP)."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    result = engine.evaluate_work_permit_eligibility(
        worker_name=worker_name,
        nationality=nationality,
        position_category=position,
        job_title=job_title,
        education_degree=degree,
        experience_years=exp,
        capital_contribution_vnd=capital,
        is_wto_internal_transfer=wto,
        married_to_vietnamese=married_vn,
        passport_number=passport,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["eligibility_status"] == "QUALIFIED" else "red"

    console.print(
        Panel(
            f"[bold {status_color}]KẾT QUẢ THẨM ĐỊNH ĐIỀU KIỆN LAO ĐỘNG NƯỚC NGOÀI[/]\n\n"
            f"  Nhân sự:              [bold]{result['worker_name']}[/] (Quốc tịch: {result['nationality']})\n"
            f"  Vị trí / Chức danh:   [bold cyan]{result['position_category']}[/] — [bold]{result['job_title']}[/]\n"
            f"  Miễn Giấy phép LĐ:    [bold yellow]{'CÓ (THUỘC DIỆN MIỄN GPLĐ)' if result['is_exempt_from_work_permit'] else 'KHÔNG (PHẢI XIN CẤP GPLĐ)'}[/bold yellow]\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]KẾT LUẬN THẨM ĐỊNH:[/]  [bold {status_color}]{result['eligibility_status']}[/bold {status_color}]\n"
            f"  Quy trình thực hiện:  {result['statutory_procedure']}\n"
            f"  Căn cứ pháp lý:       {'; '.join(result['evaluation_notes'])}\n"
            f"  Hồ sơ cần chuẩn bị:   {len(result['statutory_dossier_checklist'])} mục chứng từ",
            title="[bold blue]Foreign Work Permit Advisory[/]",
            border_style=status_color,
        )
    )


@labor_app.command("overtime")
def calculate_overtime_cmd(
    hourly_rate: float = typer.Argument(..., help="Đơn giá tiền lương theo giờ (VND/giờ)"),
    day: float = typer.Option(0.0, "--day", help="Số giờ làm thêm ngày thường (150%)"),
    weekend: float = typer.Option(0.0, "--weekend", help="Số giờ làm thêm ngày nghỉ tuần (200%)"),
    holiday: float = typer.Option(0.0, "--holiday", help="Số giờ làm thêm ngày nghỉ lễ/Tết (300%)"),
    night: float = typer.Option(0.0, "--night", help="Số giờ làm việc ca đêm thường 22h-6h (+30%)"),
    night_ot: float = typer.Option(0.0, "--night-ot", help="Số giờ làm thêm ca đêm (200%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán tiền lương làm thêm giờ và làm việc ban đêm chuẩn xác theo Điều 98 Bộ luật Lao động 2019."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    result = engine.calculate_overtime_pay(
        hourly_rate_vnd=hourly_rate,
        normal_day_ot_hours=day,
        weekend_ot_hours=weekend,
        holiday_ot_hours=holiday,
        night_shift_regular_hours=night,
        night_shift_ot_hours=night_ot,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    b = result["breakdown"]

    console.print(
        Panel(
            f"[bold green]BẢNG TÍNH TIỀN LƯƠNG LÀM THÊM GIỜ & CA ĐÊM (ĐIỀU 98 BLLĐ)[/]\n\n"
            f"  Lương cơ sở mỗi giờ:  [bold]{_format_vnd(result['base_hourly_rate_vnd'])}/giờ[/]\n"
            f"  Làm thêm ngày thường (150%): [bold yellow]{b['normal_day_ot']['hours']} giờ[/] -> {_format_vnd(b['normal_day_ot']['amount_vnd'])}\n"
            f"  Làm thêm ngày nghỉ tuần (200%): [bold yellow]{b['weekend_rest_ot']['hours']} giờ[/] -> {_format_vnd(b['weekend_rest_ot']['amount_vnd'])}\n"
            f"  Làm thêm ngày Lễ/Tết (300%): [bold yellow]{b['holiday_tet_ot']['hours']} giờ[/] -> {_format_vnd(b['holiday_tet_ot']['amount_vnd'])}\n"
            f"  Phụ cấp làm việc ca đêm (30%): [bold cyan]{b['night_shift_surcharge']['hours']} giờ[/] -> {_format_vnd(b['night_shift_surcharge']['amount_vnd'])}\n"
            f"  Làm thêm giờ ca đêm (200%): [bold cyan]{b['night_overtime']['hours']} giờ[/] -> {_format_vnd(b['night_overtime']['amount_vnd'])}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG GIỜ LÀM THÊM:[/]   [bold]{result['total_overtime_hours']} giờ[/]\n"
            f"  [bold]TỔNG TIỀN LƯƠNG THỰC LĨNH:[/] [bold green]{_format_vnd(result['total_overtime_pay_vnd'])}[/bold green]",
            title="[bold blue]Statutory Overtime Calculation[/]",
            border_style="green",
        )
    )


@labor_app.command("caps")
def validate_caps_cmd(
    monthly_hours: float = typer.Argument(..., help="Số giờ làm thêm trong tháng"),
    yearly_hours: float = typer.Argument(..., help="Số giờ làm thêm lũy kế từ đầu năm đến nay"),
    extended: bool = typer.Option(False, "--extended", help="Ngành nghề được mở rộng làm thêm 300h/năm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra giới hạn trần làm thêm giờ theo tháng (<= 40h) và theo năm (<= 200h hoặc 300h) - Điều 107 BLLĐ."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    result = engine.validate_overtime_caps(
        monthly_overtime_hours=monthly_hours,
        yearly_cumulative_hours=yearly_hours,
        is_extended_industry=extended,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_compliant"] else "red"

    console.print(
        Panel(
            f"[bold {status_color}]KIỂM TRA HẠN MỨC LÀM THÊM GIỜ (ĐIỀU 107 BỘ LUẬT LAO ĐỘNG)[/]\n\n"
            f"  Số giờ làm thêm tháng: [bold]{result['monthly_hours']}h[/] / Trần quy định: [bold yellow]{result['monthly_cap']}h/tháng[/]\n"
            f"  Lũy kế làm thêm năm:   [bold]{result['yearly_cumulative_hours']}h[/] / Trần quy định: [bold yellow]{result['yearly_cap']}h/năm[/]\n"
            f"  Ngành nghề mở rộng 300h: {'Áp dụng' if result['is_extended_industry'] else 'Không áp dụng'}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]ĐÁNH GIÁ PHÁP LÝ:[/]   [bold {status_color}]{result['statutory_risk']}[/bold {status_color}]\n"
            + (f"  Vi phạm ghi nhận:     {'; '.join(result['violations'])}" if result['violations'] else ""),
            title="[bold blue]Overtime Statutory Cap Verification[/]",
            border_style=status_color,
        )
    )


@labor_app.command("severance")
def calculate_severance_cmd(
    salary: float = typer.Argument(..., help="Tiền lương bình quân 06 tháng liền kề (VND)"),
    total_months: int = typer.Argument(..., help="Tổng thời gian làm việc thực tế (tháng)"),
    bhtn_months: int = typer.Argument(..., help="Thời gian đã tham gia BHTN (tháng)"),
    term_type: str = typer.Option("SEVERANCE", "--type", "-t", help="Loại trợ cấp (SEVERANCE: Thôi việc, JOB_LOSS: Mất việc)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán trợ cấp thôi việc (Điều 46) hoặc trợ cấp mất việc làm (Điều 47) khi chấm dứt HĐLĐ."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    result = engine.calculate_termination_allowance(
        average_salary_vnd=salary,
        total_working_months=total_months,
        bhtn_working_months=bhtn_months,
        termination_type=term_type,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]TÍNH TOÁN TRỢ CẤP CHẤM DỨT HỢP ĐỒNG LAO ĐỘNG[/]\n\n"
            f"  Loại chế độ trợ cấp:  [bold cyan]{'TRỢ CẤP THÔI VIỆC (ĐIỀU 46)' if result['termination_type'] == 'SEVERANCE' else 'TRỢ CẤP MẤT VIỆC LÀM (ĐIỀU 47)'}[/]\n"
            f"  Lương bình quân 6 tháng:[bold]{_format_vnd(result['average_salary_6_months_vnd'])}[/]\n"
            f"  Tổng thời gian công tác:{result['total_tenure_months']} tháng (~ {result['total_tenure_months'] / 12:.1f} năm)\n"
            f"  Thời gian có đóng BHTN:{result['bhtn_covered_months']} tháng\n"
            f"  Thời gian tính trợ cấp: {result['qualifying_months_not_covered_by_bhtn']} tháng -> Làm tròn: [bold yellow]{result['calculated_tenure_years']} năm[/]\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TIỀN TRỢ CẤP PHẢI TRẢ:[/] [bold green]{_format_vnd(result['statutory_allowance_vnd'])}[/bold green]\n"
            f"  Căn cứ pháp lý:       {result['governing_article']}",
            title="[bold blue]Labor Contract Termination Allowance[/]",
            border_style="green",
        )
    )


@labor_app.command("regulations")
def audit_regulations_cmd(
    enterprise: str = typer.Argument(..., help="Tên doanh nghiệp được rà soát nội quy lao động"),
    employees: int = typer.Argument(..., help="Tổng số người lao động đang làm việc"),
    written: bool = typer.Option(True, "--written/--no-written", help="Có ban hành Nội quy lao động bằng văn bản"),
    registered: bool = typer.Option(True, "--registered/--unregistered", help="Đã đăng ký NQLĐ với Sở LĐ-TB&XH"),
    filing_num: str = typer.Option("NQLD-2026-DOLAB", "--filing-num", help="Số tiếp nhận đăng ký NQLĐ tại Sở"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Rà soát tính hợp pháp của Nội quy lao động và nghĩa vụ đăng ký Sở LĐ-TB&XH (Điều 118 & 119 BLLĐ)."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    result = engine.audit_internal_regulations(
        enterprise_name=enterprise,
        total_employees=employees,
        has_written_regulations=written,
        is_registered_with_dolab=registered,
        dolab_filing_number=filing_num,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["compliance_status"] == "FULLY_COMPLIANT" else "red"

    console.print(
        Panel(
            f"[bold {status_color}]RÀ SOÁT NỘI QUY LAO ĐỘNG DOANH NGHIỆP (ĐIỀU 118 BLLĐ)[/]\n\n"
            f"  Doanh nghiệp:         [bold]{result['enterprise_name']}[/] (Quy mô: {result['total_employees']} lao động)\n"
            f"  Nghĩa vụ đăng ký Sở:  [bold]{'BẮT BUỘC (Quy mô >= 10 người)' if result['mandatory_filing_required'] else 'Không bắt buộc (< 10 người)'}[/]\n"
            f"  Văn bản nội quy:      {'ĐÃ BAN HÀNH' if result['has_written_regulations'] else 'CHƯA CÓ'}\n"
            f"  Đăng ký Sở LĐ-TB&XH:  {'ĐÃ ĐĂNG KÝ (Số: ' + (result['dolab_filing_number'] or '') + ')' if result['is_registered_with_dolab'] else 'CHƯA ĐĂNG KÝ'}\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]KẾT QUẢ ĐÁNH GIÁ:[/]   [bold {status_color}]{result['compliance_status']}[/bold {status_color}]\n"
            f"  Ghi chú pháp lý:      {'; '.join(result['statutory_notes'])}",
            title="[bold blue]Internal Labor Regulations Audit[/]",
            border_style=status_color,
        )
    )


@labor_app.command("list")
def list_labor_cmd(
    entity: str = typer.Option("workers", "--type", "-t", help="Loại thực thể (workers hoặc applications)"),
    position: str = typer.Option("ALL", "--position", "-p", help="Lọc theo vị trí công việc"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Liệt kê danh sách lao động nước ngoài hoặc hồ sơ đề nghị cấp Giấy phép lao động."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()

    if entity.lower() == "workers":
        workers = engine.list_workers(position=position, limit=limit)
        if json_mode:
            typer.echo(json.dumps({"ok": True, "workers": workers, "total": len(workers)}, indent=2, ensure_ascii=False))
            return

        table = Table(title="Danh Sách Nhân Sự Nước Ngoài Đã Thẩm Định", border_style="cyan")
        table.add_column("Mã Nhân Sự", style="cyan")
        table.add_column("Họ Và Tên", style="white")
        table.add_column("Quốc Tịch", style="yellow")
        table.add_column("Vị Trí", style="green")
        table.add_column("Chức Danh", style="magenta")
        table.add_column("Miễn GPLĐ", style="cyan")
        table.add_column("Trạng Thái", style="green")

        for w in workers:
            table.add_row(
                w["worker_id"],
                w["worker_name"],
                w["nationality"],
                w["position_category"],
                w["job_title"],
                "CÓ" if w["is_exempt"] else "KHÔNG",
                w["permit_status"],
            )
        console.print(table)
    else:
        apps = engine.list_applications(limit=limit)
        if json_mode:
            typer.echo(json.dumps({"ok": True, "applications": apps, "total": len(apps)}, indent=2, ensure_ascii=False))
            return

        table = Table(title="Danh Sách Hồ Sơ Đề Nghị Cấp Giấy Phép Lao Động", border_style="green")
        table.add_column("Mã Hồ Sơ", style="cyan")
        table.add_column("Mã Nhân Sự", style="white")
        table.add_column("Loại Hồ Sơ", style="yellow")
        table.add_column("Kết Quả Thẩm Định", style="green")
        table.add_column("Ngày Nộp", style="magenta")

        for a in apps:
            table.add_row(
                a["application_id"],
                a["worker_id"],
                a["dossier_type"],
                a["eligibility_result"],
                a["applied_at"],
            )
        console.print(table)


@labor_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn telemetry hệ thống pháp luật lao động, hồ sơ GPLĐ và tuân thủ NQLĐ."""
    from src.core.labor_engine import LaborEngine

    engine = LaborEngine()
    data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    m = data["metrics"]
    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN TRỊ LAO ĐỘNG & GIẤY PHÉP LAO ĐỘNG NƯỚC NGOÀI[/]\n\n"
            f"  Trạng thái:            [bold green]{data['status'].upper()}[/]\n"
            f"  Động cơ xử lý:         [bold]{data['engine']}[/]\n"
            f"  Lao động nước ngoài:   [bold cyan]{m['total_foreign_workers_assessed']}[/] (Miễn GPLĐ: [bold yellow]{m['total_exempt_workers']}[/])\n"
            f"  Hồ sơ cấp phép GPLĐ:   [bold cyan]{m['total_work_permit_applications']}[/]\n"
            f"  Doanh nghiệp rà soát:  [bold]{m['total_enterprises_audited']}[/] (Đạt chuẩn: [bold green]{m['compliant_enterprises']}[/])\n"
            f"  Cơ sở dữ liệu:         {data['database']}",
            title="[bold blue]Labor & Foreign Work Permit Engine Telemetry[/]",
            border_style="green",
        )
    )
