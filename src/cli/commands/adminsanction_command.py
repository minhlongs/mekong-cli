# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Commercial & Enterprise Administrative Sanctions Command Surface (Phase 151).

Statutory framework:
- Law on Handling of Administrative Violations 2012 (Luật Xử lý vi phạm hành chính số 15/2012/QH13),
  amended and supplemented by Law No. 67/2020/QH14.
- Decree No. 118/2021/ND-CP detailing articles and implementation measures of the Law on Handling of Administrative Violations.
- Decree No. 19/2020/ND-CP on inspection and disciplinary handling in administrative violation enforcement.
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.adminsanction_engine import (
    AdminSanctionEngine,
    AuthorityBranch,
    EntityType,
    MAX_FINES_INDIVIDUAL_VND,
    RemedialMeasureType,
    SanctionType,
    TWO_YEAR_LIMITATION_SECTORS,
    ViolationStatus,
)

adminsanction_app = typer.Typer(
    name="adminsanction",
    help="Vietnamese Administrative Sanctions & Violations Compliance Suite (Luật XLVPHC 2012/2020 & NĐ 118/2021/NĐ-CP).",
    no_args_is_help=False,
)
app = adminsanction_app
console = Console()


def _render_dashboard() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG XỬ LÝ VI PHẠM HÀNH CHÍNH & KHẮC PHỤC HẬU QUẢ[/bold cyan]\n"
            "[bold green]QUẢN LÝ KHUNG PHẠT TIỀN, THỜI HIỆU, THẨM QUYỀN & TỊCH THU SỐ LỢI BẤT HỢP PHÁP[/bold green]\n"
            "[dim]Luật Xử lý vi phạm hành chính số 15/2012/QH13 (sđ 67/2020/QH14) & Nghị định 118/2021/NĐ-CP[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    summary_table = Table(title="Nguyên Tắc Luật Định & Thời Hiệu Xử Phạt VPHC", box=box.ROUNDED)
    summary_table.add_column("Chỉ Tiêu Pháp Lý", style="cyan bold")
    summary_table.add_column("Quy Định Luật Định", style="yellow")
    summary_table.add_column("Căn Cứ Pháp Lý", style="green")

    summary_table.add_row(
        "Hệ số phạt Tổ chức / Doanh nghiệp",
        "Bằng 02 lần (2.0x) mức phạt cá nhân",
        "Điều 24.2 Luật XLVPHC",
    )
    summary_table.add_row(
        "Thuật toán xác định mức phạt tiền",
        "Mức trung bình = (Min + Max)/2, điều chỉnh theo tăng nặng/giảm nhẹ",
        "Điều 23 Luật XLVPHC & Điều 9 NĐ 118/2021/NĐ-CP",
    )
    summary_table.add_row(
        "Thời hiệu xử phạt thông thường",
        "01 năm tính từ khi chấm dứt hoặc phát hiện vi phạm",
        "Điều 6.1.a Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hiệu xử phạt đặc biệt (Thuế, Môi trường, Đất đai, SHTT)",
        "02 năm tính từ khi chấm dứt hoặc phát hiện vi phạm",
        "Điều 6.1.a Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hạn gửi văn bản giải trình",
        "05 ngày làm việc kể từ ngày lập biên bản VPHC",
        "Điều 61.2 Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hạn ra quyết định xử phạt",
        "07 ngày làm việc (vụ phức tạp giải trình: 30 ngày, tối đa 60 ngày)",
        "Điều 66.1 Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hiệu thi hành quyết định xử phạt",
        "01 năm kể từ ngày ra quyết định xử phạt",
        "Điều 73.1 Luật XLVPHC",
    )
    summary_table.add_row(
        "Tiền phạt chậm nộp",
        "0.05% / ngày trên số tiền phạt chưa nộp",
        "Điều 78.1 Luật XLVPHC",
    )
    console.print(summary_table)

    caps_table = Table(title="Mức Phạt Tiền Tối Đa Theo Lĩnh Vực (Cá nhân / Tổ chức = 2x)", box=box.SIMPLE_HEAD)
    caps_table.add_column("Lĩnh Vực Hoạt Động", style="cyan")
    caps_table.add_column("Mức Phạt Tối Đa Cá Nhân", style="magenta", justify="right")
    caps_table.add_column("Mức Phạt Tối Đa Tổ Chức", style="red bold", justify="right")
    caps_table.add_column("Thời Hiệu", style="yellow")

    for sector, cap_ind in sorted(MAX_FINES_INDIVIDUAL_VND.items(), key=lambda x: x[1], reverse=True)[:10]:
        cap_org = cap_ind * 2.0
        statute = "02 năm" if sector in TWO_YEAR_LIMITATION_SECTORS else "01 năm"
        caps_table.add_row(sector, f"{cap_ind:,.0f} VNĐ", f"{cap_org:,.0f} VNĐ", statute)

    console.print(caps_table)


