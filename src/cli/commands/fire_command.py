# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI commands for Vietnamese Fire Prevention, Safety & Rescue Standards Suite (Phase 92)."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

fire_app = typer.Typer(
    name="fire",
    help="Vietnamese Fire Prevention, Safety, Rescue & Engineering Standards Suite.",
)
console = Console()


@fire_app.callback(invoke_without_command=True)
def fire_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo tổng quan hoạt động phòng cháy, chữa cháy, thẩm duyệt thiết kế và nghiệm thu công trình PCCC."""
    if ctx.invoked_subcommand is not None:
        return

    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    status_data = engine.get_status()

    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return

    console.print(
        Panel(
            f"[bold green]HỆ THỐNG AN TOÀN PHÒNG CHÁY, CHỮA CHÁY & CỨU NẠN CỨU HỘ VIỆT NAM (PCCC & CNCH)[/]\n\n"
            f"  Khung pháp lý:             [bold]{status_data['statutory_law']}[/]\n"
            f"  Hồ sơ thẩm duyệt thiết kế: [bold cyan]{status_data['total_design_approvals_audited']}[/] công trình ([bold green]{status_data['approved_fire_designs']}[/] đạt chuẩn QCVN 06:2022)\n"
            f"  Hậu kiểm nghiệm thu PCCC:  [bold]{status_data['total_acceptance_inspections']}[/] công trình kiểm tra\n"
            f"  Vi phạm đưa vào sử dụng:   [bold red]{status_data['unapproved_occupancy_violations']}[/] công trình chưa nghiệm thu đưa vào hoạt động\n"
            f"  Tổng tiền phạt xử lý:      [bold red]{status_data['total_fire_safety_penalties_vnd']:,.0f} VND[/] (Nghị định 144/2021/NĐ-CP)\n"
            f"  Phương tiện PCCC kiểm định:[bold green]{status_data['certified_fire_equipment_stamped']}[/] thiết bị dán tem / {status_data['total_equipment_inspected']} kiểm định\n"
            f"  Giấy phép dịch vụ PCCC:    [bold green]{status_data['active_fire_service_licenses']}[/] doanh nghiệp đủ điều kiện kinh doanh dịch vụ PCCC",
            title="[bold green]Vietnam Fire Prevention, Safety & Rescue Telemetry[/]",
            border_style="green",
        )
    )


@fire_app.command("design")
def design_cmd(
    facility: str = typer.Argument(..., help="Tên công trình, tòa nhà hoặc cơ sở thẩm duyệt"),
    facility_type: str = typer.Option("COMMERCIAL_BUILDING", "--type", "-t", help="Loại: COMMERCIAL_BUILDING, KARAOKE_NIGHTCLUB, INDUSTRIAL_WAREHOUSE, RESIDENTIAL_HIGHRISE"),
    floors: int = typer.Option(15, "--floors", "-f", help="Số tầng của công trình"),
    area: float = typer.Option(12000.0, "--area", "-a", help="Tổng diện tích sàn xây dựng (m2)"),
    fire_class: str = typer.Option("CLASS_I", "--class", "-c", help="Bậc chịu lửa: CLASS_I, CLASS_II, CLASS_III, CLASS_IV"),
    sprinkler: bool = typer.Option(True, "--sprinkler/--no-sprinkler", help="Có trang bị hệ thống chữa cháy tự động Sprinkler"),
    alarm: bool = typer.Option(True, "--alarm/--no-alarm", help="Có trang bị hệ thống báo cháy tự động"),
    smoke: bool = typer.Option(True, "--smoke/--no-smoke", help="Có hệ thống hút khói sự cố và tăng áp buồng thang"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm duyệt thiết kế PCCC cho công trình xây dựng theo QCVN 06:2022/BXD và Nghị định 136/2020 / NĐ 50/2024."""
    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    res = engine.audit_fire_design_approval(
        facility_name=facility,
        facility_type=facility_type,
        floors_count=floors,
        floor_area_sqm=area,
        fire_resistance_class=fire_class,
        has_sprinkler=sprinkler,
        has_alarm=alarm,
        has_smoke_exhaust=smoke,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_approved"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ THẨM DUYỆT THIẾT KẾ PCCC (NGHỊ ĐỊNH 136/2020 & QCVN 06:2022)[/]\n\n"
            f"  Số văn bản thẩm duyệt:[bold cyan]{res['approval_code']}[/]\n"
            f"  Tên công trình:       [bold]{res['facility_name']}[/]\n"
            f"  Loại hình / Quy mô:   [white]{res['facility_type']}[/] ({res['floors_count']} tầng, {res['floor_area_sqm']:,.0f} m2 sàn)\n"
            f"  Bậc chịu lửa:         [yellow]{res['fire_resistance_class']}[/]\n"
            f"  Hệ thống Sprinkler:   [white]{'ĐÃ THIẾT KẾ ĐẠT CHUẨN' if res['has_sprinkler'] else '[bold red]THIẾU HỆ THỐNG SPRINKLER[/]'}[/]\n"
            f"  Báo cháy tự động:     [white]{'CÓ' if res['has_alarm'] else '[bold red]THIẾU[/]'}[/] | Hút khói sự cố: [white]{'CÓ' if res['has_smoke_exhaust'] else '[bold red]THIẾU[/]'}[/]\n"
            f"  Kết luận thẩm duyệt:  [bold {color}]{res['status']}[/]\n"
            + (f"  Thiếu sót kỹ thuật:   [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:             [bold green]Thiết kế PCCC đáp ứng đầy đủ điều kiện để thi công xây dựng[/]"),
            title=f"[bold {color}]Fire Protection Design Approval Assessment[/]",
            border_style=color,
        )
    )


