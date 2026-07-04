"""Tests for Founder Genome Core Module — types, questions, scoring."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mekong.founder import (
    BIAS_DIMENSION_MAP,
    BIAS_QUESTIONS,
    FEAR_FIELDS,
    FEAR_QUESTIONS,
    RISK_DIMENSIONS,
    RISK_QUESTIONS,
    SCHWARTZ_VALUES,
    TIPI_QUESTIONS,
    FounderGenome,
    classify_risk_level,
    extract_biases,
    score_big_five,
    score_risk,
)


# ---------------------------------------------------------------------------
# types.py — FounderGenome dataclass creation
# ---------------------------------------------------------------------------


class TestTypesCreate:
    """FounderGenome dataclass construction."""

    def test_minimal_creation(self) -> None:
        """A FounderGenome can be created with required fields."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at="2026-07-04T12:00:00+00:00",
            particle_id=None,
            mission="Build the next-generation AI platform",
            values=["self_direction", "achievement"],
            big_five={
                "openness": 85,
                "conscientiousness": 72,
                "extraversion": 45,
                "agreeableness": 60,
                "neuroticism": 30,
            },
            fears=[
                {
                    "trigger": "Losing key engineer",
                    "predicted_behavior": "Micromanage hiring",
                    "mitigation": "Build redundancy early",
                }
            ],
            risk_profile={
                "financial": 70,
                "operational": 50,
                "reputational": 40,
                "compliance": 30,
                "technical": 80,
            },
            cognitive_biases=["confirmation_bias", "optimism_bias"],
            risk_level="aggressive",
        )
        assert genome.version == "1.0.0"
        assert genome.particle_id is None
        assert genome.risk_level == "aggressive"
        assert len(genome.values) == 2
        assert len(genome.fears) == 1
        assert len(genome.cognitive_biases) == 2
        assert genome.notes == []

    def test_with_notes(self) -> None:
        """Caveats documented in notes field are preserved."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at=datetime.now(timezone.utc).isoformat(),
            particle_id="particle_abc123",
            mission="Democratize AI",
            values=["universalism"],
            big_five={k: 50 for k in ("openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism")},
            fears=[],
            risk_profile={k: 50 for k in ("financial", "operational", "reputational", "compliance", "technical")},
            cognitive_biases=[],
            risk_level="moderate",
            notes=[
                "Self-reported data — may not reflect actual behavior under pressure.",
                "TIPI-10 is a brief screening, not clinical diagnosis.",
            ],
        )
        assert len(genome.notes) == 2
        assert "self-reported" in genome.notes[0].lower()

    def test_field_types(self) -> None:
        """All fields have correct types."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at="2026-07-04T12:00:00Z",
            particle_id="p_001",
            mission="Test",
            values=["power"],
            big_five={"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
            fears=[{"trigger": "A", "predicted_behavior": "B", "mitigation": "C"}],
            risk_profile={"financial": 50, "operational": 50, "reputational": 50, "compliance": 50, "technical": 50},
            cognitive_biases=["anchoring"],
            risk_level="moderate",
        )
        assert isinstance(genome.version, str)
        assert isinstance(genome.assessed_at, str)
        assert isinstance(genome.particle_id, str | None)
        assert isinstance(genome.mission, str)
        assert isinstance(genome.values, list)
        assert isinstance(genome.big_five, dict)
        assert isinstance(genome.fears, list)
        assert isinstance(genome.risk_profile, dict)
        assert isinstance(genome.cognitive_biases, list)
        assert isinstance(genome.risk_level, str)
        assert isinstance(genome.notes, list)


# ---------------------------------------------------------------------------
# questions.py — question set counts and structure
# ---------------------------------------------------------------------------


