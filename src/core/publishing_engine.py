"""
Vietnamese Publishing, Printing, Distribution & Legal Depository Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Xuất bản 2012 (Luật số 19/2012/QH13):
  * Điều 10: Những nội dung và hành vi bị cấm trong hoạt động xuất bản (xuyên tạc lịch sử, xâm hại an ninh quốc gia, bạo lực, đồi trụy).
  * Điều 22: Điều kiện thành lập nhà xuất bản (vốn điều lệ >= 5 tỷ VND, trụ sở >= 200 m², chức danh tổng giám đốc/tổng biên tập).
  * Điều 25, 26: Đăng ký kế hoạch xuất bản, cấp mã số chuẩn quốc tế cho sách (ISBN) và quyết định xuất bản.
  * Điều 28: Nộp lưu chiểu xuất bản phẩm (nộp ít nhất 10 ngày trước khi phát hành, nộp 03 bản cho cơ quan quản lý và 02 bản cho Thư viện Quốc gia Việt Nam).
- Nghị định số 195/2013/NĐ-CP & Nghị định số 119/2020/NĐ-CP:
  * Điều kiện hoạt động in xuất bản phẩm (thiết bị, an ninh trật tự, giám đốc phụ trách chuyên ngành in).
  * Hoạt động xuất bản, phát hành xuất bản phẩm điện tử (máy chủ tại Việt Nam, biện pháp kỹ thuật chống sao chép trái phép DRM, chữ ký số).
- Nghị định số 119/2020/NĐ-CP & Nghị định số 14/2022/NĐ-CP: Xử phạt vi phạm hành chính trong hoạt động xuất bản và phát hành.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional


class PublishingEngine:
    """Core engine for Vietnamese publishing, printing, ISBN allocation, and legal depository compliance."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "publishing.db")
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
                CREATE TABLE IF NOT EXISTS publishers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    publisher_code TEXT UNIQUE NOT NULL,
                    publisher_name TEXT NOT NULL,
                    managing_agency TEXT NOT NULL,
                    charter_capital_vnd REAL NOT NULL,
                    office_area_sqm REAL NOT NULL,
                    director_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS publications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isbn TEXT UNIQUE NOT NULL,
                    publisher_code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    author_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    copies_count INTEGER NOT NULL,
                    price_vnd REAL NOT NULL,
                    decision_number TEXT NOT NULL,
                    is_ebook INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS legal_deposits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deposit_code TEXT UNIQUE NOT NULL,
                    isbn TEXT NOT NULL,
                    copies_deposited INTEGER NOT NULL,
                    national_library_copies INTEGER NOT NULL,
                    submission_date TEXT NOT NULL,
                    embargo_until_date TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS printing_facilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    facility_code TEXT UNIQUE NOT NULL,
                    facility_name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    has_security_clearance INTEGER NOT NULL,
                    offset_presses_count INTEGER NOT NULL,
                    manager_qualified INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. License Publisher (Luật Xuất bản Điều 22)
    def license_publisher(
        self,
        name: str,
        managing_agency: str,
        charter_capital_vnd: float = 5_000_000_000.0,
        office_area_sqm: float = 220.0,
        director_name: str = "Nguyễn Văn Trưởng",
    ) -> Dict[str, Any]:
        """Audits statutory conditions for establishing a publishing house under Article 22 Law 19/2012/QH13."""
        deficiencies = []
        # Min capital: 5 billion VND
        min_capital = 5_000_000_000.0
        # Min office area: 200 sqm
        min_area = 200.0

        if charter_capital_vnd < min_capital:
            deficiencies.append(f"Vốn điều lệ ({charter_capital_vnd:,.0f} VND) thấp hơn mức tối thiểu 5,000,000,000 VND")

        if office_area_sqm < min_area:
            deficiencies.append(f"Diện tích trụ sở làm việc ({office_area_sqm} m²) thấp hơn mức tối thiểu 200 m²")

        approved = len(deficiencies) == 0
        now = datetime.datetime.now()
        seq = hashlib.md5(f"{name}:{managing_agency}".encode("utf-8")).hexdigest()[:5].upper()
        pub_code = f"GP-NXB-{now.year}-{seq}"

        result = {
            "publisher_code": pub_code,
            "publisher_name": name,
            "managing_agency": managing_agency,
            "charter_capital_vnd": charter_capital_vnd,
            "min_required_capital_vnd": min_capital,
            "office_area_sqm": office_area_sqm,
            "min_required_area_sqm": min_area,
            "director_name": director_name,
            "status": "LICENSED" if approved else "REJECTED",
            "deficiencies": deficiencies,
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO publishers
                (publisher_code, publisher_name, managing_agency, charter_capital_vnd,
                 office_area_sqm, director_name, status, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pub_code,
                    name,
                    managing_agency,
                    charter_capital_vnd,
                    office_area_sqm,
                    director_name,
                    result["status"],
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # Helper: Generate Valid ISBN-13 (EAN-13 Checksum)
    def _generate_isbn13(self, seed: str) -> str:
        """Generates a mathematically valid ISBN-13 with checksum under Vietnam group prefix (978-604-...)."""
        # Prefix 978-604 (Vietnam) + 6 random/hashed digits + 1 check digit
        hash_digits = re.sub(r"\D", "", hashlib.sha256(seed.encode("utf-8")).hexdigest())[:6].zfill(6)
        base12 = f"978604{hash_digits}"

        # Calculate EAN-13 checksum: alternately multiply by 1 and 3
        s = 0
        for i, ch in enumerate(base12):
            w = 1 if i % 2 == 0 else 3
            s += int(ch) * w
        remainder = s % 10
        check_digit = 0 if remainder == 0 else 10 - remainder

        full_isbn = f"978-604-{hash_digits[:3]}-{hash_digits[3:]}-{check_digit}"
        return full_isbn

    # 2. Register Publication & Allocate ISBN (Luật Xuất bản Điều 25, 26)
    def register_publication(
        self,
        publisher_code: str,
        title: str,
        author_name: str,
        category: str = "literature",
        copies_count: int = 1000,
        price_vnd: float = 120000.0,
        is_ebook: bool = False,
    ) -> Dict[str, Any]:
        """Registers a publication plan, allocates ISBN, and records publishing decision."""
        now = datetime.datetime.now()
        year = now.year
        isbn = self._generate_isbn13(f"{publisher_code}:{title}:{author_name}:{now.timestamp()}")

        seq_dec = hashlib.md5(f"{title}:{year}".encode("utf-8")).hexdigest()[:4].upper()
        decision_number = f"QĐXB-{seq_dec}/{year}/NXB"

        result = {
            "isbn": isbn,
            "publisher_code": publisher_code,
            "title": title,
            "author_name": author_name,
            "category": category,
            "copies_count": copies_count,
            "price_vnd": price_vnd,
            "decision_number": decision_number,
            "is_ebook": is_ebook,
            "status": "APPROVED",
            "statutory_authority": "Cục Xuất bản, In và Phát hành - Bộ Thông tin và Truyền thông",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO publications
                (isbn, publisher_code, title, author_name, category, copies_count,
                 price_vnd, decision_number, is_ebook, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    isbn,
                    publisher_code,
                    title,
                    author_name,
                    category,
                    copies_count,
                    price_vnd,
                    decision_number,
                    1 if is_ebook else 0,
                    "APPROVED",
                    result["created_at"],
                ),
            )

        return result

    # 3. Submit Legal Deposit (Nộp Lưu Chiểu - Luật Xuất bản Điều 28)
    def submit_legal_deposit(
        self,
        isbn: str,
        copies_deposited: int = 3,
        national_library_copies: int = 2,
        submission_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Registers statutory legal deposit and computes the 10-day embargo release date under Article 28."""
        now = datetime.datetime.now()
        if submission_date is None:
            sub_dt = now
            sub_str = sub_dt.strftime("%Y-%m-%d")
        else:
            sub_str = submission_date
            try:
                sub_dt = datetime.datetime.fromisoformat(submission_date)
            except Exception:
                sub_dt = now

        # 10 days statutory holding period before public distribution
        embargo_dt = sub_dt + datetime.timedelta(days=10)
        embargo_str = embargo_dt.strftime("%Y-%m-%d")

        deficiencies = []
        if copies_deposited < 3:
            deficiencies.append(f"Số bản nộp lưu chiểu ({copies_deposited} bản) thấp hơn mức quy định tối thiểu 03 bản cho cơ quan quản lý")
        if national_library_copies < 2:
            deficiencies.append(f"Số bản nộp Thư viện Quốc gia ({national_library_copies} bản) thấp hơn quy định 02 bản")

        deposit_code = f"LC-{sub_dt.year}-{hashlib.md5(f'{isbn}:{sub_str}'.encode('utf-8')).hexdigest()[:6].upper()}"
        status = "DEPOSITED" if len(deficiencies) == 0 else "DEFICIENT"

        result = {
            "deposit_code": deposit_code,
            "isbn": isbn,
            "copies_deposited": copies_deposited,
            "national_library_copies": national_library_copies,
            "submission_date": sub_str,
            "embargo_until_date": embargo_str,
            "embargo_days": 10,
            "status": status,
            "deficiencies": deficiencies,
            "legal_basis": "Điều 28 Luật Xuất bản 2012 (nộp lưu chiểu ít nhất 10 ngày trước khi phát hành)",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO legal_deposits
                (deposit_code, isbn, copies_deposited, national_library_copies,
                 submission_date, embargo_until_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    deposit_code,
                    isbn,
                    copies_deposited,
                    national_library_copies,
                    sub_str,
                    embargo_str,
                    status,
                    result["created_at"],
                ),
            )

        return result

    # 4. Audit Release Eligibility (Kiểm tra điều kiện phát hành sau 10 ngày lưu chiểu)
    def audit_release_eligibility(
        self,
        deposit_code: str,
        current_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verifies if the 10-day statutory holding period has elapsed without state objections."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM legal_deposits WHERE deposit_code = ?", (deposit_code,)).fetchone()
            if not row:
                raise ValueError(f"Không tìm thấy hồ sơ nộp lưu chiểu với mã: {deposit_code}")

            record = dict(row)

        now = datetime.datetime.now()
        curr_dt = datetime.datetime.fromisoformat(current_date) if current_date else now

        embargo_dt = datetime.datetime.strptime(record["embargo_until_date"], "%Y-%m-%d")
        diff_days = (curr_dt.date() - embargo_dt.date()).days

        if diff_days >= 0:
            status = "ELIGIBLE_FOR_DISTRIBUTION"
            msg = "Đã hoàn thành thời hạn lưu chiểu 10 ngày. Xuất bản phẩm được phép phát hành hợp pháp toàn quốc."
            can_release = True
        else:
            status = "UNDER_10_DAY_EMBARGO"
            msg = f"Đang trong thời hạn đọc duyệt lưu chiểu 10 ngày (còn {-diff_days} ngày). Nghiêm cấm phát hành sớm theo Điều 28 Luật Xuất bản."
            can_release = False

        return {
            "deposit_code": deposit_code,
            "isbn": record["isbn"],
            "submission_date": record["submission_date"],
            "embargo_until_date": record["embargo_until_date"],
            "can_release": can_release,
            "status": status,
            "evaluation": msg,
            "checked_at": curr_dt.isoformat(),
        }

    # 5. Audit Printing Facility (Nghị định 195/2013/NĐ-CP Điều 11)
    def audit_printing_facility(
        self,
        facility_name: str,
        address: str,
        has_security_clearance: bool = True,
        offset_presses_count: int = 2,
        manager_qualified: bool = True,
    ) -> Dict[str, Any]:
        """Audits printing facility licensing conditions under Decree 195/2013/NĐ-CP."""
        deficiencies = []
        if not has_security_clearance:
            deficiencies.append("Chưa có Giấy chứng nhận đủ điều kiện về an ninh, trật tự của cơ quan Công an")

        if offset_presses_count < 1:
            deficiencies.append("Không có thiết bị in ấn xuất bản phẩm đáp ứng quy chuẩn kỹ thuật")

        if not manager_qualified:
            deficiencies.append("Người đứng đầu cơ sở in chưa có bằng đại học chuyên ngành in hoặc chứng chỉ bồi dưỡng quản lý in")

        compliant = len(deficiencies) == 0
        fac_code = f"PRN-{hashlib.md5(f'{facility_name}:{address}'.encode('utf-8')).hexdigest()[:6].upper()}"

        result = {
            "facility_code": fac_code,
            "facility_name": facility_name,
            "address": address,
            "has_security_clearance": has_security_clearance,
            "offset_presses_count": offset_presses_count,
            "manager_qualified": manager_qualified,
            "status": "COMPLIANT" if compliant else "NON_COMPLIANT",
            "deficiencies": deficiencies,
            "created_at": datetime.datetime.now().isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO printing_facilities
                (facility_code, facility_name, address, has_security_clearance,
                 offset_presses_count, manager_qualified, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    fac_code,
                    facility_name,
                    address,
                    1 if has_security_clearance else 0,
                    offset_presses_count,
                    1 if manager_qualified else 0,
                    result["status"],
                    result["created_at"],
                ),
            )

        return result

    # 6. List Records
    def list_records(self, category: str = "publications", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries database records across publishing domains."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["publishers", "nxb"]:
                cursor = conn.execute("SELECT * FROM publishers ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["deposits", "luu_chieu"]:
                cursor = conn.execute("SELECT * FROM legal_deposits ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["printing", "printers"]:
                cursor = conn.execute("SELECT * FROM printing_facilities ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM publications ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 7. Summary Status Telemetry
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide publishing, ISBN, and legal deposit telemetry."""
        with self._get_connection() as conn:
            total_publishers = conn.execute("SELECT COUNT(*) FROM publishers").fetchone()[0]
            licensed_publishers = conn.execute("SELECT COUNT(*) FROM publishers WHERE status = 'LICENSED'").fetchone()[0]
            total_publications = conn.execute("SELECT COUNT(*) FROM publications").fetchone()[0]
            total_deposits = conn.execute("SELECT COUNT(*) FROM legal_deposits").fetchone()[0]
            deficient_deposits = conn.execute("SELECT COUNT(*) FROM legal_deposits WHERE status = 'DEFICIENT'").fetchone()[0]
            total_printers = conn.execute("SELECT COUNT(*) FROM printing_facilities").fetchone()[0]

        compliance_rate_pct = round((1.0 - (deficient_deposits / total_deposits)) * 100.0, 1) if total_deposits > 0 else 100.0

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Xuất bản 2012 (Luật số 19/2012/QH13) & Nghị định 195/2013/NĐ-CP",
            "total_publishers": total_publishers,
            "licensed_publishers": licensed_publishers,
            "total_isbn_publications": total_publications,
            "total_legal_deposits": total_deposits,
            "deposit_compliance_rate_pct": compliance_rate_pct,
            "total_printing_facilities": total_printers,
            "timestamp": datetime.datetime.now().isoformat(),
        }

    # 8. Parity & Convenience Methods
    def register_publisher(
        self,
        publisher_name: str,
        director_name: str = "Nguyễn Văn An",
        charter_capital_vnd: float = 5_000_000_000.0,
        office_area_sqm: float = 200.0,
        headquarters_location: str = "Hà Nội",
        has_qualified_editor_in_chief: bool = True,
        managing_agency: str = "Hội Nhà văn Việt Nam",
    ) -> Dict[str, Any]:
        """Convenience wrapper for publisher licensing under Law 19/2012 Art. 22."""
        res = self.license_publisher(
            name=publisher_name,
            managing_agency=managing_agency,
            charter_capital_vnd=charter_capital_vnd,
            office_area_sqm=office_area_sqm,
            director_name=director_name,
        )
        if not has_qualified_editor_in_chief:
            res["deficiencies"].append("Tổng biên tập chưa đạt tiêu chuẩn nghiệp vụ")
            res["status"] = "DEFICIENT_CONDITIONS"
        elif res["status"] == "LICENSED":
            res["status"] = "LICENSED_APPROVED"
        else:
            res["status"] = "DEFICIENT_CONDITIONS"
        res["license_granted"] = (res["status"] == "LICENSED_APPROVED")
        return res

    def allocate_isbn(
        self,
        book_title: str,
        publisher_name: str = "Nhà xuất bản Tri Thức Mới",
        author_name: str = "Lê Minh Tuấn",
        genre: str = "science",
        publication_year: int = 2026,
    ) -> Dict[str, Any]:
        """Convenience wrapper for ISBN-13 allocation and publication registration."""
        res = self.register_publication(
            publisher_code=publisher_name,
            title=book_title,
            author_name=author_name,
            category=genre,
        )
        res["status"] = "ALLOCATED"
        return res

    def record_legal_depository(
        self,
        publisher_id: str,
        isbn: str,
        state_copies: int = 3,
        national_library_copies: int = 2,
        is_digital: bool = False,
    ) -> Dict[str, Any]:
        """Convenience wrapper for recording statutory legal deposit under Article 28."""
        res = self.submit_legal_deposit(
            isbn=isbn,
            copies_deposited=state_copies,
            national_library_copies=national_library_copies,
        )
        res["is_compliant"] = (res["status"] == "DEPOSITED")
        res["status"] = "DEPOSITED_COMPLIANT" if res["is_compliant"] else "DEFICIENT_COPIES_REJECTED"
        res["embargo_period_days"] = res.get("embargo_days", 10)
        return res

    def audit_release_decision(
        self,
        publisher_id: str,
        isbn: str,
        print_run: int = 3000,
        retail_price_vnd: float = 120_000.0,
        days_since_deposit: int = 11,
    ) -> Dict[str, Any]:
        """Convenience wrapper for checking legal deposit and 10-day reading embargo."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM legal_deposits WHERE isbn = ? ORDER BY id DESC LIMIT 1",
                (isbn,),
            ).fetchone()

        if not row:
            return {
                "isbn": isbn,
                "publisher_id": publisher_id,
                "status": "ILLEGAL_NO_LEGAL_DEPOSIT",
                "is_cleared": False,
                "estimated_fine_vnd": 20_000_000.0,
                "evaluation": "Chưa thực hiện nộp lưu chiểu xuất bản phẩm theo Điều 28 Luật Xuất bản.",
            }

        deposit = dict(row)
        if days_since_deposit < 10:
            return {
                "deposit_code": deposit["deposit_code"],
                "isbn": isbn,
                "days_since_deposit": days_since_deposit,
                "status": "UNDER_10_DAY_EMBARGO",
                "is_cleared": False,
                "estimated_fine_vnd": 15_000_000.0,
                "evaluation": f"Đang trong thời hạn đọc duyệt lưu chiểu 10 ngày (mới được {days_since_deposit} ngày). Vi phạm Điều 28.",
            }

        return {
            "deposit_code": deposit["deposit_code"],
            "isbn": isbn,
            "days_since_deposit": days_since_deposit,
            "status": "AUTHORIZED_FOR_RELEASE",
            "is_cleared": True,
            "estimated_fine_vnd": 0.0,
            "evaluation": "Đã hoàn thành thời hạn lưu chiểu 10 ngày. Xuất bản phẩm được phép phát hành hợp pháp.",
        }

    def review_printing_facility(
        self,
        facility_name: str,
        press_types: str = "offset,digital",
        has_security_clearance: bool = True,
        has_certified_print_manager: bool = True,
        address: str = "KCN Tân Bình, TP. Hồ Chí Minh",
    ) -> Dict[str, Any]:
        """Convenience wrapper for auditing printing facility compliance."""
        res = self.audit_printing_facility(
            facility_name=facility_name,
            address=address,
            has_security_clearance=has_security_clearance,
            offset_presses_count=2,
            manager_qualified=has_certified_print_manager,
        )
        res["is_licensed"] = (res["status"] == "COMPLIANT")
        res["status"] = "COMPLIANT_LICENSED" if res["is_licensed"] else "NON_COMPLIANT_REJECTED"
        return res

    def get_publishing_dashboard(self) -> Dict[str, Any]:
        """Convenience wrapper for dashboard status telemetry."""
        res = self.get_status()
        res["total_isbns_allocated"] = res.get("total_isbn_publications", 0)
        return res
