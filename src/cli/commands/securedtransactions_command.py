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
from rich.console import Console

from src.cli.commands._securedtransactions_operations import (
    deregister_cmd,
    disposal_cmd,
    priority_cmd,
    register_securedtransactions_operations,
)
from src.cli.commands._securedtransactions_queries import (
    list_records_cmd,
    register_securedtransactions_queries,
    render_securedtransactions_dashboard,
    search_cmd,
    status_cmd,
)
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
    render_securedtransactions_dashboard(console, status_data)


@securedtransactions_app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
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
) -> None:
    """Register initial or modified security measure under Civil Code 2015 and Decree 99/2022."""
    try:
        result = SecuredTransactionsEngine().register_security_interest(
            contract_number=contract_number if contract_number else contract_or_id, measure_type=measure_type,
            secured_party_name=secured_party, secured_party_id=secured_id, secured_party_address=secured_addr,
            securing_party_name=securing_party, securing_party_id=securing_id, securing_party_address=securing_addr,
            secured_obligation_amount=amount, debtor_name=debtor_name, debtor_id=debtor_id,
            secured_obligation_currency=currency, registry_office=office, registration_timestamp=time,
            notes=notes, registration_id=contract_or_id if contract_or_id.startswith("REG-") else None,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(
            f"[bold green]✓ Security Interest Registered:[/bold green] [cyan]{result['registration_id']}[/cyan]\n"
            f"  [bold]Contract:[/bold] {result['contract_number']} | [bold]Measure:[/bold] {result['measure_type']}\n"
            f"  [bold]Secured Party (Creditor):[/bold] {result['secured_party_name']} (ID: {result['secured_party_id']})\n"
            f"  [bold]Securing Party (Grantor):[/bold] {result['securing_party_name']} (ID: {result['securing_party_id']})\n"
            f"  [bold]Secured Amount:[/bold] {result['secured_obligation_amount']:,.0f} {result['secured_obligation_currency']}\n"
            f"  [bold]Timestamp (Opposability):[/bold] [yellow]{result['registration_timestamp']}[/yellow]\n"
            f"  [bold]Registry Office:[/bold] {result['registry_office']}\n"
            f"  [bold]Status:[/bold] [green]{result['status']}[/green]"
        )
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
) -> None:
    """Record collateral asset and link to security registration."""
    try:
        result = SecuredTransactionsEngine().record_collateral(
            registration_id=reg_id, asset_type=asset_type, asset_description=description,
            identifier_number=identifier if identifier else asset_id, estimated_value=value,
            location=location, is_future_asset=future, asset_id=asset_id,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(
            f"[bold green]✓ Collateral Asset Linked:[/bold green] [cyan]{result['asset_id']}[/cyan]\n"
            f"  [bold]Registration ID:[/bold] {result['registration_id']}\n"
            f"  [bold]Type:[/bold] {result['asset_type']} (Future Asset: {'Yes' if result['is_future_asset'] else 'No'})\n"
            f"  [bold]Identifier:[/bold] [bold yellow]{result['identifier_number']}[/bold yellow]\n"
            f"  [bold]Description:[/bold] {result['asset_description']}\n"
            f"  [bold]Estimated Value:[/bold] {result['estimated_value']:,.0f} VND\n"
            f"  [bold]Location:[/bold] {result['location']}\n"
            f"  [bold]Status:[/bold] [green]{result['status']}[/green]"
        )
    except Exception as e:
        console.print(f"[bold red]Error recording collateral asset:[/bold red] {e}")
        raise typer.Exit(code=1)


register_securedtransactions_operations(securedtransactions_app)
register_securedtransactions_queries(securedtransactions_app)

__all__ = [
    "securedtransactions_app", "app", "main", "register_cmd", "collateral_cmd", "priority_cmd", "disposal_cmd",
    "deregister_cmd", "search_cmd", "list_records_cmd", "status_cmd", "_render_status_dashboard",
    "AssetType", "DisposalMethod", "RegistrationStatus", "SecuredTransactionsEngine", "SecurityMeasureType",
]
