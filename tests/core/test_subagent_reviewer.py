"""Tests for SubagentReviewer — two-stage spec + quality review."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

from src.core.subagent_reviewer import (
    QualityReviewResult,
    SpecReviewResult,
    SubagentReviewer,
    _parse_status,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class TestSpecReviewResult:
    def test_construction(self):
        r = SpecReviewResult(compliant=True, issues=[], severity="none")
        assert r.compliant is True
        assert r.issues == []
        assert r.severity == "none"

    def test_to_dict(self):
        r = SpecReviewResult(compliant=False, issues=["missing test"], severity="major")
        d = r.to_dict()
        assert d == {"compliant": False, "issues": ["missing test"], "severity": "major"}


class TestQualityReviewResult:
    def test_construction(self):
        r = QualityReviewResult(score=85, issues=[], suggestions=["add docstring"], passed=True)
        assert r.score == 85
        assert r.passed is True

    def test_to_dict(self):
        r = QualityReviewResult(score=40, issues=["no tests"], suggestions=[], passed=False)
        d = r.to_dict()
        assert d == {
            "score": 40,
            "issues": ["no tests"],
            "suggestions": [],
            "passed": False,
        }


# ---------------------------------------------------------------------------
# _parse_status
# ---------------------------------------------------------------------------

class TestParseStatus:
    def test_done_status(self):
        status, _ = _parse_status("Some output\n<status>DONE</status>")
        assert status == "DONE"

    def test_done_with_concerns(self):
        status, concerns = _parse_status(
            "Output here\n<status>DONE_WITH_CONCERNS</status>\nMissing edge case test"
        )
        assert status == "DONE_WITH_CONCERNS"
        assert "edge case" in concerns

    def test_blocked_status(self):
        status, details = _parse_status(
            "<status>BLOCKED</status>\nNeed database credentials"
        )
        assert status == "BLOCKED"
        assert "credentials" in details

    def test_needs_context(self):
        status, _ = _parse_status("<status>NEEDS_CONTEXT</status>\nWhich API version?")
        assert status == "NEEDS_CONTEXT"

    def test_no_status_tag_defaults_done(self):
        status, content = _parse_status("Just some output without status tag")
        assert status == "DONE"
        assert content == ""

    def test_status_mid_output(self):
        status, _ = _parse_status(
            "Line 1\nLine 2\n<status>DONE_WITH_CONCERNS</status>\nConcern here"
        )
        assert status == "DONE_WITH_CONCERNS"


# ---------------------------------------------------------------------------
# SubagentReviewer.__init__
# ---------------------------------------------------------------------------

class TestSubagentReviewerInit:
    def test_stores_llm_client(self):
        mock_llm = MagicMock()
        reviewer = SubagentReviewer(mock_llm)
        assert reviewer._llm is mock_llm


# ---------------------------------------------------------------------------
# review_spec
# ---------------------------------------------------------------------------

class TestReviewSpec:
    def test_compliant_output(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "compliant": True,
            "issues": [],
            "severity": "none",
        }
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_spec("Build a login page", "Login page built.")
        assert result.compliant is True
        assert result.issues == []
        assert result.severity == "none"

    def test_non_compliant_output(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "compliant": False,
            "issues": ["Missing error handling", "No tests"],
            "severity": "major",
        }
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_spec("Build auth system", "Partial impl")
        assert result.compliant is False
        assert len(result.issues) == 2
        assert result.severity == "major"

    def test_missing_keys_default_values(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {}
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_spec("task", "output")
        assert result.compliant is False
        assert result.issues == []
        assert result.severity == "none"

    def test_exception_returns_safe_default(self, caplog):
        caplog.set_level(logging.WARNING)
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = RuntimeError("LLM down")
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_spec("task", "output")
        assert result.compliant is True
        assert result.issues == []
        assert result.severity == "none"
        assert any("Spec review failed" in rec.message for rec in caplog.records)

    def test_truncates_long_inputs(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {"compliant": True, "issues": [], "severity": "none"}
        reviewer = SubagentReviewer(mock_llm)
        long_spec = "x" * 5000
        long_output = "y" * 8000
        reviewer.review_spec(long_spec, long_output)
        prompt = mock_llm.generate_json.call_args[0][0]
        # Spec truncated to 2000, output truncated to 3000
        assert "x" * 2000 in prompt
        assert "y" * 3000 in prompt
        assert "x" * 2001 not in prompt


# ---------------------------------------------------------------------------
# review_quality
# ---------------------------------------------------------------------------

class TestReviewQuality:
    def test_high_score_passes(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "score": 85,
            "issues": [],
            "suggestions": ["Add more docstrings"],
        }
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_quality("Clean implementation with tests")
        assert result.score == 85
        assert result.passed is True
        assert result.suggestions == ["Add more docstrings"]

    def test_low_score_fails(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "score": 30,
            "issues": ["No error handling", "Hardcoded secrets"],
            "suggestions": [],
        }
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_quality("Bad code")
        assert result.score == 30
        assert result.passed is False
        assert len(result.issues) == 2

    def test_boundary_score_60_passes(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {"score": 60, "issues": [], "suggestions": []}
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_quality("OK code")
        assert result.passed is True

    def test_boundary_score_59_fails(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {"score": 59, "issues": [], "suggestions": []}
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_quality("Below threshold")
        assert result.passed is False

    def test_missing_keys_default_values(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {}
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_quality("output")
        assert result.score == 50
        assert result.passed is False  # 50 < 60

    def test_exception_returns_safe_default(self, caplog):
        caplog.set_level(logging.WARNING)
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = ValueError("parse error")
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.review_quality("output")
        assert result.score == 50
        assert result.passed is True  # safe default
        assert result.issues == []
        assert any("Quality review failed" in rec.message for rec in caplog.records)


# ---------------------------------------------------------------------------
# full_review
# ---------------------------------------------------------------------------

class TestFullReview:
    def test_blocked_status_skips_review(self):
        mock_llm = MagicMock()
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>BLOCKED</status>\nNeed credentials"
        result = reviewer.full_review("task", output)
        assert result["status"] == "BLOCKED"
        assert result["proceed"] is False
        assert result["action"] == "escalate"
        assert "credentials" in result["details"]
        mock_llm.generate_json.assert_not_called()

    def test_needs_context_skips_review(self):
        mock_llm = MagicMock()
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>NEEDS_CONTEXT</status>\nWhich API?"
        result = reviewer.full_review("task", output)
        assert result["status"] == "NEEDS_CONTEXT"
        assert result["proceed"] is False
        assert result["action"] == "clarify"
        mock_llm.generate_json.assert_not_called()

    def test_done_compliant_high_quality_proceeds(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [
            {"compliant": True, "issues": [], "severity": "none"},
            {"score": 80, "issues": [], "suggestions": []},
        ]
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>DONE</status>\nGreat implementation"
        result = reviewer.full_review("build login", output)
        assert result["status"] == "DONE"
        assert result["proceed"] is True
        assert result["action"] == "continue"
        assert result["spec_review"]["compliant"] is True
        assert result["quality_review"]["score"] == 80
        assert result["concerns"] is None

    def test_done_with_concerns_includes_concerns(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [
            {"compliant": True, "issues": [], "severity": "minor"},
            {"score": 70, "issues": [], "suggestions": []},
        ]
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>DONE_WITH_CONCERNS</status>\nMissing edge case"
        result = reviewer.full_review("build API", output)
        assert result["status"] == "DONE_WITH_CONCERNS"
        assert "edge case" in result["concerns"]
        assert result["proceed"] is True

    def test_non_compliant_blocks_quality_review(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.return_value = {
            "compliant": False,
            "issues": ["Wrong feature"],
            "severity": "major",
        }
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>DONE</status>\nWrong thing built"
        result = reviewer.full_review("build X", output)
        assert result["proceed"] is False
        assert result["action"] == "fix_and_retry"
        assert result["quality_review"] is None
        # Only spec review call, no quality call
        assert mock_llm.generate_json.call_count == 1

    def test_compliant_but_critical_severity_blocks(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [
            {"compliant": True, "issues": ["security vuln"], "severity": "critical"},
            {"score": 90, "issues": [], "suggestions": []},
        ]
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>DONE</status>\nImpl"
        result = reviewer.full_review("build secure auth", output)
        assert result["proceed"] is False
        assert result["action"] == "fix_and_retry"

    def test_compliant_but_low_quality_blocks(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [
            {"compliant": True, "issues": [], "severity": "none"},
            {"score": 30, "issues": ["terrible code"], "suggestions": []},
        ]
        reviewer = SubagentReviewer(mock_llm)
        output = "<status>DONE</status>\nBad code"
        result = reviewer.full_review("build feature", output)
        assert result["proceed"] is False
        assert result["action"] == "fix_and_retry"
        assert result["quality_review"]["passed"] is False

    def test_no_status_tag_defaults_done(self):
        mock_llm = MagicMock()
        mock_llm.generate_json.side_effect = [
            {"compliant": True, "issues": [], "severity": "none"},
            {"score": 75, "issues": [], "suggestions": []},
        ]
        reviewer = SubagentReviewer(mock_llm)
        result = reviewer.full_review("task", "output without status")
        assert result["status"] == "DONE"
        assert result["concerns"] is None
        assert result["proceed"] is True
