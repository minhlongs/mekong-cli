"""
Comprehensive test battery for Vietnamese Public Investment, Capital Allocation,
Feasibility & Medium-Term Planning Suite (Phase 118).
Validates statutory adherence to:
- Law on Public Investment 2019 (Law No. 39/2019/QH14 & Law 03/2022/QH15, Law 29/2023/QH15)
- Decree No. 40/2020/ND-CP (Guidance on Public Investment Law implementation)
- Decree No. 99/2021/ND-CP (State Treasury Capital Disbursement Management)
- Circular No. 12/2022/TT-BKHDT (Reporting and Assessment of Public Investment Projects)
"""

import json
import pytest
from pathlib import Path
from typer.testing import CliRunner
from src.core.pubinvestment_engine import PublicInvestmentEngine
from src.cli.commands.pubinvestment_command import pubinvestment_app
from scripts.mcp_server import (
    handle_pubinvestment_project,
    handle_pubinvestment_classify,
    handle_pubinvestment_plan,
    handle_pubinvestment_disburse,
    handle_pubinvestment_bottleneck,
    handle_pubinvestment_list,
    handle_pubinvestment_status,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


@pytest.fixture
def temp_engine(tmp_path: Path) -> PublicInvestmentEngine:
    db_file = tmp_path / "test_pubinvestment.db"
    return PublicInvestmentEngine(db_path=str(db_file))


# =============================================================================
# 1. Core Engine Tests
# =============================================================================

class TestPubInvestmentEngine:
    def test_register_project_valid(self, temp_engine: PublicInvestmentEngine) -> None:
        res = temp_engine.register_project(
            project_code="DA-CAOTOC-NB26",
            project_name="Dự án Cao tốc Bắc Nam phía Đông giai đoạn 2026-2030",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=15_000_000_000_000.0,  # 15,000 billion VND -> National Special
            capital_source="CENTRAL_BUDGET",
            managing_agency="Bộ Giao thông Vận tải",
            implementation_location="Ninh Bình - Thanh Hóa",
            start_year=2026,
            end_year=2030,
            resettlement_people=25000,
            is_nationally_sensitive=True,
        )
        assert res["project_id"].startswith("PRJ-")
        assert res["project_code"] == "DA-CAOTOC-NB26"
        assert res["project_name"] == "Dự án Cao tốc Bắc Nam phía Đông giai đoạn 2026-2030"
        assert res["classification"] == "NATIONAL_SPECIAL"
        assert "Quốc hội" in res["competent_authority"]
        assert res["total_investment_vnd"] == 15_000_000_000_000.0
        assert res["status"] == "APPROVED"

    def test_register_duplicate_project_code(self, temp_engine: PublicInvestmentEngine) -> None:
        temp_engine.register_project(
            project_code="DA-DUP-01",
            project_name="Dự án Test Trùng Lặp 1",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=50_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2028,
        )
        with pytest.raises(Exception):
            temp_engine.register_project(
                project_code="DA-DUP-01",
                project_name="Dự án Test Trùng Lặp 2",
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=60_000_000_000.0,
                capital_source="CENTRAL_BUDGET",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2026,
                end_year=2028,
            )

    def test_register_project_invalid_inputs(self, temp_engine: PublicInvestmentEngine) -> None:
        with pytest.raises(ValueError, match="Project code cannot be empty"):
            temp_engine.register_project(
                project_code="",
                project_name="Dự án thiếu mã",
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=100_000_000_000.0,
                capital_source="CENTRAL_BUDGET",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2026,
                end_year=2030,
            )

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            temp_engine.register_project(
                project_code="DA-INVALID-01",
                project_name="",
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=100_000_000_000.0,
                capital_source="CENTRAL_BUDGET",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2026,
                end_year=2030,
            )

        with pytest.raises(ValueError, match="Total investment capital cannot be negative"):
            temp_engine.register_project(
                project_code="DA-INVALID-02",
                project_name="Dự án âm tiền",
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=-100.0,
                capital_source="CENTRAL_BUDGET",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2026,
                end_year=2030,
            )

        with pytest.raises(ValueError, match="Start year cannot be after end year"):
            temp_engine.register_project(
                project_code="DA-INVALID-03",
                project_name="Dự án nghịch lý thời gian",
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=100_000_000_000.0,
                capital_source="CENTRAL_BUDGET",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2030,
                end_year=2025,
            )

        with pytest.raises(ValueError, match="Invalid sector"):
            temp_engine.register_project(
                project_code="DA-INVALID-04",
                project_name="Dự án sai lĩnh vực",
                sector="UNKNOWN_SECTOR",
                total_investment_vnd=100_000_000_000.0,
                capital_source="CENTRAL_BUDGET",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2026,
                end_year=2030,
            )

        with pytest.raises(ValueError, match="Invalid capital source"):
            temp_engine.register_project(
                project_code="DA-INVALID-05",
                project_name="Dự án sai nguồn vốn",
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=100_000_000_000.0,
                capital_source="CRYPTOCURRENCY",
                managing_agency="Ban QLDA",
                implementation_location="Hà Nội",
                start_year=2026,
                end_year=2030,
            )

    def test_classify_project_national_special(self) -> None:
        # Capital >= 10,000 billion VND
        c1 = PublicInvestmentEngine.classify_project(
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=10_000_000_000_000.0,
        )
        assert c1["classification"] == "NATIONAL_SPECIAL"
        assert "Quốc hội" in c1["competent_deciding_authority"]

        # Resettlement >= 20,000 people
        c2 = PublicInvestmentEngine.classify_project(
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=500_000_000_000.0,
            resettlement_people=20000,
        )
        assert c2["classification"] == "NATIONAL_SPECIAL"

        # Sensitive defense / security
        c3 = PublicInvestmentEngine.classify_project(
            sector="OTHER_INFRASTRUCTURE",
            total_investment_vnd=100_000_000_000.0,
            is_nationally_sensitive=True,
        )
        assert c3["classification"] == "NATIONAL_SPECIAL"

    def test_classify_project_group_a(self) -> None:
        # Transport >= 2,300 billion VND
        c1 = PublicInvestmentEngine.classify_project(
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=2_500_000_000_000.0,
        )
        assert c1["classification"] == "GROUP_A"
        assert "Thủ tướng Chính phủ" in c1["competent_deciding_authority"]

        # Agriculture >= 1,500 billion VND
        c2 = PublicInvestmentEngine.classify_project(
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=1_600_000_000_000.0,
        )
        assert c2["classification"] == "GROUP_A"

        # Health / Education >= 1,000 billion VND
        c3 = PublicInvestmentEngine.classify_project(
            sector="HEALTH_EDUCATION_CULTURE",
            total_investment_vnd=1_100_000_000_000.0,
        )
        assert c3["classification"] == "GROUP_A"

    def test_classify_project_group_b(self) -> None:
        # Transport between 120B and 2,300B
        c1 = PublicInvestmentEngine.classify_project(
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=500_000_000_000.0,
        )
        assert c1["classification"] == "GROUP_B"
        assert "HĐND cấp tỉnh" in c1["competent_deciding_authority"]

        # Agriculture between 80B and 1,500B
        c2 = PublicInvestmentEngine.classify_project(
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=100_000_000_000.0,
        )
        assert c2["classification"] == "GROUP_B"

        # Health / Education between 60B and 1,000B
        c3 = PublicInvestmentEngine.classify_project(
            sector="HEALTH_EDUCATION_CULTURE",
            total_investment_vnd=80_000_000_000.0,
        )
        assert c3["classification"] == "GROUP_B"

    def test_classify_project_group_c(self) -> None:
        # Transport < 120B
        c1 = PublicInvestmentEngine.classify_project(
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=80_000_000_000.0,
        )
        assert c1["classification"] == "GROUP_C"
        assert "Chủ tịch UBND cấp tỉnh" in c1["approving_authority"]

        # Agriculture < 80B
        c2 = PublicInvestmentEngine.classify_project(
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=50_000_000_000.0,
        )
        assert c2["classification"] == "GROUP_C"

        # Health / Education < 60B
        c3 = PublicInvestmentEngine.classify_project(
            sector="HEALTH_EDUCATION_CULTURE",
            total_investment_vnd=30_000_000_000.0,
        )
        assert c3["classification"] == "GROUP_C"

    def test_allocate_capital_plan_valid(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-CAU-01",
            project_name="Dự án Cầu Vượt Đô Thị",
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=600_000_000_000.0,
            capital_source="LOCAL_BUDGET",
            managing_agency="Ban QLDA Đầu tư Xây dựng Công trình Giao thông",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2028,
        )
        plan = temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=150_000_000_000.0,
            approved_by="UBND TP. Hà Nội",
            decision_number="QĐ-UBND-2026-01",
            priority_tier=4,
        )
        assert plan["plan_id"].startswith("PLN-")
        assert plan["fiscal_year"] == 2026
        assert plan["allocated_capital_vnd"] == 150_000_000_000.0
        assert plan["priority_tier"] == 4
        assert "Dự án chuyển tiếp" in plan["priority_description"]

    def test_allocate_capital_plan_medium_term(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-MT-01",
            project_name="Dự án Trung hạn 5 năm Bệnh viện Tỉnh",
            sector="HEALTH_EDUCATION_CULTURE",
            total_investment_vnd=800_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Sở Y tế",
            implementation_location="Quảng Nam",
            start_year=2026,
            end_year=2030,
        )
        plan = temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="MEDIUM_TERM",
            fiscal_year=2026,
            allocated_capital_vnd=800_000_000_000.0,
            approved_by="Thủ tướng Chính phủ",
            decision_number="QĐ-TTg-2026-MT",
            priority_tier=5,
        )
        assert plan["plan_type"] == "MEDIUM_TERM"
        assert plan["priority_tier"] == 5
        assert "khởi công mới" in plan["priority_description"]

    def test_allocate_capital_plan_invalid(self, temp_engine: PublicInvestmentEngine) -> None:
        with pytest.raises(KeyError, match="not found"):
            temp_engine.allocate_capital_plan(
                project_id="NON_EXISTENT_ID",
                plan_type="ANNUAL",
                fiscal_year=2026,
                allocated_capital_vnd=50_000_000_000.0,
                approved_by="Bộ GTVT",
                decision_number="QĐ-01",
            )

        proj = temp_engine.register_project(
            project_code="DA-ERR-PLAN",
            project_name="Dự án lỗi vốn",
            sector="OTHER_INFRASTRUCTURE",
            total_investment_vnd=200_000_000_000.0,
            capital_source="LOCAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Đà Nẵng",
            start_year=2026,
            end_year=2028,
        )

        with pytest.raises(ValueError, match="Allocated capital must be greater than zero"):
            temp_engine.allocate_capital_plan(
                project_id=proj["project_id"],
                plan_type="ANNUAL",
                fiscal_year=2026,
                allocated_capital_vnd=0.0,
                approved_by="UBND",
                decision_number="QĐ-02",
            )

        with pytest.raises(ValueError, match="Priority tier must be between 1 and 5"):
            temp_engine.allocate_capital_plan(
                project_id=proj["project_id"],
                plan_type="ANNUAL",
                fiscal_year=2026,
                allocated_capital_vnd=10_000_000_000.0,
                approved_by="UBND",
                decision_number="QĐ-03",
                priority_tier=99,
            )

    def test_record_disbursement_valid(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-DISB-01",
            project_name="Dự án Xây dựng Trường THPT Chuẩn",
            sector="HEALTH_EDUCATION_CULTURE",
            total_investment_vnd=100_000_000_000.0,
            capital_source="LOCAL_BUDGET",
            managing_agency="Ban QLDA ĐTXD",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2027,
        )
        temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=50_000_000_000.0,
            approved_by="UBND TP. Hà Nội",
            decision_number="QĐ-2026-PLAN",
        )
        disb = temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=20_000_000_000.0,
            treasury_office="Kho bạc Nhà nước Cầu Giấy",
            payment_voucher_number="VOUCHER-2026-001",
            recipient_contractor="Tổng công ty Xây dựng Thăng Long",
            notes="Tạm ứng đợt 1 theo hợp đồng",
        )
        assert disb["disbursement_id"].startswith("DIS-")
        assert disb["disbursed_amount_vnd"] == 20_000_000_000.0
        assert disb["total_disbursed_year_vnd"] == 20_000_000_000.0
        assert disb["allocated_capital_year_vnd"] == 50_000_000_000.0
        assert disb["disbursement_rate_pct"] == 40.0

        # Second disbursement
        disb2 = temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=15_000_000_000.0,
            treasury_office="Kho bạc Nhà nước Cầu Giấy",
            payment_voucher_number="VOUCHER-2026-002",
            recipient_contractor="Tổng công ty Xây dựng Thăng Long",
            notes="Nghiệm thu thanh toán khối lượng đợt 2",
        )
        assert disb2["total_disbursed_year_vnd"] == 35_000_000_000.0
        assert disb2["disbursement_rate_pct"] == 70.0

    def test_record_disbursement_exceed_allocation(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-DISB-EXCEED",
            project_name="Dự án Giải ngân Vượt Kế hoạch",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=100_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2027,
        )
        temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=30_000_000_000.0,
            approved_by="Bộ GTVT",
            decision_number="QĐ-EXCEED",
        )
        with pytest.raises(ValueError, match="exceeds annual capital allocation"):
            temp_engine.record_disbursement(
                project_id=proj["project_id"],
                fiscal_year=2026,
                disbursed_amount_vnd=35_000_000_000.0,
                treasury_office="Kho bạc Nhà nước",
                payment_voucher_number="VOUCHER-EXCEED",
                recipient_contractor="Nhà thầu",
            )

    def test_record_disbursement_invalid_inputs(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-DISB-INVALID",
            project_name="Dự án Kiểm tra Dữ liệu Rút vốn",
            sector="OTHER_INFRASTRUCTURE",
            total_investment_vnd=100_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2027,
        )
        temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=50_000_000_000.0,
            approved_by="Bộ GTVT",
            decision_number="QĐ-INV",
        )
        with pytest.raises(ValueError, match="Disbursed amount must be greater than zero"):
            temp_engine.record_disbursement(
                project_id=proj["project_id"],
                fiscal_year=2026,
                disbursed_amount_vnd=-5_000_000.0,
                treasury_office="Kho bạc Nhà nước",
                payment_voucher_number="VOUCHER-NEG",
                recipient_contractor="Nhà thầu",
            )

        with pytest.raises(ValueError, match="Payment voucher number cannot be empty"):
            temp_engine.record_disbursement(
                project_id=proj["project_id"],
                fiscal_year=2026,
                disbursed_amount_vnd=5_000_000.0,
                treasury_office="Kho bạc Nhà nước",
                payment_voucher_number="",
                recipient_contractor="Nhà thầu",
            )

        with pytest.raises(ValueError, match="Recipient contractor cannot be empty"):
            temp_engine.record_disbursement(
                project_id=proj["project_id"],
                fiscal_year=2026,
                disbursed_amount_vnd=5_000_000.0,
                treasury_office="Kho bạc Nhà nước",
                payment_voucher_number="VOUCHER-01",
                recipient_contractor="",
            )

    def test_assess_bottleneck_valid(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-BOTTLE-01",
            project_name="Dự án Cải tạo Kênh Thoát Nước",
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=300_000_000_000.0,
            capital_source="LOCAL_BUDGET",
            managing_agency="Sở Xây dựng",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2028,
        )
        bn = temp_engine.assess_bottleneck(
            project_id=proj["project_id"],
            bottleneck_type="LAND_CLEARANCE",
            severity_level="CRITICAL",
            estimated_delay_months=9,
            mitigation_measures="Đẩy nhanh cưỡng chế thu hồi đất và giải quyết khiếu nại bồi thường",
            responsible_party="UBND Quận Hoàng Mai",
        )
        assert bn["assessment_id"].startswith("BTN-")
        assert bn["bottleneck_type"] == "LAND_CLEARANCE"
        assert bn["severity_level"] == "CRITICAL"
        assert bn["estimated_delay_months"] == 9
        assert "thu hồi đất" in bn["mitigation_measures"]

    def test_assess_bottleneck_invalid(self, temp_engine: PublicInvestmentEngine) -> None:
        with pytest.raises(KeyError, match="not found"):
            temp_engine.assess_bottleneck(
                project_id="NON_EXISTENT_ID",
                bottleneck_type="BIDDING_PROCEDURE",
                severity_level="HIGH",
                estimated_delay_months=6,
                mitigation_measures="Tháo gỡ",
                responsible_party="Sở KHĐT",
            )

        proj = temp_engine.register_project(
            project_code="DA-BN-ERR",
            project_name="Dự án Điểm Nghẽn Lỗi",
            sector="OTHER_INFRASTRUCTURE",
            total_investment_vnd=100_000_000_000.0,
            capital_source="LOCAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hải Phòng",
            start_year=2026,
            end_year=2028,
        )
        with pytest.raises(ValueError, match="Estimated delay months cannot be negative"):
            temp_engine.assess_bottleneck(
                project_id=proj["project_id"],
                bottleneck_type="BIDDING_PROCEDURE",
                severity_level="HIGH",
                estimated_delay_months=-3,
                mitigation_measures="Tháo gỡ",
                responsible_party="Ban QLDA",
            )

        with pytest.raises(ValueError, match="Mitigation measures cannot be empty"):
            temp_engine.assess_bottleneck(
                project_id=proj["project_id"],
                bottleneck_type="BIDDING_PROCEDURE",
                severity_level="HIGH",
                estimated_delay_months=3,
                mitigation_measures="",
                responsible_party="Ban QLDA",
            )

    def test_list_records(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-LIST-01",
            project_name="Dự án Kiểm tra Danh sách",
            sector="OTHER_INFRASTRUCTURE",
            total_investment_vnd=120_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Bộ TT&TT",
            implementation_location="Toàn quốc",
            start_year=2026,
            end_year=2028,
        )
        plan = temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=40_000_000_000.0,
            approved_by="Bộ TT&TT",
            decision_number="QĐ-2026-TTTT",
        )
        disb = temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=10_000_000_000.0,
            treasury_office="Kho bạc Nhà nước Hà Nội",
            payment_voucher_number="V-01",
            recipient_contractor="Công ty CNTT",
        )
        bn = temp_engine.assess_bottleneck(
            project_id=proj["project_id"],
            bottleneck_type="BIDDING_PROCEDURE",
            severity_level="MEDIUM",
            estimated_delay_months=2,
            mitigation_measures="Đấu thầu qua mạng hệ thống Quốc gia",
            responsible_party="Tổ chuyên gia",
        )

        all_res = temp_engine.list_records(category="all")
        assert len(all_res["projects"]) == 1
        assert len(all_res["plans"]) == 1
        assert len(all_res["disbursements"]) == 1
        assert len(all_res["bottlenecks"]) == 1

        proj_res = temp_engine.list_records(category="projects")
        assert len(proj_res["projects"]) == 1

        plan_res = temp_engine.list_records(category="plans")
        assert len(plan_res["plans"]) == 1

        disb_res = temp_engine.list_records(category="disbursements")
        assert len(disb_res["disbursements"]) == 1

        bn_res = temp_engine.list_records(category="bottlenecks")
        assert len(bn_res["bottlenecks"]) == 1

    def test_get_telemetry_status(self, temp_engine: PublicInvestmentEngine) -> None:
        status_empty = temp_engine.get_telemetry_status()
        assert status_empty["status"] == "HEALTHY"
        assert status_empty["projects"]["total"] == 0
        assert status_empty["capital_and_disbursement"]["national_disbursement_rate_pct"] == 0.0

        proj = temp_engine.register_project(
            project_code="DA-TELEMETRY-01",
            project_name="Dự án Telemetry Đo Lường",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=200_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Bộ GTVT",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2028,
        )
        temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=100_000_000_000.0,
            approved_by="Thủ tướng Chính phủ",
            decision_number="QĐ-TELEM",
        )
        temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=65_000_000_000.0,
            treasury_office="Kho bạc Nhà nước TP. Hà Nội",
            payment_voucher_number="V-TELEM-01",
            recipient_contractor="Nhà thầu A",
        )
        temp_engine.assess_bottleneck(
            project_id=proj["project_id"],
            bottleneck_type="MATERIAL_PRICE_SPIKE",
            severity_level="CRITICAL",
            estimated_delay_months=5,
            mitigation_measures="Điều chỉnh bù giá vật liệu theo chỉ số giá XD của Sở Xây dựng",
            responsible_party="Sở Xây dựng",
        )

        status = temp_engine.get_telemetry_status()
        assert status["projects"]["total"] == 1
        assert status["capital_and_disbursement"]["total_annual_allocated_vnd"] == 100_000_000_000.0
        assert status["capital_and_disbursement"]["total_disbursed_vnd"] == 65_000_000_000.0
        assert status["capital_and_disbursement"]["national_disbursement_rate_pct"] == 65.0
        assert status["bottlenecks"]["total_reported"] == 1
        assert status["bottlenecks"]["critical_unresolved"] == 1
        assert "39/2019/QH14" in status["regulatory_framework"]["law"]


