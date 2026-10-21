# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI Command Suite for Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision."""

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.procuracy_engine import DetentionMeasure, ProcuracyEngine, ProcuracyLevel, ProsecutorRank, ProtestType

procuracy_app = typer.Typer(name="procuracy", help="Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Luật Tổ chức VKSND 2014)", invoke_without_command=True)
app = procuracy_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(Panel.fit("[bold cyan]VIỆN KIỂM SÁT NHÂN DÂN TỐI CAO — HỆ THỐNG CÔNG TỐ & KIỂM SÁT TƯ PHÁP[/bold cyan]\n[dim]Supreme People's Procuracy, Public Prosecution & Detention Supervision Hub (Luật Tổ chức VKSND 2014)[/dim]", box=box.DOUBLE, border_style="cyan"))
    telemetry = status_data.get("telemetry", {})
    table = Table(title="People's Procuracy Telemetry", box=box.ROUNDED, show_header=True)
    for col, st in (("Category", "bold green"), ("Metric", "cyan"), ("Value", "bold yellow")):
        table.add_column(col, style=st)
    pros, ind, det, prot = telemetry.get("prosecutors", {}), telemetry.get("criminal_indictments", {}), telemetry.get("detention_supervisions", {}), telemetry.get("judicial_protests", {})
    for cat, m, val in (
        ("Prosecutors", "Total Appointed", str(pros.get("total", 0))), ("Prosecutors", "Active Practicing", str(pros.get("active", 0))),
        ("Criminal Indictments", "Total Indictments Issued", str(ind.get("total_indictments", 0))), ("Criminal Indictments", "Pending Trial", str(ind.get("pending_trial", 0))),
        ("Criminal Indictments", "Convicted by Court", str(ind.get("convicted", 0))), ("Detention Supervisions", "Total Custody Inspections", str(det.get("total_inspections", 0))),
        ("Detention Supervisions", "Compliant Facilities", str(det.get("compliant", 0))), ("Detention Supervisions", "Overdue Releases Ordered", str(det.get("overdue_releases_ordered", 0))),
        ("Judicial Protests", "Total Protests Filed", str(prot.get("total_protests", 0))), ("Judicial Protests", "Pending Hearing", str(prot.get("pending_hearing", 0))),
        ("Judicial Protests", "Protests Accepted by Court", str(prot.get("protests_accepted", 0))),
    ):
        table.add_row(cat, m, val)
    console.print(table)


