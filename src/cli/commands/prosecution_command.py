"""CLI command group for Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.

Governed by:
- Law on Organization of the People's Procuracies 2014 (Law No. 63/2014/QH13 — Luật Tổ chức VKSND)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13 — Bộ luật Tố tụng hình sự)
- Law on Execution of Criminal Judgments 2019 (Law No. 41/2019/QH14 — Luật Thi hành án hình sự)
"""

from __future__ import annotations

import json

import typer

from src.cli.commands._prosecution_renderers import console, render_prosecution_dashboard
from src.cli.commands._prosecution_supervision import register_prosecution_supervision_commands
from src.core.prosecution_engine import (
    VALID_CRIME_GROUPS,
    VALID_INSPECTION_COMPLIANCE,
    VALID_PROCEDURAL_STAGES,
    VALID_PROCURACY_LEVELS,
    VALID_PROCURATOR_RANKS,
    VALID_PROCURATOR_STATUS,
    VALID_PROSECUTION_DECISIONS,
    VALID_REPORT_SOURCES,
    VALID_REPORT_STATUS,
    ProsecutionEngine,
)

app = typer.Typer(
    name="prosecution",
    help="Vietnamese People's Procuracy & Public Prosecution Suite (Luật Tổ chức VKSND 2014 & BLTTHS 2015).",
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def prosecution_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """Default view: Executive dashboard of People's Procuracy, Public Prosecution, and Judicial Supervision."""
    if ctx.invoked_subcommand is not None:
        return
    render_prosecution_dashboard(json_output=json_output)


@app.command("procurator")
def register_procurator_cmd(
    procurator_id: str = typer.Option(..., "--id", "-i", help="Procurator badge or identifier (e.g. KSV-VKS-00123)."),
    name: str = typer.Option(..., "--name", "-n", help="Full name of Procurator (Họ và tên Kiểm sát viên)."),
    rank: str = typer.Option("KIEM_SAT_VIEN_SO_CAP", "--rank", "-r", help="Rank: KIEM_SAT_VIEN_SO_CAP, KIEM_SAT_VIEN_TRUNG_CAP, KIEM_SAT_VIEN_CAO_CAP, KIEM_SAT_VIEN_TOI_CAO, KIEM_TRA_VIEN."),
    level: str = typer.Option("VKSND_CAP_HUYEN", "--level", "-l", help="Procuracy level: VKSND_TOI_CAO, VKSND_CAP_CAO, VKSND_CAP_TINH, VKSND_CAP_HUYEN, VKS_QUAN_SU."),
    unit: str = typer.Option(..., "--unit", "-u", help="Procuracy unit name (e.g. Viện KSND Quận 1, Viện KSND TP.HCM)."),
    decision: str = typer.Option(..., "--decision", "-d", help="Appointment decision number (Số quyết định bổ nhiệm)."),
    status: str = typer.Option("ACTIVE_DUTY", "--status", "-s", help="Status: ACTIVE_DUTY, SUSPENDED, RETIRED, ON_LEAVE."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """Register a Procurator under the Law on Organization of the People's Procuracies 2014."""
    engine = ProsecutionEngine()
    try:
        res = engine.register_procurator(
            procurator_id=procurator_id,
            full_name=name,
            rank=rank,
            procuracy_level=level,
            unit_name=unit,
            appointment_decision=decision,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering procurator:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ Registered Procurator {res['procurator_id']} — {res['full_name']} successfully![/bold green]")
    console.print(f"  Rank: [cyan]{res['rank']}[/cyan] | Unit: {res['unit_name']} | Decision: {res['appointment_decision']}")


@app.command("report")
def receive_crime_report_cmd(
    report_id: str = typer.Option(..., "--id", "-i", help="Crime report registration ID (e.g. TNB-2024-00123)."),
    source: str = typer.Option("TO_GIAC_TOI_PHAM", "--source", help="Source: TO_GIAC_TOI_PHAM, TIN_BAO_TOI_PHAM, KIEN_NGHI_KHOI_TO, TRUC_TIEP_PHAT_HIEN."),
    summary: str = typer.Option(..., "--summary", "-s", help="Brief summary of reported crime information."),
    group: str = typer.Option("SO_HUU_TAI_SAN", "--group", "-g", help="Crime group: AN_NINH_QUOC_GIA, XAM_PHAM_TINH_MANG_SUC_KHOE, SO_HUU_TAI_SAN, KINH_TE_THAM_NHUNG, MA_TUY, TRAT_TU_CONG_CONG."),
    procuracy: str = typer.Option(..., "--procuracy", "-p", help="Receiving procuracy name."),
    procurator: str = typer.Option(..., "--procurator", help="Assigned supervising procurator ID."),
    status: str = typer.Option("INVESTIGATING", "--status", help="Supervision status: INVESTIGATING, INSTITUTED_CASE, REJECTED_NO_CRIME, SUSPENDED_TEMPORARY."),
    deadline_days: int = typer.Option(20, "--deadline-days", help="Resolution deadline in days (default 20 per Art 147 BLTTHS)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """Record and supervise receipt of crime reports and denunciations under Articles 144-150 BLTTHS 2015."""
    engine = ProsecutionEngine()
    try:
        res = engine.receive_crime_report(
            report_id=report_id,
            source_type=source,
            crime_summary=summary,
            alleged_crime_group=group,
            receiving_procuracy=procuracy,
            assigned_procurator_id=procurator,
            supervision_status=status,
            resolution_deadline_days=deadline_days,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording crime report:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ Recorded Crime Report {res['report_id']} successfully![/bold green]")
    console.print(f"  Group: [yellow]{res['alleged_crime_group']}[/yellow] | Deadline: [cyan]{res['resolution_deadline']}[/cyan] | Procurator: {res['assigned_procurator_id']}")


@app.command("case")
def record_case_supervision_cmd(
    case_id: str = typer.Option(..., "--id", "-i", help="Criminal case identifier (e.g. AN-HS-2024-0045)."),
    name: str = typer.Option(..., "--name", "-n", help="Case title / subject matter."),
    agency: str = typer.Option(..., "--agency", "-a", help="Investigative police agency in charge."),
    procurator: str = typer.Option(..., "--procurator", help="Procurator supervising the investigation."),
    article: str = typer.Option(..., "--article", help="Applicable Penal Code article (e.g. Điều 174 BLHS)."),
    stage: str = typer.Option("KHOI_TO_DIEU_TRA", "--stage", help="Procedural stage: KHOI_TO_DIEU_TRA, TRUY_TO, XET_XU_SO_THAM, XET_XU_PHUC_THAM, THI_HANH_AN."),
    warrants: int = typer.Option(0, "--warrants", help="Arrest warrants approved by Procuracy."),
    detentions: int = typer.Option(0, "--detentions", help="Temporary detention orders approved."),
    demands: int = typer.Option(0, "--demands", help="Official prosecutorial investigation demands issued."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """Record criminal case investigation supervision and procedural approvals."""
    engine = ProsecutionEngine()
    try:
        res = engine.record_case_supervision(
            case_id=case_id,
            case_name=name,
            investigative_agency=agency,
            procurator_in_charge=procurator,
            legal_article=article,
            procedural_stage=stage,
            arrest_warrants_approved=warrants,
            detention_orders_approved=detentions,
            procuracy_demands_count=demands,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording case supervision:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]✓ Updated Criminal Case Supervision {res['case_id']}![/bold green]")
    console.print(f"  Title: {res['case_name']} | Stage: [cyan]{res['procedural_stage']}[/cyan] | Approvals: [yellow]{res['arrest_warrants_approved']} warrants, {res['detention_orders_approved']} detentions[/yellow]")


register_prosecution_supervision_commands(app)

__all__ = [
    "ProsecutionEngine",
    "VALID_CRIME_GROUPS",
    "VALID_INSPECTION_COMPLIANCE",
    "VALID_PROCEDURAL_STAGES",
    "VALID_PROCURACY_LEVELS",
    "VALID_PROCURATOR_RANKS",
    "VALID_PROCURATOR_STATUS",
    "VALID_PROSECUTION_DECISIONS",
    "VALID_REPORT_SOURCES",
    "VALID_REPORT_STATUS",
    "app",
]