class TestQuestions:
    """Question set definitions."""

    def test_tipi_count(self) -> None:
        """TIPI-10 has exactly 10 questions."""
        assert len(TIPI_QUESTIONS) == 10

    def test_tipi_structure(self) -> None:
        """Each TIPI question has required fields."""
        required = {"id", "text", "type", "options", "dimension"}
        for q in TIPI_QUESTIONS:
            assert required.issubset(q.keys()), f"Missing fields in {q['id']}"
            assert q["type"] == "likert_7"

    def test_tipi_dimension_coverage(self) -> None:
        """All 5 Big Five dimensions appear exactly twice (one normal, one reverse)."""
        from collections import Counter

        dim_counts: dict[str, int] = Counter()
        rev_counts: dict[str, int] = Counter()
        for q in TIPI_QUESTIONS:
            dim_counts[q["dimension"]] += 1
            if q.get("reverse_scored"):
                rev_counts[q["dimension"]] += 1

        for dim in ("extraversion", "agreeableness", "conscientiousness", "emotional_stability", "openness"):
            assert dim_counts[dim] == 2, f"{dim} should have 2 questions"
            assert rev_counts[dim] == 1, f"{dim} should have 1 reverse-scored question"

    def test_schwartz_values_count(self) -> None:
        """There are exactly 10 Schwartz values."""
        assert len(SCHWARTZ_VALUES) == 10

    def test_schwartz_values_have_ids(self) -> None:
        """Each Schwartz value has an id, label, and description."""
        for sv in SCHWARTZ_VALUES:
            assert "id" in sv
            assert "label" in sv
            assert "description" in sv

    def test_fear_fields_constant(self) -> None:
        """FEAR_FIELDS has exactly 3 field names."""
        assert FEAR_FIELDS == ["trigger", "predicted_behavior", "mitigation"]

    def test_fear_questions_count(self) -> None:
        """Fear questions represent 5 scenarios × 3 fields = 15 questions."""
        assert len(FEAR_QUESTIONS) == 15

    def test_fear_questions_rotation(self) -> None:
        """Fear questions cycle through trigger, predicted_behavior, mitigation."""
        fields = [q["field"] for q in FEAR_QUESTIONS]
        expected = (FEAR_FIELDS * 5)[:15]
        assert fields == expected, "Fear questions should cycle through fields"

    def test_risk_dimensions(self) -> None:
        """RISK_DIMENSIONS has exactly 5 dimensions."""
        assert RISK_DIMENSIONS == ["financial", "operational", "reputational", "compliance", "technical"]

    def test_risk_questions_count(self) -> None:
        """There is exactly 1 risk question per dimension = 5 questions."""
        assert len(RISK_QUESTIONS) == 5

    def test_risk_questions_dimensions_match(self) -> None:
        """Risk question dimensions match RISK_DIMENSIONS."""
        dims = {q["dimension"] for q in RISK_QUESTIONS}
        assert dims == set(RISK_DIMENSIONS)

    def test_bias_questions_count(self) -> None:
        """There are exactly 10 bias questions."""
        assert len(BIAS_QUESTIONS) == 10

    def test_bias_question_structure(self) -> None:
        """Each bias question has required fields and is yes/no type."""
        required = {"id", "text", "type", "options", "dimension"}
        for q in BIAS_QUESTIONS:
            assert required.issubset(q.keys()), f"Missing fields in {q['id']}"
            assert q["type"] == "yes_no"

    def test_bias_dimension_coverage(self) -> None:
        """Bias questions cover all expected dimensions."""
        dims = sorted(q["dimension"] for q in BIAS_QUESTIONS)
        expected = sorted([
            "confirmation_bias",
            "overconfidence",
            "sunk_cost_fallacy",
            "planning_fallacy",
            "self_serving_bias",
            "anchoring",
            "availability_heuristic",
            "framing_effect",
            "status_quo_bias",
            "optimism_bias",
        ])
        assert dims == expected


# ---------------------------------------------------------------------------
# scoring.py — scoring algorithm tests
# ---------------------------------------------------------------------------


class TestBigFiveScoring:
    """Big Five personality scoring."""

    def test_mid_range_responses(self) -> None:
        """All-neutral responses (4) produce mid-range scores (~50)."""
        responses = {f"tipi_{i:02d}": 4 for i in range(1, 11)}
        scores = score_big_five(responses)
        for dim in ("openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"):
            assert 40 <= scores[dim] <= 60, f"{dim} = {scores[dim]} should be near 50"

    def test_max_extraversion(self) -> None:
        """All max responses on extraversion items produce high score."""
        responses = {
            "tipi_01": 7,  # Extraverted, enthusiastic (normal)
            "tipi_02": 1,  # Critical, quarrelsome (reverse) — low = agreeable
            "tipi_03": 7,  # Dependable (normal)
            "tipi_04": 1,  # Anxious (reverse) — low = emotionally stable
            "tipi_05": 7,  # Open (normal)
            "tipi_06": 1,  # Reserved (reverse) — low = extraverted
            "tipi_07": 7,  # Sympathetic (normal)
            "tipi_08": 1,  # Disorganized (reverse) — low = conscientious
            "tipi_09": 7,  # Calm (normal)
            "tipi_10": 1,  # Conventional (reverse) — low = open
        }
        scores = score_big_five(responses)
        assert scores["extraversion"] >= 90, f"extraversion = {scores['extraversion']}"

    def test_reverse_scoring(self) -> None:
        """Reverse-scored items produce inverse values."""
        # High on a reverse item + low on normal item = low dimension score
        responses = {
            "tipi_01": 1,  # Extraverted: low
            "tipi_02": 7,  # Critical (reverse): high → low agreeableness
            "tipi_03": 1,  # Dependable: low
            "tipi_04": 7,  # Anxious (reverse): high → low emotional stability
            "tipi_05": 1,  # Open: low
            "tipi_06": 7,  # Reserved (reverse): high → low extraversion
            "tipi_07": 1,  # Sympathetic: low
            "tipi_08": 7,  # Disorganized (reverse): high → low conscientiousness
            "tipi_09": 1,  # Calm: low
            "tipi_10": 7,  # Conventional (reverse): high → low openness
        }
        scores = score_big_five(responses)
        for dim in ("openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"):
            assert scores[dim] <= 30, f"{dim} = {scores[dim]} should be low"

    def test_normalization_range(self) -> None:
        """All scores are clamped to 1-100 range."""
        responses = {f"tipi_{i:02d}": 4 for i in range(1, 11)}
        scores = score_big_five(responses)
        for val in scores.values():
            assert 1 <= val <= 100, f"Score {val} out of range"

    def test_neuroticism_derived(self) -> None:
        """Neuroticism is the inverse of emotional stability."""
        responses = {f"tipi_{i:02d}": 4 for i in range(1, 11)}
        scores = score_big_five(responses)
        assert scores["neuroticism"] == 101 - scores["emotional_stability"]

    def test_has_all_dimensions(self) -> None:
        """Output contains all expected Big Five dimensions plus neuroticism."""
        responses = {f"tipi_{i:02d}": 4 for i in range(1, 11)}
        scores = score_big_five(responses)
        expected = {"openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability", "neuroticism"}
        assert set(scores.keys()) == expected


