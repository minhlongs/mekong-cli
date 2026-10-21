# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite (Phase 109)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

bailiff_app = typer.Typer(name="bailiff", help="Vietnamese Bailiff, Evidence Protocol (Vi Bằng) & Civil Enforcement Suite.")
console = Console()


def _engine():
    from src.core.bailiff_engine import BailiffEngine
    return BailiffEngine()


@bailiff_app.callback(invoke_without_command=True)
def bailiff_main(ctx: typer.Context, json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Báo cáo tổng quan hoạt động Thừa phát lại, lập Vi bằng chứng cứ, tống đạt tố tụng và thi hành án dân sự."""
    if ctx.invoked_subcommand is not None:
        return
    t = _engine().get_bailiff_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold blue]HỆ THỐNG THỪA PHÁT LẠI, VI BẰNG CHỨNG CỨ & THI HÀNH ÁN DÂN SỰ[/]\n\n"
        f"  Khung pháp lý & Quản lý:   [bold]Nghị định số 08/2020/NĐ-CP & Luật Thi hành án dân sự 2014[/] ([bold yellow]Bộ Tư pháp & Sở Tư pháp[/])\n"
        f"  Vi bằng & Tống đạt:        [bold]{t['total_evidence_protocols']}[/] vi bằng ([bold green]{t['valid_evidence_protocols']}[/] hợp lệ) | [bold]{t['total_process_services']}[/] văn bản ([bold yellow]{t['total_service_fees_vnd']:,.0f} VND[/])\n"
        f"  Xác minh & Thi hành án:    [bold]{t['total_asset_verifications']}[/] vụ xác minh ([bold green]{t['enforceable_debtors']}[/] có tài sản) | [bold]{t['total_civil_enforcements']}[/] vụ THA ([bold yellow]{t['total_judgment_amount_vnd']:,.0f} VND[/] / [bold cyan]{t['total_collected_amount_vnd']:,.0f} VND[/])",
        title="[bold blue]Vietnam Bailiff & Evidence Protocol Telemetry[/]", border_style="blue",
    ))


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
    r = _engine().create_evidence_protocol(requester, desc, category, location, media, bailiff, office, doj_reg, days)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_valid"] else "red"
    reg_tag = "[green]Đã vào sổ đăng ký trong 3 ngày[/]" if r["doj_registered"] and r["registration_days_elapsed"] <= 3 else "[red]Chưa đăng ký hợp lệ[/]"
    console.print(Panel(
        f"[bold]Mã số Vi bằng:[/]       [cyan]{r['protocol_id']}[/] | [bold]Thừa phát lại:[/] [bold]{r['bailiff_name']}[/] ({r['office_name']}) | YC: [bold]{r['requester_name']}[/] ({r['category_name']})\n"
        f"[bold]Nội dung & Địa điểm:[/] [italic yellow]{r['event_description']}[/] tại {r['location']} ({r['media_attachments_count']} tệp)\n"
        f"[bold]Đăng ký Sở Tư pháp:[/]  {reg_tag} | [bold]Hiệu lực:[/] [{sc}][bold]{r['status']}[/][/] — {r['statutory_notes']}",
        title=f"[{sc}]Vi Bằng Thừa Phát Lại (Nghị Định 08/2020/NĐ-CP)[/]", border_style=sc,
    ))


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
    r = _engine().serve_process_document(recipient, doc, address, agency, method, fee, present)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold]Mã biên bản tống đạt:[/] [cyan]{r['service_id']}[/] | [bold]Cơ quan ủy thác:[/] [bold]{r['court_or_agency']}[/]\n"
        f"[bold]Văn bản & Người nhận:[/] {r['document_title']} -> [bold]{r['recipient_name']}[/] ({r['recipient_address']} | {r['service_method']})\n"
        f"[bold]Chi phí & Kết quả:[/]    [bold yellow]{r['service_fee_vnd']:,.0f} VND[/] | [green]{r['status']}[/] — {r['statutory_notes']}",
        title="[green]Biên Bản Tống Đạt Văn Bản Tố Tụng[/]", border_style="green",
    ))


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
    r = _engine().verify_asset_conditions(debtor, judgment, accounts, balance, real_estate, vehicles)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    sc = "green" if r["is_enforceable"] else "red"
    console.print(Panel(
        f"[bold]Mã biên bản xác minh:[/] [cyan]{r['verification_id']}[/] | [bold]Đương sự:[/] [bold]{r['debtor_name']}[/] ({r['judgment_number']})\n"
        f"[bold]Tài sản & Kết luận:[/]   {r['bank_accounts_found']} TK ([bold yellow]{r['total_bank_balance_vnd']:,.0f} VND[/]) | BĐS: {r['real_estate_found']} | Xe: {r['vehicles_found']} | [{sc}][bold]{r['status']}[/][/] — {r['statutory_notes']}",
        title=f"[{sc}]Biên Bản Xác Minh Điều Kiện Thi Hành Án[/]", border_style=sc,
    ))


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
    r = _engine().execute_civil_judgment(debtor, amount, judgment, collected, voluntary)
    if json_mode:
        typer.echo(json.dumps(r, indent=2, ensure_ascii=False))
        return
    console.print(Panel(
        f"[bold]Mã hồ sơ THA:[/]        [cyan]{r['enforcement_id']}[/] | [bold]Đương sự:[/] [bold]{r['debtor_name']}[/] ({r['judgment_number']}) | [bold yellow]{r['judgment_amount_vnd']:,.0f} VND[/] / [bold cyan]{r['amount_collected_vnd']:,.0f} VND[/]\n"
        f"[bold]Biện pháp & Tiến độ:[/] {'[green]Tự nguyện chấp hành[/]' if r['voluntary_compliance'] else '[red]Áp dụng cưỡng chế kê biên[/]'} | [bold green]{r['status']}[/] — {r['statutory_notes']}",
        title="[green]Hồ Sơ Tổ Chức Thi Hành Án Dân Sự[/]", border_style="green",
    ))


@bailiff_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, PROTOCOLS, SERVICES, VERIFICATIONS, ENFORCEMENTS"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục Vi bằng, hồ sơ tống đạt, biên bản xác minh tài sản và thi hành án."""
    records = _engine().list_bailiff_records(category=category, limit=limit)
    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return
    if records.get("evidence_protocols"):
        table = Table(title="Danh Sách Vi Bằng Đã Lập")
        for col, st in [("Mã Vi Bằng", "cyan"), ("Người Yêu Cầu", "bold"), ("Phân Loại", None), ("Thừa Phát Lại", None), ("Sở Tư Pháp", None), ("Trạng Thái", None)]:
            table.add_column(col, style=st)
        for row in records["evidence_protocols"]:
            table.add_row(row["protocol_id"], row["requester_name"], row["event_category"], row["bailiff_name"], "Đã đăng ký" if row["doj_registered"] else "Chưa đăng ký", row["status"])
        console.print(table)


@bailiff_app.command("status")
def status_cmd(json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON")) -> None:
    """Hiển thị tổng quan các chỉ số telemetry hoạt động Thừa phát lại và thi hành án toàn quốc."""
    t = _engine().get_bailiff_telemetry()
    if json_mode:
        typer.echo(json.dumps(t, indent=2, ensure_ascii=False))
        return
    table = Table(title="Vietnam Bailiff & Evidence Protocol Telemetry")
    table.add_column("Chỉ Số Hoạt Động Thừa Phát Lại", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")
    for k, v in [("Tổng số Vi bằng đã lập", str(t["total_evidence_protocols"])), ("Vi bằng hợp chuẩn đăng ký Sở Tư pháp", str(t["valid_evidence_protocols"])), ("Tổng số lượt tống đạt tố tụng", str(t["total_process_services"])), ("Tổng phí tống đạt thu nộp", f"{t['total_service_fees_vnd']:,.0f} VND"), ("Tổng số vụ việc xác minh tài sản", str(t["total_asset_verifications"])), ("Số vụ việc có điều kiện thi hành án", str(t["enforceable_debtors"])), ("Tổng số vụ việc tổ chức thi hành án", str(t["total_civil_enforcements"])), ("Tổng giá trị bản án phải thi hành", f"{t['total_judgment_amount_vnd']:,.0f} VND"), ("Tổng số tiền đã thu hồi được", f"{t['total_collected_amount_vnd']:,.0f} VND")]:
        table.add_row(k, v)
    console.print(table)
