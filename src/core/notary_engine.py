"""
Vietnamese Notary, Legal Practice & Judicial Authentication Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Công chứng 2014 (Luật số 53/2014/QH13) & Luật Công chứng 2024:
  * Tiêu chuẩn tổ chức hành nghề công chứng (Phòng công chứng & Văn phòng công chứng hợp danh).
  * Công chứng viên: Chứng chỉ hành nghề, bảo hiểm trách nhiệm nghề nghiệp bắt buộc.
  * Hợp đồng, giao dịch bắt buộc công chứng: Bất động sản, di sản thừa kế, tài sản có đăng ký.
  * Hệ thống Cơ sở dữ liệu công chứng ngăn chặn giao dịch giả mạo, tài sản đang thế chấp hoặc kê biên.
  * Thời hạn lưu trữ hồ sơ: Tối thiểu 20 năm, bản chính văn bản công chứng lưu trữ vĩnh viễn (Điều 64).
- Luật Luật sư 2006 (Luật số 65/2006/QH11, sửa đổi 2012):
  * Điều kiện hành nghề: Thẻ luật sư, Văn phòng luật sư / Công ty luật hợp danh hoặc TNHH.
  * Hợp đồng dịch vụ pháp lý và quy tắc đạo đức nghề nghiệp: Cấm xung đột lợi ích giữa các khách hàng (Điều 9).
- Nghị định số 23/2015/NĐ-CP:
  * Chứng thực bản sao từ bản chính, chứng thực chữ ký cá nhân và tính hợp lệ của văn bản gốc.
- Nghị định số 82/2020/NĐ-CP:
  * Xử phạt vi phạm hành chính trong hoạt động công chứng, luật sư và chứng thực tư pháp.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class NotaryEngine:
    """Core engine for Vietnamese Notary, Legal Practice and Authentication Compliance."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "notary.db")
        else:
            self.db_path = db_path
            parent = os.path.dirname(db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS notarial_contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notary_book_number TEXT UNIQUE NOT NULL,
                    contract_title TEXT NOT NULL,
                    notary_office TEXT NOT NULL,
                    notary_public_name TEXT NOT NULL,
                    party_a TEXT NOT NULL,
                    party_b TEXT NOT NULL,
                    contract_type TEXT NOT NULL,
                    transaction_value_vnd REAL NOT NULL,
                    is_mandatory_notarization INTEGER NOT NULL,
                    asset_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    is_approved INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS blocked_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT UNIQUE NOT NULL,
                    asset_description TEXT NOT NULL,
                    block_reason TEXT NOT NULL,
                    blocking_authority TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS legal_practice_agreements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agreement_code TEXT UNIQUE NOT NULL,
                    law_firm_name TEXT NOT NULL,
                    attorney_name TEXT NOT NULL,
                    bar_card_number TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    legal_matter TEXT NOT NULL,
                    fee_vnd REAL NOT NULL,
                    has_conflict_of_interest INTEGER NOT NULL,
                    has_professional_insurance INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS document_authentications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    auth_code TEXT UNIQUE NOT NULL,
                    document_title TEXT NOT NULL,
                    auth_type TEXT NOT NULL,
                    authenticating_body TEXT NOT NULL,
                    number_of_copies INTEGER NOT NULL,
                    is_original_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_fee_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Notarize Contract (Luật Công chứng 2014 & Luật Đất đai / Nhà ở)
    def notarize_contract(
        self,
        contract_title: str,
        notary_office: str,
        notary_public_name: str,
        party_a: str,
        party_b: str,
        contract_type: str = "REAL_ESTATE_TRANSFER",
        transaction_value_vnd: float = 3_000_000_000.0,
        asset_id: str = "GCN-QSDD-HN-2026-001",
        notary_fee_vnd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Performs statutory contract notarization check against legal impediments and asset blocks."""
        now = datetime.datetime.now()
        c_type = contract_type.upper().strip()
        deficiencies = []

        # Check if asset is blocked/frozen (mortgaged or under court seizure)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM blocked_assets WHERE asset_id = ?",
                (asset_id,),
            )
            blocked_row = cursor.fetchone()

        if blocked_row:
            deficiencies.append(
                f"Tài sản '{asset_id}' đang trong cơ sở dữ liệu ngăn chặn: {blocked_row['block_reason']} (Cơ quan yêu cầu: {blocked_row['blocking_authority']})"
            )

        # Mandatory notarization contract types
        mandatory_types = [
            "REAL_ESTATE_TRANSFER",  # Chuyển nhượng quyền sử dụng đất
            "REAL_ESTATE_MORTGAGE",  # Thế chấp bất động sản
            "HOUSING_PURCHASE",      # Mua bán nhà ở
            "INHERITANCE_DIVISION",  # Thỏa thuận phân chia di sản thừa kế
            "GIFT_REAL_ESTATE",      # Tặng cho quyền sử dụng đất
        ]
        is_mandatory = c_type in mandatory_types

        is_approved = len(deficiencies) == 0
        status = "NOTARIZED_APPROVED" if is_approved else "NOTARIZATION_BLOCKED"

        # Calculate statutory notary fee (Thông tư 257/2016/TT-BTC & Thông tư 111/2017)
        if notary_fee_vnd is None:
            if transaction_value_vnd <= 50_000_000:
                fee = 50_000.0
            elif transaction_value_vnd <= 100_000_000:
                fee = 100_000.0
            elif transaction_value_vnd <= 1_000_000_000:
                fee = transaction_value_vnd * 0.001
            elif transaction_value_vnd <= 3_000_000_000:
                fee = 1_000_000.0 + (transaction_value_vnd - 1_000_000_000.0) * 0.0008
            elif transaction_value_vnd <= 5_000_000_000:
                fee = 2_600_000.0 + (transaction_value_vnd - 3_000_000_000.0) * 0.0006
            elif transaction_value_vnd <= 10_000_000_000:
                fee = 3_800_000.0 + (transaction_value_vnd - 5_000_000_000.0) * 0.0005
            else:
                fee = min(70_000_000.0, 6_300_000.0 + (transaction_value_vnd - 10_000_000_000.0) * 0.0002)
        else:
            fee = notary_fee_vnd

        seq = hashlib.md5(f"{contract_title}:{party_a}:{party_b}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        book_num = f"CC-{now.year}-{seq}"

        result = {
            "notary_book_number": book_num,
            "contract_title": contract_title,
            "notary_office": notary_office,
            "notary_public_name": notary_public_name,
            "party_a": party_a,
            "party_b": party_b,
            "contract_type": c_type,
            "transaction_value_vnd": transaction_value_vnd,
            "statutory_notary_fee_vnd": round(fee, 0),
            "is_mandatory_notarization": is_mandatory,
            "asset_id": asset_id,
            "is_approved": is_approved,
            "status": status,
            "deficiencies": deficiencies,
            "archive_retention_years": 20,
            "statutory_basis": "Luật Công chứng 2014 & Thông tư 257/2016/TT-BTC",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO notarial_contracts
                (notary_book_number, contract_title, notary_office, notary_public_name,
                 party_a, party_b, contract_type, transaction_value_vnd, is_mandatory_notarization,
                 asset_id, status, is_approved, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    book_num,
                    contract_title,
                    notary_office,
                    notary_public_name,
                    party_a,
                    party_b,
                    c_type,
                    transaction_value_vnd,
                    1 if is_mandatory else 0,
                    asset_id,
                    status,
                    1 if is_approved else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 2. Block or Unblock Asset in Notary Prevention Database
    def manage_blocked_asset(
        self,
        asset_id: str,
        asset_description: str,
        block_reason: str,
        blocking_authority: str = "Tòa án Nhân dân TP. Hà Nội",
        is_blocked: bool = True,
    ) -> Dict[str, Any]:
        """Manages entry in the Notarial Asset Blocking Database (Cơ sở dữ liệu ngăn chặn giao dịch)."""
        now = datetime.datetime.now()
        with self._get_connection() as conn:
            if is_blocked:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO blocked_assets
                    (asset_id, asset_description, block_reason, blocking_authority, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (asset_id, asset_description, block_reason, blocking_authority, now.isoformat()),
                )
                action = "BLOCKED"
                summary = f"Tài sản '{asset_id}' đã được đưa vào diện ngăn chặn công chứng theo yêu cầu của {blocking_authority}"
            else:
                conn.execute("DELETE FROM blocked_assets WHERE asset_id = ?", (asset_id,))
                action = "UNBLOCKED"
                summary = f"Tài sản '{asset_id}' đã được giải tỏa ngăn chặn giao dịch"

        return {
            "asset_id": asset_id,
            "action": action,
            "is_blocked": is_blocked,
            "block_reason": block_reason if is_blocked else "None",
            "blocking_authority": blocking_authority if is_blocked else "None",
            "summary": summary,
            "statutory_basis": "Điều 62 Luật Công chứng 2014 về Cơ sở dữ liệu công chứng",
            "timestamp": now.isoformat(),
        }

    # 3. Audit Legal Practice Agreement (Luật Luật sư 2006/2012)
    def audit_legal_practice_agreement(
        self,
        law_firm_name: str,
        attorney_name: str,
        bar_card_number: str,
        client_name: str,
        legal_matter: str,
        fee_vnd: float = 50_000_000.0,
        has_conflict_of_interest: bool = False,
        has_professional_insurance: bool = True,
    ) -> Dict[str, Any]:
        """Audits attorney legal practice agreement for conflict of interest and professional insurance."""
        now = datetime.datetime.now()
        deficiencies = []

        if has_conflict_of_interest:
            deficiencies.append(
                "VI PHẠM ĐIỀU CẤM: Xung đột lợi ích thân chủ theo Điều 9 Luật Luật sư (cung cấp dịch vụ cho các bên có quyền lợi đối lập trong cùng vụ việc)"
            )

        if not has_professional_insurance:
            deficiencies.append(
                "Tổ chức hành nghề luật sư chưa mua bảo hiểm trách nhiệm nghề nghiệp bắt buộc cho luật sư theo quy định"
            )

        is_compliant = len(deficiencies) == 0
        status = "COMPLIANT_RETAINER" if is_compliant else "NON_COMPLIANT_RETAINER"
        seq = hashlib.md5(f"{law_firm_name}:{attorney_name}:{client_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        agreement_code = f"HDPL-{now.year}-{seq}"

        result = {
            "agreement_code": agreement_code,
            "law_firm_name": law_firm_name,
            "attorney_name": attorney_name,
            "bar_card_number": bar_card_number,
            "client_name": client_name,
            "legal_matter": legal_matter,
            "fee_vnd": fee_vnd,
            "has_conflict_of_interest": has_conflict_of_interest,
            "has_professional_insurance": has_professional_insurance,
            "is_compliant": is_compliant,
            "status": status,
            "deficiencies": deficiencies,
            "statutory_basis": "Điều 9, Điều 26 Luật Luật sư 2006 (sửa đổi 2012)",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO legal_practice_agreements
                (agreement_code, law_firm_name, attorney_name, bar_card_number, client_name,
                 legal_matter, fee_vnd, has_conflict_of_interest, has_professional_insurance,
                 status, is_compliant, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agreement_code,
                    law_firm_name,
                    attorney_name,
                    bar_card_number,
                    client_name,
                    legal_matter,
                    fee_vnd,
                    1 if has_conflict_of_interest else 0,
                    1 if has_professional_insurance else 0,
                    status,
                    1 if is_compliant else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. Authenticate Document / Signature (Nghị định 23/2015/NĐ-CP)
    def authenticate_document(
        self,
        document_title: str,
        auth_type: str = "COPY_AUTHENTICATION",
        authenticating_body: str = "Ủy ban Nhân dân Phường Bến Nghé, Quận 1",
        number_of_copies: int = 5,
        is_original_valid: bool = True,
    ) -> Dict[str, Any]:
        """Authenticates copies from original or individual signatures under Decree 23/2015/ND-CP."""
        now = datetime.datetime.now()
        a_type = auth_type.upper().strip()

        # Fee schedule: 2,000 VND / page or copy for certified true copy, 10,000 VND for signature authentication
        if a_type == "SIGNATURE_AUTHENTICATION":
            fee_per_unit = 10_000.0
        else:
            fee_per_unit = 2_000.0

        if not is_original_valid:
            status = "AUTHENTICATION_REFUSED"
            statutory_fee = 0.0
            legal_conclusion = "TỪ CHỐI CHỨNG THỰC: Bản chính có dấu hiệu tẩy xóa, sửa chữa hoặc không hợp lệ theo Điều 22 Nghị định 23/2015"
        else:
            status = "AUTHENTICATED_COMPLIANT"
            statutory_fee = fee_per_unit * number_of_copies
            legal_conclusion = f"Đã chứng thực hợp lệ {number_of_copies} bản theo đúng trình tự Nghị định 23/2015/NĐ-CP"

        seq = hashlib.md5(f"{document_title}:{authenticating_body}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        auth_code = f"CT-{now.year}-{seq}"

        result = {
            "auth_code": auth_code,
            "document_title": document_title,
            "auth_type": a_type,
            "authenticating_body": authenticating_body,
            "number_of_copies": number_of_copies,
            "is_original_valid": is_original_valid,
            "status": status,
            "statutory_fee_vnd": statutory_fee,
            "legal_conclusion": legal_conclusion,
            "statutory_basis": "Nghị định số 23/2015/NĐ-CP & Thông tư 226/2016/TT-BTC",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO document_authentications
                (auth_code, document_title, auth_type, authenticating_body,
                 number_of_copies, is_original_valid, status, statutory_fee_vnd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    auth_code,
                    document_title,
                    a_type,
                    authenticating_body,
                    number_of_copies,
                    1 if is_original_valid else 0,
                    status,
                    statutory_fee,
                    result["created_at"],
                ),
            )

        return result

    # 5. List Records
    def list_records(self, category: str = "contracts", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored notarial contracts, blocked assets, legal agreements, or authentications."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["blocked", "blocked_assets", "ngan_chan"]:
                cursor = conn.execute("SELECT * FROM blocked_assets ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["agreements", "law_firms", "luat_su"]:
                cursor = conn.execute("SELECT * FROM legal_practice_agreements ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["authentications", "copies", "chung_thuc"]:
                cursor = conn.execute("SELECT * FROM document_authentications ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM notarial_contracts ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 6. Telemetry & Summary Status
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide Notary, Legal Practice, and Authentication telemetry."""
        with self._get_connection() as conn:
            total_contracts = conn.execute("SELECT COUNT(*) FROM notarial_contracts").fetchone()[0]
            approved_contracts = conn.execute("SELECT COUNT(*) FROM notarial_contracts WHERE is_approved = 1").fetchone()[0]
            blocked_assets_count = conn.execute("SELECT COUNT(*) FROM blocked_assets").fetchone()[0]
            total_agreements = conn.execute("SELECT COUNT(*) FROM legal_practice_agreements").fetchone()[0]
            compliant_agreements = conn.execute("SELECT COUNT(*) FROM legal_practice_agreements WHERE is_compliant = 1").fetchone()[0]
            total_authentications = conn.execute("SELECT COUNT(*) FROM document_authentications").fetchone()[0]
            total_notary_fees = conn.execute("SELECT COALESCE(SUM(transaction_value_vnd), 0.0) FROM notarial_contracts WHERE is_approved = 1").fetchone()[0]

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Công chứng 2014 (Luật 53/2014), Luật Luật sư 2006 & Nghị định 23/2015/NĐ-CP",
            "total_notarial_contracts_executed": total_contracts,
            "approved_notarial_contracts": approved_contracts,
            "active_blocked_assets_in_registry": blocked_assets_count,
            "total_legal_agreements_audited": total_agreements,
            "compliant_legal_agreements": compliant_agreements,
            "total_document_authentications": total_authentications,
            "total_notarized_asset_value_vnd": total_notary_fees,
            "timestamp": datetime.datetime.now().isoformat(),
        }
