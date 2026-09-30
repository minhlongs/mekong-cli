"""
CLI command group for Vietnamese Civil Defense, Disaster Mitigation & National Emergency Response Suite.
Governed by Law on Civil Defense 2023 (Law No. 18/2023/QH15) & Decree No. 02/2024/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.civildefense_engine import (
    VALID_ALERT_LEVELS,
    VALID_DISASTER_CATEGORIES,
    VALID_DRILL_TYPES,
    VALID_FORCE_TYPES,
    VALID_SHELTER_STATUS,
    VALID_SHELTER_TYPES,
    CivilDefenseEngine,
)

app = typer.Typer(
    name="civildefense",
    help="Vietnamese Civil Defense & Emergency Response Suite (Law 18/2023/QH15 & Decree 02/2024/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def civildefense_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Civil Defense Readiness, Shelters, Mobilized Forces, and Emergency Alerts.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = CivilDefenseEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    evac_str = f"{telemetry['total_evacuation_capacity']:,} persons"
    shelter_str = f"{telemetry['total_shelter_capacity_persons']:,} persons"
    men_str = f"{telemetry['total_mobilized_personnel']:,} officers/troops"

    overview_text = (
        f"[bold cyan]Active Civil Defense Plans (Kế hoạch PTDS đã phê duyệt):[/bold cyan] {telemetry['active_civil_plans']} plans (Evacuation cap: [bold green]{evac_str}[/bold green])\n"
        f"[bold cyan]Ready Underground & Public Shelters (Công trình, hầm trú ẩn sẵn sàng):[/bold cyan] {telemetry['operational_ready_shelters']} shelters (Capacity: [bold green]{shelter_str}[/bold green])\n"
        f"[bold cyan]Mobilized Response Units (Lực lượng PTDS cơ động):[/bold cyan] {telemetry['mobilized_force_units']} units ({men_str}, {telemetry['total_specialized_vehicles']} vehicles)\n"
        f"[bold cyan]Completed Emergency Drills (Diễn tập thực binh & chỉ huy):[/bold cyan] {telemetry['total_emergency_drills']} drills (Avg Score: [bold green]{telemetry['average_drill_score']}/100[/bold green])\n"
        f"[bold cyan]Active Emergency Alerts (Cảnh báo thảm họa cấp 1-4):[/bold cyan] {len(telemetry['active_alerts_by_level'])} alert levels active"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]BAN CHỈ ĐẠO PHÒNG THỦ DÂN SỰ QUỐC GIA — HỆ THỐNG ĐIỀU HÀNH TÁC CHIẾN & KHẨN CẤP (LUẬT 18/2023/QH15)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    alerts_by_level = telemetry.get("active_alerts_by_level", {})
    if alerts_by_level:
        alert_table = Table(title="Tình trạng Báo động Phòng thủ Dân sự theo Cấp độ (Điều 20)", box=box.SIMPLE_HEAVY)
        alert_table.add_column("Alert Level (Cấp độ)", style="cyan")
        alert_table.add_column("Active Incidents", justify="right", style="red")
        for lvl, cnt in alerts_by_level.items():
            alert_table.add_row(lvl, str(cnt))
        console.print(alert_table)


@app.command("plan")
def register_plan_cmd(
    id_: str = typer.Option(..., "--id", help="Plan ID (e.g. PLAN-CD-HN-2026)."),
    name: str = typer.Option(..., "--name", "-n", help="Official civil defense plan name."),
    category: str = typer.Option("WAR_CONFLICT", "--category", "-c", help="WAR_CONFLICT, NUCLEAR_RADIATION, CHEMICAL_TOXIC, BIOLOGICAL_PANDEMIC, CATACLYSMIC_GEOHAZARD."),
    scope: str = typer.Option(..., "--scope", "-s", help="Jurisdiction scope (e.g. Thành phố Hà Nội, Toàn quốc)."),
    body: str = typer.Option(..., "--body", "-b", help="Commanding body (e.g. UBND Thành phố Hà Nội, BCH Quân sự)."),
    capacity: int = typer.Option(1000, "--capacity", help="Evacuation population capacity."),
    supplies: int = typer.Option(14, "--supplies", help="Essential food/medical supplies reserve days."),
    date: Optional[str] = typer.Option(None, "--date", help="Approval date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register or update a civil defense readiness plan (Article 13 Law 18/2023/QH15).
    """
    engine = CivilDefenseEngine()
    try:
        res = engine.register_plan(
            plan_id=id_,
            plan_name=name,
            category=category,
            jurisdiction_scope=scope,
            commanding_body=body,
            evacuation_capacity=capacity,
            essential_supplies_days=supplies,
            approved_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering civil defense plan:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Phê duyệt Kế hoạch Phòng thủ Dân sự thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("alert")
def issue_alert_cmd(
    id_: str = typer.Option(..., "--id", help="Alert ID (e.g. ALERT-CD-2026-001)."),
    category: str = typer.Option("CATACLYSMIC_GEOHAZARD", "--category", "-c", help="WAR_CONFLICT, NUCLEAR_RADIATION, CHEMICAL_TOXIC, BIOLOGICAL_PANDEMIC, CATACLYSMIC_GEOHAZARD."),
    level: str = typer.Option("LEVEL_2_PROVINCIAL", "--level", "-l", help="LEVEL_1_DISTRICT, LEVEL_2_PROVINCIAL, LEVEL_3_REGIONAL, LEVEL_4_NATIONAL."),
    region: str = typer.Option(..., "--region", "-r", help="Affected geographical region or coordinates."),
    authority: str = typer.Option(..., "--authority", "-a", help="Declaring authority (e.g. Thủ tướng Chính phủ, Chủ tịch UBND)."),
    evacuation: bool = typer.Option(False, "--evacuation", help="Whether mandatory evacuation is ordered."),
    actions: str = typer.Option(..., "--actions", help="Immediate response directives and mobilization measures."),
    date: Optional[str] = typer.Option(None, "--date", help="Declared date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue or escalate a civil defense alert level (Article 20 Law 18/2023/QH15).
    """
    engine = CivilDefenseEngine()
    try:
        res = engine.issue_alert(
            alert_id=id_,
            disaster_category=category,
            alert_level=level,
            affected_region=region,
            declaring_authority=authority,
            evacuation_ordered=evacuation,
            immediate_response_actions=actions,
            declared_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing civil defense alert:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Ban bố Cấp độ Phòng thủ Dân sự (Điều 20)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("shelter")
def register_shelter_cmd(
    id_: str = typer.Option(..., "--id", help="Shelter ID (e.g. SHELTER-HN-001)."),
    name: str = typer.Option(..., "--name", "-n", help="Shelter or bunker name."),
    type_: str = typer.Option("UNDERGROUND_BUNKER_SPECIALIZED", "--type", "-t", help="UNDERGROUND_BUNKER_SPECIALIZED, DUAL_USE_SUBWAY_BASEMENT, HARDENED_PUBLIC_SHELTER, MOBILE_FIELD_SHELTER."),
    address: str = typer.Option(..., "--address", "-a", help="Physical location address or coordinates."),
    capacity: int = typer.Option(500, "--capacity", help="Shelter capacity in persons."),
    filtration: bool = typer.Option(False, "--filtration", help="Equipped with specialized air filtration/ventilation."),
    cbrn: str = typer.Option("STANDARD", "--cbrn", help="CBRN chemical/radiological protection rating."),
    status: str = typer.Option("OPERATIONAL_READY", "--status", help="OPERATIONAL_READY, STANDBY_MAINTENANCE, RENOVATING, DECOMMISSIONED."),
    date: Optional[str] = typer.Option(None, "--date", help="Last technical inspection date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register and certify a civil defense shelter or bunker (Article 27 Law 18/2023/QH15).
    """
    engine = CivilDefenseEngine()
    try:
        res = engine.register_shelter(
            shelter_id=id_,
            shelter_name=name,
            shelter_type=type_,
            location_address=address,
            capacity_persons=capacity,
            air_filtration_equipped=filtration,
            cbrn_protection_level=cbrn,
            status=status,
            last_inspected_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering civil defense shelter:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Công trình Tránh trú Phòng thủ Dân sự", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("force")
def deploy_force_cmd(
    id_: str = typer.Option(..., "--id", help="Deployment ID (e.g. FORCE-DEP-01)."),
    unit: str = typer.Option(..., "--unit", "-u", help="Military / Police / Militia unit name."),
    type_: str = typer.Option("MILITARY_CORE_UNIT", "--type", "-t", help="MILITARY_CORE_UNIT, POLICE_RESCUE_UNIT, MILITIA_SELF_DEFENSE, COMMUNITY_SHOCK_TEAM, SPECIALIZED_ENGINEER_CORPS."),
    base: str = typer.Option(..., "--base", "-b", help="Stationed barracks / base location."),
    personnel: int = typer.Option(50, "--personnel", help="Active personnel headcount."),
    vehicles: int = typer.Option(5, "--vehicles", help="Specialized vehicles / equipment count."),
    readiness: float = typer.Option(1.0, "--readiness", help="Mobilization readiness time in hours."),
    officer: str = typer.Option(..., "--officer", help="Commanding contact officer."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Mobilize and deploy specialized civil defense response forces (Article 35 Law 18/2023/QH15).
    """
    engine = CivilDefenseEngine()
    try:
        res = engine.deploy_force(
            deployment_id=id_,
            unit_name=unit,
            force_type=type_,
            stationed_base=base,
            personnel_count=personnel,
            specialized_vehicles_count=vehicles,
            readiness_hours=readiness,
            contact_officer=officer,
        )
    except Exception as e:
        console.print(f"[bold red]Error mobilizing civil defense force:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Huy động Lực lượng Phòng thủ Dân sự Cơ động", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.1f} hrs" if "readiness" in str(k) else str(v))
    console.print(table)


@app.command("drill")
def log_drill_cmd(
    id_: str = typer.Option(..., "--id", help="Drill ID (e.g. DRILL-PTDS-2026-01)."),
    code: str = typer.Option(..., "--code", "-c", help="Official drill exercise code (e.g. PT-26)."),
    name: str = typer.Option(..., "--name", "-n", help="Full exercise name."),
    type_: str = typer.Option("COMBINED_FULL_SCALE", "--type", "-t", help="TABLETOP_COMMAND_DRILL, FIELD_EVACUATION_DRILL, HAZMAT_CBRN_DRILL, COMBINED_FULL_SCALE."),
    agency: str = typer.Option(..., "--agency", "-a", help="Organizing / supervising agency."),
    participants: int = typer.Option(100, "--participants", help="Number of participants."),
    duration: float = typer.Option(8.0, "--duration", help="Exercise duration in hours."),
    date: Optional[str] = typer.Option(None, "--date", help="Drill date (YYYY-MM-DD)."),
    score: float = typer.Option(85.0, "--score", help="Evaluation score (0.0 - 100.0)."),
    notes: str = typer.Option("", "--notes", help="Deficiencies notes and lessons learned."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record civil defense emergency drills and preparedness exercises (Article 18 Law 18/2023/QH15).
    """
    engine = CivilDefenseEngine()
    try:
        res = engine.log_drill(
            drill_id=id_,
            drill_code=code,
            drill_name=name,
            drill_type=type_,
            organizing_agency=agency,
            participants_count=participants,
            duration_hours=duration,
            drill_date=date,
            evaluation_score=score,
            deficiencies_notes=notes,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording civil defense drill:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký Diễn tập Phòng thủ Dân sự", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.1f}/100" if "score" in str(k) else str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="plans, alerts, shelters, forces, drills, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List civil defense plans, alerts, shelters, forces, and emergency drills.
    """
    engine = CivilDefenseEngine()
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
    Get aggregate telemetry metrics on national civil defense readiness and response posture.
    """
    engine = CivilDefenseEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Sẵn sàng Phòng thủ Dân sự Quốc gia", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} sub-categories")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
