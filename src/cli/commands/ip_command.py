# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI command suite for Intellectual Property, Trademark, Patent & Copyright Engine (Phase 49)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
ip_app = typer.Typer(
    name="ip",
    help="Intellectual Property (IP), Trademarks, Nice Classification, Patents & Software Copyright",
    add_completion=False,
)


def _format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


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

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ TÀI SẢN TRÍ TUỆ (IP) & BẢO HỘ THƯƠNG HIỆU[/]\n\n"
            f"  Khung quy chuẩn:       [bold]{status_data['regulatory_framework']}[/]\n"
            f"  Phân loại quốc tế:     [bold cyan]{status_data['nice_classification_version']}[/]\n"
            f"  Nhãn hiệu đã nộp:      [bold green]{metrics['registered_trademarks']} đơn[/]\n"
            f"  Sáng chế đã soạn:      [bold yellow]{metrics['drafted_patents']} đơn[/]\n"
            f"  Bản quyền phần mềm:    [bold magenta]{metrics['software_copyrights']} hồ sơ[/]\n"
            f"  Nhóm ngành Nice hỗ trợ: [bold]{metrics['supported_nice_classes']} nhóm ngành trọng yếu[/]",
            title="[bold blue]Intellectual Property Portfolio Dashboard[/]",
            border_style="green",
        )
    )


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
    record = engine.register_trademark(
        mark_name=mark_name,
        nice_class=nice_class,
        applicant_name=applicant,
        goods_services_spec=spec,
    )

    if json_mode:
        typer.echo(json.dumps(record, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]ĐÃ THIẾT LẬP HỒ SƠ ĐĂNG KÝ NHÃN HIỆU: {record['mark_id']}[/]\n\n"
            f"  Tên nhãn hiệu:       [bold cyan]{record['mark_name']}[/]\n"
            f"  Nhóm ngành Nice:     [bold yellow]Nhóm {record['nice_class']}[/] ({record['class_title']})\n"
            f"  Chủ đơn đăng ký:     [bold]{record['applicant_name']}[/]\n"
            f"  Danh mục bảo hộ:     {record['goods_services_spec']}\n"
            f"  Cơ quan thụ lý:      {record['statutory_authority']}\n"
            f"  Lệ phí nhà nước:     [bold green]{_format_vnd(record['official_fee_vnd'])}[/] (theo TT 263/2016)\n"
            f"  Tiến trình dự kiến:  Thẩm định hình thức (1 tháng) -> Công bố (2 tháng) -> Thẩm định nội dung (9 tháng)",
            title="[bold blue]Trademark Application Ready[/]",
            border_style="green",
        )
    )


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

    color_map = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}
    risk_color = color_map.get(result["overall_conflict_risk"], "white")

    match_lines: list[str] = []
    for m in result["top_similar_marks"]:
        match_lines.append(
            f"  - [bold]{m['existing_mark']}[/] (Nhóm {m['nice_class']}): Tương đồng {round(m['similarity_score'] * 100)}% [{m['conflict_risk']}]"
        )
    match_block = "\n".join(match_lines) if match_lines else "  - Không phát hiện nhãn hiệu tương tự trong cơ sở dữ liệu."

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ TRA CỨU XUNG ĐỘT NHÃN HIỆU: '{result['query_mark']}' (Nhóm {result['target_nice_class']})[/]\n\n"
            f"  Mức độ rủi ro xung đột: [bold {risk_color}]{result['overall_conflict_risk']}[/bold {risk_color}] (Điểm cao nhất: {result['highest_similarity_score']})\n"
            f"  Đánh giá pháp lý:       {result['legal_assessment']}\n\n"
            f"  [bold]Các nhãn hiệu tương tự phát hiện:[/]\n{match_block}",
            title="[bold blue]Trademark Conflict & Similarity Search[/]",
            border_style=risk_color,
        )
    )


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
    spec = engine.draft_patent_specification(
        title=title,
        technical_field=technical_field,
        applicant_name=applicant,
        independent_claims=indep_claims,
        dependent_claims=dep_claims,
    )

    if json_mode:
        typer.echo(json.dumps(spec, indent=2, ensure_ascii=False))
        return

    claim_lines: list[str] = []
    for c in spec["claims"]:
        claim_lines.append(f"  [bold cyan]Điểm {c['claim_number']} ({c['type']}):[/] {c['text']}")
    claims_block = "\n".join(claim_lines)

    console.print(
        Panel(
            f"[bold green]BẢN MÔ TẢ VÀ YÊU CẦU BẢO HỘ SÁNG CHẾ: {spec['patent_id']}[/]\n\n"
            f"  Tên sáng chế:        [bold]{spec['title']}[/]\n"
            f"  Lĩnh vực kỹ thuật:   {spec['technical_field']}\n"
            f"  Người nộp đơn:       [bold]{spec['applicant_name']}[/]\n"
            f"  Tổng số claims:      [bold yellow]{spec['total_claims_count']} điểm[/]\n"
            f"  Lệ phí nộp & tra cứu: [bold green]{_format_vnd(spec['official_fee_vnd'])}[/]\n\n"
            f"  [bold]Nội dung điểm yêu cầu bảo hộ (Claims):[/]\n{claims_block}",
            title="[bold blue]Patent Specification & Claims Ready[/]",
            border_style="green",
        )
    )


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
    dossier = engine.register_software_copyright(
        software_name=software_name,
        author_name=author_name,
        version=version,
        repository_url=repo_url,
        lines_of_code=loc,
    )

    if json_mode:
        typer.echo(json.dumps(dossier, indent=2, ensure_ascii=False))
        return

    doc_lines = ["  - " + item for item in dossier["required_dossier_items"]]
    dossier_block = "\n".join(doc_lines)

    console.print(
        Panel(
            f"[bold green]HỒ SƠ ĐĂNG KÝ QUYỀN TÁC GIẢ PHẦN MỀM: {dossier['copyright_id']}[/]\n\n"
            f"  Tên phần mềm:        [bold cyan]{dossier['software_name']}[/] (v{dossier['version']})\n"
            f"  Tác giả:             [bold]{dossier['author_name']}[/]\n"
            f"  Quy mô mã nguồn:     {dossier['lines_of_code']:,} lines of code\n"
            f"  Kho lưu trữ:         {dossier['repository_url']}\n"
            f"  Cơ quan cấp phép:    {dossier['statutory_authority']}\n"
            f"  Lệ phí nhà nước:     [bold green]{_format_vnd(dossier['official_fee_vnd'])}[/]\n"
            f"  Thời hạn cấp bằng:   {dossier['timeline']}\n\n"
            f"  [bold]Hồ sơ thành phần theo NĐ 17/2023/NĐ-CP:[/{dossier_block}",
            title="[bold blue]Software Copyright Registration Ready[/]",
            border_style="green",
        )
    )


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
    fees = engine.calculate_statutory_fees(
        trademark_classes=trademark_classes,
        patent_claims=patent_claims,
        software_copyrights=software_copyrights,
    )

    if json_mode:
        typer.echo(json.dumps(fees, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold cyan]BẢNG TÍNH LỆ PHÍ NHÀ NƯỚC SỞ HỮU TRÍ TUỆ (THÔNG TƯ 263/2016/TT-BTC)[/]\n\n"
            f"  Lệ phí nhãn hiệu:    [bold green]{_format_vnd(fees['trademark_fees_vnd'])}[/] ({fees['trademark_classes_count']} nhóm ngành)\n"
            f"  Lệ phí sáng chế:     [bold yellow]{_format_vnd(fees['patent_fees_vnd'])}[/] ({fees['patent_claims_count']} điểm yêu cầu bảo hộ)\n"
            f"  Lệ phí bản quyền PM: [bold magenta]{_format_vnd(fees['software_copyright_fees_vnd'])}[/] ({fees['software_copyrights_count']} phần mềm)\n"
            f"  ---------------------------------------------------\n"
            f"  [bold]TỔNG LỆ PHÍ NHÀ NƯỚC:[/] [bold green]{_format_vnd(fees['total_official_fees_vnd'])}[/]",
            title="[bold blue]State Intellectual Property Fees[/]",
            border_style="cyan",
        )
    )


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

    table = Table(title="Danh Mục Tài Sản Sở Hữu Trí Tuệ", border_style="cyan")
    table.add_column("Loại TS", style="bold")
    table.add_column("Mã hồ sơ", style="cyan")
    table.add_column("Tên tác phẩm / Nhãn hiệu", style="green")
    table.add_column("Phân nhóm / Lĩnh vực")
    table.add_column("Trạng thái", style="yellow")

    for tm in portfolio["trademarks"]:
        table.add_row("Nhãn hiệu", tm["mark_id"], tm["mark_name"], f"Nhóm {tm['nice_class']}", tm["status"])
    for pat in portfolio["patents"]:
        table.add_row("Sáng chế", pat["patent_id"], pat["title"], pat["technical_field"], pat["status"])
    for cp in portfolio["software_copyrights"]:
        table.add_row("Bản quyền PM", cp["copyright_id"], cp["software_name"], f"v{cp['version']}", cp["status"])

    console.print(table)


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

    metrics = status_data["metrics"]

    console.print(
        Panel(
            f"[bold green]THÔNG SỐ QUẢN TRỊ HỆ THỐNG SỞ HỮU TRÍ TUỆ (IP)[/]\n\n"
            f"  Trạng thái:            {status_data['status'].upper()}\n"
            f"  Khung pháp lý:         {status_data['regulatory_framework']}\n"
            f"  Phân loại Nice:        {status_data['nice_classification_version']}\n"
            f"  Nhãn hiệu đăng ký:     {metrics['registered_trademarks']} đơn\n"
            f"  Sáng chế lưu trữ:      {metrics['drafted_patents']} đơn\n"
            f"  Bản quyền phần mềm:    {metrics['software_copyrights']} hồ sơ\n"
            f"  Cơ sở dữ liệu:         {status_data['database']}",
            title="[bold blue]IP Regulatory Engine Status[/]",
            border_style="green",
        )
    )
