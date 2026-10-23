# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Contract suite record-table construction - commercial contract row layout."""

from __future__ import annotations

from rich.table import Table

_COLUMNS = (("Mã HĐ", "cyan"), ("Số HĐ", "bold"), ("Loại mẫu", "green"), ("Bên A", "white"), ("Bên B", "white"), ("Giá trị (VND)", "yellow"), ("Rủi ro", "magenta"), ("Trạng thái", ""))


def format_vnd(amount: float) -> str:
    return f"{round(amount):,} VND".replace(",", ".")


def build_contracts_table(contracts: list[dict]) -> Table:
    """Build the commercial contract table; the caller prints it."""
    table = Table(title="Danh Mục Hợp Đồng Thương Mại Doanh Nghiệp", border_style="cyan")
    for header, style in _COLUMNS:
        table.add_column(header, style=style)
    for c in contracts:
        table.add_row(c["contract_id"], c["contract_number"], c["template_type"], c["party_a_name"], c["party_b_name"], format_vnd(c["contract_value_vnd"]), f"{c['risk_level']} ({c['risk_score']})", c["status"])
    return table
