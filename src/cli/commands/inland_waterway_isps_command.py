"""CLI Commands for Inland Waterway, Feeder Barging, Maritime SAR & ISPS Security (Phases 187-190).

Provides Typer commands:
- mekong waterway / duongthuy (clearance)
- mekong barge / salan (freight)
- mekong sar / cuunan (datum, wreck)
- mekong isps / anninhcang (compliance)
"""

import dataclasses
import enum
import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.inland_waterway_isps_engine import (
    WaterwayClass,
    FeederBargeRoute,
    SARRegion,
    ISPSLevel,
    InlandWaterwayNavEngine,
    FeederBargingFreightEngine,
    MaritimeSARWreckEngine,
    PortFacilitySecurityISPSEngine,
)

console = Console()

waterway_app = typer.Typer(
    name="waterway",
    help="Phases 187-190: Inland Waterway navigation, bridge clearance & fairway depth.",
    no_args_is_help=True,
)

barge_app = typer.Typer(
    name="barge",
    help="Phase 188: Container feeder barging tariffs & Mekong transit freight.",
    no_args_is_help=True,
)

sar_app = typer.Typer(
    name="sar",
    help="Phase 189: Maritime Search & Rescue (SAR) datum box & wreck removal deadlines.",
    no_args_is_help=True,
)

isps_app = typer.Typer(
    name="isps",
    help="Phase 190: Port Facility & Ship Security (ISPS Code) compliance evaluator.",
    no_args_is_help=True,
)


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    if dataclasses.is_dataclass(obj):
        data = dataclasses.asdict(obj)
    elif hasattr(obj, "__dict__"):
        data = obj.__dict__
    else:
        data = obj
    print(json.dumps(data, indent=2, default=_json_serial))


# ---------------------------------------------------------------------------
# Waterway Commands (Phase 187)
# ---------------------------------------------------------------------------


