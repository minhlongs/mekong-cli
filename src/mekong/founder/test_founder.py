"""Tests for the founder genome assessment module — types, questions, scoring,
assess orchestration, CLI surface, and behaviour-graph integration.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid

import pytest

from src.mekong.founder.assess import assess_founder, genome_to_dict, list_founders, review_founder
from src.mekong.founder.questions import (
    BIAS_QUESTIONS,
    FEAR_QUESTIONS,
    RISK_DIMENSIONS,
    RISK_QUESTIONS,
    SCHWARTZ_VALUES,
    TIPI_QUESTIONS,
)
from src.mekong.founder.scoring import (
    classify_risk_level,
    extract_biases,
    score_big_five,
    score_risk,
)
from src.mekong.founder.types import FounderGenome

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_tipi() -> dict[str, int]:
    """Return neutral TIPI-10 responses (all 4 = neutral)."""
    return {f"tipi_{i:02d}": 4 for i in range(1, 11)}


def _default_risk() -> dict[str, int]:
    """Return moderate risk ratings (all 5)."""
    return {dim: 5 for dim in RISK_DIMENSIONS}


def _default_biases() -> dict[str, bool]:
    """Return all biases answered False."""
    return {q["id"]: False for q in BIAS_QUESTIONS}


# ---------------------------------------------------------------------------
# Test: dataclass creation and defaults
# ---------------------------------------------------------------------------


class TestTypes:
    def test_create_minimal(self) -> None:
        """A FounderGenome can be created with all required fields."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at="2026-07-04T00:00:00Z",
            particle_id=None,
            mission="Test mission",
            values=["achievement"],
            big_five={"openness": 50, "conscientiousness": 50, "extraversion": 50, "agreeableness": 50, "neuroticism": 50},
            fears=[],
            risk_profile={"financial": 50, "operational": 50, "reputational": 50, "compliance": 50, "technical": 50},
            cognitive_biases=[],
            risk_level="moderate",
        )
        assert genome.version == "1.0.0"
        assert genome.mission == "Test mission"
        assert genome.notes == []  # default factory

    def test_default_notes(self) -> None:
        """The ``notes`` field defaults to an empty list."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at="2026-07-04T00:00:00Z",
            particle_id=None,
            mission="M",
            values=[],
            big_five={},
            fears=[],
            risk_profile={},
            cognitive_biases=[],
            risk_level="conservative",
        )
        assert genome.notes == []

    def test_default_notes_custom(self) -> None:
        """Custom notes are preserved."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at="2026-07-04T00:00:00Z",
            particle_id=None,
            mission="M",
            values=[],
            big_five={},
            fears=[],
            risk_profile={},
            cognitive_biases=[],
            risk_level="conservative",
            notes=["Custom caveat."],
        )
        assert genome.notes == ["Custom caveat."]

    def test_genome_to_dict_roundtrip(self) -> None:
        """genome_to_dict produces a JSON-serialisable dict."""
        genome = FounderGenome(
            version="1.0.0",
            assessed_at="2026-07-04T00:00:00Z",
            particle_id=None,
            mission="Round-trip test",
            values=["achievement", "self_direction"],
            big_five={"openness": 80, "conscientiousness": 60, "extraversion": 40, "agreeableness": 70, "neuroticism": 30},
            fears=[{"trigger": "cash crunch", "predicted_behavior": "cut costs", "mitigation": "raise runway"}],
            risk_profile={"financial": 60, "operational": 50, "reputational": 40, "compliance": 30, "technical": 70},
            cognitive_biases=["overconfidence", "optimism_bias"],
            risk_level="aggressive",
            notes=["Note 1"],
        )
        d = genome_to_dict(genome)
        # Must be JSON-serialisable
        dumped = json.dumps(d)
        loaded = json.loads(dumped)
        assert loaded["version"] == "1.0.0"
        assert loaded["risk_level"] == "aggressive"
        assert loaded["mission"] == "Round-trip test"
        assert len(loaded["cognitive_biases"]) == 2


# ---------------------------------------------------------------------------
# Test: TIPI-10 questions
# ---------------------------------------------------------------------------


