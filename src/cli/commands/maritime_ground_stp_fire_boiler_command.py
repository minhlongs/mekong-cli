"""Bilingual Typer CLI Commands for Maritime Automation Phases 435-438.

Covers:
- shaftearth: Propeller shaft grounding earthing device & slip ring potential drop
- stpeffluent: Sewage treatment plant MBR effluent quality & holding tank divert
- firepump: Emergency fire pump priming and SOLAS discharge head
- boilerchem: Marine auxiliary boiler water chemical dosing & passivation
Strictly < 160 LOC, zero mocks.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_435_shaft_grounding_earthing_device import (
    ShaftEarthingEngine,
    ShaftEarthingTelemetry,
)
from src.core.maritime.phase_436_stp_membrane_bioreactor_effluent import (
    StpEffluentEngine,
    StpEffluentTelemetry,
)
from src.core.maritime.phase_437_emergency_fire_pump_priming import (
    EmergencyFirePumpEngine,
    EmergencyFirePumpTelemetry,
)
from src.core.maritime.phase_438_boiler_water_chemical_dosing import (
    BoilerWaterEngine,
    BoilerWaterTelemetry,
)

console = Console()
shaftearth_app = typer.Typer(name="shaftearth", help="Propeller shaft earthing potential monitoring")
stpeffluent_app = typer.Typer(name="stpeffluent", help="STP MBR effluent quality & discharge interlock")
firepump_app = typer.Typer(name="firepump", help="Emergency fire pump priming & discharge head")
boilerchem_app = typer.Typer(name="boilerchem", help="Boiler water chemical dosing & passivation")


@shaftearth_app.command("status")
def shaftearth_status(
    potential_mv: float = typer.Option(35.0, "--potential", help="Shaft slip ring potential (mV)"),
    current_a: float = typer.Option(1.2, "--current", help="Discharge current (A)"),
    brush_wear: float = typer.Option(30.0, "--wear", help="Brush wear (%)"),
) -> None:
    """Evaluate shaft grounding device voltage drop and spark erosion risk."""
    engine = ShaftEarthingEngine()
    telemetry = ShaftEarthingTelemetry(
        shaft_potential_mv=potential_mv,
        shaft_current_a=current_a,
        brush_wear_pct=brush_wear,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Shaft Earthing Status:[/bold] {res.status}")
    console.print(f"Potential: {res.shaft_potential_mv:.1f} mV (Erosion Risk: {res.spark_erosion_risk})")
    console.print(f"Current Density: {res.current_density_a_cm2:.6f} A/cm2 (Healthy: {res.earthing_healthy})")


@stpeffluent_app.command("status")
def stpeffluent_status(
    tmp_bar: float = typer.Option(0.22, "--tmp", help="Transmembrane DP (bar)"),
    tss: float = typer.Option(8.5, "--tss", help="Total suspended solids (mg/L)"),
    coliform: float = typer.Option(15.0, "--coliform", help="Coliform count (CFU/100mL)"),
    chlorine: float = typer.Option(0.25, "--chlorine", help="Free chlorine (mg/L)"),
) -> None:
    """Evaluate MBR sewage effluent quality against IMO MEPC.227(64)."""
    engine = StpEffluentEngine()
    telemetry = StpEffluentTelemetry(
        transmembrane_dp_bar=tmp_bar,
        total_suspended_solids_mg_l=tss,
        coliform_cfu_100ml=coliform,
        free_chlorine_mg_l=chlorine,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]STP Effluent Status:[/bold] {res.status}")
    console.print(f"Discharge Permitted: {res.discharge_permitted} (Divert: {res.divert_to_holding_tank})")
    console.print(f"Membrane Fouled: {res.membrane_fouled}")


@firepump_app.command("status")
def firepump_status(
    press: float = typer.Option(3.2, "--press", help="Discharge pressure (bar)"),
    prime_s: float = typer.Option(18.5, "--prime-s", help="Priming time (s)"),
    fuel_h: float = typer.Option(4.5, "--fuel-h", help="Fuel autonomy (hours)"),
) -> None:
    """Evaluate emergency fire pump priming and discharge pressure under SOLAS."""
    engine = EmergencyFirePumpEngine()
    telemetry = EmergencyFirePumpTelemetry(
        discharge_pressure_bar=press,
        priming_time_s=prime_s,
        diesel_fuel_hours_remaining=fuel_h,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Emergency Fire Pump Status:[/bold] {res.status}")
    console.print(f"Operational Ready: {res.pump_operational_ready}")
    console.print(f"Pressure Compliant: {res.pressure_compliant} (Fuel Compliant: {res.fuel_compliant})")


@boilerchem_app.command("status")
def boilerchem_status(
    po4: float = typer.Option(22.0, "--po4", help="Phosphate concentration (mg/L)"),
    n2h4: float = typer.Option(0.07, "--n2h4", help="Hydrazine concentration (mg/L)"),
    ph: float = typer.Option(10.1, "--ph", help="Boiler water pH"),
    cond: float = typer.Option(480.0, "--cond", help="Conductivity (uS/cm)"),
) -> None:
    """Evaluate boiler water chemistry, scale protection, and blowdown advisory."""
    engine = BoilerWaterEngine()
    telemetry = BoilerWaterTelemetry(
        phosphate_po4_mg_l=po4,
        hydrazine_n2h4_mg_l=n2h4,
        ph_value=ph,
        conductivity_us_cm=cond,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Boiler Water Status:[/bold] {res.status}")
    console.print(f"Passivated: {res.oxygen_passivated} (Scale Protected: {res.scale_prevention_ok})")
    console.print(f"Blowdown Required: {res.blowdown_required}")
