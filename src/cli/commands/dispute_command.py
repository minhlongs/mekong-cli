"""
CLI Commands for Mekong Dispute Resolution & Maritime Law Suite (Phases 159 - 162).
Covers:
1. Commercial Arbitration & VIAC 2024 (Phase 159)
2. Civil Judgment Enforcement & Asset Recovery (Phase 160)
3. Court Litigation & Resolution 326 Court Fees (Phase 161)
4. Maritime Law, Carrier Liability & General Average (Phase 162)
"""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.core.dispute_engine import (
    ArbitrationTribunalType,
    CommercialArbitrationEngine,
    CivilEnforcementEngine,
    CourtLitigationEngine,
)
from src.core.maritime_law_engine import (
    GeneralAverageInterest,
    MaritimeLawEngine,
)

dispute_app = typer.Typer(
    name="dispute",
    help="Hệ thống Trọng tài VIAC, Thi hành án dân sự, Tố tụng Tòa án & Luật Hàng hải (Phases 159 - 162).",
)
console = Console()


@dispute_app.callback(invoke_without_command=True)
def dispute_summary(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả dưới dạng JSON"),
) -> None:
    """Tổng quan bộ giải pháp Mekong Dispute Resolution & Maritime Law Suite."""
    if ctx.invoked_subcommand is not None:
        return

    data = {
        "suite": "Mekong Dispute & Maritime Law Suite",
        "phases": ["159", "160", "161", "162"],
        "modules": {
            "arbitration": "Commercial Arbitration & VIAC Rules 2024 (Luật TTTM 2010)",
            "enforcement": "Civil Judgment Enforcement (Luật THADS 2014 & TT 216/2016)",
            "court": "Court Litigation & Fees (BLTTDS 2015 & NQ 326/2016)",
            "maritime": "Vietnam Maritime Code 2015, SDR Carrier Limit & York-Antwerp GA",
        },
        "status": "active",
    }

    if json_mode:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            "[bold cyan]MEKONG DISPUTE RESOLUTION & MARITIME LAW SUITE[/bold cyan]\n"
            "[italic dim]Căn cứ: Luật TTTM 2010, Luật THADS 2014, BLTTDS 2015, Bộ luật Hàng hải 2015[/italic dim]\n\n"
            "  [bold yellow]1. Trọng tài VIAC:[/]    Kiểm tra điều khoản trọng tài, Biểu phí VIAC 2024, Thời hiệu 2 năm\n"
            "  [bold yellow]2. Thi hành án dân sự:[/] Thời hiệu THADS 5 năm, Phí THADS 3% (Trần 200M), Thứ tự thanh toán\n"
            "  [bold yellow]3. Tố tụng Tòa án:[/]     Phân định thẩm quyền cấp Tỉnh/Huyện, Án phí sơ thẩm & Tạm ứng 50%\n"
            "  [bold yellow]4. Luật Hàng hải:[/]      Giới hạn trách nhiệm 666.67 SDR/kiện, Tổn thất chung York-Antwerp",
            title="[bold green]Phases 159 - 162 Overview[/bold green]",
            border_style="cyan",
        )
    )


# ============================================================================
# 1. COMMERCIAL ARBITRATION SUBCOMMANDS (PHASE 159)
# ============================================================================

