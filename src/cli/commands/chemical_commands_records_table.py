# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Chemical command record-table construction — per record-type row layout."""

from __future__ import annotations

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_table as _build

_COLUMNS = (("Mã định danh", "cyan"), ("Phân loại", "white"), ("Đối tượng / Tên hóa chất", "yellow"), ("Kết quả / Trạng thái", "green"), ("Thời gian khởi tạo", "magenta"))


def _row(r: dict) -> tuple[str, ...]:
    ts = r.get("created_at", "")[:19]
    rtype = r.get("type", "unknown")
    if rtype == "classification":
        return (r.get("classification_id", ""), "Phân loại GHS", r.get("chemical_name", ""), r.get("category", ""), ts)
    if rtype == "storage_audit":
        return (r.get("audit_id", ""), "An toàn kho bãi", f"{r.get('facility_name', '')} ({r.get('chemical_name', '')})", "ĐẠT CHUẨN" if r.get("is_compliant") else "VI PHẠM", ts)
    if rtype == "import_declaration":
        return (r.get("declaration_id", ""), "Khai báo NSW", f"{r.get('importer_name', '')} - {r.get('chemical_name', '')}", r.get("status", ""), ts)
    if rtype == "transport_audit":
        return (r.get("transport_id", ""), "Vận chuyển ADR", f"{r.get('carrier_name', '')} ({r.get('un_number', '')})", "ĐỦ ĐIỀU KIỆN" if r.get("is_approved") else "CẤM LƯU HÀNH", ts)
    return ("", rtype, r.get("chemical_name", ""), r.get("status", ""), ts)


def build_table(category: str, records: list[dict]) -> Table:
    """Build the chemical records table; the caller prints it."""
    return _build(f"Danh mục hồ sơ hóa chất ({category.upper()}) - {len(records)} bản ghi", _COLUMNS, _row, records)
