"""
Autonomous Vietnamese Commercial Arbitration, Out-of-Court Dispute Resolution & New York Convention Suite.
Statutory Framework:
- Luật Trọng tài thương mại 2010 (Luật số 54/2010/QH12)
- Nghị quyết số 01/2014/NQ-HĐTP hướng dẫn thi hành Luật Trọng tài thương mại
- Nghị định số 22/2017/NĐ-CP về hòa giải thương mại (Commercial Mediation)
- Bộ luật Tố tụng dân sự 2015 (Phần thứ bảy: Công nhận và cho thi hành phán quyết của Trọng tài nước ngoài)
- Công ước New York 1958 về công nhận và cho thi hành phán quyết trọng tài nước ngoài
- Quy tắc tố tụng VIAC (Trung tâm Trọng tài Quốc tế Việt Nam)

Strict Standard Library Only: Zero external HTTP, zero vendor SDKs.
"""

import os
import json
import sqlite3
import datetime
import uuid
from typing import Dict, Any, List, Optional

ARBITRAL_INSTITUTIONS = {
    "VIAC": "Trung tâm Trọng tài Quốc tế Việt Nam (Vietnam International Arbitration Centre)",
    "SIAC": "Trung tâm Trọng tài Quốc tế Singapore (Singapore International Arbitration Centre)",
    "ICC": "Tòa Trọng tài Quốc tế ICC (International Chamber of Commerce Court of Arbitration)",
    "HKIAC": "Trung tâm Trọng tài Quốc tế Hồng Kông (Hong Kong International Arbitration Centre)",
    "AD_HOC": "Trọng tài Vụ việc theo Quy tắc UNCITRAL (Ad-hoc Arbitration under UNCITRAL Rules)",
}

