# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Insurance Business, Actuarial Solvency, Life & Non-Life Underwriting Engine.

Implements statutory insurer licensing (minimum charter capital standards under Decree 46/2023/NĐ-CP),
insurance policy underwriting & tariffing, solvency margin and Capital Adequacy Ratio (CAR) auditing,
claims settlement and indemnity deductions, and actuarial technical reserves calculation under:
- Luật Kinh doanh bảo hiểm 2022 (Luật số 08/2022/QH15)
- Nghị định số 46/2023/NĐ-CP:
  * Điều kiện thành lập, cấp phép và vốn điều lệ tối thiểu:
    - Bảo hiểm phi nhân thọ & sức khỏe: Tối thiểu 400 tỷ VND (450 tỷ VND nếu có hàng không/vệ tinh).
    - Bảo hiểm nhân thọ & sức khỏe: Tối thiểu 750 tỷ VND (1,000 tỷ VND nếu có liên kết đơn vị/hưu trí).
    - Kinh doanh tái bảo hiểm: Tối thiểu 500 tỷ VND (phi nhân thọ) hoặc 700 tỷ VND (nhân thọ/cả hai).
    - Kinh doanh môi giới bảo hiểm: Tối thiểu 50 tỷ VND.
  * Biên khả năng thanh toán tối thiểu (Minimum Solvency Margin):
    - Phi nhân thọ: Max(25% phí bảo hiểm giữ lại, 16% bồi thường bình quân 3 năm).
    - Nhân thọ: 4% dự phòng toán học + 0.1% đến 0.3% số tiền bảo hiểm chịu rủi ro.
  * Tỷ lệ an toàn vốn: Biên khả năng thanh toán thực tế / Biên tối thiểu >= 100%.
- Thông tư số 67/2023/TT-BTC & Thông tư số 68/2023/TT-BTC:
  * Phương pháp trích lập dự phòng nghiệp vụ:
    - Dự phòng phí chưa được hưởng (UPR): Tỷ lệ theo ngày 1/365 hoặc hệ số 80/20.
    - Dự phòng bồi thường khiếu nại (OCR): Theo từng hồ sơ tổn thất.
    - Dự phòng tổn thất đã phát sinh nhưng chưa khiếu nại (IBNR): 3% - 5% phí giữ lại.
- Lưu trữ SQLite WAL tại ``.mekong/insurance.db``.

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
# Statutory Insurance Baselines & Constants
# ---------------------------------------------------------------------------

INSURANCE_LICENSE_TYPES: dict[str, dict[str, typing.Any]] = {
    "NON_LIFE_INSURANCE": {
        "license_code": "NON_LIFE_INSURANCE",
        "name_vi": "Kinh doanh bảo hiểm phi nhân thọ và bảo hiểm sức khỏe",
        "min_capital_vnd": 400_000_000_000.0,
        "authority": "Bộ Tài chính",
        "description": "Bảo hiểm tài sản, thiệt hại, xe cơ giới, hàng hải, sức khỏe và tai nạn con người",
    },
    "NON_LIFE_SPECIALTY": {
        "license_code": "NON_LIFE_SPECIALTY",
        "name_vi": "Kinh doanh bảo hiểm phi nhân thọ mở rộng (Hàng không, Vệ tinh)",
        "min_capital_vnd": 450_000_000_000.0,
        "authority": "Bộ Tài chính",
        "description": "Bao gồm bảo hiểm rủi ro hàng không dân dụng, bảo hiểm vệ tinh và rủi ro không gian",
    },
    "LIFE_INSURANCE": {
        "license_code": "LIFE_INSURANCE",
        "name_vi": "Kinh doanh bảo hiểm nhân thọ và bảo hiểm sức khỏe",
        "min_capital_vnd": 750_000_000_000.0,
        "authority": "Bộ Tài chính",
        "description": "Bảo hiểm trọn đời, sinh kỳ, tử kỳ, hỗn hợp và bảo hiểm trả tiền định kỳ",
    },
    "LIFE_UNIT_LINKED": {
        "license_code": "LIFE_UNIT_LINKED",
        "name_vi": "Bảo hiểm nhân thọ mở rộng (Liên kết đơn vị, Hưu trí)",
        "min_capital_vnd": 1_000_000_000_000.0,
        "authority": "Bộ Tài chính",
        "description": "Bảo hiểm liên kết đầu tư (Unit-Linked / Universal Life) và bảo hiểm hưu trí bổ sung",
    },
    "REINSURANCE": {
        "license_code": "REINSURANCE",
        "name_vi": "Kinh doanh tái bảo hiểm",
        "min_capital_vnd": 500_000_000_000.0,
        "authority": "Bộ Tài chính",
        "description": "Nhận và nhượng tái bảo hiểm trong nước và quốc tế",
    },
    "INSURANCE_BROKERAGE": {
        "license_code": "INSURANCE_BROKERAGE",
        "name_vi": "Kinh doanh môi giới bảo hiểm",
        "min_capital_vnd": 50_000_000_000.0,
        "authority": "Bộ Tài chính",
        "description": "Môi giới bảo hiểm gốc, môi giới tái bảo hiểm và thu xếp hợp đồng bảo hiểm",
    },
}

