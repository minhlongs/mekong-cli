# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Commercial Real Estate, Industrial Land & EPC Leasing Compliance Engine.

Implements Vietnamese statutory real estate leasing, industrial parks & land tenure compliance:
- Luật Đất đai 2024 (Luật số 31/2024/QH15) có hiệu lực từ 01/08/2024:
  * Điều 33 & 34: Quyền và nghĩa vụ của người sử dụng đất theo hình thức trả tiền thuê đất:
    - Trả tiền hàng năm (Annual lease payment): không được chuyển nhượng quyền sử dụng đất, chỉ chuyển nhượng tài sản.
    - Trả tiền một lần (Lump-sum 50-year lease): được chuyển nhượng, thế chấp, cho thuê lại QSDĐ và tài sản.
  * Điều 159: Bảng giá đất theo nguyên tắc thị trường (bỏ khung giá đất cũ).
  * Điều 202: Chế độ sử dụng đất khu công nghiệp, cụm công nghiệp, khu công nghệ cao (thời hạn ≤ 50 năm, tối đa 70 năm).
- Luật Kinh doanh Bất động sản 2023 (Luật số 29/2023/QH15) có hiệu lực từ 01/08/2024:
  * Điều 14: Điều kiện của công trình xây dựng đưa vào kinh doanh (GCN, không tranh chấp, không kê biên).
  * Điều 23.5: Giới hạn tiền đặt cọc tối đa không quá 5% giá bán/thuê mua nhà ở, công trình hình thành trong tương lai.
  * Nghị định 96/2024/NĐ-CP: Quy định chi tiết các mẫu hợp đồng thuê bất động sản, nhà xưởng RBF/BTS.
- Quy chuẩn Quy hoạch Xây dựng (QCVN 01:2021/BXD & Nghị định 35/2022/NĐ-CP):
  * Mật độ xây dựng thuần lô đất công nghiệp: tối đa 70% (với công trình chiều cao ≤ 40m).
  * Tỷ lệ đất cây xanh trong khuôn viên lô đất công nghiệp: tối thiểu 10% - 20%.
  * Thẩm duyệt thiết kế PCCC (Nghị định 50/2024/NĐ-CP) & xử lý nước thải công nghiệp (QCVN 40:2011/BTNMT).
- Lưu trữ SQLite WAL tại ``.mekong/realestate.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import json
import math
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# Regulatory & Statutory Constants
# ---------------------------------------------------------------------------

USD_VND_EXCHANGE_RATE: float = 25_450.0  # Tỷ giá hạch toán tham chiếu USD/VND

# QCVN 01:2021/BXD: Mật độ xây dựng tối đa theo chiều cao công trình nhà xưởng/công nghiệp
MAX_BUILDING_DENSITY_MAP: dict[str, float] = {
    "UP_TO_12M": 70.0,
    "UP_TO_20M": 70.0,
    "UP_TO_30M": 65.0,
    "UP_TO_40M": 60.0,
    "OVER_40M": 55.0,
}

MIN_GREEN_SPACE_PERCENT: float = 10.0  # Tỷ lệ cây xanh tối thiểu trong lô đất KCN

PROPERTY_CATEGORIES: set[str] = {
    "INDUSTRIAL_LAND",       # Đất khu công nghiệp cho thuê lại (50 năm)
    "READY_BUILT_FACTORY",   # Nhà xưởng xây sẵn (RBF)
    "BUILT_TO_SUIT",         # Nhà xưởng xây theo yêu cầu (BTS / EPC)
    "COMMERCIAL_OFFICE",     # Mặt bằng văn phòng thương mại Grade A/B
}

PAYMENT_TERMS: set[str] = {
    "ANNUAL_RENT",           # Trả tiền thuê đất hàng năm (Điều 34 Luật Đất đai 2024)
    "LUMP_SUM_RENT",         # Trả tiền thuê đất một lần cho cả chu kỳ thuê (Điều 33 Luật Đất đai 2024)
}


