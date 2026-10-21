import typer
from rich.console import Console

from src.core.maritime.phase_543_scr_urea_ammonia_slip_interlock import (
    ScrUreaAmmoniaSlipEngine,
    ScrUreaDosingTelemetry,
)
from src.core.maritime.phase_544_cargo_tank_pv_breaker_mast_interlock import (
    CargoPvBreakerMastTelemetry,
    CargoTankPvBreakerMastEngine,
)
from src.core.maritime.phase_545_azipod_slewing_seal_stator_interlock import (
    AzipodPropulsorTelemetry,
    AzipodSlewingSealStatorEngine,
)
from src.core.maritime.phase_546_lng_esd_drybreak_erc_interlock import (
    LngEsdDrybreakErcEngine,
    LngEsdErcTelemetry,
)

maritime_aux21_app = typer.Typer(help="Maritime Auxiliary Automation Batch 21 (Phases 543-546)")
console = Console()


@maritime_aux21_app.command("scr-check")
def scr_check(
    bed_temp: float = 340.0,
    sulfur_pct: float = 0.08,
    nh3_slip: float = 4.0,
    dp_kpa: float = 1.1,
) -> None:
    res = ScrUreaAmmoniaSlipEngine.evaluate(
        ScrUreaDosingTelemetry(bed_temp, sulfur_pct, nh3_slip, dp_kpa)
    )
    console.print(f"[bold cyan]Phase 543 SCR Urea:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux21_app.command("pvbreaker-check")
def pvbreaker_check(
    tank_kpa: float = 6.5,
    liquid_mmwg: float = 1850.0,
    flame_temp: float = 32.0,
) -> None:
    res = CargoTankPvBreakerMastEngine.evaluate(
        CargoPvBreakerMastTelemetry(tank_kpa, liquid_mmwg, flame_temp)
    )
    console.print(f"[bold cyan]Phase 544 P/V Breaker:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux21_app.command("azipod-check")
def azipod_check(
    stator_temp: float = 115.0,
    ingress_liters: float = 2.0,
    slewing_bar: float = 175.0,
    air_temp: float = 42.0,
) -> None:
    res = AzipodSlewingSealStatorEngine.evaluate(
        AzipodPropulsorTelemetry(stator_temp, ingress_liters, slewing_bar, air_temp)
    )
    console.print(f"[bold cyan]Phase 545 Azipod:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux21_app.command("lng-esd-check")
def lng_esd_check(
    drift_m: float = 0.5,
    drip_temp: float = 18.0,
    erc_bar: float = 195.0,
    ssl_ok: bool = True,
) -> None:
    res = LngEsdDrybreakErcEngine.evaluate(
        LngEsdErcTelemetry(drift_m, drip_temp, erc_bar, ssl_ok)
    )
    console.print(f"[bold cyan]Phase 546 LNG ESD/ERC:[/bold cyan] {res.state.value} ({res.interlock_code})")
