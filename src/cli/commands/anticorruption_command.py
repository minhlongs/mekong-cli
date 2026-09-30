"""
CLI command group for Vietnamese Anti-Corruption, Asset Declaration & Integrity Oversight Suite.
Governed by Law on Anti-Corruption 2018 (Law No. 36/2018/QH14) & Decree No. 130/2020/NĐ-CP.
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.anticorruption_engine import (
    VALID_ACTION_TYPES,
    VALID_CONFLICT_CATEGORIES,
    VALID_DECLARATION_TYPES,
    VALID_GIFT_DISPOSITIONS,
    VALID_RISK_LEVELS,
    VALID_VERIFICATION_GROUNDS,
    AntiCorruptionEngine,
)

app = typer.Typer(
    name="anticorruption",
    help="Vietnamese Anti-Corruption & Asset Declaration Suite (Law 36/2018/QH14 & Decree 130/2020/NĐ-CP).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def anticorruption_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of Asset Declarations, Verifications, Gift Surrenders, and Sanctions.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = AntiCorruptionEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    wealth_str = f"{telemetry['total_declared_wealth_vnd']:,.0f} VND"
    unexp_str = f"{telemetry['total_unexplained_wealth_vnd']:,.0f} VND"
    gifts_str = f"{telemetry['total_gift_value_vnd']:,.0f} VND"

    overview_text = (
        f"[bold cyan]Total Asset Declarations (Bản kê khai TSTN):[/bold cyan] {telemetry['total_declarations']}\n"
        f"[bold cyan]Total Declared Wealth:[/bold cyan] [bold green]{wealth_str}[/bold green]\n"
        f"[bold cyan]Verifications Conducted (Đã xác minh):[/bold cyan] {telemetry['total_verifications']} "
        f"([yellow]{telemetry['verification_coverage_rate_pct']} %[/yellow] coverage)\n"
        f"[bold cyan]Unexplained Wealth Flagged (Tài sản bất minh):[/bold cyan] [bold {'red' if telemetry['total_unexplained_wealth_vnd'] > 0 else 'green'}]{unexp_str}[/]\n"
        f"[bold cyan]Official Gifts Surrendered (Quà nộp Kho bạc):[/bold cyan] {telemetry['total_gifts_surrendered']} ({gifts_str})\n"
        f"[bold cyan]Active Unresolved Conflicts of Interest:[/bold cyan] [bold {'red' if telemetry['active_unresolved_conflicts'] > 0 else 'green'}]{telemetry['active_unresolved_conflicts']}[/]\n"
        f"[bold cyan]Criminal Referrals (Chuyển CQĐT Bộ Công an / VKSNDTC):[/bold cyan] [bold {'red' if telemetry['criminal_referrals_count'] > 0 else 'green'}]{telemetry['criminal_referrals_count']}[/]"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]HỆ THỐNG KIỂM SOÁT TÀI SẢN & PHÒNG CHỐNG THAM NHŨNG (LUẬT 36/2018/QH14 & NĐ 130/2020)[/bold yellow]",
            box=box.ROUNDED,
            border_style="red",
        )
    )

    # Declarations by Status Table
    statuses = telemetry.get("declarations_by_status", {})
    if statuses:
        status_table = Table(title="Tình trạng xác minh bản kê khai", box=box.SIMPLE_HEAVY)
        status_table.add_column("Status", style="cyan")
        status_table.add_column("Count", justify="right", style="green")
        for st, count in statuses.items():
            status_table.add_row(st, str(count))
        console.print(status_table)


@app.command("declare")
def register_declaration_cmd(
    id_: str = typer.Option(..., "--id", help="Declaration ID (e.g. DEC-2026-001)."),
    declarant_id: str = typer.Option(..., "--declarant-id", "-u", help="Declarant citizen ID or employee ID."),
    name: str = typer.Option(..., "--name", "-n", help="Full name of declarant."),
    org: str = typer.Option(..., "--org", "-o", help="Organization / Agency name."),
    title: str = typer.Option(..., "--title", "-t", help="Position title."),
    type_: str = typer.Option("ANNUAL", "--type", help="FIRST_TIME, ANNUAL, PERSONNEL_APPOINTMENT, ADDITIONAL."),
    year: int = typer.Option(..., "--year", "-y", help="Declaration fiscal year."),
    real_estate: float = typer.Option(0.0, "--real-estate", help="Real estate value in VND."),
    movable: float = typer.Option(0.0, "--movable", help="Movable assets (cash, gold, vehicles >= 50M) in VND."),
    overseas: float = typer.Option(0.0, "--overseas", help="Overseas assets value in VND."),
    income: float = typer.Option(0.0, "--income", help="Annual income between declarations in VND."),
    date: Optional[str] = typer.Option(None, "--date", help="Submission date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a formal Asset and Income Declaration pursuant to Decree 130/2020/NĐ-CP.
    """
    engine = AntiCorruptionEngine()
    try:
        res = engine.register_declaration(
            declaration_id=id_,
            declarant_id=declarant_id,
            declarant_name=name,
            organization=org,
            position_title=title,
            declaration_type=type_,
            declaration_year=year,
            real_estate_value_vnd=real_estate,
            movable_assets_value_vnd=movable,
            overseas_assets_value_vnd=overseas,
            annual_income_vnd=income,
            submission_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering declaration:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Tiếp nhận bản kê khai tài sản, thu nhập thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "vnd" in str(k) else str(v))
    console.print(table)


