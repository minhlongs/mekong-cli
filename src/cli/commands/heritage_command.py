# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Cultural Heritage, Antiquities & Relics Suite (Phase 104)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

heritage_app = typer.Typer(
    name="heritage",
    help="Vietnamese Cultural Heritage, Antiquities & National Treasures Suite.",
)
console = Console()


@heritage_app.callback(invoke_without_command=True)
def heritage_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động bảo tồn di sản văn hóa, xếp hạng di tích, đăng ký cổ vật và bảo vật quốc gia."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    telemetry = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(asdict(telemetry), indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold blue]HỆ THỐNG QUẢN TRỊ BẢO TỒN DI SẢN VĂN HÓA & BẢO VẬT QUỐC GIA[/]\n\n"
            f"  Khung pháp lý:             [bold]Luật Di sản văn hóa 2024 (Luật 45/2024/QH15)[/]\n"
            f"  Cơ quan quản lý chuyên môn: [bold yellow]Cục Di sản Văn hóa (Bộ Văn hóa, Thể thao và Du lịch)[/]\n\n"
            f"  Tổng di tích xếp hạng:     [bold]{telemetry.total_relic_sites}[/] di tích ([bold green]{telemetry.special_national_sites}[/] Di tích Quốc gia Đặc biệt)\n"
            f"  Bảo vật Quốc gia:          [bold yellow]{telemetry.national_treasures_count}[/] hiện vật gốc độc bản (Thủ tướng phê duyệt)\n"
            f"  Cổ vật đã đăng ký:         [bold green]{telemetry.registered_antiquities}[/] cổ vật hợp chuẩn niên đại >= 100 năm\n"
            f"  Giấy phép khai quật:       [bold]{telemetry.active_excavation_permits}[/] dự án khảo cổ học hợp lệ có bàn giao bảo tàng\n"
            f"  Triển lãm & Trưng bày:     [bold green]{telemetry.approved_exhibitions}[/] đợt trưng bày bảo tàng / tour quốc tế đạt chuẩn vi khí hậu",
            title="[bold blue]Vietnam National Cultural Heritage Telemetry[/]",
            border_style="blue",
        )
    )


