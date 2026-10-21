# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Divorce, child custody, property settlement, search, list & status commands."""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.table import Table

from src.cli.commands.marriage_reg_asset_commands import _render_status_dashboard
from src.core.marriage_engine import MarriageEngine

console = Console()


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
            marriage_id=marriage_id, divorce_type=divorce_type, petitioner=petitioner,
            grounds=grounds, court_name=court, filing_date=date,
            has_domestic_violence=domestic_violence, wife_is_pregnant=wife_pregnant,
            nursing_child_under_12m=nursing_child,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(f"[bold yellow]✓ Divorce Petition Filed:[/bold yellow] [cyan]{result['petition_id']}[/cyan]")
        console.print(f"  [bold]Marriage ID:[/bold] {result['marriage_id']} | [bold]Type:[/bold] {result['divorce_type']}")
        console.print(f"  [bold]Petitioner:[/bold] {result['petitioner']} | [bold]Grounds:[/bold] {result['grounds']}")
        console.print(f"  [bold]Court:[/bold] {result['court_name']} | [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
    except Exception as e:
        console.print(f"[bold red]Error filing divorce petition:[/bold red] {e}")
        raise typer.Exit(code=1)


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
            petition_id=petition_id, child_name=child_name, child_dob=child_dob,
            custodial_parent=custodial_parent, monthly_support_vnd=support_amount,
            effective_date=date, notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(f"[bold green]✓ Child Custody & Support Order Granted:[/bold green] [cyan]{result['order_id']}[/cyan]")
        console.print(f"  [bold]Child:[/bold] {result['child_name']} (DOB: {result['child_dob']})")
        console.print(f"  [bold]Custodial Parent:[/bold] [green]{result['custodial_parent']}[/green] | [bold]Payer:[/bold] {result['non_custodial_parent']}")
        console.print(f"  [bold]Monthly Support:[/bold] [bold yellow]{result['monthly_support_vnd']:,.0f} VND/month[/bold yellow]")
        if result.get("notes"):
            console.print(f"  [bold]Statutory Notes:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing child custody and support:[/bold red] {e}")
        raise typer.Exit(code=1)


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
            petition_id=petition_id, judgment_number=judgment_number,
            resolution_date=date, husband_contribution_percent=husband_percent,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(f"[bold green]✓ Divorce & Property Settlement Finalized:[/bold green] [cyan]{result['petition_id']}[/cyan]")
        console.print(f"  [bold]Judgment Number:[/bold] {result['judgment_number']} | [bold]Common Wealth:[/bold] {result['total_common_value_vnd']:,.0f} VND")
        console.print(f"  [bold]Husband ({result['husband_contribution_percent']:.0f}%):[/bold] [cyan]{result['husband_total_allocation_vnd']:,.0f} VND[/cyan]")
        console.print(f"  [bold]Wife ({result['wife_contribution_percent']:.0f}%):[/bold] [magenta]{result['wife_total_allocation_vnd']:,.0f} VND[/magenta]")
    except Exception as e:
        console.print(f"[bold red]Error settling divorce:[/bold red] {e}")
        raise typer.Exit(code=1)


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
        for col, st in [("Marriage ID", "cyan"), ("Certificate", "yellow"), ("Husband", "white"), ("Wife", "magenta"), ("Reg Date", "green"), ("Regime", "cyan"), ("Status", "bold green")]:
            table.add_column(col, style=st)
        for r in records[:limit]:
            table.add_row(r["marriage_id"], r["certificate_number"], r["husband_name"], r["wife_name"], r["registration_date"], r["property_regime"], r["status"])
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Error searching marriage records:[/bold red] {e}")
        raise typer.Exit(code=1)


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
