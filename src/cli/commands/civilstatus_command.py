"""
CLI Command Suite for Vietnamese Civil Status, Vital Statistics & Population Registration.
Compliant with:
- Law on Civil Status 2014 (Luật Hộ tịch - Law No. 60/2014/QH13)
- Decree No. 123/2015/ND-CP detailing the implementation of the Law on Civil Status
- Decree No. 87/2020/ND-CP on Electronic Civil Status Database & Shared National Population Database
- Circular No. 04/2020/TT-BTP guiding the Law on Civil Status and Decree No. 123/2015/ND-CP
- Law on Identification 2023 (Law No. 26/2023/QH15) on Personal Identification Numbers (Số định danh cá nhân - DDCN)
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.civilstatus_engine import (
    CivilStatusEngine,
    CivilStatusEventType,
    CompetentLevel,
    RectificationType,
    RegistrationStatus,
)

civilstatus_app = typer.Typer(
    name="civilstatus",
    help="Vietnamese Civil Status, Vital Statistics & Population Registration Suite (Luật Hộ tịch 2014 & Nghị định 123/2015/NĐ-CP)",
    invoke_without_command=True,
)
app = civilstatus_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — QUẢN LÝ HỘ TỊCH & DÂN SỐ QUỐC GIA[/bold cyan]\n"
            "[dim]Vietnam Civil Status, Vital Statistics & National Electronic Population Database (Law 60/2014 & Decree 123/2015)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Civil Status & Vital Statistics Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category / Domain", style="bold green")
    table.add_column("Authority / Channel", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Birth Registrations",
        "National Civil Database",
        "Total Birth Records",
        str(status_data.get("total_birth_registrations", 0)),
    )
    table.add_row(
        "Birth Registrations",
        "Foreign Elements (Art 35)",
        "Foreign-Element Births",
        str(status_data.get("foreign_element_births", 0)),
    )
    table.add_row(
        "Marriage Registrations",
        "UBND Cấp Xã / Cấp Huyện",
        "Total Marriage Records",
        str(status_data.get("total_marriage_registrations", 0)),
    )
    table.add_row(
        "Marriage Registrations",
        "Foreign Elements (Art 37)",
        "Foreign-Element Marriages",
        str(status_data.get("foreign_element_marriages", 0)),
    )
    table.add_row(
        "Death Registrations",
        "Vital Statistics Registry",
        "Total Death Records",
        str(status_data.get("total_death_registrations", 0)),
    )
    table.add_row(
        "Civil Rectifications",
        "Name / Gender / Ethnicity",
        "Approved Rectifications",
        str(status_data.get("approved_rectifications", 0)),
    )
    table.add_row(
        "Electronic Extracts",
        "Decree 87/2020/ND-CP",
        "Valid Digital Extracts",
        str(status_data.get("valid_electronic_extracts", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@civilstatus_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Civil Status & Vital Statistics Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = CivilStatusEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@civilstatus_app.command("birth")
def birth_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Full legal name of the child"),
    gender: str = typer.Option(..., "--gender", "-g", help="Gender: MALE (NAM) | FEMALE (NU)"),
    birth_date: str = typer.Option(..., "--birth-date", "-b", help="Date of birth (YYYY-MM-DD)"),
    birth_place: str = typer.Option(..., "--birth-place", "-p", help="Place of birth (hospital/municipality)"),
    ethnicity: str = typer.Option("Kinh", "--ethnicity", "-e", help="Ethnicity of the child"),
    nationality: str = typer.Option("Việt Nam", "--nationality", help="Nationality of the child"),
    mother: Optional[str] = typer.Option(None, "--mother", help="Full legal name of mother"),
    mother_id: Optional[str] = typer.Option(None, "--mother-id", help="Mother's Citizen ID (12-digit CCCD/DDCN)"),
    father: Optional[str] = typer.Option(None, "--father", help="Full legal name of father"),
    father_id: Optional[str] = typer.Option(None, "--father-id", help="Father's Citizen ID (12-digit CCCD/DDCN)"),
    registrant: str = typer.Option(..., "--registrant", "-r", help="Full name of person requesting registration"),
    authority: str = typer.Option("UBND Phường Hàng Trống, Hoàn Kiếm, Hà Nội", "--authority", help="Competent civil status authority"),
    level: str = typer.Option("COMMUNE", "--level", help="Competent level: COMMUNE | DISTRICT | DIPLOMATIC_MISSION"),
    foreign_element: bool = typer.Option(False, "--foreign-element/--no-foreign-element", help="Involves foreign citizen or overseas element"),
    book_number: Optional[str] = typer.Option(None, "--book-number", help="Registration book number"),
    status: str = typer.Option("REGISTERED", "--status", "-s", help="Status: SUBMITTED | REGISTERED | REJECTED"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register birth and assign personal identification number (DDCN) under Law on Civil Status 2014."""
    try:
        engine = CivilStatusEngine()
        result = engine.register_birth(
            child_name=name,
            gender=gender,
            birth_date=birth_date,
            birth_place=birth_place,
            ethnicity=ethnicity,
            nationality=nationality,
            mother_name=mother,
            mother_citizen_id=mother_id,
            father_name=father,
            father_citizen_id=father_id,
            registrant_name=registrant,
            competent_authority=authority,
            competent_level=level,
            foreign_element=foreign_element,
            book_number=book_number,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        status_color = "green" if result["status"] == "REGISTERED" else ("yellow" if result["status"] == "SUBMITTED" else "red")
        console.print(f"[bold green]✓ Birth Registration Completed:[/bold green] [cyan]{result['registration_id']}[/cyan]")
        console.print(f"  [bold]Child Name:[/bold] {result['child_name']} ({result['gender']}) | [bold]DOB:[/bold] {result['birth_date']}")
        console.print(f"  [bold]Personal ID Number (Số ĐDCN):[/bold] [bold yellow]{result['personal_id_number']}[/bold yellow]")
        console.print(f"  [bold]Place of Birth:[/bold] {result['birth_place']}")
        console.print(f"  [bold]Parents:[/bold] Mother: {result.get('mother_name') or 'N/A'} | Father: {result.get('father_name') or 'N/A'}")
        console.print(f"  [bold]Authority:[/bold] {result['competent_authority']} ({result['competent_level']})")
        console.print(f"  [bold]Book Number:[/bold] {result['book_number']} | [bold]Status:[/bold] [{status_color}]{result['status']}[/{status_color}]")
    except Exception as e:
        console.print(f"[bold red]Error registering birth:[/bold red] {e}")
        raise typer.Exit(code=1)


@civilstatus_app.command("marriage")
def marriage_cmd(
    male_name: str = typer.Option(..., "--husband", "-m", help="Full name of male partner"),
    male_dob: str = typer.Option(..., "--husband-dob", help="Male partner date of birth (YYYY-MM-DD)"),
    male_id: str = typer.Option(..., "--husband-id", help="Male partner CCCD or passport number"),
    male_nationality: str = typer.Option("Việt Nam", "--husband-nat", help="Male partner nationality"),
    female_name: str = typer.Option(..., "--wife", "-f", help="Full name of female partner"),
    female_dob: str = typer.Option(..., "--wife-dob", help="Female partner date of birth (YYYY-MM-DD)"),
    female_id: str = typer.Option(..., "--wife-id", help="Female partner CCCD or passport number"),
    female_nationality: str = typer.Option("Việt Nam", "--wife-nat", help="Female partner nationality"),
    reg_date: Optional[str] = typer.Option(None, "--reg-date", "-d", help="Registration date (YYYY-MM-DD)"),
    authority: str = typer.Option("UBND Phường Hàng Bài, Hoàn Kiếm, Hà Nội", "--authority", help="Competent registration authority"),
    level: str = typer.Option("COMMUNE", "--level", help="Competent level: COMMUNE | DISTRICT | DIPLOMATIC_MISSION"),
    foreign_element: bool = typer.Option(False, "--foreign-element/--no-foreign-element", help="Involves foreign citizen or overseas element"),
    cert_number: Optional[str] = typer.Option(None, "--cert-number", help="Marriage certificate serial number"),
    book_number: Optional[str] = typer.Option(None, "--book-number", help="Marriage registration book number"),
    status: str = typer.Option("REGISTERED", "--status", "-s", help="Status: SUBMITTED | REGISTERED | REJECTED"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register civil marriage under Article 17-18 or Article 37-38 (Foreign element)."""
    try:
        engine = CivilStatusEngine()
        result = engine.register_marriage(
            male_name=male_name,
            male_birth_date=male_dob,
            male_citizen_id=male_id,
            male_nationality=male_nationality,
            female_name=female_name,
            female_birth_date=female_dob,
            female_citizen_id=female_id,
            female_nationality=female_nationality,
            registration_date=reg_date,
            competent_authority=authority,
            competent_level=level,
            foreign_element=foreign_element,
            certificate_number=cert_number,
            book_number=book_number,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Marriage Registered Successfully:[/bold green] [cyan]{result['registration_id']}[/cyan]")
        console.print(f"  [bold]Husband:[/bold] {result['male_name']} ({result['male_nationality']}, DOB: {result['male_birth_date']})")
        console.print(f"  [bold]Wife:[/bold] {result['female_name']} ({result['female_nationality']}, DOB: {result['female_birth_date']})")
        console.print(f"  [bold]Certificate No:[/bold] [bold yellow]{result['certificate_number']}[/bold yellow] | [bold]Book:[/bold] {result['book_number']}")
        console.print(f"  [bold]Authority:[/bold] {result['competent_authority']} ({result['competent_level']})")
        console.print(f"  [bold]Registration Date:[/bold] {result['registration_date']}")
    except Exception as e:
        console.print(f"[bold red]Error registering marriage:[/bold red] {e}")
        raise typer.Exit(code=1)


@civilstatus_app.command("death")
def death_cmd(
    deceased: str = typer.Option(..., "--deceased", "-d", help="Full name of deceased person"),
    gender: str = typer.Option(..., "--gender", "-g", help="Gender: MALE | FEMALE"),
    birth_date: str = typer.Option(..., "--birth-date", "-b", help="Date of birth (YYYY-MM-DD)"),
    death_date: str = typer.Option(..., "--death-date", help="Date of death (YYYY-MM-DD)"),
    death_place: str = typer.Option(..., "--death-place", help="Place of death"),
    cause: str = typer.Option(..., "--cause", help="Cause of death"),
    informant: str = typer.Option(..., "--informant", "-i", help="Full name of informant / person reporting"),
    authority: str = typer.Option("UBND Phường Hàng Gai, Hoàn Kiếm, Hà Nội", "--authority", help="Competent civil status authority"),
    citizen_id: Optional[str] = typer.Option(None, "--citizen-id", help="Deceased person's CCCD / ID number"),
    cert_number: Optional[str] = typer.Option(None, "--cert-number", help="Death certificate number"),
    book_number: Optional[str] = typer.Option(None, "--book-number", help="Death register book number"),
    status: str = typer.Option("REGISTERED", "--status", "-s", help="Status: SUBMITTED | REGISTERED"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register death and issue death certificate under Article 32-34."""
    try:
        engine = CivilStatusEngine()
        result = engine.register_death(
            deceased_name=deceased,
            gender=gender,
            birth_date=birth_date,
            death_date=death_date,
            death_place=death_place,
            cause_of_death=cause,
            informant_name=informant,
            competent_authority=authority,
            citizen_id=citizen_id,
            certificate_number=cert_number,
            book_number=book_number,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Death Registration Completed:[/bold green] [cyan]{result['registration_id']}[/cyan]")
        console.print(f"  [bold]Deceased:[/bold] {result['deceased_name']} ({result['gender']}, DOB: {result['birth_date']})")
        console.print(f"  [bold]Death Details:[/bold] {result['death_date']} at {result['death_place']}")
        console.print(f"  [bold]Cause:[/bold] {result['cause_of_death']}")
        console.print(f"  [bold]Certificate No:[/bold] [bold yellow]{result['death_certificate_number']}[/bold yellow] | [bold]Book:[/bold] {result['book_number']}")
        console.print(f"  [bold]Informant:[/bold] {result['informant_name']} | [bold]Authority:[/bold] {result['competent_authority']}")
    except Exception as e:
        console.print(f"[bold red]Error registering death:[/bold red] {e}")
        raise typer.Exit(code=1)


@civilstatus_app.command("rectify")
def rectify_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Full name of person requesting rectification"),
    citizen_id: str = typer.Option(..., "--citizen-id", "-c", help="Citizen ID number (12-digit CCCD)"),
    rect_type: str = typer.Option("NAME_CHANGE", "--type", "-t", help="Type: NAME_CHANGE | ETHNICITY | GENDER_CHANGE | ERROR_CORRECTION"),
    original: str = typer.Option(..., "--original", "-o", help="Original recorded content in civil registry"),
    corrected: str = typer.Option(..., "--corrected", help="Corrected / amended content"),
    legal_basis: str = typer.Option(..., "--legal-basis", help="Legal basis / statutory justification"),
    decision: str = typer.Option(..., "--decision", help="Official decision / decree number"),
    authority: str = typer.Option("UBND Quận Hoàn Kiếm, Hà Nội", "--authority", help="Competent judicial authority"),
    decision_date: Optional[str] = typer.Option(None, "--decision-date", help="Decision date (YYYY-MM-DD)"),
    status: str = typer.Option("APPROVED", "--status", help="Status: APPROVED | PENDING | REJECTED"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Rectify, change, or correct civil status record under Article 26-28."""
    try:
        engine = CivilStatusEngine()
        result = engine.rectify_civil_status(
            person_name=name,
            citizen_id=citizen_id,
            rectification_type=rect_type,
            original_content=original,
            corrected_content=corrected,
            legal_basis=legal_basis,
            decision_number=decision,
            competent_authority=authority,
            decision_date=decision_date,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Civil Status Rectification Recorded:[/bold green] [cyan]{result['rectification_id']}[/cyan]")
        console.print(f"  [bold]Person:[/bold] {result['person_name']} | [bold]CCCD:[/bold] {result['citizen_id']}")
        console.print(f"  [bold]Type:[/bold] {result['rectification_type']}")
        console.print(f"  [bold]Original:[/bold] [red]{result['original_content']}[/red] -> [bold]Corrected:[/bold] [green]{result['corrected_content']}[/green]")
        console.print(f"  [bold]Decision:[/bold] {result['decision_number']} ({result['decision_date']}) by {result['competent_authority']}")
    except Exception as e:
        console.print(f"[bold red]Error recording rectification:[/bold red] {e}")
        raise typer.Exit(code=1)


@civilstatus_app.command("extract")
def extract_cmd(
    event_type: str = typer.Option("BIRTH", "--type", "-t", help="Event type: BIRTH | MARRIAGE | DEATH | RECTIFICATION"),
    record_id: str = typer.Option(..., "--record-id", "-r", help="Source civil status record registration ID"),
    name: str = typer.Option(..., "--name", "-n", help="Subject full name"),
    authority: str = typer.Option("Sở Tư pháp TP Hà Nội", "--authority", help="Issuing department/office"),
    extract_number: Optional[str] = typer.Option(None, "--number", help="Custom extract serial number"),
    issue_date: Optional[str] = typer.Option(None, "--date", help="Issue date (YYYY-MM-DD)"),
    status: str = typer.Option("VALID", "--status", help="Status: VALID | REVOKED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue verified digital extract of civil status record under Decree 87/2020/ND-CP."""
    try:
        engine = CivilStatusEngine()
        result = engine.issue_extract(
            event_type=event_type,
            source_record_id=record_id,
            subject_name=name,
            issuing_authority=authority,
            extract_number=extract_number,
            issue_date=issue_date,
            status=status,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Digital Extract Issued:[/bold green] [cyan]{result['extract_id']}[/cyan]")
        console.print(f"  [bold]Event Type:[/bold] {result['event_type']} | [bold]Subject:[/bold] {result['subject_name']}")
        console.print(f"  [bold]Source Record:[/bold] {result['source_record_id']}")
        console.print(f"  [bold]Extract Serial:[/bold] [bold yellow]{result['extract_number']}[/bold yellow]")
        console.print(f"  [bold]Digital Signature:[/bold] [dim]{result['digital_signature']}[/dim]")
        console.print(f"  [bold]Issuing Authority:[/bold] {result['issuing_authority']} (Issued: {result['issue_date']})")
    except Exception as e:
        console.print(f"[bold red]Error issuing extract:[/bold red] {e}")
        raise typer.Exit(code=1)


@civilstatus_app.command("list")
def list_records_cmd(
    category: str = typer.Option("birth", "--category", "-c", help="Category: birth | marriage | death | rectification | paternity | extract | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List civil status and vital statistics records by category."""
    try:
        engine = CivilStatusEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Civil Status Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@civilstatus_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show Vietnamese civil status and vital statistics telemetry."""
    engine = CivilStatusEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
