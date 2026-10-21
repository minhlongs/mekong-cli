"""CLI Commands for Maritime Phases 335-338: VTS, CSS Cargo, Electric Tug, Charterparty.

Kept under 200 lines according to KISS/YAGNI principles.
"""

import json
from typing import Optional
import typer
from rich.console import Console

from src.core.maritime_vts_css_tug_charter_engine import (
    CharterpartyArbitrationEngine,
    CharterpartyDisputeInput,
    ElectricTugColdIroningEngine,
    ElectricTugColdIroningInput,
    LashingDevice,
    ProjectCargoCssLashingEngine,
    ProjectCargoLashingInput,
    VtsNavigationInput,
    VtsTssNavigationEngine,
)

console = Console()

vts_app = typer.Typer(help="Vessel Traffic Service (VTS) & TSS Route Compliance")
csscargo_app = typer.Typer(help="Project Cargo & Heavy Lift OOG CSS Lashing Safety")
electug_app = typer.Typer(help="Green Port Electric Tug & Cold Ironing Energy Management")
charter_app = typer.Typer(help="BIMCO Charterparty Performance & Maritime Arbitration")


@vts_app.command("monitor")
def monitor_vts(
    mmsi: str = typer.Option(..., "--mmsi", help="Own vessel MMSI"),
    name: str = typer.Option("MV MEKONG NAVIGATOR", "--name", help="Vessel Name"),
    lat: float = typer.Option(10.25, "--lat", help="Current Latitude"),
    lon: float = typer.Option(107.05, "--lon", help="Current Longitude"),
    course: float = typer.Option(135.0, "--course", help="Course over ground (deg)"),
    speed: float = typer.Option(12.5, "--speed", help="Speed over ground (knots)"),
    lane_name: str = typer.Option("Vung Tau TSS Inbound", "--lane-name", help="TSS Lane Name"),
    lane_heading: float = typer.Option(135.0, "--lane-heading", help="TSS Lane Heading (deg)"),
    lane_width: float = typer.Option(1.5, "--lane-width", help="TSS Lane Width (NM)"),
    xte: float = typer.Option(0.2, "--xte", help="Cross-track error (NM)"),
    target_mmsi: Optional[str] = typer.Option(None, "--target-mmsi", help="Target MMSI"),
    target_lat: Optional[float] = typer.Option(None, "--target-lat", help="Target Latitude"),
    target_lon: Optional[float] = typer.Option(None, "--target-lon", help="Target Longitude"),
    target_course: Optional[float] = typer.Option(None, "--target-course", help="Target Course (deg)"),
    target_speed: Optional[float] = typer.Option(None, "--target-speed", help="Target Speed (knots)"),
):
    inp = VtsNavigationInput(
        vessel_mmsi=mmsi,
        vessel_name=name,
        lat=lat,
        lon=lon,
        course_deg=course,
        speed_knots=speed,
        tss_lane_name=lane_name,
        tss_lane_heading_deg=lane_heading,
        tss_lane_width_nm=lane_width,
        cross_track_error_nm=xte,
        target_mmsi=target_mmsi,
        target_lat=target_lat,
        target_lon=target_lon,
        target_course_deg=target_course,
        target_speed_knots=target_speed,
    )
    res = VtsTssNavigationEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@csscargo_app.command("lashing")
def eval_lashing(
    cargo_id: str = typer.Option("OOG-TRANSFORMER-01", "--cargo-id", help="Cargo ID"),
    desc: str = typer.Option("Power Grid Transformer 120t", "--desc", help="Description"),
    mass: float = typer.Option(120.0, "--mass", help="Cargo mass in metric tons"),
    cog_h: float = typer.Option(2.2, "--cog-h", help="CoG height above deck (m)"),
    width: float = typer.Option(3.5, "--width", help="Cargo width (m)"),
    ay: float = typer.Option(5.2, "--ay", help="Transverse acceleration (m/s^2)"),
    az: float = typer.Option(2.0, "--az", help="Vertical acceleration (m/s^2)"),
    mu: float = typer.Option(0.3, "--mu", help="Dunnage friction coefficient"),
    msl: float = typer.Option(100.0, "--msl", help="MSL per lashing device (kN)"),
    lash_count: int = typer.Option(8, "--lash-count", help="Number of active transverse lashings"),
    alpha: float = typer.Option(30.0, "--alpha", help="Vertical lashing angle (deg)"),
    beta: float = typer.Option(15.0, "--beta", help="Horizontal lashing angle (deg)"),
):
    lashings = [
        LashingDevice(
            device_id=f"LASH-{i+1:02d}",
            msl_kn=msl,
            vertical_angle_deg=alpha,
            horizontal_angle_deg=beta,
        )
        for i in range(lash_count)
    ]
    inp = ProjectCargoLashingInput(
        cargo_id=cargo_id,
        description=desc,
        mass_metric_ton=mass,
        cog_height_m=cog_h,
        cargo_width_m=width,
        accel_transverse_ay=ay,
        accel_vertical_az=az,
        dunnage_friction_mu=mu,
        lashings=lashings,
    )
    res = ProjectCargoCssLashingEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@electug_app.command("energy")
