"""CLI Commands for Maritime Phases 339-342.

Covers:
- polar: IMO Polar Code POLARIS Navigation Risk Assessment
- holdwash: Cargo Hold Washwater MARPOL Annex V HME Compliance
- evfire: PCTC Car Carrier EV Lithium-ion Fire Safety Assessment
- salvage: Lloyd's Open Form LOF 2024 & SCOPIC Clause Compensation
Adheres strictly to KISS/DRY and under 200 lines.
"""

import json
import typer

from src.core.maritime_polar_wash_ev_salvage_engine import (
    EvDeckZoneInput,
    HoldCleaningInput,
    HoldWashwaterMarpolEngine,
    IceRegimeComponent,
    PctcEvFireSafetyEngine,
    PolarCodePolarisEngine,
    PolarNavigationInput,
    SalvageClaimInput,
    SalvageLofScopicEngine,
)

polar_app = typer.Typer(help="IMO Polar Code & POLARIS Risk Assessment")
holdwash_app = typer.Typer(help="Cargo Hold Washwater MARPOL HME Compliance")
evfire_app = typer.Typer(help="PCTC Car Carrier EV Lithium-ion Fire Safety")
salvage_app = typer.Typer(help="LOF 2024 & SCOPIC Clause Salvage Compensation")


@polar_app.command("evaluate")
def evaluate_polar(
    vessel: str = typer.Option("MV ARCTIC EXPLORER", "--vessel", help="Vessel Name"),
    polar_class: str = typer.Option("PC5", "--polar-class", help="Polar Class PC1-PC7 or NON_POLAR"),
    ice_type: str = typer.Option("MEDIUM_FIRST_YEAR", "--ice-type", help="Dominant Ice Type"),
    ice_tenths: int = typer.Option(7, "--ice-tenths", help="Ice concentration (0-10 tenths)"),
    mdlt: float = typer.Option(-25.0, "--mdlt", help="Mean Daily Low Temp (°C)"),
    speed: float = typer.Option(6.0, "--speed", help="Ship Speed (knots)"),
    escorted: bool = typer.Option(False, "--escorted", help="Icebreaker escort status"),
):
    inp = PolarNavigationInput(
        vessel_name=vessel,
        polar_class=polar_class,
        ice_components=[IceRegimeComponent(ice_type=ice_type, concentration_tenths=ice_tenths)],
        mdlt_celsius=mdlt,
        ship_speed_knots=speed,
        is_escorted=escorted,
    )
    res = PolarCodePolarisEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@holdwash_app.command("check")
def check_holdwash(
    hold_id: str = typer.Option("HOLD-01", "--hold-id", help="Hold Identifier"),
    cargo: str = typer.Option("Thermal Coal", "--cargo", help="Cargo Name"),
    is_hme: bool = typer.Option(False, "--is-hme", help="Harmful to Marine Environment"),
    dist_nm: float = typer.Option(15.0, "--dist-nm", help="Distance from nearest land (NM)"),
    special_area: bool = typer.Option(False, "--special-area", help="Inside MARPOL Special Area"),
    en_route: bool = typer.Option(True, "--en-route", help="Vessel is en route"),
    wash_vol_m3: float = typer.Option(80.0, "--wash-vol", help="Washwater volume m3"),
    ph: float = typer.Option(7.2, "--ph", help="Effluent pH level"),
):
    inp = HoldCleaningInput(
        hold_id=hold_id,
        cargo_name=cargo,
        is_hme=is_hme,
        distance_from_nearest_land_nm=dist_nm,
        is_in_special_area=special_area,
        vessel_en_route=en_route,
        washwater_volume_m3=wash_vol_m3,
        effluent_ph=ph,
    )
    res = HoldWashwaterMarpolEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@evfire_app.command("monitor")
def monitor_evfire(
    zone_id: str = typer.Option("ZONE-DK04", "--zone-id", help="Deck Zone ID"),
    deck_no: int = typer.Option(4, "--deck-no", help="Deck Number"),
    ev_count: int = typer.Option(120, "--ev-count", help="Number of EVs on deck"),
    area_m2: float = typer.Option(850.0, "--area", help="Deck Area m2"),
    soc_pct: float = typer.Option(45.0, "--soc", help="Average battery SoC %"),
    co_ppm: float = typer.Option(15.0, "--co", help="Carbon Monoxide PPM"),
    h2_ppm: float = typer.Option(50.0, "--h2", help="Hydrogen PPM"),
    temp_rate: float = typer.Option(0.2, "--temp-rate", help="Temperature rise rate °C/sec"),
    deluge_lpm: float = typer.Option(9500.0, "--deluge-lpm", help="Deluge pump capacity LPM"),
):
    inp = EvDeckZoneInput(
        zone_id=zone_id,
        deck_number=deck_no,
        ev_count=ev_count,
        deck_area_m2=area_m2,
        battery_avg_soc_pct=soc_pct,
        carbon_monoxide_ppm=co_ppm,
        hydrogen_ppm=h2_ppm,
        temperature_rate_c_per_sec=temp_rate,
        deluge_capacity_lpm=deluge_lpm,
    )
    res = PctcEvFireSafetyEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@salvage_app.command("settle")
def settle_salvage(
    incident_id: str = typer.Option("SALV-2026-01", "--incident", help="Salvage Incident ID"),
    vessel: str = typer.Option("MV PACIFIC CARRIER", "--vessel", help="Vessel Name"),
    salved_value: float = typer.Option(50000000.0, "--salved-value", help="Salved Value (USD)"),
    scopic: bool = typer.Option(True, "--scopic", help="SCOPIC Invoked"),
    tariff_cost: float = typer.Option(2500000.0, "--tariff-cost", help="SCOPIC Tariff Costs (USD)"),
    severity: str = typer.Option("HIGH", "--severity", help="Environmental severity (LOW/MEDIUM/HIGH)"),
):
    inp = SalvageClaimInput(
        incident_id=incident_id,
        vessel_name=vessel,
        salved_value_usd=salved_value,
        is_scopic_invoked=scopic,
        scopic_tariff_costs_usd=tariff_cost,
        environmental_danger_severity=severity,
    )
    res = SalvageLofScopicEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
