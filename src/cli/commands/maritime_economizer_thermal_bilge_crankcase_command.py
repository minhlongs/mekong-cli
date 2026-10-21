"""CLI Commands for Maritime Phases 423-426.

Economizer Soot Wash, Thermal Oil System, Bilge Water Evaporator, and Crankcase Relief & OMD.
Strictly < 160 LOC.
"""

import json
import typer
from rich.console import Console

from src.core.maritime.phase_423_economizer_soot_wash import (
    EconomizerSootWashEngine,
    EconomizerSootWashTelemetry,
)
from src.core.maritime.phase_424_thermal_oil_system import (
    ThermalOilSystemEngine,
    ThermalOilTelemetry,
)
from src.core.maritime.phase_425_bilge_water_evaporator import (
    BilgeEvaporatorEngine,
    BilgeEvaporatorTelemetry,
)
from src.core.maritime.phase_426_crankcase_relief_omd import (
    CrankcaseOmdEngine,
    CrankcaseOmdTelemetry,
)

sootwash_app = typer.Typer(help="Phase 423: Economizer Soot Water Washing & Delta-P (MEPC.340(77))")
thermaloil_app = typer.Typer(help="Phase 424: Marine Thermal Oil Heating System & N2 Blanketing (DIN 4754)")
bilgeevap_app = typer.Typer(help="Phase 425: Machinery Bilge Vacuum Evaporator & Distillation (MARPOL Annex I)")
crankcasesafety_app = typer.Typer(help="Phase 426: Crankcase Explosion Relief & OMD (IACS UR M9/M10)")
console = Console()


@sootwash_app.callback(invoke_without_command=True)
def assess_sootwash(
    inlet_temp_c: float = typer.Option(310.0, "--inlet-temp", help="Exhaust gas inlet temp in °C"),
    diff_p_kpa: float = typer.Option(1.1, "--diff-p", help="Gas-side differential pressure in kPa"),
    damper_pct: float = typer.Option(0.0, "--damper-pct", help="Bypass damper open % (100% required for wash)"),
    wash_bar: float = typer.Option(0.0, "--wash-bar", help="Wash water pressure in bar"),
    wash_active: bool = typer.Option(False, "--wash/--no-wash", help="Wash water deluge active"),
) -> None:
    """Assess economizer differential pressure, fouling, and soot fire safety."""
    engine = EconomizerSootWashEngine()
    telem = EconomizerSootWashTelemetry(
        gas_inlet_temp_c=inlet_temp_c,
        gas_diff_pressure_kpa=diff_p_kpa,
        bypass_damper_open_pct=damper_pct,
        wash_water_pressure_bar=wash_bar,
        wash_active=wash_active,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "fouling_pct": res.fouling_severity_pct,
        "soot_fire_pre_alarm": res.soot_fire_pre_alarm,
        "emergency_trip": res.soot_fire_emergency_trip,
        "wash_permit": res.wash_permit_granted,
    }, indent=2))


@thermaloil_app.callback(invoke_without_command=True)
def assess_thermaloil(
    bulk_c: float = typer.Option(260.0, "--bulk-c", help="Bulk oil temperature in °C"),
    film_c: float = typer.Option(295.0, "--film-c", help="Heater tube film temperature in °C"),
    diff_bar: float = typer.Option(1.8, "--diff-bar", help="Circulation differential pressure across heater in bar"),
    tank_level_pct: float = typer.Option(65.0, "--tank-level", help="Expansion tank level %"),
    n2_bar: float = typer.Option(0.35, "--n2-bar", help="Expansion tank N2 blanket pressure in bar"),
) -> None:
    """Assess thermal oil heater dynamics, coking risk, and N2 blanketing."""
    engine = ThermalOilSystemEngine()
    telem = ThermalOilTelemetry(
        bulk_temp_c=bulk_c,
        film_temp_c=film_c,
        heater_diff_pressure_bar=diff_bar,
        expansion_tank_level_pct=tank_level_pct,
        n2_blanket_pressure_bar=n2_bar,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "burner_clear": res.burner_interlock_clear,
        "emergency_trip": res.emergency_burner_trip,
        "film_overheat": res.film_overheat_detected,
    }, indent=2))


@bilgeevap_app.callback(invoke_without_command=True)
def assess_bilgeevap(
    vacuum_bar: float = typer.Option(0.22, "--vacuum-bar", help="Chamber vacuum pressure in bar"),
    foam_mm: float = typer.Option(40.0, "--foam-mm", help="Boiling chamber foam level in mm"),
    oil_ppm: float = typer.Option(1.2, "--oil-ppm", help="Distillate oil concentration in ppm"),
) -> None:
    """Assess vacuum bilge evaporator distillation and MARPOL discharge."""
    engine = BilgeEvaporatorEngine()
    telem = BilgeEvaporatorTelemetry(
        chamber_pressure_bar=vacuum_bar,
        foam_level_mm=foam_mm,
        distillate_oil_ppm=oil_ppm,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "overboard_permitted": res.overboard_discharge_permitted,
        "defoamer_dosing": res.defoamer_dosing_active,
        "efficiency_pct": res.distillation_efficiency_pct,
    }, indent=2))


@crankcasesafety_app.callback(invoke_without_command=True)
def assess_crankcasesafety(
    mist_mg_l: float = typer.Option(0.25, "--mist-mg-l", help="Oil mist concentration in mg/L"),
    relief_bar: float = typer.Option(0.05, "--relief-bar", help="Crankcase relief valve pressure in bar"),
    door_request: bool = typer.Option(False, "--door-open", help="Door opening requested"),
    engine_stopped: bool = typer.Option(False, "--stopped/--running", help="Engine stopped state"),
    cooling_min: float = typer.Option(30.0, "--cooling-min", help="Minutes since engine stopped"),
) -> None:
    """Assess crankcase oil mist detection, relief valve, and anti-explosion lockouts."""
    engine = CrankcaseOmdEngine()
    telem = CrankcaseOmdTelemetry(
        mist_concentration_mg_l=mist_mg_l,
        relief_valve_pressure_bar=relief_bar,
        crankcase_door_open_requested=door_request,
        engine_stopped=engine_stopped,
        minutes_since_engine_stop=cooling_min,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "mist_lel_pct": res.mist_percent_lel,
        "pre_alarm": res.pre_alarm_active,
        "emergency_slowdown": res.emergency_slowdown_trip,
        "door_lockout": res.door_opening_lockout_active,
    }, indent=2))
