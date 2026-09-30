"""
CLI command group for Vietnamese National Border, Territorial Sovereignty & Border Guard Defense Suite.
Governed by Law on Vietnam Border Defense 2020 (Law No. 66/2020/QH14) & Decree No. 34/2014/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.borderguard_engine import (
    VALID_BORDER_SEGMENTS,
    VALID_GATE_STATUSES,
    VALID_GATE_TIERS,
    VALID_INCIDENT_TYPES,
    VALID_MARKER_INTEGRITY,
    VALID_MARKER_TYPES,
    VALID_PATROL_TYPES,
    VALID_SEVERITY_LEVELS,
    VALID_ZONE_TYPES,
    BorderGuardEngine,
)

app = typer.Typer(
    name="borderguard",
    help="Vietnamese Border Guard & Territorial Sovereignty Suite (Law 66/2020/QH14 & Decree 34/2014/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def borderguard_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Border Defense, Markers Inspected, Patrol Hours, and Seized Contraband.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = BorderGuardEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    contraband_str = f"{telemetry['total_contraband_seized_vnd']:,.0f} VND"
    infr_color = "green" if telemetry["infringements_detected_patrols"] == 0 else "yellow"

    overview_text = (
        f"[bold cyan]Total National Border Markers (Cột mốc quốc giới):[/bold cyan] {telemetry['total_border_markers']}\n"
        f"[bold cyan]Active Border Belt Passes (Giấy phép vành đai biên giới):[/bold cyan] {telemetry['active_border_permits']}\n"
        f"[bold cyan]Patrol Missions / Cumulative Hours (Chuyến tuần tra / Giờ tuần tra):[/bold cyan] {telemetry['total_patrol_missions']} ({telemetry['total_patrol_hours']:,.1f} hrs)\n"
        f"[bold cyan]Infringements Detected in Patrols (Vi phạm phát hiện khi tuần tra):[/bold cyan] [{infr_color}]{telemetry['infringements_detected_patrols']}[/{infr_color}]\n"
        f"[bold cyan]Operational Border Gates (Cửa khẩu quốc gia & quốc tế):[/bold cyan] {telemetry['total_border_gates']}\n"
        f"[bold cyan]Border Incidents Investigated (Vụ việc vi phạm biên giới):[/bold cyan] {telemetry['total_border_incidents']}\n"
        f"[bold cyan]Total Contraband Seized (Tang vật buôn lậu/ma túy thu giữ):[/bold cyan] [bold green]{contraband_str}[/bold green]"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]BỘ TƯ LỆNH BỘ ĐỘI BIÊN PHÒNG — HỆ THỐNG QUẢN LÝ BIÊN GIỚI QUỐC GIA (LUẬT 66/2020/QH14)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    markers_seg = telemetry.get("markers_by_segment", {})
    if markers_seg:
        seg_table = Table(title="Phân bố Cột mốc theo Tuyến Biên giới Quốc gia", box=box.SIMPLE_HEAVY)
        seg_table.add_column("Border Segment", style="cyan")
        seg_table.add_column("Markers Count", justify="right", style="green")
        for seg, cnt in markers_seg.items():
            seg_table.add_row(seg, str(cnt))
        console.print(seg_table)


@app.command("marker")
def register_marker_cmd(
    id_: str = typer.Option(..., "--id", help="Marker unique ID (e.g. BM-VN-LA-450)."),
    number: str = typer.Option(..., "--number", "-n", help="Official boundary marker number (e.g. 450)."),
    segment: str = typer.Option("VIETNAM_LAOS", "--segment", "-s", help="VIETNAM_LAOS, VIETNAM_CAMBODIA, VIETNAM_CHINA."),
    post: str = typer.Option(..., "--post", "-p", help="Managing border guard post (Đồn Biên phòng quản lý)."),
    province: str = typer.Option(..., "--province", help="Province (Tỉnh biên giới)."),
    lat: float = typer.Option(..., "--lat", help="Latitude coordinates."),
    lon: float = typer.Option(..., "--lon", help="Longitude coordinates."),
    type_: str = typer.Option("MAIN_MONUMENT_GRANITE", "--type", "-t", help="MAIN_MONUMENT_GRANITE, AUXILIARY_MARKER, BOUNDARY_SIGN_POST, RIVER_BUOY_MARKER."),
    elev: float = typer.Option(0.0, "--elev", help="Elevation in meters above sea level."),
    integrity: str = typer.Option("INTACT", "--integrity", help="INTACT, WEATHERED, DAMAGED, DISPLACED, UNDER_REPAIR."),
    date: Optional[str] = typer.Option(None, "--date", help="Last inspection date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register and inspect a national border landmark or marker.
    """
    engine = BorderGuardEngine()
    try:
        res = engine.register_marker(
            marker_id=id_,
            marker_number=number,
            border_segment=segment,
            managing_post=post,
            province=province,
            latitude=lat,
            longitude=lon,
            marker_type=type_,
            elevation_meters=elev,
            last_inspected_date=date,
            physical_integrity=integrity,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering border marker:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Cột mốc Quốc giới thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("permit")
def issue_permit_cmd(
    id_: str = typer.Option(..., "--id", help="Permit ID (e.g. PERMIT-2026-001)."),
    name: str = typer.Option(..., "--name", "-n", help="Applicant full name."),
    id_doc: str = typer.Option(..., "--id-doc", help="CCCD or Passport number."),
    zone: str = typer.Option("BORDER_BELT", "--zone", "-z", help="BORDER_BELT, RESTRICTED_ZONE, BORDER_PASS_ROAD, ECONOMIC_BORDER_ZONE."),
    purpose: str = typer.Option(..., "--purpose", help="Official entry purpose."),
    post: str = typer.Option(..., "--post", "-p", help="Issuing border guard post."),
    nationality: str = typer.Option("VNM", "--nationality", help="Nationality code."),
    valid_from: Optional[str] = typer.Option(None, "--from", help="Start validity date (YYYY-MM-DD)."),
    valid_until: Optional[str] = typer.Option(None, "--until", help="End validity date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue an entry permit to access the border belt or restricted border area (Decree 34/2014/NĐ-CP).
    """
    engine = BorderGuardEngine()
    try:
        res = engine.issue_border_permit(
            permit_id=id_,
            applicant_name=name,
            citizen_id_or_passport=id_doc,
            zone_type=zone,
            purpose=purpose,
            issuing_post=post,
            nationality=nationality,
            valid_from=valid_from,
            valid_until=valid_until,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing border permit:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Cấp Giấy phép vào Vành đai Biên giới", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("patrol")
def log_patrol_cmd(
    id_: str = typer.Option(..., "--id", help="Patrol mission ID (e.g. PATROL-2026-001)."),
    type_: str = typer.Option("ROUTINE_FOOT_PATROL", "--type", "-t", help="ROUTINE_FOOT_PATROL, MOTORIZED_RECON, JOINT_BILATERAL_PATROL, RIVERINE_MARITIME_SORTIE, UAV_AERIAL_SURVEILLANCE."),
    post: str = typer.Option(..., "--post", "-p", help="Commanding border post."),
    leader: str = typer.Option(..., "--leader", "-l", help="Patrol squad leader rank & name."),
    notes: str = typer.Option(..., "--notes", help="Operational summary and sovereignty inspection notes."),
    team: int = typer.Option(4, "--team", help="Squad team size."),
    markers: Optional[str] = typer.Option(None, "--markers", help="Comma-separated marker IDs inspected."),
    duration: float = typer.Option(4.0, "--duration", help="Patrol duration in hours."),
    infringements: int = typer.Option(0, "--infringements", help="Infringements detected."),
    date: Optional[str] = typer.Option(None, "--date", help="Patrol date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Log a border guard patrol mission or joint bilateral patrol.
    """
    engine = BorderGuardEngine()
    marker_list = [m.strip() for m in markers.split(",")] if markers else []
    try:
        res = engine.log_patrol_mission(
            mission_id=id_,
            patrol_type=type_,
            commanding_post=post,
            patrol_leader=leader,
            summary_notes=notes,
            team_size=team,
            covered_markers=marker_list,
            duration_hours=duration,
            infringements_detected=infringements,
            patrol_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error logging patrol mission:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký Tuần tra Bảo vệ Đường biên, Mốc quốc giới", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.1f} hrs" if "duration" in str(k) else str(v))
    console.print(table)


@app.command("gate")
def register_gate_cmd(
    id_: str = typer.Option(..., "--id", help="Gate ID (e.g. GATE-HUU-NGHI)."),
    name: str = typer.Option(..., "--name", "-n", help="Border gate official name."),
    tier: str = typer.Option("INTERNATIONAL", "--tier", "-t", help="INTERNATIONAL, BILATERAL_MAIN, SUB_BORDER_GATE, LOCAL_CROSSING_POINT."),
    country: str = typer.Option("CHINA", "--country", "-c", help="CHINA, LAOS, CAMBODIA."),
    station: str = typer.Option(..., "--station", "-s", help="Border control station."),
    capacity: int = typer.Option(1000, "--capacity", help="Daily transit capacity."),
    status: str = typer.Option("NORMAL_OPERATION", "--status", help="NORMAL_OPERATION, RESTRICTED_HOURS, TEMPORARILY_CLOSED, EMERGENCY_LOCKDOWN."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a border gate or immigration checkpoint.
    """
    engine = BorderGuardEngine()
    try:
        res = engine.register_border_gate(
            gate_id=id_,
            gate_name=name,
            gate_tier=tier,
            border_country=country,
            controlling_station=station,
            daily_transit_capacity=capacity,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering border gate:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Trạm Kiểm soát / Cửa khẩu Biên giới", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("incident")
def report_incident_cmd(
    id_: str = typer.Option(..., "--id", help="Incident ID (e.g. INC-BG-2026-001)."),
    type_: str = typer.Option("ILLEGAL_ENTRY_EXIT", "--type", "-t", help="ILLEGAL_ENTRY_EXIT, SMUGGLING_CONTRABAND, BORDER_LINE_ENCROACHMENT, ARMED_TRANSGRESSION, DISPUTED_AREA_ACTIVITY."),
    severity: str = typer.Option("MAJOR", "--severity", "-s", help="CRITICAL, MAJOR, MODERATE."),
    location: str = typer.Option(..., "--location", "-l", help="Location description or marker vicinity."),
    post: str = typer.Option(..., "--post", "-p", help="Handling border post."),
    persons: int = typer.Option(1, "--persons", help="Persons involved."),
    contraband: float = typer.Option(0.0, "--contraband", help="Estimated value of contraband in VND."),
    talks: bool = typer.Option(False, "--talks", help="Whether bilateral flag talks were held."),
    status: str = typer.Option("UNDER_INVESTIGATION", "--status", help="UNDER_INVESTIGATION, RESOLVED_EXPULSION, CRIMINAL_CHARGES, DIPLOMATIC_NOTE_SENT."),
    date: Optional[str] = typer.Option(None, "--date", help="Incident date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Report a border incident, territorial encroachment, smuggling, or illegal crossing.
    """
    engine = BorderGuardEngine()
    try:
        res = engine.report_border_incident(
            incident_id=id_,
            incident_type=type_,
            severity_level=severity,
            location_description=location,
            handling_post=post,
            involved_persons_count=persons,
            contraband_value_vnd=contraband,
            bilateral_talks_held=talks,
            outcome_status=status,
            incident_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error reporting border incident:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Báo cáo Vụ việc Vi phạm Biên giới Quốc gia", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "contraband" in str(k) else str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="markers, permits, patrols, gates, incidents, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List border markers, permits, patrol missions, gates, and incidents.
    """
    engine = BorderGuardEngine()
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
    Get aggregate telemetry metrics on border defense readiness and sovereignty enforcement.
    """
    engine = BorderGuardEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Thực thi Chủ quyền & Quản lý Biên giới", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} sub-categories")
        elif isinstance(v, float) and "vnd" in str(k):
            table.add_row(str(k), f"{v:,.0f} VND")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