@app.command("verify")
def execute_verification_cmd(
    id_: str = typer.Option(..., "--id", help="Verification ID (e.g. VER-2026-001)."),
    declaration_id: str = typer.Option(..., "--declaration", "-d", help="Declaration ID to verify."),
    agency: str = typer.Option(..., "--agency", "-a", help="Verification agency name."),
    ground: str = typer.Option("ANNUAL_RANDOM_SELECTION", "--ground", "-g", help="ANNUAL_RANDOM_SELECTION, UNTRUTHFUL_SUSPICION, DENUNCIATION_EVIDENCE, APPOINTMENT_VETTING."),
    verified_wealth: float = typer.Option(..., "--verified-wealth", "-w", help="Verified actual wealth in VND."),
    summary: str = typer.Option(..., "--summary", "-s", help="Summary of verification findings."),
    date: Optional[str] = typer.Option(None, "--date", help="Conclusion decision date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Execute an integrity verification audit and determine unexplained wealth under Decree 130/2020/NĐ-CP.
    """
    engine = AntiCorruptionEngine()
    try:
        res = engine.execute_verification(
            verification_id=id_,
            declaration_id=declaration_id,
            inspecting_agency=agency,
            verification_ground=ground,
            verified_actual_wealth_vnd=verified_wealth,
            findings_summary=summary,
            decision_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error executing verification:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Kết luận xác minh tính trung thực tài sản, thu nhập", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "vnd" in str(k) else str(v))
    console.print(table)


@app.command("gift")
def record_gift_cmd(
    id_: str = typer.Option(..., "--id", help="Gift record ID (e.g. GIFT-2026-001)."),
    declarant_id: str = typer.Option(..., "--declarant-id", "-u", help="Declarant citizen ID."),
    name: str = typer.Option(..., "--name", "-n", help="Declarant name."),
    org: str = typer.Option(..., "--org", "-o", help="Organization name."),
    desc: str = typer.Option(..., "--desc", help="Description of the gift."),
    giver: str = typer.Option(..., "--giver", help="Giver identity / organization."),
    value: float = typer.Option(..., "--value", "-v", help="Estimated gift value in VND."),
    disposition: str = typer.Option("TREASURY_SURRENDER", "--disposition", help="TREASURY_SURRENDER, CHARITY_AUCTION, RETURNED_TO_GIVER, DESTROYED_PROHIBITED."),
    voucher: str = typer.Option("", "--voucher", help="State treasury voucher / receipt code."),
    date: Optional[str] = typer.Option(None, "--date", help="Surrender date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record official gift surrender and treasury receipt under Article 22 of Law 36/2018/QH14.
    """
    engine = AntiCorruptionEngine()
    try:
        res = engine.record_gift_surrender(
            gift_record_id=id_,
            declarant_id=declarant_id,
            declarant_name=name,
            organization=org,
            gift_description=desc,
            giver_identity=giver,
            estimated_value_vnd=value,
            disposition_type=disposition,
            treasury_receipt_voucher=voucher,
            surrender_date=date,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording gift surrender:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Xác nhận nộp lại quà tặng theo quy định phòng chống tham nhũng", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "vnd" in str(k) else str(v))
    console.print(table)


@app.command("conflict")
def register_conflict_cmd(
    id_: str = typer.Option(..., "--id", help="Conflict ID (e.g. COI-2026-001)."),
    person_id: str = typer.Option(..., "--person-id", "-u", help="Official ID."),
    name: str = typer.Option(..., "--name", "-n", help="Full name."),
    org: str = typer.Option(..., "--org", "-o", help="Organization name."),
    category: str = typer.Option(..., "--category", "-c", help="PROCUREMENT_BIDDING, RELATIVE_EMPLOYMENT, CAPITAL_CONTRIBUTION, OUTSIDE_ENGAGEMENT."),
    relation: str = typer.Option(..., "--relation", "-r", help="Relation description (e.g. Vợ là Giám đốc nhà thầu B)."),
    risk: str = typer.Option("MEDIUM", "--risk", help="LOW, MEDIUM, HIGH, PROHIBITED."),
    remediation: str = typer.Option("", "--remediation", help="Remediation mandate."),
    resolve: bool = typer.Option(False, "--resolve", help="Mark conflict as resolved."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register or resolve conflict of interest under Articles 23 & 29 of Law 36/2018/QH14.
    """
    engine = AntiCorruptionEngine()
    try:
        if resolve:
            res = engine.resolve_conflict_interest(conflict_id=id_, remediation_action=remediation)
        else:
            res = engine.register_conflict_interest(
                conflict_id=id_,
                person_id=person_id,
                person_name=name,
                organization=org,
                conflict_category=category,
                relative_relation=relation,
                risk_level=risk,
                remediation_action=remediation,
            )
    except Exception as e:
        console.print(f"[bold red]Error processing conflict of interest:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Đăng ký / Xử lý Xung đột Lợi ích", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("sanction")
def record_sanction_cmd(
    id_: str = typer.Option(..., "--id", help="Action ID (e.g. SANCT-2026-001)."),
    target_id: str = typer.Option(..., "--target-id", "-u", help="Sanctioned person ID."),
    name: str = typer.Option(..., "--name", "-n", help="Full name."),
    case_ref: str = typer.Option(..., "--case-ref", "-c", help="Case reference or verification ID."),
    type_: str = typer.Option(..., "--type", "-t", help="REPRIMAND, WARNING, DEMOTION, DISMISSAL, FORCED_RESIGNATION, CRIMINAL_REFERRAL."),
    authority: str = typer.Option(..., "--authority", "-a", help="Issuing disciplinary authority."),
    decision: str = typer.Option(..., "--decision", "-d", help="Decision number."),
    referral_agency: str = typer.Option("", "--referral-agency", help="Investigation agency if criminal referral."),
    date: Optional[str] = typer.Option(None, "--date", help="Sanction date (YYYY-MM-DD)."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record disciplinary sanction or criminal referral under Article 51 of Law 36/2018/QH14.
    """
    engine = AntiCorruptionEngine()
    try:
        res = engine.record_sanction_or_referral(
            action_id=id_,
            target_id=target_id,
            target_name=name,
            case_reference=case_ref,
            action_type=type_,
            issuing_authority=authority,
            decision_number=decision,
            sanction_date=date,
            referral_target_agency=referral_agency,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording sanction:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Quyết định Xử lý kỷ luật / Chuyển CQĐT hình sự", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="declarations, verifications, gifts, conflicts, sanctions, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List asset declarations, verifications, gifts, conflicts, and sanctions.
    """
    engine = AntiCorruptionEngine()
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
    Get aggregate telemetry metrics on anti-corruption oversight and asset declarations.
    """
    engine = AntiCorruptionEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Vận hành Hệ thống Phòng chống Tham nhũng", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    for k, v in telemetry.items():
        if isinstance(v, dict):
            table.add_row(str(k), f"{len(v)} sub-categories")
        elif isinstance(v, float) and "vnd" in str(k):
            table.add_row(str(k), f"{v:,.0f} VND")
        else:
            table.add_row(str(k), str(v))
    console.print(table)
