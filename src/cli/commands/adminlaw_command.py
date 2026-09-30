"""
CLI Command Suite for Vietnamese Legal Normative Documents, Regulatory Impact Assessment (RIA) & State Compensation Liability.
Compliant with:
- Law on Promulgation of Legal Normative Documents 2015 (Law No. 80/2015/QH13, amended by Law No. 63/2020/QH14)
- Law on State Compensation Liability 2017 (Luật Trách nhiệm bồi thường của Nhà nước - Law No. 10/2017/QH14)
- Decree No. 34/2016/NĐ-CP & Decree No. 154/2020/NĐ-CP detailing the Law on Promulgation of Legal Normative Documents
- Decree No. 68/2018/NĐ-CP detailing the Law on State Compensation Liability
"""

import typer
import json
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.adminlaw_engine import (
    AdminLawEngine,
    DocumentType,
    IssuingBody,
    CompensationSphere,
    AppraisalVerdict,
    FaultDegree,
)

adminlaw_app = typer.Typer(
    name="adminlaw",
    help="Vietnamese Legal Normative Documents, RIA & State Compensation Liability Suite (Luật VBQPPL & Luật TNBTNN)",
    invoke_without_command=True,
)
app = adminlaw_app
console = Console()


def _render_status_dashboard(status_data: dict) -> None:
    console.print(
        Panel.fit(
            "[bold cyan]BỘ TƯ PHÁP — HỆ THỐNG VĂN BẢN QUY PHẠM PHÁP LUẬT & BỒI THƯỜNG NHÀ NƯỚC[/bold cyan]\n"
            "[dim]Legal Normative Documents (Law 80/2015/QH13) & State Compensation Liability (Law 10/2017/QH14)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    telemetry = status_data.get("telemetry", {})
    table = Table(title="Administrative Law Telemetry", box=box.ROUNDED, show_header=True)
    table.add_column("Category", style="bold green")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold yellow")

    doc = telemetry.get("legal_normative_documents", {})
    table.add_row("Legal Documents", "Total Promulgated", str(doc.get("total", 0)))
    table.add_row("Legal Documents", "Currently Effective", str(doc.get("effective", 0)))

    ria = telemetry.get("regulatory_impact_assessments", {})
    table.add_row("RIA Evaluations", "Total Appraisals", str(ria.get("total_appraisals", 0)))
    table.add_row("RIA Evaluations", "Qualified for Enactment", str(ria.get("qualified", 0)))
    table.add_row("RIA Evaluations", "Average Economic Impact", f"{ria.get('average_economic_impact', 0.0):.1f}")
    table.add_row("RIA Evaluations", "Average Social Impact", f"{ria.get('average_social_impact', 0.0):.1f}")

    clm = telemetry.get("state_compensation_claims", {})
    table.add_row("Compensation Claims", "Total Claims Filed", str(clm.get("total_claims", 0)))
    table.add_row("Compensation Claims", "Settled Claims", str(clm.get("settled", 0)))
    table.add_row("Compensation Claims", "Total Claimed (VND)", f"{clm.get('total_claimed_vnd', 0.0):,.0f}")

    stl = telemetry.get("compensation_settlements", {})
    table.add_row("Settlement Decisions", "Total Decisions", str(stl.get("total_decisions", 0)))
    table.add_row("Settlement Decisions", "Total Awarded (VND)", f"{stl.get('total_awarded_vnd', 0.0):,.0f}")

    rmb = telemetry.get("officer_reimbursements", {})
    table.add_row("Officer Reimbursements", "Total Orders", str(rmb.get("total_orders", 0)))
    table.add_row("Officer Reimbursements", "Total Ordered (VND)", f"{rmb.get('total_reimbursement_ordered_vnd', 0.0):,.0f}")

    console.print(table)


@adminlaw_app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Vietnamese Legal Normative Documents & State Compensation Liability Dashboard."""
    if ctx.invoked_subcommand is None:
        engine = AdminLawEngine()
        status_data = engine.get_telemetry_status()

        if json_output:
            typer.echo(json.dumps(status_data, ensure_ascii=False, indent=2))
            return

        _render_status_dashboard(status_data)


@adminlaw_app.command("document")
def register_document_cmd(
    number: str = typer.Option(..., "--number", "-n", help="Document number (e.g. 80/2015/QH13)"),
    title: str = typer.Option(..., "--title", "-t", help="Official document title"),
    type: str = typer.Option(..., "--type", help="LUAT, NGHI_QUYET_QH, PHAP_LENH, NGHI_DINH, QUYET_DINH_TTG, THONG_TU, NGHI_QUYET_HDND, QUYET_DINH_UBND"),
    body: str = typer.Option(..., "--body", "-b", help="QUOC_HOI, UBTVQH, CHINH_PHU, THU_TUONG, BO_TU_PHAP, BO_TAI_CHINH, BO_CONG_AN, BO_Y_TE, HDND_CAP_TINH, UBND_CAP_TINH"),
    promulgation: Optional[str] = typer.Option(None, "--promulgation", help="Date of promulgation (YYYY-MM-DD)"),
    effective: Optional[str] = typer.Option(None, "--effective", help="Effective date (YYYY-MM-DD)"),
    status: str = typer.Option("EFFECTIVE", "--status", help="EFFECTIVE, EXPIRED, PARTIALLY_EXPIRED, SUSPENDED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Register or update a Vietnamese legal normative document under Article 4 Law No. 80/2015/QH13."""
    engine = AdminLawEngine()
    result = engine.register_document(
        doc_number=number,
        title=title,
        doc_type=type,
        issuing_body=body,
        promulgation_date=promulgation,
        effective_date=effective,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        d = result["document"]
        console.print(f"[bold green]✓ Legal Normative Document Registered:[/bold green] {d['doc_number']} - {d['title']}")
        console.print(f"  [cyan]Type:[/cyan] {d['doc_type']} | [cyan]Issuing Body:[/cyan] {d['issuing_body']} | [cyan]Status:[/cyan] {d['status']}")
        console.print(f"  [cyan]Effective Date:[/cyan] {d['effective_date']}")
    else:
        console.print(f"[bold red]✗ Failed to register document:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@adminlaw_app.command("ria")
def evaluate_ria_cmd(
    code: str = typer.Option(..., "--code", "-c", help="RIA evaluation identifier (e.g. RIA-2025-001)"),
    doc_number: str = typer.Option(..., "--doc-number", "-n", help="Associated legal document number"),
    economic: float = typer.Option(..., "--economic", "-e", help="Economic impact score (0.0 to 100.0)"),
    social: float = typer.Option(..., "--social", "-s", help="Social impact score (0.0 to 100.0)"),
    burden: str = typer.Option("STREAMLINED", "--burden", help="Administrative procedure burden: STREAMLINED, ACCEPTABLE, BURDENSOME"),
    agency: str = typer.Option("Bộ Tư pháp", "--agency", "-a", help="Appraisal agency (e.g. Bộ Tư pháp)"),
    verdict: str = typer.Option("QUALIFIED", "--verdict", help="Appraisal verdict: QUALIFIED, CONDITIONAL_REVISION, REJECTED"),
    date: Optional[str] = typer.Option(None, "--date", help="Evaluation date (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Appraisal notes / recommendations"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Conduct Regulatory Impact Assessment (RIA) & legality appraisal under Articles 35 & 58 Law No. 80/2015/QH13."""
    engine = AdminLawEngine()
    result = engine.evaluate_ria(
        eval_code=code,
        doc_number=doc_number,
        economic_impact_score=economic,
        social_impact_score=social,
        admin_procedure_burden=burden,
        evaluator_agency=agency,
        appraisal_verdict=verdict,
        evaluation_date=date,
        notes=notes,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        r = result["ria_evaluation"]
        console.print(f"[bold green]✓ RIA Legality Appraisal Completed:[/bold green] {r['eval_code']} for Doc {r['doc_number']}")
        console.print(f"  [cyan]Verdict:[/cyan] [bold yellow]{r['appraisal_verdict']}[/bold yellow] | [cyan]Burden:[/cyan] {r['admin_procedure_burden']}")
        console.print(f"  [cyan]Scores:[/cyan] Economic: {r['economic_impact_score']} | Social: {r['social_impact_score']}")
        console.print(f"  [cyan]Agency:[/cyan] {r['evaluator_agency']}")
    else:
        console.print(f"[bold red]✗ Failed to record RIA appraisal:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@adminlaw_app.command("claim")
def file_claim_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Claim identifier (e.g. CLM-2025-001)"),
    name: str = typer.Option(..., "--name", help="Claimant full name or entity"),
    citizen_id: str = typer.Option(..., "--citizen-id", help="CCCD / Tax code of claimant"),
    sphere: str = typer.Option(..., "--sphere", help="QUAN_LY_HANH_CHINH, TO_TUNG_HINH_SU, TO_TUNG_DAN_SU, TO_TUNG_HANH_CHINH, THI_HANH_AN"),
    agency: str = typer.Option(..., "--agency", "-a", help="Responsible agency causing damage"),
    amount: float = typer.Option(..., "--amount", help="Claimed damage amount (VND)"),
    date: Optional[str] = typer.Option(None, "--date", help="Filing date (YYYY-MM-DD)"),
    status: str = typer.Option("PENDING_REVIEW", "--status", help="PENDING_REVIEW, ACCEPTED, VERIFYING, SETTLED, REJECTED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """File a State Compensation liability claim under Articles 2 & 41-43 Law No. 10/2017/QH14."""
    engine = AdminLawEngine()
    result = engine.file_compensation_claim(
        claim_code=code,
        claimant_name=name,
        citizen_id_tax=citizen_id,
        sphere=sphere,
        responsible_agency=agency,
        claimed_amount_vnd=amount,
        filing_date=date,
        status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        c = result["compensation_claim"]
        console.print(f"[bold green]✓ State Compensation Claim Filed:[/bold green] {c['claim_code']}")
        console.print(f"  [cyan]Claimant:[/cyan] {c['claimant_name']} ({c['citizen_id_tax']})")
        console.print(f"  [cyan]Sphere:[/cyan] {c['sphere']} | [cyan]Agency:[/cyan] {c['responsible_agency']}")
        console.print(f"  [cyan]Claimed Amount:[/cyan] {c['claimed_amount_vnd']:,.0f} VND | [cyan]Status:[/cyan] {c['status']}")
    else:
        console.print(f"[bold red]✗ Failed to file compensation claim:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@adminlaw_app.command("settle")
def settle_claim_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Settlement decision identifier (e.g. DEC-2025-001)"),
    claim_code: str = typer.Option(..., "--claim-code", help="Associated compensation claim code"),
    material: float = typer.Option(..., "--material", help="Material damage awarded (VND)"),
    mental: float = typer.Option(0.0, "--mental", help="Mental suffering / morale damages awarded (VND)"),
    date: Optional[str] = typer.Option(None, "--date", help="Decision date (YYYY-MM-DD)"),
    status: str = typer.Option("APPROVED", "--status", help="APPROVED, DISBURSED, APPEALED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Issue a State Compensation settlement decision under Articles 45-48 Law No. 10/2017/QH14."""
    engine = AdminLawEngine()
    result = engine.settle_compensation(
        decision_code=code,
        claim_code=claim_code,
        material_damage_vnd=material,
        mental_suffering_vnd=mental,
        decision_date=date,
        payout_status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        s = result["settlement_decision"]
        console.print(f"[bold green]✓ Settlement Decision Issued:[/bold green] {s['decision_code']} for Claim {s['claim_code']}")
        console.print(f"  [cyan]Material:[/cyan] {s['material_damage_vnd']:,.0f} VND | [cyan]Mental:[/cyan] {s['mental_suffering_vnd']:,.0f} VND")
        console.print(f"  [cyan]Total Awarded:[/cyan] [bold yellow]{s['total_awarded_vnd']:,.0f} VND[/bold yellow] | [cyan]Payout:[/cyan] {s['payout_status']}")
    else:
        console.print(f"[bold red]✗ Failed to issue settlement decision:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@adminlaw_app.command("reimburse")
def order_reimbursement_cmd(
    code: str = typer.Option(..., "--code", "-c", help="Reimbursement identifier (e.g. RMB-2025-001)"),
    decision_code: str = typer.Option(..., "--decision-code", help="Associated settlement decision code"),
    officer: str = typer.Option(..., "--officer", help="Full name of at-fault public officer"),
    fault_degree: str = typer.Option(..., "--fault-degree", help="LOI_CO_Y, LOI_VO_Y_NGHIEM_TRONG"),
    amount: float = typer.Option(..., "--amount", help="Reimbursement amount (VND) to be repaid to State Budget"),
    status: str = typer.Option("ORDERED", "--status", help="ORDERED, IN_REPAYMENT, RECOVERED"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Order at-fault state officer reimbursement to State Budget under Articles 64-67 Law No. 10/2017/QH14."""
    engine = AdminLawEngine()
    result = engine.order_reimbursement(
        reimbursement_code=code,
        decision_code=decision_code,
        fault_officer_name=officer,
        fault_degree=fault_degree,
        reimbursement_amount_vnd=amount,
        reimbursement_status=status,
    )

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result.get("success"):
        r = result["officer_reimbursement"]
        console.print(f"[bold green]✓ Officer Reimbursement Order Created:[/bold green] {r['reimbursement_code']}")
        console.print(f"  [cyan]Officer:[/cyan] {r['fault_officer_name']} | [cyan]Fault Degree:[/cyan] {r['fault_degree']}")
        console.print(f"  [cyan]Amount:[/cyan] [bold yellow]{r['reimbursement_amount_vnd']:,.0f} VND[/bold yellow] | [cyan]Status:[/cyan] {r['reimbursement_status']}")
    else:
        console.print(f"[bold red]✗ Failed to create reimbursement order:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)


@adminlaw_app.command("list")
def list_cmd(
    category: str = typer.Option("documents", "--category", "-c", help="documents, ria, claims, settlements, reimbursements"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum records to return"),
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """List records from administrative law database by category."""
    engine = AdminLawEngine()
    result = engine.list_records(category=category, limit=limit)

    if json_output:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not result.get("success"):
        console.print(f"[bold red]✗ Error:[/bold red] {result.get('error')}")
        raise typer.Exit(code=1)

    records = result.get("records", [])
    cat = result.get("category", "")
    table = Table(title=f"Administrative Law Records: {cat.upper()} ({len(records)} found)", box=box.ROUNDED)

    if cat in ("documents", "document"):
        table.add_column("Doc Number", style="cyan")
        table.add_column("Title", style="bold white")
        table.add_column("Type", style="green")
        table.add_column("Issuing Body", style="yellow")
        table.add_column("Effective Date", style="magenta")
        table.add_column("Status", style="bold green")
        for r in records:
            table.add_row(r.get("doc_number"), r.get("title")[:40] + ("..." if len(r.get("title", "")) > 40 else ""), r.get("doc_type"), r.get("issuing_body"), r.get("effective_date"), r.get("status"))

    elif cat == "ria":
        table.add_column("Eval Code", style="cyan")
        table.add_column("Doc Number", style="bold white")
        table.add_column("Economic", style="yellow")
        table.add_column("Social", style="yellow")
        table.add_column("Burden", style="magenta")
        table.add_column("Verdict", style="bold green")
        for r in records:
            table.add_row(r.get("eval_code"), r.get("doc_number"), str(r.get("economic_impact_score")), str(r.get("social_impact_score")), r.get("admin_procedure_burden"), r.get("appraisal_verdict"))

    elif cat in ("claims", "claim"):
        table.add_column("Claim Code", style="cyan")
        table.add_column("Claimant", style="bold white")
        table.add_column("Sphere", style="green")
        table.add_column("Agency", style="yellow")
        table.add_column("Claimed (VND)", style="bold yellow")
        table.add_column("Status", style="magenta")
        for r in records:
            table.add_row(r.get("claim_code"), r.get("claimant_name"), r.get("sphere"), r.get("responsible_agency"), f"{r.get('claimed_amount_vnd', 0.0):,.0f}", r.get("status"))

    elif cat in ("settlements", "settlement"):
        table.add_column("Decision Code", style="cyan")
        table.add_column("Claim Code", style="cyan")
        table.add_column("Material (VND)", style="white")
        table.add_column("Mental (VND)", style="white")
        table.add_column("Total Awarded (VND)", style="bold yellow")
        table.add_column("Payout Status", style="green")
        for r in records:
            table.add_row(r.get("decision_code"), r.get("claim_code"), f"{r.get('material_damage_vnd', 0.0):,.0f}", f"{r.get('mental_suffering_vnd', 0.0):,.0f}", f"{r.get('total_awarded_vnd', 0.0):,.0f}", r.get("payout_status"))

    elif cat in ("reimbursements", "reimbursement"):
        table.add_column("Reimbursement Code", style="cyan")
        table.add_column("Decision Code", style="cyan")
        table.add_column("Officer", style="bold white")
        table.add_column("Fault Degree", style="yellow")
        table.add_column("Amount (VND)", style="bold yellow")
        table.add_column("Status", style="green")
        for r in records:
            table.add_row(r.get("reimbursement_code"), r.get("decision_code"), r.get("fault_officer_name"), r.get("fault_degree"), f"{r.get('reimbursement_amount_vnd', 0.0):,.0f}", r.get("reimbursement_status"))

    console.print(table)


@adminlaw_app.command("status")
def status_cmd(
    json_output: bool = typer.Option(False, "--json", help="Output in JSON format"),
):
    """Display Administrative Law, RIA & State Compensation status telemetry."""
    engine = AdminLawEngine()
    data = engine.get_telemetry_status()

    if json_output:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    _render_status_dashboard(data)

