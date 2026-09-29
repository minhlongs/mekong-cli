# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous VietQR / Napas 247 Instant Payment, Dynamic EMVCo QR Code & Banking Webhook Verification Engine.

Implements Vietnamese banking standards and instant interbank payments:
- Quyết định 201/QĐ-NHNN & Thông tư 07/VBHN-NHNN (Quy định về thanh toán không dùng tiền mặt và Napas 247).
- EMVCo QR Code Specification for Payment Systems (Merchant-Presented Mode).
- CRC16-CCITT polynomial 0x1021 checksum verification.
- Pluggable webhook HMAC-SHA256 signature verifier (Sepay / Napas / Open Banking API).
- Persistent SQLite WAL storage in ``.mekong/vietqr.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Vietnamese Banking Dictionary (Napas 247 Participant BIN Codes)
# ---------------------------------------------------------------------------

VIETNAMESE_BANKS: list[dict[str, str]] = [
    {"bin": "970422", "short_name": "MB", "full_name": "Ngân hàng TMCP Quân Đội (MBBank)"},
    {"bin": "970436", "short_name": "VCB", "full_name": "Ngân hàng TMCP Ngoại Thương Việt Nam (Vietcombank)"},
    {"bin": "970415", "short_name": "CTG", "full_name": "Ngân hàng TMCP Công Thương Việt Nam (VietinBank)"},
    {"bin": "970418", "short_name": "BIDV", "full_name": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam"},
    {"bin": "970405", "short_name": "VBA", "full_name": "Ngân hàng Nông nghiệp và Phát triển Nông thôn Việt Nam (Agribank)"},
    {"bin": "970407", "short_name": "TCB", "full_name": "Ngân hàng TMCP Kỹ Thương Việt Nam (Techcombank)"},
    {"bin": "970416", "short_name": "ACB", "full_name": "Ngân hàng TMCP Á Châu"},
    {"bin": "970423", "short_name": "TPB", "full_name": "Ngân hàng TMCP Tiên Phong (TPBank)"},
    {"bin": "970432", "short_name": "VPB", "full_name": "Ngân hàng TMCP Việt Nam Thịnh Vượng (VPBank)"},
    {"bin": "970454", "short_name": "BVB", "full_name": "Ngân hàng TMCP Bản Việt (BVBank)"},
]

# ---------------------------------------------------------------------------
# EMVCo TLV Constants & CRC16-CCITT Engine
# ---------------------------------------------------------------------------

_PAYLOAD_FORMAT_INDICATOR = "000201"
_POINT_OF_INITIATION_METHOD_DYNAMIC = "010212"  # 12 = Dynamic QR (contains amount)
_POINT_OF_INITIATION_METHOD_STATIC = "010211"   # 11 = Static QR
_MERCHANT_ACCOUNT_TAG = "38"
_GUI_TAG = "00"
_SERVICE_ID_NAPAS = "A000000727"
_BIN_TAG = "01"
_ACCOUNT_TAG = "02"
_SERVICE_CODE_TAG = "02"
_SERVICE_CODE_TRANSFER = "QRIBFTTA"  # Fast interbank fund transfer via Account
_CURRENCY_TAG = "53"
_CURRENCY_VND = "704"
_AMOUNT_TAG = "54"
_COUNTRY_TAG = "58"
_COUNTRY_VN = "VN"
_ADDITIONAL_DATA_TAG = "62"
_MEMO_SUBTAG = "08"
_CRC_TAG = "6304"


def _tlv(tag: str, value: str) -> str:
    """Format Tag-Length-Value chunk per EMVCo QR specification."""
    val_str = str(value)
    return f"{tag}{len(val_str):02d}{val_str}"


def _crc16_ccitt(data: str) -> str:
    """Compute CRC-16/CCITT (polynomial 0x1021, init 0xFFFF) checksum for EMVCo QR."""
    crc = 0xFFFF
    for byte in data.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def build_emvco_payload(
    bin_code: str,
    account_number: str,
    amount_vnd: int = 0,
    memo: str = "",
) -> str:
    """Construct deterministic EMVCo-compliant QR string for Napas 247."""
    clean_bin = str(bin_code).strip()
    clean_acc = str(account_number).strip()
    clean_memo = str(memo).strip()

    # Consumer / Merchant sub-tags for Tag 38
    merchant_subparts = (
        _tlv(_GUI_TAG, _SERVICE_ID_NAPAS)
        + _tlv(_BIN_TAG, clean_bin)
        + _tlv(_ACCOUNT_TAG, clean_acc)
    )
    merchant_info = _tlv(_MERCHANT_ACCOUNT_TAG, merchant_subparts)

    parts = [
        _PAYLOAD_FORMAT_INDICATOR,
        _POINT_OF_INITIATION_METHOD_DYNAMIC if amount_vnd > 0 else _POINT_OF_INITIATION_METHOD_STATIC,
        merchant_info,
        _tlv(_CURRENCY_TAG, _CURRENCY_VND),
    ]

    if amount_vnd > 0:
        parts.append(_tlv(_AMOUNT_TAG, str(amount_vnd)))

    parts.append(_tlv(_COUNTRY_TAG, _COUNTRY_VN))

    if clean_memo:
        # Tag 62 Subtag 08 (Purpose of Transaction / Memo)
        parts.append(_tlv(_ADDITIONAL_DATA_TAG, _tlv(_MEMO_SUBTAG, clean_memo)))

    raw_without_crc = "".join(parts) + _CRC_TAG
    crc = _crc16_ccitt(raw_without_crc)
    return raw_without_crc + crc


# ---------------------------------------------------------------------------
# VietQR Autonomous Engine
# ---------------------------------------------------------------------------


class VietQrEngine:
    """Autonomous VietQR / Napas 247 Instant Payment & Reconciliation Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "vietqr.db"
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
                CREATE TABLE IF NOT EXISTS bank_accounts (
                    account_id TEXT PRIMARY KEY,
                    bin_code TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    account_holder TEXT NOT NULL,
                    is_default INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS qr_codes (
                    qr_id TEXT PRIMARY KEY,
                    bin_code TEXT NOT NULL,
                    bank_short TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    account_holder TEXT NOT NULL,
                    amount_vnd INTEGER NOT NULL,
                    memo TEXT NOT NULL,
                    emvco_payload TEXT NOT NULL,
                    quicklink_url TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    bank_tx_id TEXT UNIQUE NOT NULL,
                    bin_code TEXT NOT NULL,
                    amount_vnd INTEGER NOT NULL,
                    memo TEXT NOT NULL,
                    matched_order_id TEXT,
                    status TEXT NOT NULL,
                    received_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

            # Pre-seed default corporate recipient account if none exists
            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM bank_accounts")
            if cursor.fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                conn.execute(
                    """
                    INSERT INTO bank_accounts (
                        account_id, bin_code, bank_name, account_number, account_holder, is_default, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "ACC-MEKONG-CORP",
                        "970422",
                        "MBBank (Ngân hàng Quân Đội)",
                        "0988889999",
                        "CTY TNHH CONG NGHE MEKONG",
                        1,
                        now,
                    ),
                )
                conn.commit()

    def resolve_bank(self, bank_query: str) -> dict[str, str]:
        """Resolve bank query by BIN code or short name (e.g. 'MB', 'VCB', '970422')."""
        q = bank_query.strip().upper()
        for b in VIETNAMESE_BANKS:
            if b["bin"] == q or b["short_name"].upper() == q:
                return b
        # Fallback to MBBank if unresolved
        return VIETNAMESE_BANKS[0]

    def get_default_account(self) -> dict[str, typing.Any]:
        """Fetch the default active receiving bank account."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM bank_accounts WHERE is_default = 1 LIMIT 1").fetchone()
            if row:
                return dict(row)
            row_any = conn.execute("SELECT * FROM bank_accounts LIMIT 1").fetchone()
            if row_any:
                return dict(row_any)
            return {
                "account_id": "ACC-DEFAULT",
                "bin_code": "970422",
                "bank_name": "MBBank",
                "account_number": "0988889999",
                "account_holder": "MEKONG CLI CORPORATE",
                "is_default": 1,
            }

    def generate_qr(
        self,
        bank: str = "MB",
        account_number: str = "",
        account_name: str = "",
        amount_vnd: int = 0,
        memo: str = "",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Generate official EMVCo VietQR string and Napas QuickLink."""
        bank_info = self.resolve_bank(bank)
        default_acc = self.get_default_account()

        target_acc_num = account_number.strip() if account_number else default_acc["account_number"]
        target_acc_name = account_name.strip() if account_name else default_acc["account_holder"]
        clean_amount = max(0, int(amount_vnd))
        clean_memo = memo.strip()

        # Build EMVCo payload string
        payload = build_emvco_payload(
            bin_code=bank_info["bin"],
            account_number=target_acc_num,
            amount_vnd=clean_amount,
            memo=clean_memo,
        )

        # QuickLink image URL for frictionless UI rendering
        # Format: https://img.vietqr.io/image/<BANK_BIN>-<ACCOUNT_NO>-compact2.png?amount=<AMOUNT>&addInfo=<MEMO>&accountName=<ACCOUNT_NAME>
        import urllib.parse
        encoded_acc_name = urllib.parse.quote(target_acc_name)
        encoded_memo = urllib.parse.quote(clean_memo)
        quicklink = f"https://img.vietqr.io/image/{bank_info['bin']}-{target_acc_num}-compact2.png"
        params = []
        if clean_amount > 0:
            params.append(f"amount={clean_amount}")
        if clean_memo:
            params.append(f"addInfo={encoded_memo}")
        if target_acc_name:
            params.append(f"accountName={encoded_acc_name}")
        if params:
            quicklink += "?" + "&".join(params)

        qr_id = f"VQR-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        res = {
            "ok": True,
            "qr_id": qr_id,
            "bank_bin": bank_info["bin"],
            "bank_short": bank_info["short_name"],
            "bank_full": bank_info["full_name"],
            "account_number": target_acc_num,
            "account_holder": target_acc_name,
            "amount_vnd": clean_amount,
            "memo": clean_memo,
            "emvco_payload": payload,
            "quicklink_url": quicklink,
            "created_at": now_iso,
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO qr_codes (
                        qr_id, bin_code, bank_short, account_number, account_holder,
                        amount_vnd, memo, emvco_payload, quicklink_url, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        qr_id,
                        bank_info["bin"],
                        bank_info["short_name"],
                        target_acc_num,
                        target_acc_name,
                        clean_amount,
                        clean_memo,
                        payload,
                        quicklink,
                        now_iso,
                    ),
                )
                conn.commit()

        return res

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        received_signature: str,
        secret: str,
    ) -> bool:
        """Verify HMAC-SHA256 signature from payment gateways (e.g. Sepay/Napas)."""
        if not secret or not received_signature:
            return False
        expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected.lower(), received_signature.strip().lower())

    def record_transaction(
        self,
        bank_tx_id: str,
        amount_vnd: int,
        memo: str,
        bin_code: str = "970422",
        matched_order_id: str | None = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Record an incoming bank payment transaction idempotently."""
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        tx_id = f"VTX-{str(uuid.uuid4())[:8].upper()}"

        with self._get_connection() as conn:
            existing = conn.execute(
                "SELECT * FROM transactions WHERE bank_tx_id = ?", (bank_tx_id,)
            ).fetchone()
            if existing:
                d = dict(existing)
                d["ok"] = True
                d["is_duplicate"] = True
                return d

            if save:
                conn.execute(
                    """
                    INSERT INTO transactions (
                        transaction_id, bank_tx_id, bin_code, amount_vnd,
                        memo, matched_order_id, status, received_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tx_id,
                        bank_tx_id,
                        bin_code,
                        amount_vnd,
                        memo,
                        matched_order_id,
                        "success",
                        now_iso,
                    ),
                )
                conn.commit()

        return {
            "ok": True,
            "transaction_id": tx_id,
            "bank_tx_id": bank_tx_id,
            "bin_code": bin_code,
            "amount_vnd": amount_vnd,
            "memo": memo,
            "matched_order_id": matched_order_id,
            "status": "success",
            "is_duplicate": False,
            "received_at": now_iso,
        }

    def list_transactions(self, limit: int = 20) -> list[dict[str, typing.Any]]:
        """List recent incoming bank transfer transactions."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM transactions ORDER BY received_at DESC LIMIT ?", (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def list_banks(self) -> list[dict[str, str]]:
        """List all supported Napas 247 participant banks."""
        return VIETNAMESE_BANKS

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregated VietQR system health, accounts, and transaction telemetry."""
        with self._get_connection() as conn:
            acc_count = conn.execute("SELECT COUNT(*) AS cnt FROM bank_accounts").fetchone()["cnt"]
            qr_count = conn.execute("SELECT COUNT(*) AS cnt FROM qr_codes").fetchone()["cnt"]
            tx_count = conn.execute("SELECT COUNT(*) AS cnt FROM transactions").fetchone()["cnt"]
            total_vnd_row = conn.execute("SELECT COALESCE(SUM(amount_vnd), 0) AS total FROM transactions").fetchone()
            total_vnd = int(total_vnd_row["total"]) if total_vnd_row else 0

            recent_txs = [dict(r) for r in conn.execute("SELECT * FROM transactions ORDER BY received_at DESC LIMIT 5").fetchall()]
            recent_qrs = [dict(r) for r in conn.execute("SELECT * FROM qr_codes ORDER BY created_at DESC LIMIT 5").fetchall()]

        default_acc = self.get_default_account()

        return {
            "ok": True,
            "status": "operational",
            "gateway": "VietQR / Napas 247 Instant Transfer",
            "statutory_standards": ["Quyết định 201/QĐ-NHNN", "Thông tư 07/VBHN-NHNN", "EMVCo QR v1.0"],
            "total_bank_accounts": acc_count,
            "default_account": {
                "bank": default_acc.get("bank_name"),
                "account_number": default_acc.get("account_number"),
                "account_holder": default_acc.get("account_holder"),
            },
            "total_qr_generated": qr_count,
            "total_transactions_recorded": tx_count,
            "total_volume_received_vnd": total_vnd,
            "supported_banks_count": len(VIETNAMESE_BANKS),
            "recent_transactions": recent_txs,
            "recent_qr_codes": recent_qrs,
        }
