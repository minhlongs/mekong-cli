# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese High-Tech Enterprise, Science Parks & Tech Transfer Suite (Phase 88)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from src.cli.commands.hitech_commands_records_table import build_table

hitech_app = typer.Typer(name="hitech", help="Vietnamese High-Tech Enterprise, Science Parks & Tech Transfer Compliance Suite.")
console = Console()


@hitech_app.callback(invoke_without_command=True)
def hitech_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan chứng nhận Doanh nghiệp Công nghệ cao, hợp đồng chuyển giao công nghệ và KCNC."""
    if ctx.invoked_subcommand is not None:
        return
    from src.core.hitech_engine import HitechEngine
    s = HitechEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(s, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]HỆ THỐNG QUẢN LÝ DOANH NGHIỆP CÔNG NGHỆ CAO & CHUYỂN GIAO CÔNG NGHỆ[/]\n\n"
        f"  Khung pháp lý:             [bold]{s['statutory_law']}[/]\n"
        f"  Doanh nghiệp CNC thẩm định:[bold cyan]{s['qualified_hitech_enterprises']}/{s['total_hitech_enterprises_audited']}[/] đạt chuẩn ([bold green]{s['enterprise_qualification_rate_pct']}%[/] theo QĐ 10/2021)\n"
        f"  Hợp đồng chuyển giao CN:   [bold green]{s['total_tech_transfer_contracts']}[/] hợp đồng đăng ký ([bold red]{s['prohibited_contracts_intercepted']}[/] công nghệ cấm bị chặn)\n"
        f"  Dự án Khu công nghệ cao:   [bold yellow]{s['approved_hitech_park_projects']}/{s['total_hitech_park_projects']}[/] dự án đạt chuẩn suất đầu tư >= 100 tỷ VND/ha\n"
        f"  Đánh giá ưu đãi thuế TNDN: [bold magenta]{s['total_tax_evaluations']}[/] đợt tính toán (Tiết kiệm thuế: [bold green]{s['total_statutory_tax_saved_vnd']:,.0f} VND[/])",
        title="[bold green]Vietnam High-Tech Enterprise & Technology Transfer Telemetry[/]", border_style="green",
    ))


@hitech_app.command("enterprise")
def enterprise_cmd(
    name: str = typer.Argument(..., help="Tên doanh nghiệp thẩm định"),
    rev: float = typer.Option(100_000_000_000.0, "--rev", "-r", help="Tổng doanh thu thuần hàng năm (VND)"),
    hitech_rev: float = typer.Option(75_000_000_000.0, "--hitech-rev", help="Doanh thu từ sản phẩm công nghệ cao (VND, tối thiểu 70%)"),
    rd: float = typer.Option(2_000_000_000.0, "--rd", help="Tổng chi phí R&D tại Việt Nam (VND)"),
    employees: int = typer.Option(200, "--employees", "-e", help="Tổng số lao động của doanh nghiệp"),
    rd_employees: int = typer.Option(15, "--rd-employees", help="Số lao động có bằng cao đẳng trở lên trực tiếp làm R&D"),
    scale: str = typer.Option("MEDIUM", "--scale", "-s", help="Quy mô doanh nghiệp: MICRO, SMALL, MEDIUM, LARGE, MEGA"),
    iso: bool = typer.Option(True, "--iso/--no-iso", help="Có chứng nhận hệ thống quản lý chất lượng ISO 9001"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện cấp Giấy chứng nhận Doanh nghiệp Công nghệ cao theo Quyết định số 10/2021/QĐ-TTg."""
    from src.core.hitech_engine import HitechEngine
    res = HitechEngine().audit_hitech_enterprise(company_name=name, total_revenue_vnd=rev, hitech_revenue_vnd=hitech_rev, rd_spending_vnd=rd, total_employees=employees, rd_employees=rd_employees, has_iso9001=iso, enterprise_scale=scale)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_qualified"] else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ THẨM ĐỊNH DOANH NGHIỆP CÔNG NGHỆ CAO (QUYẾT ĐỊNH 10/2021/QĐ-TTG)[/]\n\n"
        f"  Mã chứng nhận:       [bold cyan]{res['certificate_code']}[/] | Tên DN: [bold]{res['company_name']}[/] (Quy mô: [cyan]{res['enterprise_scale']}[/])\n"
        f"  Tỷ lệ doanh thu CNC: [bold]{res['hitech_ratio_pct']}%[/] (Yêu cầu >= {res['min_required_hitech_ratio_pct']}%) | Tỷ lệ R&D: [bold]{res['rd_ratio_pct']}%[/] (Yêu cầu >= {res['min_required_rd_ratio_pct']}%)\n"
        f"  Tỷ lệ nhân sự R&D:   [bold]{res['rd_employee_ratio_pct']}%[/] (Yêu cầu >= {res['min_required_rd_staff_ratio_pct']}%) | ISO 9001: [bold]{'ĐẠT CHUẨN' if res['has_iso9001'] else 'CHƯA CÓ'}[/]\n"
        f"  Kết luận thẩm định:  [bold {color}]{res['status']}[/] | Gói ưu đãi thuế: [bold]{res['tax_incentive_package']}[/]\n"
        + (f"  Thiếu sót:           [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Đáp ứng đầy đủ 04 tiêu chuẩn Doanh nghiệp Công nghệ cao[/]"),
        title=f"[bold {color}]High-Tech Enterprise Evaluation[/]", border_style=color,
    ))


