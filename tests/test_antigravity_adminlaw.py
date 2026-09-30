"""
Tests for Vietnamese Legal Normative Documents, Regulatory Impact Assessment (RIA) & State Compensation Liability Suite (Phase 138).
Compliant with:
- Law on Promulgation of Legal Normative Documents 2015 (Law No. 80/2015/QH13, amended by Law No. 63/2020/QH14)
- Law on State Compensation Liability 2017 (Luật Trách nhiệm bồi thường của Nhà nước - Law No. 10/2017/QH14)
- Decree No. 34/2016/NĐ-CP & Decree No. 154/2020/NĐ-CP
- Decree No. 68/2018/NĐ-CP
"""

import json
import os
import tempfile
import pytest
from typer.testing import CliRunner

from src.core.adminlaw_engine import (
    AdminLawEngine,
    DocumentType,
    IssuingBody,
    CompensationSphere,
    AppraisalVerdict,
    FaultDegree,
)
from src.cli.commands.adminlaw_command import adminlaw_app
from src.core.mcp_server import MekongMcpServer
import scripts.mcp_server as scripts_mcp


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["MEKONG_ADMINLAW_DB"] = path
    yield path
    os.environ.pop("MEKONG_ADMINLAW_DB", None)
    for p in (path, f"{path}-wal", f"{path}-shm"):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass


@pytest.fixture
def engine(temp_db):
    return AdminLawEngine(db_path=temp_db)


@pytest.fixture
def runner():
    return CliRunner()


