"""Typer CLI commands for Maritime Phases 415-418.

Includes:
- CPP Propeller & OD Box Hydraulics (Phase 415 DNV Pt.4 Ch.5, SOLAS II-1)
- Marine Fuel Homogenizer & Water Emulsion (Phase 416 MARPOL Annex VI, ISO 8217)
- Cargo Hold Dew Point & Desiccant Wheel (Phase 417 IMSBC Code, DNV Cargo Care)
- Crankcase Explosion Relief Valve & OMD (Phase 418 SOLAS II-1 Reg 47, IACS M9/M10)

Strictly < 200 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_415_cpp_propeller_odbox_hydraulics import (
    CppPropellerOdBoxEngine,
    CppPropellerTelemetry,
)
from src.core.maritime.phase_416_fuel_homogenizer_emulsion import (
    FuelHomogenizerEmulsionEngine,
    FuelHomogenizerTelemetry,
)
from src.core.maritime.phase_417_cargo_hold_dewpoint_desiccant import (
    CargoHoldDewPointEngine,
    CargoHoldDewPointTelemetry,
)
from src.core.maritime.phase_418_crankcase_relief_oil_mist_detector import (
    CrankcaseReliefOmdEngine,
    CrankcaseOmdTelemetry,
)

console = Console()

cpppropeller_app = typer.Typer(help="Phase 415: Propeller CPP & OD Box Hydraulics (DNV Pt.4 / SOLAS II-1)")
fuelhomogenizer_app = typer.Typer(help="Phase 416: Fuel Homogenizer & Water Emulsion (MARPOL VI / ISO 8217)")
cargodewpoint_app = typer.Typer(help="Phase 417: Cargo Hold Dew Point & Desiccant Wheel (IMSBC Code)")
crankcaseomd_app = typer.Typer(help="Phase 418: Crankcase Explosion Relief & OMD (SOLAS II-1 / IACS M10)")


@cpppropeller_app.callback(invoke_without_command=True)
def evaluate_cpp_propeller(
    pitch_cmd: float = typer.Option(18.0, "--pitch-cmd", help="Commanded pitch angle (deg)"),
    pitch_act: float = typer.Option(17.8, "--pitch-act", help="Actual measured pitch angle (deg)"),
    servo_a: float = typer.Option(48.0, "--servo-a", help="Port A servo pressure (bar)"),
    servo_b: float = typer.Option(22.0, "--servo-b", help="Port B servo pressure (bar)"),
    rpm: float = typer.Option(120.0, "--rpm", help="Shaft speed (RPM)"),
    speed_knots: float = typer.Option(15.0, "--speed", help="Ship speed (knots)"),
    lock_pin: bool = typer.Option(False, "--lock-pin", help="Emergency lock-pin engaged"),
):
    """Evaluate CPP pitch tracking, hydrodynamic thrust, and OD box seal leakage."""
    telem = CppPropellerTelemetry(
        commanded_pitch_deg=pitch_cmd,
        actual_pitch_deg=pitch_act,
        servo_port_a_pressure_bar=servo_a,
        servo_port_b_pressure_bar=servo_b,
        shaft_speed_rpm=rpm,
        ship_speed_knots=speed_knots,
        emergency_lock_pin_engaged=lock_pin,
    )
    res = CppPropellerOdBoxEngine().evaluate(telem)

    table = Table(title="Maritime Phase 415: CPP & OD Box Hydraulics (DNV Pt.4)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Advance Ratio (J)", f"{res.advance_ratio_j:.4f}")
    table.add_row("Servo Differential Pressure", f"{res.differential_servo_pressure_bar:.1f} bar")
    table.add_row("Thrust Force", f"{res.thrust_force_kn:.1f} kN")
    table.add_row("OD Box Seal Leakage", f"{res.odbox_seal_leakage_lpm:.3f} LPM")
    table.add_row("Pitch Error", f"{res.pitch_tracking_error_deg:.2f}°")
    table.add_row("Failsafe Lock-Pin", "ENGAGED" if res.fail_safe_locked else "DISENGAGED")
    console.print(table)


@fuelhomogenizer_app.callback(invoke_without_command=True)
def evaluate_fuel_homogenizer(
    rpm: float = typer.Option(3000.0, "--rpm", help="Homogenizer rotor speed (RPM)"),
    water_pct: float = typer.Option(4.5, "--water-pct", help="Water dosing ratio (%)"),
    inlet_temp: float = typer.Option(95.0, "--temp-c", help="Fuel inlet temperature (°C)"),
    target_visc: float = typer.Option(13.0, "--target-visc", help="Target engine viscosity (cSt)"),
):
    """Evaluate Fuel Homogenizer droplet shear, micro-explosion, and NOx reduction."""
    telem = FuelHomogenizerTelemetry(
        rotor_speed_rpm=rpm,
        water_dosing_ratio_pct=water_pct,
        fuel_inlet_temp_c=inlet_temp,
        target_engine_viscosity_cst=target_visc,
    )
    res = FuelHomogenizerEmulsionEngine().evaluate(telem)

    table = Table(title="Maritime Phase 416: Fuel Homogenizer & Emulsion (MARPOL VI)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Shear Rate", f"{res.shear_rate_s_minus_1:.0f} s⁻¹")
    table.add_row("Mean Droplet Size", f"{res.mean_water_droplet_um:.2f} µm")
    table.add_row("Calculated Viscosity", f"{res.calculated_viscosity_cst:.2f} cSt")
    table.add_row("Steam Valve Command", f"{res.steam_valve_command_pct:.1f}%")
    table.add_row("NOx Reduction", f"{res.estimated_nox_reduction_pct:.1f}%")
    table.add_row("Micro-Explosion", res.micro_explosion_potential)
    console.print(table)


@cargodewpoint_app.callback(invoke_without_command=True)
def evaluate_cargo_dewpoint(
    hold_temp: float = typer.Option(24.0, "--hold-temp", help="Hold temperature (°C)"),
    hold_rh: float = typer.Option(78.0, "--hold-rh", help="Hold relative humidity (%)"),
    amb_temp: float = typer.Option(28.0, "--amb-temp", help="Ambient temperature (°C)"),
    amb_rh: float = typer.Option(85.0, "--amb-rh", help="Ambient relative humidity (%)"),
    seawater_temp: float = typer.Option(16.0, "--sw-temp", help="Seawater temperature (°C)"),
    cargo_temp: float = typer.Option(18.0, "--cargo-temp", help="Cargo surface temperature (°C)"),
    rain: bool = typer.Option(False, "--rain", help="Outside precipitation/fog active"),
):
    """Evaluate cargo vs ship sweat risks, ventilation rules, and desiccant wheel."""
    telem = CargoHoldDewPointTelemetry(
        hold_temp_c=hold_temp,
        hold_relative_humidity_pct=hold_rh,
        ambient_air_temp_c=amb_temp,
        ambient_relative_humidity_pct=amb_rh,
        seawater_temp_c=seawater_temp,
        cargo_surface_temp_c=cargo_temp,
        outside_rain_or_fog=rain,
    )
    res = CargoHoldDewPointEngine().evaluate(telem)

    table = Table(title="Maritime Phase 417: Cargo Hold Dew Point & Desiccant (IMSBC)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Hold Dew Point", f"{res.hold_dew_point_c:.2f}°C")
    table.add_row("Ambient Dew Point", f"{res.ambient_dew_point_c:.2f}°C")
    table.add_row("Ship Sweat Margin", f"{res.ship_sweat_margin_c:.2f}°C")
    table.add_row("Cargo Sweat Margin", f"{res.cargo_sweat_margin_c:.2f}°C")
    table.add_row("Ventilation Rule", res.ventilation_rule)
    table.add_row("Desiccant Wheel Active", "YES" if res.desiccant_wheel_active else "NO")
    table.add_row("Moisture Extraction", f"{res.moisture_removal_rate_kg_h:.2f} kg/h")
    console.print(table)


@crankcaseomd_app.callback(invoke_without_command=True)
def evaluate_crankcase_omd(
    sample_trans: float = typer.Option(94.0, "--trans-pct", help="Sample optical transmission (%)"),
    ref_trans: float = typer.Option(99.0, "--ref-pct", help="Reference optical transmission (%)"),
    max_hotspot: float = typer.Option(75.0, "--hotspot-c", help="Highest bearing temp (°C)"),
    press_mbar: float = typer.Option(-2.5, "--press-mbar", help="Crankcase pressure (mbar)"),
):
    """Evaluate Crankcase optical oil mist density, bearing hotspot, and relief valves."""
    telem = CrankcaseOmdTelemetry(
        sample_cell_transmission_pct=sample_trans,
        reference_cell_transmission_pct=ref_trans,
        compartment_hotspot_temps_c=(max_hotspot - 3.0, max_hotspot, max_hotspot - 1.5),
        crankcase_internal_pressure_mbar=press_mbar,
    )
    res = CrankcaseReliefOmdEngine().evaluate(telem)

    table = Table(title="Maritime Phase 418: Crankcase OMD & Relief Valve (IACS M10)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Oil Mist Density", f"{res.oil_mist_concentration_mg_l:.3f} mg/L")
    table.add_row("LEL Concentration", f"{res.lel_percentage:.2f}%")
    table.add_row("Hotspot Temperature", f"{res.max_bearing_hotspot_temp_c:.1f}°C")
    table.add_row("Relief Valve Lifted", "YES" if res.relief_valve_lifted else "NO")
    table.add_row("Engine Slowdown Signal", "TRIPPED" if res.engine_slowdown_required else "CLEAR")
    console.print(table)
