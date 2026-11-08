# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Vietnamese Personal Data Protection Decree (PDPD - Nghị định 13/2023/NĐ-CP) & Privacy Engine.

Implements statutory personal data protection and cross-border transfer compliance under:
- Nghị định 13/2023/NĐ-CP của Chính phủ về Bảo vệ dữ liệu cá nhân (PDPD):
  * Phân loại dữ liệu cá nhân (Điều 2): Dữ liệu cá nhân cơ bản vs Dữ liệu cá nhân nhạy cảm
    (tài chính, ngân hàng, sinh trắc học, định vị vị trí, hồ sơ bệnh án y tế, v.v.).
  * Quyền của chủ thể dữ liệu (Điều 9): 11 quyền cơ bản bao gồm quyền được biết, đồng ý, truy cập,
    rút lại sự đồng ý, xóa dữ liệu, hạn chế xử lý, cung cấp dữ liệu, phản đối xử lý, khiếu nại, bồi thường, tự bảo vệ.
  * Đánh giá tác động xử lý dữ liệu cá nhân - DPIA (Điều 24):
    Lập hồ sơ theo Mẫu số 04 gửi Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05 - Bộ Công an)
    trong thời hạn 60 ngày kể từ ngày tiến hành xử lý dữ liệu cá nhân.
  * Chuyển dữ liệu cá nhân ra nước ngoài - Cross-Border Data Transfer (Điều 25):
    Đánh giá tác động chuyển dữ liệu (TIA), ký kết thỏa thuận cam kết bảo vệ dữ liệu (tương đương SCC),
    gửi 01 bộ hồ sơ chính đến A05 - Bộ Công an trong 60 ngày.
  * Thông báo vi phạm quy định bảo vệ dữ liệu cá nhân (Điều 26):
    Bắt buộc thông báo cho Bộ Công an (A05) trong vòng 72 giờ kể từ khi phát hiện sự cố rò rỉ, mất mát dữ liệu.
  * Bổ nhiệm Nhân sự/Bộ phận bảo vệ dữ liệu cá nhân (DPO - Điều 28) đối với dữ liệu cá nhân nhạy cảm.
- Luật An toàn thông tin mạng 2015 & Luật An ninh mạng 2018.
- Lưu trữ SQLite WAL tại ``.mekong/privacy.db``.

Pure Python standard-library-only implementation adhering strictly to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import contextlib
import datetime
import os
import pathlib
import sqlite3
import typing
import uuid

# ---------------------------------------------------------------------------
# PDPD Statutory Categories & Thresholds (Nghị định 13/2023/NĐ-CP)
# ---------------------------------------------------------------------------

BASIC_DATA_CATEGORIES: list[str] = [
    "FULL_NAME",  # Họ, chữ đệm và tên khai sinh
    "DOB",  # Ngày, tháng, năm sinh
    "GENDER",  # Giới tính
    "RESIDENCE",  # Nơi cư trú, nơi thường trú, nơi tạm trú
    "NATIONALITY",  # Quốc tịch
    "IMAGE",  # Hình ảnh của cá nhân
    "PHONE_NUMBER",  # Số điện thoại
    "ID_CARD_NUMBER",  # Số CMND/CCCD, số định danh cá nhân, số hộ chiếu
    "TAX_CODE",  # Mã số thuế cá nhân
    "EMAIL",  # Địa chỉ thư điện tử
    "DIGITAL_IDENTITY",  # Tài khoản số, dữ liệu cá nhân phản ánh hoạt động trên không gian mạng
]

SENSITIVE_DATA_CATEGORIES: list[str] = [
    "POLITICAL_RELIGIOUS_VIEWS",  # Quan điểm chính trị, quan điểm tôn giáo
    "HEALTH_MEDICAL_RECORDS",  # Tình trạng sức khỏe và đời tư ghi trong hồ sơ bệnh án
    "BIOMETRICS",  # Dữ liệu sinh trắc học (vân tay, khuôn mặt, mống mắt)
    "GENETIC_DATA",  # Dữ liệu di truyền
    "LOCATION_TRACKING",  # Vị trí địa lý thực tế của cá nhân
    "BANKING_FINANCIAL",  # Thông tin tài khoản ngân hàng, thẻ thanh toán, lịch sử giao dịch
    "CRIMINAL_RECORDS",  # Dữ liệu về tội phạm, hành vi phạm tội được thu thập
    "SEXUAL_ORIENTATION",  # Xu hướng tình dục, đời sống tình dục
]

