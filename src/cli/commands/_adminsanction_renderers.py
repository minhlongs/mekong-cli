# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rich rendering helpers for Administrative Sanctions CLI commands."""

from __future__ import annotations

from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.adminsanction_engine import (
    MAX_FINES_INDIVIDUAL_VND,
    TWO_YEAR_LIMITATION_SECTORS,
)


def render_adminsanction_dashboard(console: Console) -> None:
    """Render the statutory administrative sanctions dashboard."""
    console.print(
        Panel.fit(
            "[bold cyan]CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM — HỆ THỐNG XỬ LÝ VI PHẠM HÀNH CHÍNH & KHẮC PHỤC HẬU QUẢ[/bold cyan]\n"
            "[bold green]QUẢN LÝ KHUNG PHẠT TIỀN, THỜI HIỆU, THẨM QUYỀN & TỊCH THU SỐ LỢI BẤT HỢP PHÁP[/bold green]\n"
            "[dim]Luật Xử lý vi phạm hành chính số 15/2012/QH13 (sđ 67/2020/QH14) & Nghị định 118/2021/NĐ-CP[/dim]",
            box=box.DOUBLE,
            border_style="cyan",
        )
    )

    summary_table = Table(title="Nguyên Tắc Luật Định & Thời Hiệu Xử Phạt VPHC", box=box.ROUNDED)
    summary_table.add_column("Chỉ Tiêu Pháp Lý", style="cyan bold")
    summary_table.add_column("Quy Định Luật Định", style="yellow")
    summary_table.add_column("Căn Cứ Pháp Lý", style="green")

    summary_table.add_row(
        "Hệ số phạt Tổ chức / Doanh nghiệp",
        "Bằng 02 lần (2.0x) mức phạt cá nhân",
        "Điều 24.2 Luật XLVPHC",
    )
    summary_table.add_row(
        "Thuật toán xác định mức phạt tiền",
        "Mức trung bình = (Min + Max)/2, điều chỉnh theo tăng nặng/giảm nhẹ",
        "Điều 23 Luật XLVPHC & Điều 9 NĐ 118/2021/NĐ-CP",
    )
    summary_table.add_row(
        "Thời hiệu xử phạt thông thường",
        "01 năm tính từ khi chấm dứt hoặc phát hiện vi phạm",
        "Điều 6.1.a Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hiệu xử phạt đặc biệt (Thuế, Môi trường, Đất đai, SHTT)",
        "02 năm tính từ khi chấm dứt hoặc phát hiện vi phạm",
        "Điều 6.1.a Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hạn gửi văn bản giải trình",
        "05 ngày làm việc kể từ ngày lập biên bản VPHC",
        "Điều 61.2 Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hạn ra quyết định xử phạt",
        "07 ngày làm việc (vụ phức tạp giải trình: 30 ngày, tối đa 60 ngày)",
        "Điều 66.1 Luật XLVPHC",
    )
    summary_table.add_row(
        "Thời hiệu thi hành quyết định xử phạt",
        "01 năm kể từ ngày ra quyết định xử phạt",
        "Điều 73.1 Luật XLVPHC",
    )
    summary_table.add_row(
        "Tiền phạt chậm nộp",
        "0.05% / ngày trên số tiền phạt chưa nộp",
        "Điều 78.1 Luật XLVPHC",
    )
    console.print(summary_table)

    caps_table = Table(title="Mức Phạt Tiền Tối Đa Theo Lĩnh Vực (Cá nhân / Tổ chức = 2x)", box=box.SIMPLE_HEAD)
    caps_table.add_column("Lĩnh Vực Hoạt Động", style="cyan")
    caps_table.add_column("Mức Phạt Tối Đa Cá Nhân", style="magenta", justify="right")
    caps_table.add_column("Mức Phạt Tối Đa Tổ Chức", style="red bold", justify="right")
    caps_table.add_column("Thời Hiệu", style="yellow")

    for sector, cap_ind in sorted(MAX_FINES_INDIVIDUAL_VND.items(), key=lambda x: x[1], reverse=True)[:10]:
        cap_org = cap_ind * 2.0
        statute = "02 năm" if sector in TWO_YEAR_LIMITATION_SECTORS else "01 năm"
        caps_table.add_row(sector, f"{cap_ind:,.0f} VNĐ", f"{cap_org:,.0f} VNĐ", statute)

    console.print(caps_table)


