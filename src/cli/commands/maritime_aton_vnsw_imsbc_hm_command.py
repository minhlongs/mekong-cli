"""CLI Commands for Maritime Phases 331-334: AtoN, VNSW, IMSBC, H&M Survey.

Kept under 200 lines according to KISS/YAGNI principles.
"""

import json
from typing import Optional
import typer
from rich.console import Console

from src.core.maritime_aton_vnsw_imsbc_hm_engine import (
    AtoNTelemetryInput,
    HmDamageSurveyInput,
    IalaAtoNEngine,
    ImoFalDeclarationInput,
    ImsbcGroupBEngine,
    ImsbcGroupBInput,
    VNSWClearanceEngine,
    HmDamageSurveyEngine,
)

console = Console()

aton_app = typer.Typer(help="IALA Buoyage & AIS AtoN Telemetry Management")
vnsw_app = typer.Typer(help="VNSW Maritime Single Window & IMO FAL 1-7 Clearance")
imsbc_app = typer.Typer(help="IMSBC Group B Bulk Chemical & Hold Gas Safety")
hm_app = typer.Typer(help="Hull & Machinery (H&M) Marine Casualty Damage Survey")


@aton_app.command("eval")
def eval_aton(
    mmsi: str = typer.Option(..., "--mmsi", help="MMSI of the AtoN station"),
    region: str = typer.Option("A", "--region", help="IALA Region (A or B)"),
    mark_type: str = typer.Option("LATERAL_PORT", "--mark-type", help="AtoN Mark Type"),
    aton_type: str = typer.Option("REAL", "--aton-type", help="REAL, SYNTHETIC, or VIRTUAL"),
    nom_lat: float = typer.Option(..., "--nom-lat", help="Nominal Latitude"),
    nom_lon: float = typer.Option(..., "--nom-lon", help="Nominal Longitude"),
    cur_lat: float = typer.Option(..., "--cur-lat", help="Current Latitude"),
    cur_lon: float = typer.Option(..., "--cur-lon", help="Current Longitude"),
    voltage: float = typer.Option(12.6, "--voltage", help="Battery Voltage (V)"),
    lantern: bool = typer.Option(True, "--lantern/--no-lantern", help="Lantern operational status"),
):
    inp = AtoNTelemetryInput(
        mmsi_aton=mmsi,
        region=region,
        mark_type=mark_type,
        aton_type=aton_type,
        nominal_lat=nom_lat,
        nominal_lon=nom_lon,
        current_lat=cur_lat,
        current_lon=cur_lon,
        battery_voltage=voltage,
        lantern_active=lantern,
    )
    res = IalaAtoNEngine.evaluate(inp)
    console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@vnsw_app.command("clearance")
