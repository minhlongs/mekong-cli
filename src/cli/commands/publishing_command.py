# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Publishing, Printing, Distribution & Legal Depository Suite (Phase 86)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

publishing_app = typer.Typer(
    name="publishing",
    help="Vietnamese Publishing, Printing, Distribution & Legal Depository Suite.",
)
console = Console()


@publishing_app.callback(invoke_without_command=True)
def publishing_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động xuất bản, cấp mã ISBN, nộp lưu chiểu và điều kiện cơ sở in ấn."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ XUẤT BẢN, CẤP MÃ ISBN & NỘP LƯU CHIỂU QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['statutory_law']}[/]\n"
            f"  Nhà xuất bản được cấp phép:[bold cyan]{status_data['licensed_publishers']}/{status_data['total_publishers']}[/] NXB đạt chuẩn vốn >= 5 tỷ VND & trụ sở >= 200 m²\n"
            f"  Mã ISBN đã cấp phát:       [bold green]{status_data['total_isbn_publications']}[/] xuất bản phẩm (tiêu chuẩn ISBN-13 đầu 978-604)\n"
            f"  Hồ sơ nộp lưu chiểu:       [bold cyan]{status_data['total_legal_deposits']}[/] đợt lưu chiểu ([bold green]{status_data['deposit_compliance_rate_pct']}%[/] tuân thủ 10 ngày Điều 28)\n"
            f"  Cơ sở in ấn xuất bản phẩm: [bold yellow]{status_data['total_printing_facilities']}[/] nhà in thẩm định điều kiện an ninh trật tự & máy in",
            title="[bold green]Vietnam Publishing, Printing & Legal Depository Telemetry[/]",
            border_style="green",
        )
    )


@publishing_app.command("publisher")
def license_publisher_cmd(
    name: str = typer.Argument(..., help="Tên Nhà xuất bản"),
    agency: str = typer.Option("Hội Nhà văn Việt Nam", "--agency", "-a", help="Cơ quan chủ quản"),
    capital: float = typer.Option(5_500_000_000.0, "--capital", "-c", help="Vốn điều lệ (VND, tối thiểu 5 tỷ)"),
    area: float = typer.Option(240.0, "--area", help="Diện tích trụ sở làm việc (m², tối thiểu 200 m²)"),
    director: str = typer.Option("Nguyễn Văn Trưởng", "--director", "-d", help="Họ tên Tổng giám đốc / Giám đốc"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện thành lập và cấp phép Nhà xuất bản theo Điều 22 Luật Xuất bản 2012."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    res = engine.license_publisher(
        name=name,
        managing_agency=agency,
        charter_capital_vnd=capital,
        office_area_sqm=area,
        director_name=director,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_lic = res["status"] == "LICENSED"
    color = "green" if is_lic else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THẨM ĐỊNH ĐIỀU KIỆN THÀNH LẬP NHÀ XUẤT BẢN[/]\n\n"
            f"  Mã giấy phép:        [bold cyan]{res['publisher_code']}[/]\n"
            f"  Tên NXB:             [bold]{res['publisher_name']}[/]\n"
            f"  Cơ quan chủ quản:    [white]{res['managing_agency']}[/]\n"
            f"  Vốn điều lệ:         [bold]{res['charter_capital_vnd']:,.0f} VND[/] (Yêu cầu: [cyan]{res['min_required_capital_vnd']:,.0f} VND[/])\n"
            f"  Trụ sở làm việc:     [bold]{res['office_area_sqm']} m²[/] (Yêu cầu: [cyan]{res['min_required_area_sqm']} m²[/])\n"
            f"  Giám đốc phụ trách:  [white]{res['director_name']}[/]\n"
            f"  Kết luận thẩm định:  [bold {color}]{res['status']}[/]\n"
            + (f"  Vi phạm/Thiếu sót:   [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Đáp ứng đầy đủ Điều 22 Luật Xuất bản 2012[/]"),
            title=f"[bold {color}]Publisher Licensing Evaluation[/]",
            border_style=color,
        )
    )


