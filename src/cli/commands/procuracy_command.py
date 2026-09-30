"""
CLI Command Suite for Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision.
Compliant with:
- Law on Organization of the People's Procuracies 2014 (Luật Tổ chức Viện kiểm sát nhân dân - Law No. 63/2014/QH13)
- Criminal Procedure Code 2015 (Luật Tố tụng hình sự - Law No. 101/2015/QH13, amended 2021)
- Law on Temporary Detention and Custody 2015
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.procuracy_engine import (
    ProcuracyEngine,
    ProsecutorRank,
    ProcuracyLevel,
    DetentionMeasure,
    ProtestType,
)

procuracy_app = typer.Typer(
    name="procuracy",
    help="Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite (Luật Tổ chức VKSND 2014)",
    invoke_without_command=True,
)
app = procuracy_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]VIỆN KIỂM SÁT NHÂN DÂN TỐI CAO — HỆ THỐNG CÔNG TỐ & KIỂM SÁT TƯ PHÁP[/bold cyan]\n"
            "[dim]Supreme People's Procuracy, Public Prosecution & Detention Supervision Hub (Luật Tổ chức VKSND 2014)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    telemetry = status_data.get("telemetry", {})
    table = Table(title="People's Procuracy Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category", style="bold green")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold yellow")

    pros = telemetry.get("prosecutors", {})
    table.add_row("Prosecutors", "Total Appointed", str(pros.get("total", 0)))
    table.add_row("Prosecutors", "Active Practicing", str(pros.get("active", 0)))

    ind = telemetry.get("criminal_indictments", {})
    table.add_row("Criminal Indictments", "Total Indictments Issued", str(ind.get("total_indictments", 0)))
    table.add_row("Criminal Indictments", "Pending Trial", str(ind.get("pending_trial", 0)))
    table.add_row("Criminal Indictments", "Convicted by Court", str(ind.get("convicted", 0)))

    det = telemetry.get("detention_supervisions", {})
    table.add_row("Detention Supervisions", "Total Custody Inspections", str(det.get("total_inspections", 0)))
    table.add_row("Detention Supervisions", "Compliant Facilities", str(det.get("compliant", 0)))
    table.add_row("Detention Supervisions", "Overdue Releases Ordered", str(det.get("overdue_releases_ordered", 0)))

    prot = telemetry.get("judicial_protests", {})
    table.add_row("Judicial Protests", "Total Protests Filed", str(prot.get("total_protests", 0)))
    table.add_row("Judicial Protests", "Pending Hearing", str(prot.get("pending_hearing", 0)))
    table.add_row("Judicial Protests", "Protests Accepted by Court", str(prot.get("protests_accepted", 0)))

    console.print(table)


@procuracy_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese People's Procuracy Executive Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = ProcuracyEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@procuracy_app.command("prosecutor")
def register_prosecutor_cmd(
    badge: str = typer.Option(..., "--badge", "-b", help="Prosecutor badge number (e.g. KSV-2025-001)"),
    name: str = typer.Option(..., "--name", "-n", help="Full name of prosecutor"),
    rank: str = typer.Option(..., "--rank", "-r", help="KIEM_SAT_VIEN_SO_CAP, KIEM_SAT_VIEN_TRUNG_CAP, KIEM_SAT_VIEN_CAO_CAP, KIEM_SAT_VIEN_VKSNDTC"),
    level: str = typer.Option(..., "--level", "-l", help="VKSND_CAP_HUYEN, VKSND_CAP_TINH, VKSND_CAP_CAO, VKSND_TOI_CAO, VIEN_KIEM_SAT_QUAN_SU"),
    office: str = typer.Option(..., "--office", "-o", help="Office or division unit (e.g. Vụ 1 - VKSNDTC)"),
    date: Optional[str] = typer.Option(None, "--date", help="Appointment date (YYYY-MM-DD)"),
    status: str = typer.Option("ACTIVE", "--status", help="ACTIVE, TRANSFERRED, RETIRED, SUSPENDED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update a Procurator (Kiểm sát viên) under Article 74 Law on Organization of People's Procuracies."""
    engine = ProcuracyEngine()
    result = engine.register_prosecutor(
        badge_number=badge,
        full_name=name,
        rank=rank,
        procuracy_level=level,
        office_unit=office,
        appointment_date=date,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        p = result["prosecutor"]
        console.print(f"[bold green]✓ Prosecutor Registered:[/bold green] {p['badge_number']} - {p['full_name']}")
        console.print(f"  [cyan]Rank:[/cyan] {p['rank']} | [cyan]Level:[/cyan] {p['procuracy_level']} | [cyan]Office:[/cyan] {p['office_unit']}")
        console.print(f"  [cyan]Status:[/cyan] {p['status']} | [cyan]Appointed:[/cyan] {p['appointment_date']}")
    else:
        console.print(f"[bold red]✗ Failed to register prosecutor:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("indictment")
def issue_indictment_cmd(
    number: str = typer.Option(..., "--number", "-n", help="Indictment number (e.g. 15/CT-VKSTC-V1)"),
    case: str = typer.Option(..., "--case", "-c", help="Official criminal case name"),
    accused: str = typer.Option(..., "--accused", "-a", help="Accused person / defendant full name"),
    article: str = typer.Option(..., "--article", help="Penal Code article charged (e.g. Điều 353 BLHS 2015)"),
    prosecutor: str = typer.Option(..., "--prosecutor", "-p", help="Badge number of prosecuting attorney"),
    court: str = typer.Option(..., "--court", help="Designated trial court with jurisdiction"),
    date: Optional[str] = typer.Option(None, "--date", help="Issuing date (YYYY-MM-DD)"),
    status: str = typer.Option("ISSUED", "--status", help="ISSUED, REMANDED_INVESTIGATION, WITHDRAWN, CONVICTED, ACQUITTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue or track a criminal prosecution indictment under Article 243 Criminal Procedure Code."""
    engine = ProcuracyEngine()
    result = engine.issue_indictment(
        indictment_number=number,
        case_name=case,
        accused_name=accused,
        penal_code_article=article,
        prosecutor_badge=prosecutor,
        trial_court=court,
        issuing_date=date,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        i = result["indictment"]
        console.print(f"[bold green]✓ Criminal Indictment Issued:[/bold green] {i['indictment_number']}")
        console.print(f"  [cyan]Case:[/cyan] {i['case_name']} | [cyan]Accused:[/cyan] {i['accused_name']}")
        console.print(f"  [cyan]Charge:[/cyan] {i['penal_code_article']} | [cyan]Court:[/cyan] {i['trial_court']}")
        console.print(f"  [cyan]Prosecutor:[/cyan] {i['prosecutor_badge']} | [cyan]Status:[/cyan] {i['status']}")
    else:
        console.print(f"[bold red]✗ Failed to issue indictment:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("detention")
def record_detention_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Detention inspection code (e.g. DET-2025-001)"),
    facility: str = typer.Option(..., "--facility", "-f", help="Detention facility name (e.g. Trại tạm giam T16)"),
    detainee: str = typer.Option(..., "--detainee", "-d", help="Full name of detained person"),
    measure: str = typer.Option(..., "--measure", "-m", help="Detention measure: TAM_GIU, TAM_GIAM"),
    start: str = typer.Option(..., "--start", help="Custody start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., "--end", help="Custody expiration date (YYYY-MM-DD)"),
    inspector: str = typer.Option(..., "--inspector", help="Badge number of supervising inspector"),
    status: str = typer.Option("COMPLIANT", "--status", help="COMPLIANT, OVERDUE_RELEASE_ORDERED, UNLAWFUL_RELEASED, SANCTIONED"),
    date: Optional[str] = typer.Option(None, "--date", help="Inspection date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Supervision findings or release orders"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Supervise legality of arrest, custody, and temporary detention under Articles 22-26 Law on Organization of People's Procuracies."""
    engine = ProcuracyEngine()
    result = engine.record_detention_supervision(
        supervision_code=code,
        detention_facility=facility,
        detainee_name=detainee,
        measure_type=measure,
        custody_start_date=start,
        custody_end_date=end,
        inspector_badge=inspector,
        compliance_status=status,
        inspection_date=date,
        notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        d = result["detention_supervision"]
        console.print(f"[bold green]✓ Detention Supervision Recorded:[/bold green] {d['supervision_code']}")
        console.print(f"  [cyan]Facility:[/cyan] {d['detention_facility']} | [cyan]Detainee:[/cyan] {d['detainee_name']}")
        console.print(f"  [cyan]Measure:[/cyan] {d['measure_type']} | [cyan]Period:[/cyan] {d['custody_start_date']} -> {d['custody_end_date']}")
        console.print(f"  [cyan]Compliance Status:[/cyan] [bold yellow]{d['compliance_status']}[/bold yellow] | [cyan]Inspector:[/cyan] {d['inspector_badge']}")
    else:
        console.print(f"[bold red]✗ Failed to record detention supervision:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("protest")
def file_protest_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Protest code (e.g. PRT-2025-001)"),
    judgment: str = typer.Option(..., "--judgment", "-j", help="Judgment number protested (e.g. 45/2025/HS-ST)"),
    court: str = typer.Option(..., "--court", help="Court issuing the protested judgment"),
    type: str = typer.Option(..., "--type", "-t", help="Protest type: PHUC_THAM, GIAM_DOC_THAM, TAI_THAM"),
    ground: str = typer.Option(..., "--ground", "-g", help="Legal grounds / serious violation identified"),
    prosecutor: str = typer.Option(..., "--prosecutor", "-p", help="Badge number of protesting prosecutor"),
    date: Optional[str] = typer.Option(None, "--date", help="Filing date (YYYY-MM-DD)"),
    status: str = typer.Option("PENDING", "--status", help="PENDING, ACCEPTED, REJECTED, MODIFIED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue an appellate, cassation, or reopening protest against court judgment under Articles 27-31."""
    engine = ProcuracyEngine()
    result = engine.file_judicial_protest(
        protest_code=code,
        judgment_number=judgment,
        court_issued=court,
        protest_type=type,
        legal_ground=ground,
        prosecutor_badge=prosecutor,
        filing_date=date,
        hearing_status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        pr = result["judicial_protest"]
        console.print(f"[bold green]✓ Judicial Protest Filed:[/bold green] {pr['protest_code']}")
        console.print(f"  [cyan]Protest Type:[/cyan] [bold yellow]{pr['protest_type']}[/bold yellow] | [cyan]Judgment:[/cyan] {pr['judgment_number']}")
        console.print(f"  [cyan]Target Court:[/cyan] {pr['court_issued']} | [cyan]Hearing Status:[/cyan] {pr['hearing_status']}")
        console.print(f"  [cyan]Legal Ground:[/cyan] {pr['legal_ground']}")
    else:
        console.print(f"[bold red]✗ Failed to file judicial protest:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@procuracy_app.command("list")
def list_cmd(
    category: str = typer.Option("prosecutors", "--category", "-c", help="prosecutors, indictments, detentions, protests"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to return"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List records from People's Procuracy database by category."""
    engine = ProcuracyEngine()
    result = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)

    records = result.get("records", [])
    cat = result.get("category", "")
    table = Table(title=f"People's Procuracy Records: {cat.upper()} ({len(records)} found)", box=box.ROUNDED)

    if cat in ("prosecutors", "prosecutor"):
        table.add_column("Badge", style="cyan")
        table.add_column("Name", style="bold white")
        table.add_column("Rank", style="green")
        table.add_column("Level", style="yellow")
        table.add_column("Unit", style="magenta")
        table.add_column("Status", style="bold green")
        for r in records:
            table.add_row(r.get("badge_number"), r.get("full_name"), r.get("rank"), r.get("procuracy_level"), r.get("office_unit"), r.get("status"))

    elif cat in ("indictments", "indictment"):
        table.add_column("Indictment No", style="cyan")
        table.add_column("Case", style="bold white")
        table.add_column("Accused", style="yellow")
        table.add_column("Article", style="magenta")
        table.add_column("Prosecutor", style="white")
        table.add_column("Status", style="bold green")
        for r in records:
            table.add_row(r.get("indictment_number"), r.get("case_name"), r.get("accused_name"), r.get("penal_code_article"), r.get("prosecutor_badge"), r.get("status"))

    elif cat in ("detentions", "detention"):
        table.add_column("Code", style="cyan")
        table.add_column("Facility", style="bold white")
        table.add_column("Detainee", style="yellow")
        table.add_column("Measure", style="green")
        table.add_column("Start -> End", style="white")
        table.add_column("Compliance", style="bold magenta")
        for r in records:
            table.add_row(r.get("supervision_code"), r.get("detention_facility"), r.get("detainee_name"), r.get("measure_type"), f"{r.get('custody_start_date')} -> {r.get('custody_end_date')}", r.get("compliance_status"))

    elif cat in ("protests", "protest"):
        table.add_column("Code", style="cyan")
        table.add_column("Judgment No", style="white")
        table.add_column("Target Court", style="bold white")
        table.add_column("Type", style="yellow")
        table.add_column("Ground", style="green")
        table.add_column("Status", style="bold magenta")
        for r in records:
            table.add_row(r.get("protest_code"), r.get("judgment_number"), r.get("court_issued"), r.get("protest_type"), r.get("legal_ground")[:40] + ("..." if len(r.get("legal_ground", "")) > 40 else ""), r.get("hearing_status"))

    console.print(table)


@procuracy_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display People's Procuracy & Public Prosecution telemetry status."""
    engine = ProcuracyEngine()
    data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(data)
