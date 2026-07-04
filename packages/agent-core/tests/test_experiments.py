"""Tests for agent_core.experiments — A/B bucket assignment primitive."""

from __future__ import annotations

import pytest

from agent_core.experiments import DEFAULT_VARIANTS, bucket


def test_bucket_returns_default_variant() -> None:
    result = bucket("user-1", "exp-a")
    assert result in DEFAULT_VARIANTS


def test_bucket_is_deterministic() -> None:
    first = bucket("user-42", "exp-router")
    second = bucket("user-42", "exp-router")
    third = bucket("user-42", "exp-router")
    assert first == second == third


def test_bucket_same_user_differs_across_experiments() -> None:
    # The experiment name is part of the hash key, so different experiments
    # produce uncorrelated assignments. Demonstrate at least one user whose
    # variant flips when the experiment name changes (probabilistically
    # almost certain for independent hashes).
    flipped = False
    for i in range(50):
        a = bucket(f"user-{i}", "exp-a", ["control", "treatment"])
        b = bucket(f"user-{i}", "exp-b", ["control", "treatment"])
        if a != b:
            flipped = True
            break
    assert flipped, "experiment name must influence assignment"


def test_bucket_respects_custom_variants() -> None:
    variants = ["arm-x", "arm-y", "arm-z"]
    for i in range(20):
        result = bucket(f"user-{i}", "multi-arm", variants)
        assert result in variants


def test_bucket_single_variant_always_returns_it() -> None:
    for i in range(10):
        assert bucket(f"user-{i}", "dark-launch", ["only"]) == "only"


def test_bucket_distribution_is_roughly_uniform() -> None:
    counts = {"control": 0, "treatment": 0}
    for i in range(2000):
        variant = bucket(f"user-{i}", "exp-uniform")
        counts[variant] += 1
    # 50/50 split, tolerate ±5% deviation (100 out of 2000).
    assert abs(counts["control"] - counts["treatment"]) < 200


def test_bucket_empty_user_id_rejected() -> None:
    with pytest.raises(ValueError, match="user_id"):
        bucket("", "exp-a")


def test_bucket_empty_experiment_name_rejected() -> None:
    with pytest.raises(ValueError, match="experiment_name"):
        bucket("user-1", "")


def test_bucket_empty_variants_rejected() -> None:
    with pytest.raises(ValueError, match="variants"):
        bucket("user-1", "exp-a", [])


def test_bucket_accepts_tuple_variants() -> None:
    result = bucket("user-1", "exp-a", ("a", "b", "c"))
    assert result in ("a", "b", "c")
