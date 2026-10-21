# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI Command Suite for Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access."""

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.legalaid_engine import LegalAidEngine

legalaid_app = typer.Typer(name="legalaid", help="Vietnamese State Legal Aid, Vulnerable Population Representation & Justice Access Suite (Luật Trợ giúp pháp lý 2017)", invoke_without_command=True)
app = legalaid_app
console = Console()


@legalaid_app.callback()
def main_callback(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """Vietnamese State Legal Aid Center Executive Dashboard."""
    if ctx.invoked_subcommand is not None:
        return
    status_data = LegalAidEngine().get_telemetry_status()
    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return
    console.print(Panel.fit("[bold cyan]CỤC TRỢ GIÚP PHÁP LÝ — BỘ TƯ PHÁP VIỆT NAM[/bold cyan]\n[dim]National Legal Aid System, Vulnerable Protection & Justice Access Hub (Luật TGPL 2017)[/dim]", box=box.DOUBLE, border_style="cyan"))
    telemetry = status_data.get("telemetry", {})
    table = Table(title="State Legal Aid Telemetry", box=box.ROUNDED, show_header=True)
    for col, st in (("Category", "bold green"), ("Metric", "cyan"), ("Value", "bold yellow")):
        table.add_column(col, style=st)
    ben, off, req, proc, evals = telemetry.get("beneficiaries", {}), telemetry.get("legal_aid_officers", {}), telemetry.get("requests_and_dockets", {}), telemetry.get("court_proceedings", {}), telemetry.get("quality_evaluations", {})
    for cat, m, val in (
        ("Beneficiaries", "Total Registered", str(ben.get("total", 0))), ("Beneficiaries", "Verified Eligible", str(ben.get("verified", 0))),
        ("Legal Aid Officers", "Total Appointed / Contracted", str(off.get("total", 0))), ("Legal Aid Officers", "Active Practicing", str(off.get("active", 0))),
        ("Requests & Dockets", "Total Cases Filed", str(req.get("total", 0))), ("Requests & Dockets", "Litigation Defense", str(req.get("litigation_defense", 0))),
        ("Requests & Dockets", "Legal Counseling", str(req.get("legal_counseling", 0))), ("Requests & Dockets", "Completed Dockets", str(req.get("completed", 0))),
        ("Court Proceedings", "Total Assigned Decisions", str(proc.get("total_assigned", 0))), ("Court Proceedings", "Active in Trial", str(proc.get("active_proceedings", 0))),
        ("Quality Assessment", "Total Cases Evaluated", str(evals.get("total_evaluated", 0))), ("Quality Assessment", "Average Score (/100)", f"{evals.get('average_score', 0.0):.1f}"),
        ("Quality Assessment", "High Quality (Good/Excellent)", str(evals.get("high_quality_cases", 0))),
    ):
        table.add_row(cat, m, val)
    console.print(table)


@legalaid_app.command("beneficiary")
def register_beneficiary_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Beneficiary identifier"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of beneficiary"),
    citizen_id: str = typer.Option(..., "--citizen-id", help="CCCD / VNeID identifier"),
    category: str = typer.Option(..., "--category", help="NGUOI_CO_CONG, HO_NGHEO, TRE_EM, NGUOI_KHUYET_TAT_NANG, ..."),
    province: str = typer.Option(..., "--province", "-p", help="Province / municipality of residence"),
    proof: str = typer.Option(..., "--proof", help="Document verifying eligibility"),
    status: str = typer.Option("VERIFIED", "--status", help="VERIFIED, PENDING_VERIFICATION, REJECTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Register or update an eligible legal aid beneficiary under Article 7 Law on Legal Aid."""
    result = LegalAidEngine().register_beneficiary(code=code, full_name=name, citizen_id=citizen_id, category=category, residence_province=province, eligibility_proof=proof, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Beneficiary registered:[/bold green] {code} - {name} ({category})" if result.get("success") else f"[bold red]✗ Failed to register beneficiary:[/bold red] {result.get('error')}")


@legalaid_app.command("officer")
def register_officer_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Legal aid officer code"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of legal aid officer"),
    officer_type: str = typer.Option("TRO_GIUP_VIEN_PHAP_LY", "--type", help="TRO_GIUP_VIEN_PHAP_LY, LUAT_SU_KY_HOP_DONG, LUAT_SU_CONG_TAC_VIEN"),
    card: str = typer.Option(..., "--card", help="Officer card number or lawyer card number"),
    org: str = typer.Option(..., "--org", "-o", help="Legal aid center or law firm name"),
    dept: str = typer.Option(..., "--dept", "-d", help="Licensing Department of Justice"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, INACTIVE, SUSPENDED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Register or update a State Legal Aid Officer or contracted lawyer under Articles 17-23."""
    result = LegalAidEngine().register_officer(officer_code=code, full_name=name, officer_type=officer_type, card_number=card, organization=org, justice_dept=dept, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Legal aid officer registered:[/bold green] {code} - {name} ({officer_type})" if result.get("success") else f"[bold red]✗ Failed to register officer:[/bold red] {result.get('error')}")


@legalaid_app.command("request")
def file_request_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Request code"),
    beneficiary: str = typer.Option(..., "--beneficiary", "-b", help="Beneficiary code"),
    form: str = typer.Option("THAM_GIA_TO_TUNG", "--form", help="THAM_GIA_TO_TUNG, TU_VAN_PHAP_LUAT, DAI_DIEN_NGOAI_TO_TUNG"),
    field: str = typer.Option("HINH_SU", "--field", help="HINH_SU, DAN_SU, HON_NHAN_GIA_DINH, HANH_CHINH, LAO_DONG, DAT_DAI"),
    title: str = typer.Option(..., "--title", "-t", help="Case description / legal issue"),
    date: Optional[str] = typer.Option(None, "--date", help="Application date (YYYY-MM-DD)"),
    officer: Optional[str] = typer.Option(None, "--officer", help="Assigned legal aid officer code"),
    status: str = typer.Option("RECEIVED", "--status", help="RECEIVED, ACCEPTED, ASSIGNED, IN_PROGRESS, COMPLETED, REJECTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """File or update a legal aid application/case docket under Articles 29-33."""
    result = LegalAidEngine().file_request(request_code=code, beneficiary_code=beneficiary, form=form, legal_field=field, case_title=title, request_date=date, assigned_officer_code=officer, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Legal aid request filed:[/bold green] {code} for beneficiary {beneficiary} ({form})" if result.get("success") else f"[bold red]✗ Failed to file request:[/bold red] {result.get('error')}")


@legalaid_app.command("proceeding")
def assign_proceeding_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Assignment decision code"),
    request: str = typer.Option(..., "--request", "-r", help="Legal aid request code"),
    case: str = typer.Option(..., "--case", help="Proceeding case docket number"),
    agency: str = typer.Option(..., "--agency", "-a", help="Proceeding agency (Court, Police, Procuracy)"),
    role: str = typer.Option("NGUOI_BAO_CHUA", "--role", help="NGUOI_BAO_CHUA, NGUOI_BAO_VE_QUYEN_VA_LOI_ICH_HOP_PHAP, NGUOI_DAI_DIEN_HOP_PHAP"),
    date: Optional[str] = typer.Option(None, "--date", help="Decision date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, COMPLETED, TERMINATED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Proceeding assignment notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Issue appointment decision for legal aid officer to participate in proceedings under Article 31."""
    result = LegalAidEngine().assign_proceeding(assignment_code=code, request_code=request, case_number=case, proceeding_agency=agency, procedural_role=role, decision_date=date, status=status, notes=notes)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Proceeding assignment recorded:[/bold green] {code} in {case} ({role})" if result.get("success") else f"[bold red]✗ Failed to record proceeding assignment:[/bold red] {result.get('error')}")


@legalaid_app.command("eval")
def evaluate_quality_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Evaluation code"),
    request: str = typer.Option(..., "--request", "-r", help="Legal aid request code"),
    evaluator: str = typer.Option(..., "--evaluator", "-e", help="Name of quality evaluator / Director"),
    score: float = typer.Option(..., "--score", "-s", help="Assessment score out of 100"),
    rating: Optional[str] = typer.Option(None, "--rating", help="XUAT_SAC, TOT, DAT, KHONG_DAT"),
    date: Optional[str] = typer.Option(None, "--date", help="Evaluation date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Evaluation findings and comments"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Evaluate case quality under Circular No. 08/2017/TT-BTP (Standard, Good, Excellent, Fail)."""
    result = LegalAidEngine().evaluate_quality(eval_code=code, request_code=request, evaluator_name=evaluator, score=score, quality_rating=rating, evaluation_date=date, notes=notes)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result.get("success"):
        ev = result.get("evaluation", {})
        console.print(f"[bold green]✓ Quality evaluation recorded:[/bold green] {code} - Score: {ev.get('score')} ({ev.get('quality_rating')})")
    else:
        console.print(f"[bold red]✗ Failed to record evaluation:[/bold red] {result.get('error')}")


@legalaid_app.command("list")
def list_records_cmd(category: str = typer.Argument(..., help="beneficiaries, officers, requests, proceedings, evaluations"), limit: int = typer.Option(50, "--limit", help="Maximum records to return"), json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """List legal aid records by category (beneficiaries, officers, requests, proceedings, evaluations)."""
    result = LegalAidEngine().list_records(category=category, limit=limit)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        return
    if not (records := result.get("records", [])):
        console.print(f"[dim]No records found for category '{category}'[/dim]")
        return
    table = Table(title=f"Legal Aid Records: {category.upper()} (Count: {len(records)})", box=box.ROUNDED)
    keys = list(records[0].keys())[:6]
    for k in keys:
        table.add_column(k.replace("_", " ").title(), style="cyan")
    for r in records:
        table.add_row(*[str(r.get(k, "")) for k in keys])
    console.print(table)


@legalaid_app.command("status")
def status_cmd(json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """Display State Legal Aid telemetry and vulnerable population representation operational status."""
    result = LegalAidEngine().get_telemetry_status()
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(Panel.fit(f"[bold cyan]VIETNAMESE STATE LEGAL AID SYSTEM — OPERATIONS STATUS[/bold cyan]\n[dim]Statutory: {result.get('statutory_framework')}[/dim]", box=box.ROUNDED))
    typer.echo(json.dumps(result.get("telemetry", {}), ensure_ascii=False, indent=2))
