"""
CLI Command Suite for Vietnamese People's Courts, Judicial Adjudication & Electronic Court.
Compliant with:
- Law on Organization of People's Courts 2024 (Law No. 34/2024/QH15)
- Civil Procedure Code 2015, Criminal Procedure Code 2015, Administrative Procedure Code 2015
- Resolution No. 33/2021/QH15 on Online Court Hearings
"""

import typer
import json
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.court_engine import CourtEngine

court_app = typer.Typer(
    name="court",
    help="Vietnamese People's Courts, Judicial Adjudication & Electronic Court Suite (Law No. 34/2024/QH15)",
    invoke_without_command=True,
)
app = court_app
console = Console()



@court_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese People's Courts Executive Dashboard & Adjudication Overview."""
    if ctx.invoked_subcommand is None:
        engine = CourtEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        console.print(
            Panel.fit(
                "[bold cyan]TÒA ÁN NHÂN DÂN — PEOPLE'S COURTS OF VIETNAM[/bold cyan]\n"
                "[dim]Judicial Adjudication & Electronic Court Hub (Law No. 34/2024/QH15)[/dim]",
                box=box.DOUBLE,
                border_style="cyan",
            )
        )

        telemetry = status_data.get("telemetry", {})
        table = Table(title="Court Operations Telemetry", box=box.ROUNDED, show_header=True)
        table.add_column("Domain", style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold yellow")

        officers = telemetry.get("officers", {})
        table.add_row("Judicial Officers", "Total Officers", str(officers.get("total", 0)))
        table.add_row("Judicial Officers", "Active Officers", str(officers.get("active", 0)))

        cases = telemetry.get("cases", {})
        table.add_row("Cases & Dockets", "Total Cases", str(cases.get("total", 0)))
        table.add_row("Cases & Dockets", "Electronic Dossiers", str(cases.get("e_dossiers", 0)))
        table.add_row("Cases & Dockets", "Docketed (Thụ lý)", str(cases.get("docketed_thuly", 0)))
        table.add_row("Cases & Dockets", "In Trial (Sơ/Phúc thẩm)", str(cases.get("in_trial", 0)))
        table.add_row("Cases & Dockets", "Adjudicated / Enforcing", str(cases.get("adjudicated", 0)))
        claim_val = cases.get("total_claim_value_vnd", 0.0)
        table.add_row("Cases & Dockets", "Total Claim Value", f"{claim_val:,.0f} VND")

        hearings = telemetry.get("hearings", {})
        table.add_row("Court Hearings", "Total Hearings", str(hearings.get("total", 0)))
        table.add_row("Court Hearings", "Virtual / Hybrid (Res 33)", str(hearings.get("virtual_or_hybrid", 0)))
        table.add_row("Court Hearings", "Completed", str(hearings.get("completed", 0)))

        judgments = telemetry.get("judgments", {})
        table.add_row("Judgments & Rulings", "Total Issued", str(judgments.get("total", 0)))
        fees = judgments.get("total_court_fees_vnd", 0.0)
        table.add_row("Judgments & Rulings", "Court Fees Collected", f"{fees:,.0f} VND")
        table.add_row("Judgments & Rulings", "Public Portal Disclosed", str(judgments.get("disclosed_on_public_portal", 0)))

        filings = telemetry.get("electronic_filings", {})
        table.add_row("Electronic Filings", "Total Submissions", str(filings.get("total", 0)))
        table.add_row("Electronic Filings", "Verified / Processed", str(filings.get("processed", 0)))

        console.print(table)


@court_app.command("officer")
def register_officer_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Officer code (e.g. TP-2025-001)"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of judge or judicial officer"),
    role: str = typer.Option(..., "--role", "-r", help="Role: THAM_PHAN_TOI_CAO, THAM_PHAN_CHINH, THAM_PHAN, HOI_THAM_NHAN_DAN, HOI_THAM_QUAN_SU, THU_KY_TOA_AN, THAM_TRA_VIEN"),
    level: str = typer.Option(..., "--level", "-l", help="Court level: TAND_TOI_CAO, TAND_CAP_CAO, TAND_CAP_TINH, TAND_CAP_HUYEN, TOA_AN_QUAN_SU, TOA_SO_THAM_CHUYEN_BIET"),
    court: str = typer.Option(..., "--court", help="Court name (e.g. Tòa án nhân dân TP. Hồ Chí Minh)"),
    decision: str = typer.Option(..., "--decision", "-d", help="Appointment decision reference"),
    date: Optional[str] = typer.Option(None, "--date", help="Appointed date (YYYY-MM-DD)"),
    term: int = typer.Option(5, "--term", help="Term in years"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, SUSPENDED, RETIRED, TRANSFERRED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update a Judge, People's Assessor, Clerk, or Examiner under Law 34/2024/QH15."""
    engine = CourtEngine()
    result = engine.register_officer(
        code=code,
        full_name=name,
        role=role,
        court_level=level,
        court_name=court,
        appointment_decision=decision,
        appointed_date=date,
        term_years=term,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Judicial Officer registered successfully:[/bold green] {code} - {name} ({role})")
    else:
        console.print(f"[bold red]✗ Failed to register judicial officer:[/bold red] {result.get('error')}")


@court_app.command("case")
def file_case_cmd(
    number: str = typer.Option(..., "--number", "-n", help="Case docket number (e.g. 01/2025/TLST-KDTM)"),
    title: str = typer.Option(..., "--title", "-t", help="Case dispute title or criminal charge"),
    type: str = typer.Option(..., "--type", help="HINH_SU, DAN_SU, KINH_DOANH_THUONG_MAI, LAO_DONG, HANH_CHINH, HON_NHAN_GIA_DINH, PHA_SAN, SO_HUU_TRI_TUE"),
    level: str = typer.Option(..., "--level", "-l", help="Court level: TAND_TOI_CAO, TAND_CAP_CAO, TAND_CAP_TINH, TAND_CAP_HUYEN, TOA_AN_QUAN_SU, TOA_SO_THAM_CHUYEN_BIET"),
    court: str = typer.Option(..., "--court", help="Court name"),
    plaintiff: str = typer.Option(..., "--plaintiff", "-p", help="Plaintiff or Public Prosecutor (Nguyên đơn / Viện kiểm sát)"),
    defendant: str = typer.Option(..., "--defendant", "-d", help="Defendant or Accused (Bị đơn / Bị cáo)"),
    filing_date: Optional[str] = typer.Option(None, "--filing-date", help="Filing date (YYYY-MM-DD)"),
    acceptance_date: Optional[str] = typer.Option(None, "--acceptance-date", help="Acceptance docket date (YYYY-MM-DD)"),
    judge: Optional[str] = typer.Option(None, "--judge", help="Presiding judge code or ID"),
    stage: str = typer.Option("THU_LY", "--stage", help="Stage: THU_LY, HOA_GIAI_DOI_THOAI, CHUAN_BI_XET_XU, XET_XU_SO_THAM, XET_XU_PHUC_THAM, GIAM_DOC_THAM_TAI_THAM, THI_HANH_AN, DINH_CHI"),
    claim: float = typer.Option(0.0, "--claim", help="Disputed claim value in VND"),
    e_dossier: bool = typer.Option(True, "--e-dossier/--paper-dossier", help="Electronic dossier enabled"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """File and docket a legal case under relevant procedure codes."""
    engine = CourtEngine()
    result = engine.file_case(
        case_number=number,
        case_title=title,
        case_type=type,
        court_level=level,
        court_name=court,
        plaintiff_prosecutor=plaintiff,
        defendant_accused=defendant,
        filing_date=filing_date,
        acceptance_date=acceptance_date,
        presiding_judge_id=judge,
        stage=stage,
        claim_value=claim,
        is_electronic_dossier=e_dossier,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Case docketed successfully:[/bold green] {number} - {title} ({type})")
    else:
        console.print(f"[bold red]✗ Failed to docket case:[/bold red] {result.get('error')}")


@court_app.command("hearing")
def schedule_hearing_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Hearing code (e.g. PT-2025-001)"),
    case: str = typer.Option(..., "--case", help="Case number or ID"),
    date: str = typer.Option(..., "--date", "-d", help="Hearing datetime (ISO format)"),
    type: str = typer.Option("SO_THAM", "--type", help="SO_THAM, PHUC_THAM, GIAM_DOC_THAM, TAI_THAM, HOA_GIAI"),
    format: str = typer.Option("DIRECT", "--format", help="DIRECT, ONLINE_VIRTUAL, HYBRID"),
    members: Optional[List[str]] = typer.Option(None, "--member", "-m", help="Trial panel members (multiple allowed)"),
    courtroom: str = typer.Option("Phòng xử án số 1", "--courtroom", help="Courtroom identifier or virtual room link"),
    status: str = typer.Option("SCHEDULED", "--status", help="SCHEDULED, IN_SESSION, ADJOURNED, COMPLETED, CANCELLED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Hearing session notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Schedule a trial hearing or online court session under Resolution 33/2021/QH15."""
    engine = CourtEngine()
    result = engine.schedule_hearing(
        hearing_code=code,
        case_id=case,
        hearing_date=date,
        hearing_type=type,
        format=format,
        panel_members=members,
        courtroom=courtroom,
        status=status,
        notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Court hearing scheduled:[/bold green] {code} on {date} (Format: {format})")
    else:
        console.print(f"[bold red]✗ Failed to schedule hearing:[/bold red] {result.get('error')}")


@court_app.command("judgment")
def issue_judgment_cmd(
    number: str = typer.Option(..., "--number", "-n", help="Judgment number (e.g. 05/2025/DS-ST)"),
    case: str = typer.Option(..., "--case", help="Case number or ID"),
    type: str = typer.Option(..., "--type", help="BAN_AN_SO_THAM, BAN_AN_PHUC_THAM, QUYET_DINH_GIAM_DOC_THAM, QUYET_DINH_TAI_THAM, QUYET_DINH_CONG_NHAN_HOA_GIAI, QUYET_DINH_DINH_CHI"),
    verdict: str = typer.Option(..., "--verdict", "-v", help="Summary of adjudication verdict"),
    remedy: str = typer.Option(..., "--remedy", "-r", help="Imposed penalty, damage compensation, or procedural order"),
    issue_date: Optional[str] = typer.Option(None, "--issue-date", help="Judgment issue date (YYYY-MM-DD)"),
    effective_date: Optional[str] = typer.Option(None, "--effective-date", help="Effective date"),
    fee: float = typer.Option(0.0, "--fee", help="Court fee assessed in VND"),
    appeal_days: int = typer.Option(15, "--appeal-days", help="Statutory appeal window in days (default: 15)"),
    public: bool = typer.Option(True, "--public/--confidential", help="Disclose on Supreme Court public judgment portal"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue formal court judgment or ruling and track appeal window and public portal disclosure."""
    engine = CourtEngine()
    result = engine.issue_judgment(
        judgment_number=number,
        case_id=case,
        judgment_type=type,
        verdict_summary=verdict,
        penalty_or_remedy=remedy,
        issue_date=issue_date,
        effective_date=effective_date,
        court_fee=fee,
        appeal_deadline_days=appeal_days,
        is_public_portal_disclosed=public,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Judgment issued successfully:[/bold green] {number} ({type})")
    else:
        console.print(f"[bold red]✗ Failed to issue judgment:[/bold red] {result.get('error')}")


@court_app.command("filing")
def submit_filing_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Filing code (e.g. EC-2025-0001)"),
    name: str = typer.Option(..., "--name", "-n", help="Submitter full name / company representative"),
    id_card: str = typer.Option(..., "--id-card", help="Submitter 12-digit CCCD/VNeID or Tax Code"),
    title: str = typer.Option(..., "--title", "-t", help="Document title (e.g. Đơn khởi kiện tranh chấp)"),
    type: str = typer.Option(..., "--type", help="DON_KHOI_KIEN, DON_YEU_CAU, DON_KHANG_CAO, DON_KHIEU_NAI, CHUNG_CU_TAI_LIEU, BAN_TU_KHAI, Y_KIEN_PHAP_LY"),
    case: Optional[str] = typer.Option(None, "--case", help="Case number or ID if already docketed"),
    date: Optional[str] = typer.Option(None, "--date", help="Submission timestamp"),
    payload: Optional[str] = typer.Option(None, "--payload", help="Electronic text content or document summary"),
    status: str = typer.Option("SUBMITTED", "--status", help="SUBMITTED, VERIFIED_VALID, REJECTED, PROCESSED_INTO_CASE"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Submit electronic filing, online claim, or e-evidence under Chapter IX Law 34/2024/QH15."""
    engine = CourtEngine()
    result = engine.submit_electronic_filing(
        filing_code=code,
        submitter_name=name,
        submitter_id_card=id_card,
        document_title=title,
        document_type=type,
        case_id=case,
        submission_date=date,
        content_payload=payload,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        verif = result.get("electronic_filing", {}).get("verification_hash", "")[:12]
        console.print(f"[bold green]✓ Electronic filing submitted:[/bold green] {code} - {title} (Hash: {verif}...)")
    else:
        console.print(f"[bold red]✗ Failed to submit filing:[/bold red] {result.get('error')}")


@court_app.command("list")
def list_records_cmd(
    category: str = typer.Argument(..., help="officers, cases, hearings, judgments, filings"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to return"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List records by category (officers, cases, hearings, judgments, filings)."""
    engine = CourtEngine()
    result = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        return

    records = result.get("records", [])
    table = Table(title=f"Court Records: {category.upper()} (Count: {len(records)})", box=box.ROUNDED)

    if not records:
        console.print(f"[dim]No records found for category '{category}'[/dim]")
        return

    keys = list(records[0].keys())[:6]
    for k in keys:
        table.add_column(k.replace("_", " ").title(), style="cyan")

    for r in records:
        row_vals = [str(r.get(k, "")) for k in keys]
        table.add_row(*row_vals)

    console.print(table)


@court_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display court operations and digital transformation telemetry."""
    engine = CourtEngine()
    result = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            "[bold cyan]TÒA ÁN NHÂN DÂN — OPERATIONS STATUS[/bold cyan]\n"
            f"[dim]Statutory: {result.get('statutory_framework')}[/dim]",
            box=box.ROUNDED,
        )
    )
    typer.echo(json.dumps(result.get("telemetry", {}), ensure_ascii=False, indent=2))
