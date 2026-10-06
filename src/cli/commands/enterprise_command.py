# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Enterprise, Corporate Law, IP, Labor & VietQR Reconciliation Suite Command Surface (Phases 154 - 158).

Statutory & Technical Framework:
- Law on Enterprises 2020 (Luật Doanh nghiệp số 59/2020/QH14)
- Law on Investment 2020 (Luật Đầu tư số 61/2020/QH14)
- Law on Intellectual Property 2005 / 2022 (Luật SHTT số 50/2005/QH11 & 07/2022/QH15)
- Labor Code 2019 (Bộ luật Lao động số 45/2019/QH14) & Decree 74/2024/NĐ-CP (Minimum Wage)
- Commercial Law 2005 (Luật Thương mại số 36/2005/QH11 - Điều 301 Phạt vi phạm)
- Napas 247 VietQR Standard (EMVCo Merchant-Presented QR Code Specification)
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Optional
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.enterprise_suite_engine import (
    EnterpriseAuditEngine,
    EnterpriseFDIEngine,
    IntellectualPropertyEngine,
    InvestmentSector,
    LaborHRMEngine,
    Shareholder,
    VietQRReconEngine,
)

enterprise_app = typer.Typer(
    name="enterprise",
    help="Vietnamese Enterprise Operations, FDI, IP, Labor, VietQR & Commercial Law Suite.",
    no_args_is_help=False,
)
app = enterprise_app
console = Console()


def _render_dashboard() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG ĐIỀU HÀNH DOANH NGHIỆP & PHÁP CHẾ[/bold cyan]\n"
            "[bold green]MEKONG ENTERPRISE SUITE: FDI, SỞ HỮU TRÍ TUỆ, LAO ĐỘNG BHXH, VIETQR & HỢP ĐỒNG[/bold green]\n"
            "[dim]Luật DN 2020 | Luật Đầu tư 2020 | Luật SHTT 2022 | BLLĐ 2019 | Luật Thương mại 2005 | Napas 247[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    table = Table(title="Danh Mục 5 Trụ Cột Điều Hành Doanh Nghiệp (Enterprise Pillars)", box=box.ROUNDED)
    table.add_column("Trụ Cột (Pillar)", style="cyan")
    table.add_column("Căn Cứ Pháp Lý & Kỹ Thuật", style="yellow")
    table.add_column("Chức Năng Chính", style="green")

    table.add_row(
        "1. Doanh nghiệp & FDI",
        "Luật DN 2020 & Luật Đầu tư 2020",
        "Kiểm tra góp vốn 90 ngày, cơ cấu vốn, tỷ lệ sở hữu nước ngoài FDI.",
    )
    table.add_row(
        "2. Sở hữu Trí tuệ",
        "Luật SHTT 2005/2022 & NĐ 65/2023",
        "Tra cứu 45 nhóm Nice, tính phân biệt nhãn hiệu, bảo hộ bản quyền.",
    )
    table.add_row(
        "3. Lao động & Tiền lương",
        "BLLĐ 2019 & NĐ 74/2024/NĐ-CP",
        "Tính Gross/Net, trích nộp BHXH bắt buộc 34%, thuế TNCN 7 bậc.",
    )
    table.add_row(
        "4. Đối soát VietQR",
        "Napas 247 & Chuẩn EMVCo QR",
        "Sinh payload VietQR động, đối soát webhook HMAC-SHA256, gạch nợ 112/131.",
    )
    table.add_row(
        "5. Hợp đồng & Audit Hub",
        "Luật Thương mại 2005 (Điều 301)",
        "Kiểm tra mức trần phạt vi phạm 8%, chấm điểm sức khỏe DN toàn diện.",
    )

    console.print(table)
    console.print("\n[dim]Gõ 'mekong enterprise --help' để xem danh sách chi tiết các lệnh con.[/dim]")


