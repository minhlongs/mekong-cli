"""CLI commands for Maritime Phases 379-382 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_air_seachest_draft_pilot_engine import (
    DraftTankGaugingInput,
    DraftTankSoundingGaugingEngine,
    EngineReversibility,
    MarineStartingAirCompressorEngine,
    PilotageArpaInput,
    PortPilotageArpaCollisionEngine,
    SeachestCoolingIngressEngine,
    SeachestCoolingInput,
    SeachestSuctionType,
    StartingAirInput,
    TargetTrack,
)

console = Console()

starting_air_app = typer.Typer(
    help="Phase 379: Marine Starting Air & Compressor Engine (SOLAS II-1 Reg 26)"
)
seachest_app = typer.Typer(
    help="Phase 380: Seachest & Seawater Cooling Ingress Engine (IACS UR M62, MGPS)"
)
draft_sounding_app = typer.Typer(
    help="Phase 381: Hydrostatic Draft & Tank Sounding Gauging (IMO MSC.267(85), SOLAS XII)"
)
pilotage_arpa_app = typer.Typer(
    help="Phase 382: Port Pilotage Safety & ARPA Collision Avoidance (IMO MSC.192(79))"
)


@starting_air_app.command("evaluate")
def evaluate_starting_air(
    vessel_id: str = typer.Option("IMO9923456", "--vessel-id", "-v"),
    engine_type: str = typer.Option("REVERSIBLE", "--engine-type", help="REVERSIBLE / NON_REVERSIBLE"),
    pressure: float = typer.Option(30.0, "--pressure", "-p", help="Starting air pressure (bar)"),
    charge_time: float = typer.Option(48.0, "--charge-time", help="Recharge duration (min)"),
    consumption: float = typer.Option(1.2, "--consumption", help="Air consumption per start (bar)"),
    last_drain: float = typer.Option(25.0, "--last-drain", help="Elapsed minutes since last drain"),
) -> None:
    """Evaluate main propulsion starting air capacity and compressor automation."""
    rev_enum = (
        EngineReversibility(engine_type)
        if engine_type in [e.value for e in EngineReversibility]
        else EngineReversibility.REVERSIBLE
    )
    inp = StartingAirInput(
        vessel_id=vessel_id,
        engine_type=rev_enum,
        current_pressure_bar=pressure,
        compressor_charge_time_min=charge_time,
        air_consumption_per_start_bar=consumption,
        last_drain_elapsed_min=last_drain,
    )
    res = MarineStartingAirCompressorEngine().evaluate(inp)
    console.print(f"[bold cyan]Starting Air System:[/bold cyan] {res.vessel_id} | Status: [green]{res.system_status}[/green]")
    console.print(f"Starts: {res.available_starts}/{res.required_starts} | Compliant: {res.is_solas_compliant}")
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@seachest_app.command("evaluate")
def evaluate_seachest(
    vessel_id: str = typer.Option("IMO9923456", "--vessel-id", "-v"),
    suction: str = typer.Option("LOW_SEACHEST", "--suction", "-s", help="HIGH_SEACHEST / LOW_SEACHEST"),
    ukc: float = typer.Option(6.0, "--ukc", help="Under-keel clearance (m)"),
    inlet_p: float = typer.Option(2.4, "--inlet-p", help="Strainer inlet pressure (bar)"),
    outlet_p: float = typer.Option(2.2, "--outlet-p", help="Strainer outlet pressure (bar)"),
    flow: float = typer.Option(800.0, "--flow", help="Seawater flow (m3/h)"),
    mgps_current: float = typer.Option(4.0, "--mgps-a", help="MGPS anode current (A)"),
    temp: float = typer.Option(25.0, "--temp-c", help="Seawater temperature (deg C)"),
) -> None:
    """Evaluate seachest suction intake safety, strainer delta-P, and MGPS current."""
    suction_enum = (
        SeachestSuctionType(suction)
        if suction in [e.value for e in SeachestSuctionType]
        else SeachestSuctionType.LOW_SEACHEST
    )
    inp = SeachestCoolingInput(
        vessel_id=vessel_id,
        active_suction=suction_enum,
        under_keel_clearance_m=ukc,
        strainer_inlet_pressure_bar=inlet_p,
        strainer_outlet_pressure_bar=outlet_p,
        seawater_flow_m3_h=flow,
        mgps_anode_current_a=mgps_current,
        seawater_temp_c=temp,
    )
    res = SeachestCoolingIngressEngine().evaluate(inp)
    console.print(f"[bold cyan]Seachest Cooling Evaluation:[/bold cyan] {res.vessel_id} | Status: [green]{res.system_status}[/green]")
    console.print(f"Diff P: {res.differential_pressure_bar} bar | Clogged: {res.is_strainer_clogged} | MGPS: {res.is_mgps_effective}")
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@draft_sounding_app.command("evaluate")
def evaluate_draft_sounding(
    vessel_id: str = typer.Option("IMO9923456", "--vessel-id", "-v"),
    draft_fore: float = typer.Option(10.5, "--draft-fore", help="Fore draft (m)"),
    draft_mid_port: float = typer.Option(10.8, "--draft-port", help="Mid port draft (m)"),
    draft_mid_stbd: float = typer.Option(10.8, "--draft-stbd", help="Mid stbd draft (m)"),
    draft_aft: float = typer.Option(11.2, "--draft-aft", help="Aft draft (m)"),
    tank_height: float = typer.Option(15.0, "--tank-h", help="Tank height (m)"),
    sounding: float = typer.Option(12.0, "--sounding", help="Sounding depth (m)"),
    ingress: bool = typer.Option(False, "--ingress", help="Hold water ingress detected"),
) -> None:
    """Evaluate quarter-mean draft, trim/heel/deflection, and tank sounding ullage."""
    inp = DraftTankGaugingInput(
        vessel_id=vessel_id,
        draft_fore_m=draft_fore,
        draft_mid_port_m=draft_mid_port,
        draft_mid_starboard_m=draft_mid_stbd,
        draft_aft_m=draft_aft,
        tank_height_m=tank_height,
        sounding_level_m=sounding,
        dry_void_ingress_detected=ingress,
    )
    res = DraftTankSoundingGaugingEngine().evaluate(inp)
    console.print(f"[bold cyan]Draft & Tank Sounding:[/bold cyan] {res.vessel_id} | Status: [green]{res.system_status}[/green]")
    console.print(f"QM Draft: {res.quarter_mean_draft_m}m | Trim: {res.trim_m}m | Tank Filling: {res.tank_filling_pct}%")
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@pilotage_arpa_app.command("evaluate")
def evaluate_pilotage_arpa(
    vessel_id: str = typer.Option("IMO9923456", "--vessel-id", "-v"),
    own_speed: float = typer.Option(12.0, "--own-speed", help="Own speed (knots)"),
    own_course: float = typer.Option(90.0, "--own-course", help="Own course (deg)"),
    pilot_active: bool = typer.Option(False, "--pilot-boarding", help="Pilot boarding active"),
    ground_speed: float = typer.Option(6.5, "--ground-speed", help="Speed over ground (knots)"),
    dwt: float = typer.Option(50000.0, "--dwt", help="Deadweight (tonnes)"),
    tug_bp: float = typer.Option(65.0, "--tug-bp", help="Available tug bollard pull (TBP)"),
) -> None:
    """Evaluate port pilotage boarding speed compliance and ARPA collision kinematics."""
    targets = [
        TargetTrack(target_id="TGT01", relative_x_nm=2.0, relative_y_nm=3.0, target_speed_knots=10.0, target_course_deg=270.0)
    ]
    inp = PilotageArpaInput(
        vessel_id=vessel_id,
        own_speed_knots=own_speed,
        own_course_deg=own_course,
        targets=targets,
        pilot_boarding_active=pilot_active,
        ground_speed_knots=ground_speed,
        dwt_tonnes=dwt,
        available_tug_bollard_pull_tonnes=tug_bp,
    )
    res = PortPilotageArpaCollisionEngine().evaluate(inp)
    console.print(f"[bold cyan]Port Pilotage & ARPA:[/bold cyan] {res.vessel_id} | Status: [green]{res.system_status}[/green]")
    console.print(f"Min CPA: {res.min_cpa_nm} NM | Pilot Safe: {res.is_pilot_speed_compliant} | Tug Safe: {res.is_tug_escort_adequate}")
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")
