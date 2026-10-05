"""Unit tests for Tort & Civil Liability MCP server integration (Phase 150)."""

import json
from unittest.mock import patch
import pytest

from scripts.mcp_server import (
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
    handle_tort_calculate_health,
    handle_tort_calculate_life,
    handle_tort_calculate_property,
    handle_tort_create_case,
    handle_tort_dossier,
    handle_tort_settle,
)


class TestTortCompensationMCP:
    """Test suite for Tort Compensation MCP server integration."""

    def test_mcp_tools_spec_presence(self):
        """Verify all tort tools are present in CORE_TOOLS_SPEC."""
        tool_names = [t["name"] for t in CORE_TOOLS_SPEC]
        assert "mekong_tort_create_case" in tool_names
        assert "mekong_tort_calculate_health" in tool_names
        assert "mekong_tort_calculate_life" in tool_names
        assert "mekong_tort_calculate_property" in tool_names
        assert "mekong_tort_settle" in tool_names
        assert "mekong_tort_dossier" in tool_names

    def test_mcp_handlers_presence(self):
        """Verify all tort handlers are registered in CORE_HANDLERS."""
        assert "mekong_tort_create_case" in CORE_HANDLERS
        assert "mekong_tort_calculate_health" in CORE_HANDLERS
        assert "mekong_tort_calculate_life" in CORE_HANDLERS
        assert "mekong_tort_calculate_property" in CORE_HANDLERS
        assert "mekong_tort_settle" in CORE_HANDLERS
        assert "mekong_tort_dossier" in CORE_HANDLERS
        assert "tort_create_case" in CORE_HANDLERS
        assert "tort_calculate_health" in CORE_HANDLERS
        assert "tort_calculate_life" in CORE_HANDLERS
        assert "tort_calculate_property" in CORE_HANDLERS
        assert "tort_settle" in CORE_HANDLERS
        assert "tort_dossier" in CORE_HANDLERS

    @patch("src.core.tort_compensation_engine.TortCompensationEngine.create_case")
    def test_handle_tort_create_case(self, mock_create):
        mock_create.return_value = {
            "ok": True,
            "case": {"case_id": "TORT-TEST-MCP"},
        }
        res_str = handle_tort_create_case({
            "incident_date": "2026-03-01",
            "incident_location": "TP.HCM",
            "damage_category": "HEALTH",
        })
        res = json.loads(res_str)
        assert res["ok"] is True
        assert res["case"]["case_id"] == "TORT-TEST-MCP"

    @patch("src.core.tort_compensation_engine.TortCompensationEngine.calculate_health_damage")
    def test_handle_tort_calculate_health(self, mock_calc):
        mock_calc.return_value = {
            "ok": True,
            "data": {"final_compensation_amount": 50_000_000},
        }
        res_str = handle_tort_calculate_health({
            "treatment_costs": 30_000_000,
            "lost_income": 20_000_000,
        })
        res = json.loads(res_str)
        assert res["ok"] is True
        assert res["data"]["final_compensation_amount"] == 50_000_000

    @patch("src.core.tort_compensation_engine.TortCompensationEngine.calculate_life_damage")
    def test_handle_tort_calculate_life(self, mock_calc):
        mock_calc.return_value = {
            "ok": True,
            "data": {"final_compensation_amount": 250_000_000},
        }
        res_str = handle_tort_calculate_life({
            "funeral_costs": 30_000_000,
            "dependents_json": json.dumps([{"name": "Con", "relationship": "CHILD", "birth_date": "2020-01-01"}]),
        })
        res = json.loads(res_str)
        assert res["ok"] is True
        assert res["data"]["final_compensation_amount"] == 250_000_000

    @patch("src.core.tort_compensation_engine.TortCompensationEngine.calculate_property_damage")
    def test_handle_tort_calculate_property(self, mock_calc):
        mock_calc.return_value = {
            "ok": True,
            "data": {"final_compensation_amount": 80_000_000},
        }
        res_str = handle_tort_calculate_property({
            "lost_or_destroyed_value": 80_000_000,
        })
        res = json.loads(res_str)
        assert res["ok"] is True
        assert res["data"]["final_compensation_amount"] == 80_000_000

    @patch("src.core.tort_compensation_engine.TortCompensationEngine.create_settlement_agreement")
    def test_handle_tort_settle(self, mock_settle):
        mock_settle.return_value = {
            "ok": True,
            "settlement": {"settlement_id": "SETTLE-MCP-01"},
        }
        res_str = handle_tort_settle({
            "case_id": "TORT-MCP-01",
            "total_agreed_amount": 45_000_000,
            "payment_terms": "Thanh toán ngay",
        })
        res = json.loads(res_str)
        assert res["ok"] is True
        assert res["settlement"]["settlement_id"] == "SETTLE-MCP-01"

    @patch("src.core.tort_compensation_engine.TortCompensationEngine.generate_assessment_dossier")
    def test_handle_tort_dossier(self, mock_dossier):
        mock_dossier.return_value = {
            "ok": True,
            "dossier": {"dossier_id": "DOSSIER-MCP-01"},
        }
        res_str = handle_tort_dossier({"case_id": "TORT-MCP-01"})
        res = json.loads(res_str)
        assert res["ok"] is True
        assert res["dossier"]["dossier_id"] == "DOSSIER-MCP-01"
