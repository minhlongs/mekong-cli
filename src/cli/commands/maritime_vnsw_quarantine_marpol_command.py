"""CLI Commands for Maritime Single Window (VNSW), Border Control, Quarantine & MARPOL (Phases 191-194).

Typer Apps:
- mekong vnsw / motcua (VNSW & e-Port Clearance)
- mekong seafarer / thuyenvien (STCW Safe Manning & Shore Pass)
- mekong quarantine / kiemdich (Health Quarantine & Free Pratique)
- mekong marpol / moitruongbien (MARPOL 73/78 & Port Reception Facilities)
"""

import dataclasses
import enum
import json
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.maritime_vnsw_quarantine_marpol_engine import (
    VNSWNotificationType,
    VesselVoyageType,
    ClearanceStatus,
    SeafarerRank,
    SeafarerCrewMember,
    MaritimeSingleWindowEngine,
    SeafarerImmigrationEngine,
    MaritimeHealthQuarantineEngine,
    MARPOLPortReceptionEngine,
)

console = Console()

vnsw_app = typer.Typer(
    name="vnsw",
    help="Phase 191: Vietnam National Maritime Single Window (VNSW) & e-Port Clearance.",
    no_args_is_help=True,
)

seafarer_app = typer.Typer(
    name="seafarer",
    help="Phase 192: Seafarer Safe Manning, STCW Rest Hours & Border Immigration Shore Pass.",
    no_args_is_help=True,
)

quarantine_app = typer.Typer(
    name="quarantine",
    help="Phase 193: Maritime International Health Quarantine, SSCEC & Free Pratique.",
    no_args_is_help=True,
)

marpol_app = typer.Typer(
    name="marpol",
    help="Phase 194: Marine Environmental Protection, MARPOL 73/78 & PRF Waste Reception.",
    no_args_is_help=True,
)


