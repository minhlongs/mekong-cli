# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Non-Contractual Civil Liability & Tort Compensation Command Surface (Phase 150).

Statutory framework:
- Civil Code 2015 (Bộ luật Dân sự số 91/2015/QH13) - Phần thứ ba, Chương XX: Bồi thường thiệt hại ngoài hợp đồng (Điều 584–608)
- Resolution No. 02/2022/NQ-HDTP of Supreme People's Court on guiding non-contractual tort damages
- Decree No. 73/2024/ND-CP on statutory base salary (2,340,000 VND/month)
"""

from __future__ import annotations

import json
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.tort_compensation_engine import (
    BASE_SALARY_VND,
    CAP_MONTHS_HEALTH_DAMAGE,
    CAP_MONTHS_LIFE_DAMAGE,
    CAP_MONTHS_REPUTATION_DAMAGE,
    DamageCategory,
    FaultType,
    LiabilityType,
    TortCompensationEngine,
)

tort_app = typer.Typer(
    name="tort",
    help="Vietnamese Non-Contractual Civil Liability & Tort Compensation Suite (BLDS 2015 Điều 584–608 & NQ 02/2022/NQ-HĐTP).",
    no_args_is_help=False,
)
app = tort_app
console = Console()


def _render_dashboard() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG ĐỊNH LƯỢNG BỒI THƯỜNG THIỆT HẠI NGOÀI HỢP ĐỒNG[/bold cyan]\n"
            "[bold green]QUẢN LÝ TRÁCH NHIỆM DÂN SỰ, NGUỒN NGUY HIỂM CAO ĐỘ & HÒA GIẢI (BLDS 2015 ĐIỀU 584–608)[/bold green]\n"
            "[dim]Civil Code 2015 & Resolution 02/2022/NQ-HĐTP | Decree 73/2024/NĐ-CP (Base Salary: 2,340,000 VND)[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    summary_table = Table(title="Khung Pháp lý & Mức Trần Bồi Thường Tinh Thần (Statutory Caps)", box=box.ROUNDED)
    summary_table.add_column("Danh Mục Thiệt Hại (Category)", style="cyan")
    summary_table.add_column("Căn Cứ Pháp Lý (Legal Basis)", style="yellow")
    summary_table.add_column("Hạn Mức Trần Bù Đắp Tinh Thần", style="green")

    summary_table.add_row(
        "Sức khỏe bị xâm phạm (Health)",
        "Điều 590 BLDS 2015 & NQ 02/2022",
        f"Tối đa 50 tháng lương cơ sở ({CAP_MONTHS_HEALTH_DAMAGE * BASE_SALARY_VND:,.0f} VNĐ)",
    )
    summary_table.add_row(
        "Tính mạng bị xâm phạm (Life)",
        "Điều 591 BLDS 2015 & NQ 02/2022",
        f"Tối đa 100 tháng lương cơ sở ({CAP_MONTHS_LIFE_DAMAGE * BASE_SALARY_VND:,.0f} VNĐ)",
    )
    summary_table.add_row(
        "Danh dự, nhân phẩm, uy tín (Reputation)",
        "Điều 592 BLDS 2015",
        f"Tối đa 10 tháng lương cơ sở ({CAP_MONTHS_REPUTATION_DAMAGE * BASE_SALARY_VND:,.0f} VNĐ)",
    )
    summary_table.add_row(
        "Nguồn nguy hiểm cao độ (Strict Liability)",
        "Điều 601 BLDS 2015",
        "Trách nhiệm nghiêm ngặt ngay cả khi không có lỗi",
    )
    summary_table.add_row(
        "Thời hiệu khởi kiện (Statute Limitation)",
        "Điều 588 BLDS 2015",
        "03 năm kể từ ngày biết quyền bị xâm phạm",
    )

    console.print(summary_table)


@tort_app.callback(invoke_without_command=True)
def default_callback(ctx: typer.Context) -> None:
    """Entrypoint callback when no subcommands are supplied."""
    if ctx.invoked_subcommand is None:
        _render_dashboard()


@tort_app.command("status")
def status_cmd() -> None:
    """Display statutory parameters and legal caps dashboard."""
    _render_dashboard()


@tort_app.command("create-case")
def create_case_cmd(
    incident_date: str = typer.Option(..., "--incident-date", "-d", help="Date of incident (YYYY-MM-DD)"),
    location: str = typer.Option(..., "--location", "-l", help="Incident location"),
    category: str = typer.Option("HEALTH", "--category", "-c", help="Damage category: HEALTH, LIFE, PROPERTY, HONOR_REPUTATION"),
    liability: str = typer.Option("HIGH_RISK_SOURCE", "--liability", help="Liability type: FAULT_BASED, HIGH_RISK_SOURCE, LEGAL_ENTITY, EMPLOYER_APPRENTICE"),
    description: str = typer.Option(..., "--desc", help="Brief incident description"),
    discovery_date: Optional[str] = typer.Option(None, "--discovery-date", help="Discovery date (defaults to incident date)"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Create a new non-contractual tort liability compensation case."""
    engine = TortCompensationEngine()
    result = engine.create_case(
        incident_date=incident_date,
        incident_location=location,
        damage_category=category,
        liability_type=liability,
        description=description,
        discovery_date=discovery_date,
    )

    if json_out:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold green]✓ Đã khởi tạo hồ sơ bồi thường thành công: {result['case_id']}[/bold green]")
    limitation = result["statute_of_limitations"]
    console.print(f"[cyan]Thời hiệu khởi kiện:[/cyan] {limitation['admissibility_status']} (Còn lại: {limitation['days_remaining']} ngày)")


