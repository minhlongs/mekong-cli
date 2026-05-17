"""
MISA CSV import/export — Format tương thích MISA AMIS và MISA SME.
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List

DISCLAIMER = "File CSV dành cho import thủ công vào MISA. Kiểm tra với kế toán trước khi nhập."


@dataclass
class MISAEntry:
    """Một dòng bút toán trong MISA."""
    date: date
    voucher_no: str
    account_debit: str
    account_credit: str
    amount: Decimal
    description: str
    partner: str = ""
    cost_center: str = ""


def to_misa_csv(entries: List[MISAEntry]) -> str:
    """Xuất danh sách bút toán sang CSV format MISA."""
    output = io.StringIO()
    writer = csv.writer(output, dialect="excel")

    # Header — MISA AMIS standard columns
    writer.writerow([
        "Ngày chứng từ", "Số chứng từ", "Diễn giải",
        "TK Nợ", "TK Có", "Số tiền", "Đối tượng", "Bộ phận",
    ])

    for entry in entries:
        writer.writerow([
            entry.date.strftime("%d/%m/%Y"),
            entry.voucher_no,
            entry.description,
            entry.account_debit,
            entry.account_credit,
            str(int(entry.amount)),
            entry.partner,
            entry.cost_center,
        ])

    writer.writerow([])
    writer.writerow(["# " + DISCLAIMER])

    return output.getvalue()


def from_misa_csv(csv_content: str) -> List[MISAEntry]:
    """Parse CSV MISA để đọc danh sách bút toán."""
    entries = []
    reader = csv.DictReader(io.StringIO(csv_content))
    for row in reader:
        if row.get("Ngày chứng từ", "").startswith("#"):
            continue
        try:
            d = row.get("Ngày chứng từ", "")
            if "/" in d:
                day, month, year = d.split("/")
                entry_date = date(int(year), int(month), int(day))
            else:
                continue
            entries.append(MISAEntry(
                date=entry_date,
                voucher_no=row.get("Số chứng từ", ""),
                description=row.get("Diễn giải", ""),
                account_debit=row.get("TK Nợ", ""),
                account_credit=row.get("TK Có", ""),
                amount=Decimal(row.get("Số tiền", "0").replace(",", "")),
                partner=row.get("Đối tượng", ""),
                cost_center=row.get("Bộ phận", ""),
            ))
        except (ValueError, KeyError):
            continue
    return entries
