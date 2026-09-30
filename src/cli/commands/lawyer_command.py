"""
CLI Command Suite for Vietnamese Legal Profession, Bar Association & Law Practice.
Compliant with:
- Law on Lawyers 2006 (Law No. 65/2006/QH11) as amended by Law No. 20/2012/QH13
- Code of Professional Ethics and Conduct of Vietnamese Lawyers (Decision No. 201/QĐ-HĐLSTQ)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13) - Defense Counsel Provisions
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.lawyer_engine import LawyerEngine

lawyer_app = typer.Typer(
    name="lawyer",
    help="Vietnamese Legal Profession, Bar Association & Law Practice Suite (Luật Luật sư 2006/2012)",
    invoke_without_command=True,
)
app = lawyer_app
console = Console()


@lawyer_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Legal Profession & Bar Association Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = LawyerEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        console.print(
            Panel.fit(
                "[bold cyan]LIÊN ĐOÀN LUẬT SƯ VIỆT NAM — VIETNAM BAR FEDERATION[/bold cyan]\n"
                "[dim]Legal Profession, Practice Regulation & Defense Counsel Hub (Luật Luật sư)[/dim]",
                box=box.DOUBLE,
                border_style="cyan",
            )
        )

        telemetry = status_data.get("telemetry", {})
        table = Table(title="Bar & Law Practice Telemetry", box=box.ROUNDED, show_header=True)
        table.add_column("Category", style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="bold yellow")

        lawyers = telemetry.get("lawyers", {})
        table.add_row("Lawyers", "Total Admitted", str(lawyers.get("total", 0)))
        table.add_row("Lawyers", "Active Practicing", str(lawyers.get("active", 0)))

        firms = telemetry.get("law_firms", {})
        table.add_row("Law Firms / Offices", "Total Registered", str(firms.get("total", 0)))
        table.add_row("Law Firms / Offices", "Active Operating", str(firms.get("active", 0)))

        contracts = telemetry.get("legal_contracts", {})
        table.add_row("Legal Contracts", "Total Executed", str(contracts.get("total", 0)))
        table.add_row("Legal Contracts", "Active Ongoing", str(contracts.get("active", 0)))
        rem = contracts.get("total_remuneration_vnd", 0.0)
        table.add_row("Legal Contracts", "Total Remuneration", f"{rem:,.0f} VND")

        lit = telemetry.get("litigation", {})
        table.add_row("Litigation & Defense", "Total Participations", str(lit.get("total_participations", 0)))
        table.add_row("Litigation & Defense", "Criminal Defense Cases", str(lit.get("criminal_defense_cases", 0)))
        table.add_row("Litigation & Defense", "Accepted by Agencies", str(lit.get("accepted", 0)))

        ethics = telemetry.get("ethics_and_pro_bono", {})
        table.add_row("Ethics & Pro Bono", "Ethical Reviews", str(ethics.get("total_reviews", 0)))
        table.add_row("Ethics & Pro Bono", "Compliant Verdicts", str(ethics.get("compliant_reviews", 0)))
        pb_hours = ethics.get("total_pro_bono_hours", 0.0)
        table.add_row("Ethics & Pro Bono", "Pro Bono Legal Aid Hours", f"{pb_hours:,.1f} hrs")

        console.print(table)


@lawyer_app.command("attorney")
def register_attorney_cmd(
    card: str = typer.Option(..., "--card", "-c", help="Lawyer card number (e.g. LS-HN-01234)"),
    license_num: str = typer.Option(..., "--license", "-l", help="Practicing certificate issued by Ministry of Justice"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of lawyer"),
    bar: str = typer.Option(..., "--bar", "-b", help="Provincial Bar Association (e.g. Đoàn Luật sư TP. Hà Nội)"),
    org: str = typer.Option(..., "--org", "-o", help="Law practice organization name"),
    form: str = typer.Option("CONG_TY_LUAT_TNHH_2TV", "--form", help="VAN_PHONG_LUAT_SU, CONG_TY_LUAT_TNHH_1TV, CONG_TY_LUAT_TNHH_2TV, CONG_TY_LUAT_HOP_DANH, LUAT_SU_HANH_NGHE_CA_NHAN, TO_CHUC_LUAT_SU_NUOC_NGOAI"),
    spec: str = typer.Option("TRANH_TUNG_DAN_SU", "--spec", help="TRANH_TUNG_HINH_SU, TRANH_TUNG_DAN_SU, DOANH_NGHIEP_M_AND_A, SO_HUU_TRI_TUE, TAI_CHINH_NGAN_HANG, DAT_DAI_XAY_DUNG, QUOC_TE"),
    date: Optional[str] = typer.Option(None, "--date", help="Admission or issue date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, SUSPENDED, REVOKED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update a practicing lawyer admitted to the Bar under Law on Lawyers."""
    engine = LawyerEngine()
    result = engine.register_lawyer(
        card_number=card,
        license_number=license_num,
        full_name=name,
        bar_association=bar,
        organization_name=org,
        practice_form=form,
        specialization=spec,
        issue_date=date,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Lawyer registered successfully:[/bold green] {card} - {name} ({bar})")
    else:
        console.print(f"[bold red]✗ Failed to register lawyer:[/bold red] {result.get('error')}")


@lawyer_app.command("firm")
def register_firm_cmd(
    reg_num: str = typer.Option(..., "--reg-num", "-r", help="Registration certificate number from Dept of Justice"),
    name: str = typer.Option(..., "--name", "-n", help="Law firm or Law office name"),
    form: str = typer.Option("CONG_TY_LUAT_TNHH_2TV", "--form", help="VAN_PHONG_LUAT_SU, CONG_TY_LUAT_TNHH_1TV, CONG_TY_LUAT_TNHH_2TV, CONG_TY_LUAT_HOP_DANH, CHI_NHANH_LUAT_NUOC_NGOAI"),
    partner: str = typer.Option(..., "--partner", "-p", help="Managing Partner / Head of Law Office"),
    dept: str = typer.Option(..., "--dept", "-d", help="Licensing Department of Justice (e.g. Sở Tư pháp TP. Hà Nội)"),
    address: str = typer.Option(..., "--address", "-a", help="Headquarters address"),
    capital: float = typer.Option(0.0, "--capital", help="Charter capital in VND"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, TEMPORARILY_CLOSED, DISSOLVED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update a Law Practice Organization licensed by Department of Justice."""
    engine = LawyerEngine()
    result = engine.register_firm(
        registration_number=reg_num,
        firm_name=name,
        form=form,
        managing_partner=partner,
        justice_dept=dept,
        address=address,
        charter_capital=capital,
        operating_status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Law firm registered successfully:[/bold green] {reg_num} - {name} ({form})")
    else:
        console.print(f"[bold red]✗ Failed to register law firm:[/bold red] {result.get('error')}")


@lawyer_app.command("contract")
def execute_contract_cmd(
    contract_num: str = typer.Option(..., "--contract-num", "-n", help="Contract reference (e.g. HD-DVPL-2025-001)"),
    client: str = typer.Option(..., "--client", "-c", help="Client name (individual or corporate)"),
    tax_id: str = typer.Option(..., "--tax-id", help="Client CCCD/VNeID or Tax Identification Number"),
    scope: str = typer.Option("TU_VAN_PHAP_LUAT", "--scope", help="BAO_CHUA_HINH_SU, DAI_DIEN_TRANH_TUNG, TU_VAN_PHAP_LUAT, DAI_DIEN_NGOAI_TO_TUNG, DICH_VU_PHAP_LY_KHAC"),
    title: str = typer.Option(..., "--title", "-t", help="Case or legal matter description"),
    lawyer: str = typer.Option(..., "--lawyer", "-l", help="Assigned lawyer card number"),
    fee: float = typer.Option(0.0, "--fee", help="Remuneration / legal fee in VND"),
    date: Optional[str] = typer.Option(None, "--date", help="Signing date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="DRAFT, ACTIVE, COMPLETED, TERMINATED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Execute a mandatory statutory Legal Service Contract under Articles 54-56 Law on Lawyers."""
    engine = LawyerEngine()
    result = engine.execute_legal_contract(
        contract_number=contract_num,
        client_name=client,
        client_id_tax=tax_id,
        service_scope=scope,
        case_or_matter_title=title,
        assigned_lawyer_card=lawyer,
        remuneration_vnd=fee,
        signing_date=date,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Legal contract executed:[/bold green] {contract_num} for {client} ({scope})")
    else:
        console.print(f"[bold red]✗ Failed to execute contract:[/bold red] {result.get('error')}")


@lawyer_app.command("defense")
def record_defense_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Participation record code (e.g. TGTT-2025-001)"),
    case: str = typer.Option(..., "--case", help="Case docket or investigation case number"),
    agency: str = typer.Option(..., "--agency", "-a", help="Proceeding agency (Court, Police, Procuracy)"),
    lawyer: str = typer.Option(..., "--lawyer", "-l", help="Participating lawyer card number"),
    role: str = typer.Option("NGUOI_BAO_CHUA", "--role", help="NGUOI_BAO_CHUA, NGUOI_BAO_VE_QUYEN_LOI, NGUOI_DAI_DIEN_THEO_UY_QUYEN"),
    date: Optional[str] = typer.Option(None, "--date", help="Registration notice date (YYYY-MM-DD)"),
    status: str = typer.Option("ACCEPTED", "--status", help="REGISTERED, ACCEPTED, REJECTED, CONCLUDED"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Case proceeding notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Record formal participation in court or investigation proceedings (Thông báo người bào chữa)."""
    engine = LawyerEngine()
    result = engine.record_litigation_defense(
        participation_code=code,
        case_number=case,
        proceeding_agency=agency,
        lawyer_card=lawyer,
        procedural_role=role,
        registration_date=date,
        registration_status=status,
        notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Litigation defense recorded:[/bold green] {code} in {case} ({role})")
    else:
        console.print(f"[bold red]✗ Failed to record litigation defense:[/bold red] {result.get('error')}")


@lawyer_app.command("ethics")
def audit_ethics_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Review code (e.g. ETH-2025-001)"),
    lawyer: str = typer.Option(..., "--lawyer", "-l", help="Lawyer card number"),
    conflict_check: bool = typer.Option(True, "--conflict/--no-conflict", help="Conflict of interest checked and cleared"),
    confidentiality: bool = typer.Option(True, "--confidential/--no-confidential", help="Client confidentiality certified"),
    pro_bono: float = typer.Option(0.0, "--pro-bono", help="Statutory pro bono legal aid hours performed"),
    verdict: str = typer.Option("COMPLIANT", "--verdict", help="EXEMPLARY, COMPLIANT, WARNING_VIOLATION, DISCIPLINARY_ACTION"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Ethical audit notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Perform professional ethics, conflict of interest, and mandatory pro bono hours audit."""
    engine = LawyerEngine()
    result = engine.audit_ethical_compliance(
        review_code=code,
        lawyer_card=lawyer,
        conflict_of_interest_checked=conflict_check,
        client_confidentiality_certified=confidentiality,
        legal_aid_pro_bono_hours=pro_bono,
        compliance_verdict=verdict,
        reviewer_notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        console.print(f"[bold green]✓ Ethical review recorded:[/bold green] {code} for {lawyer} (Verdict: {verdict})")
    else:
        console.print(f"[bold red]✗ Failed to record ethical review:[/bold red] {result.get('error')}")


@lawyer_app.command("list")
def list_records_cmd(
    category: str = typer.Argument(..., help="lawyers, firms, contracts, litigation, ethics"),
    limit: int = typer.Option(50, "--limit", help="Maximum records to return"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List records by category (lawyers, firms, contracts, litigation, ethics)."""
    engine = LawyerEngine()
    result = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        return

    records = result.get("records", [])
    table = Table(title=f"Bar & Practice Records: {category.upper()} (Count: {len(records)})", box=box.ROUNDED)

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


@lawyer_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display bar telemetry and legal practice operational status."""
    engine = LawyerEngine()
    result = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            "[bold cyan]VIETNAM BAR FEDERATION — OPERATIONS STATUS[/bold cyan]\n"
            f"[dim]Statutory: {result.get('statutory_framework')}[/dim]",
            box=box.ROUNDED,
        )
    )
    typer.echo(json.dumps(result.get("telemetry", {}), ensure_ascii=False, indent=2))
