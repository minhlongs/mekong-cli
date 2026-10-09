"""Typer CLI commands for Maritime Phases 399-402.

Includes EGCS SOx Scrubber, Vacuum Fresh Water Generator,
Deck Crane Anti-Sway & SWL, and Hull UTM Gauging.
Strictly < 180 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_399_egcs_sox_wet_scrubber import (
    EgcsSoxScrubberEngine,
    EgcsScrubberInput,
    EgcsMode,
)
from src.core.maritime.phase_400_vacuum_fresh_water_generator import (
    VacuumFreshWaterGeneratorEngine,
    VacuumFwgInput,
)
from src.core.maritime.phase_401_deck_crane_anti_sway_swl import (
    DeckCraneAntiSwayEngine,
    DeckCraneInput,
)
from src.core.maritime.phase_402_utm_hull_gauging_corrosion import (
    UtmHullGaugingEngine,
    UtmHullGaugingInput,
    HullPlateCategory,
)

console = Console()

egcs_app = typer.Typer(help="Phase 399: EGCS SOx Wet Scrubber (IMO MEPC.340(77))")
fwg_app = typer.Typer(help="Phase 400: Vacuum Plate Fresh Water Generator (SOLAS II-1 Reg 26)")
crane_app = typer.Typer(help="Phase 401: Deck Crane Anti-Sway & Dynamic SWL (ILO 152 / DNV-ST-0378)")
utm_app = typer.Typer(help="Phase 402: UTM Hull Gauging & Wastage Limits (IACS UR Z10)")


@egcs_app.callback(invoke_without_command=True)
def evaluate_egcs(
    so2_ppm: float = typer.Option(12.0, "--so2-ppm", help="SO2 concentration in ppm"),
    co2_pct: float = typer.Option(5.0, "--co2-pct", help="CO2 concentration in %"),
    ph: float = typer.Option(6.8, "--ph", help="Washwater effluent pH"),
    inlet_pah: float = typer.Option(5.0, "--inlet-pah", help="Inlet PAH ug/L"),
    discharge_pah: float = typer.Option(15.0, "--discharge-pah", help="Discharge PAH ug/L"),
    turbidity: float = typer.Option(8.0, "--turbidity", help="Discharge turbidity in FNU"),
    mode: str = typer.Option("OPEN_LOOP", "--mode", help="Mode: OPEN_LOOP, CLOSED_LOOP, HYBRID"),
    seca: bool = typer.Option(False, "--seca", help="Operating within SECA / ECA area"),
):
    """Evaluate EGCS SOx scrubber emissions and effluent washwater compliance."""
    op_mode = EgcsMode.OPEN_LOOP
    if mode.upper() == "CLOSED_LOOP":
        op_mode = EgcsMode.CLOSED_LOOP
    elif mode.upper() == "HYBRID":
        op_mode = EgcsMode.HYBRID

    inp = EgcsScrubberInput(
        so2_ppm=so2_ppm,
        co2_pct=co2_pct,
        washwater_ph=ph,
        inlet_pah_ug_l=inlet_pah,
        discharge_pah_ug_l=discharge_pah,
        turbidity_fnu=turbidity,
        operating_mode=op_mode,
        in_eca_or_restricted_port=seca,
    )
    res = EgcsSoxScrubberEngine().evaluate(inp)

    table = Table(title="Maritime Phase 399: EGCS SOx Scrubber (MEPC.340(77))")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="magenta")
    table.add_row("SO2/CO2 Ratio", f"{res.emission_ratio:.2f}")
    table.add_row("MEPC.340(77) Compliant", "PASS" if res.mepc_340_77_compliant else "FAIL")
    table.add_row("Washwater Status", res.sox_washwater_status)
    table.add_row("NaOH Dosing Active", str(res.naoh_dosing_active))
    table.add_row("Discharge Lockout", str(res.discharge_lockout))
    console.print(table)


@fwg_app.callback(invoke_without_command=True)
def evaluate_fwg(
    jacket_temp: float = typer.Option(80.0, "--jacket-temp", help="Jacket water temp in deg C"),
    vacuum_bar: float = typer.Option(-0.93, "--vacuum-bar", help="Evaporator vacuum relative bar"),
    salinity_ppm: float = typer.Option(3.5, "--salinity-ppm", help="Distillate salinity TDS ppm"),
    feed_flow: float = typer.Option(12.0, "--feed-flow", help="Feed seawater flow m3/h"),
    dist_flow: float = typer.Option(1.0, "--dist-flow", help="Distillate yield flow m3/h"),
):
    """Evaluate Vacuum Fresh Water Generator evaporation and potable purity."""
    inp = VacuumFwgInput(
        jacket_water_temp_c=jacket_temp,
        evaporator_vacuum_bar=vacuum_bar,
        distillate_salinity_ppm=salinity_ppm,
        feed_seawater_flow_m3_h=feed_flow,
        distillate_flow_m3_h=dist_flow,
    )
    res = VacuumFreshWaterGeneratorEngine().evaluate(inp)

    table = Table(title="Maritime Phase 400: Vacuum Fresh Water Generator (SOLAS II-1)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="magenta")
    table.add_row("Boiling Temp (°C)", f"{res.evaporator_boiling_temp_c:.1f}")
    table.add_row("Distillate Purity", res.distillate_purity_status)
    table.add_row("3-Way Dump Valve", res.three_way_dump_valve)
    table.add_row("Thermal Efficiency", f"{res.thermal_efficiency_pct:.1f}%")
    table.add_row("Potable Certified", "YES" if res.potable_grade_certified else "NO")
    console.print(table)


@crane_app.callback(invoke_without_command=True)
def evaluate_crane(
    hook_load: float = typer.Option(18.0, "--hook-load", help="Suspended hook load in tonnes"),
    radius_m: float = typer.Option(16.0, "--radius-m", help="Working outreach radius in meters"),
    wave_hs_m: float = typer.Option(0.8, "--wave-hs-m", help="Significant wave height Hs in m"),
    sway_deg: float = typer.Option(1.2, "--sway-deg", help="Load pendulum sway angle in degrees"),
    static_swl: float = typer.Option(30.0, "--static-swl", help="Rated static SWL in tonnes"),
):
    """Evaluate Electro-Hydraulic Deck Crane anti-sway and dynamic SWL."""
    inp = DeckCraneInput(
        hook_load_tonnes=hook_load,
        boom_radius_m=radius_m,
        significant_wave_height_m=wave_hs_m,
        sway_pendulum_angle_deg=sway_deg,
        rated_static_swl_tonnes=static_swl,
    )
    res = DeckCraneAntiSwayEngine().evaluate(inp)

    table = Table(title="Maritime Phase 401: Deck Crane Anti-Sway & Dynamic SWL (ILO 152)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="magenta")
    table.add_row("Dynamic SWL (t)", f"{res.dynamic_swl_tonnes:.2f}")
    table.add_row("Load Moment (t*m)", f"{res.load_moment_ton_m:.2f}")
    table.add_row("SWL Utilization", f"{res.swl_utilization_pct:.1f}%")
    table.add_row("Anti-Sway Status", res.anti_sway_dampening_status)
    table.add_row("Operation Status", res.operation_status)
    console.print(table)


@utm_app.callback(invoke_without_command=True)
def evaluate_utm(
    category: str = typer.Option("A", "--category", help="Plate category: A (deck/bottom), B (shell), C (stiffener)"),
    as_built_mm: float = typer.Option(20.0, "--as-built-mm", help="Original as-built thickness in mm"),
    actual_mm: float = typer.Option(18.2, "--actual-mm", help="Gauged actual thickness in mm"),
    pit_depth_mm: float = typer.Option(1.5, "--pit-depth-mm", help="Localized pitting depth in mm"),
    pit_density_pct: float = typer.Option(4.0, "--pit-density-pct", help="Pitting surface density %"),
):
    """Evaluate Ultrasonic Thickness Measurement (UTM) hull corrosion limits."""
    cat_map = {
        "A": HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM,
        "B": HullPlateCategory.CATEGORY_B_SIDE_SHELL_BULKHEAD,
        "C": HullPlateCategory.CATEGORY_C_INTERNAL_STIFFENER,
    }
    plate_cat = cat_map.get(category.upper(), HullPlateCategory.CATEGORY_A_STRENGTH_DECK_BOTTOM)

    inp = UtmHullGaugingInput(
        plate_category=plate_cat,
        as_built_thickness_mm=as_built_mm,
        actual_gauged_thickness_mm=actual_mm,
        pitting_depth_mm=pit_depth_mm,
        pitting_density_pct=pit_density_pct,
    )
    res = UtmHullGaugingEngine().evaluate(inp)

    table = Table(title="Maritime Phase 402: UTM Hull Gauging (IACS UR Z10)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Status / Value", style="magenta")
    table.add_row("Wastage", f"{res.wastage_pct:.1f}% / Max {res.allowable_wastage_pct:.1f}%")
    table.add_row("Substantial Corrosion", "YES" if res.substantial_corrosion_detected else "NO")
    table.add_row("Steel Renewal Required", "RENEWAL REQUIRED" if res.renewal_steel_required else "NOT REQUIRED")
    table.add_row("Survey Recommendation", res.survey_recommendation)
    table.add_row("Integrity Status", res.structural_integrity_status)
    console.print(table)