def eval_vnsw(
    imo_argument: Optional[str] = typer.Argument(None, help="Legacy positional IMO number"),
    imo_option: Optional[str] = typer.Option(None, "--imo", help="Vessel IMO Number"),
    name: str = typer.Option("MV PACIFIC VOYAGER", "--name", help="Vessel Name"),
    port: str = typer.Option("VNSGN", "--port", help="Port of call UN/LOCODE"),
    voyage: str = typer.Option("VOY-01", "--voyage", help="Voyage number"),
    crew_count: int = typer.Option(20, "--crew-count", help="Crew members count"),
    customs: str = typer.Option("CLEARED", "--customs", help="Customs clearance status"),
    quarantine: bool = typer.Option(True, "--quarantine/--no-quarantine", help="Quarantine cleared"),
    immigration: bool = typer.Option(True, "--immigration/--no-immigration", help="Immigration cleared"),
    dues_paid: bool = typer.Option(True, "--dues/--unpaid-dues", help="Harbour dues paid"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    # Accept both the earlier positional IMO/--json interface and the newer
    # option-based Phase 332 clearance interface under the shared `vnsw` route.
    if imo_argument is not None:
        from src.cli.commands.maritime_vnsw_quarantine_marpol_command import (
            vnsw_clearance as legacy_vnsw_clearance,
        )
        legacy_vnsw_clearance(
            imo=imo_argument,
            name="MV MEKONG STAR",
            call_sign="3WKT",
            voyage_type="INTERNATIONAL",
            gt=15000.0,
            notice_type="ARRIVAL_NOTICE_24H",
            hours_before=26.0,
            forms="FAL_1,FAL_2,FAL_3,FAL_4,FAL_5,FAL_6,FAL_7",
            json_output=json_output,
        )
        return
    if imo_option is None:
        raise typer.BadParameter("Specify the IMO number as an argument or with --imo")
    inp = ImoFalDeclarationInput(
        imo_number=imo_option,
        vessel_name=name,
        call_sign="3WXYZ",
        port_of_call=port,
        voyage_number=voyage,
        fal1_general_dec=True,
        fal2_cargo_dec=True,
        fal3_stores_dec=True,
        fal4_crew_effects=True,
        fal5_crew_list_count=crew_count,
        fal6_passengers_count=0,
        fal7_dangerous_goods_manifest=False,
        customs_status=customs,
        quarantine_sanitary_cleared=quarantine,
        immigration_cleared=immigration,
        harbour_dues_paid=dues_paid,
    )
    res = VNSWClearanceEngine.evaluate(inp)
    console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@imsbc_app.command("assess")
def eval_imsbc(
    cargo: str = typer.Option("COAL", "--cargo", help="Cargo name"),
    hold: int = typer.Option(1, "--hold", help="Hold number"),
    temp: float = typer.Option(38.0, "--temp", help="Current cargo temperature (°C)"),
    prev_temp: float = typer.Option(37.0, "--prev-temp", help="Previous cargo temperature (°C)"),
    o2: float = typer.Option(20.5, "--o2", help="O2 concentration % vol"),
    co: float = typer.Option(15.0, "--co", help="CO concentration ppm"),
    ch4_lel: float = typer.Option(2.0, "--ch4-lel", help="CH4 concentration % LEL"),
    h2_lel: float = typer.Option(0.0, "--h2-lel", help="H2 concentration % LEL"),
    ph3: float = typer.Option(0.0, "--ph3", help="Phosphine gas ppm"),
):
    inp = ImsbcGroupBInput(
        cargo_name=cargo,
        hold_number=hold,
        cargo_temp_celsius=temp,
        previous_temp_celsius=prev_temp,
        o2_pct_vol=o2,
        co_ppm=co,
        ch4_pct_lel=ch4_lel,
        h2_pct_lel=h2_lel,
        ph3_ppm=ph3,
    )
    res = ImsbcGroupBEngine.evaluate(inp)
    console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))


@hm_app.command("survey")
def eval_hm(
    incident: str = typer.Option("INC-2026-001", "--incident", help="Incident ID"),
    vessel: str = typer.Option("MV MEKONG PHOENIX", "--vessel", help="Vessel Name"),
    hull_val: float = typer.Option(20000000.0, "--hull-value", help="Insured Hull Value (USD)"),
    deductible: float = typer.Option(100000.0, "--deductible", help="Policy Deductible (USD)"),
    pa_cost: float = typer.Option(500000.0, "--pa-cost", help="Particular Average repair cost (USD)"),
    ga_cost: float = typer.Option(0.0, "--ga-cost", help="General Average sacrifice cost (USD)"),
    salvage: float = typer.Option(0.0, "--salvage", help="Salvage award (USD)"),
    surveyor_fee: float = typer.Option(15000.0, "--surveyor-fee", help="Surveyor fee (USD)"),
    age: int = typer.Option(6, "--age", help="Vessel age in years"),
    new_for_old: bool = typer.Option(False, "--new-for-old", help="Apply New for Old deduction"),
):
    inp = HmDamageSurveyInput(
        incident_id=incident,
        vessel_name=vessel,
        insured_hull_value_usd=hull_val,
        deductible_usd=deductible,
        particular_average_repair_usd=pa_cost,
        general_average_sacrifice_usd=ga_cost,
        salvage_award_usd=salvage,
        surveyor_fee_usd=surveyor_fee,
        vessel_age_years=age,
        new_for_old_deduction_applicable=new_for_old,
    )
    res = HmDamageSurveyEngine.evaluate(inp)
    console.print(json.dumps(res.__dict__, indent=2, ensure_ascii=False))
