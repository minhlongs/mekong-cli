# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Phases 171 & 172 CLI subcommands: FTA Origin/Tariff Savings & EPE/On-Spot Customs."""

from __future__ import annotations

import json
from typing import List, Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.fta_duty_engine import EPECustomsEngine, FTATariffOriginEngine

console = Console()


def calc_tariff_savings(
    customs_value: float = typer.Argument(..., help="Trị giá hải quan tính thuế (VNĐ)"),
    mfn_rate: float = typer.Option(..., "--mfn", "-m", help="Thuế suất MFN thông thường (%)"),
    fta_rate: float = typer.Option(..., "--fta", "-f", help="Thuế suất ưu đãi đặc biệt FTA (%)"),
    agreement: str = typer.Option("EVFTA", "--agreement", "-a", help="Tên hiệp định (EVFTA, CPTPP, RCEP, ATIGA...)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """So sánh và tính số tiền thuế nhập khẩu tiết kiệm được nhờ hiệp định thương mại tự do FTA."""
    result = FTATariffOriginEngine.calculate_tariff_savings(
        customs_value_vnd=customs_value, mfn_rate_pct=mfn_rate, fta_rate_pct=fta_rate, agreement=agreement,
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
        product_hs=product_hs, criterion=criterion, non_originating_materials_hs=non_orig_hs,
        rvc_actual_pct=rvc_actual, rvc_threshold_pct=rvc_thresh, non_originating_value_fob_pct=fob_ratio, agreement=agreement,
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


def determine_proof(
    agreement: str = typer.Option("EVFTA", "--agreement", "-a", help="Tên hiệp định (EVFTA, CPTPP, RCEP, ATIGA)"),
    value_eur: float = typer.Option(0.0, "--value-eur", "-v", help="Trị giá lô hàng quy đổi EUR"),
    approved_exporter: bool = typer.Option(False, "--approved", "-e", help="Có chứng nhận Approved Exporter / REX"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Xác định hình thức chứng từ chứng nhận xuất xứ (C/O hoặc Tự chứng nhận) cần nộp."""
    result = FTATariffOriginEngine.determine_proof_of_origin(
        agreement=agreement, consignment_value_eur=value_eur, is_approved_exporter=approved_exporter,
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


def check_epe_conditions(
    barrier: bool = typer.Option(..., "--barrier/--no-barrier", help="Có hàng rào cứng ngăn cách khu vực"),
    camera: bool = typer.Option(..., "--camera/--no-camera", help="Có camera 24/7 kết nối hải quan"),
    gate: bool = typer.Option(..., "--gate/--no-gate", help="Có cổng/cửa ra vào riêng biệt"),
    erp: bool = typer.Option(..., "--erp/--no-erp", help="Có phần mềm quản lý xuất nhập tồn"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra điều kiện kiểm tra, giám sát hải quan bắt buộc đối với DNCX (Điều 26 NĐ 35/2022)."""
    result = EPECustomsEngine.verify_epe_conditions(
        has_physical_barrier=barrier, has_camera_24_7=camera, has_separate_gate=gate, has_erp_inventory=erp,
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


def check_on_spot(
    export_date: str = typer.Argument(..., help="Ngày thông quan tờ khai xuất khẩu tại chỗ (YYYY-MM-DD)"),
    ref_date: Optional[str] = typer.Option(None, "--ref-date", "--import-date", "-r", help="Ngày đối chiếu kiểm tra (YYYY-MM-DD)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Kiểm tra thời hạn 15 ngày làm việc hoàn thành tờ khai nhập khẩu tại chỗ đối ứng (Điều 86 TT 38/2015)."""
    result = EPECustomsEngine.check_on_spot_deadline(export_declaration_date=export_date, reference_date=ref_date)
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


def calc_scrap_sale(
    value: float = typer.Argument(..., help="Giá trị thực tế phế liệu bán vào nội địa (VNĐ)"),
    hs_code: str = typer.Option(..., "--hs", "-h", help="Mã HS của phế liệu, phế phẩm"),
    duty_rate: float = typer.Option(..., "--duty", "-d", help="Thuế suất thuế nhập khẩu (%)"),
    vat_rate: float = typer.Option(10.0, "--vat", "-v", help="Thuế suất thuế GTGT nội địa (%)"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất kết quả JSON"),
) -> None:
    """Tính thuế nhập khẩu và GTGT khi DNCX bán phế liệu, phế phẩm vào thị trường nội địa (Điều 75 TT 38)."""
    result = EPECustomsEngine.calculate_scrap_domestic_sale_tax(
        scrap_value_vnd=value, scrap_hs_code=hs_code, import_duty_rate_pct=duty_rate, vat_rate_pct=vat_rate,
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