@publishing_app.command("isbn")
def register_publication_cmd(
    title: str = typer.Argument(..., help="Tên tác phẩm xuất bản"),
    author: str = typer.Option("Tác giả Mekong", "--author", "-a", help="Tên tác giả / Dịch giả"),
    publisher_code: str = typer.Option("GP-NXB-2026-MK01", "--publisher", "-p", help="Mã NXB cấp phép"),
    category: str = typer.Option("literature", "--category", "-c", help="Thể loại: literature, science, economic, education"),
    copies: int = typer.Option(1000, "--copies", "-n", help="Số lượng in (bản)"),
    price: float = typer.Option(120000.0, "--price", help="Giá bìa (VND)"),
    ebook: bool = typer.Option(False, "--ebook/--no-ebook", help="Xuất bản phẩm điện tử"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đăng ký xuất bản, cấp mã ISBN-13 và ban hành Quyết định xuất bản (Điều 25, 26 Luật Xuất bản)."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    res = engine.register_publication(
        publisher_code=publisher_code,
        title=title,
        author_name=author,
        category=category,
        copies_count=copies,
        price_vnd=price,
        is_ebook=ebook,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]QUYẾT ĐỊNH XUẤT BẢN & MÃ SỐ CHUẨN QUỐC TẾ (ISBN)[/]\n\n"
            f"  Mã số ISBN-13:       [bold cyan]{res['isbn']}[/] (Tiêu chuẩn EAN-13 Việt Nam)\n"
            f"  Tác phẩm:            [bold]{res['title']}[/]\n"
            f"  Tác giả / Dịch giả:  [white]{res['author_name']}[/]\n"
            f"  Mã NXB xuất bản:     [white]{res['publisher_code']}[/]\n"
            f"  Thể loại:            [yellow]{res['category']}[/] ({'Xuất bản phẩm điện tử' if res['is_ebook'] else 'Sách in'})\n"
            f"  Số lượng & Giá bìa:  [bold]{res['copies_count']:,} bản[/] | [green]{res['price_vnd']:,.0f} VND[/]\n"
            f"  Số quyết định XB:    [bold]{res['decision_number']}[/]\n"
            f"  Cơ quan cấp mã:      [bold]{res['statutory_authority']}[/]",
            title="[bold green]Publication Registered & ISBN Allocated[/]",
            border_style="green",
        )
    )


