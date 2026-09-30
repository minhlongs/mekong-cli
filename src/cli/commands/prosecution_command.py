"""
CLI command group for Vietnamese People's Procuracy, Public Prosecution & Judicial Supervision Suite.
Governed by:
- Law on Organization of the People's Procuracies 2014 (Law No. 63/2014/QH13 — Luật Tổ chức VKSND)
- Criminal Procedure Code 2015 (Law No. 101/2015/QH13 — Bộ luật Tố tụng hình sự)
- Law on Execution of Criminal Judgments 2019 (Law No. 41/2019/QH14 — Luật Thi hành án hình sự)
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

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
console = Console()


@app.callback(invoke_without_command=True)
def prosecution_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of People's Procuracy, Public Prosecution, and Judicial Supervision.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = ProsecutionEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    compliance_color = "green" if telemetry["custody_compliance_rate_percent"] >= 95.0 else "yellow"

    overview_text = (
        f"[bold cyan]Active-Duty Procurators (Kiểm sát viên thường trực các cấp):[/bold cyan] {telemetry['active_duty_procurators']} procurators (Total: {telemetry['total_procurators']})\n"
        f"[bold cyan]Crime Reports Supervised (Kiểm sát thụ lý nguồn tin tội phạm - Điều 144-150):[/bold cyan] {telemetry['total_crime_reports_supervised']} reports ([yellow]{telemetry['pending_crime_reports']} pending investigation[/yellow])\n"
        f"[bold cyan]Supervised Criminal Cases (Vụ án kiểm sát điều tra & phê chuẩn tố tụng):[/bold cyan] {telemetry['supervised_criminal_cases']} cases ([cyan]{telemetry['approved_arrest_warrants']} arrest warrants[/cyan], [cyan]{telemetry['approved_detention_orders']} detentions[/cyan], [yellow]{telemetry['prosecutorial_investigation_demands']} demands[/yellow])\n"
        f"[bold cyan]Indictments Issued (Cáo trạng truy tố ra trước Tòa án - Điều 243-244):[/bold cyan] {telemetry['total_indictments_issued']} indictments ([bold green]{telemetry['cases_prosecuted_to_trial']} proceeded to trial[/bold green])\n"
        f"[bold cyan]Custody & Detention Inspections (Kiểm sát nhà tạm giữ, trại tạm giam - Luật THAHS):[/bold cyan] {telemetry['total_custody_inspections']} inspections ([{compliance_color}]{telemetry['custody_compliance_rate_percent']}% compliance rate[/{compliance_color}], [red]{telemetry['custody_violations_detected']} violations[/red])"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold red]VIỆN KIỂM SÁT NHÂN DÂN — HỆ THỐNG THỰC HÀNH QUYỀN CÔNG TỐ & KIỂM SÁT TƯ PHÁP[/bold red]",
            box=box.ROUNDED,
            border_style="red",
        )
    )


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
    """
    Register a Procurator under the Law on Organization of the People's Procuracies 2014.
    """
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
    """
    Record and supervise receipt of crime reports and denunciations under Articles 144-150 BLTTHS 2015.
    """
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
    """
    Record criminal case investigation supervision and procedural approvals.
    """
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
    """
    Issue a formal prosecutorial indictment (Cáo trạng) under Articles 243-244 BLTTHS 2015.
    """
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
    """
    Record inspection of detention facility and prison execution under Law on Execution of Criminal Judgments 2019.
    """
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
    """
    List records from the People's Procuracy and Public Prosecution database.
    """
    engine = ProsecutionEngine()
    records = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    # Render procurators table
    if "procurators" in records and records["procurators"]:
        table = Table(title="People's Procuracy Roster (Danh sách Kiểm sát viên)", box=box.SIMPLE)
        table.add_column("Procurator ID", style="cyan")
        table.add_column("Full Name", style="bold")
        table.add_column("Rank", style="yellow")
        table.add_column("Unit", style="dim")
        table.add_column("Appointment", style="dim")
        table.add_column("Status", style="green")

        for p in records["procurators"]:
            table.add_row(
                p["procurator_id"],
                p["full_name"],
                p["rank"],
                p["unit_name"],
                p["appointment_decision"],
                p["status"],
            )
        console.print(table)

    # Render crime reports table
    if "reports" in records and records["reports"]:
        table = Table(title="Crime Reports & Denunciations (Nguồn tin về tội phạm)", box=box.SIMPLE)
        table.add_column("Report ID", style="cyan")
        table.add_column("Source")
        table.add_column("Summary", style="bold")
        table.add_column("Crime Group", style="yellow")
        table.add_column("Deadline", style="magenta")
        table.add_column("Status", style="green")

        for r in records["reports"]:
            table.add_row(
                r["report_id"],
                r["source_type"],
                r["crime_summary"][:30] + ("..." if len(r["crime_summary"]) > 30 else ""),
                r["alleged_crime_group"],
                r["resolution_deadline"],
                r["supervision_status"],
            )
        console.print(table)

    # Render cases table
    if "cases" in records and records["cases"]:
        table = Table(title="Supervised Criminal Cases (Vụ án kiểm sát điều tra)", box=box.SIMPLE)
        table.add_column("Case ID", style="cyan")
        table.add_column("Case Title", style="bold")
        table.add_column("Agency")
        table.add_column("Article", style="yellow")
        table.add_column("Stage", style="magenta")
        table.add_column("Warrants / Detentions")

        for c in records["cases"]:
            table.add_row(
                c["case_id"],
                c["case_name"][:25] + ("..." if len(c["case_name"]) > 25 else ""),
                c["investigative_agency"],
                c["legal_article"],
                c["procedural_stage"],
                f"{c['arrest_warrants_approved']} / {c['detention_orders_approved']}",
            )
        console.print(table)

    # Render indictments table
    if "indictments" in records and records["indictments"]:
        table = Table(title="Prosecutorial Indictments (Cáo trạng truy tố)", box=box.SIMPLE)
        table.add_column("Indictment ID", style="cyan")
        table.add_column("Defendant", style="bold")
        table.add_column("Charged Offense")
        table.add_column("Clause", style="yellow")
        table.add_column("Decision", style="green")
        table.add_column("Issue Date")

        for ind in records["indictments"]:
            table.add_row(
                ind["indictment_id"],
                ind["defendant_name"],
                ind["charged_offense"],
                ind["applicable_clause"],
                ind["prosecution_decision"],
                ind["issue_date"],
            )
        console.print(table)

    # Render inspections table
    if "inspections" in records and records["inspections"]:
        table = Table(title="Custody & Detention Inspections (Kiểm sát tạm giữ, tạm giam)", box=box.SIMPLE)
        table.add_column("Inspection ID", style="cyan")
        table.add_column("Facility", style="bold")
        table.add_column("Checked")
        table.add_column("Violations", style="red")
        table.add_column("Compliance", style="green")
        table.add_column("Date")

        for i in records["inspections"]:
            table.add_row(
                i["inspection_id"],
                i["facility_name"],
                str(i["detainees_checked_count"]),
                str(i["violations_detected_count"]),
                i["compliance_status"],
                i["inspection_date"],
            )
        console.print(table)


@app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Display telemetry metrics for the People's Procuracy and Public Prosecution Suite.
    """
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
