"""Typer CLI commands for Maritime Phases 399-402 (Advanced Engineering AH)."""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_399_bow_thruster_thrust_pitch import BowThrusterEngine, BowThrusterInput
from src.core.maritime.phase_400_inflatable_liferaft_hru_release import LiferaftHRUEngine, LiferaftHRUInput
from src.core.maritime.phase_401_waste_incinerator_gasification import IncineratorEngine, IncineratorInput
from src.core.maritime.phase_402_vapor_emission_control_vecs import VECSEngine, VECSInput

console = Console()
bowthruster_app = typer.Typer(help="Phase 399: Marine Bow Thruster Thrust & Pitch (SOLAS II-1 Reg 29)")
liferaft_hru_app = typer.Typer(help="Phase 400: Inflatable Liferaft & HRU Float-Free Dynamics (SOLAS III)")
incinerator_app = typer.Typer(help="Phase 401: Shipboard Waste High-Temp Incinerator (MARPOL Annex V)")
vecs_app = typer.Typer(help="Phase 402: Marine Closed Vapor Emission Control System (IMO MSC/Circ.585)")


@bowthruster_app.callback(invoke_without_command=True)
def evaluate_bow_thruster(
    pitch: float = typer.Option(0.85, "--pitch", help="Pitch ratio P/D"),
    rpm: float = typer.Option(300.0, "--rpm", help="Tunnel RPM"),
    diameter: float = typer.Option(2.0, "--diameter", help="Tunnel diameter in meters"),
    speed_knots: float = typer.Option(2.0, "--speed", help="Vessel speed in knots"),
    depth_m: float = typer.Option(3.0, "--depth", help="Submersion depth in meters"),
    oil_temp_c: float = typer.Option(55.0, "--oil-temp", help="Hydraulic oil temp °C"),
    lube_bar: float = typer.Option(4.0, "--lube-bar", help="Lube oil pressure bar"),
    tank_pct: float = typer.Option(80.0, "--tank-pct", help="Header tank level %"),
    motor_kw: float = typer.Option(1200.0, "--motor-kw", help="Motor rated kW"),
):
    """Evaluate Bow Thruster net lateral thrust, cavitation index, and interlocks."""
    res = BowThrusterEngine().evaluate(BowThrusterInput(
        pitch_ratio=pitch, tunnel_rpm=rpm, tunnel_diameter_m=diameter,
        vessel_speed_knots=speed_knots, submersion_depth_m=depth_m,
        hydraulic_oil_temp_c=oil_temp_c, lube_oil_pressure_bar=lube_bar,
        header_tank_level_pct=tank_pct, motor_rated_kw=motor_kw,
    ))
    table = Table(title="Maritime Phase 399: Bow Thruster Hydrodynamics (SOLAS II-1)")
    table.add_column("Metric / Parameter", style="cyan")
    table.add_column("Value / Status", style="magenta")
    for k, v in [
        ("Net Lateral Thrust", f"{res.net_thrust_kn} kN"), ("Blade Tip Speed", f"{res.tip_speed_m_s} m/s"),
        ("Cavitation Index (sigma)", f"{res.cavitation_index}"), ("Cavitation Status", res.cavitation_status.value),
        ("Effective Power", f"{res.effective_power_kw} kW"), ("Motor Load", f"{res.motor_load_pct}%"),
        ("Power Limit Active", "YES" if res.power_limit_active else "NO"),
        ("Interlock Status", res.interlock_status.value),
        ("Operational Permitted", "PERMITTED" if res.operational_permitted else "TRIPPED"),
    ]:
        table.add_row(k, v)
    console.print(table)


@liferaft_hru_app.callback(invoke_without_command=True)
def evaluate_liferaft_hru(
    depth_m: float = typer.Option(2.5, "--depth-m", help="Submersion depth in meters"),
    tension_kn: float = typer.Option(2.3, "--tension-kn", help="Painter tension in kN"),
    stow_m: float = typer.Option(12.0, "--stow-m", help="Stowage height in meters"),
    painter_m: float = typer.Option(28.0, "--painter-m", help="Painter length in meters"),
    hru_age: int = typer.Option(14, "--hru-age", help="HRU service age in months"),
    raft_age: int = typer.Option(8, "--raft-age", help="Liferaft service age in months"),
    manual_cut: bool = typer.Option(False, "--manual-cut", help="Manual release hook triggered"),
):
    """Evaluate Inflatable Liferaft & HRU Float-Free Dynamics (SOLAS III / LSA Code IV)."""
    res = LiferaftHRUEngine().evaluate(LiferaftHRUInput(
        submersion_depth_m=depth_m, painter_line_tension_kn=tension_kn, stowage_height_m=stow_m,
        painter_line_length_m=painter_m, hru_service_age_months=hru_age,
        liferaft_service_age_months=raft_age, manual_pelican_hook_released=manual_cut,
    ))
    table = Table(title="Maritime Phase 400: Liferaft & HRU Release (SOLAS III)")
    table.add_column("Check / Criterion", style="cyan")
    table.add_column("Result", style="green")
    for k, v in [
        ("HRU Actuation State", res.hru_actuation_state.value),
        ("Float-Free Progression", res.float_free_state.value),
        ("Painter Length Compliant", "YES" if res.painter_length_compliant else "NO"),
        ("Required Min Painter", f"{res.min_required_painter_m} m"),
        ("Weak Link Parted", "YES" if res.weak_link_parted else "NO"),
        ("Weak Link Certified", "YES" if res.weak_link_compliant else "NO"),
        ("Service Validity", "VALID" if res.service_valid else "EXPIRED"),
    ]:
        table.add_row(k, v)
    console.print(table)


