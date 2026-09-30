# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Marriage, Matrimonial Property Regimes & Family Law Command Surface (Phase 147).

Statutory framework:
- Law on Marriage and Family 2014 (Luật số 52/2014/QH13)
- Decree No. 126/2014/ND-CP detailing provisions of the Law on Marriage and Family
- Civil Code 2015 (Law No. 91/2015/QH13)
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.marriage_engine import (
    AssetCategory,
    DivorceType,
    MarriageEngine,
    MarriageStatus,
    OwnershipType,
    PropertyRegimeType,
)

marriage_app = typer.Typer(
    name="marriage",
    help="Vietnamese Marriage, Matrimonial Property Regimes & Family Law Suite.",
    no_args_is_help=False,
)
app = marriage_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — QUẢN LÝ HÔN NHÂN & GIA ĐÌNH[/bold cyan]\n"
            "[bold green]BẢNG ĐIỀU HÀNH HÔN NHÂN, CHẾ ĐỘ TÀI SẢN & NGHĨA VỤ GIA ĐÌNH[/bold green]\n"
            "[dim]Ministry of Justice — Department of Civil Status, Nationality & Attestation (Bộ Tư pháp - Cục HTQTCT)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Marriage, Matrimonial Property & Family Law Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Domain / Category", style="bold green")
    table.add_column("Regulatory Channel", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Marriage Registrations",
        "Civil Status Offices (UBND)",
        "Total Legal Marriages",
        str(status_data.get("total_marriage_registrations", 0)),
    )
    table.add_row(
        "Active Marriages",
        "Monogamy Principle (Điều 5)",
        "Active Marriages",
        str(status_data.get("active_marriages", 0)),
    )
    table.add_row(
        "Divorced Marriages",
        "Court Decisions / Judgments",
        "Divorces Granted",
        str(status_data.get("divorced_marriages", 0)),
    )
    table.add_row(
        "Divorce Rate",
        "Sociodemographic Ratio",
        "Divorce Rate (%)",
        f"{status_data.get('divorce_rate_percent', 0.0):.2f}%",
    )
    table.add_row(
        "Prenuptial Regimes",
        "Notarized Agreements (Điều 47)",
        "Agreed Property Regimes",
        str(status_data.get("prenuptial_agreements_registered", 0)),
    )
    table.add_row(
        "Matrimonial Assets",
        "Common & Separate Property",
        "Total Assets Recorded",
        str(status_data.get("total_matrimonial_assets_recorded", 0)),
    )
    table.add_row(
        "Total Matrimonial Wealth",
        "Asset Valuation Appraisals",
        "Total Wealth (VND)",
        f"{status_data.get('total_matrimonial_assets_value_vnd', 0.0):,.0f} VND",
    )
    table.add_row(
        "Divorce Petitions",
        "People's Courts (TAND)",
        "Petitions Filed",
        str(status_data.get("divorce_petitions_filed", 0)),
    )
    table.add_row(
        "Child Custody & Support",
        "Parental Support (Điều 81-84)",
        "Support Orders Active",
        str(status_data.get("child_custody_support_orders", 0)),
    )
    table.add_row(
        "Monthly Child Support",
        "Enforceable Support Value",
        "Total Monthly Support",
        f"{status_data.get('total_monthly_support_ordered_vnd', 0.0):,.0f} VND",
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@marriage_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """National Marriage, Matrimonial Property & Family Law Central Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = MarriageEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@marriage_app.command("register")
def register_cmd(
    husband_name: str = typer.Argument(..., help="Husband full name"),
    wife_name: str = typer.Argument(..., help="Wife full name"),
    husband_dob: str = typer.Argument(..., help="Husband date of birth (YYYY-MM-DD, age >= 20)"),
    wife_dob: str = typer.Argument(..., help="Wife date of birth (YYYY-MM-DD, age >= 18)"),
    husband_id: str = typer.Argument(..., help="Husband citizen ID / passport"),
    wife_id: str = typer.Argument(..., help="Wife citizen ID / passport"),
    husband_addr: str = typer.Option("Hà Nội, Việt Nam", "--husband-addr", help="Husband permanent address"),
    wife_addr: str = typer.Option("Hà Nội, Việt Nam", "--wife-addr", help="Wife permanent address"),
    husband_nat: str = typer.Option("VIETNAM", "--husband-nat", help="Husband nationality"),
    wife_nat: str = typer.Option("VIETNAM", "--wife-nat", help="Wife nationality"),
    reg_date: Optional[str] = typer.Option(None, "--date", "--reg-date", help="Registration date (YYYY-MM-DD)"),
    office: str = typer.Option("UBND Phường/Xã có thẩm quyền", "--office", help="Competent Civil Status Registry Office"),
    regime: str = typer.Option("STATUTORY", "--regime", help="Property regime: STATUTORY | AGREED_PRENUPTIAL"),
    notes: str = typer.Option("", "--notes", help="Registration notes or remarks"),
    marriage_id: Optional[str] = typer.Option(None, "--marriage-id", help="Custom marriage ID"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register legal marriage with statutory age, consent, and monogamy verification."""
    try:
        engine = MarriageEngine()
        result = engine.register_marriage(
            husband_name=husband_name,
            husband_dob=husband_dob,
            husband_id=husband_id,
            husband_address=husband_addr,
            wife_name=wife_name,
            wife_dob=wife_dob,
            wife_id=wife_id,
            wife_address=wife_addr,
            registration_date=reg_date,
            registration_office=office,
            husband_nationality=husband_nat,
            wife_nationality=wife_nat,
            property_regime=regime,
            notes=notes,
            marriage_id=marriage_id,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Marriage Registered Successfully:[/bold green] [cyan]{result['marriage_id']}[/cyan]")
        console.print(f"  [bold]Certificate Code:[/bold] [bold yellow]{result['certificate_number']}[/bold yellow]")
        console.print(f"  [bold]Husband:[/bold] {result['husband_name']} (DOB: {result['husband_dob']} | ID: {result['husband_id']})")
        console.print(f"  [bold]Wife:[/bold] {result['wife_name']} (DOB: {result['wife_dob']} | ID: {result['wife_id']})")
        console.print(f"  [bold]Property Regime:[/bold] [green]{result['property_regime']}[/green]")
        console.print(f"  [bold]Registration Date:[/bold] {result['registration_date']}")
        console.print(f"  [bold]Office:[/bold] {result['registration_office']}")
        console.print(f"  [bold]Status:[/bold] [bold green]{result['status']}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Error registering marriage:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("prenuptial")
def prenuptial_cmd(
    marriage_id: str = typer.Argument(..., help="Marriage ID"),
    agreement_date: str = typer.Argument(..., help="Agreement date (YYYY-MM-DD, must be prior to or on marriage date)"),
    notary_office: str = typer.Argument(..., help="Notary office / certification authority"),
    notary_cert: str = typer.Option("NOTARY-PRENUP-2026", "--notary-cert", help="Notary certification code"),
    terms: str = typer.Option("Thỏa thuận phân định tài sản riêng và tài sản chung trước khi đăng ký kết hôn", "--terms", help="Summary of prenuptial agreement terms"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Establish or record agreed matrimonial property regime (prenuptial agreement)."""
    try:
        engine = MarriageEngine()
        result = engine.register_prenuptial_agreement(
            marriage_id=marriage_id,
            agreement_date=agreement_date,
            notary_office=notary_office,
            notary_certificate_number=notary_cert,
            terms_summary=terms,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Prenuptial Agreement Recorded:[/bold green] [cyan]{result['regime_id']}[/cyan]")
        console.print(f"  [bold]Marriage ID:[/bold] {result['marriage_id']}")
        console.print(f"  [bold]Agreement Date:[/bold] {result['agreement_date']}")
        console.print(f"  [bold]Notary Office:[/bold] {result['notary_office']} (Cert: {result['notary_certificate_number']})")
        console.print(f"  [bold]Terms:[/bold] {result['terms_summary']}")
    except Exception as e:
        console.print(f"[bold red]Error registering prenuptial agreement:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("asset")
def asset_cmd(
    marriage_id: str = typer.Argument(..., help="Marriage ID"),
    asset_name: str = typer.Argument(..., help="Asset description or title"),
    category: str = typer.Argument("REAL_ESTATE", help="REAL_ESTATE | VEHICLE | BANK_DEPOSIT_SAVINGS | CORPORATE_EQUITY | etc."),
    value: float = typer.Argument(..., help="Estimated value in VND"),
    ownership: str = typer.Option("COMMON", "--ownership", help="COMMON | HUSBAND_SEPARATE | WIFE_SEPARATE"),
    date: Optional[str] = typer.Option(None, "--date", "--acq-date", help="Acquisition date (YYYY-MM-DD)"),
    identifier: Optional[str] = typer.Option(None, "--id", "--identifier", help="Certificate/Registration number (VIN, Land Title No)"),
    notes: str = typer.Option("", "--notes", help="Asset remarks or origin notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Record property into matrimonial asset inventory (common vs separate property)."""
    try:
        engine = MarriageEngine()
        result = engine.record_matrimonial_asset(
            marriage_id=marriage_id,
            asset_name=asset_name,
            asset_category=category,
            estimated_value=value,
            ownership_type=ownership,
            acquisition_date=date,
            identifier_number=identifier,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Matrimonial Asset Recorded:[/bold green] [cyan]{result['asset_id']}[/cyan]")
        console.print(f"  [bold]Marriage ID:[/bold] {result['marriage_id']}")
        console.print(f"  [bold]Asset Name:[/bold] {result['asset_name']} ({result['asset_category']})")
        console.print(f"  [bold]Ownership:[/bold] [yellow]{result['ownership_type']}[/yellow]")
        console.print(f"  [bold]Estimated Value:[/bold] {result['estimated_value']:,.0f} VND")
        if result.get("identifier_number"):
            console.print(f"  [bold]Identifier:[/bold] {result['identifier_number']}")
    except Exception as e:
        console.print(f"[bold red]Error recording matrimonial asset:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("divorce")
def divorce_cmd(
    marriage_id: str = typer.Argument(..., help="Marriage ID"),
    divorce_type: str = typer.Argument("CONSENSUAL", help="CONSENSUAL | UNILATERAL"),
    petitioner: str = typer.Argument("BOTH", help="HUSBAND | WIFE | BOTH"),
    grounds: str = typer.Argument(..., help="Grounds for divorce"),
    court: str = typer.Option("Tòa án Nhân dân Quận/Huyện có thẩm quyền", "--court", help="Competent People's Court"),
    date: Optional[str] = typer.Option(None, "--date", help="Filing date (YYYY-MM-DD)"),
    domestic_violence: bool = typer.Option(False, "--domestic-violence", help="Grounds include domestic violence"),
    wife_pregnant: bool = typer.Option(False, "--wife-pregnant", help="Wife is currently pregnant"),
    nursing_child: bool = typer.Option(False, "--nursing-child", help="Wife is nursing a child under 12 months"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """File divorce petition with Article 51(3) statutory protection for pregnant/nursing mothers."""
    try:
        engine = MarriageEngine()
        result = engine.file_divorce_petition(
            marriage_id=marriage_id,
            divorce_type=divorce_type,
            petitioner=petitioner,
            grounds=grounds,
            court_name=court,
            filing_date=date,
            has_domestic_violence=domestic_violence,
            wife_is_pregnant=wife_pregnant,
            nursing_child_under_12m=nursing_child,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold yellow]✓ Divorce Petition Filed:[/bold yellow] [cyan]{result['petition_id']}[/cyan]")
        console.print(f"  [bold]Marriage ID:[/bold] {result['marriage_id']} | [bold]Type:[/bold] {result['divorce_type']}")
        console.print(f"  [bold]Petitioner:[/bold] {result['petitioner']}")
        console.print(f"  [bold]Grounds:[/bold] {result['grounds']}")
        console.print(f"  [bold]Court:[/bold] {result['court_name']}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error filing divorce petition:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("custody")
def custody_cmd(
    petition_id: str = typer.Argument(..., help="Divorce petition ID"),
    child_name: str = typer.Argument(..., help="Child full name"),
    child_dob: str = typer.Argument(..., help="Child date of birth (YYYY-MM-DD)"),
    custodial_parent: str = typer.Argument("MOTHER", help="MOTHER | FATHER"),
    support_amount: float = typer.Argument(..., help="Monthly support amount in VND"),
    date: Optional[str] = typer.Option(None, "--date", help="Effective order date"),
    notes: str = typer.Option("", "--notes", help="Custody order notes"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Process child custody and monthly child support order under Articles 81-84 & 110-119."""
    try:
        engine = MarriageEngine()
        result = engine.process_child_custody_support(
            petition_id=petition_id,
            child_name=child_name,
            child_dob=child_dob,
            custodial_parent=custodial_parent,
            monthly_support_vnd=support_amount,
            effective_date=date,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Child Custody & Support Order Granted:[/bold green] [cyan]{result['order_id']}[/cyan]")
        console.print(f"  [bold]Child:[/bold] {result['child_name']} (DOB: {result['child_dob']})")
        console.print(f"  [bold]Custodial Parent:[/bold] [green]{result['custodial_parent']}[/green]")
        console.print(f"  [bold]Non-Custodial Support Payer:[/bold] {result['non_custodial_parent']}")
        console.print(f"  [bold]Monthly Support:[/bold] [bold yellow]{result['monthly_support_vnd']:,.0f} VND/month[/bold yellow]")
        if result.get("notes"):
            console.print(f"  [bold]Statutory Notes:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing child custody and support:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("settle")
def settle_cmd(
    petition_id: str = typer.Argument(..., help="Divorce petition ID"),
    judgment_number: str = typer.Argument(..., help="Court judgment / decree reference number"),
    husband_percent: float = typer.Option(50.0, "--husband-percent", help="Husband contribution ratio (0-100, default 50)"),
    date: Optional[str] = typer.Option(None, "--date", help="Resolution date (YYYY-MM-DD)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Settle divorce and liquidate matrimonial property under Article 59."""
    try:
        engine = MarriageEngine()
        result = engine.settle_divorce_and_property(
            petition_id=petition_id,
            judgment_number=judgment_number,
            resolution_date=date,
            husband_contribution_percent=husband_percent,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Divorce & Property Settlement Finalized:[/bold green] [cyan]{result['petition_id']}[/cyan]")
        console.print(f"  [bold]Judgment Number:[/bold] {result['judgment_number']}")
        console.print(f"  [bold]Total Common Wealth:[/bold] {result['total_common_value_vnd']:,.0f} VND")
        console.print(f"  [bold]Husband Allocation ({result['husband_contribution_percent']:.0f}%):[/bold] [cyan]{result['husband_total_allocation_vnd']:,.0f} VND[/cyan]")
        console.print(f"  [bold]Wife Allocation ({result['wife_contribution_percent']:.0f}%):[/bold] [magenta]{result['wife_total_allocation_vnd']:,.0f} VND[/magenta]")
    except Exception as e:
        console.print(f"[bold red]Error settling divorce:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("search")
def search_cmd(
    query: Optional[str] = typer.Argument(None, help="Search query (citizen ID, spouse name, or certificate number)"),
    query_opt: Optional[str] = typer.Option(None, "--query", "-q", help="Search query string"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum search results"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Search marriage registrations and divorce records."""
    try:
        engine = MarriageEngine()
        search_str = query if query is not None else (query_opt if query_opt is not None else "")
        records = engine.search_marriage_records(query=search_str if search_str else " ")

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No marriage records found matching query '{search_str}'.[/yellow]")
            return

        table = Table(title=f"Marriage Records Search Results — Query: '{search_str}'", box=box.ROUNDED)
        table.add_column("Marriage ID", style="cyan")
        table.add_column("Certificate", style="yellow")
        table.add_column("Husband", style="white")
        table.add_column("Wife", style="magenta")
        table.add_column("Reg Date", style="green")
        table.add_column("Regime", style="cyan")
        table.add_column("Status", style="bold green")

        for r in records[:limit]:
            table.add_row(
                r["marriage_id"],
                r["certificate_number"],
                r["husband_name"],
                r["wife_name"],
                r["registration_date"],
                r["property_regime"],
                r["status"],
            )

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error searching marriage records:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("list")
def list_records_cmd(
    category: str = typer.Option("marriage", "--category", "-c", help="Category: marriage | regime | asset | petition | custody | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Pagination offset"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List marriage and family records by category."""
    try:
        engine = MarriageEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Marriage & Family Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing marriage records:[/bold red] {e}")
        raise typer.Exit(code=1)


@marriage_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show national marriage, divorce, and family statistics."""
    engine = MarriageEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
