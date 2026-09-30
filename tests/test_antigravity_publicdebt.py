"""
Comprehensive test suite for Vietnamese Public Debt Management & Sovereign Credit (Luật Quản lý nợ công số 20/2017/QH14).
Tests pure Python engine isolation, Typer CLI surface, dual MCP parity, and statutory red line calculations.
"""

import json
from pathlib import Path
from typing import Any, Dict
import pytest
from typer.testing import CliRunner

from src.core.publicdebt_engine import PublicDebtEngine
from src.cli.commands.publicdebt_command import publicdebt_app
from scripts.mcp_server import (
    handle_publicdebt_instrument,
    handle_publicdebt_schedule,
    handle_publicdebt_repay,
    handle_publicdebt_onlend,
    handle_publicdebt_safety,
    handle_publicdebt_list,
    handle_publicdebt_status,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PublicDebtEngine:
    db_file = tmp_path / "test_publicdebt.db"
    monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))
    return PublicDebtEngine(str(db_file))


# =============================================================================
# 1. Core Engine Tests
# =============================================================================

class TestPublicDebtEngine:
    def test_register_debt_instrument_valid(self, temp_engine: PublicDebtEngine) -> None:
        # Domestic Treasury Bond in VND
        res1 = temp_engine.register_debt_instrument(
            debt_code="TPCP-2026-10Y-01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="Kho bạc Nhà nước",
            borrower_name="Chính phủ Việt Nam",
            principal_amount=10_000_000_000_000.0,
            interest_rate_pct=3.85,
            tenor_years=10,
            issuance_date_str="2026-01-15",
        )
        assert res1["ok"] is True
        assert res1["debt_code"] == "TPCP-2026-10Y-01"
        assert res1["principal_vnd"] == 10_000_000_000_000.0
        assert res1["maturity_date"] == "2036-01-15"

        # Foreign ODA Loan in USD
        res2 = temp_engine.register_debt_instrument(
            debt_code="WB-ODA-VN01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="ODA_LOAN",
            creditor_name="World Bank (IBRD)",
            borrower_name="Chính phủ Việt Nam",
            principal_amount=500_000_000.0,
            original_currency="USD",
            fx_rate_to_vnd=25_400.0,
            interest_rate_pct=1.75,
            tenor_years=25,
            issuance_date_str="2026-02-01",
        )
        assert res2["ok"] is True
        assert res2["principal_vnd"] == 500_000_000.0 * 25_400.0

    def test_register_debt_instrument_duplicate(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-DUP",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=1_000_000_000.0,
            interest_rate_pct=3.0,
            tenor_years=5,
            issuance_date_str="2026-01-01",
        )
        with pytest.raises(ValueError, match="đã tồn tại trong hệ thống"):
            temp_engine.register_debt_instrument(
                debt_code="TPCP-DUP",
                debt_category="GOVERNMENT_DEBT",
                instrument_type="TREASURY_BOND",
                creditor_name="KBNN",
                borrower_name="Chính phủ",
                principal_amount=2_000_000_000.0,
                interest_rate_pct=3.5,
                tenor_years=5,
                issuance_date_str="2026-01-01",
            )

    def test_register_debt_instrument_invalid_inputs(self, temp_engine: PublicDebtEngine) -> None:
        with pytest.raises(ValueError, match="Nhóm nợ công không hợp lệ"):
            temp_engine.register_debt_instrument(
                debt_code="ERR-01",
                debt_category="PRIVATE_DEBT",
                instrument_type="TREASURY_BOND",
                creditor_name="KBNN",
                borrower_name="Chính phủ",
                principal_amount=1_000_000.0,
                interest_rate_pct=3.0,
                tenor_years=5,
                issuance_date_str="2026-01-01",
            )

        with pytest.raises(ValueError, match="Loại công cụ nợ không hợp lệ"):
            temp_engine.register_debt_instrument(
                debt_code="ERR-02",
                debt_category="GOVERNMENT_DEBT",
                instrument_type="BITCOIN_BOND",
                creditor_name="KBNN",
                borrower_name="Chính phủ",
                principal_amount=1_000_000.0,
                interest_rate_pct=3.0,
                tenor_years=5,
                issuance_date_str="2026-01-01",
            )

        with pytest.raises(ValueError, match="Số tiền vay gốc phải lớn hơn 0"):
            temp_engine.register_debt_instrument(
                debt_code="ERR-03",
                debt_category="GOVERNMENT_DEBT",
                instrument_type="TREASURY_BOND",
                creditor_name="KBNN",
                borrower_name="Chính phủ",
                principal_amount=-1000.0,
                interest_rate_pct=3.0,
                tenor_years=5,
                issuance_date_str="2026-01-01",
            )

        with pytest.raises(ValueError, match="Lãi suất vay không hợp lệ"):
            temp_engine.register_debt_instrument(
                debt_code="ERR-04",
                debt_category="GOVERNMENT_DEBT",
                instrument_type="TREASURY_BOND",
                creditor_name="KBNN",
                borrower_name="Chính phủ",
                principal_amount=1_000_000.0,
                interest_rate_pct=150.0,
                tenor_years=5,
                issuance_date_str="2026-01-01",
            )

        with pytest.raises(ValueError, match="Kỳ hạn vay"):
            temp_engine.register_debt_instrument(
                debt_code="ERR-05",
                debt_category="GOVERNMENT_DEBT",
                instrument_type="TREASURY_BOND",
                creditor_name="KBNN",
                borrower_name="Chính phủ",
                principal_amount=1_000_000.0,
                interest_rate_pct=3.0,
                tenor_years=0,
                issuance_date_str="2026-01-01",
            )

    def test_schedule_debt_service_valid(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-2026-01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=5_000_000_000_000.0,
            interest_rate_pct=4.0,
            tenor_years=5,
            issuance_date_str="2026-01-01",
        )

        res = temp_engine.schedule_debt_service(
            debt_code="TPCP-2026-01",
            payment_period="2026-K1",
            due_date_str="2026-07-01",
            principal_due_vnd=0.0,
            interest_due_vnd=100_000_000_000.0,
            fees_due_vnd=500_000_000.0,
        )
        assert res["ok"] is True
        assert res["debt_code"] == "TPCP-2026-01"
        assert res["total_due_vnd"] == 100_500_000_000.0
        assert res["status"] == "DUE"

    def test_schedule_debt_service_nonexistent_debt(self, temp_engine: PublicDebtEngine) -> None:
        with pytest.raises(ValueError, match="Không tìm thấy công cụ nợ"):
            temp_engine.schedule_debt_service(
                debt_code="NONEXISTENT-DEBT",
                payment_period="2026-K1",
                due_date_str="2026-07-01",
                principal_due_vnd=1_000_000.0,
                interest_due_vnd=100_000.0,
            )

    def test_execute_debt_repayment_partial_and_full(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-PAY-01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=1_000_000_000_000.0,
            interest_rate_pct=3.0,
            tenor_years=3,
            issuance_date_str="2026-01-01",
        )
        sched = temp_engine.schedule_debt_service(
            debt_code="TPCP-PAY-01",
            payment_period="2026-K1",
            due_date_str="2026-06-30",
            principal_due_vnd=100_000_000_000.0,
            interest_due_vnd=15_000_000_000.0,
        )
        sched_id = sched["schedule_id"]

        # Partial repayment: 50 billion out of 115 billion
        p1 = temp_engine.execute_debt_repayment(
            schedule_id=sched_id,
            paid_amount_vnd=50_000_000_000.0,
            payment_date_str="2026-06-25",
        )
        assert p1["ok"] is True
        assert p1["cumulative_paid_vnd"] == 50_000_000_000.0
        assert p1["remaining_due_vnd"] == 65_000_000_000.0
        assert p1["status"] == "PARTIAL"

        # Complete repayment: 65 billion
        p2 = temp_engine.execute_debt_repayment(
            schedule_id=sched_id,
            paid_amount_vnd=65_000_000_000.0,
            payment_date_str="2026-06-30",
        )
        assert p2["ok"] is True
        assert p2["cumulative_paid_vnd"] == 115_000_000_000.0
        assert p2["remaining_due_vnd"] == 0.0
        assert p2["status"] == "PAID"

    def test_register_onlending_agreement_valid(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="ADB-ODA-HCM01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="ODA_LOAN",
            creditor_name="ADB",
            borrower_name="Chính phủ Việt Nam",
            principal_amount=10_000_000_000_000.0,
            interest_rate_pct=2.0,
            tenor_years=20,
            issuance_date_str="2026-01-01",
        )

        res = temp_engine.register_onlending_agreement(
            onlending_code="CVL-2026-HCM-01",
            parent_debt_code="ADB-ODA-HCM01",
            sub_borrower_name="UBND TP. Hồ Chí Minh",
            project_name="Dự án Cải thiện Môi trường Nước",
            allocated_amount_vnd=4_000_000_000_000.0,
            onlending_fee_pct=0.25,
            credit_risk_tier="LOW",
        )
        assert res["ok"] is True
        assert res["onlending_code"] == "CVL-2026-HCM-01"
        assert res["allocated_amount_vnd"] == 4_000_000_000_000.0
        assert res["status"] == "ACTIVE"

    def test_register_onlending_agreement_exceed_parent(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="JICA-ODA-01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="ODA_LOAN",
            creditor_name="JICA",
            borrower_name="Chính phủ Việt Nam",
            principal_amount=2_000_000_000_000.0,
            interest_rate_pct=1.0,
            tenor_years=30,
            issuance_date_str="2026-01-01",
        )

        with pytest.raises(ValueError, match="vượt quá giá trị hiệp định vay ODA gốc"):
            temp_engine.register_onlending_agreement(
                onlending_code="CVL-ERR-EXCEED",
                parent_debt_code="JICA-ODA-01",
                sub_borrower_name="UBND Tỉnh A",
                project_name="Dự án Cầu B",
                allocated_amount_vnd=3_000_000_000_000.0,
            )

    def test_assess_sovereign_debt_safety_safe(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-SAFE",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=4_000_000_000_000_000.0,  # 4,000 trillion VND
            interest_rate_pct=3.5,
            tenor_years=10,
            issuance_date_str="2026-01-01",
        )

        # GDP = 12,000 trillion VND, Budget Revenue = 2,000 trillion VND
        # Public Debt / GDP = 4,000 / 12,000 = 33.33% (<= 60%)
        # Direct Debt Service = 300 trillion VND / 2,000 trillion = 15.0% (<= 25%)
        res = temp_engine.assess_sovereign_debt_safety(
            fiscal_year=2026,
            gdp_vnd=12_000_000_000_000_000.0,
            budget_revenue_vnd=2_000_000_000_000_000.0,
            national_external_debt_vnd=3_000_000_000_000_000.0,  # 25% of GDP (<= 50%)
            annual_direct_debt_service_vnd=300_000_000_000_000.0,
        )
        assert res["ok"] is True
        assert res["public_debt_gdp_pct"] == 33.33
        assert res["is_ceiling_breached"] is False
        assert res["risk_level"] == "SAFE"
        assert len(res["breaches"]) == 0

    def test_assess_sovereign_debt_safety_breach(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-BREACH",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=8_000_000_000_000_000.0,  # 8,000 trillion VND
            interest_rate_pct=4.0,
            tenor_years=10,
            issuance_date_str="2026-01-01",
        )

        # GDP = 10,000 trillion VND
        # Public Debt / GDP = 8,000 / 10,000 = 80.0% (> 60% RED LINE)
        # Direct Debt Service = 600 trillion / 2,000 trillion = 30% (> 25% RED LINE)
        res = temp_engine.assess_sovereign_debt_safety(
            fiscal_year=2026,
            gdp_vnd=10_000_000_000_000_000.0,
            budget_revenue_vnd=2_000_000_000_000_000.0,
            national_external_debt_vnd=6_000_000_000_000_000.0,  # 60% (> 50%)
            annual_direct_debt_service_vnd=600_000_000_000_000.0,
        )
        assert res["ok"] is True
        assert res["public_debt_gdp_pct"] == 80.0
        assert res["is_ceiling_breached"] is True
        assert res["risk_level"] == "CRITICAL"
        assert len(res["breaches"]) > 0

    def test_list_records(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-LIST-01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=1_000_000_000_000.0,
            interest_rate_pct=3.0,
            tenor_years=5,
            issuance_date_str="2026-01-01",
        )
        temp_engine.schedule_debt_service(
            debt_code="TPCP-LIST-01",
            payment_period="2026-K1",
            due_date_str="2026-07-01",
            principal_due_vnd=0.0,
            interest_due_vnd=15_000_000_000.0,
        )
        temp_engine.register_onlending_agreement(
            onlending_code="CVL-LIST-01",
            parent_debt_code="TPCP-LIST-01",
            sub_borrower_name="UBND TP. Hà Nội",
            project_name="Dự án Cầu Vĩnh Tuy",
            allocated_amount_vnd=500_000_000_000.0,
        )
        temp_engine.assess_sovereign_debt_safety(
            fiscal_year=2026,
            gdp_vnd=10_000_000_000_000_000.0,
            budget_revenue_vnd=2_000_000_000_000_000.0,
        )

        all_res = temp_engine.list_records(category="all")
        assert len(all_res["instruments"]) == 1
        assert len(all_res["schedules"]) == 1
        assert len(all_res["onlending"]) == 1
        assert len(all_res["assessments"]) == 1

    def test_get_telemetry_status(self, temp_engine: PublicDebtEngine) -> None:
        temp_engine.register_debt_instrument(
            debt_code="TPCP-TELEM-01",
            debt_category="GOVERNMENT_DEBT",
            instrument_type="TREASURY_BOND",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=2_000_000_000_000.0,
            interest_rate_pct=3.5,
            tenor_years=5,
            issuance_date_str="2026-01-01",
        )
        temp_engine.schedule_debt_service(
            debt_code="TPCP-TELEM-01",
            payment_period="2026-K1",
            due_date_str="2026-07-01",
            principal_due_vnd=100_000_000_000.0,
            interest_due_vnd=35_000_000_000.0,
        )
        status = temp_engine.get_telemetry_status()
        assert status["ok"] is True
        assert status["status"] == "HEALTHY"
        assert status["instrument_count"] == 1
        assert status["total_public_debt_vnd"] == 2_000_000_000_000.0
        assert status["government_debt_vnd"] == 2_000_000_000_000.0
        assert status["total_debt_service_due_vnd"] == 135_000_000_000.0