class TestTipiQuestions:
    def test_ten_questions(self) -> None:
        """There must be exactly 10 TIPI questions."""
        assert len(TIPI_QUESTIONS) == 10

    def test_seven_point_scale(self) -> None:
        """Every TIPI question must have 7 options with values 1-7."""
        for q in TIPI_QUESTIONS:
            assert q["type"] == "likert_7", f"{q['id']} is not likert_7"
            assert len(q["options"]) == 7
            for opt in q["options"]:
                assert 1 <= opt["value"] <= 7

    def test_each_has_dimension(self) -> None:
        """Every TIPI question must belong to a Big Five dimension."""
        dimensions = {"extraversion", "agreeableness", "conscientiousness", "emotional_stability", "openness"}
        for q in TIPI_QUESTIONS:
            assert q["dimension"] in dimensions, f"{q['id']} has unknown dimension {q['dimension']}"

    def test_reverse_scored_half(self) -> None:
        """Exactly 5 of 10 TIPI items should be reverse-scored."""
        rev = [q for q in TIPI_QUESTIONS if q.get("reverse_scored")]
        assert len(rev) == 5

    def test_question_ids_unique(self) -> None:
        """All TIPI question IDs must be unique."""
        ids = [q["id"] for q in TIPI_QUESTIONS]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Test: Schwartz values
# ---------------------------------------------------------------------------


class TestSchwartzValues:
    def test_ten_values(self) -> None:
        """There must be exactly 10 Schwartz values."""
        assert len(SCHWARTZ_VALUES) == 10

    def test_each_has_id_label_and_description(self) -> None:
        """Every value entry must have id, label, and description keys."""
        for v in SCHWARTZ_VALUES:
            assert "id" in v
            assert "label" in v
            assert "description" in v


# ---------------------------------------------------------------------------
# Test: Risk questions
# ---------------------------------------------------------------------------


class TestRiskQuestions:
    def test_five_dimensions(self) -> None:
        """There must be exactly 5 risk questions."""
        assert len(RISK_QUESTIONS) == 5

    def test_ten_point_scale(self) -> None:
        """Every risk question must have 10 options with values 1-10."""
        for q in RISK_QUESTIONS:
            assert q["type"] == "likert_10"
            assert len(q["options"]) == 10
            for opt in q["options"]:
                assert 1 <= opt["value"] <= 10


# ---------------------------------------------------------------------------
# Test: Fear questions
# ---------------------------------------------------------------------------


class TestFearQuestions:
    def test_fifteen_fear_fields(self) -> None:
        """There must be exactly 15 fear questions (5 triggers, 5 behaviors, 5 mitigations)."""
        assert len(FEAR_QUESTIONS) == 15

    def test_fear_fields_alternate(self) -> None:
        """Fear questions should cycle through trigger, predicted_behavior, mitigation."""
        fields = ["trigger", "predicted_behavior", "mitigation"]
        for i, q in enumerate(FEAR_QUESTIONS):
            expected = fields[i % 3]
            assert q["field"] == expected, f"{q['id']} expected field={expected}, got {q['field']}"


# ---------------------------------------------------------------------------
# Test: Bias questions
# ---------------------------------------------------------------------------


class TestBiasQuestions:
    def test_ten_biases(self) -> None:
        """There must be exactly 10 bias questions."""
        assert len(BIAS_QUESTIONS) == 10

    def test_bias_yes_no_type(self) -> None:
        """Every bias question must be yes_no type with boolean options."""
        for q in BIAS_QUESTIONS:
            assert q["type"] == "yes_no"
            for opt in q["options"]:
                assert isinstance(opt["value"], bool)

    def test_bias_ids_unique(self) -> None:
        """All bias question IDs must be unique."""
        ids = [q["id"] for q in BIAS_QUESTIONS]
        assert len(ids) == len(set(ids))

    def test_bias_has_bias_label(self) -> None:
        """Every bias question must have a human-readable bias_label."""
        for q in BIAS_QUESTIONS:
            assert "bias_label" in q
            assert isinstance(q["bias_label"], str)
            assert len(q["bias_label"]) > 0


# ---------------------------------------------------------------------------
# Test: Big Five scoring
# ---------------------------------------------------------------------------