class TestRiskScoring:
    """Risk profile scoring."""

    def test_correct_average(self) -> None:
        """Risk scores multiplied by 10 from 1-10 to 10-100."""
        ratings = {
            "financial": 5,
            "operational": 5,
            "reputational": 5,
            "compliance": 5,
            "technical": 5,
        }
        scores = score_risk(ratings)
        for dim in RISK_DIMENSIONS:
            assert scores[dim] == 50, f"{dim} should be 50, got {scores[dim]}"

    def test_minimum_risk(self) -> None:
        """Minimum rating 1 → score 10."""
        ratings = {dim: 1 for dim in RISK_DIMENSIONS}
        scores = score_risk(ratings)
        for dim in RISK_DIMENSIONS:
            assert scores[dim] == 10, f"{dim} should be 10, got {scores[dim]}"

    def test_maximum_risk(self) -> None:
        """Maximum rating 10 → score 100."""
        ratings = {dim: 10 for dim in RISK_DIMENSIONS}
        scores = score_risk(ratings)
        for dim in RISK_DIMENSIONS:
            assert scores[dim] == 100, f"{dim} should be 100, got {scores[dim]}"

    def test_asymmetric_ratings(self) -> None:
        """Different ratings per dimension produce correct scores."""
        ratings = {
            "financial": 3,
            "operational": 7,
            "reputational": 5,
            "compliance": 2,
            "technical": 9,
        }
        scores = score_risk(ratings)
        assert scores["financial"] == 30
        assert scores["operational"] == 70
        assert scores["reputational"] == 50
        assert scores["compliance"] == 20
        assert scores["technical"] == 90

    def test_output_dimensions(self) -> None:
        """Output contains all expected risk dimensions."""
        ratings = {dim: 5 for dim in RISK_DIMENSIONS}
        scores = score_risk(ratings)
        assert set(scores.keys()) == set(RISK_DIMENSIONS)


