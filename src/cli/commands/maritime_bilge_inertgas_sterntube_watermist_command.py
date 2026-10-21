"""Typer CLI commands for Maritime Phases 403-406.

Includes:
- Bilge Water Separator & ODMCS 15 ppm (Phase 403 MARPOL Annex I, MEPC.107(49))
- Inert Gas System & N2 Membrane Generator (Phase 404 SOLAS II-2, IMO FSS Ch.15)
- Stern Tube Hydrodynamic Lubrication & EAL Seal (Phase 405 US VGP 2013, DNV Pt.4)
- High-Pressure Water Mist Fire Extinguishing (Phase 406 SOLAS II-2, IMO MSC/Circ.1165)

Strictly < 200 LOC, zero mocks.
"""

import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime.phase_403_bilge_water_separator_odmcs import (
    BilgeOdmcsTelemetry,
    BilgeWaterSeparatorOdmcsEngine,
)
from src.core.maritime.phase_404_inert_gas_n2_generator import (
    InertGasN2GeneratorEngine,
    InertGasN2Telemetry,
)
from src.core.maritime.phase_405_stern_tube_bio_lubrication import (
    SternTubeBioLubricationEngine,
    SternTubeTelemetry,
)
from src.core.maritime.phase_406_water_mist_fire_extinguishing import (
    WaterMistFireExtinguishingEngine,
    WaterMistTelemetry,
)

console = Console()

bilgeseparator_app = typer.Typer(help="Phase 403: Bilge Water Separator & ODMCS (MARPOL Annex I Reg 14/31)")
inertgas_app = typer.Typer(help="Phase 404: Inert Gas System & N2 Membrane Generator (SOLAS II-2 / FSS 15)")
sterntube_app = typer.Typer(help="Phase 405: Stern Tube Hydrodynamic Lubrication & EAL (US VGP / DNV Pt.4)")
watermist_app = typer.Typer(help="Phase 406: Marine Water Mist Fire Extinguishing (SOLAS II-2 / Circ.1165)")


@bilgeseparator_app.callback(invoke_without_command=True)
def evaluate_bilge_separator(
    oil_ppm: float = typer.Option(8.5, "--ppm", help="Oil content in ppm"),
    flow_m3_h: float = typer.Option(2.5, "--flow", help="Sample flow rate m3/h"),
    speed_knots: float = typer.Option(12.0, "--speed", help="Vessel speed in knots"),
    droplet_um: float = typer.Option(55.0, "--droplet", help="Oil droplet diameter in microns"),
    recirc: bool = typer.Option(False, "--recirc", help="3-way valve recirculating to bilge"),
    flushing: bool = typer.Option(False, "--flushing", help="Clean water flushing active"),
):
    """Evaluate Bilge Water Separator Stokes settling, 15 ppm alarm, and ODMCS."""
    telem = BilgeOdmcsTelemetry(
        oil_content_ppm=oil_ppm,
        sample_flow_rate_m3_h=flow_m3_h,
        vessel_speed_knots=speed_knots,
        oil_droplet_diameter_um=droplet_um,
        three_way_valve_to_bilge=recirc,
        clean_water_flushing=flushing,
    )
    res = BilgeWaterSeparatorOdmcsEngine().evaluate(telem)

    table = Table(title="Maritime Phase 403: Bilge Separator & ODMCS (MEPC.107(49))")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Status", res.status.value)
    table.add_row("Stokes Rising Velocity", f"{res.stokes_rising_velocity_m_s:.6f} m/s")
    table.add_row("Coalescer Efficiency", f"{res.coalescence_retention_efficiency_pct:.1f}%")
    table.add_row("Discharge Rate", f"{res.discharge_liters_per_nautical_mile:.2f} L/NM")
    table.add_row("15 ppm ASD Trip", "ACTIVE" if res.asd_trip_activated else "CLEAR")
    table.add_row("Tamper Checksum", hex(res.audit_entry.tamper_proof_checksum))
    console.print(table)


@inertgas_app.callback(invoke_without_command=True)
def evaluate_inert_gas(
    feed_press_bar: float = typer.Option(12.0, "--press-bar", help="Feed air pressure in bar"),
    feed_temp_c: float = typer.Option(45.0, "--temp-c", help="Feed air temperature in °C"),
    o2_pct: float = typer.Option(3.8, "--o2-pct", help="Measured O2 content %"),
    deck_press_mmwg: float = typer.Option(850.0, "--deck-press", help="Deck main pressure in mmWG"),
    vent_open: bool = typer.Option(False, "--vent-open", help="Atmospheric vent valve open"),
):
    """Evaluate Inert Gas System & N2 Membrane flammability and P/V seal safety."""
    telem = InertGasN2Telemetry(
        feed_air_pressure_bar=feed_press_bar,
        feed_air_temperature_c=feed_temp_c,
        measured_oxygen_content_pct=o2_pct,
        deck_main_pressure_mmwg=deck_press_mmwg,
        atmospheric_vent_valve_open=vent_open,
    )
    res = InertGasN2GeneratorEngine().evaluate(telem)

    table = Table(title="Maritime Phase 404: Inert Gas & N2 Generator (SOLAS II-2)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Operating State", res.state.value)
    table.add_row("Oxygen Content", f"{res.oxygen_content_pct:.2f}%")
    table.add_row("Permeation Flux Ratio", f"{res.permeation_flux_ratio:.3f}")
    table.add_row("Deck Main Pressure", f"{res.deck_pressure_mmwg:.1f} mmWG")
    table.add_row("P/V Breaker Tripped", "YES" if res.pv_breaker_tripped else "NO")
    table.add_row("Atmospheric Venting", "ACTIVE" if res.atmospheric_venting_active else "CLOSED")
    console.print(table)


