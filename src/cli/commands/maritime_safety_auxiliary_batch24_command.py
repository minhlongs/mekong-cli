import typer
from rich.console import Console

from src.core.maritime.phase_555_air_lubrication_system_als_hull_nozzle_interlock import (
    AirLubricationAlsEngine,
    AirLubricationAlsTelemetry,
)
from src.core.maritime.phase_556_shaft_generator_pto_frequency_converter_interlock import (
    PtoShaftGeneratorConverterEngine,
    PtoShaftGeneratorTelemetry,
)
from src.core.maritime.phase_557_galley_wet_chemical_deep_fat_hood_interlock import (
    GalleyDeepFatHoodTelemetry,
    GalleyWetChemicalDeepFatHoodEngine,
)
from src.core.maritime.phase_558_roro_shell_door_weathertight_cleat_interlock import (
    RoRoShellDoorIndicatorsInterlockEngine,
    RoRoShellDoorTelemetry,
)

maritime_aux24_app = typer.Typer(help="Maritime Auxiliary Automation Batch 24 (Phases 555-558)")
console = Console()


@maritime_aux24_app.command("als-check")
def als_check(
    speed_kn: float = 16.0,
    roll_deg: float = 2.5,
    diff_bar: float = 0.65,
    disch_temp_c: float = 78.0,
    backflow: bool = False,
) -> None:
    res = AirLubricationAlsEngine.evaluate(
        AirLubricationAlsTelemetry(speed_kn, roll_deg, diff_bar, disch_temp_c, backflow)
    )
    console.print(f"[bold cyan]Phase 555 Hull ALS:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux24_app.command("pto-check")
def pto_check(
    rpm_pct: float = 82.0,
    dc_link_v: float = 980.0,
    igbt_temp_c: float = 58.0,
    thd_pct: float = 2.4,
    crash_stop: bool = False,
) -> None:
    res = PtoShaftGeneratorConverterEngine.evaluate(
        PtoShaftGeneratorTelemetry(rpm_pct, dc_link_v, igbt_temp_c, thd_pct, crash_stop)
    )
    console.print(f"[bold cyan]Phase 556 PTO Shaft Gen:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux24_app.command("galley-hood-check")
def galley_hood_check(
    oil_temp_c: float = 180.0,
    filter_dp_pa: float = 110.0,
    flame: bool = False,
    manual: bool = False,
) -> None:
    res = GalleyWetChemicalDeepFatHoodEngine.evaluate(
        GalleyDeepFatHoodTelemetry(oil_temp_c, filter_dp_pa, flame, manual)
    )
    console.print(f"[bold cyan]Phase 557 Galley Hood:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux24_app.command("roro-door-check")
def roro_door_check(
    cleats_locked: bool = True,
    inner_closed: bool = True,
    ingress_l_min: float = 1.5,
    hyd_bar: float = 155.0,
    sea_mode: bool = True,
) -> None:
    res = RoRoShellDoorIndicatorsInterlockEngine.evaluate(
        RoRoShellDoorTelemetry(cleats_locked, inner_closed, ingress_l_min, hyd_bar, sea_mode)
    )
    console.print(f"[bold cyan]Phase 558 Ro-Ro Shell Door:[/bold cyan] {res.state.value} ({res.interlock_code})")
