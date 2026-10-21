"""CLI Command for Maritime Phases 455-458 Automation & Safety Engine.

Provides Typer commands for Crankcase Valve, Boiler Deaerator, Fuel Homogenizer,
and Reefer Socket Protection checks.
"""

import json
import typer
from src.core.maritime.phase_455_crankcase_explosion_relief_valve import (
    CrankcaseExplosionReliefEngine,
    CrankcaseValveTelemetry,
)
from src.core.maritime.phase_456_boiler_feedwater_deaerator import (
    BoilerFeedwaterDeaeratorEngine,
    DeaeratorTelemetry,
)
from src.core.maritime.phase_457_fuel_oil_homogenizer_viscosity import (
    FuelHomogenizerViscosityEngine,
    FuelHomogenizerTelemetry,
)
from src.core.maritime.phase_458_reefer_container_socket_protection import (
    ReeferContainerSocketEngine,
    ReeferSocketTelemetry,
)

maritime_crankcase_app = typer.Typer(
    name="maritime-safe",
    help="Marine crankcase, deaerator, homogenizer & reefer diagnostics.",
)


@maritime_crankcase_app.command("crankcase-check")
def crankcase_check(
    pressure_bar: float = typer.Option(0.05, help="Crankcase pressure in bar"),
    lift_mm: float = typer.Option(0.0, help="Relief valve lift in mm"),
    reseated: bool = typer.Option(True, help="Relief valve spring re-seated"),
    mesh_clear_pct: float = typer.Option(95.0, help="Flame arrester clear area %"),
    mesh_temp_c: float = typer.Option(50.0, help="Flame mesh exit temp in C"),
) -> None:
    telemetry = CrankcaseValveTelemetry(
        crankcase_pressure_bar=pressure_bar,
        valve_lift_mm=lift_mm,
        relief_reseated=reseated,
        flame_mesh_clear_pct=mesh_clear_pct,
        flame_mesh_temp_celsius=mesh_temp_c,
    )
    res = CrankcaseExplosionReliefEngine.evaluate(telemetry)
    typer.echo(json.dumps({"status": res.status.value, "remarks": res.remarks}))


@maritime_crankcase_app.command("deaerator-check")
def deaerator_check(
    steam_p_bar: float = typer.Option(0.35, help="Steam pressure bar"),
    water_t_c: float = typer.Option(108.0, help="Water temperature C"),
    o2_ppb: float = typer.Option(4.0, help="Dissolved oxygen ppb"),
    chem_ppm: float = typer.Option(25.0, help="Scavenging reserve ppm"),
    tank_lvl_pct: float = typer.Option(60.0, help="Storage tank level %"),
) -> None:
    telemetry = DeaeratorTelemetry(
        steam_pressure_bar=steam_p_bar,
        water_temperature_celsius=water_t_c,
        dissolved_oxygen_ppb=o2_ppb,
        chemical_reserve_ppm=chem_ppm,
        storage_tank_level_pct=tank_lvl_pct,
    )
    res = BoilerFeedwaterDeaeratorEngine.evaluate(telemetry)
    typer.echo(json.dumps({"status": res.status.value, "remarks": res.remarks}))


@maritime_crankcase_app.command("homogenizer-check")
def homogenizer_check(
    cav_khz: float = typer.Option(24.0, help="Cavitation frequency kHz"),
    asphalt_um: float = typer.Option(2.5, help="Asphaltene size um"),
    visc_cst: float = typer.Option(12.5, help="Kinematic viscosity cSt"),
    p_bar: float = typer.Option(7.5, help="Booster pressure bar"),
    temp_c: float = typer.Option(135.0, help="Fuel temperature C"),
) -> None:
    telemetry = FuelHomogenizerTelemetry(
        cavitation_freq_khz=cav_khz,
        asphaltene_cluster_size_um=asphalt_um,
        kinematic_viscosity_cst=visc_cst,
        booster_pressure_bar=p_bar,
        fuel_temp_celsius=temp_c,
    )
    res = FuelHomogenizerViscosityEngine.evaluate(telemetry)
    typer.echo(json.dumps({"status": res.status.value, "remarks": res.remarks}))


@maritime_crankcase_app.command("reefer-check")
def reefer_check(
    v_ll: float = typer.Option(440.0, help="Supply voltage V"),
    amps: float = typer.Option(22.0, help="Load amps"),
    leak_ma: float = typer.Option(5.0, help="Earth leakage mA"),
    pin_temp_c: float = typer.Option(45.0, help="Pin temp C"),
    sw_eng: bool = typer.Option(True, help="Switch engaged"),
    plug_in: bool = typer.Option(True, help="Plug inserted"),
) -> None:
    telemetry = ReeferSocketTelemetry(
        voltage_l_l_volts=v_ll,
        current_load_amps=amps,
        earth_leakage_ma=leak_ma,
        pin_temperature_celsius=pin_temp_c,
        rotary_switch_engaged=sw_eng,
        plug_inserted=plug_in,
    )
    res = ReeferContainerSocketEngine.evaluate(telemetry)
    typer.echo(json.dumps({"status": res.status.value, "remarks": res.remarks}))
