# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Cyber command record-table construction — per record-type row layout."""

from __future__ import annotations

from rich.table import Table

_COLUMNS = (("Mã định danh", "cyan"), ("Phân loại", "white"), ("Đối tượng / Hệ thống", "yellow"), ("Kết quả / Đánh giá", "green"), ("Thời gian khởi tạo", "magenta"))


def _row(r: dict) -> tuple[str, ...]:
    ts = r.get("created_at", "")[:19]
    rtype = r.get("type", "unknown")
    if rtype == "localization":
        return (r.get("audit_id", ""), "Lưu trữ dữ liệu VN", r.get("service_name", ""), "ĐẠT CHUẨN" if r.get("is_compliant") else "VI PHẠM", ts)
    if rtype == "security_level":
        return (r.get("assessment_id", ""), "Cấp độ hệ thống", f"{r.get('system_name', '')} ({r.get('organization', '')})", f"CẤP ĐỘ {r.get('recommended_level', '')}", ts)
    if rtype == "incident":
        return (r.get("report_id", ""), "Sự cố VNCERT", f"{r.get('incident_title', '')} ({r.get('attack_vector', '')})", r.get("severity_level", ""), ts)
    if rtype == "service_license":
        return (r.get("license_id", ""), "Giấy phép ATTTM", r.get("firm_name", ""), "ĐỦ ĐIỀU KIỆN" if r.get("is_eligible") else "TỪ CHỐI", ts)
    return ("", rtype, "", "", ts)


def build_table(category: str, records: list[dict]) -> Table:
    """Build the cyber records table; the caller prints it."""
    table = Table(title=f"Danh mục hồ sơ an ninh mạng ({category.upper()}) - {len(records)} bản ghi", border_style="cyan")
    for header, style in _COLUMNS:
        table.add_column(header, style=style)
    for r in records:
        table.add_row(*_row(r))
    return table
