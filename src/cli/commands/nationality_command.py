"""
CLI Command Suite for Vietnamese Nationality, Naturalization, Renunciation & Dual Citizenship.
Compliant with:
- Law on Vietnamese Nationality 2008 (Luật Quốc tịch Việt Nam - Law No. 24/2008/QH12)
- Law Amending and Supplementing Law on Vietnamese Nationality 2014 (Law No. 56/2014/QH13)
- Decree No. 16/2020/ND-CP & Circular No. 02/2020/TT-BTP
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.nationality_engine import (
    NationalityEngine,
    NaturalizationExemption,
    DualNationalityPermission,
    RenunciationBar,
    NationalityStatus,
)

nationality_app = typer.Typer(
    name="nationality",
    help="Vietnamese Nationality, Naturalization, Renunciation & Dual Citizenship Suite (Luật Quốc tịch Việt Nam 2008/2014)",
    invoke_without_command=True,
)
app = nationality_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — QUẢN LÝ QUỐC TỊCH & NHẬP TỊCH[/bold cyan]\n"
            "[dim]Vietnamese Nationality, Naturalization & Dual Citizenship Hub (Luật Quốc tịch 2008/2014 & NĐ 16/2020/NĐ-CP)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Vietnamese Nationality Affairs Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category / Process", style="bold green")
    table.add_column("Competent Body", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Naturalization (Nhập quốc tịch)",
        "Ministry of Justice / State President",
        "Total Dossiers",
        str(status_data.get("total_naturalization_dossiers", 0)),
    )
    table.add_row(
        "Naturalization (Nhập quốc tịch)",
        "State President (Chủ tịch nước)",
        "Decreed Naturalizations",
        str(status_data.get("decreed_naturalizations", 0)),
    )
    table.add_row(
        "Renunciation (Thôi quốc tịch)",
        "Ministry of Justice / State President",
        "Total Dossiers",
        str(status_data.get("total_renunciation_dossiers", 0)),
    )
    table.add_row(
        "Renunciation (Thôi quốc tịch)",
        "Statutory Bars (Art 27)",
        "Barred Renunciations",
        str(status_data.get("barred_renunciations", 0)),
    )
    table.add_row(
        "Restoration (Trở lại quốc tịch)",
        "Ministry of Justice / State President",
        "Total Dossiers",
        str(status_data.get("total_restoration_dossiers", 0)),
    )
    table.add_row(
        "Restoration (Trở lại quốc tịch)",
        "State President (Chủ tịch nước)",
        "Decreed Restorations",
        str(status_data.get("decreed_restorations", 0)),
    )
    table.add_row(
        "Nationality Certificates",
        "Department of Justice / Diplomatic Missions",
        "Valid Certificates",
        str(status_data.get("valid_nationality_certificates", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@nationality_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Nationality Affairs Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = NationalityEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@nationality_app.command("naturalize")
def naturalize_cmd(
    applicant: str = typer.Option(..., "--applicant", "-a", help="Full legal name of the naturalization applicant"),
    chosen_name: str = typer.Option(..., "--chosen-name", "-n", help="Chosen Vietnamese name (mandatory under Art 19 k3)"),
    birth_date: str = typer.Option(..., "--birth-date", help="Applicant's date of birth (YYYY-MM-DD)"),
    nationality: str = typer.Option(..., "--nationality", help="Applicant's current nationality"),
    residence_years: float = typer.Option(5.0, "--residence-years", help="Years of permanent residence in Vietnam (minimum 5 yrs unless exempted)"),
    proficiency: bool = typer.Option(True, "--proficiency/--no-proficiency", help="Knowing Vietnamese sufficiently to integrate (Art 19 k1c)"),
    livelihood: bool = typer.Option(True, "--livelihood/--no-livelihood", help="Capable of ensuring livelihood in Vietnam (Art 19 k1đ)"),
    exemption: str = typer.Option("NONE", "--exemption", "-e", help="Exemption category: NONE | SPOUSE_PARENT_CHILD | SPECIAL_MERIT | BENEFICIAL_TO_STATE"),
    dual_permit: str = typer.Option("RENUNCIATION_REQUIRED", "--dual-permit", help="Dual nationality permit: RENUNCIATION_REQUIRED | SPECIAL_PRESIDENTIAL_PERMIT"),
    decision_no: Optional[str] = typer.Option(None, "--decision-no", help="Presidential Decision decree number"),
    decision_date: Optional[str] = typer.Option(None, "--decision-date", help="Date of Presidential Decision"),
    status: str = typer.Option("DOSSIER_SUBMITTED", "--status", "-s", help="Dossier status"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks and notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Process and evaluate Naturalization in Vietnam under Article 19."""
    try:
        engine = NationalityEngine()
        result = engine.process_naturalization(
            applicant_name=applicant,
            vietnamese_chosen_name=chosen_name,
            birth_date=birth_date,
            current_nationality=nationality,
            residence_years=residence_years,
            vietnamese_proficiency=proficiency,
            livelihood_assured=livelihood,
            exemption=exemption,
            dual_nationality_permit=dual_permit,
            presidential_decision_no=decision_no,
            decision_date=decision_date,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Naturalization Dossier Evaluated:[/bold green] [cyan]{result['dossier_id']}[/cyan]")
        console.print(f"  [bold]Applicant:[/bold] {result['applicant_name']} -> [bold green]{result['vietnamese_chosen_name']}[/bold green]")
        console.print(f"  [bold]Current Nationality:[/bold] {result['current_nationality']} | [bold]Resided:[/bold] {result['residence_years']} years")
        console.print(f"  [bold]Exemption Category:[/bold] {result['exemption_category']} | [bold]Dual Permit:[/bold] {result['dual_nationality_permit']}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
        if result["notes"]:
            console.print(f"  [bold]Remarks:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing naturalization:[/bold red] {e}")
        raise typer.Exit(code=1)


@nationality_app.command("renounce")
def renounce_cmd(
    applicant: str = typer.Option(..., "--applicant", "-a", help="Full name of applicant seeking renunciation of Vietnamese nationality"),
    birth_date: str = typer.Option(..., "--birth-date", help="Applicant's date of birth (YYYY-MM-DD)"),
    target_country: str = typer.Option(..., "--target-country", "-t", help="Target foreign country to acquire nationality"),
    tax_cleared: bool = typer.Option(True, "--tax-cleared/--tax-pending", help="State tax and property obligations cleared (Art 27 k2a)"),
    criminal_pending: bool = typer.Option(False, "--criminal-pending/--no-criminal-pending", help="Under criminal prosecution (Art 27 k2b)"),
    judgment_pending: bool = typer.Option(False, "--judgment-pending/--no-judgment-pending", help="Court judgment/ruling execution pending (Art 27 k2c)"),
    security_cleared: bool = typer.Option(True, "--security-cleared/--security-hazard", help="Clear of prejudice to national security (Art 27 k3)"),
    decision_no: Optional[str] = typer.Option(None, "--decision-no", help="Presidential Decision decree number"),
    decision_date: Optional[str] = typer.Option(None, "--decision-date", help="Date of Presidential Decision"),
    status: str = typer.Option("DOSSIER_SUBMITTED", "--status", "-s", help="Dossier status"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks and notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Process and evaluate Renunciation of Vietnamese Nationality under Article 27."""
    try:
        engine = NationalityEngine()
        result = engine.process_renunciation(
            applicant_name=applicant,
            birth_date=birth_date,
            target_foreign_country=target_country,
            tax_debt_cleared=tax_cleared,
            criminal_prosecution_pending=criminal_pending,
            judgment_execution_pending=judgment_pending,
            national_security_clearance=security_cleared,
            presidential_decision_no=decision_no,
            decision_date=decision_date,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        bar = result["renunciation_bar"]
        bar_color = "red" if bar != "NONE" else "green"
        console.print(f"[bold green]✓ Renunciation Dossier Evaluated:[/bold green] [cyan]{result['dossier_id']}[/cyan]")
        console.print(f"  [bold]Applicant:[/bold] {result['applicant_name']} | [bold]Target Country:[/bold] {result['target_foreign_country']}")
        console.print(f"  [bold]Statutory Bar (Art 27):[/bold] [{bar_color}]{bar}[/{bar_color}]")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
        if result["notes"]:
            console.print(f"  [bold]Remarks:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing renunciation:[/bold red] {e}")
        raise typer.Exit(code=1)


@nationality_app.command("restore")
def restore_cmd(
    applicant: str = typer.Option(..., "--applicant", "-a", help="Full name of applicant seeking restoration of Vietnamese nationality"),
    birth_date: str = typer.Option(..., "--birth-date", help="Applicant's date of birth (YYYY-MM-DD)"),
    former_status: str = typer.Option(..., "--former-status", help="Proof of former Vietnamese nationality (e.g. Birth Certificate, Old Passport)"),
    ground: str = typer.Option(..., "--ground", "-g", help="Ground for restoration (family tie, repatriation, investment, national merit)"),
    nationality: str = typer.Option(..., "--nationality", help="Applicant's current foreign nationality"),
    decision_no: Optional[str] = typer.Option(None, "--decision-no", help="Presidential Decision decree number"),
    decision_date: Optional[str] = typer.Option(None, "--decision-date", help="Date of Presidential Decision"),
    status: str = typer.Option("DOSSIER_SUBMITTED", "--status", "-s", help="Dossier status"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks and notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Process Restoration of Vietnamese Nationality under Article 23."""
    try:
        engine = NationalityEngine()
        result = engine.process_restoration(
            applicant_name=applicant,
            birth_date=birth_date,
            former_vietnamese_status=former_status,
            restoration_ground=ground,
            current_nationality=nationality,
            presidential_decision_no=decision_no,
            decision_date=decision_date,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Restoration Dossier Processed:[/bold green] [cyan]{result['dossier_id']}[/cyan]")
        console.print(f"  [bold]Applicant:[/bold] {result['applicant_name']} | [bold]Current Nationality:[/bold] {result['current_nationality']}")
        console.print(f"  [bold]Former Status Proof:[/bold] {result['former_vietnamese_status']}")
        console.print(f"  [bold]Restoration Ground:[/bold] {result['restoration_ground']}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error processing restoration:[/bold red] {e}")
        raise typer.Exit(code=1)


@nationality_app.command("certificate")
def certificate_cmd(
    applicant: str = typer.Option(..., "--applicant", "-a", help="Full name of certificate holder"),
    id_type: str = typer.Option("PASSPORT", "--id-type", help="Identification type: PASSPORT | CCCD | BIRTH_CERT"),
    id_number: str = typer.Option(..., "--id-number", help="Identification document number"),
    residence: str = typer.Option("OVERSEAS_VIETNAMESE", "--residence", help="Residence status: OVERSEAS_VIETNAMESE | DOMESTIC"),
    authority: str = typer.Option(..., "--authority", help="Issuing authority (e.g. Sở Tư pháp Hà Nội / ĐSQ Việt Nam tại Hoa Kỳ)"),
    cert_no: str = typer.Option(..., "--cert-no", "-c", help="Official certificate number (e.g. 102/2026/GXN-QT)"),
    issue_date: str = typer.Option(..., "--issue-date", help="Date of issuance (YYYY-MM-DD)"),
    status: str = typer.Option("VALID", "--status", "-s", help="Certificate status"),
    notes: str = typer.Option("", "--notes", help="Certificate notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue or register Certificate of Vietnamese Nationality under Decree 16/2020/ND-CP."""
    try:
        engine = NationalityEngine()
        result = engine.issue_nationality_certificate(
            applicant_name=applicant,
            identity_type=id_type,
            identity_number=id_number,
            residence_status=residence,
            issuing_authority=authority,
            certificate_number=cert_no,
            issue_date=issue_date,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Nationality Certificate Registered:[/bold green] [cyan]{result['cert_id']}[/cyan]")
        console.print(f"  [bold]Holder:[/bold] {result['applicant_name']} | [bold]Certificate No:[/bold] {result['certificate_number']}")
        console.print(f"  [bold]ID:[/bold] {result['identity_type']} ({result['identity_number']})")
        console.print(f"  [bold]Authority:[/bold] {result['issuing_authority']} | [bold]Date:[/bold] {result['issue_date']}")
        console.print(f"  [bold]Status:[/bold] [green]{result['status']}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error issuing nationality certificate:[/bold red] {e}")
        raise typer.Exit(code=1)


@nationality_app.command("list")
def list_records_cmd(
    category: str = typer.Option("naturalization", "--category", "-c", help="Category: naturalization | renunciation | restoration | certificate | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List nationality affairs records by category."""
    try:
        engine = NationalityEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Nationality Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@nationality_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show Vietnamese nationality affairs telemetry and system status."""
    engine = NationalityEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
