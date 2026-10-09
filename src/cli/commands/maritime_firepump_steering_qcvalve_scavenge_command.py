"""Typer CLI commands for Maritime Phases 395-398.

Includes Emergency Fire Pump, Steering Gear Dual Hydraulic,
Quick-Closing Valves, and Scavenge Air Fire Interlock.
Strictly < 200 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_395_emergency_fire_pump_sea_suction import (
    EmergencyFirePumpEngine,
    EmergencyFirePumpInput,
)
from src.core.maritime.phase_396_steering_gear_dual_hydraulic import (
    SteeringGearEngine,
    SteeringGearInput,
)
from src.core.maritime.phase_397_quick_closing_valve_emergency_shutoff import (
    QuickClosingValveEngine,
    QuickClosingValveInput,
)
from src.core.maritime.phase_398_scavenge_air_fire_detection import (
    ScavengeFireEngine,
    ScavengeFireInput,
)

console = Console()

firepump_app = typer.Typer(help="Phase 395: Emergency Fire Pump & Sea Suction Priming (SOLAS II-2 Reg 10)")
steering_app = typer.Typer(help="Phase 396: Steering Gear Dual Hydraulic Power Actuator (SOLAS II-1 Reg 29)")
qcvalve_app = typer.Typer(help="Phase 397: Quick-Closing Valve & Emergency Fuel Shut-Off (SOLAS II-2 Reg 4)")
scavenge_app = typer.Typer(help="Phase 398: Main Engine Scavenge Air Fire Detection (IACS M44)")


@firepump_app.callback(invoke_without_command=True)
def evaluate_fire_pump(
    flow_m3_h: float = typer.Option(35.0, "--flow-m3-h", help="Pump flow rate in m3/h"),
    pressure_bar: float = typer.Option(3.2, "--pressure-bar", help="Discharge pressure in bar"),
    suction_m: float = typer.Option(3.5, "--suction-m", help="Suction lift head in meters"),
    prime_sec: float = typer.Option(65.0, "--prime-sec", help="Priming time in seconds"),
    fuel_hrs: float = typer.Option(3.5, "--fuel-hrs", help="Diesel fuel autonomy in hours"),
    volts: float = typer.Option(24.8, "--volts", help="Battery voltage in V"),
):
    """Evaluate Emergency Fire Pump compliance under SOLAS II-2 Reg 10 & FSS Code Ch. 12."""
    inp = EmergencyFirePumpInput(
        discharge_flow_rate_m3_h=flow_m3_h,
        discharge_pressure_bar=pressure_bar,
        suction_lift_head_m=suction_m,
        priming_duration_seconds=prime_sec,
        diesel_fuel_endurance_hours=fuel_hrs,
        starting_battery_voltage_v=volts,
    )
    res = EmergencyFirePumpEngine().evaluate(inp)

    table = Table(title="Maritime Phase 395: Emergency Fire Pump (SOLAS II-2)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="magenta")
    table.add_row("Operational Status", res.pump_operational_status)
    table.add_row("Discharge Capacity OK", "YES" if res.discharge_capacity_compliant else "NO")
    table.add_row("Discharge Pressure OK", "YES" if res.discharge_pressure_compliant else "NO")
    table.add_row("Priming System OK", "YES" if res.suction_priming_compliant else "NO")
    table.add_row("3-Hr Fuel Endurance OK", "YES" if res.endurance_compliant else "NO")
    table.add_row("Hose Jets Supported", str(res.fire_hose_jets_supported))
    console.print(table)


@steering_app.callback(invoke_without_command=True)
def evaluate_steering(
    transit_sec: float = typer.Option(22.5, "--transit-sec", help="Rudder transit 35° to 30° in sec"),
    aux_sec: float = typer.Option(48.0, "--aux-sec", help="Auxiliary transit 15° to 15° in sec"),
    p_hyd_bar: float = typer.Option(160.0, "--hyd-bar", help="Hydraulic working pressure bar"),
    level_pct: float = typer.Option(85.0, "--level-pct", help="Reservoir level percentage"),
    pump1: bool = typer.Option(True, "--pump1/--no-pump1", help="Hydraulic pump 1 status"),
    pump2: bool = typer.Option(True, "--pump2/--no-pump2", help="Hydraulic pump 2 status"),
):
    """Evaluate Steering Gear dual hydraulic redundancy & transit speed under SOLAS II-1 Reg 29."""
    inp = SteeringGearInput(
        rudder_traversal_35_to_30_deg_sec=transit_sec,
        auxiliary_traversal_15_to_15_deg_sec=aux_sec,
        hydraulic_pressure_bar=p_hyd_bar,
        oil_reservoir_level_pct=level_pct,
        pump_1_operational=pump1,
        pump_2_operational=pump2,
    )
    res = SteeringGearEngine().evaluate(inp)

    table = Table(title="Maritime Phase 396: Steering Gear Redundancy (SOLAS II-1)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="green")
    table.add_row("Readiness Status", res.steering_readiness_status)
    table.add_row("Main Gear Speed (<=28s)", "YES" if res.main_gear_speed_compliant else "NO")
    table.add_row("Aux Gear Speed (<=60s)", "YES" if res.auxiliary_gear_speed_compliant else "NO")
    table.add_row("Dual Redundancy Active", "YES" if res.redundancy_active else "NO")
    table.add_row("Pressure Status", res.hydraulic_pressure_status)
    table.add_row("Reservoir Level OK", "YES" if res.reservoir_level_ok else "NO")
    console.print(table)


@qcvalve_app.callback(invoke_without_command=True)
def evaluate_qc_valves(
    air_bar: float = typer.Option(7.0, "--air-bar", help="Control air pressure in bar"),
    time_sec: float = typer.Option(1.8, "--time-sec", help="Closure response time in sec"),
    tripped: int = typer.Option(6, "--tripped", help="Valves successfully tripped count"),
    total: int = typer.Option(6, "--total", help="Total fuel quick-closing valves count"),
    accum_bar: float = typer.Option(28.0, "--accum-bar", help="Accumulator bottle pressure bar"),
):
    """Evaluate Quick-Closing Valve pneumatic trip readiness under SOLAS II-2 Reg 4.2.2.3.4."""
    inp = QuickClosingValveInput(
        control_air_pressure_bar=air_bar,
        closure_response_time_sec=time_sec,
        valves_tripped_count=tripped,
        valves_total_count=total,
        accumulator_bottle_pressure_bar=accum_bar,
    )
    res = QuickClosingValveEngine().evaluate(inp)

    table = Table(title="Maritime Phase 397: Quick-Closing Valve Pneumatics")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="yellow")
    table.add_row("System Status", res.valve_system_status)
    table.add_row("Control Air OK (>=5.5 bar)", "YES" if res.control_air_pressure_ok else "NO")
    table.add_row("Closure Speed OK (<=3.0s)", "YES" if res.closure_speed_compliant else "NO")
    table.add_row("Completeness", f"{res.closure_completeness_pct}%")
    table.add_row("Accumulator OK (>=20 bar)", "YES" if res.accumulator_capacity_ok else "NO")
    console.print(table)


@scavenge_app.callback(invoke_without_command=True)
def evaluate_scavenge_fire(
    piston_temp_c: float = typer.Option(85.0, "--piston-temp-c", help="Max under-piston temp °C"),
    p_scav_bar: float = typer.Option(2.4, "--scav-bar", help="Scavenge manifold pressure bar"),
    diff_exh_c: float = typer.Option(25.0, "--exh-diff-c", help="Exhaust gas temperature spread °C"),
    oil_drain_l_h: float = typer.Option(1.2, "--oil-drain-l-h", help="Cylinder oil drain rate L/h"),
    soot_mg_m3: float = typer.Option(15.0, "--soot-mg-m3", help="Soot density mg/m3"),
):
    """Evaluate Main Engine Scavenge Air Fire Monitoring & Interlocks under IACS UR M44."""
    inp = ScavengeFireInput(
        max_under_piston_temp_c=piston_temp_c,
        scavenge_manifold_pressure_bar=p_scav_bar,
        exhaust_gas_diff_temp_c=diff_exh_c,
        cylinder_oil_drain_rate_l_h=oil_drain_l_h,
        soot_density_mg_m3=soot_mg_m3,
    )
    res = ScavengeFireEngine().evaluate(inp)

    table = Table(title="Maritime Phase 398: Scavenge Fire Interlock (IACS M44)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="red")
    table.add_row("Hazard Status", res.fire_hazard_status)
    table.add_row("Under-Piston Temp OK", "YES" if res.under_piston_temp_ok else "NO")
    table.add_row("Temperature Margin to Trip", f"{res.temperature_margin_c} °C")
    table.add_row("Fouling Level", res.unburnt_oil_fouling_level)
    table.add_row("Engine Slowdown Required", "YES" if res.engine_slowdown_demanded else "NO")
    table.add_row("Smothering Medium Ready", "YES" if res.smothering_medium_ready else "NO")
    console.print(table)
