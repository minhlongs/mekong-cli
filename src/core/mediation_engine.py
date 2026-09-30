"""
Autonomous Vietnamese Commercial Mediation, Conciliation & ADR Suite.
Statutory Framework:
- Nghị định số 22/2017/NĐ-CP ngày 24/02/2017 của Chính phủ về hòa giải thương mại
- Bộ luật Tố tụng dân sự 2015 — Chương XXXIII (Thủ tục công nhận kết quả hòa giải thành ngoài Tòa án, Điều 416-419)
- Bộ luật Dân sự 2015 (Quy định về giao dịch dân sự, hợp đồng và tự do thỏa thuận)
- Công ước Singapore về Hòa giải 2018 (Singapore Convention on Mediation - UNCITRAL)
- Quy tắc hòa giải của các Trung tâm hòa giải thương mại (VICMC, VMC thuộc VIAC)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

from __future__ import annotations

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

DISPUTE_CATEGORIES = {
    "SALE_OF_GOODS": "Tranh chấp phát sinh từ hoạt động mua bán hàng hóa thương mại",
    "TECH_SERVICES": "Tranh chấp hợp đồng dịch vụ phần mềm, chuyển giao công nghệ, SaaS",
    "CONSTRUCTION_EPC": "Tranh chấp hợp đồng xây dựng, tổng thầu EPC, tiến độ thi công",
    "SHAREHOLDER_INVEST": "Tranh chấp giữa các cổ đông, thành viên góp vốn, thoái vốn đầu tư",
    "LOGISTICS_FREIGHT": "Tranh chấp dịch vụ giao nhận vận tải, logistics, thuê kho bãi",
    "INTELLECTUAL_PROPERTY": "Tranh chấp li-xăng sở hữu trí tuệ, bản quyền, nhãn hiệu thương mại",
}

# Điều 417 Bộ luật Tố tụng dân sự 2015 & Điều 4 Nghị định 22/2017/NĐ-CP
PROHIBITED_SETTLEMENT_KEYWORDS = [
    "trốn thuế",
    "gian lận thuế",
    "tẩu tán tài sản",
    "trốn tránh nghĩa vụ ngân sách nhà nước",
    "xâm phạm an ninh quốc gia",
    "rửa tiền",
    "vi phạm điều cấm của luật",
    "trái đạo đức xã hội",
]


class MediationEngine:
    """Core engine for Vietnamese Commercial Mediation, settlement drafting, and court recognition."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "mediation.db")
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
                CREATE TABLE IF NOT EXISTS mediation_agreements (
                    agreement_id TEXT PRIMARY KEY,
                    party_a TEXT NOT NULL,
                    party_b TEXT NOT NULL,
                    dispute_scope TEXT NOT NULL,
                    mediation_center TEXT NOT NULL,
                    language TEXT NOT NULL,
                    is_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mediation_cases (
                    case_id TEXT PRIMARY KEY,
                    party_a TEXT NOT NULL,
                    party_b TEXT NOT NULL,
                    dispute_category TEXT NOT NULL,
                    claim_amount_vnd REAL NOT NULL,
                    mediator_name TEXT NOT NULL,
                    mediator_experience_years INTEGER NOT NULL,
                    mediation_fee_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settlement_records (
                    settlement_id TEXT PRIMARY KEY,
                    case_id TEXT NOT NULL,
                    settlement_amount_vnd REAL NOT NULL,
                    settlement_summary TEXT NOT NULL,
                    mediator_signature INTEGER NOT NULL,
                    parties_signature INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS court_recognitions (
                    recognition_id TEXT PRIMARY KEY,
                    settlement_id TEXT NOT NULL,
                    court_name TEXT NOT NULL,
                    filing_months_elapsed REAL NOT NULL,
                    within_statute_limit INTEGER NOT NULL,
                    is_recognized INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    enforceability_order TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def draft_mediation_agreement(
        self,
        party_a: str,
        party_b: str,
        dispute_scope: str = "Tất cả các tranh chấp phát sinh từ hoặc liên quan đến hợp đồng kinh tế",
        mediation_center: str = "VICMC",
        language: str = "VIETNAMESE",
    ) -> Dict[str, Any]:
        """
        Draft and validate a commercial mediation clause or submission agreement under Decree 22/2017/NĐ-CP Art 11.
        """
        agreement_id = f"MED-AGR-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not party_a.strip() or not party_b.strip():
            violations.append("Thiếu thông tin danh tính của một trong các bên tham gia thỏa thuận")

        center_upper = mediation_center.strip().upper()
        if center_upper not in ["VICMC", "VMC", "AD_HOC"]:
            violations.append("Tổ chức hòa giải phải là VICMC, VMC (thuộc VIAC) hoặc hòa giải viên vụ việc (AD_HOC)")

        is_valid = len(violations) == 0
        status = "AGREEMENT_VALID" if is_valid else "INVALID_CLAUSE"
        statutory_notes = (
            f"Thỏa thuận hòa giải thương mại lập thành văn bản hợp lệ theo Điều 11 Nghị định 22/2017/NĐ-CP; cơ chế {center_upper}"
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        model_clause = (
            f"Mọi tranh chấp phát sinh từ hoặc liên quan đến hợp đồng này sẽ được giải quyết bằng hòa giải "
            f"tại {center_upper} theo Quy tắc hòa giải của Trung tâm này. Các bên cam kết tự nguyện tuân thủ."
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mediation_agreements (
                    agreement_id, party_a, party_b, dispute_scope, mediation_center,
                    language, is_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agreement_id, party_a.strip(), party_b.strip(), dispute_scope.strip(),
                center_upper, language.strip().upper(), 1 if is_valid else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "agreement_id": agreement_id,
            "party_a": party_a,
            "party_b": party_b,
            "dispute_scope": dispute_scope,
            "mediation_center": center_upper,
            "language": language.upper(),
            "model_clause": model_clause,
            "is_valid": is_valid,
            "status": status,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def initiate_mediation_case(
        self,
        party_a: str,
        party_b: str,
        claim_amount_vnd: float,
        dispute_category: str = "SALE_OF_GOODS",
        mediator_name: str = "Hòa giải viên Luật sư Lê Hoàng Long",
        mediator_experience_years: int = 5,
        mediation_center: str = "VICMC",
    ) -> Dict[str, Any]:
        """
        Incept a commercial mediation case and appoint qualified mediator under Decree 22/2017/NĐ-CP Art 7 & 12.
        Mediator standard: at least 2 years of practical experience (Khoản 1 Điều 7).
        """
        case_id = f"MED-CAS-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        cat_upper = dispute_category.strip().upper()

        if cat_upper not in DISPUTE_CATEGORIES:
            violations.append(f"Danh mục tranh chấp không hợp lệ: {', '.join(DISPUTE_CATEGORIES.keys())}")

        if mediator_experience_years < 2:
            violations.append(
                f"Hòa giải viên chưa đủ tiêu chuẩn hành nghề: {mediator_experience_years} năm kinh nghiệm "
                f"< tối thiểu 02 năm theo Điều 7 Khoản 1 Điểm c Nghị định 22/2017/NĐ-CP"
            )

        if claim_amount_vnd <= 0:
            violations.append("Giá trị tranh chấp phải lớn hơn 0 VND")

        # Statutory Mediation Fee Calculation (Tỷ lệ bậc thang VICMC)
        if claim_amount_vnd <= 500000000.0:
            mediation_fee_vnd = max(15000000.0, claim_amount_vnd * 0.05)
        elif claim_amount_vnd <= 2000000000.0:
            mediation_fee_vnd = 25000000.0 + (claim_amount_vnd - 500000000.0) * 0.03
        else:
            mediation_fee_vnd = 70000000.0 + (claim_amount_vnd - 2000000000.0) * 0.015

        is_valid = len(violations) == 0
        status = "CASE_ACCEPTED" if is_valid else "CASE_REJECTED"
        statutory_notes = (
            f"Vụ việc hòa giải thương mại thụ lý thành công tại {mediation_center}; Hòa giải viên đạt chuẩn Điều 7"
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO mediation_cases (
                    case_id, party_a, party_b, dispute_category, claim_amount_vnd,
                    mediator_name, mediator_experience_years, mediation_fee_vnd,
                    status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case_id, party_a.strip(), party_b.strip(), cat_upper, claim_amount_vnd,
                mediator_name.strip(), mediator_experience_years, mediation_fee_vnd,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "case_id": case_id,
            "party_a": party_a,
            "party_b": party_b,
            "dispute_category": cat_upper,
            "category_name": DISPUTE_CATEGORIES.get(cat_upper, cat_upper),
            "claim_amount_vnd": claim_amount_vnd,
            "mediator_name": mediator_name,
            "mediator_experience_years": mediator_experience_years,
            "mediation_fee_vnd": mediation_fee_vnd,
            "status": status,
            "is_valid": is_valid,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def create_settlement_record(
        self,
        case_id: str,
        settlement_amount_vnd: float,
        settlement_summary: str,
        mediator_signature: bool = True,
        parties_signature: bool = True,
    ) -> Dict[str, Any]:
        """
        Draft and validate formal Settlement Agreement (Văn bản kết quả hòa giải thành) under Decree 22/2017/NĐ-CP Art 15.
        Mandatory: Signatures of both parties and Mediator; no prohibited statutory evasions (Art 417 CPC).
        """
        settlement_id = f"MED-SET-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        summary_lower = settlement_summary.lower()

        for kw in PROHIBITED_SETTLEMENT_KEYWORDS:
            if kw in summary_lower:
                violations.append(f"Nội dung thỏa thuận vi phạm điều cấm hoặc trốn tránh nghĩa vụ: '{kw}'")

        if not mediator_signature:
            violations.append("Thiếu chữ ký của Hòa giải viên thương mại theo Khoản 2 Điều 15")

        if not parties_signature:
            violations.append("Thiếu chữ ký hoặc xác nhận của các bên tranh chấp theo Khoản 2 Điều 15")

        is_valid = len(violations) == 0
        status = "SETTLEMENT_SUCCESSFUL" if is_valid else "INVALID_SETTLEMENT"
        statutory_notes = (
            "Văn bản kết quả hòa giải thành có hiệu lực ràng buộc các bên theo quy định của pháp luật dân sự (Điều 15 khoản 5)"
            if is_valid
            else "; ".join(violations)
        )
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO settlement_records (
                    settlement_id, case_id, settlement_amount_vnd, settlement_summary,
                    mediator_signature, parties_signature, is_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                settlement_id, case_id.strip(), settlement_amount_vnd, settlement_summary.strip(),
                1 if mediator_signature else 0, 1 if parties_signature else 0,
                1 if is_valid else 0, status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "settlement_id": settlement_id,
            "case_id": case_id,
            "settlement_amount_vnd": settlement_amount_vnd,
            "settlement_summary": settlement_summary,
            "mediator_signature": mediator_signature,
            "parties_signature": parties_signature,
            "is_valid": is_valid,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def audit_court_recognition(
        self,
        settlement_id: str,
        court_name: str = "Tòa án nhân dân Thành phố Hà Nội",
        filing_months_elapsed: float = 2.0,
        has_capacity: bool = True,
        is_voluntary: bool = True,
    ) -> Dict[str, Any]:
        """
        Audit petition for Court recognition of out-of-court mediation settlement under CPC 2015 Chapter XXXIII (Arts 416-419).
        Statute of limitations: Application must be filed within 06 months from date of settlement agreement (Art 416).
        Court Decision has immediate legal effect and is enforceable under civil judgment execution laws (Art 419(1)).
        """
        recognition_id = f"MED-REC-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        within_statute_limit = filing_months_elapsed <= 6.0
        if not within_statute_limit:
            violations.append(
                f"Quá thời hiệu nộp đơn yêu cầu Tòa án công nhận: {filing_months_elapsed:.1f} tháng "
                f"> thời hạn luật định 06 tháng theo Điều 416 Bộ luật Tố tụng dân sự 2015"
            )

        if not has_capacity:
            violations.append("Đương sự không có đầy đủ năng lực hành vi dân sự theo quy định tại Điểm a Khoản 1 Điều 417")

        if not is_voluntary:
            violations.append("Thỏa thuận không dựa trên nguyên tắc tự nguyện thực sự của các bên theo Điểm c Khoản 1 Điều 417")

        is_recognized = (len(violations) == 0) and within_statute_limit
        if is_recognized:
            status = "COURT_RECOGNITION_GRANTED"
            enforceability_order = "ENFORCEABLE_AS_COURT_JUDGMENT"
            statutory_notes = (
                f"Tòa án ra quyết định công nhận kết quả hòa giải thành theo Điều 419 BLTTDS 2015; "
                f"có hiệu lực thi hành ngay, không bị kháng cáo/kháng nghị, được cưỡng chế thi hành án dân sự."
            )
        else:
            status = "RECOGNITION_REJECTED"
            enforceability_order = "NON_ENFORCEABLE"
            statutory_notes = "; ".join(violations)

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO court_recognitions (
                    recognition_id, settlement_id, court_name, filing_months_elapsed,
                    within_statute_limit, is_recognized, status, enforceability_order,
                    statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recognition_id, settlement_id.strip(), court_name.strip(), filing_months_elapsed,
                1 if within_statute_limit else 0, 1 if is_recognized else 0,
                status, enforceability_order, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "recognition_id": recognition_id,
            "settlement_id": settlement_id,
            "court_name": court_name,
            "filing_months_elapsed": filing_months_elapsed,
            "within_statute_limit": within_statute_limit,
            "is_recognized": is_recognized,
            "status": status,
            "enforceability_order": enforceability_order,
            "violations": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def audit_singapore_convention(
        self,
        settlement_id: str,
        is_cross_border: bool = True,
        is_commercial: bool = True,
        mediator_attestation: bool = True,
        has_consumer_or_family: bool = False,
    ) -> Dict[str, Any]:
        """
        Audit international settlement agreement eligibility under Singapore Convention on Mediation 2018 (Art 1 & 5).
        Allows direct cross-border enforcement without court/arbitration proceedings in signatory states.
        """
        violations = []

        if not is_cross_border:
            violations.append("Thỏa thuận không mang tính chất quốc tế (các bên cùng quốc gia và nghĩa vụ không ở nước ngoài)")

        if not is_commercial:
            violations.append("Thỏa thuận không phát sinh từ quan hệ thương mại (ngoài phạm vi áp dụng Công ước)")

        if has_consumer_or_family:
            violations.append("Công ước loại trừ tranh chấp tiêu dùng cá nhân, gia đình hoặc lao động (Điều 1 Khoản 2)")

        if not mediator_attestation:
            violations.append("Thiếu xác nhận hoặc chữ ký của hòa giải viên chứng minh thỏa thuận phát sinh từ hòa giải (Điều 4)")

        is_eligible = len(violations) == 0
        status = "CONVENTION_ELIGIBLE" if is_eligible else "INELIGIBLE"
        statutory_notes = (
            "Đủ điều kiện công nhận và thi hành trực tiếp xuyên biên giới theo Công ước Singapore về Hòa giải 2018"
            if is_eligible
            else "; ".join(violations)
        )

        return {
            "settlement_id": settlement_id,
            "is_cross_border": is_cross_border,
            "is_commercial": is_commercial,
            "mediator_attestation": mediator_attestation,
            "has_consumer_or_family": has_consumer_or_family,
            "is_eligible": is_eligible,
            "status": status,
            "violations": violations,
            "statutory_notes": statutory_notes,
        }

    def list_mediation_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered mediation agreements, cases, settlement records, and court recognition petitions."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "AGREEMENTS", "CLAUSES"]:
                cursor.execute("SELECT * FROM mediation_agreements ORDER BY created_at DESC LIMIT ?", (limit,))
                results["mediation_agreements"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "CASES"]:
                cursor.execute("SELECT * FROM mediation_cases ORDER BY created_at DESC LIMIT ?", (limit,))
                results["mediation_cases"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "SETTLEMENTS"]:
                cursor.execute("SELECT * FROM settlement_records ORDER BY created_at DESC LIMIT ?", (limit,))
                results["settlement_records"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "RECOGNITIONS"]:
                cursor.execute("SELECT * FROM court_recognitions ORDER BY created_at DESC LIMIT ?", (limit,))
                results["court_recognitions"] = [dict(row) for row in cursor.fetchall()]

        return results

    def get_mediation_telemetry(self) -> Dict[str, Any]:
        """Aggregate national commercial mediation volume, settlement rate, and court recognition metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM mediation_agreements")
            total_agreements = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*), SUM(claim_amount_vnd), SUM(mediation_fee_vnd) FROM mediation_cases")
            c_row = cursor.fetchone()
            total_cases = c_row[0] or 0
            total_claim_amount_vnd = c_row[1] or 0.0
            total_mediation_fees_vnd = c_row[2] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(settlement_amount_vnd), SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) FROM settlement_records")
            s_row = cursor.fetchone()
            total_settlements = s_row[0] or 0
            total_settlement_amount_vnd = s_row[1] or 0.0
            successful_settlements = s_row[2] or 0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_recognized = 1 THEN 1 ELSE 0 END) FROM court_recognitions")
            r_row = cursor.fetchone()
            total_court_petitions = r_row[0] or 0
            enforceable_judgments = r_row[1] or 0

        settlement_rate_pct = (successful_settlements / total_cases * 100.0) if total_cases > 0 else 0.0

        return {
            "total_mediation_agreements": total_agreements,
            "total_mediation_cases": total_cases,
            "total_claim_amount_vnd": total_claim_amount_vnd,
            "total_mediation_fees_vnd": total_mediation_fees_vnd,
            "total_settlements": total_settlements,
            "successful_settlements": successful_settlements,
            "total_settlement_amount_vnd": total_settlement_amount_vnd,
            "settlement_rate_pct": round(settlement_rate_pct, 2),
            "total_court_petitions": total_court_petitions,
            "enforceable_judgments": enforceable_judgments,
            "database_path": self.db_path,
        }
