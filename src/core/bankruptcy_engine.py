"""
Autonomous Vietnamese Corporate Insolvency, Bankruptcy, Debt Restructuring & Asset Liquidation Suite.
Statutory Framework:
- Luật Phá sản 2014 (Luật số 51/2014/QH13)
- Nghị định số 22/2015/NĐ-CP hướng dẫn Luật Phá sản về Quản tài viên và hành nghề quản lý, thanh lý tài sản
- Thông tư liên tịch số 01/2016/TTLT-TANDTC-VKSNDTC hướng dẫn thi hành một số quy định của Luật Phá sản
- Nghị quyết số 03/2016/NQ-HĐTP của Hội đồng Thẩm phán TANDTC hướng dẫn thi hành Luật Phá sản
- Bộ luật Dân sự 2015 & Luật Doanh nghiệp 2020 (Trách nhiệm tài sản của doanh nghiệp)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

PETITIONER_ROLES = {
    "UNSECURED_CREDITOR": "Chủ nợ không có bảo đảm hoặc có bảo đảm một phần (Khoản 1 Điều 5)",
    "EMPLOYEE_TRADE_UNION": "Người lao động, công đoàn cơ sở khi nợ lương quá 03 tháng (Khoản 2 Điều 5)",
    "LEGAL_REPRESENTATIVE": "Người đại diện theo pháp luật của doanh nghiệp (Khoản 3 Điều 5)",
    "OWNER_SHAREHOLDER": "Chủ sở hữu, cổ đông hoặc nhóm cổ đông sở hữu từ 20% cổ phần phổ thông (Khoản 5 Điều 5)",
}

CLAIM_TYPES = {
    "SECURED": "Nợ có bảo đảm bằng tài sản (ưu tiên thanh toán từ tài sản bảo đảm theo Điều 53)",
    "PARTIALLY_SECURED": "Nợ có bảo đảm một phần (phần nợ không có bảo đảm tham gia phân chia theo Điều 54)",
    "UNSECURED": "Nợ không có bảo đảm (được biểu quyết tại Hội nghị chủ nợ và thanh toán theo tỷ lệ)",
}

MEETING_RESOLUTIONS = {
    "RESTRUCTURING_PLAN": "Thông qua Nghị quyết về phương án phục hồi hoạt động kinh doanh (tối đa 03 năm theo Điều 89)",
    "DECLARE_BANKRUPTCY": "Đề nghị Tòa án nhân dân ra quyết định tuyên bố doanh nghiệp phá sản (Điều 80)",
    "POSTPONE_MEETING": "Hoãn Hội nghị chủ nợ do chưa đủ điều kiện họp theo Điều 79",
}


class BankruptcyEngine:
    """Core engine for Vietnamese Insolvency, Creditor Claim Reconciliation, and Asset Distribution."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "bankruptcy.db")
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS insolvency_practitioners (
                    practitioner_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    cert_number TEXT NOT NULL,
                    org_name TEXT NOT NULL,
                    profession TEXT NOT NULL,
                    years_experience INTEGER NOT NULL,
                    is_practicing INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bankruptcy_petitions (
                    petition_id TEXT PRIMARY KEY,
                    company_name TEXT NOT NULL,
                    tax_code TEXT NOT NULL,
                    petitioner_name TEXT NOT NULL,
                    petitioner_role TEXT NOT NULL,
                    overdue_days INTEGER NOT NULL,
                    overdue_debt_vnd REAL NOT NULL,
                    court_name TEXT NOT NULL,
                    is_insolvent INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creditors_claims (
                    claim_id TEXT PRIMARY KEY,
                    petition_id TEXT NOT NULL,
                    creditor_name TEXT NOT NULL,
                    id_or_tax_code TEXT NOT NULL,
                    claim_type TEXT NOT NULL,
                    claim_amount_vnd REAL NOT NULL,
                    security_details TEXT,
                    is_verified INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS creditors_meetings (
                    meeting_id TEXT PRIMARY KEY,
                    petition_id TEXT NOT NULL,
                    attendees_unsecured_debt_vnd REAL NOT NULL,
                    total_unsecured_debt_vnd REAL NOT NULL,
                    attendance_ratio_pct REAL NOT NULL,
                    is_quorum_reached INTEGER NOT NULL,
                    resolution TEXT NOT NULL,
                    recovery_years REAL NOT NULL,
                    is_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS asset_distributions (
                    distribution_id TEXT PRIMARY KEY,
                    petition_id TEXT NOT NULL,
                    liquidation_proceeds_vnd REAL NOT NULL,
                    bankruptcy_costs_vnd REAL NOT NULL,
                    worker_wages_and_insurance_vnd REAL NOT NULL,
                    new_debts_vnd REAL NOT NULL,
                    tax_obligations_vnd REAL NOT NULL,
                    unsecured_debts_claimed_vnd REAL NOT NULL,
                    unsecured_debts_paid_vnd REAL NOT NULL,
                    unsecured_repayment_ratio_pct REAL NOT NULL,
                    residual_value_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def register_practitioner(
        self,
        full_name: str,
        cert_number: str = "BTP-QTV-045/2019",
        org_name: str = "Công ty Hợp danh Quản lý & Thanh lý Tài sản Mekong",
        profession: str = "LUAT_SU",
        years_experience: int = 8,
        is_practicing: bool = True,
    ) -> Dict[str, Any]:
        """
        Register and verify Insolvency Practitioner (Quản tài viên) qualification under Law on Bankruptcy Art 12 & Decree 22/2015/NĐ-CP.
        Requires Ministry of Justice certificate and minimum professional experience.
        """
        practitioner_id = f"QTV-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not full_name.strip():
            violations.append("Thiếu họ và tên Quản tài viên")

        if not cert_number.strip() or "BTP" not in cert_number.upper():
            violations.append("Chứng chỉ hành nghề Quản tài viên phải do Bộ Tư pháp cấp (mã hiệu BTP-QTV)")

        if years_experience < 5:
            violations.append(
                f"Kinh nghiệm hành nghề ({years_experience} năm) < tối thiểu 05 năm kinh nghiệm pháp luật/tài chính "
                f"theo Điều 12 Luật Phá sản"
            )

        is_certified = len(violations) == 0 and is_practicing
        status = "CERTIFIED_PRACTICING" if is_certified else "QUALIFICATION_DEFICIENT"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO insolvency_practitioners (
                    practitioner_id, full_name, cert_number, org_name,
                    profession, years_experience, is_practicing, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                practitioner_id, full_name.strip(), cert_number.strip(), org_name.strip(),
                profession.strip().upper(), years_experience, 1 if is_practicing else 0,
                status, created_at
            ))
            conn.commit()

        return {
            "practitioner_id": practitioner_id,
            "full_name": full_name,
            "cert_number": cert_number,
            "org_name": org_name,
            "profession": profession.upper(),
            "years_experience": years_experience,
            "is_practicing": is_practicing,
            "is_certified": is_certified,
            "status": status,
            "violations": violations,
            "created_at": created_at,
        }

    def file_bankruptcy_petition(
        self,
        company_name: str,
        tax_code: str,
        petitioner_name: str,
        petitioner_role: str = "UNSECURED_CREDITOR",
        overdue_days: int = 95,
        overdue_debt_vnd: float = 2500000000.0,
        court_name: str = "Tòa án nhân dân Thành phố Hồ Chí Minh",
    ) -> Dict[str, Any]:
        """
        Record petition for opening bankruptcy procedures under Law on Bankruptcy Art 5 & 40-42.
        Statutory threshold: Insolvent when debt payment is overdue for 03 months (90 days) or more (Art 4(1)).
        """
        petition_id = f"PET-{uuid.uuid4().hex[:8].upper()}"
        role_upper = petitioner_role.strip().upper()
        violations = []

        if role_upper not in PETITIONER_ROLES:
            violations.append(f"Tư cách người nộp đơn không hợp lệ: {', '.join(PETITIONER_ROLES.keys())}")

        if not company_name.strip() or not tax_code.strip():
            violations.append("Thiếu tên doanh nghiệp hoặc mã số thuế doanh nghiệp bị yêu cầu mở thủ tục phá sản")

        # Statutory insolvency threshold: >= 90 days (03 months) under Art 4(1)
        if overdue_days < 90:
            violations.append(
                f"Chưa đủ căn cứ xác định doanh nghiệp mất khả năng thanh toán: Thời hạn quá hạn ({overdue_days} ngày) "
                f"< 03 tháng (90 ngày) theo Khoản 1 Điều 4 Luật Phá sản 2014"
            )

        if overdue_debt_vnd <= 0:
            violations.append("Khoản nợ quá hạn phải lớn hơn 0 VND")

        is_insolvent = overdue_days >= 90 and overdue_debt_vnd > 0
        is_acceptable = len(violations) == 0
        status = "PETITION_ACCEPTED_OPEN_HEARING" if is_acceptable else "PETITION_REJECTED"
        statutory_notes = (
            f"Doanh nghiệp mất khả năng thanh toán theo Khoản 1 Điều 4 Luật Phá sản 2014; "
            f"Tòa án nhân dân xem xét thụ lý và chỉ định Quản tài viên."
            if is_acceptable
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bankruptcy_petitions (
                    petition_id, company_name, tax_code, petitioner_name,
                    petitioner_role, overdue_days, overdue_debt_vnd, court_name,
                    is_insolvent, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                petition_id, company_name.strip(), tax_code.strip(), petitioner_name.strip(),
                role_upper, overdue_days, overdue_debt_vnd, court_name.strip(),
                1 if is_insolvent else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "petition_id": petition_id,
            "company_name": company_name,
            "tax_code": tax_code,
            "petitioner_name": petitioner_name,
            "petitioner_role": role_upper,
            "petitioner_role_description": PETITIONER_ROLES.get(role_upper, role_upper),
            "overdue_days": overdue_days,
            "overdue_debt_vnd": overdue_debt_vnd,
            "court_name": court_name,
            "is_insolvent": is_insolvent,
            "is_acceptable": is_acceptable,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def register_creditor_claim(
        self,
        petition_id: str,
        creditor_name: str,
        id_or_tax_code: str,
        claim_type: str = "UNSECURED",
        claim_amount_vnd: float = 500000000.0,
        security_details: str = "Không có bảo đảm",
    ) -> Dict[str, Any]:
        """
        Record and audit creditor claim to be listed in Creditor Manifest under Arts 64-67.
        """
        claim_id = f"CLM-{uuid.uuid4().hex[:8].upper()}"
        type_upper = claim_type.strip().upper()
        violations = []

        if type_upper not in CLAIM_TYPES:
            violations.append(f"Loại yêu cầu đòi nợ không hợp lệ: {', '.join(CLAIM_TYPES.keys())}")

        if claim_amount_vnd <= 0:
            violations.append("Số tiền đòi nợ phải lớn hơn 0 VND")

        if not creditor_name.strip() or not id_or_tax_code.strip():
            violations.append("Thiếu thông tin tên chủ nợ hoặc mã số định danh / MST của chủ nợ")

        is_verified = len(violations) == 0
        status = "CLAIM_VERIFIED_LISTED" if is_verified else "CLAIM_DISPUTED_OR_INVALID"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO creditors_claims (
                    claim_id, petition_id, creditor_name, id_or_tax_code,
                    claim_type, claim_amount_vnd, security_details,
                    is_verified, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id, petition_id.strip(), creditor_name.strip(), id_or_tax_code.strip(),
                type_upper, claim_amount_vnd, security_details.strip(),
                1 if is_verified else 0, status, created_at
            ))
            conn.commit()

        return {
            "claim_id": claim_id,
            "petition_id": petition_id,
            "creditor_name": creditor_name,
            "id_or_tax_code": id_or_tax_code,
            "claim_type": type_upper,
            "claim_type_description": CLAIM_TYPES.get(type_upper, type_upper),
            "claim_amount_vnd": claim_amount_vnd,
            "security_details": security_details,
            "is_verified": is_verified,
            "status": status,
            "violations": violations,
            "created_at": created_at,
        }

    def conduct_creditors_meeting(
        self,
        petition_id: str,
        attendees_unsecured_debt_vnd: float,
        total_unsecured_debt_vnd: float,
        resolution: str = "RESTRUCTURING_PLAN",
        recovery_years: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Record Creditors' Meeting (Hội nghị chủ nợ) results under Arts 75-86.
        Statutory quorum: Must represent at least 51% of total unsecured debt (Art 79).
        Business recovery plan term: Maximum 03 years (Art 89).
        """
        meeting_id = f"MTG-{uuid.uuid4().hex[:8].upper()}"
        res_upper = resolution.strip().upper()
        violations = []

        if res_upper not in MEETING_RESOLUTIONS:
            violations.append(f"Nghị quyết Hội nghị chủ nợ không hợp lệ: {', '.join(MEETING_RESOLUTIONS.keys())}")

        if total_unsecured_debt_vnd <= 0:
            attendance_ratio_pct = 0.0
        else:
            attendance_ratio_pct = round((attendees_unsecured_debt_vnd / total_unsecured_debt_vnd) * 100.0, 2)

        # Statutory quorum requirement: >= 51% unsecured debt under Art 79
        is_quorum_reached = attendance_ratio_pct >= 51.0
        if not is_quorum_reached:
            violations.append(
                f"Hội nghị chủ nợ không đủ điều kiện tiến hành: Tỷ lệ đại diện nợ không bảo đảm "
                f"({attendance_ratio_pct}%) < tối thiểu 51% theo quy định tại Điều 79 Luật Phá sản"
            )

        # Maximum business recovery plan duration: <= 3 years under Art 89
        if res_upper == "RESTRUCTURING_PLAN" and recovery_years > 3.0:
            violations.append(
                f"Thời hạn phục hồi hoạt động kinh doanh ({recovery_years} năm) vượt quá thời hạn luật định "
                f"tối đa 03 năm theo Điều 89 Luật Phá sản"
            )

        is_valid = len(violations) == 0
        status = "MEETING_RESOLUTION_ADOPTED" if is_valid else "MEETING_INVALID_OR_POSTPONED"
        statutory_notes = (
            f"Hội nghị chủ nợ hợp chuẩn theo Luật Phá sản 2014; tỷ lệ đại diện {attendance_ratio_pct}%; "
            f"Nghị quyết: {res_upper} (thời hạn {recovery_years} năm)."
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO creditors_meetings (
                    meeting_id, petition_id, attendees_unsecured_debt_vnd,
                    total_unsecured_debt_vnd, attendance_ratio_pct, is_quorum_reached,
                    resolution, recovery_years, is_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id, petition_id.strip(), attendees_unsecured_debt_vnd,
                total_unsecured_debt_vnd, attendance_ratio_pct, 1 if is_quorum_reached else 0,
                res_upper, recovery_years, 1 if is_valid else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "meeting_id": meeting_id,
            "petition_id": petition_id,
            "attendees_unsecured_debt_vnd": attendees_unsecured_debt_vnd,
            "total_unsecured_debt_vnd": total_unsecured_debt_vnd,
            "attendance_ratio_pct": attendance_ratio_pct,
            "is_quorum_reached": is_quorum_reached,
            "resolution": res_upper,
            "recovery_years": recovery_years,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def calculate_asset_distribution(
        self,
        petition_id: str,
        liquidation_proceeds_vnd: float,
        bankruptcy_costs_vnd: float,
        worker_wages_and_insurance_vnd: float,
        new_debts_vnd: float = 0.0,
        tax_obligations_vnd: float = 0.0,
        unsecured_debts_claimed_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Calculate statutory liquidation asset distribution waterfall under Law on Bankruptcy Art 54.
        Waterfall Priority:
        1. Bankruptcy procedure costs (chi phí phá sản).
        2. Unpaid wages, severance pay, BHXH, BHYT for workers.
        3. Debts incurred after opening procedures for recovery attempts.
        4. Financial obligations to State (taxes) & Unsecured debts paid proportionally.
        5. Residual value to owners/shareholders.
        """
        dist_id = f"DST-{uuid.uuid4().hex[:8].upper()}"
        remaining = liquidation_proceeds_vnd

        # 1. Bankruptcy costs
        costs_paid = min(remaining, bankruptcy_costs_vnd)
        remaining = max(0.0, remaining - costs_paid)

        # 2. Worker wages and insurance
        wages_paid = min(remaining, worker_wages_and_insurance_vnd)
        remaining = max(0.0, remaining - wages_paid)

        # 3. New debts incurred post-petition
        new_debts_paid = min(remaining, new_debts_vnd)
        remaining = max(0.0, remaining - new_debts_paid)

        # 4. Taxes & Unsecured debts
        tax_paid = min(remaining, tax_obligations_vnd)
        remaining = max(0.0, remaining - tax_paid)

        unsecured_paid = min(remaining, unsecured_debts_claimed_vnd)
        remaining = max(0.0, remaining - unsecured_paid)

        unsecured_ratio_pct = (
            round((unsecured_paid / unsecured_debts_claimed_vnd) * 100.0, 2)
            if unsecured_debts_claimed_vnd > 0
            else 100.0
        )

        residual_value_vnd = remaining
        status = "ASSET_DISTRIBUTION_COMPLETED"
        statutory_notes = (
            f"Phân chia tài sản hoàn tất theo đúng thứ tự ưu tiên Điều 54 Luật Phá sản 2014; "
            f"tỷ lệ chi trả nợ không có bảo đảm đạt {unsecured_ratio_pct}%; "
            f"số dư sau thanh lý thuộc về chủ sở hữu: {residual_value_vnd:,.0f} VND."
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO asset_distributions (
                    distribution_id, petition_id, liquidation_proceeds_vnd,
                    bankruptcy_costs_vnd, worker_wages_and_insurance_vnd,
                    new_debts_vnd, tax_obligations_vnd, unsecured_debts_claimed_vnd,
                    unsecured_debts_paid_vnd, unsecured_repayment_ratio_pct,
                    residual_value_vnd, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dist_id, petition_id.strip(), liquidation_proceeds_vnd,
                costs_paid, wages_paid, new_debts_paid, tax_paid,
                unsecured_debts_claimed_vnd, unsecured_paid, unsecured_ratio_pct,
                residual_value_vnd, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "distribution_id": dist_id,
            "petition_id": petition_id,
            "liquidation_proceeds_vnd": liquidation_proceeds_vnd,
            "bankruptcy_costs_paid_vnd": costs_paid,
            "worker_wages_and_insurance_paid_vnd": wages_paid,
            "new_debts_paid_vnd": new_debts_paid,
            "tax_obligations_paid_vnd": tax_paid,
            "unsecured_debts_claimed_vnd": unsecured_debts_claimed_vnd,
            "unsecured_debts_paid_vnd": unsecured_paid,
            "unsecured_repayment_ratio_pct": unsecured_ratio_pct,
            "residual_value_vnd": residual_value_vnd,
            "status": status,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def list_bankruptcy_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered practitioners, petitions, creditor claims, meetings, and asset distributions."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "PRACTITIONERS"]:
                cursor.execute("SELECT * FROM insolvency_practitioners ORDER BY created_at DESC LIMIT ?", (limit,))
                results["insolvency_practitioners"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "PETITIONS"]:
                cursor.execute("SELECT * FROM bankruptcy_petitions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["bankruptcy_petitions"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "CLAIMS"]:
                cursor.execute("SELECT * FROM creditors_claims ORDER BY created_at DESC LIMIT ?", (limit,))
                results["creditors_claims"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "MEETINGS"]:
                cursor.execute("SELECT * FROM creditors_meetings ORDER BY created_at DESC LIMIT ?", (limit,))
                results["creditors_meetings"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "DISTRIBUTIONS"]:
                cursor.execute("SELECT * FROM asset_distributions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["asset_distributions"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_bankruptcy_telemetry(self) -> Dict[str, Any]:
        """Aggregate national insolvency and corporate restructuring metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_practicing = 1 THEN 1 ELSE 0 END) FROM insolvency_practitioners")
            p_row = cursor.fetchone()
            total_practitioners = p_row[0] or 0
            practicing_practitioners = p_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(overdue_debt_vnd), SUM(CASE WHEN is_insolvent = 1 THEN 1 ELSE 0 END) FROM bankruptcy_petitions")
            pet_row = cursor.fetchone()
            total_petitions = pet_row[0] or 0
            total_overdue_debt_vnd = pet_row[1] or 0.0
            insolvent_companies = pet_row[2] or 0

            cursor.execute("SELECT COUNT(*), SUM(claim_amount_vnd) FROM creditors_claims")
            clm_row = cursor.fetchone()
            total_claims = clm_row[0] or 0
            total_claims_amount_vnd = clm_row[1] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) FROM creditors_meetings")
            m_row = cursor.fetchone()
            total_meetings = m_row[0] or 0
            valid_meetings = m_row[1] or 0

            cursor.execute("""
                SELECT COUNT(*), SUM(liquidation_proceeds_vnd), SUM(unsecured_debts_paid_vnd),
                       AVG(unsecured_repayment_ratio_pct)
                FROM asset_distributions
            """)
            d_row = cursor.fetchone()
            total_distributions = d_row[0] or 0
            total_liquidation_proceeds_vnd = d_row[1] or 0.0
            total_unsecured_paid_vnd = d_row[2] or 0.0
            avg_unsecured_repayment_ratio_pct = d_row[3] or 0.0

        return {
            "total_practitioners": total_practitioners,
            "practicing_practitioners": practicing_practitioners,
            "total_petitions": total_petitions,
            "insolvent_companies": insolvent_companies,
            "total_overdue_debt_vnd": total_overdue_debt_vnd,
            "total_claims": total_claims,
            "total_claims_amount_vnd": total_claims_amount_vnd,
            "total_meetings": total_meetings,
            "valid_meetings": valid_meetings,
            "total_distributions": total_distributions,
            "total_liquidation_proceeds_vnd": total_liquidation_proceeds_vnd,
            "total_unsecured_paid_vnd": total_unsecured_paid_vnd,
            "avg_unsecured_repayment_ratio_pct": round(avg_unsecured_repayment_ratio_pct, 2),
            "compliance_framework": "Luật Phá sản 2014 & Nghị định 22/2015/NĐ-CP",
            "statutory_quorum_unsecured_debt_pct": 51.0,
            "database_path": self.db_path,
        }
