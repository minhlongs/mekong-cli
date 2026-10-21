# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Priority ranking, disposal notice, and deregistration subcommands for Secured Transactions CLI."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from src.core.securedtransactions_engine import SecuredTransactionsEngine

console = Console()


def register_securedtransactions_operations(securedtransactions_app: typer.Typer) -> None:
    """Register priority, disposal, and deregister commands onto securedtransactions_app."""
    securedtransactions_app.command("priority")(priority_cmd)
    securedtransactions_app.command("disposal")(disposal_cmd)
    securedtransactions_app.command("deregister")(deregister_cmd)


def priority_cmd(
    identifier: str = typer.Argument(..., help="Asset unique identifier number (VIN, Land Certificate No)"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
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


def disposal_cmd(
    reg_id: str = typer.Argument(..., help="Security registration ID"),
    asset_id: str = typer.Argument(..., help="Collateral asset ID"),
    method: str = typer.Argument("AUCTION", help="Disposal method: AUCTION | PRIVATE_SALE | DEBT_OFFSET | OTHER"),
    reason: str = typer.Option("Bên bảo đảm không thực hiện nghĩa vụ trả nợ", "--reason", help="Statutory reason for disposal (default on loan, breach)"),
    date: str = typer.Option("2026-11-15", "--date", "--disposal-date", help="Expected disposal date (YYYY-MM-DD)"),
    party: Optional[str] = typer.Option(None, "--party", "-p", "--notifying-party", "--authorized-officer", help="Notifying secured creditor"),
    recovery_target: float = typer.Option(0.0, "--recovery-target", help="Target recovery amount in VND"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
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


def deregister_cmd(
    reg_id: str = typer.Argument(..., help="Security registration ID"),
    reason: str = typer.Argument("OBLIGATION_FULFILLED", help="Deregistration reason"),
    party: str = typer.Option("Bên bảo đảm", "--party", "-p", "--requesting-party", help="Requesting party (Secured party or securing party)"),
    officer: str = typer.Option("Chuyên viên Đăng ký Giao dịch bảo đảm", "--officer", help="Approving registrar officer"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
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