class TestBigFiveScoring:
    def test_all_neutral(self) -> None:
        """All neutral responses (4) should produce scores near 50."""
        scores = score_big_five(_default_tipi())
        for dim in ("openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"):
            assert 40 <= scores[dim] <= 60, f"{dim}={scores[dim]} not near 50"
        assert "neuroticism" in scores

    def test_max_extraversion(self) -> None:
        """Maximum extraversion responses should give extraversion=100."""
        responses = {
            "tipi_01": 7,  # extraverted (normal)
            "tipi_02": 1,  # quarrelsome (reverse) → low agreeableness
            "tipi_03": 4,  # dependable (neutral)
            "tipi_04": 1,  # anxious (reverse) → high emotional stability
            "tipi_05": 4,  # open (neutral)
            "tipi_06": 1,  # reserved (reverse) → high extraversion
            "tipi_07": 4,  # sympathetic (neutral)
            "tipi_08": 4,  # disorganized (reverse neutral)
            "tipi_09": 4,  # calm (neutral)
            "tipi_10": 4,  # conventional (reverse neutral)
        }
        scores = score_big_five(responses)
        assert scores["extraversion"] == 100  # 7 + reverse(1=7) = 14 → 100

    def test_max_openness(self) -> None:
        """Maximum openness responses should give openness=100."""
        responses = {
            "tipi_01": 4,
            "tipi_02": 4,
            "tipi_03": 4,
            "tipi_04": 4,
            "tipi_05": 7,  # open (normal)
            "tipi_06": 4,
            "tipi_07": 4,
            "tipi_08": 4,
            "tipi_09": 4,
            "tipi_10": 1,  # conventional (reverse) → high openness
        }
        scores = score_big_five(responses)
        assert scores["openness"] == 100

    def test_neuroticism_is_inverse(self) -> None:
        """Neuroticism should be 101 minus emotional_stability."""
        responses = _default_tipi()
        scores = score_big_five(responses)
        assert scores["neuroticism"] == 101 - scores["emotional_stability"]

    def test_scores_are_integers(self) -> None:
        """All Big Five scores must be integers."""
        scores = score_big_five(_default_tipi())
        for key, val in scores.items():
            assert isinstance(val, int), f"{key} is {type(val).__name__}, expected int"

    def test_scores_clamped(self) -> None:
        """Scores must be in the 1-100 range."""
        responses = _default_tipi()
        responses.update({"tipi_01": 7, "tipi_06": 1})  # max extraversion
        scores = score_big_five(responses)
        for key, val in scores.items():
            assert 1 <= val <= 100, f"{key}={val} out of range"


# ---------------------------------------------------------------------------
# Test: Risk scoring
# ---------------------------------------------------------------------------


class TestRiskScoring:
    def test_average_default(self) -> None:
        """Default risk ratings (all 5) should each map to 50."""
        scores = score_risk(_default_risk())
        for dim in RISK_DIMENSIONS:
            assert scores[dim] == 50, f"{dim}={scores[dim]}"

    def test_minimum(self) -> None:
        """Minimum rating (1) should give score 10."""
        ratings = {dim: 1 for dim in RISK_DIMENSIONS}
        scores = score_risk(ratings)
        for dim in RISK_DIMENSIONS:
            assert scores[dim] == 10

    def test_maximum(self) -> None:
        """Maximum rating (10) should give score 100."""
        ratings = {dim: 10 for dim in RISK_DIMENSIONS}
        scores = score_risk(ratings)
        for dim in RISK_DIMENSIONS:
            assert scores[dim] == 100

    def test_missing_dimension_defaults(self) -> None:
        """Missing dimensions should default to 50."""
        scores = score_risk({"financial": 10})
        assert scores["financial"] == 100
        assert scores["operational"] == 50  # default
        assert scores["technical"] == 50

    def test_scores_are_integers(self) -> None:
        """All risk scores must be integers."""
        scores = score_risk(_default_risk())
        for val in scores.values():
            assert isinstance(val, int)

    def test_scores_clamped(self) -> None:
        """Scores must be in the 10-100 range."""
        scores = score_risk(_default_risk())
        for val in scores.values():
            assert 10 <= val <= 100


# ---------------------------------------------------------------------------
# Test: Bias classification
# ---------------------------------------------------------------------------


