# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Veterinary command table construction — per record-type row layout."""

from __future__ import annotations

from rich.table import Table

from src.cli.commands.compliance_table_renderers import build_table as _build

_QUARANTINE_COLUMNS = (
    ("Mã Kiểm Dịch", "cyan"),
    ("Loài", "bold"),
    ("Số Lượng", "yellow"),
    ("Tuyến Vận Chuyển", ""),
    ("Trạng Thái", ""),
)

_SLAUGHTER_COLUMNS = (
    ("Mã Kiểm Soát", "cyan"),
    ("Cơ Sở Giết Mổ", "bold"),
    ("Loài", ""),
    ("Quy Mô", "yellow"),
    ("Đóng Dấu Thú Y", ""),
    ("Kết Luận", ""),
)

_TELEMETRY_ROWS = (
    ("Tổng chứng nhận kiểm dịch vận chuyển", "total_quarantine_certs", str),
    ("Chứng nhận kiểm dịch hợp chuẩn", "approved_quarantine_certs", str),
    ("Tổng động vật kiểm dịch hợp quy", "total_quarantined_animals", lambda v: f"{v:,} con/kg"),
    ("Số đợt bùng phát ổ dịch theo dõi", "total_outbreaks_recorded", str),
    ("Số cá thể tiêu hủy an toàn sinh học", "total_culled_animals", lambda v: f"{v:,} con"),
    ("Tổng đợt kiểm soát giết mổ", "total_slaughter_inspections", str),
    ("Lô thịt đạt chuẩn cấp tem/dấu", "passed_slaughter_batches", str),
    ("Tỷ lệ thịt sạch đạt chuẩn", "slaughter_pass_rate_pct", lambda v: f"{v}%"),
)


def _quarantine_row(r: dict) -> tuple[str, ...]:
    return (
        r["cert_id"],
        r["animal_species"],
        f"{r['quantity_head']:,}",
        f"{r['origin_province']} -> {r['destination_province']}",
        r["status"],
    )


def _slaughter_row(r: dict) -> tuple[str, ...]:
    return (
        r["inspection_id"],
        r["abattoir_name"],
        r["species"],
        f"{r['batch_size']:,}",
        "Đạt" if r["stamp_issued"] else "Từ chối",
        r["status"],
    )


def _telemetry_rows(t: dict) -> list[tuple[str, object]]:
    rows = [(label, fmt(t[key])) for label, key, fmt in _TELEMETRY_ROWS]
    rows.append((
        "Cơ sở dược thú y đạt chuẩn GMP",
        f"{t['certified_gmp_facilities']} / {t['total_medicine_facilities']}",
    ))
    return rows


def build_quarantine_table(records: list[dict]) -> Table:
    """Build the quarantine-certificate records table; the caller prints it."""
    return _build("Danh Sách Giấy Chứng Nhận Kiểm Dịch Động Vật", _QUARANTINE_COLUMNS, _quarantine_row, records)


def build_slaughter_table(records: list[dict]) -> Table:
    """Build the slaughter-inspection records table; the caller prints it."""
    return _build("Biên Bản Kiểm Soát Giết Mổ Thú Y", _SLAUGHTER_COLUMNS, _slaughter_row, records)


def build_telemetry_table(t: dict) -> Table:
    """Build the national veterinary telemetry table; the caller prints it."""
    table = Table(title="Vietnam National Veterinary Telemetry")
    table.add_column("Chỉ Số Nghiệp Vụ Thú Y", style="cyan")
    table.add_column("Giá Trị Thống Kê", style="bold yellow")
    for key, value in _telemetry_rows(t):
        table.add_row(key, value)
    return table


build_table = build_telemetry_table
