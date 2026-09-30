"""
Vietnamese Tax Administration, Electronic Invoices & Tax Audit Compliance Engine.
Pure Python standard library implementation adhering to:
- Law on Tax Administration 2019 (Law No. 38/2019/QH14)
- Decree No. 126/2020/ND-CP (Implementation of Law on Tax Administration)
- Decree No. 123/2020/ND-CP & Circular No. 78/2021/TT-BTC (Electronic Invoices & Records)
- Decree No. 125/2020/ND-CP & Decree No. 102/2021/ND-CP (Penalties for Tax Violations)
"""

import json
import os
import re
from datetime import datetime, date, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

# Valid Taxpayer Types
TAXPAYER_TYPES = {
    "ENTERPRISE",
    "INDIVIDUAL_BUSINESS",
    "FOREIGN_CONTRACTOR",
    "DEPENDENT_UNIT",
}

# Valid Tax Types
TAX_TYPES = {
    "CIT",               # Thuế Thu nhập Doanh nghiệp
    "VAT",               # Thuế Giá trị Gia tăng
    "PIT",               # Thuế Thu nhập Cá nhân
    "FCT",               # Thuế Nhà thầu nước ngoài
    "EXCISE",            # Thuế Tiêu thụ Đặc biệt
    "RESOURCE_ROYALTY",  # Thuế Tài nguyên
    "ENVIRONMENTAL",     # Thuế Bảo vệ Môi trường
}

# Valid Electronic Invoice Types
INVOICE_TYPES = {
    "VAT_INVOICE",              # Hóa đơn GTGT (Mẫu số 1)
    "SALES_INVOICE",            # Hóa đơn bán hàng (Mẫu số 2)
    "CASH_REGISTER_INVOICE",    # Hóa đơn khởi tạo từ máy tính tiền
    "PUBLIC_ASSET_INVOICE",     # Hóa đơn bán tài sản công
    "NATIONAL_RESERVE_INVOICE", # Hóa đơn bán hàng dự trữ quốc gia
}

# Valid VAT Rates
VALID_VAT_RATES = {0.0, 5.0, 8.0, 10.0}

# Valid Invoice Issue Statuses
INVOICE_STATUSES = {
    "ISSUED",
    "ADJUSTED",
    "REPLACED",
    "CANCELLED_FORM_04",
}

# Valid Tax Audit Types
AUDIT_TYPES = {
    "DESK_EXAMINATION",           # Kiểm tra hồ sơ thuế tại trụ sở cơ quan thuế
    "FIELD_EXAMINATION",          # Kiểm tra thuế tại trụ sở người nộp thuế
    "COMPREHENSIVE_INSPECTION",   # Thanh tra thuế chuyên sâu theo kế hoạch
    "TRANSFER_PRICING_INSPECTION",# Thanh tra giao dịch liên kết & chống chuyển giá
}

# Statutory Enforcement Measures in strict sequence (Art 124-125 Law No. 38/2019/QH14)
ENFORCEMENT_MEASURES = [
    "NONE",
    "BANK_ACCOUNT_FREEZE",       # 1. Trích tiền/phong tỏa tài khoản ngân hàng
    "SALARY_DEDUCTION",          # 2. Khấu trừ một phần lương/thu nhập
    "CUSTOMS_SUSPENSION",        # 3. Dừng làm thủ tục hải quan xuất nhập khẩu
    "INVOICE_INVALIDATION",      # 4. Ngừng sử dụng hóa đơn
    "ASSET_SEIZURE",             # 5. Kê biên tài sản, bán đấu giá tài sản kê biên
    "THIRD_PARTY_RECOVERY",      # 6. Thu tiền, tài sản từ bên thứ ba nắm giữ
    "LICENSE_REVOCATION",        # 7. Thu hồi giấy chứng nhận ĐKKD/giấy phép thành lập
    "EXIT_SUSPENSION",           # Tạm hoãn xuất cảnh theo Điều 66
]


