"""
Vietnamese Price Management, Anti-Price Gouging, Valuation & Public Asset Appraisal Engine.
Pure Python standard library implementation adhering to tests/test_core_boundary.py.

Statutory Framework:
- Luật Giá 2023 (Luật số 16/2023/QH15, có hiệu lực từ 01/07/2024):
  * Danh mục hàng hóa, dịch vụ bình ổn giá (Price Stabilization): Xăng dầu, điện sinh hoạt, sữa cho trẻ em dưới 06 tuổi, thóc gạo tẻ, phân bón, thuốc phòng chữa bệnh.
  * Biện pháp quản lý, điều tiết giá: Định giá của Nhà nước (khung giá, giá tối đa, giá tối thiểu), kê khai giá và niêm yết giá.
  * Quy định về Niêm yết giá (Điều 29): Niêm yết bằng Đồng Việt Nam, rõ ràng, không gây nhầm lẫn; nghiêm cấm bán cao hơn giá niêm yết.
  * Hành vi bị nghiêm cấm (Điều 7): Đầu cơ găm hàng, lợi dụng thiên tai dịch bệnh tăng giá bất hợp lý (Anti-Price Gouging).
- Chuẩn mực Thẩm định giá Việt Nam (TĐGVN) & Nghị định số 87/2024/NĐ-CP:
  * Doanh nghiệp thẩm định giá: Tối thiểu 03 Thẩm định viên về giá, vốn điều lệ >= 5 tỷ VND, bảo hiểm nghề nghiệp.
  * Chứng thư thẩm định giá (Valuation Certificate) và Báo cáo kết quả thẩm định giá.
  * Phương pháp thẩm định: So sánh (Market Comparison), Chi phí (Cost Approach), Thu nhập (Income/DCF).
- Nghị định số 109/2013/NĐ-CP & Nghị định số 49/2016/NĐ-CP:
  * Xử phạt vi phạm hành chính trong quản lý giá, bán cao hơn giá niêm yết, không kê khai giá và tăng giá bất hợp lý.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional


class PriceEngine:
    """Core engine for Vietnamese Price Surveillance, Price Stabilization, Anti-Gouging and Valuation Compliance."""

    STABILIZED_GOODS: List[str] = [
        "XĂNG DẦU",
        "ĐIỆN SINH HOẠT",
        "KHÍ DẦU MỎ HÓA LỎNG (LPG)",
        "SỮA CHO TRẺ EM DƯỚI 06 TUỔI",
        "THÓC, GẠO TẺ",
        "PHÂN BÓN ĐẠM, URE, NPK",
        "THUỐC BẢO VỆ THỰC VẬT",
        "THUỐC PHÒNG VÀ CHỮA BỆNH CHO NGƯỜI",
        "MUỐI ĂN",
        "ĐƯỜNG ĂN",
    ]

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.join(os.getcwd(), ".mekong")
            os.makedirs(base_dir, exist_ok=True)
            self.db_path = os.path.join(base_dir, "price.db")
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
                CREATE TABLE IF NOT EXISTS price_declarations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    declaration_code TEXT UNIQUE NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    old_price_vnd REAL NOT NULL,
                    declared_price_vnd REAL NOT NULL,
                    change_pct REAL NOT NULL,
                    is_stabilized_good INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    effective_date TEXT NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS price_postings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_code TEXT UNIQUE NOT NULL,
                    store_name TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    listed_price_vnd REAL NOT NULL,
                    actual_selling_price_vnd REAL NOT NULL,
                    is_posted_clearly INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    status TEXT NOT NULL,
                    estimated_fine_vnd REAL NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS valuation_certificates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    certificate_code TEXT UNIQUE NOT NULL,
                    appraisal_firm TEXT NOT NULL,
                    client_name TEXT NOT NULL,
                    asset_description TEXT NOT NULL,
                    appraised_value_vnd REAL NOT NULL,
                    valuation_method TEXT NOT NULL,
                    lead_appraiser TEXT NOT NULL,
                    licensed_appraisers_count INTEGER NOT NULL,
                    has_firm_insurance INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    is_valid INTEGER NOT NULL,
                    deficiencies TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS anti_gouging_audits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_code TEXT UNIQUE NOT NULL,
                    business_name TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    base_price_vnd REAL NOT NULL,
                    gouged_price_vnd REAL NOT NULL,
                    units_sold INTEGER NOT NULL,
                    illicit_profit_vnd REAL NOT NULL,
                    penalty_fine_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    # 1. Register / Audit Price Declaration (Kê khai giá theo Luật Giá 2023)
    def declare_price(
        self,
        enterprise_name: str,
        product_name: str,
        unit: str,
        old_price_vnd: float,
        declared_price_vnd: float,
        effective_date: Optional[str] = None,
        is_stabilized_commodity: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Registers and evaluates price declaration under Article 28 Law on Prices 2023."""
        now = datetime.datetime.now()
        eff_date = effective_date or now.strftime("%Y-%m-%d")
        deficiencies = []

        # Check if product belongs to the statutory price stabilization catalog
        prod_upper = product_name.upper().strip()
        is_stabilized = (
            is_stabilized_commodity
            if is_stabilized_commodity is not None
            else any(item in prod_upper for item in self.STABILIZED_GOODS)
        )

        change_pct = round(((declared_price_vnd - old_price_vnd) / old_price_vnd) * 100.0, 2) if old_price_vnd > 0 else 0.0

        if is_stabilized and change_pct > 15.0:
            deficiencies.append(
                f"Hàng hóa thuộc danh mục bình ổn giá tăng {change_pct}%, vượt ngưỡng cho phép 15% mà không có báo cáo giải trình chi phí hợp lý"
            )

        if declared_price_vnd <= 0:
            deficiencies.append("Mức giá kê khai không hợp lệ (nhỏ hơn hoặc bằng 0 VND)")

        is_valid = len(deficiencies) == 0
        status = "DECLARATION_ACCEPTED" if is_valid else "DECLARATION_FLAGGED"
        seq = hashlib.md5(f"{enterprise_name}:{product_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        dec_code = f"KKG-{now.year}-{seq}"

        result = {
            "declaration_code": dec_code,
            "enterprise_name": enterprise_name,
            "product_name": product_name,
            "unit": unit,
            "old_price_vnd": old_price_vnd,
            "declared_price_vnd": declared_price_vnd,
            "change_pct": change_pct,
            "is_stabilized_good": is_stabilized,
            "status": status,
            "effective_date": eff_date,
            "is_approved": is_valid,
            "deficiencies": deficiencies,
            "statutory_basis": "Điều 28 Luật Giá 2023 & Nghị định 87/2024/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO price_declarations
                (declaration_code, enterprise_name, product_name, unit, old_price_vnd,
                 declared_price_vnd, change_pct, is_stabilized_good, status, effective_date,
                 deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    dec_code,
                    enterprise_name,
                    product_name,
                    unit,
                    old_price_vnd,
                    declared_price_vnd,
                    change_pct,
                    1 if is_stabilized else 0,
                    status,
                    eff_date,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 2. Audit Price Posting / Listing Compliance (Niêm yết giá theo Điều 29 Luật Giá 2023)
    def audit_price_posting(
        self,
        store_name: str,
        product_name: str,
        listed_price_vnd: float,
        actual_selling_price_vnd: float,
        is_posted_clearly: bool = True,
        currency: str = "VND",
    ) -> Dict[str, Any]:
        """Audits retail price posting compliance under Article 29 Law on Prices and Decree 109/2013."""
        now = datetime.datetime.now()
        fine_vnd = 0.0
        curr = currency.upper().strip()

        if curr != "VND":
            status = "ILLEGAL_FOREIGN_CURRENCY_LISTING"
            fine_vnd += 40_000_000.0  # Phạt niêm yết bằng ngoại tệ trái phép (Pháp lệnh ngoại hối)
        elif not is_posted_clearly:
            status = "UNLISTED_PRICE_VIOLATION"
            fine_vnd += 1_000_000.0  # Phạt không niêm yết giá rõ ràng (500k-1M)
        elif actual_selling_price_vnd > listed_price_vnd:
            status = "SELLING_ABOVE_LISTED_PRICE"
            fine_vnd += 25_000_000.0  # Phạt bán cao hơn giá niêm yết (20M-30M theo NĐ 109/2013)
        else:
            status = "COMPLIANT_POSTING"

        seq = hashlib.md5(f"{store_name}:{product_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        audit_code = f"NYG-{now.year}-{seq}"

        result = {
            "audit_code": audit_code,
            "store_name": store_name,
            "product_name": product_name,
            "listed_price_vnd": listed_price_vnd,
            "actual_selling_price_vnd": actual_selling_price_vnd,
            "is_posted_clearly": is_posted_clearly,
            "currency": curr,
            "status": status,
            "is_compliant": status == "COMPLIANT_POSTING",
            "estimated_fine_vnd": fine_vnd,
            "statutory_basis": "Điều 29 Luật Giá 2023 & Nghị định 109/2013/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO price_postings
                (audit_code, store_name, product_name, listed_price_vnd, actual_selling_price_vnd,
                 is_posted_clearly, currency, status, estimated_fine_vnd, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_code,
                    store_name,
                    product_name,
                    listed_price_vnd,
                    actual_selling_price_vnd,
                    1 if is_posted_clearly else 0,
                    curr,
                    status,
                    fine_vnd,
                    result["created_at"],
                ),
            )

        return result

    # 3. Issue Statutory Valuation Certificate (Chứng thư thẩm định giá theo Chuẩn mực TĐGVN)
    def issue_valuation_certificate(
        self,
        appraisal_firm: str,
        client_name: str,
        asset_description: str,
        appraised_value_vnd: float,
        valuation_method: str = "MARKET_COMPARISON",
        lead_appraiser: str = "Thẩm định viên Lê Quốc Doanh (Thẻ TĐV số 8899/TĐG)",
        licensed_appraisers_count: int = 4,
        has_firm_insurance: bool = True,
    ) -> Dict[str, Any]:
        """Issues Valuation Certificate under Vietnamese Valuation Standards (TĐGVN) and Law on Prices."""
        now = datetime.datetime.now()
        method = valuation_method.upper().strip()
        deficiencies = []

        if licensed_appraisers_count < 3:
            deficiencies.append(
                f"Doanh nghiệp thẩm định giá chỉ có {licensed_appraisers_count} thẩm định viên về giá (Yêu cầu tối thiểu 03 TĐV theo Điều 49 Luật Giá 2023)"
            )

        if not has_firm_insurance:
            deficiencies.append("Doanh nghiệp chưa mua bảo hiểm trách nhiệm nghề nghiệp hoặc trích lập quỹ dự phòng rủi ro nghề nghiệp")

        if appraised_value_vnd <= 0:
            deficiencies.append("Giá trị tài sản thẩm định phải lớn hơn 0 VND")

        is_valid = len(deficiencies) == 0
        status = "CERTIFIED_VALID" if is_valid else "CERTIFICATE_REVOKED"
        seq = hashlib.md5(f"{appraisal_firm}:{client_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        cert_code = f"CTTDG-{now.year}-{seq}"

        result = {
            "certificate_code": cert_code,
            "appraisal_firm": appraisal_firm,
            "client_name": client_name,
            "asset_description": asset_description,
            "appraised_value_vnd": appraised_value_vnd,
            "valuation_method": method,
            "lead_appraiser": lead_appraiser,
            "licensed_appraisers_count": licensed_appraisers_count,
            "has_firm_insurance": has_firm_insurance,
            "is_valid": is_valid,
            "status": status,
            "deficiencies": deficiencies,
            "validity_period_months": 6,
            "statutory_basis": "Chuẩn mực Thẩm định giá Việt Nam & Điều 49-55 Luật Giá 2023",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO valuation_certificates
                (certificate_code, appraisal_firm, client_name, asset_description, appraised_value_vnd,
                 valuation_method, lead_appraiser, licensed_appraisers_count, has_firm_insurance,
                 status, is_valid, deficiencies, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cert_code,
                    appraisal_firm,
                    client_name,
                    asset_description,
                    appraised_value_vnd,
                    method,
                    lead_appraiser,
                    licensed_appraisers_count,
                    1 if has_firm_insurance else 0,
                    status,
                    1 if is_valid else 0,
                    json.dumps(deficiencies, ensure_ascii=False),
                    result["created_at"],
                ),
            )

        return result

    # 4. Anti-Price Gouging Audit (Kiểm tra tăng giá bất hợp lý, găm hàng)
    def check_price_gouging(
        self,
        business_name: str,
        product_name: str,
        base_price_vnd: float,
        gouged_price_vnd: float,
        units_sold: int = 1000,
        is_crisis_period: bool = True,
    ) -> Dict[str, Any]:
        """Audits price gouging during crisis/disaster and calculates illicit profit & fines."""
        now = datetime.datetime.now()
        increase_pct = round(((gouged_price_vnd - base_price_vnd) / base_price_vnd) * 100.0, 2) if base_price_vnd > 0 else 0.0

        # In crisis/disaster period, price surge > 20% is flagged as price gouging
        if is_crisis_period and increase_pct > 20.0:
            status = "PRICE_GOUGING_CONFIRMED"
            price_diff = max(0.0, gouged_price_vnd - (base_price_vnd * 1.20))
            illicit_profit = price_diff * units_sold
            penalty_fine = min(100_000_000.0, max(50_000_000.0, illicit_profit * 0.5))
            legal_conclusion = (
                f"HÀNH VI TĂNG GIÁ BẤT HỢP LÝ: Giá tăng {increase_pct}% trong thời gian khủng hoảng/dịch bệnh/bình ổn giá; "
                f"buộc nộp lại số tiền thu lợi bất chính {illicit_profit:,.0f} VND và xử phạt {penalty_fine:,.0f} VND"
            )
        else:
            status = "PRICE_NORMAL"
            illicit_profit = 0.0
            penalty_fine = 0.0
            legal_conclusion = "Mức biến động giá nằm trong biên độ chấp nhận được của thị trường"

        seq = hashlib.md5(f"{business_name}:{product_name}:{now.timestamp()}".encode("utf-8")).hexdigest()[:6].upper()
        audit_code = f"GOUGE-{now.year}-{seq}"

        result = {
            "audit_code": audit_code,
            "business_name": business_name,
            "product_name": product_name,
            "base_price_vnd": base_price_vnd,
            "gouged_price_vnd": gouged_price_vnd,
            "increase_pct": increase_pct,
            "units_sold": units_sold,
            "illicit_profit_vnd": illicit_profit,
            "penalty_fine_vnd": penalty_fine,
            "is_crisis_period": is_crisis_period,
            "status": status,
            "legal_conclusion": legal_conclusion,
            "statutory_basis": "Điều 7 Luật Giá 2023 & Điều 10 Nghị định 109/2013/NĐ-CP",
            "created_at": now.isoformat(),
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO anti_gouging_audits
                (audit_code, business_name, product_name, base_price_vnd, gouged_price_vnd,
                 units_sold, illicit_profit_vnd, penalty_fine_vnd, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_code,
                    business_name,
                    product_name,
                    base_price_vnd,
                    gouged_price_vnd,
                    units_sold,
                    illicit_profit,
                    penalty_fine,
                    status,
                    result["created_at"],
                ),
            )

        return result

    # 5. List Records
    def list_records(self, category: str = "declarations", limit: int = 20) -> List[Dict[str, Any]]:
        """Queries stored price declarations, postings, valuation certificates, or gouging audits."""
        cat = category.lower().strip()
        with self._get_connection() as conn:
            if cat in ["postings", "listing", "niem_yet"]:
                cursor = conn.execute("SELECT * FROM price_postings ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["valuations", "appraisals", "tham_dinh"]:
                cursor = conn.execute("SELECT * FROM valuation_certificates ORDER BY id DESC LIMIT ?", (limit,))
            elif cat in ["gouging", "violations", "tang_gia"]:
                cursor = conn.execute("SELECT * FROM anti_gouging_audits ORDER BY id DESC LIMIT ?", (limit,))
            else:
                cursor = conn.execute("SELECT * FROM price_declarations ORDER BY id DESC LIMIT ?", (limit,))

            return [dict(row) for row in cursor.fetchall()]

    # 6. Telemetry & Summary Status
    def get_status(self) -> Dict[str, Any]:
        """Aggregates system-wide Price Management, Anti-Gouging and Valuation telemetry."""
        with self._get_connection() as conn:
            total_decs = conn.execute("SELECT COUNT(*) FROM price_declarations").fetchone()[0]
            stabilized_decs = conn.execute("SELECT COUNT(*) FROM price_declarations WHERE is_stabilized_good = 1").fetchone()[0]
            total_postings = conn.execute("SELECT COUNT(*) FROM price_postings").fetchone()[0]
            posting_violations = conn.execute("SELECT COUNT(*) FROM price_postings WHERE status != 'COMPLIANT_POSTING'").fetchone()[0]
            total_valuations = conn.execute("SELECT COUNT(*) FROM valuation_certificates").fetchone()[0]
            total_appraised_value = conn.execute("SELECT COALESCE(SUM(appraised_value_vnd), 0.0) FROM valuation_certificates WHERE is_valid = 1").fetchone()[0]
            total_gouging_cases = conn.execute("SELECT COUNT(*) FROM anti_gouging_audits WHERE status = 'PRICE_GOUGING_CONFIRMED'").fetchone()[0]
            total_illicit_fines = conn.execute("SELECT COALESCE(SUM(penalty_fine_vnd + illicit_profit_vnd), 0.0) FROM anti_gouging_audits").fetchone()[0]

        return {
            "status": "HEALTHY",
            "statutory_law": "Luật Giá 2023 (Luật số 16/2023/QH15, hiệu lực từ 01/07/2024) & Chuẩn mực TĐGVN",
            "total_price_declarations": total_decs,
            "stabilized_commodities_declarations": stabilized_decs,
            "total_price_posting_inspections": total_postings,
            "posting_violations_detected": posting_violations,
            "total_valuation_certificates_issued": total_valuations,
            "total_appraised_asset_value_vnd": total_appraised_value,
            "price_gouging_cases_penalized": total_gouging_cases,
            "total_illicit_recovery_and_fines_vnd": total_illicit_fines,
            "timestamp": datetime.datetime.now().isoformat(),
        }
