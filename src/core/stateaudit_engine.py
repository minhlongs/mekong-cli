"""
Vietnamese State Audit, Supreme Audit Institution (SAV / KTNN) & Public Financial Oversight Suite.
Governed by:
- Law on State Audit 2015 (Law No. 81/2015/QH13) and Amending Law 2019 (Law No. 55/2019/QH14)
- Constitution of the Socialist Republic of Vietnam 2013 (Article 118)
- Resolution No. 999/2020/UBTVQH14 (Development Strategy of the State Audit of Vietnam)
- Decree No. 162/2021/NĐ-CP (Sanctions in the Field of State Audit)

Pure standard library implementation adhering to the core boundary invariant.
Thread-safe SQLite backend with WAL mode enabled.
"""

from __future__ import annotations

import datetime
import os
import pathlib
import sqlite3
import typing
from typing import Any, Dict, List, Optional

DEFAULT_DB_PATH = os.path.expanduser(
    os.getenv("MEKONG_STATEAUDIT_DB", "~/.mekong/stateaudit.db")
)

# Audited entity types under Article 55 of Law 81/2015/QH13
VALID_ENTITY_TYPES = {
    "MINISTRY",                    # Bộ, cơ quan ngang Bộ
    "PROVINCIAL_GOVERNMENT",       # UBND, HĐND cấp tỉnh/thành phố
    "STATE_OWNED_ENTERPRISE",      # Tập đoàn, Tổng công ty Nhà nước
    "PROJECT_MANAGEMENT_UNIT",     # Ban Quản lý dự án ODA, PPP, công trình quốc gia
    "POLITICAL_ORGANIZATION",      # Cơ quan trung ương của tổ chức chính trị - xã hội
}

# 3 Canonical Audit Types under Article 10
VALID_AUDIT_TYPES = {
    "FINANCIAL_AUDIT",             # Kiểm toán báo cáo tài chính & quyết toán NSNN
    "COMPLIANCE_AUDIT",            # Kiểm toán tuân thủ pháp luật ngân sách, đầu tư, mua sắm
    "PERFORMANCE_AUDIT",           # Kiểm toán hoạt động (Tính kinh tế, hiệu quả, hiệu lực - 3E)
    "COMPREHENSIVE_AUDIT",         # Kiểm toán tích hợp tổng thể
}

# Finding domains
VALID_DOMAINS = {
    "BUDGET_REVENUE",              # Thu ngân sách nhà nước, thuế, phí, lệ phí
    "BUDGET_EXPENDITURE",          # Chi ngân sách nhà nước, chi thường xuyên
    "PUBLIC_INVESTMENT",           # Đầu tư công, giải ngân xây lắp, đền bù GPMB
    "ASSET_MANAGEMENT",            # Quản lý, sử dụng tài sản công, đất công
    "PROCUREMENT",                 # Đấu thầu, mua sắm công, ký kết hợp đồng
    "TAX_COLLECTION",              # Quản lý thu thuế và chống thất thu ngân sách
}

# Finding severities
VALID_SEVERITIES = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}

# Statutory recommendations under Articles 37 & 48
VALID_RECOMMENDATION_TYPES = {
    "REVENUE_INCREASE",            # Tăng thu NSNN (thuế, phí, tiền sử dụng đất)
    "EXPENDITURE_DISALLOWANCE",    # Giảm chi NSNN (giảm trừ thanh quyết toán, thu hồi dự toán)
    "REIMBURSEMENT",               # Thu hồi nộp NSNN (tạm ứng quá hạn, chi sai chế độ)
    "OTHER_FINANCIAL_REMEDIATION", # Xử lý tài chính khác (ghi thu - ghi chi, điều chỉnh sổ kế toán)
    "DISCIPLINARY_ACTION",         # Kiến nghị xử lý kỷ luật cán bộ, tập thể sai phạm
    "CRIMINAL_REFERRAL",           # Chuyển hồ sơ sang Cơ quan Điều tra Bộ Công an (C03)
}