@dispute_app.command("arbitration-clause")
def check_arbitration_clause(
    clause: str = typer.Argument(..., help="Nội dung điều khoản thỏa thuận trọng tài"),
    dispute_type: str = typer.Option("commercial", "--type", "-t", help="Loại tranh chấp (commercial, civil, etc.)"),
    parties_capacity: bool = typer.Option(True, "--capacity/--no-capacity", help="Năng lực ký kết của các bên"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm tra tính hợp pháp và hiệu lực của thỏa thuận trọng tài (Điều 16, 18 Luật TTTM 2010)."""
    result = CommercialArbitrationEngine.validate_arbitration_clause(
        clause_text=clause,
        dispute_type=dispute_type,
        parties_have_capacity=parties_capacity,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    status_str = "[bold green]HỢP LỆ[/bold green]" if result.is_valid else "[bold red]VÔ HIỆU / CÓ RỦI RO[/bold red]"
    console.print(
        Panel.fit(
            f"[bold]Tình trạng:[/] {status_str}\n"
            f"[bold]Cơ quan chỉ định:[/] [cyan]{result.arbitration_institution}[/cyan]\n"
            f"[bold]Căn cứ pháp lý:[/] {result.statutory_basis}\n"
            f"[bold]Khuyến nghị:[/] {result.advice_vn}",
            title="[bold cyan]Thẩm Tra Thỏa Thuận Trọng Tài[/bold cyan]",
            border_style="green" if result.is_valid else "red",
        )
    )


@dispute_app.command("viac-fee")
def calc_viac_fee(
    claim_amount: float = typer.Argument(..., help="Giá trị tranh chấp (VNĐ)"),
    sole_arbitrator: bool = typer.Option(False, "--sole", "-s", help="Hội đồng 1 Trọng tài viên (giảm 30% phí)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính phí trọng tài VIAC theo Biểu phí Quy tắc VIAC 2024."""
    tribunal = ArbitrationTribunalType.SOLE_ARBITRATOR if sole_arbitrator else ArbitrationTribunalType.THREE_ARBITRATORS
    result = CommercialArbitrationEngine.calculate_viac_fee(
        claim_amount_vnd=claim_amount,
        tribunal_type=tribunal,
    )

    if json_mode:
        payload = {
            "claim_amount_vnd": result.claim_amount_vnd,
            "tribunal_type": result.tribunal_type.value,
            "arbitration_fee_vnd": result.arbitration_fee_vnd,
            "sole_discount_applied": result.sole_discount_applied,
            "legal_basis": result.legal_basis,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold]Giá trị tranh chấp:[/] [yellow]{result.claim_amount_vnd:,.0f} VNĐ[/yellow]\n"
            f"[bold]Hội đồng trọng tài:[/] [cyan]{result.tribunal_type.value}[/cyan]\n"
            f"[bold]Giảm 30% cho 1 TTV:[/] {'Có' if result.sole_discount_applied else 'Không'}\n"
            f"[bold]Phí trọng tài VIAC:[/] [bold green]{result.arbitration_fee_vnd:,.0f} VNĐ[/bold green]\n"
            f"[bold]Căn cứ pháp lý:[/] {result.legal_basis}",
            title="[bold yellow]Biểu Phí Trọng Tài VIAC 2024[/bold yellow]",
            border_style="yellow",
        )
    )


# ============================================================================
# 2. CIVIL JUDGMENT ENFORCEMENT SUBCOMMANDS (PHASE 160)
# ============================================================================

@dispute_app.command("enforcement-fee")
def calc_enforcement_fee(
    recovered_amount: float = typer.Argument(..., help="Số tiền thực nhận được thi hành án (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính phí thi hành án dân sự theo Thông tư 216/2016/TT-BTC (3%, trần 200 triệu VNĐ)."""
    result = CivilEnforcementEngine.calculate_enforcement_fee(recovered_amount_vnd=recovered_amount)

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold]Số tiền thực nhận:[/] [yellow]{result.recovered_amount_vnd:,.0f} VNĐ[/yellow]\n"
            f"[bold]Tỷ lệ luật định:[/] {result.statutory_fee_rate_pct}%\n"
            f"[bold]Phí THADS tính toán:[/] {result.calculated_fee_vnd:,.0f} VNĐ\n"
            f"[bold]Phí THADS thực nộp:[/] [bold green]{result.actual_fee_payable_vnd:,.0f} VNĐ[/bold green]\n"
            f"[bold]Áp trần 200 triệu VNĐ:[/] {'Có' if result.is_capped_at_200m else 'Không'}\n"
            f"[bold]Căn cứ:[/] {result.circular_basis}",
            title="[bold cyan]Phí Thi Hành Án Dân Sự (TT 216/2016)[/bold cyan]",
            border_style="cyan",
        )
    )


