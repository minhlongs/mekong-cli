"""
Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Engine.
Implements statutory compliance under:
- Law on Consumer Rights Protection 2023 (Law 19/2023/QH15, effective July 1, 2024)
- Decree 55/2024/ND-CP (Detailed regulations and measures for implementing Law on Consumer Rights Protection)
- Prime Minister Decision 07/2024/QD-TTg (List of essential goods/services requiring standard-form contract registration)
- Decree 98/2020/ND-CP & Decree 17/2022/ND-CP (Administrative penalties in consumer protection and commerce).

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


# Statutory transaction threshold for simplified summary court proceedings (Article 70 Law 19/2023/QH15)
SUMMARY_COURT_TRANSACTION_LIMIT_VND = 100_000_000.0  # 100 Million VND

# Essential industries requiring standard-form contract registration with National Competition Commission (Decision 07/2024/QD-TTg)
REGISTRATION_REQUIRED_INDUSTRIES = {
    "TELECOM",
    "ELECTRICITY",
    "CLEAN_WATER",
    "REAL_ESTATE_APARTMENT",
    "BANKING_CREDIT",
    "AIR_PASSENGER_TRANSPORT",
    "HEALTH_INSURANCE",
}


@dataclass
class DigitalPlatformComplianceAudit:
    audit_id: str
    platform_name: str
    platform_type: str
    has_transparent_algorithm_option: bool
    has_dark_patterns: bool
    dispute_mechanism_active: bool
    return_policy_days: int
    seller_verification_rate_pct: float
    is_compliant: bool
    violations: List[str]
    compliance_rating: str
    created_at: str


@dataclass
class StandardContractTermsReview:
    review_id: str
    contract_title: str
    industry_type: str
    excludes_seller_liability: bool
    restricts_consumer_dispute_rights: bool
    allows_unilateral_price_change: bool
    registered_with_ncc: bool
    is_valid: bool
    void_clauses: List[str]
    recommendations: List[str]
    created_at: str


@dataclass
class DefectiveProductRecallRecord:
    recall_id: str
    product_name: str
    defect_type: str            # GROUP_A_LIFE_THREATENING, GROUP_B_NORMAL
    batch_serial: str
    units_distributed: int
    units_recalled: int
    public_announcement_made_24h: bool
    reported_to_ministry: bool
    recall_status: str
    completion_rate_pct: float
    remedial_measures: List[str]
    created_at: str


@dataclass
class ConsumerDisputeCase:
    case_id: str
    complainant_name: str
    merchant_name: str
    transaction_value_vnd: float
    dispute_method: str         # NEGOTIATION, MEDIATION, ARBITRATION, SUMMARY_COURT_PROCEEDING
    has_evidence_invoice: bool
    seller_refused_compromise: bool
    eligible_for_summary_court: bool
    court_fee_exempt: bool
    recommended_next_steps: List[str]
    created_at: str


class ConsumerEngine:
    """
    Vietnamese Consumer Rights Protection, Digital Platform Transparency & Product Recall Engine.
    Operates with pure Python standard library and SQLite WAL persistence.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path:
            self.db_path = db_path
        else:
            base_dir = Path.home() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "consumer.db")
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
                CREATE TABLE IF NOT EXISTS platform_compliance_audits (
                    audit_id TEXT PRIMARY KEY,
                    platform_name TEXT NOT NULL,
                    platform_type TEXT NOT NULL,
                    has_transparent_algorithm_option INTEGER NOT NULL,
                    has_dark_patterns INTEGER NOT NULL,
                    dispute_mechanism_active INTEGER NOT NULL,
                    return_policy_days INTEGER NOT NULL,
                    seller_verification_rate_pct REAL NOT NULL,
                    is_compliant INTEGER NOT NULL,
                    violations_json TEXT NOT NULL,
                    compliance_rating TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS standard_contract_reviews (
                    review_id TEXT PRIMARY KEY,
                    contract_title TEXT NOT NULL,
                    industry_type TEXT NOT NULL,
                    excludes_seller_liability INTEGER NOT NULL,
                    restricts_consumer_dispute_rights INTEGER NOT NULL,
                    allows_unilateral_price_change INTEGER NOT NULL,
                    registered_with_ncc INTEGER NOT NULL,
                    is_valid INTEGER NOT NULL,
                    void_clauses_json TEXT NOT NULL,
                    recommendations_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS defective_product_recalls (
                    recall_id TEXT PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    defect_type TEXT NOT NULL,
                    batch_serial TEXT NOT NULL,
                    units_distributed INTEGER NOT NULL,
                    units_recalled INTEGER NOT NULL,
                    public_announcement_made_24h INTEGER NOT NULL,
                    reported_to_ministry INTEGER NOT NULL,
                    recall_status TEXT NOT NULL,
                    completion_rate_pct REAL NOT NULL,
                    remedial_measures_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS consumer_dispute_cases (
                    case_id TEXT PRIMARY KEY,
                    complainant_name TEXT NOT NULL,
                    merchant_name TEXT NOT NULL,
                    transaction_value_vnd REAL NOT NULL,
                    dispute_method TEXT NOT NULL,
                    has_evidence_invoice INTEGER NOT NULL,
                    seller_refused_compromise INTEGER NOT NULL,
                    eligible_for_summary_court INTEGER NOT NULL,
                    court_fee_exempt INTEGER NOT NULL,
                    recommended_next_steps_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    def audit_digital_platform_compliance(
        self,
        platform_name: str,
        platform_type: str = "E_COMMERCE_MARKETPLACE",
        has_transparent_algorithm_option: bool = True,
        has_dark_patterns: bool = False,
        dispute_mechanism_active: bool = True,
        return_policy_days: int = 15,
        seller_verification_rate_pct: float = 100.0,
    ) -> Dict[str, Any]:
        """
        Audits digital platform and e-commerce intermediary compliance under Articles 37-40 Law on Consumer Rights Protection 2023.
        """
        audit_id = f"PLT-AUD-{uuid.uuid4().hex[:8].upper()}"
        violations: List[str] = []

        if not has_transparent_algorithm_option:
            violations.append(
                "Nền tảng số không cung cấp tùy chọn tắt quảng cáo hướng đối tượng (Targeted Advertising) hoặc gợi ý hành vi theo Khoản 2 Điều 39."
            )

        if has_dark_patterns:
            violations.append(
                "Phát hiện thủ thuật giao diện thao túng tâm lý (Dark Patterns): tự động kích hoạt tính năng thanh toán, ép mua kèm hàng hóa (Khoản 1 Điều 39)."
            )

        if not dispute_mechanism_active:
            violations.append(
                "Chưa thiết lập quy trình trực tuyến tiếp nhận và xử lý khiếu nại người tiêu dùng trong thời hạn 03 ngày làm việc (Điều 38)."
            )

        if return_policy_days < 7:
            violations.append(
                f"Chính sách đổi trả/hoàn tiền ({return_policy_days} ngày) vi phạm quyền đổi trả tối thiểu 07 ngày đối với giao dịch từ xa (Điều 37)."
            )

        if seller_verification_rate_pct < 100.0:
            violations.append(
                f"Tỷ lệ xác minh danh tính người bán ({seller_verification_rate_pct}%) chưa đạt chuẩn bắt buộc 100% tài khoản bán hàng trên sàn TMĐT."
            )

        is_compliant = len(violations) == 0
        if is_compliant:
            compliance_rating = "ĐẠT CHUẨN NỀN TẢNG SỐ BẢO VỆ NGƯỜI TIÊU DÙNG (COMPLIANT)"
        elif has_dark_patterns or not dispute_mechanism_active:
            compliance_rating = "VI PHẠM NGHIÊM TRỌNG LUẬT BVQLNTD 2023 (CRITICAL_NON_COMPLIANT)"
        else:
            compliance_rating = "CẦN KHẮC PHỤC CHÍNH SÁCH BÁN HÀNG (WARNING_AMENDMENT_REQUIRED)"

        record = DigitalPlatformComplianceAudit(
            audit_id=audit_id,
            platform_name=platform_name,
            platform_type=platform_type,
            has_transparent_algorithm_option=has_transparent_algorithm_option,
            has_dark_patterns=has_dark_patterns,
            dispute_mechanism_active=dispute_mechanism_active,
            return_policy_days=return_policy_days,
            seller_verification_rate_pct=seller_verification_rate_pct,
            is_compliant=is_compliant,
            violations=violations,
            compliance_rating=compliance_rating,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO platform_compliance_audits
                (audit_id, platform_name, platform_type, has_transparent_algorithm_option,
                 has_dark_patterns, dispute_mechanism_active, return_policy_days,
                 seller_verification_rate_pct, is_compliant, violations_json, compliance_rating, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.audit_id,
                    record.platform_name,
                    record.platform_type,
                    1 if record.has_transparent_algorithm_option else 0,
                    1 if record.has_dark_patterns else 0,
                    1 if record.dispute_mechanism_active else 0,
                    record.return_policy_days,
                    record.seller_verification_rate_pct,
                    1 if record.is_compliant else 0,
                    json.dumps(record.violations, ensure_ascii=False),
                    record.compliance_rating,
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def audit_standard_contract_terms(
        self,
        contract_title: str,
        industry_type: str = "E_COMMERCE",
        excludes_seller_liability: bool = False,
        restricts_consumer_dispute_rights: bool = False,
        allows_unilateral_price_change: bool = False,
        registered_with_ncc: bool = True,
    ) -> Dict[str, Any]:
        """
        Reviews standard-form contracts and general terms & conditions under Article 25 Law 19/2023/QH15 & Decision 07/2024/QD-TTg.
        """
        review_id = f"CTR-REV-{uuid.uuid4().hex[:8].upper()}"
        void_clauses: List[str] = []
        recommendations: List[str] = []

        ind = industry_type.upper()
        requires_registration = ind in REGISTRATION_REQUIRED_INDUSTRIES

        if requires_registration and not registered_with_ncc:
            void_clauses.append(
                f"Ngành hàng '{ind}' thuộc Danh mục bắt buộc đăng ký hợp đồng theo mẫu với Ủy ban Cạnh tranh Quốc gia trước khi áp dụng (QĐ 07/2024/QĐ-TTg)."
            )

        if excludes_seller_liability:
            void_clauses.append(
                "ĐIỀU KHOẢN VÔ HIỆU: Loại trừ hoặc hạn chế trách nhiệm bồi thường thiệt hại của tổ chức, cá nhân kinh doanh (Điểm a Khoản 1 Điều 25)."
            )
            recommendations.append(
                "Xóa bỏ điều khoản miễn trừ trách nhiệm; bên bán phải chịu trách nhiệm về chất lượng hàng hóa cung cấp."
            )

        if restricts_consumer_dispute_rights:
            void_clauses.append(
                "ĐIỀU KHOẢN VÔ HIỆU: Hạn chế quyền khiếu nại, khởi kiện ra Tòa án hoặc ép buộc người tiêu dùng lựa chọn Trọng tài (Điểm d Khoản 1 Điều 25)."
            )
            recommendations.append(
                "Quy định quyền khởi kiện của người tiêu dùng tại Tòa án nhân dân nơi người tiêu dùng cư trú."
            )

        if allows_unilateral_price_change:
            void_clauses.append(
                "ĐIỀU KHOẢN VÔ HIỆU: Cho phép bên bán đơn phương thay đổi giá cả, số lượng hoặc điều kiện hợp đồng mà không có sự thỏa thuận trước (Điểm đ Khoản 1 Điều 25)."
            )
            recommendations.append(
                "Mọi thay đổi về giá bán hoặc điều kiện dịch vụ phải thông báo trước tối thiểu 30 ngày và có sự đồng ý của khách hàng."
            )

        is_valid = len(void_clauses) == 0
        if is_valid:
            recommendations.append(
                "Bộ điều khoản giao dịch chung tuân thủ đầy đủ Luật Bảo vệ quyền lợi người tiêu dùng 2023."
            )

        record = StandardContractTermsReview(
            review_id=review_id,
            contract_title=contract_title,
            industry_type=ind,
            excludes_seller_liability=excludes_seller_liability,
            restricts_consumer_dispute_rights=restricts_consumer_dispute_rights,
            allows_unilateral_price_change=allows_unilateral_price_change,
            registered_with_ncc=registered_with_ncc,
            is_valid=is_valid,
            void_clauses=void_clauses,
            recommendations=recommendations,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO standard_contract_reviews
                (review_id, contract_title, industry_type, excludes_seller_liability,
                 restricts_consumer_dispute_rights, allows_unilateral_price_change,
                 registered_with_ncc, is_valid, void_clauses_json, recommendations_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.review_id,
                    record.contract_title,
                    record.industry_type,
                    1 if record.excludes_seller_liability else 0,
                    1 if record.restricts_consumer_dispute_rights else 0,
                    1 if record.allows_unilateral_price_change else 0,
                    1 if record.registered_with_ncc else 0,
                    1 if record.is_valid else 0,
                    json.dumps(record.void_clauses, ensure_ascii=False),
                    json.dumps(record.recommendations, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def manage_defective_product_recall(
        self,
        product_name: str,
        defect_type: str = "GROUP_A_LIFE_THREATENING",
        batch_serial: str = "BAT-2026-X1",
        units_distributed: int = 10000,
        units_recalled: int = 8500,
        public_announcement_made_24h: bool = True,
        reported_to_ministry: bool = True,
    ) -> Dict[str, Any]:
        """
        Manages and monitors defective product recall under Articles 32-34 Law on Consumer Rights Protection 2023.
        """
        recall_id = f"RCL-PRD-{uuid.uuid4().hex[:8].upper()}"
        remedial_measures: List[str] = []

        d_type = defect_type.upper()
        is_group_a = "GROUP_A" in d_type

        completion_rate = (units_recalled / units_distributed * 100.0) if units_distributed > 0 else 0.0

        if is_group_a and not public_announcement_made_24h:
            remedial_measures.append(
                "VI PHẠM NGHIÊM TRỌNG: Sản phẩm khuyết tật Nhóm A có nguy cơ đe dọa tính mạng/tài sản nhưng không công bố công khai trong 24 giờ (Điều 33)."
            )

        if not reported_to_ministry:
            remedial_measures.append(
                "Chưa gửi báo cáo chương trình thu hồi và biện pháp khắc phục tới Bộ Công Thương và cơ quan chuyên môn theo luật định."
            )

        if completion_rate < 100.0:
            remedial_measures.append(
                f"Tiến độ thu hồi đạt {completion_rate:.1f}%. Tiếp tục duy trì điểm tiếp nhận thu hồi và bồi hoàn chi phí cho người tiêu dùng theo Điều 34."
            )
        else:
            remedial_measures.append(
                "Hoàn thành 100% thu hồi sản phẩm khuyết tật. Lập biên bản tiêu hủy hoặc khắc phục kỹ thuật và nghiệm thu kết thúc chương trình."
            )

        if is_group_a and not public_announcement_made_24h:
            recall_status = "CRITICAL_NON_COMPLIANT_RECALL (Vi phạm nghĩa vụ công bố thu hồi khẩn cấp)"
        elif completion_rate >= 90.0:
            recall_status = "SUCCESSFUL_RECALL_PROGRESS (Tiến độ thu hồi đạt hiệu quả cao)"
        else:
            recall_status = "ONGOING_RECALL_MANDATORY (Đang triển khai thu hồi bắt buộc)"

        record = DefectiveProductRecallRecord(
            recall_id=recall_id,
            product_name=product_name,
            defect_type=d_type,
            batch_serial=batch_serial,
            units_distributed=units_distributed,
            units_recalled=units_recalled,
            public_announcement_made_24h=public_announcement_made_24h,
            reported_to_ministry=reported_to_ministry,
            recall_status=recall_status,
            completion_rate_pct=round(completion_rate, 2),
            remedial_measures=remedial_measures,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO defective_product_recalls
                (recall_id, product_name, defect_type, batch_serial, units_distributed,
                 units_recalled, public_announcement_made_24h, reported_to_ministry,
                 recall_status, completion_rate_pct, remedial_measures_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.recall_id,
                    record.product_name,
                    record.defect_type,
                    record.batch_serial,
                    record.units_distributed,
                    record.units_recalled,
                    1 if record.public_announcement_made_24h else 0,
                    1 if record.reported_to_ministry else 0,
                    record.recall_status,
                    record.completion_rate_pct,
                    json.dumps(record.remedial_measures, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def assess_consumer_dispute(
        self,
        complainant_name: str,
        merchant_name: str,
        transaction_value_vnd: float = 25_000_000.0,
        dispute_method: str = "SUMMARY_COURT_PROCEEDING",
        has_evidence_invoice: bool = True,
        seller_refused_compromise: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluates consumer dispute and simplified court proceeding eligibility under Articles 70-71 Law 19/2023/QH15.
        """
        case_id = f"DSP-CSE-{uuid.uuid4().hex[:8].upper()}"
        recommended_next_steps: List[str] = []

        is_under_100m = transaction_value_vnd <= SUMMARY_COURT_TRANSACTION_LIMIT_VND
        eligible_for_summary_court = is_under_100m and has_evidence_invoice

        # Article 71: Consumers initiating lawsuit to protect their rights are exempt from advance court fees
        court_fee_exempt = True

        if eligible_for_summary_court:
            recommended_next_steps.append(
                f"ĐỦ ĐIỀU KIỆN ÁP DỤNG THỦ TỤC RÚT GỌN TẠI TÒA ÁN (Giao dịch {transaction_value_vnd:,.0f} VND <= 100.000.000 VND theo Điều 70 Luật BVQLNTD)."
            )
            recommended_next_steps.append(
                "Người tiêu dùng ĐƯỢC MIỄN NỘP TIỀN TẠM ỨNG ÁN PHÍ, LỆ PHÍ TÒA ÁN khi nộp đơn khởi kiện (Khoản 1 Điều 71)."
            )
        else:
            if not has_evidence_invoice:
                recommended_next_steps.append(
                    "Cần bổ sung chứng từ, hóa đơn VAT hoặc dữ liệu điện tử chứng minh giao dịch mua bán để hoàn thiện hồ sơ khởi kiện."
                )
            if not is_under_100m:
                recommended_next_steps.append(
                    f"Giá trị giao dịch ({transaction_value_vnd:,.0f} VND > 100 triệu VND) sẽ giải quyết theo thủ tục tố tụng dân sự thông thường."
                )

        if seller_refused_compromise:
            recommended_next_steps.append(
                "Bên bán từ chối thương lượng/hòa giải -> Gửi đơn khiếu nại tới Ủy ban Cạnh tranh Quốc gia hoặc Hội Bảo vệ quyền lợi người tiêu dùng (VICOPRO) để hỗ trợ khởi kiện tập thể."
            )

        record = ConsumerDisputeCase(
            case_id=case_id,
            complainant_name=complainant_name,
            merchant_name=merchant_name,
            transaction_value_vnd=transaction_value_vnd,
            dispute_method=dispute_method,
            has_evidence_invoice=has_evidence_invoice,
            seller_refused_compromise=seller_refused_compromise,
            eligible_for_summary_court=eligible_for_summary_court,
            court_fee_exempt=court_fee_exempt,
            recommended_next_steps=recommended_next_steps,
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO consumer_dispute_cases
                (case_id, complainant_name, merchant_name, transaction_value_vnd,
                 dispute_method, has_evidence_invoice, seller_refused_compromise,
                 eligible_for_summary_court, court_fee_exempt, recommended_next_steps_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.case_id,
                    record.complainant_name,
                    record.merchant_name,
                    record.transaction_value_vnd,
                    record.dispute_method,
                    1 if record.has_evidence_invoice else 0,
                    1 if record.seller_refused_compromise else 0,
                    1 if record.eligible_for_summary_court else 0,
                    1 if record.court_fee_exempt else 0,
                    json.dumps(record.recommended_next_steps, ensure_ascii=False),
                    record.created_at,
                ),
            )
            conn.commit()

        return asdict(record)

    def list_records(self, category: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lists stored records by category ('all', 'platforms', 'contracts', 'recalls', 'disputes').
        """
        records: List[Dict[str, Any]] = []
        with self._get_connection() as conn:
            if category in ("all", "platforms"):
                rows = conn.execute(
                    "SELECT * FROM platform_compliance_audits ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "platform_audit"
                    d["violations"] = json.loads(d["violations_json"])
                    records.append(d)
            if category in ("all", "contracts"):
                rows = conn.execute(
                    "SELECT * FROM standard_contract_reviews ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "contract_review"
                    d["void_clauses"] = json.loads(d["void_clauses_json"])
                    d["recommendations"] = json.loads(d["recommendations_json"])
                    records.append(d)
            if category in ("all", "recalls"):
                rows = conn.execute(
                    "SELECT * FROM defective_product_recalls ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "product_recall"
                    d["remedial_measures"] = json.loads(d["remedial_measures_json"])
                    records.append(d)
            if category in ("all", "disputes"):
                rows = conn.execute(
                    "SELECT * FROM consumer_dispute_cases ORDER BY created_at DESC LIMIT ?", (limit,)
                ).fetchall()
                for r in rows:
                    d = dict(r)
                    d["type"] = "consumer_dispute"
                    d["recommended_next_steps"] = json.loads(d["recommended_next_steps_json"])
                    records.append(d)
        return records

    def get_status(self) -> Dict[str, Any]:
        """
        Returns telemetry summary of consumer rights protection, digital platform compliance, recalls, and disputes.
        """
        with self._get_connection() as conn:
            plt_count = conn.execute("SELECT COUNT(*) FROM platform_compliance_audits").fetchone()[0]
            plt_ok = conn.execute(
                "SELECT COUNT(*) FROM platform_compliance_audits WHERE is_compliant = 1"
            ).fetchone()[0]
            ctr_count = conn.execute("SELECT COUNT(*) FROM standard_contract_reviews").fetchone()[0]
            ctr_ok = conn.execute(
                "SELECT COUNT(*) FROM standard_contract_reviews WHERE is_valid = 1"
            ).fetchone()[0]
            rcl_count = conn.execute("SELECT COUNT(*) FROM defective_product_recalls").fetchone()[0]
            dsp_count = conn.execute("SELECT COUNT(*) FROM consumer_dispute_cases").fetchone()[0]
            dsp_summary_court = conn.execute(
                "SELECT COUNT(*) FROM consumer_dispute_cases WHERE eligible_for_summary_court = 1"
            ).fetchone()[0]

        return {
            "status": "operational",
            "regulatory_framework": "Law on Consumer Rights Protection 2023 (Law 19/2023/QH15), Decree 55/2024/ND-CP, Decision 07/2024/QD-TTg",
            "competent_authority": "Ủy ban Cạnh tranh Quốc gia (Bộ Công Thương) & Hội VICOPRO",
            "total_platforms_audited": plt_count,
            "compliant_digital_platforms": plt_ok,
            "total_standard_contracts_reviewed": ctr_count,
            "valid_standard_contracts": ctr_ok,
            "active_product_recalls": rcl_count,
            "consumer_dispute_cases_total": dsp_count,
            "summary_court_eligible_cases": dsp_summary_court,
            "db_path": self.db_path,
        }
