"""Comprehensive unit tests for Binh Phap Dispatcher.

Covers 100% of src/core/binh_phap_dispatcher.py:
- Path finding helper functions (_find_recipe_path, _find_skill_path)
- 3D dispatch translations (vertical, horizontal, diagonal, pause, stop)
- Execution result reporting (vertical, horizontal group completion)
- Diagonal cycle lessons & event handling fallbacks
- Status and escalation LLM routing
- LLM client factory (ZuneF gateway, device headers, fallbacks)
- Domain registry execution, prefix routing, and error resilience
- Topic and LLM execution helpers
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.binh_phap.reactions import EventSource
from src.core.binh_phap.topology import BattleGroup, GroupStatus
from src.core.binh_phap_dispatcher import (
    BinhPhapDispatcher,
    _find_recipe_path,
    _find_skill_path,
)


@pytest.fixture
def tmp_company(tmp_path: Path) -> str:
    """Create a temporary company.json for topology engine."""
    company = tmp_path / "company.json"
    company.write_text(
        json.dumps({
            "binh_phap_state": {
                "topology": "3d",
                "current_dimension": "vertical",
                "cycle_number": 0,
                "cycle_history": [],
                "current_groups": {},
                "next_command": "swot",
                "auto_dispatch": False,
                "target_mrr": 1000,
            }
        })
    )
    return str(company)


# ---------------------------------------------------------------------------
# Path resolution helpers
# ---------------------------------------------------------------------------


class TestPathHelpers:
    def test_find_recipe_path_contract_exists(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            # First check (contract) returns True
            mock_exists.side_effect = [True]
            path = _find_recipe_path("swot")
            assert path == Path("factory/contracts/commands/swot.json")

    def test_find_recipe_path_recipe_md_exists(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            # Contract False, recipe True
            mock_exists.side_effect = [False, True]
            path = _find_recipe_path("swot")
            assert path == Path("recipes/swot.md")

    def test_find_recipe_path_neither_exists(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [False, False]
            path = _find_recipe_path("swot")
            assert path is None

    def test_find_skill_path_namespaced_exists(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [True]
            path = _find_skill_path("growth:experiment")
            assert path == Path(".claude/skills/growth-experiment/SKILL.md")

    def test_find_skill_path_namespaced_fallback_to_plain(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            # Namespaced file False, plain skill True
            mock_exists.side_effect = [False, True]
            path = _find_skill_path("growth:experiment")
            assert path == Path(".claude/skills/growth:experiment/SKILL.md")

    def test_find_skill_path_single_command_exists(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [True]
            path = _find_skill_path("cook")
            assert path == Path(".claude/skills/cook/SKILL.md")

    def test_find_skill_path_none_exists(self) -> None:
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.side_effect = [False]
            path = _find_skill_path("cook")
            assert path is None


# ---------------------------------------------------------------------------
# Dispatcher core operations
# ---------------------------------------------------------------------------


class TestBinhPhapDispatcher:
    def test_vertical_dispatch(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        action = d.next_action()
        assert action["action"] == "execute"
        assert action["command"] == "swot"
        assert action["dimension"] == "vertical"
        assert isinstance(action["needs_approval"], bool)
        assert "chapter" in action

    def test_horizontal_dispatch(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        # Set state to horizontal
        d.topology.state["current_dimension"] = "horizontal"
        action = d.next_action()
        assert action["action"] == "execute_parallel"
        assert action["dimension"] == "horizontal"
        assert "commands" in action
        assert "recipes" in action
        assert "skills" in action
        assert "group" in action

    def test_diagonal_dispatch_loop(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        # Set state to diagonal with auto_dispatch enabled
        d.topology.state["current_dimension"] = "diagonal"
        d.topology.state["auto_dispatch"] = True
        action = d.next_action()
        assert action["action"] == "execute_loop"
        assert action["dimension"] == "diagonal"
        assert "cycle" in action
        assert "commands" in action

    def test_diagonal_dispatch_pause(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.topology.state["current_dimension"] = "diagonal"
        d.topology.state["auto_dispatch"] = False
        action = d.next_action()
        assert action["action"] == "pause"

    def test_stop_after_max_failures(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        for _ in range(3):
            d.report_result("swot", success=False)
        action = d.next_action()
        assert action["action"] == "stop"

    def test_report_result_vertical_advances_and_resets_failures(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.topology.consecutive_failures = 2
        d.report_result("swot", success=True, output={"status": "ok"}, duration_ms=100)
        assert d.topology.consecutive_failures == 0
        action = d.next_action()
        assert action["command"] == "plan"

    def test_report_result_vertical_failure_increments(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.report_result("swot", success=False, error="timeout", duration_ms=50)
        assert d.topology.consecutive_failures == 1

    def test_report_result_horizontal_group_completion(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.topology.state["current_dimension"] = "horizontal"
        # Setup a group with 2 commands
        group = BattleGroup(
            name="test_group",
            commands=["cmd1", "cmd2"],
            status=GroupStatus.IN_PROGRESS,
        )
        d.topology.groups = {"test_group": group}

        # Report first command
        d.report_result("cmd1", success=True)
        assert len(group.results) == 1
        assert group.status == GroupStatus.IN_PROGRESS

        # Report second command completes the group
        d.report_result("cmd2", success=True)
        assert len(group.results) == 2
        assert group.status == GroupStatus.COMPLETED

    def test_report_result_horizontal_unmatched_command(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.topology.state["current_dimension"] = "horizontal"
        group = BattleGroup(name="g1", commands=["cmd1"])
        d.topology.groups = {"g1": group}

        # Report command that isn't in group
        d.report_result("unknown_cmd", success=True)
        assert len(group.results) == 0

    def test_report_cycle_lesson(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.report_cycle_lesson(
            mrr=750.0,
            customers=15,
            lessons=["Email campaign worked"],
            adaptations=["Scale email outreach"],
        )
        history = d.topology.state["cycle_history"]
        assert len(history) == 1
        assert history[0]["result"]["mrr"] == 750.0
        assert history[0]["lessons"] == ["Email campaign worked"]
        assert history[0]["adaptations"] == ["Scale email outreach"]

    def test_report_cycle_lesson_default_adaptations(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        d.report_cycle_lesson(mrr=500.0, customers=5, lessons=["Lesson 1"])
        history = d.topology.state["cycle_history"]
        assert history[0]["adaptations"] == []

    def test_event_handling_valid_source(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        actions = d.handle_event("ci.failed", source="github", data={"build": 12})
        assert len(actions) > 0
        assert actions[0]["event"] == "ci.failed"
        assert "debug" in actions[0]["commands"]

    def test_event_handling_invalid_source_falls_back(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        with patch.object(d.reactions, "react", return_value=[{"handled": True}]) as mock_react:
            actions = d.handle_event("unknown.event", source="invalid_source_slug")
            assert len(actions) == 1
            # Verify the event dispatched used the fallback MANUAL source
            event_obj = mock_react.call_args[0][0]
            assert event_obj.source == EventSource.MANUAL

    def test_get_status(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        status = d.get_status()
        assert status["dimension"] == "vertical"
        assert status["cycle"] == 0
        assert status["next_command"] == "swot"
        assert status["auto_dispatch"] is False
        assert status["target_mrr"] == 1000
        assert status["consecutive_failures"] == 0
        assert "groups" in status
        assert status["cycles_completed"] == 0


# ---------------------------------------------------------------------------
# Escalation & LLM client creation
# ---------------------------------------------------------------------------


class TestEscalationAndLLM:
    def test_get_llm_for_command_matching_action(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        # swot is the action command
        config = d.get_llm_for_command("swot")
        assert "model" in config
        assert "base_url" in config
        assert "escalation_level" in config

    def test_get_llm_for_command_different_from_action(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        config = d.get_llm_for_command("pivot")
        assert config["escalation_level"] == "cloud_opus"

    def test_create_llm_client_import_error(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        with patch.dict("sys.modules", {"src.core.adapters.llm.client": None}):
            client = d.create_llm_client_for_command("swot")
            assert client is None

    def test_create_llm_client_zunef_path_v1_ai(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        zunef_config = {
            "base_url": "https://gateway.zunef.com/v1/ai",
            "model": "claude-fable-5",
            "provider_name": "zunef-strategic",
        }
        with patch.object(d, "get_llm_for_command", return_value=zunef_config), \
             patch("src.core.binh_phap_dispatcher.resolve_llm_provider", return_value=zunef_config), \
             patch("src.core.providers.OpenAICompatibleProvider") as mock_provider, \
             patch("src.core.adapters.llm.client.LLMClient") as mock_client:
            d.create_llm_client_for_command("swot")
            mock_provider.assert_called_once()
            call_kwargs = mock_provider.call_args[1]
            assert call_kwargs["base_url"] == "https://gateway.zunef.com"
            assert call_kwargs["extra_headers"]["X-ZUNEF-CLIENT"] == "claude-code"
            mock_client.assert_called_once()

    def test_create_llm_client_zunef_path_v1(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        zunef_config = {
            "base_url": "https://gateway.zunef.com/v1",
            "model": "claude-fable-5",
            "provider_name": "zunef",
        }
        with patch("src.core.binh_phap_dispatcher.resolve_llm_provider", return_value=zunef_config), \
             patch("src.core.providers.OpenAICompatibleProvider") as mock_provider, \
             patch("src.core.adapters.llm.client.LLMClient"):
            d.create_llm_client_for_command("swot")
            assert mock_provider.call_args[1]["base_url"] == "https://gateway.zunef.com"

    def test_create_llm_client_zunef_fails_falls_through(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        zunef_config = {
            "base_url": "https://gateway.zunef.com/v1",
            "model": "claude-fable-5",
            "provider_name": "zunef",
        }
        with patch("src.core.binh_phap_dispatcher.resolve_llm_provider", return_value=zunef_config), \
             patch("src.core.providers.OpenAICompatibleProvider", side_effect=RuntimeError("Provider err")), \
             patch("src.core.binh_phap_dispatcher.create_provider_for_level", return_value=None), \
             patch("src.core.adapters.llm.client.LLMClient") as mock_client:
            d.create_llm_client_for_command("swot")
            # Falls through to final fallback
            mock_client.assert_called_with()

    def test_create_llm_client_non_zunef_provider_success(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        anthropic_config = {
            "base_url": "https://api.anthropic.com/v1",
            "model": "claude-sonnet-4-6",
            "provider_name": "anthropic-sonnet",
        }
        mock_prov = MagicMock()
        with patch("src.core.binh_phap_dispatcher.resolve_llm_provider", return_value=anthropic_config), \
             patch("src.core.binh_phap_dispatcher.create_provider_for_level", return_value=mock_prov), \
             patch("src.core.adapters.llm.client.LLMClient") as mock_client:
            d.create_llm_client_for_command("launch")
            mock_client.assert_called_once_with(providers=[mock_prov])

    def test_create_llm_client_non_zunef_provider_exception(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        anthropic_config = {
            "base_url": "https://api.anthropic.com/v1",
            "model": "claude-sonnet-4-6",
            "provider_name": "anthropic-sonnet",
        }
        mock_prov = MagicMock()
        with patch("src.core.binh_phap_dispatcher.resolve_llm_provider", return_value=anthropic_config), \
             patch("src.core.binh_phap_dispatcher.create_provider_for_level", return_value=mock_prov), \
             patch("src.core.adapters.llm.client.LLMClient", side_effect=[Exception("init failed"), MagicMock()]) as mock_client:
            d.create_llm_client_for_command("launch")
            assert mock_client.call_count == 2

    def test_create_llm_client_local_mlx_fallback_success(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        # swot in Ch1 gets STRATEGIC from topology, but let's test a command that yields local_mlx
        with patch.object(d.topology, "get_llm_provider", return_value="local_mlx"), \
             patch.object(d.topology, "dispatch_next", return_value={"command": "standup", "llm": "local_mlx"}), \
             patch("src.core.binh_phap_dispatcher.create_provider_for_level", return_value=None), \
             patch("src.core.providers.OpenAICompatibleProvider") as mock_prov, \
             patch("src.core.adapters.llm.client.LLMClient") as mock_client:
            d.create_llm_client_for_command("standup")
            mock_prov.assert_called_once()
            assert mock_prov.call_args[1]["model"] == "qwen3.5-9b"
            mock_client.assert_called_once()

    def test_create_llm_client_local_mlx_fallback_exception(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        with patch.object(d.topology, "get_llm_provider", return_value="local_mlx"), \
             patch.object(d.topology, "dispatch_next", return_value={"command": "standup", "llm": "local_mlx"}), \
             patch("src.core.binh_phap_dispatcher.create_provider_for_level", return_value=None), \
             patch("src.core.providers.OpenAICompatibleProvider", side_effect=Exception("ollama down")), \
             patch("src.core.adapters.llm.client.LLMClient") as mock_client:
            d.create_llm_client_for_command("standup")
            mock_client.assert_called_with()


# ---------------------------------------------------------------------------
# Domain module registry & execution
# ---------------------------------------------------------------------------


class TestDomainExecution:
    def test_get_domain_meta_exact(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        meta = d._get_domain_meta("budget")
        assert meta == ("src.commercial.finance", "FinanceEngine", "budget_review")

    def test_get_domain_meta_prefix(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        meta = d._get_domain_meta("growth:experiment:subtopic")
        assert meta == ("src.commercial.growth", "GrowthEngine", "experiment")

    def test_get_domain_meta_unmatched(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        meta = d._get_domain_meta("unknown_xyz")
        assert meta is None

    def test_execute_domain_not_registered(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        res = d._execute_domain("unsupported_topic", prompt="test")
        assert "error" in res
        assert res["domain"] == "unsupported_topic"
        assert "available" in res

    def test_execute_domain_success_dict(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        mock_instance = MagicMock()
        mock_instance.budget_review.return_value = {"approved": True, "amount": 5000}
        mock_class = MagicMock(return_value=mock_instance)
        mock_mod = MagicMock(FinanceEngine=mock_class)

        with patch("importlib.import_module", return_value=mock_mod):
            res = d._execute_domain("budget", prompt="Review Q3", context={"quarter": "Q3"})
            assert res["approved"] is True
            assert res["domain"] == "budget"
            assert res["module"] == "src.commercial.finance"
            assert res["method"] == "budget_review"
            mock_instance.budget_review.assert_called_once_with(quarter="Q3", prompt="Review Q3")

    def test_execute_domain_success_non_dict(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        mock_instance = MagicMock()
        mock_instance.check.return_value = "all systems healthy"
        mock_class = MagicMock(return_value=mock_instance)
        mock_mod = MagicMock(HealthMonitor=mock_class)

        with patch("importlib.import_module", return_value=mock_mod):
            res = d._execute_domain("health", prompt="check status")
            assert res["result"] == "all systems healthy"
            assert res["domain"] == "health"

    def test_execute_domain_exception_handled(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        with patch("importlib.import_module", side_effect=ImportError("No module named foo")):
            res = d._execute_domain("budget", prompt="crash")
            assert "error" in res
            assert "No module named foo" in res["error"]

    def test_execute_for_topic(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        with patch.object(d, "_execute_domain", return_value={"status": "done"}) as mock_exec:
            res = d.execute_for_topic("budget", prompt="plan", context={"c": 1})
            mock_exec.assert_called_once_with("budget", "plan", {"c": 1})
            assert res["status"] == "done"
            assert "meta" in res
            assert "topology" in res
            assert res["meta"]["dimension"] == "vertical"

    def test_execute_llm_with_domain(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        res = d.execute_llm("test prompt", domain="pricing")
        assert res["domain"] == "pricing"
        assert res["prompt"] == "test prompt"
        assert "llm" in res
        assert "note" in res

    def test_execute_llm_without_domain(self, tmp_company: str) -> None:
        d = BinhPhapDispatcher(company_json=tmp_company)
        res = d.execute_llm("test prompt", domain=None)
        assert res["domain"] == "swot"
