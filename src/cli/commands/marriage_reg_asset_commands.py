# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Marriage registration, prenuptial regime, asset recording & status dashboard."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.marriage_engine import MarriageEngine

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

    table.add_row("Marriage Registrations", "Civil Status Offices (UBND)", "Total Legal Marriages", str(status_data.get("total_marriage_registrations", 0)))
    table.add_row("Active Marriages", "Monogamy Principle (Điều 5)", "Active Marriages", str(status_data.get("active_marriages", 0)))
    table.add_row("Divorced Marriages", "Court Decisions / Judgments", "Divorces Granted", str(status_data.get("divorced_marriages", 0)))
    table.add_row("Divorce Rate", "Sociodemographic Ratio", "Divorce Rate (%)", f"{status_data.get('divorce_rate_percent', 0.0):.2f}%")
    table.add_row("Prenuptial Regimes", "Notarized Agreements (Điều 47)", "Agreed Property Regimes", str(status_data.get("prenuptial_agreements_registered", 0)))
    table.add_row("Matrimonial Assets", "Common & Separate Property", "Total Assets Recorded", str(status_data.get("total_matrimonial_assets_recorded", 0)))
    table.add_row("Total Matrimonial Wealth", "Asset Valuation Appraisals", "Total Wealth (VND)", f"{status_data.get('total_matrimonial_assets_value_vnd', 0.0):,.0f} VND")
    table.add_row("Divorce Petitions", "People's Courts (TAND)", "Petitions Filed", str(status_data.get("divorce_petitions_filed", 0)))
    table.add_row("Child Custody & Support", "Parental Support (Điều 81-84)", "Support Orders Active", str(status_data.get("child_custody_support_orders", 0)))
    table.add_row("Monthly Child Support", "Enforceable Support Value", "Total Monthly Support", f"{status_data.get('total_monthly_support_ordered_vnd', 0.0):,.0f} VND")
    table.add_row("Compliance Logs", "Inter-Agency Audit Trail", "Audit Events", str(status_data.get("audit_logs_count", 0)))

    console.print(table)


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
