"""
CLI command group for Vietnamese Coast Guard & Maritime Law Enforcement Suite.
Governed by Law on Vietnam Coast Guard 2018 (Law No. 33/2018/QH14) & Decree No. 61/2019/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.coastguard_engine import (
    VALID_COASTGUARD_REGIONS,
    VALID_INSPECTION_REASONS,
    VALID_IUU_VIOLATIONS,
    VALID_PATROL_TYPES,
    VALID_SAR_TYPES,
    VALID_VESSEL_CLASSES,
    VALID_VESSEL_STATUS,
    CoastGuardEngine,
)

app = typer.Typer(
    name="coastguard",
    help="Vietnamese Coast Guard & Maritime Law Enforcement Suite (Law 33/2018/QH14 & Decree 61/2019/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def coastguard_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Coast Guard Fleet, Maritime Patrols, Inspections, IUU Deterrence, and SAR.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = CoastGuardEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    nm_str = f"{telemetry['total_nautical_miles']:,.1f} NM"
    fines_str = f"{telemetry['total_inspection_fines_vnd']:,.0f} VND"
    iuu_str = f"{telemetry['total_iuu_penalties_vnd']:,.0f} VND"
    infr_color = "green" if telemetry["infringements_detected"] == 0 else "yellow"

    overview_text = (
        f"[bold cyan]Mission-Ready Coast Guard Cutters (Tàu CSB trực sẵn sàng chiến đấu):[/bold cyan] {telemetry['mission_ready_vessels']} vessels\n"
        f"[bold cyan]Sovereignty Patrols / Days at Sea (Chuyến tuần tra / Ngày trên biển):[/bold cyan] {telemetry['total_maritime_patrols']} sorties ({telemetry['total_days_at_sea']} days, [bold green]{nm_str}[/bold green])\n"
        f"[bold cyan]Boarding Inspections at Sea (Kiểm tra, kiểm soát trên biển):[/bold cyan] {telemetry['total_inspections']} vessels ([{infr_color}]{telemetry['infringements_detected']} infringements[/{infr_color}], [bold green]{fines_str}[/bold green] in fines)\n"
        f"[bold cyan]Anti-IUU Deterrence Cases (Xử lý vi phạm khai thác hải sản IUU):[/bold cyan] {telemetry['total_iuu_cases']} cases (Fines: [bold green]{iuu_str}[/bold green])\n"
        f"[bold cyan]Maritime Search & Rescue (Tìm kiếm cứu nạn, cứu hộ trên biển):[/bold cyan] {telemetry['total_sar_missions']} missions ([bold green]{telemetry['total_lives_rescued']} fishermen/crew rescued[/bold green])"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]BỘ TƯ LỆNH CẢNH SÁT BIỂN VIỆT NAM — HỆ THỐNG ĐIỀU HÀNH CHẤP PHÁP BIỂN (LUẬT 33/2018/QH14)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    vessels_by_region = telemetry.get("vessels_by_region", {})
    if vessels_by_region:
        reg_table = Table(title="Phân bổ Lực lượng Tàu Chấp pháp theo Vùng Cảnh sát biển", box=box.SIMPLE_HEAVY)
        reg_table.add_column("Coast Guard Region (Vùng CSB)", style="cyan")
        reg_table.add_column("Assigned Vessels", justify="right", style="green")
        for reg, cnt in vessels_by_region.items():
            reg_table.add_row(reg, str(cnt))
        console.print(reg_table)


@app.command("vessel")
def register_vessel_cmd(
    id_: str = typer.Option(..., "--id", help="Vessel unique ID (e.g. CSB-8002)."),
    hull: str = typer.Option(..., "--hull", "-n", help="Official hull number (e.g. 8002)."),
    type_: str = typer.Option("OFFSHORE_PATROL_VESSEL_OPV", "--class", "-c", help="OFFSHORE_PATROL_VESSEL_OPV, FAST_PATROL_BOAT_FPB, RESCUE_TUG_SALVAGE, RECON_SURVEILLANCE."),
    region: str = typer.Option("REGION_2_CENTRAL", "--region", "-r", help="REGION_1_NORTH, REGION_2_CENTRAL, REGION_3_SOUTH, REGION_4_SOUTHWEST."),
    port: str = typer.Option(..., "--port", "-p", help="Home port base (e.g. Cảng Kỳ Hà, Quảng Nam)."),
    displacement: float = typer.Option(400.0, "--displacement", "-d", help="Displacement in tons."),
    year: int = typer.Option(2020, "--year", "-y", help="Commissioning year."),
    status: str = typer.Option("ACTIVE_MISSION_READY", "--status", help="ACTIVE_MISSION_READY, ON_SEA_PATROL, SCHEDULED_DRYDOCK, STANDBY_HARBOR."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a Coast Guard patrol cutter or specialized ship (Article 29 Law 33/2018/QH14).
    """
    engine = CoastGuardEngine()
    try:
        res = engine.register_vessel(
            vessel_id=id_,
            hull_number=hull,
            vessel_class=type_,
            assigned_region=region,
            home_port=port,
            displacement_tons=displacement,
            commission_year=year,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering Coast Guard vessel:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Tàu Tuần tra Cảnh sát biển thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("patrol")
def log_patrol_cmd(
    id_: str = typer.Option(..., "--id", help="Patrol mission ID (e.g. PATROL-CSB-2026-01)."),
    vessel: str = typer.Option(..., "--vessel", "-v", help="Participating Coast Guard vessel ID."),
    type_: str = typer.Option("ROUTINE_EEZ_PATROL", "--type", "-t", help="ROUTINE_EEZ_PATROL, JOINT_BILATERAL_PATROL, ANTI_SMUGGLING_SWEEP, SOVEREIGNTY_PROTECTION_SORTIE."),
    scope: str = typer.Option(..., "--scope", "-s", help="Sea area scope (e.g. Thềm lục địa phía Nam, Vịnh Bắc Bộ)."),
    commander: str = typer.Option(..., "--commander", help="Commanding officer rank & name."),
    days: int = typer.Option(7, "--days", help="Number of days at sea."),
    miles: float = typer.Option(500.0, "--miles", help="Nautical miles covered."),
    start: Optional[str] = typer.Option(None, "--start", help="Patrol departure date (YYYY-MM-DD)."),
    end: Optional[str] = typer.Option(None, "--end", help="Patrol return date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Log a maritime sovereignty patrol or EEZ surveillance sortie (Article 11 Law 33/2018/QH14).
    """
    engine = CoastGuardEngine()
    try:
        res = engine.log_patrol(
            patrol_id=id_,
            vessel_id=vessel,
            patrol_type=type_,
            sea_area_scope=scope,
            commanding_officer=commander,
            days_at_sea=days,
            nautical_miles=miles,
            start_date=start,
            end_date=end,
        )
    except Exception as e:
        console.print(f"[bold red]Error logging maritime patrol:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký Hành trình Tuần tra Chấp pháp Biển", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.1f} NM" if "nautical" in str(k) else str(v))
    console.print(table)


@app.command("inspect")
def record_inspection_cmd(
    id_: str = typer.Option(..., "--id", help="Inspection ID (e.g. INSP-CSB-2026-001)."),
    target: str = typer.Option(..., "--target", "-t", help="Target vessel name."),
    reg: str = typer.Option(..., "--reg", help="Registration or IMO number."),
    reason: str = typer.Option("ROUTINE_CHECKS", "--reason", "-r", help="ROUTINE_CHECKS, SMUGGLING_CONTRABAND_SUSPICION, STS_ILLEGAL_TRANSFER, FOREIGN_ENCROACHMENT, ENVIRONMENTAL_VIOLATION."),
    coords: str = typer.Option(..., "--coords", help="Geographical coordinates of boarding (e.g. 09°32'N 106°45'E)."),
    inspecting_vessel: str = typer.Option(..., "--by", help="Inspecting Coast Guard vessel ID."),
    flag: str = typer.Option("VNM", "--flag", help="Vessel flag state."),
    violations: bool = typer.Option(False, "--violations", help="Whether statutory violations were detected."),
    fine: float = typer.Option(0.0, "--fine", help="Administrative fine in VND."),
    contraband: str = typer.Option("", "--contraband", help="Description of seized contraband or smuggled oil."),
    date: Optional[str] = typer.Option(None, "--date", help="Inspection date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record a boarding inspection and maritime law enforcement interdiction (Article 13 Law 33/2018/QH14).
    """
    engine = CoastGuardEngine()
    try:
        res = engine.record_inspection(
            inspection_id=id_,
            target_vessel_name=target,
            registration_or_imo=reg,
            flag_state=flag,
            inspection_reason=reason,
            location_coordinates=coords,
            inspecting_vessel_id=inspecting_vessel,
            violations_found=violations,
            fine_amount_vnd=fine,
            contraband_description=contraband,
            inspection_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording maritime inspection:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Biên bản Kiểm tra, Chấp pháp trên Biển", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "fine" in str(k) else str(v))
    console.print(table)


@app.command("iuu")
def report_iuu_cmd(
    id_: str = typer.Option(..., "--id", help="IUU case ID (e.g. IUU-2026-001)."),
    vessel: str = typer.Option(..., "--vessel", "-v", help="Violating fishing vessel registration number (e.g. BV-92345-TS)."),
    owner: str = typer.Option(..., "--owner", "-o", help="Vessel owner or captain name."),
    province: str = typer.Option(..., "--province", "-p", help="Vessel home coastal province."),
    violation: str = typer.Option("VMS_DISCONNECTION", "--violation", help="VMS_DISCONNECTION, CROSSING_MARITIME_BOUNDARY, UNREGISTERED_VESSEL_3_NO, BANNED_FISHING_GEAR."),
    authority: str = typer.Option(..., "--authority", "-a", help="Handling Coast Guard command."),
    penalty: float = typer.Option(0.0, "--penalty", help="Administrative fine in VND."),
    license_revoked: bool = typer.Option(False, "--revoke-license", help="Revocation of master/captain license."),
    impounded: bool = typer.Option(False, "--impound", help="Vessel impoundment."),
    date: Optional[str] = typer.Option(None, "--date", help="Sanction date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record an IUU fishing infringement and statutory sanction (Decree 42/2019/NĐ-CP & EC Yellow Card Action).
    """
    engine = CoastGuardEngine()
    try:
        res = engine.report_iuu_case(
            case_id=id_,
            fishing_vessel_id=vessel,
            owner_or_captain=owner,
            home_province=province,
            violation_type=violation,
            handling_authority=authority,
            penalty_amount_vnd=penalty,
            license_revoked=license_revoked,
            vessel_impounded=impounded,
            sanction_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error reporting IUU case:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Xử phạt Vi phạm Khai thác Hải sản IUU", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "penalty" in str(k) else str(v))
    console.print(table)


@app.command("sar")
def log_sar_cmd(
    id_: str = typer.Option(..., "--id", help="SAR mission ID (e.g. SAR-2026-001)."),
    name: str = typer.Option(..., "--name", "-n", help="SAR mission name."),
    type_: str = typer.Option("VESSEL_DISTRESS_TOW", "--type", "-t", help="VESSEL_DISTRESS_TOW, CREW_MEDICAL_EMERGENCY, SHIPWRECK_SINKING_RESCUE, TYPHOON_EVACUATION_ESCORT."),
    location: str = typer.Option(..., "--location", "-l", help="Distress coordinates or sea area."),
    target: str = typer.Option(..., "--target", help="Involved vessel in distress name/number."),
    responding_vessel: str = typer.Option(..., "--by", help="Responding Coast Guard ship ID."),
    rescued: int = typer.Option(0, "--rescued", help="Number of persons rescued alive."),
    salvaged: bool = typer.Option(True, "--salvaged", help="Whether distressed vessel was towed or salvaged."),
    date: Optional[str] = typer.Option(None, "--date", help="SAR mission date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Log a maritime search and rescue or maritime disaster relief sortie (Article 8 Law 33/2018/QH14).
    """
    engine = CoastGuardEngine()
    try:
        res = engine.log_sar_mission(
            sar_id=id_,
            mission_name=name,
            sar_type=type_,
            distress_location=location,
            involved_vessel_name=target,
            responding_vessel_id=responding_vessel,
            rescued_persons_count=rescued,
            assisted_vessel_salvaged=salvaged,
            mission_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error logging SAR mission:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký Cứu nạn, Cứu hộ trên Biển (SAR)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="vessels, patrols, inspections, iuu, sar, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List Coast Guard vessels, patrols, boarding inspections, IUU crackdowns, and SAR missions.
    """
    engine = CoastGuardEngine()
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
    Get aggregate telemetry metrics on Coast Guard fleet readiness, patrols, and maritime law enforcement.
    """
    engine = CoastGuardEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Hoạt động Lực lượng Cảnh sát biển Việt Nam", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} sub-regions")
        elif isinstance(v, float) and "vnd" in str(k):
            table.add_row(str(k), f"{v:,.0f} VND")
        elif isinstance(v, float) and "nautical" in str(k):
            table.add_row(str(k), f"{v:,.1f} NM")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
