# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Hitech command record-table construction — one row layout per record type."""

from __future__ import annotations

from typing import Callable

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_table as _build

_ENTERPRISE_COLUMNS = (("Mã chứng nhận", "bold cyan"), ("Tên doanh nghiệp", "white"), ("Tỷ lệ CNC", "green"), ("Tỷ lệ R&D", "yellow"), ("Nhân sự R&D", "magenta"), ("Trạng thái", "bold"))
_CONTRACT_COLUMNS = (("Mã hợp đồng", "bold cyan"), ("Tên hợp đồng", "white"), ("Công nghệ", "yellow"), ("Hướng", "magenta"), ("Giá trị", "green"), ("Trạng thái", "bold"))
_PARK_COLUMNS = (("Mã dự án", "bold cyan"), ("Tên dự án", "white"), ("Khu CNC", "yellow"), ("Diện tích", "white"), ("Vốn/ha", "green"), ("Trạng thái", "bold"))
_TAX_COLUMNS = (("Mã tính toán", "bold cyan"), ("Doanh nghiệp", "white"), ("Năm", "yellow"), ("Thuế suất", "cyan"), ("Tiết kiệm thuế", "bold green"), ("Trạng thái", "bold"))


def _enterprise_cells(r: dict) -> tuple[str, ...]:
    c = "green" if r.get("is_qualified") else "red"
    return (r.get("certificate_code", ""), r.get("company_name", ""), f"{r.get('hitech_ratio_pct', 0)}%", f"{r.get('rd_ratio_pct', 0)}%", f"{r.get('rd_employee_ratio_pct', 0)}%", f"[{c}]{r.get('status', '')}[/]")


def _contract_cells(r: dict) -> tuple[str, ...]:
    c = "green" if r.get("status") == "REGISTERED_COMPLIANT" else ("red" if "PROHIBITED" in r.get("status", "") else "yellow")
    return (r.get("registration_code", ""), r.get("contract_title", ""), r.get("technology_name", ""), r.get("transfer_direction", ""), f"{r.get('contract_value_usd', 0):,.0f} USD", f"[{c}]{r.get('status', '')}[/]")


def _park_cells(r: dict) -> tuple[str, ...]:
    c = "green" if r.get("status") == "APPROVED_FOR_HITECH_PARK" else "red"
    return (r.get("project_code", ""), r.get("project_name", ""), r.get("park_name", ""), f"{r.get('land_area_ha', 0)} ha", f"{r.get('capital_per_ha_vnd', 0):,.0f} VND/ha", f"[{c}]{r.get('status', '')}[/]")


def _tax_cells(r: dict) -> tuple[str, ...]:
    return (r.get("evaluation_code", ""), r.get("company_name", ""), str(r.get("operating_year", 0)), f"{r.get('applied_tax_rate_pct', 0)}%", f"{r.get('tax_saved_vnd', 0):,.0f} VND", r.get("status", ""))


_BRANCHES: tuple[tuple[tuple[str, ...], tuple[tuple[str, str], ...], Callable[[dict], tuple[str, ...]]], ...] = (
    (("contracts", "transfers", "chuyen_giao"), _CONTRACT_COLUMNS, _contract_cells),
    (("parks", "projects", "kcnc"), _PARK_COLUMNS, _park_cells),
    (("taxes", "tax_incentives", "thue"), _TAX_COLUMNS, _tax_cells),
)


def build_table(category: str, limit: int, records: list[dict]) -> Table:
    """Build the hitech records table; the caller prints it."""
    title = f"Danh mục hồ sơ công nghệ cao [{category.upper()}] (Tối đa {limit} bản ghi)"
    for aliases, columns, cells in _BRANCHES:
        if category in aliases:
            return _build(title, columns, cells, records)
    return _build(title, _ENTERPRISE_COLUMNS, _enterprise_cells, records)