@dispute_app.command("enforcement-priority")
def calc_enforcement_priority(
    total_recovered: float = typer.Argument(..., help="Tổng tiền thu được từ thi hành án (VNĐ)"),
    alimony: float = typer.Option(0.0, "--alimony", "-a", help="Nghĩa vụ tiền cấp dưỡng (VNĐ)"),
    labor: float = typer.Option(0.0, "--labor", "-l", help="Tiền lương, trợ cấp thôi việc (VNĐ)"),
    court_fee: float = typer.Option(0.0, "--court", "-c", help="Án phí, lệ phí Tòa án (VNĐ)"),
    other_claims: float = typer.Option(0.0, "--other", "-o", help="Nghĩa vụ thi hành án khác (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Phân bổ thứ tự thanh toán tiền thi hành án dân sự (Điều 47 Luật THADS 2014)."""
    result = CivilEnforcementEngine.distribute_payment_priority(
        total_recovered_amount=total_recovered,
        alimony_due=alimony,
        labor_salary_due=labor,
        court_fees_due=court_fee,
        other_claims_due=other_claims,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    table = Table(title="Phân Bổ Thứ Tự Ưu Tiên Thanh Toán (Điều 47)", box=box.ROUNDED)
    table.add_column("Thứ tự ưu tiên", style="cyan")
    table.add_column("Khoản nghĩa vụ", style="bold")
    table.add_column("Số tiền chi trả (VNĐ)", style="green")

    table.add_row("Hạng 1", "Tiền cấp dưỡng", f"{result.alimony_paid:,.0f}")
    table.add_row("Hạng 2", "Tiền lương & trợ cấp thôi việc", f"{result.labor_paid:,.0f}")
    table.add_row("Hạng 3", "Án phí, lệ phí Tòa án", f"{result.court_fee_paid:,.0f}")
    table.add_row("Hạng 4", "Các nghĩa vụ khác", f"{result.other_claims_paid:,.0f}")
    table.add_row("Dư lại", "Tiền trả lại cho người phải THA", f"{result.remaining_surplus:,.0f}")

    console.print(table)


# ============================================================================
# 3. COURT LITIGATION SUBCOMMANDS (PHASE 161)
# ============================================================================

@dispute_app.command("court-fee")
def calc_court_fee(
    claim_amount: float = typer.Argument(..., help="Giá trị tranh chấp (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính án phí sơ thẩm và tạm ứng án phí 50% theo Nghị quyết 326/2016/UBTVQH14."""
    result = CourtLitigationEngine.calculate_court_fee(claim_amount_vnd=claim_amount)

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold]Giá trị tranh chấp:[/] [yellow]{result.claim_amount_vnd:,.0f} VNĐ[/yellow]\n"
            f"[bold]Khung luật định:[/] {result.statutory_bracket_desc}\n"
            f"[bold]Án phí sơ thẩm:[/] [bold green]{result.first_instance_fee_vnd:,.0f} VNĐ[/bold green]\n"
            f"[bold]Tạm ứng án phí (50%):[/] [bold yellow]{result.advance_payment_vnd:,.0f} VNĐ[/bold yellow]\n"
            f"[bold]Căn cứ pháp lý:[/] {result.legal_basis}",
            title="[bold cyan]Án Phí Dân Sự / Kinh Doanh Thương Mại (NQ 326)[/bold cyan]",
            border_style="cyan",
        )
    )


@dispute_app.command("court-jurisdiction")
def check_court_jurisdiction(
    foreign_element: bool = typer.Option(False, "--foreign", "-f", help="Vụ việc có yếu tố nước ngoài"),
    ip_dispute: bool = typer.Option(False, "--ip", help="Tranh chấp sở hữu trí tuệ"),
    maritime_dispute: bool = typer.Option(False, "--maritime", "-m", help="Tranh chấp hàng hải"),
    province: str = typer.Option("TP. Hồ Chí Minh", "--province", "-p", help="Tỉnh/Thành phố liên quan"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Phân định thẩm quyền Tòa án cấp Tỉnh hay cấp Huyện (Điều 35, 37 BLTTDS 2015)."""
    result = CourtLitigationEngine.resolve_jurisdiction(
        has_foreign_element=foreign_element,
        is_intellectual_property=ip_dispute,
        is_maritime=maritime_dispute,
        province=province,
    )

    if json_mode:
        payload = {
            "court_level": result.court_level.value,
            "has_foreign_element": result.has_foreign_element,
            "is_intellectual_property": result.is_intellectual_property,
            "is_maritime": result.is_maritime,
            "competent_forum_vn": result.competent_forum_vn,
            "legal_basis": result.legal_basis,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold]Cấp Tòa án thẩm quyền:[/] [bold yellow]{result.court_level.value.upper()}[/bold yellow]\n"
            f"[bold]Cơ quan thụ lý dự kiến:[/] [bold green]{result.competent_forum_vn}[/bold green]\n"
            f"[bold]Căn cứ pháp lý:[/] {result.legal_basis}",
            title="[bold cyan]Phân Định Thẩm Quyền Tòa Án (BLTTDS 2015)[/bold cyan]",
            border_style="cyan",
        )
    )


# ============================================================================
# 4. MARITIME LAW SUBCOMMANDS (PHASE 162)
# ============================================================================

@dispute_app.command("carrier-liability")
def calc_carrier_liability(
    packages: int = typer.Argument(..., help="Số lượng kiện hàng / đơn vị bao gói"),
    weight_kg: float = typer.Argument(..., help="Tổng trọng lượng cả bì (kg)"),
    actual_loss: float = typer.Argument(..., help="Tổn thất thực tế (VNĐ)"),
    sdr_rate: float = typer.Option(34500.0, "--sdr-rate", "-r", help="Tỷ giá SDR/VNĐ"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính giới hạn trách nhiệm bồi thường của người vận chuyển (Điều 152 Bộ luật Hàng hải 2015)."""
    result = MaritimeLawEngine.calculate_carrier_liability(
        packages_count=packages,
        gross_weight_kg=weight_kg,
        actual_loss_vnd=actual_loss,
        sdr_rate_vnd=sdr_rate,
    )

    if json_mode:
        typer.echo(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return

    console.print(
        Panel.fit(
            f"[bold]Số kiện hàng:[/] {result.packages_count} | [bold]Trọng lượng:[/] {result.gross_weight_kg:,.1f} kg\n"
            f"[bold]Tổn thất thực tế:[/] [yellow]{result.actual_loss_vnd:,.0f} VNĐ[/yellow]\n"
            f"[bold]Hạn mức luật định (SDR):[/] {result.applicable_limit_sdr:,.2f} SDR\n"
            f"[bold]Trần bồi thường quy đổi:[/] {result.statutory_ceiling_vnd:,.0f} VNĐ\n"
            f"[bold]Số tiền người VC phải trả:[/] [bold green]{result.carrier_payable_vnd:,.0f} VNĐ[/bold green]\n"
            f"[bold]Áp dụng giới hạn trách nhiệm:[/] {'Có' if result.is_limited else 'Không'}\n"
            f"[bold]Căn cứ pháp lý:[/] {result.legal_basis}",
            title="[bold cyan]Giới Hạn Trách Nhiệm Vận Chuyển Hàng Hải (Điều 152)[/bold cyan]",
            border_style="cyan",
        )
    )


@dispute_app.command("general-average")
def calc_general_average(
    ship_val: float = typer.Option(..., "--ship-val", "-s", help="Giá trị tàu chịu phân bổ (VNĐ)"),
    cargo_val: float = typer.Option(..., "--cargo-val", "-c", help="Giá trị hàng hóa chịu phân bổ (VNĐ)"),
    freight_val: float = typer.Option(0.0, "--freight-val", "-f", help="Cước phí chịu phân bổ (VNĐ)"),
    ship_loss: float = typer.Option(0.0, "--ship-loss", help="Tổn thất/hy sinh của tàu (VNĐ)"),
    cargo_loss: float = typer.Option(0.0, "--cargo-loss", help="Tổn thất/hy sinh của hàng (VNĐ)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính toán phân bổ tổn thất chung (General Average - York-Antwerp Rules 2016)."""
    interests = [
        GeneralAverageInterest("Tàu biển (Vessel)", contributory_value_vnd=ship_val, sacrifice_incurred_vnd=ship_loss),
        GeneralAverageInterest("Hàng hóa (Cargo)", contributory_value_vnd=cargo_val, sacrifice_incurred_vnd=cargo_loss),
    ]
    if freight_val > 0:
        interests.append(GeneralAverageInterest("Cước phí (Freight)", contributory_value_vnd=freight_val, sacrifice_incurred_vnd=0.0))

    result = MaritimeLawEngine.calculate_general_average(interests)

    if json_mode:
        payload = {
            "total_contributory_value_vnd": result.total_contributory_value_vnd,
            "total_general_average_loss_vnd": result.total_general_average_loss_vnd,
            "contribution_ratio_pct": result.contribution_ratio_pct,
            "is_zero_sum_balanced": result.is_zero_sum_balanced,
            "participants": [p.__dict__ for p in result.participants],
            "legal_basis": result.legal_basis,
        }
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Bảng Phân Bổ Tổn Thất Chung (Tỷ lệ: {result.contribution_ratio_pct:.4f}%)", box=box.ROUNDED)
    table.add_column("Đối tượng chịu phân bổ", style="cyan")
    table.add_column("Giá trị chịu PB (VNĐ)", style="yellow")
    table.add_column("Hy sinh/Chi phí (VNĐ)", style="red")
    table.add_column("Đóng góp gộp (VNĐ)", style="blue")
    table.add_column("Quyết toán ròng (VNĐ)", style="bold green")

    for p in result.participants:
        table.add_row(
            p.interest_name,
            f"{p.contributory_value_vnd:,.0f}",
            f"{p.sacrifice_incurred_vnd:,.0f}",
            f"{p.gross_contribution_vnd:,.0f}",
            f"{p.net_settlement_vnd:+,.0f}",
        )

    console.print(table)
