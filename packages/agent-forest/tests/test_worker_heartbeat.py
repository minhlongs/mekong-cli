"""Tests for worker heartbeat publisher + aggregator helpers."""

from __future__ import annotations

import time

import fakeredis
import pytest

from agent_forest.worker.heartbeat import (
    count_alive,
    default_worker_id,
    last_seen_timestamp,
    publish,
)


@pytest.fixture
def r():
    return fakeredis.FakeRedis(decode_responses=True)


def test_default_worker_id_stable_and_non_empty(monkeypatch):
    monkeypatch.delenv("AGENT_FOREST_WORKER_ID", raising=False)
    a = default_worker_id()
    b = default_worker_id()
    assert a == b
    assert "-" in a  # hostname-pid


def test_default_worker_id_env_override(monkeypatch):
    monkeypatch.setenv("AGENT_FOREST_WORKER_ID", "custom-id-42")
    assert default_worker_id() == "custom-id-42"


def test_publish_sets_key_with_ttl(r):
    publish(r, "w1", ttl_seconds=30)
    assert r.exists("workers:heartbeat:w1") == 1
    ttl = r.ttl("workers:heartbeat:w1")
    assert 0 < ttl <= 30


def test_count_alive_scans_heartbeat_keyspace(r):
    assert count_alive(r) == 0
    publish(r, "w1")
    publish(r, "w2")
    assert count_alive(r) == 2
    # Non-heartbeat keys are excluded
    r.set("other:key", "x")
    assert count_alive(r) == 2


def test_last_seen_timestamp_returns_max(r):
    assert last_seen_timestamp(r) == 0
    publish(r, "w-old")
    # Overwrite with explicit older ts by direct SET
    r.setex("workers:heartbeat:w-old", 60, int(time.time()) - 120)
    publish(r, "w-new")
    latest = last_seen_timestamp(r)
    now = int(time.time())
    assert abs(latest - now) < 5  # newer heartbeat dominates


def test_last_seen_ignores_non_numeric_value(r):
    r.setex("workers:heartbeat:w-bad", 60, "not-a-number")
    assert last_seen_timestamp(r) == 0
