"""
Vietnamese Competition, Antitrust, Anti-Monopoly & Economic Concentration Engine.
Implements compliance under Law on Competition 2018 (Law 23/2018/QH14),
Decree 35/2020/ND-CP (detailed regulations on economic concentration and anti-competitive practices),
and National Competition Commission (Ủy ban Cạnh tranh Quốc gia - NCC) mandates.

Pure Python standard-library-only engine with SQLite WAL persistence.
Compliant with tests/test_core_boundary.py AST invariant.
"""

from dataclasses import asdict, dataclass
import datetime
import json
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid


# Statutory Notification Thresholds under Article 33 Law on Competition 2018 & Decree 35/2020/ND-CP Article 13
DEFAULT_ASSET_THRESHOLD_VND = 3_000_000_000_000       # 3,000 tỷ VND
CREDIT_ASSET_THRESHOLD_VND = 12_000_000_000_000      # 12,000 tỷ VND (tổ chức tín dụng)

DEFAULT_REVENUE_THRESHOLD_VND = 3_000_000_000_000     # 3,000 tỷ VND
CREDIT_REVENUE_THRESHOLD_VND = 10_000_000_000_000    # 10,000 tỷ VND

TRANSACTION_VALUE_THRESHOLD_VND = 1_000_000_000_000  # 1,000 tỷ VND (giao dịch trong nước)
COMBINED_MARKET_SHARE_THRESHOLD_PCT = 20.0            # 20.0% thị phần kết hợp trên thị trường liên quan

# Market Dominance Thresholds under Article 24 Law on Competition 2018
DOMINANCE_SINGLE_PCT = 30.0   # CR1 >= 30%
DOMINANCE_CR2_PCT = 50.0      # CR2 >= 50%
DOMINANCE_CR3_PCT = 65.0      # CR3 >= 65%
DOMINANCE_CR4_PCT = 75.0      # CR4 >= 75%


@dataclass
class EconomicConcentrationAudit:
    concentration_id: str
    merger_name: str
    acquiring_entity: str
    target_entity: str
    total_assets_vnd: float
    total_revenue_vnd: float
    transaction_value_vnd: float
    combined_market_share_pct: float
    pre_hhi: float
    post_hhi: float
    delta_hhi: float
    is_credit_institution: bool
    requires_notification: bool
    notification_triggers: List[str]
    verdict: str
    reasons: List[str]
    created_at: str


@dataclass
class MarketDominanceAssessment:
    assessment_id: str
    enterprise_name: str
    market_share_pct: float
    cr_group_shares: List[float]
    is_dominant: bool
    dominance_basis: str
    significant_market_power: bool
    risk_level: str
    compliance_guidelines: List[str]
    created_at: str


@dataclass
class AntiCompetitiveAgreementAudit:
    audit_id: str
    agreement_title: str
    parties_count: int
    agreement_type: str
    is_horizontal: bool
    is_prohibited: bool
    violation_nature: str
    max_fine_rate_pct: float
    potential_fine_vnd: float
    remediation_notes: str
    created_at: str


@dataclass
class LeniencyApplication:
    application_id: str
    violation_id: str
    enterprise_name: str
    submission_order: int
    self_confessed: bool
    submitted_evidence: bool
    is_eligible: bool
    fine_exemption_pct: float
    status: str
    created_at: str


