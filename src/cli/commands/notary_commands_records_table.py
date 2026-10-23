# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Notary suite record-table construction - per category row layout."""

from __future__ import annotations

from rich.table import Table

_COLUMN_SPECS = {
    "blocked": (("Mã tài sản", "bold cyan"), ("Mô tả", "white"), ("Lý do ngăn chặn", "red"), ("Cơ quan yêu cầu", "yellow"), ("Thời điểm", "white")),
    "agreements": (("Mã HĐ", "bold cyan"), ("Tổ chức LS", "white"), ("Luật sư", "yellow"), ("Thân chủ", "magenta"), ("Thù lao", "green"), ("Trạng thái", "bold")),
    "authentications": (("Mã CT", "bold cyan"), ("Tên văn bản", "white"), ("Loại", "yellow"), ("Cơ quan", "magenta"), ("Số bản", "white"), ("Lệ phí", "green"), ("Trạng thái", "bold")),
    "contracts": (("Số sổ CC", "bold cyan"), ("Tên hợp đồng", "white"), ("Loại HĐ", "yellow"), ("Mã tài sản", "magenta"), ("Giá trị GD", "green"), ("Trạng thái", "bold")),
}

_BLOCKED_ALIASES = ("blocked", "blocked_assets", "ngan_chan")

_AGREEMENT_ALIASES = ("agreements", "law_firms", "luat_su")

_AUTHENTICATION_ALIASES = ("authentications", "copies", "chung_thuc")


def _status_cell(is_ok: bool, status: str) -> str:
    return f"[{'green' if is_ok else 'red'}]{status}[/]"


def _blocked_row(r: dict) -> tuple[str, ...]:
    return (r.get("asset_id", ""), r.get("asset_description", ""), r.get("block_reason", ""), r.get("blocking_authority", ""), r.get("created_at", "")[:19])


def _agreement_row(r: dict) -> tuple[str, ...]:
    status = _status_cell(bool(r.get("is_compliant")), r.get("status", ""))
    return (r.get("agreement_code", ""), r.get("law_firm_name", ""), r.get("attorney_name", ""), r.get("client_name", ""), f"{r.get('fee_vnd', 0):,.0f} VND", status)


def _authentication_row(r: dict) -> tuple[str, ...]:
    status = _status_cell(r.get("status") == "AUTHENTICATED_COMPLIANT", r.get("status", ""))
    return (r.get("auth_code", ""), r.get("document_title", ""), r.get("auth_type", ""), r.get("authenticating_body", ""), str(r.get("number_of_copies", 0)), f"{r.get('statutory_fee_vnd', 0):,.0f} VND", status)


def _contract_row(r: dict) -> tuple[str, ...]:
    status = _status_cell(bool(r.get("is_approved")), r.get("status", ""))
    return (r.get("notary_book_number", ""), r.get("contract_title", ""), r.get("contract_type", ""), r.get("asset_id", ""), f"{r.get('transaction_value_vnd', 0):,.0f} VND", status)


def build_records_table(category: str, limit: int, records: list[dict]) -> Table:
    """Build the notary records table; the caller prints it."""
    if category in _BLOCKED_ALIASES:
        columns, row_fn = _COLUMN_SPECS["blocked"], _blocked_row
    elif category in _AGREEMENT_ALIASES:
        columns, row_fn = _COLUMN_SPECS["agreements"], _agreement_row
    elif category in _AUTHENTICATION_ALIASES:
        columns, row_fn = _COLUMN_SPECS["authentications"], _authentication_row
    else:
        columns, row_fn = _COLUMN_SPECS["contracts"], _contract_row
    table = Table(title=f"Danh mục hồ sơ công chứng & bổ trợ tư pháp [{category.upper()}] (Tối đa {limit} bản ghi)")
    for header, style in columns:
        table.add_column(header, style=style)
    for r in records:
        table.add_row(*row_fn(r))
    return table
