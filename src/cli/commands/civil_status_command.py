# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite (Phase 108)."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

civil_status_app = typer.Typer(
    name="civil-status",
    help="Vietnamese Civil Registration, Vital Statistics & Identification Registry Suite.",
)
console = Console()


@civil_status_app.callback(invoke_without_command=True)
def civil_status_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan đăng ký hộ tịch, thống kê sinh tử và quản lý định danh căn cước công dân."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    telemetry = engine.get_civil_status_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG ĐĂNG KÝ HỘ TỊCH & CĂN CƯỚC DÂN CƯ QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Hộ tịch 2014 & Luật Căn cước 2023 (Luật số 26/2023/QH15)[/]\n"
            f"  Cơ sở dữ liệu quốc gia:    [bold yellow]CSDL Hộ tịch điện tử & CSDL Căn cước VNeID Mức 2[/]\n\n"
            f"  Đăng ký khai sinh:         [bold]{telemetry['total_birth_registrations']}[/] trẻ em ([bold green]{telemetry['on_time_birth_registrations']}[/] đúng hạn 60 ngày)\n"
            f"  Đăng ký kết hôn:           [bold]{telemetry['total_marriage_registrations']}[/] cặp ([bold green]{telemetry['approved_marriages']}[/] hợp lệ theo Luật HN&GĐ)\n"
            f"  Đăng ký khai tử:           [bold]{telemetry['total_death_registrations']}[/] trường hợp\n"
            f"  Tăng tự nhiên dân số:      [bold cyan]+{telemetry['population_natural_growth']}[/] nhân khẩu\n"
            f"  Thẻ Căn cước đã cấp:       [bold]{telemetry['total_identity_cards_issued']}[/] thẻ ([bold green]{telemetry['active_vneid_level2_users']}[/] kích hoạt VNeID Mức 2)\n"
            f"  Bản sao trích lục hộ tịch: [bold]{telemetry['total_civil_extracts_issued']}[/] trích lục đã cấp",
            title="[bold blue]Vietnam Civil Registration & Identification Telemetry[/]",
            border_style="blue",
        )
    )


