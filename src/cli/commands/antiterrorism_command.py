"""
CLI command group for Vietnamese Anti-Terrorism, Homeland Security & Target Protection Suite.
Governed by Law on Anti-Terrorism 2013 (Law No. 28/2013/QH13) & Decree No. 07/2014/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.antiterrorism_engine import (
    VALID_PROTECTION_LEVELS,
    VALID_TACTICAL_SCENARIOS,
    VALID_TARGET_CATEGORIES,
    VALID_TARGET_STATUSES,
    VALID_THREAT_LEVELS,
    VALID_THREAT_TYPES,
    AntiTerrorismEngine,
)

app = typer.Typer(
    name="antiterrorism",
    help="Vietnamese Anti-Terrorism & Target Protection Suite (Law 28/2013/QH13 & Decree 07/2014/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def antiterrorism_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Homeland Security, Protected Targets, Threat Alerts, and Terrorist Asset Freezes.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = AntiTerrorismEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    funds_str = f"{telemetry['total_frozen_funds_vnd']:,.0f} VND"
    alert_color = "green" if telemetry["active_threat_alerts"] == 0 else "yellow" if telemetry["active_threat_alerts"] < 3 else "red"

    overview_text = (
        f"[bold cyan]Total Protected Targets (Mục tiêu trọng yếu ANQG):[/bold cyan] {telemetry['total_protected_targets']}\n"
        f"[bold cyan]Active Threat Alerts (Cảnh báo nguy cơ khủng bố):[/bold cyan] [{alert_color}]{telemetry['active_threat_alerts']}[/{alert_color}]\n"
        f"[bold cyan]Contingency Emergency Plans (Phương án tác chiến):[/bold cyan] {telemetry['total_emergency_plans']}\n"
        f"[bold cyan]Designated Terrorist Entities (Tổ chức/cá nhân khủng bố):[/bold cyan] {telemetry['designated_terrorist_entities']}\n"
        f"[bold cyan]Frozen Accounts / Funds (Tài khoản & tài sản bị phong tỏa):[/bold cyan] {telemetry['total_frozen_accounts']} ({funds_str})\n"
        f"[bold cyan]Tactical Operations Conducted (Chiến dịch tác chiến):[/bold cyan] {telemetry['tactical_operations_count']}\n"
        f"[bold cyan]Hostages Rescued / Suspects Neutralized:[/bold cyan] [bold green]{telemetry['hostages_rescued']}[/bold green] rescued / "
        f"[bold yellow]{telemetry['suspects_neutralized']}[/bold yellow] neutralized"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]BỘ CHỈ HUY TÁC CHIẾN PHÒNG CHỐNG KHỦNG BỐ & BẢO VỆ MỤC TIÊU (LUẬT 28/2013/QH13)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    targets_status = telemetry.get("targets_by_status", {})
    if targets_status:
        target_table = Table(title="Trạng thái an ninh các mục tiêu trọng yếu", box=box.SIMPLE_HEAVY)
        target_table.add_column("Status", style="cyan")
        target_table.add_column("Count", justify="right", style="green")
        for st, count in targets_status.items():
            target_table.add_row(st, str(count))
        console.print(target_table)


@app.command("target")
def register_target_cmd(
    id_: str = typer.Option(..., "--id", help="Target ID (e.g. TGT-BCA-01)."),
    name: str = typer.Option(..., "--name", "-n", help="Target official name."),
    category: str = typer.Option("POLITICAL_HEADQUARTERS", "--category", "-c", help="POLITICAL_HEADQUARTERS, CRITICAL_INFRASTRUCTURE, FINANCIAL_COMMUNICATION_HUB, DIPLOMATIC_MISSION, MILITARY_DEFENSE_INSTALLATION."),
    level: str = typer.Option("SPECIAL_CLASS", "--level", "-l", help="SPECIAL_CLASS, CLASS_I, CLASS_II."),
    guard: str = typer.Option(..., "--guard", "-g", help="Guard command force (e.g. Bộ Tư lệnh Cảnh vệ K01)."),
    address: str = typer.Option(..., "--address", "-a", help="Location address."),
    perimeter: float = typer.Option(100.0, "--perimeter", "-p", help="Security cordon radius in meters."),
    status: str = typer.Option("SECURE", "--status", "-s", help="SECURE, HEIGHTENED_ALERT, LOCKED_DOWN, THREAT_DETECTED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a vital national security target under Decree 37/2009/NĐ-CP.
    """
    engine = AntiTerrorismEngine()
    try:
        res = engine.register_target(
            target_id=id_,
            target_name=name,
            target_category=category,
            protection_level=level,
            guard_force=guard,
            location_address=address,
            security_perimeter_meters=perimeter,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering target:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký mục tiêu trọng yếu an ninh quốc gia thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} m" if "perimeter" in str(k) else str(v))
    console.print(table)


