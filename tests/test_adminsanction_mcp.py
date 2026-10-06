"""Unit tests for Administrative Sanctions MCP tools (Phase 152)."""

import json
import pytest
from scripts.mcp_server import (
    handle_adminsanction_assess_jurisdiction,
    handle_adminsanction_assess_relief,
    handle_adminsanction_calculate_fine,
    handle_adminsanction_calculate_remedial_measures,
    handle_adminsanction_check_limitations,
    handle_adminsanction_create_case,
    handle_adminsanction_dashboard,
    handle_adminsanction_generate_decision,
)


class TestAdminSanctionMCP:
    """Test suite for MCP tool handlers of Administrative Sanctions module."""

    def test_mcp_create_case(self):
        """Test handle_adminsanction_create_case MCP handler."""
        raw = handle_adminsanction_create_case({
            "subject_type": "INDIVIDUAL",
            "subject_name": "Phạm Văn Quang",
            "violation_category": "TRAFFIC",
            "violation_date": "2026-02-20",
            "violation_location": "Đà Nẵng",
            "behavior_description": "Không đội mũ bảo hiểm khi tham gia giao thông",
        })
        data = json.loads(raw)
        assert data["subject_name"] == "Phạm Văn Quang"
        assert data["status"] == "RECORDED"
        assert "case_id" in data

    def test_mcp_full_sanction_workflow(self):
        """Test full MCP administrative sanction workflow."""
        # 1. Create case
        r1 = json.loads(handle_adminsanction_create_case({
            "subject_type": "ORGANIZATION",
            "subject_name": "Công ty TNHH Hoàng Gia",
            "violation_category": "ENVIRONMENT",
            "violation_date": "2026-02-10",
            "violation_location": "Bình Dương",
            "behavior_description": "Xả nước thải chưa qua xử lý",
        }))
        cid = r1["case_id"]

        # 2. Calculate fine
        r2 = json.loads(handle_adminsanction_calculate_fine({
            "min_fine_vnd": 30_000_000,
            "max_fine_vnd": 50_000_000,
            "subject_type": "ORGANIZATION",
            "mitigating_count": 0,
            "aggravating_count": 1,
        }))
        assert "fine_calculation" in r2

        # 3. Assess jurisdiction
        r3 = json.loads(handle_adminsanction_assess_jurisdiction({
            "fine_amount_vnd": 45_000_000,
            "violation_category": "ENVIRONMENT",
            "subject_type": "ORGANIZATION",
        }))
        assert "competent_authority" in r3

        # 4. Remedial measures
        r4 = json.loads(handle_adminsanction_calculate_remedial_measures({
            "measure_types": ["REMEDY_ENVIRONMENTAL_POLLUTION"],
            "rectification_cost_estimate_vnd": 20_000_000,
            "execution_deadline_days": 30,
        }))
        assert r4["total_financial_rectification_vnd"] == 20_000_000

        # 5. Generate decision
        r5 = json.loads(handle_adminsanction_generate_decision({
            "case_id": cid,
            "fine_amount_vnd": 45_000_000,
            "primary_sanction": "Phạt tiền",
            "issuing_officer": "Chủ tịch UBND Tỉnh",
        }))
        assert r5["status"] == "DECIDED"

        # 6. Check limitations
        r6 = json.loads(handle_adminsanction_check_limitations({"case_id": cid}))
        assert r6["is_expired"] is False

        # 7. Dashboard
        r7 = json.loads(handle_adminsanction_dashboard({}))
        assert "total_cases" in r7
