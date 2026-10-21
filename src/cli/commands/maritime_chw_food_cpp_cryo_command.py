"""Maritime Typer CLI Commands: Phases 387-390."""

from rich.console import Console
from rich.table import Table
import typer

from src.core.maritime.phase_387_chilled_water_hvac_control import ChilledWaterHvacEngine, ChilledWaterHvacInput
from src.core.maritime.phase_388_food_waste_pulper_biodigestion import FoodWastePulperEngine, FoodWastePulperInput
from src.core.maritime.phase_389_cpp_pitch_hydraulic_load import CppPitchControlEngine, CppPitchControlInput
from src.core.maritime.phase_390_cryogenic_tank_leak_insulation import CryogenicTankLeakEngine, CryogenicTankLeakInput

console = Console()
hvac_app = typer.Typer(help="Maritime Chilled Water HVAC & Cargo Hold Climate Control")
food_app = typer.Typer(help="MARPOL Annex V Food Waste Pulper & Bio-Digestion")
cpp_app = typer.Typer(help="Controllable Pitch Propeller (CPP) Hydraulics & Load")
cryo_app = typer.Typer(help="Cryogenic Cargo Tank Leak Sniffer & Insulation Relief")


@hvac_app.command("evaluate")
def evaluate_hvac(
    flow_m3_h: float = typer.Option(65.0, help="Chilled water flow rate m3/h"),
    t_supply: float = typer.Option(7.0, help="CHW supply temp C"),
    t_return: float = typer.Option(12.0, help="CHW return temp C"),
    power_kw: float = typer.Option(85.0, help="Compressor power kW"),
    amb_t: float = typer.Option(32.0, help="Ambient temp C"),
    amb_rh: float = typer.Option(80.0, help="Ambient relative humidity %"),
    hold_t: float = typer.Option(24.0, help="Hold air temp C"),
    cargo_t: float = typer.Option(22.0, help="Cargo surface temp C"),
    hold_rh: float = typer.Option(65.0, help="Hold relative humidity %"),
    refrigerant_ppm: float = typer.Option(0.0, help="Refrigerant gas leak ppm"),
) -> None:
    """Evaluates chilled water loop duty, COP, hold sweat and halocarbon leak."""
    res = ChilledWaterHvacEngine().evaluate(ChilledWaterHvacInput(
        chw_flow_rate_m3_h=flow_m3_h, chw_temp_supply_c=t_supply, chw_temp_return_c=t_return,
        compressor_power_kw=power_kw, ambient_temp_c=amb_t, ambient_relative_humidity_pct=amb_rh,
        cargo_hold_temp_c=hold_t, cargo_surface_temp_c=cargo_t, cargo_hold_rh_pct=hold_rh,
        refrigerant_concentration_ppm=refrigerant_ppm,
    ))
    table = Table(title="Marine Chilled Water & Cargo Hold HVAC Assessment (ISO 5149)")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in [
        ("Cooling Capacity (kW)", f"{res.cooling_capacity_kw:.2f}"), ("Actual COP", f"{res.cop_actual:.2f}"),
        ("Outside Dew Point", f"{res.ambient_dew_point_c:.1f} °C"), ("Cargo Hold Dew Point", f"{res.hold_dew_point_c:.1f} °C"),
        ("Sweat Hazard", res.sweat_hazard), ("Ventilation Action", res.ventilation_action),
        ("Chiller Status", res.chiller_status), ("Compressor Trip", str(res.compressor_trip)),
    ]:
        table.add_row(k, v)
    console.print(table)


@food_app.command("evaluate")
def evaluate_food(
    particle_mm: float = typer.Option(18.0, help="Screened particle size mm (<=25mm)"),
    dist_nm: float = typer.Option(14.0, help="Distance to nearest land NM"),
    special_area: bool = typer.Option(False, help="Inside MARPOL Special Area"),
    speed_kts: float = typer.Option(12.0, help="Ship navigation speed knots"),
    vfa_tic: float = typer.Option(0.22, help="Digester VFA/TIC ratio"),
    grease_ppm: float = typer.Option(8.5, help="Grease trap oil content ppm"),
    waste_kg: float = typer.Option(120.0, help="Daily food waste kg"),
) -> None:
    """Evaluates MARPOL Annex V food waste comminution and discharge compliance."""
    res = FoodWastePulperEngine().evaluate(FoodWastePulperInput(
        particle_size_mm=particle_mm, distance_to_nearest_land_nm=dist_nm, in_special_area=special_area,
        ship_speed_knots=speed_kts, vfa_to_tic_ratio=vfa_tic, grease_trap_oil_ppm=grease_ppm, daily_waste_mass_kg=waste_kg,
    ))
    table = Table(title="Food Waste Pulper & Bio-Digestion Status (MARPOL Annex V)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Evaluation", style="green")
    for k, v in [
        ("Comminution Compliant (<=25mm)", str(res.comminution_compliant)),
        ("Overboard Discharge Permitted", str(res.discharge_permitted)),
        ("Digester Health", res.digester_status), ("Grease Trap Compliant", str(res.grease_trap_compliant)),
        ("Biogas Yield Est (m3)", f"{res.biogas_yield_estimate_m3:.2f}"),
        ("Regulatory Classification", res.regulatory_classification),
    ]:
        table.add_row(k, v)
    console.print(table)


