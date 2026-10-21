"""CLI command group for Maritime Automation Phases 427-430.

Provides bilingual Typer commands for:
- Cylinder lubrication feed rate & cold corrosion monitoring.
- SCR Urea/DEF De-NOx catalytic reduction & ammonia slip.
- Cargo hold bilge suction valve interlock & jet eductor dewatering.
- Hull ICAF copper dissolution & ultrasonic bio-fouling protection.
Strictly < 160 LOC, zero mocks.
"""

import json
from typing import Optional
import typer
from rich.console import Console

from src.core.maritime.phase_427_cylinder_lubrication_alpha import (
    CylinderLubricationEngine,
    CylinderLubricationTelemetry,
)
from src.core.maritime.phase_428_scr_urea_denox import (
    SCRDeNOxEngine,
    SCRDeNOxTelemetry,
)
from src.core.maritime.phase_429_cargo_hold_bilge_eductor import (
    CargoHoldBilgeEngine,
    CargoHoldBilgeTelemetry,
)
from src.core.maritime.phase_430_hull_icaf_ultrasonic import (
    HullAntiFoulingEngine,
    HullAntiFoulingTelemetry,
)

console = Console()

cylinder_app = typer.Typer(help="Phase 427: ME Cylinder Lubrication Alpha ACC & BN Control")
scr_app = typer.Typer(help="Phase 428: Marine SCR Urea De-NOx & Tier III Emissions")
bilge_app = typer.Typer(help="Phase 429: Cargo Hold Bilge Suction & Jet Eductor Dewatering")
icaf_app = typer.Typer(help="Phase 430: Hull ICAF & Ultrasonic Anti-Biofouling")


@cylinder_app.callback(invoke_without_command=True)
def evaluate_cylinder_lubrication(
    power_kw: float = typer.Option(14500.0, "--power-kw", help="Main Engine current power in kW"),
    sulfur_pct: float = typer.Option(0.45, "--sulfur-pct", help="Fuel sulfur content %"),
    oil_bn: float = typer.Option(40.0, "--oil-bn", help="Cylinder oil Base Number (BN) mg KOH/g"),
    liner_temp_c: float = typer.Option(165.0, "--liner-temp-c", help="Cylinder liner wall temp °C"),
    drain_bn: float = typer.Option(22.0, "--drain-bn", help="Scrape-down drain residual BN"),
    drain_fe_ppm: float = typer.Option(85.0, "--drain-fe-ppm", help="Scrape-down drain iron content ppm"),
) -> None:
    """Evaluates Alpha ACC cylinder oil dosing, BN neutralization, and liner wear."""
    engine = CylinderLubricationEngine()
    telem = CylinderLubricationTelemetry(
        engine_power_kw=power_kw,
        fuel_sulfur_pct=sulfur_pct,
        lubricant_bn_mg_koh_g=oil_bn,
        liner_wall_temp_c=liner_temp_c,
        drain_oil_residual_bn=drain_bn,
        drain_oil_iron_ppm=drain_fe_ppm,
    )
    res = engine.evaluate(telem)
    console.print(f"[bold cyan]ME Cylinder Lubrication Assessment (Phase 427):[/bold cyan] {res.status}")
    console.print(f"Feed Rate: {res.specific_feed_rate_g_kwh} g/kWh | Daily: {res.daily_consumption_liters} L/day")
    console.print(f"BN Neutralization Margin: {res.bn_neutralization_margin} | Scuffing Risk: {res.liner_scuffing_risk}")
    if res.warnings:
        console.print(f"[yellow]Warnings:[/yellow] {json.dumps(res.warnings, indent=2)}")


