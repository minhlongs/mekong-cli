# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shared rich-table construction for the Vietnamese compliance command suites.

Each suite keeps its own column specs and bilingual labels local; this module
only holds the two construction shapes they repeat, so a suite's command module
stays within the file-size limit.
"""

from __future__ import annotations

from typing import Callable, Iterable

from rich.table import Table


def build_table(title: str, columns: Iterable[tuple[str, str]], extract: Callable[[dict], Iterable[str]], records: Iterable[dict], border_style: str | None = None) -> Table:
    """Build a table from column (header, style) pairs and a per-record cell extractor."""
    table = Table(title=title, border_style=border_style)
    for header, style in columns:
        table.add_column(header, style=style)
    for record in records:
        table.add_row(*extract(record))
    return table


def build_key_value_table(
    title: str,
    rows: Iterable[tuple[str, object]],
    border_style: str,
    headers: tuple[str, str] = ("Chỉ số", "Giá trị"),
    value_style: str = "white",
    justify_value: bool = False,
) -> Table:
    """Build a two-column Chỉ số / Giá trị table."""
    table = Table(title=title, border_style=border_style)
    table.add_column(headers[0], style="bold cyan")
    table.add_column(headers[1], style=value_style, justify="right" if justify_value else "left")
    for key, value in rows:
        table.add_row(key, value)
    return table