def render_case_result(console: Console, res: dict[str, Any]) -> None:
    """Render newly created VPHC case details."""
    console.print(Panel(f"[bold green]Đã lập hồ sơ vụ việc VPHC thành công: {res['case_id']}[/bold green]", border_style="green"))
    table = Table(box=box.ROUNDED)
    table.add_column("Thuộc Tính", style="cyan bold")
    table.add_column("Chi Tiết Hồ Sơ", style="white")

    table.add_row("Mã Hồ Sơ", res["case_id"])
    table.add_row("Đối Tượng Vi Phạm", f"{res['violator_name']} ({res['entity_type']})")
    table.add_row("Lĩnh Vực", res["sector"])
    table.add_row("Mô Tả Vi Phạm", res["violation_description"])
    table.add_row("Thời Điểm Vi Phạm", res["violation_date"])
    table.add_row("Thời Điểm Phát Hiện", res["discovery_date"])
    table.add_row("Trạng Thái Hành Vi", res["violation_status"])
    table.add_row(
        "Thời Hiệu Xử Phạt",
        f"{res['statute_of_limitations']['statute_limit_years']} năm (Hết hạn: {res['statute_of_limitations']['expiry_date']})",
    )
    table.add_row("Số Ngày Còn Lại", str(res["statute_of_limitations"]["days_remaining"]))
    table.add_row(
        "Đánh Giá Thời Hiệu",
        "[bold red]HẾT THỜI HIỆU[/bold red]" if res["statute_of_limitations"]["is_time_barred"] else "[bold green]CÒN THỜI HIỆU HỢP LỆ[/bold green]",
    )
    table.add_row("Khuyến Nghị Pháp Lý", res["statute_of_limitations"]["action_recommendation"])

    console.print(table)


def render_fine_result(console: Console, res: dict[str, Any]) -> None:
    """Render statutory fine calculation table."""
    console.print(Panel("[bold cyan]KẾT QUẢ TÍNH TOÁN TIỀN PHẠT LUẬT ĐỊNH (NĐ 118/2021/NĐ-CP)[/bold cyan]", border_style="cyan"))
    table = Table(box=box.ROUNDED)
    table.add_column("Hạng Mục Tính Toán", style="cyan bold")
    table.add_column("Giá Trị Áp Dụng", style="yellow")

    table.add_row("Đối Tượng Áp Dụng", f"{res['entity_type']} (Hệ số: {res['multiplier']}x)")
    table.add_row(
        "Khung Luật Định (Cá nhân)",
        f"{res['statutory_bracket_individual']['min']:,.0f} VNĐ - {res['statutory_bracket_individual']['max']:,.0f} VNĐ",
    )
    table.add_row(
        "Khung Áp Dụng Thực Tế",
        f"{res['applied_bracket']['min']:,.0f} VNĐ - {res['applied_bracket']['max']:,.0f} VNĐ (Mức TB: {res['applied_bracket']['average']:,.0f} VNĐ)",
    )
    table.add_row("Tình Tiết Giảm Nhẹ (Điều 9)", f"{len(res['mitigating_factors'])}: {', '.join(res['mitigating_factors']) if res['mitigating_factors'] else 'Không'}")
    table.add_row("Tình Tiết Tăng Nặng (Điều 10)", f"{len(res['aggravating_factors'])}: {', '.join(res['aggravating_factors']) if res['aggravating_factors'] else 'Không'}")
    table.add_row(
        "[bold green]MỨC PHẠT TIỀN CHÍNH THỨC[/bold green]",
        f"[bold green]{res['final_payable_fine_vnd']:,.0f} VNĐ[/bold green]",
    )
    table.add_row("Giải Thích Thuật Toán", res["formula_explanation"])

    console.print(table)
