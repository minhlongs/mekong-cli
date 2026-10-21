"""Typer CLI command groups for Maritime Phases 439-442.

Supports: thruster, incinerator, hydrophore, bwmsneutral.
Strictly < 120 LOC, zero mocks.
"""

import typer
from src.core.maritime.phase_439_bow_thruster_hydraulic_interlocks import (
    BowThrusterEngine,
    BowThrusterTelemetry,
)
from src.core.maritime.phase_440_marine_incinerator_safety import (
    IncineratorEngine,
    IncineratorTelemetry,
)
from src.core.maritime.phase_441_hydrophore_fresh_water_control import (
    HydrophoreEngine,
    HydrophoreTelemetry,
)
from src.core.maritime.phase_442_bwms_tro_neutralization import (
    BwmsNeutralizationEngine,
    BwmsNeutralizationTelemetry,
)

thruster_app = typer.Typer(help="Bow Thruster Hydraulic Interlocks (Phase 439)")
incinerator_app = typer.Typer(help="Marine Incinerator Flue Gas & O2 Safety (Phase 440)")
hydrophore_app = typer.Typer(help="Hydrophore Sanitary Fresh Water Control (Phase 441)")
bwms_app = typer.Typer(help="BWMS TRO Neutralization & Overboard Safety (Phase 442)")


@thruster_app.command("check")
def check_thruster(
    press: float = typer.Option(185.0, "--press", help="Header pressure in bar"),
    temp: float = typer.Option(52.0, "--temp", help="Oil temp in C"),
    tank: float = typer.Option(60.0, "--tank", help="Gravity tank pct"),
    demand: float = typer.Option(15.0, "--demand", help="Pitch demand deg"),
    actual: float = typer.Option(15.2, "--actual", help="Pitch actual deg"),
    current: float = typer.Option(320.0, "--current", help="Motor current A"),
) -> None:
    telemetry = BowThrusterTelemetry(
        header_pressure_bar=press,
        oil_temperature_c=temp,
        gravity_tank_level_pct=tank,
        pitch_demand_deg=demand,
        pitch_actual_deg=actual,
        motor_current_a=current,
    )
    res = BowThrusterEngine().evaluate(telemetry)
    typer.echo(f"Operational: {res.is_operational} | {res.summary_en}")


@incinerator_app.command("check")
def check_incinerator(
    comb: float = typer.Option(950.0, "--comb", help="Combustion chamber temp C"),
    flue: float = typer.Option(310.0, "--flue", help="Flue gas temp C"),
    o2: float = typer.Option(8.5, "--o2", help="Oxygen residual pct vol"),
    draft: float = typer.Option(-3.5, "--draft", help="Furnace draft mbar"),
    visc: float = typer.Option(12.0, "--visc", help="Sludge viscosity cSt"),
) -> None:
    telemetry = IncineratorTelemetry(
        combustion_temp_c=comb,
        flue_gas_temp_c=flue,
        oxygen_residual_pct=o2,
        furnace_draft_mbar=draft,
        sludge_viscosity_cst=visc,
    )
    res = IncineratorEngine().evaluate(telemetry)
    typer.echo(f"Safe to burn: {res.is_safe_to_burn_sludge} | {res.summary_en}")


@hydrophore_app.command("check")
def check_hydrophore(
    press: float = typer.Option(4.2, "--press", help="System pressure bar"),
    water: float = typer.Option(68.0, "--water", help="Water volume pct"),
    uv: float = typer.Option(45.0, "--uv", help="UV dose mJ/cm2"),
    pump1: bool = typer.Option(True, "--pump1", help="Pump 1 currently running"),
) -> None:
    telemetry = HydrophoreTelemetry(
        system_pressure_bar=press,
        water_volume_pct=water,
        uv_intensity_dose_mj_cm2=uv,
    )
    res = HydrophoreEngine().evaluate(telemetry, pump1)
    typer.echo(f"Pump1: {res.is_pump1_running}, Pump2: {res.is_pump2_running} | {res.summary_en}")


@bwms_app.command("check")
def check_bwms(
    tro: float = typer.Option(0.04, "--tro", help="Effluent TRO mg/L"),
    neut: float = typer.Option(12.5, "--neut", help="Neutralizer flow L/h"),
    ballast: float = typer.Option(200.0, "--ballast", help="Ballast discharge m3/h"),
    orp: float = typer.Option(280.0, "--orp", help="Redox potential mV"),
    sample: bool = typer.Option(True, "--sample", help="Sample pump running"),
) -> None:
    telemetry = BwmsNeutralizationTelemetry(
        effluent_tro_mg_l=tro,
        neutralizer_dosing_flow_l_h=neut,
        ballast_discharge_flow_m3_h=ballast,
        redox_potential_orp_mv=orp,
        sample_pump_running=sample,
    )
    res = BwmsNeutralizationEngine().evaluate(telemetry)
    typer.echo(f"Discharge Permitted: {res.is_overboard_discharge_permitted} | {res.summary_en}")
