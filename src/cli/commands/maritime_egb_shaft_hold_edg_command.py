"""Typer CLI commands for Maritime Phases 407-410.

Includes Exhaust Gas Boiler Soot Blow, Shaft Earthing Galvanic Potential,
Cargo Hold Dew Point Ventilation, and EDG 45s Blackout Recovery.
Strictly < 180 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_407_egb_economizer_soot_blow import (
    EgbEconomizerEngine,
    EgbEconomizerInput,
)
from src.core.maritime.phase_408_shaft_earthing_galvanic import (
    ShaftEarthingEngine,
    ShaftEarthingInput,
)
from src.core.maritime.phase_409_cargo_dewpoint_ventilation import (
    HoldPsychrometricInput,
    HoldVentilationEngine,
)
from src.core.maritime.phase_410_emergency_generator_blackout import (
    EdgBlackoutEngine,
    EdgBlackoutInput,
)

console = Console()

egb_app = typer.Typer(help="Phase 407: Exhaust Gas Boiler Economizer & Soot Blow (SOLAS II-2 Reg 4 / DNV Pt.4)")
shaftearth_app = typer.Typer(help="Phase 408: Shaft Earthing & Hull Galvanic Potential (DNV-RP-B401 / ISO 15541)")
holdvent_app = typer.Typer(help="Phase 409: Cargo Hold Dew Point & Hold Ventilation (IMSBC Code / IMO MSC.268(85))")
edgblackout_app = typer.Typer(help="Phase 410: Emergency Diesel Generator 45s Blackout Sequence (SOLAS II-1 Reg 42/43)")


@egb_app.callback(invoke_without_command=True)
def evaluate_egb(
    inlet_temp: float = typer.Option(310.0, "--inlet-temp", help="Exhaust gas inlet temp (°C)"),
    outlet_temp: float = typer.Option(175.0, "--outlet-temp", help="Economizer exit temp (°C)"),
    gas_dp: float = typer.Option(32.0, "--gas-dp", help="Gas differential pressure (mmWC)"),
    sat_temp: float = typer.Option(164.0, "--sat-temp", help="Boiler drum saturation temp (°C)"),
    circ_flow: float = typer.Option(24.0, "--circ-flow", help="Circulating water flow (m3/h)"),
    engine_load: float = typer.Option(75.0, "--engine-load", help="Main engine load (%)"),
    steam_p: float = typer.Option(8.5, "--steam-p", help="Soot blow steam pressure (bar)"),
):
    """Evaluate EGB heat recovery efficiency, soot fouling, and fire hazard index."""
    inp = EgbEconomizerInput(
        flue_gas_inlet_temp_c=inlet_temp,
        flue_gas_outlet_temp_c=outlet_temp,
        gas_differential_pressure_mmwc=gas_dp,
        steam_saturation_temp_c=sat_temp,
        circulation_water_flow_m3_h=circ_flow,
        main_engine_load_pct=engine_load,
        soot_blower_steam_pressure_bar=steam_p,
    )
    res = EgbEconomizerEngine().evaluate(inp)
    table = Table(title="Maritime Phase 407: EGB Economizer & Soot Blow (SOLAS II-2)")
    table.add_column("Metric", style="cyan")
    table.add_column("Evaluation", style="magenta")
    table.add_row("Status", res.status.value)
    table.add_row("Thermal Effectiveness", f"{res.heat_transfer_effectiveness:.3f}")
    table.add_row("Soot Blow Recommended", "YES" if res.soot_blow_recommended else "NO")
    table.add_row("Soot Blow Permitted", "YES" if res.soot_blow_permitted else "NO")
    table.add_row("Soot Fire Risk", "HIGH ALERT" if res.soot_fire_risk_detected else "NORMAL")
    console.print(table)


@shaftearth_app.callback(invoke_without_command=True)
def evaluate_shaft_earthing(
    shaft_mv: float = typer.Option(24.0, "--shaft-mv", help="Shaft-to-hull potential drop (mV)"),
    brush_ohm: float = typer.Option(0.025, "--brush-ohm", help="Silver-graphite brush resistance (Ohm)"),
    ref_mv: float = typer.Option(-920.0, "--ref-mv", help="Ag/AgCl reference electrode potential (mV)"),
    current_a: float = typer.Option(3.2, "--current-a", help="Shaft discharge bypass current (A)"),
):
    """Evaluate shaft grounding, bearing spark erosion risk, and hull cathodic potential."""
    inp = ShaftEarthingInput(
        shaft_voltage_mv=shaft_mv,
        brush_contact_resistance_ohm=brush_ohm,
        reference_electrode_mv=ref_mv,
        shaft_discharge_current_a=current_a,
    )
    res = ShaftEarthingEngine().evaluate(inp)
    table = Table(title="Maritime Phase 408: Shaft Earthing & Galvanic Protection (DNV-RP-B401)")
    table.add_column("Metric", style="cyan")
    table.add_column("Evaluation", style="magenta")
    table.add_row("Status", res.status.value)
    table.add_row("Shaft Voltage Safe", "YES" if res.shaft_voltage_safe else "HIGH")
    table.add_row("Brush Condition Safe", "YES" if res.brush_condition_safe else "WORN")
    table.add_row("Cathodic Potential Safe", "YES" if res.cathodic_potential_safe else "ANOMALY")
    table.add_row("Spark Erosion Risk", "CRITICAL" if res.bearing_spark_erosion_risk else "NEGLIGIBLE")
    console.print(table)


@holdvent_app.callback(invoke_without_command=True)
def evaluate_hold_vent(
    hold_temp: float = typer.Option(22.0, "--hold-temp", help="Hold air dry bulb temp (°C)"),
    hold_rh: float = typer.Option(78.0, "--hold-rh", help="Hold relative humidity (%)"),
    outside_temp: float = typer.Option(14.0, "--outside-temp", help="Outside air dry bulb temp (°C)"),
    outside_rh: float = typer.Option(65.0, "--outside-rh", help="Outside relative humidity (%)"),
    cargo_temp: float = typer.Option(20.0, "--cargo-temp", help="Bulk cargo surface temp (°C)"),
    deck_temp: float = typer.Option(12.0, "--deck-temp", help="Steel deckhead / hull temp (°C)"),
):
    """Evaluate Magnus-Tetens dew points and IMSBC ventilation rules to prevent cargo/ship sweat."""
    inp = HoldPsychrometricInput(
        hold_temp_c=hold_temp,
        hold_relative_humidity_pct=hold_rh,
        outside_temp_c=outside_temp,
        outside_relative_humidity_pct=outside_rh,
        cargo_surface_temp_c=cargo_temp,
        deckhead_hull_temp_c=deck_temp,
    )
    res = HoldVentilationEngine().evaluate(inp)
    table = Table(title="Maritime Phase 409: Cargo Hold Dew Point Ventilation (IMSBC Code)")
    table.add_column("Metric", style="cyan")
    table.add_column("Evaluation", style="magenta")
    table.add_row("Status", res.status.value)
    table.add_row("Hold Dew Point", f"{res.hold_dew_point_c}°C")
    table.add_row("Outside Dew Point", f"{res.outside_dew_point_c}°C")
    table.add_row("Cargo Sweat Risk", "ACTIVE" if res.cargo_sweat_risk else "NONE")
    table.add_row("Ship Sweat Risk", "ACTIVE" if res.ship_sweat_risk else "NONE")
    table.add_row("Ventilation Action", res.ventilation_action)
    console.print(table)


@edgblackout_app.callback(invoke_without_command=True)
def evaluate_edg_blackout(
    msb_v: float = typer.Option(0.0, "--msb-v", help="Main switchboard voltage (V)"),
    elapsed_s: float = typer.Option(18.5, "--elapsed-s", help="Seconds elapsed since blackout (s)"),
    air_bar: float = typer.Option(24.0, "--air-bar", help="Starting air pressure (bar)"),
    batt_v: float = typer.Option(26.2, "--batt-v", help="Starter battery terminal voltage (V)"),
    edg_hz: float = typer.Option(60.0, "--edg-hz", help="EDG alternator frequency (Hz)"),
    edg_v: float = typer.Option(442.0, "--edg-v", help="EDG alternator voltage (V)"),
    esb_closed: bool = typer.Option(True, "--esb-closed", help="ESB breaker closed status"),
):
    """Evaluate SOLAS 45s dead ship blackout recovery timeline and starting readiness."""
    inp = EdgBlackoutInput(
        msb_voltage_volts=msb_v,
        blackout_elapsed_sec=elapsed_s,
        starting_air_pressure_bar=air_bar,
        starter_battery_volts=batt_v,
        edg_frequency_hz=edg_hz,
        edg_voltage_volts=edg_v,
        esb_breaker_closed=esb_closed,
    )
    res = EdgBlackoutEngine().evaluate(inp)
    table = Table(title="Maritime Phase 410: EDG 45s Blackout Sequence (SOLAS II-1)")
    table.add_column("Metric", style="cyan")
    table.add_column("Evaluation", style="magenta")
    table.add_row("Status", res.status.value)
    table.add_row("SOLAS 45s Compliant", "YES" if res.solas_45s_compliant else "NO")
    table.add_row("Frequency Stabilized", "YES" if res.frequency_stabilized else "NO")
    table.add_row("Voltage Stabilized", "YES" if res.voltage_stabilized else "NO")
    table.add_row("Starting Energy OK", "YES" if res.starting_energy_sufficient else "LOW")
    table.add_row("Elapsed Time", f"{res.elapsed_time_sec:.1f} s")
    console.print(table)