@enterprise_app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Callback chính khi không có subcommand."""
    if ctx.invoked_subcommand is None:
        _render_dashboard()


@enterprise_app.command(name="corp")
def check_corp(
    committed: float = typer.Option(1_000_000_000.0, "--committed", "-c", help="Vốn điều lệ cam kết (VNĐ)"),
    contributed: float = typer.Option(1_000_000_000.0, "--contributed", "-p", help="Vốn thực tế đã góp (VNĐ)"),
    inc_date: str = typer.Option("2026-01-01", "--inc-date", "-d", help="Ngày cấp ĐKKD (YYYY-MM-DD)"),
    sector: str = typer.Option("it_software", "--sector", "-s", help="Ngành nghề đầu tư (it_software, fintech, etc.)"),
    foreign_pct: float = typer.Option(0.0, "--foreign-pct", "-f", help="Tỷ lệ vốn nước ngoài (%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Thẩm tra nghĩa vụ góp vốn và điều kiện đầu tư FDI."""
    status = EnterpriseFDIEngine.check_charter_capital(committed, contributed, inc_date)
    sec_enum = InvestmentSector(sector) if sector in [e.value for e in InvestmentSector] else InvestmentSector.IT_SOFTWARE

    shs = [
        Shareholder(name="Cổ đông VN", is_foreign=False, nationality="VN", capital_committed=committed * (1.0 - foreign_pct / 100.0), capital_contributed=contributed * (1.0 - foreign_pct / 100.0)),
    ]
    if foreign_pct > 0:
        shs.append(Shareholder(name="Cổ đông Ngoại", is_foreign=True, nationality="FDI", capital_committed=committed * (foreign_pct / 100.0), capital_contributed=contributed * (foreign_pct / 100.0)))

    fdi_status = EnterpriseFDIEngine.assess_fdi_ownership(shs, sec_enum)

    res = {
        "charter_capital": asdict(status),
        "fdi_ownership": asdict(fdi_status)
    }

    if as_json:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return

    table = Table(title="Đánh Giá Pháp Lý Doanh Nghiệp & Đầu Tư FDI", box=box.ROUNDED)
    table.add_column("Chỉ Số", style="cyan")
    table.add_column("Giá Trị", style="green")
    table.add_column("Căn Cứ / Ghi Chú", style="yellow")

    table.add_row("Vốn điều lệ cam kết", f"{status.total_committed:,.0f} VNĐ", "Giấy phép ĐKKD")
    table.add_row("Vốn thực góp", f"{status.total_contributed:,.0f} VNĐ", f"Tỷ lệ: {status.contribution_ratio_pct}%")
    table.add_row("Tiến độ 90 ngày", "ĐÃ HOÀN TẤT" if status.is_fully_paid else ("QUÁ HẠN" if status.is_overdue_90_days else "Đang trong hạn"), status.penalty_risk_vn)
    table.add_row("Sở hữu nước ngoài (FDI)", f"{fdi_status.total_foreign_ownership_pct}%", f"Trần ngành {fdi_status.sector.value}: {fdi_status.cap_allowed_pct}%")
    table.add_row("Tuân thủ Luật Đầu tư", "HỢP PHÁP" if fdi_status.is_compliant else "VƯỢT TRẦN", fdi_status.legal_basis)

    console.print(table)


