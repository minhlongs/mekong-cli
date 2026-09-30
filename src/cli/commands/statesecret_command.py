"""
CLI command group for Vietnamese State Secrets & Classified Intelligence Protection Suite.
Governed by Law on Protection of State Secrets 2018 (Law No. 35/2018/QH14) & Decree No. 26/2020/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.statesecret_engine import (
    VALID_CARRIER_TYPES,
    VALID_CLASSIFICATION_LEVELS,
    VALID_DECLASSIFICATION_TYPES,
    VALID_DESTRUCTION_METHODS,
    VALID_INCIDENT_TYPES,
    VALID_OPERATION_TYPES,
    VALID_SEVERITY_LEVELS,
    StateSecretEngine,
)

app = typer.Typer(
    name="statesecret",
    help="Vietnamese State Secrets & Classified Protection Suite (Law 35/2018/QH14 & Decree 26/2020/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def statesecret_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of State Secrets inventory, authorizations, declassifications, and incident status.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = StateSecretEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    incident_color = "green" if telemetry["active_security_incidents"] == 0 else "red"

    overview_text = (
        f"[bold cyan]Total Classified Items (Tài liệu/vật mang BMNN):[/bold cyan] {telemetry['total_classified_items']}\n"
        f"[bold cyan]Active Access Authorizations (Ủy quyền sao chụp/tiếp cận):[/bold cyan] {telemetry['active_authorizations']}\n"
        f"[bold cyan]Declassifications & Adjustments (Hồ sơ giải mật/điều chỉnh):[/bold cyan] {telemetry['total_declassifications']}\n"
        f"[bold cyan]Secure Destructions Executed (Hồ sơ tiêu hủy an toàn):[/bold cyan] {telemetry['total_destructions']}\n"
        f"[bold cyan]Active Security Incidents (Sự cố lộ, mất BMNN đang điều tra):[/bold cyan] [{incident_color}]{telemetry['active_security_incidents']}[/{incident_color}]"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]HỆ THỐNG QUẢN LÝ BẢO VỆ BÍ MẬT NHÀ NƯỚC (LUẬT 35/2018/QH14)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    items_level = telemetry.get("items_by_level", {})
    if items_level:
        lvl_table = Table(title="Phân loại theo Độ mật (Điều 7 Luật 35/2018/QH14)", box=box.SIMPLE_HEAVY)
        lvl_table.add_column("Classification Level", style="cyan")
        lvl_table.add_column("Count", justify="right", style="green")
        for lvl, cnt in items_level.items():
            lvl_table.add_row(lvl, str(cnt))
        console.print(lvl_table)


@app.command("classify")
def register_item_cmd(
    id_: str = typer.Option(..., "--id", help="Item ID (e.g. SEC-2026-001)."),
    title: str = typer.Option(..., "--title", "-t", help="Classified document or carrier title."),
    level: str = typer.Option("MAT", "--level", "-l", help="TUYET_MAT, TOI_MAT, MAT."),
    agency: str = typer.Option(..., "--agency", "-a", help="Originating government agency."),
    authority: str = typer.Option(..., "--auth", help="Approving authority official name/position."),
    carrier: str = typer.Option("DOCUMENT_PAPER", "--carrier", "-c", help="DOCUMENT_PAPER, DIGITAL_STORAGE_USB_ENCRYPTED, CRYPTOGRAPHIC_KEY_DEVICE, PHYSICAL_SAMPLE_SPECIMEN, SCIENTIFIC_RESEARCH_MODEL."),
    years: Optional[int] = typer.Option(None, "--years", "-y", help="Custom protection duration in years."),
    scope: Optional[str] = typer.Option(None, "--scope", help="Comma-separated recipient scope agencies/positions."),
    stamp: Optional[str] = typer.Option(None, "--stamp", help="Official secret stamp code (Thông tư 24/2020/TT-BCA)."),
    date: Optional[str] = typer.Option(None, "--date", help="Registration date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register and classify a state secret document or carrier under Article 10 of Law 35/2018/QH14.
    """
    engine = StateSecretEngine()
    scope_list = [s.strip() for s in scope.split(",")] if scope else []
    try:
        res = engine.register_classified_item(
            item_id=id_,
            item_title=title,
            classification_level=level,
            originating_agency=agency,
            approving_authority=authority,
            carrier_type=carrier,
            registered_date=date,
            custom_protection_years=years,
            recipient_scope=scope_list,
            stamp_code=stamp,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering classified item:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký và xác định độ mật thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("authorize")
def authorize_access_cmd(
    id_: str = typer.Option(..., "--id", help="Authorization ID (e.g. AUTH-2026-001)."),
    item_id: str = typer.Option(..., "--item-id", "-i", help="Classified item ID."),
    person: str = typer.Option(..., "--person", "-p", help="Authorized person name & title."),
    authority: str = typer.Option(..., "--auth-by", help="Authorizing official name."),
    op: str = typer.Option("READ_ACCESS", "--op", help="READ_ACCESS, COPY_DUPLICATE, EXTRACT_SUMMARY, TAKE_OUTSIDE_OFFICE."),
    purpose: str = typer.Option(..., "--purpose", help="Official purpose of access."),
    valid_from: Optional[str] = typer.Option(None, "--from", help="Start validity date (YYYY-MM-DD)."),
    valid_until: Optional[str] = typer.Option(None, "--until", help="End validity date (YYYY-MM-DD)."),
    copies: int = typer.Option(0, "--copies", help="Number of copies authorized."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Authorize access, copying, extracting, or taking secret documents out of headquarters (Articles 11, 14, 15).
    """
    engine = StateSecretEngine()
    try:
        res = engine.authorize_access(
            auth_id=id_,
            item_id=item_id,
            authorized_person=person,
            authorizing_official=authority,
            operation_type=op,
            purpose=purpose,
            valid_from=valid_from,
            valid_until=valid_until,
            copy_count=copies,
        )
    except Exception as e:
        console.print(f"[bold red]Error authorizing access:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Cấp phép tiếp cận / sao chụp bí mật nhà nước", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("adjust")
def adjust_classification_cmd(
    id_: str = typer.Option(..., "--id", help="Declassification record ID (e.g. DECLAS-2026-001)."),
    item_id: str = typer.Option(..., "--item-id", "-i", help="Classified item ID."),
    type_: str = typer.Option("FULL_DECLASSIFICATION", "--type", "-t", help="FULL_DECLASSIFICATION, PARTIAL_DECLASSIFICATION, TERM_EXPIRATION, GRADE_DOWNGRADE, GRADE_UPGRADE, TERM_EXTENSION."),
    decision: str = typer.Option(..., "--decision", "-d", help="Decision document number."),
    authority: str = typer.Option(..., "--authority", "-a", help="Competent decision authority."),
    reason: str = typer.Option(..., "--reason", "-r", help="Legal or operational grounds summary."),
    new_level: Optional[str] = typer.Option(None, "--new-level", help="New classification level if upgraded or downgraded."),
    ext_years: Optional[int] = typer.Option(None, "--ext-years", help="Years to extend if TERM_EXTENSION."),
    date: Optional[str] = typer.Option(None, "--date", help="Effective date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Execute declassification, grade adjustment, or protection term extension (Articles 20, 21, 22).
    """
    engine = StateSecretEngine()
    try:
        res = engine.adjust_classification(
            declass_id=id_,
            item_id=item_id,
            declass_type=type_,
            decision_number=decision,
            decision_authority=authority,
            reason_summary=reason,
            new_level=new_level,
            effective_date=date,
            extension_years=ext_years,
        )
    except Exception as e:
        console.print(f"[bold red]Error adjusting classification:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Quyết định Giải mật / Điều chỉnh độ mật", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("destruct")
def execute_destruction_cmd(
    id_: str = typer.Option(..., "--id", help="Destruction record ID (e.g. DEST-2026-001)."),
    item_id: str = typer.Option(..., "--item-id", "-i", help="Classified item ID to destroy."),
    chair: str = typer.Option(..., "--chair", help="Chairperson of Destruction Council."),
    method: str = typer.Option("INCINERATION_HIGH_TEMP", "--method", "-m", help="INCINERATION_HIGH_TEMP, PULPING_CHEMICAL, PHYSICAL_SHREDDING_DIN66399_P7, CRYPTOGRAPHIC_ERASURE_DOD."),
    minutes: str = typer.Option(..., "--minutes", help="Destruction minutes reference number."),
    witnesses: Optional[str] = typer.Option(None, "--witnesses", help="Comma-separated witness names."),
    date: Optional[str] = typer.Option(None, "--date", help="Destruction date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record secure destruction of classified documents or carriers pursuant to Article 23 Law 35/2018/QH14.
    """
    engine = StateSecretEngine()
    witness_list = [w.strip() for w in witnesses.split(",")] if witnesses else []
    try:
        res = engine.execute_destruction(
            destruct_id=id_,
            item_id=item_id,
            destruction_council_chair=chair,
            destruction_method=method,
            minutes_reference=minutes,
            destruction_date=date,
            witness_list=witness_list,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording destruction:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Biên bản tiêu hủy an toàn bí mật nhà nước", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("incident")
def report_incident_cmd(
    id_: str = typer.Option(..., "--id", help="Incident ID (e.g. INC-2026-001)."),
    item_id: str = typer.Option(..., "--item-id", "-i", help="Compromised item ID."),
    type_: str = typer.Option("LEAK_DISCLOSURE", "--type", "-t", help="LEAK_DISCLOSURE, LOSS_MISPLACEMENT, UNAUTHORIZED_COPY, CYBER_INTERCEPTION, TAMPERING_ALTERATION."),
    severity: str = typer.Option("MAJOR", "--severity", "-s", help="CRITICAL, MAJOR, MODERATE."),
    suspect: str = typer.Option(..., "--suspect", help="Suspect person or entity."),
    quarantine: str = typer.Option(..., "--quarantine", help="Quarantine and immediate containment measures taken."),
    referral: Optional[str] = typer.Option(None, "--referral", help="Investigative referral agency (e.g. Cục An ninh chính trị nội bộ A03)."),
    date: Optional[str] = typer.Option(None, "--date", help="Discovery date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Report and investigate a state secret disclosure or compromise incident (Article 26 & Criminal Code Arts 337/338).
    """
    engine = StateSecretEngine()
    try:
        res = engine.report_security_incident(
            incident_id=id_,
            item_id=item_id,
            incident_type=type_,
            severity_level=severity,
            suspect_person=suspect,
            quarantine_measures=quarantine,
            discovery_date=date,
            referral_agency=referral,
        )
    except Exception as e:
        console.print(f"[bold red]Error reporting security incident:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Báo cáo sự cố an ninh bí mật nhà nước", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="items, authorizations, declassifications, destructions, incidents, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List state secret items, authorizations, declassification records, destructions, and incidents.
    """
    engine = StateSecretEngine()
    records = engine.list_records(record_type=record_type, limit=limit)

    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for category, items in records.items():
        table = Table(title=f"Danh mục {category.upper()} ({len(items)} bản ghi)", box=box.ROUNDED)
        if not items:
            console.print(f"[dim]No {category} found.[/dim]")
            continue

        columns = list(items[0].keys())
        for col in columns[:6]:
            table.add_column(col, style="cyan")
        for item in items:
            table.add_row(*[str(item.get(c, "")) for c in columns[:6]])
        console.print(table)


@app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Get aggregate telemetry metrics on state secrets protection and compliance readiness.
    """
    engine = StateSecretEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số An toàn Bảo vệ Bí mật Nhà nước", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} sub-categories")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
