"""
CLI command group for Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite.
Governed by Law on Road Traffic Safety and Order 2024 (Law No. 36/2024/QH15) & Road Law 2024 (Law No. 35/2024/QH15).
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.traffic_engine import (
    VALID_ACTIONS_TAKEN,
    VALID_CAMERA_STATUS,
    VALID_CAMERA_VIOLATIONS,
    VALID_DRUG_RESULTS,
    VALID_EMISSIONS_STANDARDS,
    VALID_INSPECTION_RESULTS,
    VALID_LICENSE_CLASSES,
    VALID_LICENSE_STATUS,
    VALID_STOP_REASONS,
    VALID_VEHICLE_TYPES,
    TrafficEngine,
)

app = typer.Typer(
    name="traffic",
    help="Vietnamese Road Traffic Safety, Demerit Points & Law Enforcement Suite (Luật Trật tự, ATGT Đường bộ 2024).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def traffic_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Driver Licenses, 12 Demerit Points, Citations, Camera Ticketing, Inspections & Sobriety.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = TrafficEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    fines_str = f"{telemetry['total_fines_vnd']:,.0f} VND"
    alc_color = "green" if telemetry["alcohol_violations_detected"] == 0 else "red"

    overview_text = (
        f"[bold cyan]Active Driver Licenses (GPLX hợp lệ trong hệ thống):[/bold cyan] {telemetry['active_valid_licenses']} licenses ([yellow]{telemetry['suspended_licenses_zero_points']} suspended / 0 points remaining[/yellow])\n"
        f"[bold cyan]Traffic Citations & Fines (Biên bản vi phạm TTATGT / Tiền phạt):[/bold cyan] {telemetry['total_tickets_issued']} tickets ([bold green]{fines_str}[/bold green], [bold red]{telemetry['total_points_deducted']} points deducted[/bold red])\n"
        f"[bold cyan]Automated AI Camera Notices (Phạt nguội qua camera giám sát AI):[/bold cyan] {telemetry['pending_camera_notices']} pending notices\n"
        f"[bold cyan]Vehicle Roadworthiness Inspections (Phương tiện đạt tiêu chuẩn kiểm định):[/bold cyan] {telemetry['passed_vehicle_inspections']} vehicles certified\n"
        f"[bold cyan]Traffic Police Patrol Stops & Sobriety (Kiểm tra nồng độ cồn & ma túy):[/bold cyan] {telemetry['total_road_stops']} stops ([{alc_color}]{telemetry['alcohol_violations_detected']} alcohol violations detected[/{alc_color}])"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]CỤC CẢNH SÁT GIAO THÔNG — TRUNG TÂM QUẢN LÝ DỮ LIỆU TTATGT ĐƯỜNG BỘ (LUẬT 36/2024/QH15)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )


@app.command("license")
def register_license_cmd(
    number: str = typer.Option(..., "--number", "-n", help="Driver license number (e.g. 790123456789)."),
    name: str = typer.Option(..., "--name", help="Driver full name."),
    citizen_id: str = typer.Option(..., "--citizen-id", "-c", help="Citizen ID number (CCCD 12 digits)."),
    class_: str = typer.Option("B", "--class", help="License class: A1, A, B1, B, C1, C, D1, D2, D, BE, CE, DE."),
    issue: Optional[str] = typer.Option(None, "--issue", help="Issue date (YYYY-MM-DD)."),
    expiry: Optional[str] = typer.Option(None, "--expiry", help="Expiry date (YYYY-MM-DD)."),
    points: int = typer.Option(12, "--points", help="Initial points (default 12 under Article 58)."),
    status: str = typer.Option("ACTIVE_VALID", "--status", help="ACTIVE_VALID, POINTS_EXHAUSTED_SUSPENDED, REVOKED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a driver license and initialize 12 statutory points (Article 58 Law 36/2024/QH15).
    """
    engine = TrafficEngine()
    try:
        res = engine.register_license(
            license_number=number,
            driver_name=name,
            citizen_id=citizen_id,
            license_class=class_,
            issue_date=issue,
            expiry_date=expiry,
            total_points=points,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering driver license:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Giấy phép Lái xe & 12 Điểm số Thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("ticket")
def issue_ticket_cmd(
    id_: str = typer.Option(..., "--id", help="Ticket ID (e.g. TCK-2026-0001)."),
    license_: str = typer.Option(..., "--license", "-l", help="Driver license number."),
    plate: str = typer.Option(..., "--plate", "-p", help="Vehicle plate number (e.g. 30A-998.88)."),
    code: str = typer.Option(..., "--code", help="Statutory violation code (e.g. D100-D5-D3)."),
    desc: str = typer.Option(..., "--desc", help="Violation details description."),
    location: str = typer.Option(..., "--location", help="Violation location or intersection."),
    officer: str = typer.Option(..., "--officer", help="Officer badge number."),
    fine: float = typer.Option(0.0, "--fine", help="Administrative fine amount in VND."),
    points: int = typer.Option(0, "--points", help="Demerit points to deduct (0 to 12)."),
    date: Optional[str] = typer.Option(None, "--date", help="Citation date (YYYY-MM-DD)."),
    paid: bool = typer.Option(False, "--paid", help="Whether fine has been paid."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue a traffic police citation and deduct driver license points (Article 58 & 65 Law 36/2024/QH15).
    """
    engine = TrafficEngine()
    try:
        res = engine.issue_ticket(
            ticket_id=id_,
            license_number=license_,
            vehicle_plate=plate,
            violation_code=code,
            violation_description=desc,
            fine_amount_vnd=fine,
            points_deducted=points,
            location=location,
            officer_badge=officer,
            ticket_date=date,
            paid=paid,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing traffic ticket:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Lập Biên bản Xử phạt Vi phạm Giao thông", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "fine" in str(k) else str(v))
    console.print(table)


@app.command("camera")
def record_camera_cmd(
    id_: str = typer.Option(..., "--id", help="Camera notice ID (e.g. CAM-2026-0001)."),
    plate: str = typer.Option(..., "--plate", "-p", help="Vehicle plate number (e.g. 51F-123.45)."),
    type_: str = typer.Option("SPEEDING_OVER_LIMIT", "--type", "-t", help="SPEEDING_OVER_LIMIT, RUNNING_RED_LIGHT, WRONG_LANE_USAGE, RETROGRADE_WRONG_WAY, ILLEGAL_STOPPING_PARKING."),
    location: str = typer.Option(..., "--location", help="Surveillance camera location."),
    value: str = typer.Option(..., "--value", help="Measured detection value (e.g. 95 km/h / 60 km/h)."),
    date: Optional[str] = typer.Option(None, "--date", help="Detection date (YYYY-MM-DD)."),
    due: Optional[str] = typer.Option(None, "--due", help="Due date to appear/pay (YYYY-MM-DD)."),
    status: str = typer.Option("NOTICE_ISSUED", "--status", help="NOTICE_ISSUED, RESOLVED_PAID, ESCALATED_WARNING_FLAG."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record an automated AI surveillance camera traffic violation notice (Article 72 & 73 Law 36/2024/QH15).
    """
    engine = TrafficEngine()
    try:
        res = engine.record_camera_notice(
            notice_id=id_,
            vehicle_plate=plate,
            violation_type=type_,
            camera_location=location,
            measured_value=value,
            notice_date=date,
            due_date=due,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording camera notice:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Thông báo Vi phạm Phạt nguội Camera AI", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("inspection")
def record_inspection_cmd(
    id_: str = typer.Option(..., "--id", help="Inspection ID (e.g. INSP-DK-2026-01)."),
    plate: str = typer.Option(..., "--plate", "-p", help="Vehicle registration plate."),
    vin: str = typer.Option(..., "--vin", help="Vehicle Identification Number (VIN)."),
    type_: str = typer.Option("PASSENGER_CAR", "--type", "-t", help="PASSENGER_CAR, HEAVY_TRUCK, BUS_COACH, TRACTOR_TRAILER, ELECTRIC_VEHICLE."),
    center: str = typer.Option(..., "--center", help="Inspection center code (e.g. TTDK-2903D)."),
    brake: float = typer.Option(65.0, "--brake", help="Brake efficiency percentage."),
    emissions: str = typer.Option("EURO_5", "--emissions", help="EURO_4, EURO_5, EURO_6, ZERO_EMISSION_EV."),
    result: str = typer.Option("PASSED", "--result", help="PASSED, FAILED_DEFECTS_DETECTED."),
    valid: Optional[str] = typer.Option(None, "--valid", help="Inspection certificate validity date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record a periodic motor vehicle safety and emissions inspection (Article 42 Law 36/2024/QH15).
    """
    engine = TrafficEngine()
    try:
        res = engine.record_inspection(
            inspection_id=id_,
            vehicle_plate=plate,
            vin_number=vin,
            vehicle_type=type_,
            center_code=center,
            brake_efficiency_percent=brake,
            emissions_standard=emissions,
            result=result,
            valid_until=valid,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording vehicle inspection:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Giấy chứng nhận Kiểm định An toàn Kỹ thuật & Bảo vệ Môi trường", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:.1f}%" if "percent" in str(k) else str(v))
    console.print(table)


@app.command("stop")
def log_stop_cmd(
    id_: str = typer.Option(..., "--id", help="Road stop ID (e.g. STOP-2026-0001)."),
    plate: str = typer.Option(..., "--plate", "-p", help="Vehicle plate number."),
    reason: str = typer.Option("ROUTINE_ALCOHOL_CHECK", "--reason", "-r", help="ROUTINE_ALCOHOL_CHECK, SPEED_INTERCEPT, OVERLOAD_CHECK, SUSPICIOUS_BEHAVIOR."),
    unit: str = typer.Option(..., "--unit", "-u", help="Traffic police division / squad name."),
    alcohol: float = typer.Option(0.0, "--alcohol", help="Breath alcohol concentration in mg/l (0.0 = zero)."),
    drug: str = typer.Option("NEGATIVE", "--drug", help="NEGATIVE, POSITIVE_OPIATES, POSITIVE_METH, POSITIVE_THC."),
    action: str = typer.Option("CLEARED_NO_VIOLATION", "--action", help="CLEARED_NO_VIOLATION, TICKETED_FINE_POINTS, VEHICLE_IMPOUNDED."),
    time: Optional[str] = typer.Option(None, "--time", help="Stop timestamp (ISO format)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Log a traffic police patrol stop with alcohol breathalyzer and drug screening (Article 8 & 65 Law 36/2024/QH15).
    """
    engine = TrafficEngine()
    try:
        res = engine.log_road_stop(
            stop_id=id_,
            vehicle_plate=plate,
            stop_reason=reason,
            officer_unit=unit,
            breath_alcohol_mg_l=alcohol,
            drug_screening_result=drug,
            action_taken=action,
            stop_timestamp=time,
        )
    except Exception as e:
        console.print(f"[bold red]Error logging road stop:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký Dừng xe & Kiểm tra Nồng độ Cồn, Ma túy", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:.3f} mg/l" if "alcohol" in str(k) else str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="licenses, tickets, camera, inspections, stops, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List records across driver licenses, tickets, camera notices, inspections, and road stops.
    """
    engine = TrafficEngine()
    records = engine.list_records(record_type=record_type, limit=limit)

    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for category, items in records.items():
        table = Table(title=f"Danh mục {category.upper()} ({len(items)} bản ghi)", box=box.ROUNDED)
        if not items:
            console.print(f"[dim]No {category} found.[/dim]")
            continue

        columns = list(items[0].keys())
        for col in columns[:6]:
            table.add_column(col, style="cyan")
        for item in items:
            table.add_row(*[str(item.get(c, "")) for c in columns[:6]])
        console.print(table)


@app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Get aggregate telemetry metrics on driver licenses, demerit points deducted, camera ticketing, and sobriety checks.
    """
    engine = TrafficEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Vận hành Hệ thống Trật tự, An toàn Giao thông Đường bộ", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, float) and "vnd" in str(k):
            table.add_row(str(k), f"{v:,.0f} VND")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
