"""
Unit and integration tests for Vietnamese National Reserves, Strategic Stockpiling & Emergency Relief Suite.
Governed by Law on National Reserve 2012 (Law No. 22/2012/QH13) & Decree No. 94/2013/NĐ-CP.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Generator

import pytest
from typer.testing import CliRunner

from src.cli.commands.nationalreserve_command import app as nationalreserve_app
from src.core.nationalreserve_engine import NationalReserveEngine


@pytest.fixture
def temp_db() -> Generator[str, None, None]:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    os.environ["MEKONG_NATIONALRESERVE_DB"] = path
    yield path
    if os.path.exists(path):
        os.remove(path)


class TestNationalReserveEngine:
    def test_register_warehouse_valid(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        res = engine.register_warehouse(
            warehouse_code="KHO-DT-HN01",
            warehouse_name="Kho Dự trữ Quốc gia Đông Anh",
            region="NORTH",
            managing_unit="Cục Dự trữ Nhà nước khu vực Hà Nội",
            storage_type="CONTROLLED_ATMOSPHERE_N2",
            total_capacity=50000.0,
        )
        assert res["warehouse_code"] == "KHO-DT-HN01"
        assert res["region"] == "NORTH"
        assert res["storage_type"] == "CONTROLLED_ATMOSPHERE_N2"
        assert res["total_capacity"] == 50000.0
        assert res["current_utilization"] == 0.0

    def test_register_warehouse_duplicate(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-DUP",
            warehouse_name="Kho Test",
            region="CENTRAL",
            managing_unit="Cục DTNN Đà Nẵng",
            storage_type="REGULAR_STORAGE",
            total_capacity=10000.0,
        )
        with pytest.raises(ValueError, match="already exists"):
            engine.register_warehouse(
                warehouse_code="KHO-DUP",
                warehouse_name="Kho Test 2",
                region="CENTRAL",
                managing_unit="Cục DTNN Đà Nẵng",
                storage_type="REGULAR_STORAGE",
                total_capacity=10000.0,
            )

    def test_register_warehouse_invalid_inputs(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        with pytest.raises(ValueError, match="Invalid region"):
            engine.register_warehouse(
                warehouse_code="KHO-INV1",
                warehouse_name="Kho Test",
                region="UNKNOWN_REGION",
                managing_unit="Cục DTNN",
                storage_type="REGULAR_STORAGE",
                total_capacity=1000.0,
            )
        with pytest.raises(ValueError, match="Invalid storage_type"):
            engine.register_warehouse(
                warehouse_code="KHO-INV2",
                warehouse_name="Kho Test",
                region="NORTH",
                managing_unit="Cục DTNN",
                storage_type="OPEN_AIR",
                total_capacity=1000.0,
            )
        with pytest.raises(ValueError, match="strictly positive"):
            engine.register_warehouse(
                warehouse_code="KHO-INV3",
                warehouse_name="Kho Test",
                region="NORTH",
                managing_unit="Cục DTNN",
                storage_type="REGULAR_STORAGE",
                total_capacity=0.0,
            )

    def test_intake_inventory_valid(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-HN",
            warehouse_name="Kho Hà Nội",
            region="NORTH",
            managing_unit="Cục DTNN Hà Nội",
            storage_type="CONTROLLED_ATMOSPHERE_N2",
            total_capacity=20000.0,
        )
        res = engine.intake_inventory(
            inventory_code="DTQG-GAO-2026-01",
            warehouse_code="KHO-HN",
            item_category="GRAIN_FOOD",
            item_name="Gạo tẻ dự trữ quốc gia 15% tấm",
            quantity=5000.0,
            unit="TAN",
            intake_date="2026-02-01",
            max_storage_months=18,
            unit_cost_vnd=14500000.0,
            quality_status="PASSED",
        )
        assert res["inventory_code"] == "DTQG-GAO-2026-01"
        assert res["quantity"] == 5000.0
        assert res["total_value_vnd"] == 5000.0 * 14500000.0
        assert res["rotation_due_date"] == "2027-08-01"
        assert res["warehouse_utilization_now"] == 5000.0

    def test_intake_inventory_capacity_exceeded(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-SMALL",
            warehouse_name="Kho Nhỏ",
            region="CENTRAL",
            managing_unit="Cục DTNN",
            storage_type="REGULAR_STORAGE",
            total_capacity=100.0,
        )
        with pytest.raises(ValueError, match="Warehouse capacity exceeded"):
            engine.intake_inventory(
                inventory_code="DTQG-BIG",
                warehouse_code="KHO-SMALL",
                item_category="GRAIN_FOOD",
                item_name="Thóc tẻ",
                quantity=150.0,
                unit="TAN",
                intake_date="2026-03-01",
                max_storage_months=12,
            )

    def test_intake_inventory_invalid_category(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-TEST",
            warehouse_name="Kho Test",
            region="SOUTH",
            managing_unit="Cục DTNN",
            storage_type="REGULAR_STORAGE",
            total_capacity=1000.0,
        )
        with pytest.raises(ValueError, match="Invalid item_category"):
            engine.intake_inventory(
                inventory_code="DTQG-INV",
                warehouse_code="KHO-TEST",
                item_category="LUXURY_GOODS",
                item_name="Kim cương",
                quantity=10.0,
                unit="KG",
                intake_date="2026-01-01",
                max_storage_months=12,
            )

    def test_inspect_inventory_quality(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-DN",
            warehouse_name="Kho Đà Nẵng",
            region="CENTRAL",
            managing_unit="Cục DTNN Đà Nẵng",
            storage_type="REGULAR_STORAGE",
            total_capacity=5000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-XUONG-01",
            warehouse_code="KHO-DN",
            item_category="RESCUE_EQUIPMENT",
            item_name="Xuồng cao tốc DT4",
            quantity=20.0,
            unit="CHIEC",
            intake_date="2026-01-10",
            max_storage_months=36,
            unit_cost_vnd=250000000.0,
        )
        res = engine.inspect_inventory_quality(
            inventory_code="DTQG-XUONG-01",
            quality_status="WARNING",
        )
        assert res["quality_status"] == "WARNING"
        assert res["previous_status"] == "PASSED"
        assert res["status_updated"] is True

    def test_allocate_relief_valid(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-QB",
            warehouse_name="Kho Bắc Trung Bộ",
            region="CENTRAL",
            managing_unit="Cục DTNN Nghệ Tĩnh",
            storage_type="REGULAR_STORAGE",
            total_capacity=10000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-GAO-QB",
            warehouse_code="KHO-QB",
            item_category="GRAIN_FOOD",
            item_name="Gạo cứu trợ thiên tai",
            quantity=4000.0,
            unit="TAN",
            intake_date="2026-01-01",
            max_storage_months=12,
            unit_cost_vnd=15000000.0,
        )

        res = engine.allocate_relief(
            allocation_code="XUAT-CT-2026-001",
            decision_number="QĐ 142/QĐ-TTg",
            decision_authority="PRIME_MINISTER",
            purpose="DISASTER_RELIEF",
            inventory_code="DTQG-GAO-QB",
            beneficiary_locality="Tỉnh Quảng Bình",
            allocated_quantity=1500.0,
            dispatch_date="2026-10-20",
        )
        assert res["allocation_code"] == "XUAT-CT-2026-001"
        assert res["allocated_quantity"] == 1500.0
        assert res["budget_replenishment_vnd"] == 1500.0 * 15000000.0
        assert res["remaining_inventory_quantity"] == 2500.0
        assert res["warehouse_utilization_now"] == 2500.0

    def test_allocate_relief_insufficient_stock(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-MINI",
            warehouse_name="Kho Mini",
            region="SOUTH",
            managing_unit="Cục DTNN",
            storage_type="REGULAR_STORAGE",
            total_capacity=500.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-MINI-01",
            warehouse_code="KHO-MINI",
            item_category="GRAIN_FOOD",
            item_name="Gạo",
            quantity=100.0,
            unit="TAN",
            intake_date="2026-01-01",
            max_storage_months=12,
        )
        with pytest.raises(ValueError, match="Insufficient stock"):
            engine.allocate_relief(
                allocation_code="XUAT-FAIL",
                decision_number="QĐ 999",
                decision_authority="PRIME_MINISTER",
                purpose="DISASTER_RELIEF",
                inventory_code="DTQG-MINI-01",
                beneficiary_locality="Tỉnh Thừa Thiên Huế",
                allocated_quantity=200.0,
                dispatch_date="2026-10-21",
            )

    def test_plan_stock_rotation_valid(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-ROT",
            warehouse_name="Kho Xoay Vòng",
            region="NORTH",
            managing_unit="Cục DTNN Hà Nội",
            storage_type="REGULAR_STORAGE",
            total_capacity=5000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-ROT-01",
            warehouse_code="KHO-ROT",
            item_category="GRAIN_FOOD",
            item_name="Gạo tẻ kho",
            quantity=3000.0,
            unit="TAN",
            intake_date="2025-06-01",
            max_storage_months=12,
            unit_cost_vnd=14000000.0,
        )
        res = engine.plan_stock_rotation(
            rotation_code="XR-2026-01",
            inventory_code="DTQG-ROT-01",
            plan_year=2026,
            rotation_type="AUCTION_SALE",
            outgoing_quantity=2000.0,
            replacement_deadline="2026-12-31",
            realized_proceeds_vnd=28000000000.0,
            reacquisition_budget_vnd=29000000000.0,
        )
        assert res["rotation_code"] == "XR-2026-01"
        assert res["outgoing_quantity"] == 2000.0
        assert res["status"] == "PLANNED"

    def test_plan_stock_rotation_exceeds_stock(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-EXCEED",
            warehouse_name="Kho Test",
            region="NORTH",
            managing_unit="Cục DTNN",
            storage_type="REGULAR_STORAGE",
            total_capacity=1000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-EXC",
            warehouse_code="KHO-EXCEED",
            item_category="GRAIN_FOOD",
            item_name="Gạo",
            quantity=500.0,
            unit="TAN",
            intake_date="2026-01-01",
            max_storage_months=12,
        )
        with pytest.raises(ValueError, match="Outgoing quantity exceeds"):
            engine.plan_stock_rotation(
                rotation_code="XR-EXC",
                inventory_code="DTQG-EXC",
                plan_year=2026,
                rotation_type="AUCTION_SALE",
                outgoing_quantity=800.0,
                replacement_deadline="2026-12-31",
            )

    def test_execute_rotation_replenishment(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-REP",
            warehouse_name="Kho Replenish",
            region="NORTH",
            managing_unit="Cục DTNN Hà Nội",
            storage_type="REGULAR_STORAGE",
            total_capacity=5000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-REP-01",
            warehouse_code="KHO-REP",
            item_category="GRAIN_FOOD",
            item_name="Gạo",
            quantity=2000.0,
            unit="TAN",
            intake_date="2025-01-01",
            max_storage_months=12,
            unit_cost_vnd=14000000.0,
        )
        engine.plan_stock_rotation(
            rotation_code="XR-REP-01",
            inventory_code="DTQG-REP-01",
            plan_year=2026,
            rotation_type="AUCTION_SALE",
            outgoing_quantity=1000.0,
            replacement_deadline="2026-12-31",
        )
        res = engine.execute_rotation_replenishment(
            rotation_code="XR-REP-01",
            replenished_quantity=1000.0,
            unit_cost_vnd=14500000.0,
        )
        assert res["rotation_code"] == "XR-REP-01"
        assert res["status"] == "COMPLETED"
        assert res["replenished_quantity"] == 1000.0
        assert res["updated_inventory_quantity"] == 3000.0

    def test_list_records(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-LST",
            warehouse_name="Kho List",
            region="SOUTH",
            managing_unit="Cục DTNN TPHCM",
            storage_type="REGULAR_STORAGE",
            total_capacity=10000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-LST-01",
            warehouse_code="KHO-LST",
            item_category="PETROLEUM_ENERGY",
            item_name="Xăng Ron 95 DTQG",
            quantity=2000.0,
            unit="LIT",
            intake_date="2026-01-01",
            max_storage_months=6,
        )
        all_recs = engine.list_records(record_type="all")
        assert len(all_recs["warehouses"]) == 1
        assert len(all_recs["inventories"]) == 1
        assert "allocations" in all_recs
        assert "rotations" in all_recs

    def test_get_telemetry_status(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-TEL1",
            warehouse_name="Kho Telemetry",
            region="CENTRAL_HIGHLANDS",
            managing_unit="Cục DTNN Tây Nguyên",
            storage_type="REGULAR_STORAGE",
            total_capacity=10000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-TEL-01",
            warehouse_code="KHO-TEL1",
            item_category="AGRICULTURAL_SEEDS",
            item_name="Giống lúa thuần",
            quantity=1000.0,
            unit="TAN",
            intake_date="2026-01-01",
            max_storage_months=3,  # Urgent rotation within 60 days if examined in late Feb
            unit_cost_vnd=25000000.0,
        )
        telemetry = engine.get_telemetry_status()
        assert telemetry["total_warehouses"] == 1
        assert telemetry["total_capacity"] == 10000.0
        assert telemetry["total_utilized_capacity"] == 1000.0
        assert telemetry["warehouse_utilization_rate_pct"] == 10.0
        assert telemetry["total_inventory_items"] == 1
        assert "AGRICULTURAL_SEEDS" in telemetry["inventory_by_category"]


class TestNationalReserveCli:
    def test_cli_default_callback(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(nationalreserve_app, [])
        assert result.exit_code == 0
        assert "CỤC DỰ TRỮ NHÀ NƯỚC" in result.output

    def test_cli_status_json(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(nationalreserve_app, ["status", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_warehouses" in data
        assert "total_reserve_stock_value_vnd" in data

    def test_cli_warehouse_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(
            nationalreserve_app,
            [
                "warehouse",
                "--code", "KHO-CLI-01",
                "--name", "Kho Dự trữ CLI",
                "--region", "NORTH",
                "--unit", "Cục DTNN Hà Nội",
                "--storage-type", "CONTROLLED_ATMOSPHERE_N2",
                "--capacity", "30000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["warehouse_code"] == "KHO-CLI-01"
        assert data["total_capacity"] == 30000.0

    def test_cli_intake_command(self, temp_db: str) -> None:
        runner = CliRunner()
        # First register warehouse
        runner.invoke(
            nationalreserve_app,
            [
                "warehouse",
                "--code", "KHO-CLI-02",
                "--name", "Kho Dự trữ CLI 2",
                "--region", "SOUTH",
                "--unit", "Cục DTNN TPHCM",
                "--capacity", "50000",
            ],
        )
        # Intake
        result = runner.invoke(
            nationalreserve_app,
            [
                "intake",
                "--code", "DTQG-CLI-GAO",
                "--warehouse", "KHO-CLI-02",
                "--category", "GRAIN_FOOD",
                "--name", "Gạo tẻ dự trữ CLI",
                "--quantity", "5000",
                "--unit", "TAN",
                "--date", "2026-03-01",
                "--months", "12",
                "--cost-vnd", "14000000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["inventory_code"] == "DTQG-CLI-GAO"
        assert data["quantity"] == 5000.0

    def test_cli_inspect_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            nationalreserve_app,
            [
                "warehouse",
                "--code", "KHO-CLI-03",
                "--name", "Kho 3",
                "--region", "CENTRAL",
                "--unit", "Cục DTNN",
                "--capacity", "10000",
            ],
        )
        runner.invoke(
            nationalreserve_app,
            [
                "intake",
                "--code", "DTQG-CLI-INSP",
                "--warehouse", "KHO-CLI-03",
                "--category", "GRAIN_FOOD",
                "--name", "Gạo",
                "--quantity", "1000",
                "--unit", "TAN",
                "--date", "2026-01-01",
            ],
        )
        result = runner.invoke(
            nationalreserve_app,
            [
                "inspect",
                "--code", "DTQG-CLI-INSP",
                "--status", "WARNING",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["quality_status"] == "WARNING"

    def test_cli_relief_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            nationalreserve_app,
            [
                "warehouse",
                "--code", "KHO-CLI-04",
                "--name", "Kho 4",
                "--region", "CENTRAL",
                "--unit", "Cục DTNN",
                "--capacity", "10000",
            ],
        )
        runner.invoke(
            nationalreserve_app,
            [
                "intake",
                "--code", "DTQG-CLI-REL",
                "--warehouse", "KHO-CLI-04",
                "--category", "GRAIN_FOOD",
                "--name", "Gạo",
                "--quantity", "3000",
                "--unit", "TAN",
                "--date", "2026-01-01",
                "--cost-vnd", "15000000",
            ],
        )
        result = runner.invoke(
            nationalreserve_app,
            [
                "relief",
                "--code", "XUAT-CLI-01",
                "--decision", "QĐ 189/QĐ-TTg",
                "--authority", "PRIME_MINISTER",
                "--purpose", "DISASTER_RELIEF",
                "--inventory", "DTQG-CLI-REL",
                "--locality", "Tỉnh Quảng Bình",
                "--quantity", "1000",
                "--date", "2026-10-15",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["allocated_quantity"] == 1000.0
        assert data["beneficiary_locality"] == "Tỉnh Quảng Bình"

    def test_cli_rotate_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            nationalreserve_app,
            [
                "warehouse",
                "--code", "KHO-CLI-05",
                "--name", "Kho 5",
                "--region", "NORTH",
                "--unit", "Cục DTNN",
                "--capacity", "10000",
            ],
        )
        runner.invoke(
            nationalreserve_app,
            [
                "intake",
                "--code", "DTQG-CLI-ROT",
                "--warehouse", "KHO-CLI-05",
                "--category", "GRAIN_FOOD",
                "--name", "Gạo",
                "--quantity", "2000",
                "--unit", "TAN",
                "--date", "2025-06-01",
            ],
        )
        result = runner.invoke(
            nationalreserve_app,
            [
                "rotate",
                "--code", "XR-CLI-01",
                "--inventory", "DTQG-CLI-ROT",
                "--year", "2026",
                "--type", "AUCTION_SALE",
                "--quantity", "1000",
                "--deadline", "2026-12-31",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["rotation_code"] == "XR-CLI-01"

    def test_cli_replenish_command(self, temp_db: str) -> None:
        runner = CliRunner()
        runner.invoke(
            nationalreserve_app,
            [
                "warehouse",
                "--code", "KHO-CLI-06",
                "--name", "Kho 6",
                "--region", "NORTH",
                "--unit", "Cục DTNN",
                "--capacity", "10000",
            ],
        )
        runner.invoke(
            nationalreserve_app,
            [
                "intake",
                "--code", "DTQG-CLI-REP",
                "--warehouse", "KHO-CLI-06",
                "--category", "GRAIN_FOOD",
                "--name", "Gạo",
                "--quantity", "2000",
                "--unit", "TAN",
                "--date", "2025-06-01",
            ],
        )
        runner.invoke(
            nationalreserve_app,
            [
                "rotate",
                "--code", "XR-CLI-REP",
                "--inventory", "DTQG-CLI-REP",
                "--year", "2026",
                "--type", "AUCTION_SALE",
                "--quantity", "1000",
                "--deadline", "2026-12-31",
            ],
        )
        result = runner.invoke(
            nationalreserve_app,
            [
                "replenish",
                "--code", "XR-CLI-REP",
                "--quantity", "1000",
                "--cost-vnd", "14500000",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "COMPLETED"

    def test_cli_list_command(self, temp_db: str) -> None:
        runner = CliRunner()
        result = runner.invoke(nationalreserve_app, ["list", "--type", "all", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "warehouses" in data



class TestNationalReserveMcp:
    def test_mcp_standalone_warehouse(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_nationalreserve_warehouse

        res_str = handle_nationalreserve_warehouse({
            "warehouse_code": "KHO-MCP-01",
            "warehouse_name": "Kho MCP Test",
            "region": "NORTH",
            "managing_unit": "Cục DTNN Hà Nội",
            "storage_type": "REGULAR_STORAGE",
            "total_capacity": 25000,
        })
        res = json.loads(res_str)
        assert res["warehouse_code"] == "KHO-MCP-01"

    def test_mcp_standalone_intake(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_nationalreserve_intake,
            handle_nationalreserve_warehouse,
        )

        handle_nationalreserve_warehouse({
            "warehouse_code": "KHO-MCP-02",
            "warehouse_name": "Kho MCP 2",
            "region": "CENTRAL",
            "managing_unit": "Cục DTNN Đà Nẵng",
            "storage_type": "REGULAR_STORAGE",
            "total_capacity": 20000,
        })
        res_str = handle_nationalreserve_intake({
            "inventory_code": "DTQG-MCP-01",
            "warehouse_code": "KHO-MCP-02",
            "item_category": "GRAIN_FOOD",
            "item_name": "Gạo dự trữ",
            "quantity": 3000,
            "unit": "TAN",
            "intake_date": "2026-01-15",
            "max_storage_months": 12,
        })
        res = json.loads(res_str)
        assert res["inventory_code"] == "DTQG-MCP-01"

    def test_mcp_standalone_inspect(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_nationalreserve_inspect,
            handle_nationalreserve_intake,
            handle_nationalreserve_warehouse,
        )

        handle_nationalreserve_warehouse({
            "warehouse_code": "KHO-MCP-03",
            "warehouse_name": "Kho MCP 3",
            "region": "SOUTH",
            "managing_unit": "Cục DTNN",
            "storage_type": "REGULAR_STORAGE",
            "total_capacity": 10000,
        })
        handle_nationalreserve_intake({
            "inventory_code": "DTQG-MCP-03",
            "warehouse_code": "KHO-MCP-03",
            "item_category": "GRAIN_FOOD",
            "item_name": "Gạo",
            "quantity": 1000,
            "unit": "TAN",
            "intake_date": "2026-01-15",
        })
        res_str = handle_nationalreserve_inspect({
            "inventory_code": "DTQG-MCP-03",
            "quality_status": "PASSED",
        })
        res = json.loads(res_str)
        assert res["quality_status"] == "PASSED"

    def test_mcp_standalone_relief(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_nationalreserve_intake,
            handle_nationalreserve_relief,
            handle_nationalreserve_warehouse,
        )

        handle_nationalreserve_warehouse({
            "warehouse_code": "KHO-MCP-04",
            "warehouse_name": "Kho MCP 4",
            "region": "CENTRAL",
            "managing_unit": "Cục DTNN",
            "storage_type": "REGULAR_STORAGE",
            "total_capacity": 10000,
        })
        handle_nationalreserve_intake({
            "inventory_code": "DTQG-MCP-04",
            "warehouse_code": "KHO-MCP-04",
            "item_category": "GRAIN_FOOD",
            "item_name": "Gạo",
            "quantity": 4000,
            "unit": "TAN",
            "intake_date": "2026-01-15",
            "unit_cost_vnd": 14000000,
        })
        res_str = handle_nationalreserve_relief({
            "allocation_code": "XUAT-MCP-01",
            "decision_number": "QĐ 142/QĐ-TTg",
            "decision_authority": "PRIME_MINISTER",
            "purpose": "DISASTER_RELIEF",
            "inventory_code": "DTQG-MCP-04",
            "beneficiary_locality": "Tỉnh Quảng Bình",
            "allocated_quantity": 1000,
            "dispatch_date": "2026-10-15",
        })
        res = json.loads(res_str)
        assert res["allocated_quantity"] == 1000.0

    def test_mcp_standalone_rotate(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_nationalreserve_intake,
            handle_nationalreserve_rotate,
            handle_nationalreserve_warehouse,
        )

        handle_nationalreserve_warehouse({
            "warehouse_code": "KHO-MCP-05",
            "warehouse_name": "Kho MCP 5",
            "region": "NORTH",
            "managing_unit": "Cục DTNN",
            "storage_type": "REGULAR_STORAGE",
            "total_capacity": 10000,
        })
        handle_nationalreserve_intake({
            "inventory_code": "DTQG-MCP-05",
            "warehouse_code": "KHO-MCP-05",
            "item_category": "GRAIN_FOOD",
            "item_name": "Gạo",
            "quantity": 3000,
            "unit": "TAN",
            "intake_date": "2025-06-01",
        })
        res_str = handle_nationalreserve_rotate({
            "rotation_code": "XR-MCP-01",
            "inventory_code": "DTQG-MCP-05",
            "plan_year": 2026,
            "rotation_type": "AUCTION_SALE",
            "outgoing_quantity": 1500,
            "replacement_deadline": "2026-12-31",
        })
        res = json.loads(res_str)
        assert res["rotation_code"] == "XR-MCP-01"

    def test_mcp_standalone_replenish(self, temp_db: str) -> None:
        from scripts.mcp_server import (
            handle_nationalreserve_intake,
            handle_nationalreserve_replenish,
            handle_nationalreserve_rotate,
            handle_nationalreserve_warehouse,
        )

        handle_nationalreserve_warehouse({
            "warehouse_code": "KHO-MCP-06",
            "warehouse_name": "Kho MCP 6",
            "region": "NORTH",
            "managing_unit": "Cục DTNN",
            "storage_type": "REGULAR_STORAGE",
            "total_capacity": 10000,
        })
        handle_nationalreserve_intake({
            "inventory_code": "DTQG-MCP-06",
            "warehouse_code": "KHO-MCP-06",
            "item_category": "GRAIN_FOOD",
            "item_name": "Gạo",
            "quantity": 3000,
            "unit": "TAN",
            "intake_date": "2025-06-01",
        })
        handle_nationalreserve_rotate({
            "rotation_code": "XR-MCP-REP",
            "inventory_code": "DTQG-MCP-06",
            "plan_year": 2026,
            "rotation_type": "AUCTION_SALE",
            "outgoing_quantity": 1000,
            "replacement_deadline": "2026-12-31",
        })
        res_str = handle_nationalreserve_replenish({
            "rotation_code": "XR-MCP-REP",
            "replenished_quantity": 1000,
            "unit_cost_vnd": 14500000,
        })
        res = json.loads(res_str)
        assert res["status"] == "COMPLETED"

    def test_mcp_standalone_list(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_nationalreserve_list

        res_str = handle_nationalreserve_list({"category": "all"})
        res = json.loads(res_str)
        assert "warehouses" in res

    def test_mcp_standalone_status(self, temp_db: str) -> None:
        from scripts.mcp_server import handle_nationalreserve_status

        res_str = handle_nationalreserve_status({})
        res = json.loads(res_str)
        assert "total_warehouses" in res

    def test_core_mcp_server_integration(self, temp_db: str) -> None:
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        res_str = server._handle_nationalreserve_warehouse(
            warehouse_code="KHO-CORE-MCP",
            warehouse_name="Kho Core MCP",
            region="MEKONG_DELTA",
            managing_unit="Cục DTNN Cần Thơ",
            storage_type="REGULAR_STORAGE",
            total_capacity=15000,
        )
        res = json.loads(res_str)
        assert res["warehouse_code"] == "KHO-CORE-MCP"

        stat_str = server._handle_nationalreserve_status()
        stat = json.loads(stat_str)
        assert stat["total_warehouses"] >= 1


class TestNationalReserveEdgeCases:
    def test_all_item_categories(self, temp_db: str) -> None:
        from src.core.nationalreserve_engine import VALID_CATEGORIES

        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-MULTI",
            warehouse_name="Kho Đa năng",
            region="NORTH",
            managing_unit="Cục DTNN",
            storage_type="REGULAR_STORAGE",
            total_capacity=100000.0,
        )
        for i, cat in enumerate(VALID_CATEGORIES):
            res = engine.intake_inventory(
                inventory_code=f"DTQG-CAT-{i}",
                warehouse_code="KHO-MULTI",
                item_category=cat,
                item_name=f"Mặt hàng {cat}",
                quantity=100.0,
                unit="TAN",
                intake_date="2026-01-01",
                max_storage_months=12,
            )
            assert res["item_category"] == cat

    def test_multiple_relief_allocations_until_depleted(self, temp_db: str) -> None:
        engine = NationalReserveEngine(db_path=temp_db)
        engine.register_warehouse(
            warehouse_code="KHO-DEPLETE",
            warehouse_name="Kho Cứu trợ",
            region="CENTRAL",
            managing_unit="Cục DTNN",
            storage_type="REGULAR_STORAGE",
            total_capacity=5000.0,
        )
        engine.intake_inventory(
            inventory_code="DTQG-DEPLETE-01",
            warehouse_code="KHO-DEPLETE",
            item_category="GRAIN_FOOD",
            item_name="Gạo",
            quantity=1000.0,
            unit="TAN",
            intake_date="2026-01-01",
            max_storage_months=12,
            unit_cost_vnd=14000000.0,
        )
        # Allocation 1: 400
        engine.allocate_relief(
            allocation_code="XUAT-DEP-1",
            decision_number="QĐ 01",
            decision_authority="PRIME_MINISTER",
            purpose="DISASTER_RELIEF",
            inventory_code="DTQG-DEPLETE-01",
            beneficiary_locality="Xã A",
            allocated_quantity=400.0,
            dispatch_date="2026-10-01",
        )
        # Allocation 2: 600 (remaining = 0)
        res = engine.allocate_relief(
            allocation_code="XUAT-DEP-2",
            decision_number="QĐ 02",
            decision_authority="PRIME_MINISTER",
            purpose="DISASTER_RELIEF",
            inventory_code="DTQG-DEPLETE-01",
            beneficiary_locality="Xã B",
            allocated_quantity=600.0,
            dispatch_date="2026-10-02",
        )
        assert res["remaining_inventory_quantity"] == 0.0
        assert res["warehouse_utilization_now"] == 0.0

        # Allocation 3: failure due to zero stock
        with pytest.raises(ValueError, match="Insufficient stock"):
            engine.allocate_relief(
                allocation_code="XUAT-DEP-3",
                decision_number="QĐ 03",
                decision_authority="PRIME_MINISTER",
                purpose="DISASTER_RELIEF",
                inventory_code="DTQG-DEPLETE-01",
                beneficiary_locality="Xã C",
                allocated_quantity=10.0,
                dispatch_date="2026-10-03",
            )
