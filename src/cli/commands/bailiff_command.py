# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite (Phase 109)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

bailiff_app = typer.Typer(
    name="bailiff",
    help="Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite.",
)
console = Console()


@bailiff_app.callback(invoke_without_command=True)
def bailiff_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động Thừa phát lại, lập Vi bằng chứng cứ, tống đạt tố tụng và thi hành án dân sự."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    telemetry = engine.get_bailiff_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG THỪA PHÁT LẠI, VI BẰNG CHỨNG CỨ & THI HÀNH ÁN DÂN SỰ[/]\n\n"
            f"  Khung pháp lý:             [bold]Nghị định số 08/2020/NĐ-CP & Luật Thi hành án dân sự 2014[/]\n"
            f"  Cơ quan quản lý:           [bold yellow]Bộ Tư pháp & Các Sở Tư pháp tỉnh, thành phố trực thuộc TW[/]\n\n"
            f"  Vi bằng đã lập:            [bold]{telemetry['total_evidence_protocols']}[/] vi bằng ([bold green]{telemetry['valid_evidence_protocols']}[/] hợp lệ, đã đăng ký Sở Tư pháp)\n"
            f"  Tống đạt tố tụng:          [bold]{telemetry['total_process_services']}[/] văn bản ([bold yellow]{telemetry['total_service_fees_vnd']:,.0f} VND[/] phí tống đạt)\n"
            f"  Xác minh điều kiện THA:    [bold]{telemetry['total_asset_verifications']}[/] vụ ([bold green]{telemetry['enforceable_debtors']}[/] đương sự có tài sản kê biên)\n"
            f"  Thi hành án dân sự:        [bold]{telemetry['total_civil_enforcements']}[/] vụ việc\n"
            f"  Giá trị phải thi hành án:  [bold yellow]{telemetry['total_judgment_amount_vnd']:,.0f} VND[/]\n"
            f"  Số tiền đã thu hồi được:   [bold cyan]{telemetry['total_collected_amount_vnd']:,.0f} VND[/]",
            title="[bold blue]Vietnam Bailiff & Evidence Protocol Telemetry[/]",
            border_style="blue",
        )
    )


