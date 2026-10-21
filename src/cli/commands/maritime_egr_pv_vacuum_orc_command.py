"""Typer CLI commands for Maritime Phases 451-454.

Commands for EGR WTS, Cargo Tank P/V Valve, Vacuum Sewage, and ORC Evaporator.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_451_egr_water_treatment_system import (
    EgrWaterTreatmentEngine,
    EgrWtsTelemetry,
)
from src.core.maritime.phase_452_cargo_tank_high_velocity_pv_valve import (
    CargoPvValveEngine,
    PvValveTelemetry,
)
from src.core.maritime.phase_453_marine_sewage_vacuum_collection import (
    SewageVacuumSystemEngine,
    SewageVacuumTelemetry,
)
from src.core.maritime.phase_454_waste_heat_recovery_orc_evaporator import (
    WhrOrcEvaporatorEngine,
    OrcEvaporatorTelemetry,
)

app = typer.Typer(help="Maritime Phases 451-454 Operational Assessment CLI")
console = Console()


@app.command("egr-check")
def check_egr(
    ph: float = 7.4,
    turbidity: float = 12.0,
    pah: float = 25.0,
    centrifuge_eff: float = 94.0,
    sludge_pct: float = 45.0,
) -> None:
    """Evaluate EGR bleed-off water treatment compliance under MEPC.307(73)."""
    tel = EgrWtsTelemetry(ph, turbidity, pah, centrifuge_eff, sludge_pct)
    res = EgrWaterTreatmentEngine.evaluate(tel)
    color = "green" if res.overboard_discharge_permitted else "red"
    console.print(f"[{color}]EGR WTS Status: {res.status.value}[/{color}]")
    console.print(f"Remarks: {res.remarks}")


@app.command("pv-check")
def check_pv(
    pressure_kpa: float = 5.0,
    efflux_vel: float = 32.0,
    mesh_clear_pct: float = 95.0,
    magnetic_lift: bool = True,
    disc_lift: float = 0.0,
) -> None:
    """Evaluate High-Velocity P/V Valve venting under ISO 15364."""
    tel = PvValveTelemetry(pressure_kpa, efflux_vel, mesh_clear_pct, magnetic_lift, disc_lift)
    res = CargoPvValveEngine.evaluate(tel)
    color = "red" if res.safety_alarm else "green"
    console.print(f"[{color}]P/V Valve Status: {res.status.value}[/{color}]")
    console.print(f"Remarks: {res.remarks}")


@app.command("sewage-check")
def check_sewage(
    vacuum_kpa: float = -50.0,
    buffer_level: float = 40.0,
    motive_bar: float = 3.2,
    dist_shore_nm: float = 15.0,
) -> None:
    """Evaluate Sewage Vacuum System operation under ISO 15749."""
    tel = SewageVacuumTelemetry(vacuum_kpa, buffer_level, motive_bar, dist_shore_nm)
    res = SewageVacuumSystemEngine.evaluate(tel)
    color = "red" if res.alarm_active else "green"
    console.print(f"[{color}]Sewage System Status: {res.status.value}[/{color}]")
    console.print(f"Remarks: {res.remarks}")


@app.command("orc-check")
def check_orc(
    film_temp: float = 240.0,
    superheat: float = 22.0,
    diverter_pct: float = 100.0,
    leak: bool = False,
    expander_bar: float = 18.0,
) -> None:
    """Evaluate Waste Heat Recovery ORC Evaporator Safety under IACS UR M53."""
    tel = OrcEvaporatorTelemetry(film_temp, superheat, diverter_pct, leak, expander_bar)
    res = WhrOrcEvaporatorEngine.evaluate(tel)
    color = "red" if res.safety_alarm else "green"
    console.print(f"[{color}]ORC Evaporator Status: {res.status.value}[/{color}]")
    console.print(f"Remarks: {res.remarks}")