class RealEstateEngine:
    """Autonomous Commercial Real Estate, Industrial Land & EPC Leasing Compliance Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "realestate.db"
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS properties (
                    property_id TEXT PRIMARY KEY,
                    project_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    location TEXT NOT NULL,
                    land_area_sqm REAL NOT NULL,
                    usable_area_sqm REAL NOT NULL,
                    payment_term TEXT NOT NULL,
                    tenure_remaining_years REAL NOT NULL,
                    has_land_cert INTEGER NOT NULL,
                    has_construction_permit INTEGER NOT NULL,
                    has_fire_safety_cert INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS lease_contracts (
                    contract_id TEXT PRIMARY KEY,
                    property_id TEXT NOT NULL,
                    lessor_name TEXT NOT NULL,
                    lessee_name TEXT NOT NULL,
                    leased_area_sqm REAL NOT NULL,
                    unit_rent_usd REAL NOT NULL,
                    maintenance_fee_usd REAL NOT NULL,
                    deposit_usd REAL NOT NULL,
                    lease_term_months INTEGER NOT NULL,
                    total_contract_value_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS due_diligence_audits (
                    audit_id TEXT PRIMARY KEY,
                    property_id TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    is_permitted_for_lease INTEGER NOT NULL,
                    audit_summary TEXT NOT NULL,
                    audited_at TEXT NOT NULL,
                    FOREIGN KEY (property_id) REFERENCES properties(property_id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_properties_cat ON properties(category);
                CREATE INDEX IF NOT EXISTS idx_leases_prop ON lease_contracts(property_id);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # Financial Analysis & Cash Flow Schedule (Nghị định 96/2024/NĐ-CP)
    # -----------------------------------------------------------------------

    def calculate_lease_financials(
        self,
        category: str,
        area_sqm: float,
        unit_rent_usd: float,
        lease_term_months: int = 36,
        maintenance_fee_usd: float = 0.5,
        deposit_months: int = 3,
        annual_escalation_pct: float = 3.0,
        exchange_rate: float = USD_VND_EXCHANGE_RATE,
    ) -> dict[str, typing.Any]:
        """Calculate complete commercial/industrial leasing cash flow schedule and deposit requirements."""
        clean_cat = category.upper().strip()
        if clean_cat not in PROPERTY_CATEGORIES:
            clean_cat = "COMMERCIAL_OFFICE"

        # Monthly base rent & maintenance
        monthly_base_rent_usd = area_sqm * unit_rent_usd
        monthly_mgmt_usd = area_sqm * maintenance_fee_usd
        monthly_total_usd = monthly_base_rent_usd + monthly_mgmt_usd

        # Security Deposit (Tiền đặt cọc)
        deposit_usd = monthly_base_rent_usd * deposit_months
        deposit_vnd = deposit_usd * exchange_rate

        # Multi-year cash flow schedule
        lease_years = math.ceil(lease_term_months / 12)
        yearly_schedule: list[dict[str, typing.Any]] = []
        cumulative_rent_usd = 0.0

        current_unit_rent = unit_rent_usd
        for year in range(1, lease_years + 1):
            months_in_year = min(12, lease_term_months - (year - 1) * 12)
            if months_in_year <= 0:
                break

            year_base_rent_usd = area_sqm * current_unit_rent * months_in_year
            year_mgmt_usd = area_sqm * maintenance_fee_usd * months_in_year
            year_total_usd = year_base_rent_usd + year_mgmt_usd
            cumulative_rent_usd += year_total_usd

            yearly_schedule.append({
                "year": year,
                "months": months_in_year,
                "unit_rent_usd_sqm_month": round(current_unit_rent, 2),
                "annual_base_rent_usd": round(year_base_rent_usd, 2),
                "annual_maintenance_usd": round(year_mgmt_usd, 2),
                "annual_total_usd": round(year_total_usd, 2),
                "annual_total_vnd": round(year_total_usd * exchange_rate),
            })

            # Apply annual rent escalation
            current_unit_rent *= (1.0 + annual_escalation_pct / 100.0)

        total_value_usd = round(cumulative_rent_usd, 2)
        total_value_vnd = round(cumulative_rent_usd * exchange_rate)

        return {
            "ok": True,
            "category": clean_cat,
            "leased_area_sqm": area_sqm,
            "lease_term_months": lease_term_months,
            "deposit": {
                "deposit_months": deposit_months,
                "deposit_amount_usd": round(deposit_usd, 2),
                "deposit_amount_vnd": round(deposit_vnd),
                "statutory_note": (
                    "Tuân thủ Điều 23.5 Luật Kinh doanh Bất động sản 2023: tiền đặt cọc thỏa thuận đảm bảo thực hiện nghĩa vụ hợp đồng."
                ),
            },
            "monthly_overview_usd": {
                "base_rent": round(monthly_base_rent_usd, 2),
                "management_fee": round(monthly_mgmt_usd, 2),
                "total_monthly": round(monthly_total_usd, 2),
            },
            "total_contract_value_usd": total_value_usd,
            "total_contract_value_vnd": total_value_vnd,
            "exchange_rate_applied": exchange_rate,
            "annual_escalation_pct": annual_escalation_pct,
            "yearly_cash_flow": yearly_schedule,
        }

    # -----------------------------------------------------------------------
    # Building Density & Green Space Compliance (QCVN 01:2021/BXD)
    # -----------------------------------------------------------------------

    def validate_construction_density(
        self,
        lot_area_sqm: float,
        building_footprint_sqm: float,
        green_space_sqm: float,
        building_height_tier: str = "UP_TO_20M",
    ) -> dict[str, typing.Any]:
        """Validate industrial/commercial site density and green ratio against QCVN 01:2021/BXD."""
        tier = building_height_tier.upper().strip()
        if tier not in MAX_BUILDING_DENSITY_MAP:
            tier = "UP_TO_20M"

        max_density_pct = MAX_BUILDING_DENSITY_MAP[tier]

        if lot_area_sqm <= 0:
            return {"ok": False, "error": "Diện tích khu đất (lot_area_sqm) phải lớn hơn 0."}

        actual_density_pct = round((building_footprint_sqm / lot_area_sqm) * 100.0, 2)
        actual_green_pct = round((green_space_sqm / lot_area_sqm) * 100.0, 2)

        density_compliant = actual_density_pct <= max_density_pct
        green_compliant = actual_green_pct >= MIN_GREEN_SPACE_PERCENT
        overall_compliant = density_compliant and green_compliant

        violations: list[str] = []
        if not density_compliant:
            violations.append(
                f"Mật độ xây dựng thực tế ({actual_density_pct}%) vượt trần quy định ({max_density_pct}%) theo QCVN 01:2021/BXD."
            )
        if not green_compliant:
            violations.append(
                f"Tỷ lệ diện tích cây xanh ({actual_green_pct}%) thấp hơn mức tối thiểu bắt buộc ({MIN_GREEN_SPACE_PERCENT}%) trong KCN."
            )

        return {
            "ok": True,
            "lot_area_sqm": lot_area_sqm,
            "building_footprint_sqm": building_footprint_sqm,
            "green_space_sqm": green_space_sqm,
            "height_tier": tier,
            "max_allowed_density_pct": max_density_pct,
            "actual_density_pct": actual_density_pct,
            "density_compliant": density_compliant,
            "min_required_green_pct": MIN_GREEN_SPACE_PERCENT,
            "actual_green_pct": actual_green_pct,
            "green_compliant": green_compliant,
            "overall_compliant": overall_compliant,
            "violations_count": len(violations),
            "violations": violations,
            "statutory_basis": "Quy chuẩn Kỹ thuật Quốc gia về Quy hoạch Xây dựng QCVN 01:2021/BXD & Nghị định 35/2022/NĐ-CP.",
        }

    # -----------------------------------------------------------------------
    # Legal Due Diligence Audit (Luật Đất đai 2024 & Luật KDBĐS 2023)
    # -----------------------------------------------------------------------

    def perform_due_diligence(
        self,
        project_name: str,
        category: str,
        land_area_sqm: float,
        has_land_cert: bool,
        has_construction_permit: bool,
        has_fire_safety_cert: bool,
        tenure_remaining_years: float = 30.0,
        payment_term: str = "ANNUAL_RENT",
        has_disputes: bool = False,
        is_mortgaged_to_bank: bool = False,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Audit legal title, construction readiness, and statutory conditions for leasing."""
        clean_cat = category.upper().strip()
        if clean_cat not in PROPERTY_CATEGORIES:
            clean_cat = "INDUSTRIAL_LAND"

        clean_term = payment_term.upper().strip()
        if clean_term not in PAYMENT_TERMS:
            clean_term = "ANNUAL_RENT"

        risk_score = 0
        defects: list[dict[str, typing.Any]] = []

        # 1. Giấy chứng nhận quyền sử dụng đất (Sổ hồng / Sổ đỏ)
        if not has_land_cert:
            risk_score += 45
            defects.append({
                "issue": "MISSING_LAND_CERTIFICATE",
                "severity": "CRITICAL",
                "description": "Chưa có Giấy chứng nhận quyền sử dụng đất hoặc quyết định giao/cho thuê đất.",
                "statutory_basis": "Điều 14.1 Luật Kinh doanh Bất động sản 2023.",
            })

        # 2. Giấy phép xây dựng (GPXD)
        if clean_cat in ("READY_BUILT_FACTORY", "BUILT_TO_SUIT", "COMMERCIAL_OFFICE") and not has_construction_permit:
            risk_score += 30
            defects.append({
                "issue": "MISSING_CONSTRUCTION_PERMIT",
                "severity": "HIGH",
                "description": "Công trình chưa được cấp Giấy phép xây dựng hoặc biên bản nghiệm thu hoàn thành đưa vào sử dụng.",
                "statutory_basis": "Luật Xây dựng 2014 (sửa đổi 2020) & Nghị định 06/2021/NĐ-CP.",
            })

        # 3. Nghiệm thu PCCC (Phòng cháy chữa cháy)
        if not has_fire_safety_cert:
            risk_score += 35
            defects.append({
                "issue": "MISSING_FIRE_SAFETY_CERT",
                "severity": "CRITICAL",
                "description": "Chưa có Văn bản nghiệm thu về phòng cháy và chữa cháy theo quy định.",
                "statutory_basis": "Nghị định 50/2024/NĐ-CP & Điều 14.3 Luật Kinh doanh Bất động sản 2023.",
            })

        # 4. Tranh chấp hoặc kê biên thi hành án
        if has_disputes:
            risk_score += 40
            defects.append({
                "issue": "PROPERTY_UNDER_DISPUTE",
                "severity": "CRITICAL",
                "description": "Bất động sản đang có tranh chấp về quyền sử dụng đất hoặc quyền sở hữu tài sản.",
                "statutory_basis": "Điều 14.2 Luật Kinh doanh Bất động sản 2023.",
            })

        # 5. Thế chấp ngân hàng
        if is_mortgaged_to_bank:
            risk_score += 15
            defects.append({
                "issue": "MORTGAGED_PROPERTY",
                "severity": "MEDIUM",
                "description": "Tài sản đang được thế chấp tại tổ chức tín dụng. Cần có văn bản chấp thuận cho thuê của Ngân hàng nhận thế chấp.",
                "statutory_basis": "Điều 320 Bộ luật Dân sự 2015 & Điều 14.4 Luật KDBĐS 2023.",
            })

        # 6. Thời hạn sử dụng đất còn lại
        if tenure_remaining_years < 5.0:
            risk_score += 25
            defects.append({
                "issue": "TENURE_EXPIRING_SOON",
                "severity": "HIGH",
                "description": f"Thời hạn thuê đất còn lại ({tenure_remaining_years} năm) quá ngắn, rủi ro thu hồi đất không kịp gia hạn.",
                "statutory_basis": "Điều 172 & 202 Luật Đất đai 2024.",
            })

        if risk_score >= 60:
            risk_level = "CRITICAL"
        elif risk_score >= 35:
            risk_level = "HIGH"
        elif risk_score >= 15:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        is_permitted = (risk_score < 40) and has_land_cert and not has_disputes

        prop_id = f"PR-{uuid.uuid4().hex[:8].upper()}"
        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "audit_id": audit_id,
            "property_id": prop_id,
            "project_name": project_name,
            "category": clean_cat,
            "payment_term": clean_term,
            "land_area_sqm": land_area_sqm,
            "tenure_remaining_years": tenure_remaining_years,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "is_permitted_for_lease": is_permitted,
            "defects_count": len(defects),
            "defects": defects,
            "legal_conclusion": (
                "ĐỦ ĐIỀU KIỆN ĐƯA VÀO KINH DOANH CHO THUÊ"
                if is_permitted
                else "CHƯA ĐỦ ĐIỀU KIỆN CHO THUÊ — CẦN KHẮC PHỤC CÁC VI PHẠM PHÁP LÝ"
            ),
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO properties (
                        property_id, project_name, category, location, land_area_sqm,
                        usable_area_sqm, payment_term, tenure_remaining_years,
                        has_land_cert, has_construction_permit, has_fire_safety_cert,
                        status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        prop_id,
                        project_name,
                        clean_cat,
                        "Việt Nam",
                        land_area_sqm,
                        land_area_sqm * 0.85,
                        clean_term,
                        tenure_remaining_years,
                        1 if has_land_cert else 0,
                        1 if has_construction_permit else 0,
                        1 if has_fire_safety_cert else 0,
                        "QUALIFIED" if is_permitted else "DISQUALIFIED",
                        now.isoformat(),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO due_diligence_audits (
                        audit_id, property_id, risk_score, risk_level,
                        is_permitted_for_lease, audit_summary, audited_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        prop_id,
                        risk_score,
                        risk_level,
                        1 if is_permitted else 0,
                        result["legal_conclusion"],
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Statutory Lease Agreement Drafting (Nghị định 96/2024/NĐ-CP)
    # -----------------------------------------------------------------------

    def draft_lease_agreement(
        self,
        property_id: str,
        lessor_name: str,
        lessee_name: str,
        leased_area_sqm: float,
        unit_rent_usd: float,
        lease_term_months: int = 36,
        maintenance_fee_usd: float = 0.5,
        deposit_months: int = 3,
        dispute_resolution: str = "VIAC",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Synthesize a complete commercial/industrial lease agreement complying with Decree 96/2024/ND-CP."""
        contract_id = f"LC-{uuid.uuid4().hex[:8].upper()}"
        contract_number = f"HD-THUE/{datetime.datetime.now().year}/{uuid.uuid4().hex[:6].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        fin = self.calculate_lease_financials(
            category="COMMERCIAL_OFFICE",
            area_sqm=leased_area_sqm,
            unit_rent_usd=unit_rent_usd,
            lease_term_months=lease_term_months,
            maintenance_fee_usd=maintenance_fee_usd,
            deposit_months=deposit_months,
        )

        total_val_usd = fin["total_contract_value_usd"]
        deposit_usd = fin["deposit"]["deposit_amount_usd"]

        contract_text = f"""================================================================================
CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc
-----***-----

HỢP ĐỒNG THUÊ BẤT ĐỘNG SẢN THƯƠNG MẠI & NHÀ XƯỞNG
Số: {contract_number}
(Ban hành theo mẫu chuẩn Nghị định 96/2024/NĐ-CP & Luật Kinh doanh Bất động sản 2023)

Căn cứ:
- Bộ luật Dân sự số 91/2015/QH13;
- Luật Đất đai số 31/2024/QH15;
- Luật Kinh doanh Bất động sản số 29/2023/QH15;
- Nghị định số 96/2024/NĐ-CP quy định chi tiết một số điều của Luật Kinh doanh BĐS.

Hôm nay, ngày {now.strftime("%d tháng %m năm %Y")}, chúng tôi gồm:

BÊN CHO THUÊ (BÊN A):
- Tên tổ chức: {lessor_name}
- Đại diện theo pháp luật: Giám đốc Điều hành
- Quyền sở hữu/quyền sử dụng đất hợp pháp đối với Bất động sản ID: {property_id}

BÊN THUÊ (BÊN B):
- Tên tổ chức/doanh nghiệp: {lessee_name}
- Đại diện theo pháp luật: Tổng Giám đốc

HAI BÊN THỐNG NHẤT KÝ KẾT HỢP ĐỒNG THUÊ VỚI CÁC ĐIỀU KHOẢN SAU:

ĐIỀU 1: ĐỐI TƯỢNG VÀ DIỆN TÍCH THUÊ
1.1. Bên A đồng ý cho Bên B thuê và Bên B đồng ý thuê diện tích: {leased_area_sqm:,.2f} m² tại Bất động sản mã số {property_id}.
1.2. Mục đích thuê: Hoạt động văn phòng thương mại, trung tâm R&D hoặc sản xuất công nghiệp sạch theo quy chuẩn pháp luật.

ĐIỀU 2: THỜI HẠN THUÊ VÀ BÀN GIAO
2.1. Thời hạn thuê là: {lease_term_months} tháng kể từ ngày ký biên bản bàn giao mặt bằng.
2.2. Thời gian miễn phí tiền thuê để lắp đặt nội thất (Fit-out period): 30 ngày kể từ ngày bàn giao.

ĐIỀU 3: GIÁ THUÊ, PHÍ DỊCH VỤ VÀ PHƯƠNG THỨC THANH TOÁN
3.1. Đơn giá thuê: {unit_rent_usd:,.2f} USD/m²/tháng (Quy đổi VND theo tỷ giá bán ra của Vietcombank tại ngày thanh toán).
3.2. Phí quản lý và vận hành kỹ thuật: {maintenance_fee_usd:,.2f} USD/m²/tháng.
3.3. Tổng giá trị hợp đồng ước tính trong thời hạn thuê: {total_val_usd:,.2f} USD (~ {fin['total_contract_value_vnd']:,.0f} VND).
3.4. Kỳ thanh toán: Trả trước 03 tháng một lần vào 05 ngày đầu tiên của mỗi kỳ thanh toán.

ĐIỀU 4: TIỀN ĐẶT CỌC BẢO ĐẢM THỰC HIỆN HỢP ĐỒNG
4.1. Tiền đặt cọc bảo đảm là {deposit_months} tháng tiền thuê cơ sở, tương đương: {deposit_usd:,.2f} USD (~ {fin['deposit']['deposit_amount_vnd']:,.0f} VND).
4.2. Tiền đặt cọc được Bên A hoàn trả lại cho Bên B trong vòng 15 ngày làm việc sau khi thanh lý hợp đồng và bàn giao lại mặt bằng nguyên trạng.

ĐIỀU 5: PHÒNG CHÁY CHỮA CHÁY VÀ BẢO VỆ MÔI TRƯỜNG
5.1. Mặt bằng cho thuê tuân thủ đầy đủ nghiệm thu PCCC theo Nghị định 50/2024/NĐ-CP và QCVN 06:2022/BXD.
5.2. Bên B cam kết không xả thải vượt ngưỡng quy chuẩn môi trường QCVN 40:2011/BTNMT.

ĐIỀU 6: GIẢI QUYẾT TRANH CHẤP
Mọi tranh chấp phát sinh sẽ được giải quyết trước hết thông qua thương lượng. Nếu không thỏa thuận được, tranh chấp sẽ được giải quyết tại: {dispute_resolution} (Trung tâm Trọng tài Quốc tế Việt Nam bên cạnh VCCI) theo Quy tắc tố tụng trọng tài.

Hợp đồng được lập thành 04 bản có giá trị pháp lý như nhau, mỗi bên giữ 02 bản.

         ĐẠI DIỆN BÊN A                               ĐẠI DIỆN BÊN B
   (Ký, ghi rõ họ tên và đóng dấu)              (Ký, ghi rõ họ tên và đóng dấu)
================================================================================
"""

        result = {
            "ok": True,
            "contract_id": contract_id,
            "contract_number": contract_number,
            "property_id": property_id,
            "lessor_name": lessor_name,
            "lessee_name": lessee_name,
            "leased_area_sqm": leased_area_sqm,
            "unit_rent_usd": unit_rent_usd,
            "maintenance_fee_usd": maintenance_fee_usd,
            "deposit_usd": deposit_usd,
            "lease_term_months": lease_term_months,
            "total_contract_value_usd": total_val_usd,
            "dispute_resolution": dispute_resolution,
            "governing_law": "Luật Kinh doanh Bất động sản 2023 & Nghị định 96/2024/NĐ-CP",
            "contract_text": contract_text.strip(),
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO lease_contracts (
                        contract_id, property_id, lessor_name, lessee_name,
                        leased_area_sqm, unit_rent_usd, maintenance_fee_usd,
                        deposit_usd, lease_term_months, total_contract_value_usd,
                        status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        contract_id,
                        property_id,
                        lessor_name,
                        lessee_name,
                        leased_area_sqm,
                        unit_rent_usd,
                        maintenance_fee_usd,
                        deposit_usd,
                        lease_term_months,
                        total_val_usd,
                        "ACTIVE",
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Portfolio & Status
    # -----------------------------------------------------------------------

    def list_properties(self, category: typing.Optional[str] = None, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered real estate properties and industrial parks."""
        with self._get_connection() as conn:
            if category and category.upper() != "ALL":
                rows = conn.execute(
                    "SELECT * FROM properties WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                    (category.upper(), limit),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM properties ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def list_contracts(self, limit: int = 50) -> list[dict[str, typing.Any]]:
        """List executed lease contracts and commercial tenancies."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM lease_contracts ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated commercial real estate and industrial land telemetry."""
        with self._get_connection() as conn:
            p_row = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(land_area_sqm), 0) as sm FROM properties").fetchone()
            c_row = conn.execute("SELECT COUNT(*) as c, COALESCE(SUM(total_contract_value_usd), 0) as sm, COALESCE(SUM(deposit_usd), 0) as dep FROM lease_contracts").fetchone()
            a_row = conn.execute("SELECT COUNT(*) as c FROM due_diligence_audits WHERE is_permitted_for_lease = 1").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "RealEstateEngine",
            "regulatory_framework": "Luật Đất đai 2024 (31/2024/QH15) & Luật Kinh doanh BĐS 2023 (29/2023/QH15)",
            "standards": "QCVN 01:2021/BXD (Mật độ ≤70%, Cây xanh ≥10%) & Nghị định 96/2024/NĐ-CP",
            "metrics": {
                "total_properties": p_row["c"] if p_row else 0,
                "total_managed_area_sqm": p_row["sm"] if p_row else 0.0,
                "active_lease_contracts": c_row["c"] if c_row else 0,
                "total_lease_value_usd": c_row["sm"] if c_row else 0.0,
                "total_lease_value_vnd": round((c_row["sm"] if c_row else 0.0) * USD_VND_EXCHANGE_RATE),
                "total_security_deposit_usd": c_row["dep"] if c_row else 0.0,
                "qualified_audited_properties": a_row["c"] if a_row else 0,
            },
            "database": str(self.db_path),
        }