class TestAdminLawEngine:
    def test_register_document_valid(self, engine):
        res = engine.register_document(
            doc_number="80/2015/QH13",
            title="Luật Ban hành văn bản quy phạm pháp luật",
            doc_type="LUAT",
            issuing_body="QUOC_HOI",
            promulgation_date="2015-06-22",
            effective_date="2016-07-01",
            status="EFFECTIVE",
        )
        assert res["success"] is True
        doc = res["document"]
        assert doc["doc_number"] == "80/2015/QH13"
        assert doc["doc_type"] == DocumentType.LUAT.value
        assert doc["issuing_body"] == IssuingBody.QUOC_HOI.value
        assert "Article 4 Law on Promulgation" in res["statutory_reference"]

    def test_register_document_missing_fields(self, engine):
        res = engine.register_document(
            doc_number="",
            title="",
            doc_type="",
            issuing_body="",
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_register_document_invalid_type(self, engine):
        res = engine.register_document(
            doc_number="01/TEST",
            title="Test Document",
            doc_type="INVALID_TYPE",
            issuing_body="CHINH_PHU",
        )
        assert res["success"] is False
        assert "Invalid document type" in res["error"]

    def test_register_document_invalid_issuing_body(self, engine):
        res = engine.register_document(
            doc_number="02/TEST",
            title="Test Document",
            doc_type="NGHI_DINH",
            issuing_body="UNKNOWN_BODY",
        )
        assert res["success"] is False
        assert "Invalid issuing body" in res["error"]

    def test_register_document_invalid_status(self, engine):
        res = engine.register_document(
            doc_number="03/TEST",
            title="Test Document",
            doc_type="THONG_TU",
            issuing_body="BO_TU_PHAP",
            status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid status" in res["error"]

    def test_register_document_conflict_update(self, engine):
        engine.register_document(
            doc_number="10/2017/QH14",
            title="Luật Trách nhiệm bồi thường của Nhà nước",
            doc_type="LUAT",
            issuing_body="QUOC_HOI",
            status="EFFECTIVE",
        )
        res = engine.register_document(
            doc_number="10/2017/QH14",
            title="Luật Trách nhiệm bồi thường của Nhà nước (Cập nhật)",
            doc_type="LUAT",
            issuing_body="QUOC_HOI",
            status="EFFECTIVE",
        )
        assert res["success"] is True
        assert res["document"]["title"] == "Luật Trách nhiệm bồi thường của Nhà nước (Cập nhật)"

    def test_evaluate_ria_valid(self, engine):
        res = engine.evaluate_ria(
            eval_code="RIA-2025-001",
            doc_number="80/2015/QH13",
            economic_impact_score=88.5,
            social_impact_score=92.0,
            admin_procedure_burden="STREAMLINED",
            evaluator_agency="Bộ Tư pháp",
            appraisal_verdict="QUALIFIED",
            notes="Chính sách bảo đảm tính hợp hiến, hợp pháp và giảm tải thủ tục hành chính.",
        )
        assert res["success"] is True
        ria = res["ria_evaluation"]
        assert ria["eval_code"] == "RIA-2025-001"
        assert ria["economic_impact_score"] == 88.5
        assert ria["social_impact_score"] == 92.0
        assert ria["appraisal_verdict"] == AppraisalVerdict.QUALIFIED.value
        assert "Articles 35 & 58" in res["statutory_reference"]

    def test_evaluate_ria_missing_fields(self, engine):
        res = engine.evaluate_ria(
            eval_code="",
            doc_number="",
            economic_impact_score=None,
            social_impact_score=None,
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_evaluate_ria_invalid_score_bounds(self, engine):
        res_low = engine.evaluate_ria(
            eval_code="RIA-002",
            doc_number="80/2015/QH13",
            economic_impact_score=-5.0,
            social_impact_score=50.0,
        )
        assert res_low["success"] is False
        assert "between 0.0 and 100.0" in res_low["error"]

        res_high = engine.evaluate_ria(
            eval_code="RIA-003",
            doc_number="80/2015/QH13",
            economic_impact_score=50.0,
            social_impact_score=105.0,
        )
        assert res_high["success"] is False
        assert "between 0.0 and 100.0" in res_high["error"]

    def test_evaluate_ria_invalid_burden(self, engine):
        res = engine.evaluate_ria(
            eval_code="RIA-004",
            doc_number="80/2015/QH13",
            economic_impact_score=80.0,
            social_impact_score=80.0,
            admin_procedure_burden="HEAVY",
        )
        assert res["success"] is False
        assert "Invalid burden level" in res["error"]

    def test_evaluate_ria_invalid_verdict(self, engine):
        res = engine.evaluate_ria(
            eval_code="RIA-005",
            doc_number="80/2015/QH13",
            economic_impact_score=80.0,
            social_impact_score=80.0,
            appraisal_verdict="INVALID_VERDICT",
        )
        assert res["success"] is False
        assert "Invalid appraisal verdict" in res["error"]

    def test_evaluate_ria_conflict_update(self, engine):
        engine.evaluate_ria(
            eval_code="RIA-2025-006",
            doc_number="80/2015/QH13",
            economic_impact_score=75.0,
            social_impact_score=70.0,
            appraisal_verdict="CONDITIONAL_REVISION",
        )
        res = engine.evaluate_ria(
            eval_code="RIA-2025-006",
            doc_number="80/2015/QH13",
            economic_impact_score=85.0,
            social_impact_score=88.0,
            appraisal_verdict="QUALIFIED",
        )
        assert res["success"] is True
        assert res["ria_evaluation"]["appraisal_verdict"] == "QUALIFIED"
        assert res["ria_evaluation"]["economic_impact_score"] == 85.0

    def test_file_compensation_claim_valid(self, engine):
        res = engine.file_compensation_claim(
            claim_code="CLM-2025-001",
            claimant_name="Nguyễn Văn A",
            citizen_id_tax="001088001122",
            sphere="TO_TUNG_HINH_SU",
            responsible_agency="Công an Quận Ba Đình",
            claimed_amount_vnd=500_000_000,
            filing_date="2025-03-01",
            status="PENDING_REVIEW",
        )
        assert res["success"] is True
        clm = res["compensation_claim"]
        assert clm["claim_code"] == "CLM-2025-001"
        assert clm["sphere"] == CompensationSphere.TO_TUNG_HINH_SU.value
        assert clm["claimed_amount_vnd"] == 500_000_000.0
        assert "Articles 2 & 41-43" in res["statutory_reference"]

    def test_file_compensation_claim_missing_fields(self, engine):
        res = engine.file_compensation_claim(
            claim_code="",
            claimant_name="",
            citizen_id_tax="",
            sphere="",
            responsible_agency="",
            claimed_amount_vnd=0,
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_file_compensation_claim_negative_amount(self, engine):
        res = engine.file_compensation_claim(
            claim_code="CLM-002",
            claimant_name="Trần Văn B",
            citizen_id_tax="001088009988",
            sphere="QUAN_LY_HANH_CHINH",
            responsible_agency="UBND Phường Hàng Mã",
            claimed_amount_vnd=-100_000,
        )
        assert res["success"] is False
        assert "non-negative" in res["error"]

    def test_file_compensation_claim_invalid_sphere(self, engine):
        res = engine.file_compensation_claim(
            claim_code="CLM-003",
            claimant_name="Lê Văn C",
            citizen_id_tax="001088004455",
            sphere="INVALID_SPHERE",
            responsible_agency="Chi cục Thuế",
            claimed_amount_vnd=50_000_000,
        )
        assert res["success"] is False
        assert "Invalid compensation sphere" in res["error"]

    def test_file_compensation_claim_invalid_status(self, engine):
        res = engine.file_compensation_claim(
            claim_code="CLM-004",
            claimant_name="Phạm Văn D",
            citizen_id_tax="001088003322",
            sphere="THI_HANH_AN",
            responsible_agency="Chi cục THADS",
            claimed_amount_vnd=30_000_000,
            status="UNKNOWN_STATUS",
        )
        assert res["success"] is False
        assert "Invalid claim status" in res["error"]

    def test_file_compensation_claim_conflict_update(self, engine):
        engine.file_compensation_claim(
            claim_code="CLM-2025-005",
            claimant_name="Vũ Thị E",
            citizen_id_tax="001088006677",
            sphere="TO_TUNG_DAN_SU",
            responsible_agency="TAND Quận 1",
            claimed_amount_vnd=150_000_000,
            status="PENDING_REVIEW",
        )
        res = engine.file_compensation_claim(
            claim_code="CLM-2025-005",
            claimant_name="Vũ Thị E",
            citizen_id_tax="001088006677",
            sphere="TO_TUNG_DAN_SU",
            responsible_agency="TAND Quận 1",
            claimed_amount_vnd=180_000_000,
            status="ACCEPTED",
        )
        assert res["success"] is True
        assert res["compensation_claim"]["claimed_amount_vnd"] == 180_000_000.0
        assert res["compensation_claim"]["status"] == "ACCEPTED"

    def test_settle_compensation_valid(self, engine):
        res = engine.settle_compensation(
            decision_code="DEC-2025-001",
            claim_code="CLM-2025-001",
            material_damage_vnd=350_000_000,
            mental_suffering_vnd=150_000_000,
            decision_date="2025-03-15",
            payout_status="APPROVED",
        )
        assert res["success"] is True
        stl = res["settlement_decision"]
        assert stl["decision_code"] == "DEC-2025-001"
        assert stl["material_damage_vnd"] == 350_000_000.0
        assert stl["mental_suffering_vnd"] == 150_000_000.0
        assert stl["total_awarded_vnd"] == 500_000_000.0
        assert "Articles 45-48" in res["statutory_reference"]

    def test_settle_compensation_missing_fields(self, engine):
        res = engine.settle_compensation(
            decision_code="",
            claim_code="",
            material_damage_vnd=0,
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_settle_compensation_negative_damages(self, engine):
        res_mat = engine.settle_compensation(
            decision_code="DEC-002",
            claim_code="CLM-001",
            material_damage_vnd=-10_000,
            mental_suffering_vnd=0,
        )
        assert res_mat["success"] is False
        assert "non-negative" in res_mat["error"]

        res_men = engine.settle_compensation(
            decision_code="DEC-003",
            claim_code="CLM-001",
            material_damage_vnd=10_000,
            mental_suffering_vnd=-5_000,
        )
        assert res_men["success"] is False
        assert "non-negative" in res_men["error"]

    def test_settle_compensation_invalid_payout_status(self, engine):
        res = engine.settle_compensation(
            decision_code="DEC-004",
            claim_code="CLM-001",
            material_damage_vnd=100_000,
            payout_status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid payout status" in res["error"]

    def test_settle_compensation_conflict_update(self, engine):
        engine.settle_compensation(
            decision_code="DEC-2025-005",
            claim_code="CLM-2025-001",
            material_damage_vnd=100_000_000,
            mental_suffering_vnd=50_000_000,
            payout_status="APPROVED",
        )
        res = engine.settle_compensation(
            decision_code="DEC-2025-005",
            claim_code="CLM-2025-001",
            material_damage_vnd=120_000_000,
            mental_suffering_vnd=50_000_000,
            payout_status="DISBURSED",
        )
        assert res["success"] is True
        assert res["settlement_decision"]["total_awarded_vnd"] == 170_000_000.0
        assert res["settlement_decision"]["payout_status"] == "DISBURSED"

    def test_order_reimbursement_valid(self, engine):
        res = engine.order_reimbursement(
            reimbursement_code="RMB-2025-001",
            decision_code="DEC-2025-001",
            fault_officer_name="Nguyễn Văn Sai",
            fault_degree="LOI_CO_Y",
            reimbursement_amount_vnd=50_000_000,
            reimbursement_status="ORDERED",
        )
        assert res["success"] is True
        rmb = res["officer_reimbursement"]
        assert rmb["reimbursement_code"] == "RMB-2025-001"
        assert rmb["fault_degree"] == FaultDegree.LOI_CO_Y.value
        assert rmb["reimbursement_amount_vnd"] == 50_000_000.0
        assert "Articles 64-67" in res["statutory_reference"]

    def test_order_reimbursement_missing_fields(self, engine):
        res = engine.order_reimbursement(
            reimbursement_code="",
            decision_code="",
            fault_officer_name="",
            fault_degree="",
            reimbursement_amount_vnd=0,
        )
        assert res["success"] is False
        assert "Missing mandatory" in res["error"]

    def test_order_reimbursement_negative_amount(self, engine):
        res = engine.order_reimbursement(
            reimbursement_code="RMB-002",
            decision_code="DEC-001",
            fault_officer_name="Trần Văn Lỗi",
            fault_degree="LOI_VO_Y_NGHIEM_TRONG",
            reimbursement_amount_vnd=-5_000_000,
        )
        assert res["success"] is False
        assert "non-negative" in res["error"]

    def test_order_reimbursement_invalid_fault_degree(self, engine):
        res = engine.order_reimbursement(
            reimbursement_code="RMB-003",
            decision_code="DEC-001",
            fault_officer_name="Lê Văn Hại",
            fault_degree="INVALID_DEGREE",
            reimbursement_amount_vnd=10_000_000,
        )
        assert res["success"] is False
        assert "Invalid fault degree" in res["error"]

    def test_order_reimbursement_invalid_status(self, engine):
        res = engine.order_reimbursement(
            reimbursement_code="RMB-004",
            decision_code="DEC-001",
            fault_officer_name="Phạm Văn Sơ",
            fault_degree="LOI_VO_Y_NGHIEM_TRONG",
            reimbursement_amount_vnd=15_000_000,
            reimbursement_status="INVALID_STATUS",
        )
        assert res["success"] is False
        assert "Invalid reimbursement status" in res["error"]

    def test_order_reimbursement_conflict_update(self, engine):
        engine.order_reimbursement(
            reimbursement_code="RMB-2025-005",
            decision_code="DEC-2025-001",
            fault_officer_name="Hoàng Văn Nhầm",
            fault_degree="LOI_VO_Y_NGHIEM_TRONG",
            reimbursement_amount_vnd=20_000_000,
            reimbursement_status="ORDERED",
        )
        res = engine.order_reimbursement(
            reimbursement_code="RMB-2025-005",
            decision_code="DEC-2025-001",
            fault_officer_name="Hoàng Văn Nhầm",
            fault_degree="LOI_VO_Y_NGHIEM_TRONG",
            reimbursement_amount_vnd=20_000_000,
            reimbursement_status="RECOVERED",
        )
        assert res["success"] is True
        assert res["officer_reimbursement"]["reimbursement_status"] == "RECOVERED"

    def test_list_records_valid_categories(self, engine):
        engine.register_document("DOC-1", "Law 1", "LUAT", "QUOC_HOI")
        engine.evaluate_ria("RIA-1", "DOC-1", 85.0, 90.0)
        engine.file_compensation_claim("CLM-1", "Claimant 1", "123", "QUAN_LY_HANH_CHINH", "Agency", 10_000_000)
        engine.settle_compensation("DEC-1", "CLM-1", 10_000_000)
        engine.order_reimbursement("RMB-1", "DEC-1", "Officer 1", "LOI_CO_Y", 2_000_000)

        for cat in ("documents", "ria", "claims", "settlements", "reimbursements"):
            res = engine.list_records(cat)
            assert res["success"] is True
            assert res["count"] >= 1
            assert len(res["records"]) >= 1

    def test_list_records_invalid_category(self, engine):
        res = engine.list_records("invalid_cat")
        assert res["success"] is False
        assert "Invalid category" in res["error"]

    def test_telemetry_status_empty(self, engine):
        status = engine.get_telemetry_status()
        assert status["success"] is True
        t = status["telemetry"]
        assert t["legal_normative_documents"]["total"] == 0
        assert t["regulatory_impact_assessments"]["total_appraisals"] == 0
        assert t["state_compensation_claims"]["total_claims"] == 0
        assert t["compensation_settlements"]["total_decisions"] == 0
        assert t["officer_reimbursements"]["total_orders"] == 0

    def test_telemetry_status_populated(self, engine):
        engine.register_document("DOC-1", "Law 1", "LUAT", "QUOC_HOI", status="EFFECTIVE")
        engine.register_document("DOC-2", "Decree 1", "NGHI_DINH", "CHINH_PHU", status="EXPIRED")
        engine.evaluate_ria("RIA-1", "DOC-1", 80.0, 90.0, appraisal_verdict="QUALIFIED")
        engine.evaluate_ria("RIA-2", "DOC-2", 60.0, 70.0, appraisal_verdict="CONDITIONAL_REVISION")
        engine.file_compensation_claim("CLM-1", "Claimant 1", "123", "QUAN_LY_HANH_CHINH", "Agency", 50_000_000, status="SETTLED")
        engine.settle_compensation("DEC-1", "CLM-1", 40_000_000, 10_000_000)
        engine.order_reimbursement("RMB-1", "DEC-1", "Officer 1", "LOI_CO_Y", 10_000_000)

        status = engine.get_telemetry_status()
        assert status["success"] is True
        t = status["telemetry"]
        assert t["legal_normative_documents"]["total"] == 2
        assert t["legal_normative_documents"]["effective"] == 1
        assert t["regulatory_impact_assessments"]["total_appraisals"] == 2
        assert t["regulatory_impact_assessments"]["qualified"] == 1
        assert t["regulatory_impact_assessments"]["average_economic_impact"] == 70.0
        assert t["regulatory_impact_assessments"]["average_social_impact"] == 80.0
        assert t["state_compensation_claims"]["total_claims"] == 1
        assert t["state_compensation_claims"]["settled"] == 1
        assert t["state_compensation_claims"]["total_claimed_vnd"] == 50_000_000.0
        assert t["compensation_settlements"]["total_decisions"] == 1
        assert t["compensation_settlements"]["total_awarded_vnd"] == 50_000_000.0
        assert t["officer_reimbursements"]["total_orders"] == 1
        assert t["officer_reimbursements"]["total_reimbursement_ordered_vnd"] == 10_000_000.0


class TestAdminLawCLI:
    def test_cli_help(self, runner):
        res = runner.invoke(adminlaw_app, ["--help"])
        assert res.exit_code == 0
        assert "Vietnamese Legal Normative Documents" in res.output

    def test_cli_status_dashboard(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, ["status"])
        assert res.exit_code == 0
        assert "Administrative Law Telemetry" in res.output

    def test_cli_status_json(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, ["status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert "telemetry" in data

    def test_cli_document_success_and_json(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "document",
            "--number", "80/2015/QH13",
            "--title", "Luật Ban hành VBQPPL",
            "--type", "LUAT",
            "--body", "QUOC_HOI",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["document"]["doc_number"] == "80/2015/QH13"

    def test_cli_document_validation_failure(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "document",
            "--number", "80/2015/QH13",
            "--title", "Luật Ban hành VBQPPL",
            "--type", "INVALID_TYPE",
            "--body", "QUOC_HOI",
        ])
        assert res.exit_code == 1
        assert "Failed to register document" in res.output

    def test_cli_ria_success_and_json(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "ria",
            "--code", "RIA-001",
            "--doc-number", "80/2015/QH13",
            "--economic", "90.0",
            "--social", "95.0",
            "--burden", "STREAMLINED",
            "--verdict", "QUALIFIED",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["ria_evaluation"]["eval_code"] == "RIA-001"

    def test_cli_ria_validation_failure(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "ria",
            "--code", "RIA-002",
            "--doc-number", "80/2015/QH13",
            "--economic", "150.0",
            "--social", "50.0",
        ])
        assert res.exit_code == 1
        assert "Failed to record RIA appraisal" in res.output

    def test_cli_claim_success_and_json(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "claim",
            "--code", "CLM-001",
            "--name", "Nguyễn Văn X",
            "--citizen-id", "001090123456",
            "--sphere", "TO_TUNG_HINH_SU",
            "--agency", "Công an Hà Nội",
            "--amount", "200000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["compensation_claim"]["claim_code"] == "CLM-001"

    def test_cli_claim_validation_failure(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "claim",
            "--code", "CLM-002",
            "--name", "Nguyễn Văn Y",
            "--citizen-id", "001090654321",
            "--sphere", "INVALID_SPHERE",
            "--agency", "UBND",
            "--amount", "1000000",
        ])
        assert res.exit_code == 1
        assert "Failed to file compensation claim" in res.output

    def test_cli_settle_success_and_json(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "settle",
            "--code", "DEC-001",
            "--claim-code", "CLM-001",
            "--material", "150000000",
            "--mental", "50000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["settlement_decision"]["total_awarded_vnd"] == 200_000_000.0

    def test_cli_settle_validation_failure(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "settle",
            "--code", "DEC-002",
            "--claim-code", "CLM-001",
            "--material", "-1000",
        ])
        assert res.exit_code == 1
        assert "Failed to issue settlement decision" in res.output

    def test_cli_reimburse_success_and_json(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "reimburse",
            "--code", "RMB-001",
            "--decision-code", "DEC-001",
            "--officer", "Cán bộ A",
            "--fault-degree", "LOI_CO_Y",
            "--amount", "30000000",
            "--json",
        ])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["success"] is True
        assert data["officer_reimbursement"]["reimbursement_code"] == "RMB-001"

    def test_cli_reimburse_validation_failure(self, runner, temp_db):
        res = runner.invoke(adminlaw_app, [
            "reimburse",
            "--code", "RMB-002",
            "--decision-code", "DEC-001",
            "--officer", "Cán bộ B",
            "--fault-degree", "INVALID_DEGREE",
            "--amount", "10000000",
        ])
        assert res.exit_code == 1
        assert "Failed to create reimbursement order" in res.output

    def test_cli_list_records(self, runner, temp_db):
        # Insert records first
        runner.invoke(adminlaw_app, [
            "document",
            "--number", "63/2020/QH14",
            "--title", "Luật Sửa đổi VBQPPL",
            "--type", "LUAT",
            "--body", "QUOC_HOI",
        ])
        runner.invoke(adminlaw_app, [
            "ria",
            "--code", "RIA-010",
            "--doc-number", "63/2020/QH14",
            "--economic", "85",
            "--social", "90",
        ])
        runner.invoke(adminlaw_app, [
            "claim",
            "--code", "CLM-010",
            "--name", "Lê Văn C",
            "--citizen-id", "001099887766",
            "--sphere", "QUAN_LY_HANH_CHINH",
            "--agency", "Sở Xây dựng",
            "--amount", "50000000",
        ])
        runner.invoke(adminlaw_app, [
            "settle",
            "--code", "DEC-010",
            "--claim-code", "CLM-010",
            "--material", "50000000",
        ])
        runner.invoke(adminlaw_app, [
            "reimburse",
            "--code", "RMB-010",
            "--decision-code", "DEC-010",
            "--officer", "Thanh tra viên D",
            "--fault-degree", "LOI_VO_Y_NGHIEM_TRONG",
            "--amount", "5000000",
        ])

        for cat in ("documents", "ria", "claims", "settlements", "reimbursements"):
            res_txt = runner.invoke(adminlaw_app, ["list", "--category", cat])
            assert res_txt.exit_code == 0
            assert "Administrative Law Records" in res_txt.output

            res_json = runner.invoke(adminlaw_app, ["list", "--category", cat, "--json"])
            assert res_json.exit_code == 0
            data = json.loads(res_json.output)
            assert data["success"] is True
            assert data["count"] >= 1


class TestAdminLawMCP:
    def test_core_mcp_server_handlers(self, temp_db):
        server = MekongMcpServer()

        # 1. Document
        res_doc = json.loads(server._handle_adminlaw_document(
            number="80/2015/QH13",
            title="Luật Ban hành VBQPPL",
            type="LUAT",
            body="QUOC_HOI",
            promulgation="2015-06-22",
            effective="2016-07-01",
        ))
        assert res_doc["success"] is True

        # 2. RIA
        res_ria = json.loads(server._handle_adminlaw_ria(
            code="RIA-MCP-01",
            doc_number="80/2015/QH13",
            economic=90.0,
            social=95.0,
            burden="STREAMLINED",
            agency="Bộ Tư pháp",
            verdict="QUALIFIED",
        ))
        assert res_ria["success"] is True

        # 3. Claim
        res_claim = json.loads(server._handle_adminlaw_claim(
            code="CLM-MCP-01",
            name="Nguyễn Văn MCP",
            citizen_id="001099123456",
            sphere="TO_TUNG_HINH_SU",
            agency="Viện kiểm sát",
            amount=300_000_000,
        ))
        assert res_claim["success"] is True

        # 4. Settle
        res_settle = json.loads(server._handle_adminlaw_settle(
            code="DEC-MCP-01",
            claim_code="CLM-MCP-01",
            material=200_000_000,
            mental=100_000_000,
        ))
        assert res_settle["success"] is True

        # 5. Reimburse
        res_reimb = json.loads(server._handle_adminlaw_reimburse(
            code="RMB-MCP-01",
            decision_code="DEC-MCP-01",
            officer="Kiểm sát viên E",
            fault_degree="LOI_CO_Y",
            amount=60_000_000,
        ))
        assert res_reimb["success"] is True

        # 6. List
        res_list = json.loads(server._handle_adminlaw_list(category="documents", limit=10))
        assert res_list["success"] is True
        assert res_list["count"] >= 1

        # 7. Status
        res_status = json.loads(server._handle_adminlaw_status())
        assert res_status["success"] is True
        assert res_status["telemetry"]["legal_normative_documents"]["total"] >= 1

    def test_scripts_mcp_server_handlers_and_aliases(self, temp_db):
        # Verify all tools registered in CORE_HANDLERS
        tools = [
            "mekong_adminlaw_document",
            "mekong_adminlaw_ria",
            "mekong_adminlaw_claim",
            "mekong_adminlaw_settle",
            "mekong_adminlaw_reimburse",
            "mekong_adminlaw_list",
            "mekong_adminlaw_status",
            "adminlaw_document",
            "adminlaw_ria",
            "adminlaw_claim",
            "adminlaw_settle",
            "adminlaw_reimburse",
            "adminlaw_list",
            "adminlaw_status",
        ]
        for t in tools:
            assert t in scripts_mcp.CORE_HANDLERS, f"Missing handler for {t}"

        # Test execution via CORE_HANDLERS
        # 1. Document
        res_doc = json.loads(scripts_mcp.CORE_HANDLERS["mekong_adminlaw_document"]({
            "number": "80/2015/QH13",
            "title": "Luật Ban hành VBQPPL",
            "type": "LUAT",
            "body": "QUOC_HOI",
        }))
        assert res_doc["success"] is True

        # 2. RIA
        res_ria = json.loads(scripts_mcp.CORE_HANDLERS["mekong_adminlaw_ria"]({
            "code": "RIA-SCRIPTS-01",
            "doc_number": "80/2015/QH13",
            "economic": 85.0,
            "social": 88.0,
        }))
        assert res_ria["success"] is True

        # 3. Claim
        res_claim = json.loads(scripts_mcp.CORE_HANDLERS["mekong_adminlaw_claim"]({
            "code": "CLM-SCRIPTS-01",
            "name": "Trần Thị F",
            "citizen_id": "001099654321",
            "sphere=" : "QUAN_LY_HANH_CHINH",
            "sphere": "QUAN_LY_HANH_CHINH",
            "agency": "UBND Huyện",
            "amount": 75_000_000,
        }))
        assert res_claim["success"] is True

        # 4. Settle
        res_settle = json.loads(scripts_mcp.CORE_HANDLERS["mekong_adminlaw_settle"]({
            "code": "DEC-SCRIPTS-01",
            "claim_code": "CLM-SCRIPTS-01",
            "material": 75_000_000,
        }))
        assert res_settle["success"] is True

        # 5. Reimburse
        res_reimb = json.loads(scripts_mcp.CORE_HANDLERS["mekong_adminlaw_reimburse"]({
            "code": "RMB-SCRIPTS-01",
            "decision_code": "DEC-SCRIPTS-01",
            "officer": "Chủ tịch xã G",
            "fault_degree": "LOI_VO_Y_NGHIEM_TRONG",
            "amount": 10_000_000,
        }))
        assert res_reimb["success"] is True

        # 6. List
        res_list = json.loads(scripts_mcp.CORE_HANDLERS["adminlaw_list"]({
            "category": "claims",
        }))
        assert res_list["success"] is True
        assert res_list["count"] >= 1

        # 7. Status
        res_status = json.loads(scripts_mcp.CORE_HANDLERS["adminlaw_status"]({}))
        assert res_status["success"] is True
        assert res_status["telemetry"]["legal_normative_documents"]["total"] >= 1
