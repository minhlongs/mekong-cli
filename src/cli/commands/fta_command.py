# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Vietnam Free Trade Agreements (FTAs), EPE, AEO & Duty Exemption CLI Commands (Phases 171 - 174).

Provides CLI commands for:
- Phase 171: FTAs Preferential Tariffs & Rules of Origin Engine
- Phase 172: Export Processing Enterprises (EPE) & Industrial Parks Regime Engine
- Phase 173: Authorized Economic Operator (AEO) & Risk Channeling Engine
- Phase 174: Duty Exemption, Refund & Material Reconciliation (BCQT 15) Engine
"""

from __future__ import annotations

import json
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.core.fta_duty_engine import (
    FTATariffOriginEngine,
    EPECustomsEngine,
    AEOComplianceEngine,
    DutyExemptionRefundEngine,
)

fta_app = typer.Typer(
    name="fta",
    help="FTA — Vietnam Free Trade Agreements, EPE, AEO & Duty Exemption Suite (Phases 171-174)",
    no_args_is_help=False,
)
console = Console()


@fta_app.callback(invoke_without_command=True)
def fta_default(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất thông tin tổng quan dạng JSON"),
) -> None:
    """Tổng quan bộ công cụ Hiệp định FTA, Doanh nghiệp Chế xuất, AEO & Hoàn thuế XNK."""
    if ctx.invoked_subcommand is not None:
        return

    if json_mode:
        data = {
            "suite": "Mekong Vietnam FTA, EPE, AEO & Duty Exemption Suite",
            "phases": [171, 172, 173, 174],
            "subcommands": [
                "savings",
                "origin",
                "proof",
                "epe-check",
                "on-spot",
                "scrap",
                "aeo",
                "channel",
                "refund-sxxk",
                "bcqt",
            ],
            "statutes": [
                "Nghị định 115/2022/NĐ-CP (EVFTA), NĐ 116/2022/NĐ-CP (CPTPP), NĐ 129/2022/NĐ-CP (RCEP)",
                "Nghị định 35/2022/NĐ-CP (KCN & DNCX), Điều 86 Thông tư 38/2015/TT-BTC & TT 39/2018/TT-BTC",
                "Điều 42-45 Luật Hải quan 2014, Thông tư 72/2015/TT-BTC & Thông tư 07/2019/TT-BTC (AEO)",
                "Luật Thuế XNK 2016, Nghị định 134/2016/NĐ-CP & Nghị định 18/2021/NĐ-CP, Mẫu 15/BCQT-NVL/GSQL",
            ],
        }
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
        return

    panel_content = (
        "[bold cyan]Mekong Vietnam FTA, EPE, AEO & Duty Exemption Suite (Phases 171-174)[/bold cyan]\n\n"
        "[bold green]1. Ưu đãi Thuế quan & Tiêu chí Xuất xứ FTA (Phase 171):[/bold green]\n"
        "   - [yellow]savings[/yellow]: So sánh thuế MFN vs FTA & tính số thuế tiết kiệm\n"
        "   - [yellow]origin[/yellow]: Thẩm định tiêu chí xuất xứ (WO, CC, CTH, CTSH, RVC, De Minimis)\n"
        "   - [yellow]proof[/yellow]: Xác định hình thức chứng từ xuất xứ (C/O EUR.1, CPTPP, RCEP, REX)\n\n"
        "[bold green]2. Doanh nghiệp Chế xuất & XNK Tại chỗ (Phase 172):[/bold green]\n"
        "   - [yellow]epe-check[/yellow]: Kiểm tra 4 điều kiện giám sát hải quan DNCX (NĐ 35/2022)\n"
        "   - [yellow]on-spot[/yellow]: Kiểm tra hạn 15 ngày làm việc tờ khai đối ứng XNK tại chỗ (Điều 86 TT 38)\n"
        "   - [yellow]scrap[/yellow]: Tính thuế NK & GTGT khi bán phế liệu/phế phẩm vào nội địa\n\n"
        "[bold green]3. Doanh nghiệp Ưu tiên & Quản lý Rủi ro (Phase 173):[/bold green]\n"
        "   - [yellow]aeo[/yellow]: Đánh giá điều kiện công nhận Doanh nghiệp Ưu tiên AEO (TT 72/2015)\n"
        "   - [yellow]channel[/yellow]: Phân luồng tờ khai hải quan (Xanh / Vàng / Đỏ) & thời gian thông quan\n\n"
        "[bold green]4. Miễn Hoàn thuế XNK & Báo cáo Quyết toán (Phase 174):[/bold green]\n"
        "   - [yellow]refund-sxxk[/yellow]: Tính số thuế NK được hoàn cho hàng sản xuất xuất khẩu (Điều 36 NĐ 134)\n"
        "   - [yellow]bcqt[/yellow]: Cân đối xuất nhập tồn nguyên liệu Mẫu 15/BCQT & cảnh báo ấn định thuế\n"
    )
    console.print(Panel(panel_content, box=box.ROUNDED, border_style="cyan"))


# ---------------------------------------------------------------------
# Phase 171: FTAs & Origin Commands
# ---------------------------------------------------------------------

@fta_app.command("savings")
def calc_tariff_savings(
    customs_value: float = typer.Argument(..., help="Trị giá hải quan tính thuế (VNĐ)"),
    mfn_rate: float = typer.Option(..., "--mfn", "-m", help="Thuế suất MFN thông thường (%)"),
    fta_rate: float = typer.Option(..., "--fta", "-f", help="Thuế suất ưu đãi đặc biệt FTA (%)"),
    agreement: str = typer.Option("EVFTA", "--agreement", "-a", help="Tên hiệp định (EVFTA, CPTPP, RCEP, ATIGA...)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """So sánh và tính số tiền thuế nhập khẩu tiết kiệm được nhờ hiệp định thương mại tự do FTA."""
    result = FTATariffOriginEngine.calculate_tariff_savings(
        customs_value_vnd=customs_value,
        mfn_rate_pct=mfn_rate,
        fta_rate_pct=fta_rate,
        agreement=agreement,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    table = Table(title=f"SO SÁNH THUẾ QUAN & TIẾT KIỆM FTA ({result.effective_agreement})", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="bold green", justify="right")

    table.add_row("Trị giá hải quan", f"{result.customs_value_vnd:,.0f} VNĐ")
    table.add_row("Thuế suất MFN", f"{result.mfn_rate_pct}%")
    table.add_row(f"Thuế suất FTA ({result.effective_agreement})", f"{result.fta_rate_pct}%")
    table.add_row("Tiền thuế MFN phải nộp", f"{result.mfn_duty_vnd:,.0f} VNĐ")
    table.add_row("Tiền thuế FTA phải nộp", f"{result.fta_duty_vnd:,.0f} VNĐ")
    table.add_row("Số tiền thuế tiết kiệm", f"{result.duty_savings_vnd:,.0f} VNĐ")
    table.add_row("Tỷ lệ giảm chi phí thuế", f"{result.savings_pct}%")

    console.print(table)
    console.print(Panel(result.advice_vn, title="Tư Vấn Tối Ưu Chi Phí", border_style="yellow"))


@fta_app.command("origin")
def evaluate_origin(
    product_hs: str = typer.Argument(..., help="Mã số HS của sản phẩm thành phẩm (ví dụ: 8504.40)"),
    criterion: str = typer.Option(..., "--criterion", "-c", help="Tiêu chí xuất xứ (WO, CC, CTH, CTSH, RVC, DE_MINIMIS)"),
    non_orig_hs: Optional[List[str]] = typer.Option(None, "--non-orig-hs", "-n", help="Danh sách mã HS nguyên liệu không xuất xứ"),
    rvc_actual: Optional[float] = typer.Option(None, "--rvc", help="Tỷ lệ hàm lượng khu vực thực tế (%)"),
    rvc_thresh: float = typer.Option(40.0, "--rvc-thresh", help="Ngưỡng RVC yêu cầu (%)"),
    fob_ratio: Optional[float] = typer.Option(None, "--fob-ratio", help="Tỷ lệ nguyên liệu không xuất xứ so với FOB (%)"),
    agreement: str = typer.Option("CPTPP", "--agreement", "-a", help="Hiệp định áp dụng (EVFTA, CPTPP, RCEP...)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Thẩm định điều kiện đáp ứng tiêu chí xuất xứ hàng hóa theo quy tắc xuất xứ FTA."""
    result = FTATariffOriginEngine.evaluate_origin_criterion(
        product_hs=product_hs,
        criterion=criterion,
        non_originating_materials_hs=non_orig_hs,
        rvc_actual_pct=rvc_actual,
        rvc_threshold_pct=rvc_thresh,
        non_originating_value_fob_pct=fob_ratio,
        agreement=agreement,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    qual_str = "[bold green]ĐẠT TIÊU CHÍ XUẤT XỨ (QUALIFIED)[/bold green]" if result.is_qualified else "[bold red]KHÔNG ĐẠT TIÊU CHÍ (DISQUALIFIED)[/bold red]"

    table = Table(title="KẾT QUẢ THẨM ĐỊNH QUY TẮC XUẤT XỨ FTA", box=box.ROUNDED)
    table.add_column("Thông tin", style="cyan")
    table.add_column("Giá trị", style="white")

    table.add_row("Mã HS thành phẩm", result.product_hs)
    table.add_row("Tiêu chí kiểm tra", result.criterion)
    table.add_row("Kết luận xuất xứ", qual_str)
    if result.rvc_calculated_pct is not None:
        table.add_row("Hàm lượng RVC thực tế", f"{result.rvc_calculated_pct}% (Ngưỡng: {result.rvc_threshold_pct}%)")
    if result.non_originating_value_pct is not None:
        table.add_row("Tỷ lệ De Minimis thực tế", f"{result.non_originating_value_pct}% (Trần: {result.de_minimis_threshold_pct}%)")
    table.add_row("Chứng từ xuất xứ yêu cầu", result.proof_type_required)

    console.print(table)
    console.print(Panel(result.details_vn, title="Chi Tiết Đánh Giá Pháp Lý", border_style="cyan"))


@fta_app.command("proof")
def determine_proof(
    agreement: str = typer.Option("EVFTA", "--agreement", "-a", help="Tên hiệp định (EVFTA, CPTPP, RCEP, ATIGA)"),
    value_eur: float = typer.Option(0.0, "--value-eur", "-v", help="Trị giá lô hàng quy đổi EUR"),
    approved_exporter: bool = typer.Option(False, "--approved", "-e", help="Có chứng nhận Approved Exporter / REX"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định hình thức chứng từ chứng nhận xuất xứ (C/O hoặc Tự chứng nhận) cần nộp."""
    result = FTATariffOriginEngine.determine_proof_of_origin(
        agreement=agreement,
        consignment_value_eur=value_eur,
        is_approved_exporter=approved_exporter,
    )

    if json_mode:
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    table = Table(title=f"CHỨNG TỪ CHỨNG NHẬN XUẤT XỨ ({agreement.upper()})", box=box.ROUNDED)
    table.add_column("Mục", style="cyan")
    table.add_column("Quy định", style="bold green")

    table.add_row("Hiệp định", result["agreement"])
    table.add_row("Hình thức chứng nhận", result["required_proof_form"])
    table.add_row("Cơ chế thực hiện", result["issuance_mechanism"])

    console.print(table)


# ---------------------------------------------------------------------
# Phase 172: EPE & Industrial Parks Commands
# ---------------------------------------------------------------------

@fta_app.command("epe-check")
def check_epe_conditions(
    barrier: bool = typer.Option(..., "--barrier/--no-barrier", help="Có hàng rào cứng ngăn cách khu vực"),
    camera: bool = typer.Option(..., "--camera/--no-camera", help="Có camera 24/7 kết nối hải quan"),
    gate: bool = typer.Option(..., "--gate/--no-gate", help="Có cổng/cửa ra vào riêng biệt"),
    erp: bool = typer.Option(..., "--erp/--no-erp", help="Có phần mềm quản lý xuất nhập tồn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra điều kiện kiểm tra, giám sát hải quan bắt buộc đối với DNCX (Điều 26 NĐ 35/2022)."""
    result = EPECustomsEngine.verify_epe_conditions(
        has_physical_barrier=barrier,
        has_camera_24_7=camera,
        has_separate_gate=gate,
        has_erp_inventory=erp,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    status_color = "bold green" if result.is_compliant else "bold red"
    console.print(Panel(f"[{status_color}]{result.customs_supervision_status}[/{status_color}]", title="KẾT QUẢ KIỂM TRA ĐIỀU KIỆN DNCX"))

    if result.missing_conditions:
        console.print("[bold red]Các điều kiện chưa hoàn thiện:[/bold red]")
        for cond in result.missing_conditions:
            console.print(f" - [red]✗[/red] {cond}")

    console.print(Panel(result.recommendations_vn, title="Khuyến Nghị Pháp Lý & Hải Quan", border_style="yellow"))


@fta_app.command("on-spot")
def check_on_spot(
    export_date: str = typer.Argument(..., help="Ngày thông quan tờ khai xuất khẩu tại chỗ (YYYY-MM-DD)"),
    ref_date: Optional[str] = typer.Option(None, "--ref-date", "--import-date", "-r", help="Ngày đối chiếu kiểm tra (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra thời hạn 15 ngày làm việc hoàn thành tờ khai nhập khẩu tại chỗ đối ứng (Điều 86 TT 38/2015)."""
    result = EPECustomsEngine.check_on_spot_deadline(
        export_declaration_date=export_date,
        reference_date=ref_date,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    status_color = "bold red" if result.is_overdue else "bold green"
    table = Table(title="THEO DÕI THỜI HẠN TỜ KHAI ĐỐI ỨNG XNK TẠI CHỖ", box=box.ROUNDED)
    table.add_column("Chỉ số", style="cyan")
    table.add_column("Giá trị", style="white")

    table.add_row("Ngày tờ khai xuất", result.export_declaration_date)
    table.add_row("Số ngày đã trôi qua", f"{result.days_elapsed} ngày")
    table.add_row("Thời hạn quy định tối đa", f"{result.deadline_days} ngày làm việc")
    table.add_row("Số ngày còn lại", f"{result.remaining_days} ngày")
    table.add_row("Trạng thái tuân thủ", f"[{status_color}]{result.compliance_status}[/{status_color}]")

    console.print(table)
    console.print(Panel(result.advice_vn, title="Cảnh Báo Tuân Thủ Hải Quan", border_style="yellow"))


@fta_app.command("scrap")
def calc_scrap_sale(
    value: float = typer.Argument(..., help="Giá trị thực tế phế liệu bán vào nội địa (VNĐ)"),
    hs_code: str = typer.Option(..., "--hs", "-h", help="Mã HS của phế liệu, phế phẩm"),
    duty_rate: float = typer.Option(..., "--duty", "-d", help="Thuế suất thuế nhập khẩu (%)"),
    vat_rate: float = typer.Option(10.0, "--vat", "-v", help="Thuế suất thuế GTGT nội địa (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính thuế nhập khẩu và GTGT khi DNCX bán phế liệu, phế phẩm vào thị trường nội địa (Điều 75 TT 38)."""
    result = EPECustomsEngine.calculate_scrap_domestic_sale_tax(
        scrap_value_vnd=value,
        scrap_hs_code=hs_code,
        import_duty_rate_pct=duty_rate,
        vat_rate_pct=vat_rate,
    )

    if json_mode:
        typer.echo(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    table = Table(title="THUẾ NỘI ĐỊA ÁP DỤNG CHO PHẾ LIỆU DNCX (LOẠI HÌNH A42)", box=box.ROUNDED)
    table.add_column("Khoản mục", style="cyan")
    table.add_column("Số tiền", style="bold green", justify="right")

    table.add_row("Trị giá bán phế liệu", f"{result.scrap_value_vnd:,.0f} VNĐ")
    table.add_row(f"Thuế nhập khẩu ({result.import_duty_rate_pct}%)", f"{result.import_duty_vnd:,.0f} VNĐ")
    table.add_row(f"Thuế GTGT ({result.vat_rate_pct}%)", f"{result.vat_vnd:,.0f} VNĐ")
    table.add_row("Tổng nghĩa vụ thuế phải nộp", f"{result.total_tax_payable_vnd:,.0f} VNĐ")

    console.print(table)
    console.print(Panel(result.notes_vn, title="Lưu Ý Kê Khai Hải Quan", border_style="cyan"))


# ---------------------------------------------------------------------
# Phase 173: AEO & Risk Channeling Commands
# ---------------------------------------------------------------------

@fta_app.command("aeo")
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


@fta_app.command("channel")
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


# ---------------------------------------------------------------------
# Phase 174: Duty Exemption, Refund & BCQT 15 Commands
# ---------------------------------------------------------------------

@fta_app.command("refund-sxxk")
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


@fta_app.command("bcqt")
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