@sterntube_app.callback(invoke_without_command=True)
def evaluate_stern_tube(
    temp_c: float = typer.Option(48.0, "--temp-c", help="Bearing temperature °C"),
    rpm: float = typer.Option(85.0, "--rpm", help="Shaft speed RPM"),
    load_n: float = typer.Option(185000.0, "--load-n", help="Bearing load in N"),
    oil_press_bar: float = typer.Option(1.25, "--seal-bar", help="Seal oil pressure in bar"),
    aft_draft_m: float = typer.Option(9.8, "--draft-m", help="Aft draft in meters"),
    water_ppm: float = typer.Option(350.0, "--water-ppm", help="EAL water content ppm"),
    tan_val: float = typer.Option(0.65, "--tan", help="Total Acid Number mg KOH/g"),
):
    """Evaluate Stern Tube Sommerfeld lubrication number and EAL seal differential pressure."""
    telem = SternTubeTelemetry(
        bearing_temperature_c=temp_c,
        shaft_speed_rpm=rpm,
        bearing_load_n=load_n,
        seal_oil_pressure_bar=oil_press_bar,
        aft_draft_m=aft_draft_m,
        eal_water_content_ppm=water_ppm,
        total_acid_number_tan_mg_koh_g=tan_val,
    )
    res = SternTubeBioLubricationEngine().evaluate(telem)

    table = Table(title="Maritime Phase 405: Stern Tube Bio-Lubrication (VGP / DNV Pt.4)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Lubrication Regime", res.regime.value)
    table.add_row("Sommerfeld Number (S)", f"{res.sommerfeld_number:.4f}")
    table.add_row("Film Parameter (lambda)", f"{res.film_parameter_lambda:.2f}")
    table.add_row("Differential Seal Pressure", f"{res.differential_seal_pressure_bar:.3f} bar")
    table.add_row("Overpressure Adequate", "PASS" if res.oil_overpressure_adequate else "FAIL")
    table.add_row("EAL Health Status", res.eal_health_status)
    console.print(table)


@watermist_app.callback(invoke_without_command=True)
def evaluate_water_mist(
    nozzle_bar: float = typer.Option(120.0, "--nozzle-bar", help="Nozzle pressure in bar"),
    nozzles_count: int = typer.Option(16, "--nozzles", help="Number of active nozzles"),
    volume_m3: float = typer.Option(850.0, "--volume-m3", help="Enclosure volume in m3"),
    fire_kw: float = typer.Option(4500.0, "--fire-kw", help="Fire heat release rate kW"),
    duration_s: float = typer.Option(180.0, "--duration-s", help="Discharge duration seconds"),
    storage_m3: float = typer.Option(12.0, "--storage-m3", help="Freshwater storage volume m3"),
):
    """Evaluate Marine High-Pressure Water Mist atomization, cooling duty, and inerting."""
    telem = WaterMistTelemetry(
        nozzle_operating_pressure_bar=nozzle_bar,
        active_nozzles_count=nozzles_count,
        enclosure_volume_m3=volume_m3,
        fire_heat_release_rate_kw=fire_kw,
        discharge_duration_seconds=duration_s,
        freshwater_storage_volume_m3=storage_m3,
    )
    res = WaterMistFireExtinguishingEngine().evaluate(telem)

    table = Table(title="Maritime Phase 406: Water Mist Extinguishing (SOLAS II-2)")
    table.add_column("Parameter / Indicator", style="cyan")
    table.add_column("Value / Status", style="magenta")
    table.add_row("Operating Mode", res.mode.value)
    table.add_row("Total Flow Rate", f"{res.total_flow_rate_lpm:.1f} LPM")
    table.add_row("Latent Cooling Capacity", f"{res.latent_cooling_capacity_kw:.1f} kW")
    table.add_row("Steam Volume Expansion", f"{res.steam_volume_ratio_pct:.1f}%")
    table.add_row("Estimated Depleted O2", f"{res.estimated_depleted_o2_pct:.1f}%")
    table.add_row("Water Storage Adequate", "PASS" if res.adequate_water_storage else "FAIL")
    table.add_row("Extinguishment Assured", "ASSURED" if res.extinguishment_assured else "UNASSURED")
    console.print(table)
