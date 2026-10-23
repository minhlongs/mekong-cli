# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Intellectual Property, Trademark, Patent & Copyright Engine (Phase 49)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from src.cli.commands.ip_commands_format_vnd import format_vnd as _format_vnd
from src.cli.commands.ip_commands_panels_table import build_dashboard, build_fees_panel, build_portfolio_table, build_status_panel
from src.cli.commands.ip_commands_patents_table import build_copyright_panel, build_patent_panel
from src.cli.commands.ip_commands_trademarks_table import build_application_panel, build_search_panel

console = Console()
ip_app = typer.Typer(name="ip", help="Intellectual Property (IP), Trademarks, Nice Classification, Patents & Software Copyright", add_completion=False)


@ip_app.callback(invoke_without_command=True)
def ip_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Hệ thống Quản lý Quyền Sở hữu Trí tuệ (IP), Nhãn hiệu, Sáng chế & Bản quyền phần mềm."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(build_dashboard(status_data))


@ip_app.command("trademark")
def register_trademark_cmd(
    mark_name: str = typer.Argument(..., help="Tên nhãn hiệu đăng ký (ví dụ: MekongAI)"),
    nice_class: str = typer.Option("09", "--class", "-c", help="Nhóm ngành Nice (09, 35, 36, 38, 41, 42, 45)"),
    applicant: str = typer.Option("Công Ty Công Nghệ Mekong", "--applicant", "-a", help="Tên chủ đơn / tổ chức đăng ký"),
    spec: str = typer.Option("", "--spec", "-s", help="Mô tả danh mục sản phẩm / dịch vụ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Nộp đơn đăng ký bảo hộ nhãn hiệu theo Thỏa ước Nice & Luật SHTT 2022."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    record = engine.register_trademark(mark_name=mark_name, nice_class=nice_class, applicant_name=applicant, goods_services_spec=spec)

    if json_mode:
        typer.echo(json.dumps(record, indent=2, ensure_ascii=False))
        return

    console.print(build_application_panel(record, _format_vnd))


@ip_app.command("search")
def search_trademark_cmd(
    mark_name: str = typer.Argument(..., help="Tên nhãn hiệu cần tra cứu tương tự"),
    nice_class: str = typer.Option("09", "--class", "-c", help="Nhóm ngành Nice mục tiêu (mặc định: 09)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tra cứu xung đột và đánh giá khả năng gây nhầm lẫn của nhãn hiệu (Điều 74 Luật SHTT)."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    result = engine.search_trademark_similarity(mark_name=mark_name, nice_class=nice_class)

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(build_search_panel(result))


@ip_app.command("patent")
def draft_patent_cmd(
    title: str = typer.Argument(..., help="Tên sáng chế / giải pháp kỹ thuật"),
    technical_field: str = typer.Argument(..., help="Lĩnh vực kỹ thuật của sáng chế"),
    applicant: str = typer.Option("Tổ chức Nghiên cứu Mekong", "--applicant", "-a", help="Tên tổ chức nộp đơn"),
    indep_claims: int = typer.Option(1, "--indep-claims", help="Số điểm yêu cầu bảo hộ độc lập"),
    dep_claims: int = typer.Option(2, "--dep-claims", help="Số điểm yêu cầu bảo hộ phụ thuộc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Soạn thảo bản mô tả sáng chế và các điểm yêu cầu bảo hộ (Claims) theo Điều 102 Luật SHTT."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    spec = engine.draft_patent_specification(title=title, technical_field=technical_field, applicant_name=applicant, independent_claims=indep_claims, dependent_claims=dep_claims)

    if json_mode:
        typer.echo(json.dumps(spec, indent=2, ensure_ascii=False))
        return

    console.print(build_patent_panel(spec, _format_vnd))


@ip_app.command("copyright")
def register_copyright_cmd(
    software_name: str = typer.Argument(..., help="Tên phần mềm / chương trình máy tính"),
    author_name: str = typer.Argument(..., help="Tên tác giả sáng tạo"),
    version: str = typer.Option("1.0.0", "--version", "-v", help="Phiên bản phần mềm"),
    repo_url: str = typer.Option("", "--repo", help="Kho lưu trữ mã nguồn VCS"),
    loc: int = typer.Option(10000, "--loc", help="Số dòng mã nguồn (Lines of Code)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Thiết lập hồ sơ đăng ký bản quyền tác phẩm phần mềm máy tính (Nghị định 17/2023/NĐ-CP)."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    dossier = engine.register_software_copyright(software_name=software_name, author_name=author_name, version=version, repository_url=repo_url, lines_of_code=loc)

    if json_mode:
        typer.echo(json.dumps(dossier, indent=2, ensure_ascii=False))
        return

    console.print(build_copyright_panel(dossier, _format_vnd))


@ip_app.command("fees")
def calculate_fees_cmd(
    trademark_classes: int = typer.Option(1, "--tm-classes", help="Số nhóm ngành nhãn hiệu đăng ký"),
    patent_claims: int = typer.Option(1, "--pat-claims", help="Số điểm yêu cầu bảo hộ sáng chế"),
    software_copyrights: int = typer.Option(1, "--copyrights", help="Số lượng phần mềm đăng ký bản quyền"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Tính toán chi tiết lệ phí nhà nước bảo hộ SHTT theo Thông tư 263/2016/TT-BTC."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    fees = engine.calculate_statutory_fees(trademark_classes=trademark_classes, patent_claims=patent_claims, software_copyrights=software_copyrights)

    if json_mode:
        typer.echo(json.dumps(fees, indent=2, ensure_ascii=False))
        return

    console.print(build_fees_panel(fees, _format_vnd))


@ip_app.command("list")
def list_portfolio_cmd(
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dạng JSON"),
) -> None:
    """Truy vấn danh mục tài sản sở hữu trí tuệ đã đăng ký trong hệ thống."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    portfolio = engine.list_portfolio(limit=limit)

    if json_mode:
        typer.echo(json.dumps(portfolio, indent=2, ensure_ascii=False))
        return

    console.print(build_portfolio_table(portfolio))


@ip_app.command("status")
def ip_status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông số dạng JSON"),
) -> None:
    """Tra cứu trạng thái cơ sở dữ liệu sở hữu trí tuệ và phân loại Nice."""
    from src.core.ip_engine import IpEngine

    engine = IpEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(build_status_panel(status_data))
