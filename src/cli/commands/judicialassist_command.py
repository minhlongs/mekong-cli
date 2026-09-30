"""
CLI Command Suite for Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation.
Compliant with:
- Law on Mutual Legal Assistance 2007 (Luật Tương trợ tư pháp - Law No. 08/2007/QH12)
- Criminal Procedure Code 2015 (Part Eight: International Cooperation)
- Civil Procedure Code 2015 (Part Eight: Foreign-Element Procedures)
- Joint Circular No. 02/2016/TTLT & Joint Circular No. 12/2016/TTLT
"""

import typer
import json
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.judicialassist_engine import (
    JudicialAssistEngine,
    CivilRequestType,
    CriminalRequestType,
    ExtraditionGround,
    RefusalGround,
    RequestDirection,
    CooperationBasis,
    WorkflowStatus,
)

judicialassist_app = typer.Typer(
    name="judicialassist",
    help="Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Suite (Luật Tương trợ tư pháp 2007)",
    invoke_without_command=True,
)
app = judicialassist_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG TƯƠNG TRỢ TƯ PHÁP QUỐC TẾ[/bold cyan]\n"
            "[dim]Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Hub (Luật Tương trợ tư pháp 2007)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Cross-Border Judicial Assistance Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Domain / Pillar", style="bold green")
    table.add_column("Focal Authority", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Civil MLA (Dân sự)",
        "Ministry of Justice (Bộ Tư pháp)",
        "Total Requests",
        str(status_data.get("total_civil_requests", 0)),
    )
    table.add_row(
        "Civil MLA (Dân sự)",
        "Ministry of Justice",
        "Total Costs (USD)",
        f"${status_data.get('total_civil_costs_usd', 0.0):,.2f}",
    )
    table.add_row(
        "Criminal MLA (Hình sự)",
        "Supreme People's Procuracy (VKSNDTC)",
        "Total Requests",
        str(status_data.get("total_criminal_requests", 0)),
    )
    table.add_row(
        "Criminal MLA (Hình sự)",
        "Supreme People's Procuracy",
        "Asset Value (VND)",
        f"{status_data.get('total_criminal_assets_vnd', 0.0):,.0f} VND",
    )
    table.add_row(
        "Extradition (Dẫn độ)",
        "Ministry of Public Security (Bộ Công an)",
        "Total Dossiers",
        str(status_data.get("total_extradition_dossiers", 0)),
    )
    table.add_row(
        "Extradition (Dẫn độ)",
        "Ministry of Public Security",
        "Refused / Barred",
        str(status_data.get("refused_extraditions", 0)),
    )
    table.add_row(
        "Sentence Transfer (Chuyển giao)",
        "Ministry of Public Security (Bộ Công an)",
        "Total Transfers",
        str(status_data.get("total_sentence_transfers", 0)),
    )
    table.add_row(
        "Sentence Transfer (Chuyển giao)",
        "Ministry of Public Security",
        "Completed",
        str(status_data.get("completed_sentence_transfers", 0)),
    )
    table.add_row(
        "Bilateral Treaties",
        "Ministry of Foreign Affairs (Bộ Ngoại giao)",
        "Active Treaties",
        str(status_data.get("active_bilateral_treaties", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@judicialassist_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Mutual Legal Assistance Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = JudicialAssistEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@judicialassist_app.command("civil")
def create_civil_cmd(
    case_code: str = typer.Option(..., "--case-code", "-c", help="Court civil case code (e.g. 15/2026/TLST-DS)"),
    direction: str = typer.Option("OUTGOING", "--direction", "-d", help="Direction: OUTGOING | INCOMING"),
    request_type: str = typer.Option("SERVICE_OF_DOCUMENTS", "--type", "-t", help="Type: SERVICE_OF_DOCUMENTS | EVIDENCE_COLLECTION | ASSET_VERIFICATION | EXPERT_SUMMONS"),
    requesting_body: str = typer.Option(..., "--requesting-body", "-r", help="Requesting court or judicial body"),
    foreign_country: str = typer.Option(..., "--foreign-country", "-f", help="Target foreign country name"),
    target_person: str = typer.Option(..., "--target", help="Name of target person or entity"),
    service_address: str = typer.Option(..., "--address", help="Service address in target country"),
    basis: str = typer.Option("BILATERAL_TREATY", "--basis", help="Basis: BILATERAL_TREATY | MULTILATERAL_CONVENTION | RECIPROCITY_PRINCIPLE"),
    costs_usd: float = typer.Option(0.0, "--costs-usd", help="Estimated judicial service costs in USD"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Workflow status"),
    notes: str = typer.Option("", "--notes", help="Case notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Submit and record a Civil Mutual Legal Assistance Request under Art 10-16."""
    try:
        engine = JudicialAssistEngine()
        result = engine.create_civil_request(
            case_code=case_code,
            direction=direction,
            request_type=request_type,
            requesting_body=requesting_body,
            foreign_country=foreign_country,
            target_person_org=target_person,
            service_address=service_address,
            cooperation_basis=basis,
            costs_usd=costs_usd,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Civil Mutual Legal Assistance Request Registered:[/bold green] [cyan]{result['request_id']}[/cyan]")
        console.print(f"  [bold]Case Code:[/bold] {result['case_code']} | [bold]Direction:[/bold] {result['direction']}")
        console.print(f"  [bold]Type:[/bold] {result['request_type']} | [bold]Country:[/bold] {result['foreign_country']}")
        console.print(f"  [bold]Target:[/bold] {result['target_person_org']} | [bold]Costs:[/bold] ${result['costs_usd']:,.2f}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error registering civil request:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("criminal")
def create_criminal_cmd(
    case_code: str = typer.Option(..., "--case-code", "-c", help="Criminal case dossier number"),
    direction: str = typer.Option("OUTGOING", "--direction", "-d", help="Direction: OUTGOING | INCOMING"),
    request_type: str = typer.Option("TESTIMONY_EXTRACTION", "--type", "-t", help="Type: TESTIMONY_EXTRACTION | SEARCH_AND_SEIZURE | CRIME_SCENE_EXAMINATION | ASSET_FREEZE_CONFISCATION | CRIMINAL_RECORD_CHECK"),
    agency: str = typer.Option(..., "--agency", "-a", help="Requesting agency (VKSND / CQĐT)"),
    foreign_country: str = typer.Option(..., "--foreign-country", "-f", help="Target foreign country"),
    offense: str = typer.Option(..., "--offense", help="Alleged offense description"),
    dual_criminality: bool = typer.Option(True, "--dual-criminality/--no-dual-criminality", help="Dual criminality satisfied"),
    basis: str = typer.Option("BILATERAL_TREATY", "--basis", help="Basis: BILATERAL_TREATY | MULTILATERAL_CONVENTION | RECIPROCITY_PRINCIPLE"),
    asset_vnd: float = typer.Option(0.0, "--asset-vnd", help="Asset value for freeze/confiscation in VND"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Workflow status"),
    notes: str = typer.Option("", "--notes", help="Case notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Submit and record a Criminal Mutual Legal Assistance Request under Art 17-31."""
    try:
        engine = JudicialAssistEngine()
        result = engine.create_criminal_request(
            case_code=case_code,
            direction=direction,
            request_type=request_type,
            requesting_agency=agency,
            foreign_country=foreign_country,
            alleged_offense=offense,
            dual_criminality=dual_criminality,
            cooperation_basis=basis,
            asset_value_vnd=asset_vnd,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Criminal Mutual Legal Assistance Request Registered:[/bold green] [cyan]{result['request_id']}[/cyan]")
        console.print(f"  [bold]Case Code:[/bold] {result['case_code']} | [bold]Direction:[/bold] {result['direction']}")
        console.print(f"  [bold]Agency:[/bold] {result['requesting_agency']} | [bold]Country:[/bold] {result['foreign_country']}")
        console.print(f"  [bold]Offense:[/bold] {result['alleged_offense']} | [bold]Dual Criminality:[/bold] {result['dual_criminality'] == 1}")
        console.print(f"  [bold]Asset Value:[/bold] {result['asset_value_vnd']:,.0f} VND | [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error registering criminal request:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("extradition")
def evaluate_extradition_cmd(
    subject: str = typer.Option(..., "--subject", "-n", help="Full name of the subject requested for extradition"),
    nationality: str = typer.Option(..., "--nationality", help="Nationality of the subject"),
    direction: str = typer.Option("INCOMING", "--direction", "-d", help="Direction: INCOMING | OUTGOING"),
    country: str = typer.Option(..., "--country", "-c", help="Requesting / requested country"),
    ground: str = typer.Option("PROSECUTION_INVESTIGATION", "--ground", "-g", help="Ground: PROSECUTION_INVESTIGATION | SENTENCE_EXECUTION"),
    offense: str = typer.Option(..., "--offense", help="Name of offense committed"),
    penalty_months: int = typer.Option(24, "--penalty-months", help="Statutory penalty framework in months (minimum 12 for prosecution)"),
    remaining_months: int = typer.Option(0, "--remaining-months", help="Remaining sentence in months (minimum 6 for sentence execution)"),
    dual_criminality: bool = typer.Option(True, "--dual-criminality/--no-dual-criminality", help="Dual criminality satisfied"),
    provisional_arrest: bool = typer.Option(False, "--provisional-arrest/--no-provisional-arrest", help="Under provisional arrest (Art 41)"),
    arrest_date: Optional[str] = typer.Option(None, "--arrest-date", help="Date of provisional arrest (YYYY-MM-DD)"),
    vietnamese_citizen: bool = typer.Option(False, "--vietnamese-citizen/--not-vietnamese-citizen", help="Subject is a Vietnamese citizen (Art 35 k1a)"),
    limitations_expired: bool = typer.Option(False, "--expired-limitations/--valid-limitations", help="Statute of limitations expired (Art 35 k1b)"),
    ne_bis_in_idem: bool = typer.Option(False, "--ne-bis-in-idem/--no-prior-judgment", help="Prior final judgment rendered (Art 35 k1c)"),
    torture_risk: bool = typer.Option(False, "--torture-risk/--no-torture-risk", help="Risk of torture/persecution (Art 35 k1d)"),
    political_offense: bool = typer.Option(False, "--political-offense/--common-crime", help="Political or military offense (Art 35 k1đ)"),
    no_death_penalty_assurance: bool = typer.Option(False, "--no-death-penalty-assurance", help="No written assurance against death penalty (Art 35 k2a)"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Dossier status"),
    notes: str = typer.Option("", "--notes", help="Dossier notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Evaluate and record an Extradition Dossier according to statutory standards (Art 32-48)."""
    try:
        engine = JudicialAssistEngine()
        result = engine.evaluate_extradition(
            subject_name=subject,
            nationality=nationality,
            direction=direction,
            requesting_country=country,
            extradition_ground=ground,
            offense_name=offense,
            penalty_framework_months=penalty_months,
            remaining_sentence_months=remaining_months,
            dual_criminality=dual_criminality,
            provisional_arrest=provisional_arrest,
            arrest_date=arrest_date,
            is_vietnamese_citizen=vietnamese_citizen,
            statute_of_limitations_expired=limitations_expired,
            ne_bis_in_idem=ne_bis_in_idem,
            torture_persecution_risk=torture_risk,
            political_military_offense=political_offense,
            death_penalty_without_assurance=no_death_penalty_assurance,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        refusal = result["refusal_ground"]
        refusal_color = "red" if refusal != "NONE" else "green"
        console.print(f"[bold green]✓ Extradition Dossier Evaluated:[/bold green] [cyan]{result['dossier_id']}[/cyan]")
        console.print(f"  [bold]Subject:[/bold] {result['subject_name']} ({result['nationality']}) | [bold]Direction:[/bold] {result['direction']}")
        console.print(f"  [bold]Country:[/bold] {result['requesting_country']} | [bold]Offense:[/bold] {result['offense_name']}")
        console.print(f"  [bold]Ground:[/bold] {result['extradition_ground']} | [bold]Penalty Framework:[/bold] {result['penalty_framework_months']} mos")
        console.print(f"  [bold]Provisional Arrest:[/bold] {result['provisional_arrest'] == 1} (Date: {result['arrest_date'] or 'N/A'})")
        console.print(f"  [bold]Refusal Analysis:[/bold] [{refusal_color}]{refusal}[/{refusal_color}]")
        console.print(f"  [bold]Final Status:[/bold] [yellow]{result['status']}[/yellow]")
        if result["notes"]:
            console.print(f"  [bold]Notes:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error evaluating extradition dossier:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("transfer")
def process_transfer_cmd(
    prisoner: str = typer.Option(..., "--prisoner", "-p", help="Full name of the sentenced prisoner"),
    nationality: str = typer.Option(..., "--nationality", help="Prisoner's nationality"),
    direction: str = typer.Option("OUTGOING", "--direction", "-d", help="Direction: OUTGOING | INCOMING"),
    from_country: str = typer.Option(..., "--from-country", help="Transferring state"),
    to_country: str = typer.Option(..., "--to-country", help="Receiving state"),
    original_months: int = typer.Option(..., "--original-months", help="Total sentence term in months"),
    served_months: int = typer.Option(..., "--served-months", help="Sentence term already served in months"),
    remaining_months: int = typer.Option(..., "--remaining-months", help="Sentence term remaining in months (minimum 12 mos)"),
    consent: bool = typer.Option(True, "--consent/--no-consent", help="Voluntary written consent of prisoner (Art 50 k1b)"),
    dual_criminality: bool = typer.Option(True, "--dual-criminality/--no-dual-criminality", help="Dual criminality satisfied (Art 50 k1d)"),
    compensation_cleared: bool = typer.Option(True, "--compensation-cleared/--compensation-pending", help="Civil liabilities cleared (Art 51 k1c)"),
    court_decision: Optional[str] = typer.Option(None, "--court-decision", help="Court transfer approval decision number"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Workflow status"),
    notes: str = typer.Option("", "--notes", help="Transfer notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Process and record the Transfer of a Sentenced Person under Art 49-64."""
    try:
        engine = JudicialAssistEngine()
        result = engine.process_sentence_transfer(
            prisoner_name=prisoner,
            prisoner_nationality=nationality,
            direction=direction,
            from_country=from_country,
            to_country=to_country,
            original_sentence_months=original_months,
            served_sentence_months=served_months,
            remaining_sentence_months=remaining_months,
            prisoner_written_consent=consent,
            dual_criminality=dual_criminality,
            civil_compensation_cleared=compensation_cleared,
            court_decision=court_decision,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Sentence Transfer Dossier Processed:[/bold green] [cyan]{result['transfer_id']}[/cyan]")
        console.print(f"  [bold]Prisoner:[/bold] {result['prisoner_name']} ({result['prisoner_nationality']})")
        console.print(f"  [bold]Route:[/bold] {result['from_country']} -> {result['to_country']}")
        console.print(f"  [bold]Sentence:[/bold] {result['served_sentence_months']}/{result['original_sentence_months']} mos served | [bold]Remaining:[/bold] {result['remaining_sentence_months']} mos")
        console.print(f"  [bold]Consent:[/bold] {result['prisoner_written_consent'] == 1} | [bold]Dual Criminality:[/bold] {result['dual_criminality'] == 1} | [bold]Civil Cleared:[/bold] {result['civil_compensation_cleared'] == 1}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
        if result["notes"]:
            console.print(f"  [bold]Statutory Remarks:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing sentence transfer:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("treaty")
def register_treaty_cmd(
    country: str = typer.Option(..., "--country", "-c", help="Signatory country name"),
    title: str = typer.Option(..., "--title", "-t", help="Official title of the bilateral treaty"),
    signing_date: str = typer.Option(..., "--signing-date", help="Date of signing (YYYY-MM-DD)"),
    effective_date: str = typer.Option(..., "--effective-date", help="Date entry into force (YYYY-MM-DD)"),
    domains: List[str] = typer.Option(["CIVIL", "CRIMINAL", "EXTRADITION"], "--domain", "-d", help="Covered domains (e.g. CIVIL, CRIMINAL, EXTRADITION, SENTENCE_TRANSFER)"),
    active: bool = typer.Option(True, "--active/--inactive", help="Whether treaty is currently active"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register a Bilateral Mutual Legal Assistance / Extradition Treaty."""
    try:
        engine = JudicialAssistEngine()
        result = engine.register_bilateral_treaty(
            country_name=country,
            treaty_title=title,
            signing_date=signing_date,
            effective_date=effective_date,
            covered_domains=domains,
            is_active=active,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Bilateral Treaty Registered:[/bold green] [cyan]{result['treaty_id']}[/cyan]")
        console.print(f"  [bold]Partner Country:[/bold] {result['country_name']}")
        console.print(f"  [bold]Title:[/bold] {result['treaty_title']}")
        console.print(f"  [bold]Timeline:[/bold] Signed: {result['signing_date']} | Effective: {result['effective_date']}")
        console.print(f"  [bold]Covered Domains:[/bold] {', '.join(result['covered_domains'])}")
        console.print(f"  [bold]Active Status:[/bold] [green]{'ACTIVE' if result['is_active'] == 1 else 'INACTIVE'}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error registering bilateral treaty:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("list")
def list_records_cmd(
    category: str = typer.Option("civil", "--category", "-c", help="Category: civil | criminal | extradition | transfer | treaty | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List cross-border judicial assistance records by category."""
    try:
        engine = JudicialAssistEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Cross-Border Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show cross-border judicial assistance telemetry and system status."""
    engine = JudicialAssistEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
