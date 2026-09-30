"""
CLI Command Suite for Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access.
Compliant with:
- Law on Legal Aid 2017 (Luật Trợ giúp pháp lý - Law No. 11/2017/QH14)
- Decree No. 144/2017/NĐ-CP detailing implementation of the Law on Legal Aid
- Circular No. 08/2017/TT-BTP on Quality Standards & Assessment of Legal Aid Cases
- Criminal Procedure Code 2015 & Civil Procedure Code 2015
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.legalaid_engine import LegalAidEngine

legalaid_app = typer.Typer(
    name="legalaid",
    help="Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access Suite (Luật Trợ giúp pháp lý 2017)",
    invoke_without_command=True,
)
app = legalaid_app
console = Console()


@legalaid_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese State Legal Aid Center Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = LegalAidEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        console.print(
            Panel.fit(
                "[bold cyan]CỤC TRỢ GIÚP PHÁP LÝ — BỘ TƯ PHÁP VIỆT NAM[/bold cyan]\n"
                "[dim]National Legal Aid System, Vulnerable Protection & Justice Access Hub (Luật TGPL 2017)[/dim]",
                box=box.DOUBLE,
                border_style="cyan",
            )
        )

        telemetry = status_data.get("telemetry", {})
        table = Table(title="State Legal Aid Telemetry", box=box.ROUNDED, show_header=True)
        table.add_column("Category", style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold yellow")

        ben = telemetry.get("beneficiaries", {})
        table.add_row("Beneficiaries", "Total Registered", str(ben.get("total", 0)))
        table.add_row("Beneficiaries", "Verified Eligible", str(ben.get("verified", 0)))

        off = telemetry.get("legal_aid_officers", {})
        table.add_row("Legal Aid Officers", "Total Appointed / Contracted", str(off.get("total", 0)))
        table.add_row("Legal Aid Officers", "Active Practicing", str(off.get("active", 0)))

        req = telemetry.get("requests_and_dockets", {})
        table.add_row("Requests & Dockets", "Total Cases Filed", str(req.get("total", 0)))
        table.add_row("Requests & Dockets", "Litigation Defense", str(req.get("litigation_defense", 0)))
        table.add_row("Requests & Dockets", "Legal Counseling", str(req.get("legal_counseling", 0)))
        table.add_row("Requests & Dockets", "Completed Dockets", str(req.get("completed", 0)))

        proc = telemetry.get("court_proceedings", {})
        table.add_row("Court Proceedings", "Total Assigned Decisions", str(proc.get("total_assigned", 0)))
        table.add_row("Court Proceedings", "Active in Trial", str(proc.get("active_proceedings", 0)))

        evals = telemetry.get("quality_evaluations", {})
        table.add_row("Quality Assessment", "Total Cases Evaluated", str(evals.get("total_evaluated", 0)))
        table.add_row("Quality Assessment", "Average Score (/100)", f"{evals.get('average_score', 0.0):.1f}")
        table.add_row("Quality Assessment", "High Quality (Good/Excellent)", str(evals.get("high_quality_cases", 0)))

        console.print(table)


@legalaid_app.command("beneficiary")
def register_beneficiary_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Beneficiary identifier (e.g. BEN-2025-001)"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of beneficiary"),
    citizen_id: str = typer.Option(..., "--citizen-id", help="CCCD / VNeID identifier"),
    category: str = typer.Option(..., "--category", help="NGUOI_CO_CONG, HO_NGHEO, TRE_EM, NGUOI_KHUYET_TAT_NANG, DONG_BAO_DANTOC_THIEUSO, NAN_NHAN_BAO_LUC_GIA_DINH, NGUOI_TU_DU_16_DEN_DUOI_18_BI_BUOC_TOI, NGUOI_KHO_KHAN_TAI_CHINH"),
    province: str = typer.Option(..., "--province", "-p", help="Province / municipality of residence"),
    proof: str = typer.Option(..., "--proof", help="Document verifying eligibility (e.g. Giấy chứng nhận hộ nghèo)"),
    status: str = typer.Option("VERIFIED", "--status", help="VERIFIED, PENDING_VERIFICATION, REJECTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update an eligible legal aid beneficiary under Article 7 Law on Legal Aid."""
    engine = LegalAidEngine()
    result = engine.register_beneficiary(
        code=code,
        full_name=name,
        citizen_id=citizen_id,
        category=category,
        residence_province=province,
        eligibility_proof=proof,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Beneficiary registered:[/bold green] {code} - {name} ({category})")
    else:
        console.print(f"[bold red]✗ Failed to register beneficiary:[/bold red] {result.get('error')}")


@legalaid_app.command("officer")
def register_officer_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Legal aid officer code (e.g. TGV-HN-001)"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of legal aid officer"),
    officer_type: str = typer.Option("TRO_GIUP_VIEN_PHAP_LY", "--type", help="TRO_GIUP_VIEN_PHAP_LY, LUAT_SU_KY_HOP_DONG, LUAT_SU_CONG_TAC_VIEN"),
    card: str = typer.Option(..., "--card", help="Officer card number or lawyer card number"),
    org: str = typer.Option(..., "--org", "-o", help="Legal aid center or law firm name"),
    dept: str = typer.Option(..., "--dept", "-d", help="Licensing Department of Justice (e.g. Sở Tư pháp TP. Hà Nội)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, INACTIVE, SUSPENDED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update a State Legal Aid Officer or contracted lawyer under Articles 17-23."""
    engine = LegalAidEngine()
    result = engine.register_officer(
        officer_code=code,
        full_name=name,
        officer_type=officer_type,
        card_number=card,
        organization=org,
        justice_dept=dept,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Legal aid officer registered:[/bold green] {code} - {name} ({officer_type})")
    else:
        console.print(f"[bold red]✗ Failed to register officer:[/bold red] {result.get('error')}")


@legalaid_app.command("request")
def file_request_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Request code (e.g. YCTGPL-2025-001)"),
    beneficiary: str = typer.Option(..., "--beneficiary", "-b", help="Beneficiary code"),
    form: str = typer.Option("THAM_GIA_TO_TUNG", "--form", help="THAM_GIA_TO_TUNG, TU_VAN_PHAP_LUAT, DAI_DIEN_NGOAI_TO_TUNG"),
    field: str = typer.Option("HINH_SU", "--field", help="HINH_SU, DAN_SU, HON_NHAN_GIA_DINH, HANH_CHINH, LAO_DONG, DAT_DAI"),
    title: str = typer.Option(..., "--title", "-t", help="Case description / legal issue"),
    date: Optional[str] = typer.Option(None, "--date", help="Application date (YYYY-MM-DD)"),
    officer: Optional[str] = typer.Option(None, "--officer", help="Assigned legal aid officer code"),
    status: str = typer.Option("RECEIVED", "--status", help="RECEIVED, ACCEPTED, ASSIGNED, IN_PROGRESS, COMPLETED, REJECTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """File or update a legal aid application/case docket under Articles 29-33."""
    engine = LegalAidEngine()
    result = engine.file_request(
        request_code=code,
        beneficiary_code=beneficiary,
        form=form,
        legal_field=field,
        case_title=title,
        request_date=date,
        assigned_officer_code=officer,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Legal aid request filed:[/bold green] {code} for beneficiary {beneficiary} ({form})")
    else:
        console.print(f"[bold red]✗ Failed to file request:[/bold red] {result.get('error')}")


@legalaid_app.command("proceeding")
def assign_proceeding_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Assignment decision code (e.g. QD-TGPL-2025-001)"),
    request: str = typer.Option(..., "--request", "-r", help="Legal aid request code"),
    case: str = typer.Option(..., "--case", help="Proceeding case docket number"),
    agency: str = typer.Option(..., "--agency", "-a", help="Proceeding agency (Court, Police, Procuracy)"),
    role: str = typer.Option("NGUOI_BAO_CHUA", "--role", help="NGUOI_BAO_CHUA, NGUOI_BAO_VE_QUYEN_VA_LOI_ICH_HOP_PHAP, NGUOI_DAI_DIEN_HOP_PHAP"),
    date: Optional[str] = typer.Option(None, "--date", help="Decision date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, COMPLETED, TERMINATED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Proceeding assignment notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue appointment decision for legal aid officer to participate in proceedings under Article 31."""
    engine = LegalAidEngine()
    result = engine.assign_proceeding(
        assignment_code=code,
        request_code=request,
        case_number=case,
        proceeding_agency=agency,
        procedural_role=role,
        decision_date=date,
        status=status,
        notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Proceeding assignment recorded:[/bold green] {code} in {case} ({role})")
    else:
        console.print(f"[bold red]✗ Failed to record proceeding assignment:[/bold red] {result.get('error')}")


@legalaid_app.command("eval")
def evaluate_quality_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Evaluation code (e.g. DGCL-2025-001)"),
    request: str = typer.Option(..., "--request", "-r", help="Legal aid request code"),
    evaluator: str = typer.Option(..., "--evaluator", "-e", help="Name of quality evaluator / Director"),
    score: float = typer.Option(..., "--score", "-s", help="Assessment score out of 100"),
    rating: Optional[str] = typer.Option(None, "--rating", help="XUAT_SAC, TOT, DAT, KHONG_DAT (auto-derived if omitted)"),
    date: Optional[str] = typer.Option(None, "--date", help="Evaluation date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Evaluation findings and comments"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Evaluate case quality under Circular No. 08/2017/TT-BTP (Standard, Good, Excellent, Fail)."""
    engine = LegalAidEngine()
    result = engine.evaluate_quality(
        eval_code=code,
        request_code=request,
        evaluator_name=evaluator,
        score=score,
        quality_rating=rating,
        evaluation_date=date,
        notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        evaluation = result.get("evaluation", {})
        console.print(f"[bold green]✓ Quality evaluation recorded:[/bold green] {code} - Score: {evaluation.get('score')} ({evaluation.get('quality_rating')})")
    else:
        console.print(f"[bold red]✗ Failed to record evaluation:[/bold red] {result.get('error')}")


@legalaid_app.command("list")
def list_records_cmd(
    category: str = typer.Argument(..., help="beneficiaries, officers, requests, proceedings, evaluations"),
    limit: int = typer.Option(50, "--limit", help="Maximum records to return"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List legal aid records by category (beneficiaries, officers, requests, proceedings, evaluations)."""
    engine = LegalAidEngine()
    result = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        return

    records = result.get("records", [])
    table = Table(title=f"Legal Aid Records: {category.upper()} (Count: {len(records)})", box=box.ROUNDED)

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


@legalaid_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display State Legal Aid telemetry and vulnerable population representation operational status."""
    engine = LegalAidEngine()
    result = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            "[bold cyan]VIETNAMESE STATE LEGAL AID SYSTEM — OPERATIONS STATUS[/bold cyan]\n"
            f"[dim]Statutory: {result.get('statutory_framework')}[/dim]",
            box=box.ROUNDED,
        )
    )
    typer.echo(json.dumps(result.get("telemetry", {}), ensure_ascii=False, indent=2))