INSURANCE_PRODUCT_LINES: dict[str, dict[str, typing.Any]] = {
    "MOTOR_VEHICLE": {
        "code": "MOTOR_VEHICLE",
        "name_vi": "Bảo hiểm xe cơ giới (TNDS bắt buộc & vật chất thân xe)",
        "category": "NON_LIFE",
        "base_rate": 0.015,
        "default_deductible_vnd": 1_000_000.0,
    },
    "FIRE_EXPLOSION": {
        "code": "FIRE_EXPLOSION",
        "name_vi": "Bảo hiểm cháy, nổ bắt buộc cơ sở nguy hiểm",
        "category": "NON_LIFE",
        "base_rate": 0.001,
        "default_deductible_vnd": 10_000_000.0,
    },
    "CARGO_MARINE": {
        "code": "CARGO_MARINE",
        "name_vi": "Bảo hiểm hàng hóa vận chuyển nội địa & xuất nhập khẩu",
        "category": "NON_LIFE",
        "base_rate": 0.0025,
        "default_deductible_vnd": 5_000_000.0,
    },
    "HEALTH_ACCIDENT": {
        "code": "HEALTH_ACCIDENT",
        "name_vi": "Bảo hiểm sức khỏe, y tế viện phí & tai nạn toàn diện",
        "category": "HEALTH",
        "base_rate": 0.022,
        "default_deductible_vnd": 500_000.0,
    },
    "LIFE_TERM": {
        "code": "LIFE_TERM",
        "name_vi": "Bảo hiểm nhân thọ tử kỳ có thời hạn",
        "category": "LIFE",
        "base_rate": 0.008,
        "default_deductible_vnd": 0.0,
    },
    "LIFE_ENDOWMENT": {
        "code": "LIFE_ENDOWMENT",
        "name_vi": "Bảo hiểm nhân thọ hỗn hợp bảo vệ kết hợp tích lũy tiết kiệm",
        "category": "LIFE",
        "base_rate": 0.035,
        "default_deductible_vnd": 0.0,
    },
    "LIFE_UNIT_LINKED": {
        "code": "LIFE_UNIT_LINKED",
        "name_vi": "Bảo hiểm nhân thọ liên kết đầu tư (Universal / Unit-Linked Life)",
        "category": "LIFE",
        "base_rate": 0.042,
        "default_deductible_vnd": 0.0,
    },
}

SOLVENCY_STATUSES: dict[str, dict[str, typing.Any]] = {
    "HEALTHY": {
        "min_car": 1.50,
        "rating": "VỮNG MẠNH",
        "action": "Hoạt động kinh doanh bình thường, an toàn vốn cao",
    },
    "COMPLIANT": {
        "min_car": 1.00,
        "rating": "ĐẠT CHUẨN LUẬT ĐỊNH",
        "action": "Đủ khả năng thanh toán theo quy định Bộ Tài chính",
    },
    "WARNING_SUPERVISED": {
        "min_car": 0.80,
        "rating": "CẢNH BÁO GIÁM SÁT",
        "action": "Yêu cầu lập phương án khôi phục khả năng thanh toán gửi Bộ Tài chính",
    },
    "INSOLVENT_ALERT": {
        "min_car": 0.0,
        "rating": "NGUY CƠ MẤT KHẢ NĂNG THANH TOÁN",
        "action": "Bộ Tài chính áp dụng biện pháp kiểm soát đặc biệt và đình chỉ mở rộng nghiệp vụ",
    },
}


