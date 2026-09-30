"""
Test suite for Vietnamese Archives, Digital Records & State Secrets Declassification Suite (Phase 103).
Covers:
- ArchivesEngine (pure standard-library engine, SQLite WAL persistence).
- CLI surface (mekong archives seal/appraise/declassify/practitioner/warehouse/list/status).
- MCP parity across scripts/mcp_server.py and src/core/mcp_server.py.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.core.archives_engine import ArchivesEngine
from src.cli.commands.archives_command import archives_app


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = str(Path(tmpdir) / "test_archives.db")
        yield db_path


class TestArchivesEngine:
    def test_engine_init_and_tables(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        with engine._get_connection() as conn:
            tables = [
                r[0]
                for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
            ]
        assert "archival_electronic_records" in tables
        assert "archival_retention_appraisals" in tables
        assert "archival_declassification_reviews" in tables
        assert "archival_practitioners" in tables
        assert "archival_warehouse_audits" in tables

    def test_seal_electronic_record_compliant(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.seal_electronic_record(
            agency_code="UBND-HCM",
            title="Quyết định quy hoạch đô thị sáng tạo 2025",
            doc_format="PDF/A-1a",
            content_bytes=b"sample archival content binary data",
            digital_signature=True,
            tsa_timestamp=True,
            retention="PERMANENT",
            security_level="UNCLASSIFIED",
        )
        assert res.status == "SEALED_COMPLIANT"
        assert res.record_id.startswith("REC-")
        assert len(res.checksum_sha256) == 64
        assert len(res.reasons) == 0

    def test_seal_electronic_record_invalid_format_and_missing_sig(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.seal_electronic_record(
            agency_code="UBND-HN",
            title="Báo cáo tài chính nội bộ",
            doc_format="DOCX",
            digital_signature=False,
            tsa_timestamp=False,
            retention="10_YEARS",
            security_level="CONFIDENTIAL",
        )
        assert res.status == "SEAL_FAILED"
        assert any("DOCX" in r for r in res.reasons)
        assert any("chữ ký số" in r for r in res.reasons)
        assert any("dấu thời gian" in r for r in res.reasons)

    def test_appraise_retention_permanent(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.appraise_retention(
            record_id="REC-2024-001",
            title="Nghị quyết đại hội cổ đông thành lập doanh nghiệp",
            created_year=2000,
            retention_schedule="PERMANENT",
        )
        assert res.destruction_status == "PRESERVED_PERMANENT"
        assert not res.is_expired
        assert any("vĩnh viễn" in r for r in res.reasons)

    def test_appraise_retention_active(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.appraise_retention(
            record_id="REC-2024-002",
            title="Hợp đồng dịch vụ bảo trì 2022",
            created_year=2022,
            retention_schedule="5_YEARS",
        )
        assert res.destruction_status == "ACTIVE_RETENTION"
        assert not res.is_expired

    def test_appraise_retention_expired_approved_for_destruction(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.appraise_retention(
            record_id="REC-2024-003",
            title="Phiếu thu chi và chứng từ thanh toán năm 2010",
            created_year=2010,
            retention_schedule="10_YEARS",
            has_appraisal_council=True,
            state_archives_approved=True,
            director_signed=True,
        )
        assert res.is_expired
        assert res.destruction_status == "APPROVED_FOR_DESTRUCTION"
        assert len(res.reasons) == 0

    def test_appraise_retention_expired_rejected_missing_council(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.appraise_retention(
            record_id="REC-2024-004",
            title="Công văn trao đổi nghiệp vụ 2015",
            created_year=2015,
            retention_schedule="5_YEARS",
            has_appraisal_council=False,
            state_archives_approved=True,
            director_signed=False,
        )
        assert res.is_expired
        assert res.destruction_status == "DESTRUCTION_REJECTED"
        assert any("Hội đồng" in r for r in res.reasons)
        assert any("Quyết định tiêu hủy" in r for r in res.reasons)

    def test_declassification_automatic_term_expired(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        # Confidential: 10 years statutory protection
        res = engine.review_declassification(
            record_id="SEC-2010-001",
            title="Phương án bảo đảm an ninh hệ thống mạng nội bộ 2010",
            security_level="CONFIDENTIAL",
            classified_year=2010,
            authorized_by="Cục An ninh mạng",
        )
        assert res.term_expired
        assert res.declassification_status == "DECLASSIFIED"
        assert any("Tự động giải mật" in r for r in res.reasons)

    def test_declassification_active_secret(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        # Top Secret: 30 years
        res = engine.review_declassification(
            record_id="SEC-2020-001",
            title="Kế hoạch tác chiến chiến lược",
            security_level="TOP_SECRET",
            classified_year=2020,
            authorized_by="Bộ Quốc phòng",
            request_early=False,
        )
        assert not res.term_expired
        assert res.declassification_status == "ACTIVE_SECRET"

    def test_declassification_early_approved(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.review_declassification(
            record_id="SEC-2018-001",
            title="Đề án khảo sát tài nguyên khoáng sản",
            security_level="SECRET",
            classified_year=2018,
            authorized_by="Bộ Tài nguyên và Môi trường",
            request_early=True,
            national_interest_safeguarded=True,
            head_of_agency_approval=True,
        )
        assert res.declassification_status == "DECLASSIFIED"
        assert res.early_declassification
        assert any("trước thời hạn" in r for r in res.reasons)

    def test_declassification_early_rejected(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.review_declassification(
            record_id="SEC-2022-001",
            title="Phương án phòng thủ vùng biên cương",
            security_level="TOP_SECRET",
            classified_year=2022,
            authorized_by="Bộ Quốc phòng",
            request_early=True,
            national_interest_safeguarded=False,
            head_of_agency_approval=False,
        )
        assert res.declassification_status == "REJECTED"
        assert any("nguy hại" in r for r in res.reasons)

    def test_practitioner_audit_eligible(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.audit_practitioner(
            name="Nguyễn Thị Thanh",
            degree_major="Lưu trữ học và Quản trị văn phòng",
            experience_years=5,
            passed_national_exam=True,
            clean_record=True,
        )
        assert res.is_eligible
        assert res.certificate_no.startswith("VTLT-CCHN-")
        assert len(res.reasons) == 0

    def test_practitioner_audit_ineligible_irrelevant_major_and_exp(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.audit_practitioner(
            name="Trần Văn Minh",
            degree_major="Kỹ thuật Cơ khí",
            experience_years=1,
            passed_national_exam=False,
            clean_record=False,
        )
        assert not res.is_eligible
        assert res.certificate_no == "N/A"
        assert any("Chuyên ngành" in r for r in res.reasons)
        assert any("Thời gian" in r for r in res.reasons)

    def test_warehouse_audit_compliant(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.audit_warehouse(
            facility_name="Kho Lưu trữ Trung tâm 1",
            temp_celsius=20.5,
            humidity_pct=52.5,
            clean_gas_fire_system=True,
            cctv_247=True,
            fireproof_shelving=True,
        )
        assert res.grade == "GRADE_A_COMPLIANT"
        assert len(res.reasons) == 0

    def test_warehouse_audit_non_compliant(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        res = engine.audit_warehouse(
            facility_name="Kho Chứa Tài liệu Tạm",
            temp_celsius=29.0,
            humidity_pct=75.0,
            clean_gas_fire_system=False,
            cctv_247=False,
            fireproof_shelving=False,
        )
        assert res.grade == "NON_COMPLIANT"
        assert any("Nhiệt độ" in r for r in res.reasons)
        assert any("Độ ẩm" in r for r in res.reasons)
        assert any("khí sạch" in r for r in res.reasons)

    def test_telemetry_and_list_records(self, temp_db: str):
        engine = ArchivesEngine(db_path=temp_db)
        engine.seal_electronic_record("UBND", "Văn bản 1", "PDF/A-1a")
        engine.appraise_retention("R1", "Tài liệu", 2010, "10_YEARS")
        engine.review_declassification("S1", "Mật", "CONFIDENTIAL", 2010, "Bộ")
        engine.audit_practitioner("Lê A", "Lưu trữ", 4)
        engine.audit_warehouse("Kho A", 20.0, 52.0)

        telemetry = engine.get_status()
        assert telemetry.total_records >= 1
        assert telemetry.compliant_sealed_records >= 1
        assert telemetry.permanent_records >= 1
        assert telemetry.declassified_records >= 1

        records = engine.list_records(category="all", limit=10)
        assert "electronic_records" in records
        assert "retention_appraisals" in records
        assert "declassification_reviews" in records
        assert "practitioners" in records
        assert "warehouse_audits" in records


class TestArchivesCli:
    def setup_method(self):
        self.runner = CliRunner()

    def test_cli_overview_and_json(self):
        res = self.runner.invoke(archives_app, [])
        assert res.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ LƯU TRỮ SỐ" in res.output

        res_json = self.runner.invoke(archives_app, ["--json"])
        assert res_json.exit_code == 0
        data = json.loads(res_json.output)
        assert "total_records" in data

    def test_cli_seal_cmd(self):
        res = self.runner.invoke(
            archives_app,
            [
                "seal",
                "SO-NOI-VU",
                "Quy chế văn thư lưu trữ điện tử cơ quan",
                "--format", "PDF/A-1a",
                "--retention", "PERMANENT",
                "--signature",
                "--tsa",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["status"] == "SEALED_COMPLIANT"

    def test_cli_appraise_cmd(self):
        res = self.runner.invoke(
            archives_app,
            [
                "appraise",
                "REC-2012-009",
                "Hồ sơ thanh toán công tác phí năm 2012",
                "--year", "2012",
                "--schedule", "10_YEARS",
                "--council",
                "--approval",
                "--director",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["destruction_status"] == "APPROVED_FOR_DESTRUCTION"

    def test_cli_declassify_cmd(self):
        res = self.runner.invoke(
            archives_app,
            [
                "declassify",
                "SEC-2005-001",
                "Kế hoạch phân bổ ngân sách bí mật 2005",
                "--security", "CONFIDENTIAL",
                "--year", "2005",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["declassification_status"] == "DECLASSIFIED"

    def test_cli_practitioner_cmd(self):
        res = self.runner.invoke(
            archives_app,
            [
                "practitioner",
                "Vũ Thị Lan",
                "--major", "Lưu trữ học",
                "--exp", "4",
                "--exam",
                "--clean",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["is_eligible"] is True

    def test_cli_warehouse_cmd(self):
        res = self.runner.invoke(
            archives_app,
            [
                "warehouse",
                "Kho Lưu trữ Tỉnh Đồng Nai",
                "--temp", "21.0",
                "--humidity", "53.0",
                "--fire-gas",
                "--cctv",
                "--shelving",
                "--json",
            ],
        )
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["grade"] == "GRADE_A_COMPLIANT"

    def test_cli_list_and_status_cmds(self):
        res_list = self.runner.invoke(archives_app, ["list", "--category", "all", "--json"])
        assert res_list.exit_code == 0
        data_list = json.loads(res_list.output)
        assert isinstance(data_list, dict)

        res_status = self.runner.invoke(archives_app, ["status", "--json"])
        assert res_status.exit_code == 0
        data_status = json.loads(res_status.output)
        assert "total_records" in data_status


class TestArchivesMcpHandlers:
    def test_scripts_mcp_server_handlers(self):
        from scripts.mcp_server import (
            handle_archives_seal,
            handle_archives_appraise,
            handle_archives_declassify,
            handle_archives_practitioner,
            handle_archives_warehouse,
            handle_archives_list,
            handle_archives_status,
        )

        res_seal = json.loads(handle_archives_seal({
            "agency_code": "VP-CP",
            "title": "Nghị quyết phiên họp thường kỳ",
            "doc_format": "PDF/A-1a",
        }))
        assert res_seal["status"] == "SEALED_COMPLIANT"

        res_appraise = json.loads(handle_archives_appraise({
            "record_id": "REC-TEST-1",
            "title": "Biên bản kiểm tra kỹ thuật",
            "created_year": 2012,
            "retention_schedule": "10_YEARS",
        }))
        assert res_appraise["destruction_status"] == "APPROVED_FOR_DESTRUCTION"

        res_declass = json.loads(handle_archives_declassify({
            "record_id": "SEC-TEST-1",
            "title": "Báo cáo nội bộ mật",
            "security_level": "CONFIDENTIAL",
            "classified_year": 2010,
        }))
        assert res_declass["declassification_status"] == "DECLASSIFIED"

        res_prac = json.loads(handle_archives_practitioner({
            "name": "Hoàng Anh",
            "degree_major": "Lưu trữ học",
            "experience_years": 4,
        }))
        assert res_prac["is_eligible"] is True

        res_wh = json.loads(handle_archives_warehouse({
            "facility_name": "Kho A",
            "temp_celsius": 20.0,
            "humidity_pct": 52.0,
        }))
        assert res_wh["grade"] == "GRADE_A_COMPLIANT"

        res_list = json.loads(handle_archives_list({"category": "all"}))
        assert isinstance(res_list, dict)

        res_status = json.loads(handle_archives_status({}))
        assert "total_records" in res_status

    def test_core_mcp_server_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer(name="test-server")

        res_seal = json.loads(server._handle_archives_seal(
            agency_code="BO-TC",
            title="Thông tư ban hành biểu mẫu",
            doc_format="PDF/A-1a",
        ))
        assert res_seal["status"] == "SEALED_COMPLIANT"

        res_appraise = json.loads(server._handle_archives_appraise(
            record_id="REC-TEST-2",
            title="Kế hoạch công tác năm 2015",
            created_year=2015,
            retention_schedule="5_YEARS",
        ))
        assert res_appraise["destruction_status"] == "APPROVED_FOR_DESTRUCTION"

        res_declass = json.loads(server._handle_archives_declassify(
            record_id="SEC-TEST-2",
            title="Tài liệu mật 2012",
            security_level="CONFIDENTIAL",
            classified_year=2012,
        ))
        assert res_declass["declassification_status"] == "DECLASSIFIED"

        res_prac = json.loads(server._handle_archives_practitioner(
            name="Đặng Văn B",
            degree_major="Lưu trữ học",
            experience_years=3,
        ))
        assert res_prac["is_eligible"] is True

        res_wh = json.loads(server._handle_archives_warehouse(
            facility_name="Kho B",
            temp_celsius=19.5,
            humidity_pct=51.0,
        ))
        assert res_wh["grade"] == "GRADE_A_COMPLIANT"

        res_list = json.loads(server._handle_archives_list(category="all"))
        assert isinstance(res_list, dict)

        res_status = json.loads(server._handle_archives_status())
        assert "total_records" in res_status
