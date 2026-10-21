# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Enforcement, authority check, remedy, and decision subcommands for Administrative Sanctions CLI."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.adminsanction_engine import (
    AdminSanctionEngine,
    RemedialMeasureType,
)

console = Console()


def register_enforcement_commands(adminsanction_app: typer.Typer) -> None:
    """Register authority check, remedy, and decision commands onto adminsanction_app."""
    adminsanction_app.command("assess-jurisdiction")(assess_jurisdiction)
    adminsanction_app.command("check-authority")(check_authority)
    adminsanction_app.command("remedy")(calculate_remedy)
    adminsanction_app.command("decide")(generate_decision)


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
    res = AdminSanctionEngine().assess_authority_jurisdiction(
        branch=branch, officer_title=title, proposed_fine_vnd=fine_amount,
        requires_license_suspension=suspend_license, requires_confiscation=confiscate, confiscated_value_vnd=confiscate_value,
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
    for k, v in [
        ("Cơ Quan / Ngành", res["authority_branch"]), ("Chức Danh Người Xử Phạt", res["officer_title"]),
        ("Hạn Mức Phạt Tiền Tối Đa", f"{res['officer_fine_limit_vnd']:,.0f} VNĐ"),
        ("Quyền Tước GP / Đình Chỉ", "Có thẩm quyền" if res["can_suspend_license"] else "KHÔNG có thẩm quyền"),
        ("Quyền Tịch Thu Tang Vật", "Có thẩm quyền" if res["can_confiscate_assets"] else "KHÔNG có thẩm quyền"),
        ("Căn Cứ / Lý Do", "\n".join(res["jurisdiction_reasons"])),
    ]:
        table.add_row(k, v)
    if res["procedural_escalation"]:
        table.add_row("[bold yellow]Hướng Xử Lý Hồ Sơ[/bold yellow]", f"[bold yellow]{res['procedural_escalation']}[/bold yellow]")
    console.print(table)


def calculate_remedy(
    revenue: float = typer.Option(0.0, "--revenue", "-r", help="Doanh thu/tiền thu trực tiếp từ vi phạm (VNĐ)"),
    costs: float = typer.Option(0.0, "--costs", "-c", help="Chi phí hợp pháp, hợp lệ được trừ (VNĐ)"),
    dissipated: float = typer.Option(0.0, "--dissipated", "-d", help="Trị giá tang vật đã tiêu thụ, tẩu tán (VNĐ)"),
    restore_state: bool = typer.Option(False, "--restore-state", help="Buộc khôi phục lại tình trạng ban đầu"),
    dismantle: bool = typer.Option(False, "--dismantle", help="Buộc tháo dỡ công trình trái phép"),
    json_output: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán biện pháp khắc phục hậu quả & thu hồi số lợi bất hợp pháp (Điều 28)."""
    measures = []
    if restore_state:
        measures.append({"measure_type": RemedialMeasureType.RESTORE_ORIGINAL_STATE.value, "description": "Buộc khôi phục lại tình trạng ban đầu đã bị thay đổi do hành vi vi phạm hành chính gây ra", "deadline_days": 15})
    if dismantle:
        measures.append({"measure_type": RemedialMeasureType.DISMANTLE_CONSTRUCTION.value, "description": "Buộc tháo dỡ công trình, phần công trình xây dựng không có giấy phép hoặc sai phép", "deadline_days": 30})
    res = AdminSanctionEngine().calculate_remedial_measures(measures=measures, direct_illegal_revenue_vnd=revenue, legitimate_deductible_costs_vnd=costs, dissipated_asset_value_vnd=dissipated)
    if json_output:
        console.print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel("[bold magenta]BIỆN PHÁP KHẮC PHỤC HẬU QUẢ & THU HỒI SỐ LỢI BẤT HỢP PHÁP[/bold magenta]", border_style="magenta"))
    table = Table(box=box.ROUNDED)
    table.add_column("Hạng Mục Khắc Phục", style="cyan bold")
    table.add_column("Định Lượng & Nghĩa Vụ", style="yellow")
    for k, v in [
        ("Doanh Thu Trực Tiếp Từ Vi Phạm", f"{res['direct_illegal_revenue_vnd']:,.0f} VNĐ"),
        ("Chi Phí Hợp Lệ Được Giảm Trừ", f"{res['deductible_costs_vnd']:,.0f} VNĐ"),
        ("[bold red]Số Lợi Bất Hợp Pháp Phải Nộp Lại[/bold red]", f"[bold red]{res['net_illegal_profit_vnd']:,.0f} VNĐ[/bold red]"),
        ("Truy Thu Trị Giá Tang Vật Đã Tẩu Tán", f"{res['dissipated_asset_reimbursement_vnd']:,.0f} VNĐ"),
        ("[bold green]TỔNG NGHĨA VỤ TÀI CHÍNH KHẮC PHỤC[/bold green]", f"[bold green]{res['total_remedial_financial_obligation_vnd']:,.0f} VNĐ[/bold green]"),
    ]:
        table.add_row(k, v)
    console.print(table)


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
    res = AdminSanctionEngine().generate_sanction_decision(
        case_id=case_id, decision_number=number, issuing_authority=authority, issuing_officer_title=officer,
        principal_sanction=principal, fine_amount_vnd=fine, illegal_profit_amount_vnd=illegal_profit, execution_deadline_days=deadline,
    )
    if json_output:
        console.print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    console.print(Panel(f"[bold green]ĐÃ BAN HÀNH QUYẾT ĐỊNH XỬ PHẠT: {res['decision_number']}[/bold green]", border_style="green"))
    table = Table(box=box.ROUNDED)
    table.add_column("Thông Tin Quyết Định", style="cyan bold")
    table.add_column("Nội Dung Pháp Lý", style="white")
    for k, v in [
        ("Mã Quyết Định Hệ Thống", res["decision_id"]), ("Mã Hồ Sơ Gốc", res["case_id"]),
        ("Cơ Quan Ban Hành", res["issuing_authority"]), ("Người Có Thẩm Quyền", res["issuing_officer_title"]),
        ("Hình Thức Xử Phạt Chính", res["principal_sanction"]), ("Mức Phạt Tiền", f"{res['fine_amount_vnd']:,.0f} VNĐ"),
        ("Số Lợi Bất Hợp Pháp", f"{res['illegal_profit_disgorgement_vnd']:,.0f} VNĐ"),
        ("[bold green]TỔNG NGHĨA VỤ PHẢI NỘP[/bold green]", f"[bold green]{res['total_financial_obligation_vnd']:,.0f} VNĐ[/bold green]"),
        ("Thời Hạn Chấp Hành Tự Nguyện", f"{res['execution_terms']['voluntary_execution_deadline_days']} ngày"),
        ("Hết Hạn Thời Hiệu Thi Hành", res["execution_terms"]["statute_of_execution_expiry"]),
        ("Dự Kiến Xóa Tiền Sự (Coi Chưa Bị Xử Phạt)", res["execution_terms"]["record_clearance_projection"]),
        ("Quyền Khiếu Nại / Khởi Kiện", res["execution_terms"]["right_to_appeal"]),
    ]:
        table.add_row(k, v)
    console.print(table)