class CompetitionEngine:
    """
    Vietnamese Competition, Antitrust & Economic Concentration Engine.
    Adheres strictly to the standard library only.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            mekong_dir = Path.home() / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(mekong_dir / "competition.db")
        else:
            self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS economic_concentrations (
                    concentration_id TEXT PRIMARY KEY,
                    merger_name TEXT NOT NULL,
                    acquiring_entity TEXT NOT NULL,
                    target_entity TEXT NOT NULL,
                    total_assets_vnd REAL NOT NULL,
                    total_revenue_vnd REAL NOT NULL,
                    transaction_value_vnd REAL NOT NULL,
                    combined_market_share_pct REAL NOT NULL,
                    pre_hhi REAL NOT NULL,
                    post_hhi REAL NOT NULL,
                    delta_hhi REAL NOT NULL,
                    is_credit_institution INTEGER NOT NULL,
                    requires_notification INTEGER NOT NULL,
                    notification_triggers_json TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    reasons_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_dominance_assessments (
                    assessment_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    market_share_pct REAL NOT NULL,
                    cr_group_shares_json TEXT NOT NULL,
                    is_dominant INTEGER NOT NULL,
                    dominance_basis TEXT NOT NULL,
                    significant_market_power INTEGER NOT NULL,
                    risk_level TEXT NOT NULL,
                    compliance_guidelines_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS anti_competitive_agreements (
                    audit_id TEXT PRIMARY KEY,
                    agreement_title TEXT NOT NULL,
                    parties_count INTEGER NOT NULL,
                    agreement_type TEXT NOT NULL,
                    is_horizontal INTEGER NOT NULL,
                    is_prohibited INTEGER NOT NULL,
                    violation_nature TEXT NOT NULL,
                    max_fine_rate_pct REAL NOT NULL,
                    potential_fine_vnd REAL NOT NULL,
                    remediation_notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS leniency_applications (
                    application_id TEXT PRIMARY KEY,
                    violation_id TEXT NOT NULL,
                    enterprise_name TEXT NOT NULL,
                    submission_order INTEGER NOT NULL,
                    self_confessed INTEGER NOT NULL,
                    submitted_evidence INTEGER NOT NULL,
                    is_eligible INTEGER NOT NULL,
                    fine_exemption_pct REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_economic_concentration(
        self,
        merger_name: str,
        acquiring_entity: str,
        target_entity: str,
        total_assets_vnd: float,
        total_revenue_vnd: float,
        transaction_value_vnd: float,
        combined_market_share_pct: float,
        pre_hhi: float = 1200.0,
        post_hhi: float = 1500.0,
        is_credit_institution: bool = False,
    ) -> Dict[str, Any]:
        """
        Audits economic concentration (M&A) notification threshold and anti-competitive impact
        under Article 33 Law on Competition 2018 & Decree 35/2020/ND-CP Article 13 & 14.
        """
        concentration_id = f"CONC-{uuid.uuid4().hex[:8].upper()}"
        triggers: List[str] = []
        reasons: List[str] = []

        asset_limit = CREDIT_ASSET_THRESHOLD_VND if is_credit_institution else DEFAULT_ASSET_THRESHOLD_VND
        rev_limit = CREDIT_REVENUE_THRESHOLD_VND if is_credit_institution else DEFAULT_REVENUE_THRESHOLD_VND

        # Check notification thresholds
        if total_assets_vnd >= asset_limit:
            triggers.append(f"Tổng tài sản tại Việt Nam ({total_assets_vnd:,.0f} VND) >= ngưỡng luật định ({asset_limit:,.0f} VND).")

        if total_revenue_vnd >= rev_limit:
            triggers.append(f"Tổng doanh thu bán ra hoặc mua vào ({total_revenue_vnd:,.0f} VND) >= ngưỡng luật định ({rev_limit:,.0f} VND).")

        if transaction_value_vnd >= TRANSACTION_VALUE_THRESHOLD_VND:
            triggers.append(f"Giá trị giao dịch tập trung kinh tế ({transaction_value_vnd:,.0f} VND) >= ngưỡng 1.000 tỷ VND.")

        if combined_market_share_pct >= COMBINED_MARKET_SHARE_THRESHOLD_PCT:
            triggers.append(f"Thị phần kết hợp trên thị trường liên quan ({combined_market_share_pct:.1f}%) >= ngưỡng 20.0%.")

        requires_notification = len(triggers) > 0
        delta_hhi = post_hhi - pre_hhi

        # Evaluate anti-competitive impact (Article 30 & Decree 35/2020 Art. 14)
        if combined_market_share_pct >= 50.0:
            verdict = "PROHIBITED_SIGNIFICANT_RESTRAINT"
            reasons.append("Thị phần kết hợp vượt quá 50%, có nguy cơ tạo ra hoặc củng cố vị trí thống lĩnh thị trường.")
        elif post_hhi > 1800.0 and delta_hhi > 200.0:
            verdict = "SUBJECT_TO_OFFICIAL_REVIEW"
            reasons.append(f"Thị trường sau sáp nhập tập trung cao (Post-HHI {post_hhi:.0f} > 1800) và mức tăng Delta HHI ({delta_hhi:.0f} > 200).")
        elif requires_notification:
            verdict = "NOTIFICATION_REQUIRED_PRELIMINARY"
            reasons.append("Chạm ngưỡng thông báo tập trung kinh tế; cần nộp hồ sơ thẩm định sơ bộ 30 ngày cho Ủy ban Cạnh tranh Quốc gia.")
        else:
            verdict = "CLEARED_WITHOUT_NOTIFICATION"
            reasons.append("Giao dịch không chạm ngưỡng thông báo luật định; được phép tiến hành mà không cần thủ tục chấp thuận cạnh tranh.")

        record = EconomicConcentrationAudit(
            concentration_id=concentration_id,
            merger_name=merger_name,
            acquiring_entity=acquiring_entity,
            target_entity=target_entity,
            total_assets_vnd=total_assets_vnd,
            total_revenue_vnd=total_revenue_vnd,
            transaction_value_vnd=transaction_value_vnd,
            combined_market_share_pct=combined_market_share_pct,
            pre_hhi=pre_hhi,
            post_hhi=post_hhi,
            delta_hhi=delta_hhi,
            is_credit_institution=is_credit_institution,
            requires_notification=requires_notification,
            notification_triggers=triggers,
            verdict=verdict,
            reasons=reasons,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO economic_concentrations
                (concentration_id, merger_name, acquiring_entity, target_entity, total_assets_vnd, total_revenue_vnd,
                 transaction_value_vnd, combined_market_share_pct, pre_hhi, post_hhi, delta_hhi, is_credit_institution,
                 requires_notification, notification_triggers_json, verdict, reasons_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.concentration_id,
                    record.merger_name,
                    record.acquiring_entity,
                    record.target_entity,
                    record.total_assets_vnd,
                    record.total_revenue_vnd,
                    record.transaction_value_vnd,
                    record.combined_market_share_pct,
                    record.pre_hhi,
                    record.post_hhi,
                    record.delta_hhi,
                    1 if record.is_credit_institution else 0,
                    1 if record.requires_notification else 0,
                    json.dumps(record.notification_triggers, ensure_ascii=False),
                    record.verdict,
                    json.dumps(record.reasons, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def assess_market_dominance(
        self,
        enterprise_name: str,
        market_share_pct: float,
        cr_group_shares: Optional[List[float]] = None,
        has_essential_facility: bool = False,
        financial_superiority: bool = False,
    ) -> Dict[str, Any]:
        """
        Assesses market dominance under Article 24 Law on Competition 2018 (CR1, CR2, CR3, CR4).
        """
        assessment_id = f"DOM-{uuid.uuid4().hex[:8].upper()}"
        shares = cr_group_shares or [market_share_pct]
        shares_sorted = sorted(shares, reverse=True)

        is_dominant = False
        basis = "NON_DOMINANT"
        guidelines: List[str] = []

        # Single enterprise dominance (CR1 >= 30%)
        if market_share_pct >= DOMINANCE_SINGLE_PCT:
            is_dominant = True
            basis = f"SINGLE_DOMINANCE (Thị phần đơn lẻ {market_share_pct:.1f}% >= 30.0%)"
        elif len(shares_sorted) >= 2 and sum(shares_sorted[:2]) >= DOMINANCE_CR2_PCT:
            is_dominant = True
            basis = f"COLLECTIVE_DOMINANCE_CR2 (Nhóm 2 doanh nghiệp chiếm {sum(shares_sorted[:2]):.1f}% >= 50.0%)"
        elif len(shares_sorted) >= 3 and sum(shares_sorted[:3]) >= DOMINANCE_CR3_PCT:
            is_dominant = True
            basis = f"COLLECTIVE_DOMINANCE_CR3 (Nhóm 3 doanh nghiệp chiếm {sum(shares_sorted[:3]):.1f}% >= 65.0%)"
        elif len(shares_sorted) >= 4 and sum(shares_sorted[:4]) >= DOMINANCE_CR4_PCT:
            is_dominant = True
            basis = f"COLLECTIVE_DOMINANCE_CR4 (Nhóm 4 doanh nghiệp chiếm {sum(shares_sorted[:4]):.1f}% >= 75.0%)"

        has_significant_power = is_dominant or has_essential_facility or financial_superiority

        if is_dominant:
            risk_level = "HIGH"
            guidelines.append("Nghiêm cấm bán hàng hóa, dịch vụ dưới giá thành toàn bộ dẫn đến loại bỏ đối thủ (Điều 27).")
            guidelines.append("Nghiêm cấm áp đặt giá mua, giá bán hoặc ấn định giá bán lại tối thiểu cho đại lý.")
            guidelines.append("Nghiêm cấm ngăn cản sự tham gia hoặc mở rộng thị trường của doanh nghiệp khác.")
            guidelines.append("Nghiêm cấm áp đặt điều kiện bất bình đẳng hoặc ép buộc khách hàng chấp nhận nghĩa vụ không liên quan.")
        elif has_significant_power:
            risk_level = "MEDIUM"
            guidelines.append("Doanh nghiệp sở hữu cơ sở hạ tầng thiết yếu hoặc ưu thế tài chính lớn; cần cẩn trọng tránh hành vi hạn chế cạnh tranh.")
        else:
            risk_level = "LOW"
            guidelines.append("Doanh nghiệp ở vị thế cạnh tranh thông thường, không bị kiểm soát nghiêm ngặt theo chế định vị trí thống lĩnh.")

        record = MarketDominanceAssessment(
            assessment_id=assessment_id,
            enterprise_name=enterprise_name,
            market_share_pct=market_share_pct,
            cr_group_shares=shares_sorted,
            is_dominant=is_dominant,
            dominance_basis=basis,
            significant_market_power=has_significant_power,
            risk_level=risk_level,
            compliance_guidelines=guidelines,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO market_dominance_assessments
                (assessment_id, enterprise_name, market_share_pct, cr_group_shares_json, is_dominant,
                 dominance_basis, significant_market_power, risk_level, compliance_guidelines_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.assessment_id,
                    record.enterprise_name,
                    record.market_share_pct,
                    json.dumps(record.cr_group_shares),
                    1 if record.is_dominant else 0,
                    record.dominance_basis,
                    1 if record.significant_market_power else 0,
                    record.risk_level,
                    json.dumps(record.compliance_guidelines, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_anti_competitive_agreement(
        self,
        agreement_title: str,
        parties_count: int,
        agreement_type: str = "PRICE_FIXING",  # PRICE_FIXING, MARKET_SHARING, OUTPUT_RESTRICTION, BID_RIGGING
        is_horizontal: bool = True,  # Giữa các đối thủ cạnh tranh trên cùng thị trường
        annual_revenue_vnd: float = 100_000_000_000.0,
    ) -> Dict[str, Any]:
        """
        Audits anti-competitive agreements and cartels under Article 11 & 12 Law on Competition 2018.
        Horizontal cartels (price fixing, market sharing, output restriction, bid rigging) are strictly prohibited per se.
        """
        audit_id = f"AGR-{uuid.uuid4().hex[:8].upper()}"

        # Article 12: Thỏa thuận cấm tuyệt đối (per se illegal) đối với thỏa thuận ngang
        per_se_types = ("PRICE_FIXING", "MARKET_SHARING", "OUTPUT_RESTRICTION", "BID_RIGGING")
        is_prohibited = False
        nature = "COMPLIANT_COMMERCIAL_AGREEMENT"
        max_fine_rate = 0.0

        if agreement_type.upper() == "BID_RIGGING":
            is_prohibited = True
            nature = "CRIMINAL_BID_RIGGING_COLLUSION"
            max_fine_rate = 10.0  # Tịch thu và phạt nặng đến 10%
        elif is_horizontal and agreement_type.upper() in per_se_types:
            is_prohibited = True
            nature = f"STRICTLY_PROHIBITED_HORIZONTAL_CARTEL ({agreement_type})"
            max_fine_rate = 5.0  # Đến 5% tổng doanh thu theo Điều 111
        elif not is_horizontal and agreement_type.upper() in ("PRICE_FIXING", "MARKET_SHARING"):
            is_prohibited = True
            nature = f"PROHIBITED_VERTICAL_RESTRAINT ({agreement_type})"
            max_fine_rate = 5.0

        potential_fine = annual_revenue_vnd * (max_fine_rate / 100.0)

        notes = (
            "Hành vi thỏa thuận hạn chế cạnh tranh bị cấm tuyệt đối theo Điều 12 Luật Cạnh tranh 2018. "
            "Doanh nghiệp tự nguyện khai báo trước khi bị phát hiện có thể được hưởng chính sách khoan hồng (miễn giảm đến 100% tiền phạt)."
            if is_prohibited
            else "Thỏa thuận thương mại thông thường, không phát hiện dấu hiệu vi phạm thỏa thuận hạn chế cạnh tranh."
        )

        record = AntiCompetitiveAgreementAudit(
            audit_id=audit_id,
            agreement_title=agreement_title,
            parties_count=parties_count,
            agreement_type=agreement_type,
            is_horizontal=is_horizontal,
            is_prohibited=is_prohibited,
            violation_nature=nature,
            max_fine_rate_pct=max_fine_rate,
            potential_fine_vnd=potential_fine,
            remediation_notes=notes,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO anti_competitive_agreements
                (audit_id, agreement_title, parties_count, agreement_type, is_horizontal, is_prohibited,
                 violation_nature, max_fine_rate_pct, potential_fine_vnd, remediation_notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.agreement_title,
                    record.parties_count,
                    record.agreement_type,
                    1 if record.is_horizontal else 0,
                    1 if record.is_prohibited else 0,
                    record.violation_nature,
                    record.max_fine_rate_pct,
                    record.potential_fine_vnd,
                    record.remediation_notes,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def apply_leniency_program(
        self,
        enterprise_name: str,
        violation_id: str,
        submission_order: int = 1,
        self_confessed: bool = True,
        submitted_evidence: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluates leniency application under Article 112 Law on Competition 2018.
        Exemption policy:
        - 1st applicant: 100% fine exemption.
        - 2nd applicant: 60% fine exemption.
        - 3rd applicant: 40% fine exemption.
        - 4th+ applicant: 0% fine exemption.
        """
        application_id = f"LEN-{uuid.uuid4().hex[:8].upper()}"

        is_eligible = self_confessed and submitted_evidence
        exemption_pct = 0.0

        if is_eligible:
            if submission_order == 1:
                exemption_pct = 100.0
                status = "APPROVED_FULL_EXEMPTION (Miễn 100% tiền phạt)"
            elif submission_order == 2:
                exemption_pct = 60.0
                status = "APPROVED_PARTIAL_EXEMPTION (Giảm 60% tiền phạt)"
            elif submission_order == 3:
                exemption_pct = 40.0
                status = "APPROVED_PARTIAL_EXEMPTION (Giảm 40% tiền phạt)"
            else:
                exemption_pct = 0.0
                status = "REJECTED_QUOTA_EXCEEDED (Quá hạn ngạch tối đa 3 doanh nghiệp đầu tiên)"
        else:
            status = "REJECTED_INSUFFICIENT_COOPERATION (Chưa tự nguyện thú nhận hoặc chưa nộp chứng cứ có giá trị)"

        record = LeniencyApplication(
            application_id=application_id,
            violation_id=violation_id,
            enterprise_name=enterprise_name,
            submission_order=submission_order,
            self_confessed=self_confessed,
            submitted_evidence=submitted_evidence,
            is_eligible=is_eligible,
            fine_exemption_pct=exemption_pct,
            status=status,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO leniency_applications
                (application_id, violation_id, enterprise_name, submission_order, self_confessed,
                 submitted_evidence, is_eligible, fine_exemption_pct, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.application_id,
                    record.violation_id,
                    record.enterprise_name,
                    record.submission_order,
                    1 if record.self_confessed else 0,
                    1 if record.submitted_evidence else 0,
                    1 if record.is_eligible else 0,
                    record.fine_exemption_pct,
                    record.status,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists recent records by category ('all', 'concentrations', 'dominance', 'agreements', 'leniency').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "concentrations"):
                rows = conn.execute(
                    "SELECT * FROM economic_concentrations ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "concentration"
                    d["notification_triggers"] = json.loads(d["notification_triggers_json"])
                    d["reasons"] = json.loads(d["reasons_json"])
                    records.append(d)
            if category in ("all", "dominance"):
                rows = conn.execute(
                    "SELECT * FROM market_dominance_assessments ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "dominance"
                    d["cr_group_shares"] = json.loads(d["cr_group_shares_json"])
                    d["compliance_guidelines"] = json.loads(d["compliance_guidelines_json"])
                    records.append(d)
            if category in ("all", "agreements"):
                rows = conn.execute(
                    "SELECT * FROM anti_competitive_agreements ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "agreement"
                    records.append(d)
            if category in ("all", "leniency"):
                rows = conn.execute(
                    "SELECT * FROM leniency_applications ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "leniency"
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of competition and antitrust compliance.
        """
        with self._get_connection() as conn:
            conc_count = conn.execute("SELECT COUNT(*) FROM economic_concentrations").fetchone()[0]
            notif_req_count = conn.execute(
                "SELECT COUNT(*) FROM economic_concentrations WHERE requires_notification = 1"
            ).fetchone()[0]
            dom_count = conn.execute("SELECT COUNT(*) FROM market_dominance_assessments").fetchone()[0]
            dom_confirmed = conn.execute(
                "SELECT COUNT(*) FROM market_dominance_assessments WHERE is_dominant = 1"
            ).fetchone()[0]
            agr_count = conn.execute("SELECT COUNT(*) FROM anti_competitive_agreements").fetchone()[0]
            proh_count = conn.execute(
                "SELECT COUNT(*) FROM anti_competitive_agreements WHERE is_prohibited = 1"
            ).fetchone()[0]
            len_count = conn.execute("SELECT COUNT(*) FROM leniency_applications").fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on Competition 2018 (Law 23/2018/QH14) & Decree 35/2020/ND-CP",
            "supervisory_authority": "National Competition Commission (Ủy ban Cạnh tranh Quốc gia - NCC)",
            "total_concentrations_audited": conc_count,
            "notifications_required_count": notif_req_count,
            "total_dominance_assessments": dom_count,
            "dominant_positions_confirmed": dom_confirmed,
            "total_agreements_audited": agr_count,
            "prohibited_cartels_detected": proh_count,
            "leniency_applications_processed": len_count,
            "db_path": self.db_path,
        }