# =============================================================================
# 2. CLI Command Tests
# =============================================================================

class TestPubInvestmentCli:
    def test_cli_classify_command(self) -> None:
        result = runner.invoke(
            pubinvestment_app,
            [
                "classify",
                "--sector", "TRANSPORT_ENERGY_INDUSTRY",
                "--capital", "3000000000000",
            ],
        )
        assert result.exit_code == 0
        assert "KẾT QUẢ PHÂN LOẠI DỰ ÁN ĐẦU TƯ CÔNG" in result.output
        assert "GROUP_A" in result.output

    def test_cli_classify_json(self) -> None:
        result = runner.invoke(
            pubinvestment_app,
            [
                "classify",
                "--sector", "HEALTH_EDUCATION_CULTURE",
                "--capital", "50000000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["classification"] == "GROUP_C"

    def test_cli_project_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        result = runner.invoke(
            pubinvestment_app,
            [
                "project",
                "--code", "DA-CLI-01",
                "--name", "Dự án Nâng cấp Đường Vành đai 4",
                "--sector", "TRANSPORT_ENERGY_INDUSTRY",
                "--capital", "12000000000000",
                "--agency", "Ban QLDA Giao thông",
                "--location", "Hà Nội - Hưng Yên - Bắc Ninh",
            ],
        )
        assert result.exit_code == 0
        assert "ĐĂNG KÝ DỰ ÁN ĐẦU TƯ CÔNG THÀNH CÔNG" in result.output
        assert "DA-CLI-01" in result.output

    def test_cli_project_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        result = runner.invoke(
            pubinvestment_app,
            [
                "project",
                "--code", "DA-CLI-JSON",
                "--name", "Dự án Xây dựng Trường Đại học Mới",
                "--sector", "HEALTH_EDUCATION_CULTURE",
                "--capital", "1500000000000",
                "--agency", "Bộ GD&ĐT",
                "--location", "Hà Nội",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["project_code"] == "DA-CLI-JSON"
        assert data["classification"] == "GROUP_A"

    def test_cli_plan_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        # Register first
        reg_res = runner.invoke(
            pubinvestment_app,
            [
                "project",
                "--code", "DA-CLI-PLAN",
                "--name", "Dự án Bệnh viện Nhi Trung ương cơ sở 2",
                "--sector", "HEALTH_EDUCATION_CULTURE",
                "--capital", "2000000000000",
                "--agency", "Bộ Y tế",
                "--location", "Hà Nội",
                "--json",
            ],
        )
        proj_id = json.loads(reg_res.output)["project_id"]

        # Allocate plan
        result = runner.invoke(
            pubinvestment_app,
            [
                "plan",
                proj_id,
                "--year", "2026",
                "--capital", "500000000000",
                "--priority", "4",
            ],
        )
        assert result.exit_code == 0
        assert "PHÂN BỔ KẾ HOẠCH VỐN ĐẦU TƯ CÔNG THÀNH CÔNG" in result.output

    def test_cli_disburse_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        reg_res = runner.invoke(
            pubinvestment_app,
            [
                "project",
                "--code", "DA-CLI-DISB",
                "--name", "Dự án Cải tạo Hạ tầng Thủy lợi",
                "--sector", "AGRICULTURE_IRRIGATION_URBAN",
                "--capital", "100000000000",
                "--agency", "Bộ Nông nghiệp",
                "--location", "Nam Định",
                "--json",
            ],
        )
        proj_id = json.loads(reg_res.output)["project_id"]

        runner.invoke(
            pubinvestment_app,
            [
                "plan",
                proj_id,
                "--year", "2026",
                "--capital", "40000000000",
            ],
        )
        result = runner.invoke(
            pubinvestment_app,
            [
                "disburse",
                proj_id,
                "--voucher", "RUT-VON-2026-001",
                "--contractor", "Công ty Xây dựng Thủy lợi",
                "--amount", "15000000000",
                "--year", "2026",
            ],
        )
        assert result.exit_code == 0
        assert "GHI NHẬN GIẢI NGÂN VỐN KHO BẠC NHÀ NƯỚC THÀNH CÔNG" in result.output
        assert "37.5%" in result.output

    def test_cli_bottleneck_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        reg_res = runner.invoke(
            pubinvestment_app,
            [
                "project",
                "--code", "DA-CLI-BN",
                "--name", "Dự án Tuyến Đường sắt Đô thị",
                "--sector", "TRANSPORT_ENERGY_INDUSTRY",
                "--capital", "20000000000000",
                "--agency", "UBND Thành phố",
                "--location", "Hà Nội",
                "--json",
            ],
        )
        proj_id = json.loads(reg_res.output)["project_id"]

        result = runner.invoke(
            pubinvestment_app,
            [
                "bottleneck",
                proj_id,
                "--type", "LAND_CLEARANCE",
                "--severity", "CRITICAL",
                "--delay", "12",
                "--measures", "Báo cáo Thủ tướng Chính phủ và Ban Chỉ đạo Quốc gia",
                "--party", "UBND Thành phố",
            ],
        )
        assert result.exit_code == 0
        assert "GHI NHẬN ĐIỂM NGHẼN TIẾN ĐỘ DỰ ÁN ĐẦU TƯ CÔNG" in result.output
        assert "CRITICAL" in result.output

    def test_cli_list_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        runner.invoke(
            pubinvestment_app,
            [
                "project",
                "--code", "DA-CLI-LIST",
                "--name", "Dự án Thí điểm List",
                "--sector", "OTHER_INFRASTRUCTURE",
                "--capital", "50000000000",
                "--agency", "Sở KHĐT",
                "--location", "Hà Nội",
            ],
        )
        result = runner.invoke(
            pubinvestment_app,
            ["list", "--type", "projects"],
        )
        assert result.exit_code == 0
        assert "DA-CLI-LIST" in result.output

    def test_cli_status_command(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        result = runner.invoke(
            pubinvestment_app,
            ["status"],
        )
        assert result.exit_code == 0
        assert "Public Investment Subsystem Status" in result.output

    def test_cli_status_json(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        result = runner.invoke(
            pubinvestment_app,
            ["status", "--json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "HEALTHY"
        assert "regulatory_framework" in data


# =============================================================================
# 3. MCP Tool Handler Tests (Dual Parity)
# =============================================================================

class TestPubInvestmentMcp:
    def test_mcp_standalone_classify(self) -> None:
        raw = handle_pubinvestment_classify({
            "sector": "TRANSPORT_ENERGY_INDUSTRY",
            "total_investment_vnd": 3_000_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["classification"] == "GROUP_A"
        assert "Thủ tướng Chính phủ" in data["competent_deciding_authority"]

    def test_mcp_standalone_project(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_project({
            "project_code": "DA-MCP-01",
            "project_name": "Dự án Nâng cấp Cảng Hàng không Chu Lai",
            "sector": "TRANSPORT_ENERGY_INDUSTRY",
            "total_investment_vnd": 11_000_000_000_000.0,
            "resettlement_people": 5000,
        })
        data = json.loads(raw)
        assert data["project_code"] == "DA-MCP-01"
        assert data["classification"] == "NATIONAL_SPECIAL"

    def test_mcp_standalone_project_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_project({
            "project_code": "",
            "project_name": "Dự án thiếu mã",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_plan(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        # Register first
        reg_raw = handle_pubinvestment_project({
            "project_code": "DA-MCP-PLAN",
            "project_name": "Dự án MCP Plan",
            "sector": "TRANSPORT_ENERGY_INDUSTRY",
            "total_investment_vnd": 100_000_000_000.0,
        })
        proj_id = json.loads(reg_raw)["project_id"]

        raw = handle_pubinvestment_plan({
            "project_id": proj_id,
            "plan_type": "ANNUAL",
            "fiscal_year": 2026,
            "allocated_capital_vnd": 30_000_000_000.0,
            "priority_tier": 3,
        })
        data = json.loads(raw)
        assert data["priority_tier"] == 3
        assert "ODA" in data["priority_description"]

    def test_mcp_standalone_plan_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_plan({
            "project_id": "NON_EXISTENT_PROJECT",
            "allocated_capital_vnd": 10_000_000_000.0,
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_disburse(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        reg_raw = handle_pubinvestment_project({
            "project_code": "DA-MCP-DISB",
            "project_name": "Dự án MCP Disburse",
            "sector": "TRANSPORT_ENERGY_INDUSTRY",
            "total_investment_vnd": 50_000_000_000.0,
        })
        proj_id = json.loads(reg_raw)["project_id"]

        handle_pubinvestment_plan({
            "project_id": proj_id,
            "fiscal_year": 2026,
            "allocated_capital_vnd": 20_000_000_000.0,
        })
        raw = handle_pubinvestment_disburse({
            "project_id": proj_id,
            "fiscal_year": 2026,
            "disbursed_amount_vnd": 10_000_000_000.0,
            "payment_voucher_number": "MCP-VOUCHER-01",
            "recipient_contractor": "Nhà thầu MCP",
        })
        data = json.loads(raw)
        assert data["disbursement_rate_pct"] == 50.0

    def test_mcp_standalone_disburse_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_disburse({
            "project_id": "NON_EXISTENT_PROJECT",
            "payment_voucher_number": "ERR-VOUCHER",
            "recipient_contractor": "Nhà thầu",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data

    def test_mcp_standalone_bottleneck(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        reg_raw = handle_pubinvestment_project({
            "project_code": "DA-MCP-BN",
            "project_name": "Dự án MCP Bottleneck",
            "sector": "TRANSPORT_ENERGY_INDUSTRY",
            "total_investment_vnd": 100_000_000_000.0,
        })
        proj_id = json.loads(reg_raw)["project_id"]

        raw = handle_pubinvestment_bottleneck({
            "project_id": proj_id,
            "bottleneck_type": "BIDDING_PROCEDURE",
            "severity_level": "HIGH",
            "estimated_delay_months": 4,
            "mitigation_measures": "Hủy thầu và tổ chức đấu thầu rộng rãi qua mạng",
            "responsible_party": "Tổ chuyên gia đấu thầu",
        })
        data = json.loads(raw)
        assert data["bottleneck_type"] == "BIDDING_PROCEDURE"

    def test_mcp_standalone_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_list({"category": "all"})
        data = json.loads(raw)
        assert "projects" in data
        assert "plans" in data

    def test_mcp_standalone_status(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_status({})
        data = json.loads(raw)
        assert data["status"] == "HEALTHY"
        assert "regulatory_framework" in data

    def test_core_mcp_server_integration(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_core_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        server = MekongMcpServer()

        # Test project tool
        proj_raw = server._handle_pubinvestment_project(
            project_code="DA-CORE-MCP-01",
            project_name="Dự án Cốt lõi MCP Server",
            sector="OTHER_INFRASTRUCTURE",
            total_investment_vnd=50_000_000_000.0,
            managing_agency="Ban QLDA Core",
            implementation_location="Hà Nội",
        )
        proj_data = json.loads(proj_raw)
        assert proj_data["classification"] == "GROUP_B"
        proj_id = proj_data["project_id"]

        # Test classify tool
        class_raw = server._handle_pubinvestment_classify(
            sector="AGRICULTURE_IRRIGATION_URBAN",
            total_investment_vnd=2_000_000_000_000.0,
        )
        class_data = json.loads(class_raw)
        assert class_data["classification"] == "GROUP_A"

        # Test plan tool
        plan_raw = server._handle_pubinvestment_plan(
            project_id=proj_id,
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=20_000_000_000.0,
            priority_tier=1,
        )
        plan_data = json.loads(plan_raw)
        assert plan_data["priority_tier"] == 1

        # Test disburse tool
        disb_raw = server._handle_pubinvestment_disburse(
            project_id=proj_id,
            fiscal_year=2026,
            disbursed_amount_vnd=10_000_000_000.0,
            payment_voucher_number="VOUCHER-CORE-01",
            recipient_contractor="Nhà thầu Core",
        )
        disb_data = json.loads(disb_raw)
        assert disb_data["disbursement_rate_pct"] == 50.0

        # Test bottleneck tool
        bn_raw = server._handle_pubinvestment_bottleneck(
            project_id=proj_id,
            bottleneck_type="ENVIRONMENT_PERMIT",
            severity_level="MEDIUM",
            estimated_delay_months=2,
            mitigation_measures="Hoàn tất ĐTM trình Bộ Tài nguyên và Môi trường",
        )
        bn_data = json.loads(bn_raw)
        assert bn_data["bottleneck_type"] == "ENVIRONMENT_PERMIT"

        # Test list tool
        list_raw = server._handle_pubinvestment_list(category="all")
        list_data = json.loads(list_raw)
        assert len(list_data["projects"]) == 1

        # Test status tool
        status_raw = server._handle_pubinvestment_status()
        status_data = json.loads(status_raw)
        assert status_data["status"] == "HEALTHY"
        assert status_data["projects"]["total"] == 1
        assert status_data["capital_and_disbursement"]["national_disbursement_rate_pct"] == 50.0

    def test_mcp_standalone_bottleneck_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "mcp_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        raw = handle_pubinvestment_bottleneck({
            "project_id": "NON_EXISTENT_ID",
            "bottleneck_type": "LAND_CLEARANCE",
            "mitigation_measures": "Tháo gỡ",
            "responsible_party": "UBND",
        })
        data = json.loads(raw)
        assert data["ok"] is False
        assert "error" in data


# =============================================================================
# 4. In-Depth Boundary & Edge Case Tests
# =============================================================================

class TestPubInvestmentEdgeCases:
    def test_allocate_all_priority_tiers(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-TIERS-01",
            project_name="Dự án Thử nghiệm 5 Bậc Ưu tiên",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=500_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2030,
        )
        for tier in (1, 2, 3, 4, 5):
            plan = temp_engine.allocate_capital_plan(
                project_id=proj["project_id"],
                plan_type="ANNUAL",
                fiscal_year=2026,
                allocated_capital_vnd=10_000_000_000.0,
                approved_by="Thủ tướng Chính phủ",
                decision_number=f"QĐ-TIER-{tier}",
                priority_tier=tier,
            )
            assert plan["priority_tier"] == tier
            assert f"Bậc {tier} Điều 51" in plan["priority_description"]

    def test_classify_project_invalid_sector(self) -> None:
        with pytest.raises(ValueError, match="Invalid sector"):
            PublicInvestmentEngine.classify_project(
                sector="INVALID_SECTOR",
                total_investment_vnd=100_000_000_000.0,
            )

    def test_classify_project_negative_capital(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            PublicInvestmentEngine.classify_project(
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=-50_000_000.0,
            )

    def test_classify_project_negative_resettlement(self) -> None:
        with pytest.raises(ValueError, match="cannot be negative"):
            PublicInvestmentEngine.classify_project(
                sector="TRANSPORT_ENERGY_INDUSTRY",
                total_investment_vnd=100_000_000_000.0,
                resettlement_people=-50,
            )

    def test_disbursement_multiple_vouchers_cumulative(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-CUMUL-01",
            project_name="Dự án Giải ngân Nhiều Đợt",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=200_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hải Phòng",
            start_year=2026,
            end_year=2028,
        )
        temp_engine.allocate_capital_plan(
            project_id=proj["project_id"],
            plan_type="ANNUAL",
            fiscal_year=2026,
            allocated_capital_vnd=100_000_000_000.0,
            approved_by="Bộ GTVT",
            decision_number="QĐ-CUMUL-PLAN",
        )
        # 3 disbursement steps
        d1 = temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=20_000_000_000.0,
            treasury_office="Kho bạc Nhà nước HP",
            payment_voucher_number="VOUCHER-HP-01",
            recipient_contractor="Nhà thầu 1",
        )
        assert d1["total_disbursed_year_vnd"] == 20_000_000_000.0
        assert d1["disbursement_rate_pct"] == 20.0

        d2 = temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=30_000_000_000.0,
            treasury_office="Kho bạc Nhà nước HP",
            payment_voucher_number="VOUCHER-HP-02",
            recipient_contractor="Nhà thầu 2",
        )
        assert d2["total_disbursed_year_vnd"] == 50_000_000_000.0
        assert d2["disbursement_rate_pct"] == 50.0

        d3 = temp_engine.record_disbursement(
            project_id=proj["project_id"],
            fiscal_year=2026,
            disbursed_amount_vnd=50_000_000_000.0,
            treasury_office="Kho bạc Nhà nước HP",
            payment_voucher_number="VOUCHER-HP-03",
            recipient_contractor="Nhà thầu 3",
        )
        assert d3["total_disbursed_year_vnd"] == 100_000_000_000.0
        assert d3["disbursement_rate_pct"] == 100.0

    def test_bottleneck_all_types(self, temp_engine: PublicInvestmentEngine) -> None:
        proj = temp_engine.register_project(
            project_code="DA-BN-ALL",
            project_name="Dự án Thử nghiệm 6 Loại Điểm Nghẽn",
            sector="TRANSPORT_ENERGY_INDUSTRY",
            total_investment_vnd=500_000_000_000.0,
            capital_source="CENTRAL_BUDGET",
            managing_agency="Ban QLDA",
            implementation_location="Hà Nội",
            start_year=2026,
            end_year=2029,
        )
        for bn_type in temp_engine.BOTTLENECK_TYPES:
            bn = temp_engine.assess_bottleneck(
                project_id=proj["project_id"],
                bottleneck_type=bn_type,
                severity_level="MEDIUM",
                estimated_delay_months=3,
                mitigation_measures=f"Giải pháp xử lý điểm nghẽn {bn_type}",
                responsible_party="Ban Chỉ đạo Dự án",
            )
            assert bn["bottleneck_type"] == bn_type
            assert bn["resolved"] is False

    def test_cli_main_callback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        db_file = tmp_path / "cli_main_pubinvest.db"
        monkeypatch.setenv("MEKONG_PUBINVESTMENT_DB", str(db_file))

        result = runner.invoke(pubinvestment_app, [])
        assert result.exit_code == 0
        assert "HỆ THỐNG QUẢN LÝ ĐẦU TƯ CÔNG, KẾ HOẠCH VỐN & GIẢI NGÂN KBNN QUỐC GIA" in result.output

        result_json = runner.invoke(pubinvestment_app, ["--json"])
        assert result_json.exit_code == 0
        data = json.loads(result_json.output)
        assert data["ok"] is True
        assert data["status"] == "HEALTHY"