@bailiff_app.command("protocol")
def protocol_cmd(
    requester: str = typer.Argument(..., help="Họ và tên người yêu cầu lập Vi bằng"),
    desc: str = typer.Option("Ghi nhận hiện trạng ranh giới đất và công trình xây dựng liền kề", "--desc", "-d", help="Mô tả sự kiện, hành vi yêu cầu lập vi bằng"),
    category: str = typer.Option("PROPERTY_STATUS", "--category", "-c", help="Danh mục: PROPERTY_STATUS, TRANSACTION_DELIVERY, INTERNET_IP_INFRINGEMENT, INHERITANCE_WILL, COMMERCIAL_DEFAULT, CORPORATE_MEETING"),
    location: str = typer.Option("Số 15 Phố Tràng Tiền, Quận Hoàn Kiếm, Hà Nội", "--location", "-l", help="Địa điểm lập vi bằng"),
    media: int = typer.Option(5, "--media", "-m", help="Số lượng ảnh chụp, video, âm thanh đính kèm"),
    bailiff: str = typer.Option("Thừa phát lại Nguyễn Đức Toàn", "--bailiff", help="Họ tên Thừa phát lại thực hiện"),
    office: str = typer.Option("Văn phòng Thừa phát lại Ba Đình, Hà Nội", "--office", help="Tên Văn phòng Thừa phát lại"),
    doj_reg: bool = typer.Option(True, "--doj-reg/--no-doj-reg", help="Đã gửi đăng ký tại Sở Tư pháp theo Điều 39"),
    days: int = typer.Option(2, "--days", help="Số ngày làm việc kể từ ngày lập vi bằng đến khi gửi Sở Tư pháp"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Lập Vi bằng chứng cứ trực tiếp theo Nghị định 08/2020/NĐ-CP Điều 36-41."""
    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    result = engine.create_evidence_protocol(
        requester_name=requester,
        event_description=desc,
        event_category=category,
        location=location,
        media_attachments_count=media,
        bailiff_name=bailiff,
        office_name=office,
        doj_registered=doj_reg,
        registration_days_elapsed=days,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_valid"] else "red"
    console.print(
        Panel(
            f"[bold]Mã số Vi bằng:[/]           [cyan]{result['protocol_id']}[/]\n"
            f"[bold]Thừa phát lại:[/]           [bold]{result['bailiff_name']}[/] ({result['office_name']})\n"
            f"[bold]Người yêu cầu:[/]           [bold]{result['requester_name']}[/]\n"
            f"[bold]Phân loại sự kiện:[/]       {result['category_name']}\n"
            f"[bold]Nội dung ghi nhận:[/]       [italic yellow]{result['event_description']}[/]\n"
            f"[bold]Địa điểm lập:[/]            {result['location']}\n"
            f"[bold]Tài liệu đính kèm:[/]       {result['media_attachments_count']} tệp ảnh/video ghi âm\n"
            f"[bold]Đăng ký Sở Tư pháp:[/]      {'[green]Đã vào sổ đăng ký trong 3 ngày[/]' if result['doj_registered'] and result['registration_days_elapsed'] <= 3 else '[red]Chưa đăng ký hợp lệ[/]'}\n"
            f"[bold]Hiệu lực pháp lý:[/]        [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Giá trị chứng cứ:[/]        {result['statutory_notes']}",
            title=f"[{status_color}]Vi Bằng Thừa Phát Lại (Nghị Định 08/2020/NĐ-CP)[/]",
            border_style=status_color,
        )
    )


@bailiff_app.command("serve")
def serve_cmd(
    recipient: str = typer.Argument(..., help="Tên đương sự / cá nhân, tổ chức nhận văn bản"),
    doc: str = typer.Option("Thông báo thụ lý vụ án kinh doanh thương mại", "--doc", "-d", help="Tên văn bản tố tụng"),
    agency: str = typer.Option("Tòa án nhân dân Thành phố Hà Nội", "--agency", "-a", help="Cơ quan yêu cầu tống đạt"),
    address: str = typer.Option("Tổ dân phố 8, Phường Cống Vị, Ba Đình, Hà Nội", "--address", help="Địa chỉ nơi tống đạt"),
    method: str = typer.Option("DIRECT_DELIVERY", "--method", "-m", help="Phương thức: DIRECT_DELIVERY, POSTAL_AFFIXED, AUTHORITY_ASSISTANCE"),
    fee: float = typer.Option(150000.0, "--fee", help="Mức chi phí tống đạt (VND)"),
    present: bool = typer.Option(True, "--present/--no-present", help="Đương sự có mặt trực tiếp ký nhận"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tống đạt văn bản tố tụng của Tòa án, Viện kiểm sát và Cơ quan THADS theo Điều 32-35."""
    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    result = engine.serve_process_document(
        recipient_name=recipient,
        document_title=doc,
        recipient_address=address,
        court_or_agency=agency,
        service_method=method,
        service_fee_vnd=fee,
        recipient_present=present,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã biên bản tống đạt:[/]     [cyan]{result['service_id']}[/]\n"
            f"[bold]Cơ quan ủy thác:[/]          [bold]{result['court_or_agency']}[/]\n"
            f"[bold]Văn bản tống đạt:[/]         {result['document_title']}\n"
            f"[bold]Người nhận văn bản:[/]       [bold]{result['recipient_name']}[/]\n"
            f"[bold]Địa chỉ tống đạt:[/]         {result['recipient_address']}\n"
            f"[bold]Phương thức tống đạt:[/]     {result['service_method']}\n"
            f"[bold]Chi phí tống đạt:[/]         [bold yellow]{result['service_fee_vnd']:,.0f} VND[/]\n"
            f"[bold]Kết quả tống đạt:[/]         [green]{result['status']}[/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title="[green]Biên Bản Tống Đạt Văn Bản Tố Tụng[/]",
            border_style="green",
        )
    )


@bailiff_app.command("verify")
def verify_cmd(
    debtor: str = typer.Argument(..., help="Họ và tên người phải thi hành án"),
    judgment: str = typer.Option("Bản án số 45/2025/KDTM-ST", "--judgment", "-j", help="Số bản án, quyết định"),
    accounts: int = typer.Option(2, "--accounts", help="Số lượng tài khoản ngân hàng tìm thấy"),
    balance: float = typer.Option(350000000.0, "--balance", help="Tổng số dư tài khoản ngân hàng xác minh được (VND)"),
    real_estate: int = typer.Option(1, "--real-estate", help="Số lượng bất động sản sở hữu"),
    vehicles: int = typer.Option(1, "--vehicles", help="Số lượng phương tiện cơ giới sở hữu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Xác minh điều kiện thi hành án (tài khoản ngân hàng, bất động sản, xe cơ giới) theo Điều 43-50."""
    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    result = engine.verify_asset_conditions(
        debtor_name=debtor,
        judgment_number=judgment,
        bank_accounts_found=accounts,
        total_bank_balance_vnd=balance,
        real_estate_found=real_estate,
        vehicles_found=vehicles,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_enforceable"] else "red"
    console.print(
        Panel(
            f"[bold]Mã biên bản xác minh:[/]     [cyan]{result['verification_id']}[/]\n"
            f"[bold]Người phải thi hành án:[/]   [bold]{result['debtor_name']}[/]\n"
            f"[bold]Căn cứ bản án số:[/]         {result['judgment_number']}\n"
            f"[bold]Tài khoản ngân hàng:[/]      {result['bank_accounts_found']} tài khoản ([bold yellow]{result['total_bank_balance_vnd']:,.0f} VND[/])\n"
            f"[bold]Bất động sản phát hiện:[/]   {result['real_estate_found']} tài sản nhà đất có GCNQSDĐ\n"
            f"[bold]Phương tiện cơ giới:[/]      {result['vehicles_found']} ô tô/xe máy đăng ký chính chủ\n"
            f"[bold]Kết luận điều kiện THA:[/]   [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Chi tiết kết luận:[/]        {result['statutory_notes']}",
            title=f"[{status_color}]Biên Bản Xác Minh Điều Kiện Thi Hành Án[/]",
            border_style=status_color,
        )
    )


@bailiff_app.command("enforce")
def enforce_cmd(
    debtor: str = typer.Argument(..., help="Họ và tên người phải thi hành án"),
    amount: float = typer.Option(500000000.0, "--amount", "-a", help="Số tiền phải thi hành theo bản án (VND)"),
    judgment: str = typer.Option("Quyết định số 12/2026/QĐST-DS", "--judgment", "-j", help="Số bản án, quyết định"),
    collected: float = typer.Option(0.0, "--collected", "-c", help="Số tiền đã thu hồi được (VND)"),
    voluntary: bool = typer.Option(True, "--voluntary/--no-voluntary", help="Đương sự tự nguyện thi hành trong thời hạn 10 ngày"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tổ chức trực tiếp thi hành bản án, quyết định dân sự theo yêu cầu của đương sự (Điều 51-56)."""
    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    result = engine.execute_civil_judgment(
        debtor_name=debtor,
        judgment_amount_vnd=amount,
        judgment_number=judgment,
        amount_collected_vnd=collected,
        voluntary_compliance=voluntary,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã hồ sơ thi hành án:[/]     [cyan]{result['enforcement_id']}[/]\n"
            f"[bold]Người phải thi hành án:[/]   [bold]{result['debtor_name']}[/]\n"
            f"[bold]Căn cứ bản án:[/]            {result['judgment_number']}\n"
            f"[bold]Nghĩa vụ phải thi hành:[/]   [bold yellow]{result['judgment_amount_vnd']:,.0f} VND[/]\n"
            f"[bold]Số tiền đã thu hồi:[/]       [bold cyan]{result['amount_collected_vnd']:,.0f} VND[/]\n"
            f"[bold]Biện pháp thi hành:[/]       {'[green]Tự nguyện chấp hành[/]' if result['voluntary_compliance'] else '[red]Áp dụng cưỡng chế kê biên[/]'}\n"
            f"[bold]Tiến độ thi hành án:[/]      [bold green]{result['status']}[/]\n"
            f"[bold]Ghi chú chấp hành:[/]        {result['statutory_notes']}",
            title="[green]Hồ Sơ Tổ Chức Thi Hành Án Dân Sự[/]",
            border_style="green",
        )
    )


@bailiff_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, PROTOCOLS, SERVICES, VERIFICATIONS, ENFORCEMENTS"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục Vi bằng, hồ sơ tống đạt, biên bản xác minh tài sản và thi hành án."""
    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    records = engine.list_bailiff_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "evidence_protocols" in records and records["evidence_protocols"]:
        table = Table(title="Danh Sách Vi Bằng Đã Lập")
        table.add_column("Mã Vi Bằng", style="cyan")
        table.add_column("Người Yêu Cầu", style="bold")
        table.add_column("Phân Loại")
        table.add_column("Thừa Phát Lại")
        table.add_column("Sở Tư Pháp")
        table.add_column("Trạng Thái")
        for row in records["evidence_protocols"]:
            table.add_row(
                row["protocol_id"],
                row["requester_name"],
                row["event_category"],
                row["bailiff_name"],
                "Đã đăng ký" if row["doj_registered"] else "Chưa đăng ký",
                row["status"],
            )
        console.print(table)


@bailiff_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động Thừa phát lại và thi hành án toàn quốc."""
    from src.core.bailiff_engine import BailiffEngine

    engine = BailiffEngine()
    telemetry = engine.get_bailiff_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Vietnam Bailiff & Evidence Protocol Telemetry")
    table.add_column("Chỉ Số Hoạt Động Thừa Phát Lại", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")

    table.add_row("Tổng số Vi bằng đã lập", str(telemetry["total_evidence_protocols"]))
    table.add_row("Vi bằng hợp chuẩn đăng ký Sở Tư pháp", str(telemetry["valid_evidence_protocols"]))
    table.add_row("Tổng số lượt tống đạt tố tụng", str(telemetry["total_process_services"]))
    table.add_row("Tổng phí tống đạt thu nộp", f"{telemetry['total_service_fees_vnd']:,.0f} VND")
    table.add_row("Tổng số vụ việc xác minh tài sản", str(telemetry["total_asset_verifications"]))
    table.add_row("Số vụ việc có điều kiện thi hành án", str(telemetry["enforceable_debtors"]))
    table.add_row("Tổng số vụ việc tổ chức thi hành án", str(telemetry["total_civil_enforcements"]))
    table.add_row("Tổng giá trị bản án phải thi hành", f"{telemetry['total_judgment_amount_vnd']:,.0f} VND")
    table.add_row("Tổng số tiền đã thu hồi được", f"{telemetry['total_collected_amount_vnd']:,.0f} VND")

    console.print(table)
