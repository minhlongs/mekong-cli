# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Price command record-table construction — one row layout per record type."""

from __future__ import annotations

from typing import Callable

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_table as _build

_DECLARATION_COLUMNS = (("Mã kê khai", "bold cyan"), ("Doanh nghiệp", "white"), ("Mặt hàng", "white"), ("Giá mới", "yellow"), ("Biến động", "cyan"), ("Trạng thái", "bold"))
_POSTING_COLUMNS = (("Mã KT", "bold cyan"), ("Cửa hàng", "white"), ("Sản phẩm", "white"), ("Giá niêm yết", "green"), ("Giá bán TT", "yellow"), ("Trạng thái", "bold"))
_VALUATION_COLUMNS = (("Số chứng thư", "bold cyan"), ("Doanh nghiệp TĐG", "white"), ("Khách hàng", "yellow"), ("Phương pháp", "cyan"), ("Giá trị thẩm định", "bold green"), ("Trạng thái", "bold"))
_GOUGING_COLUMNS = (("Mã TT", "bold cyan"), ("Cơ sở vi phạm", "white"), ("Sản phẩm", "white"), ("Thu lợi bất chính", "bold red"), ("Tiền phạt", "red"), ("Trạng thái", "bold"))


def _declaration_cells(r: dict) -> tuple[str, ...]:
    c = "green" if r.get("status") == "DECLARATION_ACCEPTED" else "red"
    return (r.get("declaration_code", ""), r.get("enterprise_name", ""), r.get("product_name", ""), f"{r.get('declared_price_vnd', 0):,.0f} VND", f"{r.get('change_pct', 0)}%", f"[{c}]{r.get('status', '')}[/]")


def _posting_cells(r: dict) -> tuple[str, ...]:
    c = "green" if r.get("status") == "COMPLIANT_POSTING" else "red"
    return (r.get("audit_code", ""), r.get("store_name", ""), r.get("product_name", ""), f"{r.get('listed_price_vnd', 0):,.0f} VND", f"{r.get('actual_selling_price_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")


def _valuation_cells(r: dict) -> tuple[str, ...]:
    c = "green" if r.get("is_valid") else "red"
    return (r.get("certificate_code", ""), r.get("appraisal_firm", ""), r.get("client_name", ""), r.get("valuation_method", ""), f"{r.get('appraised_value_vnd', 0):,.0f} VND", f"[{c}]{r.get('status', '')}[/]")


def _gouging_cells(r: dict) -> tuple[str, ...]:
    return (r.get("audit_code", ""), r.get("business_name", ""), r.get("product_name", ""), f"{r.get('illicit_profit_vnd', 0):,.0f} VND", f"{r.get('penalty_fine_vnd', 0):,.0f} VND", r.get("status", ""))


_BRANCHES: tuple[tuple[tuple[str, ...], tuple[tuple[str, str], ...], Callable[[dict], tuple[str, ...]]], ...] = (
    (("postings", "listing", "niem_yet"), _POSTING_COLUMNS, _posting_cells),
    (("valuations", "appraisals", "tham_dinh"), _VALUATION_COLUMNS, _valuation_cells),
    (("gouging", "violations", "tang_gia"), _GOUGING_COLUMNS, _gouging_cells),
)


def build_table(category: str, limit: int, records: list[dict]) -> Table:
    """Build the price records table; the caller prints it."""
    title = f"Danh mục quản lý giá & thẩm định giá [{category.upper()}] (Tối đa {limit} bản ghi)"
    for aliases, columns, cells in _BRANCHES:
        if category in aliases:
            return _build(title, columns, cells, records)
    return _build(title, _DECLARATION_COLUMNS, _declaration_cells, records)
