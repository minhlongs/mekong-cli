# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Personal Data Protection Decree (PDPD Decree 13/2023/ND-CP) Engine (Phase 59)."""

from __future__ import annotations

import ast
import json
import pathlib
import sqlite3

import pytest
from typer.testing import CliRunner

from src.core.privacy_engine import (
    BASIC_DATA_CATEGORIES,
    SENSITIVE_DATA_CATEGORIES,
    DATA_SUBJECT_RIGHTS,
    BREACH_MAX_NOTIFICATION_HOURS,
    DPIA_FILING_DEADLINE_DAYS,
    PrivacyEngine,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestPrivacyCoreBoundary:
    """Ensure PrivacyEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/privacy_engine.py")
        assert source_path.exists(), "privacy_engine.py must exist"

        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        disallowed = {"requests", "httpx", "urllib3", "aiohttp", "pydantic", "fastapi", "typer"}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    pkg = alias.name.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed import: {pkg}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    pkg = node.module.split(".")[0]
                    assert pkg not in disallowed, f"Disallowed from-import: {pkg}"


# ---------------------------------------------------------------------------
# Engine Unit Tests
# ---------------------------------------------------------------------------


class TestPrivacyEngine:
    """Test PrivacyEngine audit, DPIA Form 04, cross-border TIA, 72h breach response, and DSAR."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> PrivacyEngine:
        db_file = tmp_path / "test_privacy.db"
        return PrivacyEngine(db_path=db_file)

    def test_constants_and_categories(self) -> None:
        assert "FULL_NAME" in BASIC_DATA_CATEGORIES
        assert "PHONE_NUMBER" in BASIC_DATA_CATEGORIES
        assert "BIOMETRICS" in SENSITIVE_DATA_CATEGORIES
        assert "BANKING_FINANCIAL" in SENSITIVE_DATA_CATEGORIES
        assert len(DATA_SUBJECT_RIGHTS) == 11
        assert "RIGHT_TO_DELETE" in DATA_SUBJECT_RIGHTS
        assert BREACH_MAX_NOTIFICATION_HOURS == 72
        assert DPIA_FILING_DEADLINE_DAYS == 60

    def test_audit_enterprise_compliance_compliant(self, engine: PrivacyEngine) -> None:
        # Enterprise with sensitive data, appointed DPO, and completed DPIA dossier
        res = engine.audit_enterprise_compliance(
            enterprise_name="VinBrain Healthcare AI",
            controller_type="CONTROLLER_AND_PROCESSOR",
            has_sensitive_data=True,
            has_dpo=True,
            has_cross_border=False,
            has_dpia_dossier=True,
        )
        assert res["ok"] is True
        assert res["audit_id"].startswith("AUD-")
        assert res["compliance_score"] == 100.0
        assert res["compliance_status"] == "COMPLIANT"
        assert len(res["compliance_gaps"]) == 0

    def test_audit_enterprise_compliance_missing_dpo(self, engine: PrivacyEngine) -> None:
        # Article 28 violation: processing sensitive data without a DPO
        res = engine.audit_enterprise_compliance(
            enterprise_name="Fintech Micro Lending JSC",
            controller_type="CONTROLLER",
            has_sensitive_data=True,
            has_dpo=False,  # Violation!
            has_dpia_dossier=True,
        )
        assert res["ok"] is True
        assert res["compliance_score"] < 100.0
        assert any("DPO" in gap for gap in res["compliance_gaps"])
        assert any("Điều 28" in rec for rec in res["statutory_recommendations"])

    def test_audit_enterprise_compliance_missing_dpia(self, engine: PrivacyEngine) -> None:
        # Article 24 violation: missing DPIA assessment dossier
        res = engine.audit_enterprise_compliance(
            enterprise_name="E-Commerce Retail Co",
            controller_type="CONTROLLER",
            has_sensitive_data=False,
            has_dpo=False,
            has_dpia_dossier=False,  # Violation!
        )
        assert res["ok"] is True
        assert res["compliance_score"] <= 70.0
        assert any("DPIA" in gap for gap in res["compliance_gaps"])

    def test_create_dpia_assessment_sensitive(self, engine: PrivacyEngine) -> None:
        # Processing sensitive biometric & financial data -> High Risk, DPO mandatory
        res = engine.create_dpia_assessment(
            activity_name="Xác thực eKYC & Mở tài khoản số",
            processing_purpose="Định danh điện tử khách hàng ngân hàng số",
            data_categories=["FULL_NAME", "ID_CARD_NUMBER", "BIOMETRICS", "BANKING_FINANCIAL"],
            legal_basis="CONSENT",
            security_measures="AES-256 HSM, Zero Trust RBAC, TLS 1.3",
        )
        assert res["ok"] is True
        assert res["dpia_id"].startswith("DPIA-")
        assert res["is_sensitive_data_processed"] is True
        assert res["risk_assessment"]["risk_level"] == "HIGH_RISK"
        assert res["risk_assessment"]["dpo_mandatory"] is True
        assert res["form_04_a05"]["status"] == "DOSSIER_COMPILED"
        assert "A05" in res["form_04_a05"]["filing_recipient"]

    def test_create_dpia_assessment_basic(self, engine: PrivacyEngine) -> None:
        # Basic customer contact processing -> Low Risk
        res = engine.create_dpia_assessment(
            activity_name="Gửi bản tin Marketing qua Email",
            processing_purpose="Chăm sóc khách hàng định kỳ",
            data_categories=["FULL_NAME", "EMAIL"],
            legal_basis="CONSENT",
        )
        assert res["ok"] is True
        assert res["is_sensitive_data_processed"] is False
        assert res["risk_assessment"]["risk_level"] == "LOW_RISK"
        assert res["risk_assessment"]["dpo_mandatory"] is False

    def test_evaluate_cross_border_transfer_with_scc(self, engine: PrivacyEngine) -> None:
        # Article 25: Overseas transfer with signed SCC agreement
        res = engine.evaluate_cross_border_transfer(
            transfer_name="Lưu trữ Dữ liệu AWS Singapore",
            recipient_entity="Amazon Web Services Inc",
            destination_country="Singapore",
            data_types=["FULL_NAME", "PHONE_NUMBER", "EMAIL"],
            record_count=25000,
            has_scc=True,
        )
        assert res["ok"] is True
        assert res["transfer_id"].startswith("XFER-")
        assert res["transfer_status"] == "PERMITTED_WITH_FILING"
        assert res["compliance_checks"]["has_data_transfer_agreement"] is True

    def test_evaluate_cross_border_transfer_missing_scc(self, engine: PrivacyEngine) -> None:
        # Article 25 violation: transfer without SCC / data protection agreement
        res = engine.evaluate_cross_border_transfer(
            transfer_name="Chuyển dữ liệu cho đối tác nước ngoài",
            recipient_entity="Unknown Third Party Corp",
            destination_country="Cayman Islands",
            data_types=["FULL_NAME", "BANKING_FINANCIAL"],
            record_count=5000,
            has_scc=False,
        )
        assert res["ok"] is True
        assert res["transfer_status"] == "RESTRICTED_MISSING_SCC"
        assert any("Chưa có văn bản cam kết" in res["status_note"] for _ in [1])

    def test_report_data_breach_within_72h(self, engine: PrivacyEngine) -> None:
        # Article 26: Breach detected 4 hours ago -> within 72h window
        res = engine.report_data_breach(
            incident_name="Lỗ hổng API rò rỉ số điện thoại",
            severity="HIGH",
            affected_count=12000,
            breach_type="UNAUTHORIZED_API_ACCESS",
            hours_elapsed=4.0,
            mitigation_plan="Revoked leaked JWT secrets, blocked offending IPs, patched rate limiter",
        )
        assert res["ok"] is True
        assert res["incident_id"].startswith("BRC-")
        assert res["statutory_timeline"]["is_72h_compliant"] is True
        assert res["statutory_timeline"]["hours_remaining_to_report_a05"] == 68.0
        assert res["a05_reporting"]["status"] == "IMMEDIATE_ACTION_REQUIRED"

    def test_report_data_breach_exceeding_72h(self, engine: PrivacyEngine) -> None:
        # Article 26: Breach detected 80 hours ago -> statutory deadline exceeded
        res = engine.report_data_breach(
            incident_name="Ransomware mã hóa cơ sở dữ liệu cũ",
            severity="CRITICAL",
            affected_count=50000,
            breach_type="RANSOMWARE",
            hours_elapsed=80.0,
        )
        assert res["ok"] is True
        assert res["statutory_timeline"]["is_72h_compliant"] is False
        assert res["statutory_timeline"]["hours_remaining_to_report_a05"] == 0.0
        assert res["a05_reporting"]["status"] == "DEADLINE_EXCEEDED"

    def test_handle_dsar_request_deletion_and_access(self, engine: PrivacyEngine) -> None:
        # Article 9: Right to delete (3 days deadline)
        res_del = engine.handle_dsar_request(
            request_type="RIGHT_TO_DELETE",
            subject_id="CCCD-079090012345",
            details="Yêu cầu xóa toàn bộ lịch sử giao dịch và tài khoản",
        )
        assert res_del["ok"] is True
        assert res_del["request_id"].startswith("DSAR-")
        assert res_del["statutory_deadline"]["deadline_days"] == 3

        # Article 9: Right to access (7 days deadline)
        res_acc = engine.handle_dsar_request(
            request_type="RIGHT_TO_ACCESS",
            subject_id="USER-998877",
            details="Yêu cầu trích xuất dữ liệu cá nhân đang lưu trữ",
        )
        assert res_acc["ok"] is True
        assert res_acc["statutory_deadline"]["deadline_days"] == 7

    # -- Article 9.2 / 9.4: consent grant and withdrawal --------------------

    def test_consent_is_recorded_and_listed(self, engine: PrivacyEngine) -> None:
        subject = "CCCD-079090012345"
        engine.audit_enterprise_compliance("Test Corp", "CONTROLLER")

        granted = engine.record_consent(
            subject_id=subject,
            purpose="Gửi thông báo khuyến mãi qua Zalo OA",
            legal_basis="CONSENT",
            consent_given=True,
        )
        assert granted["ok"] is True
        assert granted["consent_id"].startswith("CONSENT-")

        listing = engine.list_consents(subject)
        assert listing["ok"] is True
        assert len(listing["consents"]) == 1
        assert listing["consents"][0]["purpose"] == "Gửi thông báo khuyến mãi qua Zalo OA"
        assert listing["consents"][0]["consent_given"] is True
        assert listing["consents"][0]["withdrawn_at"] is None

    def test_consent_can_be_withdrawn(self, engine: PrivacyEngine) -> None:
        subject = "USER-CONSENT-WD"
        granted = engine.record_consent(subject, "Mục đích marketing", "CONSENT", True)

        withdrawn = engine.withdraw_consent(granted["consent_id"])
        assert withdrawn["ok"] is True
        assert withdrawn["withdrawn_at"] is not None

        listing = engine.list_consents(subject)
        assert len(listing["consents"]) == 1
        # The grant remains on record; withdrawal is recorded by its timestamp,
        # not by erasing the history that consent was once given.
        assert listing["consents"][0]["consent_given"] is True
        assert listing["consents"][0]["withdrawn_at"] is not None

    def test_consent_refusal_can_be_recorded(self, engine: PrivacyEngine) -> None:
        subject = "USER-CONSENT-REFUSED"
        res = engine.record_consent(subject, "Chia sẻ dữ liệu cho bên thứ ba", "CONSENT", False)

        assert res["ok"] is True
        listing = engine.list_consents(subject)
        assert listing["consents"][0]["consent_given"] is False

    def test_withdraw_unknown_consent_fails(self, engine: PrivacyEngine) -> None:
        res = engine.withdraw_consent("CONSENT-NOPE")
        assert res["ok"] is False

    # -- Article 9.5: the right to delete is honoured by real erasure --------

    @staticmethod
    def _seed_zalo_db(zalo_path: pathlib.Path, subject_id: str,
                      other_user_id: str = "ZALO-OTHER-001") -> None:
        """Seed a sibling Zalo OA database the way ZaloEngine lays it out.

        Erasure must go through raw SQL rather than ZaloEngine, because that
        engine auto-reseeds canonical followers whenever the table is empty.
        """
        conn = sqlite3.connect(str(zalo_path))
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS followers (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL DEFAULT '',
                    segment TEXT NOT NULL DEFAULT 'standard',
                    followed_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    template TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    sent_at TEXT NOT NULL
                );
                """
            )
            conn.executemany(
                "INSERT INTO followers (user_id, name, phone, segment, followed_at)"
                " VALUES (?, ?, ?, ?, ?)",
                [
                    (subject_id, "Chủ dữ liệu", "0900000001", "vip", "2026-01-01T00:00:00+00:00"),
                    (other_user_id, "Người khác", "0900000002", "standard", "2026-01-01T00:00:00+00:00"),
                ],
            )
            conn.executemany(
                "INSERT INTO messages (message_id, user_id, text, template, status, sent_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    ("MSG-1", subject_id, "Xin chào", "greeting", "sent", "2026-01-01T00:00:00+00:00"),
                    ("MSG-2", subject_id, "Ưu đãi mới", "promo", "sent", "2026-01-01T00:00:00+00:00"),
                    ("MSG-3", other_user_id, "Không liên quan", "greeting", "sent", "2026-01-01T00:00:00+00:00"),
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def test_erase_subject_data_purges_other_tenants_data(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """Erasure removes only the subject's rows and leaves other users intact."""
        subject = "CCCD-079090012345"
        other = "ZALO-OTHER-001"
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, subject, other)

        # An older, unrelated request from the same subject is purged; the
        # request being served right now is kept so the receipt stays readable.
        engine.handle_dsar_request("RIGHT_TO_ACCESS", subject, save=True)
        current = "DSAR-KEEP-ME"
        with engine._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO dsar_requests "
                "(request_id, subject_id, request_type, details, status, deadline_days, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (current, subject, "RIGHT_TO_DELETE", "served now",
                 "PROCESSING", 3, "2026-01-01T00:00:00+00:00"),
            )
            conn.commit()

        result = engine.erase_subject_data(
            subject, exclude_request_id=current, zalo_db_path=zalo_path,
        )

        assert result["ok"] is True
        assert result["total_erased"] > 0
        assert result["erased_rows"]["zalo_followers"] == 1
        assert result["erased_rows"]["zalo_messages"] == 2
        assert result["erased_rows"]["consent_log"] == 0
        assert "zalo_followers" in result["stores_touched"]

        survivors = sqlite3.connect(str(zalo_path)).execute(
            "SELECT COUNT(*) FROM followers WHERE user_id = ?", (subject,),
        ).fetchone()[0]
        assert survivors == 0
        others_kept = sqlite3.connect(str(zalo_path)).execute(
            "SELECT COUNT(*) FROM followers WHERE user_id = ?", (other,),
        ).fetchone()[0]
        assert others_kept == 1
        messages_kept = sqlite3.connect(str(zalo_path)).execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ?", (other,),
        ).fetchone()[0]
        assert messages_kept == 1

    def test_erase_subject_data_purges_consent_history(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        subject = "CCCD-CONSENT-ERASE"
        engine.record_consent(subject, "Mục đích A", "CONSENT", True)
        engine.record_consent(subject, "Mục đích B", "LEGITIMATE_INTEREST", True)

        result = engine.erase_subject_data(subject, zalo_db_path=tmp_path / "absent.db")

        assert result["erased_rows"]["consent_log"] == 2
        assert engine.list_consents(subject)["consents"] == []

    def test_erase_subject_data_reports_absent_zalo_store(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """A missing Zalo store is reported as zero, never as a crash."""
        result = engine.erase_subject_data("NOBODY", zalo_db_path=tmp_path / "missing.db")

        assert result["ok"] is True
        assert result["erased_rows"]["zalo_followers"] == 0
        assert result["erased_rows"]["zalo_messages"] == 0

    def test_erase_subject_data_matches_zalo_rows_by_phone(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """A subject identified by phone still has their Zalo rows erased.

        Zalo keys its rows by its own UID, while a DSAR arrives under whatever
        identifier the subject used. Matching only `user_id` would report a clean
        zero for exactly the subjects whose messages do exist.
        """
        subject_phone = "0901234567"
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, "zalo-user-001")
        with sqlite3.connect(str(zalo_path)) as conn:
            conn.execute(
                "UPDATE followers SET phone = ?, name = ? WHERE user_id = ?",
                (subject_phone, "Nguyễn Văn A", "zalo-user-001"),
            )
            conn.execute(
                "INSERT INTO messages (message_id, user_id, text, template, status, sent_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                ("MSG-PHONE-1", "zalo-user-001", "Tin nhắn riêng", "direct", "sent", "2026-01-01T00:00:00+00:00"),
            )
            conn.commit()

        result = engine.erase_subject_data(
            subject_phone, exclude_request_id="DSAR-KEEP", zalo_db_path=zalo_path,
        )

        assert result["erased_rows"]["zalo_followers"] == 1
        assert result["erased_rows"]["zalo_messages"] == 3
        with sqlite3.connect(str(zalo_path)) as conn:
            survivors = [r[0] for r in conn.execute("SELECT user_id FROM followers")]
            assert survivors == ["ZALO-OTHER-001"]
            assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1

    def test_erase_subject_data_dry_run_deletes_nothing(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """A preview reports counts without touching any store."""
        subject = "CCCD-DRYRUN"
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, subject)
        engine.handle_dsar_request("RIGHT_TO_ACCESS", subject, save=True)
        engine.record_consent(subject, "Mục đích A", "CONSENT", True)

        preview = engine.erase_subject_data(
            subject, zalo_db_path=zalo_path, save=False,
        )

        assert preview["erased_rows"]["zalo_followers"] == 1
        assert preview["erased_rows"]["zalo_messages"] == 2
        assert preview["erased_rows"]["dsar_requests"] == 1
        assert preview["erased_rows"]["consent_log"] == 1

        # Nothing actually went away, in any store.
        with sqlite3.connect(str(zalo_path)) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM followers WHERE user_id = ?", (subject,)
            ).fetchone()[0] == 1
        assert len(engine.list_dsar_requests()["requests"]) == 1
        assert len(engine.list_consents(subject)["consents"]) == 1

    def test_erase_subject_data_report_names_unreachable_stores(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """Receipts name the stores this engine cannot reach, so COMPLETED is
        never read as a promise that every copy of the data is gone."""
        result = engine.erase_subject_data("ANYONE", zalo_db_path=tmp_path / "absent.db")
        assert "cloudflare_d1:mekong-d1.leads" in result["pending_external_stores"]

    def test_empty_subject_id_erases_nothing(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """A blank identifier must not become a table-wide delete."""
        subject = "CCCD-BLANK-CANARY"
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, subject)

        result = engine.erase_subject_data("   ", zalo_db_path=zalo_path)

        assert result["total_erased"] == 0
        with sqlite3.connect(str(zalo_path)) as conn:
            assert conn.execute("SELECT COUNT(*) FROM followers").fetchone()[0] == 2
            assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 3

    def test_erase_subject_data_erases_direct_zalo_messages_without_follower_row(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """Direct messages sent to a raw Zalo UID must still be erased even when
        no corresponding row exists in followers."""
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, "zalo-user-other")
        with sqlite3.connect(str(zalo_path)) as conn:
            conn.execute(
                "INSERT INTO messages (message_id, user_id, text, template, status, sent_at)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                ("MSG-DIRECT-1", "zalo-uid-direct-123", "Tin nhắn trực tiếp", "direct", "sent", "2026-01-01T00:00:00+00:00"),
            )
            conn.commit()

        result = engine.erase_subject_data(
            "zalo-uid-direct-123", zalo_db_path=zalo_path,
        )

        assert result["erased_rows"]["zalo_followers"] == 0
        assert result["erased_rows"]["zalo_messages"] == 1
        assert result["total_erased"] == 1
        with sqlite3.connect(str(zalo_path)) as conn:
            remaining = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id = ?",
                ("zalo-uid-direct-123",),
            ).fetchone()[0]
            assert remaining == 0

    def test_zalo_engine_and_privacy_engine_share_mekong_root_path(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Both engines resolve .mekong/zalo.db under MEKONG_ROOT."""
        from src.core.zalo_engine import ZaloEngine

        monkeypatch.setenv("MEKONG_ROOT", str(tmp_path))
        zalo = ZaloEngine()
        privacy = PrivacyEngine()
        assert zalo.db_path == privacy.db_path.parent / "zalo.db"

    def test_dsar_right_to_delete_completes_after_real_purge(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """A deletion request is only marked COMPLETED once data is really gone."""
        subject = "CCCD-DSAR-DELETE"
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, subject)
        engine.record_consent(subject, "Mục đích marketing", "CONSENT", True)

        res = engine.handle_dsar_request(
            request_type="RIGHT_TO_DELETE",
            subject_id=subject,
            details="Xóa toàn bộ dữ liệu",
            save=True,
        )

        assert res["status"] == "COMPLETED"
        assert res["erasure"]["erased_rows"]["zalo_followers"] == 1
        assert res["erasure"]["erased_rows"]["zalo_messages"] == 2
        assert res["erasure"]["erased_rows"]["consent_log"] == 1
        assert res["completed_at"] is not None

        stored = engine.list_dsar_requests()
        served = [r for r in stored["requests"] if r["request_id"] == res["request_id"]]
        assert len(served) == 1
        assert served[0]["status"] == "COMPLETED"

    def test_dsar_right_to_access_does_not_erase(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        subject = "CCCD-DSAR-ACCESS"
        zalo_path = tmp_path / "zalo.db"
        self._seed_zalo_db(zalo_path, subject)

        res = engine.handle_dsar_request(
            request_type="RIGHT_TO_ACCESS", subject_id=subject, save=True,
        )

        assert res["status"] == "PROCESSING"
        assert "erasure" not in res
        assert engine.list_consents(subject)["consents"] == []

    def test_dsar_right_to_delete_with_no_records_stays_open(
        self, engine: PrivacyEngine, tmp_path: pathlib.Path,
    ) -> None:
        """A purge that matched nothing must not close as COMPLETED.

        "COMPLETED" claims the subject's data is gone. When nothing was erased
        there is nothing to support that claim, so the request stays open for a
        human to check the identifier rather than closing itself.
        """
        res = engine.handle_dsar_request(
            request_type="RIGHT_TO_DELETE",
            subject_id="cccd-not-in-any-store",
            details="Xóa toàn bộ dữ liệu",
            save=True,
        )

        assert res["erasure"]["total_erased"] == 0
        assert res["status"] == "NO_RECORDS_FOUND"
        assert "completed_at" not in res

        stored = [r for r in engine.list_dsar_requests()["requests"]
                  if r["request_id"] == res["request_id"]]
        assert stored[0]["status"] == "NO_RECORDS_FOUND"

    def test_list_records_and_status(self, engine: PrivacyEngine) -> None:
        engine.audit_enterprise_compliance("Test Corp", "CONTROLLER")
        engine.create_dpia_assessment("Act 1", "Purpose 1", ["FULL_NAME", "BIOMETRICS"])
        engine.evaluate_cross_border_transfer("Xfer 1", "Recip 1", "Singapore", ["FULL_NAME"])
        engine.report_data_breach("Breach 1", "HIGH", 500, "EXFILTRATION", 2.0)
        engine.handle_dsar_request("RIGHT_TO_ACCESS", "SUBJ-01")

        dpias = engine.list_dpia_assessments()
        assert dpias["ok"] is True
        assert len(dpias["assessments"]) >= 1

        xfers = engine.list_cross_border_transfers()
        assert xfers["ok"] is True
        assert len(xfers["transfers"]) >= 1

        breaches = engine.list_breach_incidents()
        assert breaches["ok"] is True
        assert len(breaches["breaches"]) >= 1

        dsars = engine.list_dsar_requests()
        assert dsars["ok"] is True
        assert len(dsars["requests"]) >= 1

        status = engine.get_status()
        assert status["ok"] is True
        assert status["metrics"]["total_compliance_audits"] >= 1
        assert status["metrics"]["total_dpia_assessments"] >= 1
        assert status["metrics"]["total_cross_border_transfers"] >= 1
        assert status["metrics"]["total_breach_incidents"] >= 1


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestPrivacyCli:
    """Test mekong privacy command group execution."""

    @pytest.fixture(autouse=True)
    def setup_app(self) -> None:
        self.app = build_app()

    def test_cli_main_json(self) -> None:
        result = runner.invoke(self.app, ["privacy", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert "governing_law" in data
        assert "Nghị định 13/2023" in data["governing_law"]

    def test_cli_audit_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "audit",
                "Tập đoàn Công nghệ Alpha",
                "--role",
                "CONTROLLER_AND_PROCESSOR",
                "--sensitive",
                "--dpo",
                "--dpia",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["enterprise_name"] == "Tập đoàn Công nghệ Alpha"
        assert data["compliance_status"] == "COMPLIANT"

    def test_cli_audit_console(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "audit",
                "Công ty Khởi nghiệp Beta",
                "--role",
                "CONTROLLER",
            ],
        )
        assert result.exit_code == 0
        assert "Công ty Khởi nghiệp Beta" in result.output

    def test_cli_dpia_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "dpia",
                "Thu thập dữ liệu khuôn mặt cửa ra vào",
                "Kiểm soát an ninh văn phòng",
                "FULL_NAME,BIOMETRICS,IMAGE",
                "--basis",
                "CONSENT",
                "--security",
                "AES-256",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["is_sensitive_data_processed"] is True
        assert data["risk_assessment"]["risk_level"] == "HIGH_RISK"

    def test_cli_transfer_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "transfer",
                "Đồng bộ máy chủ Tokyo",
                "Line Corp",
                "Japan",
                "FULL_NAME,EMAIL",
                "--count",
                "5000",
                "--scc",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["destination_country"] == "Japan"
        assert data["transfer_status"] == "PERMITTED_WITH_FILING"

    def test_cli_breach_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "breach",
                "Rò rỉ cơ sở dữ liệu thử nghiệm",
                "HIGH",
                "3500",
                "UNPROTECTED_S3_BUCKET",
                "--hours",
                "1.5",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["statutory_timeline"]["is_72h_compliant"] is True

    def test_cli_dsar_json(self) -> None:
        result = runner.invoke(
            self.app,
            [
                "privacy",
                "dsar",
                "RIGHT_TO_DELETE",
                "CCCD-012345678999",
                "--details",
                "Yêu cầu xóa tài khoản người dùng",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["subject_id"] == "CCCD-012345678999"
        assert data["statutory_deadline"]["deadline_days"] == 3

    def test_cli_list_json(self) -> None:
        res = runner.invoke(self.app, ["privacy", "list", "--type", "dpia", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "assessments" in data

    def test_cli_status_json(self) -> None:
        res = runner.invoke(self.app, ["privacy", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["ok"] is True
        assert "metrics" in data

    # -- Consent & erasure subcommands (Điều 9.2 / 9.4 / 9.5) ----------------

    @pytest.fixture
    def cli_db(self, monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> pathlib.Path:
        """Point the default-constructed PrivacyEngine at a throwaway root.

        Without this the CLI writes into the repository's own `.mekong/`.
        """
        root = tmp_path / "mekong-root"
        root.mkdir()
        monkeypatch.setenv("MEKONG_ROOT", str(root))
        return root

    def test_cli_consent_help_renders(self) -> None:
        res = runner.invoke(self.app, ["privacy", "consent", "--help"])
        assert res.exit_code == 0
        assert "grant" in res.output
        assert "withdraw" in res.output

    def test_cli_erase_help_renders(self) -> None:
        res = runner.invoke(self.app, ["privacy", "erase", "--help"])
        assert res.exit_code == 0
        assert "9.5" in res.output

    def test_cli_consent_grant_list_withdraw(self, cli_db: pathlib.Path) -> None:
        subject = "CCCD-CLI-001"

        granted = runner.invoke(
            self.app, ["privacy", "consent", "grant", subject,
                       "--purpose", "Gửi thông báo khuyến mãi Zalo OA", "--json"],
        )
        assert granted.exit_code == 0
        consent_id = json.loads(granted.output)["consent_id"]
        assert consent_id.startswith("CONSENT-")

        listed = runner.invoke(self.app, ["privacy", "consent", "list", subject, "--json"])
        assert listed.exit_code == 0
        rows = json.loads(listed.output)["consents"]
        assert len(rows) == 1
        assert rows[0]["consent_given"] is True

        withdrawn = runner.invoke(self.app, ["privacy", "consent", "withdraw", consent_id, "--json"])
        assert withdrawn.exit_code == 0
        assert json.loads(withdrawn.output)["withdrawn_count"] == 1

        relisted = runner.invoke(self.app, ["privacy", "consent", "list", subject, "--json"])
        assert json.loads(relisted.output)["consents"][0]["withdrawn_at"] is not None

    def test_cli_consent_grant_requires_purpose(self, cli_db: pathlib.Path) -> None:
        res = runner.invoke(self.app, ["privacy", "consent", "grant", "CCCD-CLI-002", "--json"])
        assert res.exit_code != 0

    def test_cli_consent_rejects_unknown_action(self, cli_db: pathlib.Path) -> None:
        res = runner.invoke(self.app, ["privacy", "consent", "escalate", "X"])
        assert res.exit_code == 2

    def test_cli_erase_purges_recorded_consent(self, cli_db: pathlib.Path) -> None:
        subject = "CCCD-CLI-ERASE"
        runner.invoke(self.app, ["privacy", "consent", "grant", subject,
                                "--purpose", "Mục đích A", "--json"])
        runner.invoke(self.app, ["privacy", "consent", "grant", subject,
                                "--purpose", "Mục đích B", "--json"])

        erased = runner.invoke(self.app, ["privacy", "erase", subject, "--json", "--yes"])
        assert erased.exit_code == 0
        payload = json.loads(erased.output)
        assert payload["erased_rows"]["consent_log"] == 2
        assert payload["total_erased"] == 2

        after = runner.invoke(self.app, ["privacy", "consent", "list", subject, "--json"])
        assert json.loads(after.output)["consents"] == []

    def test_cli_erase_is_idempotent(self, cli_db: pathlib.Path) -> None:
        subject = "CCCD-CLI-IDEMPOTENT"

        first = runner.invoke(self.app, ["privacy", "erase", subject, "--json", "--yes"])
        second = runner.invoke(self.app, ["privacy", "erase", subject, "--json", "--yes"])

        assert first.exit_code == 0
        assert second.exit_code == 0
        assert json.loads(first.output)["total_erased"] == 0
        assert json.loads(second.output)["total_erased"] == 0

    def test_cli_erase_dry_run_keeps_everything(self, cli_db: pathlib.Path) -> None:
        """--dry-run previews the counts and deletes nothing."""
        subject = "CCCD-CLI-DRYRUN"
        runner.invoke(self.app, ["privacy", "consent", "grant", subject,
                                "--purpose", "Mục đích A", "--json"])

        preview = runner.invoke(self.app, ["privacy", "erase", subject, "--dry-run", "--json"])
        assert preview.exit_code == 0
        payload = json.loads(preview.output)
        assert payload["erased_rows"]["consent_log"] == 1

        after = runner.invoke(self.app, ["privacy", "consent", "list", subject, "--json"])
        assert len(json.loads(after.output)["consents"]) == 1

    def test_cli_erase_aborts_when_confirmation_declined(self, cli_db: pathlib.Path) -> None:
        """A live run without --yes stops rather than deleting irreversibly."""
        subject = "CCCD-CLI-CONFIRM"
        runner.invoke(self.app, ["privacy", "consent", "grant", subject,
                                "--purpose", "Mục đích A", "--json"])

        declined = runner.invoke(
            self.app, ["privacy", "erase", subject, "--json"], input="n\n",
        )
        assert declined.exit_code != 0

        after = runner.invoke(self.app, ["privacy", "consent", "list", subject, "--json"])
        assert len(json.loads(after.output)["consents"]) == 1


# ---------------------------------------------------------------------------
# Dual MCP Server Parity Tests
# ---------------------------------------------------------------------------


class TestPrivacyMcpParity:
    """Test FastMCP and fallback pure JSON-RPC tool parity for privacy tools."""

    def test_fastmcp_handlers_exist(self) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        assert hasattr(server, "_handle_privacy_audit")
        assert hasattr(server, "_handle_privacy_dpia")
        assert hasattr(server, "_handle_privacy_transfer")
        assert hasattr(server, "_handle_privacy_breach")
        assert hasattr(server, "_handle_privacy_dsar")
        assert hasattr(server, "_handle_privacy_list")
        assert hasattr(server, "_handle_privacy_status")

    def test_scripts_mcp_handlers_wired(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        tool_names = {t["name"] for t in CORE_TOOLS_SPEC}
        expected = [
            "mekong_privacy_audit",
            "mekong_privacy_dpia",
            "mekong_privacy_transfer",
            "mekong_privacy_breach",
            "mekong_privacy_dsar",
            "mekong_privacy_list",
            "mekong_privacy_status",
        ]
        for name in expected:
            assert name in tool_names, f"{name} must be in CORE_TOOLS_SPEC"
            assert name in CORE_HANDLERS, f"{name} must be in CORE_HANDLERS"

    def test_pure_json_rpc_invocation(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS

        a_handler = CORE_HANDLERS["mekong_privacy_audit"]
        a_raw = a_handler({
            "enterprise_name": "Tiki Vietnam",
            "controller_type": "CONTROLLER_AND_PROCESSOR",
            "has_sensitive_data": True,
            "has_dpo": True,
            "has_dpia_dossier": True,
        })
        a_res = json.loads(a_raw)
        assert a_res["ok"] is True
        assert a_res["enterprise_name"] == "Tiki Vietnam"
        assert a_res["compliance_score"] == 100.0

        d_handler = CORE_HANDLERS["mekong_privacy_dpia"]
        d_raw = d_handler({
            "activity_name": "Phân tích hành vi mua sắm",
            "processing_purpose": "Gợi ý sản phẩm thương mại điện tử",
            "data_categories": ["FULL_NAME", "EMAIL", "PHONE_NUMBER"],
        })
        d_res = json.loads(d_raw)
        assert d_res["ok"] is True
        assert d_res["is_sensitive_data_processed"] is False

        b_handler = CORE_HANDLERS["mekong_privacy_breach"]
        b_raw = b_handler({
            "incident_name": "Rò rỉ mã khóa xác thực",
            "severity": "HIGH",
            "affected_count": 800,
            "breach_type": "KEY_EXPOSURE",
            "hours_elapsed": 5.0,
        })
        b_res = json.loads(b_raw)
        assert b_res["ok"] is True
        assert b_res["statutory_timeline"]["is_72h_compliant"] is True
