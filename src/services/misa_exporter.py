# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
MISA AMIS CSV exporter — Phase 7 P03.

Generates 8-column voucher CSV from conversions.jsonl for monthly upload
to MISA AMIS accounting software (dominant VN SME accounting tool).

⚠️ DRAFT ACCOUNT CODES — accountant review pending (2026-05-17):
- 131 — Phải thu khách hàng (Customer receivables / AR)
- 511 — Doanh thu bán hàng và cung cấp dịch vụ (Service revenue)
- 33311 — Thuế GTGT đầu ra (Output VAT 10%)

Founder MUST get accountant sign-off before first real export to AMIS.
Overrides supported via env vars:
  MEKONG_MISA_DEBIT_ACCOUNT   (default 131)
  MEKONG_MISA_CREDIT_ACCOUNT  (default 511)
  MEKONG_MISA_VAT_ACCOUNT     (default 33311)

See docs/vn-misa-export.md for accountant review workflow.

MISA AMIS schema (voucher import CSV — 8 columns):
  voucher_date    YYYY-MM-DD
  voucher_no      PIL-YYYYMM-NNN (ascending within month)
  debit_account   default 131
  credit_account  default 511
  amount_vnd      integer
  description     "Mekong pilot {tier} — {user_id}"
  partner_id      pilot user_id (placeholder; real partner code if assigned)
  tax_code        empty for pilot tier (50% disc, no invoice issued)

Encoding: UTF-8 with BOM (Excel + AMIS compat for Vietnamese accents).
"""
from __future__ import annotations

import csv
import io
import os
from dataclasses import asdict, dataclass, field
from typing import IO, Optional


# UTF-8 BOM — required for Excel + AMIS to parse Vietnamese accents correctly
UTF8_BOM = "﻿"

# CSV column order (MISA AMIS voucher import schema 2026)
MISA_HEADERS = [
    "voucher_date",
    "voucher_no",
    "debit_account",
    "credit_account",
    "amount_vnd",
    "description",
    "partner_id",
    "tax_code",
]


def _default_debit() -> str:
    return os.environ.get("MEKONG_MISA_DEBIT_ACCOUNT", "131")


def _default_credit() -> str:
    return os.environ.get("MEKONG_MISA_CREDIT_ACCOUNT", "511")


def _default_vat() -> str:
    return os.environ.get("MEKONG_MISA_VAT_ACCOUNT", "33311")


@dataclass
class MISARow:
    """One MISA voucher row. Field order matches MISA_HEADERS exactly."""
    voucher_date: str       # YYYY-MM-DD
    voucher_no: str         # PIL-YYYYMM-NNN
    amount_vnd: int
    description: str
    partner_id: str
    debit_account: str = field(default_factory=_default_debit)
    credit_account: str = field(default_factory=_default_credit)
    tax_code: str = ""      # blank for pilot tier (informal, no invoice)


def _parse_ym(ym: str) -> tuple[int, int]:
    """Parse YYYY-MM → (year, month). Raises ValueError on bad format."""
    if not ym or len(ym) != 7 or ym[4] != "-":
        raise ValueError(f"Expected YYYY-MM, got {ym!r}")
    return int(ym[:4]), int(ym[5:7])


def _extract_ym(iso_date_or_datetime: str) -> Optional[str]:
    """Extract YYYY-MM from ISO date or datetime. Returns None on parse fail.

    Accepts: 2026-05-17, 2026-05-17T18:30:00+00:00, 2026-05-17T18:30:00Z, etc.
    """
    if not iso_date_or_datetime:
        return None
    try:
        # Strip Z + microseconds if present, then take first 7 chars (YYYY-MM)
        return iso_date_or_datetime[:7] if len(iso_date_or_datetime) >= 7 else None
    except (TypeError, IndexError):
        return None


def build_misa_rows(
    conversions: list[dict],
    from_ym: str,
    to_ym: str,
    org_id_filter: Optional[str] = None,
) -> list[MISARow]:
    """Filter conversions by date range (+ optional org) → map to MISARow.

    Date range filter uses `started_at` ISO date (YYYY-MM-DD) extracted to
    YYYY-MM for comparison. Inclusive both ends.

    org_id_filter: when set, only rows where c.get("org_id","default") ==
    org_id_filter are included. None means no org filtering (back-compat).

    Voucher numbers: `PIL-YYYYMM-NNN` ascending within each month. NNN
    restarts at 001 per month. Sorting is by started_at ASC for
    determinism.
    """
    if org_id_filter is not None:
        conversions = [
            c for c in conversions
            if (c.get("org_id") or "default") == org_id_filter
        ]

    from_y, from_m = _parse_ym(from_ym)
    to_y, to_m = _parse_ym(to_ym)
    from_key = from_y * 12 + from_m
    to_key = to_y * 12 + to_m
    if to_key < from_key:
        raise ValueError(f"Range invalid: to_ym ({to_ym}) before from_ym ({from_ym})")

    in_range: list[dict] = []
    for c in conversions:
        ym = _extract_ym(c.get("started_at", ""))
        if not ym:
            continue
        try:
            cy, cm = _parse_ym(ym)
        except ValueError:
            continue
        key = cy * 12 + cm
        if from_key <= key <= to_key:
            in_range.append(c)

    # Sort ascending by started_at for stable voucher numbering
    in_range.sort(key=lambda c: c.get("started_at", ""))

    # Counter per-month for voucher numbering
    seq_per_month: dict[str, int] = {}
    rows: list[MISARow] = []
    for c in in_range:
        started = c.get("started_at", "")
        ym = _extract_ym(started) or ""
        ym_compact = ym.replace("-", "")  # YYYYMM
        seq_per_month[ym_compact] = seq_per_month.get(ym_compact, 0) + 1
        voucher_no = f"PIL-{ym_compact}-{seq_per_month[ym_compact]:03d}"
        rows.append(MISARow(
            voucher_date=started[:10],  # YYYY-MM-DD
            voucher_no=voucher_no,
            amount_vnd=int(c.get("monthly_vnd", 0)),
            description=f"Mekong pilot {c.get('tier', 'unknown')} — {c.get('user_id', '')}",
            partner_id=c.get("user_id", ""),
        ))
    return rows


def write_csv(rows: list[MISARow], fp: IO[str]) -> None:
    """Write rows to a text stream, prepending UTF-8 BOM + header row.

    The caller owns the file handle (don't close it here). Use a
    text-mode file opened with encoding="utf-8" so the BOM is written
    correctly as a 3-byte sequence (EF BB BF) by Python's encoder.
    """
    fp.write(UTF8_BOM)
    writer = csv.DictWriter(fp, fieldnames=MISA_HEADERS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(asdict(row))


def to_csv_bytes(rows: list[MISARow]) -> bytes:
    """Convenience: build a UTF-8 BOM CSV in-memory and return bytes.

    Used by the HTTP route for StreamingResponse. The CLI script writes
    to disk via write_csv() directly to avoid building the whole thing
    in memory (though for N=100 it's negligible).
    """
    buf = io.StringIO()
    write_csv(rows, buf)
    return buf.getvalue().encode("utf-8")
