"""CLI Commands for Maritime Automation Phases 443-446."""

import typer
from rich.console import Console

from src.core.maritime.phase_443_cargo_deepwell_hydraulic_stripping import (
    DeepwellPumpEngine,
    DeepwellPumpTelemetry,
)
from src.core.maritime.phase_444_nitrogen_psa_membrane_purity import (
    NitrogenPsaEngine,
    NitrogenPsaTelemetry,
)
from src.core.maritime.phase_445_cargo_hold_h2s_extraction_fan import (
    ToxicGasExtractionEngine,
    ToxicGasExtractionTelemetry,
)
from src.core.maritime.phase_446_double_bottom_radar_overfill import (
    TankOverfillEngine,
    TankOverfillTelemetry,
)

app = typer.Typer(name="maritime-cargo", help="Maritime Cargo & Tank Safety (Phases 443-446)")
console = Console()


@app.command("pump-check")
def check_deepwell_pump(
    header_bar: float = typer.Option(230.0, help="Hydraulic header pressure in bar"),
    return_bar: float = typer.Option(18.0, help="Hydraulic return pressure in bar"),
    leakage_l_min: float = typer.Option(0.1, help="Cofferdam purge leakage L/min"),
    cargo_leak: bool = typer.Option(False, help="Cargo seal leakage flag"),
    oil_leak: bool = typer.Option(False, help="Hydraulic seal leakage flag"),
    suction_bar: float = typer.Option(0.35, help="Stripping suction pressure bar"),
    cargo_temp_c: float = typer.Option(25.0, help="Cargo temperature Celsius"),
) -> None:
    engine = DeepwellPumpEngine()
    telemetry = DeepwellPumpTelemetry(
        hydraulic_header_pressure_bar=header_bar,
        hydraulic_return_pressure_bar=return_bar,
        cofferdam_purge_leakage_l_min=leakage_l_min,
        cargo_leakage_detected=cargo_leak,
        hydraulic_oil_ingress=oil_leak,
        stripping_suction_pressure_bar=suction_bar,
        cargo_temp_celsius=cargo_temp_c,
    )
    result = engine.evaluate(telemetry)
    console.print(f"[bold]Deepwell Pump Safe:[/bold] {result.is_safe}")
    console.print(f"Throttle recommendation: {result.recommended_flow_throttle_pct}%")
    for alarm in result.active_alarms:
        console.print(f"[red]{alarm}[/red]")


@app.command("psa-check")
def check_psa_nitrogen(
    o2_pct: float = typer.Option(2.5, help="O2 concentration percentage"),
    feed_press_bar: float = typer.Option(8.2, help="Feed air pressure bar"),
    feed_temp_c: float = typer.Option(40.0, help="Feed air temperature C"),
    dew_point_c: float = typer.Option(-45.0, help="Feed air dew point C"),
    buffer_bar: float = typer.Option(7.5, help="Buffer tank pressure bar"),
) -> None:
    engine = NitrogenPsaEngine()
    telemetry = NitrogenPsaTelemetry(
        oxygen_content_pct=o2_pct,
        feed_air_pressure_bar=feed_press_bar,
        feed_air_temp_celsius=feed_temp_c,
        feed_air_dew_point_celsius=dew_point_c,
        buffer_tank_pressure_bar=buffer_bar,
    )
    result = engine.evaluate(telemetry)
    console.print(f"[bold]Nitrogen PSA Safe:[/bold] {result.is_safe}")
    console.print(f"Dump Valve Open: {result.dump_valve_open}")
    for alarm in result.active_alarms:
        console.print(f"[red]{alarm}[/red]")


@app.command("overfill-check")
def check_tank_overfill(
    sounding_pct: float = typer.Option(85.0, help="Radar sounding volume %"),
    high_high_sensor: bool = typer.Option(False, help="Independent high-high sensor tripped"),
    bunker_rate: float = typer.Option(150.0, help="Bunkering flow rate m3/h"),
    manifold_closed: bool = typer.Option(False, help="Manifold valve closed"),
    vent_mbar: float = typer.Option(5.0, help="Vent trunk pressure mbar"),
) -> None:
    engine = TankOverfillEngine()
    telemetry = TankOverfillTelemetry(
        radar_sounding_pct=sounding_pct,
        independent_high_high_sensor=high_high_sensor,
        bunker_flow_rate_m3_h=bunker_rate,
        manifold_valve_closed=manifold_closed,
        vent_trunk_pressure_mbar=vent_mbar,
    )
    result = engine.evaluate(telemetry)
    console.print(f"[bold]Overfill Protection Safe:[/bold] {result.is_safe}")
    console.print(f"Manifold Emergency Trip: {result.manifold_shutdown_tripped}")
    console.print(f"Time to Overflow: {result.time_to_overflow_seconds} seconds")
    for alarm in result.active_alarms:
        console.print(f"[red]{alarm}[/red]")
