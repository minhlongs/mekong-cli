"""Tests for the constitutional sandbox engine (Phase 5).

Test fixtures are derived from ``format_schema`` constants rather than from
hand-written examples to ensure the parser and rule engine stay in sync with
the shared format contract.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from src.mekong.constitution.format_schema import (
    CONSTITUTION_HEADER_PATTERN,
    MAX_LINES,
    MIN_ARTICLES,
)
from src.mekong.constitution.parser import (
    parse_constitution,
    Article,
    Constitution,
)
from src.mekong.constitution.review import review_constitution
from src.mekong.constitution.rules import RULES

# ---------------------------------------------------------------------------
# Helpers to build test fixtures from format_schema constants
# ---------------------------------------------------------------------------

# Minimum number of articles needed to pass the parser's MIN_ARTICLES gate.
_MIN_VIABLE = MIN_ARTICLES  # 3


def _make_constitution(
    articles: list[tuple[int, str, str]],
    preamble: str = "",
) -> str:
    """Build a constitution markdown string from structured article data.

    Each tuple is ``(number, title, content)``.
    """
    lines = [preamble] if preamble else []
    first = True
    for num, title, content in articles:
        if first and not preamble:
            lines.append("# ZenOS Test Constitution")
            first = False
        elif first:
            first = False
        lines.append(f"\n## Article {num}: {title}")
        if content:
            lines.append(content)
    return "\n".join(lines)


def _write_temp(text: str) -> Path:
    """Write *text* to a temporary file and return its ``Path``."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".md",
        delete=False,
        encoding="utf-8",
    )
    tmp.write(text)
    tmp.close()
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------


class TestParser:
    def test_parse_valid(self):
        """A well-formed constitution parses correctly."""
        md = _make_constitution([
            (1, "Mission Integrity", "This is the mission."),
            (2, "Right to Exit", "You may exit."),
            (3, "Anti-Capture and Evolution", "No capture."),
        ])
        path = _write_temp(md)
        constitution = parse_constitution(path)
        os.unlink(path)

        assert isinstance(constitution, Constitution)
        assert len(constitution.articles) >= _MIN_VIABLE
        assert constitution.articles[0].title == "Mission Integrity"
        assert constitution.articles[0].number == 1
        assert constitution.articles[1].category == "exit"
        assert constitution.articles[2].category == "governance"

    def test_parse_classifies_categories(self):
        """Articles are classified into the correct categories."""
        md = _make_constitution([
            (1, "Mission and Purpose", "Our mission."),
            (2, "Governance Model", "How we decide."),
            (3, "AI Cells", "AI limits."),
            (4, "Token Economics", "Reward distribution."),
            (5, "Right to Exit", "Leave anytime."),
            (6, "Open Commons", "Shared resources."),
        ])
        path = _write_temp(md)
        c = parse_constitution(path)
        os.unlink(path)

        assert c.categories == sorted(["mission", "governance", "ai_cells",
                                       "economics", "exit", "commons"])

    def test_parse_missing_file(self):
        """Non-existent file raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            parse_constitution("/nonexistent/path.md")

    def test_parse_fewer_than_min_articles(self):
        """Fewer than MIN_ARTICLES raises ValueError."""
        md = _make_constitution([
            (1, "Mission", "One article."),
        ])
        path = _write_temp(md)
        with pytest.raises(ValueError, match="minimum"):
            parse_constitution(path)
        os.unlink(path)

    def test_parse_too_many_lines(self):
        """More than MAX_LINES raises ValueError."""
        articles = [(i + 1, f"Article {i + 1}", "x") for i in range(20)]
        md = _make_constitution(articles, preamble="# Header\n")
        # Pad with blank lines to exceed MAX_LINES
        extra_lines = "\n" * (MAX_LINES - len(md.split("\n")) + 5)
        md += extra_lines

        path = _write_temp(md)
        with pytest.raises(ValueError, match="exceeds"):
            parse_constitution(path)
        os.unlink(path)

    def test_parse_single_hash_header_rejected(self):
        """A bare ``# heading`` inside the body (after an article) is rejected."""
        md = (
            "## Article 1: Mission\n\nTest.\n\n"
            "# Invalid Body Header\n\n"
            "## Article 2: Exit\n\nExit.\n\n"
            "## Article 3: Governance\n\nGovern.\n"
        )
        path = _write_temp(md)
        with pytest.raises(ValueError, match="unauthorised"):
            parse_constitution(path)
        os.unlink(path)

    def test_parse_triple_hash_allowed(self):
        """Triple-hash headers within articles are allowed."""
        md = _make_constitution([
            (1, "Mission", "Mission text.\n### Subsection\nDetails."),
            (2, "Exit", "Exit content."),
            (3, "Governance", "Governance content."),
        ])
        path = _write_temp(md)
        constitution = parse_constitution(path)
        os.unlink(path)
        assert "### Subsection" in constitution.articles[0].content

    def test_parse_article_with_multiline_content(self):
        """Articles capture multi-line content correctly."""
        md = _make_constitution([
            (1, "Mission", "Line one.\nLine two.\n\nLine three."),
            (2, "Exit", "Exit content."),
            (3, "Governance", "Governance content."),
        ])
        path = _write_temp(md)
        c = parse_constitution(path)
        os.unlink(path)
        assert "Line one." in c.articles[0].content
        assert "Line three." in c.articles[0].content

    def test_parse_header_regex(self):
        """The header pattern from format_schema matches correctly."""
        import re
        pattern = re.compile(CONSTITUTION_HEADER_PATTERN, re.MULTILINE)
        m = pattern.match("## Article 1: Mission Integrity")
        assert m is not None
        assert m.group(1) == "1"
        assert m.group(2) == "Mission Integrity"


