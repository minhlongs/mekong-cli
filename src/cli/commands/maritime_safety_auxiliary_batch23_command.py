import typer
from rich.console import Console

from src.core.maritime.phase_551_cpp_controllable_pitch_propeller_servo_interlock import (
    CppPropellerServoEngine,
    CppPropellerServoTelemetry,
)
from src.core.maritime.phase_552_cargo_reliquefaction_boil_off_gcu_interlock import (
    CargoReliqBoilOffGcuEngine,
    CargoReliqBoilOffGcuTelemetry,
)
from src.core.maritime.phase_553_engine_room_local_water_mist_fwla_interlock import (
    EngineRoomLocalWaterMistFwlaEngine,
    LocalWaterMistFwlaTelemetry,
)
from src.core.maritime.phase_554_rudder_roll_fin_stabilizer_zero_speed_interlock import (
    FinStabilizerHousingEngine,
    FinStabilizerHousingTelemetry,
)

maritime_aux23_app = typer.Typer(help="Maritime Auxiliary Automation Batch 23 (Phases 551-554)")
console = Console()


@maritime_aux23_app.command("cpp-check")
def cpp_check(
    pressure_bar: float = 42.0,
    oil_temp_c: float = 54.0,
    error_pct: float = 0.3,
) -> None:
    res = CppPropellerServoEngine.evaluate(
        CppPropellerServoTelemetry(pressure_bar, oil_temp_c, error_pct)
    )
    console.print(f"[bold cyan]Phase 551 CPP Servo:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux23_app.command("reliq-check")
def reliq_check(
    tank_kpag: float = 11.5,
    disch_temp_c: float = 95.0,
    suct_temp_c: float = -125.0,
    gcu_flame: bool = True,
) -> None:
    res = CargoReliqBoilOffGcuEngine.evaluate(
        CargoReliqBoilOffGcuTelemetry(tank_kpag, disch_temp_c, suct_temp_c, gcu_flame)
    )
    console.print(f"[bold cyan]Phase 552 Reliq GCU:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux23_app.command("fwla-check")
def fwla_check(
    flame: bool = False,
    smoke: bool = False,
    header_bar: float = 6.5,
    manual: bool = False,
) -> None:
    res = EngineRoomLocalWaterMistFwlaEngine.evaluate(
        LocalWaterMistFwlaTelemetry(flame, smoke, header_bar, manual)
    )
    console.print(f"[bold cyan]Phase 553 Local Mist FWLA:[/bold cyan] {res.state.value} ({res.interlock_code})")


@maritime_aux23_app.command("finstab-check")
def finstab_check(
    speed_kn: float = 14.5,
    hyd_bar: float = 140.0,
    load_pct: float = 55.0,
    pin_free: bool = True,
) -> None:
    res = FinStabilizerHousingEngine.evaluate(
        FinStabilizerHousingTelemetry(speed_kn, hyd_bar, load_pct, pin_free)
    )
    console.print(f"[bold cyan]Phase 554 Fin Stabilizer:[/bold cyan] {res.state.value} ({res.interlock_code})")
