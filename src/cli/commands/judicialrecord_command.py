"""
CLI Command Suite for Vietnamese Judicial Records, Criminal Clearance & VNeID Electronic Certificates.
Compliant with:
- Law on Judicial Records 2009 (Luật Lý lịch tư pháp - Law No. 28/2009/QH12)
- Decree No. 111/2010/ND-CP detailing implementation of Law on Judicial Records
- Circular No. 06/2013/TT-BTP & Circular No. 04/2024/TT-BTP on judicial record forms & VNeID
- Penal Code 2015/2017 (Articles 69, 70, 71, 72, 73 on Criminal Record Remission)
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.judicialrecord_engine import (
    JudicialRecordEngine,
    CertificateFormType,
    ClearanceStatus,
    RequestStatus,
    CrimeSeverity,
)

judicialrecord_app = typer.Typer(
    name="judicialrecord",
    help="Vietnamese Judicial Records & Criminal Clearance Suite (Luật Lý lịch tư pháp 2009 & BLHS 2015)",
    invoke_without_command=True,
)
app = judicialrecord_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG QUẢN LÝ LÝ LỊCH TƯ PHÁP QUỐC GIA[/bold cyan]\n"
            "[dim]National Center for Judicial Records — Ministry of Justice (Luật Lý lịch tư pháp 2009 & VNeID Integration)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Judicial Records & Criminal Clearance Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category / Domain", style="bold green")
    table.add_column("Authority / Authority Channel", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Certificate Requests",
        "National Civil Portal & VNeID",
        "Total Requests",
        str(status_data.get("total_certificate_requests", 0)),
    )
    table.add_row(
        "Form No. 1 (Phiếu số 1)",
        "Citizens & Organizations (Điều 41)",
        "Form 1 Requests",
        str(status_data.get("form_1_requests", 0)),
    )
    table.add_row(
        "Form No. 2 (Phiếu số 2)",
        "Procedural Agencies & Individuals (Điều 42)",
        "Form 2 Requests",
        str(status_data.get("form_2_requests", 0)),
    )
    table.add_row(
        "Electronic VNeID",
        "VNeID Level 2 Authentication",
        "VNeID Verified Requests",
        str(status_data.get("vneid_verified_requests", 0)),
    )
    table.add_row(
        "Criminal Convictions",
        "People's Courts Transcripts",
        "Convictions Recorded",
        str(status_data.get("criminal_convictions_recorded", 0)),
    )
    table.add_row(
        "Clearance Evaluations",
        "Articles 70-73 Penal Code 2015",
        "Evaluations Performed",
        str(status_data.get("clearance_evaluations_performed", 0)),
    )
    table.add_row(
        "Remitted Records",
        "Statutory Automated Clearance (Điều 70)",
        "Cleared Records",
        str(status_data.get("cleared_criminal_records", 0)),
    )
    table.add_row(
        "Prohibition Orders",
        "Corporate & Office Bans",
        "Active Prohibitions",
        str(status_data.get("active_prohibition_orders", 0)),
    )
    table.add_row(
        "Issued Certificates",
        "Official Cryptographic LLTP",
        "Issued Certificates",
        str(status_data.get("issued_certificates_total", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@judicialrecord_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Judicial Records & Criminal History Clearance Central Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = JudicialRecordEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@judicialrecord_app.command("request")
def request_cmd(
    form_type: str = typer.Option("FORM_1", "--form", "-f", help="Form type: FORM_1 (Phiếu số 1) | FORM_2 (Phiếu số 2)"),
    name: str = typer.Option(..., "--name", "-n", help="Full legal name of the requester"),
    citizen_id: str = typer.Option(..., "--id", "-i", help="Citizen ID / CCCD / Passport number"),
    dob: str = typer.Option(..., "--dob", help="Date of birth (YYYY-MM-DD)"),
    gender: str = typer.Option("MALE", "--gender", "-g", help="Gender: MALE | FEMALE"),
    permanent: str = typer.Option(..., "--permanent", "-p", help="Permanent residential address"),
    current: str = typer.Option(..., "--current", "-c", help="Current residential address"),
    purpose: str = typer.Option("Tư pháp và xin việc làm", "--purpose", help="Request purpose"),
    nationality: str = typer.Option("Việt Nam", "--nat", help="Requester nationality"),
    authority: Optional[str] = typer.Option(None, "--authority", help="Competent Department of Justice or National Center"),
    vneid: bool = typer.Option(True, "--vneid/--no-vneid", help="Verified via VNeID Level 2"),
    prohibition: bool = typer.Option(False, "--prohibition/--no-prohibition", help="Request certification of corporate/post ban (Form 1)"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Submit application for Judicial Record Certificate (Phiếu lý lịch tư pháp số 1 hoặc số 2)."""
    try:
        engine = JudicialRecordEngine()
        result = engine.request_certificate(
            form_type=form_type,
            citizen_name=name,
            citizen_id=citizen_id,
            dob=dob,
            gender=gender,
            permanent_address=permanent,
            current_address=current,
            request_purpose=purpose,
            nationality=nationality,
            competent_authority=authority,
            vneid_verified=vneid,
            include_prohibition=prohibition,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        form_desc = "Phiếu Lý lịch tư pháp số 1" if result["form_type"] == "FORM_1" else "Phiếu Lý lịch tư pháp số 2"
        console.print(f"[bold green]✓ Judicial Record Request Submitted:[/bold green] [cyan]{result['request_id']}[/cyan]")
        console.print(f"  [bold]Form Type:[/bold] {result['form_type']} ({form_desc})")
        console.print(f"  [bold]Citizen:[/bold] {result['citizen_name']} (ID: {result['citizen_id']}, DOB: {result['dob']})")
        console.print(f"  [bold]Permanent Address:[/bold] {result['permanent_address']}")
        console.print(f"  [bold]VNeID Verified:[/bold] {'Yes (Cấp độ 2)' if result['vneid_verified'] else 'No'}")
        console.print(f"  [bold]Competent Authority:[/bold] {result['competent_authority']}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error submitting request:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialrecord_app.command("conviction")
def conviction_cmd(
    citizen_id: str = typer.Option(..., "--id", "-i", help="Citizen ID / CCCD number"),
    judgment: str = typer.Option(..., "--judgment", "-j", help="Court judgment number"),
    court: str = typer.Option(..., "--court", "-c", help="Name of deciding People's Court"),
    date: str = typer.Option(..., "--date", help="Judgment date (YYYY-MM-DD)"),
    offense: str = typer.Option(..., "--offense", "-o", help="Offense legal name under Penal Code"),
    severity: str = typer.Option("LESS_SERIOUS", "--severity", "-s", help="LESS_SERIOUS | SERIOUS | VERY_SERIOUS | PARTICULARLY_SERIOUS"),
    primary_penalty: str = typer.Option(..., "--primary-penalty", help="Primary penalty (e.g., 2 năm tù, Cải tạo không giam giữ)"),
    penalty_completed_date: str = typer.Option(..., "--penalty-completed-date", help="Date main penalty / probation was completed (YYYY-MM-DD)"),
    additional_penalty: Optional[str] = typer.Option(None, "--additional-penalty", help="Additional penalties"),
    civil_completed: bool = typer.Option(True, "--civil/--no-civil", help="Civil damage compensation completed"),
    fees_completed: bool = typer.Option(True, "--fees/--no-fees", help="Court fees and execution costs completed"),
    notes: str = typer.Option("", "--notes", help="Conviction record notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Record criminal conviction into National Judicial Database."""
    try:
        engine = JudicialRecordEngine()
        result = engine.record_conviction(
            citizen_id=citizen_id,
            court_judgment_number=judgment,
            deciding_court=court,
            judgment_date=date,
            offense_name=offense,
            severity=severity,
            primary_penalty=primary_penalty,
            penalty_completed_date=penalty_completed_date,
            additional_penalty=additional_penalty,
            civil_obligation_completed=civil_completed,
            court_fee_completed=fees_completed,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Criminal Conviction Recorded:[/bold green] [cyan]{result['conviction_id']}[/cyan]")
        console.print(f"  [bold]Citizen ID:[/bold] {result['citizen_id']}")
        console.print(f"  [bold]Judgment:[/bold] {result['court_judgment_number']} ({result['deciding_court']})")
        console.print(f"  [bold]Offense:[/bold] {result['offense_name']} (Severity: {result['severity']})")
        console.print(f"  [bold]Penalty:[/bold] {result['primary_penalty']} (Completed: {result['penalty_completed_date']})")
        console.print(f"  [bold]Civil & Fees Obligation:[/bold] {'Completed' if result['civil_obligation_completed'] and result['court_fee_completed'] else 'Pending'}")
    except Exception as e:
        console.print(f"[bold red]Error recording conviction:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialrecord_app.command("clearance")
def clearance_cmd(
    conviction_id: str = typer.Option(..., "--conviction-id", "-c", help="Conviction ID to evaluate"),
    ref_date: Optional[str] = typer.Option(None, "--ref-date", help="Evaluation reference date (YYYY-MM-DD)"),
    recidivism: bool = typer.Option(False, "--recidivism/--no-recidivism", help="Committed new crime during testing period"),
    court_decision: Optional[str] = typer.Option(None, "--court-decision", help="Court decision reference under Articles 71-72"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Evaluate criminal record remission (Xóa án tích) under Articles 70-73 Penal Code 2015."""
    try:
        engine = JudicialRecordEngine()
        result = engine.evaluate_clearance(
            conviction_id=conviction_id,
            reference_date=ref_date,
            recidivism_committed=recidivism,
            court_decision_ref=court_decision,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        status_color = "green" if result["clearance_status"] == "CLEARED" else "red"
        console.print(f"[bold green]✓ Criminal Clearance Evaluated:[/bold green] [cyan]{result['evaluation_id']}[/cyan]")
        console.print(f"  [bold]Conviction ID:[/bold] {result['conviction_id']}")
        console.print(f"  [bold]Clearance Status:[/bold] [{status_color}]{result['clearance_status']}[/{status_color}]")
        console.print(f"  [bold]Required Years:[/bold] {result['statutory_years_required']} years | [bold]Elapsed:[/bold] {result['years_elapsed']} years")
        console.print(f"  [bold]Legal Basis:[/bold] {result['legal_basis']}")
    except Exception as e:
        console.print(f"[bold red]Error evaluating clearance:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialrecord_app.command("prohibition")
def prohibition_cmd(
    citizen_id: str = typer.Option(..., "--id", "-i", help="Citizen ID / CCCD number"),
    prohibition_type: str = typer.Option("Cấm đảm nhiệm chức vụ quản lý doanh nghiệp", "--type", "-t", help="Prohibition type"),
    court: str = typer.Option(..., "--court", "-c", help="Court that issued prohibition order"),
    judgment: str = typer.Option(..., "--judgment", "-j", help="Judgment number"),
    start_date: str = typer.Option(..., "--start-date", help="Effective start date (YYYY-MM-DD)"),
    details: str = typer.Option(..., "--details", "-d", help="Specific prohibition provisions"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="Effective end date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE | EXPIRED | LIFTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Record prohibition from holding positions or managing enterprises."""
    try:
        engine = JudicialRecordEngine()
        result = engine.record_prohibition(
            citizen_id=citizen_id,
            prohibition_type=prohibition_type,
            issuing_court=court,
            judgment_number=judgment,
            start_date=start_date,
            details=details,
            end_date=end_date,
            status=status,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Prohibition Order Recorded:[/bold green] [cyan]{result['prohibition_id']}[/cyan]")
        console.print(f"  [bold]Citizen ID:[/bold] {result['citizen_id']}")
        console.print(f"  [bold]Type:[/bold] {result['prohibition_type']}")
        console.print(f"  [bold]Judgment:[/bold] {result['judgment_number']} ({result['issuing_court']})")
        console.print(f"  [bold]Period:[/bold] {result['start_date']} to {result.get('end_date') or 'Indefinite'}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error recording prohibition:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialrecord_app.command("issue")
def issue_cmd(
    request_id: str = typer.Option(..., "--request-id", "-r", help="Judicial record request ID"),
    number: Optional[str] = typer.Option(None, "--number", help="Custom certificate serial number"),
    date: Optional[str] = typer.Option(None, "--date", help="Issuance date (YYYY-MM-DD)"),
    sig: Optional[str] = typer.Option(None, "--sig", help="Custom digital signature string"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Synthesize criminal history and issue official electronic Judicial Record Certificate."""
    try:
        engine = JudicialRecordEngine()
        result = engine.issue_certificate(
            request_id=request_id,
            certificate_number=number,
            issue_date=date,
            custom_digital_signature=sig,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        form_desc = "Phiếu số 1" if result["form_type"] == "FORM_1" else "Phiếu số 2"
        console.print(f"[bold green]✓ Official Judicial Record Certificate Issued:[/bold green] [cyan]{result['certificate_id']}[/cyan]")
        console.print(f"  [bold]Certificate Serial:[/bold] [bold yellow]{result['certificate_number']}[/bold yellow] ({form_desc})")
        console.print(f"  [bold]Citizen:[/bold] {result['citizen_name']} (ID: {result['citizen_id']})")
        console.print(f"  [bold]Criminal Record Entry:[/bold] [green]{result['criminal_record_entry']}[/green]")
        console.print(f"  [bold]Prohibition Entry:[/bold] {result['prohibition_entry']}")
        console.print(f"  [bold]Digital Token:[/bold] [dim]{result['digital_signature']}[/dim]")
        console.print(f"  [bold]QR Verification:[/bold] [cyan]{result['qr_verification_token']}[/cyan]")
        console.print(f"  [bold]Authority:[/bold] {result['issuing_authority']} ({result['issue_date']})")
    except Exception as e:
        console.print(f"[bold red]Error issuing certificate:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialrecord_app.command("list")
def list_records_cmd(
    category: str = typer.Option("request", "--category", "-c", help="Category: request | conviction | evaluation | prohibition | certificate | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Pagination offset"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List judicial record entries by category."""
    try:
        engine = JudicialRecordEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Judicial Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialrecord_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show national judicial record and criminal clearance statistics."""
    engine = JudicialRecordEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
