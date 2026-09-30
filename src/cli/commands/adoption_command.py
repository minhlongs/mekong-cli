"""
CLI Command Suite for Vietnamese Child Adoption & Hague Intercountry Adoption Management.
Compliant with:
- Law on Adoption 2010 (Luật Nuôi con nuôi - Law No. 52/2010/QH12)
- Decree No. 19/2011/ND-CP detailing the implementation of the Law on Adoption
- Decree No. 24/2019/ND-CP amending Decree No. 19/2011/ND-CP
- Circular No. 10/2020/TT-BTP on adoption forms, records, and registries
- Hague Convention on Protection of Children and Co-operation in Respect of Intercountry Adoption 1993
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.adoption_engine import (
    AdoptionEngine,
    AdoptionType,
    AdopterRelationship,
    AdoptionStatus,
    PostPlacementRating,
)

adoption_app = typer.Typer(
    name="adoption",
    help="Vietnamese Child Adoption & Hague Intercountry Adoption Suite (Luật Nuôi con nuôi 2010)",
    invoke_without_command=True,
)
app = adoption_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — QUẢN LÝ NUÔI CON NUÔI QUỐC GIA[/bold cyan]\n"
            "[dim]Vietnam Child Adoption & 1993 Hague Intercountry Adoption Central Control (Law 52/2010 & Decree 19/2011)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Child Adoption & Child Welfare Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category / Domain", style="bold green")
    table.add_column("Authority / Channel", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Adoption Applications",
        "National Civil System",
        "Total Applications",
        str(status_data.get("total_adoption_applications", 0)),
    )
    table.add_row(
        "Domestic Adoptions",
        "Commune People's Committee (UBND cấp xã)",
        "Domestic Adoptions",
        str(status_data.get("domestic_adoptions", 0)),
    )
    table.add_row(
        "Intercountry Adoptions",
        "Dept of Child Adoption - MOJ (Cục Con nuôi)",
        "Intercountry Adoptions",
        str(status_data.get("intercountry_adoptions", 0)),
    )
    table.add_row(
        "Completed Registrations",
        "Official Register Books",
        "Completed Registrations",
        str(status_data.get("completed_registrations", 0)),
    )
    table.add_row(
        "Hague Convention",
        "1993 Hague Convention Accredited",
        "Hague Dossiers Processed",
        str(status_data.get("hague_dossiers_processed", 0)),
    )
    table.add_row(
        "Post-Placement",
        "3-Year Semi-Annual Monitoring",
        "Reports Filed",
        str(status_data.get("post_placement_reports_filed", 0)),
    )
    table.add_row(
        "Child Welfare",
        "Physical & Psychological Adaptation",
        "Thriving Assessments",
        str(status_data.get("thriving_children_assessments", 0)),
    )
    table.add_row(
        "Certificates",
        "Official MOJ Certificates",
        "Valid Certificates",
        str(status_data.get("valid_adoption_certificates", 0)),
    )
    table.add_row(
        "Judicial Terminations",
        "People's Court Judgments",
        "Court Terminations",
        str(status_data.get("court_terminations", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@adoption_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Child Adoption & Hague Intercountry Central Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = AdoptionEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@adoption_app.command("apply")
def apply_cmd(
    adoption_type: str = typer.Option("DOMESTIC", "--type", "-t", help="Type: DOMESTIC | INTERCOUNTRY"),
    adopter: str = typer.Option(..., "--adopter", "-a", help="Full legal name of the primary adopter"),
    adopter_dob: str = typer.Option(..., "--adopter-dob", help="Adopter date of birth (YYYY-MM-DD)"),
    adopter_id: str = typer.Option(..., "--adopter-id", help="Adopter citizen ID or passport number"),
    child: str = typer.Option(..., "--child", "-c", help="Full legal name of the child"),
    child_dob: str = typer.Option(..., "--child-dob", help="Child date of birth (YYYY-MM-DD)"),
    child_gender: str = typer.Option("MALE", "--gender", "-g", help="Gender: MALE | FEMALE"),
    child_origin: str = typer.Option(..., "--origin", "-o", help="Origin: nurturing center, hospital, or parental residence"),
    relationship: str = typer.Option("UNRELATED", "--rel", "-r", help="Relationship: UNRELATED | STEP_PARENT | NATURAL_AUNT_UNCLE"),
    adopter_nat: str = typer.Option("Việt Nam", "--adopter-nat", help="Adopter nationality"),
    marital_status: str = typer.Option("MARRIED", "--marital", help="Adopter marital status: MARRIED | SINGLE"),
    co_adopter: Optional[str] = typer.Option(None, "--co-adopter", help="Full name of spouse/co-adopter"),
    co_adopter_dob: Optional[str] = typer.Option(None, "--co-adopter-dob", help="Co-adopter date of birth"),
    co_adopter_id: Optional[str] = typer.Option(None, "--co-adopter-id", help="Co-adopter ID number"),
    parents_consent: bool = typer.Option(True, "--parents-consent/--no-parents-consent", help="Consent of biological parents/guardian"),
    child_consent: bool = typer.Option(True, "--child-consent/--no-child-consent", help="Consent of child if 9 years or older"),
    authority: Optional[str] = typer.Option(None, "--authority", help="Competent registration authority"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register and validate child adoption application under Law on Adoption 2010."""
    try:
        engine = AdoptionEngine()
        result = engine.apply_adoption(
            adoption_type=adoption_type,
            adopter_name=adopter,
            adopter_dob=adopter_dob,
            adopter_id=adopter_id,
            child_name=child,
            child_dob=child_dob,
            child_gender=child_gender,
            child_origin=child_origin,
            relationship=relationship,
            adopter_nationality=adopter_nat,
            adopter_marital_status=marital_status,
            co_adopter_name=co_adopter,
            co_adopter_dob=co_adopter_dob,
            co_adopter_id=co_adopter_id,
            biological_parents_consent=parents_consent,
            child_consent=child_consent,
            competent_authority=authority,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Adoption Application Registered:[/bold green] [cyan]{result['application_id']}[/cyan]")
        console.print(f"  [bold]Type:[/bold] {result['adoption_type']} | [bold]Relationship:[/bold] {result['relationship']}")
        console.print(f"  [bold]Adopter:[/bold] {result['adopter_name']} ({result['adopter_nationality']}, DOB: {result['adopter_dob']})")
        if result.get("co_adopter_name"):
            console.print(f"  [bold]Co-Adopter (Spouse):[/bold] {result['co_adopter_name']}")
        console.print(f"  [bold]Child:[/bold] {result['child_name']} ({result['child_gender']}, DOB: {result['child_dob']})")
        console.print(f"  [bold]Origin:[/bold] {result['child_origin']}")
        console.print(f"  [bold]Authority:[/bold] {result['competent_authority']}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error registering adoption application:[/bold red] {e}")
        raise typer.Exit(code=1)


@adoption_app.command("intercountry")
def intercountry_cmd(
    app_id: str = typer.Option(..., "--app-id", "-a", help="Adoption application ID"),
    country: str = typer.Option(..., "--country", "-c", help="Foreign receiving country"),
    central_authority: str = typer.Option(..., "--central-authority", help="Foreign Central Adoption Authority"),
    agency: str = typer.Option(..., "--agency", help="Accredited foreign adoption agency in Vietnam"),
    home_study: str = typer.Option(..., "--home-study", help="Date of foreign home study report (YYYY-MM-DD)"),
    dept_approval: str = typer.Option(..., "--dept-approval", help="Child Adoption Department (BTP) approval number"),
    provincial_decision: str = typer.Option(..., "--provincial-decision", help="Provincial People's Committee adoption decision number"),
    hague: bool = typer.Option(True, "--hague/--no-hague", help="Hague Adoption Convention compliant"),
    handover_date: Optional[str] = typer.Option(None, "--handover-date", help="Handover ceremony date (YYYY-MM-DD)"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Process Hague Convention intercountry child adoption dossier."""
    try:
        engine = AdoptionEngine()
        result = engine.process_intercountry(
            application_id=app_id,
            foreign_country=country,
            foreign_central_authority=central_authority,
            accredited_adoption_agency=agency,
            home_study_date=home_study,
            department_approval_number=dept_approval,
            provincial_decision_number=provincial_decision,
            hague_compliant=hague,
            handover_date=handover_date,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Hague Intercountry Dossier Approved:[/bold green] [cyan]{result['dossier_id']}[/cyan]")
        console.print(f"  [bold]Application ID:[/bold] {result['application_id']}")
        console.print(f"  [bold]Receiving Country:[/bold] {result['foreign_country']} (Hague Compliant: {'Yes' if result['hague_compliant'] else 'No'})")
        console.print(f"  [bold]Accredited Agency:[/bold] {result['accredited_adoption_agency']}")
        console.print(f"  [bold]Dept Approval No:[/bold] {result['department_approval_number']}")
        console.print(f"  [bold]Provincial Decision No:[/bold] {result['provincial_decision_number']}")
        console.print(f"  [bold]Status:[/bold] [green]{result['status']}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error processing intercountry dossier:[/bold red] {e}")
        raise typer.Exit(code=1)


@adoption_app.command("report")
def report_cmd(
    app_id: str = typer.Option(..., "--app-id", "-a", help="Adoption application ID"),
    period: int = typer.Option(6, "--period", "-p", help="Reporting period in months: 6 | 12 | 18 | 24 | 30 | 36"),
    health: str = typer.Option(..., "--health", help="Child physical health and medical assessment"),
    edu: str = typer.Option(..., "--edu", help="Educational and linguistic adaptation"),
    psych: str = typer.Option(..., "--psych", help="Psychological well-being and family integration"),
    assessor: str = typer.Option(..., "--assessor", help="Full name of social worker / assessor"),
    org: str = typer.Option(..., "--org", help="Assessor organization or social service body"),
    rating: str = typer.Option("GOOD", "--rating", "-r", help="Rating: EXCELLENT | GOOD | SATISFACTORY | CONCERNING"),
    date: Optional[str] = typer.Option(None, "--date", help="Assessment date (YYYY-MM-DD)"),
    recs: str = typer.Option("", "--recs", help="Recommendations and next steps"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Submit post-placement welfare and development report (semi-annual for 3 years)."""
    try:
        engine = AdoptionEngine()
        result = engine.submit_post_placement_report(
            application_id=app_id,
            reporting_period_months=period,
            health_status=health,
            educational_adaptation=edu,
            psychological_state=psych,
            assessor_name=assessor,
            assessor_organization=org,
            welfare_rating=rating,
            assessment_date=date,
            recommendations=recs,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        rating_color = "green" if result["welfare_rating"] in ("EXCELLENT", "GOOD") else ("yellow" if result["welfare_rating"] == "SATISFACTORY" else "red")
        console.print(f"[bold green]✓ Post-Placement Report Filed:[/bold green] [cyan]{result['report_id']}[/cyan]")
        console.print(f"  [bold]Period:[/bold] {result['reporting_period_months']} Months Post-Handover")
        console.print(f"  [bold]Rating:[/bold] [{rating_color}]{result['welfare_rating']}[/{rating_color}]")
        console.print(f"  [bold]Health:[/bold] {result['health_status']}")
        console.print(f"  [bold]Education/Integration:[/bold] {result['educational_adaptation']}")
        console.print(f"  [bold]Assessor:[/bold] {result['assessor_name']} ({result['assessor_organization']})")
    except Exception as e:
        console.print(f"[bold red]Error filing post-placement report:[/bold red] {e}")
        raise typer.Exit(code=1)


@adoption_app.command("certificate")
def certificate_cmd(
    app_id: str = typer.Option(..., "--app-id", "-a", help="Adoption application ID"),
    new_name: Optional[str] = typer.Option(None, "--new-name", "-n", help="Child's new full name post-adoption"),
    authority: str = typer.Option("UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội", "--authority", help="Issuing People's Committee"),
    number: Optional[str] = typer.Option(None, "--number", help="Custom certificate serial number"),
    book: Optional[str] = typer.Option(None, "--book", help="Custom register book serial"),
    date: Optional[str] = typer.Option(None, "--date", help="Date of issuance (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue official Certificate of Adoption (Giấy chứng nhận nuôi con nuôi)."""
    try:
        engine = AdoptionEngine()
        result = engine.issue_adoption_certificate(
            application_id=app_id,
            child_new_name=new_name,
            issuing_authority=authority,
            certificate_number=number,
            book_number=book,
            issue_date=date,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Adoption Certificate Issued:[/bold green] [cyan]{result['certificate_id']}[/cyan]")
        console.print(f"  [bold]Certificate Serial:[/bold] [bold yellow]{result['certificate_number']}[/bold yellow] | [bold]Book:[/bold] {result['book_number']}")
        console.print(f"  [bold]Child Name:[/bold] {result['child_new_name']}")
        console.print(f"  [bold]Adopter:[/bold] {result['adopter_full_name']}")
        console.print(f"  [bold]Digital Token:[/bold] [dim]{result['digital_signature']}[/dim]")
        console.print(f"  [bold]Issuing Authority:[/bold] {result['issuing_authority']} ({result['issue_date']})")
    except Exception as e:
        console.print(f"[bold red]Error issuing adoption certificate:[/bold red] {e}")
        raise typer.Exit(code=1)


@adoption_app.command("terminate")
def terminate_cmd(
    app_id: str = typer.Option(..., "--app-id", "-a", help="Adoption application ID"),
    judgment: str = typer.Option(..., "--judgment", "-j", help="Court judgment number"),
    court: str = typer.Option(..., "--court", "-c", help="Name of deciding People's Court"),
    grounds: str = typer.Option(..., "--grounds", help="Statutory grounds for termination (Điều 25)"),
    custody: str = typer.Option(..., "--custody", help="Child custody arrangement post-termination"),
    date: Optional[str] = typer.Option(None, "--date", help="Termination date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Enforce judicial termination of adoption relationship under Article 25."""
    try:
        engine = AdoptionEngine()
        result = engine.terminate_adoption(
            application_id=app_id,
            court_judgment_number=judgment,
            court_name=court,
            grounds=grounds,
            child_custody_arrangement=custody,
            termination_date=date,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold red]✓ Adoption Terminated Pursuant to Court Judgment:[/bold red] [cyan]{result['termination_id']}[/cyan]")
        console.print(f"  [bold]Application ID:[/bold] {result['application_id']}")
        console.print(f"  [bold]Judgment:[/bold] {result['court_judgment_number']} by {result['court_name']}")
        console.print(f"  [bold]Grounds:[/bold] {result['grounds']}")
        console.print(f"  [bold]Custody Arrangement:[/bold] {result['child_custody_arrangement']}")
        console.print(f"  [bold]Status:[/bold] [red]{result['status']}[/red]")
    except Exception as e:
        console.print(f"[bold red]Error terminating adoption:[/bold red] {e}")
        raise typer.Exit(code=1)


@adoption_app.command("list")
def list_records_cmd(
    category: str = typer.Option("application", "--category", "-c", help="Category: application | intercountry | report | certificate | termination | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List child adoption records by category."""
    try:
        engine = AdoptionEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Adoption Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@adoption_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show Vietnamese child adoption and Hague Convention telemetry."""
    engine = AdoptionEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