# Recommendation implementation statuses
VALID_RECOMMENDATION_STATUSES = {
    "PENDING",
    "PARTIALLY_IMPLEMENTED",
    "FULLY_IMPLEMENTED",
    "OVERDUE",
}

# Engagement statuses
VALID_ENGAGEMENT_STATUSES = {
    "PLANNED",
    "IN_PROGRESS",
    "CONCLUDED",
    "PUBLISHED",
}


class StateAuditEngine:
    """
    Core engine managing Vietnamese State Audit (Kiểm toán Nhà nước - KTNN) missions,
    statutory audit findings, financial & accountability recommendations, and fiscal recovery tracking.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            db_path = os.environ.get(
                "MEKONG_STATEAUDIT_DB",
                os.path.expanduser("~/.mekong/stateaudit.db")
            )
        self.db_path = os.path.expanduser(db_path)
        pathlib.Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS audit_engagements (
                    engagement_code TEXT PRIMARY KEY,
                    decision_number TEXT NOT NULL,
                    audited_entity TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    audit_type TEXT NOT NULL,
                    audit_scope_year INTEGER NOT NULL,
                    lead_auditor TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'IN_PROGRESS',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_findings (
                    finding_code TEXT PRIMARY KEY,
                    engagement_code TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    description TEXT NOT NULL,
                    statutory_violation TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'MEDIUM',
                    evidence_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(engagement_code) REFERENCES audit_engagements(engagement_code)
                );

                CREATE TABLE IF NOT EXISTS audit_recommendations (
                    recommendation_code TEXT PRIMARY KEY,
                    finding_code TEXT NOT NULL,
                    engagement_code TEXT NOT NULL,
                    recommendation_type TEXT NOT NULL,
                    amount_vnd REAL NOT NULL DEFAULT 0.0,
                    description TEXT NOT NULL,
                    target_agency TEXT NOT NULL,
                    settlement_deadline TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    amount_implemented_vnd REAL NOT NULL DEFAULT 0.0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(finding_code) REFERENCES audit_findings(finding_code),
                    FOREIGN KEY(engagement_code) REFERENCES audit_engagements(engagement_code)
                );

                CREATE TABLE IF NOT EXISTS recommendation_settlements (
                    settlement_id TEXT PRIMARY KEY,
                    recommendation_code TEXT NOT NULL,
                    settlement_date TEXT NOT NULL,
                    amount_settled_vnd REAL NOT NULL DEFAULT 0.0,
                    treasury_voucher_number TEXT NOT NULL,
                    evidence_notes TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(recommendation_code) REFERENCES audit_recommendations(recommendation_code)
                );

                CREATE INDEX IF NOT EXISTS idx_find_eng ON audit_findings(engagement_code);
                CREATE INDEX IF NOT EXISTS idx_rec_find ON audit_recommendations(finding_code);
                CREATE INDEX IF NOT EXISTS idx_rec_eng ON audit_recommendations(engagement_code);
                CREATE INDEX IF NOT EXISTS idx_rec_type ON audit_recommendations(recommendation_type);
                CREATE INDEX IF NOT EXISTS idx_settle_rec ON recommendation_settlements(recommendation_code);
                """
            )

    def register_engagement(
        self,
        engagement_code: str,
        decision_number: str,
        audited_entity: str,
        entity_type: str,
        audit_type: str,
        audit_scope_year: int,
        lead_auditor: str,
        start_date: str,
        end_date: str,
        status: str = "IN_PROGRESS",
    ) -> Dict[str, Any]:
        """
        Register a formal State Audit engagement pursuant to Decision by the State Auditor General.
        """
        code = engagement_code.strip()
        dec_no = decision_number.strip()
        entity = audited_entity.strip()
        etype = entity_type.strip().upper()
        atype = audit_type.strip().upper()
        lead = lead_auditor.strip()
        stat = status.strip().upper()

        if not code or not dec_no or not entity or not lead:
            raise ValueError("engagement_code, decision_number, audited_entity, and lead_auditor cannot be empty.")
        if etype not in VALID_ENTITY_TYPES:
            raise ValueError(f"Invalid entity_type '{etype}'. Must be one of: {sorted(VALID_ENTITY_TYPES)}")
        if atype not in VALID_AUDIT_TYPES:
            raise ValueError(f"Invalid audit_type '{atype}'. Must be one of: {sorted(VALID_AUDIT_TYPES)}")
        if stat not in VALID_ENGAGEMENT_STATUSES:
            raise ValueError(f"Invalid status '{stat}'. Must be one of: {sorted(VALID_ENGAGEMENT_STATUSES)}")
        if audit_scope_year < 1990 or audit_scope_year > 2100:
            raise ValueError(f"Invalid audit_scope_year '{audit_scope_year}'.")

        try:
            s_dt = datetime.date.fromisoformat(start_date.strip())
            e_dt = datetime.date.fromisoformat(end_date.strip())
        except ValueError:
            raise ValueError("start_date and end_date must be in YYYY-MM-DD format.")

        if e_dt < s_dt:
            raise ValueError("end_date cannot be earlier than start_date.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT engagement_code FROM audit_engagements WHERE engagement_code = ?", (code,))
            if cur.fetchone():
                raise ValueError(f"Audit engagement '{code}' already exists.")

            cur.execute(
                """
                INSERT INTO audit_engagements (
                    engagement_code, decision_number, audited_entity, entity_type,
                    audit_type, audit_scope_year, lead_auditor, start_date, end_date,
                    status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    code, dec_no, entity, etype, atype, int(audit_scope_year),
                    lead, s_dt.isoformat(), e_dt.isoformat(), stat, created_at,
                ),
            )
            conn.commit()

        return {
            "engagement_code": code,
            "decision_number": dec_no,
            "audited_entity": entity,
            "entity_type": etype,
            "audit_type": atype,
            "audit_scope_year": int(audit_scope_year),
            "lead_auditor": lead,
            "start_date": s_dt.isoformat(),
            "end_date": e_dt.isoformat(),
            "status": stat,
            "created_at": created_at,
        }

    def record_finding(
        self,
        finding_code: str,
        engagement_code: str,
        domain: str,
        description: str,
        statutory_violation: str,
        severity: str = "MEDIUM",
        evidence_summary: str = "",
    ) -> Dict[str, Any]:
        """
        Record a discovered fiscal infraction, compliance defect, or 3E inefficiency in State Audit delegation notes.
        """
        fcode = finding_code.strip()
        ecode = engagement_code.strip()
        dom = domain.strip().upper()
        desc = description.strip()
        violation = statutory_violation.strip()
        sev = severity.strip().upper()

        if not fcode or not desc or not violation:
            raise ValueError("finding_code, description, and statutory_violation cannot be empty.")
        if dom not in VALID_DOMAINS:
            raise ValueError(f"Invalid domain '{dom}'. Must be one of: {sorted(VALID_DOMAINS)}")
        if sev not in VALID_SEVERITIES:
            raise ValueError(f"Invalid severity '{sev}'. Must be one of: {sorted(VALID_SEVERITIES)}")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT engagement_code FROM audit_engagements WHERE engagement_code = ?", (ecode,))
            if not cur.fetchone():
                raise ValueError(f"Audit engagement '{ecode}' does not exist.")

            cur.execute("SELECT finding_code FROM audit_findings WHERE finding_code = ?", (fcode,))
            if cur.fetchone():
                raise ValueError(f"Audit finding '{fcode}' already exists.")

            cur.execute(
                """
                INSERT INTO audit_findings (
                    finding_code, engagement_code, domain, description,
                    statutory_violation, severity, evidence_summary, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (fcode, ecode, dom, desc, violation, sev, evidence_summary.strip(), created_at),
            )
            conn.commit()

        return {
            "finding_code": fcode,
            "engagement_code": ecode,
            "domain": dom,
            "description": desc,
            "statutory_violation": violation,
            "severity": sev,
            "evidence_summary": evidence_summary.strip(),
            "created_at": created_at,
        }

    def issue_recommendation(
        self,
        recommendation_code: str,
        finding_code: str,
        recommendation_type: str,
        description: str,
        target_agency: str,
        settlement_deadline: str,
        amount_vnd: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Issue a formal State Audit Recommendation under Articles 37 & 48 of Law 81/2015/QH13.
        Includes fiscal recoveries (tăng thu, giảm chi, thu hồi) and accountability actions.
        """
        rcode = recommendation_code.strip()
        fcode = finding_code.strip()
        rtype = recommendation_type.strip().upper()
        desc = description.strip()
        target = target_agency.strip()

        if not rcode or not desc or not target:
            raise ValueError("recommendation_code, description, and target_agency cannot be empty.")
        if rtype not in VALID_RECOMMENDATION_TYPES:
            raise ValueError(f"Invalid recommendation_type '{rtype}'. Must be one of: {sorted(VALID_RECOMMENDATION_TYPES)}")
        if amount_vnd < 0:
            raise ValueError("amount_vnd cannot be negative.")

        try:
            deadline_dt = datetime.date.fromisoformat(settlement_deadline.strip())
        except ValueError:
            raise ValueError("settlement_deadline must be in YYYY-MM-DD format.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT finding_code, engagement_code FROM audit_findings WHERE finding_code = ?", (fcode,))
            f_row = cur.fetchone()
            if not f_row:
                raise ValueError(f"Finding '{fcode}' does not exist.")

            ecode = f_row["engagement_code"]

            cur.execute("SELECT recommendation_code FROM audit_recommendations WHERE recommendation_code = ?", (rcode,))
            if cur.fetchone():
                raise ValueError(f"Recommendation '{rcode}' already exists.")

            cur.execute(
                """
                INSERT INTO audit_recommendations (
                    recommendation_code, finding_code, engagement_code,
                    recommendation_type, amount_vnd, description,
                    target_agency, settlement_deadline, status,
                    amount_implemented_vnd, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', 0.0, ?)
                """,
                (
                    rcode, fcode, ecode, rtype, float(amount_vnd),
                    desc, target, deadline_dt.isoformat(), created_at,
                ),
            )
            conn.commit()

        return {
            "recommendation_code": rcode,
            "finding_code": fcode,
            "engagement_code": ecode,
            "recommendation_type": rtype,
            "amount_vnd": float(amount_vnd),
            "description": desc,
            "target_agency": target,
            "settlement_deadline": deadline_dt.isoformat(),
            "status": "PENDING",
            "amount_implemented_vnd": 0.0,
            "created_at": created_at,
        }

    def record_settlement(
        self,
        settlement_id: str,
        recommendation_code: str,
        settlement_date: str,
        treasury_voucher_number: str,
        amount_settled_vnd: float = 0.0,
        evidence_notes: str = "",
    ) -> Dict[str, Any]:
        """
        Record implementation/remediation by audited entity (nộp NSNN, giảm trừ quyết toán, hoặc kỷ luật).
        Updates cumulative settled amount and recommendation status.
        """
        sid = settlement_id.strip()
        rcode = recommendation_code.strip()
        voucher = treasury_voucher_number.strip()

        if not sid or not voucher:
            raise ValueError("settlement_id and treasury_voucher_number cannot be empty.")
        if amount_settled_vnd < 0:
            raise ValueError("amount_settled_vnd cannot be negative.")

        try:
            s_dt = datetime.date.fromisoformat(settlement_date.strip())
        except ValueError:
            raise ValueError("settlement_date must be in YYYY-MM-DD format.")

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT recommendation_code, amount_vnd, amount_implemented_vnd, status, recommendation_type
                FROM audit_recommendations WHERE recommendation_code = ?
                """,
                (rcode,),
            )
            rec = cur.fetchone()
            if not rec:
                raise ValueError(f"Recommendation '{rcode}' does not exist.")

            cur.execute("SELECT settlement_id FROM recommendation_settlements WHERE settlement_id = ?", (sid,))
            if cur.fetchone():
                raise ValueError(f"Settlement '{sid}' already exists.")

            cur.execute(
                """
                INSERT INTO recommendation_settlements (
                    settlement_id, recommendation_code, settlement_date,
                    amount_settled_vnd, treasury_voucher_number, evidence_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (sid, rcode, s_dt.isoformat(), float(amount_settled_vnd), voucher, evidence_notes.strip(), created_at),
            )

            current_impl = float(rec["amount_implemented_vnd"]) + float(amount_settled_vnd)
            total_req = float(rec["amount_vnd"])

            if total_req > 0:
                if current_impl >= total_req:
                    new_status = "FULLY_IMPLEMENTED"
                else:
                    new_status = "PARTIALLY_IMPLEMENTED"
            else:
                # Non-financial recommendation (e.g. disciplinary or administrative)
                new_status = "FULLY_IMPLEMENTED"

            cur.execute(
                """
                UPDATE audit_recommendations
                SET amount_implemented_vnd = ?, status = ?
                WHERE recommendation_code = ?
                """,
                (current_impl, new_status, rcode),
            )
            conn.commit()

        return {
            "settlement_id": sid,
            "recommendation_code": rcode,
            "settlement_date": s_dt.isoformat(),
            "amount_settled_vnd": float(amount_settled_vnd),
            "treasury_voucher_number": voucher,
            "cumulative_implemented_vnd": current_impl,
            "total_recommended_vnd": total_req,
            "new_status": new_status,
            "evidence_notes": evidence_notes.strip(),
            "created_at": created_at,
        }

    def conclude_engagement(
        self,
        engagement_code: str,
        status: str = "CONCLUDED",
    ) -> Dict[str, Any]:
        """
        Conclude or publish final audit report and recommendations.
        """
        code = engagement_code.strip()
        stat = status.strip().upper()
        if stat not in ("CONCLUDED", "PUBLISHED"):
            raise ValueError(f"status must be 'CONCLUDED' or 'PUBLISHED', got '{stat}'.")

        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT engagement_code, audited_entity FROM audit_engagements WHERE engagement_code = ?", (code,))
            row = cur.fetchone()
            if not row:
                raise ValueError(f"Engagement '{code}' not found.")

            cur.execute("UPDATE audit_engagements SET status = ? WHERE engagement_code = ?", (stat, code))
            conn.commit()

        return {
            "engagement_code": code,
            "audited_entity": row["audited_entity"],
            "status": stat,
            "status_updated": True,
        }

    def list_records(
        self,
        record_type: str = "all",
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        List audit engagements, findings, recommendations, and settlements.
        """
        rtype = record_type.strip().lower()
        lim = max(1, min(limit, 500))
        res: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cur = conn.cursor()
            if rtype in ("engagements", "all"):
                cur.execute("SELECT * FROM audit_engagements ORDER BY start_date DESC LIMIT ?", (lim,))
                res["engagements"] = [dict(r) for r in cur.fetchall()]

            if rtype in ("findings", "all"):
                cur.execute("SELECT * FROM audit_findings ORDER BY created_at DESC LIMIT ?", (lim,))
                res["findings"] = [dict(r) for r in cur.fetchall()]

            if rtype in ("recommendations", "all"):
                cur.execute("SELECT * FROM audit_recommendations ORDER BY created_at DESC LIMIT ?", (lim,))
                res["recommendations"] = [dict(r) for r in cur.fetchall()]

            if rtype in ("settlements", "all"):
                cur.execute("SELECT * FROM recommendation_settlements ORDER BY settlement_date DESC LIMIT ?", (lim,))
                res["settlements"] = [dict(r) for r in cur.fetchall()]

        return res

    def get_telemetry_status(self) -> Dict[str, Any]:
        """
        Aggregate executive oversight metrics of the State Audit system:
        total missions, financial recovery recommendations by type, implementation rates, and criminal referrals.
        """
        today_iso = datetime.date.today().isoformat()

        with self._get_connection() as conn:
            cur = conn.cursor()

            # Engagements breakdown
            cur.execute("SELECT COUNT(*) AS total FROM audit_engagements")
            total_eng = cur.fetchone()["total"] or 0

            cur.execute("SELECT COUNT(*) AS c FROM audit_engagements WHERE status = 'IN_PROGRESS'")
            in_progress_eng = cur.fetchone()["c"] or 0

            cur.execute("SELECT COUNT(*) AS c FROM audit_engagements WHERE status IN ('CONCLUDED', 'PUBLISHED')")
            concluded_eng = cur.fetchone()["c"] or 0

            # Findings count and severity
            cur.execute("SELECT COUNT(*) AS c FROM audit_findings")
            total_findings = cur.fetchone()["c"] or 0

            cur.execute("SELECT severity, COUNT(*) AS c FROM audit_findings GROUP BY severity")
            severity_breakdown = {r["severity"]: r["c"] for r in cur.fetchall()}

            # Recommendations breakdown
            cur.execute(
                """
                SELECT COUNT(*) AS c, SUM(amount_vnd) AS total_vnd, SUM(amount_implemented_vnd) AS impl_vnd
                FROM audit_recommendations
                """
            )
            rec_row = cur.fetchone()
            total_recs = rec_row["c"] or 0
            total_rec_vnd = float(rec_row["total_vnd"] or 0.0)
            total_impl_vnd = float(rec_row["impl_vnd"] or 0.0)
            impl_rate = round((total_impl_vnd / total_rec_vnd * 100.0), 2) if total_rec_vnd > 0 else 0.0

            cur.execute(
                """
                SELECT recommendation_type, COUNT(*) AS c, SUM(amount_vnd) AS total_vnd, SUM(amount_implemented_vnd) AS impl_vnd
                FROM audit_recommendations
                GROUP BY recommendation_type
                """
            )
            type_breakdown = {
                r["recommendation_type"]: {
                    "count": r["c"],
                    "recommended_vnd": float(r["total_vnd"] or 0.0),
                    "implemented_vnd": float(r["impl_vnd"] or 0.0),
                }
                for r in cur.fetchall()
            }

            cur.execute("SELECT COUNT(*) AS c FROM audit_recommendations WHERE recommendation_type = 'CRIMINAL_REFERRAL'")
            criminal_referrals = cur.fetchone()["c"] or 0

            cur.execute("SELECT COUNT(*) AS c FROM audit_recommendations WHERE recommendation_type = 'DISCIPLINARY_ACTION'")
            disciplinary_actions = cur.fetchone()["c"] or 0

            cur.execute(
                """
                SELECT COUNT(*) AS c FROM audit_recommendations
                WHERE status IN ('PENDING', 'PARTIALLY_IMPLEMENTED') AND settlement_deadline < ?
                """,
                (today_iso,),
            )
            overdue_recs = cur.fetchone()["c"] or 0

        return {
            "total_audit_engagements": total_eng,
            "engagements_in_progress": in_progress_eng,
            "engagements_concluded": concluded_eng,
            "total_audit_findings": total_findings,
            "findings_by_severity": severity_breakdown,
            "total_recommendations": total_recs,
            "total_recommended_amount_vnd": total_rec_vnd,
            "total_implemented_amount_vnd": total_impl_vnd,
            "fiscal_implementation_rate_pct": impl_rate,
            "recommendations_by_type": type_breakdown,
            "criminal_referrals_count": criminal_referrals,
            "disciplinary_actions_count": disciplinary_actions,
            "overdue_recommendations_count": overdue_recs,
        }
