# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Search, list, status subcommands, and dashboard renderer for Secured Transactions CLI."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.securedtransactions_engine import SecuredTransactionsEngine

console = Console()


def render_securedtransactions_dashboard(console_inst: Console, status_data: dict) -> None:
    """Render the National Secured Transactions telemetry dashboard."""
    console_inst.print(
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

    table.add_row("Security Registrations", "National Registry Centers (BTP)", "Total Registrations", str(status_data.get("total_security_registrations", 0)))
    table.add_row("Active Registrations", "Valid Security Interests (Điều 297 BLDS)", "Active Registrations", str(status_data.get("active_security_registrations", 0)))
    table.add_row("Secured Value (VND)", "Registered Secured Credit", "Total Secured Amount", f"{status_data.get('total_secured_obligation_value_vnd', 0.0):,.0f} VND")
    table.add_row("Collateral Assets", "Real Estate, Movables, Rights", "Total Collateral Assets", str(status_data.get("total_collateral_assets", 0)))
    table.add_row("Collateral Value (VND)", "Estimated Collateral Appraisal", "Total Collateral Valuation", f"{status_data.get('total_collateral_value_vnd', 0.0):,.0f} VND")
    table.add_row("Priority Rankings", "Statutory Payment Order (Điều 308 BLDS)", "Active Priority Records", str(status_data.get("active_priority_rankings", 0)))
    table.add_row("Disposal Notices", "Collateral Enforcement (Điều 51 NĐ 99)", "Active Disposal Notices", str(status_data.get("active_disposal_notices", 0)))
    table.add_row("Deregistrations", "Obligations Released (Điều 52 NĐ 99)", "Deregistrations Processed", str(status_data.get("deregistrations_processed", 0)))
    table.add_row("Compliance Logs", "Inter-Agency Audit Trail", "Audit Events", str(status_data.get("audit_logs_count", 0)))

    console_inst.print(table)


def register_securedtransactions_queries(securedtransactions_app: typer.Typer) -> None:
    """Register search, list, and status commands onto securedtransactions_app."""
    securedtransactions_app.command("search")(search_cmd)
    securedtransactions_app.command("list")(list_records_cmd)
    securedtransactions_app.command("status")(status_cmd)


def search_cmd(
    query: Optional[str] = typer.Argument(None, help="Search query (contract number, debtor ID, debtor name, or asset identifier)"),
    query_opt: Optional[str] = typer.Option(None, "--query", "-q", help="Search query string"),
    reg_type: Optional[str] = typer.Option(None, "--reg-type", help="Registration measure type filter"),
    asset_type: Optional[str] = typer.Option(None, "--asset-type", help="Asset type filter"),
    authority: Optional[str] = typer.Option(None, "--authority", help="Registry authority filter"),
    status: Optional[str] = typer.Option(None, "--status", help="Status filter"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum search results"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
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


def list_records_cmd(
    category: str = typer.Option("registration", "--category", "-c", help="Category: registration | collateral | priority | disposal | deregistration | audit"),
    status: Optional[str] = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Pagination offset"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
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


def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Show national secured transactions registry statistics."""
    engine = SecuredTransactionsEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    render_securedtransactions_dashboard(console, status_data)
