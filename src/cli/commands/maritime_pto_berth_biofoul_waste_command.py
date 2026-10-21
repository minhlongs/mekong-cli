"""CLI commands for Maritime Phases 371-374 with bilingual Vietnamese aliases.

Strictly kept under 200 lines.
"""

import typer
from rich.console import Console

from src.core.maritime_pto_berth_biofoul_waste_engine import (
    BerthRequest,
    BiofoulingInspection,
    PortBerthCraneBapQcspEngine,
    BiofoulingHullCleaningEngine,
    PortWasteOilCoprocessingEngine,
    ShaftGeneratorInput,
    ShaftGeneratorPtoPtiEngine,
    ShaftHybridMode,
    WasteOilBatch,
)

console = Console()

shaft_pto_app = typer.Typer(
    help="Phase 371: Shaft Generator PTO/PTI Hybrid Engine (DNV-RU-SHIP, IEC 60092-501)"
)
berth_alloc_app = typer.Typer(
    help="Phase 372: Port Berth & Quay Crane Allocation BAP/QCSP (UNCTAD, PIANC WG 158)"
)
biofoul_app = typer.Typer(
    help="Phase 373: Marine Biofouling & In-Water Cleaning (IMO MEPC.378(80), BIMCO IWC)"
)
waste_oil_app = typer.Typer(
    help="Phase 374: Port Circular Waste Oil Co-Processing (MARPOL Annex I, TT 02/2022)"
)


