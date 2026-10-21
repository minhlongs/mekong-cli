"""CLI sub-app for Maritime Phases 459-462 Propulsion & Cargo Auxiliary Safety Systems."""

import typer
from rich.console import Console

from src.core.maritime.phase_459_ballast_tank_stripping_eductor import (
    BallastTankStrippingEductorEngine,
    BallastEductorTelemetry,
)
from src.core.maritime.phase_460_cargo_pump_room_gas_detection import (
    CargoPumpRoomGasDetectionEngine,
    PumpRoomGasTelemetry,
)
from src.core.maritime.phase_461_controllable_pitch_propeller_emergency_pitch import (
    CppEmergencyPitchEngine,
    CppPitchTelemetry,
)
from src.core.maritime.phase_462_intermediate_shaft_bearing_cooling import (
    IntermediateShaftBearingEngine,
    ShaftBearingTelemetry,
)

maritime_aux_app = typer.Typer(
    name="maritime-aux",
    help="Maritime Phases 459-462 Auxiliary Propulsion & Cargo Safety Systems",
)
console = Console()


@maritime_aux_app.command("eductor-check")
def check_ballast_eductor(
    drive_p: float = typer.Option(4.5, help="Drive water pressure (bar)"),
    suction_vac: float = typer.Option(-0.85, help="Suction vacuum gauge (bar)"),
    back_p: float = typer.Option(1.2, help="Discharge backpressure (bar)"),
    vib: float = typer.Option(2.1, help="Cavitation vibration (mm/s)"),
    flow: float = typer.Option(15.0, help="Stripping flow rate (m3/h)"),
) -> None:
    """Assess Ballast Tank Stripping Eductor Venturi Performance (Phase 459)."""
    t = BallastEductorTelemetry(drive_p, suction_vac, back_p, vib, flow)
    res = BallastTankStrippingEductorEngine.evaluate(t)
    console.print(f"[bold green]Status:[/bold green] {res.status.value}")
    console.print(f"Backpressure Ratio: {res.backpressure_ratio:.3f} | Remarks: {res.remarks}")


@maritime_aux_app.command("pumproom-check")
def check_pump_room_gas(
    lel: float = typer.Option(2.0, help="Hydrocarbon LEL (%)"),
    h2s: float = typer.Option(0.5, help="Toxic H2S (ppm)"),
    dp: float = typer.Option(75.0, help="Ventilation DP (Pa)"),
    bilge_alarm: bool = typer.Option(False, help="Bilge high level alarm"),
    flow_mbar: float = typer.Option(20.0, help="Sampling flow DP (mbar)"),
) -> None:
    """Assess Cargo Pump Room Gas Detection & Ventilation (Phase 460)."""
    t = PumpRoomGasTelemetry(lel, h2s, dp, bilge_alarm, flow_mbar)
    res = CargoPumpRoomGasDetectionEngine.evaluate(t)
    console.print(f"[bold green]Status:[/bold green] {res.status.value}")
    console.print(f"Gas Free: {res.gas_free} | Isolated: {res.pump_room_isolated} | Remarks: {res.remarks}")


@maritime_aux_app.command("cpp-pitch-check")
def check_cpp_pitch(
    servo_p: float = typer.Option(32.0, help="Servo oil pressure (bar)"),
    demanded: float = typer.Option(12.0, help="Demanded pitch (deg)"),
    ch_a: float = typer.Option(12.1, help="Actual pitch Ch A (deg)"),
    ch_b: float = typer.Option(12.1, help="Actual pitch Ch B (deg)"),
    lock_pin: bool = typer.Option(False, help="Emergency lock pin engaged"),
    manual_pump: bool = typer.Option(False, help="Manual hand pump active"),
) -> None:
    """Assess CPP Emergency Pitch Control & Locking (Phase 461)."""
    t = CppPitchTelemetry(servo_p, demanded, ch_a, ch_b, lock_pin, manual_pump)
    res = CppEmergencyPitchEngine.evaluate(t)
    console.print(f"[bold green]Status:[/bold green] {res.status.value}")
    console.print(f"Pitch Dev: {res.pitch_deviation_deg:.2f}° | Fail-as-is: {res.fail_as_is_engaged} | Remarks: {res.remarks}")


@maritime_aux_app.command("shaft-bearing-check")
def check_shaft_bearing(
    metal_temp: float = typer.Option(52.0, help="Bearing metal temp (°C)"),
    sump_temp: float = typer.Option(46.0, help="Oil sump temp (°C)"),
    cooling_flow: float = typer.Option(22.0, help="Cooling water flow (L/min)"),
    oil_ring: bool = typer.Option(True, help="Oil ring rotating"),
    water_pct: float = typer.Option(0.02, help="Water content in oil (%)"),
) -> None:
    """Assess Intermediate Shaft Bearing Lube & Cooling (Phase 462)."""
    t = ShaftBearingTelemetry(metal_temp, sump_temp, cooling_flow, oil_ring, water_pct)
    res = IntermediateShaftBearingEngine.evaluate(t)
    console.print(f"[bold green]Status:[/bold green] {res.status.value}")
    console.print(f"Slowdown Required: {res.engine_slowdown_required} | Remarks: {res.remarks}")
