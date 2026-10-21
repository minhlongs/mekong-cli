"""CLI commands for Maritime Phases 363-366 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_lsa_pms_dredge_tug_engine import (
    DredgedSedimentInput,
    DredgingSedimentBeneficiationEngine,
    LifeboatHruInput,
    LifeboatHruReleaseEngine,
    MarineGeneratorPmsEngine,
    MarineGeneratorUnit,
    OvidTugWinchVettingEngine,
    PmsEvaluationInput,
    TugVettingInput,
)

console = Console()

lifeboat_app = typer.Typer(help="Phase 363: LSA Lifeboat & HRU Release (SOLAS III, MSC.81(70))")
marine_pms_app = typer.Typer(help="Phase 364: Marine Generator PMS & Blackout Prevention (IEC 60092-202)")
dredge_spoil_app = typer.Typer(help="Phase 365: Port Dredging Spoil Beneficial Reuse (QCVN 43:2017)")
tug_vetting_app = typer.Typer(help="Phase 366: OCIMF OVID Tug Vetting & Towing Winch (OCIMF OVID, STCW III/3)")


@lifeboat_app.command("evaluate")
def evaluate_lifeboat(
    boat_id: str = typer.Option("LB-01", "--boat-id", "-b"),
    drop_height: float = typer.Option(18.0, "--drop-height", "-h"),
    ramp_angle: float = typer.Option(33.0, "--ramp-angle", "-r"),
    entry_angle: float = typer.Option(56.0, "--entry-angle", "-e"),
    peak_g: float = typer.Option(9.2, "--peak-g", "-g"),
    hru_depth: float = typer.Option(2.5, "--hru-depth", "-d"),
    interlock: bool = typer.Option(True, "--interlock/--locked", "-i"),
) -> None:
    """Evaluate free-fall lifeboat launch trajectory, g-force, and HRU hydrostatic activation."""
    inp = LifeboatHruInput(
        boat_id=boat_id,
        drop_height_m=drop_height,
        ramp_angle_deg=ramp_angle,
        entry_angle_deg=entry_angle,
        peak_acceleration_g=peak_g,
        hru_water_depth_m=hru_depth,
        is_manual_interlock_released=interlock,
    )
    res = LifeboatHruReleaseEngine.evaluate(inp)
    console.print(f"[bold cyan]Lifeboat & HRU Evaluation:[/bold cyan] {res.boat_id}")
    console.print(f"Impact Vel: {res.impact_velocity_m_s} m/s | Safe: {res.is_safe_to_launch_or_float} | Status: [green]{res.safety_status}[/green]")
    for adv in res.advisories:
        console.print(f" - {adv}")


@marine_pms_app.command("evaluate")
def evaluate_pms(
    dg1_kw: float = typer.Option(720.0, "--dg1-kw"),
    dg2_kw: float = typer.Option(740.0, "--dg2-kw"),
    rated_kw: float = typer.Option(1000.0, "--rated-kw"),
    frequency: float = typer.Option(60.0, "--freq", "-f"),
    voltage_pct: float = typer.Option(100.0, "--volt-pct", "-v"),
    sustained_s: float = typer.Option(0.0, "--sustained-s", "-s"),
) -> None:
    """Evaluate marine generator load sharing, standby auto-start, and blackout trip."""
    inp = PmsEvaluationInput(
        generators=[
            MarineGeneratorUnit(gen_id="DG-01", rated_kw=rated_kw, current_kw=dg1_kw, frequency_hz=frequency, voltage_pct=voltage_pct),
            MarineGeneratorUnit(gen_id="DG-02", rated_kw=rated_kw, current_kw=dg2_kw, frequency_hz=frequency, voltage_pct=voltage_pct),
        ],
        sustained_overload_seconds=sustained_s,
    )
    res = MarineGeneratorPmsEngine.evaluate(inp)
    console.print(f"[bold cyan]Marine Generator PMS:[/bold cyan] Load: {res.total_load_pct}% MCR")
    console.print(f"Auto-Start: {res.is_auto_start_required} | Imbalance: {res.max_imbalance_pct}% | Risk: [yellow]{res.blackout_risk_status}[/yellow]")
    for adv in res.advisories:
        console.print(f" - {adv}")


@dredge_spoil_app.command("evaluate")
def evaluate_dredge(
    batch_id: str = typer.Option("SED-2026-01", "--batch-id", "-b"),
    tbt: float = typer.Option(0.0005, "--tbt", "-t"),
    pah: float = typer.Option(2.4, "--pah", "-p"),
    solids: float = typer.Option(65.0, "--solids", "-s"),
    ucs: float = typer.Option(72.0, "--ucs", "-u"),
) -> None:
    """Evaluate port dredged sediment chemical contamination and beneficial reuse gate."""
    inp = DredgedSedimentInput(
        batch_id=batch_id,
        tbt_mg_kg=tbt,
        total_pah_mg_kg=pah,
        heavy_metals={"as": 12.0, "cd": 0.8, "pb": 32.0, "hg": 0.15, "cu": 40.0, "zn": 120.0},
        solids_content_pct=solids,
        stabilized_ucs_kpa=ucs,
    )
    res = DredgingSedimentBeneficiationEngine.evaluate(inp)
    console.print(f"[bold cyan]Sediment Beneficiation:[/bold cyan] {res.batch_id}")
    console.print(f"Class: {res.sediment_class} | Approved: {res.is_beneficial_reuse_approved} | Dest: [green]{res.reuse_destination}[/green]")
    for adv in res.advisories:
        console.print(f" - {adv}")


@tug_vetting_app.command("evaluate")
def evaluate_tug(
    tug_id: str = typer.Option("TUG-SONG-TIEN-01", "--tug-id", "-t"),
    bp: float = typer.Option(65.0, "--bp", "-p"),
    towline_mbl: float = typer.Option(150.0, "--towline-mbl", "-m"),
    winch_brake: float = typer.Option(130.0, "--winch-brake", "-w"),
    release_time: float = typer.Option(1.8, "--release-time", "-r"),
    speed: float = typer.Option(10.0, "--speed", "-s"),
    stcw: bool = typer.Option(True, "--stcw/--no-stcw"),
) -> None:
    """Evaluate port tug vetting, winch brake holding, and escort steering/braking forces."""
    inp = TugVettingInput(
        tug_id=tug_id,
        certified_bollard_pull_t=bp,
        towline_mbl_t=towline_mbl,
        winch_brake_hold_t=winch_brake,
        quick_release_time_s=release_time,
        escort_speed_knots=speed,
        has_stcw_iii_3_endorsement=stcw,
    )
    res = OvidTugWinchVettingEngine.evaluate(inp)
    console.print(f"[bold cyan]OCIMF OVID Tug Vetting:[/bold cyan] {res.tug_id}")
    console.print(f"Brake Hold: {res.brake_hold_ratio_pct}% MBL | Steering F_y: {res.escort_steering_force_kn} kN | Status: [green]{res.overall_vetting_status}[/green]")
    for adv in res.advisories:
        console.print(f" - {adv}")
