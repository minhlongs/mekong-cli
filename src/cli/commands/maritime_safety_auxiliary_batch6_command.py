"""CLI Commands for Maritime Automation Phases 483-486.

Strictly < 100 LOC.
"""

import typer
from rich.console import Console

from src.core.maritime.phase_483_stp_aeration_sludge_return import (
    StpAerationSludgeReturnEngine,
    StpAerationTelemetry,
)
from src.core.maritime.phase_484_bearing_mist_slowdown import (
    BearingMistSlowdownEngine,
    BearingMistSlowdownTelemetry,
)
from src.core.maritime.phase_485_egb_circulation_dryrun import (
    EgbCirculationDryRunEngine,
    EgbCirculationTelemetry,
)
from src.core.maritime.phase_486_emergency_gen_blackout import (
    EmergencyGenBlackoutEngine,
    EmergencyGenTelemetry,
)

maritime_aux6_app = typer.Typer(
    name="maritime-aux6",
    help="Maritime Automation Phases 483-486: STP Aeration, Bearing Mist, EGB Circ, EDG Blackout",
)
console = Console()


@maritime_aux6_app.command("stpaeration-check")
def check_stp_aeration(
    do_mg_l: float = typer.Option(2.5, help="Dissolved oxygen mg/L"),
    p_bar: float = typer.Option(0.30, help="Diffuser pressure bar"),
    running: bool = typer.Option(True, help="Duty blower running state"),
    standby_ready: bool = typer.Option(True, help="Standby blower ready state"),
    flow_l_min: float = typer.Option(25.0, help="Sludge return flow L/min"),
    elapsed_s: float = typer.Option(0.0, help="Failover elapsed seconds"),
) -> None:
    """Evaluate STP aeration dissolved oxygen and sludge recirculation."""
    telem = StpAerationTelemetry(do_mg_l, p_bar, running, standby_ready, flow_l_min, elapsed_s)
    res = StpAerationSludgeReturnEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux6_app.command("bearingmist-check")
def check_bearing_mist(
    crosshead_c: float = typer.Option(68.0, help="Max crosshead temp deg C"),
    main_c: float = typer.Option(65.0, help="Max main bearing temp deg C"),
    delta_t: float = typer.Option(4.0, help="Bearing temp delta deg C"),
    oil_mist_lel: float = typer.Option(0.5, help="Crankcase oil mist % LEL"),
    lo_p_bar: float = typer.Option(2.2, help="Lube oil inlet pressure bar"),
    load_pct: float = typer.Option(75.0, help="Engine load %"),
) -> None:
    """Evaluate main engine bearing temperature and oil mist slowdown."""
    telem = BearingMistSlowdownTelemetry(crosshead_c, main_c, delta_t, oil_mist_lel, lo_p_bar, load_pct)
    res = BearingMistSlowdownEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux6_app.command("egbcirc-check")
def check_egb_circulation(
    diff_p_bar: float = typer.Option(1.5, help="Circulation pump dP bar"),
    flow_m3_h: float = typer.Option(20.0, help="Water flow m3/h"),
    standby_avail: bool = typer.Option(True, help="Standby pump available"),
    loss_s: float = typer.Option(0.0, help="Loss of flow duration seconds"),
    exh_c: float = typer.Option(310.0, help="Exhaust inlet temp deg C"),
    eco_c: float = typer.Option(140.0, help="Economizer inlet temp deg C"),
    tsat_c: float = typer.Option(165.0, help="Saturation temp deg C"),
) -> None:
    """Evaluate EGB forced circulation differential pressure and dry-run trip."""
    telem = EgbCirculationTelemetry(diff_p_bar, flow_m3_h, standby_avail, loss_s, exh_c, eco_c, tsat_c)
    res = EgbCirculationDryRunEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")


@maritime_aux6_app.command("edgblackout-check")
def check_edg_blackout(
    bus_pct: float = typer.Option(100.0, help="Main bus voltage %"),
    freq_hz: float = typer.Option(60.0, help="EDG frequency Hz"),
    volt_v: float = typer.Option(440.0, help="EDG voltage V"),
    elapsed_s: float = typer.Option(0.0, help="Blackout elapsed seconds"),
    tank_hours: float = typer.Option(12.0, help="Fuel day tank capacity hours"),
    attempts: int = typer.Option(3, help="Start attempts remaining"),
    breaker_closed: bool = typer.Option(False, help="Breaker closed"),
    qc_tripped: bool = typer.Option(False, help="Pneumatic quick-closing valve tripped"),
) -> None:
    """Evaluate emergency diesel generator blackout restoration and fuel endurance."""
    telem = EmergencyGenTelemetry(bus_pct, freq_hz, volt_v, elapsed_s, tank_hours, attempts, breaker_closed, qc_tripped)
    res = EmergencyGenBlackoutEngine.evaluate(telem)
    console.print(f"[bold green]Status:[/] {res.status.value}\nRemarks: {res.remarks}")
