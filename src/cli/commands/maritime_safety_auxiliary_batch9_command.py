"""CLI commands for Maritime Safety Auxiliary Batch 9 (Phases 495-498).
Strictly < 95 LOC, Typer subcommands for OWS, OMD, Boiler, and Fire Pump.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_495_ows_15ppm_bilge_alarm import Ows15PpmBilgeAlarmEngine, OwsTelemetry
from src.core.maritime.phase_496_crankcase_oil_mist_detector import (
    CrankcaseOilMistDetectorEngine, OilMistTelemetry,
)
from src.core.maritime.phase_497_boiler_water_level_fuel_cutoff import (
    BoilerWaterLevelFuelCutoffEngine, BoilerWaterTelemetry,
)
from src.core.maritime.phase_498_emergency_fire_pump_priming import (
    EmergencyFirePumpPrimingEngine, FirePumpTelemetry,
)

maritime_aux9_app = typer.Typer(
    name="maritime-aux9",
    help="Maritime Safety Automation Batch 9: OWS, OMD, Boiler Level, Fire Pump Priming",
)
console = Console()

@maritime_aux9_app.command("ows-check")
def check_ows(ppm: float = 12.0, flow: float = 1.0, clean_water: bool = False, special_area: bool = False):
    res = Ows15PpmBilgeAlarmEngine.evaluate(
        OwsTelemetry(oil_content_ppm=ppm, sample_flow_l_per_min=flow, clean_water_flushing_active=clean_water, in_special_area=special_area)
    )
    console.print(f"[bold cyan]OWS Routing:[/bold cyan] {res.valve_routing.value} | Overboard: {res.overboard_allowed} | Alarm: {res.alarm_reason}")

@maritime_aux9_app.command("omd-check")
def check_omd(opacity: float = 0.5, fan_pa: float = 150.0, arrester: bool = True):
    res = CrankcaseOilMistDetectorEngine.evaluate(
        OilMistTelemetry(mist_opacity_pct=opacity, fan_differential_pa=fan_pa, flame_arrester_intact=arrester)
    )
    console.print(f"[bold yellow]OMD Command:[/bold yellow] {res.engine_command.value} | Alarm: {res.alarm_active} | Code: {res.alarm_code}")

@maritime_aux9_app.command("boiler-check")
def check_boiler(level_mm: float = 0.0, probe_match: bool = True):
    res = BoilerWaterLevelFuelCutoffEngine.evaluate(
        BoilerWaterTelemetry(water_level_mm=level_mm, differential_probe_matched=probe_match)
    )
    console.print(f"[bold red]Boiler Burner:[/bold red] {res.burner_state.value} | Alarm: {res.alarm_active} | Code: {res.alarm_code}")

@maritime_aux9_app.command("firepump-check")
def check_firepump(suction_open: bool = True, discharge_bar: float = 3.0, elapsed_sec: float = 10.0):
    res = EmergencyFirePumpPrimingEngine.evaluate(
        FirePumpTelemetry(suction_valve_open=suction_open, suction_vacuum_bar=-0.45, discharge_pressure_bar=discharge_bar, priming_elapsed_sec=elapsed_sec)
    )
    console.print(f"[bold green]Fire Pump:[/bold green] {res.pump_status.value} | Pressurized: {res.fire_main_pressurized} | Code: {res.alarm_code}")