class TestBiasClassification:
    def test_zero_biases_conservative(self) -> None:
        """Zero biases with moderate risk should classify as conservative."""
        risk_scores = score_risk(_default_risk())
        level = classify_risk_level(0, risk_scores)
        assert level == "conservative"

    def test_three_biases_conservative(self) -> None:
        """Up to 3 biases should be conservative with moderate risk."""
        risk_scores = score_risk(_default_risk())
        level = classify_risk_level(3, risk_scores)
        assert level == "conservative"

    def test_four_biases_moderate(self) -> None:
        """4 biases should be moderate with moderate risk."""
        risk_scores = score_risk(_default_risk())
        level = classify_risk_level(4, risk_scores)
        assert level == "moderate"

    def test_six_biases_moderate(self) -> None:
        """6 biases should be moderate with moderate risk."""
        risk_scores = score_risk(_default_risk())
        level = classify_risk_level(6, risk_scores)
        assert level == "moderate"

    def test_seven_biases_aggressive(self) -> None:
        """7+ biases should be aggressive with very high risk appetite."""
        risk_scores = score_risk({dim: 10 for dim in RISK_DIMENSIONS})
        level = classify_risk_level(7, risk_scores)
        assert level == "aggressive"

    def test_ten_biases_aggressive(self) -> None:
        """10 biases should be aggressive with very high risk appetite."""
        risk_scores = score_risk({dim: 10 for dim in RISK_DIMENSIONS})
        level = classify_risk_level(10, risk_scores)
        assert level == "aggressive"

    def test_high_risk_aggressive(self) -> None:
        """Many biases with very high risk appetite should be aggressive."""
        risk_scores = score_risk({dim: 10 for dim in RISK_DIMENSIONS})
        level = classify_risk_level(7, risk_scores)
        assert level == "aggressive"

    def test_extract_biases_empty(self) -> None:
        """extract_biases with no positive responses returns empty list."""
        result = extract_biases(_default_biases())
        assert result == []

    def test_extract_biases_some(self) -> None:
        """extract_biases returns only the dimensions where bias is True."""
        responses = {
            "bias_confirmation": True,
            "bias_overconfidence": False,
            "bias_sunk_cost": True,
        }
        result = extract_biases(responses)
        assert "confirmation_bias" in result
        assert "overconfidence" not in result
        assert "sunk_cost_fallacy" in result
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Test: Assess flow (programmatic)
# ---------------------------------------------------------------------------


class TestAssessFlow:
    def test_full_assessment_produces_genome(self) -> None:
        """A complete set of inputs should produce a fully populated genome."""
        genome = assess_founder(
            mission="Build the future of AI",
            tipi_responses=_default_tipi(),
            values=["achievement", "self_direction", "stimulation"],
            fears=[{"trigger": "running out of cash", "predicted_behavior": "panic raise", "mitigation": "12-month runway buffer"}],
            risk_ratings={"financial": 7, "operational": 6, "reputational": 5, "compliance": 4, "technical": 8},
            bias_responses={"bias_confirmation": True, "bias_overconfidence": True},
        )
        assert isinstance(genome, FounderGenome)
        assert genome.version == "1.0.0"
        assert genome.mission == "Build the future of AI"
        assert genome.values == ["achievement", "self_direction", "stimulation"]
        assert len(genome.fears) == 1
        assert "openness" in genome.big_five
        assert "neuroticism" in genome.big_five
        assert len(genome.risk_profile) == 5
        assert genome.cognitive_biases == ["confirmation_bias", "overconfidence"]
        assert genome.risk_level in ("conservative", "moderate", "aggressive")
        assert len(genome.notes) == 3

    def test_assessment_sections_present(self) -> None:
        """The genome should contain all expected assessment sections."""
        genome = assess_founder(
            mission="Test mission",
            tipi_responses=_default_tipi(),
            values=["achievement"],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
        )
        # All required fields must be non-empty / non-None where appropriate
        assert genome.big_five != {}
        assert genome.risk_profile != {}
        assert isinstance(genome.cognitive_biases, list)
        assert genome.particle_id is None
        assert "assessed_at" in repr(genome.assessed_at) or genome.assessed_at != ""

    def test_assessment_with_particle_id(self) -> None:
        """Providing a particle_id should propagate it through the genome."""
        genome = assess_founder(
            mission="Linked mission",
            tipi_responses=_default_tipi(),
            values=["achievement"],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            particle_id="particle-abc-123",
        )
        assert genome.particle_id == "particle-abc-123"


