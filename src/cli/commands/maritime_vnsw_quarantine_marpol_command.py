"""CLI Commands for Maritime Single Window (VNSW), Border Control, Quarantine & MARPOL (Phases 191-194)."""

import dataclasses
import enum
import json
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from src.core.maritime_vnsw_quarantine_marpol_engine import (
    VNSWNotificationType, VesselVoyageType, SeafarerRank, SeafarerCrewMember,
    MaritimeSingleWindowEngine, SeafarerImmigrationEngine,
    MaritimeHealthQuarantineEngine, MARPOLPortReceptionEngine,
)

console = Console()

vnsw_app = typer.Typer(name="vnsw", help="Phase 191: Vietnam National Maritime Single Window (VNSW) & e-Port Clearance.", no_args_is_help=True)
seafarer_app = typer.Typer(name="seafarer", help="Phase 192: Seafarer Safe Manning, STCW Rest Hours & Border Immigration Shore Pass.", no_args_is_help=True)
quarantine_app = typer.Typer(name="quarantine", help="Phase 193: Maritime International Health Quarantine, SSCEC & Free Pratique.", no_args_is_help=True)
marpol_app = typer.Typer(name="marpol", help="Phase 194: Marine Environmental Protection, MARPOL 73/78 & PRF Waste Reception.", no_args_is_help=True)


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    data = dataclasses.asdict(obj) if dataclasses.is_dataclass(obj) else (obj.__dict__ if hasattr(obj, "__dict__") else obj)
    print(json.dumps(data, indent=2, default=_json_serial))


def _print_table(title: str, col1: str, col2: str, rows: list[tuple[str, str]]) -> None:
    table = Table(title=title)
    table.add_column(col1, style="cyan")
    table.add_column(col2, style="green")
    for k, v in rows:
        table.add_row(k, v)
    console.print(table)


