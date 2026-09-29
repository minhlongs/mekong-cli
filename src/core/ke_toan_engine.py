# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese Accounting Standard (VAS), Circular 78 Electronic Invoices & Journal Entry Engine.

Provides offline, deterministic electronic invoicing, general ledger postings,
and XML generation compliant with Vietnamese accounting frameworks:
- Thông tư 78/2021/TT-BTC & Nghị định 123/2020/NĐ-CP (Electronic Invoices schema)
- Thông tư 200/2014/TT-BTC & Thông tư 133/2016/TT-BTC (VAS Chart of Accounts)
- Double-entry bookkeeping balance validation (Total Debit == Total Credit)

Pure Python standard-library-only implementation adhering to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
from decimal import Decimal, ROUND_HALF_UP
import json
import pathlib
import sqlite3
import typing
import uuid
import xml.dom.minidom
from xml.etree.ElementTree import Element, SubElement, tostring

VAT_RATES: dict[int, Decimal] = {
    0: Decimal("0.00"),
    5: Decimal("0.05"),
    8: Decimal("0.08"),
    10: Decimal("0.10"),
}

DISCLAIMER = "Tư vấn AI — không thay thế kế toán có chứng chỉ hành nghề."

# Canonical VAS Chart of Accounts (Thông tư 200 & 133)
CANONICAL_ACCOUNTS = [
    {"code": "111", "name": "Tiền mặt (Cash)", "type": "asset", "balance": "debit"},
    {"code": "112", "name": "Tiền gửi ngân hàng (Bank deposits)", "type": "asset", "balance": "debit"},
    {"code": "131", "name": "Phải thu của khách hàng (Trade receivables)", "type": "asset", "balance": "debit"},
    {"code": "1331", "name": "Thuế GTGT được khấu trừ (Deductible VAT)", "type": "asset", "balance": "debit"},
    {"code": "152", "name": "Nguyên liệu, vật liệu (Raw materials)", "type": "asset", "balance": "debit"},
    {"code": "156", "name": "Hàng hóa (Merchandise inventory)", "type": "asset", "balance": "debit"},
    {"code": "331", "name": "Phải trả cho người bán (Trade payables)", "type": "liability", "balance": "credit"},
    {"code": "3331", "name": "Thuế GTGT phải nộp (Output VAT payable)", "type": "liability", "balance": "credit"},
    {"code": "511", "name": "Doanh thu bán hàng và CCDV (Revenue)", "type": "revenue", "balance": "credit"},
    {"code": "632", "name": "Giá vốn hàng bán (Cost of Goods Sold)", "type": "expense", "balance": "debit"},
    {"code": "642", "name": "Chi phí quản lý doanh nghiệp (Admin expenses)", "type": "expense", "balance": "debit"},
    {"code": "911", "name": "Xác định kết quả kinh doanh (Income summary)", "type": "equity", "balance": "credit"},
]


