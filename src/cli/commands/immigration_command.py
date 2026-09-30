"""
CLI Command Suite for Vietnamese Immigration, Entry, Exit, Transit, Residence & Visa Management.
Compliant with:
- Law on Entry, Exit, Transit, and Residence of Foreigners in Vietnam (Law 47/2014 & Law 23/2023)
- Law on Exit and Entry of Vietnamese Citizens (Law 49/2019 & Law 23/2023)
- Decree No. 75/2020/ND-CP & Decree No. 127/2024/ND-CP
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.immigration_engine import (
    ImmigrationEngine,
    VisaType,
    ResidenceCardType,
    MovementDirection,
    BorderGateType,
    RestrictionType,
    PassportType,
    ImmigrationStatus,
)

immigration_app = typer.Typer(
    name="immigration",
    help="Vietnamese Immigration, Entry/Exit, Residence & Visa Management Suite (Luật Xuất nhập cảnh & Cư trú 2014/2023)",
    invoke_without_command=True,
)
app = immigration_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — QUẢN LÝ XUẤT NHẬP CẢNH & CƯ TRÚ[/bold cyan]\n"
            "[dim]Vietnam Immigration, Border Control & Citizen Passport Control Plane (Law 47/2014 & Law 23/2023)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Immigration & Border Affairs Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category / Domain", style="bold green")
    table.add_column("Authority / Channel", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Foreigner Visas",
        "Immigration Dept (Cục QLXNC)",
        "Total Visa Applications",
        str(status_data.get("total_visa_applications", 0)),
    )
    table.add_row(
        "Foreigner Visas",
        "Active / Granted",
        "Active Granted Visas",
        str(status_data.get("active_granted_visas", 0)),
    )
    table.add_row(
        "Residence Cards",
        "TRC (Thẻ tạm trú 1-5 yrs)",
        "Active TRC Cards",
        str(status_data.get("active_trc_cards", 0)),
    )
    table.add_row(
        "Residence Cards",
        "PRC (Thẻ thường trú)",
        "Active PRC Cards",
        str(status_data.get("active_prc_cards", 0)),
    )
    table.add_row(
        "Border Movements",
        "International Border Gates",
        "Total Crossings",
        str(status_data.get("total_border_movements", 0)),
    )
    table.add_row(
        "Border Movements",
        "Cleared Passages",
        "Cleared Movements",
        str(status_data.get("cleared_movements", 0)),
    )
    table.add_row(
        "Border Movements",
        "Security Interceptions",
        "Intercepted Movements",
        str(status_data.get("intercepted_movements", 0)),
    )
    table.add_row(
        "Border Movements",
        "Autogates (Cổng tự động)",
        "Autogate Passages",
        str(status_data.get("autogate_movements", 0)),
    )
    table.add_row(
        "Restrictions",
        "Entry Suspensions & Exit Postponements",
        "Active Orders",
        str(status_data.get("active_restriction_orders", 0)),
    )
    table.add_row(
        "Citizen Passports",
        "E-Passports with Chip",
        "Chip Passports",
        str(status_data.get("electronic_chip_passports", 0)),
    )
    table.add_row(
        "Citizen Passports",
        "Autogate Enrolled Citizens",
        "Autogate Citizens",
        str(status_data.get("autogate_enrolled_citizens", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@immigration_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Immigration & Border Control Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = ImmigrationEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@immigration_app.command("visa")
def visa_cmd(
    applicant: str = typer.Option(..., "--applicant", "-a", help="Full legal name of the foreign applicant"),
    nationality: str = typer.Option(..., "--nationality", help="Foreign applicant's nationality"),
    passport_number: str = typer.Option(..., "--passport-number", "-p", help="Foreign passport number"),
    passport_expiry: str = typer.Option(..., "--passport-expiry", help="Passport expiration date (YYYY-MM-DD)"),
    visa_type: str = typer.Option("EV", "--visa-type", "-t", help="Visa category: EV | DL | DN1 | DN2 | DT1 | DT2 | DT3 | DT4 | LD1 | LD2 | TT | DH | NG"),
    duration_days: int = typer.Option(90, "--duration-days", "-d", help="Visa duration in days (e.g. 90 for EV)"),
    entries: str = typer.Option("SINGLE", "--entries", help="Entries allowed: SINGLE | MULTIPLE"),
    sponsor: Optional[str] = typer.Option(None, "--sponsor", help="Inviting or sponsoring agency / organization"),
    port: str = typer.Option("Noi Bai International Airport", "--port", help="Intended international port of entry"),
    valid_from: Optional[str] = typer.Option(None, "--valid-from", help="Start date of visa validity (YYYY-MM-DD)"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Dossier status: SUBMITTED | GRANTED | REJECTED"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or evaluate foreigner visa application under Law 47/2014 & Law 23/2023."""
    try:
        engine = ImmigrationEngine()
        result = engine.apply_visa(
            applicant_name=applicant,
            nationality=nationality,
            passport_number=passport_number,
            passport_expiry=passport_expiry,
            visa_type=visa_type,
            duration_days=duration_days,
            entries_allowed=entries,
            inviting_organization=sponsor,
            port_of_entry=port,
            valid_from=valid_from,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        status_color = "green" if result["status"] == "GRANTED" else ("yellow" if result["status"] == "SUBMITTED" else "red")
        console.print(f"[bold green]✓ Visa Application Processed:[/bold green] [cyan]{result['visa_id']}[/cyan]")
        console.print(f"  [bold]Applicant:[/bold] {result['applicant_name']} ({result['nationality']})")
        console.print(f"  [bold]Passport:[/bold] {result['passport_number']} (Exp: {result['passport_expiry']})")
        console.print(f"  [bold]Type:[/bold] {result['visa_type']} | [bold]Duration:[/bold] {result['duration_days']} days ({result['entries_allowed']})")
        console.print(f"  [bold]Valid:[/bold] {result['valid_from']} -> {result['valid_until']}")
        console.print(f"  [bold]Status:[/bold] [{status_color}]{result['status']}[/{status_color}]")
        if result["notes"]:
            console.print(f"  [bold]Remarks:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing visa application:[/bold red] {e}")
        raise typer.Exit(code=1)


@immigration_app.command("residence")
def residence_cmd(
    holder: str = typer.Option(..., "--holder", "-h", help="Full name of card holder"),
    nationality: str = typer.Option(..., "--nationality", help="Holder's nationality"),
    passport_number: str = typer.Option(..., "--passport-number", "-p", help="Foreign passport number"),
    card_type: str = typer.Option("TRC", "--card-type", "-t", help="Card type: TRC (Temporary) | PRC (Permanent)"),
    symbol: str = typer.Option("DT1", "--symbol", "-s", help="Symbol category: DT1 | DT2 | DT3 | LD1 | LD2 | TT"),
    duration_months: int = typer.Option(36, "--duration-months", "-d", help="Validity period in months (1-120)"),
    sponsor: str = typer.Option(..., "--sponsor", help="Sponsoring enterprise or Vietnamese family sponsor"),
    address: str = typer.Option(..., "--address", help="Residential address in Vietnam"),
    issue_date: Optional[str] = typer.Option(None, "--issue-date", help="Date of issuance (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="Card status: ACTIVE | EXPIRED | REVOKED"),
    notes: str = typer.Option("", "--notes", help="Card notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue or manage Temporary (TRC) or Permanent (PRC) Residence Card."""
    try:
        engine = ImmigrationEngine()
        result = engine.issue_residence_card(
            holder_name=holder,
            nationality=nationality,
            passport_number=passport_number,
            card_type=card_type,
            card_symbol=symbol,
            duration_months=duration_months,
            sponsor_entity=sponsor,
            residential_address=address,
            issue_date=issue_date,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Residence Card Issued:[/bold green] [cyan]{result['card_id']}[/cyan]")
        console.print(f"  [bold]Holder:[/bold] {result['holder_name']} ({result['nationality']}) | [bold]Passport:[/bold] {result['passport_number']}")
        console.print(f"  [bold]Type:[/bold] {result['card_type']} ({result['card_symbol']}) | [bold]Duration:[/bold] {result['duration_months']} months")
        console.print(f"  [bold]Validity:[/bold] {result['issue_date']} -> {result['expiry_date']}")
        console.print(f"  [bold]Sponsor:[/bold] {result['sponsor_entity']}")
        console.print(f"  [bold]Address:[/bold] {result['residential_address']}")
    except Exception as e:
        console.print(f"[bold red]Error issuing residence card:[/bold red] {e}")
        raise typer.Exit(code=1)


@immigration_app.command("border")
def border_cmd(
    person: str = typer.Option(..., "--person", "-p", help="Full name of person crossing border"),
    nationality: str = typer.Option(..., "--nationality", help="Person's nationality"),
    passport_number: str = typer.Option(..., "--passport-number", help="Passport number"),
    direction: str = typer.Option("ENTRY", "--direction", "-d", help="Direction: ENTRY | EXIT"),
    gate: str = typer.Option("Noi Bai International Airport", "--gate", "-g", help="Border gate name"),
    gate_type: str = typer.Option("INTERNATIONAL_AIRPORT", "--gate-type", help="Gate type: INTERNATIONAL_AIRPORT | INTERNATIONAL_SEAPORT | LAND_BORDER_GATE | AUTOGATE"),
    flight_code: Optional[str] = typer.Option(None, "--flight-code", help="Flight or transport registration code (e.g. VN210)"),
    autogate: bool = typer.Option(False, "--autogate/--manual-booth", help="Processed via Autogate automated kiosk"),
    notes: str = typer.Option("", "--notes", help="Movement remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Log and verify Entry/Exit border movement with automated security screening."""
    try:
        engine = ImmigrationEngine()
        result = engine.log_border_movement(
            person_name=person,
            nationality=nationality,
            passport_number=passport_number,
            direction=direction,
            border_gate=gate,
            gate_type=gate_type,
            transport_code=flight_code,
            autogate_used=autogate,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        clear_color = "green" if result["clearance_status"] == "CLEARED" else "red"
        console.print(f"[bold green]✓ Border Movement Registered:[/bold green] [cyan]{result['movement_id']}[/cyan]")
        console.print(f"  [bold]Passenger:[/bold] {result['person_name']} ({result['nationality']}) | [bold]Passport:[/bold] {result['passport_number']}")
        console.print(f"  [bold]Direction:[/bold] {result['direction']} @ {result['border_gate']} ({result['gate_type']})")
        console.print(f"  [bold]Autogate:[/bold] {'Yes' if result['autogate_used'] else 'No'}")
        console.print(f"  [bold]Clearance:[/bold] [{clear_color}]{result['clearance_status']}[/{clear_color}]")
        if result["notes"]:
            console.print(f"  [bold]Remarks:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error registering border movement:[/bold red] {e}")
        raise typer.Exit(code=1)


@immigration_app.command("restriction")
def restriction_cmd(
    subject: str = typer.Option(..., "--subject", "-s", help="Full name of target subject"),
    nationality: str = typer.Option(..., "--nationality", help="Target subject's nationality"),
    passport_number: str = typer.Option(..., "--passport-number", "-p", help="Passport number"),
    restriction_type: str = typer.Option("ENTRY_SUSPENSION", "--type", "-t", help="Restriction: ENTRY_SUSPENSION (Art 21) | EXIT_POSTPONEMENT (Art 28) | EXPULSION"),
    basis: str = typer.Option(..., "--basis", "-b", help="Statutory legal basis (e.g. Art 21 k1 Law 47/2014, Tax debt Art 28 k1)"),
    authority: str = typer.Option(..., "--authority", help="Issuing competent body (TAND, VKSND, BCA, Tax Dept)"),
    effective_from: Optional[str] = typer.Option(None, "--from", help="Effective start date (YYYY-MM-DD)"),
    effective_until: Optional[str] = typer.Option(None, "--until", help="Effective end date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="Order status: ACTIVE | REVOKED | EXPIRED"),
    notes: str = typer.Option("", "--notes", help="Order remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Impose or register Entry Suspension or Exit Postponement order."""
    try:
        engine = ImmigrationEngine()
        result = engine.register_restriction(
            subject_name=subject,
            nationality=nationality,
            passport_number=passport_number,
            restriction_type=restriction_type,
            legal_basis=basis,
            issuing_body=authority,
            effective_from=effective_from,
            effective_until=effective_until,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Restriction Order Registered:[/bold green] [cyan]{result['order_id']}[/cyan]")
        console.print(f"  [bold]Subject:[/bold] {result['subject_name']} ({result['nationality']}) | [bold]Passport:[/bold] {result['passport_number']}")
        console.print(f"  [bold]Type:[/bold] [red]{result['restriction_type']}[/red] | [bold]Basis:[/bold] {result['legal_basis']}")
        console.print(f"  [bold]Issuing Body:[/bold] {result['issuing_body']} | [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error registering restriction order:[/bold red] {e}")
        raise typer.Exit(code=1)


@immigration_app.command("passport")
def passport_cmd(
    name: str = typer.Option(..., "--name", "-n", help="Full Vietnamese citizen name"),
    citizen_id: str = typer.Option(..., "--citizen-id", "-c", help="Citizen ID number (12-digit CCCD)"),
    birth_date: str = typer.Option(..., "--birth-date", help="Citizen's date of birth (YYYY-MM-DD)"),
    passport_type: str = typer.Option("ELECTRONIC_CHIP", "--type", "-t", help="Passport type: ELECTRONIC_CHIP | REGULAR | OFFICIAL | DIPLOMATIC"),
    passport_number: Optional[str] = typer.Option(None, "--number", "-p", help="Passport serial number"),
    chip: bool = typer.Option(True, "--chip/--no-chip", help="Embedded ICAO compliant biometric chip"),
    autogate: bool = typer.Option(True, "--autogate/--no-autogate", help="Autogate automatic border gate enrollment"),
    authority: str = typer.Option("Cục Quản lý xuất nhập cảnh - Bộ Công an", "--authority", help="Issuing immigration authority"),
    issue_date: Optional[str] = typer.Option(None, "--issue-date", help="Date of issuance (YYYY-MM-DD)"),
    notes: str = typer.Option("", "--notes", help="Passport notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue or register Vietnamese Citizen Electronic Passport and Autogate enrollment."""
    try:
        engine = ImmigrationEngine()
        result = engine.issue_citizen_passport(
            citizen_name=name,
            citizen_id=citizen_id,
            birth_date=birth_date,
            passport_type=passport_type,
            passport_number=passport_number,
            has_electronic_chip=chip,
            autogate_enrolled=autogate,
            issuing_authority=authority,
            issue_date=issue_date,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Citizen Passport Registered:[/bold green] [cyan]{result['passport_id']}[/cyan]")
        console.print(f"  [bold]Citizen:[/bold] {result['citizen_name']} | [bold]CCCD:[/bold] {result['citizen_id']}")
        console.print(f"  [bold]Passport No:[/bold] {result['passport_number']} ({result['passport_type']})")
        console.print(f"  [bold]Biometric Chip:[/bold] {'Yes' if result['has_electronic_chip'] else 'No'} | [bold]Autogate Enrolled:[/bold] {'Yes' if result['autogate_enrolled'] else 'No'}")
        console.print(f"  [bold]Validity:[/bold] {result['issue_date']} -> {result['expiry_date']}")
    except Exception as e:
        console.print(f"[bold red]Error registering citizen passport:[/bold red] {e}")
        raise typer.Exit(code=1)


@immigration_app.command("list")
def list_records_cmd(
    category: str = typer.Option("visa", "--category", "-c", help="Category: visa | residence | movement | restriction | passport | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List immigration and border management records by category."""
    try:
        engine = ImmigrationEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Immigration Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@immigration_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show Vietnamese immigration, border control and passport telemetry."""
    engine = ImmigrationEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