@incinerator_app.callback(invoke_without_command=True)
def evaluate_incinerator(
    p_temp: float = typer.Option(880.0, "--p-temp", help="Primary chamber temp °C"),
    s_temp: float = typer.Option(1100.0, "--s-temp", help="Secondary chamber temp °C"),
    res_time: float = typer.Option(1.2, "--res-time", help="Residence time in seconds"),
    co_mg: float = typer.Option(120.0, "--co-mg", help="CO emissions in mg/MJ"),
    o2_pct: float = typer.Option(8.5, "--o2-pct", help="Excess O2 %"),
    smoke: float = typer.Option(0.5, "--smoke", help="Smoke density Ringelmann"),
    draft_pa: float = typer.Option(-120.0, "--draft-pa", help="Draft pressure Pa"),
    flame: bool = typer.Option(True, "--flame/--no-flame", help="Flame detector status"),
):
    """Evaluate Shipboard Incinerator thermodynamics & emissions under MEPC.244(66)."""
    res = IncineratorEngine().evaluate(IncineratorInput(
        primary_chamber_temp_c=p_temp, secondary_chamber_temp_c=s_temp,
        residence_time_s=res_time, flue_gas_co_mg_mj=co_mg, oxygen_content_pct=o2_pct,
        smoke_density_ringelmann=smoke, draft_pressure_pa=draft_pa, flame_detected=flame,
    ))
    table = Table(title="Maritime Phase 401: Waste Incinerator (MEPC.244(66))")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Conformance", style="yellow")
    for k, v in [
        ("Operational Status", res.status.value),
        ("Waste Charging Permitted", "YES" if res.waste_charging_permitted else "LOCKED"),
        ("Dioxin Destruction Verified", "PASS" if res.dioxin_destruction_verified else "FAIL"),
        ("Flue Emissions Compliant", "YES" if res.flue_emissions_compliant else "EXCEEDED"),
        ("Safety Trip Active", "TRIPPED" if res.safety_trip_active else "CLEAR"),
        ("Combustion Efficiency", f"{res.combustion_efficiency_pct}%"),
    ]:
        table.add_row(k, v)
    console.print(table)


@vecs_app.callback(invoke_without_command=True)
def evaluate_vecs(
    p_bar: float = typer.Option(0.04, "--press-bar", help="Vapor manifold pressure bar"),
    cargo_pct: float = typer.Option(85.0, "--cargo-pct", help="Tank filling %"),
    o2_pct: float = typer.Option(4.5, "--o2-pct", help="Vapor oxygen %"),
    dp_bar: float = typer.Option(0.02, "--dp-bar", help="Arrester diff pressure bar"),
    temp_c: float = typer.Option(28.0, "--temp-c", help="Arrester temperature °C"),
    rate_m3: float = typer.Option(2500.0, "--rate", help="Loading rate m3/h"),
):
    """Evaluate Marine VECS manifold pressure, inerting, and overfill safety."""
    res = VECSEngine().evaluate(VECSInput(
        manifold_pressure_bar=p_bar, cargo_level_pct=cargo_pct, vapor_oxygen_pct=o2_pct,
        arrester_dp_bar=dp_bar, arrester_temp_c=temp_c, loading_rate_m3_h=rate_m3,
    ))
    table = Table(title="Maritime Phase 402: Tanker VECS (IMO MSC/Circ.585)")
    table.add_column("Safety Envelope", style="cyan")
    table.add_column("Telemetry / Status", style="red")
    for k, v in [
        ("Manifold Pressure Status", res.pressure_status.value),
        ("Cargo Overfill Level", res.overfill_level.value),
        ("Vapor Oxygen Safe (<8%)", "SAFE" if res.oxygen_safe else "EXPLOSION RISK"),
        ("Detonation Arrester OK", "PASS" if res.arrester_pass else "FAULT"),
        ("Cargo Loading Permitted", "PERMITTED" if res.cargo_loading_permitted else "SHUTDOWN"),
        ("Max Allowable Rate", f"{res.max_allowable_loading_rate_m3_h} m3/h"),
    ]:
        table.add_row(k, v)
    console.print(table)