class ArbitrationEngine:
    """Core engine for Vietnamese Commercial Arbitration & Foreign Award Enforcement."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.expanduser("~/.mekong")
            os.makedirs(base_dir, exist_ok=True)
            db_path = os.path.join(base_dir, "arbitration.db")
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
                CREATE TABLE IF NOT EXISTS arbitration_agreements (
                    clause_id TEXT PRIMARY KEY,
                    contract_title TEXT NOT NULL,
                    institution TEXT NOT NULL,
                    seat TEXT NOT NULL,
                    governing_law TEXT NOT NULL,
                    language TEXT NOT NULL,
                    num_arbitrators INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arbitration_claims (
                    claim_id TEXT PRIMARY KEY,
                    clause_id TEXT,
                    claimant TEXT NOT NULL,
                    respondent TEXT NOT NULL,
                    dispute_subject TEXT NOT NULL,
                    dispute_amount_vnd REAL NOT NULL,
                    arbitration_fee_vnd REAL NOT NULL,
                    status TEXT NOT NULL,
                    tribunal_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS arbitral_awards (
                    award_id TEXT PRIMARY KEY,
                    claim_id TEXT NOT NULL,
                    tribunal_president TEXT NOT NULL,
                    award_date TEXT NOT NULL,
                    claim_granted_pct REAL NOT NULL,
                    amount_awarded_vnd REAL NOT NULL,
                    is_final_binding INTEGER NOT NULL,
                    set_aside_risk TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS foreign_award_enforcements (
                    dossier_id TEXT PRIMARY KEY,
                    foreign_tribunal TEXT NOT NULL,
                    origin_country TEXT NOT NULL,
                    award_amount_usd REAL NOT NULL,
                    new_york_convention_member INTEGER NOT NULL,
                    consular_authenticated INTEGER NOT NULL,
                    statute_of_limitations_valid INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    statutory_notes TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def draft_arbitration_clause(
        self,
        contract_title: str,
        institution: str = "VIAC",
        seat: str = "Hà Nội",
        governing_law: str = "VIETNAMESE_LAW",
        language: str = "VIETNAMESE",
        num_arbitrators: int = 3,
    ) -> Dict[str, Any]:
        """
        Draft and validate a commercial arbitration clause under Law on Commercial Arbitration Article 16-19.
        """
        clause_id = f"ARB-CLS-{uuid.uuid4().hex[:8].upper()}"
        violations = []
        inst_upper = institution.strip().upper()

        if inst_upper not in ARBITRAL_INSTITUTIONS:
            violations.append(f"Tổ chức trọng tài phải thuộc danh mục hợp lệ: {', '.join(ARBITRAL_INSTITUTIONS.keys())}")

        if num_arbitrators not in [1, 3]:
            violations.append("Số lượng trọng tài viên phải là số lẻ (1 hoặc 3 trọng tài viên theo Điều 39)")

        is_valid = len(violations) == 0
        statutory_notes = "Điều khoản trọng tài thương mại hợp lệ và có hiệu lực ràng buộc (Điều 16, 18)" if is_valid else "; ".join(violations)

        model_clause = (
            f"Mọi tranh chấp phát sinh từ hoặc liên quan đến hợp đồng này sẽ được giải quyết bằng trọng tài "
            f"tại {ARBITRAL_INSTITUTIONS.get(inst_upper, inst_upper)} theo Quy tắc tố tụng trọng tài của Trung tâm này. "
            f"Địa điểm trọng tài là {seat}. Luật áp dụng là {governing_law}. Ngôn ngữ trọng tài là {language}. "
            f"Hội đồng trọng tài gồm {num_arbitrators} trọng tài viên."
        )

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO arbitration_agreements (
                    clause_id, contract_title, institution, seat, governing_law,
                    language, num_arbitrators, is_valid, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clause_id, contract_title.strip(), inst_upper, seat.strip(),
                governing_law.upper(), language.upper(), num_arbitrators,
                1 if is_valid else 0, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "clause_id": clause_id,
            "contract_title": contract_title,
            "institution": inst_upper,
            "institution_name": ARBITRAL_INSTITUTIONS.get(inst_upper, inst_upper),
            "seat": seat,
            "governing_law": governing_law.upper(),
            "language": language.upper(),
            "num_arbitrators": num_arbitrators,
            "is_valid": is_valid,
            "valid_clause": is_valid,
            "violations": violations,
            "flaws": violations,
            "clause_text": model_clause,
            "model_clause": model_clause,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def calculate_viac_fee(self, dispute_amount_vnd: float, tribunal_size: int = 3) -> float:
        """
        Calculate statutory arbitration fee based on dispute quantum under VIAC Fee Schedule.
        """
        if dispute_amount_vnd <= 0:
            return 20000000.0  # Minimum administrative fee

        # Graduated fee scale
        if dispute_amount_vnd <= 500000000.0:  # <= 500M
            base_fee = max(30000000.0, dispute_amount_vnd * 0.06)
        elif dispute_amount_vnd <= 2000000000.0:  # <= 2B
            base_fee = 30000000.0 + (dispute_amount_vnd - 500000000.0) * 0.04
        elif dispute_amount_vnd <= 10000000000.0:  # <= 10B
            base_fee = 90000000.0 + (dispute_amount_vnd - 2000000000.0) * 0.025
        elif dispute_amount_vnd <= 50000000000.0:  # <= 50B
            base_fee = 290000000.0 + (dispute_amount_vnd - 10000000000.0) * 0.015
        else:
            base_fee = 890000000.0 + (dispute_amount_vnd - 50000000000.0) * 0.008

        # Sole arbitrator receives 70% of 3-arbitrator tribunal fee
        if tribunal_size == 1:
            base_fee *= 0.7

        return round(base_fee, 0)

    def file_arbitration_claim(
        self,
        claimant: str,
        respondent: str,
        dispute_subject: str,
        dispute_amount_vnd: float,
        clause_id: Optional[str] = None,
        tribunal_size: int = 3,
    ) -> Dict[str, Any]:
        """
        Register statement of commercial arbitration claim under Law on Commercial Arbitration Article 30-34.
        """
        claim_id = f"ARB-CLM-{uuid.uuid4().hex[:8].upper()}"
        fee_vnd = self.calculate_viac_fee(dispute_amount_vnd, tribunal_size)
        status = "CLAIM_REGISTERED"
        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO arbitration_claims (
                    claim_id, clause_id, claimant, respondent, dispute_subject,
                    dispute_amount_vnd, arbitration_fee_vnd, status, tribunal_size, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim_id, clause_id, claimant.strip(), respondent.strip(),
                dispute_subject.strip(), dispute_amount_vnd, fee_vnd,
                status, tribunal_size, created_at
            ))
            conn.commit()

        return {
            "claim_id": claim_id,
            "clause_id": clause_id,
            "claimant": claimant,
            "respondent": respondent,
            "dispute_subject": dispute_subject,
            "dispute_amount_vnd": dispute_amount_vnd,
            "arbitration_fee_vnd": fee_vnd,
            "tribunal_size": tribunal_size,
            "status": status,
            "created_at": created_at,
        }

    def render_arbitral_award(
        self,
        claim_id: str,
        tribunal_president: str = "GS. TS. Lê Hồng Hạnh",
        claim_granted_pct: float = 100.0,
        amount_awarded_vnd: Optional[float] = None,
        award_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Issue final and binding arbitral award and audit Article 68 set-aside grounds.
        """
        award_id = f"ARB-AWD-{uuid.uuid4().hex[:8].upper()}"
        if not award_date:
            award_date = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

        # Fetch claim details if exists
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT dispute_amount_vnd FROM arbitration_claims WHERE claim_id = ?", (claim_id,))
            row = cursor.fetchone()
            dispute_amt = row[0] if row else 1000000000.0
            found_claim = row is not None

        if amount_awarded_vnd is None:
            amount_awarded_vnd = round(dispute_amt * (claim_granted_pct / 100.0), 0)

        # Audit Article 68 risk
        if not found_claim:
            set_aside_risk = "HIGH"
            is_final_binding = False
            status = "SET_ASIDE_RISK_HIGH"
            compliance_notes = ["Không tìm thấy hồ sơ khởi kiện trọng tài gốc trong hệ thống (Điều 68)"]
            statutory_notes = "; ".join(compliance_notes)
        else:
            set_aside_risk = "LOW"
            is_final_binding = True
            status = "FINAL_AND_BINDING"
            compliance_notes = ["Phán quyết trọng tài tuân thủ đầy đủ thẩm quyền và thủ tục tố tụng (Điều 68)"]
            statutory_notes = "Phán quyết trọng tài có giá trị chung thẩm và bắt buộc thi hành kể từ ngày ban hành (Điều 61)"

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO arbitral_awards (
                    award_id, claim_id, tribunal_president, award_date,
                    claim_granted_pct, amount_awarded_vnd, is_final_binding,
                    set_aside_risk, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                award_id, claim_id, tribunal_president.strip(), award_date,
                claim_granted_pct, amount_awarded_vnd, 1 if is_final_binding else 0,
                set_aside_risk, statutory_notes, created_at
            ))
            if found_claim:
                cursor.execute("UPDATE arbitration_claims SET status = 'AWARD_RENDERED' WHERE claim_id = ?", (claim_id,))
            conn.commit()

        return {
            "award_id": award_id,
            "claim_id": claim_id,
            "status": status,
            "tribunal_president": tribunal_president,
            "award_date": award_date,
            "claim_granted_pct": claim_granted_pct,
            "amount_awarded_vnd": amount_awarded_vnd,
            "is_final_binding": is_final_binding,
            "set_aside_risk": set_aside_risk,
            "compliance_notes": compliance_notes,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def enforce_foreign_award(
        self,
        foreign_tribunal: str,
        origin_country: str = "Singapore",
        award_amount_usd: float = 2500000.0,
        new_york_convention_member: bool = True,
        consular_authenticated: bool = True,
        years_since_award: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Audit petition for recognition and enforcement of foreign arbitral award under New York Convention 1958 & CPC 2015.
        """
        dossier_id = f"FRG-ENF-{uuid.uuid4().hex[:8].upper()}"
        violations = []

        if not new_york_convention_member:
            violations.append("Quốc gia ban hành phán quyết không phải là thành viên Công ước New York 1958 (yêu cầu nguyên tắc có đi có lại)")

        if not consular_authenticated:
            violations.append("Bản chính/Bản sao hợp lệ phán quyết và thỏa thuận trọng tài chưa được hợp pháp hóa lãnh sự (Điều 453 BLTTDS)")

        if years_since_award > 3.0:
            violations.append("Thời hiệu nộp đơn yêu cầu công nhận và cho thi hành phán quyết trọng tài nước ngoài là 03 năm kể từ ngày phán quyết có hiệu lực (Điều 451)")

        statute_of_limitations_valid = years_since_award <= 3.0
        is_eligible = len(violations) == 0
        status = "ELIGIBLE_FOR_RECOGNITION" if is_eligible else "REJECTED_INADMISSIBLE"
        statutory_notes = "Đủ điều kiện thụ lý công nhận và cho thi hành tại Tòa án nhân dân cấp tỉnh tại Việt Nam" if is_eligible else "; ".join(violations)

        created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO foreign_award_enforcements (
                    dossier_id, foreign_tribunal, origin_country, award_amount_usd,
                    new_york_convention_member, consular_authenticated,
                    statute_of_limitations_valid, status, statutory_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dossier_id, foreign_tribunal.strip(), origin_country.strip(),
                award_amount_usd, 1 if new_york_convention_member else 0,
                1 if consular_authenticated else 0, 1 if statute_of_limitations_valid else 0,
                status, statutory_notes, created_at
            ))
            conn.commit()

        return {
            "dossier_id": dossier_id,
            "foreign_tribunal": foreign_tribunal,
            "origin_country": origin_country,
            "award_amount_usd": award_amount_usd,
            "new_york_convention_member": new_york_convention_member,
            "consular_authenticated": consular_authenticated,
            "statute_of_limitations_valid": statute_of_limitations_valid,
            "status": status,
            "is_eligible": is_eligible,
            "violations": violations,
            "grounds_for_refusal": violations,
            "statutory_notes": statutory_notes,
            "created_at": created_at,
        }

    def list_arbitration_records(self, category: str = "ALL", limit: int = 50) -> Dict[str, Any]:
        """List registered arbitration agreements, claims, awards, and foreign enforcement dossiers."""
        cat_upper = category.strip().upper()
        results: Dict[str, Any] = {}

        with self._get_connection() as conn:
            cursor = conn.cursor()
            if cat_upper in ["ALL", "CLAUSES"]:
                cursor.execute("SELECT * FROM arbitration_agreements ORDER BY created_at DESC LIMIT ?", (limit,))
                results["clauses"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "CLAIMS"]:
                cursor.execute("SELECT * FROM arbitration_claims ORDER BY created_at DESC LIMIT ?", (limit,))
                results["claims"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "AWARDS"]:
                cursor.execute("SELECT * FROM arbitral_awards ORDER BY created_at DESC LIMIT ?", (limit,))
                results["awards"] = [dict(row) for row in cursor.fetchall()]

            if cat_upper in ["ALL", "FOREIGN"]:
                cursor.execute("SELECT * FROM foreign_award_enforcements ORDER BY created_at DESC LIMIT ?", (limit,))
                foreign_rows = [dict(row) for row in cursor.fetchall()]
                results["foreign_enforcements"] = foreign_rows
                results["foreign_awards"] = foreign_rows

        return results

    def get_arbitration_telemetry(self) -> Dict[str, Any]:
        """Aggregate commercial arbitration claims, total dispute volume, and enforcement telemetry."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END) FROM arbitration_agreements")
            cl_row = cursor.fetchone()
            total_clauses = cl_row[0] or 0
            valid_clauses = cl_row[1] or 0

            cursor.execute("SELECT COUNT(*), SUM(dispute_amount_vnd), SUM(arbitration_fee_vnd) FROM arbitration_claims")
            c_row = cursor.fetchone()
            total_claims = c_row[0] or 0
            total_dispute_amount_vnd = c_row[1] or 0.0
            total_fees_collected_vnd = c_row[2] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(amount_awarded_vnd) FROM arbitral_awards")
            a_row = cursor.fetchone()
            total_awards = a_row[0] or 0
            total_amount_awarded_vnd = a_row[1] or 0.0

            cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status = 'ELIGIBLE_FOR_RECOGNITION' THEN 1 ELSE 0 END), SUM(award_amount_usd) FROM foreign_award_enforcements")
            f_row = cursor.fetchone()
            total_foreign_dossiers = f_row[0] or 0
            eligible_foreign_dossiers = f_row[1] or 0
            total_foreign_amount_usd = f_row[2] or 0.0

        return {
            "total_arbitration_clauses": total_clauses,
            "valid_clauses": valid_clauses,
            "total_arbitration_claims": total_claims,
            "total_dispute_amount_vnd": total_dispute_amount_vnd,
            "total_fees_collected_vnd": total_fees_collected_vnd,
            "total_awards_rendered": total_awards,
            "total_amount_awarded_vnd": total_amount_awarded_vnd,
            "total_foreign_dossiers": total_foreign_dossiers,
            "eligible_foreign_dossiers": eligible_foreign_dossiers,
            "total_foreign_amount_usd": total_foreign_amount_usd,
            "database_path": self.db_path,
        }