class TestBiasClassification:
    """Risk level classification."""

    def test_conservative_by_bias_count(self) -> None:
        """0-3 biases classifies as conservative regardless of risk score."""
        high_risk = {dim: 100 for dim in RISK_DIMENSIONS}
        result = classify_risk_level(bias_count=2, risk_scores=high_risk)
        assert result == "conservative"

    def test_conservative_by_risk(self) -> None:
        """Average risk < 4 (1-10 scale) classifies as conservative."""
        low_risk = {dim: 30 for dim in RISK_DIMENSIONS}  # avg = 3.0 on 1-10
        result = classify_risk_level(bias_count=5, risk_scores=low_risk)
        assert result == "conservative"

    def test_moderate_by_bias_count(self) -> None:
        """4-6 biases with moderate risk classifies as moderate."""
        moderate_risk = {dim: 60 for dim in RISK_DIMENSIONS}  # avg = 6.0
        result = classify_risk_level(bias_count=5, risk_scores=moderate_risk)
        assert result == "moderate"

    def test_moderate_by_risk(self) -> None:
        """Average risk < 7 but >= 4 classifies as moderate."""
        moderate_risk = {dim: 50 for dim in RISK_DIMENSIONS}  # avg = 5.0
        result = classify_risk_level(bias_count=8, risk_scores=moderate_risk)
        assert result == "moderate"

    def test_aggressive_by_both(self) -> None:
        """7+ biases and avg risk >= 7 classifies as aggressive."""
        high_risk = {dim: 80 for dim in RISK_DIMENSIONS}  # avg = 8.0
        result = classify_risk_level(bias_count=8, risk_scores=high_risk)
        assert result == "aggressive"

    def test_aggressive_high_bias_high_risk(self) -> None:
        """High bias + high risk = aggressive."""
        high_risk = {dim: 90 for dim in RISK_DIMENSIONS}
        result = classify_risk_level(bias_count=10, risk_scores=high_risk)
        assert result == "aggressive"

    def test_conservative_zero_bias(self) -> None:
        """Zero biases classifies as conservative."""
        high_risk = {dim: 100 for dim in RISK_DIMENSIONS}
        result = classify_risk_level(bias_count=0, risk_scores=high_risk)
        assert result == "conservative"

    def test_boundary_bias_three_to_four(self) -> None:
        """3 biases is still conservative, 4 biases can be moderate with high risk."""
        high_risk = {dim: 100 for dim in RISK_DIMENSIONS}
        assert classify_risk_level(bias_count=3, risk_scores=high_risk) == "conservative"
        # 4 biases with high risk → not conservative (risk doesn't trigger conservative)
        result = classify_risk_level(bias_count=4, risk_scores=high_risk)
        assert result in ("moderate", "aggressive")

    def test_boundary_bias_six_to_seven(self) -> None:
        """6 biases with high risk is moderate, 7 biases is aggressive."""
        moderate_risk = {dim: 65 for dim in RISK_DIMENSIONS}  # avg = 6.5
        result_6 = classify_risk_level(bias_count=6, risk_scores=moderate_risk)
        assert result_6 == "moderate"
        result_7 = classify_risk_level(bias_count=7, risk_scores=moderate_risk)
        assert result_7 in ("moderate", "aggressive")

    def test_returns_string(self) -> None:
        """Classification returns one of three expected strings."""
        low_risk = {dim: 10 for dim in RISK_DIMENSIONS}
        result = classify_risk_level(bias_count=1, risk_scores=low_risk)
        assert result in ("conservative", "moderate", "aggressive")

    def test_empty_risk_scores(self) -> None:
        """Empty risk_scores does not crash (uses default avg 5.0)."""
        result = classify_risk_level(bias_count=5, risk_scores={})
        assert isinstance(result, str)

    def test_mixed_risk_level_combinations(self) -> None:
        """Exercises various (bias_count, avg_risk) combinations."""
        test_cases = [
            (2, {"financial": 10, "operational": 10, "reputational": 10, "compliance": 10, "technical": 10}, "conservative"),
            (5, {"financial": 40, "operational": 40, "reputational": 40, "compliance": 40, "technical": 40}, "moderate"),
            (9, {"financial": 80, "operational": 80, "reputational": 80, "compliance": 80, "technical": 80}, "aggressive"),
        ]
        for bias_count, risk_scores, expected in test_cases:
            result = classify_risk_level(bias_count=bias_count, risk_scores=risk_scores)
            assert result == expected, f"bias={bias_count} risk={risk_scores}: expected {expected}, got {result}"


class TestExtractBiases:
    """Bias extraction from yes/no responses."""

    def test_all_present(self) -> None:
        """All True responses extract all biases."""
        responses = {qid: True for qid in BIAS_DIMENSION_MAP}
        biases = extract_biases(responses)
        assert len(biases) == 10

    def test_none_present(self) -> None:
        """All False responses extract no biases."""
        responses = {qid: False for qid in BIAS_DIMENSION_MAP}
        biases = extract_biases(responses)
        assert biases == []

    def test_partial_biases(self) -> None:
        """Only True responses are extracted."""
        responses = {
            "bias_confirmation": True,
            "bias_overconfidence": False,
            "bias_sunk_cost": True,
            "bias_planning": False,
            "bias_self_serving": False,
            "bias_anchoring": False,
            "bias_availability": True,
            "bias_framing": False,
            "bias_status_quo": False,
            "bias_optimism": False,
        }
        biases = extract_biases(responses)
        assert set(biases) == {"confirmation_bias", "sunk_cost_fallacy", "availability_heuristic"}

    def test_unknown_keys_ignored(self) -> None:
        """Unknown question IDs are silently ignored."""
        responses = {
            "bias_confirmation": True,
            "bias_nonexistent": True,
        }
        biases = extract_biases(responses)
        assert biases == ["confirmation_bias"]
