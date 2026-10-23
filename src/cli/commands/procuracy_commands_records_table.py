# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Procuracy suite dashboard and record-table construction."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def render_status_dashboard(status_data: dict) -> None:
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


_COLUMN_SPECS = {
    "prosecutors": (("Badge", "cyan"), ("Name", "bold white"), ("Rank", "green"), ("Level", "yellow"), ("Unit", "magenta"), ("Status", "bold green")),
    "indictments": (("Indictment No", "cyan"), ("Case", "bold white"), ("Accused", "yellow"), ("Article", "magenta"), ("Prosecutor", "white"), ("Status", "bold green")),
    "detentions": (("Code", "cyan"), ("Facility", "bold white"), ("Detainee", "yellow"), ("Measure", "green"), ("Start -> End", "white"), ("Compliance", "bold magenta")),
    "protests": (("Code", "cyan"), ("Judgment No", "white"), ("Target Court", "bold white"), ("Type", "yellow"), ("Ground", "green"), ("Status", "bold magenta")),
}

_RENDERERS = {
    "prosecutors": lambda r: (r.get("badge_number"), r.get("full_name"), r.get("rank"), r.get("procuracy_level"), r.get("office_unit"), r.get("status")),
    "indictments": lambda r: (r.get("indictment_number"), r.get("case_name"), r.get("accused_name"), r.get("penal_code_article"), r.get("prosecutor_badge"), r.get("status")),
    "detentions": lambda r: (r.get("supervision_code"), r.get("detention_facility"), r.get("detainee_name"), r.get("measure_type"), f"{r.get('custody_start_date')} -> {r.get('custody_end_date')}", r.get("compliance_status")),
    "protests": lambda r: (r.get("protest_code"), r.get("judgment_number"), r.get("court_issued"), r.get("protest_type"), _truncate_ground(r.get("legal_ground", "")), r.get("hearing_status")),
}


def _truncate_ground(ground: str) -> str:
    return ground[:40] + ("..." if len(ground) > 40 else "")


_SINGULAR = {"prosecutor": "prosecutors", "indictment": "indictments", "detention": "detentions", "protest": "protests"}


def build_records_table(cat: str, records: list[dict]) -> Table:
    """Build the procuracy records table; the caller prints it."""
    key = cat if cat in _COLUMN_SPECS else _SINGULAR.get(cat, cat)
    table = Table(title=f"People's Procuracy Records: {cat.upper()} ({len(records)} found)", box=box.ROUNDED)
    if key not in _COLUMN_SPECS:
        return table
    for header, style in _COLUMN_SPECS[key]:
        table.add_column(header, style=style)
    for r in records:
        table.add_row(*_RENDERERS[key](r))
    return table