@scr_app.callback(invoke_without_command=True)
def evaluate_scr_denox(
    inlet_temp_c: float = typer.Option(330.0, "--inlet-temp-c", help="SCR catalyst inlet temperature °C"),
    raw_nox_ppm: float = typer.Option(1150.0, "--raw-nox-ppm", help="Engine raw NOx concentration ppm"),
    outlet_nox_ppm: float = typer.Option(195.0, "--outlet-nox-ppm", help="SCR outlet NOx concentration ppm"),
    ammonia_slip_ppm: float = typer.Option(4.2, "--ammonia-slip-ppm", help="SCR outlet NH3 slip ppm"),
    dp_kpa: float = typer.Option(1.45, "--dp-kpa", help="Catalyst differential pressure kPa"),
    def_level_pct: float = typer.Option(68.0, "--def-level-pct", help="DEF / Urea storage tank level %"),
) -> None:
    """Evaluates SCR De-NOx reduction kinetics, urea dosing, and ABS condensation risk."""
    engine = SCRDeNOxEngine()
    telem = SCRDeNOxTelemetry(
        catalyst_inlet_temp_c=inlet_temp_c,
        raw_nox_ppm=raw_nox_ppm,
        exhaust_nox_outlet_ppm=outlet_nox_ppm,
        ammonia_slip_ppm=ammonia_slip_ppm,
        catalyst_dp_kpa=dp_kpa,
        def_tank_level_pct=def_level_pct,
    )
    res = engine.evaluate(telem)
    console.print(f"[bold cyan]SCR De-NOx Assessment (Phase 428):[/bold cyan] {res.status}")
    console.print(f"Efficiency: {res.denox_efficiency_pct}% | Urea Dosing: {res.urea_dosing_rate_l_h} L/h")
    console.print(f"Tier III Compliant: {res.tier_iii_compliant} | ABS Risk: {res.abs_condensation_risk}")
    if res.warnings:
        console.print(f"[yellow]Warnings:[/yellow] {json.dumps(res.warnings, indent=2)}")


@bilge_app.callback(invoke_without_command=True)
def evaluate_hold_bilge(
    water_level_m: float = typer.Option(0.08, "--water-level-m", help="Hold bilge well water level meters"),
    motive_bar: float = typer.Option(6.8, "--motive-bar", help="Eductor driving motive pressure bar"),
    lift_m: float = typer.Option(4.2, "--lift-m", help="Suction lift vertical height meters"),
    suction_open: bool = typer.Option(False, "--suction-open", help="Bilge suction valve status"),
    motive_open: bool = typer.Option(False, "--motive-open", help="Eductor motive supply valve status"),
) -> None:
    """Evaluates cargo hold bilge water ingress (WIDS) and eductor dewatering capacity."""
    engine = CargoHoldBilgeEngine()
    telem = CargoHoldBilgeTelemetry(
        water_level_meters=water_level_m,
        motive_water_pressure_bar=motive_bar,
        suction_lift_height_m=lift_m,
        bilge_suction_valve_open=suction_open,
        motive_valve_open=motive_open,
    )
    res = engine.evaluate(telem)
    console.print(f"[bold cyan]Cargo Hold Bilge & Eductor (Phase 429):[/bold cyan] {res.status}")
    console.print(f"WIDS Level: {res.water_ingress_alarm_level} | Dewatering: {res.dewatering_capacity_m3_h} m3/h")
    console.print(f"Backflow Hazard: {res.backflow_risk} | Operational Ready: {res.eductor_operational_ready}")
    if res.warnings:
        console.print(f"[yellow]Warnings:[/yellow] {json.dumps(res.warnings, indent=2)}")


@icaf_app.callback(invoke_without_command=True)
def evaluate_hull_icaf(
    flow_m3_h: float = typer.Option(1200.0, "--flow-m3-h", help="Seawater cooling flow rate m3/h"),
    cu_current_a: float = typer.Option(2.45, "--cu-current-a", help="Cu anode current in Amperes"),
    depleted_kg: float = typer.Option(8.5, "--depleted-kg", help="Consumed Cu anode mass in kg"),
    transducer_ohms: float = typer.Option(85.0, "--transducer-ohms", help="Ultrasonic transducer impedance"),
    idle_days: int = typer.Option(3, "--idle-days", help="Vessel idle days in port/anchorage"),
) -> None:
    """Evaluates seachest ICAF electrolytic copper dosing and ultrasonic biofouling prevention."""
    engine = HullAntiFoulingEngine()
    telem = HullAntiFoulingTelemetry(
        seawater_flow_m3_h=flow_m3_h,
        cu_anode_current_amps=cu_current_a,
        cu_anode_consumed_mass_kg=depleted_kg,
        ultrasonic_transducer_impedance_ohms=transducer_ohms,
        vessel_idle_days=idle_days,
    )
    res = engine.evaluate(telem)
    console.print(f"[bold cyan]Hull ICAF & Ultrasonic Protection (Phase 430):[/bold cyan] {res.status}")
    console.print(f"Cu Dosing: {res.cu_concentration_ppb} ppb | Depletion: {res.cu_anode_depletion_pct}%")
    console.print(f"Risk Level: {res.biofouling_risk_level} | Transducer Healthy: {res.ultrasonic_transducer_healthy}")
    if res.warnings:
        console.print(f"[yellow]Warnings:[/yellow] {json.dumps(res.warnings, indent=2)}")
