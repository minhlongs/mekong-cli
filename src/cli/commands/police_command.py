"""
CLI command group for Vietnamese People's Public Security & Grassroots Security Forces Suite.
Governed by:
- Law on People's Public Security 2018 (Law No. 37/2018/QH14) as amended by Law No. 21/2023/QH15
- Law on Forces Participating in Safeguarding Security and Order at the Grassroots Level 2023 (Law No. 30/2023/QH15)
- Decree No. 40/2024/NĐ-CP & Circular No. 14/2024/TT-BCA
- Law on Residence 2020 (Law No. 68/2020/QH15)
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.police_engine import (
    VALID_GEAR_TYPES,
    VALID_INCIDENT_SEVERITIES,
    VALID_INCIDENT_TYPES,
    VALID_OFFICER_STATUS,
    VALID_PATROL_TYPES,
    VALID_POLICE_RANKS,
    VALID_RESIDENCE_COMPLIANCE,
    VALID_RESOLUTION_STATUS,
    VALID_SPECIALIZATIONS,
    VALID_TEAM_STATUS,
    PoliceEngine,
)

app = typer.Typer(
    name="police",
    help="Vietnamese People's Public Security & Grassroots Security Forces Suite (Luật CAND & Luật Lực lượng tham gia bảo vệ ANTT ở cơ sở).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def police_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of People's Public Security, Grassroots Security Teams, Incident Triage & Patrols.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = PoliceEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    crit_color = "green" if telemetry["open_critical_emergencies"] == 0 else "red"

    overview_text = (
        f"[bold cyan]Active-Duty Police Officers (Cán bộ, Chiến sĩ CAND thường trực):[/bold cyan] {telemetry['active_duty_officers']} officers\n"
        f"[bold cyan]Grassroots Security Teams (Lực lượng tham gia bảo vệ ANTT ở cơ sở - Luật 30/2023):[/bold cyan] {telemetry['active_grassroots_teams']} teams ([green]{telemetry['grassroots_personnel_count']} members deployed[/green])\n"
        f"[bold cyan]Public Security Incidents (Vụ việc an ninh trật tự tiếp nhận / xử lý):[/bold cyan] {telemetry['total_security_incidents']} cases ([{crit_color}]{telemetry['open_critical_emergencies']} open critical emergencies[/{crit_color}])\n"
        f"[bold cyan]Joint Patrol Missions (Nhiệm vụ tuần tra liên quân địa bàn - TT 14/2024):[/bold cyan] {telemetry['total_patrol_missions']} patrols ([yellow]{telemetry['patrol_persons_checked']} persons checked[/yellow], [red]{telemetry['patrol_infractions_detected']} infractions[/red])\n"
        f"[bold cyan]Household Residence Inspections (Kiểm tra hành chính cư trú - Luật Cư trú 2020):[/bold cyan] {telemetry['total_residence_checks']} checks ([bold green]{telemetry['residence_compliance_rate_percent']}% compliance rate[/bold green])"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold red]BỘ CÔNG AN — HỆ THỐNG QUẢN LÝ AN NINH TRẬT TỰ & LỰC LƯỢNG BẢO VỆ CƠ SỞ[/bold red]",
            box=box.ROUNDED,
            border_style="red",
        )
    )


@app.command("officer")
def register_officer_cmd(
    badge: str = typer.Option(..., "--badge", "-b", help="Officer badge number (e.g. BCA-CAND-012345)."),
    name: str = typer.Option(..., "--name", "-n", help="Officer full name."),
    rank: str = typer.Option("DAI_UY", "--rank", "-r", help="Police rank (e.g. THIEU_UY, TRUNG_UY, THUONG_UY, DAI_UY, THIEU_TA, TRUNG_TA, THUONG_TA, DAI_TA)."),
    position: str = typer.Option(..., "--position", "-p", help="Officer position/title (e.g. Cảnh sát khu vực, Trưởng Công an Xã)."),
    unit: str = typer.Option(..., "--unit", "-u", help="Command unit name (e.g. Công an Phường Bến Nghé, Quận 1)."),
    spec: str = typer.Option("CANH_SAT_QLHC_TTXH", "--spec", help="Specialization division."),
    status: str = typer.Option("ON_DUTY_ACTIVE", "--status", help="ON_DUTY_ACTIVE, STANDBY_RESERVE, SPECIAL_MISSION, RETIRED_DISCHARGED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register an officer of the People's Public Security (Law on People's Public Security 2018).
    """
    engine = PoliceEngine()
    try:
        res = engine.register_officer(
            officer_badge=badge,
            full_name=name,
            rank=rank,
            position=position,
            unit_name=unit,
            specialization=spec,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering police officer:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký Cán bộ Chiến sĩ Công an Nhân dân", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("team")
def register_team_cmd(
    id_: str = typer.Option(..., "--id", help="Grassroots security team ID (e.g. GR-TEAM-Q1-TDP05)."),
    name: str = typer.Option(..., "--name", "-n", help="Team designation name (e.g. Tổ Bảo vệ ANTT Tổ dân phố 5)."),
    ward: str = typer.Option(..., "--ward", "-w", help="Ward / Commune name (Phường / Xã)."),
    district: str = typer.Option(..., "--district", "-d", help="District / County name (Quận / Huyện / TP thuộc tỉnh)."),
    city: str = typer.Option("TP. Hồ Chí Minh", "--city", "-c", help="Province or centrally governed city."),
    leader: str = typer.Option(..., "--leader", "-l", help="Team leader name (Tổ trưởng)."),
    members: int = typer.Option(3, "--members", "-m", help="Total team member count (min 3 under Article 14 Law 30/2023)."),
    gear: str = typer.Option("STANDARD_SUPPORT_GEAR", "--gear", help="STANDARD_SUPPORT_GEAR, ENHANCED_PATROL_KIT, FULL_EQUIPMENT_SPEC."),
    status: str = typer.Option("ACTIVE_DEPLOYED", "--status", help="ACTIVE_DEPLOYED, TRAINING_PHASE, STANDBY_STATIONARY."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a grassroots security team under Law No. 30/2023/QH15 and Decree No. 40/2024/NĐ-CP.
    """
    engine = PoliceEngine()
    try:
        res = engine.register_grassroots_team(
            team_id=id_,
            team_name=name,
            ward_commune=ward,
            district_county=district,
            province_city=city,
            team_leader_name=leader,
            member_count=members,
            equipped_gear=gear,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering grassroots security team:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Thành lập Tổ Bảo vệ An ninh, Trật tự ở Cơ sở (Luật 30/2023/QH15)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("incident")
def report_incident_cmd(
    id_: str = typer.Option(..., "--id", help="Incident ID (e.g. INC-POLICE-2026-001)."),
    type_: str = typer.Option("PUBLIC_DISORDER", "--type", "-t", help="PUBLIC_DISORDER, PROPERTY_THEFT_BURGLARY, DOMESTIC_VIOLENCE, ILLEGAL_GAMBLING, DRUG_RELATED_ACTIVITY, CYBER_FRAUD_COMPLAINT, RESIDENCE_LAW_VIOLATION."),
    location: str = typer.Option(..., "--location", "-l", help="Specific incident scene address."),
    ward: str = typer.Option(..., "--ward", "-w", help="Ward / Commune name."),
    reporter: str = typer.Option(..., "--reporter", help="Reporting citizen name or surveillance trigger."),
    unit: str = typer.Option(..., "--unit", "-u", help="Assigned handling police station / team."),
    severity: str = typer.Option("MEDIUM_INVESTIGATION", "--severity", "-s", help="CRITICAL_EMERGENCY, HIGH_PRIORITY, MEDIUM_INVESTIGATION, LOW_COMMUNITY_MEDIATION."),
    status: str = typer.Option("REPORTED_DISPATCHED", "--status", help="REPORTED_DISPATCHED, INVESTIGATING_ON_SCENE, RESOLVED_CLOSED, TRANSFERRED_PROSECUTION."),
    date: Optional[str] = typer.Option(None, "--date", help="Incident date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Report a public security or social order incident (Article 16 Law 37/2018 & Law 30/2023).
    """
    engine = PoliceEngine()
    try:
        res = engine.report_incident(
            incident_id=id_,
            incident_type=type_,
            location=location,
            ward_commune=ward,
            reported_by=reporter,
            assigned_unit=unit,
            severity=severity,
            resolution_status=status,
            incident_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error reporting security incident:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Tiếp nhận & Xử lý Vụ việc An ninh Trật tự", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("patrol")
def log_patrol_cmd(
    id_: str = typer.Option(..., "--id", help="Patrol mission ID (e.g. PATROL-2026-001)."),
    type_: str = typer.Option("JOINT_POLICE_GRASSROOTS", "--type", "-t", help="JOINT_POLICE_GRASSROOTS, NIGHT_ROUTINE_SECURITY, CRIME_HOTSPOT_SWEEP, HOLIDAY_EVENT_PROTECTION."),
    route: str = typer.Option(..., "--route", "-r", help="Patrol route, quarter, or surveillance zone."),
    badge: str = typer.Option(..., "--badge", "-b", help="Lead police officer badge number."),
    team: str = typer.Option(..., "--team", help="Participating grassroots security team ID."),
    start: Optional[str] = typer.Option(None, "--start", help="Start timestamp (ISO format)."),
    end: Optional[str] = typer.Option(None, "--end", help="End timestamp (ISO format)."),
    checked: int = typer.Option(0, "--checked", help="Number of suspicious persons/vehicles checked."),
    infractions: int = typer.Option(0, "--infractions", help="Number of infractions/violations detected."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Log a joint security patrol mission (Circular 14/2024/TT-BCA).
    """
    engine = PoliceEngine()
    try:
        res = engine.log_patrol_mission(
            mission_id=id_,
            patrol_type=type_,
            route_or_zone=route,
            lead_officer_badge=badge,
            grassroots_team_id=team,
            start_time=start,
            end_time=end,
            persons_checked=checked,
            infractions_detected=infractions,
        )
    except Exception as e:
        console.print(f"[bold red]Error logging patrol mission:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký Tuần tra Kiểm soát Địa bàn (Thông tư 14/2024/TT-BCA)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("residence")
def record_residence_cmd(
    id_: str = typer.Option(..., "--id", help="Residence check ID (e.g. RES-2026-001)."),
    address: str = typer.Option(..., "--address", "-a", help="Inspected domicile address."),
    head: str = typer.Option(..., "--head", help="Household head or host name (Chủ hộ / Đại diện cơ sở)."),
    badge: str = typer.Option(..., "--badge", "-b", help="Inspecting police officer badge number."),
    registered: int = typer.Option(1, "--registered", help="Registered permanent/temporary residents count."),
    present: int = typer.Option(1, "--present", help="Actual persons present during inspection."),
    temp_stay: bool = typer.Option(True, "--temp-stay/--no-temp-stay", help="Whether temporary stay notification was filed."),
    violating: int = typer.Option(0, "--violating", help="Number of persons with residence law violations."),
    date: Optional[str] = typer.Option(None, "--date", help="Check date (YYYY-MM-DD)."),
    compliance: str = typer.Option("COMPLIANT_VERIFIED", "--compliance", help="COMPLIANT_VERIFIED, IRREGULARITIES_NOTICE_ISSUED, FINES_PROPOSED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record an administrative household residence and temporary stay inspection (Law on Residence 2020).
    """
    engine = PoliceEngine()
    try:
        res = engine.record_residence_check(
            check_id=id_,
            address=address,
            household_head_name=head,
            inspecting_officer_badge=badge,
            registered_residents_count=registered,
            actual_present_count=present,
            temporary_stay_verified=temp_stay,
            violating_persons_count=violating,
            check_date=date,
            compliance_status=compliance,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording residence check:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Biên bản Kiểm tra Hành chính Cư trú (Luật Cư trú 2020)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="officers, teams, incidents, patrols, residence, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List records across officers, grassroots teams, incidents, patrols, and residence checks.
    """
    engine = PoliceEngine()
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
    Get aggregate telemetry metrics on People's Public Security and Grassroots Security forces.
    """
    engine = PoliceEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Vận hành Lực lượng Công an Nhân dân & Bảo vệ ANTT Cơ sở", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if "percent" in str(k):
            table.add_row(str(k), f"{v}%")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
