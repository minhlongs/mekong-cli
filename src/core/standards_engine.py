"""
Vietnamese Technical Standards, Metrology & Product Quality Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Tiêu chuẩn và Quy chuẩn kỹ thuật 2006 (Luật số 68/2006/QH11):
  * Tiêu chuẩn quốc gia (TCVN): Tự nguyện áp dụng (voluntary).
  * Quy chuẩn kỹ thuật quốc gia (QCVN): Bắt buộc áp dụng (mandatory).
  * Công bố hợp chuẩn (TCVN) và công bố hợp quy (QCVN).
- Luật Chất lượng sản phẩm, hàng hóa 2007 (Luật số 05/2007/QH12):
  * Phân loại sản phẩm hàng hóa: Nhóm 1 (an toàn) và Nhóm 2 (có khả năng gây mất an toàn).
  * Hàng hóa Nhóm 2 bắt buộc phải chứng nhận hợp quy, công bố hợp quy và gắn Dấu Hợp Quy CR trước khi lưu thông.
  * Kiểm tra chất lượng hàng hóa nhập khẩu và thu hồi sản phẩm khuyết tật.
- Luật Đo lường 2011 (Luật số 04/2011/QH13):
  * Phương tiện đo nhóm 2 (cân thương mại, cột đo xăng dầu, công tơ điện, đồng hồ nước, máy đo nồng độ cồn...).
  * Phê duyệt mẫu, kiểm định ban đầu, kiểm định định kỳ, tem niêm phong và kẹp chì kiểm định.
- Thông tư số 28/2012/TT-BKHCN & Thông tư số 02/2017/TT-BKHCN:
  * Quy định về công bố hợp chuẩn, công bố hợp quy và phương thức đánh giá sự phù hợp.
  * Quy chuẩn dấu hợp quy CR: Chiều cao tối thiểu 5mm, kèm mã tổ chức chứng nhận và số công bố.
- Nghị định số 119/2017/NĐ-CP & Nghị định số 126/2021/NĐ-CP:
  * Xử phạt vi phạm hành chính trong lĩnh vực tiêu chuẩn, đo lường và chất lượng sản phẩm hàng hóa.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


# Pre-populated canonical standards registry (TCVN & QCVN)
BUILTIN_STANDARDS = [
    {
        "code": "TCVN ISO 9001:2015",
        "title": "Hệ thống quản lý chất lượng - Các yêu cầu",
        "type": "TCVN",
        "category": "Quality Management",
        "is_mandatory": False,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "TCVN ISO 14001:2015",
        "title": "Hệ thống quản lý môi trường - Các yêu cầu",
        "type": "TCVN",
        "category": "Environment",
        "is_mandatory": False,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "TCVN ISO 22000:2018",
        "title": "Hệ thống quản lý an toàn thực phẩm - Yêu cầu đối với các tổ chức trong chuỗi thực phẩm",
        "type": "TCVN",
        "category": "Food Safety",
        "is_mandatory": False,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "TCVN ISO/IEC 27001:2022",
        "title": "Công nghệ thông tin - Các kỹ thuật an toàn - Hệ thống quản lý an toàn thông tin",
        "type": "TCVN",
        "category": "Information Security",
        "is_mandatory": False,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "QCVN 04:2009/BKHCN",
        "title": "Quy chuẩn kỹ thuật quốc gia về an toàn đối với thiết bị điện và điện tử",
        "type": "QCVN",
        "category": "Electrical Safety",
        "is_mandatory": True,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "QCVN 09:2012/BKHCN",
        "title": "Quy chuẩn kỹ thuật quốc gia về tương thích điện từ đối với thiết bị điện và điện tử gia dụng (EMC)",
        "type": "QCVN",
        "category": "EMC",
        "is_mandatory": True,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "QCVN 03:2019/BKHCN",
        "title": "Quy chuẩn kỹ thuật quốc gia về an toàn đồ chơi trẻ em",
        "type": "QCVN",
        "category": "Children Toys",
        "is_mandatory": True,
        "issuing_body": "Bộ Khoa học và Công nghệ",
    },
    {
        "code": "QCVN 16:2023/BXD",
        "title": "Quy chuẩn kỹ thuật quốc gia về sản phẩm, hàng hóa vật liệu xây dựng",
        "type": "QCVN",
        "category": "Building Materials",
        "is_mandatory": True,
        "issuing_body": "Bộ Xây dựng",
    },
    {
        "code": "QCVN 01:2017/BCT",
        "title": "Quy chuẩn kỹ thuật quốc gia về mức giới hạn hàm lượng formaldehyt và các amin thơm chuyển hóa từ thuốc nhuộm azo trong sản phẩm dệt may",
        "type": "QCVN",
        "category": "Textiles",
        "is_mandatory": True,
        "issuing_body": "Bộ Công Thương",
    },
    {
        "code": "QCVN 01-1:2018/BYT",
        "title": "Quy chuẩn kỹ thuật quốc gia về chất lượng nước sạch sử dụng cho mục đích sinh hoạt",
        "type": "QCVN",
        "category": "Clean Water",
        "is_mandatory": True,
        "issuing_body": "Bộ Y tế",
    },
]


class StandardsEngine:
    """Core engine for Vietnamese technical standards (TCVN/QCVN), CR mark, metrology & quality compliance."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "standards.db")
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
                CREATE TABLE IF NOT EXISTS standards_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    is_mandatory INTEGER NOT NULL,
                    issuing_body TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conformity_declarations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    declaration_code TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    manufacturer TEXT NOT NULL,
                    standard_code TEXT NOT NULL,
                    conformity_type TEXT NOT NULL,
                    test_report_no TEXT NOT NULL,
                    cert_body TEXT NOT NULL,
                    is_group_2 INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cr_mark_verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    verification_code TEXT UNIQUE NOT NULL,
                    product_name TEXT NOT NULL,
                    has_cr_mark INTEGER NOT NULL,
                    cr_height_mm REAL NOT NULL,
                    cert_body_code TEXT NOT NULL,
                    declaration_code TEXT NOT NULL,
                    is_group_2 INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    estimated_fine_vnd REAL NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS measuring_instruments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument_code TEXT UNIQUE NOT NULL,
                    instrument_name TEXT NOT NULL,
                    instrument_type TEXT NOT NULL,
                    serial_number TEXT NOT NULL,
                    last_verification_date TEXT NOT NULL,
                    validity_period_months INTEGER NOT NULL,
                    expiry_date TEXT NOT NULL,
                    seal_intact INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    estimated_fine_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS quality_inspections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    inspection_code TEXT UNIQUE NOT NULL,
                    batch_no TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    sample_size INTEGER NOT NULL,
                    defective_units INTEGER NOT NULL,
                    defect_rate_pct REAL NOT NULL,
                    inspection_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

            # Seed standard catalog if empty
            count = conn.execute("SELECT COUNT(*) FROM standards_catalog").fetchone()[0]
            if count == 0:
                now_str = datetime.datetime.now().isoformat()
                for s in BUILTIN_STANDARDS:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO standards_catalog
                        (code, title, type, category, is_mandatory, issuing_body, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (s["code"], s["title"], s["type"], s["category"], 1 if s["is_mandatory"] else 0, s["issuing_body"], now_str),
                    )

    # 1. Lookup Standard (TCVN / QCVN)
    def lookup_standard(self, query: str = "", standard_type: str = "ALL") -> List[Dict[str, Any]]:
        """Queries the national standards database for TCVN and QCVN regulations."""
        with self._get_connection() as conn:
            q = f"%{query.strip()}%"
            type_filter = standard_type.upper().strip()

            if type_filter in ["TCVN", "QCVN"]:
                cursor = conn.execute(
                    """
                    SELECT * FROM standards_catalog
                    WHERE (code LIKE ? OR title LIKE ? OR category LIKE ?)
                      AND type = ?
                    ORDER BY id ASC
                    """,
                    (q, q, q, type_filter),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM standards_catalog
                    WHERE code LIKE ? OR title LIKE ? OR category LIKE ?
                    ORDER BY id ASC
                    """,
                    (q, q, q),
                )

            return [dict(row) for row in cursor.fetchall()]

    # 2. Register Conformity Declaration (Công bố hợp chuẩn / hợp quy)
    def register_conformity_declaration(
        self,
        product_name: str,
        manufacturer: str,
        standard_code: str,
        conformity_type: str = "HOP_QUY",
        test_report_no: str = "TR-2026-001",
        cert_body: str = "QUATEST 3",
        is_group_2: bool = True,
    ) -> Dict[str, Any]:
        """Registers conformity declaration under Circular 28/2012/TT-BKHCN & Law 68/2006."""
        now = datetime.datetime.now()
        deficiencies = []
        c_type = conformity_type.upper().strip()

        # Rule 1: Group 2 products (potentially hazardous) MUST declare HOP_QUY with QCVN
        if is_group_2 and c_type != "HOP_QUY":
            deficiencies.append(
                "Sản phẩm Nhóm 2 bắt buộc phải chứng nhận và công bố HỢP QUY (QCVN), không được chỉ công bố hợp chuẩn tự nguyện"
            )

        # Rule 2: If standard is TCVN but claiming HOP_QUY, verify validity
        if "TCVN" in standard_code and c_type == "HOP_QUY":
            deficiencies.append(
                "Công bố HỢP QUY phải dựa trên Quy chuẩn kỹ thuật quốc gia (QCVN), không thể công bố hợp quy trực tiếp theo TCVN"
            )

        status = "REGISTERED_COMPLIANT" if len(deficiencies) == 0 else "DEFICIENT_REJECTED"
        seq = hashlib.md5(f"{product_name}:{manufacturer}:{standard_code}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        prefix = "DKHQ" if c_type == "HOP_QUY" else "DKHC"
        dec_code = f"{prefix}-{now.year}-{seq}"

        result = {
            "declaration_code": dec_code,
            "product_name": product_name,
            "manufacturer": manufacturer,
            "standard_code": standard_code,
            "conformity_type": c_type,
            "test_report_no": test_report_no,
            "cert_body": cert_body,
            "is_group_2": is_group_2,
            "status": status,
            "is_approved": status == "REGISTERED_COMPLIANT",
            "deficiencies": deficiencies,
            "statutory_basis": "Thông tư 28/2012/TT-BKHCN & Luật Tiêu chuẩn và Quy chuẩn kỹ thuật 2006",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO conformity_declarations
                (declaration_code, product_name, manufacturer, standard_code, conformity_type,
                 test_report_no, cert_body, is_group_2, status, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dec_code,
                    product_name,
                    manufacturer,
                    standard_code,
                    c_type,
                    test_report_no,
                    cert_body,
                    1 if is_group_2 else 0,
                    status,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 3. Verify CR Marking (Dấu Hợp Quy CR)
    def verify_cr_marking(
        self,
        product_name: str,
        has_cr_mark: bool = True,
        cr_height_mm: float = 6.0,
        cert_body_code: str = "VN01",
        declaration_code: str = "DKHQ-2026-001",
        is_group_2: bool = True,
    ) -> Dict[str, Any]:
        """Audits CR mark compliance under Circular 28/2012 & Decree 119/2017."""
        deficiencies = []
        fine_vnd = 0.0

        if is_group_2:
            if not has_cr_mark:
                deficiencies.append("Hàng hóa Nhóm 2 không gắn Dấu Hợp Quy CR trước khi lưu thông ra thị trường")
                fine_vnd += 25_000_000.0  # Decree 119/2017 & 126/2021: 20-30M VND
            else:
                # Minimum height for CR mark is 5.0 mm
                if cr_height_mm < 5.0:
                    deficiencies.append(f"Kích thước chiều cao dấu CR ({cr_height_mm} mm) nhỏ hơn mức tối thiểu 5.0 mm theo quy chuẩn")
                    fine_vnd += 15_000_000.0
                if not cert_body_code or cert_body_code.strip() == "":
                    deficiencies.append("Dấu CR thiếu mã số của tổ chức chứng nhận sự phù hợp được chỉ định")
                    fine_vnd += 10_000_000.0
                if not declaration_code or declaration_code.strip() == "":
                    deficiencies.append("Dấu CR không kèm thông tin số đăng ký bản công bố hợp quy")
                    fine_vnd += 10_000_000.0

        is_compliant = len(deficiencies) == 0
        status = "COMPLIANT_CR_MARK" if is_compliant else "VIOLATION_CR_MARK"
        now = datetime.datetime.now()
        seq = hashlib.md5(f"{product_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        ver_code = f"CR-VER-{now.year}-{seq}"

        result = {
            "verification_code": ver_code,
            "product_name": product_name,
            "is_group_2": is_group_2,
            "has_cr_mark": has_cr_mark,
            "cr_height_mm": cr_height_mm,
            "min_required_height_mm": 5.0,
            "cert_body_code": cert_body_code,
            "declaration_code": declaration_code,
            "status": status,
            "is_compliant": is_compliant,
            "estimated_fine_vnd": fine_vnd,
            "deficiencies": deficiencies,
            "legal_consequences": "Đình chỉ lưu thông, thu hồi sản phẩm và xử phạt vi phạm hành chính theo Nghị định 119/2017/NĐ-CP" if not is_compliant else "Đủ điều kiện lưu thông hợp pháp trên toàn quốc",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cr_mark_verifications
                (verification_code, product_name, has_cr_mark, cr_height_mm, cert_body_code,
                 declaration_code, is_group_2, status, estimated_fine_vnd, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    ver_code,
                    product_name,
                    1 if has_cr_mark else 0,
                    cr_height_mm,
                    cert_body_code,
                    declaration_code,
                    1 if is_group_2 else 0,
                    status,
                    fine_vnd,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. Audit Measuring Instrument (Kiểm định phương tiện đo nhóm 2)
    def audit_measuring_instrument(
        self,
        instrument_name: str,
        instrument_type: str,
        serial_number: str,
        last_verification_date: str,
        validity_period_months: int = 12,
        seal_intact: bool = True,
        check_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Audits verification validity and lead sealing of Group 2 measuring instruments under Law on Metrology 2011."""
        now = datetime.datetime.now()
        check_dt = datetime.datetime.fromisoformat(check_date) if check_date else now

        try:
            last_dt = datetime.datetime.strptime(last_verification_date, "%Y-%m-%d")
        except Exception:
            last_dt = now

        # Compute expiration date
        exp_year = last_dt.year + (last_dt.month + validity_period_months - 1) // 12
        exp_month = (last_dt.month + validity_period_months - 1) % 12 + 1
        exp_day = min(last_dt.day, 28)
        exp_dt = datetime.datetime(exp_year, exp_month, exp_day)
        exp_str = exp_dt.strftime("%Y-%m-%d")

        deficiencies = []
        fine_vnd = 0.0

        is_expired = check_dt > exp_dt
        if is_expired:
            deficiencies.append(f"Giấy chứng nhận/tem kiểm định đã hết hiệu lực từ ngày {exp_str}")
            fine_vnd += 15_000_000.0  # Decree 119/2017

        if not seal_intact:
            deficiencies.append("Kẹp chì niêm phong hoặc tem niêm phong kiểm định bị rách vỡ / có dấu hiệu tác động sai lệch")
            fine_vnd += 20_000_000.0

        if not seal_intact:
            status = "BROKEN_SEAL_VIOLATION"
        elif is_expired:
            status = "EXPIRED_VERIFICATION"
        else:
            status = "VERIFIED_VALID"

        seq = hashlib.md5(f"{instrument_name}:{serial_number}".encode("utf-8")).hexdigest()[:6].upper()
        inst_code = f"MET-{now.year}-{seq}"

        result = {
            "instrument_code": inst_code,
            "instrument_name": instrument_name,
            "instrument_type": instrument_type,
            "serial_number": serial_number,
            "last_verification_date": last_verification_date,
            "validity_period_months": validity_period_months,
            "expiry_date": exp_str,
            "seal_intact": seal_intact,
            "is_valid": status == "VERIFIED_VALID",
            "status": status,
            "estimated_fine_vnd": fine_vnd,
            "deficiencies": deficiencies,
            "legal_basis": "Điều 19 Luật Đo lường 2011 (quản lý phương tiện đo nhóm 2)",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO measuring_instruments
                (instrument_code, instrument_name, instrument_type, serial_number,
                 last_verification_date, validity_period_months, expiry_date, seal_intact,
                 status, estimated_fine_vnd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inst_code,
                    instrument_name,
                    instrument_type,
                    serial_number,
                    last_verification_date,
                    validity_period_months,
                    exp_str,
                    1 if seal_intact else 0,
                    status,
                    fine_vnd,
                    result["created_at"],
                ),
            )

        return result

    # 5. Record Quality Inspection (Kiểm tra chất lượng lô hàng & xuất nhập khẩu)
    def record_quality_inspection(
        self,
        batch_no: str,
        product_name: str,
        origin: str = "Việt Nam",
        sample_size: int = 100,
        defective_units: int = 0,
        inspection_type: str = "IMPORT_INSPECTION",
    ) -> Dict[str, Any]:
        """Audits state quality inspection for goods batch under Law on Product Quality 2007."""
        rate_pct = round((defective_units / sample_size) * 100.0, 2) if sample_size > 0 else 0.0
        now = datetime.datetime.now()

        # Defect tolerance: maximum 1% defect rate for critical parameters
        passed = defective_units == 0 or rate_pct <= 1.0
        status = "PASSED_INSPECTION" if passed else "FAILED_INSPECTION"
        decision = "THÔNG QUAN / CHO PHÉP LƯU THÔNG" if passed else "TẠM DỪNG LƯU THÔNG / TÁI XUẤT / THU HỒI TIÊU HỦY"

        seq = hashlib.md5(f"{batch_no}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        insp_code = f"KTCL-{now.year}-{seq}"

        result = {
            "inspection_code": insp_code,
            "batch_no": batch_no,
            "product_name": product_name,
            "origin": origin,
            "sample_size": sample_size,
            "defective_units": defective_units,
            "defect_rate_pct": rate_pct,
            "inspection_type": inspection_type,
            "status": status,
            "is_passed": passed,
            "decision": decision,
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO quality_inspections
                (inspection_code, batch_no, product_name, origin, sample_size,
                 defective_units, defect_rate_pct, inspection_type, status, decision, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    insp_code,
                    batch_no,
                    product_name,
                    origin,
                    sample_size,
                    defective_units,
                    rate_pct,
                    inspection_type,
                    status,
                    decision,
                    result["created_at"],
                ),
            )

        return result

    # 6. List Records
    def list_records(self, category: str = "standards", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored technical standards, declarations, CR markings, metrology or inspections."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["declarations", "hop_quy", "hop_chuan"]:
                cursor = conn.execute("SELECT * FROM conformity_declarations ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["cr_marks", "cr", "dau_cr"]:
                cursor = conn.execute("SELECT * FROM cr_mark_verifications ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["instruments", "metrology", "do_luong"]:
                cursor = conn.execute("SELECT * FROM measuring_instruments ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["inspections", "quality", "kiem_tra"]:
                cursor = conn.execute("SELECT * FROM quality_inspections ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM standards_catalog ORDER BY id ASC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 7. Telemetry & Summary Status
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide standards, metrology, and product quality telemetry."""
        with self._get_connection() as conn:
            total_standards = conn.execute("SELECT COUNT(*) FROM standards_catalog").fetchone()[0]
            total_declarations = conn.execute("SELECT COUNT(*) FROM conformity_declarations").fetchone()[0]
            compliant_declarations = conn.execute("SELECT COUNT(*) FROM conformity_declarations WHERE status = 'REGISTERED_COMPLIANT'").fetchone()[0]
            total_cr_checks = conn.execute("SELECT COUNT(*) FROM cr_mark_verifications").fetchone()[0]
            cr_violations = conn.execute("SELECT COUNT(*) FROM cr_mark_verifications WHERE status = 'VIOLATION_CR_MARK'").fetchone()[0]
            total_instruments = conn.execute("SELECT COUNT(*) FROM measuring_instruments").fetchone()[0]
            valid_instruments = conn.execute("SELECT COUNT(*) FROM measuring_instruments WHERE status = 'VERIFIED_VALID'").fetchone()[0]
            total_inspections = conn.execute("SELECT COUNT(*) FROM quality_inspections").fetchone()[0]

        dec_rate = round((compliant_declarations / total_declarations) * 100.0, 1) if total_declarations > 0 else 100.0
        inst_rate = round((valid_instruments / total_instruments) * 100.0, 1) if total_instruments > 0 else 100.0

        return {
            "status": "HEALTHY",
            "regulatory_framework": "Luật Tiêu chuẩn và Quy chuẩn kỹ thuật 2006, Luật Chất lượng sản phẩm hàng hóa 2007 & Luật Đo lường 2011",
            "total_standards_cataloged": total_standards,
            "total_conformity_declarations": total_declarations,
            "declaration_compliance_rate_pct": dec_rate,
            "total_cr_mark_verifications": total_cr_checks,
            "cr_mark_violations_detected": cr_violations,
            "total_measuring_instruments_audited": total_instruments,
            "instrument_verification_rate_pct": inst_rate,
            "total_quality_inspections": total_inspections,
            "timestamp": datetime.datetime.now().isoformat(),
        }
