# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Physical Training, Sports & Anti-Doping Suite (Phase 105)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sports_app = typer.Typer(
    name="sports",
    help="Vietnamese Physical Training, Sports, Professional Athletics & Anti-Doping Suite.",
)
console = Console()


@sports_app.callback(invoke_without_command=True)
def sports_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động thể dục thể thao, hợp đồng VĐV chuyên nghiệp, kiểm tra doping và thể thao mạo hiểm."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    telemetry = engine.get_sports_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN TRỊ THỂ DỤC THỂ THAO & PHÒNG CHỐNG DOPING QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Thể dục, Thể thao 2006 (Sửa đổi 2018 số 26/2018/QH14)[/]\n"
            f"  Cơ quan quản lý chuyên môn: [bold yellow]Cục Thể dục thể thao & Trung tâm Doping - Y học Thể thao (VADC)[/]\n\n"
            f"  Hợp đồng VĐV chuyên nghiệp: [bold]{telemetry['total_contracts']}[/] ([bold green]{telemetry['approved_contracts']}[/] hợp đồng chuẩn Điều 32, 33)\n"
            f"  Tổng quỹ lương VĐV:        [bold yellow]{telemetry['total_salary_pool_vnd']:,.0f} VND[/]\n"
            f"  Kiểm tra Doping (WADA):    [bold]{telemetry['total_doping_tests']}[/] mẫu thử ([bold red]{telemetry['positive_doping_cases']}[/] ca vi phạm, [bold cyan]{telemetry['tue_exemptions']}[/] miễn trừ TUE)\n"
            f"  Tỷ lệ mẫu sạch:            [bold green]{telemetry['clean_doping_rate_pct']}%[/]\n"
            f"  Cơ sở thể thao mạo hiểm:   [bold]{telemetry['total_extreme_permits']}[/] ([bold green]{telemetry['licensed_extreme_facilities']}[/] cơ sở được cấp phép Thông tư 04/2019)\n"
            f"  Giải thi đấu thể thao:     [bold]{telemetry['total_tournaments']}[/] ([bold green]{telemetry['sanctioned_tournaments']}[/] giải đấu phê duyệt an toàn Điều 37, 38)",
            title="[bold blue]Vietnam National Sports & Anti-Doping Telemetry[/]",
            border_style="blue",
        )
    )