DATA_SUBJECT_RIGHTS: dict[str, str] = {
    "RIGHT_TO_KNOW": "Quyền được biết về hoạt động xử lý dữ liệu (Điều 9.1)",
    "RIGHT_TO_CONSENT": "Quyền đồng ý hoặc không đồng ý xử lý dữ liệu (Điều 9.2)",
    "RIGHT_TO_ACCESS": "Quyền truy cập để xem, chỉnh sửa dữ liệu cá nhân (Điều 9.3)",
    "RIGHT_TO_WITHDRAW_CONSENT": "Quyền rút lại sự đồng ý đã cung cấp (Điều 9.4)",
    "RIGHT_TO_DELETE": "Quyền xóa dữ liệu hoặc yêu cầu xóa dữ liệu (Điều 9.5)",
    "RIGHT_TO_RESTRICT": "Quyền yêu cầu hạn chế xử lý dữ liệu cá nhân (Điều 9.6)",
    "RIGHT_TO_DATA_PORTABILITY": "Quyền yêu cầu cung cấp dữ liệu cá nhân của mình (Điều 9.7)",
    "RIGHT_TO_OBJECT": "Quyền phản đối Bên kiểm soát xử lý dữ liệu (Điều 9.8)",
    "RIGHT_TO_COMPLAIN": "Quyền khiếu nại, tố cáo hoặc khởi kiện theo luật (Điều 9.9)",
    "RIGHT_TO_CLAIM_DAMAGES": "Quyền yêu cầu bồi thường thiệt hại khi xảy ra vi phạm (Điều 9.10)",
    "RIGHT_TO_SELF_DEFENSE": "Quyền tự bảo vệ theo quy định của Bộ luật Dân sự (Điều 9.11)",
}

CONTROLLER_TYPES: dict[str, str] = {
    "CONTROLLER": "Bên Kiểm soát dữ liệu cá nhân (Data Controller)",
    "PROCESSOR": "Bên Xử lý dữ liệu cá nhân (Data Processor)",
    "CONTROLLER_AND_PROCESSOR": "Bên Kiểm soát và xử lý dữ liệu cá nhân (Data Controller & Processor)",
    "THIRD_PARTY": "Bên thứ ba được phép xử lý dữ liệu cá nhân",
}

BREACH_MAX_NOTIFICATION_HOURS: int = 72  # Thời hạn tối đa 72h thông báo Bộ Công an A05 (Điều 26)
DPIA_FILING_DEADLINE_DAYS: int = 60  # Thời hạn lập & nộp hồ sơ DPIA trong 60 ngày (Điều 24 & 25)


class RecordList(list):
    """List subclass that supports both list iteration and dict-like key lookups."""

    def __init__(self, items: list, key: str = "items") -> None:
        super().__init__(items)
        self.key = key

    def __getitem__(self, item: typing.Any) -> typing.Any:
        if isinstance(item, str):
            if item == "ok":
                return True
            if item in (self.key, "records", "assessments", "transfers", "breaches", "requests"):
                return list(self)
            raise KeyError(item)
        return super().__getitem__(item)

    def __contains__(self, item: typing.Any) -> bool:
        if isinstance(item, str) and item in ("ok", self.key, "records", "assessments", "transfers", "breaches", "requests"):
            return True
        return super().__contains__(item)

    def get(self, item: str, default: typing.Any = None) -> typing.Any:
        if item == "ok":
            return True
        if item in (self.key, "records", "assessments", "transfers", "breaches", "requests"):
            return list(self)
        return default


