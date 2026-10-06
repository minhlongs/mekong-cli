"""Unit tests for Administrative Sanctions CLI command surface (Phase 152)."""

import json
import pytest
from typer.testing import CliRunner
from src.cli.commands.adminsanction_command import adminsanction_app

runner = CliRunner()


class TestAdminSanctionCLI:
    """Test suite for adminsanction command surface."""

    def test_status_command(self):
        """Test status command execution."""
        result = runner.invoke(adminsanction_app, ["status"])
        assert result.exit_code == 0
        assert "XỬ PHẠT VI PHẠM HÀNH CHÍNH" in result.stdout or "Thời hiệu" in result.stdout

    def test_create_case_command(self):
        """Test create-case CLI command."""
        result = runner.invoke(
            adminsanction_app,
            [
                "create-case",
                "--subject-type", "INDIVIDUAL",
                "--subject-name", "Trần Văn Long",
                "--category", "TRAFFIC",
                "--date", "2026-02-15",
                "--location", "TP. Hồ Chí Minh",
                "--behavior", "Vượt tốc độ quy định",
            ],
        )
        assert result.exit_code == 0
        assert "SANCT-" in result.stdout or "Đã lập hồ sơ vụ việc" in result.stdout

    def test_create_case_command_json(self):
        """Test create-case with --json flag."""
        result = runner.invoke(
            adminsanction_app,
            [
                "create-case",
                "--subject-type", "ORGANIZATION",
                "--subject-name", "Công ty TNHH Á Châu",
                "--category", "TAX",
                "--date", "2026-01-20",
                "--location", "Hà Nội",
                "--behavior", "Chậm nộp tờ khai thuế",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "case_id" in data
        assert data["subject_name"] == "Công ty TNHH Á Châu"

    def test_calculate_fine_command(self):
        """Test calculate-fine CLI command."""
        result = runner.invoke(
            adminsanction_app,
            [
                "calculate-fine",
                "--min-fine", "4000000",
                "--max-fine", "6000000",
                "--subject-type", "INDIVIDUAL",
                "--mitigating", "1",
                "--aggravating", "0",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "fine_calculation" in data
        assert data["fine_calculation"]["calculated_fine_vnd"] < 5_000_000.0

    def test_assess_jurisdiction_command(self):
        """Test assess-jurisdiction CLI command."""
        result = runner.invoke(
            adminsanction_app,
            [
                "assess-jurisdiction",
                "--fine", "15000000",
                "--category", "TRAFFIC",
                "--subject-type", "INDIVIDUAL",
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["competent_authority"] == "DISTRICT_CHAIR"

    def test_dashboard_command(self):
        """Test dashboard CLI command."""
        result = runner.invoke(adminsanction_app, ["dashboard", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert "total_cases" in data
        assert "statutory_compliance" in data