# ---------------------------------------------------------------------------
# Rule tests
# ---------------------------------------------------------------------------


class TestRules:
    def test_missing_mission(self):
        """P0 FAIL: Missing mission article."""
        md = _make_constitution([
            (1, "Right to Exit", "Exit."),
            (2, "Anti-Capture and Evolution", "No capture."),
            (3, "Economics", "Economic rules."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        assert result.verdict == "FAIL"
        ids = [f["id"] for f in result.fails]
        assert "MISSION_REQUIRED" in ids

    def test_missing_right_to_exit(self):
        """P0 FAIL: Missing right to exit article."""
        md = _make_constitution([
            (1, "Mission Integrity", "Mission."),
            (2, "Anti-Capture and Evolution", "No capture."),
            (3, "Economics", "Economic rules."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        assert result.verdict == "FAIL"
        ids = [f["id"] for f in result.fails]
        assert "EXIT_REQUIRED" in ids

    def test_missing_anti_capture(self):
        """P0 FAIL: Missing anti-capture article."""
        md = _make_constitution([
            (1, "Mission Integrity", "Mission."),
            (2, "Right to Exit", "Exit."),
            (3, "Economics", "Economic rules."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        assert result.verdict == "FAIL"
        ids = [f["id"] for f in result.fails]
        assert "ANTI_CAPTURE_REQUIRED" in ids

    def test_contradictory_governance(self):
        """P0 FAIL: Contradictory governance provisions in same article."""
        md = _make_constitution([
            (1, "Mission Integrity",
             "This particle's mission is to serve the community."),
            (2, "Governance",
             "The founder makes all decisions unilaterally. "
             "The community votes on all decisions through consensus."),
            (3, "Right to Exit", "Members may leave at any time."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        ids = [f["id"] for f in result.fails]
        assert "NO_SELF_CONTRADICTION" in ids

    def test_empty_article_content(self):
        """P0 FAIL: Article with empty content."""
        md = _make_constitution([
            (1, "Mission Integrity", ""),
            (2, "Right to Exit", "Exit content."),
            (3, "Anti-Capture and Evolution", "Anti-capture."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        ids = [f["id"] for f in result.fails]
        assert "NONEMPTY_ARTICLES" in ids

    def test_valid_constitution(self):
        """Valid constitution passes all P0 checks and has no FAIL results."""
        md = _make_constitution([
            (1, "Mission Integrity",
             "Our mission is to serve the community through shared value."),
            (2, "Anti-Capture and Evolution",
             "No single agent may control the particle. "
             "Multi-sig treasury required. Governance "
             "follows separation of powers."),
            (3, "Right to Exit",
             "Participants may exit at any time."),
            (4, "AI Cell Boundaries",
             "AI agents operate within defined boundaries. "
             "Automation limits are set by governance vote."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        fail_ids = [f["id"] for f in result.fails]
        assert not fail_ids, f"Expected no FAIL results, got: {fail_ids}"

    def test_adversarial_pattern_absolute_authority(self):
        """P1 WARNING: Absolute authority pattern detected."""
        md = _make_constitution([
            (1, "Mission Integrity", "Serve the community."),
            (2, "Governance",
             "The founder has absolute authority over all decisions."),
            (3, "Right to Exit", "Exit anytime."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        warn_ids = [w["id"] for w in result.warnings]
        assert "ADVERSARIAL_PATTERN" in warn_ids

    def test_adversarial_pattern_unilateral_amendment(self):
        """P1 WARNING: Unilateral amendment detected."""
        md = _make_constitution([
            (1, "Mission Integrity", "Our mission is clear."),
            (2, "Governance",
             "The founder alone may amend this constitution."),
            (3, "Right to Exit", "Exit anytime."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        warn_ids = [w["id"] for w in result.warnings]
        assert "ADVERSARIAL_PATTERN" in warn_ids

    def test_adversarial_pattern_broad_mission(self):
        """P1 WARNING: Overly broad mission."""
        md = _make_constitution([
            (1, "Mission Integrity",
             "Our mission is to do anything and everything."),
            (2, "Anti-Capture", "Oversight committee."),
            (3, "Right to Exit", "Exit anytime."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        warn_ids = [w["id"] for w in result.warnings]
        assert "ADVERSARIAL_PATTERN" in warn_ids

    def test_anti_concentration_warning(self):
        """P1 WARNING: No anti-concentration mechanisms."""
        md = _make_constitution([
            (1, "Mission Integrity", "Serve the mission."),
            (2, "Governance",
             "The leader decides everything."),
            (3, "Right to Exit", "Exit anytime."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        warn_ids = [w["id"] for w in result.warnings]
        assert "ANTI_CONCENTRATION" in warn_ids

    def test_ai_boundaries_warning(self):
        """P1 WARNING: No AI boundaries defined."""
        md = _make_constitution([
            (1, "Mission Integrity", "Serve the mission."),
            (2, "Anti-Capture", "Multi-sig oversight committee."),
            (3, "Right to Exit", "Exit anytime."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        warn_ids = [w["id"] for w in result.warnings]
        assert "AI_BOUNDARIES" in warn_ids


# ---------------------------------------------------------------------------
# Full-integration tests
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_particle_init_review_valid(self):
        """End-to-end: review a valid constitution -> no FAIL results."""
        md = _make_constitution([
            (1, "Mission Integrity",
             "Our mission is to build great things together."),
            (2, "Anti-Capture and Evolution",
             "Multi-sig treasury with board oversight and term limits."),
            (3, "Right to Exit",
             "Any participant may exit at any time."),
            (4, "AI Boundaries",
             "AI agents must operate within governance limits."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        fail_ids = [f["id"] for f in result.fails]
        assert not fail_ids, f"Expected no FAIL results, got: {fail_ids}"

    def test_particle_init_review_fail(self):
        """End-to-end: review an adversarial constitution -> FAIL."""
        md = _make_constitution([
            (1, "Operation Control",
             "The founding agent has absolute power."),
            (2, "Rewards",
             "All revenue goes to the founder."),
            (3, "Data",
             "All data belongs to the founder."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        assert result.verdict == "FAIL"
        fail_ids = [f["id"] for f in result.fails]
        assert "MISSION_REQUIRED" in fail_ids
        assert "EXIT_REQUIRED" in fail_ids

    def test_ostrom_principles_counted(self):
        """Ostrom principle counting is accurate."""
        md = _make_constitution([
            (1, "Mission Integrity",
             "Clear membership: who may join and participate."),
            (2, "Governance",
             "Collective decision-making. Proportional "
             "distribution of rewards. Monitoring and audit. "
             "Graduated sanctions for violations. "
             "Conflict resolution via arbitration."),
            (3, "Right to Exit",
             "Right to organize autonomously. "
             "Nested multi-level governance structure."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        # The Ostrom info result should mention the count
        ostrom_results = [
            i for i in result.infos
            if i["id"] == "OSTROM_PRINCIPLES"
        ]
        assert len(ostrom_results) == 1
        assert "Ostrom" in ostrom_results[0]["message"]

    def test_review_output_format(self):
        """ReviewResult.format() produces expected structure."""
        md = _make_constitution([
            (1, "Mission Integrity", "Mission."),
            (2, "Right to Exit", "Exit."),
            (3, "Anti-Capture and Evolution", "No capture."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        output = result.format()
        assert "CONSTITUTIONAL REVIEW" in output
        assert "PASS" in output or "FAIL" in output or "WARNINGS" in output
        assert "Articles:" in output
        assert "Lines:" in output


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_parser_edge_empty_file(self):
        """An empty file raises ValueError."""
        path = _write_temp("")
        with pytest.raises(ValueError, match="minimum"):
            parse_constitution(path)
        os.unlink(path)

    def test_parser_no_markdown_headers(self):
        """File with no article headers raises ValueError."""
        path = _write_temp("Just some text.\n\nNo headers here.")
        with pytest.raises(ValueError, match="minimum"):
            parse_constitution(path)
        os.unlink(path)

    def test_review_whitespace_only_articles(self):
        """Articles with only whitespace are considered empty (P0 FAIL)."""
        md = _make_constitution([
            (1, "Mission Integrity", "   \n\n  "),
            (2, "Right to Exit", "  "),
            (3, "Anti-Capture and Evolution", "Anti-capture content."),
        ])
        path = _write_temp(md)
        result = review_constitution(path)
        os.unlink(path)
        fail_ids = [f["id"] for f in result.fails]
        assert "NONEMPTY_ARTICLES" in fail_ids

    def test_review_nonexistent_file(self):
        """review_constitution on a missing file raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            review_constitution("/does/not/exist.md")

    def test_constitution_property_article_titles(self):
        """Constitution.article_titles returns correct titles."""
        md = _make_constitution([
            (1, "Mission Integrity", "A"),
            (2, "Right to Exit", "B"),
            (3, "Anti-Capture and Evolution", "C"),
        ])
        path = _write_temp(md)
        c = parse_constitution(path)
        os.unlink(path)
        assert c.article_titles == ["Mission Integrity", "Right to Exit",
                                    "Anti-Capture and Evolution"]

    def test_constitution_property_missing_required(self):
        """Constitution.missing_required identifies missing articles."""
        md = _make_constitution([
            (1, "Mission Integrity", "A"),
            (2, "Right to Exit", "B"),
            (3, "Anti-Capture and Evolution", "C"),
        ])
        path = _write_temp(md)
        c = parse_constitution(path)
        os.unlink(path)
        missing = c.missing_required()
        assert isinstance(missing, list)
        assert len(missing) == 0  # All required articles present

    def test_get_article_by_number(self):
        """Constitution.get_article_by_number returns correct article."""
        md = _make_constitution([
            (1, "Mission Integrity", "A"),
            (2, "Right to Exit", "B"),
            (3, "Anti-Capture and Evolution", "C"),
        ])
        path = _write_temp(md)
        c = parse_constitution(path)
        os.unlink(path)
        art = c.get_article_by_number(2)
        assert art is not None
        assert art.title == "Right to Exit"
        assert c.get_article_by_number(99) is None