# ---------------------------------------------------------------------------
# Test: Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_mission(self) -> None:
        """An empty mission string should be accepted."""
        genome = assess_founder(
            mission="",
            tipi_responses=_default_tipi(),
            values=[],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
        )
        assert genome.mission == ""

    def test_missing_tipi_responses_default_to_4(self) -> None:
        """Missing TIPI responses should default to 4 (neutral) in scoring."""
        responses = {"tipi_01": 7}  # only 1 of 10
        scores = score_big_five(responses)
        # The normalized score should be calculable (defaults fill missing)
        for dim in ("openness", "conscientiousness", "extraversion", "agreeableness", "emotional_stability"):
            assert 1 <= scores[dim] <= 100

    def test_empty_fears(self) -> None:
        """An empty fears list should be accepted."""
        genome = assess_founder(
            mission="No fears",
            tipi_responses=_default_tipi(),
            values=["achievement"],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
        )
        assert genome.fears == []

    def test_empty_values(self) -> None:
        """An empty values list should be accepted."""
        genome = assess_founder(
            mission="No values",
            tipi_responses=_default_tipi(),
            values=[],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
        )
        assert genome.values == []

    def test_all_biases_present(self) -> None:
        """All 10 biases True should produce 10 biases and aggressive risk level with high risk appetite."""
        all_biases = {q["id"]: True for q in BIAS_QUESTIONS}
        high_risk = {dim: 10 for dim in RISK_DIMENSIONS}
        genome = assess_founder(
            mission="Maximum bias",
            tipi_responses=_default_tipi(),
            values=["power"],
            fears=[],
            risk_ratings=high_risk,
            bias_responses=all_biases,
        )
        assert len(genome.cognitive_biases) == 10
        assert genome.risk_level == "aggressive"


# ---------------------------------------------------------------------------
# Test: CLI commands (using Typer CliRunner)
# ---------------------------------------------------------------------------