@vnsw_app.command("clearance")
def vnsw_clearance(
    imo: str = typer.Argument("9382710", help="Vessel IMO Number"),
    name: str = typer.Option("MV MEKONG STAR", "--name", "-n", help="Vessel Name"),
    call_sign: str = typer.Option("3WKT", "--call-sign", help="Vessel Call Sign"),
    voyage_type: str = typer.Option("INTERNATIONAL", "--voyage", help="Voyage Type (INTERNATIONAL, DOMESTIC)"),
    gt: float = typer.Option(15000.0, "--gt", help="Gross Tonnage (GT)"),
    notice_type: str = typer.Option("ARRIVAL_NOTICE_24H", "--notice-type", help="Notification Type"),
    hours_before: float = typer.Option(26.0, "--hours", help="Hours notice sent before event"),
    forms: str = typer.Option("FAL_1,FAL_2,FAL_3,FAL_4,FAL_5,FAL_6,FAL_7", "--forms", help="Comma-separated FAL forms submitted"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate VNSW port clearance compliance, FAL document checklist, and statutory dues."""
    v_type = VesselVoyageType(voyage_type.upper()) if voyage_type.upper() in VesselVoyageType.__members__ else VesselVoyageType.INTERNATIONAL
    n_type = VNSWNotificationType(notice_type.upper()) if notice_type.upper() in VNSWNotificationType.__members__ else VNSWNotificationType.ARRIVAL_NOTICE_24H
    submitted = [f.strip() for f in forms.split(",") if f.strip()]
    res = MaritimeSingleWindowEngine.evaluate_port_clearance(imo, name, call_sign, v_type, gt, n_type, hours_before, submitted)
    if json_output:
        _dump_json(res)
        return
    _print_table(f"VNSW Port Clearance Assessment — {res.vessel_name} (IMO {res.imo_number})", "Parameter", "Details", [
        ("Voyage & Tonnage", f"{res.voyage_type.value} ({res.gross_tonnage:,.0f} GT)"),
        ("Notification Timeliness", "[green]TIMELY[/green]" if res.is_notification_timely else "[red]DELAYED/BREACH[/red]"),
        ("Dossier Completeness", "[green]COMPLETE[/green]" if res.is_dossier_complete else f"[red]MISSING: {', '.join(res.missing_declarations)}[/red]"),
        ("Clearance Status", f"[bold yellow]{res.status.value}[/bold yellow]"),
        ("Clearance Permit No", res.clearance_permit_no),
        ("Tonnage Dues", f"{res.tonnage_dues_vnd:,.0f} VND"),
        ("Maritime Safety Fee", f"{res.maritime_safety_fee_vnd:,.0f} VND"),
        ("Port Clearance Fee", f"{res.port_clearance_fee_vnd:,.0f} VND"),
        ("Total Statutory Dues", f"[bold green]{res.total_statutory_dues_vnd:,.0f} VND[/bold green]"),
        ("QR Verification URL", res.qr_verification_payload),
    ])


@seafarer_app.command("audit")
def seafarer_audit(
    vessel_name: str = typer.Argument("MV PACIFIC OCEAN", help="Vessel Name"),
    assessment_date: Optional[str] = typer.Option(None, "--assess-date", help="Assessment date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Audit seafarer safe manning levels, STCW rest hours, and issue Shore Passes."""
    sample_crew = [
        SeafarerCrewMember("Nguyen Van A", "VNM", "B1234567", "VN-0988", SeafarerRank.MASTER, "2028-12-31", "2028-12-31", 11.0, 84.0),
        SeafarerCrewMember("Tran Van B", "VNM", "B2345678", "VN-0989", SeafarerRank.CHIEF_MATE, "2028-12-31", "2028-12-31", 10.5, 80.0),
        SeafarerCrewMember("Le Van C", "VNM", "B3456789", "VN-0990", SeafarerRank.CHIEF_ENGINEER, "2028-12-31", "2028-12-31", 12.0, 88.0),
        SeafarerCrewMember("Pham Van D", "VNM", "B4567890", "VN-0991", SeafarerRank.SECOND_ENGINEER, "2028-12-31", "2028-12-31", 10.0, 78.0),
        SeafarerCrewMember("Do Van E", "VNM", "B5678901", "VN-0992", SeafarerRank.RATING_ABLE_SEAMAN, "2028-12-31", "2028-12-31", 10.0, 77.0),
    ]
    res = SeafarerImmigrationEngine.audit_crew_and_immigration(vessel_name, sample_crew, assessment_date)
    if json_output:
        _dump_json(res)
        return
    _print_table(f"Seafarer Manning & Border Immigration Audit — {res.vessel_name}", "Criterion", "Evaluation", [
        ("Total Crew Complement", f"{res.total_crew_count} Seafarers"),
        ("Safe Manning (MSMD)", "[green]COMPLIANT[/green]" if res.is_safe_manning_compliant else "[red]NON-COMPLIANT[/red]"),
        ("STCW Rest Compliance", "[green]COMPLIANT[/green]" if res.is_stcw_rest_compliant else "[red]BREACH DETECTED[/red]"),
        ("Shore Passes Granted", f"[bold green]{res.shore_pass_granted_count}[/bold green]"),
        ("Shore Passes Denied", f"[bold red]{res.shore_pass_denied_count}[/bold red]"),
        ("Immigration Status", res.immigration_status.value),
    ])


@quarantine_app.command("evaluate")
def quarantine_evaluate(
    vessel_name: str = typer.Argument("MV OCEAN PEARL", help="Vessel Name"),
    sscec_expiry: str = typer.Option("2026-12-31", "--sscec-exp", help="SSCEC expiry date (YYYY-MM-DD)"),
    infected_cases: int = typer.Option(0, "--cases", help="Communicable disease cases detected"),
    yellow_fever_port: bool = typer.Option(False, "--yellow-fever", help="Has visited endemic yellow fever port"),
    assess_date: Optional[str] = typer.Option(None, "--assess-date", help="Assessment date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Evaluate Maritime Declaration of Health, SSCEC validity, and Free Pratique."""
    res = MaritimeHealthQuarantineEngine.evaluate_health_quarantine(vessel_name, sscec_expiry, infected_cases, yellow_fever_port, assess_date)
    if json_output:
        _dump_json(res)
        return
    rows = [
        ("SSCEC Certificate Expiry", f"{res.sscec_valid_until_iso} ({'VALID' if res.is_sscec_valid else 'EXPIRED'})"),
        ("Communicable Cases", f"{res.communicable_cases_detected} Cases"),
        ("Epidemiological Risk Score", f"{res.epidemiological_risk_score:.2f}"),
        ("Quarantine Status", f"[bold yellow]{res.quarantine_status.value}[/bold yellow]"),
        ("Yellow Flag 'Q' Required", "[bold red]YES (HOISTED)[/bold red]" if res.yellow_flag_required else "[bold green]NO[/bold green]"),
    ]
    if res.free_pratique_certificate_no:
        rows.append(("Free Pratique Cert No", res.free_pratique_certificate_no))
    _print_table(f"Maritime International Health Quarantine — {res.vessel_name}", "Parameter", "Result", rows)


@marpol_app.command("audit")
def marpol_audit(
    vessel_name: str = typer.Argument("MV GREEN VOYAGER", help="Vessel Name"),
    ows_ppm: float = typer.Option(12.5, "--ows-ppm", help="OWS bilge oil content in ppm"),
    fuel_sulfur: float = typer.Option(0.45, "--sulfur", help="Fuel sulfur content percentage"),
    sludge_m3: float = typer.Option(5.0, "--sludge", help="Sludge volume delivered to PRF (m3)"),
    garbage_m3: float = typer.Option(2.0, "--garbage", help="Garbage volume delivered to PRF (m3)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Audit MARPOL Annex I/VI compliance and PRF waste delivery certificate."""
    res = MARPOLPortReceptionEngine.evaluate_environmental_compliance(vessel_name, ows_ppm, fuel_sulfur, sludge_m3, garbage_m3)
    if json_output:
        _dump_json(res)
        return
    rows = [
        ("OWS Bilge Oil Content", f"{res.ows_bilge_oil_content_ppm:.1f} ppm ({'PASS (<=15 ppm)' if res.is_ows_compliant else 'FAIL (>15 ppm)'})"),
        ("Fuel Sulfur Content", f"{res.fuel_sulfur_content_pct:.2f}% ({'PASS (<=0.50%)' if res.is_fuel_sulfur_compliant else 'FAIL (>0.50%)'})"),
        ("Overall MARPOL Compliance", "[bold green]COMPLIANT[/bold green]" if res.is_marpol_fully_compliant else "[bold red]BREACH DETECTED[/bold red]"),
    ]
    if res.prf_waste_delivery_receipt_no:
        rows.extend([
            ("PRF Waste Delivery Receipt", res.prf_waste_delivery_receipt_no),
            ("Disposed Volumes", f"{res.sludge_delivered_m3} m3 Sludge, {res.garbage_delivered_m3} m3 Garbage"),
            ("Environmental PRF Tariff", f"{res.environmental_levy_vnd:,.0f} VND"),
        ])
    _print_table(f"MARPOL 73/78 & Port Reception Environmental Audit — {res.vessel_name}", "Inspection Item", "Compliance Status", rows)
