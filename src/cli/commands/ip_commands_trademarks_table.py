# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""IP command trademark panel construction — application & conflict search."""

from __future__ import annotations

from typing import Callable

from rich.panel import Panel

_COLOR_MAP = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}


def build_application_panel(record: dict, format_vnd: Callable[[float], str]) -> Panel:
    """Build the trademark application panel; the caller prints it."""
    return Panel(
        f"[bold green]ĐÃ THIẾT LẬP HỒ SƠ ĐĂNG KÝ NHÃN HIỆU: {record['mark_id']}[/]\n\n"
        f"  Tên nhãn hiệu:       [bold cyan]{record['mark_name']}[/]\n"
        f"  Nhóm ngành Nice:     [bold yellow]Nhóm {record['nice_class']}[/] ({record['class_title']})\n"
        f"  Chủ đơn đăng ký:     [bold]{record['applicant_name']}[/]\n"
        f"  Danh mục bảo hộ:     {record['goods_services_spec']}\n"
        f"  Cơ quan thụ lý:      {record['statutory_authority']}\n"
        f"  Lệ phí nhà nước:     [bold green]{format_vnd(record['official_fee_vnd'])}[/] (theo TT 263/2016)\n"
        f"  Tiến trình dự kiến:  Thẩm định hình thức (1 tháng) -> Công bố (2 tháng) -> Thẩm định nội dung (9 tháng)",
        title="[bold blue]Trademark Application Ready[/]",
        border_style="green",
    )


def build_search_panel(result: dict) -> Panel:
    """Build the trademark conflict search panel; the caller prints it."""
    risk_color = _COLOR_MAP.get(result["overall_conflict_risk"], "white")

    match_lines: list[str] = []
    for m in result["top_similar_marks"]:
        match_lines.append(f"  - [bold]{m['existing_mark']}[/] (Nhóm {m['nice_class']}): Tương đồng {round(m['similarity_score'] * 100)}% [{m['conflict_risk']}]")
    match_block = "\n".join(match_lines) if match_lines else "  - Không phát hiện nhãn hiệu tương tự trong cơ sở dữ liệu."

    return Panel(
        f"[bold cyan]KẾT QUẢ TRA CỨU XUNG ĐỘT NHÃN HIỆU: '{result['query_mark']}' (Nhóm {result['target_nice_class']})[/]\n\n"
        f"  Mức độ rủi ro xung đột: [bold {risk_color}]{result['overall_conflict_risk']}[/bold {risk_color}] (Điểm cao nhất: {result['highest_similarity_score']})\n"
        f"  Đánh giá pháp lý:       {result['legal_assessment']}\n\n"
        f"  [bold]Các nhãn hiệu tương tự phát hiện:[/]\n{match_block}",
        title="[bold blue]Trademark Conflict & Similarity Search[/]",
        border_style=risk_color,
    )
