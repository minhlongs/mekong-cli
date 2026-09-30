# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Vietnamese Registration of Security Interests & Secured Transactions Suite (Phase 146)."""

from __future__ import annotations

import ast
import json
import os
import pathlib
import pytest
from typer.testing import CliRunner

from src.core.securedtransactions_engine import (
    AssetType,
    DisposalMethod,
    RegistrationStatus,
    SecuredTransactionsEngine,
    SecurityMeasureType,
)
from src.cli.app_setup import build_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Core Boundary & AST Neutrality Tests
# ---------------------------------------------------------------------------


class TestSecuredTransactionsCoreBoundary:
    """Ensure SecuredTransactionsEngine uses only pure standard library modules."""

    def test_pure_standard_library_imports(self) -> None:
        source_path = pathlib.Path("src/core/securedtransactions_engine.py")
        assert source_path.exists(), "securedtransactions_engine.py must exist"

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


class TestSecuredTransactionsEngine:
    """Unit tests for SecuredTransactionsEngine under BLDS 2015 and Decree 99/2022/NĐ-CP."""

    @pytest.fixture
    def engine(self, tmp_path: pathlib.Path) -> SecuredTransactionsEngine:
        db_path = str(tmp_path / "test_securedtransactions.db")
        return SecuredTransactionsEngine(db_path=db_path)

    def test_register_security_measure_success(self, engine: SecuredTransactionsEngine) -> None:
        reg = engine.register_security_measure(
            contract_number="HD-TC-2026/001",
            measure_type="MORTGAGE",
            secured_party_name="Ngân hàng TMCP Ngoại thương Việt Nam - Chi nhánh Cần Thơ",
            secured_party_id="0100112437-005",
            secured_party_address="Số 1 Hòa Bình, Ninh Kiều, Cần Thơ",
            securing_party_name="Công ty Cổ phần Nông nghiệp Mekong Xanh",
            securing_party_id="1801654321",
            securing_party_address="KCN Trà Nóc, Bình Thủy, Cần Thơ",
            secured_obligation_amount=15_000_000_000.0,
            registry_office="Văn phòng Đăng ký đất đai TP. Cần Thơ",
            registration_id="REG-2026-TEST01",
            notes="Thế chấp quyền sử dụng đất và tài sản gắn liền với đất",
        )
        assert reg["registration_id"] == "REG-2026-TEST01"
        assert reg["contract_number"] == "HD-TC-2026/001"
        assert reg["measure_type"] == "MORTGAGE"
        assert reg["secured_obligation_amount"] == 15_000_000_000.0
        assert reg["status"] == "REGISTERED"

    def test_register_security_measure_validation(self, engine: SecuredTransactionsEngine) -> None:
        with pytest.raises(ValueError, match="contract number cannot be empty"):
            engine.register_security_measure(
                contract_number="",
                measure_type="MORTGAGE",
                secured_party_name="Bank A",
                secured_party_id="0101",
                secured_party_address="Addr A",
                securing_party_name="Borrower B",
                securing_party_id="0202",
                securing_party_address="Addr B",
                secured_obligation_amount=1_000_000.0,
            )

        with pytest.raises(ValueError, match="Invalid security measure type"):
            engine.register_security_measure(
                contract_number="HD-01",
                measure_type="INVALID_MEASURE",
                secured_party_name="Bank A",
                secured_party_id="0101",
                secured_party_address="Addr A",
                securing_party_name="Borrower B",
                securing_party_id="0202",
                securing_party_address="Addr B",
                secured_obligation_amount=1_000_000.0,
            )

        with pytest.raises(ValueError, match="strictly greater than 0"):
            engine.register_security_measure(
                contract_number="HD-02",
                measure_type="PLEDGE",
                secured_party_name="Bank A",
                secured_party_id="0101",
                secured_party_address="Addr A",
                securing_party_name="Borrower B",
                securing_party_id="0202",
                securing_party_address="Addr B",
                secured_obligation_amount=-500.0,
            )

    def test_record_collateral_and_priority_calculation(self, engine: SecuredTransactionsEngine) -> None:
        # Register 1st mortgage (earlier timestamp)
        reg1 = engine.register_security_measure(
            contract_number="HD-TC-01",
            measure_type="MORTGAGE",
            secured_party_name="Ngân hàng Vietcombank",
            secured_party_id="0100112437",
            secured_party_address="Hà Nội",
            securing_party_name="Công ty Mekong Agri",
            securing_party_id="1801234567",
            securing_party_address="Cần Thơ",
            secured_obligation_amount=10_000_000_000.0,
            registration_timestamp="2026-01-10T08:00:00Z",
            registration_id="REG-01",
        )
        assert reg1["registration_id"] == "REG-01"

        # Register 2nd mortgage on same asset (later timestamp)
        reg2 = engine.register_security_measure(
            contract_number="HD-TC-02",
            measure_type="MORTGAGE",
            secured_party_name="Ngân hàng BIDV",
            secured_party_id="0100150619",
            secured_party_address="Cần Thơ",
            securing_party_name="Công ty Mekong Agri",
            securing_party_id="1801234567",
            securing_party_address="Cần Thơ",
            secured_obligation_amount=5_000_000_000.0,
            registration_timestamp="2026-02-15T14:30:00Z",
            registration_id="REG-02",
        )
        assert reg2["registration_id"] == "REG-02"

        # Link same collateral asset to both registrations
        asset1 = engine.record_collateral(
            registration_id="REG-01",
            asset_type="REAL_ESTATE",
            asset_description="QSDĐ Thửa 128 Tờ bản đồ 15 Cần Thơ",
            identifier_number="GCN-CT-2024-998811",
            estimated_value=20_000_000_000.0,
            location="Ninh Kiều, Cần Thơ",
            asset_id="ASSET-01",
        )
        assert asset1["asset_id"] == "ASSET-01"

        asset2 = engine.record_collateral(
            registration_id="REG-02",
            asset_type="REAL_ESTATE",
            asset_description="QSDĐ Thửa 128 Tờ bản đồ 15 Cần Thơ (Thế chấp thứ hai)",
            identifier_number="GCN-CT-2024-998811",
            estimated_value=20_000_000_000.0,
            location="Ninh Kiều, Cần Thơ",
            asset_id="ASSET-02",
        )
        assert asset2["asset_id"] == "ASSET-02"

        # Priority calculation under Điều 308 BLDS 2015
        rankings = engine.calculate_priority("GCN-CT-2024-998811")
        assert len(rankings) == 2
        # Rank 1: Vietcombank (registered Jan 10)
        assert rankings[0]["priority_rank"] == 1
        assert rankings[0]["registration_id"] == "REG-01"
        assert rankings[0]["secured_party"] == "Ngân hàng Vietcombank"
        assert rankings[0]["claim_amount"] == 10_000_000_000.0

        # Rank 2: BIDV (registered Feb 15)
        assert rankings[1]["priority_rank"] == 2
        assert rankings[1]["registration_id"] == "REG-02"
        assert rankings[1]["secured_party"] == "Ngân hàng BIDV"
        assert rankings[1]["claim_amount"] == 5_000_000_000.0

    def test_disposal_notice_registration(self, engine: SecuredTransactionsEngine) -> None:
        reg = engine.register_security_measure(
            contract_number="HD-CC-01",
            measure_type="PLEDGE",
            secured_party_name="Quỹ Tín dụng Nhân dân Mekong",
            secured_party_id="01019988",
            secured_party_address="Vĩnh Long",
            securing_party_name="Hộ kinh doanh Lê Văn Tám",
            securing_party_id="086088112233",
            securing_party_address="Vĩnh Long",
            secured_obligation_amount=500_000_000.0,
            registration_id="REG-DISP-01",
        )
        asset = engine.record_collateral(
            registration_id="REG-DISP-01",
            asset_type="VEHICLE",
            asset_description="Xe tải Isuzu 5 tấn",
            identifier_number="65C-123.45",
            estimated_value=650_000_000.0,
            location="Vĩnh Long",
            asset_id="ASSET-TRUCK-01",
        )

        disp = engine.register_disposal_notice(
            registration_id="REG-DISP-01",
            asset_id="ASSET-TRUCK-01",
            disposal_reason="Bên bảo đảm vi phạm nghĩa vụ trả nợ gốc quá hạn 90 ngày",
            expected_disposal_date="2026-10-30",
            notifying_party="Quỹ Tín dụng Nhân dân Mekong",
            disposal_method="AUCTION",
            notice_id="DISP-TEST-01",
        )
        assert disp["notice_id"] == "DISP-TEST-01"
        assert disp["disposal_method"] == "AUCTION"
        assert disp["status"] == "ACTIVE"

        # Check registration status updated
        updated_reg = engine.get_record("registration", "REG-DISP-01")
        assert updated_reg["status"] == "DISPOSAL_NOTICE"

    def test_deregister_security_interest(self, engine: SecuredTransactionsEngine) -> None:
        reg = engine.register_security_measure(
            contract_number="HD-BL-01",
            measure_type="GUARANTEE",
            secured_party_name="Ngân hàng Agribank",
            secured_party_id="0100686174",
            secured_party_address="Hà Nội",
            securing_party_name="Công ty Bảo lãnh Mekong",
            securing_party_id="180998877",
            securing_party_address="An Giang",
            secured_obligation_amount=2_000_000_000.0,
            registration_id="REG-DEREG-01",
        )
        asset = engine.record_collateral(
            registration_id="REG-DEREG-01",
            asset_type="INVENTORY_GOODS",
            asset_description="100 tấn lúa Jasmine chuẩn xuất khẩu",
            identifier_number="LOT-JAS-2026-001",
            estimated_value=2_500_000_000.0,
            location="Kho Long Xuyên, An Giang",
            asset_id="ASSET-LUA-01",
        )

        # Deregister / giải chấp
        dereg = engine.deregister_security_interest(
            registration_id="REG-DEREG-01",
            deregistration_reason="OBLIGATION_FULFILLED",
            requesting_party="Công ty Bảo lãnh Mekong",
            approving_officer="Chuyên viên Nguyễn Văn Thanh",
            deregistration_id="DEREG-TEST-01",
        )
        assert dereg["deregistration_id"] == "DEREG-TEST-01"
        assert dereg["certificate_code"].startswith("CERT-XOA-BPBD-")

        # Verify registration marked DEREGISTERED
        reg_after = engine.get_record("registration", "REG-DEREG-01")
        assert reg_after["status"] == "DEREGISTERED"

        # Verify collateral asset marked RELEASED
        asset_after = engine.get_record("collateral", "ASSET-LUA-01")
        assert asset_after["status"] == "RELEASED"

        # Verify priority rankings cleared for released registration
        rankings = engine.calculate_priority("LOT-JAS-2026-001")
        assert len(rankings) == 0

    def test_search_and_telemetry(self, engine: SecuredTransactionsEngine) -> None:
        engine.register_security_measure(
            contract_number="HD-SEARCH-01",
            measure_type="TITLE_RETENTION",
            secured_party_name="Công ty Máy Nông Nghiệp Kubota",
            secured_party_id="030998811",
            secured_party_address="Bình Dương",
            securing_party_name="Hợp tác xã Nông nghiệp Thới Lai",
            securing_party_id="1800112233",
            securing_party_address="Thới Lai, Cần Thơ",
            secured_obligation_amount=800_000_000.0,
            registration_id="REG-SEARCH-01",
        )
        engine.record_collateral(
            registration_id="REG-SEARCH-01",
            asset_type="EQUIPMENT_MACHINERY",
            asset_description="Máy gặt đập liên hợp Kubota DC-70 Plus",
            identifier_number="VIN-KUBOTA-DC70-8899",
            estimated_value=900_000_000.0,
            location="Thới Lai, Cần Thơ",
            asset_id="ASSET-KUBOTA-01",
        )

        results = engine.search_security_interest("DC70-8899")
        assert len(results) >= 1
        assert results[0]["contract_number"] == "HD-SEARCH-01"

        stats = engine.get_telemetry_status()
        assert stats["total_security_registrations"] >= 1
        assert stats["total_collateral_assets"] >= 1
        assert stats["system_status"] == "ONLINE_HEALTHY"


