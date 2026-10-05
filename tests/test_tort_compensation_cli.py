"""Unit tests for Tort & Civil Liability CLI command surface (Phase 150)."""

import json
from unittest.mock import MagicMock, patch
import pytest
from typer.testing import CliRunner

from src.cli.commands.tort_command import tort_app

runner = CliRunner()


class TestTortCompensationCLI:
    """Test suite for tort command surface."""

    def test_status_command(self):
        """Test status command execution."""
        result = runner.invoke(tort_app, ["status"])
        assert result.exit_code == 0
        assert "BỒI THƯỜNG THIỆT HẠI NGOÀI HỢP ĐỒNG" in result.stdout or "Mức Trần" in result.stdout

    def test_create_case_command(self):
        """Test create-case CLI command."""
        result = runner.invoke(
            tort_app,
            [
                "create-case",
                "--incident-date", "2026-02-15",
                "--location", "TP. Hồ Chí Minh",
                "--category", "HEALTH",
                "--liability", "HIGH_RISK_SOURCE",
                "--desc", "Tai nạn giao thông",
            ],
        )
        assert result.exit_code == 0
        assert "TC-" in result.stdout or "khởi tạo hồ sơ" in result.stdout

    def test_create_case_command_json(self):
        """Test create-case command with --json flag."""
        result = runner.invoke(
            tort_app,
            [
                "create-case",
                "--incident-date", "2026-02-15",
                "--location", "Hà Nội",
                "--category", "PROPERTY",
                "--liability", "FAULT_BASED",
                "--desc", "Hư hỏng tài sản",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "case_id" in data
        assert data["damage_category"] == "PROPERTY"

    def test_calculate_health_command(self):
        """Test calculate-health CLI command."""
        result = runner.invoke(
            tort_app,
            [
                "calculate-health",
                "--treatment", "25000000",
                "--lost-income", "15000000",
                "--caregiver", "5000000",
                "--disability-pct", "10",
            ],
        )
        assert result.exit_code == 0
        assert "TỔNG MỨC BỒI THƯỜNG SỨC KHỎE" in result.stdout

    def test_calculate_life_command(self):
        """Test calculate-life CLI command."""
        result = runner.invoke(
            tort_app,
            [
                "calculate-life",
                "--funeral", "30000000",
                "--treatment", "10000000",
                "--dependents-count", "2",
                "--monthly-allowance", "2340000",
                "--duration-months", "60",
            ],
        )
        assert result.exit_code == 0
        assert "TỔNG MỨC BỒI THƯỜNG TÍNH MẠNG" in result.stdout

    def test_settle_command(self):
        """Test settle CLI command."""
        # First create a case
        create_res = runner.invoke(
            tort_app,
            [
                "create-case",
                "--incident-date", "2026-02-15",
                "--location", "Đà Nẵng",
                "--category", "HEALTH",
                "--liability", "HIGH_RISK_SOURCE",
                "--desc", "Thương tích do tai nạn",
                "--json",
            ],
        )
        case_data = json.loads(create_res.stdout)
        cid = case_data["case_id"]

        settle_res = runner.invoke(
            tort_app,
            [
                "settle",
                "--case-id", cid,
                "--amount", "45000000",
                "--terms", "Thanh toán trong 3 ngày",
            ],
        )
        assert settle_res.exit_code == 0
        assert "SA-" in settle_res.stdout or "biên bản hòa giải" in settle_res.stdout