@shaft_pto_app.command("evaluate")
def evaluate_shaft_pto(
    vessel_id: str = typer.Option("IMO9912345", "--vessel-id", "-v"),
    mcr: float = typer.Option(12000.0, "--mcr", help="ME MCR (kW)"),
    me_rpm: float = typer.Option(82.0, "--rpm", help="Current ME RPM"),
    rated_rpm: float = typer.Option(95.0, "--rated-rpm", help="Rated ME RPM"),
    me_load: float = typer.Option(7200.0, "--load", help="ME Load (kW)"),
    pto_cap: float = typer.Option(1800.0, "--pto-cap", help="PTO capacity (kW)"),
    req_kw: float = typer.Option(1200.0, "--power-kw", help="Requested shaft power (kW)"),
    hotel_kw: float = typer.Option(900.0, "--hotel-kw", help="Ship hotel load (kW)"),
    mode: str = typer.Option("PTO", "--mode", "-m", help="Mode: PTO, PTI, PTH, DISENGAGED"),
) -> None:
    """Evaluate shaft generator PTO/PTI fuel savings and speed inhibit limits."""
    mode_enum = (
        ShaftHybridMode(mode)
        if mode in [e.value for e in ShaftHybridMode]
        else ShaftHybridMode.PTO
    )
    inp = ShaftGeneratorInput(
        vessel_id=vessel_id,
        main_engine_mcr_kw=mcr,
        main_engine_speed_rpm=me_rpm,
        main_engine_rated_rpm=rated_rpm,
        current_me_load_kw=me_load,
        shaft_gen_capacity_kw=pto_cap,
        shaft_power_kw=req_kw,
        hotel_load_kw=hotel_kw,
        requested_mode=mode_enum,
    )
    res = ShaftGeneratorPtoPtiEngine().evaluate(inp)
    console.print(f"[bold cyan]Shaft PTO/PTI Hybrid Evaluation:[/bold cyan] {res.vessel_id}")
    console.print(
        f"Mode: [green]{res.active_mode.value}[/green] | PTO Allowed: {res.is_pto_permitted} | "
        f"Fuel Savings: [bold green]{res.fuel_savings_kg_per_h:.1f} kg/h[/bold green]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@berth_alloc_app.command("evaluate")
def evaluate_berth_allocation(
    vessel: str = typer.Option("Cai Mep Express", "--vessel", "-v"),
    loa: float = typer.Option(330.0, "--loa", help="Vessel LOA (m)"),
    draft: float = typer.Option(14.5, "--draft", "-d", help="Vessel draft (m)"),
    moves: int = typer.Option(1200, "--moves", "-m", help="Container moves"),
    berth_len: float = typer.Option(380.0, "--berth-len", help="Assigned berth length (m)"),
    depth: float = typer.Option(14.0, "--depth", help="Chart depth (m)"),
    tide: float = typer.Option(2.5, "--tide", "-t", help="Tide elevation (m)"),
    cranes: int = typer.Option(3, "--cranes", "-c", help="Assigned quay cranes"),
    crane_dist: float = typer.Option(45.0, "--crane-dist", help="Crane spacing (m)"),
) -> None:
    """Evaluate berth allocation BAP and quay crane scheduling QCSP constraints."""
    req = BerthRequest(
        vessel_name=vessel,
        loa_m=loa,
        draft_m=draft,
        container_moves=moves,
        assigned_berth_length_m=berth_len,
        berth_chart_depth_m=depth,
        tide_height_m=tide,
        assigned_cranes=cranes,
        crane_spacing_m=crane_dist,
    )
    res = PortBerthCraneBapQcspEngine().evaluate(req)
    console.print(f"[bold cyan]Berth & Crane Allocation (BAP/QCSP):[/bold cyan] {res.vessel_name}")
    console.print(
        f"Status: [bold green]{res.status.value}[/bold green] | UKC: {res.actual_ukc_m:.2f}m | "
        f"Turnaround: [bold yellow]{res.estimated_turnaround_hours:.1f} hrs[/bold yellow]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@biofoul_app.command("evaluate")
def evaluate_biofouling(
    vessel_id: str = typer.Option("IMO9765432", "--vessel-id", "-v"),
    lof: int = typer.Option(2, "--lof", "-l", help="Level of Fouling (0-5)"),
    area: float = typer.Option(14500.0, "--area", "-a", help="Wetted surface area (m2)"),
    power_kw: float = typer.Option(16000.0, "--power", "-p", help="Baseline power (kW)"),
    capture_pct: float = typer.Option(99.4, "--capture", "-c", help="ROV capture %"),
    mesh_um: float = typer.Option(5.0, "--mesh", "-m", help="Filter mesh (microns)"),
) -> None:
    """Evaluate hull biofouling powering penalty and in-water cleaning compliance."""
    insp = BiofoulingInspection(
        vessel_id=vessel_id,
        level_of_fouling=lof,
        hull_surface_area_m2=area,
        baseline_propulsion_power_kw=power_kw,
        rov_capture_efficiency_pct=capture_pct,
        filtration_mesh_micron=mesh_um,
    )
    res = BiofoulingHullCleaningEngine().evaluate(insp)
    console.print(f"[bold cyan]Biofouling & In-Water Cleaning Report:[/bold cyan] {res.vessel_id}")
    console.print(
        f"LoF: {res.level_of_fouling} | Permission: [bold green]{res.permission.value}[/bold green] | "
        f"Power Penalty: +{res.power_penalty_pct}% (+{res.added_propulsion_power_kw:.0f} kW)"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")


@waste_oil_app.command("evaluate")
def evaluate_waste_oil(
    batch_id: str = typer.Option("SLOP-HCM-09", "--batch-id", "-b"),
    volume: float = typer.Option(120.0, "--volume", "-v", help="Sludge volume (m3)"),
    flash: float = typer.Option(68.0, "--flash", "-f", help="Flash point (C)"),
    water_pct: float = typer.Option(35.0, "--water", "-w", help="Water %"),
    effluent_ppm: float = typer.Option(11.5, "--ppm", help="Effluent oil ppm"),
    lhv: float = typer.Option(40.5, "--lhv", help="RFO LHV (MJ/kg)"),
) -> None:
    """Evaluate port circular waste oil reception, dewatering, and cement co-processing."""
    batch = WasteOilBatch(
        batch_id=batch_id,
        volume_m3=volume,
        flash_point_c=flash,
        water_content_pct=water_pct,
        effluent_oil_ppm=effluent_ppm,
        rfo_lhv_mj_kg=lhv,
    )
    res = PortWasteOilCoprocessingEngine().evaluate(batch)
    console.print(f"[bold cyan]Circular Waste Oil Co-Processing:[/bold cyan] {res.batch_id}")
    console.print(
        f"Status: [bold green]{res.status.value}[/bold green] | Safe: {res.is_safe_to_receive} | "
        f"RFO: {res.recovered_fuel_oil_tonnes:.1f}t | CO2 Offset: [bold green]{res.co2_offset_tonnes:.1f}t[/bold green]"
    )
    for w in res.warnings:
        console.print(f" - [yellow]{w}[/yellow]")