@tort_app.command("calculate-health")
def calculate_health_cmd(
    treatment_costs: float = typer.Option(..., "--treatment", "-t", help="Medical treatment & rehabilitation costs (VNĐ)"),
    lost_income: float = typer.Option(..., "--lost-income", "-i", help="Lost income of victim (VNĐ)"),
    caregiver_costs: float = typer.Option(0.0, "--caregiver", help="Caregiver lost income/costs (VNĐ)"),
    other_costs: float = typer.Option(0.0, "--other", help="Other reasonable expenses (VNĐ)"),
    disability_pct: float = typer.Option(0.0, "--disability-pct", help="Disability percentage (0-100%)"),
    victim_fault_pct: float = typer.Option(0.0, "--victim-fault", help="Victim fault percentage (0-100%)"),
    economic_difficulty: bool = typer.Option(False, "--difficulty", help="Defendant severe economic difficulty"),
    unintentional: bool = typer.Option(True, "--unintentional", help="Defendant fault was unintentional"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Calculate statutory compensation for harm to health (Điều 590 BLDS & NQ 02/2022)."""
    engine = TortCompensationEngine()
    result = engine.calculate_health_damage(
        treatment_and_rehab_costs=treatment_costs,
        lost_income_victim=lost_income,
        caregiver_costs_and_lost_income=caregiver_costs,
        other_actual_expenses=other_costs,
        disability_percentage=disability_pct,
        victim_fault_percentage=victim_fault_pct,
        defendant_economic_difficulty=economic_difficulty,
        defendant_is_unintentional=unintentional,
    )

    if json_out:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(Panel.fit(
        f"[bold yellow]TỔNG MỨC BỒI THƯỜNG SỨC KHỎE PHẢI NỘP: {result['final_payable_compensation']:,.0f} VNĐ[/bold yellow]\n"
        f"[dim]Thiệt hại vật chất: {result['breakdown']['total_material_damage']:,.0f} VNĐ | Bù đắp tinh thần: {result['breakdown']['emotional_distress']:,.0f} VNĐ[/dim]",
        box=box.ROUNDED,
        border_style="green",
    ))


@tort_app.command("calculate-life")
def calculate_life_cmd(
    treatment_costs: float = typer.Option(0.0, "--treatment", "-t", help="Medical treatment costs prior to death (VNĐ)"),
    funeral_costs: float = typer.Option(..., "--funeral", "-f", help="Reasonable funeral expenses (VNĐ)"),
    dependents_count: int = typer.Option(0, "--dependents-count", help="Number of statutory dependents"),
    monthly_allowance: float = typer.Option(BASE_SALARY_VND, "--monthly-allowance", help="Monthly allowance per dependent (VNĐ)"),
    duration_months: int = typer.Option(120, "--duration-months", help="Duration of support in months"),
    victim_fault_pct: float = typer.Option(0.0, "--victim-fault", help="Victim fault percentage (0-100%)"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Calculate statutory compensation for loss of life (Điều 591, 593 BLDS & NQ 02/2022)."""
    engine = TortCompensationEngine()
    dependents_list = []
    for i in range(dependents_count):
        dependents_list.append({
            "full_name": f"Người phụ thuộc #{i+1}",
            "relationship": "CHILD" if i == 0 else "PARENT",
            "monthly_allowance": monthly_allowance,
            "duration_months": duration_months,
        })

    result = engine.calculate_life_damage(
        pre_death_treatment_costs=treatment_costs,
        reasonable_funeral_expenses=funeral_costs,
        dependents=dependents_list,
        victim_fault_percentage=victim_fault_pct,
    )

    if json_out:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(Panel.fit(
        f"[bold red]TỔNG MỨC BỒI THƯỜNG TÍNH MẠNG PHẢI NỘP: {result['final_payable_compensation']:,.0f} VNĐ[/bold red]\n"
        f"[dim]Mai táng: {result['breakdown']['reasonable_funeral_expenses']:,.0f} VNĐ | Cấp dưỡng: {result['breakdown']['total_dependent_allowances']:,.0f} VNĐ | Tinh thần: {result['breakdown']['emotional_distress']:,.0f} VNĐ[/dim]",
        box=box.ROUNDED,
        border_style="red",
    ))


@tort_app.command("settle")
def settle_cmd(
    case_id: str = typer.Option(..., "--case-id", "-c", help="Case ID"),
    amount: float = typer.Option(..., "--amount", "-a", help="Total agreed settlement amount (VNĐ)"),
    terms: str = typer.Option(..., "--terms", help="Payment terms & installment plan"),
    conciliator: Optional[str] = typer.Option(None, "--conciliator", help="Conciliator / Mediator name"),
    court_recognized: bool = typer.Option(False, "--court-recognized", help="Recognized by Court decree"),
    json_out: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Record an out-of-court settlement agreement (Biên bản hòa giải thành)."""
    engine = TortCompensationEngine()
    result = engine.create_settlement_agreement(
        case_id=case_id,
        total_agreed_amount=amount,
        payment_terms=terms,
        conciliator_name=conciliator,
        is_court_recognized=court_recognized,
    )

    if json_out:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    console.print(f"[bold green]✓ Đã lập biên bản hòa giải thành: {result['settlement_id']}[/bold green]")
    console.print(f"[cyan]Tổng số tiền thỏa thuận:[/cyan] {result['total_agreed_amount']:,.0f} VNĐ")
