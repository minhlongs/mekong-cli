"""CLI Command Suite for Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation."""

from __future__ import annotations

import json

import typer
from rich.console import Console

from src.cli.commands._judicialassist_operations import (
    evaluate_extradition_cmd, process_transfer_cmd,
    register_judicialassist_operations, register_treaty_cmd,
)
from src.cli.commands._judicialassist_queries import (
    list_records_cmd, register_judicialassist_queries,
    render_judicialassist_dashboard, status_cmd,
)
from src.core.judicialassist_engine import (
    CivilRequestType, CooperationBasis, CriminalRequestType, ExtraditionGround,
    JudicialAssistEngine, RefusalGround, RequestDirection, WorkflowStatus,
)

judicialassist_app = typer.Typer(
    name="judicialassist",
    help="Vietnamese Mutual Legal Assistance, Extradition & Cross-Border Judicial Cooperation Suite (Luật Tương trợ tư pháp 2007)",
    invoke_without_command=True,
)
app = judicialassist_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    render_judicialassist_dashboard(console, status_data)


@judicialassist_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Vietnamese Mutual Legal Assistance Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        status_data = JudicialAssistEngine().get_telemetry_status()
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2)) if json_output else _render_status_dashboard(status_data)


@judicialassist_app.command("civil")
def create_civil_cmd(
    case_code: str = typer.Option(..., "--case-code", "-c", help="Court civil case code (e.g. 15/2026/TLST-DS)"),
    direction: str = typer.Option("OUTGOING", "--direction", "-d", help="Direction: OUTGOING | INCOMING"),
    request_type: str = typer.Option("SERVICE_OF_DOCUMENTS", "--type", "-t", help="Type: SERVICE_OF_DOCUMENTS | EVIDENCE_COLLECTION | ASSET_VERIFICATION | EXPERT_SUMMONS"),
    requesting_body: str = typer.Option(..., "--requesting-body", "-r", help="Requesting court or judicial body"),
    foreign_country: str = typer.Option(..., "--foreign-country", "-f", help="Target foreign country name"),
    target_person: str = typer.Option(..., "--target", help="Name of target person or entity"),
    service_address: str = typer.Option(..., "--address", help="Service address in target country"),
    basis: str = typer.Option("BILATERAL_TREATY", "--basis", help="Basis: BILATERAL_TREATY | MULTILATERAL_CONVENTION | RECIPROCITY_PRINCIPLE"),
    costs_usd: float = typer.Option(0.0, "--costs-usd", help="Estimated judicial service costs in USD"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Workflow status"),
    notes: str = typer.Option("", "--notes", help="Case notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Submit and record a Civil Mutual Legal Assistance Request under Art 10-16."""
    try:
        result = JudicialAssistEngine().create_civil_request(
            case_code=case_code, direction=direction, request_type=request_type,
            requesting_body=requesting_body, foreign_country=foreign_country,
            target_person_org=target_person, service_address=service_address,
            cooperation_basis=basis, costs_usd=costs_usd, status=status, notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(
            f"[bold green]✓ Civil Mutual Legal Assistance Request Registered:[/bold green] [cyan]{result['request_id']}[/cyan]\n"
            f"  [bold]Case Code:[/bold] {result['case_code']} | [bold]Direction:[/bold] {result['direction']}\n"
            f"  [bold]Type:[/bold] {result['request_type']} | [bold]Country:[/bold] {result['foreign_country']}\n"
            f"  [bold]Target:[/bold] {result['target_person_org']} | [bold]Costs:[/bold] ${result['costs_usd']:,.2f}\n"
            f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]"
        )
    except Exception as e:
        console.print(f"[bold red]Error registering civil request:[/bold red] {e}")
        raise typer.Exit(code=1)


@judicialassist_app.command("criminal")
def create_criminal_cmd(
    case_code: str = typer.Option(..., "--case-code", "-c", help="Criminal case dossier number"),
    direction: str = typer.Option("OUTGOING", "--direction", "-d", help="Direction: OUTGOING | INCOMING"),
    request_type: str = typer.Option("TESTIMONY_EXTRACTION", "--type", "-t", help="Type: TESTIMONY_EXTRACTION | SEARCH_AND_SEIZURE | CRIME_SCENE_EXAMINATION | ASSET_FREEZE_CONFISCATION | CRIMINAL_RECORD_CHECK"),
    agency: str = typer.Option(..., "--agency", "-a", help="Requesting agency (VKSND / CQĐT)"),
    foreign_country: str = typer.Option(..., "--foreign-country", "-f", help="Target foreign country"),
    offense: str = typer.Option(..., "--offense", help="Alleged offense description"),
    dual_criminality: bool = typer.Option(True, "--dual-criminality/--no-dual-criminality", help="Dual criminality satisfied"),
    basis: str = typer.Option("BILATERAL_TREATY", "--basis", help="Basis: BILATERAL_TREATY | MULTILATERAL_CONVENTION | RECIPROCITY_PRINCIPLE"),
    asset_vnd: float = typer.Option(0.0, "--asset-vnd", help="Asset value for freeze/confiscation in VND"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Workflow status"),
    notes: str = typer.Option("", "--notes", help="Case notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Submit and record a Criminal Mutual Legal Assistance Request under Art 17-31."""
    try:
        result = JudicialAssistEngine().create_criminal_request(
            case_code=case_code, direction=direction, request_type=request_type,
            requesting_agency=agency, foreign_country=foreign_country, alleged_offense=offense,
            dual_criminality=dual_criminality, cooperation_basis=basis, asset_value_vnd=asset_vnd,
            status=status, notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return
        console.print(
            f"[bold green]✓ Criminal Mutual Legal Assistance Request Registered:[/bold green] [cyan]{result['request_id']}[/cyan]\n"
            f"  [bold]Case Code:[/bold] {result['case_code']} | [bold]Direction:[/bold] {result['direction']}\n"
            f"  [bold]Agency:[/bold] {result['requesting_agency']} | [bold]Country:[/bold] {result['foreign_country']}\n"
            f"  [bold]Offense:[/bold] {result['alleged_offense']} | [bold]Dual Criminality:[/bold] {result['dual_criminality'] == 1}\n"
            f"  [bold]Asset Value:[/bold] {result['asset_value_vnd']:,.0f} VND | [bold]Status:[/bold] [yellow]{result['status']}[/yellow]"
        )
    except Exception as e:
        console.print(f"[bold red]Error registering criminal request:[/bold red] {e}")
        raise typer.Exit(code=1)


register_judicialassist_operations(judicialassist_app)
register_judicialassist_queries(judicialassist_app)

__all__ = [
    "judicialassist_app", "app", "main_callback", "create_civil_cmd", "create_criminal_cmd",
    "evaluate_extradition_cmd", "process_transfer_cmd", "register_treaty_cmd",
    "list_records_cmd", "status_cmd", "_render_status_dashboard", "JudicialAssistEngine",
    "CivilRequestType", "CriminalRequestType", "ExtraditionGround", "RefusalGround",
    "RequestDirection", "CooperationBasis", "WorkflowStatus",
]
