# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Registration of Security Interests & Secured Transactions Command Surface (Phase 146).

Implements statutory compliance workflows under Civil Code 2015 (Articles 292-350),
Decree No. 99/2022/ND-CP, Circular No. 08/2023/TT-BTP, Land Law 2024, and Maritime Code 2015.
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.securedtransactions_engine import (
    AssetType,
    DisposalMethod,
    RegistrationStatus,
    SecuredTransactionsEngine,
    SecurityMeasureType,
)

securedtransactions_app = typer.Typer(
    name="securedtransactions",
    help="Vietnamese Registration of Security Interests & Collateral Priority Management Engine.",
    no_args_is_help=False,
)
app = securedtransactions_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG ĐĂNG KÝ BIỆN PHÁP BẢO ĐẢM QUỐC GIA[/bold cyan]\n"
            "[bold green]BẢNG ĐIỀU HÀNH GIAO DỊCH BẢO ĐẢM VÀ THỨ TỰ ƯU TIÊN THANH TOÁN[/bold green]\n"
            "[dim]National Registration Agency for Secured Transactions — MOJ (Cục Đăng ký quốc gia giao dịch bảo đảm - BTP)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Secured Transactions & Collateral Registry Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category / Domain", style="bold green")
    table.add_column("Authority / Registry Channel", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row(
        "Security Registrations",
        "National Registry Centers (BTP)",
        "Total Registrations",
        str(status_data.get("total_security_registrations", 0)),
    )
    table.add_row(
        "Active Registrations",
        "Valid Security Interests (Điều 297 BLDS)",
        "Active Registrations",
        str(status_data.get("active_security_registrations", 0)),
    )
    table.add_row(
        "Secured Value (VND)",
        "Registered Secured Credit",
        "Total Secured Amount",
        f"{status_data.get('total_secured_obligation_value_vnd', 0.0):,.0f} VND",
    )
    table.add_row(
        "Collateral Assets",
        "Real Estate, Movables, Rights",
        "Total Collateral Assets",
        str(status_data.get("total_collateral_assets", 0)),
    )
    table.add_row(
        "Collateral Value (VND)",
        "Estimated Collateral Appraisal",
        "Total Collateral Valuation",
        f"{status_data.get('total_collateral_value_vnd', 0.0):,.0f} VND",
    )
    table.add_row(
        "Priority Rankings",
        "Statutory Payment Order (Điều 308 BLDS)",
        "Active Priority Records",
        str(status_data.get("active_priority_rankings", 0)),
    )
    table.add_row(
        "Disposal Notices",
        "Collateral Enforcement (Điều 51 NĐ 99)",
        "Active Disposal Notices",
        str(status_data.get("active_disposal_notices", 0)),
    )
    table.add_row(
        "Deregistrations",
        "Obligations Released (Điều 52 NĐ 99)",
        "Deregistrations Processed",
        str(status_data.get("deregistrations_processed", 0)),
    )
    table.add_row(
        "Compliance Logs",
        "Inter-Agency Audit Trail",
        "Audit Events",
        str(status_data.get("audit_logs_count", 0)),
    )

    console.print(table)


@securedtransactions_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """National Secured Transactions & Security Measures Central Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = SecuredTransactionsEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@securedtransactions_app.command("register")
def register_cmd(
    contract_or_id: str = typer.Argument(..., help="Contract number or registration ID"),
    measure_type: str = typer.Argument("MORTGAGE", help="Measure type: MORTGAGE | PLEDGE | TITLE_RETENTION | GUARANTEE | etc."),
    secured_party: str = typer.Argument(..., help="Secured party name (Bank/Creditor)"),
    securing_party: str = typer.Argument(..., help="Securing party name (Grantor/Owner)"),
    amount: float = typer.Argument(..., help="Secured obligation amount in currency"),
    contract_number: Optional[str] = typer.Option(None, "--contract", "-c", "--contract-number", help="Security contract number"),
    secured_id: str = typer.Option("0100112437", "--secured-id", "--secured-party-id", help="Secured party enterprise ID / Tax code"),
    secured_addr: str = typer.Option("Số 1 Hà Nội", "--secured-addr", "--secured-party-addr", help="Secured party registered address"),
    securing_id: str = typer.Option("1801234567", "--securing-id", "--securing-party-id", help="Securing party citizen ID / enterprise ID"),
    securing_addr: str = typer.Option("Cần Thơ, Việt Nam", "--securing-addr", "--securing-party-addr", help="Securing party permanent address"),
    currency: str = typer.Option("VND", "--currency", help="Currency: VND | USD"),
    asset_type: str = typer.Option("REAL_ESTATE", "--asset-type", help="Asset type classification"),
    debtor_name: Optional[str] = typer.Option(None, "--debtor-name", help="Debtor name if different from securing party"),
    debtor_id: Optional[str] = typer.Option(None, "--debtor-id", help="Debtor ID"),
    office: Optional[str] = typer.Option(None, "--office", "--authority", help="Competent Secured Transactions Registration Center"),
    time: Optional[str] = typer.Option(None, "--time", "--effective-date", help="Exact registration timestamp (ISO format)"),
    notes: str = typer.Option("", "--notes", help="Dossier remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register initial or modified security measure under Civil Code 2015 and Decree 99/2022."""
    try:
        engine = SecuredTransactionsEngine()
        actual_contract = contract_number if contract_number else contract_or_id
        actual_reg_id = contract_or_id if contract_or_id.startswith("REG-") else None

        result = engine.register_security_interest(
            contract_number=actual_contract,
            measure_type=measure_type,
            secured_party_name=secured_party,
            secured_party_id=secured_id,
            secured_party_address=secured_addr,
            securing_party_name=securing_party,
            securing_party_id=securing_id,
            securing_party_address=securing_addr,
            secured_obligation_amount=amount,
            debtor_name=debtor_name,
            debtor_id=debtor_id,
            secured_obligation_currency=currency,
            registry_office=office,
            registration_timestamp=time,
            notes=notes,
            registration_id=actual_reg_id,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Security Interest Registered:[/bold green] [cyan]{result['registration_id']}[/cyan]")
        console.print(f"  [bold]Contract:[/bold] {result['contract_number']} | [bold]Measure:[/bold] {result['measure_type']}")
        console.print(f"  [bold]Secured Party (Creditor):[/bold] {result['secured_party_name']} (ID: {result['secured_party_id']})")
        console.print(f"  [bold]Securing Party (Grantor):[/bold] {result['securing_party_name']} (ID: {result['securing_party_id']})")
        console.print(f"  [bold]Secured Amount:[/bold] {result['secured_obligation_amount']:,.0f} {result['secured_obligation_currency']}")
        console.print(f"  [bold]Timestamp (Opposability):[/bold] [yellow]{result['registration_timestamp']}[/yellow]")
        console.print(f"  [bold]Registry Office:[/bold] {result['registry_office']}")
        console.print(f"  [bold]Status:[/bold] [green]{result['status']}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error registering security measure:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("collateral")
def collateral_cmd(
    reg_id: str = typer.Argument(..., help="Security registration ID"),
    asset_id: str = typer.Argument(..., help="Collateral asset ID"),
    description: str = typer.Argument(..., help="Detailed collateral description"),
    asset_type: str = typer.Argument("REAL_ESTATE", help="REAL_ESTATE | MOVABLE_PROPERTY | PROPERTY_RIGHT | VEHICLE | etc."),
    value: float = typer.Argument(..., help="Estimated collateral valuation in VND"),
    identifier: Optional[str] = typer.Option(None, "--id", "-i", "--identifier", help="Unique asset identifier (Chassis No, Land Cert No, Contract No)"),
    location: str = typer.Option("Việt Nam", "--location", "-l", help="Asset location / storage / registration place"),
    future: bool = typer.Option(False, "--future/--no-future", help="Asset formed in the future"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Record collateral asset and link to security registration."""
    try:
        engine = SecuredTransactionsEngine()
        actual_id = identifier if identifier else asset_id

        result = engine.record_collateral(
            registration_id=reg_id,
            asset_type=asset_type,
            asset_description=description,
            identifier_number=actual_id,
            estimated_value=value,
            location=location,
            is_future_asset=future,
            asset_id=asset_id,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Collateral Asset Linked:[/bold green] [cyan]{result['asset_id']}[/cyan]")
        console.print(f"  [bold]Registration ID:[/bold] {result['registration_id']}")
        console.print(f"  [bold]Type:[/bold] {result['asset_type']} (Future Asset: {'Yes' if result['is_future_asset'] else 'No'})")
        console.print(f"  [bold]Identifier:[/bold] [bold yellow]{result['identifier_number']}[/bold yellow]")
        console.print(f"  [bold]Description:[/bold] {result['asset_description']}")
        console.print(f"  [bold]Estimated Value:[/bold] {result['estimated_value']:,.0f} VND")
        console.print(f"  [bold]Location:[/bold] {result['location']}")
        console.print(f"  [bold]Status:[/bold] [green]{result['status']}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error recording collateral asset:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("priority")
def priority_cmd(
    identifier: str = typer.Argument(..., help="Asset unique identifier number (VIN, Land Certificate No)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Calculate statutory repayment priority ranking over an asset under Article 308 Civil Code 2015."""
    try:
        engine = SecuredTransactionsEngine()
        rankings = engine.calculate_priority(asset_identifier=identifier)

        if json_output:
            typer.echo(json.dumps(rankings, ensure_ascii=False, indent=2))
            return

        if not rankings:
            console.print(f"[yellow]No active security registrations found for asset identifier '{identifier}'.[/yellow]")
            return

        table = Table(title=f"Statutory Repayment Priority Ranking — Asset: {identifier} (Điều 308 BLDS 2015)", box=box.ROUNDED)
        table.add_column("Rank", style="bold yellow")
        table.add_column("Secured Party (Creditor)", style="cyan")
        table.add_column("Registration ID", style="white")
        table.add_column("Claim Amount", style="bold green")
        table.add_column("Registration Timestamp", style="magenta")
        table.add_column("Opposable", style="green")

        for r in rankings:
            table.add_row(
                f"#{r['priority_rank']}",
                r["secured_party"],
                r["registration_id"],
                f"{r['claim_amount']:,.0f} VND",
                r["registration_timestamp"],
                "Yes (Đối kháng)",
            )

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error computing priority ranking:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("disposal")
def disposal_cmd(
    reg_id: str = typer.Argument(..., help="Security registration ID"),
    asset_id: str = typer.Argument(..., help="Collateral asset ID"),
    method: str = typer.Argument("AUCTION", help="Disposal method: AUCTION | PRIVATE_SALE | DEBT_OFFSET | OTHER"),
    reason: str = typer.Option("Bên bảo đảm không thực hiện nghĩa vụ trả nợ", "--reason", help="Statutory reason for disposal (default on loan, breach)"),
    date: str = typer.Option("2026-11-15", "--date", "--disposal-date", help="Expected disposal date (YYYY-MM-DD)"),
    party: Optional[str] = typer.Option(None, "--party", "-p", "--notifying-party", "--authorized-officer", help="Notifying secured creditor"),
    recovery_target: float = typer.Option(0.0, "--recovery-target", help="Target recovery amount in VND"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register formal notice of collateral disposal under Article 51 Decree 99/2022."""
    try:
        engine = SecuredTransactionsEngine()
        actual_party = party if party else "Bên nhận bảo đảm"

        result = engine.register_disposal_notice(
            registration_id=reg_id,
            asset_id=asset_id,
            disposal_reason=reason,
            expected_disposal_date=date,
            notifying_party=actual_party,
            disposal_method=method,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold red]✓ Notice of Collateral Disposal Registered:[/bold red] [cyan]{result['notice_id']}[/cyan]")
        console.print(f"  [bold]Registration ID:[/bold] {result['registration_id']} | [bold]Asset ID:[/bold] {result['asset_id']}")
        console.print(f"  [bold]Reason:[/bold] {result['disposal_reason']}")
        console.print(f"  [bold]Method:[/bold] {result['disposal_method']} (Expected Date: {result['expected_disposal_date']})")
        console.print(f"  [bold]Notifying Party:[/bold] {result['notifying_party']} ({result['notice_date']})")
        console.print(f"  [bold]Status:[/bold] [red]{result['status']}[/red]")
    except Exception as e:
        console.print(f"[bold red]Error registering disposal notice:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("deregister")
def deregister_cmd(
    reg_id: str = typer.Argument(..., help="Security registration ID"),
    reason: str = typer.Argument("OBLIGATION_FULFILLED", help="Deregistration reason"),
    party: str = typer.Option("Bên bảo đảm", "--party", "-p", "--requesting-party", help="Requesting party (Secured party or securing party)"),
    officer: str = typer.Option("Chuyên viên Đăng ký Giao dịch bảo đảm", "--officer", help="Approving registrar officer"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Release and cancel security interest registration upon obligation termination under Article 52 Decree 99/2022."""
    try:
        engine = SecuredTransactionsEngine()
        result = engine.deregister_security_interest(
            registration_id=reg_id,
            deregistration_reason=reason,
            requesting_party=party,
            approving_officer=officer,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Security Interest Deregistered (Giải chấp thành công):[/bold green] [cyan]{result['deregistration_id']}[/cyan]")
        console.print(f"  [bold]Registration ID:[/bold] {result['registration_id']}")
        console.print(f"  [bold]Certificate Code:[/bold] [bold yellow]{result['certificate_code']}[/bold yellow]")
        console.print(f"  [bold]Reason:[/bold] {result['deregistration_reason']}")
        console.print(f"  [bold]Approving Officer:[/bold] {result['approving_officer']} ({result['release_date']})")
        console.print(f"  [bold]Status:[/bold] [green]{result['status']}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error deregistering security interest:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("search")
def search_cmd(
    query: Optional[str] = typer.Argument(None, help="Search query (contract number, debtor ID, debtor name, or asset identifier)"),
    query_opt: Optional[str] = typer.Option(None, "--query", "-q", help="Search query string"),
    reg_type: Optional[str] = typer.Option(None, "--reg-type", help="Registration measure type filter"),
    asset_type: Optional[str] = typer.Option(None, "--asset-type", help="Asset type filter"),
    authority: Optional[str] = typer.Option(None, "--authority", help="Registry authority filter"),
    status: Optional[str] = typer.Option(None, "--status", help="Status filter"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum search results"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Search registered security measures across National Registry database."""
    try:
        engine = SecuredTransactionsEngine()
        search_str = query if query is not None else (query_opt if query_opt is not None else "")
        records = engine.search_security_interest(query=search_str if search_str else " ")

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No security registrations found matching query '{search_str}'.[/yellow]")
            return

        table = Table(title=f"Secured Transactions Search Results — Query: '{search_str}'", box=box.ROUNDED)
        table.add_column("Reg ID", style="cyan")
        table.add_column("Contract", style="white")
        table.add_column("Measure", style="green")
        table.add_column("Secured Party", style="yellow")
        table.add_column("Securing Party", style="magenta")
        table.add_column("Amount (VND)", style="bold cyan")
        table.add_column("Status", style="bold green")

        for r in records[:limit]:
            table.add_row(
                r["registration_id"],
                r["contract_number"],
                r["measure_type"],
                r["secured_party_name"],
                r["securing_party_name"],
                f"{r['secured_obligation_amount']:,.0f}",
                r["status"],
            )

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error searching security interests:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("list")
def list_records_cmd(
    category: str = typer.Option("registration", "--category", "-c", help="Category: registration | collateral | priority | disposal | deregistration | audit"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Pagination offset"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List secured transactions records by category."""
    try:
        engine = SecuredTransactionsEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Secured Transactions Records — {category.upper()}", box=box.ROUNDED)
        cols = list(records[0].keys())[:6]
        for c in cols:
            table.add_column(c.replace("_", " ").title(), style="cyan")

        for r in records:
            table.add_row(*[str(r.get(c, "")) for c in cols])

        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error listing records:[/bold red] {e}")
        raise typer.Exit(code=1)


@securedtransactions_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Show national secured transactions registry statistics."""
    engine = SecuredTransactionsEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(status_data)
