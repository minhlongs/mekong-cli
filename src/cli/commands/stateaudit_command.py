"""
CLI command group for Vietnamese State Audit, Supreme Audit Institution (SAV / KTNN) & Public Financial Oversight Suite.
Governed by Law on State Audit 2015 (Law No. 81/2015/QH13) & Amending Law 2019 (Law No. 55/2019/QH14).
"""

from __future__ import annotations

import json
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.stateaudit_engine import (
    VALID_AUDIT_TYPES,
    VALID_DOMAINS,
    VALID_ENGAGEMENT_STATUSES,
    VALID_ENTITY_TYPES,
    VALID_RECOMMENDATION_TYPES,
    VALID_SEVERITIES,
    StateAuditEngine,
)

app = typer.Typer(
    name="stateaudit",
    help="Vietnamese State Audit (KTNN) & Public Financial Oversight Suite (Law 81/2015/QH13).",
    no_args_is_help=False,
)
console = Console()


@app.callback(invoke_without_command=True)
def stateaudit_default(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Default view: Executive dashboard of State Audit operations, recommendations, recoveries, and legal compliance.
    """
    if ctx.invoked_subcommand is not None:
        return

    engine = StateAuditEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    # Executive Overview Panel
    rec_vnd_str = f"{telemetry['total_recommended_amount_vnd']:,.0f} VND"
    impl_vnd_str = f"{telemetry['total_implemented_amount_vnd']:,.0f} VND"
    rate_color = "green" if telemetry["fiscal_implementation_rate_pct"] >= 80 else "yellow" if telemetry["fiscal_implementation_rate_pct"] >= 50 else "red"

    overview_text = (
        f"[bold cyan]Total Audit Engagements (Cuộc kiểm toán):[/bold cyan] {telemetry['total_audit_engagements']} "
        f"({telemetry['engagements_in_progress']} in progress, {telemetry['engagements_concluded']} concluded)\n"
        f"[bold cyan]Total Audit Findings (Phát hiện sai phạm):[/bold cyan] {telemetry['total_audit_findings']}\n"
        f"[bold cyan]Total Audit Recommendations (Kiến nghị xử lý):[/bold cyan] {telemetry['total_recommendations']}\n"
        f"[bold cyan]Total Financial Recommended:[/bold cyan] [bold yellow]{rec_vnd_str}[/bold yellow]\n"
        f"[bold cyan]Total Fiscal Recoveries Implemented:[/bold cyan] [bold green]{impl_vnd_str}[/bold green] "
        f"([{rate_color}]{telemetry['fiscal_implementation_rate_pct']} %[/{rate_color}])\n"
        f"[bold cyan]Criminal Referrals (Chuyển CQĐT Bộ Công an):[/bold cyan] [bold {'red' if telemetry['criminal_referrals_count'] > 0 else 'green'}]{telemetry['criminal_referrals_count']}[/]\n"
        f"[bold cyan]Disciplinary Actions (Kiến nghị xử lý kỷ luật):[/bold cyan] [bold {'yellow' if telemetry['disciplinary_actions_count'] > 0 else 'green'}]{telemetry['disciplinary_actions_count']}[/]\n"
        f"[bold cyan]Overdue Recommendations (Quá hạn chưa thực hiện):[/bold cyan] [bold {'red' if telemetry['overdue_recommendations_count'] > 0 else 'green'}]{telemetry['overdue_recommendations_count']}[/]"
    )

    console.print(
        Panel(
            overview_text,
            title="[bold yellow]KIỂM TOÁN NHÀ NƯỚC VIỆT NAM (SAV) — HỆ THỐNG GIÁM SÁT TÀI CHÍNH CÔNG (LUẬT 81/2015/QH13)[/bold yellow]",
            box=box.ROUNDED,
            border_style="yellow",
        )
    )

    # Recommendations Breakdown Table
    type_breakdown = telemetry.get("recommendations_by_type", {})
    if type_breakdown:
        rec_table = Table(
            title="Chi tiết kiến nghị kiểm toán theo hình thức xử lý (Điều 37 & 48 Luật KTNN)",
            box=box.SIMPLE_HEAVY,
            header_style="bold blue",
        )
        rec_table.add_column("Recommendation Type", style="cyan", justify="left")
        rec_table.add_column("Count", justify="right")
        rec_table.add_column("Recommended (VND)", justify="right", style="yellow")
        rec_table.add_column("Implemented (VND)", justify="right", style="green")

        for rtype, rdata in type_breakdown.items():
            rec_table.add_row(
                rtype,
                str(rdata["count"]),
                f"{rdata['recommended_vnd']:,.0f}",
                f"{rdata['implemented_vnd']:,.0f}",
            )
        console.print(rec_table)


@app.command("engagement")
def register_engagement_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Audit engagement code (e.g. KTNN-2026-BXD-01)."),
    decision: str = typer.Option(..., "--decision", "-d", help="Decision number by State Auditor General (e.g. QĐ 112/QĐ-KTNN)."),
    entity: str = typer.Option(..., "--entity", "-e", help="Audited entity name."),
    entity_type: str = typer.Option("MINISTRY", "--type", "-t", help="MINISTRY, PROVINCIAL_GOVERNMENT, STATE_OWNED_ENTERPRISE, PROJECT_MANAGEMENT_UNIT, POLITICAL_ORGANIZATION."),
    audit_type: str = typer.Option("COMPLIANCE_AUDIT", "--audit-type", "-a", help="FINANCIAL_AUDIT, COMPLIANCE_AUDIT, PERFORMANCE_AUDIT, COMPREHENSIVE_AUDIT."),
    year: int = typer.Option(..., "--year", "-y", help="Fiscal scope year being audited."),
    lead: str = typer.Option(..., "--lead", "-l", help="Head of the audit delegation (Trưởng đoàn kiểm toán)."),
    start: str = typer.Option(..., "--start", help="Audit start date (YYYY-MM-DD)."),
    end: str = typer.Option(..., "--end", help="Audit conclusion deadline (YYYY-MM-DD)."),
    status: str = typer.Option("IN_PROGRESS", "--status", "-s", help="PLANNED, IN_PROGRESS, CONCLUDED, PUBLISHED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Register a formal State Audit mission pursuant to Decision by the State Auditor General.
    """
    engine = StateAuditEngine()
    try:
        res = engine.register_engagement(
            engagement_code=code,
            decision_number=decision,
            audited_entity=entity,
            entity_type=entity_type,
            audit_type=audit_type,
            audit_scope_year=year,
            lead_auditor=lead,
            start_date=start,
            end_date=end,
            status=status,
        )
    except Exception as e:
        console.print(f"[bold red]Error registering audit engagement:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Quyết định Kiểm toán Nhà nước ban hành thành công", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("finding")
def record_finding_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Finding code (e.g. FIND-2026-001)."),
    engagement: str = typer.Option(..., "--engagement", "-e", help="Audit engagement code."),
    domain: str = typer.Option(..., "--domain", help="BUDGET_REVENUE, BUDGET_EXPENDITURE, PUBLIC_INVESTMENT, ASSET_MANAGEMENT, PROCUREMENT, TAX_COLLECTION."),
    desc: str = typer.Option(..., "--desc", help="Detailed description of defect or leak."),
    violation: str = typer.Option(..., "--violation", "-v", help="Statutory law article violated."),
    severity: str = typer.Option("MEDIUM", "--severity", "-s", help="LOW, MEDIUM, HIGH, CRITICAL."),
    evidence: str = typer.Option("", "--evidence", help="Summary of audit proof and documentation."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record an identified compliance defect, budget leak, or 3E inefficiency in State Audit logs.
    """
    engine = StateAuditEngine()
    try:
        res = engine.record_finding(
            finding_code=code,
            engagement_code=engagement,
            domain=domain,
            description=desc,
            statutory_violation=violation,
            severity=severity,
            evidence_summary=evidence,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording audit finding:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Ghi nhận sai phạm / khiếm khuyết kiểm toán", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), str(v))
    console.print(table)


@app.command("recommend")
def issue_recommendation_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Recommendation code (e.g. REC-2026-001)."),
    finding: str = typer.Option(..., "--finding", "-f", help="Associated finding code."),
    type_: str = typer.Option(..., "--type", "-t", help="REVENUE_INCREASE, EXPENDITURE_DISALLOWANCE, REIMBURSEMENT, OTHER_FINANCIAL_REMEDIATION, DISCIPLINARY_ACTION, CRIMINAL_REFERRAL."),
    desc: str = typer.Option(..., "--desc", help="Actionable recommendation text."),
    agency: str = typer.Option(..., "--agency", "-a", help="Target agency responsible for implementation."),
    deadline: str = typer.Option(..., "--deadline", "-d", help="Settlement deadline (YYYY-MM-DD)."),
    amount: float = typer.Option(0.0, "--amount", help="Fiscal recovery amount in VND."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Issue a formal State Audit Recommendation under Articles 37 & 48 of Law 81/2015/QH13.
    """
    engine = StateAuditEngine()
    try:
        res = engine.issue_recommendation(
            recommendation_code=code,
            finding_code=finding,
            recommendation_type=type_,
            description=desc,
            target_agency=agency,
            settlement_deadline=deadline,
            amount_vnd=amount,
        )
    except Exception as e:
        console.print(f"[bold red]Error issuing recommendation:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Ban hành kiến nghị xử lý kiểm toán", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "amount" in str(k) else str(v))
    console.print(table)


@app.command("settle")
def record_settlement_cmd(
    id_: str = typer.Option(..., "--id", help="Settlement record ID (e.g. SETTLE-2026-001)."),
    code: str = typer.Option(..., "--code", "-c", help="Recommendation code."),
    date: str = typer.Option(..., "--date", "-d", help="Settlement date (YYYY-MM-DD)."),
    voucher: str = typer.Option(..., "--voucher", help="State treasury voucher / official resolution number."),
    amount: float = typer.Option(0.0, "--amount", help="Amount settled/reimbursed in VND."),
    evidence: str = typer.Option("", "--evidence", help="Evidence notes and remediation confirmation."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Record execution / financial remediation by audited entity.
    """
    engine = StateAuditEngine()
    try:
        res = engine.record_settlement(
            settlement_id=id_,
            recommendation_code=code,
            settlement_date=date,
            treasury_voucher_number=voucher,
            amount_settled_vnd=amount,
            evidence_notes=evidence,
        )
    except Exception as e:
        console.print(f"[bold red]Error recording settlement:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    table = Table(title="Xác nhận thực hiện kết luận kiểm toán", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    for k, v in res.items():
        table.add_row(str(k), f"{v:,.0f} VND" if "vnd" in str(k) else str(v))
    console.print(table)


@app.command("conclude")
def conclude_engagement_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Engagement code."),
    status: str = typer.Option("CONCLUDED", "--status", "-s", help="CONCLUDED or PUBLISHED."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    Conclude or officially publish the final audit report.
    """
    engine = StateAuditEngine()
    try:
        res = engine.conclude_engagement(engagement_code=code, status=status)
    except Exception as e:
        console.print(f"[bold red]Error concluding engagement:[/bold red] {e}")
        raise typer.Exit(code=1)

    if json_output:
        typer.echo(json.dumps(res, indent=2, ensure_ascii=False))
        return

    console.print(f"[bold green]Audit engagement {code} updated to status: {status.upper()}[/bold green]")


@app.command("list")
def list_records_cmd(
    record_type: str = typer.Option("all", "--type", "-t", help="engagements, findings, recommendations, settlements, all."),
    limit: int = typer.Option(50, "--limit", "-l", help="Max records to return."),
    json_output: bool = typer.Option(False, "--json", help="Emit output as JSON."),
) -> None:
    """
    List state audit engagements, findings, recommendations, and settlements.
    """
    engine = StateAuditEngine()
    records = engine.list_records(record_type=record_type, limit=limit)

    if json_output:
        typer.echo(json.dumps(records, indent=2, ensure_ascii=False))
        return

    for category, items in records.items():
        table = Table(title=f"Danh sách {category.upper()} ({len(items)} bản ghi)", box=box.ROUNDED)
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
    Get aggregate telemetry metrics on state audit engagements and fiscal recoveries.
    """
    engine = StateAuditEngine()
    telemetry = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(telemetry, indent=2, ensure_ascii=False))
        return

    table = Table(title="Chỉ số Vận hành Hệ thống Kiểm toán Nhà nước", box=box.ROUNDED)
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
