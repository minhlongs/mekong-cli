"""Tests for src/core/webhook_events.py — AgencyOS webhook event models."""
from __future__ import annotations

from datetime import datetime, timezone

from src.core.webhook_events import (
    WEBHOOK_EVENT_PAYLOADS,
    CreditsLowPayload,
    MissionCreatedPayload,
    MissionDonePayload,
    MissionFailPayload,
    MissionMetrics,
    PlanPayload,
    PlanStep,
    StepDonePayload,
    StepFailPayload,
    StepStartPayload,
)


class TestMissionMetrics:
    def test_cache_hit_rate_zero_when_no_queries(self):
        metrics = MissionMetrics()
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.cache_hit_rate == 0.0

    def test_cache_hit_rate_calculated_correctly(self):
        metrics = MissionMetrics(
            llm_calls=10,
            llm_tokens_in=500,
            llm_tokens_out=200,
            cache_hits=6,
            cache_misses=2,
        )
        assert metrics.cache_hit_rate == 0.75


class TestPlanStepAndPayload:
    def test_plan_step_defaults(self):
        step = PlanStep(order=0, title="Init repo", agent="git")
        assert step.order == 0
        assert step.title == "Init repo"
        assert step.agent == "git"
        assert step.params == {}
        assert step.estimated_duration == 0
        assert step.dependencies == []

    def test_plan_payload(self):
        steps = [
            PlanStep(order=0, title="Step 1", agent="a1"),
            PlanStep(order=1, title="Step 2", agent="a2", dependencies=[0]),
        ]
        payload = PlanPayload(
            mission_id="msn_123",
            plan_id="plan_456",
            steps=steps,
            total_estimated_duration=60,
        )
        assert payload.mission_id == "msn_123"
        assert payload.plan_id == "plan_456"
        assert len(payload.steps) == 2
        assert payload.total_estimated_duration == 60
        assert isinstance(payload.created_at, datetime)


class TestMissionCreatedPayload:
    def test_creation_with_defaults(self):
        payload = MissionCreatedPayload(
            mission_id="msn_001",
            goal="Analyze codebase",
            tenant_id="ten_abc",
        )
        assert payload.mission_id == "msn_001"
        assert payload.goal == "Analyze codebase"
        assert payload.tenant_id == "ten_abc"
        assert payload.priority == "normal"
        assert payload.webhook_url is None
        assert payload.estimated_credits == 1
        assert isinstance(payload.created_at, datetime)


class TestStepLifecyclePayloads:
    def test_step_start_payload(self):
        payload = StepStartPayload(
            mission_id="msn_001",
            step_order=1,
            step_title="Run tests",
            agent="tester",
            retry_count=1,
        )
        assert payload.step_order == 1
        assert payload.retry_count == 1
        assert isinstance(payload.started_at, datetime)

    def test_step_done_payload(self):
        payload = StepDonePayload(
            mission_id="msn_001",
            step_order=1,
            step_title="Run tests",
            exit_code=0,
            duration_seconds=12.5,
            stdout="pass",
            stderr="",
            artifacts=["test.xml"],
            credits_used=2,
        )
        assert payload.exit_code == 0
        assert payload.duration_seconds == 12.5
        assert payload.artifacts == ["test.xml"]
        assert payload.credits_used == 2

    def test_step_fail_payload(self):
        payload = StepFailPayload(
            mission_id="msn_001",
            step_order=2,
            step_title="Deploy",
            error_message="Connection refused",
            error_type="NetworkError",
            exit_code=1,
            duration_seconds=3.2,
            retry_count=2,
            max_retries=3,
            retry_after_seconds=5,
        )
        assert payload.error_type == "NetworkError"
        assert payload.retry_after_seconds == 5


class TestMissionOutcomePayloads:
    def test_mission_done_payload(self):
        metrics = MissionMetrics(llm_calls=5, cache_hits=2, cache_misses=2)
        payload = MissionDonePayload(
            mission_id="msn_001",
            goal="Ship release",
            status="completed",
            total_duration_seconds=120.0,
            total_steps=4,
            successful_steps=4,
            failed_steps=0,
            total_credits_used=4,
            artifacts=["build/app.zip"],
            completed_at=datetime.now(timezone.utc),
            metrics=metrics,
        )
        assert payload.status == "completed"
        assert payload.total_credits_used == 4
        assert payload.metrics.cache_hit_rate == 0.5

    def test_mission_fail_payload(self):
        payload = MissionFailPayload(
            mission_id="msn_002",
            goal="Ship release",
            status="failed",
            error_message="OOM crash",
            error_type="MemoryError",
            failed_step_order=3,
            total_duration_seconds=45.0,
            partial_steps_completed=2,
            credits_refunded=3,
            retry_exhausted=True,
        )
        assert payload.status == "failed"
        assert payload.credits_refunded == 3
        assert payload.retry_exhausted is True


class TestCreditsLowPayload:
    def test_credits_low_payload_defaults(self):
        payload = CreditsLowPayload(
            tenant_id="ten_xyz",
            current_balance=4,
        )
        assert payload.current_balance == 4
        assert payload.threshold == 10
        assert payload.recommended_top_up == 100
        assert payload.last_mission_cost == 0
        assert isinstance(payload.warned_at, datetime)


class TestWebhookEventPayloadsRegistry:
    def test_registry_contains_all_events(self):
        expected_keys = {
            "mission.created",
            "mission.planning",
            "mission.step.started",
            "mission.step.completed",
            "mission.step.failed",
            "mission.completed",
            "mission.failed",
            "credits.low",
        }
        assert set(WEBHOOK_EVENT_PAYLOADS.keys()) == expected_keys
        for key, cls in WEBHOOK_EVENT_PAYLOADS.items():
            assert issubclass(cls, MissionCreatedPayload.__base__)