@app.command("alert")
def issue_threat_alert_cmd(
    id_: str = typer.Option(..., "--id", help="Alert ID (e.g. ALERT-2026-001)."),
    source: str = typer.Option(..., "--source", "-s", help="Threat origin or intelligence source."),
    type_: str = typer.Option("ARMED_ATTACK", "--type", "-t", help="ARMED_ATTACK, BOMB_EXPLOSIVE_CBRN, CYBER_TERRORISM, HOSTAGE_HIJACKING, INFRASTRUCTURE_SABOTAGE."),
    level: str = typer.Option("SUBSTANTIAL_YELLOW", "--level", "-l", help="ELEVATED_BLUE, SUBSTANTIAL_YELLOW, SEVERE_ORANGE, CRITICAL_RED."),
    summary: str = typer.Option(..., "--summary", help="Intelligence summary and threat analysis."),
    targets: Optional[str] = typer.Option(None, "--targets", help="Comma-separated target IDs affected."),
    date: Optional[str] = typer.Option(None, "--date", help="Issuance date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue a formal terrorism threat warning pursuant to Law 28/2013/QH13.
    """
    engine = AntiTerrorismEngine()
    affected = [t.strip() for t in targets.split(",")] if targets else []
    try:
        res = engine.issue_threat_alert(
            alert_id=id_,
            threat_source=source,
            threat_type=type_,
            threat_level=level,
            intelligence_summary=summary,
            affected_targets=affected,
            issued_at=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing threat alert:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Phát lệnh cảnh báo nguy cơ khủng bố", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("plan")
def register_emergency_plan_cmd(
    id_: str = typer.Option(..., "--id", help="Plan ID (e.g. PLAN-CT-001)."),
    target_id: str = typer.Option(..., "--target-id", "-t", help="Target ID."),
    name: str = typer.Option(..., "--name", "-n", help="Plan name."),
    scenario: str = typer.Option("HOSTAGE_RESCUE", "--scenario", "-s", help="HOSTAGE_RESCUE, BOMB_DISPOSAL_EOD, CBRN_DECONTAMINATION, AIR_SPACE_INTERCEPTION, CYBER_COUNTERMEASURE."),
    agency: str = typer.Option(..., "--agency", "-a", help="Lead command agency."),
    units: Optional[str] = typer.Option(None, "--units", help="Comma-separated participating units."),
    drill: Optional[str] = typer.Option(None, "--drill", help="Last drill date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a counter-terrorism contingency battle plan for a critical target.
    """
    engine = AntiTerrorismEngine()
    unit_list = [u.strip() for u in units.split(",")] if units else []
    try:
        res = engine.register_emergency_plan(
            plan_id=id_,
            target_id=target_id,
            plan_name=name,
            tactical_scenario=scenario,
            lead_command_agency=agency,
            participating_units=unit_list,
            last_drill_date=drill,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering emergency plan:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Phê duyệt phương án tác chiến phòng chống khủng bố", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("designate")
def designate_entity_cmd(
    id_: str = typer.Option(..., "--id", help="Entity ID (e.g. TERR-001)."),
    name: str = typer.Option(..., "--name", "-n", help="Organization or individual name."),
    type_: str = typer.Option("ORGANIZATION", "--type", "-t", help="ORGANIZATION or INDIVIDUAL."),
    decision: str = typer.Option(..., "--decision", "-d", help="Designation decision document number."),
    aliases: Optional[str] = typer.Option(None, "--aliases", help="Comma-separated aliases."),
    date: Optional[str] = typer.Option(None, "--date", help="Designation date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Designate a terrorist entity subject to immediate asset freeze (Article 34 Law 28/2013/QH13).
    """
    engine = AntiTerrorismEngine()
    alias_list = [a.strip() for a in aliases.split(",")] if aliases else []
    try:
        res = engine.designate_terrorist_entity(
            entity_id=id_,
            entity_name=name,
            entity_type=type_,
            designation_decision=decision,
            designation_date=date,
            aliases=alias_list,
        )
    except Exception as e:
        console.print(f"[bold red]Error designating entity:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ định danh sách tổ chức/cá nhân khủng bố (Lệnh phong tỏa tài sản)", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("freeze")
def record_freeze_cmd(
    id_: str = typer.Option(..., "--id", help="Terrorist entity ID."),
    accounts: int = typer.Option(..., "--accounts", "-a", help="Number of bank accounts frozen."),
    amount: float = typer.Option(..., "--amount", help="Amount of funds frozen in VND."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record execution of terrorist asset and bank account freeze.
    """
    engine = AntiTerrorismEngine()
    try:
        res = engine.record_asset_freeze(
            entity_id=id_,
            accounts_count=accounts,
            frozen_amount_vnd=amount,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording asset freeze:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Xác nhận thực hiện phong tỏa tài khoản khủng bố", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "vnd" in str(k) else str(v))
    console.print(table)


@app.command("operate")
def log_operation_cmd(
    id_: str = typer.Option(..., "--id", help="Operation ID (e.g. OP-2026-001)."),
    alert_id: str = typer.Option(..., "--alert-id", "-a", help="Alert ID."),
    target_id: str = typer.Option(..., "--target-id", "-t", help="Target ID."),
    action: str = typer.Option(..., "--action", help="Tactical action executed."),
    officer: str = typer.Option(..., "--officer", "-o", help="Commanding officer name."),
    hostages: int = typer.Option(0, "--hostages", help="Hostages rescued."),
    neutralized: int = typer.Option(0, "--neutralized", help="Suspects neutralized."),
    status: str = typer.Option("RESOLVED_SUCCESS", "--status", "-s", help="IN_PROGRESS, RESOLVED_SUCCESS, STAND_DOWN."),
    date: Optional[str] = typer.Option(None, "--date", help="Operation date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Log an active tactical counter-terrorism operation or hostage rescue mission.
    """
    engine = AntiTerrorismEngine()
    try:
        res = engine.log_tactical_operation(
            operation_id=id_,
            alert_id=alert_id,
            target_id=target_id,
            tactical_action=action,
            commanding_officer=officer,
            hostages_rescued=hostages,
            suspects_neutralized=neutralized,
            outcome_status=status,
            operation_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error logging tactical operation:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Nhật ký tác chiến chống khủng bố", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="targets, alerts, plans, sanctions, operations, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List protected targets, alerts, emergency plans, sanctions, and operations.
    """
    engine = AntiTerrorismEngine()
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
    Get aggregate telemetry metrics on homeland security and counter-terrorism readiness.
    """
    engine = AntiTerrorismEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Sẵn sàng Tác chiến Phòng chống Khủng bố", box=box.ROUNDED)
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
