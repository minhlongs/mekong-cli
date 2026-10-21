# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phases 173 & 174 CLI subcommands: AEO Risk Channeling & Duty Refund / BCQT 15."""

from __future__ import annotations

import json
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.fta_duty_engine import AEOComplianceEngine, DutyExemptionRefundEngine

console = Console()


def evaluate_aeo(
    enterprise_type: str = typer.Option("GENERAL_TRADER", "--enterprise-type", "--type", "-t", help="Loại hình (GENERAL_TRADER, AGRI_AQUA_TEXTILE, HIGH_TECH_SOFTWARE, CUSTOMS_BROKER)"),
    turnover_usd: float = typer.Option(..., "--turnover-usd", "--turnover", "-u", help="Kim ngạch XNK bình quân năm (USD)"),
    compliance_years: int = typer.Option(2, "--years", "-y", help="Số năm tuân thủ pháp luật hải quan liên tục"),
    major_violations: bool = typer.Option(False, "--violations", help="Có vi phạm pháp luật thuế/hải quan nghiêm trọng"),
    unqualified_audit: bool = typer.Option(False, "--unqualified-audit", help="Báo cáo kiểm toán có ngoại trừ hoặc không chấp nhận"),
    declarations: int = typer.Option(0, "--declarations", "-d", help="Số lượng tờ khai/năm (đối với đại lý hải quan)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện công nhận Doanh nghiệp Ưu tiên (AEO) theo Điều 42 Luật Hải quan 2014."""
    result = AEOComplianceEngine.evaluate_aeo_eligibility(
        enterprise_type=enterprise_type,
        annual_turnover_usd=turnover_usd,
        compliance_years=compliance_years,
        had_major_tax_violations=major_violations,
        has_unqualified_audit=unqualified_audit,
        custom_broker_declarations=declarations,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    status_color = "bold green" if result.is_eligible else "bold red"
    console.print(Panel(f"[{status_color}]{result.summary_vn}[/{status_color}]", title="KẾT QUẢ THẨM ĐỊNH DOANH NGHIỆP ƯU TIÊN (AEO)"))

    table = Table(box=box.ROUNDED)
    table.add_column("Tiêu chí", style="cyan")
    table.add_column("Thực tế", style="white")
    table.add_column("Ngưỡng quy định", style="yellow")
    table.add_column("Đánh giá", style="bold")

    t_eval = "[green]ĐẠT[/green]" if result.turnover_qualified else "[red]CHƯA ĐẠT[/red]"
    c_eval = "[green]ĐẠT[/green]" if result.compliance_qualified else "[red]CHƯA ĐẠT[/red]"
    a_eval = "[green]ĐẠT[/green]" if result.audit_opinion_clean else "[red]CHƯA ĐẠT[/red]"

    table.add_row("Kim ngạch / Tờ khai", f"{result.annual_turnover_usd:,.0f} USD", f"{result.turnover_threshold_usd:,.0f} USD/năm", t_eval)
    table.add_row("Lịch sử tuân thủ", f"{result.compliance_years} năm", ">= 2 năm không vi phạm", c_eval)
    table.add_row("Kiểm toán độc lập", "Chấp nhận toàn phần" if result.audit_opinion_clean else "Có ý kiến ngoại trừ", "Chấp nhận toàn phần", a_eval)

    console.print(table)

    if result.is_eligible:
        console.print("[bold green]Quyền lợi đặc quyền của Doanh nghiệp AEO:[/bold green]")
        for b in result.statutory_benefits_vn:
            console.print(f" - [green]✓[/green] {b}")


def assess_channeling(
    is_aeo: bool = typer.Option(False, "--aeo", help="Doanh nghiệp đã được công nhận AEO"),
    risk_score: float = typer.Option(0.0, "--risk", "-r", help="Điểm rủi ro hệ thống (0 - 100)"),
    alert: bool = typer.Option(False, "--alert", help="Có thông tin tình báo cảnh báo rủi ro trọng điểm"),
    random: bool = typer.Option(False, "--random", help="Rơi vào kiểm tra xác suất ngẫu nhiên (<= 0.5%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Đánh giá phân luồng hải quan (Xanh / Vàng / Đỏ) và thời gian thông quan dự kiến."""
    result = AEOComplianceEngine.assess_customs_channel(
        is_aeo=is_aeo,
        risk_score=risk_score,
        has_intelligence_alert=alert,
        random_inspection_hit=random,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    table = Table(title="KẾT QUẢ PHÂN LUỒNG TỜ KHAI HẢI QUAN & QUẢN LÝ RỦI RO", box=box.ROUNDED)
    table.add_column("Thông số", style="cyan")
    table.add_column("Giá trị", style="bold white")

    ch_name = "LUỒNG XANH" if "GREEN" in result.channel else ("LUỒNG VÀNG" if "YELLOW" in result.channel else "LUỒNG ĐỎ")
    table.add_row("Luồng tờ khai", f"{result.channel} ({ch_name})")
    table.add_row("Tỷ lệ kiểm tra thực tế", f"{result.inspection_ratio_pct}%")
    table.add_row("Kiểm tra hồ sơ chi tiết", "CÓ" if result.documentary_check_required else "MIỄN KIỂM TRA")
    table.add_row("Kiểm tra thực tế hàng hóa", "CÓ" if result.physical_inspection_required else "MIỄN KIỂM TRA")
    table.add_row("Thời gian thông quan ước tính", f"{result.handling_timeline_hours} giờ")

    console.print(table)
    console.print(Panel(result.rationale_vn, title="Lý Do Phân Luồng", border_style="yellow"))


def calc_sxxk_refund(
    duty_paid: float = typer.Argument(..., help="Tổng tiền thuế nhập khẩu đã nộp cho lô nguyên liệu (VNĐ)"),
    imported_qty: float = typer.Argument(..., help="Tổng số lượng nguyên liệu nhập khẩu"),
    exported_qty: float = typer.Argument(..., help="Số lượng nguyên liệu đã thực tế xuất khẩu"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính số thuế nhập khẩu được hoàn đối với nguyên liệu nhập khẩu sản xuất xuất khẩu (SXXK)."""
    result = DutyExemptionRefundEngine.calculate_sxxk_duty_refund(
        total_duty_paid_vnd=duty_paid,
        raw_material_imported_qty=imported_qty,
        raw_material_exported_qty=exported_qty,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    table = Table(title="TÍNH TOÁN HOÀN THUẾ NHẬP KHẨU NGUYÊN LIỆU SXXK (ĐIỀU 36 NĐ 134)", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="bold green", justify="right")

    table.add_row("Số thuế NK đã nộp", f"{result.total_duty_paid_vnd:,.0f} VNĐ")
    table.add_row("Lượng nguyên liệu nhập khẩu", f"{result.raw_material_imported_qty:,.2f}")
    table.add_row("Lượng nguyên liệu đã xuất khẩu", f"{result.raw_material_exported_qty:,.2f}")
    table.add_row("Tỷ lệ hoàn thuế", f"{result.refund_ratio_pct}%")
    table.add_row("Số tiền thuế được hoàn", f"{result.refund_duty_amount_vnd:,.0f} VNĐ")
    table.add_row("Số tiền thuế còn lại chưa hoàn", f"{result.retained_duty_amount_vnd:,.0f} VNĐ")

    console.print(table)
    console.print(Panel(result.advice_vn, title="Khuyến Nghị Hồ Sơ Hoàn Thuế", border_style="cyan"))


def reconcile_bcqt(
    opening: float = typer.Argument(..., help="Số lượng tồn đầu kỳ"),
    imported: float = typer.Argument(..., help="Số lượng nhập trong kỳ"),
    exported: float = typer.Argument(..., help="Số lượng thành phẩm xuất khẩu"),
    bom: float = typer.Option(..., "--bom", "-b", help="Định mức tiêu hao nguyên vật liệu (BOM)"),
    scrap: float = typer.Option(0.0, "--scrap", "-s", help="Lượng phế phẩm tiêu hao được duyệt"),
    actual: float = typer.Option(..., "--actual", "-a", help="Số lượng tồn kho thực tế kiểm kê cuối kỳ"),
    unit_duty: float = typer.Option(0.0, "--unit-duty", "-u", help="Đơn giá thuế nhập khẩu bình quân (VNĐ/đơn vị)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Cân đối Báo cáo Quyết toán Mẫu 15/BCQT-NVL/GSQL và cảnh báo rủi ro ấn định thuế chênh lệch âm."""
    result = DutyExemptionRefundEngine.reconcile_materials_bcqt15(
        opening_balance=opening,
        imported_in_period=imported,
        exported_finished_goods_qty=exported,
        bom_consumption_norm=bom,
        approved_scrap_qty=scrap,
        actual_physical_inventory=actual,
        raw_material_unit_duty_vnd=unit_duty,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    border_color = "red" if result.is_deficit_risk else ("green" if result.is_balanced else "yellow")

    table = Table(title="BÁO CÁO CÂN BẰNG QUYẾT TOÁN NGUYÊN LIỆU (MẪU 15/BCQT-NVL/GSQL)", box=box.ROUNDED)
    table.add_column("Chỉ tiêu", style="cyan")
    table.add_column("Số lượng / Giá trị", style="white", justify="right")

    table.add_row("Tồn đầu kỳ", f"{result.opening_balance:,.2f}")
    table.add_row("Nhập trong kỳ", f"{result.imported_in_period:,.2f}")
    table.add_row("Xuất sản phẩm", f"{result.exported_finished_goods_qty:,.2f}")
    table.add_row("Định mức tiêu hao (BOM)", f"{result.bom_consumption_norm:,.4f}")
    table.add_row("Phế phẩm hợp lệ", f"{result.approved_scrap_qty:,.2f}")
    table.add_row("Tồn lý thuyết cuối kỳ", f"{result.theoretical_closing_balance:,.2f}")
    table.add_row("Tồn kiểm kê thực tế", f"{result.actual_physical_inventory:,.2f}")
    table.add_row("Chênh lệch (Variance)", f"{result.variance_qty:,.2f}")

    if result.is_deficit_risk:
        table.add_row("Thuế NK có nguy cơ bị truy thu", f"[bold red]{result.potential_unpaid_duty_vnd:,.0f} VNĐ[/bold red]")
        table.add_row("Tiền phạt chậm nộp dự kiến", f"[bold red]{result.late_payment_interest_per_day_vnd:,.0f} VNĐ/ngày[/bold red]")

    console.print(table)
    console.print(Panel(result.audit_warning_vn, title="Cảnh Báo Kiểm Tra Sau Thông Quan & Quyết Toán", border_style=border_color))
