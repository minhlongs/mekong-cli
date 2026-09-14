"""Tests for Hybrid LLM Router — Main Orchestrator.

Tests the 9-stage pipeline integration with mocked LLM calls.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from src.core.hybrid_router import (
    MissionResult,
    route_and_execute,
    _get_system_state,
)
from src.core.mcu_gate import MCUGate
from src.core.model_selector import SystemState
from src.core.fallback_chain import FallbackResult


@pytest.fixture
def gate():
    g = MCUGate(":memory:")
    g.seed_balance("t1", 100)
    yield g
    g.close()


@pytest.fixture
def api_state():
    """System state with API keys only (no local)."""
    return SystemState(
        local_available=False,
        local_models=[],
        api_keys={"anthropic": True, "google": True, "openai": False},
        tenant_tier="growth",
    )


class TestMissionResult:
    def test_success_result(self):
        r = MissionResult(success=True, mission_id="m1", model_used="claude-sonnet-4-6", mcu_charged=3)
        assert r.success is True
        assert r.mcu_charged == 3

    def test_failure_result(self):
        r = MissionResult(success=False, error="insufficient_mcu")
        assert r.success is False
        assert r.model_used is None

    def test_defaults(self):
        r = MissionResult(success=True)
        assert r.mission_id == ""
        assert r.output == ""
        assert r.attempts == []


class TestRouteAndExecuteStage2:
    """Test MCU lock failures (Stage 2)."""

    def test_insufficient_mcu(self, gate, api_state):
        gate_low = MCUGate(":memory:")
        gate_low.seed_balance("t1", 2)

        result = asyncio.run(route_and_execute(
            goal="build a complex distributed system with microservices",
            tenant_id="t1",
            mcu_gate=gate_low,
            system_state=api_state,
        ))
        assert result.success is False
        assert "insufficient_mcu" in result.error or "tenant_not_found" in result.error
        gate_low.close()

    def test_unknown_tenant(self, api_state):
        gate = MCUGate(":memory:")
        result = asyncio.run(route_and_execute(
            goal="hello",
            tenant_id="ghost",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert result.success is False
        assert result.error == "tenant_not_found"
        gate.close()


class TestRouteAndExecuteSuccess:
    """Test successful execution (Stages 1-9)."""

    @patch("src.raas.credits.CreditStore")
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_full_pipeline_success(self, mock_exec, mock_credit_store_class, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            tokens_output=50,
            attempts=["gemini-2.0-flash"],
            output="Hello world response",
        )

        # Mock CreditStore to return high balance (>200) to skip watermark
        mock_store_instance = MagicMock()
        mock_store_instance.get_balance.return_value = 250
        mock_credit_store_class.return_value = mock_store_instance

        result = asyncio.run(route_and_execute(
            goal="write a simple hello world script",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))

        assert result.success is True
        assert result.model_used == "gemini-2.0-flash"
        assert result.mcu_charged > 0
        assert result.output == "Hello world response"
        assert result.profile is not None

    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_mcu_deducted_on_success(self, mock_exec, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            tokens_output=10,
            attempts=["gemini-2.0-flash"],
            output="done",
        )

        bal_before = gate.get_balance("t1")["balance"]
        asyncio.run(route_and_execute(
            goal="fix a small bug",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        bal_after = gate.get_balance("t1")["balance"]
        assert bal_after < bal_before

    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_auto_generates_mission_id(self, mock_exec, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True, model_used="gemini-2.0-flash",
            tokens_output=1, attempts=["gemini-2.0-flash"], output="ok",
        )

        result = asyncio.run(route_and_execute(
            goal="hello",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert len(result.mission_id) > 0


class TestRouteAndExecuteFailure:
    """Test failure paths (Stage 6+7)."""

    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_all_models_failed_refunds_mcu(self, mock_exec, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=False,
            error="all_models_failed",
            attempts=["gemini-2.0-flash", "gpt-4o-mini"],
        )

        bal_before = gate.get_balance("t1")["balance"]
        result = asyncio.run(route_and_execute(
            goal="do something",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        bal_after = gate.get_balance("t1")["balance"]

        assert result.success is False
        assert result.error == "all_models_failed"
        assert bal_after == bal_before  # fully refunded

    @patch("src.core.hybrid_router.execute_with_fallback", side_effect=ConnectionError("down"))
    def test_execution_exception_refunds_mcu(self, mock_exec, gate, api_state):
        bal_before = gate.get_balance("t1")["balance"]
        result = asyncio.run(route_and_execute(
            goal="test task",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        bal_after = gate.get_balance("t1")["balance"]

        assert result.success is False
        assert "execution_failed" in result.error
        assert bal_after == bal_before


class TestGetSystemState:
    @patch("src.core.local_adapter.OllamaAdapter")
    def test_local_unavailable(self, mock_adapter_cls):
        mock_adapter = MagicMock()
        mock_adapter.health_check.return_value = False
        mock_adapter_cls.return_value = mock_adapter

        state = _get_system_state()
        assert state.local_available is False
        assert state.local_models == []

    @patch("src.core.local_adapter.OllamaAdapter")
    def test_local_available(self, mock_adapter_cls):
        mock_adapter = MagicMock()
        mock_adapter.health_check.return_value = True
        mock_adapter.list_models.return_value = ["llama3.2:3b"]
        mock_adapter_cls.return_value = mock_adapter

        state = _get_system_state()
        assert state.local_available is True
        assert "llama3.2:3b" in state.local_models

    @patch("src.core.local_adapter.OllamaAdapter", side_effect=RuntimeError("init failed"))
    def test_local_init_exception(self, mock_adapter_cls):
        state = _get_system_state()
        assert state.local_available is False
        assert state.local_models == []


class TestStage1AndMatchingCommand:
    @patch("src.core.hybrid_router.find_best_command")
    @patch("src.core.hybrid_router.build_system_prompt", return_value="custom prompt")
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_matched_command_used(self, mock_exec, mock_build_prompt, mock_find_cmd, gate, api_state):
        cmd = MagicMock()
        cmd.id = "test-cmd"
        mock_find_cmd.return_value = cmd

        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="cmd output",
            attempts=["gemini-2.0-flash"],
        )

        result = asyncio.run(route_and_execute(
            goal="test matching command",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert result.success is True
        assert mock_build_prompt.called
        assert mock_exec.call_args[1]["system_prompt"] == "custom prompt"


class TestMultiAgentCollaboration:
    @patch("src.core.hybrid_router.classify_multi_agent", return_value=["planner", "coder"])
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_multi_agent_success(self, mock_exec, mock_multi, gate, api_state):
        mock_exec.side_effect = [
            FallbackResult(success=True, model_used="m1", output="Plan created"),
            FallbackResult(success=True, model_used="m2", output="Code created"),
        ]

        result = asyncio.run(route_and_execute(
            goal="complex project requiring team",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))

        assert result.success is True
        assert "[PLANNER]" in result.output
        assert "[CODER]" in result.output

    @patch("src.core.hybrid_router.classify_multi_agent", return_value=["planner", "coder"])
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_multi_agent_exec_exception_and_blocked(self, mock_exec, mock_multi, gate, api_state):
        mock_exec.side_effect = RuntimeError("network crash")

        result = asyncio.run(route_and_execute(
            goal="multi agent crash",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))

        assert result.success is False
        assert "multi_agent_blocked" in result.error

    @patch("src.core.hybrid_router.classify_multi_agent", return_value=["planner", "coder"])
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_multi_agent_unsuccessful_result(self, mock_exec, mock_multi, gate, api_state):
        mock_exec.return_value = FallbackResult(success=False, error="model out of tokens")

        result = asyncio.run(route_and_execute(
            goal="multi agent fail",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))

        assert result.success is False
        assert "multi_agent_blocked" in result.error


class TestStage7And8EdgeCases:
    @patch("src.core.hybrid_router.SubagentReviewer")
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_reviewer_proceed_false(self, mock_exec, mock_reviewer_cls, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="raw output",
            attempts=["gemini-2.0-flash"],
        )

        mock_reviewer = MagicMock()
        mock_reviewer.full_review.return_value = {
            "proceed": False,
            "spec_review": {"issues": ["issue1"]},
        }
        mock_reviewer_cls.return_value = mock_reviewer

        result = asyncio.run(route_and_execute(
            goal="review issues",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert result.success is True

    @patch("src.core.hybrid_router.SubagentReviewer", side_effect=RuntimeError("reviewer init failed"))
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_reviewer_exception_handled(self, mock_exec, mock_reviewer_cls, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="raw output",
            attempts=["gemini-2.0-flash"],
        )

        result = asyncio.run(route_and_execute(
            goal="reviewer crash",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert result.success is True

    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_mcu_confirm_failure_logged(self, mock_exec, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="done",
            attempts=["gemini-2.0-flash"],
        )

        gate_mock = MagicMock()
        lock_mock = MagicMock()
        lock_mock.success = True
        lock_mock.lock_id = "lock-1"
        gate_mock.check_and_lock.return_value = lock_mock

        confirm_mock = MagicMock()
        confirm_mock.success = False
        confirm_mock.error = "ledger unavailable"
        confirm_mock.charged = 0
        confirm_mock.refunded = 0
        gate_mock.confirm.return_value = confirm_mock

        result = asyncio.run(route_and_execute(
            goal="confirm fail",
            tenant_id="t1",
            mcu_gate=gate_mock,
            system_state=api_state,
        ))
        assert result.success is True


class TestWatermarkAndSyncWrapper:
    @patch("src.raas.credits.CreditStore")
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_watermark_appended_for_low_balance(self, mock_exec, mock_credit_store_cls, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="Simple output",
            attempts=["gemini-2.0-flash"],
        )
        mock_store = MagicMock()
        mock_store.get_balance.return_value = 50
        mock_credit_store_cls.return_value = mock_store

        result = asyncio.run(route_and_execute(
            goal="watermark test",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert "Generated by [MekongMind]" in result.output

    @patch("src.raas.credits.CreditStore")
    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_watermark_skipped_if_already_present(self, mock_exec, mock_credit_store_cls, gate, api_state):
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="Text www.mekongmind.com",
            attempts=["gemini-2.0-flash"],
        )
        mock_store = MagicMock()
        mock_store.get_balance.side_effect = RuntimeError("db down")
        mock_credit_store_cls.return_value = mock_store

        result = asyncio.run(route_and_execute(
            goal="watermark already present",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        ))
        assert result.output == "Text www.mekongmind.com"

    @patch("src.core.hybrid_router.execute_with_fallback")
    def test_route_sync_wrapper(self, mock_exec, gate, api_state):
        from src.core.hybrid_router import route_sync
        mock_exec.return_value = FallbackResult(
            success=True,
            model_used="gemini-2.0-flash",
            output="sync res",
            attempts=["gemini-2.0-flash"],
        )
        res = route_sync(
            goal="sync call",
            tenant_id="t1",
            mcu_gate=gate,
            system_state=api_state,
        )
        assert res.success is True
        assert "sync res" in res.output