class PrivacyEngine:
    """Autonomous Vietnamese Personal Data Protection Decree (PDPD) Engine."""

    def __init__(self, db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None) -> None:
        if db_path is not None:
            self.db_path = pathlib.Path(db_path)
        else:
            base_dir = pathlib.Path(os.environ.get("MEKONG_ROOT", "."))
            mekong_dir = base_dir / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "privacy.db"
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
                CREATE TABLE IF NOT EXISTS compliance_audits (
                    audit_id TEXT PRIMARY KEY,
                    enterprise_name TEXT NOT NULL,
                    controller_type TEXT NOT NULL,
                    has_sensitive_data INTEGER NOT NULL,
                    has_dpo INTEGER NOT NULL,
                    has_cross_border INTEGER NOT NULL,
                    compliance_score REAL NOT NULL,
                    compliance_status TEXT NOT NULL,
                    recommendations TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dpia_assessments (
                    dpia_id TEXT PRIMARY KEY,
                    activity_name TEXT NOT NULL,
                    processing_purpose TEXT NOT NULL,
                    data_categories TEXT NOT NULL,
                    is_sensitive INTEGER NOT NULL,
                    legal_basis TEXT NOT NULL,
                    security_measures TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    form_04_ready INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS cross_border_transfers (
                    transfer_id TEXT PRIMARY KEY,
                    transfer_name TEXT NOT NULL,
                    recipient_entity TEXT NOT NULL,
                    destination_country TEXT NOT NULL,
                    data_types TEXT NOT NULL,
                    record_count INTEGER NOT NULL,
                    has_scc INTEGER NOT NULL,
                    a05_notified INTEGER NOT NULL,
                    risk_assessment TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS breach_incidents (
                    incident_id TEXT PRIMARY KEY,
                    incident_name TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    affected_count INTEGER NOT NULL,
                    breach_type TEXT NOT NULL,
                    hours_elapsed REAL NOT NULL,
                    is_72h_compliant INTEGER NOT NULL,
                    a05_reported INTEGER NOT NULL,
                    mitigation_plan TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dsar_requests (
                    request_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    status TEXT NOT NULL,
                    deadline_days INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS consent_log (
                    consent_id TEXT PRIMARY KEY,
                    subject_id TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    legal_basis TEXT NOT NULL,
                    consent_given INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL,
                    withdrawn_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_audit_ent ON compliance_audits(enterprise_name);
                CREATE INDEX IF NOT EXISTS idx_dpia_act ON dpia_assessments(activity_name);
                CREATE INDEX IF NOT EXISTS idx_transfer_dest ON cross_border_transfers(destination_country);
                CREATE INDEX IF NOT EXISTS idx_breach_sev ON breach_incidents(severity);
                CREATE INDEX IF NOT EXISTS idx_dsar_sub ON dsar_requests(subject_id);
                """
            )
            conn.commit()

    # -----------------------------------------------------------------------
    # PDPD Enterprise Compliance Audit (Nghị định 13/2023/NĐ-CP)
    # -----------------------------------------------------------------------

    def audit_enterprise_compliance(
        self,
        enterprise_name: str,
        controller_type: str = "CONTROLLER_AND_PROCESSOR",
        has_sensitive_data: bool = False,
        has_dpo: bool = False,
        has_cross_border: bool = False,
        has_dpia_dossier: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Conduct enterprise data privacy compliance audit against Decree 13/2023/ND-CP."""
        clean_type = controller_type.upper().strip()
        if clean_type not in CONTROLLER_TYPES:
            clean_type = "CONTROLLER_AND_PROCESSOR"

        score: float = 100.0
        gaps: list[str] = []
        recommendations: list[str] = []

        # Check DPO requirement for sensitive data (Article 28)
        if has_sensitive_data and not has_dpo:
            score -= 25.0
            gaps.append("Thiếu Nhân sự / Bộ phận Bảo vệ dữ liệu cá nhân (DPO) cho dữ liệu cá nhân nhạy cảm (Điều 28).")
            recommendations.append("Bổ nhiệm ngay DPO hoặc chỉ định phòng ban chuyên trách bảo vệ dữ liệu cá nhân theo Điều 28 Nghị định 13.")

        # Check DPIA dossier requirement (Article 24)
        if not has_dpia_dossier:
            score -= 30.0
            gaps.append("Chưa hoàn thành Hồ sơ đánh giá tác động xử lý dữ liệu cá nhân (DPIA - Điều 24).")
            recommendations.append("Lập hồ sơ DPIA theo Mẫu số 04 gửi Cục A05 - Bộ Công an trong thời hạn 60 ngày.")

        # Check Cross-border transfer dossier requirement (Article 25)
        if has_cross_border:
            recommendations.append("Lập Hồ sơ đánh giá tác động chuyển dữ liệu ra nước ngoài và ký thỏa thuận bảo vệ dữ liệu (SCC) gửi A05 (Điều 25).")

        # Determine compliance status
        if score >= 90.0:
            status = "COMPLIANT"
            status_desc = "Doanh nghiệp tuân thủ tốt các quy định trọng yếu của Nghị định 13/2023/NĐ-CP."
        elif score >= 70.0:
            status = "PARTIALLY_COMPLIANT"
            status_desc = "Doanh nghiệp đáp ứng phần lớn nhưng còn thiếu sót thủ tục hành chính hoặc hồ sơ A05."
        else:
            status = "HIGH_NON_COMPLIANCE_RISK"
            status_desc = "Doanh nghiệp có rủi ro pháp lý cao, có nguy cơ bị phạt hành chính hoặc đình chỉ xử lý dữ liệu."

        audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "audit_id": audit_id,
            "enterprise_name": enterprise_name,
            "controller_role": clean_type,
            "role_description": CONTROLLER_TYPES[clean_type],
            "audit_criteria": {
                "has_sensitive_data": has_sensitive_data,
                "has_dpo": has_dpo,
                "has_cross_border_transfer": has_cross_border,
                "has_dpia_dossier": has_dpia_dossier,
            },
            "compliance_score": round(score, 1),
            "compliance_status": status,
            "status_description": status_desc,
            "compliance_gaps": gaps,
            "statutory_recommendations": recommendations,
            "governing_law": "Nghị định 13/2023/NĐ-CP về Bảo vệ dữ liệu cá nhân (Bộ Công an)",
            "audited_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO compliance_audits (
                        audit_id, enterprise_name, controller_type, has_sensitive_data,
                        has_dpo, has_cross_border, compliance_score, compliance_status,
                        recommendations, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        audit_id,
                        enterprise_name,
                        clean_type,
                        1 if has_sensitive_data else 0,
                        1 if has_dpo else 0,
                        1 if has_cross_border else 0,
                        score,
                        status,
                        "; ".join(recommendations),
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Data Protection Impact Assessment (DPIA - Điều 24)
    # -----------------------------------------------------------------------

    def create_dpia_assessment(
        self,
        activity_name: str,
        processing_purpose: str,
        data_categories: list[str],
        legal_basis: str = "CONSENT",
        security_measures: str = "AES-256 Encryption, Role-Based Access Control, TLS 1.3",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Create DPIA dossier under Article 24 Decree 13/2023/ND-CP (Form 04 / Mẫu số 04)."""
        is_sensitive = any(cat.upper() in SENSITIVE_DATA_CATEGORIES for cat in data_categories)

        # Risk classification
        if is_sensitive:
            risk_level = "HIGH_RISK"
            risk_desc = "Hoạt động xử lý có chứa Dữ liệu cá nhân nhạy cảm, bắt buộc áp dụng biện pháp kỹ thuật cao và chỉ định DPO."
        elif len(data_categories) > 5:
            risk_level = "MEDIUM_RISK"
            risk_desc = "Hoạt động xử lý khối lượng lớn trường dữ liệu cơ bản, cần rà soát biện pháp phân quyền truy cập."
        else:
            risk_level = "LOW_RISK"
            risk_desc = "Hoạt động xử lý dữ liệu cơ bản ở mức tiêu chuẩn."

        dpia_id = f"DPIA-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline = now + datetime.timedelta(days=DPIA_FILING_DEADLINE_DAYS)

        result = {
            "ok": True,
            "dpia_id": dpia_id,
            "activity_name": activity_name,
            "processing_purpose": processing_purpose,
            "data_categories": data_categories,
            "is_sensitive_data_processed": is_sensitive,
            "legal_basis": legal_basis,
            "security_measures": security_measures,
            "risk_assessment": {
                "risk_level": risk_level,
                "description": risk_desc,
                "dpo_mandatory": is_sensitive,
            },
            "form_04_a05": {
                "status": "DOSSIER_COMPILED",
                "form_template": "Mẫu số 04 - Đánh giá tác động xử lý dữ liệu cá nhân (NĐ 13/2023/NĐ-CP)",
                "filing_recipient": "Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05 - Bộ Công an)",
                "submission_deadline": deadline.strftime("%Y-%m-%d"),
                "statutory_retention": "Lưu trữ tại trụ sở Doanh nghiệp và sẵn sàng phục vụ thanh tra, kiểm tra",
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO dpia_assessments (
                        dpia_id, activity_name, processing_purpose, data_categories,
                        is_sensitive, legal_basis, security_measures, risk_level,
                        form_04_ready, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        dpia_id,
                        activity_name,
                        processing_purpose,
                        ", ".join(data_categories),
                        1 if is_sensitive else 0,
                        legal_basis,
                        security_measures,
                        risk_level,
                        1,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Cross-Border Data Transfer Assessment (Điều 25)
    # -----------------------------------------------------------------------

    def evaluate_cross_border_transfer(
        self,
        transfer_name: str,
        recipient_entity: str,
        destination_country: str,
        data_types: list[str],
        record_count: int = 1000,
        has_scc: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Evaluate cross-border data transfer compliance under Article 25 Decree 13/2023/ND-CP."""
        has_sensitive = any(dt.upper() in SENSITIVE_DATA_CATEGORIES for dt in data_types)

        compliance_checks = {
            "has_data_transfer_agreement": has_scc,
            "has_recipient_protection_guarantee": has_scc,
            "is_sensitive_data_included": has_sensitive,
            "filing_to_a05_required": True,
        }

        if has_scc:
            status = "PERMITTED_WITH_FILING"
            status_note = "Hợp lệ để chuyển dữ liệu ra nước ngoài sau khi hoàn tất hồ sơ gửi A05 - Bộ Công an."
        else:
            status = "RESTRICTED_MISSING_SCC"
            status_note = "CẢNH BÁO: Chưa có văn bản cam kết bảo vệ dữ liệu giữa Bên chuyển và Bên nhận theo Điều 25.2."

        transfer_id = f"XFER-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline = now + datetime.timedelta(days=DPIA_FILING_DEADLINE_DAYS)

        result = {
            "ok": True,
            "transfer_id": transfer_id,
            "transfer_name": transfer_name,
            "recipient_entity": recipient_entity,
            "destination_country": destination_country,
            "data_types": data_types,
            "record_count": record_count,
            "compliance_checks": compliance_checks,
            "transfer_status": status,
            "status_note": status_note,
            "a05_filing_requirements": {
                "dossier_name": "Hồ sơ đánh giá tác động chuyển dữ liệu cá nhân ra nước ngoài (Điều 25)",
                "submission_deadline": deadline.strftime("%Y-%m-%d"),
                "post_transfer_inspection": "Bộ Công an kiểm tra định kỳ 01 năm/lần hoặc khi có dấu hiệu vi phạm",
            },
            "evaluated_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO cross_border_transfers (
                        transfer_id, transfer_name, recipient_entity, destination_country,
                        data_types, record_count, has_scc, a05_notified, risk_assessment, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        transfer_id,
                        transfer_name,
                        recipient_entity,
                        destination_country,
                        ", ".join(data_types),
                        record_count,
                        1 if has_scc else 0,
                        0,
                        status,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Data Breach Incident 72-Hour Response (Điều 26)
    # -----------------------------------------------------------------------

    def report_data_breach(
        self,
        incident_name: str,
        severity: str,
        affected_count: int,
        breach_type: str,
        hours_elapsed: float = 2.0,
        mitigation_plan: str = "Revoked compromised tokens, enabled network isolation, activated incident team",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Track and manage personal data breach incident within 72-hour statutory deadline (Article 26)."""
        clean_sev = severity.upper().strip()
        if clean_sev not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            clean_sev = "HIGH"

        is_72h_compliant = hours_elapsed <= BREACH_MAX_NOTIFICATION_HOURS
        remaining_hours = max(0.0, BREACH_MAX_NOTIFICATION_HOURS - hours_elapsed)

        incident_id = f"BRC-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)

        result = {
            "ok": True,
            "incident_id": incident_id,
            "incident_name": incident_name,
            "severity": clean_sev,
            "affected_count": affected_count,
            "breach_type": breach_type,
            "statutory_timeline": {
                "hours_elapsed": hours_elapsed,
                "statutory_limit_hours": BREACH_MAX_NOTIFICATION_HOURS,
                "hours_remaining_to_report_a05": round(remaining_hours, 1),
                "is_72h_compliant": is_72h_compliant,
            },
            "a05_reporting": {
                "recipient": "Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05 - Bộ Công an)",
                "notification_form": "Mẫu số 03 - Thông báo vi phạm quy định bảo vệ dữ liệu cá nhân",
                "status": "IMMEDIATE_ACTION_REQUIRED" if remaining_hours > 0 else "DEADLINE_EXCEEDED",
            },
            "mitigation_plan": mitigation_plan,
            "reported_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO breach_incidents (
                        incident_id, incident_name, severity, affected_count,
                        breach_type, hours_elapsed, is_72h_compliant, a05_reported,
                        mitigation_plan, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        incident_name,
                        clean_sev,
                        affected_count,
                        breach_type,
                        hours_elapsed,
                        1 if is_72h_compliant else 0,
                        1 if hours_elapsed > 0 else 0,
                        mitigation_plan,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Data Subject Access Request (DSAR - Điều 9)
    # -----------------------------------------------------------------------

    def handle_dsar_request(
        self,
        request_type: str,
        subject_id: str,
        details: str = "Request under Article 9 PDPD",
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Process Data Subject Access Request (DSAR) under Article 9 of Decree 13/2023/ND-CP."""
        clean_type = request_type.upper().strip()
        if clean_type not in DATA_SUBJECT_RIGHTS:
            clean_type = "RIGHT_TO_ACCESS"

        # Decree 13 Article 9: Controller must respond within 72 hours for critical requests
        deadline_days = 3 if clean_type in ("RIGHT_TO_DELETE", "RIGHT_TO_WITHDRAW_CONSENT", "RIGHT_TO_RESTRICT") else 7

        request_id = f"DSAR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline = now + datetime.timedelta(days=deadline_days)

        result = {
            "ok": True,
            "request_id": request_id,
            "subject_id": subject_id,
            "request_type": clean_type,
            "right_description": DATA_SUBJECT_RIGHTS[clean_type],
            "details": details,
            "status": "PROCESSING",
            "statutory_deadline": {
                "deadline_days": deadline_days,
                "due_date": deadline.strftime("%Y-%m-%d %H:%M:%S UTC"),
            },
            "created_at": now.isoformat(),
        }

        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO dsar_requests (
                        request_id, subject_id, request_type, details,
                        status, deadline_days, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        request_id,
                        subject_id,
                        clean_type,
                        details,
                        "PROCESSING",
                        deadline_days,
                        now.isoformat(),
                    ),
                )
                conn.commit()

        # The right to delete is only honoured when the data is actually gone.
        # Acknowledging the request and deleting nothing would leave the subject
        # holding a receipt for a right they never received.
        if clean_type == "RIGHT_TO_DELETE":
            erasure = self.erase_subject_data(
                subject_id, exclude_request_id=request_id if save else None
            )
            result["erasure"] = erasure
            # "COMPLETED" is a claim that the subject's data is gone. When the
            # purge matched nothing there is nothing to support that claim, so
            # the request stays open for a human to check the identifier rather
            # than closing itself with a receipt for data that still exists.
            result["status"] = (
                "COMPLETED" if erasure["total_erased"] > 0 else "NO_RECORDS_FOUND"
            )
            if erasure["total_erased"] > 0:
                result["completed_at"] = now.isoformat()
            if save:
                with self._get_connection() as conn:
                    conn.execute(
                        "UPDATE dsar_requests SET status = ? WHERE request_id = ?",
                        (result["status"], request_id),
                    )
                    conn.commit()

        return result

    # -----------------------------------------------------------------------
    # Telemetry & Status
    # -----------------------------------------------------------------------

    def list_dpia_assessments(self, limit: int = 50) -> RecordList:
        """List DPIA assessments."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM dpia_assessments ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="assessments")

    def list_cross_border_transfers(self, limit: int = 50) -> RecordList:
        """List cross-border data transfer assessments."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM cross_border_transfers ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="transfers")

    def list_breach_incidents(self, limit: int = 50) -> RecordList:
        """List recorded data breach incidents."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM breach_incidents ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="breaches")

    def list_dsar_requests(self, limit: int = 50) -> RecordList:
        """List data subject requests."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM dsar_requests ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return RecordList([dict(r) for r in rows], key="requests")

    # -----------------------------------------------------------------------
    # Consent recording & withdrawal (Điều 9.2 / 9.4)
    # -----------------------------------------------------------------------

    def record_consent(
        self,
        subject_id: str,
        purpose: str,
        legal_basis: str,
        consent_given: bool = True,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Record a consent decision for *subject_id*.

        A refusal is recorded with the same weight as a grant: the controller has
        to be able to prove both that it asked and what the answer was.
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        consent_id = f"CONSENT-{uuid.uuid4().hex[:8].upper()}"
        result = {
            "ok": True,
            "consent_id": consent_id,
            "subject_id": subject_id,
            "purpose": purpose,
            "legal_basis": legal_basis,
            "consent_given": bool(consent_given),
            "recorded_at": now,
            "withdrawn_at": None,
        }
        if save:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO consent_log (
                        consent_id, subject_id, purpose, legal_basis,
                        consent_given, recorded_at, withdrawn_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        consent_id, subject_id, purpose, legal_basis,
                        1 if consent_given else 0, now, None,
                    ),
                )
                conn.commit()
        return result

    def withdraw_consent(self, subject_or_consent_id: str, purpose: str | None = None) -> dict[str, typing.Any]:
        """Withdraw a previously granted consent, ending its processing basis.

        Withdrawing consent revokes the legal basis for future processing; it
        does not delete data already lawfully recorded. Erasure is a separate
        right and is requested through :meth:`handle_dsar_request`.

        Args:
            subject_or_consent_id: Either a consent id (``CONSENT-...``) or a data
                subject id. A consent id withdraws exactly that decision; a
                subject id withdraws every consent still open for the subject.
            purpose: Restrict the withdrawal to one purpose. When omitted, every
                open consent for the subject is withdrawn.

        Returns:
            Counts of withdrawn records, plus the list of ids affected. Reports
            ``ok`` false when nothing was withdrawn, because a caller who asked
            for a withdrawal and got silence needs to know that.
        """
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        identifier = (subject_or_consent_id or "").strip()
        by_consent_id = identifier.upper().startswith("CONSENT-")

        with self._get_connection() as conn:
            if by_consent_id:
                rows = conn.execute(
                    "SELECT consent_id, subject_id FROM consent_log "
                    "WHERE consent_id = ? AND consent_given = 1 AND withdrawn_at IS NULL",
                    (identifier,),
                ).fetchall()
            elif purpose:
                rows = conn.execute(
                    "SELECT consent_id, subject_id FROM consent_log "
                    "WHERE subject_id = ? AND purpose = ? AND consent_given = 1 "
                    "AND withdrawn_at IS NULL",
                    (identifier, purpose),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT consent_id, subject_id FROM consent_log "
                    "WHERE subject_id = ? AND consent_given = 1 AND withdrawn_at IS NULL",
                    (identifier,),
                ).fetchall()
            consent_ids = [r["consent_id"] for r in rows]
            subjects = sorted({str(r["subject_id"]) for r in rows})
            for consent_id in consent_ids:
                conn.execute(
                    "UPDATE consent_log SET withdrawn_at = ? WHERE consent_id = ?",
                    (now, consent_id),
                )
            conn.commit()

        return {
            "ok": bool(consent_ids),
            "subject_id": subjects[0] if len(subjects) == 1 else None,
            "subject_ids": subjects,
            "purpose": purpose,
            "withdrawn_count": len(consent_ids),
            "consent_ids": consent_ids,
            "withdrawn_at": now if consent_ids else None,
            "detail": (
                "Đã ghi nhận rút sự đồng ý" if consent_ids
                else "Không tìm thấy sự đồng ý đang hiệu lực để rút"
            ),
        }

    def list_consents(self, subject_id: str | None = None, limit: int = 50) -> RecordList:
        """List consent records, newest first, optionally filtered by subject."""
        with self._get_connection() as conn:
            if subject_id:
                rows = conn.execute(
                    "SELECT * FROM consent_log WHERE subject_id = ? "
                    "ORDER BY recorded_at DESC LIMIT ?",
                    (subject_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM consent_log ORDER BY recorded_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        consents = [dict(r) for r in rows]
        for consent in consents:
            # SQLite has no boolean column; callers must not have to remember that
            # when deciding whether a legal basis is still standing.
            consent["consent_given"] = bool(consent.get("consent_given"))
        return RecordList(consents, key="consents")

    # -----------------------------------------------------------------------
    # Subject erasure (Điều 9.5)
    # -----------------------------------------------------------------------

    def erase_subject_data(
        self,
        subject_id: str,
        exclude_request_id: str | None = None,
        zalo_db_path: typing.Optional[typing.Union[str, pathlib.Path]] = None,
        save: bool = True,
    ) -> dict[str, typing.Any]:
        """Delete every row identifying *subject_id* across the live PII stores.

        The right to delete is only honoured if the deletion actually happens, so
        this walks the concrete stores that hold subject data and reports what it
        removed from each. A store that does not exist yet contributes a zero
        count rather than an error — a subject has no row in a database that was
        never created.

        Args:
            subject_id: Data subject identifier (user id, email or DSAR subject).
            exclude_request_id: When set, a prior DSAR request row carrying this
                identifier is kept so the audit trail for the current request
                survives the purge.
            zalo_db_path: Location of the Zalo store. Defaults to the sibling
                ``zalo.db`` next to the privacy database, which is where a normal
                install keeps them.
            save: When false, report the counts without deleting anything.

        Returns:
            Per-store deleted counts plus a total and the stores touched.
        """
        if zalo_db_path is None:
            zalo_db_path = self.db_path.parent / "zalo.db"
        zalo_path = pathlib.Path(zalo_db_path)
        subject_id = (subject_id or "").strip()

        # A subject's Zalo rows are keyed by their Zalo UID, while a DSAR arrives
        # under a CCCD, an email or a phone number. Matching only `user_id` would
        # report a clean zero for exactly the subjects whose rows do exist, so
        # resolve every Zalo UID that identifies this subject first.
        zalo_user_ids = self._resolve_zalo_user_ids(zalo_path, subject_id)
        # The identifier the subject arrived under is also a key the store may use
        # directly: a message sent to a raw UID leaves no follower row to resolve
        # from. Leaving it out would erase nothing and still report success.
        if subject_id and subject_id not in zalo_user_ids:
            zalo_user_ids.append(subject_id)
        # With no subject and no resolved UID there is nothing to match; the empty
        # predicate keeps the statement valid and deletes no rows.
        user_match = (
            "(" + " OR ".join(["user_id = ?"] * len(zalo_user_ids)) + ")"
            if zalo_user_ids else "1=0"
        )

        counts = {
            "zalo_followers": self._delete_where(
                zalo_path, "followers", user_match, tuple(zalo_user_ids), save
            ),
            "zalo_messages": self._delete_where(
                zalo_path, "messages", user_match, tuple(zalo_user_ids), save
            ),
            "dsar_requests": self._delete_prior_requests(
                subject_id, exclude_request_id, save
            ),
            "consent_log": self._delete_where(
                self.db_path, "consent_log", "subject_id = ?", (subject_id,), save
            ),
        }
        return {
            "ok": True,
            "subject_id": subject_id,
            "erased_rows": counts,
            "total_erased": sum(counts.values()),
            "stores_touched": [k for k, v in counts.items() if v],
            # Stores this engine cannot reach directly are named here rather than
            # left off, so an operator never reads "COMPLETED" as a promise that
            # every copy of the subject's data is gone.
            "pending_external_stores": ["cloudflare_d1:mekong-d1.leads"],
        }

    def _resolve_zalo_user_ids(self, zalo_path: pathlib.Path, subject_id: str) -> list[str]:
        """Return every Zalo UID that identifies *subject_id*.

        The Zalo store keys rows by its own UID and keeps name and phone on the
        follower row, so a subject who arrives as a phone number or a CCCD has to
        be resolved to the UID before their messages can be found.
        """
        if not zalo_path.is_file() or not subject_id:
            return []
        with contextlib.closing(self._get_foreign_connection(zalo_path)) as conn:
            if "followers" not in self._existing_tables(conn):
                return []
            rows = conn.execute(
                "SELECT user_id FROM followers WHERE user_id = ? OR phone = ? OR name = ?",
                (subject_id, subject_id, subject_id),
            ).fetchall()
            return [str(r["user_id"]) for r in rows]

    def _delete_where(
        self,
        db_path: pathlib.Path,
        table: str,
        where: str,
        params: tuple,
        save: bool,
    ) -> int:
        """Delete matching rows from *table* if the database and table exist."""
        if not db_path.is_file():
            return 0
        # Table names come from the literal call sites in this module, never from
        # caller input, so composing the statement here stays injection-free.
        table = table.replace('"', '')
        with contextlib.closing(self._get_foreign_connection(db_path)) as conn:
            if table not in self._existing_tables(conn):
                return 0
            if not save:
                cursor = conn.execute(
                    f'SELECT COUNT(*) AS c FROM "{table}" WHERE {where or "1=0"}', params
                )
                return int(cursor.fetchone()["c"])
            if not where:
                return 0
            cursor = conn.execute(f'DELETE FROM "{table}" WHERE {where}', params)
            conn.commit()
            return int(cursor.rowcount or 0)

    def _delete_prior_requests(self, subject_id: str, exclude_request_id: str | None, save: bool) -> int:
        """Delete earlier DSAR rows for the subject, keeping the active request."""
        with self._get_connection() as conn:
            if exclude_request_id:
                rows = conn.execute(
                    "SELECT request_id FROM dsar_requests "
                    "WHERE subject_id = ? AND request_id != ?",
                    (subject_id, exclude_request_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT request_id FROM dsar_requests WHERE subject_id = ?",
                    (subject_id,),
                ).fetchall()
            request_ids = [str(r["request_id"]) for r in rows]
            # A dry run must not delete; it reports what a real run would remove.
            if save:
                for request_id in request_ids:
                    conn.execute(
                        "DELETE FROM dsar_requests WHERE request_id = ?", (request_id,)
                    )
                conn.commit()
        return len(request_ids)

    @staticmethod
    def _existing_tables(conn: sqlite3.Connection) -> set[str]:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        return {r["name"] for r in rows}

    def _get_foreign_connection(self, db_path: pathlib.Path) -> sqlite3.Connection:
        """Open a connection to a sibling store without creating it.

        A missing database is not an error for a delete request — the caller has
        already checked the file exists — so no ``mode=ro`` guard is needed and
        the deletion can commit.
        """
        conn = sqlite3.connect(str(db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def get_status(self) -> dict[str, typing.Any]:
        """Retrieve aggregated PDPD data privacy compliance metrics."""
        with self._get_connection() as conn:
            a_row = conn.execute("SELECT COUNT(*) as c, AVG(compliance_score) as avg_s FROM compliance_audits").fetchone()
            d_row = conn.execute("SELECT COUNT(*) as c, SUM(CASE WHEN is_sensitive = 1 THEN 1 ELSE 0 END) as sens FROM dpia_assessments").fetchone()
            t_row = conn.execute("SELECT COUNT(*) as c, SUM(record_count) as sum_r FROM cross_border_transfers").fetchone()
            b_row = conn.execute("SELECT COUNT(*) as c, SUM(affected_count) as sum_aff, SUM(CASE WHEN is_72h_compliant = 1 THEN 1 ELSE 0 END) as comp_72h FROM breach_incidents").fetchone()
            ds_row = conn.execute("SELECT COUNT(*) as c FROM dsar_requests").fetchone()

        return {
            "ok": True,
            "status": "operational",
            "engine": "PrivacyEngine",
            "governing_law": "Nghị định 13/2023/NĐ-CP (Bảo vệ dữ liệu cá nhân - PDPD)",
            "supervisory_authority": "Cục An ninh mạng và phòng, chống tội phạm sử dụng công nghệ cao (A05 - Bộ Công an)",
            "metrics": {
                "total_compliance_audits": a_row["c"] if a_row else 0,
                "avg_compliance_score": round(a_row["avg_s"], 1) if (a_row and a_row["avg_s"]) else 100.0,
                "total_dpia_assessments": d_row["c"] if d_row else 0,
                "sensitive_dpia_count": d_row["sens"] if d_row else 0,
                "total_cross_border_transfers": t_row["c"] if t_row else 0,
                "total_cross_border_records": t_row["sum_r"] if (t_row and t_row["sum_r"]) else 0,
                "total_breach_incidents": b_row["c"] if b_row else 0,
                "total_affected_individuals": b_row["sum_aff"] if (b_row and b_row["sum_aff"]) else 0,
                "compliant_72h_breaches": b_row["comp_72h"] if b_row else 0,
                "total_dsar_requests": ds_row["c"] if ds_row else 0,
            },
            "database": str(self.db_path),
        }
