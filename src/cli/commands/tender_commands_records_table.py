# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tender command record-table construction — National E-GP package listing."""

from __future__ import annotations

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_table as _build

_COLUMNS = (("Mã gói thầu", "cyan"), ("Số E-GP", "bold"), ("Tên gói thầu", "white"), ("Chủ đầu tư", "green"), ("Hình thức", "yellow"), ("Dự toán (VND)", "magenta"), ("Trạng thái", ""))


def format_vnd(amount: float) -> str:
    """Render a VND amount with Vietnamese dot thousands separators."""
    return f"{round(amount):,} VND".replace(",", ".")


def _cells(r: dict) -> tuple[str, ...]:
    return (r["tender_id"], r["package_number"], r["package_name"], r["procuring_entity"], r["procurement_method"], format_vnd(r["budget_vnd"]), r["status"])


def build_table(tenders: list[dict]) -> Table:
    """Build the E-GP tender list table; the caller prints it."""
    return _build("Danh Mục Gói Thầu Mua Sắm Công (National E-GP)", _COLUMNS, _cells, tenders, border_style="cyan")