@publishing_app.command("deposit")
def submit_deposit_cmd(
    isbn: str = typer.Argument(..., help="Mã số ISBN của xuất bản phẩm"),
    copies: int = typer.Option(3, "--copies", "-c", help="Số bản nộp lưu chiểu cho cơ quan quản lý (tối thiểu 3 bản)"),
    library_copies: int = typer.Option(2, "--library-copies", "-l", help="Số bản nộp Thư viện Quốc gia (tối thiểu 2 bản)"),
    date: str = typer.Option(None, "--date", "-d", help="Ngày nộp lưu chiểu (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Nộp lưu chiểu xuất bản phẩm và tính toán thời hạn 10 ngày trước khi phát hành (Điều 28 Luật Xuất bản)."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    res = engine.submit_legal_deposit(
        isbn=isbn,
        copies_deposited=copies,
        national_library_copies=library_copies,
        submission_date=date,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["status"] == "DEPOSITED"
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]XÁC NHẬN NỘP LƯU CHIỂU XUẤT BẢN PHẨM (ĐIỀU 28 LUẬT XUẤT BẢN)[/]\n\n"
            f"  Mã số lưu chiểu:     [bold cyan]{res['deposit_code']}[/]\n"
            f"  Mã ISBN:             [white]{res['isbn']}[/]\n"
            f"  Số bản nộp quản lý:  [bold]{res['copies_deposited']} bản[/] (Quy định: tối thiểu 3 bản)\n"
            f"  Nộp Thư viện QG:     [bold]{res['national_library_copies']} bản[/] (Quy định: tối thiểu 2 bản)\n"
            f"  Ngày nộp lưu chiểu:  [cyan]{res['submission_date']}[/]\n"
            f"  Hạn cấm phát hành:   [bold red]Đến hết ngày {res['embargo_until_date']}[/] (10 ngày đọc duyệt)\n"
            f"  Ngày được phát hành: [bold green]Từ ngày {res['embargo_until_date']}[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            + (f"  Vi phạm:             [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Đáp ứng đầy đủ thủ tục nộp lưu chiểu theo luật định[/]"),
            title=f"[bold {color}]Legal Depository Submission Receipt[/]",
            border_style=color,
        )
    )


@publishing_app.command("release")
def audit_release_cmd(
    deposit_code: str = typer.Argument(..., help="Mã xác nhận nộp lưu chiểu"),
    current_date: str = typer.Option(None, "--date", "-d", help="Ngày kiểm tra phát hành (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra điều kiện phát hành sau thời hạn 10 ngày nộp lưu chiểu."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    try:
        res = engine.audit_release_eligibility(deposit_code=deposit_code, current_date=current_date)
    except ValueError as exc:
        console.print(f"[bold red]Lỗi tra cứu:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_rel = res["can_release"]
    color = "green" if is_rel else "red"

    console.print(
        Panel(
            f"[bold {color}]KIỂM TRA ĐIỀU KIỆN PHÁT HÀNH XUẤT BẢN PHẨM[/]\n\n"
            f"  Mã lưu chiểu:        [bold cyan]{res['deposit_code']}[/]\n"
            f"  Mã ISBN:             [white]{res['isbn']}[/]\n"
            f"  Ngày nộp:            [white]{res['submission_date']}[/] | Hạn lưu chiểu: [white]{res['embargo_until_date']}[/]\n"
            f"  Được phép phát hành: [bold {color}]{'CÓ' if is_rel else 'CHƯA ĐƯỢC PHÉP'}[/]\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]\n"
            f"  Đánh giá:            [bold]{res['evaluation']}[/]",
            title=f"[bold {color}]Distribution Release Authorization Audit[/]",
            border_style=color,
        )
    )


@publishing_app.command("printing")
def audit_printing_cmd(
    name: str = typer.Argument(..., help="Tên cơ sở in xuất bản phẩm"),
    address: str = typer.Option("KCN Tân Bình, TP. Hồ Chí Minh", "--address", "-a", help="Địa chỉ xưởng in"),
    security: bool = typer.Option(True, "--security/--no-security", help="Có Giấy chứng nhận đủ điều kiện an ninh trật tự"),
    presses: int = typer.Option(2, "--presses", "-p", help="Số lượng máy in offset / kỹ thuật số"),
    qualified: bool = typer.Option(True, "--qualified/--no-qualified", help="Người đứng đầu có bằng cấp chuyên ngành in"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện hoạt động cơ sở in xuất bản phẩm theo Nghị định 195/2013/NĐ-CP."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    res = engine.audit_printing_facility(
        facility_name=name,
        address=address,
        has_security_clearance=security,
        offset_presses_count=presses,
        manager_qualified=qualified,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_comp = res["status"] == "COMPLIANT"
    color = "green" if is_comp else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH ĐIỀU KIỆN HOẠT ĐỘNG CƠ SỞ IN XUẤT BẢN PHẨM[/]\n\n"
            f"  Mã cơ sở in:         [bold cyan]{res['facility_code']}[/]\n"
            f"  Tên cơ sở:           [bold]{res['facility_name']}[/]\n"
            f"  Địa chỉ xưởng:       [white]{res['address']}[/]\n"
            f"  An ninh trật tự:     [bold]{'Đạt chuẩn Công an' if res['has_security_clearance'] else 'CHƯA CÓ GIẤY PHÉP'}[/]\n"
            f"  Thiết bị in ấn:      [bold]{res['offset_presses_count']} máy in công nghiệp[/]\n"
            f"  Trình độ quản lý:    [bold]{'Đạt chuẩn đại học chuyên ngành' if res['manager_qualified'] else 'CHƯA ĐẠT CHUẨN'}[/]\n"
            f"  Kết luận thẩm định:  [bold {color}]{res['status']}[/]\n"
            + (f"  Thiếu sót:           [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Đáp ứng đầy đủ Nghị định 195/2013/NĐ-CP[/]"),
            title=f"[bold {color}]Printing Facility Audit Result[/]",
            border_style=color,
        )
    )


@publishing_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("publications", help="Danh mục: publications, publishers, deposits, printing"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục xuất bản phẩm, nhà xuất bản, hồ sơ lưu chiểu hoặc xưởng in."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ xuất bản [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["publishers", "nxb"]:
        table.add_column("Mã NXB", style="bold cyan")
        table.add_column("Tên NXB", style="white")
        table.add_column("Cơ quan chủ quản", style="yellow")
        table.add_column("Vốn điều lệ", style="white")
        table.add_column("Diện tích", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "LICENSED" else "red"
            table.add_row(r.get("publisher_code", ""), r.get("publisher_name", ""), r.get("managing_agency", ""), f"{r.get('charter_capital_vnd', 0):,.0f} VND", f"{r.get('office_area_sqm', 0)} m²", f"[{color}]{r.get('status', '')}[/]")
    elif category in ["deposits", "luu_chieu"]:
        table.add_column("Mã lưu chiểu", style="bold cyan")
        table.add_column("Mã ISBN", style="white")
        table.add_column("Bản nộp", style="yellow")
        table.add_column("Ngày nộp", style="white")
        table.add_column("Hết hạn cấm phát hành", style="green")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "DEPOSITED" else "red"
            table.add_row(r.get("deposit_code", ""), r.get("isbn", ""), f"{r.get('copies_deposited', 0)}/{r.get('national_library_copies', 0)}", r.get("submission_date", ""), r.get("embargo_until_date", ""), f"[{color}]{r.get('status', '')}[/]")
    elif category in ["printing", "printers"]:
        table.add_column("Mã xưởng in", style="bold cyan")
        table.add_column("Tên cơ sở", style="white")
        table.add_column("Địa chỉ", style="white")
        table.add_column("Số máy in", style="yellow")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "COMPLIANT" else "red"
            table.add_row(r.get("facility_code", ""), r.get("facility_name", ""), r.get("address", ""), str(r.get("offset_presses_count", 0)), f"[{color}]{r.get('status', '')}[/]")
    else:
        table.add_column("Mã ISBN", style="bold cyan")
        table.add_column("Tác phẩm", style="white")
        table.add_column("Tác giả", style="yellow")
        table.add_column("Số QĐXB", style="white")
        table.add_column("Số lượng", style="green")
        table.add_column("Giá bìa", style="white")
        for r in records:
            table.add_row(r.get("isbn", ""), r.get("title", ""), r.get("author_name", ""), r.get("decision_number", ""), f"{r.get('copies_count', 0):,} bản", f"{r.get('price_vnd', 0):,.0f} VND")

    console.print(table)


@publishing_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp ngành xuất bản, in ấn và nộp lưu chiểu quốc gia."""
    from src.core.publishing_engine import PublishingEngine

    engine = PublishingEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
