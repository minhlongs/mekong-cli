"""CLI commands for Maritime Phases 375-378 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_voyage_voc_yard_greywater_engine import (
    ContainerItem,
    ContainerYardRtgDispatchEngine,
    HvacCondensateGreywaterEngine,
    VocRecoveryInput,
    VocVaporRecoveryBalancingEngine,
    VoyageRoutingInput,
    VoyageWeatherRoutingCiiEngine,
    WaterReclamationInput,
    YardBlockInput,
)

console = Console()

weather_cii_app = typer.Typer(
    help="Phase 375: Voyage Weather Routing & CII Engine (ISO 15016, IMO MEPC.328(76))"
)
voc_vapor_app = typer.Typer(
    help="Phase 376: Tanker VOC Vapor Recovery & Balancing (MARPOL Annex VI Reg 15, OCIMF VEC)"
)
yard_stack_app = typer.Typer(
    help="Phase 377: Container Yard Block Stacking & RTG Crane Dispatch (UNCTAD, Decision 1579)"
)
greywater_app = typer.Typer(
    help="Phase 378: HVAC Condensate & Greywater Circular Reclamation (QCVN 14:2008/BTNMT)"
)


@weather_cii_app.command("evaluate")
def evaluate_weather_cii(
    vessel_id: str = typer.Option("IMO9876543", "--vessel-id", "-v"),
    dwt: float = typer.Option(55000.0, "--dwt", "-d", help="Deadweight tonnage (DWT)"),
    dist: float = typer.Option(2400.0, "--dist", help="Voyage distance (nm)"),
    speed: float = typer.Option(14.5, "--speed", "-s", help="Planned speed (knots)"),
    power: float = typer.Option(8500.0, "--power", "-p", help="Calm sea power (kW)"),
    beaufort: int = typer.Option(5, "--beaufort", "-b", help="Beaufort scale (0-12)"),
    wave_hs: float = typer.Option(2.5, "--wave-hs", "-w", help="Wave height Hs (m)"),
    fuel_t: float = typer.Option(72.0, "--fuel", "-f", help="Fuel consumed (tonnes)"),
) -> None:
    """Evaluate voyage weather added resistance, CII rating, and optimal speed."""
    inp = VoyageRoutingInput(
        vessel_id=vessel_id,
        dwt_tonnes=dwt,
        distance_nm=dist,
        planned_speed_knots=speed,
        calm_sea_power_kw=power,
        beaufort_scale=beaufort,
        significant_wave_height_m=wave_hs,
        fuel_consumption_tonnes=fuel_t,
    )
    res = VoyageWeatherRoutingCiiEngine().evaluate(inp)
    console.print(f"[bold cyan]Voyage Weather & CII Evaluation:[/bold cyan] {res.vessel_id}")
    console.print(
        f"CII Rating: [bold green]{res.cii_rating.value}[/bold green] | "
        f"Attained CII: {res.attained_cii:.2f} | Required CII: {res.required_cii:.2f} | "
        f"Optimal Speed: [bold yellow]{res.optimal_speed_knots:.1f} kts[/bold yellow]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@voc_vapor_app.command("evaluate")
def evaluate_voc_vapor(
    tanker_id: str = typer.Option("MT Cuu Long", "--tanker-id", "-t"),
    load_rate: float = typer.Option(3000.0, "--load-rate", "-r", help="Loading rate (m3/h)"),
    vap_cap: float = typer.Option(4000.0, "--vap-cap", "-c", help="Vapor capacity (m3/h)"),
    pressure: float = typer.Option(7.5, "--pressure", "-p", help="Tank pressure (kPa)"),
    o2_pct: float = typer.Option(5.2, "--o2", help="Oxygen level (% vol)"),
    voc_conc: float = typer.Option(800.0, "--voc-conc", help="VOC density (g/m3)"),
    h2s: float = typer.Option(0.5, "--h2s", help="H2S level (ppm)"),
) -> None:
    """Evaluate oil tanker VOC recovery, vapor balancing ratio, and GHG offsets."""
    inp = VocRecoveryInput(
        tanker_id=tanker_id,
        loading_rate_m3_h=load_rate,
        vapor_return_capacity_m3_h=vap_cap,
        tank_pressure_kpa=pressure,
        oxygen_content_pct=o2_pct,
        voc_concentration_g_m3=voc_conc,
        h2s_content_ppm=h2s,
    )
    res = VocVaporRecoveryBalancingEngine().evaluate(inp)
    console.print(f"[bold cyan]VOC Recovery & Vapor Balancing:[/bold cyan] {res.tanker_id}")
    console.print(
        f"Safe to Load: [bold green]{res.is_safe_to_load}[/bold green] | "
        f"Vapor Balanced: {res.is_vapor_balanced} | "
        f"VOC Recov: [bold green]{res.voc_recovered_kg_h:.1f} kg/h[/bold green] | "
        f"CO2 Offset: [bold yellow]{res.co2_eq_offset_kg_h:.1f} kg/h[/bold yellow]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@yard_stack_app.command("evaluate")
def evaluate_yard_stack(
    block_id: str = typer.Option("BLK-E04", "--block-id", "-b"),
    containers_count: int = typer.Option(8, "--containers", "-n", help="Mock test stack size"),
    rtg_cranes: int = typer.Option(2, "--rtg", help="Available RTG cranes"),
    qc_cranes: int = typer.Option(3, "--qc", help="Active Quay cranes"),
    gantry_dist: float = typer.Option(110.0, "--gantry-dist", help="Gantry travel (m)"),
) -> None:
    """Evaluate container yard block stacking reshuffle penalty and RTG dispatch."""
    # Deterministic test stack for CLI verification
    items = [
        ContainerItem(f"CNTR-{i:03d}", bay=1, row=1, tier=i + 1, departure_order=(i % 2) + 1)
        for i in range(min(containers_count, 10))
    ]
    inp = YardBlockInput(
        block_id=block_id,
        containers=items,
        available_rtg_cranes=rtg_cranes,
        active_quay_cranes=qc_cranes,
        gantry_travel_distance_m=gantry_dist,
    )
    res = ContainerYardRtgDispatchEngine().evaluate(inp)
    console.print(f"[bold cyan]Yard Block Stacking & RTG Dispatch:[/bold cyan] {res.block_id}")
    console.print(
        f"Containers: {res.total_containers} | "
        f"Reshuffles: [bold yellow]{res.total_reshuffles_required}[/bold yellow] | "
        f"RTG/QC Ratio: {res.rtg_qc_ratio:.2f} | "
        f"Cost-to-Go: [bold green]{res.cost_to_go_score}[/bold green]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@greywater_app.command("evaluate")
def evaluate_greywater(
    vessel_id: str = typer.Option("IMO9876543", "--vessel-id", "-v"),
    air_flow: float = typer.Option(12000.0, "--air-flow", help="HVAC flow (m3/h)"),
    hum_in: float = typer.Option(18.5, "--hum-in", help="Supply air moisture (g/kg)"),
    hum_out: float = typer.Option(9.2, "--hum-out", help="Leaving coil moisture (g/kg)"),
    tds: float = typer.Option(18.0, "--tds", help="Condensate TDS (ppm)"),
    greywater_m3: float = typer.Option(15.0, "--greywater", help="Greywater inflow (m3/d)"),
    bod5: float = typer.Option(12.0, "--bod5", help="Treated BOD5 (mg/L)"),
    tss: float = typer.Option(6.0, "--tss", help="Treated TSS (mg/L)"),
    turb: float = typer.Option(1.1, "--turb", help="Turbidity (NTU)"),
    coliform: float = typer.Option(45.0, "--coliform", help="Coliform (MPN/100mL)"),
    uv_dose: float = typer.Option(45.0, "--uv-dose", help="UV dose (mJ/cm2)"),
    in_mpa: bool = typer.Option(False, "--mpa", help="In Marine Protected Area"),
) -> None:
    """Evaluate HVAC condensate harvesting, QCVN 14 greywater reuse, and cost savings."""
    inp = WaterReclamationInput(
        vessel_id=vessel_id,
        air_flow_rate_m3_h=air_flow,
        humidity_in_g_kg=hum_in,
        humidity_out_g_kg=hum_out,
        condensate_tds_ppm=tds,
        greywater_daily_inflow_m3=greywater_m3,
        treated_bod5_mg_l=bod5,
        treated_tss_mg_l=tss,
        treated_turbidity_ntu=turb,
        treated_coliform_mpn_100ml=coliform,
        uv_c_dose_mj_cm2=uv_dose,
        in_marine_protected_area=in_mpa,
    )
    res = HvacCondensateGreywaterEngine().evaluate(inp)
    console.print(f"[bold cyan]HVAC Condensate & Greywater Reclamation:[/bold cyan] {res.vessel_id}")
    console.print(
        f"Condensate: [bold green]{res.condensate_harvest_m3_day:.1f} m3/d[/bold green] | "
        f"Boiler Safe: {res.is_boiler_feed_suitable} | QCVN 14: {res.is_qcvn14_compliant} | "
        f"Savings: [bold yellow]${res.cost_savings_usd_day:.1f}/day[/bold yellow]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")