@procuracy_app.callback()
def main_callback(ctx: typer.Context, json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """Vietnamese People's Procuracy Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        status_data = ProcuracyEngine().get_telemetry_status()
        typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2)) if json_output else _render_status_dashboard(status_data)


@procuracy_app.command("prosecutor")
def register_prosecutor_cmd(
    badge: str = typer.Option(..., "--badge", "-b", help="Prosecutor badge number"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of prosecutor"),
    rank: str = typer.Option(..., "--rank", "-r", help="KIEM_SAT_VIEN_SO_CAP, KIEM_SAT_VIEN_TRUNG_CAP, KIEM_SAT_VIEN_CAO_CAP, KIEM_SAT_VIEN_VKSNDTC"),
    level: str = typer.Option(..., "--level", "-l", help="VKSND_CAP_HUYEN, VKSND_CAP_TINH, VKSND_CAP_CAO, VKSND_TOI_CAO, VIEN_KIEM_SAT_QUAN_SU"),
    office: str = typer.Option(..., "--office", "-o", help="Office or division unit"),
    date: Optional[str] = typer.Option(None, "--date", help="Appointment date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, TRANSFERRED, RETIRED, SUSPENDED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Register or update a Procurator (Kiểm sát viên) under Article 74 Law on Organization of People's Procuracies."""
    result = ProcuracyEngine().register_prosecutor(badge_number=badge, full_name=name, rank=rank, procuracy_level=level, office_unit=office, appointment_date=date, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result.get("success"):
        p = result["prosecutor"]
        console.print(f"[bold green]✓ Prosecutor Registered:[/bold green] {p['badge_number']} - {p['full_name']} ({p['rank']} | {p['procuracy_level']} | {p['office_unit']})")
    else:
        console.print(f"[bold red]✗ Failed to register prosecutor:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("indictment")
def issue_indictment_cmd(
    number: str = typer.Option(..., "--number", "-n", help="Indictment number"),
    case: str = typer.Option(..., "--case", "-c", help="Official criminal case name"),
    accused: str = typer.Option(..., "--accused", "-a", help="Accused person / defendant full name"),
    article: str = typer.Option(..., "--article", help="Penal Code article charged"),
    prosecutor: str = typer.Option(..., "--prosecutor", "-p", help="Badge number of prosecuting attorney"),
    court: str = typer.Option(..., "--court", help="Designated trial court with jurisdiction"),
    date: Optional[str] = typer.Option(None, "--date", help="Issuing date (YYYY-MM-DD)"),
    status: str = typer.Option("ISSUED", "--status", help="ISSUED, REMANDED_INVESTIGATION, WITHDRAWN, CONVICTED, ACQUITTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Issue or track a criminal prosecution indictment under Article 243 Criminal Procedure Code."""
    result = ProcuracyEngine().issue_indictment(indictment_number=number, case_name=case, accused_name=accused, penal_code_article=article, prosecutor_badge=prosecutor, trial_court=court, issuing_date=date, status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result.get("success"):
        i = result["indictment"]
        console.print(f"[bold green]✓ Criminal Indictment Issued:[/bold green] {i['indictment_number']} ({i['case_name']} | {i['accused_name']} | {i['penal_code_article']})")
    else:
        console.print(f"[bold red]✗ Failed to issue indictment:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("detention")
def record_detention_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Detention inspection code"),
    facility: str = typer.Option(..., "--facility", "-f", help="Detention facility name"),
    detainee: str = typer.Option(..., "--detainee", "-d", help="Full name of detained person"),
    measure: str = typer.Option(..., "--measure", "-m", help="Detention measure: TAM_GIU, TAM_GIAM"),
    start: str = typer.Option(..., "--start", help="Custody start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="Custody expiration date (YYYY-MM-DD)"),
    inspector: str = typer.Option(..., "--inspector", help="Badge number of supervising inspector"),
    status: str = typer.Option("COMPLIANT", "--status", help="COMPLIANT, OVERDUE_RELEASE_ORDERED, UNLAWFUL_RELEASED, SANCTIONED"),
    date: Optional[str] = typer.Option(None, "--date", help="Inspection date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Supervision findings or release orders"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Supervise legality of arrest, custody, and temporary detention under Articles 22-26 Law on Organization of People's Procuracies."""
    result = ProcuracyEngine().record_detention_supervision(supervision_code=code, detention_facility=facility, detainee_name=detainee, measure_type=measure, custody_start_date=start, custody_end_date=end, inspector_badge=inspector, compliance_status=status, inspection_date=date, notes=notes)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result.get("success"):
        d = result["detention_supervision"]
        console.print(f"[bold green]✓ Detention Supervision Recorded:[/bold green] {d['supervision_code']} ({d['detention_facility']} | {d['detainee_name']} | {d['compliance_status']})")
    else:
        console.print(f"[bold red]✗ Failed to record detention supervision:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("protest")
def file_protest_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Protest code"),
    judgment: str = typer.Option(..., "--judgment", "-j", help="Judgment number protested"),
    court: str = typer.Option(..., "--court", help="Court issuing the protested judgment"),
    type: str = typer.Option(..., "--type", "-t", help="Protest type: PHUC_THAM, GIAM_DOC_THAM, TAI_THAM"),
    ground: str = typer.Option(..., "--ground", "-g", help="Legal grounds / serious violation identified"),
    prosecutor: str = typer.Option(..., "--prosecutor", "-p", help="Badge number of protesting prosecutor"),
    date: Optional[str] = typer.Option(None, "--date", help="Filing date (YYYY-MM-DD)"),
    status: str = typer.Option("PENDING", "--status", help="PENDING, ACCEPTED, REJECTED, MODIFIED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
) -> None:
    """Issue an appellate, cassation, or reopening protest against court judgment under Articles 27-31."""
    result = ProcuracyEngine().file_judicial_protest(protest_code=code, judgment_number=judgment, court_issued=court, protest_type=type, legal_ground=ground, prosecutor_badge=prosecutor, filing_date=date, hearing_status=status)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if result.get("success"):
        pr = result["judicial_protest"]
        console.print(f"[bold green]✓ Judicial Protest Filed:[/bold green] {pr['protest_code']} ({pr['protest_type']} | {pr['judgment_number']} | {pr['hearing_status']})")
    else:
        console.print(f"[bold red]✗ Failed to file judicial protest:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("list")
def list_cmd(category: str = typer.Option("prosecutors", "--category", "-c", help="prosecutors, indictments, detentions, protests"), limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to return"), json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """List records from People's Procuracy database by category."""
    result = ProcuracyEngine().list_records(category=category, limit=limit)
    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return
    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)
    records, cat = result.get("records", []), result.get("category", "")
    table = Table(title=f"People's Procuracy Records: {cat.upper()} ({len(records)} found)", box=box.ROUNDED)
    if cat in ("prosecutors", "prosecutor"):
        for col, st in (("Badge", "cyan"), ("Name", "bold white"), ("Rank", "green"), ("Level", "yellow"), ("Unit", "magenta"), ("Status", "bold green")):
            table.add_column(col, style=st)
        for r in records:
            table.add_row(r.get("badge_number"), r.get("full_name"), r.get("rank"), r.get("procuracy_level"), r.get("office_unit"), r.get("status"))
    elif cat in ("indictments", "indictment"):
        for col, st in (("Indictment No", "cyan"), ("Case", "bold white"), ("Accused", "yellow"), ("Article", "magenta"), ("Prosecutor", "white"), ("Status", "bold green")):
            table.add_column(col, style=st)
        for r in records:
            table.add_row(r.get("indictment_number"), r.get("case_name"), r.get("accused_name"), r.get("penal_code_article"), r.get("prosecutor_badge"), r.get("status"))
    elif cat in ("detentions", "detention"):
        for col, st in (("Code", "cyan"), ("Facility", "bold white"), ("Detainee", "yellow"), ("Measure", "green"), ("Start -> End", "white"), ("Compliance", "bold magenta")):
            table.add_column(col, style=st)
        for r in records:
            table.add_row(r.get("supervision_code"), r.get("detention_facility"), r.get("detainee_name"), r.get("measure_type"), f"{r.get('custody_start_date')} -> {r.get('custody_end_date')}", r.get("compliance_status"))
    elif cat in ("protests", "protest"):
        for col, st in (("Code", "cyan"), ("Judgment No", "white"), ("Target Court", "bold white"), ("Type", "yellow"), ("Ground", "green"), ("Status", "bold magenta")):
            table.add_column(col, style=st)
        for r in records:
            g = r.get("legal_ground", "")
            table.add_row(r.get("protest_code"), r.get("judgment_number"), r.get("court_issued"), r.get("protest_type"), g[:40] + ("..." if len(g) > 40 else ""), r.get("hearing_status"))
    console.print(table)


@procuracy_app.command("status")
def status_cmd(json_output: bool = typer.Option(False, "--json", help="Output in JSON format")) -> None:
    """Display People's Procuracy & Public Prosecution telemetry status."""
    data = ProcuracyEngine().get_telemetry_status()
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2)) if json_output else _render_status_dashboard(data)


__all__ = ["DetentionMeasure", "ProcuracyEngine", "ProcuracyLevel", "ProsecutorRank", "ProtestType", "app", "procuracy_app"]