@enterprise_app.command(name="ip")
def check_ip(
    mark: str = typer.Option(..., "--mark", "-m", help="Tên nhãn hiệu cần thẩm định"),
    nice_class: int = typer.Option(9, "--class", "-c", help="Nhóm Nice quốc tế (1 - 45)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Đánh giá tính phân biệt và khả năng bảo hộ nhãn hiệu theo Luật SHTT."""
    result = IntellectualPropertyEngine.evaluate_trademark(mark, nice_class)
    if as_json:
        typer.echo(json.dumps(asdict(result), ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Thẩm Định Nhãn Hiệu: '{mark}' (Nhóm Nice {nice_class})", box=box.ROUNDED)
    table.add_column("Tiêu Chí", style="cyan")
    table.add_column("Kết Quả", style="green")

    table.add_row("Điểm tính phân biệt", f"{result.distinctiveness_score} / 100")
    table.add_row("Khả năng cấp bằng", "ĐỦ ĐIỀU KIỆN" if result.is_registrable else "RỦI RO BỊ TỪ CHỐI")
    table.add_row("Khuyến nghị Cục SHTT", result.advice_vn)
    if result.risk_factors:
        table.add_row("Yếu tố rủi ro", "; ".join(result.risk_factors))

    console.print(table)


@enterprise_app.command(name="labor")
def calculate_labor(
    gross: float = typer.Option(..., "--gross", "-g", help="Mức lương thỏa thuận Gross (VNĐ)"),
    dependents: int = typer.Option(0, "--dependents", "-d", help="Số người phụ thuộc giảm trừ gia cảnh"),
    region: int = typer.Option(1, "--region", "-r", help="Vùng lương tối thiểu (1, 2, 3, 4)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Tính bảng lương Net, trích nộp BHXH bắt buộc và Thuế TNCN."""
    p = LaborHRMEngine.calculate_payroll(gross, dependents, region)
    if as_json:
        typer.echo(json.dumps(asdict(p), ensure_ascii=False, indent=2))
        return

    table = Table(title=f"Bảng Phân Bổ Lương & Bảo Hiểm Bắt Buộc (Vùng {region})", box=box.ROUNDED)
    table.add_column("Khoản Mục", style="cyan")
    table.add_column("NLĐ Chịu (Trích Lương)", style="yellow")
    table.add_column("Doanh Nghiệp Đóng (Chi Phí)", style="red")

    table.add_row("Lương Gross thỏa thuận", f"{p.gross_salary:,.0f} VNĐ", "-")
    table.add_row("Lương căn cứ đóng BHXH", f"{p.base_insurance_salary:,.0f} VNĐ", f"{p.base_insurance_salary:,.0f} VNĐ")
    table.add_row("BHXH (NLĐ: 8% / DN: 17.5%)", f"{p.ee_bhxh:,.0f} VNĐ", f"{p.er_bhxh:,.0f} VNĐ")
    table.add_row("BHYT (NLĐ: 1.5% / DN: 3%)", f"{p.ee_bhyt:,.0f} VNĐ", f"{p.er_bhyt:,.0f} VNĐ")
    table.add_row("BHTN (NLĐ: 1% / DN: 1%)", f"{p.ee_bhtn:,.0f} VNĐ", f"{p.er_bhtn:,.0f} VNĐ")
    table.add_row("Kinh phí công đoàn (DN: 2%)", "-", f"{p.er_union:,.0f} VNĐ")
    table.add_row("Tổng trích bảo hiểm", f"{p.ee_total_insurance:,.0f} VNĐ (10.5%)", f"{p.er_total_insurance:,.0f} VNĐ (23.5%)")
    table.add_row("Thuế TNCN lũy tiến 7 bậc", f"{p.pit_amount:,.0f} VNĐ", "-")
    table.add_row("LƯƠNG THỰC LĨNH (NET)", f"[bold green]{p.net_salary:,.0f} VNĐ[/bold green]", "-")
    table.add_row("TỔNG CHI PHÍ DOANH NGHIỆP", "-", f"[bold magenta]{p.total_company_burden:,.0f} VNĐ[/bold magenta]")

    console.print(table)


@enterprise_app.command(name="recon")
def vietqr_recon(
    bin_code: str = typer.Option("970422", "--bin", "-b", help="Mã BIN ngân hàng thụ hưởng (VD: 970422 MBBank)"),
    account: str = typer.Option("0123456789", "--account", "-a", help="Số tài khoản thụ hưởng"),
    amount: Optional[int] = typer.Option(500_000, "--amount", help="Số tiền giao dịch (VNĐ)"),
    memo: Optional[str] = typer.Option("MEKONG-INV-001", "--memo", help="Nội dung thanh toán"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Sinh chuỗi payload chuẩn VietQR Napas 247 (EMVCo QR)."""
    payload = VietQRReconEngine.generate_vietqr_payload(bin_code, account, amount, memo)
    res = {
        "bank_bin": bin_code,
        "account": account,
        "amount": amount,
        "memo": memo,
        "emvco_payload": payload
    }
    if as_json:
        typer.echo(json.dumps(res, ensure_ascii=False, indent=2))
        return

    table = Table(title="Payload Mã Chuẩn Napas 247 VietQR (EMVCo)", box=box.ROUNDED)
    table.add_column("Thuộc Tính", style="cyan")
    table.add_column("Giá Trị", style="green")

    table.add_row("Ngân hàng (BIN)", bin_code)
    table.add_row("Số tài khoản", account)
    table.add_row("Số tiền", f"{amount:,.0f} VNĐ" if amount else "Tự do")
    table.add_row("Nội dung (Memo)", memo or "-")
    table.add_row("EMVCo Payload", f"[bold yellow]{payload}[/bold yellow]")

    console.print(table)


@enterprise_app.command(name="contract")
def review_contract(
    value: float = typer.Option(..., "--value", "-v", help="Giá trị hợp đồng / phần nghĩa vụ vi phạm (VNĐ)"),
    penalty_pct: float = typer.Option(8.0, "--penalty-pct", "-p", help="Tỷ lệ phạt vi phạm thỏa thuận (%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Thẩm định tính hợp pháp của điều khoản phạt vi phạm theo Điều 301 Luật Thương mại."""
    check = EnterpriseAuditEngine.review_contract_penalty(value, penalty_pct)
    if as_json:
        typer.echo(json.dumps(asdict(check), ensure_ascii=False, indent=2))
        return

    table = Table(title="Thẩm Định Phạt Vi Phạm Hợp Đồng Thương Mại", box=box.ROUNDED)
    table.add_column("Tiêu Chí", style="cyan")
    table.add_column("Giá Trị", style="green")

    table.add_row("Giá trị vi phạm", f"{check.contract_value:,.0f} VNĐ")
    table.add_row("Mức phạt thỏa thuận", f"{check.agreed_penalty_pct}%")
    table.add_row("Trần luật định (Điều 301 LTM)", f"{check.max_legal_penalty_pct}% ({check.max_legal_penalty_amount:,.0f} VNĐ)")
    table.add_row("Tính hợp pháp", "HỢP PHÁP" if check.is_commercial_law_compliant else "VI PHẠM (VÔ HIỆU)")
    table.add_row("Cảnh báo pháp lý", check.warning_vn)

    console.print(table)


@enterprise_app.command(name="audit")
def full_audit(
    committed: float = typer.Option(2_000_000_000.0, "--committed", help="Vốn cam kết"),
    contributed: float = typer.Option(2_000_000_000.0, "--contributed", help="Vốn thực góp"),
    inc_date: str = typer.Option("2026-01-01", "--inc-date", help="Ngày ĐKKD"),
    mark: str = typer.Option("MekongAI", "--mark", help="Tên nhãn hiệu chính"),
    nice_class: int = typer.Option(9, "--class", help="Nhóm Nice nhãn hiệu"),
    employees: int = typer.Option(10, "--employees", help="Số lượng nhân viên ký HĐLĐ"),
    unsettled_pct: float = typer.Option(5.0, "--unsettled-pct", help="Tỷ lệ công nợ chưa đối soát (%)"),
    as_json: bool = typer.Option(False, "--json", help="Xuất kết quả định dạng JSON"),
) -> None:
    """Đánh giá toàn diện 360 độ sức khỏe pháp lý và tài chính doanh nghiệp."""
    cap_status = EnterpriseFDIEngine.check_charter_capital(committed, contributed, inc_date)
    tm_status = IntellectualPropertyEngine.evaluate_trademark(mark, nice_class)
    audit = EnterpriseAuditEngine.audit_enterprise_health(
        capital_status=cap_status,
        fdi_status=None,
        trademark_result=tm_status,
        payroll_count=employees,
        unsettled_invoices_pct=unsettled_pct
    )

    if as_json:
        typer.echo(json.dumps(asdict(audit), ensure_ascii=False, indent=2))
        return

    table = Table(title="Báo Cáo Sức Khỏe Doanh Nghiệp Toàn Diện (Enterprise Health Score)", box=box.ROUNDED)
    table.add_column("Hạng Mục Trụ Cột", style="cyan")
    table.add_column("Điểm Số", style="green")

    for k, v in audit.pillar_scores.items():
        table.add_row(k, f"{v} / 100")

    table.add_row("[bold]ĐIỂM TỔNG THỂ[/bold]", f"[bold magenta]{audit.overall_score} / 100[/bold magenta]")
    table.add_row("[bold]MỨC ĐỘ RỦI RO[/bold]", f"[bold {'green' if audit.risk_level == 'LOW' else 'red'}]{audit.risk_level}[/bold]")

    console.print(table)
    if audit.recommendations_vn:
        console.print("\n[bold yellow]Khuyến nghị khắc phục:[/bold yellow]")
        for r in audit.recommendations_vn:
            console.print(f"- {r}")