def eval_electug(
    name: str = typer.Option("E-TUG SAIGON 01", "--name", help="Tugboat Name"),
    bat_kwh: float = typer.Option(2500.0, "--bat-kwh", help="Battery capacity (kWh)"),
    soc: float = typer.Option(45.0, "--soc", help="Current battery SoC (%)"),
    bp_tons: float = typer.Option(70.0, "--bp-tons", help="Bollard Pull Ahead (tons)"),
    duration_h: float = typer.Option(2.0, "--duration", help="Towage duration (hours)"),
    energy_kwh: float = typer.Option(18.0, "--energy-kwh", help="Energy consumed (kWh)"),
    grid_max_kw: float = typer.Option(1200.0, "--grid-max-kw", help="Shore substation limit (kW)"),
    berth_kw: float = typer.Option(800.0, "--berth-kw", help="Vessel hotel load (kW)"),
    charge_kw: float = typer.Option(400.0, "--charge-kw", help="Charging power demand (kW)"),
):
    inp = ElectricTugColdIroningInput(
        tug_name=name,
        battery_capacity_kwh=bat_kwh,
        current_soc_pct=soc,
        bollard_pull_ahead_tons=bp_tons,
        towage_duration_hours=duration_h,
        towage_energy_consumed_kwh=energy_kwh,
        shore_grid_max_kw=grid_max_kw,
        vessel_berth_load_kw=berth_kw,
        shore_charging_power_kw=charge_kw,
    )
    res = ElectricTugColdIroningEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@charter_app.command("dispute")
def eval_charter(
    fixture: str = typer.Option("FIX-2026-NYPE", "--fixture", help="Fixture ID"),
    vessel: str = typer.Option("MV MEKONG PRIDE", "--vessel", help="Vessel Name"),
    charter_type: str = typer.Option("TIME_CHARTER", "--charter-type", help="TIME_CHARTER / VOYAGE_CHARTER"),
    daily_rate: float = typer.Option(18000.0, "--daily-rate", help="Daily hire or demurrage rate (USD)"),
    bunker_price: float = typer.Option(650.0, "--bunker-price", help="VLSFO bunker price (USD/MT)"),
    distance: Optional[float] = typer.Option(3600.0, "--distance", help="Voyage distance (NM)"),
    warr_speed: Optional[float] = typer.Option(13.0, "--warr-speed", help="Warranted speed (knots)"),
    rec_speed: Optional[float] = typer.Option(11.5, "--rec-speed", help="Recorded good weather speed (knots)"),
    warr_fuel: Optional[float] = typer.Option(24.0, "--warr-fuel", help="Warranted fuel (MT/day)"),
    rec_fuel: Optional[float] = typer.Option(26.0, "--rec-fuel", help="Recorded fuel (MT/day)"),
    beaufort: int = typer.Option(3, "--beaufort", help="Beaufort scale observed"),
    sea_state: int = typer.Option(2, "--sea-state", help="Douglas sea state"),
    allowed_laytime: Optional[float] = typer.Option(None, "--allowed-laytime", help="Allowed laytime hours"),
    used_laytime: Optional[float] = typer.Option(None, "--used-laytime", help="Actual laytime hours used"),
    forum: str = typer.Option("LMAA_ICP", "--forum", help="LMAA_ICP or VMAC"),
):
    inp = CharterpartyDisputeInput(
        fixture_id=fixture,
        vessel_name=vessel,
        charter_type=charter_type,
        daily_hire_or_demurrage_usd=daily_rate,
        bunker_price_usd_per_mt=bunker_price,
        voyage_distance_nm=distance,
        warranted_speed_knots=warr_speed,
        recorded_speed_knots=rec_speed,
        warranted_fuel_mt_day=warr_fuel,
        recorded_fuel_mt_day=rec_fuel,
        beaufort_scale=beaufort,
        douglas_sea_state=sea_state,
        allowed_laytime_hours=allowed_laytime,
        actual_laytime_used_hours=used_laytime,
        arbitration_forum=forum,
    )
    res = CharterpartyArbitrationEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