# =============================================================================
# 2. Typer CLI Command Surface Tests
# =============================================================================

class TestPublicDebtCli:
    def test_cli_default_callback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        result = runner.invoke(publicdebt_app, [])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ NỢ CÔNG & TÍN NHIỆM QUỐC GIA" in result.output

    def test_cli_status_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        result = runner.invoke(publicdebt_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"

    def test_cli_instrument_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        result = runner.invoke(
            publicdebt_app,
            [
                "instrument",
                "--code", "TPCP-CLI-01",
                "--creditor", "Kho bạc Nhà nước",
                "--borrower", "Chính phủ Việt Nam",
                "--amount", "5000000000000",
                "--rate", "3.75",
                "--tenor", "10",
                "--issue-date", "2026-01-15",
            ],
        )
        assert result.exit_code == 0
        assert "ĐĂNG KÝ CÔNG CỤ NỢ CÔNG THÀNH CÔNG" in result.output
        assert "TPCP-CLI-01" in result.output

    def test_cli_instrument_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        result = runner.invoke(
            publicdebt_app,
            [
                "instrument",
                "--code", "TPCP-CLI-JSON",
                "--creditor", "KBNN",
                "--borrower", "Chính phủ",
                "--amount", "1000000000000",
                "--rate", "3.5",
                "--tenor", "5",
                "--issue-date", "2026-01-15",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["ok"] is True
        assert data["debt_code"] == "TPCP-CLI-JSON"

    def test_cli_schedule_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        runner.invoke(
            publicdebt_app,
            [
                "instrument",
                "--code", "TPCP-CLI-SCHED",
                "--creditor", "KBNN",
                "--borrower", "Chính phủ",
                "--amount", "1000000000000",
                "--rate", "3.0",
                "--tenor", "5",
                "--issue-date", "2026-01-01",
            ],
        )
        result = runner.invoke(
            publicdebt_app,
            [
                "schedule",
                "--code", "TPCP-CLI-SCHED",
                "--period", "2026-K1",
                "--due-date", "2026-07-01",
                "--principal", "50000000000",
                "--interest", "15000000000",
            ],
        )
        assert result.exit_code == 0
        assert "LẬP LỊCH TRÌNH NGHĨA VỤ TRẢ NỢ CÔNG" in result.output
        assert "65,000,000,000 VND" in result.output

    def test_cli_repay_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        runner.invoke(
            publicdebt_app,
            [
                "instrument",
                "--code", "TPCP-CLI-REPAY",
                "--creditor", "KBNN",
                "--borrower", "Chính phủ",
                "--amount", "500000000000",
                "--rate", "3.0",
                "--tenor", "5",
                "--issue-date", "2026-01-01",
            ],
        )
        res_sched = runner.invoke(
            publicdebt_app,
            [
                "schedule",
                "--code", "TPCP-CLI-REPAY",
                "--period", "2026-K1",
                "--due-date", "2026-07-01",
                "--principal", "10000000000",
                "--interest", "5000000000",
                "--json",
            ],
        )
        sched_id = json.loads(res_sched.output)["schedule_id"]

        result = runner.invoke(
            publicdebt_app,
            [
                "repay",
                sched_id,
                "--amount", "15000000000",
            ],
        )
        assert result.exit_code == 0
        assert "XÁC NHẬN THANH TOÁN TRẢ NỢ CÔNG THÀNH CÔNG" in result.output
        assert "PAID" in result.output

    def test_cli_onlend_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        runner.invoke(
            publicdebt_app,
            [
                "instrument",
                "--code", "ODA-CLI-PARENT",
                "--creditor", "World Bank",
                "--borrower", "Chính phủ Việt Nam",
                "--amount", "8000000000000",
                "--rate", "1.5",
                "--tenor", "20",
                "--issue-date", "2026-01-01",
            ],
        )
        result = runner.invoke(
            publicdebt_app,
            [
                "onlend",
                "--code", "CVL-CLI-01",
                "--parent-debt", "ODA-CLI-PARENT",
                "--borrower", "UBND TP. Hà Nội",
                "--project", "Đường sắt đô thị Tuyến số 3",
                "--amount", "3000000000000",
                "--fee", "0.25",
            ],
        )
        assert result.exit_code == 0
        assert "KÝ KẾT HỢP ĐỒNG CHO VAY LẠI VỐN VAY ODA THÀNH CÔNG" in result.output
        assert "CVL-CLI-01" in result.output

    def test_cli_safety_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        result = runner.invoke(
            publicdebt_app,
            [
                "safety",
                "--year", "2026",
                "--gdp", "12000000000000000",
                "--revenue", "2000000000000000",
            ],
        )
        assert result.exit_code == 0
        assert "BÁO CÁO ĐÁNH GIÁ CHỈ TIÊU AN TOÀN NỢ CÔNG QUỐC GIA" in result.output
        assert "Nợ công / GDP" in result.output

    def test_cli_list_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        runner.invoke(
            publicdebt_app,
            [
                "instrument",
                "--code", "TPCP-CLI-LIST",
                "--creditor", "KBNN",
                "--borrower", "Chính phủ",
                "--amount", "1000000000000",
                "--rate", "3.0",
                "--tenor", "5",
                "--issue-date", "2026-01-01",
            ],
        )
        result = runner.invoke(
            publicdebt_app,
            ["list", "--type", "instruments"],
        )
        assert result.exit_code == 0
        assert "TPCP-CLI-LIST" in result.output


# =============================================================================
# 3. MCP Tool Handler Tests (Dual Parity)
# =============================================================================

class TestPublicDebtMcp:
    def test_mcp_standalone_instrument(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        raw = handle_publicdebt_instrument({
            "debt_code": "TPCP-MCP-01",
            "creditor_name": "KBNN",
            "borrower_name": "Chính phủ",
            "principal_amount": 2_000_000_000_000.0,
            "interest_rate_pct": 3.8,
            "tenor_years": 10,
            "issuance_date_str": "2026-01-15",
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["debt_code"] == "TPCP-MCP-01"

    def test_mcp_standalone_instrument_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        raw = handle_publicdebt_instrument({
            "debt_code": "",
            "creditor_name": "KBNN",
            "borrower_name": "Chính phủ",
            "principal_amount": -100.0,
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_schedule(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        handle_publicdebt_instrument({
            "debt_code": "TPCP-MCP-SCHED",
            "creditor_name": "KBNN",
            "borrower_name": "Chính phủ",
            "principal_amount": 1_000_000_000_000.0,
            "interest_rate_pct": 3.0,
            "tenor_years": 5,
            "issuance_date_str": "2026-01-01",
        })
        raw = handle_publicdebt_schedule({
            "debt_code": "TPCP-MCP-SCHED",
            "due_date_str": "2026-07-01",
            "principal_due_vnd": 50_000_000_000.0,
            "interest_due_vnd": 15_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["total_due_vnd"] == 65_000_000_000.0

    def test_mcp_standalone_repay(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        handle_publicdebt_instrument({
            "debt_code": "TPCP-MCP-REPAY",
            "creditor_name": "KBNN",
            "borrower_name": "Chính phủ",
            "principal_amount": 1_000_000_000_000.0,
            "interest_rate_pct": 3.0,
            "tenor_years": 5,
            "issuance_date_str": "2026-01-01",
        })
        sched = json.loads(handle_publicdebt_schedule({
            "debt_code": "TPCP-MCP-REPAY",
            "due_date_str": "2026-07-01",
            "principal_due_vnd": 10_000_000_000.0,
            "interest_due_vnd": 5_000_000_000.0,
        }))
        raw = handle_publicdebt_repay({
            "schedule_id": sched["schedule_id"],
            "paid_amount_vnd": 15_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["status"] == "PAID"

    def test_mcp_standalone_onlend(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        handle_publicdebt_instrument({
            "debt_code": "ODA-MCP-PARENT",
            "creditor_name": "JICA",
            "borrower_name": "Chính phủ",
            "principal_amount": 5_000_000_000_000.0,
            "interest_rate_pct": 1.2,
            "tenor_years": 30,
            "issuance_date_str": "2026-01-01",
        })
        raw = handle_publicdebt_onlend({
            "onlending_code": "CVL-MCP-01",
            "parent_debt_code": "ODA-MCP-PARENT",
            "sub_borrower_name": "UBND TP. Đà Nẵng",
            "project_name": "Cảng Liên Chiểu",
            "allocated_amount_vnd": 2_000_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["onlending_code"] == "CVL-MCP-01"

    def test_mcp_standalone_safety(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        raw = handle_publicdebt_safety({
            "fiscal_year": 2026,
            "gdp_vnd": 12_000_000_000_000_000.0,
            "budget_revenue_vnd": 2_000_000_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is True
        assert "public_debt_gdp_pct" in data

    def test_mcp_standalone_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        raw = handle_publicdebt_list({"category": "all"})
        data = json.loads(raw)
        assert data["ok"] is True
        assert "instruments" in data

    def test_mcp_standalone_status(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        raw = handle_publicdebt_status({})
        data = json.loads(raw)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"

    def test_core_mcp_server_integration(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "server_publicdebt.db"
        monkeypatch.setenv("MEKONG_PUBLICDEBT_DB", str(db_file))

        server = MekongMcpServer()
        app = server.create_app()
        assert app is not None

        # Verify handlers callable via server instance
        res_inst = server._handle_publicdebt_instrument(
            debt_code="TPCP-SERVER-01",
            creditor_name="KBNN",
            borrower_name="Chính phủ",
            principal_amount=1_000_000_000_000.0,
            interest_rate_pct=3.5,
            tenor_years=5,
            issuance_date_str="2026-01-01",
        )
        data_inst = json.loads(res_inst)
        assert data_inst["ok"] is True

        res_st = server._handle_publicdebt_status()
        data_st = json.loads(res_st)
        assert data_st["ok"] is True
        assert data_st["instrument_count"] == 1


# =============================================================================
# 4. Edge Cases & Statutory Public Debt Rules
# =============================================================================

class TestPublicDebtEdgeCases:
    def test_all_debt_categories(self, temp_engine: PublicDebtEngine) -> None:
        for idx, cat in enumerate(["GOVERNMENT_DEBT", "GOVERNMENT_GUARANTEED_DEBT", "LOCAL_GOVERNMENT_DEBT"]):
            code = f"DEBT-CAT-{idx:02d}"
            res = temp_engine.register_debt_instrument(
                debt_code=code,
                debt_category=cat,
                instrument_type="TREASURY_BOND" if cat == "GOVERNMENT_DEBT" else ("POLICY_BANK_BOND" if cat == "GOVERNMENT_GUARANTEED_DEBT" else "MUNICIPAL_BOND"),
                creditor_name="Creditor",
                borrower_name="Borrower",
                principal_amount=500_000_000.0,
                interest_rate_pct=3.0,
                tenor_years=5,
                issuance_date_str="2026-01-01",
            )
            assert res["debt_category"] == cat

    def test_multi_currency_conversions(self, temp_engine: PublicDebtEngine) -> None:
        currencies = [
            ("USD", 25_400.0),
            ("EUR", 27_800.0),
            ("JPY", 168.0),
        ]
        for cur, rate in currencies:
            code = f"LOAN-{cur}"
            res = temp_engine.register_debt_instrument(
                debt_code=code,
                debt_category="GOVERNMENT_DEBT",
                instrument_type="ODA_LOAN",
                creditor_name="Foreign Lender",
                borrower_name="Chính phủ",
                principal_amount=1_000_000.0,
                original_currency=cur,
                fx_rate_to_vnd=rate,
                interest_rate_pct=1.5,
                tenor_years=15,
                issuance_date_str="2026-01-01",
            )
            assert res["principal_vnd"] == 1_000_000.0 * rate
