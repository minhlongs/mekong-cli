"""CLI commands for Maritime Phases 359-362 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_autopilot_shaft_inert_waste_engine import (
    AdaptiveAutopilotEngine,
    AdaptiveAutopilotInput,
    ShaftAlignmentVibrationEngine,
    ShaftAlignmentVibrationInput,
    N2InertGasEngine,
    N2InertGasInput,
    SeaportWastewaterEngine,
    SeaportWastewaterInput,
)

console = Console()

autopilot_app = typer.Typer(help="Phase 359: Adaptive Autopilot & Rudder Monitoring (IMO MSC.64/67)")
shaft_app = typer.Typer(help="Phase 360: Propeller Shaft Alignment & Whirling Vibration (IACS UR M68)")
inert_app = typer.Typer(help="Phase 361: N2 Inert Gas Generator & Dew Point Control (IGC Code Ch.9)")
waste_app = typer.Typer(help="Phase 362: Remote Seaport Wastewater Recycling & ZLD (QCVN 14/40)")


@autopilot_app.command("evaluate")
def evaluate_autopilot(
    vessel_id: str = typer.Option("V-AUTO-01", "--vessel-id", "-v"),
    target_heading: float = typer.Option(90.0, "--target-heading", "-t"),
    actual_heading: float = typer.Option(88.5, "--actual-heading", "-a"),
    rot: float = typer.Option(0.2, "--rot", "-r"),
    rudder_angle: float = typer.Option(2.0, "--rudder-angle", "-g"),
    sea_state: int = typer.Option(3, "--sea-state", "-s"),
    speed: float = typer.Option(14.0, "--speed", "-k"),
    lag_sec: float = typer.Option(1.0, "--lag-sec", "-l"),
) -> None:
    """Evaluate adaptive heading control, deadband, and SOLAS lag."""
    inp = AdaptiveAutopilotInput(
        vessel_id=vessel_id,
        target_heading_deg=target_heading,
        actual_heading_deg=actual_heading,
        rate_of_turn_deg_s=rot,
        actual_rudder_angle_deg=rudder_angle,
        sea_state_douglas=sea_state,
        speed_knots=speed,
        command_latency_seconds=lag_sec,
    )
    res = AdaptiveAutopilotEngine.evaluate(inp)
    console.print(f"[bold cyan]Autopilot Evaluation:[/bold cyan] {res.vessel_id}")
    console.print(f"Heading Error: {res.heading_error_deg}° | Deadband: {res.adaptive_deadband_deg}° | Commanded Rudder: {res.commanded_rudder_angle_deg}°")
    console.print(f"Follow-up Error: {res.rudder_follow_up_error_deg}° | Status: [yellow]{res.status}[/yellow]")
    for adv in res.advisories:
        console.print(f" - {adv}")


@shaft_app.command("evaluate")
def evaluate_shaft(
    shaft_id: str = typer.Option("SHAFT-01", "--shaft-id", "-s"),
    rpm: float = typer.Option(95.0, "--rpm", "-r"),
    blades: int = typer.Option(5, "--blades", "-b"),
    reaction_kn: float = typer.Option(380.0, "--reaction-kn", "-f"),
    length_m: float = typer.Option(1.2, "--length-m", "-l"),
    dia_m: float = typer.Option(0.55, "--dia-m", "-d"),
    natural_freq: float = typer.Option(7.9, "--nat-freq", "-n"),
    vib_rms: float = typer.Option(3.2, "--vib-rms", "-v"),
) -> None:
    """Evaluate aft stern tube bearing pressure and barred speed range."""
    inp = ShaftAlignmentVibrationInput(
        shaft_id=shaft_id,
        engine_rpm=rpm,
        propeller_blades_count=blades,
        aft_bearing_reaction_kn=reaction_kn,
        bearing_length_m=length_m,
        bearing_diameter_m=dia_m,
        whirling_natural_frequency_hz=natural_freq,
        vibration_velocity_rms_mm_s=vib_rms,
    )
    res = ShaftAlignmentVibrationEngine.evaluate(inp)
    console.print(f"[bold green]Shaft Vibration Evaluation:[/bold green] {res.shaft_id}")
    console.print(f"ASTB Pressure: {res.aft_bearing_pressure_mpa} MPa (Safe: {res.is_bearing_pressure_safe})")
    console.print(f"BPF: {res.blade_passing_frequency_hz} Hz | Resonance Margin: {res.whirling_resonance_margin_percent}% | BSR: {res.is_in_barred_speed_range}")
    console.print(f"Severity: {res.vibration_severity_grade} | Status: [yellow]{res.status}[/yellow]")
    for adv in res.advisories:
        console.print(f" - {adv}")


@inert_app.command("evaluate")
def evaluate_inert(
    generator_id: str = typer.Option("IGG-N2-01", "--gen-id", "-g"),
    tank_id: str = typer.Option("TANK-LPG-01", "--tank-id", "-t"),
    o2_pct: float = typer.Option(0.75, "--o2-pct", "-o"),
    dew_point: float = typer.Option(-45.0, "--dew-point", "-d"),
    delta_p: float = typer.Option(0.22, "--delta-p", "-p"),
    flow_m3: float = typer.Option(1200.0, "--flow-m3", "-f"),
    feed_press: float = typer.Option(7.5, "--feed-press", "-a"),
) -> None:
    """Evaluate N2 gas purity, dew point, and supply interlocks."""
    inp = N2InertGasInput(
        generator_id=generator_id,
        target_tank_id=tank_id,
        delivered_o2_percent_vol=o2_pct,
        measured_dew_point_celsius=dew_point,
        dryer_differential_pressure_bar=delta_p,
        inert_gas_flow_rate_m3_h=flow_m3,
        feed_air_pressure_bar=feed_press,
    )
    res = N2InertGasEngine.evaluate(inp)
    console.print(f"[bold magenta]N2 Inert Gas Evaluation:[/bold magenta] {res.generator_id} -> {res.target_tank_id}")
    console.print(f"O2 Compliant: {res.is_o2_compliant_igc} | Dew Point Dry: {res.is_dew_point_dry} | Cargo Supply Permitted: {res.is_cargo_supply_permitted}")
    console.print(f"Dryer Regen Required: {res.is_dryer_regeneration_required} | Status: [yellow]{res.atmosphere_safety_status}[/yellow]")
    for adv in res.advisories:
        console.print(f" - {adv}")


@waste_app.command("evaluate")
def evaluate_waste(
    facility_id: str = typer.Option("PORT-ISLAND-01", "--fac-id", "-i"),
    influent_m3: float = typer.Option(200.0, "--influent", "-q"),
    recycled_m3: float = typer.Option(175.0, "--recycled", "-r"),
    bod5: float = typer.Option(12.0, "--bod5", "-b"),
    turbidity: float = typer.Option(1.1, "--turbidity", "-t"),
    coliform: float = typer.Option(45.0, "--coliform", "-c"),
    tds: float = typer.Option(950.0, "--tds", "-s"),
    uv_active: bool = typer.Option(True, "--uv-active", "-u"),
) -> None:
    """Evaluate remote port wastewater recycling, ZLD rate, and effluent standards."""
    inp = SeaportWastewaterInput(
        facility_id=facility_id,
        influent_flow_m3_day=influent_m3,
        recycled_permeate_m3_day=recycled_m3,
        effluent_bod5_mg_l=bod5,
        effluent_turbidity_ntu=turbidity,
        effluent_coliform_mpn_100ml=coliform,
        feed_tds_mg_l=tds,
        is_uv_disinfection_active=uv_active,
    )
    res = SeaportWastewaterEngine.evaluate(inp)
    console.print(f"[bold blue]Wastewater Recycling Evaluation:[/bold blue] {res.facility_id}")
    console.print(f"Recovery Rate: {res.water_recovery_rate_percent}% (ZLD OK: {res.is_zld_target_achieved})")
    console.print(f"Effluent Compliant: {res.is_effluent_compliant} | Brackish RO Required: {res.is_brackish_ro_required}")
    console.print(f"Status: [yellow]{res.operational_status}[/yellow]")
    for adv in res.advisories:
        console.print(f" - {adv}")
