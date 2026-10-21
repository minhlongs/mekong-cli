"""Table and panel renderers for Vietnamese People's Procuracy CLI commands."""

from __future__ import annotations

import json
from typing import Any

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.prosecution_engine import ProsecutionEngine

console = Console()


def render_prosecution_dashboard(json_output: bool = False) -> None:
    """Render default executive dashboard or JSON telemetry."""
    engine = ProsecutionEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    compliance_color = "green" if telemetry["custody_compliance_rate_percent"] >= 95.0 else "yellow"
    overview_text = (
        f"[bold cyan]Active-Duty Procurators (Kiểm sát viên thường trực các cấp):[/bold cyan] "
        f"{telemetry['active_duty_procurators']} procurators (Total: {telemetry['total_procurators']})\n"
        f"[bold cyan]Crime Reports Supervised (Kiểm sát thụ lý nguồn tin tội phạm - Điều 144-150):[/bold cyan] "
        f"{telemetry['total_crime_reports_supervised']} reports ([yellow]{telemetry['pending_crime_reports']} pending investigation[/yellow])\n"
        f"[bold cyan]Supervised Criminal Cases (Vụ án kiểm sát điều tra & phê chuẩn tố tụng):[/bold cyan] "
        f"{telemetry['supervised_criminal_cases']} cases ([cyan]{telemetry['approved_arrest_warrants']} arrest warrants[/cyan], "
        f"[cyan]{telemetry['approved_detention_orders']} detentions[/cyan], [yellow]{telemetry['prosecutorial_investigation_demands']} demands[/yellow])\n"
        f"[bold cyan]Indictments Issued (Cáo trạng truy tố ra trước Tòa án - Điều 243-244):[/bold cyan] "
        f"{telemetry['total_indictments_issued']} indictments ([bold green]{telemetry['cases_prosecuted_to_trial']} proceeded to trial[/bold green])\n"
        f"[bold cyan]Custody & Detention Inspections (Kiểm sát nhà tạm giữ, trại tạm giam - Luật THAHS):[/bold cyan] "
        f"{telemetry['total_custody_inspections']} inspections ([{compliance_color}]{telemetry['custody_compliance_rate_percent']}% compliance rate[/{compliance_color}], "
        f"[red]{telemetry['custody_violations_detected']} violations[/red])"
    )
    console.print(
        Panel(
            overview_text,
            title="[bold red]VIỆN KIỂM SÁT NHÂN DÂN — HỆ THỐNG THỰC HÀNH QUYỀN CÔNG TỐ & KIỂM SÁT TƯ PHÁP[/bold red]",
            box=box.ROUNDED,
            border_style="red",
        )
    )


def render_prosecution_records(records: dict[str, Any]) -> None:
    """Render procurators, reports, cases, indictments, and inspections tables."""
    if "procurators" in records and records["procurators"]:
        table = Table(title="People's Procuracy Roster (Danh sách Kiểm sát viên)", box=box.SIMPLE)
        for col, st in [("Procurator ID", "cyan"), ("Full Name", "bold"), ("Rank", "yellow"), ("Unit", "dim"), ("Appointment", "dim"), ("Status", "green")]:
            table.add_column(col, style=st)
        for p in records["procurators"]:
            table.add_row(p["procurator_id"], p["full_name"], p["rank"], p["unit_name"], p["appointment_decision"], p["status"])
        console.print(table)

    if "reports" in records and records["reports"]:
        table = Table(title="Crime Reports & Denunciations (Nguồn tin về tội phạm)", box=box.SIMPLE)
        for col, st in [("Report ID", "cyan"), ("Source", None), ("Summary", "bold"), ("Crime Group", "yellow"), ("Deadline", "magenta"), ("Status", "green")]:
            table.add_column(col, style=st)
        for r in records["reports"]:
            summary = r["crime_summary"][:30] + ("..." if len(r["crime_summary"]) > 30 else "")
            table.add_row(r["report_id"], r["source_type"], summary, r["alleged_crime_group"], r["resolution_deadline"], r["supervision_status"])
        console.print(table)

    if "cases" in records and records["cases"]:
        table = Table(title="Supervised Criminal Cases (Vụ án kiểm sát điều tra)", box=box.SIMPLE)
        for col, st in [("Case ID", "cyan"), ("Case Title", "bold"), ("Agency", None), ("Article", "yellow"), ("Stage", "magenta"), ("Warrants / Detentions", None)]:
            table.add_column(col, style=st)
        for c in records["cases"]:
            title = c["case_name"][:25] + ("..." if len(c["case_name"]) > 25 else "")
            table.add_row(c["case_id"], title, c["investigative_agency"], c["legal_article"], c["procedural_stage"], f"{c['arrest_warrants_approved']} / {c['detention_orders_approved']}")
        console.print(table)

    if "indictments" in records and records["indictments"]:
        table = Table(title="Prosecutorial Indictments (Cáo trạng truy tố)", box=box.SIMPLE)
        for col, st in [("Indictment ID", "cyan"), ("Defendant", "bold"), ("Charged Offense", None), ("Clause", "yellow"), ("Decision", "green"), ("Issue Date", None)]:
            table.add_column(col, style=st)
        for ind in records["indictments"]:
            table.add_row(ind["indictment_id"], ind["defendant_name"], ind["charged_offense"], ind["applicable_clause"], ind["prosecution_decision"], ind["issue_date"])
        console.print(table)

    if "inspections" in records and records["inspections"]:
        table = Table(title="Custody & Detention Inspections (Kiểm sát tạm giữ, tạm giam)", box=box.SIMPLE)
        for col, st in [("Inspection ID", "cyan"), ("Facility", "bold"), ("Checked", None), ("Violations", "red"), ("Compliance", "green"), ("Date", None)]:
            table.add_column(col, style=st)
        for i in records["inspections"]:
            table.add_row(i["inspection_id"], i["facility_name"], str(i["detainees_checked_count"]), str(i["violations_detected_count"]), i["compliance_status"], i["inspection_date"])
        console.print(table)