class TaxAdminEngine:
    """Core autonomous engine for Vietnamese Tax Administration & E-Invoicing."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_TAXADMIN_DB",
                str(Path.home() / ".mekong" / "taxadmin.db")
            )
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS taxpayers (
                    taxpayer_id TEXT PRIMARY KEY,
                    tax_code TEXT UNIQUE NOT NULL,
                    taxpayer_name TEXT NOT NULL,
                    legal_rep TEXT NOT NULL,
                    taxpayer_type TEXT NOT NULL,
                    tax_office TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'ACTIVE',
                    registered_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS tax_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    tax_code TEXT NOT NULL,
                    tax_type TEXT NOT NULL,
                    tax_period TEXT NOT NULL,
                    declared_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    assessed_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    paid_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    due_date TEXT NOT NULL,
                    days_overdue INTEGER NOT NULL DEFAULT 0,
                    late_payment_interest_vnd REAL NOT NULL DEFAULT 0.0,
                    enforcement_measure TEXT NOT NULL DEFAULT 'NONE',
                    exit_suspension INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (tax_code) REFERENCES taxpayers(tax_code)
                );

                CREATE TABLE IF NOT EXISTS electronic_invoices (
                    invoice_id TEXT PRIMARY KEY,
                    invoice_code TEXT UNIQUE NOT NULL,
                    invoice_type TEXT NOT NULL,
                    seller_tax_code TEXT NOT NULL,
                    seller_name TEXT NOT NULL,
                    buyer_tax_code TEXT NOT NULL,
                    buyer_name TEXT NOT NULL,
                    subtotal_vnd REAL NOT NULL,
                    vat_rate_pct REAL NOT NULL,
                    vat_amount_vnd REAL NOT NULL,
                    total_amount_vnd REAL NOT NULL,
                    tax_authority_code TEXT,
                    issue_status TEXT NOT NULL DEFAULT 'ISSUED',
                    reference_invoice_code TEXT,
                    issued_at TEXT NOT NULL,
                    FOREIGN KEY (seller_tax_code) REFERENCES taxpayers(tax_code)
                );

                CREATE TABLE IF NOT EXISTS tax_audits (
                    audit_id TEXT PRIMARY KEY,
                    tax_code TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    tax_office TEXT NOT NULL,
                    decision_number TEXT NOT NULL,
                    audit_year INTEGER NOT NULL,
                    underdeclared_tax_vnd REAL NOT NULL DEFAULT 0.0,
                    penalty_amount_vnd REAL NOT NULL DEFAULT 0.0,
                    late_payment_fee_vnd REAL NOT NULL DEFAULT 0.0,
                    total_recovery_vnd REAL NOT NULL DEFAULT 0.0,
                    violation_description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
                    concluded_at TEXT NOT NULL,
                    FOREIGN KEY (tax_code) REFERENCES taxpayers(tax_code)
                );
            """)

    @staticmethod
    def validate_tax_code(tax_code: str) -> bool:
        """Validate Vietnamese Tax Identification Number (MST) format (10 or 13 digits)."""
        pattern = r"^\d{10}(-\d{3})?$"
        return bool(re.match(pattern, tax_code.strip()))

    def register_taxpayer(
        self,
        tax_code: str,
        taxpayer_name: str,
        legal_rep: str,
        taxpayer_type: str = "ENTERPRISE",
        tax_office: str = "Cục Thuế TP. Hà Nội",
        status: str = "ACTIVE",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Register a taxpayer into the national tax register under Law No. 38/2019/QH14."""
        tax_code = tax_code.strip()
        if not self.validate_tax_code(tax_code):
            raise ValueError(f"Mã số thuế không hợp lệ theo chuẩn 10 số hoặc 13 số: {tax_code}")

        if taxpayer_type not in TAXPAYER_TYPES:
            raise ValueError(f"Loại người nộp thuế không hợp lệ: {taxpayer_type}. Phải thuộc: {TAXPAYER_TYPES}")

        if not taxpayer_name.strip():
            raise ValueError("Tên người nộp thuế không được để trống")
        if not legal_rep.strip():
            raise ValueError("Người đại diện theo pháp luật không được để trống")

        taxpayer_id = f"TAX-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata_str = json.dumps(metadata or {}, ensure_ascii=False)

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO taxpayers (
                        taxpayer_id, tax_code, taxpayer_name, legal_rep,
                        taxpayer_type, tax_office, status, registered_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        taxpayer_id, tax_code, taxpayer_name.strip(), legal_rep.strip(),
                        taxpayer_type, tax_office.strip(), status, now_iso, metadata_str
                    )
                )
            except sqlite3.IntegrityError:
                raise ValueError(f"Mã số thuế {tax_code} đã tồn tại trong hệ thống quản lý thuế")

        return {
            "ok": True,
            "taxpayer_id": taxpayer_id,
            "tax_code": tax_code,
            "taxpayer_name": taxpayer_name.strip(),
            "legal_rep": legal_rep.strip(),
            "taxpayer_type": taxpayer_type,
            "tax_office": tax_office.strip(),
            "status": status,
            "registered_at": now_iso,
        }

    def assess_tax_and_interest(
        self,
        tax_code: str,
        tax_type: str,
        tax_period: str,
        declared_amount_vnd: float,
        assessed_amount_vnd: float,
        due_date_str: str,
        paid_amount_vnd: float = 0.0,
        current_date_str: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record tax assessment, compute days overdue, calculate late payment interest at 0.03%/day
        under Article 59, and determine statutory enforcement measure under Article 124-125.
        """
        tax_code = tax_code.strip()
        if tax_type not in TAX_TYPES:
            raise ValueError(f"Loại thuế không hợp lệ: {tax_type}. Phải thuộc: {TAX_TYPES}")

        if declared_amount_vnd < 0 or assessed_amount_vnd < 0 or paid_amount_vnd < 0:
            raise ValueError("Số tiền thuế không được âm")

        # Verify taxpayer exists
        with self._get_connection() as conn:
            row = conn.execute("SELECT tax_code, legal_rep FROM taxpayers WHERE tax_code = ?", (tax_code,)).fetchone()
            if not row:
                raise ValueError(f"Không tìm thấy người nộp thuế với mã số thuế: {tax_code}")

        try:
            due_dt = date.fromisoformat(due_date_str)
        except ValueError:
            raise ValueError(f"Hạn nộp thuế không đúng định dạng YYYY-MM-DD: {due_date_str}")

        if current_date_str:
            try:
                curr_dt = date.fromisoformat(current_date_str)
            except ValueError:
                raise ValueError(f"Ngày tính tiền phạt không đúng định dạng YYYY-MM-DD: {current_date_str}")
        else:
            curr_dt = date.today()

        effective_assessed = max(declared_amount_vnd, assessed_amount_vnd)
        outstanding_tax = max(0.0, effective_assessed - paid_amount_vnd)

        # Calculate late payment interest (Tiền chậm nộp 0.03%/ngày theo Điều 59)
        days_overdue = max(0, (curr_dt - due_dt).days) if outstanding_tax > 0 else 0
        late_interest = round(outstanding_tax * 0.0003 * days_overdue, 2)

        # Determine statutory enforcement measure & exit suspension based on overdue days and amount
        enforcement_measure = "NONE"
        exit_suspension = 0
        status = "PENDING"

        if outstanding_tax == 0.0:
            status = "SETTLED"
        elif paid_amount_vnd > 0:
            status = "PARTIALLY_PAID"

        if outstanding_tax > 0 and days_overdue > 0:
            if days_overdue >= 90:
                status = "ENFORCING"
                # Over 90 days: apply Art 124 enforcement hierarchy
                if days_overdue < 120:
                    enforcement_measure = "BANK_ACCOUNT_FREEZE"
                elif days_overdue < 150:
                    enforcement_measure = "INVOICE_INVALIDATION"
                elif days_overdue < 180:
                    enforcement_measure = "CUSTOMS_SUSPENSION"
                elif days_overdue < 210:
                    enforcement_measure = "ASSET_SEIZURE"
                else:
                    enforcement_measure = "LICENSE_REVOCATION"

                # Exit suspension under Art 66 for enterprise legal rep with overdue debts over 90 days
                if outstanding_tax >= 50_000_000.0:
                    exit_suspension = 1
            else:
                status = "PENDING"

        assessment_id = f"AST-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tax_assessments (
                    assessment_id, tax_code, tax_type, tax_period,
                    declared_amount_vnd, assessed_amount_vnd, paid_amount_vnd,
                    due_date, days_overdue, late_payment_interest_vnd,
                    enforcement_measure, exit_suspension, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment_id, tax_code, tax_type, tax_period,
                    declared_amount_vnd, assessed_amount_vnd, paid_amount_vnd,
                    due_date_str, days_overdue, late_interest,
                    enforcement_measure, exit_suspension, status, now_iso
                )
            )

        return {
            "ok": True,
            "assessment_id": assessment_id,
            "tax_code": tax_code,
            "tax_type": tax_type,
            "tax_period": tax_period,
            "declared_amount_vnd": declared_amount_vnd,
            "assessed_amount_vnd": assessed_amount_vnd,
            "effective_tax_vnd": effective_assessed,
            "paid_amount_vnd": paid_amount_vnd,
            "outstanding_tax_vnd": outstanding_tax,
            "due_date": due_date_str,
            "days_overdue": days_overdue,
            "late_payment_interest_vnd": late_interest,
            "total_payable_vnd": outstanding_tax + late_interest,
            "enforcement_measure": enforcement_measure,
            "exit_suspension": bool(exit_suspension),
            "status": status,
        }

    def issue_electronic_invoice(
        self,
        invoice_code: str,
        invoice_type: str,
        seller_tax_code: str,
        buyer_tax_code: str,
        buyer_name: str,
        subtotal_vnd: float,
        vat_rate_pct: float = 10.0,
        with_tax_authority_code: bool = True,
    ) -> Dict[str, Any]:
        """
        Issue an electronic invoice complying with Decree No. 123/2020/ND-CP and Circular No. 78/2021/TT-BTC.
        """
        invoice_code = invoice_code.strip()
        seller_tax_code = seller_tax_code.strip()
        buyer_tax_code = buyer_tax_code.strip()

        if invoice_type not in INVOICE_TYPES:
            raise ValueError(f"Loại hóa đơn điện tử không hợp lệ: {invoice_type}. Phải thuộc: {INVOICE_TYPES}")

        if vat_rate_pct not in VALID_VAT_RATES:
            raise ValueError(f"Thuế suất GTGT không hợp lệ: {vat_rate_pct}%. Phải thuộc: {VALID_VAT_RATES}")

        if subtotal_vnd < 0:
            raise ValueError("Tổng tiền hàng hóa trước thuế không được âm")

        if not buyer_name.strip():
            raise ValueError("Tên người mua không được để trống")

        # Check seller exists and active
        with self._get_connection() as conn:
            seller = conn.execute(
                "SELECT tax_code, taxpayer_name, status FROM taxpayers WHERE tax_code = ?",
                (seller_tax_code,)
            ).fetchone()
            if not seller:
                raise ValueError(f"Người bán (MST: {seller_tax_code}) chưa được đăng ký trong hệ thống")
            if seller["status"] != "ACTIVE":
                raise ValueError(f"Người bán đang ở trạng thái {seller['status']}, không đủ điều kiện phát hành hóa đơn")

        vat_amount = round(subtotal_vnd * (vat_rate_pct / 100.0), 2)
        total_amount = round(subtotal_vnd + vat_amount, 2)

        # Generate Tax Authority E-Invoice Code (Mã của cơ quan thuế) if requested
        tax_authority_code = None
        if with_tax_authority_code:
            tax_authority_code = f"CQT-{datetime.now(timezone.utc).strftime('%y%m%d')}-{uuid.uuid4().hex[:12].upper()}"

        invoice_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO electronic_invoices (
                        invoice_id, invoice_code, invoice_type, seller_tax_code,
                        seller_name, buyer_tax_code, buyer_name, subtotal_vnd,
                        vat_rate_pct, vat_amount_vnd, total_amount_vnd,
                        tax_authority_code, issue_status, issued_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id, invoice_code, invoice_type, seller_tax_code,
                        seller["taxpayer_name"], buyer_tax_code, buyer_name.strip(),
                        subtotal_vnd, vat_rate_pct, vat_amount, total_amount,
                        tax_authority_code, "ISSUED", now_iso
                    )
                )
            except sqlite3.IntegrityError:
                raise ValueError(f"Ký hiệu hóa đơn số {invoice_code} đã tồn tại trong hệ thống")

        return {
            "ok": True,
            "invoice_id": invoice_id,
            "invoice_code": invoice_code,
            "invoice_type": invoice_type,
            "seller_tax_code": seller_tax_code,
            "seller_name": seller["taxpayer_name"],
            "buyer_tax_code": buyer_tax_code,
            "buyer_name": buyer_name.strip(),
            "subtotal_vnd": subtotal_vnd,
            "vat_rate_pct": vat_rate_pct,
            "vat_amount_vnd": vat_amount,
            "total_amount_vnd": total_amount,
            "tax_authority_code": tax_authority_code,
            "issue_status": "ISSUED",
            "issued_at": now_iso,
        }

    def adjust_electronic_invoice(
        self,
        original_invoice_code: str,
        action: str,  # "ADJUST", "REPLACE", "CANCEL_FORM_04"
        new_invoice_code: Optional[str] = None,
        adjusted_diff_vnd: float = 0.0,
        explanation: str = "Sai sót thông tin hóa đơn",
    ) -> Dict[str, Any]:
        """
        Handle erroneous e-invoice correction under Article 19 Decree No. 123/2020/ND-CP.
        """
        original_invoice_code = original_invoice_code.strip()
        action = action.upper().strip()
        if action not in ("ADJUST", "REPLACE", "CANCEL_FORM_04"):
            raise ValueError(f"Hành động xử lý sai sót hóa đơn không hợp lệ: {action}. Phải là ADJUST, REPLACE, hoặc CANCEL_FORM_04")

        with self._get_connection() as conn:
            orig = conn.execute(
                "SELECT * FROM electronic_invoices WHERE invoice_code = ?",
                (original_invoice_code,)
            ).fetchone()
            if not orig:
                raise ValueError(f"Không tìm thấy hóa đơn gốc: {original_invoice_code}")
            if orig["issue_status"] == "CANCELLED_FORM_04":
                raise ValueError(f"Hóa đơn {original_invoice_code} đã bị hủy theo Mẫu 04/SS-HĐĐT, không thể điều chỉnh tiếp")

            now_iso = datetime.now(timezone.utc).isoformat()

            if action == "CANCEL_FORM_04":
                conn.execute(
                    "UPDATE electronic_invoices SET issue_status = 'CANCELLED_FORM_04' WHERE invoice_code = ?",
                    (original_invoice_code,)
                )
                return {
                    "ok": True,
                    "action": "CANCEL_FORM_04",
                    "original_invoice_code": original_invoice_code,
                    "status": "CANCELLED_FORM_04",
                    "form_04_notice": f"TB-04SS-{uuid.uuid4().hex[:6].upper()}",
                    "explanation": explanation,
                    "processed_at": now_iso,
                }

            if not new_invoice_code:
                raise ValueError("Bắt buộc cung cấp mã hóa đơn mới khi thực hiện ADJUST hoặc REPLACE")

            new_invoice_code = new_invoice_code.strip()
            new_status = "ADJUSTED" if action == "ADJUST" else "REPLACED"

            # Update original invoice
            conn.execute(
                "UPDATE electronic_invoices SET issue_status = ? WHERE invoice_code = ?",
                (new_status, original_invoice_code)
            )

            # Insert replacement or adjustment invoice record
            new_id = f"INV-{uuid.uuid4().hex[:8].upper()}"
            subtotal = orig["subtotal_vnd"] + adjusted_diff_vnd if action == "ADJUST" else orig["subtotal_vnd"]
            vat_rate = orig["vat_rate_pct"]
            vat_amt = round(subtotal * (vat_rate / 100.0), 2)
            tot_amt = round(subtotal + vat_amt, 2)
            cqt_code = f"CQT-{datetime.now(timezone.utc).strftime('%y%m%d')}-{uuid.uuid4().hex[:12].upper()}"

            conn.execute(
                """
                INSERT INTO electronic_invoices (
                    invoice_id, invoice_code, invoice_type, seller_tax_code,
                    seller_name, buyer_tax_code, buyer_name, subtotal_vnd,
                    vat_rate_pct, vat_amount_vnd, total_amount_vnd,
                    tax_authority_code, issue_status, reference_invoice_code, issued_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    new_id, new_invoice_code, orig["invoice_type"], orig["seller_tax_code"],
                    orig["seller_name"], orig["buyer_tax_code"], orig["buyer_name"],
                    subtotal, vat_rate, vat_amt, tot_amt,
                    cqt_code, new_status, original_invoice_code, now_iso
                )
            )

        return {
            "ok": True,
            "action": action,
            "original_invoice_code": original_invoice_code,
            "new_invoice_code": new_invoice_code,
            "status": new_status,
            "new_total_amount_vnd": tot_amt,
            "tax_authority_code": cqt_code,
            "explanation": explanation,
            "processed_at": now_iso,
        }

    def record_tax_audit(
        self,
        tax_code: str,
        audit_type: str,
        tax_office: str,
        decision_number: str,
        audit_year: int,
        underdeclared_tax_vnd: float,
        is_tax_evasion: bool = False,
        evasion_penalty_multiplier: float = 1.0,
        late_payment_days: int = 30,
        violation_description: str = "Khai sai dẫn đến thiếu số tiền thuế phải nộp",
    ) -> Dict[str, Any]:
        """
        Record tax audit & inspection conclusions with administrative penalties under Decree No. 125/2020/ND-CP.
        - Underdeclaration: 20% penalty on underdeclared amount (Điều 16).
        - Tax evasion: 1.0x to 3.0x fine on evaded tax amount (Điều 17).
        - Late payment interest: 0.03% / day on underdeclared amount.
        """
        tax_code = tax_code.strip()
        if audit_type not in AUDIT_TYPES:
            raise ValueError(f"Loại kiểm tra/thanh tra thuế không hợp lệ: {audit_type}. Phải thuộc: {AUDIT_TYPES}")

        if underdeclared_tax_vnd < 0:
            raise ValueError("Số tiền thuế khai thiếu hoặc trốn thuế không được âm")

        if audit_year < 2000 or audit_year > 2100:
            raise ValueError(f"Năm thanh tra không hợp lệ: {audit_year}")

        with self._get_connection() as conn:
            tp = conn.execute("SELECT tax_code, taxpayer_name FROM taxpayers WHERE tax_code = ?", (tax_code,)).fetchone()
            if not tp:
                raise ValueError(f"Không tìm thấy người nộp thuế với MST: {tax_code}")

        # Compute administrative fines under Decree 125/2020/ND-CP
        if is_tax_evasion:
            if evasion_penalty_multiplier < 1.0 or evasion_penalty_multiplier > 3.0:
                raise ValueError("Mức phạt trốn thuế phải từ 1.0 lần đến 3.0 lần số tiền trốn thuế theo Điều 17 Nghị định 125")
            penalty_amount = round(underdeclared_tax_vnd * evasion_penalty_multiplier, 2)
        else:
            # 20% underdeclaration penalty under Art 16
            penalty_amount = round(underdeclared_tax_vnd * 0.20, 2)

        # Late payment interest for the underdeclared period
        late_payment_fee = round(underdeclared_tax_vnd * 0.0003 * max(0, late_payment_days), 2)
        total_recovery = round(underdeclared_tax_vnd + penalty_amount + late_payment_fee, 2)

        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO tax_audits (
                    audit_id, tax_code, audit_type, tax_office,
                    decision_number, audit_year, underdeclared_tax_vnd,
                    penalty_amount_vnd, late_payment_fee_vnd, total_recovery_vnd,
                    violation_description, status, concluded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id, tax_code, audit_type, tax_office.strip(),
                    decision_number.strip(), audit_year, underdeclared_tax_vnd,
                    penalty_amount, late_payment_fee, total_recovery,
                    violation_description.strip(), "CONCLUDED", now_iso
                )
            )

        return {
            "ok": True,
            "audit_id": audit_id,
            "tax_code": tax_code,
            "taxpayer_name": tp["taxpayer_name"],
            "audit_type": audit_type,
            "tax_office": tax_office.strip(),
            "decision_number": decision_number.strip(),
            "audit_year": audit_year,
            "underdeclared_tax_vnd": underdeclared_tax_vnd,
            "penalty_amount_vnd": penalty_amount,
            "late_payment_fee_vnd": late_payment_fee,
            "total_recovery_vnd": total_recovery,
            "is_tax_evasion": is_tax_evasion,
            "penalty_rate": f"{evasion_penalty_multiplier}x" if is_tax_evasion else "20%",
            "violation_description": violation_description.strip(),
            "status": "CONCLUDED",
            "concluded_at": now_iso,
        }

    def list_records(self, category: str = "all", limit: int = 50) -> Dict[str, Any]:
        """List taxpayers, tax assessments, electronic invoices, or audit findings."""
        category = category.lower().strip()
        result: Dict[str, Any] = {"ok": True, "category": category}

        with self._get_connection() as conn:
            if category in ("all", "taxpayers"):
                rows = conn.execute(
                    "SELECT * FROM taxpayers ORDER BY registered_at DESC LIMIT ?", (limit,)
                ).fetchall()
                result["taxpayers"] = [dict(r) for r in rows]

            if category in ("all", "assessments"):
                rows = conn.execute(
                    "SELECT * FROM tax_assessments ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                result["assessments"] = [dict(r) for r in rows]

            if category in ("all", "invoices"):
                rows = conn.execute(
                    "SELECT * FROM electronic_invoices ORDER BY issued_at DESC LIMIT ?", (limit,)
                ).fetchall()
                result["invoices"] = [dict(r) for r in rows]

            if category in ("all", "audits"):
                rows = conn.execute(
                    "SELECT * FROM tax_audits ORDER BY concluded_at DESC LIMIT ?", (limit,)
                ).fetchall()
                result["audits"] = [dict(r) for r in rows]

        return result

    def get_telemetry_status(self) -> Dict[str, Any]:
        """Aggregate national tax compliance, e-invoicing volume, and audit recovery metrics."""
        with self._get_connection() as conn:
            taxpayer_count = conn.execute("SELECT COUNT(*) FROM taxpayers").fetchone()[0]
            assessment_count = conn.execute("SELECT COUNT(*) FROM tax_assessments").fetchone()[0]
            invoice_count = conn.execute("SELECT COUNT(*) FROM electronic_invoices").fetchone()[0]
            audit_count = conn.execute("SELECT COUNT(*) FROM tax_audits").fetchone()[0]

            tot_tax = conn.execute(
                "SELECT COALESCE(SUM(assessed_amount_vnd), 0.0), COALESCE(SUM(paid_amount_vnd), 0.0), COALESCE(SUM(late_payment_interest_vnd), 0.0) FROM tax_assessments"
            ).fetchone()
            total_assessed = tot_tax[0]
            total_paid = tot_tax[1]
            total_late_interest = tot_tax[2]

            tot_inv = conn.execute(
                "SELECT COALESCE(SUM(total_amount_vnd), 0.0), COALESCE(SUM(vat_amount_vnd), 0.0) FROM electronic_invoices WHERE issue_status != 'CANCELLED_FORM_04'"
            ).fetchone()
            total_invoice_revenue = tot_inv[0]
            total_vat_collected = tot_inv[1]

            tot_audit = conn.execute(
                "SELECT COALESCE(SUM(total_recovery_vnd), 0.0), COALESCE(SUM(penalty_amount_vnd), 0.0) FROM tax_audits"
            ).fetchone()
            total_audit_recovery = tot_audit[0]
            total_penalties = tot_audit[1]

            enforcing_count = conn.execute(
                "SELECT COUNT(*) FROM tax_assessments WHERE status = 'ENFORCING'"
            ).fetchone()[0]

            exit_suspended_count = conn.execute(
                "SELECT COUNT(*) FROM tax_assessments WHERE exit_suspension = 1"
            ).fetchone()[0]

        collection_rate = (total_paid / total_assessed * 100.0) if total_assessed > 0 else 100.0

        return {
            "ok": True,
            "status": "HEALTHY",
            "taxpayer_count": taxpayer_count,
            "assessment_count": assessment_count,
            "invoice_count": invoice_count,
            "audit_count": audit_count,
            "total_assessed_vnd": total_assessed,
            "total_paid_vnd": total_paid,
            "total_late_payment_interest_vnd": total_late_interest,
            "collection_rate_pct": round(collection_rate, 2),
            "total_invoice_revenue_vnd": total_invoice_revenue,
            "total_vat_collected_vnd": total_vat_collected,
            "total_audit_recovery_vnd": total_audit_recovery,
            "total_penalties_vnd": total_penalties,
            "enforcing_count": enforcing_count,
            "exit_suspended_count": exit_suspended_count,
            "database_path": str(self.db_path),
        }