@civil_status_app.command("birth")
def birth_cmd(
    child_name: str = typer.Argument(..., help="Họ và tên khai sinh của trẻ"),
    dob: str = typer.Option("2026-09-01", "--dob", "-d", help="Ngày sinh (YYYY-MM-DD)"),
    gender: str = typer.Option("NAM", "--gender", "-g", help="Giới tính: NAM / NỮ"),
    mother: str = typer.Option("Nguyễn Thị Mai", "--mother", "-m", help="Họ và tên người mẹ"),
    father: Optional[str] = typer.Option("Trần Văn Hùng", "--father", "-f", help="Họ và tên người cha"),
    province: str = typer.Option("Hà Nội", "--province", "-p", help="Tỉnh/Thành phố đăng ký khai sinh"),
    place: str = typer.Option("Bệnh viện Phụ sản Hà Nội", "--place", help="Nơi sinh"),
    notice: bool = typer.Option(True, "--notice/--no-notice", help="Có Giấy chứng sinh của cơ sở y tế"),
    reg_date: Optional[str] = typer.Option(None, "--reg-date", help="Ngày nộp hồ sơ đăng ký khai sinh"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký khai sinh và tự động tạo Số định danh cá nhân 12 số theo Luật Hộ tịch & Luật Căn cước."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    result = engine.register_birth(
        child_name=child_name,
        date_of_birth=dob,
        gender=gender,
        mother_name=mother,
        father_name=father,
        birth_place=place,
        province=province,
        hospital_birth_notice=notice,
        registration_date=reg_date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_registered"] else "red"
    console.print(
        Panel(
            f"[bold]Mã giấy khai sinh:[/]       [cyan]{result['cert_id']}[/]\n"
            f"[bold]Số định danh cá nhân:[/]    [bold yellow]{result['personal_id']}[/]\n"
            f"[bold]Họ và tên trẻ:[/]            [bold]{result['child_name']}[/]\n"
            f"[bold]Giới tính:[/]                {result['gender']}\n"
            f"[bold]Ngày tháng năm sinh:[/]      {result['date_of_birth']}\n"
            f"[bold]Nơi sinh:[/]                 {result['birth_place']}\n"
            f"[bold]Mẹ đẻ:[/]                    {result['mother_name']}\n"
            f"[bold]Cha đẻ:[/]                   {result['father_name'] or 'Chưa xác định'}\n"
            f"[bold]Đăng ký đúng hạn:[/]         {'[green]Đúng hạn trong 60 ngày[/]' if result['registered_on_time'] else '[yellow]Quá hạn 60 ngày[/]'}\n"
            f"[bold]Trạng thái:[/]               [{status_color}]{result['status']}[/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Giấy Khai Sinh & Số Định Danh Cá Nhân[/]",
            border_style=status_color,
        )
    )


@civil_status_app.command("marriage")
def marriage_cmd(
    groom: str = typer.Argument(..., help="Họ và tên Chồng"),
    bride: str = typer.Argument(..., help="Họ và tên Vợ"),
    groom_dob: str = typer.Option("1998-05-15", "--groom-dob", help="Ngày sinh Chồng (YYYY-MM-DD)"),
    groom_pid: str = typer.Option("001098012345", "--groom-pid", help="Số định danh / CCCD của Chồng"),
    bride_dob: str = typer.Option("2000-08-20", "--bride-dob", help="Ngày sinh Vợ (YYYY-MM-DD)"),
    bride_pid: str = typer.Option("001100067890", "--bride-pid", help="Số định danh / CCCD của Vợ"),
    single_cert: bool = typer.Option(True, "--single-cert/--no-single-cert", help="Có Giấy xác nhận tình trạng hôn nhân hợp lệ"),
    consent: bool = typer.Option(True, "--consent/--no-consent", help="Tự nguyện kết hôn hoàn toàn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký kết hôn và cấp Giấy chứng nhận kết hôn theo Luật Hộ tịch & Luật Hôn nhân gia đình."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    result = engine.register_marriage(
        groom_name=groom,
        groom_dob=groom_dob,
        groom_pid=groom_pid,
        bride_name=bride,
        bride_dob=bride_dob,
        bride_pid=bride_pid,
        single_status_verified=single_cert,
        voluntary_consent=consent,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_approved"] else "red"
    console.print(
        Panel(
            f"[bold]Mã chứng nhận kết hôn:[/]   [cyan]{result['cert_id']}[/]\n"
            f"[bold]Chồng:[/]                     [bold]{result['groom_name']}[/] ({result['groom_age']} tuổi, ĐD: {result['groom_pid']})\n"
            f"[bold]Vợ:[/]                       [bold]{result['bride_name']}[/] ({result['bride_age']} tuổi, ĐD: {result['bride_pid']})\n"
            f"[bold]Đủ tuổi kết hôn:[/]          {'[green]Nam đủ 20, Nữ đủ 18[/]' if result['is_legal_age'] else '[red]Chưa đủ tuổi luật định[/]'}\n"
            f"[bold]Xác nhận tình trạng:[/]      {'[green]Độc thân hợp pháp[/]' if result['single_status_verified'] else '[red]Chưa có xác nhận độc thân[/]'}\n"
            f"[bold]Kết luận phê duyệt:[/]       [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Giấy Chứng Nhận Kết Hôn[/]",
            border_style=status_color,
        )
    )


@civil_status_app.command("death")
def death_cmd(
    deceased: str = typer.Argument(..., help="Họ và tên người chết"),
    pid: str = typer.Option("001050012345", "--pid", help="Số định danh cá nhân của người chết"),
    dod: str = typer.Option("2026-09-20", "--dod", "-d", help="Ngày chết (YYYY-MM-DD)"),
    cause: str = typer.Option("Bệnh lý tự nhiên", "--cause", "-c", help="Nguyên nhân chết"),
    place: str = typer.Option("Bệnh viện Bạch Mai, Hà Nội", "--place", help="Nơi chết"),
    notice: bool = typer.Option(True, "--notice/--no-notice", help="Có Giấy báo tử của cơ sở y tế"),
    reg_date: Optional[str] = typer.Option(None, "--reg-date", help="Ngày nộp hồ sơ khai tử"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký khai tử và khóa trạng thái công dân trên Cơ sở dữ liệu quốc gia về dân cư."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    result = engine.register_death(
        deceased_name=deceased,
        personal_id=pid,
        date_of_death=dod,
        cause_of_death=cause,
        place_of_death=place,
        death_notice_verified=notice,
        registration_date=reg_date,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_registered"] else "red"
    console.print(
        Panel(
            f"[bold]Mã trích lục khai tử:[/]     [cyan]{result['cert_id']}[/]\n"
            f"[bold]Người chết:[/]                [bold]{result['deceased_name']}[/]\n"
            f"[bold]Số định danh đã khóa:[/]      [bold yellow]{result['personal_id']}[/]\n"
            f"[bold]Ngày chết:[/]                 {result['date_of_death']}\n"
            f"[bold]Nguyên nhân:[/]               {result['cause_of_death']}\n"
            f"[bold]Nơi chết:[/]                  {result['place_of_death']}\n"
            f"[bold]Đăng ký đúng hạn (15 ngày):[/]{'[green]Đúng hạn[/]' if result['on_time'] else '[yellow]Quá hạn[/]'}\n"
            f"[bold]Trạng thái:[/]               [{status_color}]{result['status']}[/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Đăng Ký Khai Tử & Khóa Dữ Liệu Dân Cư[/]",
            border_style=status_color,
        )
    )


@civil_status_app.command("identity")
def identity_cmd(
    name: str = typer.Argument(..., help="Họ và tên công dân cấp thẻ Căn cước"),
    pid: str = typer.Option("001098055667", "--pid", help="Số định danh cá nhân 12 số"),
    dob: str = typer.Option("1998-10-12", "--dob", "-d", help="Ngày sinh (YYYY-MM-DD)"),
    gender: str = typer.Option("NAM", "--gender", "-g", help="Giới tính: NAM / NỮ"),
    nationality: str = typer.Option("VIỆT NAM", "--nationality", help="Quốc tịch"),
    iris: bool = typer.Option(True, "--iris/--no-iris", help="Thu nhận sinh trắc học mống mắt (Luật Căn cước 2023)"),
    fingerprint: bool = typer.Option(True, "--fingerprint/--no-fingerprint", help="Thu nhận vân tay 10 ngón"),
    face: bool = typer.Option(True, "--face/--no-face", help="Chụp ảnh khuôn mặt kỹ thuật số"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra và cấp Thẻ Căn cước gắn chip và tài khoản VNeID Mức 2 theo Luật Căn cước 2023."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    result = engine.issue_identity_card(
        full_name=name,
        date_of_birth=dob,
        personal_id=pid,
        gender=gender,
        nationality=nationality,
        has_iris_biometrics=iris,
        has_fingerprints=fingerprint,
        has_facial_photo=face,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    status_color = "green" if result["is_eligible"] else "red"
    console.print(
        Panel(
            f"[bold]Mã phát hành thẻ:[/]         [cyan]{result['card_id']}[/]\n"
            f"[bold]Số Căn cước (Định danh):[/]  [bold yellow]{result['personal_id']}[/]\n"
            f"[bold]Họ và tên:[/]                [bold]{result['full_name']}[/]\n"
            f"[bold]Độ tuổi:[/]                  {result['age']} tuổi (Sinh: {result['date_of_birth']})\n"
            f"[bold]Giới tính / Quốc tịch:[/]    {result['gender']} / {result['nationality']}\n"
            f"[bold]Sinh trắc học mống mắt:[/]   {'[green]Đã thu nhận mống mắt[/]' if result['has_iris_biometrics'] else '[red]Thiếu mống mắt[/]'}\n"
            f"[bold]Vân tay 10 ngón:[/]          {'[green]Đã thu nhận vân tay[/]' if result['has_fingerprints'] else '[red]Thiếu vân tay[/]'}\n"
            f"[bold]Ảnh chân dung số:[/]         {'[green]Đạt chuẩn ICAO[/]' if result['has_facial_photo'] else '[red]Thiếu ảnh[/]'}\n"
            f"[bold]Định danh VNeID Mức 2:[/]    {'[green]ĐÃ KÍCH HOẠT[/]' if result['vneid_level2_active'] else '[yellow]Chưa kích hoạt[/]'}\n"
            f"[bold]Hạn sử dụng thẻ:[/]          [bold cyan]{result['expiration_date']}[/]\n"
            f"[bold]Trạng thái phát hành:[/]     [{status_color}][bold]{result['status']}[/][/]\n"
            f"[bold]Căn cứ pháp lý:[/]          {result['statutory_notes']}",
            title=f"[{status_color}]Thẻ Căn Cước Chip & Định Danh Điện Tử VNeID[/]",
            border_style=status_color,
        )
    )


@civil_status_app.command("extract")
def extract_cmd(
    event_type: str = typer.Argument(..., help="Loại sự kiện hộ tịch: BIRTH, MARRIAGE, DEATH"),
    source_cert: str = typer.Argument(..., help="Mã giấy chứng nhận hộ tịch gốc"),
    applicant: str = typer.Option("Công dân yêu cầu", "--applicant", "-a", help="Họ tên người yêu cầu cấp trích lục"),
    purpose: str = typer.Option("Bổ sung hồ sơ công chức / thủ tục pháp lý", "--purpose", help="Mục đích sử dụng trích lục"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Cấp bản sao Trích lục hộ tịch từ Cơ sở dữ liệu hộ tịch điện tử theo Điều 63 Luật Hộ tịch."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    result = engine.issue_civil_extract(
        event_type=event_type,
        source_cert_id=source_cert,
        applicant_name=applicant,
        purpose=purpose,
    )

    if json_mode:
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold]Mã trích lục điện tử:[/]     [cyan]{result['extract_id']}[/]\n"
            f"[bold]Loại sự kiện hộ tịch:[/]     [bold]{result['event_type']}[/]\n"
            f"[bold]Hồ sơ chứng nhận gốc:[/]     {result['source_cert_id']}\n"
            f"[bold]Người yêu cầu cấp:[/]        [bold]{result['applicant_name']}[/]\n"
            f"[bold]Mục đích sử dụng:[/]         {result['purpose']}\n"
            f"[bold]Ngày cấp trích lục:[/]       {result['issued_date']}\n"
            f"[bold]Hiệu lực pháp lý:[/]         [green]{result['status']}[/]\n"
            f"[bold]Ghi chú pháp lý:[/]          {result['statutory_notes']}",
            title="[green]Bản Sao Trích Lục Hộ Tịch Điện Tử[/]",
            border_style="green",
        )
    )


@civil_status_app.command("list")
def list_cmd(
    category: str = typer.Option("ALL", "--category", "-c", help="Danh mục: ALL, BIRTH, MARRIAGE, DEATH, IDENTITY, EXTRACT"),
    limit: int = typer.Option(50, "--limit", "-l", help="Số lượng bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục giấy khai sinh, kết hôn, khai tử, thẻ căn cước và trích lục hộ tịch."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    records = engine.list_civil_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    if "births" in records and records["births"]:
        table = Table(title="Danh Sách Đăng Ký Khai Sinh")
        table.add_column("Mã Khai Sinh", style="cyan")
        table.add_column("Số Định Danh (12 số)", style="bold yellow")
        table.add_column("Họ và Tên", style="bold")
        table.add_column("Giới Tính")
        table.add_column("Ngày Sinh")
        table.add_column("Đúng Hạn (60 ngày)")
        for row in records["births"]:
            table.add_row(
                row["cert_id"],
                row["personal_id"],
                row["child_name"],
                row["gender"],
                row["date_of_birth"],
                "Đúng hạn" if row["registered_on_time"] else "Quá hạn",
            )
        console.print(table)

    if "marriages" in records and records["marriages"]:
        table = Table(title="Danh Sách Đăng Ký Kết Hôn")
        table.add_column("Mã Kết Hôn", style="cyan")
        table.add_column("Chồng", style="bold")
        table.add_column("Vợ", style="bold")
        table.add_column("Đủ Tuổi Luật Định")
        table.add_column("Trạng Thái")
        for row in records["marriages"]:
            table.add_row(
                row["cert_id"],
                row["groom_name"],
                row["bride_name"],
                "Hợp chuẩn" if row["is_legal_age"] else "Chưa đủ tuổi",
                row["status"],
            )
        console.print(table)


@civil_status_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry dân số, hộ tịch và căn cước công dân quốc gia."""
    from src.core.civil_status_engine import CivilStatusEngine

    engine = CivilStatusEngine()
    telemetry = engine.get_civil_status_telemetry()

    if json_mode:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Vietnam Civil Registration & Identification Telemetry")
    table.add_column("Chỉ Số Dân Cư & Hộ Tịch", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")

    table.add_row("Tổng số đăng ký khai sinh", str(telemetry["total_birth_registrations"]))
    table.add_row("Khai sinh đúng hạn (trong 60 ngày)", str(telemetry["on_time_birth_registrations"]))
    table.add_row("Tổng số đăng ký kết hôn", str(telemetry["total_marriage_registrations"]))
    table.add_row("Đăng ký kết hôn hợp chuẩn phê duyệt", str(telemetry["approved_marriages"]))
    table.add_row("Tổng số đăng ký khai tử", str(telemetry["total_death_registrations"]))
    table.add_row("Tăng tự nhiên dân số", f"+{telemetry['population_natural_growth']}")
    table.add_row("Tổng Thẻ Căn cước đã cấp", str(telemetry["total_identity_cards_issued"]))
    table.add_row("Tài khoản VNeID Mức 2 kích hoạt", str(telemetry["active_vneid_level2_users"]))
    table.add_row("Tổng bản sao trích lục hộ tịch cấp", str(telemetry["total_civil_extracts_issued"]))

    console.print(table)
