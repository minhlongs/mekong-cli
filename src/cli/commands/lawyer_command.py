# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI Command Suite for Vietnamese Legal Profession, Bar Association & Law Practice."""

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.lawyer_engine import LawyerEngine

lawyer_app = typer.Typer(name="lawyer", help="Vietnamese Legal Profession, Bar Association & Law Practice Suite (Luật Luật sư 2006/2012)", invoke_without_command=True)
app = lawyer_app
console = Console()


@lawyer_app.callback()
def main_callback(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """Vietnamese Legal Profession & Bar Association Executive Dashboard."""
    if ctx.invoked_subcommand is not None:
        return
    status_data = LawyerEngine().get_telemetry_status()
    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return
    console.print(Panel.fit("[bold cyan]LIÊN ĐOÀN LUẬT SƯ VIỆT NAM — VIETNAM BAR FEDERATION[/bold cyan]\n[dim]Legal Profession, Practice Regulation & Defense Counsel Hub (Luật Luật sư)[/dim]", box=box.DOUBLE, border_style="cyan"))
    telemetry = status_data.get("telemetry", {})
    table = Table(title="Bar & Law Practice Telemetry", box=box.ROUNDED, show_header=True)
    for col, st in (("Category", "bold green"), ("Metric", "cyan"), ("Value", "bold yellow")):
        table.add_column(col, style=st)
    lawyers, firms, contracts, lit, ethics = telemetry.get("lawyers", {}), telemetry.get("law_firms", {}), telemetry.get("legal_contracts", {}), telemetry.get("litigation", {}), telemetry.get("ethics_and_pro_bono", {})
    for cat, m, val in (
        ("Lawyers", "Total Admitted", str(lawyers.get("total", 0))), ("Lawyers", "Active Practicing", str(lawyers.get("active", 0))),
        ("Law Firms / Offices", "Total Registered", str(firms.get("total", 0))), ("Law Firms / Offices", "Active Operating", str(firms.get("active", 0))),
        ("Legal Contracts", "Total Executed", str(contracts.get("total", 0))), ("Legal Contracts", "Active Ongoing", str(contracts.get("active", 0))),
        ("Legal Contracts", "Total Remuneration", f"{contracts.get('total_remuneration_vnd', 0.0):,.0f} VND"),
        ("Litigation & Defense", "Total Participations", str(lit.get("total_participations", 0))), ("Litigation & Defense", "Criminal Defense Cases", str(lit.get("criminal_defense_cases", 0))),
        ("Litigation & Defense", "Accepted by Agencies", str(lit.get("accepted", 0))), ("Ethics & Pro Bono", "Ethical Reviews", str(ethics.get("total_reviews", 0))),
        ("Ethics & Pro Bono", "Compliant Verdicts", str(ethics.get("compliant_reviews", 0))), ("Ethics & Pro Bono", "Pro Bono Legal Aid Hours", f"{ethics.get('total_pro_bono_hours', 0.0):,.1f} hrs"),
    ):
        table.add_row(cat, m, val)
    console.print(table)


@lawyer_app.command("attorney")
def register_attorney_cmd(
    card: str = typer.Option(..., "--card", "-c", help="Lawyer card number (e.g. LS-HN-01234)"),
    license_num: str = typer.Option(..., "--license", "-l", help="Practicing certificate issued by Ministry of Justice"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of lawyer"),
    bar: str = typer.Option(..., "--bar", "-b", help="Provincial Bar Association"),
    org: str = typer.Option(..., "--org", "-o", help="Law practice organization name"),
    form: str = typer.Option("CONG_TY_LUAT_TNHH_2TV", "--form", help="VAN_PHONG_LUAT_SU, CONG_TY_LUAT_TNHH_1TV, ..."),
    spec: str = typer.Option("TRANH_TUNG_DAN_SU", "--spec", help="TRANH_TUNG_HINH_SU, TRANH_TUNG_DAN_SU, ..."),
    date: Optional[str] = typer.Option(None, "--date", help="Admission or issue date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, SUSPENDED, REVOKED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Register or update a practicing lawyer admitted to the Bar under Law on Lawyers."""
    result = LawyerEngine().register_lawyer(card_number=card, license_number=license_num, full_name=name, bar_association=bar, organization_name=org, practice_form=form, specialization=spec, issue_date=date, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Lawyer registered successfully:[/bold green] {card} - {name} ({bar})" if result.get("success") else f"[bold red]✗ Failed to register lawyer:[/bold red] {result.get('error')}")


@lawyer_app.command("firm")
def register_firm_cmd(
    reg_num: str = typer.Option(..., "--reg-num", "-r", help="Registration certificate number from Dept of Justice"),
    name: str = typer.Option(..., "--name", "-n", help="Law firm or Law office name"),
    form: str = typer.Option("CONG_TY_LUAT_TNHH_2TV", "--form", help="VAN_PHONG_LUAT_SU, CONG_TY_LUAT_TNHH_1TV, ..."),
    partner: str = typer.Option(..., "--partner", "-p", help="Managing Partner / Head of Law Office"),
    dept: str = typer.Option(..., "--dept", "-d", help="Licensing Department of Justice"),
    address: str = typer.Option(..., "--address", "-a", help="Headquarters address"),
    capital: float = typer.Option(0.0, "--capital", help="Charter capital in VND"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, TEMPORARILY_CLOSED, DISSOLVED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Register or update a Law Practice Organization licensed by Department of Justice."""
    result = LawyerEngine().register_firm(registration_number=reg_num, firm_name=name, form=form, managing_partner=partner, justice_dept=dept, address=address, charter_capital=capital, operating_status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Law firm registered successfully:[/bold green] {reg_num} - {name} ({form})" if result.get("success") else f"[bold red]✗ Failed to register law firm:[/bold red] {result.get('error')}")


@lawyer_app.command("contract")
def execute_contract_cmd(
    contract_num: str = typer.Option(..., "--contract-num", "-n", help="Contract reference"),
    client: str = typer.Option(..., "--client", "-c", help="Client name"),
    tax_id: str = typer.Option(..., "--tax-id", help="Client CCCD/VNeID or Tax ID"),
    scope: str = typer.Option("TU_VAN_PHAP_LUAT", "--scope", help="BAO_CHUA_HINH_SU, DAI_DIEN_TRANH_TUNG, ..."),
    title: str = typer.Option(..., "--title", "-t", help="Case or legal matter description"),
    lawyer: str = typer.Option(..., "--lawyer", "-l", help="Assigned lawyer card number"),
    fee: float = typer.Option(0.0, "--fee", help="Remuneration / legal fee in VND"),
    date: Optional[str] = typer.Option(None, "--date", help="Signing date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="DRAFT, ACTIVE, COMPLETED, TERMINATED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Execute a mandatory statutory Legal Service Contract under Articles 54-56 Law on Lawyers."""
    result = LawyerEngine().execute_legal_contract(contract_number=contract_num, client_name=client, client_id_tax=tax_id, service_scope=scope, case_or_matter_title=title, assigned_lawyer_card=lawyer, remuneration_vnd=fee, signing_date=date, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Legal contract executed:[/bold green] {contract_num} for {client} ({scope})" if result.get("success") else f"[bold red]✗ Failed to execute contract:[/bold red] {result.get('error')}")


@lawyer_app.command("defense")
def record_defense_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Participation record code"),
    case: str = typer.Option(..., "--case", help="Case docket or investigation case number"),
    agency: str = typer.Option(..., "--agency", "-a", help="Proceeding agency (Court, Police, Procuracy)"),
    lawyer: str = typer.Option(..., "--lawyer", "-l", help="Participating lawyer card number"),
    role: str = typer.Option("NGUOI_BAO_CHUA", "--role", help="NGUOI_BAO_CHUA, NGUOI_BAO_VE_QUYEN_LOI, NGUOI_DAI_DIEN_THEO_UY_QUYEN"),
    date: Optional[str] = typer.Option(None, "--date", help="Registration notice date (YYYY-MM-DD)"),
    status: str = typer.Option("ACCEPTED", "--status", help="REGISTERED, ACCEPTED, REJECTED, CONCLUDED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Case proceeding notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Record formal participation in court or investigation proceedings (Thông báo người bào chữa)."""
    result = LawyerEngine().record_litigation_defense(participation_code=code, case_number=case, proceeding_agency=agency, lawyer_card=lawyer, procedural_role=role, registration_date=date, registration_status=status, notes=notes)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Litigation defense recorded:[/bold green] {code} in {case} ({role})" if result.get("success") else f"[bold red]✗ Failed to record litigation defense:[/bold red] {result.get('error')}")


@lawyer_app.command("ethics")
def audit_ethics_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Review code"),
    lawyer: str = typer.Option(..., "--lawyer", "-l", help="Lawyer card number"),
    conflict_check: bool = typer.Option(True, "--conflict/--no-conflict", help="Conflict of interest checked"),
    confidentiality: bool = typer.Option(True, "--confidential/--no-confidential", help="Client confidentiality certified"),
    pro_bono: float = typer.Option(0.0, "--pro-bono", help="Statutory pro bono legal aid hours performed"),
    verdict: str = typer.Option("COMPLIANT", "--verdict", help="EXEMPLARY, COMPLIANT, WARNING_VIOLATION, DISCIPLINARY_ACTION"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Ethical audit notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Perform professional ethics, conflict of interest, and mandatory pro bono hours audit."""
    result = LawyerEngine().audit_ethical_compliance(review_code=code, lawyer_card=lawyer, conflict_of_interest_checked=conflict_check, client_confidentiality_certified=confidentiality, legal_aid_pro_bono_hours=pro_bono, compliance_verdict=verdict, reviewer_notes=notes)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(f"[bold green]✓ Ethical review recorded:[/bold green] {code} for {lawyer} (Verdict: {verdict})" if result.get("success") else f"[bold red]✗ Failed to record ethical review:[/bold red] {result.get('error')}")


@lawyer_app.command("list")
def list_records_cmd(category: str = typer.Argument(..., help="lawyers, firms, contracts, litigation, ethics"), limit: int = typer.Option(50, "--limit", help="Maximum records to return"), json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """List records by category (lawyers, firms, contracts, litigation, ethics)."""
    result = LawyerEngine().list_records(category=category, limit=limit)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        return
    if not (records := result.get("records", [])):
        console.print(f"[dim]No records found for category '{category}'[/dim]")
        return
    table = Table(title=f"Bar & Practice Records: {category.upper()} (Count: {len(records)})", box=box.ROUNDED)
    keys = list(records[0].keys())[:6]
    for k in keys:
        table.add_column(k.replace("_", " ").title(), style="cyan")
    for r in records:
        table.add_row(*[str(r.get(k, "")) for k in keys])
    console.print(table)


@lawyer_app.command("status")
def status_cmd(json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """Display bar telemetry and legal practice operational status."""
    result = LawyerEngine().get_telemetry_status()
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    console.print(Panel.fit(f"[bold cyan]VIETNAM BAR FEDERATION — OPERATIONS STATUS[/bold cyan]\n[dim]Statutory: {result.get('statutory_framework')}[/dim]", box=box.ROUNDED))
    typer.echo(json.dumps(result.get("telemetry", {}), ensure_ascii=False, indent=2))
