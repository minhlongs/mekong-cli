"""CLI commands for Maritime Phases 367-370 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_fuel_bess_esi_ahc_engine import (
    BessModuleInput,
    EsiShipInput,
    FuelOilIso8217Engine,
    FuelSampleInput,
    MarineBatteryBessEngine,
    MooringAutoTensionAhcEngine,
    PortEsiGreenIncentiveEngine,
    SpotTestRating,
    WinchSensorInput,
)

console = Console()

fuel_quality_app = typer.Typer(help="Phase 367: Marine Fuel ISO 8217 & Compatibility (ISO 8217:2024, ASTM D4740)")
marine_bess_app = typer.Typer(help="Phase 368: Marine Battery BESS & Thermal Runaway (DNV-RU-SHIP, IEC 62619)")
port_esi_app = typer.Typer(help="Phase 369: Port Environmental Ship Index & Green Dues (WPCI ESI, TT 39/2023)")
mooring_ahc_app = typer.Typer(help="Phase 370: Mooring Winch Auto-Tension & AHC Wave Damping (OCIMF MEG4, ISO 3730)")


@fuel_quality_app.command("evaluate")
def evaluate_fuel(
    sample_id: str = typer.Option("VLSFO-2026-01", "--sample-id", "-s"),
    grade: str = typer.Option("VLSFO", "--grade", "-g"),
    al_si: float = typer.Option(18.5, "--al-si", "-a"),
    flash: float = typer.Option(66.0, "--flash", "-f"),
    visc: float = typer.Option(180.0, "--visc", "-v"),
    tsp: float = typer.Option(0.04, "--tsp", "-t"),
    sulfur: float = typer.Option(0.48, "--sulfur"),
    spot: str = typer.Option("2", "--spot"),
) -> None:
    """Evaluate bunker fuel ISO 8217 cat fines, flash point, and ASTM D4740 compatibility."""
    spot_enum = SpotTestRating(spot) if spot in [e.value for e in SpotTestRating] else SpotTestRating.GOOD
    inp = FuelSampleInput(
        sample_id=sample_id,
        fuel_grade=grade,
        al_plus_si_mg_kg=al_si,
        flash_point_c=flash,
        viscosity_at_50c_cst=visc,
        total_sediment_potential_pct=tsp,
        sulfur_pct=sulfur,
        spot_test_rating=spot_enum,
    )
    res = FuelOilIso8217Engine().evaluate(inp)
    console.print(f"[bold cyan]ISO 8217 Fuel Evaluation:[/bold cyan] {res.sample_id} ({grade})")
    console.print(f"Status: [green]{res.status}[/green] | Cat Fines: {res.cat_fines_status} | Preheat Temp: {res.recommended_preheat_temp_c}°C")
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@marine_bess_app.command("evaluate")
def evaluate_bess(
    pack_id: str = typer.Option("BESS-PACK-A1", "--pack-id", "-p"),
    soc: float = typer.Option(75.0, "--soc", "-s"),
    soh: float = typer.Option(94.0, "--soh", "-h"),
    c_rate: float = typer.Option(0.8, "--c-rate", "-c"),
    temp: float = typer.Option(34.0, "--temp", "-t"),
    delta_t: float = typer.Option(2.1, "--delta-t", "-d"),
    h2: float = typer.Option(0.0, "--h2"),
    co: float = typer.Option(0.0, "--co"),
    peak_shaving: bool = typer.Option(False, "--peak-shaving/--standard"),
) -> None:
    """Evaluate marine BESS battery pack safety, C-rate, and off-gas thermal runaway stage."""
    inp = BessModuleInput(
        pack_id=pack_id,
        soc_pct=soc,
        soh_pct=soh,
        c_rate=c_rate,
        cell_max_temp_c=temp,
        cell_delta_temp_c=delta_t,
        offgas_h2_ppm=h2,
        offgas_co_ppm=co,
        is_peak_shaving_mode=peak_shaving,
    )
    res = MarineBatteryBessEngine().evaluate(inp)
    console.print(f"[bold cyan]Marine BESS Safety Evaluation:[/bold cyan] {res.pack_id}")
    console.print(f"Trip Stage: [bold red]{res.trip_stage.value}[/bold red] | Safe: {res.is_safe} | Max C-rate: {res.allowable_c_rate}C")
    for act in res.actions_required:
        console.print(f" - {act}")


@port_esi_app.command("evaluate")
def evaluate_esi(
    vessel_imo: str = typer.Option("IMO9876543", "--imo", "-i"),
    vessel_name: str = typer.Option("MEKONG GREEN VOYAGER", "--name", "-n"),
    nox_red: float = typer.Option(45.0, "--nox-red", "-x"),
    sulfur: float = typer.Option(0.10, "--sulfur", "-s"),
    co2_gain: float = typer.Option(18.0, "--co2-gain", "-c"),
    ops: bool = typer.Option(True, "--ops/--no-ops"),
) -> None:
    """Evaluate ship Environmental Ship Index (ESI) score and port dues discount."""
    inp = EsiShipInput(
        vessel_imo=vessel_imo,
        vessel_name=vessel_name,
        nox_reduction_pct=nox_red,
        fuel_sulfur_pct=sulfur,
        co2_improvement_pct=co2_gain,
        has_ops_cold_ironing=ops,
    )
    res = PortEsiGreenIncentiveEngine().evaluate(inp)
    console.print(f"[bold cyan]Port ESI & Green Dues:[/bold cyan] {res.vessel_name} (Total ESI: {res.esi_total_score})")
    console.print(f"Tier: [bold green]{res.tier.value}[/bold green] | Discount: {res.port_dues_discount_pct}%")
    for inc in res.eligible_incentives:
        console.print(f" - {inc}")


@mooring_ahc_app.command("evaluate")
def evaluate_mooring(
    winch_id: str = typer.Option("WINCH-FWD-01", "--winch-id", "-w"),
    tension: float = typer.Option(180.0, "--tension", "-t"),
    mbl: float = typer.Option(1000.0, "--mbl", "-m"),
    target_pct: float = typer.Option(20.0, "--target-pct"),
    heave_amp: float = typer.Option(0.75, "--heave-amp", "-a"),
    wave_period: float = typer.Option(7.5, "--wave-period", "-p"),
    load_rms: float = typer.Option(0.06, "--load-rms", "-r"),
) -> None:
    """Evaluate mooring winch auto-tension rendering/heaving and AHC heave compensation."""
    inp = WinchSensorInput(
        winch_id=winch_id,
        measured_tension_kn=tension,
        mbl_kn=mbl,
        target_tension_pct_mbl=target_pct,
        ship_heave_amplitude_m=heave_amp,
        wave_period_s=wave_period,
        load_displacement_rms_m=load_rms,
    )
    res = MooringAutoTensionAhcEngine().evaluate(inp)
    console.print(f"[bold cyan]Auto-Tension & AHC Winch:[/bold cyan] {res.winch_id}")
    console.print(f"Action: [bold yellow]{res.action_state.value}[/bold yellow] | AHC Eff: {res.ahc_efficiency_pct}% | Cmd Speed: {res.command_winch_speed_m_s} m/s")
    for w in res.warnings:
        console.print(f" - {w}")
