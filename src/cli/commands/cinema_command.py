# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Cinema, Film Production, Age Classification & Censorship Suite (Phase 85)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

cinema_app = typer.Typer(
    name="cinema",
    help="Vietnamese Cinema, Film Production, Age Classification & Censorship Suite.",
)
console = Console()


@cinema_app.callback(invoke_without_command=True)
def cinema_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động điện ảnh, phân loại độ tuổi phim, cấp phép phổ biến và tỷ lệ suất chiếu tại rạp."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG QUẢN LÝ ĐIỆN ẢNH & THẨM ĐỊNH PHÂN LOẠI PHIM QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['statutory_law']}[/]\n"
            f"  Phim đã phân loại:         [bold cyan]{status_data['total_films_classified']}[/] tác phẩm ([bold red]{status_data['banned_films_count']}[/] phim bị cấm phổ biến - Mức C)\n"
            f"  Giấy phép phổ biến GPHPP:  [bold green]{status_data['total_distribution_permits_gphpp']}[/] giấy phép đã được Cục Điện ảnh cấp\n"
            f"  Kiểm toán hạn ngạch rạp:   [bold cyan]{status_data['total_cinema_quota_audits']}[/] cụm rạp ([bold green]{status_data['quota_compliance_rate_pct']}%[/] đạt chuẩn >= 10% phim Việt)\n"
            f"  Phim OTT / Không gian mạng:[bold cyan]{status_data['total_ott_films_audited']}[/] phim được hậu kiểm ([bold red]{status_data['ott_violations_count']}[/] vi phạm cảnh báo/chủ quyền)\n"
            f"  Yêu cầu gỡ bỏ OTT 24h:     [bold yellow]{status_data['total_ott_takedowns']}[/] vụ việc xử lý gỡ bỏ theo Điều 19 Luật Điện ảnh 2022",
            title="[bold green]Vietnam Cinema & Film Censorship Telemetry[/]",
            border_style="green",
        )
    )


