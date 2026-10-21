"""CLI commands for Maritime Safety Auxiliary Batch 17 (Phases 527-530).
Strictly < 85 LOC, Typer subcommands for Cylinder Lubricator, Bilge Tank, Cargo Smoke, Freefall Boat.
"""
import typer
from rich.console import Console

from src.core.maritime.phase_527_cylinder_lubricator_alpha_dosage import (
    CylinderLubricatorAlphaDosageEngine, CylinderLubricatorTelemetry,
)
from src.core.maritime.phase_528_bilge_holding_tank_interface import (
    BilgeHoldingTankInterfaceEngine, BilgeHoldingTankTelemetry,
)
from src.core.maritime.phase_529_cargo_smoke_extraction_fan_supervision import (
    CargoSmokeExtractionFanSupervisionEngine, CargoSmokeExtractionTelemetry,
)
from src.core.maritime.phase_530_freefall_lifeboat_release_interlock import (
    FreefallLifeboatReleaseInterlockEngine, FreefallLifeboatTelemetry,
)

maritime_aux17_app = typer.Typer(
    name="maritime-aux17",
    help="Maritime Safety Automation Batch 17: Cylinder Lubricator, Bilge Tank, Cargo Smoke, Freefall Boat",
)
console = Console()


@maritime_aux17_app.command("cyllubricator-check")
def check_cyllubricator(sulfur_pct: float = 0.45, bn: float = 70.0, feed_rate: float = 0.85) -> None:
    res = CylinderLubricatorAlphaDosageEngine.evaluate(
        CylinderLubricatorTelemetry(fuel_sulfur_pct=sulfur_pct, cylinder_oil_bn=bn, actual_feed_rate_g_kwh=feed_rate)
    )
    console.print(f"[bold cyan]Cylinder Lubricator:[/bold cyan] {res.lubricator_state.value} | Target: {res.target_acc_feed_g_kwh} | Code: {res.alarm_code}")


@maritime_aux17_app.command("bilgetank-check")
def check_bilgetank(fill_pct: float = 45.0, oil_layer_mm: float = 80.0, temp_c: float = 52.0) -> None:
    res = BilgeHoldingTankInterfaceEngine.evaluate(
        BilgeHoldingTankTelemetry(tank_fill_pct=fill_pct, oil_emulsion_layer_mm=oil_layer_mm, heating_coil_temp_c=temp_c)
    )
    console.print(f"[bold green]Bilge Holding Tank:[/bold green] {res.tank_state.value} | OWS Start: {res.start_ows_feed_pump_cmd} | Code: {res.alarm_code}")


@maritime_aux17_app.command("cargosmoke-check")
def check_cargosmoke(dp_pa: float = 120.0, obscuration_pct_m: float = 0.2) -> None:
    res = CargoSmokeExtractionFanSupervisionEngine.evaluate(
        CargoSmokeExtractionTelemetry(fan_suction_dp_pa=dp_pa, smoke_obscuration_pct_per_m=obscuration_pct_m)
    )
    console.print(f"[bold yellow]Cargo Smoke Extraction:[/bold yellow] {res.extraction_state.value} | Standby Fan: {res.standby_fan_cutin_cmd} | Code: {res.alarm_code}")


@maritime_aux17_app.command("freefallboat-check")
def check_freefallboat(hyd_bar: float = 185.0, pin_removed: bool = True, speed_kn: float = 12.0) -> None:
    res = FreefallLifeboatReleaseInterlockEngine.evaluate(
        FreefallLifeboatTelemetry(hydraulic_release_bar=hyd_bar, harbor_securing_pin_removed=pin_removed, vessel_speed_kn=speed_kn)
    )
    console.print(f"[bold red]Free-Fall Lifeboat:[/bold red] {res.lifeboat_state.value} | Permitted: {res.primary_freefall_release_permitted} | Code: {res.alarm_code}")
