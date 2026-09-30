"""
Autonomous Vietnamese Judicial Expertise, Forensic Assessment & Electronic Evidence Suite.
Statutory Framework:
- Luật Giám định tư pháp 2012 (sửa đổi, bổ sung 2020, Luật số 56/2020/QH14)
- Nghị định số 157/2020/NĐ-CP & Nghị định số 85/2013/NĐ-CP hướng dẫn Luật Giám định tư pháp
- Bộ luật Tố tụng hình sự 2015 (Điều 99, 107 về thu thập, bảo quản chứng cứ điện tử; Điều 205-214 về giám định)
- Bộ luật Tố tụng dân sự 2015 (Điều 102 về trưng cầu, yêu cầu giám định)
- Bộ luật Hình sự 2015 (Điều 382 về tội cung cấp tài liệu sai sự thật hoặc khai báo gian dối)
- Pháp lệnh số 02/2012/UBTVQH13 về chi phí giám định, định giá; chi phí cho người làm chứng, người phiên dịch

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
import hashlib
from typing import Dict, Any, List, Optional

FORENSIC_DOMAINS = {
    "FINANCIAL_ACCOUNTING": "Giám định tài chính - kế toán, thuế, kiểm toán, thất thoát ngân sách",
    "DIGITAL_EVIDENCE": "Giám định kỹ thuật số, dữ liệu điện tử, mã độc, viễn thông",
    "CONSTRUCTION_QUALITY": "Giám định sự cố công trình, chất lượng xây dựng, suất vốn đầu tư",
    "INTELLECTUAL_PROPERTY": "Giám định quyền tác giả phần mềm, nhãn hiệu, sáng chế, bí mật kinh doanh",
    "DOCUMENT_SIGNATURE": "Giám định chữ ký, con dấu, tài liệu giả mạo, tuổi mực, kỹ thuật hình sự",
}

# Điều 34 Luật Giám định tư pháp: Các trường hợp không được thực hiện giám định tư pháp (Xung đột lợi ích)
PROHIBITED_CONFLICT_KEYWORDS = [
    "người thân thích của đương sự",
    "người có quyền lợi liên quan trực tiếp",
    "người đã tham gia tố tụng với tư cách khác",
    "bị đe dọa hoặc mua chuộc",
    "có căn cứ rõ ràng cho thấy không vô tư",
]


class ForensicEngine:
    """Core engine for Vietnamese Judicial Expertise, Forensic Assessment, and Chain of Custody."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "forensic.db")
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
                CREATE TABLE IF NOT EXISTS judicial_experts (
                    expert_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    degree TEXT NOT NULL,
                    years_experience INTEGER NOT NULL,
                    card_number TEXT NOT NULL,
                    issuing_authority TEXT NOT NULL,
                    is_certified INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forensic_requisitions (
                    requisition_id TEXT PRIMARY KEY,
                    requesting_agency TEXT NOT NULL,
                    case_code TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    assessment_target TEXT NOT NULL,
                    estimated_fee_vnd REAL NOT NULL,
                    deadline_days INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expert_conclusions (
                    conclusion_id TEXT PRIMARY KEY,
                    requisition_id TEXT NOT NULL,
                    lead_expert_id TEXT NOT NULL,
                    methodology TEXT NOT NULL,
                    conclusion_verdict TEXT NOT NULL,
                    has_sworn_statement INTEGER NOT NULL,
                    has_conflict_of_interest INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chain_of_custody (
                    custody_id TEXT PRIMARY KEY,
                    evidence_name TEXT NOT NULL,
                    source_device TEXT NOT NULL,
                    sha256_hash TEXT NOT NULL,
                    write_blocker_used INTEGER NOT NULL,
                    seizure_witnesses_count INTEGER NOT NULL,
                    is_admissible INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def register_judicial_expert(
        self,
        full_name: str,
        domain: str = "DIGITAL_EVIDENCE",
        degree: str = "Kỹ sư An toàn Thông tin / Thạc sĩ KHMT",
        years_experience: int = 7,
        card_number: str = "GĐTP-08/2023/BTP",
        issuing_authority: str = "Bộ Tư pháp",
    ) -> Dict[str, Any]:
        """
        Register and verify certified Judicial Expert under Law on Judicial Expertise Arts 7 & 18.
        Statutory threshold: At least 5 years of practical experience in the relevant domain (Khoản 1 Điều 7).
        """
        expert_id = f"JEX-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        dom_upper = domain.strip().upper()

        if dom_upper not in FORENSIC_DOMAINS:
            violations.append(f"Lĩnh vực giám định không hợp lệ: {', '.join(FORENSIC_DOMAINS.keys())}")

        if years_experience < 5:
            violations.append(
                f"Chưa đủ tiêu chuẩn bổ nhiệm Giám định viên tư pháp: {years_experience} năm kinh nghiệm "
                f"< tối thiểu 05 năm theo Điều 7 Khoản 1 Điểm b Luật Giám định tư pháp"
            )

        if not card_number.strip():
            violations.append("Thiếu số thẻ / quyết định bổ nhiệm giám định viên tư pháp của cơ quan có thẩm quyền")

        is_certified = len(violations) == 0
        status = "CERTIFIED_EXPERT" if is_certified else "QUALIFICATION_DEFICIENT"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO judicial_experts (
                    expert_id, full_name, domain, degree, years_experience,
                    card_number, issuing_authority, is_certified, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                expert_id, full_name.strip(), dom_upper, degree.strip(), years_experience,
                card_number.strip(), issuing_authority.strip(), 1 if is_certified else 0, status, created_at
            ))
            conn.commit()

        return {
            "expert_id": expert_id,
            "full_name": full_name,
            "domain": dom_upper,
            "domain_description": FORENSIC_DOMAINS.get(dom_upper, dom_upper),
            "degree": degree,
            "years_experience": years_experience,
            "card_number": card_number,
            "issuing_authority": issuing_authority,
            "is_certified": is_certified,
            "status": status,
            "violations": violations,
            "created_at": created_at,
        }

    def solicit_assessment(
        self,
        requesting_agency: str,
        case_code: str,
        assessment_target: str,
        domain: str = "DIGITAL_EVIDENCE",
        dispute_value_vnd: float = 2000000000.0,
        deadline_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Record a statutory judicial assessment requisition (Quyết định trưng cầu giám định) under Art 25-26.
        Computes statutory assessment advance fee schedule.
        """
        requisition_id = f"REQ-{uuid.uuid4().hex[:8].upper()}"
        dom_upper = domain.strip().upper()
        violations = []

        if dom_upper not in FORENSIC_DOMAINS:
            violations.append(f"Lĩnh vực trưng cầu không hợp lệ: {', '.join(FORENSIC_DOMAINS.keys())}")

        if not requesting_agency.strip() or not case_code.strip():
            violations.append("Thiếu thông tin cơ quan tiến hành tố tụng hoặc mã hiệu vụ án")

        # Statutory Forensic Fee Estimation (Pháp lệnh 02/2012/UBTVQH13)
        if dispute_value_vnd <= 500000000.0:
            estimated_fee_vnd = max(10000000.0, dispute_value_vnd * 0.04)
        elif dispute_value_vnd <= 5000000000.0:
            estimated_fee_vnd = 20000000.0 + (dispute_value_vnd - 500000000.0) * 0.02
        else:
            estimated_fee_vnd = 110000000.0 + (dispute_value_vnd - 5000000000.0) * 0.01

        status = "REQUISITION_ACCEPTED" if len(violations) == 0 else "REQUISITION_INVALID"
        statutory_notes = (
            f"Trưng cầu giám định tư pháp hợp lệ theo quy định của BLTTHS/BLTTDS; thời hạn {deadline_days} ngày"
            if len(violations) == 0
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO forensic_requisitions (
                    requisition_id, requesting_agency, case_code, domain,
                    assessment_target, estimated_fee_vnd, deadline_days, status,
                    statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                requisition_id, requesting_agency.strip(), case_code.strip(), dom_upper,
                assessment_target.strip(), estimated_fee_vnd, deadline_days, status,
                statutory_notes, created_at
            ))
            conn.commit()

        return {
            "requisition_id": requisition_id,
            "requesting_agency": requesting_agency,
            "case_code": case_code,
            "domain": dom_upper,
            "domain_description": FORENSIC_DOMAINS.get(dom_upper, dom_upper),
            "assessment_target": assessment_target,
            "estimated_fee_vnd": estimated_fee_vnd,
            "deadline_days": deadline_days,
            "status": status,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def issue_expert_conclusion(
        self,
        requisition_id: str,
        lead_expert_id: str,
        methodology: str,
        conclusion_verdict: str,
        has_sworn_statement: bool = True,
        has_conflict_of_interest: bool = False,
    ) -> Dict[str, Any]:
        """
        Formulate statutory Judicial Assessment Conclusion (Kết luận giám định tư pháp) under Art 32.
        Mandatory: Sworn statement under Criminal Code Art 382, no conflict of interest (Art 34).
        """
        conclusion_id = f"CON-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not has_sworn_statement:
            violations.append("Thiếu cam kết chịu trách nhiệm hình sự về tính trung thực theo Điều 382 Bộ luật Hình sự")

        if has_conflict_of_interest:
            violations.append("Giám định viên vi phạm quy định về xung đột lợi ích theo Điều 34 Luật Giám định tư pháp")

        if not methodology.strip():
            violations.append("Thiếu phương pháp giám định khoa học, thiết bị chuyên dụng và căn cứ kỹ thuật")

        is_valid = len(violations) == 0
        status = "CONCLUSION_LEGALLY_EFFECTIVE" if is_valid else "CONCLUSION_INVALID"
        statutory_notes = (
            "Kết luận giám định tư pháp hoàn tất hợp chuẩn theo Điều 32 Luật Giám định tư pháp; "
            "là nguồn chứng cứ theo Điều 87 Bộ luật Tố tụng hình sự 2015."
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO expert_conclusions (
                    conclusion_id, requisition_id, lead_expert_id, methodology,
                    conclusion_verdict, has_sworn_statement, has_conflict_of_interest,
                    is_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                conclusion_id, requisition_id.strip(), lead_expert_id.strip(), methodology.strip(),
                conclusion_verdict.strip(), 1 if has_sworn_statement else 0,
                1 if has_conflict_of_interest else 0, 1 if is_valid else 0,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "conclusion_id": conclusion_id,
            "requisition_id": requisition_id,
            "lead_expert_id": lead_expert_id,
            "methodology": methodology,
            "conclusion_verdict": conclusion_verdict,
            "has_sworn_statement": has_sworn_statement,
            "has_conflict_of_interest": has_conflict_of_interest,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def audit_digital_chain_of_custody(
        self,
        evidence_name: str,
        source_device: str,
        raw_evidence_data: str,
        write_blocker_used: bool = True,
        seizure_witnesses_count: int = 2,
    ) -> Dict[str, Any]:
        """
        Audit digital forensics chain of custody and SHA-256 hash preservation under Criminal Procedure Code Arts 99 & 107.
        Ensures evidence integrity from physical seizure to courtroom presentation.
        """
        custody_id = f"COC-{uuid.uuid4().hex[:8].upper()}"
        sha256_hash = hashlib.sha256(raw_evidence_data.encode("utf-8")).hexdigest()
        violations = []

        if not write_blocker_used:
            violations.append("Không sử dụng thiết bị chống ghi (Write-Blocker) khi trích xuất bản sao nhị phân (Bit-stream Image)")

        if seizure_witnesses_count < 2:
            violations.append(
                f"Số lượng người chứng kiến khi niêm phong ({seizure_witnesses_count}) "
                f"< tối thiểu 02 người theo quy định tại Điều 107 BLTTHS 2015"
            )

        is_admissible = len(violations) == 0
        status = "CHAIN_OF_CUSTODY_INTACT" if is_admissible else "CHAIN_COMPROMISED"
        statutory_notes = (
            f"Dữ liệu điện tử được bảo toàn nguyên vẹn với mã băm SHA-256 [{sha256_hash[:16]}...]; "
            f"đáp ứng đầy đủ điều kiện chứng cứ tố tụng theo Điều 99, 107 BLTTHS 2015."
            if is_admissible
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO chain_of_custody (
                    custody_id, evidence_name, source_device, sha256_hash,
                    write_blocker_used, seizure_witnesses_count, is_admissible,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                custody_id, evidence_name.strip(), source_device.strip(), sha256_hash,
                1 if write_blocker_used else 0, seizure_witnesses_count,
                1 if is_admissible else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "custody_id": custody_id,
            "evidence_name": evidence_name,
            "source_device": source_device,
            "sha256_hash": sha256_hash,
            "write_blocker_used": write_blocker_used,
            "seizure_witnesses_count": seizure_witnesses_count,
            "is_admissible": is_admissible,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def list_forensic_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered judicial experts, requisitions, conclusions, and evidence custody records."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "EXPERTS"]:
                cursor.execute("SELECT * FROM judicial_experts ORDER BY created_at DESC LIMIT ?", (limit,))
                results["judicial_experts"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "REQUISITIONS"]:
                cursor.execute("SELECT * FROM forensic_requisitions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["forensic_requisitions"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "CONCLUSIONS"]:
                cursor.execute("SELECT * FROM expert_conclusions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["expert_conclusions"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "CUSTODY"]:
                cursor.execute("SELECT * FROM chain_of_custody ORDER BY created_at DESC LIMIT ?", (limit,))
                results["chain_of_custody"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_forensic_telemetry(self) -> Dict[str, Any]:
        """Aggregate national judicial expertise volume, certified experts, and evidence integrity metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_certified = 1 THEN 1 ELSE 0 END) FROM judicial_experts")
            e_row = cursor.fetchone()
            total_experts = e_row[0] or 0
            certified_experts = e_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(estimated_fee_vnd) FROM forensic_requisitions")
            r_row = cursor.fetchone()
            total_requisitions = r_row[0] or 0
            total_estimated_fees_vnd = r_row[1] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) FROM expert_conclusions")
            c_row = cursor.fetchone()
            total_conclusions = c_row[0] or 0
            valid_conclusions = c_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_admissible = 1 THEN 1 ELSE 0 END) FROM chain_of_custody")
            cu_row = cursor.fetchone()
            total_custody_records = cu_row[0] or 0
            admissible_evidence_records = cu_row[1] or 0

        validity_rate_pct = (valid_conclusions / total_conclusions * 100.0) if total_conclusions > 0 else 0.0

        return {
            "total_experts": total_experts,
            "certified_experts": certified_experts,
            "total_requisitions": total_requisitions,
            "total_estimated_fees_vnd": total_estimated_fees_vnd,
            "total_conclusions": total_conclusions,
            "valid_conclusions": valid_conclusions,
            "validity_rate_pct": round(validity_rate_pct, 2),
            "total_custody_records": total_custody_records,
            "admissible_evidence_records": admissible_evidence_records,
            "database_path": self.db_path,
        }
