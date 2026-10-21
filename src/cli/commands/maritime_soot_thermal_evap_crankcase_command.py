"""CLI Commands for Maritime Phases 423-426.

Economizer Soot Washing, Thermal Oil Heaters, Bilge Vacuum Evaporators, and Crankcase OMD.
Strictly < 140 LOC.
"""

import json
import typer
from rich.console import Console

from src.core.maritime.phase_423_economizer_soot_wash_fire import (
    EconomizerSootWaterWashEngine,
    EconomizerSootTelemetry,
)
from src.core.maritime.phase_424_thermal_oil_heater_expansion import (
    ThermalOilHeaterExpansionEngine,
    ThermalOilTelemetry,
)
from src.core.maritime.phase_425_bilge_vacuum_evaporator import (
    BilgeVacuumEvaporatorEngine,
    BilgeVacuumEvaporatorTelemetry,
)
from src.core.maritime.phase_426_crankcase_relief_oil_mist import (
    CrankcaseReliefMistEngine,
    CrankcaseReliefMistTelemetry,
)

economizer_app = typer.Typer(help="Phase 423: Marine Economizer Soot Wash & Fire Prevention")
thermal_oil_app = typer.Typer(help="Phase 424: Thermal Oil Heater & Expansion Tank Closed-Loop")
bilge_evap_app = typer.Typer(help="Phase 425: Bilge Water Vacuum Evaporator & Sludge Distillation")
crankcase_app = typer.Typer(help="Phase 426: Crankcase Explosion Relief & Gravimetric Oil Mist")
console = Console()


@economizer_app.callback(invoke_without_command=True)
def assess_economizer(
    dp_kpa: float = typer.Option(1.65, "--dp-kpa", help="Differential pressure across gas bank (kPa)"),
    temp_outlet_c: float = typer.Option(175.0, "--temp-outlet-c", help="Exhaust gas outlet temp (°C)"),
    rise_rate_c_min: float = typer.Option(1.2, "--rise-rate-c-min", help="Exhaust temp rise rate (°C/min)"),
    wash_active: bool = typer.Option(False, "--wash-active/--no-wash", help="Active soot wash"),
    holding_ph: float = typer.Option(7.1, "--holding-ph", help="Washwater holding tank pH"),
) -> None:
    """Assess economizer soot fouling, runaway fire hazards, and wash neutralization."""
    engine = EconomizerSootWaterWashEngine()
    telem = EconomizerSootTelemetry(
        differential_pressure_kpa=dp_kpa,
        exhaust_gas_outlet_temp_c=temp_outlet_c,
        temp_rise_rate_c_min=rise_rate_c_min,
        soot_wash_active=wash_active,
        holding_tank_ph=holding_ph,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "soot_fouling_index": res.soot_fouling_index,
        "emergency_soot_fire_trip": res.emergency_soot_fire_trip,
        "naoh_dosing_rate_l_h": res.naoh_dosing_rate_l_h,
    }, indent=2))


@thermal_oil_app.callback(invoke_without_command=True)
def assess_thermal_oil(
    heater_outlet_c: float = typer.Option(260.0, "--heater-outlet-c", help="Heater outlet temp (°C)"),
    heat_flux_kw: float = typer.Option(45.0, "--heat-flux-kw", help="Heat flux (kW/m²)"),
    flow_v: float = typer.Option(2.4, "--flow-v", help="Flow velocity (m/s)"),
    n2_bar: float = typer.Option(0.35, "--n2-bar", help="Nitrogen blanket pressure (bar)"),
    tank_level_pct: float = typer.Option(55.0, "--tank-level-pct", help="Expansion tank level (%)"),
) -> None:
    """Assess thermal oil film degradation, turbulent circulation, and N2 blanket."""
    engine = ThermalOilHeaterExpansionEngine()
    telem = ThermalOilTelemetry(
        heater_outlet_temp_c=heater_outlet_c,
        heat_flux_kw_m2=heat_flux_kw,
        flow_velocity_m_s=flow_v,
        n2_blanket_pressure_bar=n2_bar,
        expansion_tank_level_pct=tank_level_pct,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "film_temperature_c": res.film_temperature_c,
        "reynolds_number": res.reynolds_number,
        "burner_trip_demanded": res.burner_trip_demanded,
    }, indent=2))


@bilge_evap_app.callback(invoke_without_command=True)
def assess_bilge_evaporator(
    vac_bar: float = typer.Option(0.15, "--vac-bar", help="Vacuum pressure (bar abs)"),
    chamber_temp_c: float = typer.Option(54.0, "--chamber-temp-c", help="Evaporation chamber temp (°C)"),
    distillate_ppm: float = typer.Option(2.1, "--distillate-ppm", help="Distillate oil ppm"),
    sludge_pct: float = typer.Option(68.0, "--sludge-pct", help="Sludge concentrate oil %"),
    foam: bool = typer.Option(False, "--foam/--no-foam", help="Chamber foam detected"),
) -> None:
    """Assess sub-atmospheric bilge water distillation and oil concentration."""
    engine = BilgeVacuumEvaporatorEngine()
    telem = BilgeVacuumEvaporatorTelemetry(
        vacuum_pressure_bar_abs=vac_bar,
        evaporation_chamber_temp_c=chamber_temp_c,
        distillate_oil_ppm=distillate_ppm,
        sludge_concentrate_oil_pct=sludge_pct,
        foam_detected=foam,
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "theoretical_boiling_temp_c": res.theoretical_boiling_temp_c,
        "distillate_purity_compliant": res.distillate_purity_compliant,
        "overboard_discharge_permitted": res.overboard_discharge_permitted,
    }, indent=2))


@crankcase_app.callback(invoke_without_command=True)
def assess_crankcase_omd(
    volume_m3: float = typer.Option(48.0, "--volume-m3", help="Engine crankcase volume (m³)"),
    area_cm2: float = typer.Option(2500.0, "--area-cm2", help="Installed relief valve area (cm²)"),
    intensity_ratio: float = typer.Option(0.85, "--intensity-ratio", help="Optical intensity ratio I/I0"),
    bearing_delta: float = typer.Option(3.0, "--bearing-delta", help="Max bearing temp deviation (°C)"),
) -> None:
    """Assess crankcase explosion relief sizing, gravimetric oil mist, and shutdown."""
    engine = CrankcaseReliefMistEngine()
    telem = CrankcaseReliefMistTelemetry(
        crankcase_volume_m3=volume_m3,
        installed_relief_valve_area_cm2=area_cm2,
        optical_intensity_i=intensity_ratio * 100.0,
        optical_intensity_i0=100.0,
        bearing_temperatures_c=(72.0, 72.0 + bearing_delta),
    )
    res = engine.evaluate(telem)
    console.print(json.dumps({
        "status": res.status,
        "oil_mist_concentration_mg_l": res.oil_mist_concentration_mg_l,
        "emergency_slowdown_trip": res.emergency_slowdown_trip,
        "relief_area_compliant": res.relief_area_compliant,
    }, indent=2))
