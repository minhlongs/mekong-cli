# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Extradition evaluation, sentence transfer, and bilateral treaty subcommands for Judicial Assistance CLI."""

from __future__ import annotations

import json
from typing import List, Optional

import typer
from rich.console import Console

from src.core.judicialassist_engine import JudicialAssistEngine

console = Console()


def register_judicialassist_operations(judicialassist_app: typer.Typer) -> None:
    """Register extradition, transfer, and treaty commands onto judicialassist_app."""
    judicialassist_app.command("extradition")(evaluate_extradition_cmd)
    judicialassist_app.command("transfer")(process_transfer_cmd)
    judicialassist_app.command("treaty")(register_treaty_cmd)


def evaluate_extradition_cmd(
    subject: str = typer.Option(..., "--subject", "-n", help="Full name of the subject requested for extradition"),
    nationality: str = typer.Option(..., "--nationality", help="Nationality of the subject"),
    direction: str = typer.Option("INCOMING", "--direction", "-d", help="Direction: INCOMING | OUTGOING"),
    country: str = typer.Option(..., "--country", "-c", help="Requesting / requested country"),
    ground: str = typer.Option("PROSECUTION_INVESTIGATION", "--ground", "-g", help="Ground: PROSECUTION_INVESTIGATION | SENTENCE_EXECUTION"),
    offense: str = typer.Option(..., "--offense", help="Name of offense committed"),
    penalty_months: int = typer.Option(24, "--penalty-months", help="Statutory penalty framework in months (minimum 12 for prosecution)"),
    remaining_months: int = typer.Option(0, "--remaining-months", help="Remaining sentence in months (minimum 6 for sentence execution)"),
    dual_criminality: bool = typer.Option(True, "--dual-criminality/--no-dual-criminality", help="Dual criminality satisfied"),
    provisional_arrest: bool = typer.Option(False, "--provisional-arrest/--no-provisional-arrest", help="Under provisional arrest (Art 41)"),
    arrest_date: Optional[str] = typer.Option(None, "--arrest-date", help="Date of provisional arrest (YYYY-MM-DD)"),
    vietnamese_citizen: bool = typer.Option(False, "--vietnamese-citizen/--not-vietnamese-citizen", help="Subject is a Vietnamese citizen (Art 35 k1a)"),
    limitations_expired: bool = typer.Option(False, "--expired-limitations/--valid-limitations", help="Statute of limitations expired (Art 35 k1b)"),
    ne_bis_in_idem: bool = typer.Option(False, "--ne-bis-in-idem/--no-prior-judgment", help="Prior final judgment rendered (Art 35 k1c)"),
    torture_risk: bool = typer.Option(False, "--torture-risk/--no-torture-risk", help="Risk of torture/persecution (Art 35 k1d)"),
    political_offense: bool = typer.Option(False, "--political-offense/--common-crime", help="Political or military offense (Art 35 k1đ)"),
    no_death_penalty_assurance: bool = typer.Option(False, "--no-death-penalty-assurance", help="No written assurance against death penalty (Art 35 k2a)"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Dossier status"),
    notes: str = typer.Option("", "--notes", help="Dossier notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Evaluate and record an Extradition Dossier according to statutory standards (Art 32-48)."""
    try:
        engine = JudicialAssistEngine()
        result = engine.evaluate_extradition(
            subject_name=subject,
            nationality=nationality,
            direction=direction,
            requesting_country=country,
            extradition_ground=ground,
            offense_name=offense,
            penalty_framework_months=penalty_months,
            remaining_sentence_months=remaining_months,
            dual_criminality=dual_criminality,
            provisional_arrest=provisional_arrest,
            arrest_date=arrest_date,
            is_vietnamese_citizen=vietnamese_citizen,
            statute_of_limitations_expired=limitations_expired,
            ne_bis_in_idem=ne_bis_in_idem,
            torture_persecution_risk=torture_risk,
            political_military_offense=political_offense,
            death_penalty_without_assurance=no_death_penalty_assurance,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        refusal = result["refusal_ground"]
        refusal_color = "red" if refusal != "NONE" else "green"
        console.print(f"[bold green]✓ Extradition Dossier Evaluated:[/bold green] [cyan]{result['dossier_id']}[/cyan]")
        console.print(f"  [bold]Subject:[/bold] {result['subject_name']} ({result['nationality']}) | [bold]Direction:[/bold] {result['direction']}")
        console.print(f"  [bold]Country:[/bold] {result['requesting_country']} | [bold]Offense:[/bold] {result['offense_name']}")
        console.print(f"  [bold]Ground:[/bold] {result['extradition_ground']} | [bold]Penalty Framework:[/bold] {result['penalty_framework_months']} mos")
        console.print(f"  [bold]Provisional Arrest:[/bold] {result['provisional_arrest'] == 1} (Date: {result['arrest_date'] or 'N/A'})")
        console.print(f"  [bold]Refusal Analysis:[/bold] [{refusal_color}]{refusal}[/{refusal_color}]")
        console.print(f"  [bold]Final Status:[/bold] [yellow]{result['status']}[/yellow]")
        if result["notes"]:
            console.print(f"  [bold]Notes:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error evaluating extradition dossier:[/bold red] {e}")
        raise typer.Exit(code=1)


def process_transfer_cmd(
    prisoner: str = typer.Option(..., "--prisoner", "-p", help="Full name of the sentenced prisoner"),
    nationality: str = typer.Option(..., "--nationality", help="Prisoner's nationality"),
    direction: str = typer.Option("OUTGOING", "--direction", "-d", help="Direction: OUTGOING | INCOMING"),
    from_country: str = typer.Option(..., "--from-country", help="Transferring state"),
    to_country: str = typer.Option(..., "--to-country", help="Receiving state"),
    original_months: int = typer.Option(..., "--original-months", help="Total sentence term in months"),
    served_months: int = typer.Option(..., "--served-months", help="Sentence term already served in months"),
    remaining_months: int = typer.Option(..., "--remaining-months", help="Sentence term remaining in months (minimum 12 mos)"),
    consent: bool = typer.Option(True, "--consent/--no-consent", help="Voluntary written consent of prisoner (Art 50 k1b)"),
    dual_criminality: bool = typer.Option(True, "--dual-criminality/--no-dual-criminality", help="Dual criminality satisfied (Art 50 k1d)"),
    compensation_cleared: bool = typer.Option(True, "--compensation-cleared/--compensation-pending", help="Civil liabilities cleared (Art 51 k1c)"),
    court_decision: Optional[str] = typer.Option(None, "--court-decision", help="Court transfer approval decision number"),
    status: str = typer.Option("SUBMITTED", "--status", "-s", help="Workflow status"),
    notes: str = typer.Option("", "--notes", help="Transfer notes and remarks"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Process and record the Transfer of a Sentenced Person under Art 49-64."""
    try:
        engine = JudicialAssistEngine()
        result = engine.process_sentence_transfer(
            prisoner_name=prisoner,
            prisoner_nationality=nationality,
            direction=direction,
            from_country=from_country,
            to_country=to_country,
            original_sentence_months=original_months,
            served_sentence_months=served_months,
            remaining_sentence_months=remaining_months,
            prisoner_written_consent=consent,
            dual_criminality=dual_criminality,
            civil_compensation_cleared=compensation_cleared,
            court_decision=court_decision,
            status=status,
            notes=notes,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Sentence Transfer Dossier Processed:[/bold green] [cyan]{result['transfer_id']}[/cyan]")
        console.print(f"  [bold]Prisoner:[/bold] {result['prisoner_name']} ({result['prisoner_nationality']})")
        console.print(f"  [bold]Route:[/bold] {result['from_country']} -> {result['to_country']}")
        console.print(f"  [bold]Sentence:[/bold] {result['served_sentence_months']}/{result['original_sentence_months']} mos served | [bold]Remaining:[/bold] {result['remaining_sentence_months']} mos")
        console.print(f"  [bold]Consent:[/bold] {result['prisoner_written_consent'] == 1} | [bold]Dual Criminality:[/bold] {result['dual_criminality'] == 1} | [bold]Civil Cleared:[/bold] {result['civil_compensation_cleared'] == 1}")
        console.print(f"  [bold]Status:[/bold] [yellow]{result['status']}[/yellow]")
        if result["notes"]:
            console.print(f"  [bold]Statutory Remarks:[/bold] [dim]{result['notes']}[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error processing sentence transfer:[/bold red] {e}")
        raise typer.Exit(code=1)


def register_treaty_cmd(
    country: str = typer.Option(..., "--country", "-c", help="Signatory country name"),
    title: str = typer.Option(..., "--title", "-t", help="Official title of the bilateral treaty"),
    signing_date: str = typer.Option(..., "--signing-date", help="Date of signing (YYYY-MM-DD)"),
    effective_date: str = typer.Option(..., "--effective-date", help="Date entry into force (YYYY-MM-DD)"),
    domains: List[str] = typer.Option(["CIVIL", "CRIMINAL", "EXTRADITION"], "--domain", "-d", help="Covered domains (e.g. CIVIL, CRIMINAL, EXTRADITION, SENTENCE_TRANSFER)"),
    active: bool = typer.Option(True, "--active/--inactive", help="Whether treaty is currently active"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Register a Bilateral Mutual Legal Assistance / Extradition Treaty."""
    try:
        engine = JudicialAssistEngine()
        result = engine.register_bilateral_treaty(
            country_name=country,
            treaty_title=title,
            signing_date=signing_date,
            effective_date=effective_date,
            covered_domains=domains,
            is_active=active,
        )
        if json_output:
            typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
            return

        console.print(f"[bold green]✓ Bilateral Treaty Registered:[/bold green] [cyan]{result['treaty_id']}[/cyan]")
        console.print(f"  [bold]Partner Country:[/bold] {result['country_name']}")
        console.print(f"  [bold]Title:[/bold] {result['treaty_title']}")
        console.print(f"  [bold]Timeline:[/bold] Signed: {result['signing_date']} | Effective: {result['effective_date']}")
        console.print(f"  [bold]Covered Domains:[/bold] {', '.join(result['covered_domains'])}")
        console.print(f"  [bold]Active Status:[/bold] [green]{'ACTIVE' if result['is_active'] == 1 else 'INACTIVE'}[/green]")
    except Exception as e:
        console.print(f"[bold red]Error registering bilateral treaty:[/bold red] {e}")
        raise typer.Exit(code=1)