@waterway_app.command("clearance")
def waterway_clearance(
    vessel_name: str = typer.Argument("Barge SG-8899", help="Vessel / Barge name"),
    waterway_class: str = typer.Option("CLASS_I", "--class", "-c", help="Waterway class (SPECIAL, CLASS_I to VI)"),
    bridge_name: str = typer.Option("Binh Loi Bridge", "--bridge", "-b", help="Bridge name"),
    bridge_air_draft: float = typer.Option(10.0, "--bridge-air", help="Bridge air draft height in meters"),
    vessel_air_draft: float = typer.Option(8.2, "--vessel-air", help="Vessel air draft height in meters"),
    channel_depth: float = typer.Option(4.5, "--channel-depth", help="Channel water depth in meters"),
    vessel_draft: float = typer.Option(3.2, "--vessel-draft", help="Vessel actual draft in meters"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Assess bridge air draft clearance and channel Under Keel Clearance (UKC)."""
    try:
        w_class = WaterwayClass(waterway_class.upper())
    except ValueError:
        w_class = WaterwayClass.CLASS_I

    res = InlandWaterwayNavEngine.evaluate_clearance(
        vessel_name=vessel_name,
        waterway_class=w_class,
        bridge_name=bridge_name,
        bridge_air_draft_m=bridge_air_draft,
        vessel_air_draft_m=vessel_air_draft,
        channel_depth_m=channel_depth,
        vessel_draft_m=vessel_draft,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"Inland Waterway Clearance Assessment — {vessel_name}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Waterway Class", res.waterway_class.value)
    table.add_row("Bridge Target", res.bridge_name)
    table.add_row("Bridge Air Draft", f"{res.bridge_air_draft_m:.2f} m")
    table.add_row("Vessel Air Draft", f"{res.vessel_air_draft_m:.2f} m")
    table.add_row("Net Air Clearance", f"{res.net_air_clearance_m:.2f} m ({'SAFE' if res.is_air_draft_safe else 'DANGER'})")
    table.add_row("Channel Depth", f"{res.channel_depth_m:.2f} m")
    table.add_row("Vessel Draft", f"{res.vessel_draft_m:.2f} m")
    table.add_row("Under Keel Clearance (UKC)", f"{res.under_keel_clearance_m:.2f} m ({'SAFE' if res.is_ukc_safe else 'GROUNDING RISK'})")
    table.add_row("Transit Status", "[bold green]PERMITTED[/bold green]" if res.can_transit else "[bold red]PROHIBITED[/bold red]")

    console.print(table)


@waterway_app.command("standards")
def waterway_standards(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Display inland waterway classifications under Circular 46/2016/TT-BGTVT."""
    standards_data = [
        {"class": "SPECIAL", "min_depth_m": 4.0, "min_air_draft_m": 11.0, "description": "Cấp Đặc biệt (Vận tải đa phương thức & tàu pha sông biển VR-SB)"},
        {"class": "CLASS_I", "min_depth_m": 3.0, "min_air_draft_m": 9.0, "description": "Cấp I (Sông Tiền, Sông Hậu, Sông Đồng Nai, Sông Hồng)"},
        {"class": "CLASS_II", "min_depth_m": 2.5, "min_air_draft_m": 7.0, "description": "Cấp II (Sông Sài Gòn, Kênh Chợ Gạo)"},
        {"class": "CLASS_III", "min_depth_m": 2.0, "min_air_draft_m": 6.0, "description": "Cấp III (Kênh Láp Vò, Sông Vàm Cỏ Đông)"},
        {"class": "CLASS_IV", "min_depth_m": 1.5, "min_air_draft_m": 5.0, "description": "Cấp IV (Kênh rạch nội đồng cấp vùng)"},
        {"class": "CLASS_V", "min_depth_m": 1.2, "min_air_draft_m": 4.0, "description": "Cấp V (Kênh nhánh địa phương)"},
        {"class": "CLASS_VI", "min_depth_m": 1.0, "min_air_draft_m": 3.5, "description": "Cấp VI (Kênh rạch nhỏ nông thôn)"},
    ]
    if json_output:
        _dump_json(standards_data)
        return

    table = Table(title="Inland Waterway Classification Standards (TT 46/2016/TT-BGTVT)")
    table.add_column("Waterway Class", style="cyan")
    table.add_column("Min Depth", justify="right")
    table.add_column("Min Bridge Air Draft", justify="right")
    table.add_column("Applicable Corridors", style="green")

    for row in standards_data:
        table.add_row(row["class"], f"{row['min_depth_m']:.1f} m", f"{row['min_air_draft_m']:.1f} m", row["description"])

    console.print(table)


# ---------------------------------------------------------------------------
# Barge Commands (Phase 188)
# ---------------------------------------------------------------------------


@barge_app.command("freight")
def barge_freight(
    route: str = typer.Argument("HCM_CAI_MEP", help="Barge route (HCM_CAI_MEP, MEKONG_DELTA_CAI_MEP, HCM_PHNOM_PENH, HAI_PHONG_BAC_NINH)"),
    teu: int = typer.Option(50, "--teu", help="Number of 20ft (TEU) containers"),
    feu: int = typer.Option(10, "--feu", help="Number of 40ft (FEU) containers"),
    dg_count: int = typer.Option(0, "--dg", help="Number of Dangerous Goods (DG) containers"),
    dwt: float = typer.Option(2000.0, "--dwt", help="Barge DWT deadweight tonnage"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Calculate feeder container barging freight and port charges."""
    try:
        b_route = FeederBargeRoute(route.upper())
    except ValueError:
        b_route = FeederBargeRoute.HCM_CAI_MEP

    res = FeederBargingFreightEngine.calculate_freight(
        route=b_route,
        teu_count=teu,
        feu_count=feu,
        dg_containers_count=dg_count,
        barge_dwt_tonnage=dwt,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"Container Feeder Barging Freight — {res.route.value}")
    table.add_column("Cost Item", style="cyan")
    table.add_column("Amount", style="green")

    table.add_row("Cargo Payload", f"{res.teu_count} TEU + {res.feu_count} FEU ({res.dg_containers_count} DG)")
    table.add_row("Base Barge Freight", f"{res.base_freight_vnd:,.0f} VND")
    table.add_row("DG Cargo Surcharge (+10%)", f"{res.dg_surcharge_vnd:,.0f} VND")
    table.add_row("TT 248 Waterway Port Dues", f"{res.waterway_port_dues_vnd:,.0f} VND")
    if res.cross_border_mekong_fee_vnd > 0:
        table.add_row("Cross-Border Treaty Fee", f"{res.cross_border_mekong_fee_vnd:,.0f} VND")
    table.add_row("Total Cost (VND)", f"[bold green]{res.total_barging_cost_vnd:,.0f} VND[/bold green]")
    table.add_row("Total Cost (USD)", f"${res.total_barging_cost_usd:,.2f}")
    table.add_row("Estimated Transit Time", f"{res.transit_hours_estimated:.1f} Hours")

    console.print(table)


@barge_app.command("routes")
def barge_routes(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """List standard container feeder barging routes and benchmark transit metrics."""
    routes_data = [
        {"route": "HCM_CAI_MEP", "distance_nm": 45, "transit_hours": 4.5, "teu_vnd": 1800000, "feu_vnd": 3200000},
        {"route": "MEKONG_DELTA_CAI_MEP", "distance_nm": 120, "transit_hours": 14.0, "teu_vnd": 3500000, "feu_vnd": 6200000},
        {"route": "HCM_PHNOM_PENH", "distance_nm": 190, "transit_hours": 32.0, "teu_vnd": 8500000, "feu_vnd": 15000000},
        {"route": "HAI_PHONG_BAC_NINH", "distance_nm": 65, "transit_hours": 7.0, "teu_vnd": 2200000, "feu_vnd": 3900000},
    ]
    if json_output:
        _dump_json(routes_data)
        return

    table = Table(title="Feeder Barging Routes & Benchmark Tariffs")
    table.add_column("Route Code", style="cyan")
    table.add_column("Distance", justify="right")
    table.add_column("Est. Hours", justify="right")
    table.add_column("Rate / TEU", justify="right")
    table.add_column("Rate / FEU", justify="right", style="green")

    for r in routes_data:
        table.add_row(r["route"], f"{r['distance_nm']} NM", f"{r['transit_hours']}h", f"{r['teu_vnd']:,} VND", f"{r['feu_vnd']:,} VND")

    console.print(table)


# ---------------------------------------------------------------------------
# SAR Commands (Phase 189)
# ---------------------------------------------------------------------------


@sar_app.command("datum")
def sar_datum(
    incident_id: str = typer.Argument(..., help="SAR Incident reference ID"),
    region: str = typer.Option("REGION_III", "--region", "-r", help="SAR Region (REGION_I to IV)"),
    lat: float = typer.Option(10.25, "--lat", help="Last Known Position Latitude"),
    lon: float = typer.Option(107.05, "--lon", help="Last Known Position Longitude"),
    drift_hours: float = typer.Option(4.0, "--drift-hours", help="Elapsed drift duration in hours"),
    current_speed: float = typer.Option(1.5, "--current-speed", help="Water current speed in knots"),
    current_dir: float = typer.Option(210.0, "--current-dir", help="Water current direction in degrees"),
    wind_speed: float = typer.Option(15.0, "--wind-speed", help="Surface wind speed in knots"),
    wind_dir: float = typer.Option(45.0, "--wind-dir", help="Surface wind direction in degrees"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Compute IAMSAR datum drift position and rectangular search area box."""
    try:
        s_region = SARRegion(region.upper())
    except ValueError:
        s_region = SARRegion.REGION_III

    res = MaritimeSARWreckEngine.calculate_sar_datum(
        incident_id=incident_id,
        sar_region=s_region,
        initial_lat=lat,
        initial_lon=lon,
        drift_hours=drift_hours,
        water_current_speed_knots=current_speed,
        water_current_direction_deg=current_dir,
        wind_speed_knots=wind_speed,
        wind_direction_deg=wind_dir,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"Maritime SAR Datum & Search Box — {res.incident_id}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Details", style="green")

    table.add_row("SAR Region", res.sar_region.value)
    table.add_row("Last Known Pos (LKP)", f"{res.initial_lat:.4f}°N, {res.initial_lon:.4f}°E")
    table.add_row("Drift Duration", f"{res.drift_hours:.1f} Hours")
    table.add_row("Computed Datum Pos", f"[bold yellow]{res.datum_lat:.4f}°N, {res.datum_lon:.4f}°E[/bold yellow]")
    table.add_row("Search Radius", f"{res.search_radius_nm:.2f} NM")
    table.add_row("Search Box Area", f"{res.search_box_area_sq_nm:.2f} sq NM")
    table.add_row("Primary Rescue Base", res.primary_sar_base)

    console.print(table)


@sar_app.command("wreck")
def sar_wreck(
    vessel_name: str = typer.Argument(..., help="Sunken vessel name"),
    sinking_date: str = typer.Option(..., "--sinking-date", help="Sinking date (YYYY-MM-DD)"),
    assessment_date: Optional[str] = typer.Option(None, "--assess-date", help="Assessment date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate 30-day statutory wreck removal plan deadline (Decree 05/2017/NĐ-CP)."""
    res = MaritimeSARWreckEngine.assess_wreck_removal(
        vessel_name=vessel_name,
        sinking_date_iso=sinking_date,
        assessment_date_iso=assessment_date,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"Wreck Removal Statutory Assessment — {res.vessel_name}")
    table.add_column("Statutory Criterion", style="cyan")
    table.add_column("Evaluation", style="green")

    table.add_row("Sinking Date", res.sinking_date_iso)
    table.add_row("Days Elapsed", f"{res.days_elapsed} Days")
    table.add_row("Statutory Plan Window", f"{res.statutory_plan_deadline_days} Days")
    table.add_row("Days Remaining", f"{res.days_remaining_for_plan} Days")
    table.add_row("Deadline Status", "[bold red]BREACHED[/bold red]" if res.is_deadline_breached else "[bold green]VALID[/bold green]")
    table.add_row("Action Order", res.action_order)
    table.add_row("Maritime Lien (Art 284)", "ENFORCEABLE" if res.maritime_lien_enforceable else "NOT APPLICABLE")

    console.print(table)


# ---------------------------------------------------------------------------
# ISPS Port Security Commands (Phase 190)
# ---------------------------------------------------------------------------


@isps_app.command("compliance")
def isps_compliance(
    facility_name: str = typer.Argument("Cai Mep International Terminal", help="Port Facility name"),
    port_level: str = typer.Option("LEVEL_1", "--port-level", help="Port ISPS level (LEVEL_1, LEVEL_2, LEVEL_3)"),
    vessel_name: str = typer.Option("MV MAERSK HANOI", "--vessel", "-v", help="Incoming vessel name"),
    ship_level: str = typer.Option("LEVEL_1", "--ship-level", help="Ship ISPS level (LEVEL_1, LEVEL_2, LEVEL_3)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate ISPS Code security levels and Declaration of Security (DoS) obligations."""
    try:
        p_lvl = ISPSLevel(port_level.upper())
        s_lvl = ISPSLevel(ship_level.upper())
    except ValueError:
        p_lvl = ISPSLevel.LEVEL_1
        s_lvl = ISPSLevel.LEVEL_1

    res = PortFacilitySecurityISPSEngine.evaluate_security_compliance(
        facility_name=facility_name,
        port_isps_level=p_lvl,
        vessel_name=vessel_name,
        ship_isps_level=s_lvl,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"ISPS Port Facility & Ship Security Evaluation")
    table.add_column("Security Parameter", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Port Facility", f"{res.facility_name} ({res.port_isps_level.value})")
    table.add_row("Visiting Vessel", f"{res.vessel_name} ({res.ship_isps_level.value})")
    table.add_row("Effective Operating Level", f"[bold yellow]{res.effective_operational_level.value}[/bold yellow]")
    table.add_row("Declaration of Security (DoS)", "[bold red]MANDATORY REQUIRED[/bold red]" if res.is_declaration_of_security_required else "NOT REQUIRED")
    table.add_row("Access Control Rule", res.access_control_rule)
    table.add_row("Cargo Supervision", res.cargo_handling_supervision)

    console.print(table)


@isps_app.command("levels")
def isps_levels_info(
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Display ISPS Code security levels hierarchy and operational triggers."""
    levels_data = [
        {"level": "LEVEL_1", "state": "Normal", "description": "Baseline minimum appropriate protective security measures maintained at all times."},
        {"level": "LEVEL_2", "state": "Heightened", "description": "Heightened risk of security incident; 100% ID check, waterside patrol, search all vehicles."},
        {"level": "LEVEL_3", "state": "Exceptional", "description": "Probable or imminent security incident; operations suspended, port lockdown, Coast Guard control."},
    ]
    if json_output:
        _dump_json(levels_data)
        return

    table = Table(title="ISPS Code Security Levels (SOLAS Chapter XI-2 / Decree 159/2018/NĐ-CP)")
    table.add_column("ISPS Level", style="cyan")
    table.add_column("State", style="yellow")
    table.add_column("Operational Protocols & Controls", style="green")

    for l in levels_data:
        table.add_row(l["level"], l["state"], l["description"])

    console.print(table)
