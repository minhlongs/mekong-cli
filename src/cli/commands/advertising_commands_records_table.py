# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Advertising record-table layouts — column specs per record category.

Category aliases (xnndqc, cross_border, ooh) map onto their canonical layout.
"""

from __future__ import annotations

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_key_value_table as _kv, build_table as _build

RECORDS_TITLE = "Danh mục hồ sơ quảng cáo [{category}] (Tối đa {limit} bản ghi)"

_COLUMNS = {
    "approvals": (("Mã XNNDQC", "bold cyan"), ("Sản phẩm", "white"), ("Ngành hàng", "yellow"), ("Đơn vị", "white"), ("Hiệu lực đến", "green"), ("Trạng thái", "bold green")),
    "takedowns": (("Mã vụ việc", "bold cyan"), ("Nền tảng", "yellow"), ("Mã quảng cáo", "white"), ("Hành vi", "red"), ("Thời gian trôi qua", "white"), ("Trạng thái", "bold")),
    "billboards": (("Mã giấy phép", "bold cyan"), ("Vị trí", "white"), ("Diện tích", "white"), ("Chiều cao", "white"), ("Tĩnh không", "white"), ("Trạng thái", "bold")),
}
_ALIASES = {"xnndqc": "approvals", "cross_border": "takedowns", "ooh": "billboards"}
_DEFAULT = "checks"


def _cells(category: str, r: dict) -> tuple[str, ...]:
    if category == "takedowns":
        colour = "green" if "ON_TIME" in r.get("status", "") else ("yellow" if "PENDING" in r.get("status", "") else "red")
        return (r.get("takedown_id", ""), r.get("platform", ""), r.get("ad_id", ""), r.get("violation_type", ""), f"{r.get('hours_elapsed', 0)}h", f"[{colour}]{r.get('status', '')}[/]")
    if category == "billboards":
        colour = "green" if r.get("status") == "APPROVED" else "red"
        return (r.get("permit_id", ""), r.get("location_type", ""), f"{r.get('area_sqm', 0)} m²", f"{r.get('height_m', 0)} m", f"{r.get('clearance_m', 0)} m", f"[{colour}]{r.get('status', '')}[/]")
    if category == "approvals":
        return (r.get("xnndqc_code", ""), r.get("product_name", ""), r.get("product_category", ""), r.get("applicant_name", ""), r.get("valid_until", ""), r.get("status", ""))
    colour = "green" if r.get("status") == "COMPLIANT" else "red"
    return (r.get("check_id", ""), r.get("content_preview", ""), r.get("product_type", ""), f"[{colour}]{r.get('status', '')}[/]", f"{r.get('estimated_fine_min_vnd', 0):,} - {r.get('estimated_fine_max_vnd', 0):,}")


def _columns(category: str):
    if category == _DEFAULT:
        return (("Mã thẩm định", "bold cyan"), ("Nội dung tóm tắt", "white"), ("Loại sản phẩm", "yellow"), ("Trạng thái", "bold"), ("Tiền phạt ước tính (VND)", "red"))
    return _COLUMNS[category]


def build_table(category: str, records: list[dict], limit: int) -> Table:
    """Build the records table for a category; the caller prints it."""
    key = _ALIASES.get(category, category)
    title = RECORDS_TITLE.format(category=category.upper(), limit=limit)
    if key not in _COLUMNS and key != _DEFAULT:
        key = _DEFAULT
    return _build(title, _columns(key), lambda r: _cells(key, r), records)


def build_key_value_table(title: str, rows, border_style: str) -> Table:
    """Build a two-column Chỉ số / Giá trị table."""
    return _kv(title, rows, border_style)
