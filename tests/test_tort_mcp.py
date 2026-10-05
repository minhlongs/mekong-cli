"""Unit tests for Tort & Civil Liability MCP server tools (Phase 150)."""

import json
import pytest
from scripts.mcp_server import (
    handle_tort_create_case,
    handle_tort_calculate_health,
    handle_tort_calculate_life,
    handle_tort_calculate_property,
    handle_tort_settle,
    handle_tort_dossier,
)


class TestTortMCPHandlers:
    """Test suite for Tort MCP tool handlers."""

    def test_mcp_create_case(self):
        """Test handle_tort_create_case MCP handler."""
        raw_res = handle_tort_create_case({
            "incident_date": "2026-03-01",
            "incident_location": "TP. Hồ Chí Minh",
            "damage_category": "HEALTH",
            "liability_type": "HIGH_RISK_SOURCE",
            "description": "Tai nạn xe máy và xe tải",
        })
        res = json.loads(raw_res)
        assert "case_id" in res
        assert res["damage_category"] == "HEALTH"
        assert res["liability_type"] == "HIGH_RISK_SOURCE"

    def test_mcp_calculate_health(self):
        """Test handle_tort_calculate_health MCP handler."""
        raw_res = handle_tort_calculate_health({
            "treatment_costs": 15000000.0,
            "lost_income": 10000000.0,
            "caregiver_costs": 5000000.0,
            "disability_percentage": 0.0,
            "victim_fault_percentage": 10.0,
        })
        res = json.loads(raw_res)
        assert "final_payable_compensation" in res
        assert res["damage_category"] == "HEALTH"
        assert res["breakdown"]["total_material_damage"] == 30000000.0

    def test_mcp_calculate_life(self):
        """Test handle_tort_calculate_life MCP handler."""
        dependents = [
            {"full_name": "Cháu A", "relationship": "CHILD", "monthly_allowance": 2340000.0, "duration_months": 120}
        ]
        raw_res = handle_tort_calculate_life({
            "pre_death_treatment_costs": 10000000.0,
            "funeral_costs": 30000000.0,
            "dependents_json": json.dumps(dependents),
            "victim_fault_percentage": 0.0,
        })
        res = json.loads(raw_res)
        assert "final_payable_compensation" in res
        assert res["damage_category"] == "LIFE"

    def test_mcp_calculate_property(self):
        """Test handle_tort_calculate_property MCP handler."""
        raw_res = handle_tort_calculate_property({
            "lost_or_destroyed_value": 50000000.0,
            "repair_costs": 10000000.0,
            "lost_income": 5000000.0,
            "mitigation_costs": 2000000.0,
            "victim_fault_percentage": 0.0,
        })
        res = json.loads(raw_res)
        assert "final_payable_compensation" in res
        assert res["breakdown"]["total_material_damage"] == 67000000.0

    def test_mcp_settle_and_dossier(self):
        """Test handle_tort_settle and handle_tort_dossier MCP handlers."""
        # Create case first
        case_raw = handle_tort_create_case({
            "incident_date": "2026-03-01",
            "incident_location": "Hà Nội",
            "damage_category": "PROPERTY",
            "liability_type": "HIGH_RISK_SOURCE",
            "description": "Thiệt hại hàng hóa do phương tiện giao thông",
        })
        case_data = json.loads(case_raw)
        cid = case_data["case_id"]

        settle_raw = handle_tort_settle({
            "case_id": cid,
            "agreed_amount": 55000000.0,
            "payment_terms": "Thanh toán 1 lần trong 7 ngày",
            "conciliator": "Hòa giải viên cơ sở",
            "court_recognized": True,
        })
        settle_data = json.loads(settle_raw)
        assert "settlement_id" in settle_data
        assert settle_data["total_agreed_amount"] == 55000000.0

        dossier_raw = handle_tort_dossier({"case_id": cid})
        dossier = json.loads(dossier_raw)
        assert dossier["dossier_id"] == f"DOSSIER-{cid}"
        assert dossier["case_summary"]["status"] == "SETTLED"