@heritage_app.command("relic")
def relic_cmd(
    name: str = typer.Argument(..., help="Tên di tích lịch sử - văn hóa hoặc danh lam thắng cảnh"),
    classification: str = typer.Option("NATIONAL", "--class", "-c", help="Cấp xếp hạng: SPECIAL_NATIONAL, NATIONAL, PROVINCIAL"),
    province: str = typer.Option("Hà Nội", "--province", "-p", help="Tỉnh/Thành phố trực thuộc"),
    zone1: float = typer.Option(5000.0, "--zone1", help="Diện tích Khu vực bảo vệ I (m2, bảo vệ nguyên trạng)"),
    zone2: float = typer.Option(15000.0, "--zone2", help="Diện tích Khu vực bảo vệ II (m2, vùng đệm)"),
    construction_z1: bool = typer.Option(False, "--construction-z1/--no-construction-z1", help="Có xây dựng công trình mới trong Khu vực bảo vệ I (nghiêm cấm)"),
    minister_approved: bool = typer.Option(True, "--minister-approved/--no-minister-approved", help="Có ý kiến chấp thuận bằng văn bản của Bộ trưởng Bộ VHTTDL cho vùng đệm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm tra khu vực bảo vệ di tích và tuân thủ xây dựng theo Điều 27-32 Luật Di sản văn hóa 2024."""
    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    res = engine.assess_relic_site(
        name=name,
        classification=classification,
        province=province,
        zone1_area_sqm=zone1,
        zone2_area_sqm=zone2,
        construction_in_zone1=construction_z1,
        minister_approved=minister_approved,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.status == "PROTECTED_COMPLIANT" else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Đạt đầy đủ tiêu chuẩn bảo vệ nguyên trạng di tích."

    console.print(
        Panel(
            f"[bold cyan]KẾT QUẢ THẨM ĐỊNH KHU VỰC BẢO VỆ DI TÍCH[/]\n\n"
            f"  Mã di tích:            [bold]{res.site_id}[/]\n"
            f"  Tên di tích:           [bold]{res.name}[/]\n"
            f"  Cấp xếp hạng:          [bold cyan]{res.classification}[/]\n"
            f"  Địa bàn:               {res.province}\n"
            f"  Khu vực bảo vệ I:      [bold]{res.zone1_area_sqm} m2[/] (Bảo vệ nguyên trạng)\n"
            f"  Khu vực bảo vệ II:     [bold]{res.zone2_area_sqm} m2[/] (Vùng đệm cảnh quan)\n"
            f"  Xây dựng tại Khu I:    [{'red' if res.construction_in_zone1 else 'green'}]{'VI PHẠM (CÓ XÂY DỰNG)' if res.construction_in_zone1 else 'KHÔNG CÓ (NGUYÊN TRẠNG)'}[/]\n"
            f"  Chấp thuận của Bộ:     [{'green' if res.minister_approved else 'red'}]{'ĐÃ CÓ VĂN BẢN' if res.minister_approved else 'CHƯA CÓ CHẤP THUẬN'}[/]\n"
            f"  Kết luận thẩm định:    [bold {status_color}]{res.status}[/bold {status_color}]\n\n"
            f"  Chi tiết pháp lý:\n{reasons_str}",
            title="[bold blue]Heritage Relic Site Assessment (Articles 27-32)[/]",
            border_style="cyan",
        )
    )


@heritage_app.command("artifact")
def artifact_cmd(
    name: str = typer.Argument(..., help="Tên hiện vật, cổ vật hoặc bảo vật"),
    category: str = typer.Option("ANTIQUITY", "--cat", "-c", help="Phân loại: NATIONAL_TREASURE, ANTIQUITY, RELIC_OBJECT"),
    period: str = typer.Option("Đông Sơn", "--period", help="Niên đại, thời kỳ lịch sử"),
    material: str = typer.Option("Đồng thau", "--material", "-m", help="Chất liệu chế tác"),
    owner: str = typer.Option("STATE", "--owner", "-o", help="Hình thức sở hữu: STATE, COMMUNITY, PRIVATE"),
    unique: bool = typer.Option(True, "--unique/--common", help="Hiện vật gốc độc bản (bắt buộc cho Bảo vật quốc gia)"),
    age: int = typer.Option(150, "--age", help="Tuổi hiện vật (năm, cổ vật >= 100 năm)"),
    value: bool = typer.Option(True, "--value/--no-value", help="Có giá trị lịch sử, văn hóa, khoa học tiêu biểu đặc biệt"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Đăng ký di vật, cổ vật và thẩm định tiêu chuẩn Bảo vật Quốc gia (Điều 39-44 Luật Di sản văn hóa 2024)."""
    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    res = engine.register_artifact(
        name=name,
        category=category,
        origin_period=period,
        material=material,
        owner_type=owner,
        is_unique=unique,
        age_years=age,
        historical_scientific_value=value,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.status == "REGISTERED_COMPLIANT" else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Hồ sơ hợp chuẩn đăng ký di sản văn hóa quốc gia."

    console.print(
        Panel(
            f"[bold cyan]HỒ SƠ ĐĂNG KÝ CỔ VẬT & BẢO VẬT QUỐC GIA[/]\n\n"
            f"  Mã hiện vật:           [bold]{res.artifact_id}[/]\n"
            f"  Tên hiện vật:          [bold]{res.name}[/]\n"
            f"  Phân loại di vật:      [bold cyan]{res.category}[/]\n"
            f"  Thời kỳ lịch sử:       {res.origin_period} | Chất liệu: [bold]{res.material}[/]\n"
            f"  Hình thức sở hữu:      {res.owner_type}\n"
            f"  Hiện vật gốc độc bản:  [{'green' if res.is_unique else 'yellow'}]{'ĐỘC BẢN' if res.is_unique else 'KHÔNG ĐỘC BẢN'}[/]\n"
            f"  Cấm chuyển nhượng XK:  [{'red' if res.export_prohibited else 'green'}]{'CẤM XUẤT KHẨU THƯƠNG MẠI' if res.export_prohibited else 'ĐƯỢC PHÉP'}[/]\n"
            f"  Công nhận Bảo vật QG:  [{'bold yellow' if res.recognized_as_treasure else 'white'}]{'ĐỦ TIÊU CHUẨN BẢO VẬT QUỐC GIA' if res.recognized_as_treasure else 'CỔ VẬT THƯỜNG'}[/]\n"
            f"  Giấy chứng nhận số:    [bold green]{res.registration_cert_no}[/]\n"
            f"  Trạng thái hồ sơ:      [bold {status_color}]{res.status}[/bold {status_color}]\n\n"
            f"  Đánh giá chuyên môn:\n{reasons_str}",
            title="[bold blue]Artifact & National Treasure Registration[/]",
            border_style="cyan",
        )
    )


@heritage_app.command("excavate")
def excavate_cmd(
    project: str = typer.Argument(..., help="Tên đề án thăm dò, khai quật khảo cổ"),
    location: str = typer.Argument(..., help="Địa điểm khai quật khảo cổ"),
    lead: str = typer.Argument(..., help="Chủ trì khai quật khảo cổ"),
    major: str = typer.Option("Khảo cổ học", "--major", "-m", help="Chuyên ngành cử nhân/thạc sĩ của chủ trì"),
    exp: int = typer.Option(4, "--exp", "-e", help="Số năm kinh nghiệm tham gia khai quật khảo cổ (>= 3 năm)"),
    days: int = typer.Option(60, "--days", "-d", help="Thời hạn cấp phép khai quật (ngày)"),
    handover: bool = typer.Option(True, "--handover/--no-handover", help="Cam kết bàn giao toàn bộ hiện vật thu được vào bảo tàng công lập"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Thẩm định cấp phép thăm dò, khai quật khảo cổ học theo Điều 35-38 Luật Di sản văn hóa 2024."""
    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    res = engine.permit_excavation(
        project_name=project,
        location=location,
        lead_archaeologist=lead,
        degree_major=major,
        experience_years=exp,
        permit_days=days,
        artifacts_handed_over=handover,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if res.is_approved else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Đủ điều kiện cấp Giấy phép khai quật khảo cổ học."

    console.print(
        Panel(
            f"[bold cyan]THẨM ĐỊNH CẤP PHÉP KHAI QUẬT KHẢO CỔ HỌC[/]\n\n"
            f"  Số giấy phép:          [bold]{res.permit_id}[/]\n"
            f"  Dự án khảo cổ:         [bold]{res.project_name}[/]\n"
            f"  Địa bàn khai quật:     {res.location}\n"
            f"  Chuyên gia chủ trì:    [bold]{res.lead_archaeologist}[/]\n"
            f"  Chuyên ngành đào tạo:  {res.degree_major} | Kinh nghiệm: [bold]{res.experience_years} năm[/] (chuẩn: >= 3 năm)\n"
            f"  Thời hạn khai quật:    [bold]{res.permit_days} ngày[/]\n"
            f"  Bàn giao bảo tàng:     [{'green' if res.artifacts_handed_over_to_museum else 'red'}]{'CAM KẾT ĐẦY ĐỦ' if res.artifacts_handed_over_to_museum else 'KHÔNG CAM KẾT'}[/]\n"
            f"  Kết quả thẩm duyệt:    [bold {status_color}]{res.status}[/bold {status_color}]\n\n"
            f"  Chi tiết điều kiện:\n{reasons_str}",
            title="[bold blue]Archaeological Excavation Licensing (Articles 35-38)[/]",
            border_style="cyan",
        )
    )


@heritage_app.command("exhibit")
def exhibit_cmd(
    museum: str = typer.Argument(..., help="Tên bảo tàng tổ chức trưng bày"),
    art_id: str = typer.Argument(..., help="Mã định danh hiện vật"),
    art_name: str = typer.Argument(..., help="Tên hiện vật"),
    treasure: bool = typer.Option(False, "--treasure/--not-treasure", help="Hiện vật là Bảo vật Quốc gia"),
    overseas: bool = typer.Option(False, "--overseas", help="Tour trưng bày triển lãm ở nước ngoài"),
    insurance: bool = typer.Option(True, "--insurance/--no-insurance", help="Đã mua bảo hiểm toàn diện 100% giá trị hiện vật"),
    pm_approval: bool = typer.Option(True, "--pm-approval/--no-pm-approval", help="Có Quyết định phê duyệt của Thủ tướng Chính phủ đối với Bảo vật quốc gia"),
    temp: float = typer.Option(22.0, "--temp", "-t", help="Nhiệt độ phòng trưng bày (chuẩn: 18.0 - 24.0 °C)"),
    humidity: float = typer.Option(55.0, "--humidity", help="Độ ẩm phòng trưng bày (chuẩn: 45.0 - 65.0 %)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Kiểm tra điều kiện trưng bày bảo tàng và xuất khẩu tạm thời triển lãm nước ngoài (Điều 47-53)."""
    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    res = engine.audit_exhibition(
        museum_name=museum,
        artifact_id=art_id,
        artifact_name=art_name,
        is_national_treasure=treasure,
        is_overseas_tour=overseas,
        insurance_covered_100pct=insurance,
        prime_minister_approval=pm_approval,
        temp_celsius=temp,
        humidity_pct=humidity,
    )

    if json_mode:
        typer.echo(json.dumps(asdict(res), indent=2, ensure_ascii=False))
        return

    status_color = "green" if "APPROVED" in res.status else "red"
    reasons_str = "\n".join(f"    - {r}" for r in res.reasons) if res.reasons else "    Đạt đầy đủ quy chuẩn an toàn trưng bày và bảo quản."

    console.print(
        Panel(
            f"[bold cyan]KIỂM ĐỊNH ĐIỀU KIỆN TRƯNG BÀY & TRIỂN LÃM HIỆN VẬT[/]\n\n"
            f"  Mã kiểm định:          [bold]{res.exhibition_id}[/]\n"
            f"  Bảo tàng tổ chức:      [bold]{res.museum_name}[/]\n"
            f"  Hiện vật trưng bày:    {res.artifact_id} - [bold]{res.artifact_name}[/]\n"
            f"  Bảo vật Quốc gia:      [{'yellow' if res.is_national_treasure else 'white'}]{'BẢO VẬT QUỐC GIA' if res.is_national_treasure else 'CỔ VẬT THƯỜNG'}[/]\n"
            f"  Triển lãm nước ngoài:  {'CÓ' if res.is_overseas_tour else 'TRONG NƯỚC'}\n"
            f"  Bảo hiểm toàn diện:    [{'green' if res.insurance_covered_100pct else 'red'}]{'100% GIÁ TRỊ' if res.insurance_covered_100pct else 'THIẾU BẢO HIỂM'}[/]\n"
            f"  Phê duyệt Thủ tướng:   [{'green' if res.prime_minister_approval else 'red'}]{'ĐÃ CÓ QUYẾT ĐỊNH' if res.prime_minister_approval else 'CHƯA CÓ'}[/]\n"
            f"  Vi khí hậu bảo quản:   [bold]{res.temp_celsius}°C[/] (18-24°C) | [bold]{res.humidity_pct}%[/] (45-65%)\n"
            f"  Trạng thái phê duyệt:  [bold {status_color}]{res.status}[/bold {status_color}]\n\n"
            f"  Chi tiết thẩm định:\n{reasons_str}",
            title="[bold blue]Museum Exhibition & Overseas Tour Audit[/]",
            border_style="cyan",
        )
    )


@heritage_app.command("list")
def list_cmd(
    category: str = typer.Option("all", "--category", "-c", help="Danh mục: all, sites, artifacts, excavations, exhibitions"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số lượng kết quả tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Tra cứu danh mục di tích xếp hạng, cổ vật đăng ký, giấy phép khảo cổ và đợt trưng bày bảo tàng."""
    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    data = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return

    if "relic_sites" in data and data["relic_sites"]:
        table = Table(title="Danh Sách Di Tích Lịch Sử - Văn Hóa & Danh Lam Thắng Cảnh", border_style="blue")
        table.add_column("Mã di tích", style="cyan")
        table.add_column("Tên di tích", style="white")
        table.add_column("Cấp xếp hạng", style="yellow")
        table.add_column("Tỉnh/Thành", style="green")
        table.add_column("Trạng thái", style="magenta")

        for r in data["relic_sites"]:
            table.add_row(
                r["site_id"],
                r["name"],
                r["classification"],
                r["province"],
                r["status"],
            )
        console.print(table)

    if "artifacts" in data and data["artifacts"]:
        table = Table(title="Danh Sách Cổ Vật & Bảo Vật Quốc Gia Đăng Ký", border_style="magenta")
        table.add_column("Mã hiện vật", style="cyan")
        table.add_column("Tên hiện vật", style="white")
        table.add_column("Phân loại", style="yellow")
        table.add_column("Niên đại", style="green")
        table.add_column("Chất liệu", style="white")
        table.add_column("Số chứng nhận", style="blue")
        table.add_column("Trạng thái", style="green")

        for r in data["artifacts"]:
            table.add_row(
                r["artifact_id"],
                r["name"],
                r["category"],
                r["origin_period"],
                r["material"],
                r["registration_cert_no"],
                r["status"],
            )
        console.print(table)


@heritage_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Hiển thị tổng quan các chỉ số telemetry bảo tồn di sản văn hóa quốc gia."""
    from src.core.heritage_engine import HeritageEngine

    engine = HeritageEngine()
    telemetry = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(asdict(telemetry), indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ Số Telemetry Bảo Tồn Di Sản Văn Hóa Quốc Gia", border_style="blue")
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="bold green")

    table.add_row("Tổng số di tích xếp hạng", str(telemetry.total_relic_sites))
    table.add_row("Di tích Quốc gia Đặc biệt", str(telemetry.special_national_sites))
    table.add_row("Bảo vật Quốc gia công nhận", str(telemetry.national_treasures_count))
    table.add_row("Cổ vật hợp chuẩn đăng ký", str(telemetry.registered_antiquities))
    table.add_row("Dự án khảo cổ học được cấp phép", str(telemetry.active_excavation_permits))
    table.add_row("Trưng bày & Triển lãm đạt chuẩn vi khí hậu", str(telemetry.approved_exhibitions))

    console.print(table)
