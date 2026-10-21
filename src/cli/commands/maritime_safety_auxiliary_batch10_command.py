"""CLI commands for Maritime Safety Auxiliary Batch 10 (Phases 499-502).
Strictly < 90 LOC, Typer subcommands for Turbocharger, FWG, CO2 Flooding, and Viscometer.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_499_turbocharger_overspeed_surge import (
    TurbochargerOverspeedSurgeEngine, TurbochargerTelemetry,
)
from src.core.maritime.phase_500_fresh_water_generator_salinity import (
    FreshWaterGeneratorSalinityEngine, FwgTelemetry,
)
from src.core.maritime.phase_501_co2_total_flooding_interlock import (
    Co2FloodingTelemetry, Co2TotalFloodingInterlockEngine,
)
from src.core.maritime.phase_502_fuel_oil_viscometer_heater import (
    FuelOilViscometerHeaterEngine, FuelViscometerTelemetry,
)

maritime_aux10_app = typer.Typer(
    name="maritime-aux10",
    help="Maritime Safety Automation Batch 10: Turbocharger, FWG, CO2 Interlock, Viscometer",
)
console = Console()


@maritime_aux10_app.command("tc-check")
def check_tc(rpm: float = 15000.0, lube_bar: float = 1.6, exhaust_c: float = 440.0, surges: int = 0) -> None:
    res = TurbochargerOverspeedSurgeEngine.evaluate(
        TurbochargerTelemetry(rotor_rpm=rpm, lube_oil_inlet_bar=lube_bar, exhaust_inlet_temp_c=exhaust_c, surge_pulses_per_min=surges)
    )
    console.print(f"[bold cyan]TC Status:[/bold cyan] {res.status.value} | Slowdown: {res.slowdown_requested} | Code: {res.alarm_code}")


@maritime_aux10_app.command("fwg-check")
def check_fwg(vacuum_bar: float = -0.90, ejector_bar: float = 2.8, salinity_ppm: float = 1.5) -> None:
    res = FreshWaterGeneratorSalinityEngine.evaluate(
        FwgTelemetry(shell_vacuum_bar=vacuum_bar, ejector_water_pressure_bar=ejector_bar, distillate_salinity_ppm=salinity_ppm)
    )
    console.print(f"[bold green]FWG State:[/bold green] {res.distribution_state.value} | Compliant: {res.potable_water_compliant} | Code: {res.alarm_code}")


@maritime_aux10_app.command("co2-check")
def check_co2(door_open: bool = False, delay_sec: float = 0.0, fans_tripped: bool = True, dampers_closed: bool = True, pilot_bar: float = 55.0) -> None:
    res = Co2TotalFloodingInterlockEngine.evaluate(
        Co2FloodingTelemetry(cabinet_door_opened=door_open, pre_discharge_delay_sec=delay_sec, ventilation_fans_tripped=fans_tripped, fire_dampers_closed=dampers_closed, pilot_cylinder_pressure_bar=pilot_bar)
    )
    console.print(f"[bold red]CO2 Release:[/bold red] {res.release_status.value} | Manifold Open: {res.main_manifold_valve_open} | Code: {res.alarm_code}")


@maritime_aux10_app.command("visc-check")
def check_visc(viscosity_cst: float = 13.5, fuel_temp_c: float = 128.0, ramp_c_min: float = 0.8) -> None:
    res = FuelOilViscometerHeaterEngine.evaluate(
        FuelViscometerTelemetry(viscosity_cst=viscosity_cst, fuel_temp_c=fuel_temp_c, temp_ramp_c_per_min=ramp_c_min)
    )
    console.print(f"[bold yellow]Viscometer:[/bold yellow] {res.control_state.value} | Steam Valve: {res.recommended_steam_valve_pct}% | Code: {res.alarm_code}")
