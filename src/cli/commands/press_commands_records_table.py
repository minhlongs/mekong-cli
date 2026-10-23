# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Press suite record-table and correction-panel construction."""

from __future__ import annotations

from rich.panel import Panel
from rich.table import Table

_COLUMNS = ("Mục", "Mã Bản Ghi", "Tên Đối Tượng / Đơn Vị", "Chỉ Số / Nội Dung", "Trạng Thái")

_STYLES = ("cyan", "dim", "bold", "", "")

_WIDTHS = (12, 16, 28, 26, 20)


def _row(r: dict) -> tuple[str, ...] | None:
    cat = r.get("category", "")
    if cat == "credential":
        return ("THẺ/CHỨC DANH", r["credential_id"], r["holder_name"], f"{r['credential_type']} @ {r['press_agency']}", r["status"])
    if cat == "icp":
        return ("TRANG ICP", r["audit_id"], r["website_domain"], f"Tin tự làm: {r['self_produced_ratio_pct']:.1f}%", r["compliance_status"])
    if cat == "ott":
        return ("OTT VOD", r["license_id"], r["service_name"], f"{r['service_type']} - {r['provider_name']}", r["status"])
    if cat == "correction":
        return ("CẢI CHÍNH", r["correction_id"], r["press_agency"], f"{r['article_title'][:24]}...", r["status"])
    return None


def build_table(category: str, records: list[dict]) -> Table:
    """Build the press records table; the caller prints it."""
    table = Table(title=f"Danh Sách Hồ Sơ Quản Lý Báo Chí & Truyền Thông ({category.upper()})", show_header=True)
    for col, st, w in zip(_COLUMNS, _STYLES, _WIDTHS):
        table.add_column(col, style=st, width=w)
    for r in records:
        cells = _row(r)
        if cells is not None:
            table.add_row(*cells)
    return table


def build_correction_panel(res: dict, c_color: str) -> Panel:
    """Build the correction & apology panel; the caller prints it."""
    apology = "[green]CÓ[/]" if res["public_apology_included"] else "[red]THIẾU[/]"
    reply = "[green]ĐẢM BẢO[/]" if res["right_of_reply_granted"] else "[red]CHƯA[/]"
    return Panel(
        f"[bold red]GIÁM SÁT CẢI CHÍNH & XIN LỖI CÔNG KHAI (ĐIỀU 42 LUẬT BÁO CHÍ)[/]\n\n"
        f"  Mã vụ việc: [bold]{res['correction_id']}[/] | Cơ quan: [bold]{res['press_agency']}[/] ({res['medium_type']}) | Bài viết: {res['article_title']} ({res['publication_date']})\n"
        f"  Vi phạm: [bold red]{res['violation_nature']}[/] | Thời gian đăng: [bold]{res['published_hours_after_request']}h[/] (Hạn <= {res['statutory_deadline_hours']}h)\n"
        f"  Xin lỗi công khai: {apology} | Duy trì trang chủ: [bold]{res['retention_days']} ngày[/] | Quyền phản hồi: {reply}\n"
        f"  Đánh giá chấp hành: [bold {c_color}]{res['status']}[/bold {c_color}]",
        title="[bold red]Statutory Press Correction & Apology (Article 42)[/]", border_style="red",
    )
