"""CLI Commands for Maritime Phases 343-346.

Covers:
- ecdis: IMO Res. A.893(21) / SOLAS V/34 ECDIS Passage Planning & Safety Contour
- mfmbunker: Singapore SS 648:2019 Bunkering Coriolis MFM & Cappuccino Alert
- noihoint: Marine Boiler Water Chemical Treatment & Blowdown Rate
- portagency: FONASBA / Circular 39/2023 Port Agency PDA/FDA Disbursements
Adheres strictly to KISS/DRY and under 200 lines.
"""

import json
import typer

from src.core.maritime_ecdis_mfm_boiler_agency_engine import (
    BoilerWaterInput,
    BoilerWaterTreatmentEngine,
    BunkeringMfmEngine,
    BunkeringMfmInput,
    EcdisPassagePlanningEngine,
    PassageLegInput,
    PortAgencyDisbursementEngine,
    PortAgencyDisbursementInput,
)

ecdis_app = typer.Typer(help="ECDIS Passage Planning & Safety Contour Engine")
mfmbunker_app = typer.Typer(help="Bunkering Coriolis MFM & Cappuccino Alert Engine")
noihoint_app = typer.Typer(help="Marine Boiler Water Chemical Conditioning Engine")
portagency_app = typer.Typer(help="Port Agency PDA/FDA Disbursements Reconciliation")


@ecdis_app.command("plan")
def plan_passage(
    leg: str = typer.Option("LEG-SGP-VNTG", "--leg", help="Passage Leg Identifier"),
    speed: float = typer.Option(10.0, "--speed", help="Planned speed (knots)"),
    draft: float = typer.Option(8.5, "--draft", help="Static draft (meters)"),
    cb: float = typer.Option(0.80, "--cb", help="Block coefficient Cb"),
    ukc: float = typer.Option(1.0, "--ukc", help="UKC policy allowance (meters)"),
    tide: float = typer.Option(1.5, "--tide", help="Height of tide (meters)"),
    catzoc: str = typer.Option("A1", "--catzoc", help="CATZOC category (A1, A2, B, C, U)"),
    depth: float = typer.Option(11.0, "--depth", help="Charted channel depth (meters)"),
    channel: str = typer.Option("NARROW", "--channel", help="Channel type (NARROW, APPROACH, OPEN_SEA)"),
):
    inp = PassageLegInput(
        leg_name=leg,
        planned_speed_knots=speed,
        static_draft_m=draft,
        block_coefficient_cb=cb,
        ukc_policy_m=ukc,
        height_of_tide_m=tide,
        catzoc_category=catzoc,
        channel_depth_charted_m=depth,
        channel_type=channel,
    )
    res = EcdisPassagePlanningEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@mfmbunker_app.command("verify")
def verify_bunkering(
    bunker_id: str = typer.Option("BNK-2026-042", "--bunker-id", help="Bunker Operation ID"),
    fuel: str = typer.Option("VLSFO", "--fuel", help="Fuel Grade (VLSFO, MGO, ULSFO)"),
    mfm_mass: float = typer.Option(500.0, "--mfm-mass", help="MFM totalizer mass (MT)"),
    sounding_mass: float = typer.Option(495.0, "--sounding-mass", help="Vessel sounding mass (MT)"),
    drive_gain: float = typer.Option(45.0, "--drive-gain", help="Drive Gain percentage (%)"),
    density: float = typer.Option(985.0, "--density", help="Fuel density (kg/m3)"),
    density_drop: float = typer.Option(0.5, "--density-drop", help="Density fluctuation (%)"),
    sulfur: float = typer.Option(0.48, "--sulfur", help="Sulfur content percentage (%)"),
    eca: bool = typer.Option(False, "--eca", help="Vessel inside SECA zone"),
):
    inp = BunkeringMfmInput(
        bunker_id=bunker_id,
        fuel_grade=fuel,
        mfm_totalizer_mass_mt=mfm_mass,
        vessel_sounding_mass_mt=sounding_mass,
        average_drive_gain_pct=drive_gain,
        fuel_density_kg_m3=density,
        density_fluctuation_pct=density_drop,
        sulfur_content_pct=sulfur,
        is_eca_zone=eca,
    )
    res = BunkeringMfmEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@noihoint_app.command("analyze")
def analyze_boiler_water(
    boiler_id: str = typer.Option("BLR-AUX-01", "--boiler-id", help="Boiler ID"),
    boiler_type: str = typer.Option("AUXILIARY", "--type", help="Boiler type (AUXILIARY, HIGH_PRESSURE)"),
    pressure: float = typer.Option(8.5, "--pressure", help="Operating pressure (bar)"),
    ph: float = typer.Option(10.2, "--ph", help="Boiler water pH"),
    cl: float = typer.Option(120.0, "--cl", help="Chloride (ppm)"),
    alk: float = typer.Option(180.0, "--alk", help="P-alkalinity (ppm)"),
    po4: float = typer.Option(30.0, "--po4", help="Phosphate (ppm)"),
    n2h4: float = typer.Option(0.12, "--n2h4", help="Hydrazine (ppm)"),
    feed_cl: float = typer.Option(5.0, "--feed-cl", help="Feedwater chloride (ppm)"),
):
    inp = BoilerWaterInput(
        boiler_id=boiler_id,
        boiler_type=boiler_type,
        operating_pressure_bar=pressure,
        water_ph=ph,
        chloride_ppm=cl,
        p_alkalinity_ppm=alk,
        phosphate_ppm=po4,
        hydrazine_ppm=n2h4,
        feedwater_chloride_ppm=feed_cl,
    )
    res = BoilerWaterTreatmentEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@portagency_app.command("reconcile")
def reconcile_port_agency(
    call_id: str = typer.Option("CALL-2026-SG-01", "--call-id", help="Port Call ID"),
    vessel: str = typer.Option("MV MEKONG PIONEER", "--vessel", help="Vessel Name"),
    advance: float = typer.Option(35000.0, "--advance", help="Advance received (USD)"),
    tonnage: float = typer.Option(4500.0, "--tonnage", help="Tonnage dues (USD)"),
    pilotage: float = typer.Option(5200.0, "--pilotage", help="Pilotage dues (USD)"),
    towage: float = typer.Option(8500.0, "--towage", help="Towage dues (USD)"),
    berthage: float = typer.Option(3800.0, "--berthage", help="Berthage dues (USD)"),
    mooring: float = typer.Option(1200.0, "--mooring", help="Mooring/linesmen dues (USD)"),
    garbage_water: float = typer.Option(1500.0, "--garbage-water", help="Garbage and water (USD)"),
    agency_fee: float = typer.Option(3000.0, "--agency-fee", help="Agreed Agency Fee (USD)"),
    pda_total: float = typer.Option(34000.0, "--pda-total", help="Proforma PDA Total (USD)"),
):
    inp = PortAgencyDisbursementInput(
        call_id=call_id,
        vessel_name=vessel,
        advance_received_usd=advance,
        tonnage_dues_usd=tonnage,
        pilotage_dues_usd=pilotage,
        towage_dues_usd=towage,
        berthage_dues_usd=berthage,
        linesmen_and_mooring_usd=mooring,
        garbage_freshwater_usd=garbage_water,
        agency_fee_usd=agency_fee,
        proforma_total_usd=pda_total,
    )
    res = PortAgencyDisbursementEngine.evaluate(inp)
    print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
