"""Bilingual Typer CLI Commands for Maritime Automation Phases 431-434.

Covers:
- sterntube: Stern tube lube gravity DP & seal temperature
- gensync: Auxiliary diesel generator auto-sync & load sharing
- scrubberwash: Wet scrubber washwater PAH & turbidity monitoring
- emgbilge: Machinery space emergency bilge suction valve interlock
Strictly < 160 LOC, zero mocks.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_431_stern_tube_lube_gravity import (
    SternTubeLubeEngine,
    SternTubeLubeTelemetry,
)
from src.core.maritime.phase_432_diesel_gen_sync_loadshare import (
    DieselGenSyncEngine,
    GeneratorSyncTelemetry,
)
from src.core.maritime.phase_433_scrubber_washwater_monitoring import (
    ScrubberWashwaterEngine,
    ScrubberWashwaterTelemetry,
)
from src.core.maritime.phase_434_emergency_bilge_suction import (
    EmergencyBilgeSuctionEngine,
    EmergencyBilgeTelemetry,
)

console = Console()
sterntube_app = typer.Typer(name="sterntube", help="Stern tube lube DP & seal monitoring")
gensync_app = typer.Typer(name="gensync", help="Generator auto-synchronizing & load sharing")
scrubberwash_app = typer.Typer(name="scrubberwash", help="EGCS washwater quality monitoring")
emgbilge_app = typer.Typer(name="emgbilge", help="Emergency bilge suction valve interlock")


@sterntube_app.command("status")
def sterntube_status(
    tank_height: float = typer.Option(6.5, "--height", help="Gravity tank height (m)"),
    draft: float = typer.Option(8.2, "--draft", help="Seawater draft (m)"),
    fwd_temp: float = typer.Option(52.0, "--fwd-temp", help="Forward seal temp (C)"),
    aft_temp: float = typer.Option(58.0, "--aft-temp", help="Aft seal temp (C)"),
    water_pct: float = typer.Option(0.35, "--water", help="Water in oil (%)"),
) -> None:
    """Check stern tube gravity head differential pressure and seal integrity."""
    engine = SternTubeLubeEngine()
    telemetry = SternTubeLubeTelemetry(
        gravity_tank_height_m=tank_height,
        ship_draft_m=draft,
        fwd_seal_temp_c=fwd_temp,
        aft_seal_temp_c=aft_temp,
        water_content_pct=water_pct,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Stern Tube Status:[/bold] {res.status}")
    console.print(f"Differential Pressure: {res.differential_pressure_bar:.3f} bar (In envelope: {res.dp_in_envelope})")


@gensync_app.command("status")
def gensync_status(
    bus_freq: float = typer.Option(60.0, "--bus-f", help="Bus frequency (Hz)"),
    inc_freq: float = typer.Option(60.1, "--inc-f", help="Incoming frequency (Hz)"),
    bus_v: float = typer.Option(440.0, "--bus-v", help="Bus voltage (V)"),
    inc_v: float = typer.Option(442.0, "--inc-v", help="Incoming voltage (V)"),
    phase_diff: float = typer.Option(3.5, "--phase", help="Phase angle diff (deg)"),
) -> None:
    """Evaluate generator synchronizing window and breaker close permission."""
    engine = DieselGenSyncEngine()
    telemetry = GeneratorSyncTelemetry(
        bus_frequency_hz=bus_freq,
        incoming_frequency_hz=inc_freq,
        bus_voltage_v=bus_v,
        incoming_voltage_v=inc_v,
        phase_angle_diff_deg=phase_diff,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Gen Sync Status:[/bold] {res.status}")
    console.print(f"Breaker Close Permitted: {res.breaker_close_permitted}")


@scrubberwash_app.command("status")
def scrubberwash_status(
    inlet_ntu: float = typer.Option(3.2, "--inlet-ntu", help="Inlet turbidity (FNU)"),
    out_ntu: float = typer.Option(18.5, "--out-ntu", help="Discharge turbidity (FNU)"),
    pah: float = typer.Option(24.0, "--pah", help="PAH (ug/L)"),
    ph: float = typer.Option(6.8, "--ph", help="Discharge pH"),
) -> None:
    """Verify EGCS scrubber washwater overboard compliance against MEPC.340(77)."""
    engine = ScrubberWashwaterEngine()
    telemetry = ScrubberWashwaterTelemetry(
        inlet_turbidity_fnu=inlet_ntu,
        discharge_turbidity_fnu=out_ntu,
        discharge_pah_ug_l=pah,
        discharge_ph=ph,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Scrubber Wash Status:[/bold] {res.status}")
    console.print(f"Overboard Permitted: {res.overboard_discharge_allowed}")


@emgbilge_app.command("status")
def emgbilge_status(
    level_mm: float = typer.Option(120.0, "--level", help="Bilge well level (mm)"),
    valve_open: float = typer.Option(0.0, "--valve", help="Emergency valve % open"),
) -> None:
    """Inspect machinery space emergency bilge suction valve and water levels."""
    engine = EmergencyBilgeSuctionEngine()
    telemetry = EmergencyBilgeTelemetry(
        bilge_water_level_mm=level_mm,
        emergency_valve_open_pct=valve_open,
    )
    res = engine.evaluate(telemetry)
    console.print(f"[bold]Emergency Bilge Status:[/bold] {res.status}")
    console.print(f"Alarm State: {res.bilge_alarm_state}")
