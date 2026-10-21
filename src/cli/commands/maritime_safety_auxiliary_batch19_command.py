"""CLI commands for Maritime Safety Auxiliary Batch 19 (Phases 535-538).
Strictly < 85 LOC, Typer subcommands for Exhaust Valve, Cargo Pumproom, Hull Stress, Helideck JP-5.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_535_exhaust_valve_actuator_supervision import (
    ExhaustValveActuatorSupervisionEngine, ExhaustValveActuatorTelemetry,
)
from src.core.maritime.phase_536_cargo_pumproom_vent_gas_interlock import (
    CargoPumproomTelemetry, CargoPumproomVentGasInterlockEngine,
)
from src.core.maritime.phase_537_hull_stress_slamming_monitor import (
    HullStressSlammingMonitorEngine, HullStressSlammingTelemetry,
)
from src.core.maritime.phase_538_helideck_jp5_refueling_interlock import (
    HelideckJp5RefuelingInterlockEngine, HelideckRefuelingTelemetry,
)

maritime_aux19_app = typer.Typer(
    name="maritime-aux19",
    help="Maritime Safety Automation Batch 19: Exhaust Valve, Cargo Pumproom, Hull Stress, Helideck JP-5",
)
console = Console()


@maritime_aux19_app.command("exhvalve-check")
def check_exhvalve(
    air_bar: float = 7.2, rpm: float = 12.0, leak_l_h: float = 0.2, load_pct: float = 75.0
) -> None:
    res = ExhaustValveActuatorSupervisionEngine.evaluate(
        ExhaustValveActuatorTelemetry(air_bar, rpm, leak_l_h, load_pct)
    )
    console.print(f"[bold cyan]Exhaust Valve:[/bold cyan] {res.state.value} | Cutout: {res.cylinder_fuel_cutout_cmd} | Code: {res.interlock_code}")


@maritime_aux19_app.command("pumproom-check")
def check_pumproom(
    ach: float = 24.0, lel_pct: float = 1.5, bearing_c: float = 54.0, bilge_mm: float = 60.0
) -> None:
    res = CargoPumproomVentGasInterlockEngine.evaluate(
        CargoPumproomTelemetry(ach, lel_pct, bearing_c, bilge_mm)
    )
    console.print(f"[bold green]Cargo Pumproom:[/bold green] {res.state.value} | COP Trip: {res.cargo_oil_pump_trip_cmd} | Code: {res.interlock_code}")


@maritime_aux19_app.command("hullstress-check")
def check_hullstress(
    stress_mpa: float = 120.0, limit_mpa: float = 175.0, slams: int = 0, accel_g: float = 0.15
) -> None:
    res = HullStressSlammingMonitorEngine.evaluate(
        HullStressSlammingTelemetry(stress_mpa, limit_mpa, slams, accel_g)
    )
    console.print(f"[bold yellow]Hull Stress:[/bold yellow] {res.state.value} | Util%: {res.stress_utilization_pct} | Code: {res.interlock_code}")


@maritime_aux19_app.command("helideckjp5-check")
def check_helideckjp5(
    bond_ohms: float = 2.5, water_ppm: float = 4.0, dp_bar: float = 0.35, deadman_held: bool = True
) -> None:
    res = HelideckJp5RefuelingInterlockEngine.evaluate(
        HelideckRefuelingTelemetry(bond_ohms, water_ppm, dp_bar, deadman_held)
    )
    console.print(f"[bold red]Helideck JP-5:[/bold red] {res.state.value} | Solenoid Open: {res.fuel_solenoid_valve_open} | Code: {res.interlock_code}")