@fire_app.command("accept")
def accept_cmd(
    facility: str = typer.Argument(..., help="Tên công trình kiểm tra nghiệm thu"),
    pressure: float = typer.Option(0.45, "--pressure", "-p", help="Áp lực nước chữa cháy tại họng nước xa nhất (MPa, >= 0.40)"),
    switch_sec: float = typer.Option(12.0, "--switch-sec", "-s", help="Thời gian chuyển đổi nguồn máy phát dự phòng (giây, <= 15)"),
    smoke_ok: bool = typer.Option(True, "--smoke-ok/--smoke-fail", help="Hệ thống hút khói và tăng áp thang bộ hoạt động tốt"),
    exit_ok: bool = typer.Option(True, "--exit-ok/--exit-fail", help="Lối và cửa thoát nạn mở đúng hướng, không bị cản trở"),
    operational: bool = typer.Option(False, "--operational/--non-operational", help="Công trình đã tự ý đưa vào sử dụng trước khi nghiệm thu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Nghiệm thu an toàn PCCC trước khi đưa công trình vào sử dụng theo Điều 15 Nghị định 136/2020/NĐ-CP."""
    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    res = engine.inspect_fire_acceptance(
        facility_name=facility,
        water_pressure_mpa=pressure,
        generator_switch_sec=switch_sec,
        is_smoke_system_ok=smoke_ok,
        is_exit_doors_compliant=exit_ok,
        is_already_operational=operational,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_accepted"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ NGHIỆM THU AN TOÀN PCCC (ĐIỀU 15 NGHỊ ĐỊNH 136/2020)[/]\n\n"
            f"  Biên bản nghiệm thu:  [bold cyan]{res['inspection_code']}[/]\n"
            f"  Công trình nghiệm thu:[bold]{res['facility_name']}[/]\n"
            f"  Áp lực nước chữa cháy:[white]{res['water_pressure_mpa']} MPa[/] (Yêu cầu >= 0.40 MPa)\n"
            f"  Đóng điện dự phòng:   [white]{res['generator_switch_sec']} giây[/] (Yêu cầu <= 15s)\n"
            f"  Hút khói & Cửa thoát: [white]{'ĐẠT CHUẨN' if res['is_smoke_system_ok'] and res['is_exit_doors_compliant'] else '[bold red]KHÔNG ĐẠT YÊU CẦU[/]'}[/]\n"
            f"  Tự ý hoạt động trước: [white]{'[bold red]CÓ (VI PHẠM PHÁP LUẬT)[/]' if res['is_already_operational'] else 'CHƯA'}[/]\n"
            f"  Kết luận nghiệm thu:  [bold {color}]{res['status']}[/]\n"
            + (f"  Tồn tại / Lỗi nghiệm thu:[bold red]{'; '.join(res['deficiencies'])}[/]\n" if res["deficiencies"] else "")
            + (f"  Mức phạt hành chính:  [bold red]{res['penalty_fine_vnd']:,.0f} VND (Nghị định 144/2021/NĐ-CP)[/]" if res["penalty_fine_vnd"] > 0 else "  Đánh giá:             [bold green]Công trình đủ điều kiện an toàn PCCC, được phép đưa vào hoạt động[/]"),
            title=f"[bold {color}]Fire Protection Acceptance Inspection[/]",
            border_style=color,
        )
    )


@fire_app.command("equip")
def equip_cmd(
    serial: str = typer.Argument(..., help="Số sê-ri hoặc mã quản lý phương tiện PCCC"),
    equip_type: str = typer.Option("EXTINGUISHER_ABC_4KG", "--type", "-t", help="Loại: EXTINGUISHER_ABC_4KG, EXTINGUISHER_CO2_5KG, SPRINKLER_HEAD_DN15, FIRE_HOSE_DN65"),
    mfr: str = typer.Option("Công ty TNHH Thiết bị PCCC Mekong", "--mfr", "-m", help="Nhà sản xuất phương tiện PCCC"),
    pressure: float = typer.Option(14.0, "--pressure", "-p", help="Áp suất làm việc kiểm tra (bar)"),
    tested: bool = typer.Option(True, "--tested/--untested", help="Đã qua kiểm định mẫu tại phòng thử nghiệm"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm định phương tiện PCCC và cấp tem kiểm định PCCC theo Điều 38 Nghị định 136/2020/NĐ-CP."""
    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    res = engine.verify_fire_equipment(
        equipment_type=equip_type,
        serial_number=serial,
        manufacturer=mfr,
        pressure_rating_bar=pressure,
        has_factory_testing=tested,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_certified"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]KẾT QUẢ KIỂM ĐỊNH PHƯƠNG TIỆN PCCC (ĐIỀU 38 NGHỊ ĐỊNH 136/2020)[/]\n\n"
            f"  Mã kiểm định:        [bold cyan]{res['verification_code']}[/]\n"
            f"  Số sê-ri / Quản lý:  [bold]{res['serial_number']}[/]\n"
            f"  Loại phương tiện:    [white]{res['equipment_type']}[/]\n"
            f"  Nhà sản xuất:        [white]{res['manufacturer']}[/]\n"
            f"  Áp suất kiểm tra:    [yellow]{res['pressure_rating_bar']} bar[/]\n"
            f"  Tem kiểm định PCCC:  [bold green]{res['stamp_issued']}[/]\n"
            f"  Thời hạn tem:        [bold]{res['validity_years']} năm[/]\n"
            f"  Kết luận kiểm định:  [bold {color}]{res['status']}[/]",
            title=f"[bold {color}]Fire Equipment Certification & Stamping[/]",
            border_style=color,
        )
    )


@fire_app.command("license")
def license_cmd(
    firm: str = typer.Argument(..., help="Tên doanh nghiệp kinh doanh dịch vụ PCCC"),
    director: str = typer.Option("Kỹ sư Trần Anh Tuấn", "--director", "-d", help="Họ tên người đại diện pháp luật"),
    director_cert: bool = typer.Option(True, "--director-cert/--no-director-cert", help="Người đứng đầu có chứng chỉ bồi dưỡng kiến thức PCCC"),
    engineers: int = typer.Option(2, "--engineers", "-e", help="Số lượng kỹ sư có chứng chỉ hành nghề PCCC (>= 1)"),
    facility: bool = typer.Option(True, "--facility/--no-facility", help="Cơ sở vật chất, phương tiện thiết bị phục vụ dịch vụ PCCC đầy đủ"),
    scope: str = typer.Option("DESIGN_AND_SUPERVISION", "--scope", "-s", help="Phạm vi hoạt động: DESIGN_AND_SUPERVISION, INSTALLATION, MAINTENANCE"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra điều kiện kinh doanh dịch vụ PCCC theo Điều 41 Nghị định 136/2020 và Nghị định 50/2024."""
    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    res = engine.license_fire_service_firm(
        firm_name=firm,
        technical_director=director,
        has_director_certificate=director_cert,
        certified_engineers_count=engineers,
        has_equipment_facility=facility,
        scope=scope,
    )

    if json_mode:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    is_ok = res["is_licensed"]
    color = "green" if is_ok else "red"

    console.print(
        Panel(
            f"[bold {color}]THẨM ĐỊNH ĐIỀU KIỆN KINH DOANH DỊCH VỤ PCCC (ĐIỀU 41)[/]\n\n"
            f"  Số giấy phép:        [bold cyan]{res['license_code']}[/]\n"
            f"  Tên doanh nghiệp:    [bold]{res['firm_name']}[/]\n"
            f"  Người đứng đầu:      [white]{res['technical_director']}[/] ({'Đã có chứng chỉ bồi dưỡng PCCC' if res['has_director_certificate'] else '[bold red]Chưa có chứng chỉ[/]'})\n"
            f"  Nhân sự có CCHN:     [white]{res['certified_engineers_count']} kỹ sư có chứng chỉ hành nghề PCCC[/]\n"
            f"  Cơ sở vật chất:      [white]{'ĐẠT YÊU CẦU' if res['has_equipment_facility'] else '[bold red]CHƯA ĐỦ ĐIỀU KIỆN[/]'}[/]\n"
            f"  Phạm vi hoạt động:   [cyan]{res['scope']}[/]\n"
            f"  Thời hạn giấy phép:  [bold]{res['validity_years']} năm[/]\n"
            f"  Kết luận thẩm tra:   [bold {color}]{res['status']}[/]\n"
            + (f"  Thiếu sót hồ sơ:     [bold red]{'; '.join(res['deficiencies'])}[/]" if res["deficiencies"] else "  Đánh giá:            [bold green]Doanh nghiệp đủ điều kiện kinh doanh dịch vụ phòng cháy và chữa cháy[/]"),
            title=f"[bold {color}]Fire Service Business Licensing Assessment[/]",
            border_style=color,
        )
    )


@fire_app.command("list")
def list_records_cmd(
    category: str = typer.Argument("designs", help="Danh mục: designs, acceptances, equipments, licenses"),
    limit: int = typer.Option(20, "--limit", "-l", help="Số bản ghi tối đa"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tra cứu danh mục hồ sơ thẩm duyệt thiết kế, nghiệm thu, kiểm định phương tiện hoặc giấy phép dịch vụ PCCC."""
    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_mode:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    table = Table(title=f"Danh mục an toàn PCCC & cứu nạn cứu hộ [{category.upper()}] (Tối đa {limit} bản ghi)")
    if category in ["acceptances", "inspections", "nghiem_thu"]:
        table.add_column("Mã nghiệm thu", style="bold cyan")
        table.add_column("Tên công trình", style="white")
        table.add_column("Áp lực nước", style="yellow")
        table.add_column("Điện dự phòng", style="cyan")
        table.add_column("Tiền phạt", style="bold red")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_accepted") else "red"
            table.add_row(
                r.get("inspection_code", ""),
                r.get("facility_name", ""),
                f"{r.get('water_pressure_mpa', 0)} MPa",
                f"{r.get('generator_switch_sec', 0)}s",
                f"{r.get('penalty_fine_vnd', 0):,.0f} VND",
                f"[{color}]{r.get('status', '')}[/]",
            )
    elif category in ["equipments", "devices", "phuong_tien", "kiem_dinh"]:
        table.add_column("Mã kiểm định", style="bold cyan")
        table.add_column("Số sê-ri", style="white")
        table.add_column("Loại thiết bị", style="yellow")
        table.add_column("Nhà sản xuất", style="white")
        table.add_column("Áp suất (bar)", style="cyan")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_certified") else "red"
            table.add_row(
                r.get("verification_code", ""),
                r.get("serial_number", ""),
                r.get("equipment_type", ""),
                r.get("manufacturer", ""),
                str(r.get("pressure_rating_bar", 0)),
                f"[{color}]{r.get('status', '')}[/]",
            )
    elif category in ["licenses", "firms", "kinh_doanh"]:
        table.add_column("Số giấy phép", style="bold cyan")
        table.add_column("Doanh nghiệp", style="white")
        table.add_column("Người đại diện", style="yellow")
        table.add_column("Kỹ sư CCHN", style="cyan")
        table.add_column("Phạm vi", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_licensed") else "red"
            table.add_row(
                r.get("license_code", ""),
                r.get("firm_name", ""),
                r.get("technical_director", ""),
                str(r.get("certified_engineers_count", 0)),
                r.get("scope", ""),
                f"[{color}]{r.get('status', '')}[/]",
            )
    else:
        table.add_column("Mã thẩm duyệt", style="bold cyan")
        table.add_column("Tên công trình", style="white")
        table.add_column("Loại hình", style="yellow")
        table.add_column("Số tầng", style="cyan")
        table.add_column("Diện tích (m2)", style="white")
        table.add_column("Trạng thái", style="bold")
        for r in records:
            color = "green" if r.get("is_approved") else "red"
            table.add_row(
                r.get("approval_code", ""),
                r.get("facility_name", ""),
                r.get("facility_type", ""),
                str(r.get("floors_count", 0)),
                f"{r.get('floor_area_sqm', 0):,.0f}",
                f"[{color}]{r.get('status', '')}[/]",
            )

    console.print(table)


@fire_app.command("status")
def status_cmd(
    json_mode: bool = typer.Option(True, "--json", help="Xuất kết quả dưới định dạng JSON"),
) -> None:
    """Báo cáo chỉ số telemetry tổng hợp an toàn PCCC, thẩm duyệt thiết kế và nghiệm thu công trình."""
    from src.core.fire_engine import FireEngine

    engine = FireEngine()
    data = engine.get_status()
    typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
