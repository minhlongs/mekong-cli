"""Indictment, custody inspection, list, and status commands for People's Procuracy Suite."""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.table import Table

from src.cli.commands._prosecution_renderers import console, render_prosecution_records
from src.core.prosecution_engine import ProsecutionEngine


def register_prosecution_supervision_commands(app: typer.Typer) -> None:
    """Register indictment, inspection, list, and status subcommands."""

    @app.command("indictment")
    def issue_indictment_cmd(
        indictment_id: str = typer.Option(..., "--id", "-i", help="Indictment registration ID (e.g. CT-2024-0089)."),
        case_id: str = typer.Option(..., "--case-id", "-c", help="Criminal case ID being prosecuted."),
        defendant: str = typer.Option(..., "--defendant", "-d", help="Full name of defendant/accused person."),
        offense: str = typer.Option(..., "--offense", help="Charged crime / offense title."),
        clause: str = typer.Option(..., "--clause", help="Applicable clause and article of Penal Code."),
        procuracy: str = typer.Option(..., "--procuracy", help="Issuing People's Procuracy."),
        procurator: str = typer.Option(..., "--procurator", help="Signing Procurator ID."),
        decision: str = typer.Option("PROCEED_TRIAL", "--decision", help="Decision: PROCEED_TRIAL, RETURN_ADDITIONAL_INVESTIGATION, WITHDRAW_SUSPEND."),
        issue_date: Optional[str] = typer.Option(None, "--issue-date", help="Date of issuance in YYYY-MM-DD format."),
        json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
    ) -> None:
        """Issue a formal prosecutorial indictment (Cáo trạng) under Articles 243-244 BLTTHS 2015."""
        engine = ProsecutionEngine()
        try:
            res = engine.issue_indictment(
                indictment_id=indictment_id,
                case_id=case_id,
                defendant_name=defendant,
                charged_offense=offense,
                applicable_clause=clause,
                issuing_procuracy=procuracy,
                signing_procurator_id=procurator,
                prosecution_decision=decision,
                issue_date=issue_date,
            )
        except Exception as e:
            console.print(f"[bold red]Error issuing indictment:[/bold red] {e}")
            raise typer.Exit(code=1)

        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
            return

        console.print(f"[bold green]✓ Issued Indictment {res['indictment_id']} for Defendant {res['defendant_name']}![/bold green]")
        console.print(f"  Offense: [yellow]{res['charged_offense']} ({res['applicable_clause']})[/yellow] | Decision: [bold cyan]{res['prosecution_decision']}[/bold cyan]")

    @app.command("inspection")
    def record_custody_inspection_cmd(
        inspection_id: str = typer.Option(..., "--id", "-i", help="Custody inspection ID (e.g. KS-TG-2024-0012)."),
        facility: str = typer.Option(..., "--facility", "-f", help="Detention facility or prison name."),
        procuracy: str = typer.Option(..., "--procuracy", help="Inspecting People's Procuracy."),
        procurator: str = typer.Option(..., "--procurator", help="Lead inspecting Procurator ID."),
        checked: int = typer.Option(10, "--checked", help="Total detainees or prisoners inspected."),
        violations: int = typer.Option(0, "--violations", help="Infractions or legal violations detected."),
        protest: bool = typer.Option(False, "--protest/--no-protest", help="Whether formal protest / corrective demand was issued."),
        compliance: str = typer.Option("STANDARD_COMPLIANT", "--compliance", help="Compliance: STANDARD_COMPLIANT, CORRECTIVE_DEMAND_ISSUED, FORMAL_PROTEST_FILED."),
        date: Optional[str] = typer.Option(None, "--date", help="Inspection date in YYYY-MM-DD format."),
        json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
    ) -> None:
        """Record inspection of detention facility and prison execution under Law on Execution of Criminal Judgments 2019."""
        engine = ProsecutionEngine()
        try:
            res = engine.record_custody_inspection(
                inspection_id=inspection_id,
                facility_name=facility,
                inspecting_procuracy=procuracy,
                lead_procurator_id=procurator,
                detainees_checked_count=checked,
                violations_detected_count=violations,
                protest_recommendation_issued=protest,
                compliance_status=compliance,
                inspection_date=date,
            )
        except Exception as e:
            console.print(f"[bold red]Error recording custody inspection:[/bold red] {e}")
            raise typer.Exit(code=1)

        if json_output:
            typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
            return

        console.print(f"[bold green]✓ Recorded Custody Inspection {res['inspection_id']} at {res['facility_name']}![/bold green]")
        console.print(f"  Detainees: {res['detainees_checked_count']} | Violations: {res['violations_detected_count']} | Status: [cyan]{res['compliance_status']}[/cyan]")

    @app.command("list")
    def list_records_cmd(
        category: str = typer.Option("all", "--category", "-c", help="Category: procurators, reports, cases, indictments, inspections, all."),
        limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to retrieve."),
        json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
    ) -> None:
        """List records from the People's Procuracy and Public Prosecution database."""
        engine = ProsecutionEngine()
        records = engine.list_records(category=category, limit=limit)
        if json_output:
            typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
            return
        render_prosecution_records(records)

    @app.command("status")
    def status_cmd(
        json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
    ) -> None:
        """Display telemetry metrics for the People's Procuracy and Public Prosecution Suite."""
        engine = ProsecutionEngine()
        telemetry = engine.get_telemetry_status()
        if json_output:
            typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
            return
        table = Table(title="People's Procuracy & Public Prosecution Telemetry", box=box.ROUNDED)
        table.add_column("Indicator", style="bold cyan")
        table.add_column("Value", style="bold green")
        for k, v in telemetry.items():
            table.add_row(k.replace("_", " ").title(), str(v))
        console.print(table)
