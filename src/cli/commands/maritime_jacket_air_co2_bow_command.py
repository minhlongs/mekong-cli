"""Typer CLI commands for Maritime Phases 411-414.

Covers Main Engine Jacket Water, Starting Air Compressor,
Fixed High-Pressure CO2 Fire System, and Ro-Ro Bow Door Latching.
Strictly < 180 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_411_jacket_water_preheating import (
    JacketWaterEngine,
    JacketWaterTelemetry,
)
from src.core.maritime.phase_412_starting_air_compressor import (
    StartingAirCompressorEngine,
    AirCompressorTelemetry,
)
from src.core.maritime.phase_413_fixed_co2_fire_extinguishing import (
    FixedCo2FireSystemEngine,
    Co2SystemTelemetry,
)
from src.core.maritime.phase_414_roro_bow_door_latching import (
    RoRoBowDoorLatchingEngine,
    BowDoorTelemetry,
)

console = Console()

jacket_app = typer.Typer(help="Phase 411: ME Jacket Water Preheating & Cooling (ISO 8217 / MAN ES)")
aircomp_app = typer.Typer(help="Phase 412: Starting Air Compressor & Unloader Relief (SOLAS II-1 Reg 26)")
co2sys_app = typer.Typer(help="Phase 413: Fixed CO2 Fire Extinguishing System (SOLAS II-2 Reg 10 / FSS Code)")
bowdoor_app = typer.Typer(help="Phase 414: Ro-Ro Bow Visor & Inner Door Hydraulic Latching (SOLAS II-1 Reg 17-1)")


@jacket_app.callback(invoke_without_command=True)
def evaluate_jacket(
    inlet: float = typer.Option(75.0, "--inlet", help="Inlet temp (°C)"),
    outlet: float = typer.Option(84.0, "--outlet", help="Outlet temp (°C)"),
    tank_pct: float = typer.Option(65.0, "--tank-pct", help="Expansion tank level (%)"),
    press_bar: float = typer.Option(2.1, "--press", help="Static pressure (bar)"),
    flow: float = typer.Option(120.0, "--flow", help="Circulation flow (m3/h)"),
    nitrite: float = typer.Option(1100.0, "--nitrite", help="Nitrite inhibitor (ppm)"),
    preheater: bool = typer.Option(False, "--preheater", help="Preheater status"),
):
    """Evaluate ME jacket cooling water preheating and thermostatic mixing balance."""
    t = JacketWaterTelemetry(
        inlet_temp_c=inlet,
        outlet_temp_c=outlet,
        expansion_tank_level_pct=tank_pct,
        static_pressure_bar=press_bar,
        circulation_flow_m3h=flow,
        nitrite_concentration_ppm=nitrite,
        preheater_active=preheater,
    )
    res = JacketWaterEngine().evaluate(t)
    table = Table(title="Maritime Phase 411: Jacket Water Cooling & Preheating")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Temp Rise (ΔT)", f"{res.temp_rise_c} °C")
    table.add_row("Valve Pos", f"{res.valve_position_pct} %")
    table.add_row("Start Permissive", "GRANTED" if res.start_permissive else "LOCKED")
    console.print(table)


@aircomp_app.callback(invoke_without_command=True)
def evaluate_air_compressor(
    s1_bar: float = typer.Option(5.5, "--s1", help="Stage 1 pressure (bar)"),
    s2_bar: float = typer.Option(30.0, "--s2", help="Stage 2 pressure (bar)"),
    recv_bar: float = typer.Option(24.0, "--recv", help="Receiver pressure (bar)"),
    oil_bar: float = typer.Option(3.2, "--oil", help="Oil pressure (bar)"),
    unloader: bool = typer.Option(False, "--unloader", help="Unloader valve open"),
    drain_min: float = typer.Option(10.0, "--drain-interval", help="Drain interval (min)"),
    charge_min: float = typer.Option(45.0, "--recharge-min", help="0-30 bar recharge time (min)"),
    hrs: float = typer.Option(1250.0, "--hours", help="Running hours"),
):
    """Evaluate 2-stage air compressor operation and SOLAS recharge compliance."""
    t = AirCompressorTelemetry(
        stage1_pressure_bar=s1_bar,
        stage2_pressure_bar=s2_bar,
        receiver_pressure_bar=recv_bar,
        oil_pressure_bar=oil_bar,
        unloader_valve_open=unloader,
        drain_interval_minutes=drain_min,
        recharge_time_minutes=charge_min,
        running_hours=hrs,
    )
    res = StartingAirCompressorEngine().evaluate(t)
    table = Table(title="Maritime Phase 412: Starting Air Compressor & Unloader Relief")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Auto-Start Demanded", "YES" if res.auto_start_demanded else "NO")
    table.add_row("Auto-Stop Demanded", "YES" if res.auto_stop_demanded else "NO")
    table.add_row("SOLAS Recharge Compliant", "YES" if res.solas_charge_compliant else "NO")
    console.print(table)


@co2sys_app.callback(invoke_without_command=True)
def evaluate_co2_system(
    gross_v: float = typer.Option(4000.0, "--gross-vol", help="Gross volume (m3)"),
    mach_v: float = typer.Option(600.0, "--mach-vol", help="Machinery equipment volume (m3)"),
    cyl_count: int = typer.Option(35, "--cyl-count", help="Installed cylinders count"),
    cyl_mass: float = typer.Option(45.0, "--cyl-mass", help="Cylinder nominal mass (kg)"),
    disch_sec: float = typer.Option(95.0, "--disch-sec", help="Discharge time (s)"),
    delay_sec: float = typer.Option(25.0, "--delay-sec", help="Pre-discharge alarm delay (s)"),
    damper_closed: bool = typer.Option(True, "--damper-closed", help="Vent damper closed"),
    qcv_tripped: bool = typer.Option(True, "--qcv-tripped", help="Fuel QCV tripped"),
    door_open: bool = typer.Option(True, "--door-open", help="Cabinet door open"),
):
    """Evaluate SOLAS II-2 / FSS Code CO2 flooding mass and safety interlocks."""
    t = Co2SystemTelemetry(
        protected_space_gross_volume_m3=gross_v,
        machinery_equipment_volume_m3=mach_v,
        installed_cylinders_count=cyl_count,
        cylinder_nominal_mass_kg=cyl_mass,
        discharge_time_seconds=disch_sec,
        pre_discharge_delay_seconds=delay_sec,
        ventilation_damper_closed=damper_closed,
        fuel_quick_closing_valves_tripped=qcv_tripped,
        cabinet_door_open=door_open,
    )
    res = FixedCo2FireSystemEngine().evaluate(t)
    table = Table(title="Maritime Phase 413: Fixed High-Pressure CO2 Flooding")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Required CO2 Mass", f"{res.required_co2_mass_kg} kg")
    table.add_row("Installed CO2 Mass", f"{res.installed_co2_mass_kg} kg")
    table.add_row("Interlocks Satisfied", "YES" if res.interlocks_satisfied else "NO")
    console.print(table)


@bowdoor_app.callback(invoke_without_command=True)
def evaluate_bow_door(
    hyd_bar: float = typer.Option(175.0, "--hyd-bar", help="Hydraulic pressure (bar)"),
    s_a: bool = typer.Option(True, "--sensor-a", help="Sensor A locked"),
    s_b: bool = typer.Option(True, "--sensor-b", help="Sensor B locked"),
    seal_bar: float = typer.Option(4.0, "--seal-bar", help="Inflatable seal pressure (bar)"),
    water_m: float = typer.Option(0.0, "--water-m", help="Water level (m)"),
    speed_kts: float = typer.Option(18.0, "--speed-kts", help="Vessel speed (knots)"),
    cleats_eng: int = typer.Option(12, "--cleats-eng", help="Cleats engaged count"),
    cleats_tot: int = typer.Option(12, "--cleats-tot", help="Total cleats count"),
):
    """Evaluate Ro-Ro bow door locking cleats, dual sensors, and water ingress."""
    t = BowDoorTelemetry(
        hydraulic_pressure_bar=hyd_bar,
        sensor_a_locked=s_a,
        sensor_b_locked=s_b,
        inflatable_seal_pressure_bar=seal_bar,
        compartment_water_level_m=water_m,
        vessel_speed_knots=speed_kts,
        cleats_engaged_count=cleats_eng,
        cleats_total_count=cleats_tot,
    )
    res = RoRoBowDoorLatchingEngine().evaluate(t)
    table = Table(title="Maritime Phase 414: Ro-Ro Bow Visor & Door Latching")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Status", res.status)
    table.add_row("Dual Sensors Concordant", "YES" if res.sensors_concordant else "NO")
    table.add_row("Water Ingress Level", str(res.water_ingress_alarm_level))
    table.add_row("Navigation Permissive", "GRANTED" if res.navigation_permissive else "REVOKED")
    console.print(table)