class TestCliCommands:
    @pytest.fixture
    def db_path(self) -> str:
        """Create a temporary database file."""
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "test_founder.db")
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
        os.rmdir(tmp)

    def test_cli_help(self) -> None:
        """``mekong founder --help`` should print the help text."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(founder_app, ["--help"])
        assert result.exit_code == 0
        assert "Founder Genome Assessment" in result.stdout

    def test_cli_assess_help(self) -> None:
        """``mekong founder assess --help`` should describe options."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(founder_app, ["assess", "--help"])
        assert result.exit_code == 0
        assert "mission" in result.stdout.lower() or "--mission" in result.stdout

    def test_cli_review_help(self) -> None:
        """``mekong founder review --help`` should describe arguments."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(founder_app, ["review", "--help"])
        assert result.exit_code == 0

    def test_cli_list_empty(self, db_path: str) -> None:
        """``mekong founder list`` on an empty graph prints no-founders message."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(founder_app, ["list", "--db", db_path])
        assert result.exit_code == 0
        assert "No founders found" in result.stdout or "0" in result.stdout

    def test_cli_list_with_one_founder(self, db_path: str) -> None:
        """``mekong founder list`` after assess should show one founder."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        # Assess first
        assess_founder(
            mission="CLI list test",
            tipi_responses=_default_tipi(),
            values=["achievement"],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            db_path=db_path,
        )

        runner = CliRunner()
        result = runner.invoke(founder_app, ["list", "--db", db_path])
        assert result.exit_code == 0
        assert "CLI list test" in result.stdout or "Found" in result.stdout

    def test_cli_assess_json_output(self, db_path: str) -> None:
        """``mekong founder assess`` should return valid JSON containing the genome."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(
            founder_app,
            [
                "assess",
                "--mission", "CLI JSON output",
                "--tipi", json.dumps(_default_tipi()),
                "--values", '["achievement"]',
                "--risk", json.dumps(_default_risk()),
                "--biases", json.dumps(_default_biases()),
                "--db", db_path,
            ],
        )
        assert result.exit_code == 0, f"STDERR: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["mission"] == "CLI JSON output"
        assert "risk_level" in output
        assert "cognitive_biases" in output

    def test_cli_review_not_found(self, db_path: str) -> None:
        """``mekong founder review`` on a non-existent ID should exit with error."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(founder_app, ["review", "non-existent-id", "--db", db_path])
        assert result.exit_code == 1
        assert "not found" in (result.stdout.lower() + result.stderr.lower())


# ---------------------------------------------------------------------------
# Test: Graph integration (store + retrieve)
# ---------------------------------------------------------------------------


class TestGraphIntegration:
    @pytest.fixture
    def db_path(self) -> str:
        """Create a temporary database file."""
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "test_founder_graph.db")
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
        os.rmdir(tmp)

    def test_store_and_retrieve_genome(self, db_path: str) -> None:
        """Assess then review should return matching genome data."""
        uid = str(uuid.uuid4())
        genome = assess_founder(
            mission="Graph test mission",
            tipi_responses=_default_tipi(),
            values=["achievement", "self_direction"],
            fears=[{"trigger": "market downturn", "predicted_behavior": "pivot", "mitigation": "diversify revenue"}],
            risk_ratings={"financial": 8, "operational": 6, "reputational": 5, "compliance": 3, "technical": 7},
            bias_responses={"bias_confirmation": True, "bias_overconfidence": True, "bias_sunk_cost": False},
            uid=uid,
            db_path=db_path,
        )

        # Review by original UID
        entity = review_founder(uid, db_path=db_path)
        assert entity is not None
        meta = entity["metadata"]
        assert meta["mission"] == "Graph test mission"
        assert meta["risk_level"] == genome.risk_level
        assert meta["values"] == ["achievement", "self_direction"]
        assert len(meta["fears"]) == 1
        assert len(meta["cognitive_biases"]) == 2

    def test_list_founders(self, db_path: str) -> None:
        """After assessing two founders, list should return both."""
        assess_founder(
            mission="Founder A",
            tipi_responses=_default_tipi(),
            values=["achievement"],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            db_path=db_path,
        )
        assess_founder(
            mission="Founder B",
            tipi_responses=_default_tipi(),
            values=["benevolence"],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            db_path=db_path,
        )

        founders = list_founders(db_path=db_path)
        assert len(founders) == 2
        missions = {f["metadata"]["mission"] for f in founders if "metadata" in f}
        assert "Founder A" in missions
        assert "Founder B" in missions

    def test_list_empty(self, db_path: str) -> None:
        """An empty graph should return an empty list."""
        founders = list_founders(db_path=db_path)
        assert founders == []

    def test_review_nonexistent(self, db_path: str) -> None:
        """Reviewing a non-existent entity should return None."""
        entity = review_founder("does-not-exist", db_path=db_path)
        assert entity is None

    def test_genome_metadata_is_serialised(self, db_path: str) -> None:
        """The stored entity metadata should be a proper JSON dict."""
        uid = str(uuid.uuid4())
        assess_founder(
            mission="Metadata check",
            tipi_responses=_default_tipi(),
            values=[],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            uid=uid,
            db_path=db_path,
        )

        entity = review_founder(uid, db_path=db_path)
        assert entity is not None
        # metadata should be a dict, not a string
        assert isinstance(entity["metadata"], dict)
        assert entity["metadata"]["version"] == "1.0.0"  # type: ignore[index]

    def test_entity_kind_is_founder(self, db_path: str) -> None:
        """The stored entity should have kind='founder'."""
        uid = str(uuid.uuid4())
        assess_founder(
            mission="Kind check",
            tipi_responses=_default_tipi(),
            values=[],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            uid=uid,
            db_path=db_path,
        )

        entity = review_founder(uid, db_path=db_path)
        assert entity is not None
        assert entity["kind"] == "founder"

    def test_assessment_recorded_as_behavior(self, db_path: str) -> None:
        """An assessment should create a behavior edge in the graph."""
        uid = str(uuid.uuid4())
        assess_founder(
            mission="Behavior test",
            tipi_responses=_default_tipi(),
            values=[],
            fears=[],
            risk_ratings=_default_risk(),
            bias_responses=_default_biases(),
            uid=uid,
            db_path=db_path,
        )

        from src.mekong.graph.store import get_behaviors, open_db

        conn = open_db(db_path)
        try:
            behaviors = get_behaviors(
                conn,
                source_id=f"founder:{uid}",
                action="founder_assessment",
            )
            assert len(behaviors) >= 1
            assert behaviors[0].action == "founder_assessment"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Test: CLI edge cases (missing graph, invalid input)
# ---------------------------------------------------------------------------


class TestCliEdgeCases:
    def test_cli_invalid_json(self) -> None:
        """Invalid JSON input should produce an error."""
        from typer.testing import CliRunner

        from src.cli.commands.founder import founder_app

        runner = CliRunner()
        result = runner.invoke(
            founder_app,
            [
                "assess",
                "--tipi", "not valid json",
                "--db", "/tmp/nonexistent/test.db",
            ],
        )
        assert result.exit_code == 1
        assert "Error" in result.stdout or "Error" in result.stderr