@adminsanction_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON"),
) -> None:
    """Vietnamese Administrative Sanctions & Violations Compliance Suite."""
    if ctx.invoked_subcommand is None:
        engine = AdminSanctionEngine()
        data = engine.get_statutory_dashboard()
        if json_output:
            typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            _render_dashboard()


@adminsanction_app.command("status")
def status(
    json_output: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON"),
) -> None:
    """Hiển thị bảng điều khiển khung pháp lý xử lý vi phạm hành chính."""
    engine = AdminSanctionEngine()
    data = engine.get_statutory_dashboard()
    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _render_dashboard()


@adminsanction_app.command("dashboard")
def dashboard(
    json_output: bool = typer.Option(False, "--json", help="Xuất dữ liệu dạng JSON"),
) -> None:
    """Hiển thị bảng điều khiển vi phạm hành chính (alias)."""
    engine = AdminSanctionEngine()
    data = engine.get_statutory_dashboard()
    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _render_dashboard()


@adminsanction_app.command("create-case")
def create_case(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Tên cá nhân/tổ chức vi phạm"),
    subject_name: Optional[str] = typer.Option(None, "--subject-name", help="Tên cá nhân/tổ chức vi phạm"),
    entity: Optional[str] = typer.Option(None, "--entity", "-e", help="Loại đối tượng"),
    subject_type: Optional[str] = typer.Option(None, "--subject-type", help="Loại đối tượng: INDIVIDUAL hoặc ORGANIZATION"),
    sector: Optional[str] = typer.Option(None, "--sector", "-s", help="Lĩnh vực vi phạm"),
    category: Optional[str] = typer.Option(None, "--category", help="Lĩnh vực vi phạm"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Mô tả hành vi"),
    behavior: Optional[str] = typer.Option(None, "--behavior", help="Mô tả hành vi vi phạm hành chính"),
    violation_date: Optional[str] = typer.Option(None, "--violation-date", help="Ngày vi phạm (YYYY-MM-DD)"),
    date: Optional[str] = typer.Option(None, "--date", help="Ngày vi phạm (YYYY-MM-DD)"),
    location: Optional[str] = typer.Option(None, "--location", help="Địa điểm vi phạm"),
    discovery_date: Optional[str] = typer.Option(None, "--discovery-date", help="Ngày phát hiện vi phạm (YYYY-MM-DD)"),
    status: str = typer.Option("CONCLUDED", "--status", help="Trạng thái vi phạm: CONCLUDED hoặc ONGOING"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Lập hồ sơ vụ việc vi phạm hành chính và kiểm tra thời hiệu xử phạt."""
    final_name = subject_name or name or "Chưa xác định"
    final_entity = subject_type or entity or "ORGANIZATION"
    final_sector = category or sector or "ENVIRONMENTAL_PROTECTION"
    final_desc = behavior or description or "Hành vi vi phạm hành chính"
    final_date = date or violation_date or "2026-01-01"

    engine = AdminSanctionEngine()
    res = engine.create_case(
        violator_name=final_name,
        entity_type=final_entity,
        sector=final_sector,
        violation_description=final_desc,
        violation_date=final_date,
        discovery_date=discovery_date,
        violation_status=status,
        violation_location=location,
    )

    if json_output:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel(f"[bold green]Đã lập hồ sơ vụ việc VPHC thành công: {res['case_id']}[/bold green]", border_style="green"))
    table = Table(box=box.ROUNDED)
    table.add_column("Thuộc Tính", style="cyan bold")
    table.add_column("Chi Tiết Hồ Sơ", style="white")

    table.add_row("Mã Hồ Sơ", res["case_id"])
    table.add_row("Đối Tượng Vi Phạm", f"{res['violator_name']} ({res['entity_type']})")
    table.add_row("Lĩnh Vực", res["sector"])
    table.add_row("Mô Tả Vi Phạm", res["violation_description"])
    table.add_row("Thời Điểm Vi Phạm", res["violation_date"])
    table.add_row("Thời Điểm Phát Hiện", res["discovery_date"])
    table.add_row("Trạng Thái Hành Vi", res["violation_status"])
    table.add_row(
        "Thời Hiệu Xử Phạt",
        f"{res['statute_of_limitations']['statute_limit_years']} năm (Hết hạn: {res['statute_of_limitations']['expiry_date']})",
    )
    table.add_row("Số Ngày Còn Lại", str(res["statute_of_limitations"]["days_remaining"]))
    table.add_row(
        "Đánh Giá Thời Hiệu",
        f"[bold red]HẾT THỜI HIỆU[/bold red]" if res["statute_of_limitations"]["is_time_barred"] else "[bold green]CÒN THỜI HIỆU HỢP LỆ[/bold green]",
    )
    table.add_row("Khuyến Nghị Pháp Lý", res["statute_of_limitations"]["action_recommendation"])

    console.print(table)


@adminsanction_app.command("calculate-fine")
def calculate_fine(
    min_fine: Optional[float] = typer.Option(None, "--min", "-m", help="Mức phạt tối thiểu khung cá nhân (VNĐ)"),
    min_fine_opt: Optional[float] = typer.Option(None, "--min-fine", help="Mức phạt tối thiểu"),
    max_fine: Optional[float] = typer.Option(None, "--max", "-M", help="Mức phạt tối đa khung cá nhân (VNĐ)"),
    max_fine_opt: Optional[float] = typer.Option(None, "--max-fine", help="Mức phạt tối đa"),
    entity: Optional[str] = typer.Option(None, "--entity", "-e", help="INDIVIDUAL hoặc ORGANIZATION (x2)"),
    subject_type: Optional[str] = typer.Option(None, "--subject-type", help="INDIVIDUAL hoặc ORGANIZATION"),
    mitigating: Optional[str] = typer.Option(None, "--mitigating", help="Danh sách hoặc số lượng tình tiết giảm nhẹ"),
    aggravating: Optional[str] = typer.Option(None, "--aggravating", help="Danh sách hoặc số lượng tình tiết tăng nặng"),
    case_id: Optional[str] = typer.Option(None, "--case-id", help="Mã hồ sơ liên kết (nếu có)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán mức tiền phạt luật định theo Nghị định 118/2021/NĐ-CP và Điều 23 Luật XLVPHC."""
    engine = AdminSanctionEngine()
    final_min = min_fine_opt if min_fine_opt is not None else (min_fine if min_fine is not None else 1_000_000.0)
    final_max = max_fine_opt if max_fine_opt is not None else (max_fine if max_fine is not None else 2_000_000.0)
    final_entity = subject_type or entity or "ORGANIZATION"

    mit_list: List[str] = []
    if mitigating:
        if mitigating.strip().isdigit():
            mit_list = [f"Tình tiết giảm nhẹ #{i+1}" for i in range(int(mitigating.strip()))]
        else:
            mit_list = [x.strip() for x in mitigating.split(",") if x.strip()]

    agg_list: List[str] = []
    if aggravating:
        if aggravating.strip().isdigit():
            agg_list = [f"Tình tiết tăng nặng #{i+1}" for i in range(int(aggravating.strip()))]
        else:
            agg_list = [x.strip() for x in aggravating.split(",") if x.strip()]

    res = engine.calculate_statutory_fine(
        statutory_min_fine_individual=final_min,
        statutory_max_fine_individual=final_max,
        entity_type=final_entity,
        mitigating_factors=mit_list,
        aggravating_factors=agg_list,
        case_id=case_id,
    )
    res["fine_calculation"] = {
        "calculated_fine_vnd": res["final_payable_fine_vnd"],
        "applied_min": res["applied_bracket"]["min"],
        "applied_max": res["applied_bracket"]["max"],
        "average": res["applied_bracket"]["average"],
    }

    if json_output:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel(f"[bold cyan]KẾT QUẢ TÍNH TOÁN TIỀN PHẠT LUẬT ĐỊNH (NĐ 118/2021/NĐ-CP)[/bold cyan]", border_style="cyan"))
    table = Table(box=box.ROUNDED)
    table.add_column("Hạng Mục Tính Toán", style="cyan bold")
    table.add_column("Giá Trị Áp Dụng", style="yellow")

    table.add_row("Đối Tượng Áp Dụng", f"{res['entity_type']} (Hệ số: {res['multiplier']}x)")
    table.add_row(
        "Khung Luật Định (Cá nhân)",
        f"{res['statutory_bracket_individual']['min']:,.0f} VNĐ - {res['statutory_bracket_individual']['max']:,.0f} VNĐ",
    )
    table.add_row(
        "Khung Áp Dụng Thực Tế",
        f"{res['applied_bracket']['min']:,.0f} VNĐ - {res['applied_bracket']['max']:,.0f} VNĐ (Mức TB: {res['applied_bracket']['average']:,.0f} VNĐ)",
    )
    table.add_row("Tình Tiết Giảm Nhẹ (Điều 9)", f"{len(res['mitigating_factors'])}: {', '.join(res['mitigating_factors']) if res['mitigating_factors'] else 'Không'}")
    table.add_row("Tình Tiết Tăng Nặng (Điều 10)", f"{len(res['aggravating_factors'])}: {', '.join(res['aggravating_factors']) if res['aggravating_factors'] else 'Không'}")
    table.add_row(
        "[bold green]MỨC PHẠT TIỀN CHÍNH THỨC[/bold green]",
        f"[bold green]{res['final_payable_fine_vnd']:,.0f} VNĐ[/bold green]",
    )
    table.add_row("Giải Thích Thuật Toán", res["formula_explanation"])

    console.print(table)


@adminsanction_app.command("assess-jurisdiction")
def assess_jurisdiction(
    fine: float = typer.Option(..., "--fine", "-f", help="Mức tiền phạt đề xuất (VNĐ)"),
    category: str = typer.Option("GENERAL", "--category", "-c", "--sector", help="Lĩnh vực vi phạm"),
    subject_type: str = typer.Option("INDIVIDUAL", "--subject-type", "-e", help="INDIVIDUAL hoặc ORGANIZATION"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Đánh giá thẩm quyền chức danh xử phạt vi phạm hành chính."""
    if fine <= 5_000_000.0:
        authority = "COMMUNE_CHAIR"
    elif fine <= 50_000_000.0 or (subject_type.upper() == "ORGANIZATION" and fine <= 100_000_000.0):
        authority = "DISTRICT_CHAIR"
    else:
        authority = "PROVINCE_CHAIR"

    data = {
        "competent_authority": authority,
        "fine_amount_vnd": fine,
        "category": category,
        "subject_type": subject_type,
    }
    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        console.print(f"[bold green]Thẩm quyền xử phạt:[/bold green] {authority}")


@adminsanction_app.command("check-authority")
def check_authority(
    branch: str = typer.Option("PEOPLE_COMMITTEE", "--branch", "-b", help="Ngành/Cơ quan: PEOPLE_COMMITTEE, INSPECTORATE, MARKET_SURVEILLANCE, TAX_AUTHORITY, etc."),
    title: str = typer.Option("CHỦ TỊCH HUYỆN", "--title", "-t", help="Chức danh người xử phạt"),
    fine_amount: float = typer.Option(..., "--fine", "-f", help="Mức tiền phạt đề xuất (VNĐ)"),
    suspend_license: bool = typer.Option(False, "--suspend-license", help="Có áp dụng hình thức tước quyền sử dụng GPLX/chứng chỉ không"),
    confiscate: bool = typer.Option(False, "--confiscate", help="Có tịch thu tang vật, phương tiện không"),
    confiscate_value: float = typer.Option(0.0, "--confiscate-value", help="Trị giá tang vật, phương tiện tịch thu (VNĐ)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Kiểm tra thẩm quyền xử phạt của chức danh theo Điều 38–51 Luật XLVPHC."""
    engine = AdminSanctionEngine()
    res = engine.assess_authority_jurisdiction(
        branch=branch,
        officer_title=title,
        proposed_fine_vnd=fine_amount,
        requires_license_suspension=suspend_license,
        requires_confiscation=confiscate,
        confiscated_value_vnd=confiscate_value,
    )

    if json_output:
        console.print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    is_valid = res["is_competent"]
    status_text = "[bold green]HỢP LỆ VỀ THẨM QUYỀN[/bold green]" if is_valid else "[bold red]VƯỢT QUÁ THẨM QUYỀN (CẦN CHUYỂN HỒ SƠ)[/bold red]"
    console.print(Panel(f"KẾT QUẢ THẨM ĐỊNH THẨM QUYỀN XỬ PHẠT: {status_text}", border_style="green" if is_valid else "red"))

    table = Table(box=box.ROUNDED)
    table.add_column("Tiêu Chí Thẩm Định", style="cyan bold")
    table.add_column("Kết Quả Đánh Giá", style="white")

    table.add_row("Cơ Quan / Ngành", res["authority_branch"])
    table.add_row("Chức Danh Người Xử Phạt", res["officer_title"])
    table.add_row("Hạn Mức Phạt Tiền Tối Đa", f"{res['officer_fine_limit_vnd']:,.0f} VNĐ")
    table.add_row("Quyền Tước GP / Đình Chỉ", "Có thẩm quyền" if res["can_suspend_license"] else "KHÔNG có thẩm quyền")
    table.add_row("Quyền Tịch Thu Tang Vật", "Có thẩm quyền" if res["can_confiscate_assets"] else "KHÔNG có thẩm quyền")
    table.add_row("Căn Cứ / Lý Do", "\n".join(res["jurisdiction_reasons"]))
    if res["procedural_escalation"]:
        table.add_row("[bold yellow]Hướng Xử Lý Hồ Sơ[/bold yellow]", f"[bold yellow]{res['procedural_escalation']}[/bold yellow]")

    console.print(table)


@adminsanction_app.command("remedy")
def calculate_remedy(
    revenue: float = typer.Option(0.0, "--revenue", "-r", help="Doanh thu/tiền thu trực tiếp từ vi phạm (VNĐ)"),
    costs: float = typer.Option(0.0, "--costs", "-c", help="Chi phí hợp pháp, hợp lệ được trừ (VNĐ)"),
    dissipated: float = typer.Option(0.0, "--dissipated", "-d", help="Trị giá tang vật đã tiêu thụ, tẩu tán (VNĐ)"),
    restore_state: bool = typer.Option(False, "--restore-state", help="Buộc khôi phục lại tình trạng ban đầu"),
    dismantle: bool = typer.Option(False, "--dismantle", help="Buộc tháo dỡ công trình trái phép"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán biện pháp khắc phục hậu quả & thu hồi số lợi bất hợp pháp (Điều 28)."""
    engine = AdminSanctionEngine()
    measures = []
    if restore_state:
        measures.append({
            "measure_type": RemedialMeasureType.RESTORE_ORIGINAL_STATE.value,
            "description": "Buộc khôi phục lại tình trạng ban đầu đã bị thay đổi do hành vi vi phạm hành chính gây ra",
            "deadline_days": 15,
        })
    if dismantle:
        measures.append({
            "measure_type": RemedialMeasureType.DISMANTLE_CONSTRUCTION.value,
            "description": "Buộc tháo dỡ công trình, phần công trình xây dựng không có giấy phép hoặc sai phép",
            "deadline_days": 30,
        })

    res = engine.calculate_remedial_measures(
        measures=measures,
        direct_illegal_revenue_vnd=revenue,
        legitimate_deductible_costs_vnd=costs,
        dissipated_asset_value_vnd=dissipated,
    )

    if json_output:
        console.print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel("[bold magenta]BIỆN PHÁP KHẮC PHỤC HẬU QUẢ & THU HỒI SỐ LỢI BẤT HỢP PHÁP[/bold magenta]", border_style="magenta"))
    table = Table(box=box.ROUNDED)
    table.add_column("Hạng Mục Khắc Phục", style="cyan bold")
    table.add_column("Định Lượng & Nghĩa Vụ", style="yellow")

    table.add_row("Doanh Thu Trực Tiếp Từ Vi Phạm", f"{res['direct_illegal_revenue_vnd']:,.0f} VNĐ")
    table.add_row("Chi Phí Hợp Lệ Được Giảm Trừ", f"{res['deductible_costs_vnd']:,.0f} VNĐ")
    table.add_row("[bold red]Số Lợi Bất Hợp Pháp Phải Nộp Lại[/bold red]", f"[bold red]{res['net_illegal_profit_vnd']:,.0f} VNĐ[/bold red]")
    table.add_row("Truy Thu Trị Giá Tang Vật Đã Tẩu Tán", f"{res['dissipated_asset_reimbursement_vnd']:,.0f} VNĐ")
    table.add_row("[bold green]TỔNG NGHĨA VỤ TÀI CHÍNH KHẮC PHỤC[/bold green]", f"[bold green]{res['total_remedial_financial_obligation_vnd']:,.0f} VNĐ[/bold green]")

    console.print(table)


@adminsanction_app.command("decide")
def generate_decision(
    case_id: str = typer.Option(..., "--case-id", "-c", help="Mã hồ sơ VPHC"),
    number: str = typer.Option("QD-XPVPHC/2026/01", "--number", "-n", help="Số quyết định xử phạt"),
    authority: str = typer.Option("UBND Tỉnh Bình Dương", "--authority", "-a", help="Cơ quan ban hành"),
    officer: str = typer.Option("Chủ tịch UBND Tỉnh", "--officer", "-o", help="Chức danh người ban hành"),
    principal: str = typer.Option("FINE", "--principal", "-p", help="Hình thức phạt chính: FINE, WARNING"),
    fine: float = typer.Option(..., "--fine", "-f", help="Mức tiền phạt (VNĐ)"),
    illegal_profit: float = typer.Option(0.0, "--profit", help="Số lợi bất hợp pháp buộc nộp lại (VNĐ)"),
    deadline: int = typer.Option(10, "--deadline", "-d", help="Thời hạn chấp hành quyết định (ngày)"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Ban hành quyết định xử phạt vi phạm hành chính chính thức."""
    engine = AdminSanctionEngine()
    res = engine.generate_sanction_decision(
        case_id=case_id,
        decision_number=number,
        issuing_authority=authority,
        issuing_officer_title=officer,
        principal_sanction=principal,
        fine_amount_vnd=fine,
        illegal_profit_amount_vnd=illegal_profit,
        execution_deadline_days=deadline,
    )

    if json_output:
        console.print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel(f"[bold green]ĐÃ BAN HÀNH QUYẾT ĐỊNH XỬ PHẠT: {res['decision_number']}[/bold green]", border_style="green"))
    table = Table(box=box.ROUNDED)
    table.add_column("Thông Tin Quyết Định", style="cyan bold")
    table.add_column("Nội Dung Pháp Lý", style="white")

    table.add_row("Mã Quyết Định Hệ Thống", res["decision_id"])
    table.add_row("Mã Hồ Sơ Gốc", res["case_id"])
    table.add_row("Cơ Quan Ban Hành", res["issuing_authority"])
    table.add_row("Người Có Thẩm Quyền", res["issuing_officer_title"])
    table.add_row("Hình Thức Xử Phạt Chính", res["principal_sanction"])
    table.add_row("Mức Phạt Tiền", f"{res['fine_amount_vnd']:,.0f} VNĐ")
    table.add_row("Số Lợi Bất Hợp Pháp", f"{res['illegal_profit_disgorgement_vnd']:,.0f} VNĐ")
    table.add_row("[bold green]TỔNG NGHĨA VỤ PHẢI NỘP[/bold green]", f"[bold green]{res['total_financial_obligation_vnd']:,.0f} VNĐ[/bold green]")
    table.add_row("Thời Hạn Chấp Hành Tự Nguyện", f"{res['execution_terms']['voluntary_execution_deadline_days']} ngày")
    table.add_row("Hết Hạn Thời Hiệu Thi Hành", res['execution_terms']['statute_of_execution_expiry'])
    table.add_row("Dự Kiến Xóa Tiền Sự (Coi Chưa Bị Xử Phạt)", res['execution_terms']['record_clearance_projection'])
    table.add_row("Quyền Khiếu Nại / Khởi Kiện", res['execution_terms']['right_to_appeal'])

    console.print(table)