@sports_app.command("contract")
def contract_cmd(
    name: str = typer.Argument(..., help="Họ tên vận động viên chuyên nghiệp"),
    sport: str = typer.Option("BÓNG ĐÁ", "--sport", "-s", help="Môn thể thao thi đấu (BÓNG ĐÁ, ĐIỀN KINH, BƠI LỘI, VÕ THUẬT)"),
    club: str = typer.Option("CLB Hà Nội", "--club", "-c", help="Câu lạc bộ / Đơn vị quản lý sử dụng"),
    contract_type: str = typer.Option("PROFESSIONAL", "--type", "-t", help="Loại hợp đồng: PROFESSIONAL, TRANSFER, TRAINING"),
    salary: float = typer.Option(35000000.0, "--salary", help="Mức tiền lương hàng tháng (VND)"),
    months: int = typer.Option(24, "--months", "-m", help="Thời hạn hợp đồng lao động (tháng)"),
    insurance: bool = typer.Option(True, "--insurance/--no-insurance", help="Đã tham gia bảo hiểm tai nạn lao động, bệnh nghề nghiệp & BHYT"),
    training_fee: float = typer.Option(0.0, "--training-fee", help="Chi phí đào tạo bồi hoàn (VND)"),
    transfer_fee: float = typer.Option(0.0, "--transfer-fee", help="Phí chuyển nhượng vận động viên (VND)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký và thẩm định hợp đồng lao động VĐV chuyên nghiệp, chuyển nhượng theo Điều 32, 33 Luật TDTT."""
    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    result = engine.contract_athlete(
        athlete_name=name,
        sport=sport,
        club_name=club,
        contract_type=contract_type,
        salary_vnd=salary,
        duration_months=months,
        insurance_covered=insurance,
        training_fee_vnd=training_fee,
        transfer_fee_vnd=transfer_fee,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["status"] == "APPROVED" else "red"
    console.print(
        Panel(
            f"[bold]Mã hợp đồng:[/]             [cyan]{result['contract_id']}[/]\n"
            f"[bold]Vận động viên:[/]           [bold]{result['athlete_name']}[/] ({result['sport']})\n"
            f"[bold]Câu lạc bộ:[/]              {result['club_name']}\n"
            f"[bold]Loại hợp đồng:[/]           {result['contract_type']}\n"
            f"[bold]Mức lương tháng:[/]         [yellow]{result['salary_vnd']:,.0f} VND[/]\n"
            f"[bold]Thời hạn:[/]                {result['duration_months']} tháng\n"
            f"[bold]Bảo hiểm thể thao:[/]       {'[green]Đầy đủ[/]' if result['insurance_covered'] else '[red]Chưa tham gia[/]'}\n"
            f"[bold]Phí chuyển nhượng:[/]       {result['transfer_fee_vnd']:,.0f} VND\n"
            f"[bold]Trạng thái thẩm định:[/]    [{status_color}]{result['status']}[/]\n"
            f"[bold]Ghi chú pháp lý:[/]         {result['statutory_notes']}",
            title=f"[{status_color}]Đăng Ký Hợp Đồng VĐV Chuyên Nghiệp[/]",
            border_style=status_color,
        )
    )


@sports_app.command("doping")
def doping_cmd(
    name: str = typer.Argument(..., help="Họ tên vận động viên được lấy mẫu kiểm tra"),
    sport: str = typer.Option("ĐIỀN KINH", "--sport", "-s", help="Môn thể thao"),
    sample_type: str = typer.Option("URINE", "--sample-type", help="Loại mẫu thử: URINE, BLOOD"),
    substance: Optional[str] = typer.Option(None, "--substance", help="Tên hoạt chất phát hiện (nếu có)"),
    wada_class: Optional[str] = typer.Option(None, "--wada-class", "-w", help="Nhóm chất cấm WADA (S0–S9, M1–M3)"),
    has_tue: bool = typer.Option(False, "--has-tue/--no-tue", help="Có hồ sơ xin miễn trừ do điều trị y tế TUE"),
    tue_approved: bool = typer.Option(False, "--tue-approved/--no-tue-approved", help="Đã được Hội đồng Y khoa VADC phê duyệt miễn trừ TUE"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Ngày lấy mẫu (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Xử lý kết quả kiểm tra Doping và đánh giá chế tài xử phạt theo WADA Code & Thông tư 17/2019."""
    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    result = engine.test_doping(
        athlete_name=name,
        sport=sport,
        sample_type=sample_type,
        substance_detected=substance,
        wada_class=wada_class,
        has_tue=has_tue,
        tue_approved=tue_approved,
        collection_date=date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    if result["result"] == "NEGATIVE":
        color = "green"
    elif result["result"] == "TUE_EXEMPTION":
        color = "cyan"
    else:
        color = "red"

    console.print(
        Panel(
            f"[bold]Mã kiểm tra:[/]             [cyan]{result['test_id']}[/]\n"
            f"[bold]Vận động viên:[/]           [bold]{result['athlete_name']}[/] ({result['sport']})\n"
            f"[bold]Loại mẫu:[/]                {result['sample_type']}\n"
            f"[bold]Ngày lấy mẫu:[/]            {result['collection_date']}\n"
            f"[bold]Hoạt chất phát hiện:[/]     {result['substance_detected'] or 'Không phát hiện (Âm tính)'}\n"
            f"[bold]Nhóm WADA:[/]               {result['wada_class'] or 'N/A'} ({result['wada_class_description']})\n"
            f"[bold]Miễn trừ y tế TUE:[/]       {'[green]Hợp lệ[/]' if result['tue_approved'] else '[red]Không có/Chưa duyệt[/]'}\n"
            f"[bold]Kết luận:[/]                [{color}][bold]{result['result']}[/][/]\n"
            f"[bold]Án phạt cấm thi đấu:[/]     [yellow]{result['sanction_months']} tháng[/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{color}]Biên Bản Kiểm Tra Doping & Chế Tài WADA[/]",
            border_style=color,
        )
    )


@sports_app.command("extreme")
def extreme_cmd(
    facility: str = typer.Argument(..., help="Tên cơ sở/doanh nghiệp kinh doanh thể thao mạo hiểm"),
    sport_type: str = typer.Option("PARAGLIDING", "--sport-type", "-s", help="Môn thể thao mạo hiểm: PARAGLIDING, ROCK_CLIMBING, SCUBA_DIVING, BUNGEE_JUMPING"),
    certified_coach: bool = typer.Option(True, "--coach/--no-coach", help="Có HLV/HDV có chứng chỉ chuyên môn"),
    rescue_certified: bool = typer.Option(True, "--rescue/--no-rescue", help="Có nhân viên cứu nạn cứu hộ đạt chuẩn"),
    equipment: bool = typer.Option(True, "--equipment/--no-equipment", help="Trang thiết bị chuyên dùng kiểm định an toàn"),
    medical: bool = typer.Option(True, "--medical/--no-medical", help="Có phương án y tế và cơ sở cấp cứu liên kết"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm định điều kiện an toàn và cấp phép cơ sở kinh doanh thể thao mạo hiểm theo Thông tư 04/2019."""
    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    result = engine.license_extreme_sport(
        facility_name=facility,
        sport_type=sport_type,
        certified_coach=certified_coach,
        rescue_certified=rescue_certified,
        equipment_inspected=equipment,
        medical_plan=medical,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    color = "green" if result["status"] == "LICENSED" else "red"
    console.print(
        Panel(
            f"[bold]Mã cấp phép:[/]             [cyan]{result['permit_id']}[/]\n"
            f"[bold]Cơ sở kinh doanh:[/]        [bold]{result['facility_name']}[/]\n"
            f"[bold]Môn thể thao mạo hiểm:[/]   {result['sport_type']}\n"
            f"[bold]HLV có chứng chỉ:[/]        {'[green]Đạt chuẩn[/]' if result['certified_coach'] else '[red]Vi phạm[/]'}\n"
            f"[bold]Nhân viên cứu hộ:[/]        {'[green]Đạt chuẩn[/]' if result['rescue_certified'] else '[red]Vi phạm[/]'}\n"
            f"[bold]Kiểm định an toàn:[/]       {'[green]Đã kiểm định[/]' if result['equipment_inspected'] else '[red]Chưa kiểm định[/]'}\n"
            f"[bold]Phương án cấp cứu y tế:[/]  {'[green]Sẵn sàng[/]' if result['medical_plan'] else '[red]Thiếu phương án[/]'}\n"
            f"[bold]Kết luận thẩm định:[/]      [{color}][bold]{result['status']}[/][/]\n"
            f"[bold]Danh sách vi phạm:[/]       {', '.join(result['violations']) if result['violations'] else '[green]Không có vi phạm[/]'}",
            title=f"[{color}]Thẩm Định Cơ Sở Kinh Doanh Thể Thao Mạo Hiểm[/]",
            border_style=color,
        )
    )


@sports_app.command("tournament")
def tournament_cmd(
    name: str = typer.Argument(..., help="Tên giải thi đấu thể thao"),
    sport: str = typer.Option("BÓNG ĐÁ", "--sport", "-s", help="Môn thể thao thi đấu"),
    scale: str = typer.Option("NATIONAL", "--scale", help="Quy mô giải đấu: NATIONAL, REGIONAL, PROVINCIAL"),
    organizer: str = typer.Option("Liên đoàn Bóng đá Việt Nam", "--organizer", "-o", help="Đơn vị tổ chức"),
    venue: str = typer.Option("Sân vận động Quốc gia Mỹ Đình", "--venue", "-v", help="Địa điểm / Nhà thi đấu"),
    lighting: float = typer.Option(1500.0, "--lighting", help="Độ rọi chiếu sáng thi đấu (Lux, tối thiểu 500)"),
    medical: bool = typer.Option(True, "--medical/--no-medical", help="Có đội ngũ y tế thường trực"),
    emergency: bool = typer.Option(True, "--emergency/--no-emergency", help="Có đầy đủ cửa thoát hiểm khẩn cấp"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra điều kiện an toàn và phê duyệt tổ chức giải thi đấu thể thao theo Điều 37, 38 Luật TDTT."""
    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    result = engine.sanction_tournament(
        tournament_name=name,
        sport=sport,
        scale=scale,
        organizer=organizer,
        venue_name=venue,
        lighting_lux=lighting,
        medical_team=medical,
        emergency_exits=emergency,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    color = "green" if result["status"] == "SANCTIONED" else "red"
    console.print(
        Panel(
            f"[bold]Mã phê duyệt:[/]            [cyan]{result['sanction_id']}[/]\n"
            f"[bold]Tên giải đấu:[/]            [bold]{result['tournament_name']}[/] ({result['sport']})\n"
            f"[bold]Quy mô giải:[/]             {result['scale']}\n"
            f"[bold]Đơn vị tổ chức:[/]          {result['organizer']}\n"
            f"[bold]Địa điểm thi đấu:[/]        {result['venue_name']}\n"
            f"[bold]Độ rọi chiếu sáng:[/]       [yellow]{result['lighting_lux']:.0f} Lux[/]\n"
            f"[bold]Bố trí y tế cấp cứu:[/]     {'[green]Đạt[/]' if result['medical_team'] else '[red]Không đạt[/]'}\n"
            f"[bold]Lối thoát hiểm:[/]          {'[green]Đạt[/]' if result['emergency_exits'] else '[red]Không đạt[/]'}\n"
            f"[bold]Kết luận phê duyệt:[/]      [{color}][bold]{result['status']}[/][/]\n"
            f"[bold]Ghi chú pháp lý:[/]         {result['statutory_notes']}",
            title=f"[{color}]Phê Duyệt Tổ Chức Giải Thi Đấu Thể Thao[/]",
            border_style=color,
        )
    )


@sports_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục tra cứu: ALL, CONTRACTS, DOPING, EXTREME, TOURNAMENTS"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ hợp đồng VĐV, kết quả doping, giấy phép thể thao mạo hiểm và giải đấu."""
    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    records = engine.list_sports_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "contracts" in records and records["contracts"]:
        table = Table(title="Danh Sách Hợp Đồng Vận Động Viên Chuyên Nghiệp")
        table.add_column("Mã HĐ", style="cyan")
        table.add_column("Vận Động Viên", style="bold")
        table.add_column("Môn", style="magenta")
        table.add_column("CLB", style="green")
        table.add_column("Lương/Tháng", style="yellow")
        table.add_column("Trạng Thái")
        for row in records["contracts"]:
            table.add_row(
                row["contract_id"],
                row["athlete_name"],
                row["sport"],
                row["club_name"],
                f"{row['salary_vnd']:,.0f} VND",
                row["status"],
            )
        console.print(table)

    if "doping_tests" in records and records["doping_tests"]:
        table = Table(title="Kết Quả Kiểm Tra Doping & WADA Sanctions")
        table.add_column("Mã Test", style="cyan")
        table.add_column("Vận Động Viên", style="bold")
        table.add_column("Môn")
        table.add_column("Hoạt Chất")
        table.add_column("WADA Class", style="yellow")
        table.add_column("Kết Quả")
        table.add_column("Án Phạt", style="red")
        for row in records["doping_tests"]:
            table.add_row(
                row["test_id"],
                row["athlete_name"],
                row["sport"],
                row["substance_detected"] or "Âm tính",
                row["wada_class"] or "-",
                row["result"],
                f"{row['sanction_months']} tháng" if row["sanction_months"] > 0 else "-",
            )
        console.print(table)


@sports_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry thể thao và phòng chống doping quốc gia."""
    from src.core.sports_engine import SportsEngine

    engine = SportsEngine()
    telemetry = engine.get_sports_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Vietnam National Sports Telemetry")
    table.add_column("Chỉ Số Nghiệp Vụ", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")

    table.add_row("Tổng hợp đồng VĐV đã đăng ký", str(telemetry["total_contracts"]))
    table.add_row("Hợp đồng VĐV hợp chuẩn phê duyệt", str(telemetry["approved_contracts"]))
    table.add_row("Tổng quỹ lương VĐV chuyên nghiệp", f"{telemetry['total_salary_pool_vnd']:,.0f} VND")
    table.add_row("Tổng mẫu kiểm tra Doping (WADA)", str(telemetry["total_doping_tests"]))
    table.add_row("Số ca dương tính vi phạm", str(telemetry["positive_doping_cases"]))
    table.add_row("Số ca miễn trừ điều trị TUE", str(telemetry["tue_exemptions"]))
    table.add_row("Tỷ lệ mẫu thử sạch", f"{telemetry['clean_doping_rate_pct']}%")
    table.add_row("Cơ sở thể thao mạo hiểm cấp phép", f"{telemetry['licensed_extreme_facilities']} / {telemetry['total_extreme_permits']}")
    table.add_row("Giải thi đấu thể thao phê duyệt", f"{telemetry['sanctioned_tournaments']} / {telemetry['total_tournaments']}")

    console.print(table)
