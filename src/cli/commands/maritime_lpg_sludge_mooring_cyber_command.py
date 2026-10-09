"""CLI commands for Maritime Phases 355-358 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_lpg_sludge_mooring_cyber_engine import (
    LpgReliquefactionEngine,
    LpgReliquefactionInput,
    SludgeIncineratorEngine,
    SludgeIncineratorInput,
    SmartMooringEngine,
    SmartMooringInput,
    MaritimeCyberEngine,
    MaritimeCyberInput,
)

console = Console()

lpg_app = typer.Typer(help="Phase 355: LPG Cargo Reliquefaction & Compressor (IGC Code Ch.7)")
sludge_app = typer.Typer(help="Phase 356: MARPOL Annex I Bilge Sludge & Incinerator Interlocks")
mooring_app = typer.Typer(help="Phase 357: OCIMF MEG4 Smart Mooring Tension & Passing Ship Surge")
cyber_app = typer.Typer(help="Phase 358: IMO MSC.428(98) & IACS UR E26/E27 Maritime Cyber Resilience")


@lpg_app.command("evaluate")
def evaluate_lpg(
    vessel_id: str = typer.Option("V-LPG-01", "--vessel-id", "-v"),
    cargo_type: str = typer.Option("PROPANE", "--cargo", "-c"),
    heat_leak_kw: float = typer.Option(180.0, "--heat-leak", "-q"),
    tank_press_barg: float = typer.Option(0.15, "--tank-press", "-p"),
    marvs_barg: float = typer.Option(0.25, "--marvs", "-m"),
    flow_kg_h: float = typer.Option(1600.0, "--flow-rate", "-f"),
    power_kw: float = typer.Option(120.0, "--power", "-w"),
    active_comp: int = typer.Option(1, "--active-comp", "-a"),
    total_comp: int = typer.Option(2, "--total-comp", "-t"),
) -> None:
    """Evaluate LPG BOG generation, COP, and MARVS margins."""
    inp = LpgReliquefactionInput(
        vessel_id=vessel_id,
        cargo_type=cargo_type,
        heat_leakage_kw=heat_leak_kw,
        tank_pressure_barg=tank_press_barg,
        marvs_pressure_barg=marvs_barg,
        compressor_mass_flow_kg_h=flow_kg_h,
        compressor_shaft_power_kw=power_kw,
        active_compressor_count=active_comp,
        total_compressor_count=total_comp,
    )
    res = LpgReliquefactionEngine.evaluate(inp)
    console.print(f"[bold green]LPG Reliquefaction Result: {res.status}[/bold green]")
    console.print(f"BOG Rate: {res.bog_rate_kg_h} kg/h | Capacity: {res.reliquefaction_capacity_kg_h} kg/h | COP: {res.refrigeration_cop}")
    console.print(f"MARVS Ratio: {res.tank_pressure_ratio_to_marvs*100:.1f}% | Safe: {res.is_pressure_safe}")
    for adv in res.advisories:
        console.print(f" - {adv}")


@sludge_app.command("evaluate")
def evaluate_sludge(
    vessel_id: str = typer.Option("V-TANKER-02", "--vessel-id", "-v"),
    hfo_m3: float = typer.Option(35.0, "--hfo-m3"),
    mgo_m3: float = typer.Option(5.0, "--mgo-m3"),
    tank_m3: float = typer.Option(12.0, "--tank-m3"),
    cap_m3: float = typer.Option(18.0, "--cap-m3"),
    prim_temp_c: float = typer.Option(870.0, "--prim-temp"),
    sec_temp_c: float = typer.Option(1120.0, "--sec-temp"),
    oil_ppm: float = typer.Option(12.0, "--oil-ppm"),
    pump_running: bool = typer.Option(True, "--pump-running/--pump-stopped"),
) -> None:
    """Evaluate Sludge generation, chamber interlocks, and OWS 15ppm limits."""
    inp = SludgeIncineratorInput(
        vessel_id=vessel_id,
        daily_hfo_consumed_m3=hfo_m3,
        daily_mgo_consumed_m3=mgo_m3,
        sludge_holding_tank_m3=tank_m3,
        sludge_tank_capacity_m3=cap_m3,
        primary_chamber_temp_c=prim_temp_c,
        secondary_chamber_temp_c=sec_temp_c,
        oil_content_ppm=oil_ppm,
        is_sludge_pump_running=pump_running,
    )
    res = SludgeIncineratorEngine.evaluate(inp)
    console.print(f"[bold cyan]Sludge & Incinerator Result: {res.status}[/bold cyan]")
    console.print(f"Est Daily Sludge: {res.estimated_daily_sludge_m3} m3 | Fullness: {res.sludge_tank_fullness_percent}% ({res.days_to_tank_overflow} days left)")
    console.print(f"Incinerator Compliant: {res.is_incinerator_combustion_compliant} | OWS Discharge Allowed: {res.is_ows_discharge_permitted}")
    for adv in res.advisories:
        console.print(f" - {adv}")


@mooring_app.command("evaluate")
def evaluate_mooring(
    berth_id: str = typer.Option("B-CAILAN-01", "--berth-id", "-b"),
    vessel_id: str = typer.Option("V-BULK-03", "--vessel-id", "-v"),
    material: str = typer.Option("SYNTHETIC", "--material", "-m"),
    mbl_tonnes: float = typer.Option(85.0, "--mbl"),
    measured_tension: float = typer.Option(38.0, "--tension", "-t"),
    pass_speed_knots: float = typer.Option(8.0, "--pass-speed"),
    pass_disp_tonnes: float = typer.Option(60000.0, "--pass-disp"),
    pass_sep_m: float = typer.Option(65.0, "--pass-sep"),
) -> None:
    """Evaluate MEG4 line tension, passing ship surge, and snap-back hazards."""
    inp = SmartMooringInput(
        berth_id=berth_id,
        vessel_id=vessel_id,
        line_material=material,
        ship_design_mbl_tonnes=mbl_tonnes,
        measured_line_tension_tonnes=measured_tension,
        passing_vessel_speed_knots=pass_speed_knots,
        passing_vessel_displacement_tonnes=pass_disp_tonnes,
        passing_vessel_separation_m=pass_sep_m,
    )
    res = SmartMooringEngine.evaluate(inp)
    console.print(f"[bold yellow]Smart Mooring Surge Result: {res.status}[/bold yellow]")
    console.print(f"WLL: {res.permissible_wll_tonnes} t | Surge Force: {res.hydrodynamic_surge_force_kn} kN | Total Tension: {res.total_projected_tension_tonnes} t")
    console.print(f"Snap-Back Critical: {res.is_snap_back_risk_critical} | Exclusion Radius: {res.snap_back_exclusion_radius_m} m")
    for adv in res.advisories:
        console.print(f" - {adv}")


@cyber_app.command("evaluate")
def evaluate_cyber(
    vessel_id: str = typer.Option("V-CONTAINER-04", "--vessel-id", "-v"),
    nav_iso: bool = typer.Option(True, "--nav-iso/--nav-open"),
    prop_iso: bool = typer.Option(True, "--prop-iso/--prop-open"),
    crew_iso: bool = typer.Option(True, "--crew-iso/--crew-open"),
    nmea_err_rate: float = typer.Option(0.005, "--nmea-err"),
    gps_jump_kts: float = typer.Option(0.5, "--gps-jump"),
    sat_link: str = typer.Option("STARLINK_LEO", "--sat-link"),
    sat_lat_ms: float = typer.Option(45.0, "--sat-lat"),
    unauth_usb: bool = typer.Option(False, "--unauth-usb/--no-usb"),
) -> None:
    """Evaluate IACS E26/E27 cyber resilience, NMEA spoofing, and satellite failover."""
    inp = MaritimeCyberInput(
        vessel_id=vessel_id,
        is_navigation_ot_isolated=nav_iso,
        is_propulsion_ot_isolated=prop_iso,
        is_crew_welfare_it_segmented=crew_iso,
        detected_nmea_checksum_error_rate=nmea_err_rate,
        gps_position_jump_knots=gps_jump_kts,
        active_satellite_link=sat_link,
        satellite_latency_ms=sat_lat_ms,
        is_unauthorized_usb_detected=unauth_usb,
    )
    res = MaritimeCyberEngine.evaluate(inp)
    console.print(f"[bold red]Maritime Cyber Result: {res.status} (Threat: {res.cyber_threat_level})[/bold red]")
    console.print(f"Segmentation: {res.segmentation_score_percent}% | NMEA Spoofed: {res.is_nmea_spoofing_detected}")
    console.print(f"Recommended Sat: {res.recommended_satellite_link} | Crew Quarantined: {res.is_crew_internet_quarantined}")
    for adv in res.advisories:
        console.print(f" - {adv}")