def _json_serial(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    return str(obj)


def _dump_json(obj):
    if dataclasses.is_dataclass(obj):
        data = dataclasses.asdict(obj)
    elif hasattr(obj, "__dict__"):
        data = obj.__dict__
    else:
        data = obj
    print(json.dumps(data, indent=2, default=_json_serial))


# ---------------------------------------------------------------------------
# Phase 191: VNSW & Port Clearance Commands
# ---------------------------------------------------------------------------


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

    res = MaritimeSingleWindowEngine.evaluate_port_clearance(
        imo_number=imo,
        vessel_name=name,
        call_sign=call_sign,
        voyage_type=v_type,
        gross_tonnage=gt,
        notification_type=n_type,
        hours_before_event=hours_before,
        submitted_forms=submitted,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"VNSW Port Clearance Assessment — {res.vessel_name} (IMO {res.imo_number})")
    table.add_column("Parameter", style="cyan")
    table.add_column("Details", style="green")

    table.add_row("Voyage & Tonnage", f"{res.voyage_type.value} ({res.gross_tonnage:,.0f} GT)")
    table.add_row("Notification Timeliness", "[green]TIMELY[/green]" if res.is_notification_timely else "[red]DELAYED/BREACH[/red]")
    table.add_row("Dossier Completeness", "[green]COMPLETE[/green]" if res.is_dossier_complete else f"[red]MISSING: {', '.join(res.missing_declarations)}[/red]")
    table.add_row("Clearance Status", f"[bold yellow]{res.status.value}[/bold yellow]")
    table.add_row("Clearance Permit No", res.clearance_permit_no)
    table.add_row("Tonnage Dues", f"{res.tonnage_dues_vnd:,.0f} VND")
    table.add_row("Maritime Safety Fee", f"{res.maritime_safety_fee_vnd:,.0f} VND")
    table.add_row("Port Clearance Fee", f"{res.port_clearance_fee_vnd:,.0f} VND")
    table.add_row("Total Statutory Dues", f"[bold green]{res.total_statutory_dues_vnd:,.0f} VND[/bold green]")
    table.add_row("QR Verification URL", res.qr_verification_payload)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 192: Seafarer Manning & Shore Pass Commands
# ---------------------------------------------------------------------------


@seafarer_app.command("audit")
def seafarer_audit(
    vessel_name: str = typer.Argument("MV PACIFIC OCEAN", help="Vessel Name"),
    assessment_date: Optional[str] = typer.Option(None, "--assess-date", help="Assessment date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """Audit seafarer safe manning levels, STCW rest hours, and issue Shore Passes."""
    # Standard crew composition sample for evaluation
    sample_crew = [
        SeafarerCrewMember("Nguyen Van A", "VNM", "B1234567", "VN-0988", SeafarerRank.MASTER, "2028-12-31", "2028-12-31", 11.0, 84.0),
        SeafarerCrewMember("Tran Van B", "VNM", "B2345678", "VN-0989", SeafarerRank.CHIEF_MATE, "2028-12-31", "2028-12-31", 10.5, 80.0),
        SeafarerCrewMember("Le Van C", "VNM", "B3456789", "VN-0990", SeafarerRank.CHIEF_ENGINEER, "2028-12-31", "2028-12-31", 12.0, 88.0),
        SeafarerCrewMember("Pham Van D", "VNM", "B4567890", "VN-0991", SeafarerRank.SECOND_ENGINEER, "2028-12-31", "2028-12-31", 10.0, 78.0),
        SeafarerCrewMember("Do Van E", "VNM", "B5678901", "VN-0992", SeafarerRank.RATING_ABLE_SEAMAN, "2028-12-31", "2028-12-31", 10.0, 77.0),
    ]

    res = SeafarerImmigrationEngine.audit_crew_and_immigration(
        vessel_name=vessel_name,
        crew_list=sample_crew,
        assessment_date_iso=assessment_date,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"Seafarer Manning & Border Immigration Audit — {res.vessel_name}")
    table.add_column("Criterion", style="cyan")
    table.add_column("Evaluation", style="green")

    table.add_row("Total Crew Complement", f"{res.total_crew_count} Seafarers")
    table.add_row("Safe Manning (MSMD)", "[green]COMPLIANT[/green]" if res.is_safe_manning_compliant else "[red]NON-COMPLIANT[/red]")
    table.add_row("STCW Rest Compliance", "[green]COMPLIANT[/green]" if res.is_stcw_rest_compliant else "[red]BREACH DETECTED[/red]")
    table.add_row("Shore Passes Granted", f"[bold green]{res.shore_pass_granted_count}[/bold green]")
    table.add_row("Shore Passes Denied", f"[bold red]{res.shore_pass_denied_count}[/bold red]")
    table.add_row("Immigration Status", res.immigration_status.value)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 193: Maritime Health Quarantine Commands
# ---------------------------------------------------------------------------


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
    res = MaritimeHealthQuarantineEngine.evaluate_health_quarantine(
        vessel_name=vessel_name,
        sscec_valid_until_iso=sscec_expiry,
        communicable_cases_detected=infected_cases,
        has_visited_endemic_yellow_fever_port=yellow_fever_port,
        assessment_date_iso=assess_date,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"Maritime International Health Quarantine — {res.vessel_name}")
    table.add_column("Parameter", style="cyan")
    table.add_column("Result", style="green")

    table.add_row("SSCEC Certificate Expiry", f"{res.sscec_valid_until_iso} ({'VALID' if res.is_sscec_valid else 'EXPIRED'})")
    table.add_row("Communicable Cases", f"{res.communicable_cases_detected} Cases")
    table.add_row("Epidemiological Risk Score", f"{res.epidemiological_risk_score:.2f}")
    table.add_row("Quarantine Status", f"[bold yellow]{res.quarantine_status.value}[/bold yellow]")
    table.add_row("Yellow Flag 'Q' Required", "[bold red]YES (HOISTED)[/bold red]" if res.yellow_flag_required else "[bold green]NO[/bold green]")
    if res.free_pratique_certificate_no:
        table.add_row("Free Pratique Cert No", res.free_pratique_certificate_no)

    console.print(table)


# ---------------------------------------------------------------------------
# Phase 194: MARPOL & Port Reception Facilities Commands
# ---------------------------------------------------------------------------


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
    res = MARPOLPortReceptionEngine.evaluate_environmental_compliance(
        vessel_name=vessel_name,
        ows_bilge_oil_content_ppm=ows_ppm,
        fuel_sulfur_content_pct=fuel_sulfur,
        sludge_delivered_m3=sludge_m3,
        garbage_delivered_m3=garbage_m3,
    )

    if json_output:
        _dump_json(res)
        return

    table = Table(title=f"MARPOL 73/78 & Port Reception Environmental Audit — {res.vessel_name}")
    table.add_column("Inspection Item", style="cyan")
    table.add_column("Compliance Status", style="green")

    table.add_row("OWS Bilge Oil Content", f"{res.ows_bilge_oil_content_ppm:.1f} ppm ({'PASS (<=15 ppm)' if res.is_ows_compliant else 'FAIL (>15 ppm)'})")
    table.add_row("Fuel Sulfur Content", f"{res.fuel_sulfur_content_pct:.2f}% ({'PASS (<=0.50%)' if res.is_fuel_sulfur_compliant else 'FAIL (>0.50%)'})")
    table.add_row("Overall MARPOL Compliance", "[bold green]COMPLIANT[/bold green]" if res.is_marpol_fully_compliant else "[bold red]BREACH DETECTED[/bold red]")
    if res.prf_waste_delivery_receipt_no:
        table.add_row("PRF Waste Delivery Receipt", res.prf_waste_delivery_receipt_no)
        table.add_row("Disposed Volumes", f"{res.sludge_delivered_m3} m3 Sludge, {res.garbage_delivered_m3} m3 Garbage")
        table.add_row("Environmental PRF Tariff", f"{res.environmental_levy_vnd:,.0f} VND")

    console.print(table)