def format_vnd(amount: Decimal | float | int) -> str:
    """Format numeric amount as Vietnamese Dong string (e.g. 15.000.000 đ)."""
    val = int(Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return f"{val:,} đ".replace(",", ".")


class KeToanEngine:
    """Vietnamese Accounting Standard (VAS) and TT78 E-Invoicing Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "ke_toan.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY,
                    invoice_series TEXT NOT NULL,
                    invoice_number INTEGER NOT NULL,
                    invoice_date TEXT NOT NULL,
                    seller_name TEXT NOT NULL,
                    seller_tax_code TEXT NOT NULL,
                    buyer_name TEXT NOT NULL,
                    buyer_tax_code TEXT NOT NULL DEFAULT '',
                    description TEXT NOT NULL,
                    subtotal REAL NOT NULL,
                    vat_rate INTEGER NOT NULL,
                    vat_amount REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    items_json TEXT NOT NULL DEFAULT '[]',
                    xml_content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS journal_entries (
                    entry_id TEXT PRIMARY KEY,
                    invoice_id TEXT,
                    entry_date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    total_debit REAL NOT NULL,
                    total_credit REAL NOT NULL,
                    entries_json TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts_chart (
                    account_code TEXT PRIMARY KEY,
                    account_name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    normal_balance TEXT NOT NULL
                )
                """
            )
            conn.commit()

            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM accounts_chart")
            if cursor.fetchone()["cnt"] == 0:
                for acc in CANONICAL_ACCOUNTS:
                    conn.execute(
                        """
                        INSERT INTO accounts_chart (account_code, account_name, account_type, normal_balance)
                        VALUES (?, ?, ?, ?)
                        """,
                        (acc["code"], acc["name"], acc["type"], acc["balance"]),
                    )
                conn.commit()

    def create_invoice(
        self,
        amount: float | int | Decimal,
        buyer: str,
        vat_rate: int = 10,
        seller: str = "Doanh Nghiệp",
        seller_tax_code: str = "0000000000",
        buyer_tax_code: str = "",
        description: str = "Hàng hóa/Dịch vụ",
        invoice_series: str = "C25TAA",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Create a TT78-compliant electronic invoice with VAT calculations."""
        subtotal_dec = Decimal(str(amount)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        vat_factor = VAT_RATES.get(vat_rate, Decimal("0.10"))
        vat_dec = (subtotal_dec * vat_factor).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total_dec = subtotal_dec + vat_dec

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        today_iso = now_dt.date().isoformat()
        now_iso = now_dt.isoformat()

        # Determine next invoice number
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT COALESCE(MAX(invoice_number), 0) + 1 AS next_num FROM invoices WHERE invoice_series = ?",
                (invoice_series,),
            )
            invoice_num = cursor.fetchone()["next_num"]

        invoice_id = f"INV-{invoice_series}-{invoice_num:06d}"

        items = [
            {
                "line_no": 1,
                "item_code": "SP001",
                "description": description,
                "unit": "Cái",
                "quantity": 1,
                "unit_price": float(subtotal_dec),
                "subtotal": float(subtotal_dec),
                "vat_rate_pct": vat_rate,
                "vat_amount": float(vat_dec),
                "total": float(total_dec),
            }
        ]

        invoice_dict = {
            "invoice_id": invoice_id,
            "invoice_series": invoice_series,
            "invoice_number": invoice_num,
            "invoice_date": today_iso,
            "seller_name": seller,
            "seller_tax_code": seller_tax_code,
            "buyer_name": buyer,
            "buyer_tax_code": buyer_tax_code,
            "description": description,
            "subtotal": float(subtotal_dec),
            "vat_rate": vat_rate,
            "vat_amount": float(vat_dec),
            "total_amount": float(total_dec),
            "items": items,
            "formatted": {
                "subtotal": format_vnd(subtotal_dec),
                "vat": format_vnd(vat_dec),
                "total": format_vnd(total_dec),
            },
            "created_at": now_iso,
        }

        xml_output = self._generate_xml_from_data(invoice_dict)
        invoice_dict["xml_content"] = xml_output

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO invoices (
                        invoice_id, invoice_series, invoice_number, invoice_date,
                        seller_name, seller_tax_code, buyer_name, buyer_tax_code,
                        description, subtotal, vat_rate, vat_amount, total_amount,
                        items_json, xml_content, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        invoice_series,
                        invoice_num,
                        today_iso,
                        seller,
                        seller_tax_code,
                        buyer,
                        buyer_tax_code,
                        description,
                        float(subtotal_dec),
                        vat_rate,
                        float(vat_dec),
                        float(total_dec),
                        json.dumps(items),
                        xml_output,
                        now_iso,
                    ),
                )
                conn.commit()

        return invoice_dict

    def get_invoice(self, invoice_id: str) -> dict[str, typing.Any] | None:
        """Retrieve an invoice by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
            row = cursor.fetchone()
            if not row:
                return None
            data = dict(row)
            data["items"] = json.loads(data["items_json"])
            data["formatted"] = {
                "subtotal": format_vnd(data["subtotal"]),
                "vat": format_vnd(data["vat_amount"]),
                "total": format_vnd(data["total_amount"]),
            }
            return data

    def _generate_xml_from_data(self, data: dict[str, typing.Any]) -> str:
        """Serialize invoice data to Circular 78 / Decree 123 XML format."""
        root = Element("HDon")

        tt_chung = SubElement(root, "TTChung")
        SubElement(tt_chung, "KHMSHDon").text = "1"
        SubElement(tt_chung, "KHHDon").text = data.get("invoice_series", "C25TAA")
        SubElement(tt_chung, "SHDon").text = str(data.get("invoice_number", 1))
        SubElement(tt_chung, "NLap").text = data.get("invoice_date", datetime.date.today().isoformat())
        SubElement(tt_chung, "DVTTe").text = "VND"
        SubElement(tt_chung, "TGia").text = "1"

        nd_hdon = SubElement(root, "NDHDon")

        nb = SubElement(nd_hdon, "NBan")
        SubElement(nb, "Ten").text = data.get("seller_name", "Doanh Nghiệp")
        SubElement(nb, "MST").text = data.get("seller_tax_code", "0000000000")

        nm = SubElement(nd_hdon, "NMua")
        SubElement(nm, "Ten").text = data.get("buyer_name", "")
        if data.get("buyer_tax_code"):
            SubElement(nm, "MST").text = data["buyer_tax_code"]

        ds_hhhd = SubElement(nd_hdon, "DSHHDVu")
        items = data.get("items", [])
        for i, item in enumerate(items, 1):
            hhhd = SubElement(ds_hhhd, "HHDVu")
            SubElement(hhhd, "STT").text = str(i)
            SubElement(hhhd, "MHang").text = item.get("item_code", f"SP{i:03d}")
            SubElement(hhhd, "THHDVu").text = item.get("description", "Hàng hóa/Dịch vụ")
            SubElement(hhhd, "DVTinh").text = item.get("unit", "Cái")
            SubElement(hhhd, "SLuong").text = str(item.get("quantity", 1))
            SubElement(hhhd, "DGia").text = str(item.get("unit_price", 0))
            SubElement(hhhd, "ThTien").text = str(item.get("subtotal", 0))
            SubElement(hhhd, "Tsuat").text = f"{item.get('vat_rate_pct', 10)}%"
            SubElement(hhhd, "TThue").text = str(item.get("vat_amount", 0))

        tt_toan = SubElement(nd_hdon, "TToan")
        SubElement(tt_toan, "TgTCThue").text = str(data.get("subtotal", 0))
        SubElement(tt_toan, "TgTThue").text = str(data.get("vat_amount", 0))
        SubElement(tt_toan, "TgTTTBSo").text = str(data.get("total_amount", 0))

        xml_str = tostring(root, encoding="unicode")
        return xml.dom.minidom.parseString(xml_str).toprettyxml(indent="  ")

    def create_vas_journal(
        self,
        invoice_id_or_data: str | dict[str, typing.Any],
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Create balanced double-entry VAS journal for sales (Nợ 131 / Có 511, Có 3331)."""
        if isinstance(invoice_id_or_data, str):
            inv = self.get_invoice(invoice_id_or_data)
            if not inv:
                raise ValueError(f"Invoice not found: {invoice_id_or_data}")
        else:
            inv = invoice_id_or_data

        subtotal = float(inv.get("subtotal", 0.0))
        vat_amount = float(inv.get("vat_amount", 0.0))
        total_amount = float(inv.get("total_amount", subtotal + vat_amount))

        entry_id = f"JRN-{str(uuid.uuid4())[:8].upper()}"
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        today_iso = now_dt.date().isoformat()
        now_iso = now_dt.isoformat()

        entries = [
            {
                "account": "131",
                "account_name": "Phải thu của khách hàng",
                "debit": total_amount,
                "credit": 0.0,
                "note": f"Phải thu khách hàng {inv.get('buyer_name', '')}",
            },
            {
                "account": "511",
                "account_name": "Doanh thu bán hàng và CCDV",
                "debit": 0.0,
                "credit": subtotal,
                "note": "Doanh thu bán hàng hóa/dịch vụ",
            },
            {
                "account": "3331",
                "account_name": "Thuế GTGT phải nộp",
                "debit": 0.0,
                "credit": vat_amount,
                "note": "Thuế GTGT đầu ra phải nộp NSNN",
            },
        ]

        total_debit = sum(e["debit"] for e in entries)
        total_credit = sum(e["credit"] for e in entries)

        # Enforce double-entry balance invariant
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Unbalanced journal entry: Debit ({total_debit}) != Credit ({total_credit})")

        journal_dict = {
            "entry_id": entry_id,
            "invoice_id": inv.get("invoice_id", ""),
            "entry_date": today_iso,
            "description": f"Ghi nhận doanh thu bán hàng — {inv.get('buyer_name', '')}",
            "total_debit": total_debit,
            "total_credit": total_credit,
            "balanced": True,
            "entries": entries,
            "disclaimer": DISCLAIMER,
            "created_at": now_iso,
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO journal_entries (
                        entry_id, invoice_id, entry_date, description,
                        total_debit, total_credit, entries_json, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id,
                        inv.get("invoice_id", ""),
                        today_iso,
                        journal_dict["description"],
                        total_debit,
                        total_credit,
                        json.dumps(entries),
                        now_iso,
                    ),
                )
                conn.commit()

        return journal_dict

    def list_invoices(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List historical invoices from database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM invoices ORDER BY created_at DESC LIMIT ?", (limit,))
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["items"] = json.loads(d["items_json"])
                d["formatted"] = {
                    "subtotal": format_vnd(d["subtotal"]),
                    "vat": format_vnd(d["vat_amount"]),
                    "total": format_vnd(d["total_amount"]),
                }
                results.append(d)
            return results

    def list_journal_entries(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List historical journal entries from database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM journal_entries ORDER BY created_at DESC LIMIT ?", (limit,))
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["entries"] = json.loads(d["entries_json"])
                results.append(d)
            return results

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve accounting engine telemetry and ledger status."""
        with self._get_connection() as conn:
            inv_stats = conn.execute(
                "SELECT COUNT(*) AS total_count, COALESCE(SUM(subtotal), 0) AS total_subtotal, COALESCE(SUM(vat_amount), 0) AS total_vat, COALESCE(SUM(total_amount), 0) AS total_amount FROM invoices"
            ).fetchone()

            jrn_stats = conn.execute(
                "SELECT COUNT(*) AS total_jrn, COALESCE(SUM(total_debit), 0) AS sum_debit FROM journal_entries"
            ).fetchone()

            acc_count = conn.execute("SELECT COUNT(*) AS total_acc FROM accounts_chart").fetchone()["total_acc"]

        recent_invs = self.list_invoices(limit=5)
        recent_jrns = self.list_journal_entries(limit=5)

        return {
            "status": "operational",
            "total_invoices": inv_stats["total_count"],
            "total_revenue": round(inv_stats["total_subtotal"], 2),
            "total_vat_output": round(inv_stats["total_vat"], 2),
            "total_gross_invoiced": round(inv_stats["total_amount"], 2),
            "total_journal_entries": jrn_stats["total_jrn"],
            "total_ledger_turnover": round(jrn_stats["sum_debit"], 2),
            "total_accounts": acc_count,
            "recent_invoices": recent_invs,
            "recent_journals": recent_jrns,
            "standards_compliance": {
                "electronic_invoices": "Thông tư 78/2021/TT-BTC & Nghị định 123/2020/NĐ-CP",
                "accounting_framework": "Thông tư 200/2014/TT-BTC & Thông tư 133/2016/TT-BTC (VAS)",
                "schema_validation": "TCT XML Schema",
            },
        }
