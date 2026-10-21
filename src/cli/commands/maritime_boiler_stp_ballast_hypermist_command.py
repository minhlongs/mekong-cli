"""CLI Commands for Maritime Phases 419-422.

Auxiliary Boiler, STP Chlorination, Ballast Anodes, and Hyper-Mist Fire Extinguishing.
Strictly < 140 LOC.
"""

import json
import typer
from rich.console import Console

from src.core.maritime.phase_419_boiler_drum_blowdown import BoilerDrumBlowdownEngine, BoilerDrumTelemetry
from src.core.maritime.phase_420_stp_electrolytic_chlorination import StpChlorinationEngine, StpChlorinationTelemetry
from src.core.maritime.phase_421_ballast_anodic_protection import BallastAnodicProtectionEngine, BallastAnodicTelemetry
from src.core.maritime.phase_422_hypermist_water_fire import HyperMistFireExtinguishingEngine, HyperMistTelemetry

boiler_app = typer.Typer(help="Phase 419: Marine Auxiliary Boiler Drum & Blowdown")
stp_app = typer.Typer(help="Phase 420: Marine STP Electrolytic Disinfection & Dechlorination")
ballast_app = typer.Typer(help="Phase 421: Ballast Tank Cathodic Protection & Anode Depletion")
hypermist_app = typer.Typer(help="Phase 422: Hyper-Mist Local Water-Based Machinery Fire Extinguishing")
console = Console()


@boiler_app.callback(invoke_without_command=True)
def assess_boiler(
    level_mm: float = typer.Option(0.0, "--level-mm", help="Drum water level in mm"),
    steam_tph: float = typer.Option(12.0, "--steam-tph", help="Steam mass flow in t/h"),
    pressure_bar: float = typer.Option(16.5, "--pressure-bar", help="Drum pressure in bar"),
    tds_ppm: float = typer.Option(2200.0, "--tds-ppm", help="TDS in ppm"),
    flame: bool = typer.Option(True, "--flame/--no-flame", help="Burner flame detected"),
) -> None:
    """Assess boiler drum level and blowdown requirements."""
    engine = BoilerDrumBlowdownEngine()
    telemetry = BoilerDrumTelemetry(
        drum_level_mm=level_mm,
        steam_mass_flow_tph=steam_tph,
        feedwater_flow_tph=steam_tph,
        drum_pressure_bar=pressure_bar,
        water_tds_ppm=tds_ppm,
        burner_flame_detected=flame,
    )
    res = engine.evaluate(telemetry)
    console.print(json.dumps({
        "status": res.status,
        "valve_demand": res.feedwater_valve_demand_pct,
        "surface_blowdown": res.surface_blowdown_active,
        "burner_tripped": res.burner_tripped,
    }, indent=2))


@stp_app.callback(invoke_without_command=True)
def assess_stp(
    current_a: float = typer.Option(25.0, "--current-a", help="Electrolytic cell current in A"),
    tank_trc: float = typer.Option(2.2, "--tank-trc", help="Contact tank TRC in ppm"),
    overboard_trc: float = typer.Option(0.2, "--overboard-trc", help="Overboard discharge TRC in ppm"),
    cod: float = typer.Option(95.0, "--cod", help="COD in mg/L"),
) -> None:
    """Assess STP disinfection and overboard discharge status."""
    engine = StpChlorinationEngine()
    telemetry = StpChlorinationTelemetry(
        cell_current_amperes=current_a,
        disinfection_tank_trc_ppm=tank_trc,
        overboard_trc_ppm=overboard_trc,
        chemical_oxygen_demand_mg_l=cod,
    )
    res = engine.evaluate(telemetry)
    console.print(json.dumps({
        "status": res.status,
        "disinfection_effective": res.disinfection_effective,
        "overboard_permitted": res.overboard_discharge_permitted,
    }, indent=2))


@ballast_app.callback(invoke_without_command=True)
def assess_ballast(
    potential_mv: float = typer.Option(-920.0, "--potential-mv", help="Ag/AgCl potential in mV"),
    current_a: float = typer.Option(4.8, "--current-a", help="Applied circuit current in A"),
    hours: float = typer.Option(4800.0, "--hours", help="Operating hours"),
) -> None:
    """Assess cathodic protection and sacrificial zinc mass depletion."""
    engine = BallastAnodicProtectionEngine()
    telemetry = BallastAnodicTelemetry(
        ref_electrode_potential_mv=potential_mv,
        applied_current_amperes=current_a,
        accumulated_operating_hours=hours,
    )
    res = engine.evaluate(telemetry)
    console.print(json.dumps({
        "status": res.status,
        "polarization_adequate": res.polarization_adequate,
        "remaining_anode_life_pct": res.remaining_anode_life_pct,
    }, indent=2))


@hypermist_app.callback(invoke_without_command=True)
def assess_hypermist(
    flame: bool = typer.Option(False, "--flame", help="UV/IR flame sensor"),
    heat: bool = typer.Option(False, "--heat", help="Thermal heat sensor"),
    pressure_bar: float = typer.Option(142.0, "--pressure-bar", help="Pump discharge pressure in bar"),
) -> None:
    """Assess hyper-mist fire detection and actuation."""
    engine = HyperMistFireExtinguishingEngine()
    telemetry = HyperMistTelemetry(
        uv_ir_flame_detected=flame,
        thermal_heat_detected=heat,
        pump_discharge_pressure_bar=pressure_bar,
    )
    res = engine.evaluate(telemetry)
    console.print(json.dumps({
        "status": res.status,
        "fire_confirmed": res.fire_confirmed,
        "pump_active": res.pump_active,
    }, indent=2))