@cinema_app.command("classify")
def classify_film_cmd(
    title: str = typer.Argument(..., help="Tên tác phẩm điện ảnh"),
    violence: int = typer.Option(0, "--violence", "-v", help="Mức độ bạo lực (0-5)"),
    nudity: int = typer.Option(0, "--nudity", "-n", help="Mức độ tình dục / khỏa thân (0-5)"),
    horror: int = typer.Option(0, "--horror", "-h", help="Mức độ kinh dị / rùng rợn (0-5)"),
    profanity: int = typer.Option(0, "--profanity", "-p", help="Mức độ ngôn từ thô tục (0-5)"),
    drugs: int = typer.Option(0, "--drugs", "-d", help="Mức độ chất kích thích / ma túy (0-5)"),
    danger: int = typer.Option(0, "--danger", help="Mức độ hành vi nguy hiểm dễ bắt chước (0-5)"),
    sovereign_violation: bool = typer.Option(False, "--sovereign-violation/--no-sovereign-violation", help="Có nội dung vi phạm chủ quyền lãnh thổ (đường lưỡi bò, xuyên tạc lịch sử)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định và xác định mức phân loại độ tuổi phim theo Thông tư số 05/2023/TT-BVHTTDL (P, K, T13, T16, T18, C)."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    res = engine.classify_film(
        title=title,
        violence_level=violence,
        nudity_level=nudity,
        horror_level=horror,
        profanity_level=profanity,
        drug_substance=drugs,
        dangerous_acts=danger,
        sovereign_violation=sovereign_violation,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ban = res["is_prohibited"]
    color = "red" if is_ban else ("yellow" if res["rating"] in ["T18", "T16"] else "green")

    table = Table(title=f"Kết quả phân loại độ tuổi tác phẩm: {res['title']}", border_style=color)
    table.add_column("Chỉ tiêu", style="bold cyan")
    table.add_column("Chi tiết", style="white")

    table.add_row("Mã hồ sơ", res["classification_id"])
    table.add_row("Tên phim", res["title"])
    table.add_row("Mức phân loại", f"[bold {color}]{res['rating']}[/]")
    table.add_row("Ý nghĩa phân loại", res["rating_description"])
    table.add_row("Cảnh báo nội dung", "\n".join(res["warning_tags"]) if res["warning_tags"] else "[green]Không có cảnh báo đặc biệt[/]")
    table.add_row("Yêu cầu hiển thị", res["display_requirement"])
    table.add_row("Căn cứ pháp lý", res["legal_basis"])

    console.print(table)


@cinema_app.command("permit")
def issue_permit_cmd(
    title: str = typer.Argument(..., help="Tên tác phẩm điện ảnh"),
    producer: str = typer.Option("Hãng phim Mekong Pictures", "--producer", "-p", help="Tên nhà sản xuất"),
    rating: str = typer.Option("T16", "--rating", "-r", help="Mức phân loại độ tuổi (P, K, T13, T16, T18)"),
    duration: int = typer.Option(115, "--duration", "-d", help="Thời lượng phim (phút)"),
    country: str = typer.Option("Việt Nam", "--country", "-c", help="Quốc gia sản xuất"),
    director: str = typer.Option("Nguyễn Văn Đạo", "--director", help="Tên đạo diễn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Cấp Giấy phép phổ biến phim (GPHPP) cho phim chiếu rạp hoặc truyền hình."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    try:
        res = engine.issue_distribution_permit(
            film_title=title,
            producer_name=producer,
            rating=rating,
            duration_min=duration,
            country_of_origin=country,
            director=director,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi cấp giấy phép:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]GIẤY PHÉP PHỔ BIẾN PHIM (GPHPP)[/]\n\n"
            f"  Số giấy phép:        [bold cyan]{res['permit_code']}[/]\n"
            f"  Tên tác phẩm:        [bold]{res['film_title']}[/]\n"
            f"  Nhà sản xuất:        [white]{res['producer_name']}[/]\n"
            f"  Đạo diễn & Quốc gia: [white]{res['director']}[/] ({res['country_of_origin']})\n"
            f"  Thời lượng:          [white]{res['duration_min']} phút[/]\n"
            f"  Mức phân loại:       [bold yellow]{res['rating']}[/]\n"
            f"  Cơ quan cấp phép:    [bold]{res['issuing_authority']}[/]\n"
            f"  Ngày cấp:            [green]{res['issue_date']}[/] | Trạng thái: [bold green]{res['status']}[/]",
            title="[bold green]Film Distribution Permit Issued[/]",
            border_style="green",
        )
    )


@cinema_app.command("quota")
def audit_quota_cmd(
    cinema_name: str = typer.Argument(..., help="Tên cụm rạp chiếu phim"),
    total: int = typer.Option(500, "--total", "-t", help="Tổng số suất chiếu trong kỳ kiểm toán"),
    vn_screenings: int = typer.Option(65, "--vn", "-v", help="Số suất chiếu phim Việt Nam"),
    prime_total: int = typer.Option(150, "--prime-total", help="Tổng số suất chiếu trong khung giờ vàng 18h-22h"),
    prime_vn: int = typer.Option(25, "--prime-vn", help="Số suất chiếu phim Việt trong khung giờ vàng"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm toán hạn ngạch tỷ lệ suất chiếu phim Việt Nam tại cụm rạp theo Điều 9 Nghị định 131/2022/NĐ-CP (>= 10%)."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    try:
        res = engine.audit_cinema_screen_quota(
            cinema_name=cinema_name,
            total_screenings=total,
            vn_screenings=vn_screenings,
            prime_time_total=prime_total,
            prime_time_vn=prime_vn,
        )
    except ValueError as exc:
        console.print(f"[bold red]Lỗi kiểm toán:[/] {exc}")
        raise typer.Exit(code=1)

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_comp = res["status"] == "COMPLIANT"
    color = "green" if is_comp else "red"

    console.print(
        Panel(
            f"[bold {color}]KIỂM TOÁN HẠN NGẠCH SUẤT CHIẾU PHIM VIỆT NAM TẠI RẠP[/]\n\n"
            f"  Mã kiểm toán:        [bold cyan]{res['audit_id']}[/]\n"
            f"  Cụm rạp:             [bold]{res['cinema_name']}[/]\n"
            f"  Tổng suất chiếu:     [white]{res['total_screenings']} suất[/]\n"
            f"  Suất chiếu phim VN:  [bold]{res['vn_screenings']} suất[/] (Tỷ lệ: [bold]{res['vn_ratio_pct']}%[/] / Hạn ngạch: [cyan]{res['min_required_ratio_pct']}%[/])\n"
            f"  Giờ vàng 18h-22h:    [white]{res['prime_time_vn']}/{res['prime_time_total']} suất[/]\n"
            f"  Thiếu hụt suất chiếu:[bold red]{res['shortfall_screenings']} suất[/]\n"
            f"  Kết luận kiểm toán:  [bold {color}]{res['status']}[/]\n"
            + (f"  Vi phạm:             [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Tuân thủ:            [bold green]Đáp ứng đầy đủ Điều 9 Nghị định 131/2022/NĐ-CP[/]"),
            title=f"[bold {color}]Cinema Screen Quota Audit Result[/]",
            border_style=color,
        )
    )


@cinema_app.command("ott")
def verify_ott_cmd(
    platform: str = typer.Argument("Netflix", help="Nền tảng OTT VOD (Netflix, VieON, FPT Play, Galaxy Play)"),
    film_id: str = typer.Option("OTT-MOV-8801", "--film-id", help="Mã định danh phim trên nền tảng"),
    title: str = typer.Option("Hành Trình Mekong", "--title", "-t", help="Tên phim"),
    rating: str = typer.Option("T18", "--rating", "-r", help="Mức phân loại độ tuổi tự công bố"),
    warning: bool = typer.Option(True, "--warning/--no-warning", help="Có hiển thị thông điệp cảnh báo nội dung nhạy cảm"),
    sovereign: bool = typer.Option(True, "--sovereign/--no-sovereign", help="Đảm bảo toàn vẹn chủ quyền lãnh thổ (không có đường lưỡi bò phi pháp)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Hậu kiểm tuân thủ phổ biến phim trên không gian mạng OTT VOD theo Điều 19 Luật Điện ảnh 2022."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    res = engine.verify_ott_film_compliance(
        platform=platform,
        film_id=film_id,
        film_title=title,
        rating=rating,
        has_warning_banner=warning,
        sovereign_clean=sovereign,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_comp = res["status"] == "COMPLIANT"
    color = "green" if is_comp else "red"

    console.print(
        Panel(
            f"[bold {color}]HẬU KIỂM PHỔ BIẾN PHIM TRÊN KHÔNG GIAN MẠNG (OTT VOD)[/]\n\n"
            f"  Mã hồ sơ:            [bold cyan]{res['record_id']}[/]\n"
            f"  Nền tảng trực tuyến: [bold yellow]{res['platform']}[/] (Mã phim: [white]{res['film_id']}[/])\n"
            f"  Tên tác phẩm:        [bold]{res['film_title']}[/] (Phân loại: [cyan]{res['rating']}[/])\n"
            f"  Hiển thị cảnh báo:   [bold]{'Đạt chuẩn' if res['has_warning_banner'] else 'KHÔNG HIỂN THỊ'}[/]\n"
            f"  Chủ quyền lãnh thổ:  [bold]{'Toàn vẹn' if res['sovereign_clean'] else 'VI PHẠM ĐIỀU 9'}[/]\n"
            f"  Kết luận hậu kiểm:   [bold {color}]{res['status']}[/]\n"
            f"  Chế tài rủi ro:      [bold red]{res['sanction_risk']}[/]",
            title="[bold green]OTT Streaming Content & Warning Compliance[/]",
            border_style=color,
        )
    )


@cinema_app.command("takedown")
def track_takedown_cmd(
    platform: str = typer.Argument("Netflix", help="Nền tảng OTT"),
    film_id: str = typer.Option("OTT-MOV-8801", "--film-id", help="Mã phim vi phạm"),
    reason: str = typer.Option("Hình ảnh đường lưỡi bò phi pháp vi phạm chủ quyền", "--reason", "-r", help="Lý do yêu cầu gỡ bỏ"),
    notice_time: str = typer.Option(None, "--notice-time", help="Thời điểm yêu cầu gỡ bỏ (ISO string)"),
    resolved_time: str = typer.Option(None, "--resolved-time", help="Thời điểm hoàn thành gỡ bỏ (ISO string)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Giám sát xử lý gỡ bỏ phim vi phạm trên không gian mạng trong 24 giờ theo Điều 19 Luật Điện ảnh 2022."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    res = engine.track_ott_takedown(
        platform=platform,
        film_id=film_id,
        reason=reason,
        notice_timestamp=notice_time,
        resolved_timestamp=resolved_time,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = "OVERDUE" not in res["status"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]GIÁM SÁT GỠ BỎ PHIM VI PHẠM TRÊN KHÔNG GIAN MẠNG (24H SLA)[/]\n\n"
            f"  Mã vụ việc:          [bold cyan]{res['takedown_id']}[/]\n"
            f"  Nền tảng trực tuyến: [bold yellow]{res['platform']}[/] (Mã phim: [white]{res['film_id']}[/])\n"
            f"  Lý do gỡ bỏ:         [bold red]{res['reason']}[/]\n"
            f"  Thời gian thông báo: [cyan]{res['notice_timestamp']}[/]\n"
            f"  Thời gian giải quyết:[white]{res['resolved_timestamp'] or 'Đang xử lý'}[/] (Đã trôi qua: [bold]{res['hours_elapsed']} giờ[/] / Hạn định: 24.0 giờ)\n"
            f"  Trạng thái:          [bold {color}]{res['status']}[/]",
            title="[bold green]Article 19 Cinema Law 24h Takedown Enforcement[/]",
            border_style=color,
        )
    )


@cinema_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("classifications", help="Danh mục: classifications, permits, quotas, ott, takedowns"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục tác phẩm đã phân loại, giấy phép phát hành, kiểm toán hạn ngạch rạp hoặc phim OTT."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục hồ sơ điện ảnh [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["permits", "gphpp"]:
        table.add_column("Số GPHPP", style="bold cyan")
        table.add_column("Tên tác phẩm", style="white")
        table.add_column("Nhà sản xuất", style="yellow")
        table.add_column("Phân loại", style="bold green")
        table.add_column("Thời lượng", style="white")
        table.add_column("Ngày cấp", style="green")
        for r in records:
            table.add_row(r.get("permit_code", ""), r.get("film_title", ""), r.get("producer_name", ""), r.get("rating", ""), f"{r.get('duration_min', 0)}p", r.get("issue_date", ""))
    elif category in ["quotas", "screens", "cinemas"]:
        table.add_column("Mã kiểm toán", style="bold cyan")
        table.add_column("Cụm rạp", style="white")
        table.add_column("Suất chiếu VN/Tổng", style="yellow")
        table.add_column("Tỷ lệ %", style="white")
        table.add_column("Thiếu hụt", style="red")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "COMPLIANT" else "red"
            table.add_row(r.get("audit_id", ""), r.get("cinema_name", ""), f"{r.get('vn_screenings', 0)}/{r.get('total_screenings', 0)}", f"{r.get('vn_ratio_pct', 0)}%", f"{r.get('shortfall_screenings', 0)}", f"[{color}]{r.get('status', '')}[/]")
    elif category in ["ott", "streaming"]:
        table.add_column("Mã hồ sơ", style="bold cyan")
        table.add_column("Nền tảng", style="yellow")
        table.add_column("Tên phim", style="white")
        table.add_column("Phân loại", style="bold")
        table.add_column("Cảnh báo", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("status") == "COMPLIANT" else "red"
            table.add_row(r.get("record_id", ""), r.get("platform", ""), r.get("film_title", ""), r.get("rating", ""), "Có" if r.get("has_warning_banner") else "Không", f"[{color}]{r.get('status', '')}[/]")
    else:
        table.add_column("Mã phân loại", style="bold cyan")
        table.add_column("Tên tác phẩm", style="white")
        table.add_column("Mức độ", style="bold")
        table.add_column("Mô tả", style="white")
        table.add_column("Cấm chiếu", style="red")
        for r in records:
            rate = r.get("rating", "")
            color = "red" if rate == "C" else ("yellow" if rate in ["T18", "T16"] else "green")
            table.add_row(r.get("classification_id", ""), r.get("title", ""), f"[{color}]{rate}[/]", r.get("rating_description", "")[:40] + "...", "Có" if r.get("is_prohibited") else "Không")

    console.print(table)


@cinema_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp ngành điện ảnh, phân loại phim và hạn ngạch rạp."""
    from src.core.cinema_engine import CinemaEngine

    engine = CinemaEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