class RecordList(list):
    """List with Rich table display capability for CLI output."""

    def __init__(self, items: list[dict[str, typing.Any]], key: str = "items"):
        super().__init__(items)
        self.key = key

    @property
    def data(self) -> list[dict[str, typing.Any]]:
        return list(self)

    def to_dict(self) -> dict[str, typing.Any]:
        return {self.key: list(self)}


class InsuranceEngine:
    """Core engine for Vietnamese Insurance, Actuarial Solvency & Underwriting."""

    def __init__(self, db_path: pathlib.Path | str | None = None) -> None:
        if db_path is None:
            data_dir = pathlib.Path(os.environ.get("MEKONG_DATA_DIR", ".mekong"))
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "insurance.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS insurance_licenses (
                    license_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    tax_id TEXT NOT NULL UNIQUE,
                    license_type TEXT NOT NULL,
                    charter_capital_vnd REAL NOT NULL,
                    min_required_capital_vnd REAL NOT NULL,
                    legal_representative TEXT NOT NULL,
                    head_office TEXT NOT NULL,
                    licensing_authority TEXT NOT NULL,
                    license_number TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL,
                    registered_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS insurance_policies (
                    policy_id TEXT PRIMARY KEY,
                    policyholder_name TEXT NOT NULL,
                    product_line TEXT NOT NULL,
                    product_name_vi TEXT NOT NULL,
                    category TEXT NOT NULL,
                    sum_insured_vnd REAL NOT NULL,
                    premium_vnd REAL NOT NULL,
                    deductible_vnd REAL NOT NULL,
                    term_months INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    free_look_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS solvency_audits (
                    audit_id TEXT PRIMARY KEY,
                    insurer_name TEXT NOT NULL,
                    is_life INTEGER NOT NULL,
                    actual_margin_vnd REAL NOT NULL,
                    minimum_margin_vnd REAL NOT NULL,
                    capital_adequacy_ratio REAL NOT NULL,
                    solvency_status TEXT NOT NULL,
                    regulatory_verdict TEXT NOT NULL,
                    audited_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS claims_settlements (
                    claim_id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    incident_description TEXT NOT NULL,
                    claimed_amount_vnd REAL NOT NULL,
                    deductible_vnd REAL NOT NULL,
                    net_settled_amount_vnd REAL NOT NULL,
                    damage_proof_verified INTEGER NOT NULL,
                    is_approved INTEGER NOT NULL,
                    settlement_status TEXT NOT NULL,
                    settled_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS actuarial_reserves (
                    reserve_id TEXT PRIMARY KEY,
                    insurer_name TEXT NOT NULL,
                    product_line TEXT NOT NULL,
                    written_premium_vnd REAL NOT NULL,
                    unearned_premium_reserve_vnd REAL NOT NULL,
                    outstanding_claim_reserve_vnd REAL NOT NULL,
                    ibnr_reserve_vnd REAL NOT NULL,
                    total_reserves_vnd REAL NOT NULL,
                    calculated_at TEXT NOT NULL
                );
                """
            )

    # -----------------------------------------------------------------------
    # Insurer Licensing (Decree 46/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def issue_insurer_license(
        self,
        enterprise_name: str,
        tax_id: str,
        license_type: str = "NON_LIFE_INSURANCE",
        charter_capital_vnd: float = 400_000_000_000.0,
        legal_representative: str = "Nguyễn Văn Hùng",
        head_office: str = "Hà Nội",
    ) -> dict[str, typing.Any]:
        """Verify charter capital thresholds and issue insurance enterprise license."""
        l_type = license_type.upper().strip()
        if l_type not in INSURANCE_LICENSE_TYPES:
            valid_types = ", ".join(INSURANCE_LICENSE_TYPES.keys())
            raise ValueError(f"Loại giấy phép bảo hiểm không hợp lệ '{license_type}'. Hợp lệ: {valid_types}")

        cfg = INSURANCE_LICENSE_TYPES[l_type]
        min_capital = cfg["min_capital_vnd"]

        if charter_capital_vnd < min_capital:
            raise ValueError(
                f"Vốn điều lệ không đủ điều kiện theo Nghị định 46/2023/NĐ-CP: "
                f"cung cấp {charter_capital_vnd:,.0f} VND, yêu cầu tối thiểu {min_capital:,.0f} VND"
            )

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        license_id = str(uuid.uuid4())
        norm_tax = tax_id.strip()
        lic_number = f"GP-BH-{l_type[:4]}-{norm_tax[:6]}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO insurance_licenses (
                    license_id, enterprise_name, tax_id, license_type,
                    charter_capital_vnd, min_required_capital_vnd, legal_representative,
                    head_office, licensing_authority, license_number, status, registered_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    license_id,
                    enterprise_name,
                    norm_tax,
                    l_type,
                    charter_capital_vnd,
                    min_capital,
                    legal_representative,
                    head_office,
                    cfg["authority"],
                    lic_number,
                    "ACTIVE",
                    now,
                ),
            )

        return {
            "status": "success",
            "license_id": license_id,
            "license_profile": {
                "license_number": lic_number,
                "enterprise_name": enterprise_name,
                "tax_id": norm_tax,
                "license_type": l_type,
                "license_name_vi": cfg["name_vi"],
                "charter_capital_vnd": charter_capital_vnd,
                "min_required_capital_vnd": min_capital,
                "legal_representative": legal_representative,
                "head_office": head_office,
                "licensing_authority": cfg["authority"],
                "status": "ACTIVE",
                "registered_at": now,
            },
            "statutory_reference": "Luật Kinh doanh bảo hiểm 2022 (Điều 64) & Nghị định số 46/2023/NĐ-CP (Điều 35)",
        }

    # -----------------------------------------------------------------------
    # Policy Underwriting & Issuance
    # -----------------------------------------------------------------------

    def underwrite_policy(
        self,
        policyholder_name: str,
        product_line: str = "MOTOR_VEHICLE",
        sum_insured_vnd: float = 1_000_000_000.0,
        premium_vnd: float = 15_000_000.0,
        deductible_vnd: float = 1_000_000.0,
        term_months: int = 12,
        start_date: str = "2026-10-01",
    ) -> dict[str, typing.Any]:
        """Underwrite and issue insurance policy certificate."""
        p_line = product_line.upper().strip()
        if p_line not in INSURANCE_PRODUCT_LINES:
            valid_lines = ", ".join(INSURANCE_PRODUCT_LINES.keys())
            raise ValueError(f"Nghiệp vụ bảo hiểm không hợp lệ '{product_line}'. Hợp lệ: {valid_lines}")

        if sum_insured_vnd <= 0:
            raise ValueError("Số tiền bảo hiểm phải lớn hơn 0")
        if premium_vnd <= 0:
            raise ValueError("Phí bảo hiểm phải lớn hơn 0")
        if term_months <= 0:
            raise ValueError("Thời hạn hợp đồng bảo hiểm phải lớn hơn 0 tháng")

        prod_cfg = INSURANCE_PRODUCT_LINES[p_line]
        policy_id = f"POL-{p_line[:4]}-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Calculate end date
        try:
            st = datetime.date.fromisoformat(start_date)
            # Add approx term_months (30 days/month)
            end_date = (st + datetime.timedelta(days=term_months * 30)).isoformat()
        except Exception:
            end_date = "2027-10-01"

        free_look = 21 if prod_cfg["category"] == "LIFE" else 0

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO insurance_policies (
                    policy_id, policyholder_name, product_line, product_name_vi,
                    category, sum_insured_vnd, premium_vnd, deductible_vnd,
                    term_months, start_date, end_date, free_look_days, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy_id,
                    policyholder_name,
                    p_line,
                    prod_cfg["name_vi"],
                    prod_cfg["category"],
                    sum_insured_vnd,
                    premium_vnd,
                    deductible_vnd,
                    term_months,
                    start_date,
                    end_date,
                    free_look,
                    "IN_FORCE",
                    now,
                ),
            )

        return {
            "status": "success",
            "policy_id": policy_id,
            "policy_profile": {
                "policy_id": policy_id,
                "policyholder_name": policyholder_name,
                "product_line": p_line,
                "product_name_vi": prod_cfg["name_vi"],
                "category": prod_cfg["category"],
                "sum_insured_vnd": sum_insured_vnd,
                "premium_vnd": premium_vnd,
                "deductible_vnd": deductible_vnd,
                "term_months": term_months,
                "start_date": start_date,
                "end_date": end_date,
                "free_look_days": free_look,
                "status": "IN_FORCE",
                "created_at": now,
            },
            "statutory_reference": "Luật Kinh doanh bảo hiểm 2022 (Điều 17, 18, 35) & Thông tư 67/2023/TT-BTC",
        }

    # -----------------------------------------------------------------------
    # Solvency Margin & CAR Auditing (Decree 46/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def audit_solvency_margin(
        self,
        insurer_name: str,
        actual_solvency_margin_vnd: float,
        net_premium_retained_vnd: float = 2_000_000_000_000.0,
        avg_annual_claims_vnd: float = 1_000_000_000_000.0,
        mathematical_reserve_vnd: float = 0.0,
        sum_at_risk_vnd: float = 0.0,
        is_life: bool = False,
    ) -> dict[str, typing.Any]:
        """Audit minimum solvency margin and Capital Adequacy Ratio (CAR)."""
        if actual_solvency_margin_vnd < 0:
            raise ValueError("Biên khả năng thanh toán thực tế không thể âm")

        if is_life:
            # Life: 4% mathematical reserves + 0.1% sum at risk
            min_margin = (0.04 * mathematical_reserve_vnd) + (0.001 * sum_at_risk_vnd)
            if min_margin <= 0:
                min_margin = 200_000_000_000.0  # Default statutory minimum floor
        else:
            # Non-life: Max(25% net premium, 16% 3-year avg claims)
            min_margin = max(0.25 * net_premium_retained_vnd, 0.16 * avg_annual_claims_vnd)

        car_ratio = actual_solvency_margin_vnd / min_margin if min_margin > 0 else 1.0

        if car_ratio >= 1.50:
            status_key = "HEALTHY"
        elif car_ratio >= 1.00:
            status_key = "COMPLIANT"
        elif car_ratio >= 0.80:
            status_key = "WARNING_SUPERVISED"
        else:
            status_key = "INSOLVENT_ALERT"

        status_cfg = SOLVENCY_STATUSES[status_key]
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_id = f"SOLV-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO solvency_audits (
                    audit_id, insurer_name, is_life, actual_margin_vnd,
                    minimum_margin_vnd, capital_adequacy_ratio, solvency_status,
                    regulatory_verdict, audited_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    audit_id,
                    insurer_name,
                    1 if is_life else 0,
                    actual_solvency_margin_vnd,
                    min_margin,
                    car_ratio,
                    status_key,
                    status_cfg["action"],
                    now,
                ),
            )

        return {
            "status": "success",
            "audit_id": audit_id,
            "solvency_profile": {
                "audit_id": audit_id,
                "insurer_name": insurer_name,
                "business_type": "LIFE" if is_life else "NON_LIFE",
                "actual_margin_vnd": actual_solvency_margin_vnd,
                "minimum_margin_vnd": min_margin,
                "capital_adequacy_ratio": round(car_ratio, 4),
                "capital_adequacy_percent": f"{car_ratio * 100:.2f}%",
                "solvency_status": status_key,
                "solvency_rating_vi": status_cfg["rating"],
                "regulatory_verdict": status_cfg["action"],
                "is_solvent": car_ratio >= 1.0,
                "audited_at": now,
            },
            "statutory_reference": "Nghị định số 46/2023/NĐ-CP (Điều 36, 37, 38) về Biên khả năng thanh toán",
        }

    # -----------------------------------------------------------------------
    # Claims Settlement & Indemnity
    # -----------------------------------------------------------------------

    def settle_claim(
        self,
        policy_id: str,
        incident_description: str,
        claimed_amount_vnd: float,
        damage_proof_verified: bool = True,
        is_approved: bool = True,
        custom_deductible_vnd: float | None = None,
    ) -> dict[str, typing.Any]:
        """Process insurance claim settlement, verify coverage and apply deductibles."""
        if claimed_amount_vnd <= 0:
            raise ValueError("Số tiền khiếu nại bồi thường phải lớn hơn 0")

        # Fetch policy deductible if available
        deductible = 1_000_000.0 if custom_deductible_vnd is None else custom_deductible_vnd
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT deductible_vnd FROM insurance_policies WHERE policy_id = ?", (policy_id,))
            row = cursor.fetchone()
            if row is not None and custom_deductible_vnd is None:
                deductible = float(row["deductible_vnd"])

        if is_approved and damage_proof_verified:
            net_settled = max(0.0, claimed_amount_vnd - deductible)
            status_str = "SETTLED_APPROVED"
        else:
            net_settled = 0.0
            status_str = "REJECTED_DISAPPROVED"

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        claim_id = f"CLM-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO claims_settlements (
                    claim_id, policy_id, incident_description, claimed_amount_vnd,
                    deductible_vnd, net_settled_amount_vnd, damage_proof_verified,
                    is_approved, settlement_status, settled_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    policy_id,
                    incident_description,
                    claimed_amount_vnd,
                    deductible,
                    net_settled,
                    1 if damage_proof_verified else 0,
                    1 if is_approved else 0,
                    status_str,
                    now,
                ),
            )

        return {
            "status": "success",
            "claim_id": claim_id,
            "claim_profile": {
                "claim_id": claim_id,
                "policy_id": policy_id,
                "incident_description": incident_description,
                "claimed_amount_vnd": claimed_amount_vnd,
                "deductible_vnd": deductible,
                "net_settled_amount_vnd": net_settled,
                "damage_proof_verified": damage_proof_verified,
                "is_approved": is_approved,
                "settlement_status": status_str,
                "settled_at": now,
            },
            "statutory_reference": "Luật Kinh doanh bảo hiểm 2022 (Điều 30, 31, 32) về giải quyết bồi thường",
        }

    # -----------------------------------------------------------------------
    # Actuarial Technical Reserves Calculation
    # -----------------------------------------------------------------------

    def calculate_technical_reserves(
        self,
        insurer_name: str,
        product_line: str = "MOTOR_VEHICLE",
        written_premium_vnd: float = 50_000_000_000.0,
        unearned_ratio: float = 0.50,
        outstanding_claims_vnd: float = 10_000_000_000.0,
        ibnr_rate: float = 0.05,
    ) -> dict[str, typing.Any]:
        """Compute actuarial unearned premium (UPR), outstanding (OCR) and IBNR reserves."""
        if written_premium_vnd < 0:
            raise ValueError("Phí bảo hiểm gốc không thể âm")
        if not (0.0 <= unearned_ratio <= 1.0):
            raise ValueError("Tỷ lệ phí chưa được hưởng phải trong khoảng [0.0, 1.0]")

        upr = written_premium_vnd * unearned_ratio
        ocr = outstanding_claims_vnd
        ibnr = written_premium_vnd * ibnr_rate
        total_reserves = upr + ocr + ibnr

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        reserve_id = f"RES-{uuid.uuid4().hex[:10].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO actuarial_reserves (
                    reserve_id, insurer_name, product_line, written_premium_vnd,
                    unearned_premium_reserve_vnd, outstanding_claim_reserve_vnd,
                    ibnr_reserve_vnd, total_reserves_vnd, calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reserve_id,
                    insurer_name,
                    product_line.upper(),
                    written_premium_vnd,
                    upr,
                    ocr,
                    ibnr,
                    total_reserves,
                    now,
                ),
            )

        return {
            "status": "success",
            "reserve_id": reserve_id,
            "reserve_profile": {
                "reserve_id": reserve_id,
                "insurer_name": insurer_name,
                "product_line": product_line.upper(),
                "written_premium_vnd": written_premium_vnd,
                "unearned_premium_reserve_vnd": upr,
                "outstanding_claim_reserve_vnd": ocr,
                "ibnr_reserve_vnd": ibnr,
                "total_reserves_vnd": total_reserves,
                "calculated_at": now,
            },
            "statutory_reference": "Nghị định số 46/2023/NĐ-CP (Điều 39, 40) & Thông tư số 67/2023/TT-BTC",
        }

    # -----------------------------------------------------------------------
    # Listing & Status Telemetry APIs
    # -----------------------------------------------------------------------

    def list_licenses(self, limit: int = 50) -> RecordList:
        """List registered insurance enterprise licenses."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT license_id, enterprise_name, tax_id, license_type,
                       charter_capital_vnd, min_required_capital_vnd,
                       legal_representative, licensing_authority, license_number,
                       status, registered_at
                FROM insurance_licenses
                ORDER BY registered_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="licenses")

    def list_policies(self, limit: int = 50) -> RecordList:
        """List active insurance policies."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT policy_id, policyholder_name, product_line, product_name_vi,
                       category, sum_insured_vnd, premium_vnd, deductible_vnd,
                       term_months, start_date, end_date, status, created_at
                FROM insurance_policies
                ORDER BY created_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="policies")

    def list_solvency_audits(self, limit: int = 50) -> RecordList:
        """List solvency and CAR audits."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT audit_id, insurer_name, is_life, actual_margin_vnd,
                       minimum_margin_vnd, capital_adequacy_ratio, solvency_status,
                       regulatory_verdict, audited_at
                FROM solvency_audits
                ORDER BY audited_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="solvency_audits")

    def list_claims(self, limit: int = 50) -> RecordList:
        """List claims settlements."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT claim_id, policy_id, incident_description, claimed_amount_vnd,
                       deductible_vnd, net_settled_amount_vnd, damage_proof_verified,
                       is_approved, settlement_status, settled_at
                FROM claims_settlements
                ORDER BY settled_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="claims")

    def list_reserves(self, limit: int = 50) -> RecordList:
        """List actuarial reserve calculations."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT reserve_id, insurer_name, product_line, written_premium_vnd,
                       unearned_premium_reserve_vnd, outstanding_claim_reserve_vnd,
                       ibnr_reserve_vnd, total_reserves_vnd, calculated_at
                FROM actuarial_reserves
                ORDER BY calculated_at DESC LIMIT ?
                """,
                (limit,),
            )
            rows = [dict(r) for r in cursor.fetchall()]
        return RecordList(rows, key="reserves")

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate insurance industry telemetry, capital safety & claim metrics."""
        with self._get_connection() as conn:
            licenses_cnt = conn.execute("SELECT COUNT(*) FROM insurance_licenses WHERE status = 'ACTIVE'").fetchone()[0]
            policies_cnt = conn.execute("SELECT COUNT(*) FROM insurance_policies WHERE status = 'IN_FORCE'").fetchone()[0]
            sum_insured_total = conn.execute("SELECT COALESCE(SUM(sum_insured_vnd), 0.0) FROM insurance_policies").fetchone()[0]
            premium_total = conn.execute("SELECT COALESCE(SUM(premium_vnd), 0.0) FROM insurance_policies").fetchone()[0]
            claims_cnt = conn.execute("SELECT COUNT(*) FROM claims_settlements").fetchone()[0]
            claims_settled_total = conn.execute(
                "SELECT COALESCE(SUM(net_settled_amount_vnd), 0.0) FROM claims_settlements WHERE settlement_status = 'SETTLED_APPROVED'"
            ).fetchone()[0]
            solvency_audits_cnt = conn.execute("SELECT COUNT(*) FROM solvency_audits").fetchone()[0]
            healthy_solvency_cnt = conn.execute(
                "SELECT COUNT(*) FROM solvency_audits WHERE solvency_status IN ('HEALTHY', 'COMPLIANT')"
            ).fetchone()[0]
            reserves_total = conn.execute("SELECT COALESCE(SUM(total_reserves_vnd), 0.0) FROM actuarial_reserves").fetchone()[0]

        loss_ratio = (claims_settled_total / premium_total * 100) if premium_total > 0 else 0.0

        return {
            "status": "online",
            "regulatory_framework": "Luật Kinh doanh bảo hiểm 2022 & Nghị định 46/2023/NĐ-CP",
            "regulatory_authority": "Bộ Tài chính (Cục Quản lý, giám sát bảo hiểm)",
            "metrics": {
                "active_insurers": licenses_cnt,
                "in_force_policies": policies_cnt,
                "total_sum_insured_vnd": float(sum_insured_total),
                "total_written_premium_vnd": float(premium_total),
                "total_claims_processed": claims_cnt,
                "total_claims_settled_vnd": float(claims_settled_total),
                "loss_ratio_percent": f"{loss_ratio:.2f}%",
                "solvency_audits_count": solvency_audits_cnt,
                "capital_compliant_insurers": healthy_solvency_cnt,
                "total_technical_reserves_vnd": float(reserves_total),
            },
        }