# ---------------------------------------------------------------------------
# CLI Command Tests
# ---------------------------------------------------------------------------


class TestSecuredTransactionsCLI:
    """Test suite for mekong securedtransactions CLI commands and aliases."""

    @pytest.fixture
    def app(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
        db_path = str(tmp_path / "test_cli_securedtransactions.db")
        monkeypatch.setenv("MEKONG_SECUREDTRANSACTIONS_DB", db_path)
        return build_app()

    def test_status_command(self, app) -> None:
        res = runner.invoke(app, ["securedtransactions", "status", "--json"])
        assert res.exit_code == 0
        data = json.loads(res.output)
        assert data["system_status"] == "ONLINE_HEALTHY"

        # Console rich output
        res_con = runner.invoke(app, ["securedtransactions", "status"])
        assert res.exit_code == 0
        assert "BẢNG ĐIỀU HÀNH GIAO DỊCH BẢO ĐẢM" in res_con.output

    def test_register_collateral_priority_flow(self, app) -> None:
        # 1. Register security measure
        res_reg = runner.invoke(app, [
            "securedtransactions", "register",
            "REG-CLI-01",
            "MORTGAGE",
            "Ngân hàng Thương mại Cổ phần Ngoại thương",
            "Doanh nghiệp Tư nhân Mekong Rice",
            "12000000000",
            "--contract-number", "HD-CLI-2026/01",
            "--secured-party-id", "0100112233",
            "--securing-party-id", "1800554433",
            "--asset-type", "REAL_ESTATE",
            "--authority", "LAND_REGISTRY_OFFICE",
            "--notes", "Thế chấp kho bãi xay xát lúa gạo",
            "--json",
        ])
        assert res_reg.exit_code == 0
        data_reg = json.loads(res_reg.output)
        assert data_reg["registration_id"] == "REG-CLI-01"
        assert data_reg["status"] == "REGISTERED"

        # 2. Add collateral asset
        res_col = runner.invoke(app, [
            "securedtransactions", "collateral",
            "REG-CLI-01",
            "ASSET-CLI-KHO01",
            "Nhà xưởng xay xát và QSDĐ diện tích 5000m2",
            "REAL_ESTATE",
            "16000000000",
            "--identifier", "GCN-KHO-2026-88",
            "--location", "Ô Môn, Cần Thơ",
            "--json",
        ])
        assert res_col.exit_code == 0
        data_col = json.loads(res_col.output)
        assert data_col["asset_id"] == "ASSET-CLI-KHO01"

        # 3. Calculate priority ranking
        res_pri = runner.invoke(app, [
            "securedtransactions", "priority",
            "GCN-KHO-2026-88",
            "--json",
        ])
        assert res_pri.exit_code == 0
        data_pri = json.loads(res_pri.output)
        assert len(data_pri) == 1
        assert data_pri[0]["priority_rank"] == 1

        # 4. Issue disposal notice
        res_disp = runner.invoke(app, [
            "securedtransactions", "disposal",
            "REG-CLI-01",
            "ASSET-CLI-KHO01",
            "AUCTION",
            "--reason", "Chậm thanh toán nghĩa vụ nợ gốc",
            "--disposal-date", "2026-11-20",
            "--notifying-party", "Ngân hàng Thương mại Cổ phần Ngoại thương",
            "--json",
        ])
        assert res_disp.exit_code == 0
        data_disp = json.loads(res_disp.output)
        assert data_disp["disposal_method"] == "AUCTION"

        # 5. Deregister (giải chấp)
        res_dereg = runner.invoke(app, [
            "securedtransactions", "deregister",
            "REG-CLI-01",
            "OBLIGATION_FULFILLED",
            "--requesting-party", "Doanh nghiệp Tư nhân Mekong Rice",
            "--officer", "Công chứng viên Hoàng Văn",
            "--json",
        ])
        assert res_dereg.exit_code == 0
        data_dereg = json.loads(res_dereg.output)
        assert "CERT-XOA-BPBD-" in data_dereg["certificate_code"]

        # 6. Search
        res_srch = runner.invoke(app, [
            "securedtransactions", "search",
            "--query", "Mekong Rice",
            "--json",
        ])
        assert res_srch.exit_code == 0
        data_srch = json.loads(res_srch.output)
        assert len(data_srch) >= 1

        # 7. List
        res_lst = runner.invoke(app, [
            "securedtransactions", "list",
            "--category", "registration",
            "--json",
        ])
        assert res_lst.exit_code == 0
        data_lst = json.loads(res_lst.output)
        assert len(data_lst) >= 1

    def test_cli_aliases(self, app) -> None:
        # mekong baodam status
        res1 = runner.invoke(app, ["baodam", "status", "--json"])
        assert res1.exit_code == 0
        data1 = json.loads(res1.output)
        assert data1["system_status"] == "ONLINE_HEALTHY"

        # mekong giaodichbaodam status
        res2 = runner.invoke(app, ["giaodichbaodam", "status", "--json"])
        assert res2.exit_code == 0
        data2 = json.loads(res2.output)
        assert data2["system_status"] == "ONLINE_HEALTHY"


# ---------------------------------------------------------------------------
# MCP Server Tool Parity Tests
# ---------------------------------------------------------------------------


class TestSecuredTransactionsMCP:
    """Ensure FastMCP and Pure-Python JSON-RPC 2.0 dual server parity for secured transactions tools."""

    def test_src_core_mcp_securedtransactions_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = str(tmp_path / "test_mcp_core_securedtransactions.db")
        monkeypatch.setenv("MEKONG_SECUREDTRANSACTIONS_DB", db_path)
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()

        # 1. Register
        res_reg = json.loads(server._handle_securedtransactions_register(
            contract_number="HD-MCP-CORE-01",
            measure_type="MORTGAGE",
            secured_party_name="VCB MCP",
            secured_party_id="010101",
            secured_party_address="Hà Nội",
            securing_party_name="Grantor MCP",
            securing_party_id="020202",
            securing_party_address="TPHCM",
            secured_obligation_amount=5_000_000_000.0,
            registration_id="REG-MCP-01",
        ))
        assert res_reg["registration_id"] == "REG-MCP-01"

        # 2. Collateral
        res_col = json.loads(server._handle_securedtransactions_collateral(
            registration_id="REG-MCP-01",
            asset_type="REAL_ESTATE",
            asset_description="Bất động sản MCP Test",
            identifier_number="ASSET-ID-MCP-01",
            estimated_value=7_000_000_000.0,
            location="Quận 1, TPHCM",
            asset_id="ASSET-MCP-01",
        ))
        assert res_col["asset_id"] == "ASSET-MCP-01"

        # 3. Priority
        res_pri = json.loads(server._handle_securedtransactions_priority(
            asset_identifier="ASSET-ID-MCP-01",
        ))
        assert len(res_pri) == 1
        assert res_pri[0]["priority_rank"] == 1

        # 4. Disposal
        res_disp = json.loads(server._handle_securedtransactions_disposal(
            registration_id="REG-MCP-01",
            asset_id="ASSET-MCP-01",
            disposal_reason="Breach of repayment obligation",
            expected_disposal_date="2026-12-01",
            notifying_party="VCB MCP",
        ))
        assert res_disp["disposal_method"] == "AUCTION"

        # 5. Deregister
        res_dereg = json.loads(server._handle_securedtransactions_deregister(
            registration_id="REG-MCP-01",
            deregistration_reason="Obligation completed",
            requesting_party="Grantor MCP",
            approving_officer="Officer Mai",
        ))
        assert "CERT-XOA-BPBD-" in res_dereg["certificate_code"]

        # 6. Search
        res_srch = json.loads(server._handle_securedtransactions_search(
            query="VCB MCP",
        ))
        assert len(res_srch) >= 1

        # 7. Status
        res_stat = json.loads(server._handle_securedtransactions_status())
        assert res_stat["system_status"] == "ONLINE_HEALTHY"

    def test_scripts_mcp_securedtransactions_handlers(self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
        db_path = str(tmp_path / "test_mcp_scripts_securedtransactions.db")
        monkeypatch.setenv("MEKONG_SECUREDTRANSACTIONS_DB", db_path)
        from scripts.mcp_server import (
            handle_securedtransactions_collateral,
            handle_securedtransactions_deregister,
            handle_securedtransactions_disposal,
            handle_securedtransactions_priority,
            handle_securedtransactions_register,
            handle_securedtransactions_search,
            handle_securedtransactions_status,
        )

        # 1. Register
        res_reg = json.loads(handle_securedtransactions_register({
            "contract_number": "HD-SCRIPT-01",
            "measure_type": "PLEDGE",
            "secured_party_name": "Agribank Script",
            "secured_party_id": "010203",
            "secured_party_address": "Hà Nội",
            "securing_party_name": "Farmer B",
            "securing_party_id": "040506",
            "securing_party_address": "Đồng Tháp",
            "secured_obligation_amount": 1_000_000_000.0,
            "registration_id": "REG-SCRIPT-01",
        }))
        assert res_reg["registration_id"] == "REG-SCRIPT-01"

        # 2. Collateral
        res_col = json.loads(handle_securedtransactions_collateral({
            "registration_id": "REG-SCRIPT-01",
            "asset_type": "AGRICULTURAL_PRODUCT",
            "asset_description": "Kho gạo tồn kho 200 tấn",
            "identifier_number": "RICE-LOT-SCRIPT-01",
            "estimated_value": 1_800_000_000.0,
            "location": "Sa Đéc, Đồng Tháp",
            "asset_id": "ASSET-SCRIPT-01",
        }))
        assert res_col["asset_id"] == "ASSET-SCRIPT-01"

        # 3. Priority
        res_pri = json.loads(handle_securedtransactions_priority({
            "asset_identifier": "RICE-LOT-SCRIPT-01",
        }))
        assert len(res_pri) == 1
        assert res_pri[0]["priority_rank"] == 1

        # 4. Disposal
        res_disp = json.loads(handle_securedtransactions_disposal({
            "registration_id": "REG-SCRIPT-01",
            "asset_id": "ASSET-SCRIPT-01",
            "disposal_reason": "Default on agricultural loan",
            "expected_disposal_date": "2026-11-10",
            "notifying_party": "Agribank Script",
        }))
        assert res_disp["status"] == "ACTIVE"

        # 5. Deregister
        res_dereg = json.loads(handle_securedtransactions_deregister({
            "registration_id": "REG-SCRIPT-01",
            "deregistration_reason": "Debt cleared",
            "requesting_party": "Farmer B",
            "approving_officer": "Registrar Lan",
        }))
        assert "CERT-XOA-BPBD-" in res_dereg["certificate_code"]

        # 6. Search
        res_srch = json.loads(handle_securedtransactions_search({
            "query": "Farmer B",
        }))
        assert len(res_srch) >= 1

        # 7. Status
        res_stat = json.loads(handle_securedtransactions_status({}))
        assert res_stat["system_status"] == "ONLINE_HEALTHY"

    def test_scripts_mcp_core_tools_spec_and_handlers(self) -> None:
        from scripts.mcp_server import CORE_HANDLERS, CORE_TOOLS_SPEC

        expected_tools = [
            "mekong_securedtransactions_register",
            "mekong_securedtransactions_collateral",
            "mekong_securedtransactions_priority",
            "mekong_securedtransactions_disposal",
            "mekong_securedtransactions_deregister",
            "mekong_securedtransactions_search",
            "mekong_securedtransactions_status",
        ]

        spec_names = {t["name"] for t in CORE_TOOLS_SPEC}
        for tool in expected_tools:
            assert tool in spec_names, f"Tool {tool} missing from CORE_TOOLS_SPEC"
            assert tool in CORE_HANDLERS, f"Tool {tool} missing from CORE_HANDLERS"
            bare_name = tool.replace("mekong_", "")
            assert bare_name in CORE_HANDLERS, f"Alias {bare_name} missing from CORE_HANDLERS"
