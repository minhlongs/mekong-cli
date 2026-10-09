"""Typer CLI Command Group for Maritime Phases 351-354.

Commands:
- loadingcomp / ondinhtau: Bulk carrier loading computer, stability & hull stress
- hnsdrift / toicathns: HNS chemical spill drift trajectory & hazard perimeter
- centralcool / lammatbien: Central seawater cooling, scoop savings & MGPS biofouling
- ecert / chungchiso: Marine electronic certificates & IMO FAL verification
Strictly kept under 200 lines.
"""

import json
import typer
from rich.console import Console

from src.core.maritime_loading_hns_cool_ecert_engine import (
    BulkLoadingEngine,
    BulkLoadingInput,
    CentralCoolingEngine,
    CentralCoolingInput,
    HnsDriftEngine,
    HnsDriftInput,
    MarineEcertEngine,
    MarineEcertInput,
)

console = Console()

loading_app = typer.Typer(help="Bulk Carrier Loading Computer & Intact Stability (Phase 351)")
hns_app = typer.Typer(help="HNS Chemical Spill Drift Trajectory & Hazard Zone (Phase 352)")
cooling_app = typer.Typer(help="Central Seawater Cooling & MGPS Bio-Fouling (Phase 353)")
ecert_app = typer.Typer(help="Marine Electronic Certificates & IMO FAL Verification (Phase 354)")


@loading_app.command("evaluate")
def evaluate_loading(
    vessel: str = typer.Option("BULK-01", "--vessel", "-v", help="Vessel ID"),
    disp: float = typer.Option(65000.0, "--displacement", "-d", help="Displacement (tonnes)"),
    km: float = typer.Option(11.2, "--km", help="Transverse KM (m)"),
    kg: float = typer.Option(9.8, "--kg", help="Solid KG (m)"),
    swbm: float = typer.Option(120000.0, "--swbm", help="Calculated SWBM (kN.m)"),
    swbm_perm: float = typer.Option(150000.0, "--swbm-perm", help="Permissible SWBM (kN.m)"),
):
    """Evaluate bulk carrier loading computer stability and hull bending/shear stress."""
    inp = BulkLoadingInput(
        vessel_id=vessel,
        displacement_tonnes=disp,
        km_transverse_m=km,
        kg_solid_m=kg,
        calculated_swbm_kntm=swbm,
        permissible_swbm_kntm=swbm_perm,
    )
    res = BulkLoadingEngine.evaluate(inp)
    console.print_json(json.dumps(res.__dict__))


@hns_app.command("simulate")
def simulate_hns_drift(
    un_number: str = typer.Option("UN1203", "--un", help="Chemical UN Number"),
    name: str = typer.Option("MOTOR SPIRIT", "--name", help="Chemical name"),
    group: str = typer.Option("FE", "--group", help="CEDRE behavior group (E/F/D/S)"),
    tonnes: float = typer.Option(50.0, "--tonnes", help="Spill quantity (tonnes)"),
    curr_spd: float = typer.Option(1.5, "--curr-spd", help="Current speed (knots)"),
    curr_dir: float = typer.Option(90.0, "--curr-dir", help="Current direction (deg)"),
    wind_spd: float = typer.Option(20.0, "--wind-spd", help="Wind speed (knots)"),
    wind_dir: float = typer.Option(180.0, "--wind-dir", help="Wind direction (deg)"),
    hours: float = typer.Option(4.0, "--hours", help="Elapsed hours"),
):
    """Simulate HNS chemical spill drift vector and emergency isolation perimeter."""
    inp = HnsDriftInput(
        chemical_un_number=un_number,
        chemical_name=name,
        behavior_group=group,
        spill_quantity_tonnes=tonnes,
        current_speed_knots=curr_spd,
        current_direction_deg=curr_dir,
        wind_speed_knots=wind_spd,
        wind_direction_deg=wind_dir,
        elapsed_hours=hours,
    )
    res = HnsDriftEngine.evaluate(inp)
    console.print_json(json.dumps(res.__dict__))


@cooling_app.command("evaluate")
def evaluate_cooling(
    vessel: str = typer.Option("CONTAINER-01", "--vessel", "-v", help="Vessel ID"),
    heat_kw: float = typer.Option(4500.0, "--heat-kw", help="Heat duty (kW)"),
    fw_in: float = typer.Option(48.0, "--fw-in", help="Freshwater inlet temp (°C)"),
    fw_out: float = typer.Option(36.0, "--fw-out", help="Freshwater outlet temp (°C)"),
    sw_in: float = typer.Option(28.0, "--sw-in", help="Seawater inlet temp (°C)"),
    speed: float = typer.Option(15.0, "--speed", help="Vessel speed (knots)"),
    mgps_cu: float = typer.Option(2.5, "--mgps-cu", help="MGPS Cu anode current (Amps)"),
):
    """Evaluate central seawater cooling heat balance and MGPS bio-fouling dosing."""
    inp = CentralCoolingInput(
        vessel_id=vessel,
        heat_duty_kw=heat_kw,
        freshwater_in_temp_c=fw_in,
        freshwater_out_temp_c=fw_out,
        seawater_in_temp_c=sw_in,
        vessel_speed_knots=speed,
        mgps_copper_current_amps=mgps_cu,
    )
    res = CentralCoolingEngine.evaluate(inp)
    console.print_json(json.dumps(res.__dict__))


@ecert_app.command("verify")
def verify_ecert(
    cert_id: str = typer.Option("UTN-DNV-2025-001", "--cert-id", help="Certificate UTN"),
    cert_type: str = typer.Option("CLASS", "--cert-type", help="Certificate Type"),
    imo: str = typer.Option("IMO9876543", "--imo", help="Vessel IMO"),
    name: str = typer.Option("MEKONG VOYAGER", "--name", help="Vessel Name"),
    ro: str = typer.Option("DNV", "--ro", help="Issuing RO"),
    issue_date: str = typer.Option("2025-01-15", "--issue-date", help="Issue Date (YYYY-MM-DD)"),
    expiry_date: str = typer.Option("2030-01-14", "--expiry-date", help="Expiry Date (YYYY-MM-DD)"),
    url: str = typer.Option("https://verify.dnv.com/ecert", "--url", help="Verification URL"),
    signature: str = typer.Option("", "--sig", help="Digital signature (hex)"),
):
    """Verify marine electronic statutory certificate integrity and status."""
    import hashlib
    if not signature:
        raw = f"{cert_id}|{imo}|{cert_type}|{ro}|{issue_date}|{expiry_date}"
        signature = hashlib.sha256(raw.encode("utf-8")).hexdigest()

    inp = MarineEcertInput(
        certificate_id=cert_id,
        certificate_type=cert_type,
        vessel_imo=imo,
        vessel_name=name,
        issuing_ro=ro,
        issue_date_iso=issue_date,
        expiry_date_iso=expiry_date,
        verification_url=url,
        digital_signature_hex=signature,
    )
    res = MarineEcertEngine.evaluate(inp)
    console.print_json(json.dumps(res.__dict__))