@hitech_app.command("transfer")
def transfer_cmd(
    title: str = typer.Argument(..., help="Tên hợp đồng chuyển giao công nghệ"),
    transferor: str = typer.Option("Kyoto Advanced Materials Inc", "--transferor", help="Bên giao công nghệ"),
    transferee: str = typer.Option("Công ty CP Công nghệ Mekong", "--transferee", help="Bên nhận công nghệ"),
    tech_name: str = typer.Option("Công nghệ chế tạo vi mạch bán dẫn 7nm", "--tech", help="Tên công nghệ chuyển giao"),
    direction: str = typer.Option("INWARD_FOREIGN", "--direction", "-d", help="Hướng chuyển giao: INWARD_FOREIGN, OUTWARD_FOREIGN, DOMESTIC"),
    value: float = typer.Option(500_000.0, "--value", "-v", help="Giá trị hợp đồng chuyển giao (USD)"),
    state_capital: bool = typer.Option(False, "--state-capital/--private-capital", help="Dự án có sử dụng vốn ngân sách nhà nước"),
    category: str = typer.Option("ENCOURAGED", "--category", "-c", help="Danh mục công nghệ: ENCOURAGED, RESTRICTED, PROHIBITED"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký hợp đồng chuyển giao công nghệ theo Điều 31 Luật Chuyển giao công nghệ 2017."""
    from src.core.hitech_engine import HitechEngine
    res = HitechEngine().register_tech_transfer_contract(contract_title=title, transferor=transferor, transferee=transferee, technology_name=tech_name, transfer_direction=direction, contract_value_usd=value, uses_state_capital=state_capital, technology_category=category)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_approved"] else "red"
    console.print(Panel(
        f"[bold {color}]KẾT QUẢ ĐĂNG KÝ HỢP ĐỒNG CHUYỂN GIAO CÔNG NGHỆ (ĐIỀU 31 LUẬT CGCN)[/]\n\n"
        f"  Mã đăng ký:          [bold cyan]{res['registration_code']}[/] | Tên hợp đồng: [bold]{res['contract_title']}[/]\n"
        f"  Bên giao CN:         [white]{res['transferor']}[/] -> Bên nhận CN: [white]{res['transferee']}[/]\n"
        f"  Công nghệ:           [yellow]{res['technology_name']}[/] (Nhóm: [bold]{res['technology_category']}[/])\n"
        f"  Hướng & Giá trị:     [cyan]{res['transfer_direction']}[/] | [bold]{res['contract_value_usd']:,.0f} USD[/] | Bắt buộc ĐK: [bold]{'CÓ' if res['is_mandatory_registration'] else 'Tự nguyện'}[/]\n"
        f"  Trạng thái:          [bold {color}]{res['status']}[/] | Kết luận pháp lý: [bold]{res['legal_status']}[/]"
        + (f"\n  Mức phạt ước tính:   [bold red]{res['estimated_fine_vnd']:,.0f} VND[/]" if res["estimated_fine_vnd"] > 0 else ""),
        title=f"[bold {color}]Technology Transfer Contract Registration[/]", border_style=color,
    ))


@hitech_app.command("park")
def park_cmd(
    name: str = typer.Argument(..., help="Tên dự án đầu tư vào Khu công nghệ cao"),
    park_name: str = typer.Option("Khu Công Nghệ Cao TP. Hồ Chí Minh (SHTP)", "--park", "-p", help="Tên Khu công nghệ cao"),
    area: float = typer.Option(5.0, "--area", "-a", help="Diện tích đất đăng ký thuê (ha)"),
    capital: float = typer.Option(600_000_000_000.0, "--capital", "-c", help="Tổng vốn đầu tư đăng ký (VND)"),
    export_ratio: float = typer.Option(85.0, "--export", help="Tỷ lệ xuất khẩu dự kiến (%)"),
    tech_transfer: bool = typer.Option(True, "--tech-transfer/--no-tech-transfer", help="Cam kết chuyển giao công nghệ cho doanh nghiệp trong nước"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện tiếp nhận dự án đầu tư vào Khu công nghệ cao quốc gia (Nghị định 10/2024/NĐ-CP)."""
    from src.core.hitech_engine import HitechEngine
    res = HitechEngine().audit_hitech_park_project(project_name=name, park_name=park_name, land_area_ha=area, investment_capital_vnd=capital, export_ratio_pct=export_ratio, commits_tech_transfer=tech_transfer)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    color = "green" if res["is_approved"] else "red"
    console.print(Panel(
        f"[bold {color}]THẨM ĐỊNH DỰ ÁN ĐẦU TƯ KHU CÔNG NGHỆ CAO QUỐC GIA (NĐ 10/2024/NĐ-CP)[/]\n\n"
        f"  Mã dự án:            [bold cyan]{res['project_code']}[/] | Tên dự án: [bold]{res['project_name']}[/]\n"
        f"  Khu công nghệ cao:   [cyan]{res['park_name']}[/] | Diện tích: [white]{res['land_area_ha']} ha[/] | Tổng vốn: [bold]{res['investment_capital_vnd']:,.0f} VND[/]\n"
        f"  Suất vốn đầu tư:     [bold]{res['capital_per_ha_vnd']:,.0f} VND/ha[/] (Yêu cầu >= {res['min_required_capital_per_ha_vnd']:,.0f} VND/ha)\n"
        f"  Cam kết chuyển giao: [bold]{'CÓ' if res['commits_tech_transfer'] else 'CHƯA CAM KẾT'}[/] | Kết luận: [bold {color}]{res['status']}[/]\n"
        + (f"  Thiếu sót:           [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:            [bold green]Đáp ứng đầy đủ điều kiện suất đầu tư và tiêu chuẩn KCNC[/]"),
        title=f"[bold {color}]High-Tech Park Project Audit[/]", border_style=color,
    ))


@hitech_app.command("tax")
def tax_cmd(
    company: str = typer.Argument(..., help="Tên doanh nghiệp"),
    profit: float = typer.Option(50_000_000_000.0, "--profit", "-p", help="Lợi nhuận trước thuế trong năm tính thuế (VND)"),
    year: int = typer.Option(2, "--year", "-y", help="Năm hoạt động có thu nhập chịu thuế (Năm 1-15)"),
    hitech: bool = typer.Option(True, "--hitech/--no-hitech", help="Đã được cấp chứng nhận Doanh nghiệp Công nghệ cao"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán số thuế TNDN được miễn, giảm và tiết kiệm thuế theo gói ưu đãi công nghệ cao."""
    from src.core.hitech_engine import HitechEngine
    res = HitechEngine().calculate_tax_incentives(company_name=company, profit_before_tax_vnd=profit, operating_year=year, is_certified_hitech=hitech)
    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold green]TÍNH TOÁN ƯU ĐÃI THUẾ THU NHẬP DOANH NGHIỆP (TNDN) CÔNG NGHỆ CAO[/]\n\n"
        f"  Mã tính toán:        [bold cyan]{res['evaluation_code']}[/] | DN: [bold]{res['company_name']}[/] (Năm hoạt động: [yellow]{res['operating_year']}[/])\n"
        f"  Lợi nhuận chịu thuế: [bold]{res['profit_before_tax_vnd']:,.0f} VND[/] | Thuế phổ thông: [white]{res['standard_tax_vnd']:,.0f} VND[/] ({res['standard_tax_rate_pct']}%)\n"
        f"  Thuế suất áp dụng:   [bold cyan]{res['applied_tax_rate_pct']}%[/] | Thuế phải nộp: [bold yellow]{res['incentive_tax_vnd']:,.0f} VND[/]\n"
        f"  Số thuế tiết kiệm:   [bold green]{res['tax_saved_vnd']:,.0f} VND[/] | Giai đoạn: [bold green]{res['evaluation_summary']}[/]",
        title="[bold green]Corporate Income Tax Incentive Evaluation[/]", border_style="green",
    ))


@hitech_app.command("list")
def list_records_cmd(category: str = typer.Argument("enterprises", help="Danh mục: enterprises, contracts, parks, taxes"), limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"), json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON")) -> None:
    """Tra cứu danh mục doanh nghiệp công nghệ cao, hợp đồng chuyển giao công nghệ hoặc dự án KCNC."""
    from src.core.hitech_engine import HitechEngine
    records = HitechEngine().list_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    console.print(build_table(category, limit, records))


@hitech_app.command("status")
def status_cmd(json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo chỉ số telemetry tổng hợp Doanh nghiệp Công nghệ cao, hợp đồng chuyển giao và KCNC."""
    from src.core.hitech_engine import HitechEngine
    typer.echo(json.dumps(HitechEngine().get_status(), indent=2, ensure_ascii=False))
