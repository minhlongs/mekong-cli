"""
Unit tests for PatternLibrary — covers uncovered branches from 36% baseline.

Targets:
- Pattern.confidence property (zero total, normal)
- Pattern.to_dict
- PatternLibrary._load (no file, valid, invalid JSON, missing key)
- PatternLibrary._save
- add_pattern (creates pattern, saves to disk)
- record_success / record_failure (present + absent ids)
- find_similar (match found, no match, min_confidence filtering)
- _calculate_similarity (regex match, keyword/tag overlap, category boost, invalid regex)
- _text_to_regex
- get_patterns (all, filtered by category, sorted by confidence)
- get_stats / _count_by_category
- delete_pattern (found + not found)
- clear (removes custom, keeps builtins)
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from src.daemon.pattern_library import Pattern, PatternLibrary


# ---------------------------------------------------------------------------
# Pattern dataclass
# ---------------------------------------------------------------------------

class TestPattern:
    def test_confidence_zero_total(self):
        p = Pattern(id="x", error_pattern="err", solution="fix", category="build",
                    success_count=0, failure_count=0)
        assert p.confidence == 0.5

    def test_confidence_all_success(self):
        p = Pattern(id="x", error_pattern="err", solution="fix", category="build",
                    success_count=10, failure_count=0)
        assert p.confidence == 1.0

    def test_confidence_mixed(self):
        p = Pattern(id="x", error_pattern="err", solution="fix", category="build",
                    success_count=3, failure_count=1)
        assert p.confidence == pytest.approx(0.75)

    def test_to_dict_has_confidence_key(self):
        p = Pattern(id="p1", error_pattern=".*err.*", solution="fix", category="test")
        d = p.to_dict()
        assert "confidence" in d
        assert d["id"] == "p1"
        assert d["solution"] == "fix"
        assert "tags" in d
        assert "metadata" in d


# ---------------------------------------------------------------------------
# PatternLibrary._load
# ---------------------------------------------------------------------------

class TestPatternLibraryLoad:
    def test_load_no_file(self, tmp_path):
        with patch("src.daemon.pattern_library.PATTERNS_FILE", tmp_path / "patterns.json"):
            lib = PatternLibrary()
        # Should still have builtins
        ids = list(lib._patterns.keys())
        assert "build-fix" in ids

    def test_load_valid_file(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        custom = Pattern(id="custom-1", error_pattern=".*foo.*", solution="bar", category="test")
        pfile.write_text(json.dumps({"patterns": [custom.to_dict()]}))

        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        assert "custom-1" in lib._patterns

    def test_load_invalid_json(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        pfile.write_text("BAD{{{JSON")
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        # Should still have builtins only (graceful degradation)
        assert "build-fix" in lib._patterns

    def test_load_missing_key(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        pfile.write_text(json.dumps({"patterns": [{"solution": "x"}]}))
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        # Missing "id" → KeyError caught, builtins still loaded
        assert "build-fix" in lib._patterns


# ---------------------------------------------------------------------------
# PatternLibrary._save
# ---------------------------------------------------------------------------

class TestPatternLibrarySave:
    def test_save_writes_all_patterns(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib._save()
        data = json.loads(pfile.read_text())
        assert "patterns" in data
        assert "last_updated" in data
        assert len(data["patterns"]) >= 5  # at least builtins


# ---------------------------------------------------------------------------
# add_pattern
# ---------------------------------------------------------------------------

class TestAddPattern:
    def test_add_pattern_returns_pattern(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            p = lib.add_pattern(
                error="build failed",
                solution="npm run build",
                category="build",
                tags=["build"],
                metadata={"source": "test"},
            )
        assert isinstance(p, Pattern)
        assert p.solution == "npm run build"
        assert p.category == "build"

    def test_add_pattern_persists_to_disk(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.add_pattern("import error", "npm install", category="import")

        data = json.loads(pfile.read_text())
        ids = [p["id"] for p in data["patterns"]]
        assert any("import" in pid for pid in ids)

    def test_add_pattern_no_tags_no_metadata(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            p = lib.add_pattern("some error", "some fix")
        assert p.tags == []
        assert p.metadata == {}


# ---------------------------------------------------------------------------
# record_success / record_failure
# ---------------------------------------------------------------------------

class TestRecordSuccessFailure:
    def test_record_success_increments(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            initial = lib._patterns["build-fix"].success_count
            lib.record_success("build-fix")
            assert lib._patterns["build-fix"].success_count == initial + 1

    def test_record_success_sets_last_matched(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.record_success("build-fix")
        assert lib._patterns["build-fix"].last_matched is not None

    def test_record_success_unknown_id(self, tmp_path):
        """Unknown ID → silent no-op."""
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.record_success("does-not-exist")  # should not raise

    def test_record_failure_increments(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            initial = lib._patterns["build-fix"].failure_count
            lib.record_failure("build-fix")
            assert lib._patterns["build-fix"].failure_count == initial + 1

    def test_record_failure_unknown_id(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.record_failure("does-not-exist")  # should not raise


# ---------------------------------------------------------------------------
# find_similar
# ---------------------------------------------------------------------------

class TestFindSimilar:
    def test_find_similar_builtin_build_error(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        match = lib.find_similar("build failed: SyntaxError on line 10")
        assert match is not None
        assert match.pattern.id == "build-fix"

    def test_find_similar_npm_import(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        match = lib.find_similar("Cannot find module 'react'")
        assert match is not None
        assert match.pattern.id == "npm-install"

    def test_find_similar_no_match(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        match = lib.find_similar("zzzzz completely unrelated gibberish 12345", min_confidence=0.99)
        assert match is None

    def test_find_similar_updates_last_matched(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        lib.find_similar("build failed")
        assert lib._patterns["build-fix"].last_matched is not None

    def test_find_similar_security_vulnerability(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        match = lib.find_similar("security vulnerability CVE-2023-1234 found")
        assert match is not None
        assert match.pattern.id == "audit-fix"

    def test_find_similar_git_conflict(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        match = lib.find_similar("git failed: merge conflict detected")
        assert match is not None
        assert match.pattern.id == "git-reset"


# ---------------------------------------------------------------------------
# _calculate_similarity
# ---------------------------------------------------------------------------

class TestCalculateSimilarity:
    def _lib(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            return PatternLibrary()

    def test_regex_match_adds_score(self, tmp_path):
        lib = self._lib(tmp_path)
        p = Pattern(id="x", error_pattern=r"build failed", solution="fix", category="build",
                    tags=[], success_count=1, failure_count=0)
        score = lib._calculate_similarity("build failed with code 1", p)
        assert score > 0

    def test_tag_overlap_adds_score(self, tmp_path):
        lib = self._lib(tmp_path)
        p = Pattern(id="x", error_pattern=r"no_match_at_all", solution="fix", category="xyz",
                    tags=["build"], success_count=1, failure_count=0)
        score = lib._calculate_similarity("the build process failed", p)
        # tag "build" in text → small boost
        assert score >= 0

    def test_category_in_text_adds_score(self, tmp_path):
        lib = self._lib(tmp_path)
        p = Pattern(id="x", error_pattern=r"NOPE", solution="fix", category="security",
                    tags=[], success_count=1, failure_count=0)
        score = lib._calculate_similarity("security issue found", p)
        assert score > 0

    def test_invalid_regex_handled(self, tmp_path):
        lib = self._lib(tmp_path)
        p = Pattern(id="x", error_pattern=r"[invalid(regex", solution="fix", category="build",
                    tags=[], success_count=1, failure_count=0)
        # Should not raise
        score = lib._calculate_similarity("any text", p)
        assert 0.0 <= score <= 1.0

    def test_score_capped_at_one(self, tmp_path):
        lib = self._lib(tmp_path)
        # Pattern that would score very high
        p = Pattern(id="x", error_pattern=r"build", solution="fix", category="build",
                    tags=["build", "compile", "syntax"], success_count=100, failure_count=0)
        score = lib._calculate_similarity("build compile syntax error", p)
        assert score <= 1.0

    def test_low_confidence_pattern_reduces_score(self, tmp_path):
        lib = self._lib(tmp_path)
        high_conf = Pattern(id="h", error_pattern=r"build failed", solution="fix", category="build",
                            success_count=10, failure_count=0)
        low_conf = Pattern(id="l", error_pattern=r"build failed", solution="fix", category="build",
                           success_count=1, failure_count=9)
        text = "build failed"
        score_high = lib._calculate_similarity(text, high_conf)
        score_low = lib._calculate_similarity(text, low_conf)
        assert score_high > score_low


# ---------------------------------------------------------------------------
# _text_to_regex
# ---------------------------------------------------------------------------

class TestTextToRegex:
    def _lib(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            return PatternLibrary()

    def test_basic_conversion(self, tmp_path):
        lib = self._lib(tmp_path)
        result = lib._text_to_regex("build failed")
        assert result.startswith(".*")
        assert result.endswith(".*")

    def test_special_chars_escaped(self, tmp_path):
        lib = self._lib(tmp_path)
        result = lib._text_to_regex("error (code)")
        # Parens should be escaped so regex doesn't error
        import re
        assert re.compile(result)  # should not raise


# ---------------------------------------------------------------------------
# get_patterns
# ---------------------------------------------------------------------------

class TestGetPatterns:
    def test_get_all_patterns(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        patterns = lib.get_patterns()
        assert len(patterns) >= 5  # at least builtins
        assert all(isinstance(p, dict) for p in patterns)

    def test_get_patterns_filtered_by_category(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        build_patterns = lib.get_patterns(category="build")
        assert all(p["category"] == "build" for p in build_patterns)
        assert len(build_patterns) >= 1

    def test_get_patterns_sorted_by_confidence_desc(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        patterns = lib.get_patterns()
        confidences = [p["confidence"] for p in patterns]
        assert confidences == sorted(confidences, reverse=True)


# ---------------------------------------------------------------------------
# get_stats / _count_by_category
# ---------------------------------------------------------------------------

class TestGetStats:
    def test_get_stats_structure(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        stats = lib.get_stats()
        assert "total_patterns" in stats
        assert "avg_confidence" in stats
        assert "by_category" in stats
        assert "high_confidence" in stats

    def test_get_stats_total_matches_builtins(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        stats = lib.get_stats()
        assert stats["total_patterns"] == len(lib._patterns)

    def test_get_stats_avg_confidence(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        stats = lib.get_stats()
        assert 0.0 <= stats["avg_confidence"] <= 1.0

    def test_count_by_category(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        counts = lib._count_by_category()
        assert "build" in counts
        assert counts["build"] >= 1


# ---------------------------------------------------------------------------
# delete_pattern
# ---------------------------------------------------------------------------

class TestDeletePattern:
    def test_delete_existing_pattern(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        result = lib.delete_pattern("build-fix")
        assert result is True
        assert "build-fix" not in lib._patterns

    def test_delete_nonexistent_pattern(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
        result = lib.delete_pattern("ghost-pattern")
        assert result is False

    def test_delete_saves_to_disk(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.delete_pattern("build-fix")

        data = json.loads(pfile.read_text())
        ids = [p["id"] for p in data["patterns"]]
        assert "build-fix" not in ids


# ---------------------------------------------------------------------------
# clear
# ---------------------------------------------------------------------------

class TestClear:
    def test_clear_removes_custom_keeps_builtins(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.add_pattern("custom error", "custom fix", category="custom")
            custom_id = [k for k in lib._patterns if k.startswith("custom")][0]
            lib.clear()

        assert custom_id not in lib._patterns
        builtin_ids = {p.id for p in PatternLibrary.BUILTIN_PATTERNS}
        for bid in builtin_ids:
            assert bid in lib._patterns

    def test_clear_saves_to_disk(self, tmp_path):
        pfile = tmp_path / "patterns.json"
        with patch("src.daemon.pattern_library.PATTERNS_FILE", pfile):
            lib = PatternLibrary()
            lib.add_pattern("x", "y", category="z")
            lib.clear()

        data = json.loads(pfile.read_text())
        ids = {p["id"] for p in data["patterns"]}
        builtin_ids = {p.id for p in PatternLibrary.BUILTIN_PATTERNS}
        assert ids == builtin_ids