@cpp_app.command("evaluate")
def evaluate_cpp(
    commanded_pitch: float = typer.Option(20.0, help="Commanded pitch deg"),
    actual_pitch: float = typer.Option(19.8, help="Actual feedback pitch deg"),
    travel_time_s: float = typer.Option(18.0, help="Full travel stroke time s"),
    pressure_bar: float = typer.Option(55.0, help="Servo oil pressure bar"),
    seal_bar: float = typer.Option(2.2, help="Stern tube seal header pressure bar"),
    seawater_bar: float = typer.Option(1.6, help="Seawater draft pressure bar"),
    engine_load_pct: float = typer.Option(88.0, help="Engine load % MCR"),
    exhaust_t: float = typer.Option(430.0, help="Mean exhaust gas temp C"),
) -> None:
    """Evaluates CPP hydraulic servo response, stern tube seal and combinator load."""
    res = CppPitchControlEngine().evaluate(CppPitchControlInput(
        commanded_pitch_deg=commanded_pitch, actual_pitch_deg=actual_pitch, pitch_travel_time_s=travel_time_s,
        hydraulic_pressure_bar=pressure_bar, seal_header_pressure_bar=seal_bar,
        sea_water_draft_pressure_bar=seawater_bar, main_engine_load_pct=engine_load_pct, exhaust_gas_temp_c=exhaust_t,
    ))
    table = Table(title="Controllable Pitch Propeller (CPP) Hydraulics (DNV-RU-SHIP)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Evaluation", style="green")
    for k, v in [
        ("Hydraulic Servo Status", res.hydraulic_status), ("Travel Rate Compliant (<=25s)", str(res.pitch_response_compliant)),
        ("Stern Tube Seal Barrier Intact", str(res.seal_barrier_intact)), ("Seal Margin", f"{res.seal_pressure_margin_bar:.2f} bar"),
        ("Engine Overload Active", str(res.engine_overload_protection)), ("Recommended Pitch", f"{res.recommended_pitch_deg:.1f}°"),
    ]:
        table.add_row(k, v)
    console.print(table)


@cryo_app.command("evaluate")
def evaluate_cryo(
    ch4_vol_pct: float = typer.Option(0.05, help="Methane in interbarrier vol %"),
    dew_point_c: float = typer.Option(-45.0, help="Insulation dew point C"),
    o2_pct: float = typer.Option(0.5, help="Oxygen in N2 blanket vol %"),
    diff_p_kpa: float = typer.Option(0.8, help="Insulation space diff pressure kPa"),
    hull_temp_c: float = typer.Option(12.0, help="Inner hull steel temp C"),
    glycol_active: bool = typer.Option(True, help="Glycol heating loop active"),
) -> None:
    """Evaluates cryogenic gas carrier primary barrier leak and insulation pressure relief."""
    res = CryogenicTankLeakEngine().evaluate(CryogenicTankLeakInput(
        methane_concentration_vol_pct=ch4_vol_pct, dew_point_c=dew_point_c, oxygen_concentration_pct=o2_pct,
        insulation_diff_pressure_kpa=diff_p_kpa, inner_hull_steel_temp_c=hull_temp_c, glycol_heating_active=glycol_active,
    ))
    table = Table(title="Cryogenic Cargo Tank Leak & Insulation Relief (IMO IGC Code)")
    table.add_column("Parameter", style="cyan")
    table.add_column("Evaluation", style="green")
    for k, v in [
        ("Barrier Integrity", res.barrier_integrity), ("Atmosphere Inert Compliant", str(res.atmosphere_inert_compliant)),
        ("Pressure Relief Required", str(res.pressure_relief_required)), ("Cold Spot Detected (<0C)", str(res.hull_cold_spot_detected)),
        ("Tank Safety Status", res.cargo_tank_safety_status), ("Mast Vent Active", str(res.vent_mast_exhaust_active)),
    ]:
        table.add_row(k, v)
    console.print(table)
