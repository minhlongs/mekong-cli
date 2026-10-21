# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""List, status subcommands, and dashboard renderer for Judicial Assistance CLI."""

from __future__ import annotations

import json

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.judicialassist_engine import JudicialAssistEngine

console = Console()


def render_judicialassist_dashboard(console_inst: Console, status_data: dict) -> None:
    """Render the Mutual Legal Assistance & Cross-Border Judicial Cooperation dashboard."""
    console_inst.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG TƯƠNG TRỢ TƯ PHÁP QUỐC TẾ[/bold cyan]\n"
            "[dim]Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Hub (Luật Tương trợ tư pháp 2007)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Cross-Border Judicial Assistance Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Domain / Pillar", style="bold green")
    table.add_column("Focal Authority", style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="bold yellow")

    table.add_row("Civil MLA (Dân sự)", "Ministry of Justice (Bộ Tư pháp)", "Total Requests", str(status_data.get("total_civil_requests", 0)))
    table.add_row("Civil MLA (Dân sự)", "Ministry of Justice", "Total Costs (USD)", f"${status_data.get('total_civil_costs_usd', 0.0):,.2f}")
    table.add_row("Criminal MLA (Hình sự)", "Supreme People's Procuracy (VKSNDTC)", "Total Requests", str(status_data.get("total_criminal_requests", 0)))
    table.add_row("Criminal MLA (Hình sự)", "Supreme People's Procuracy", "Asset Value (VND)", f"{status_data.get('total_criminal_assets_vnd', 0.0):,.0f} VND")
    table.add_row("Extradition (Dẫn độ)", "Ministry of Public Security (Bộ Công an)", "Total Dossiers", str(status_data.get("total_extradition_dossiers", 0)))
    table.add_row("Extradition (Dẫn độ)", "Ministry of Public Security", "Refused / Barred", str(status_data.get("refused_extraditions", 0)))
    table.add_row("Sentence Transfer (Chuyển giao)", "Ministry of Public Security (Bộ Công an)", "Total Transfers", str(status_data.get("total_sentence_transfers", 0)))
    table.add_row("Sentence Transfer (Chuyển giao)", "Ministry of Public Security", "Completed", str(status_data.get("completed_sentence_transfers", 0)))
    table.add_row("Bilateral Treaties", "Ministry of Foreign Affairs (Bộ Ngoại giao)", "Active Treaties", str(status_data.get("active_bilateral_treaties", 0)))
    table.add_row("Compliance Logs", "Inter-Agency Audit Trail", "Audit Events", str(status_data.get("audit_logs_count", 0)))

    console_inst.print(table)


def register_judicialassist_queries(judicialassist_app: typer.Typer) -> None:
    """Register list and status commands onto judicialassist_app."""
    judicialassist_app.command("list")(list_records_cmd)
    judicialassist_app.command("status")(status_cmd)


def list_records_cmd(
    category: str = typer.Option("civil", "--category", "-c", help="Category: civil | criminal | extradition | transfer | treaty | audit"),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of records to retrieve"),
    offset: int = typer.Option(0, "--offset", "-o", help="Offset for pagination"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """List cross-border judicial assistance records by category."""
    try:
        engine = JudicialAssistEngine()
        records = engine.list_records(category=category.lower().strip(), limit=limit, offset=offset)

        if json_output:
            typer.echo(json.dumps(records, ensure_ascii=False, indent=2))
            return

        if not records:
            console.print(f"[yellow]No records found for category '{category}'.[/yellow]")
            return

        table = Table(title=f"Cross-Border Records — {category.upper()}", box=box.ROUNDED)
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
    """Show cross-border judicial assistance telemetry and system status."""
    engine = JudicialAssistEngine()
    status_data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
        return

    render_judicialassist_dashboard(console, status_data)
