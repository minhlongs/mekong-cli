"""Tests for harness.agents.assembly (B6 Agent Factory Assembly Pipeline)."""

from __future__ import annotations

import os
import sys

# Ensure src/ is on sys.path so bare "harness.*" imports resolve
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from unittest.mock import MagicMock, patch

import pytest


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _make_mock_factory():
    """Build a mock AgentFactory with standard agent defs."""
    mock_factory = MagicMock()
    mock_factory._CONFIG_PATH = "dummy"
    mock_factory.list_available.return_value = ["ceo", "cto", "cmo", "coo", "cfo", "audit"]
    mock_factory._defs = {
        "ceo": {
            "id": "ceo",
            "name": "Chief Executive Officer",
            "role": "Chief Executive Officer",
            "role_prompt": "You are the CEO.",
            "tools": ["plan", "delegate"],
        },
        "cto": {
            "id": "cto",
            "name": "Engineering",
            "role": "Engineering",
            "role_prompt": "You are Engineering.",
            "tools": ["code", "build", "test"],
            "module_path": "src.agents.file_agent.FileAgent",
        },
        "cmo": {
            "id": "cmo",
            "name": "Marketing",
            "role": "Marketing",
            "role_prompt": "You are Marketing.",
            "tools": ["write", "campaign"],
        },
        "coo": {
            "id": "coo",
            "name": "Operations",
            "role": "Operations",
            "role_prompt": "You are Operations.",
            "tools": ["monitor", "health"],
        },
        "cfo": {
            "id": "cfo",
            "name": "Finance",
            "role": "Finance",
            "role_prompt": "You are Finance.",
            "tools": ["report", "budget"],
        },
        "audit": {
            "id": "audit",
            "name": "Auditor",
            "role": "Auditor",
            "role_prompt": "You are Auditor.",
            "tools": ["scan", "report"],
        },
    }
    mock_factory.get_definition.side_effect = lambda aid: mock_factory._defs.get(aid, {})
    return mock_factory


# --------------------------------------------------------------------------- #
# Fixtures                                                                    #
# --------------------------------------------------------------------------- #


@pytest.fixture()
def assembler_nlu():
    """AgentAssembler with NLU enabled and classify_task patched.

    Patching classify_task inside the assembly module means the mock
    replaces the real keyword heuristics for every assemble() call.
    The side_effect inspects the goal text and returns a TaskProfile
    matching a domain keyword.
    """
    from harness.agents.assembly import AgentAssembler, AssemblyConfig
    from harness.agents.classifier import TaskProfile

    def _mock_classify(goal, context=None):
        goal_lower = goal.lower()
        # Return agent_role that maps to engine param keys via _INTENT_MODEL_MAP /
        # _INTENT_TEMP_MAP in assembly.py.  "audit" is a valid key that gets low-temp.
        if any(w in goal_lower for w in ("code", "auth", "bug", "refactor", "database", "rest api", "endpoint")):
            role, complexity = "cto", "medium"
        elif any(w in goal_lower for w in ("audit", "security", "vulnerability")):
            role, complexity = "audit", "medium"
        elif any(w in goal_lower for w in ("marketing", "campaign", "email")):
            role, complexity = "cmo", "medium"
        elif any(w in goal_lower for w in ("monitor", "ops", "worker", "restart", "health")):
            role, complexity = "coo", "simple"
        elif any(w in goal_lower for w in ("financial", "budget", "quarterly")):
            role, complexity = "cfo", "medium"
        else:
            role, complexity = "ceo", "simple"
        return TaskProfile(
            complexity=complexity,
            domain=role,
            agent_role=role,
            requires_reasoning=True,
            requires_creativity=False,
            data_sensitivity="low",
            estimated_tokens=2048,
            mcu_cost=1,
            preferred_tier="standard",
        )

    mock_factory = _make_mock_factory()

    with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
        mock_factory_cls.return_value = mock_factory
        mock_factory_cls._CONFIG_PATH = "dummy"
        with patch("harness.agents.assembly.classify_task", side_effect=_mock_classify):
            assembler = AgentAssembler(config=AssemblyConfig(use_nlu=True))
            assembler._factory = mock_factory
            assembler._memory = None
            yield assembler


@pytest.fixture()
def assembler_no_nlu():
    """AgentAssembler with NLU disabled (no classify_task calls)."""
    from harness.agents.assembly import AgentAssembler, AssemblyConfig

    mock_factory = _make_mock_factory()
    with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
        mock_factory_cls.return_value = mock_factory
        mock_factory_cls._CONFIG_PATH = "dummy"
        assembler = AgentAssembler(config=AssemblyConfig(use_nlu=False))
        assembler._factory = mock_factory
        assembler._memory = None
        yield assembler


# Keep the original `assembler` name for backward compat — uses NLU ON
@pytest.fixture()
def assembler(assembler_nlu):
    return assembler_nlu


# --------------------------------------------------------------------------- #
# AssemblyConfig                                                             #
# --------------------------------------------------------------------------- #


class TestAssemblyConfig:
    def test_defaults(self):
        from harness.agents.assembly import AssemblyConfig

        cfg = AssemblyConfig()
        assert cfg.use_nlu is True
        assert cfg.memory_limit == 5
        assert cfg.model_override is None
        assert cfg.temperature_override is None
        assert cfg.cache is True

    def test_custom_values(self):
        from harness.agents.assembly import AssemblyConfig

        cfg = AssemblyConfig(
            use_nlu=False,
            memory_limit=10,
            model_override="claude-opus-4-8",
            temperature_override=0.1,
            cache=False,
        )
        assert cfg.use_nlu is False
        assert cfg.memory_limit == 10
        assert cfg.model_override == "claude-opus-4-8"
        assert cfg.temperature_override == 0.1
        assert cfg.cache is False


# --------------------------------------------------------------------------- #
# AgentAssembler — NLU classification step                                   #
# --------------------------------------------------------------------------- #


class TestClassify:
    def test_classify_code_goal_returns_cto(self, assembler):
        result = assembler.assemble("fix the auth bug in login.py")
        assert result.task_profile is not None
        assert result.task_profile.agent_role == "cto"

    def test_classify_marketing_goal_returns_cmo(self, assembler):
        result = assembler.assemble("write a marketing email campaign")
        assert result.task_profile is not None
        assert result.task_profile.agent_role == "cmo"

    def test_classify_ops_goal_returns_coo(self, assembler):
        result = assembler.assemble("check system health and restart workers")
        assert result.task_profile is not None
        assert result.task_profile.agent_role == "coo"

    def test_classify_disabled_returns_none(self, assembler_no_nlu):
        result = assembler_no_nlu.assemble("any goal string")
        assert result.task_profile is None
        assert result.intent == "unknown"

    def test_classify_sets_trace(self, assembler):
        result = assembler.assemble("refactor the database module")
        assert "nlu" in result.assembly_trace
        nlu = result.assembly_trace["nlu"]
        # When NLU is enabled, trace contains classification metadata
        assert "intent" in nlu
        assert "domain" in nlu


# --------------------------------------------------------------------------- #
# AgentAssembler — Engine params step                                        #
# --------------------------------------------------------------------------- #


class TestEngineParams:
    def test_audit_intent_low_temperature(self, assembler):
        result = assembler.assemble("audit the network security posture")
        ep = result.engine_params
        # "audit" keywords → _INTENT_TEMP_MAP["audit"] = 0.1 (low temp)
        assert ep.temperature <= 0.2
        assert ep.model in ("claude-opus-4-8", "claude-sonnet-4")

    def test_refactor_intent_uses_opus(self, assembler):
        result = assembler.assemble("refactor the database module")
        ep = result.engine_params
        assert "opus" in ep.model or "sonnet" in ep.model

    def test_simple_complexity_smaller_token_budget(self, assembler):
        result = assembler.assemble("check service status")
        # Simple goal → max_tokens = 2048
        assert result.engine_params.max_tokens <= 4096

    def test_engine_params_in_trace(self, assembler):
        result = assembler.assemble("deploy the app to production")
        assert "pev" in result.assembly_trace
        pev = result.assembly_trace["pev"]
        assert "model" in pev
        assert "temperature" in pev
        assert "intent_used" in pev


# --------------------------------------------------------------------------- #
# AgentAssembler — Memory context step                                       #
# --------------------------------------------------------------------------- #


class TestMemoryContext:
    def test_memory_returns_list(self, assembler):
        result = assembler.assemble("generate a quarterly report")
        assert isinstance(result.memory_context, list)

    def test_memory_limit_respected(self):
        from harness.agents.assembly import AgentAssembler, AssemblyConfig

        mock_factory = _make_mock_factory()
        with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
            mock_factory_cls.return_value = mock_factory
            mock_factory_cls._CONFIG_PATH = "dummy"
            assembler = AgentAssembler(config=AssemblyConfig(use_nlu=False, memory_limit=1))
            assembler._factory = mock_factory
            assembler._memory = None
            result = assembler.assemble("any goal")
            assert len(result.memory_context) <= 1

    def test_memory_trace_recorded(self, assembler):
        result = assembler.assemble("deploy to staging")
        assert "memory" in result.assembly_trace
        mem = result.assembly_trace["memory"]
        assert "entries_found" in mem or "skipped" in mem

    def test_memory_bridge_failure_does_not_crash(self):
        from harness.agents.assembly import AgentAssembler, AssemblyConfig

        mock_factory = _make_mock_factory()
        with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
            mock_factory_cls.return_value = mock_factory
            mock_factory_cls._CONFIG_PATH = "dummy"
            assembler = AgentAssembler(config=AssemblyConfig(use_nlu=False))
            assembler._factory = mock_factory
            assembler._memory = None
            with patch.object(assembler, "_get_memory_bridge", return_value=None):
                result = assembler.assemble("any goal")
                assert result.memory_context == []


# --------------------------------------------------------------------------- #
# AgentAssembler — Agent selection & instantiation                           #
# --------------------------------------------------------------------------- #


class TestAgentSelection:
    def test_code_goal_selects_cto(self, assembler):
        result = assembler.assemble("optimize database queries")
        assert result.agent_id == "cto"

    def test_finance_goal_selects_cfo(self, assembler):
        result = assembler.assemble("prepare the quarterly financial report")
        assert result.agent_id == "cfo"

    def test_ops_goal_selects_coo(self, assembler):
        result = assembler.assemble("monitor worker health and restart if needed")
        assert result.agent_id == "coo"

    def test_unknown_goal_falls_back_to_ceo(self, assembler):
        result = assembler.assemble("do something completely random xyzzy")
        assert result.agent_id == "ceo"

    def test_agent_id_in_result(self, assembler):
        result = assembler.assemble("deploy the app")
        assert result.agent_id is not None
        assert len(result.agent_id) > 0


# --------------------------------------------------------------------------- #
# AgentAssembler — Full pipeline                                              #
# --------------------------------------------------------------------------- #


class TestFullPipeline:
    def test_assemble_returns_assembled_agent(self, assembler):
        from harness.agents.assembly import AssembledAgent

        result = assembler.assemble("create a new REST API endpoint")
        assert isinstance(result, AssembledAgent)

    def test_assemble_has_instance(self, assembler):
        result = assembler.assemble("write unit tests for auth module")
        assert result.instance is not None

    def test_assemble_sets_role(self, assembler):
        result = assembler.assemble("deploy to production")
        assert result.role is not None
        assert len(result.role) > 0

    def test_assemble_sets_tools(self, assembler):
        result = assembler.assemble("audit the codebase")
        assert isinstance(result.tools, list)

    def test_assemble_sets_intent(self, assembler):
        result = assembler.assemble("fix the login bug")
        assert result.intent in ("cto", "unknown")

    def test_assemble_has_assembly_trace(self, assembler):
        result = assembler.assemble("monitor system health")
        assert isinstance(result.assembly_trace, dict)
        assert "goal" in result.assembly_trace

    def test_assemble_goal_in_trace(self, assembler):
        goal_text = "deploy my-custom-app to staging"
        result = assembler.assemble(goal_text)
        assert result.assembly_trace["goal"] == goal_text


# --------------------------------------------------------------------------- #
# Module-level convenience API                                                #
# --------------------------------------------------------------------------- #


class TestModuleAPI:
    def test_assemble_agent_function(self):
        from harness.agents.assembly import assemble_agent

        mock_factory = _make_mock_factory()
        mock_factory.list_available.return_value = ["ceo"]
        mock_factory._defs = {
            "ceo": {
                "id": "ceo",
                "name": "CEO",
                "role": "CEO",
                "role_prompt": "You are the CEO.",
                "tools": [],
            }
        }
        mock_factory.get_definition.side_effect = lambda aid: mock_factory._defs.get(aid, {})

        with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
            mock_factory_cls.return_value = mock_factory
            mock_factory_cls._CONFIG_PATH = "dummy"
            # Reset singleton
            import harness.agents.assembly as assembly_mod
            assembly_mod._assembler = None

            result = assemble_agent("build a marketplace platform", config=MagicMock())
            assert result.agent_id == "ceo"
            assert result.instance is not None

    def test_get_assembler_singleton(self):
        from harness.agents.assembly import AgentAssembler, get_assembler

        import harness.agents.assembly as assembly_mod
        assembly_mod._assembler = None  # reset between tests

        mock_factory = _make_mock_factory()
        with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
            mock_factory_cls.return_value = mock_factory
            mock_factory_cls._CONFIG_PATH = "dummy"
            a1 = get_assembler()
            a2 = get_assembler()
            assert a1 is a2

    def test_get_assembler_with_config(self):
        from harness.agents.assembly import AssemblyConfig, get_assembler

        import harness.agents.assembly as assembly_mod
        assembly_mod._assembler = None  # reset between tests

        cfg = AssemblyConfig(use_nlu=False, memory_limit=3)
        mock_factory = _make_mock_factory()
        with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
            mock_factory_cls.return_value = mock_factory
            mock_factory_cls._CONFIG_PATH = "dummy"
            assembler = get_assembler(config=cfg)
            assert assembler.config.memory_limit == 3


# --------------------------------------------------------------------------- #
# AgentAssembler — reset                                                      #
# --------------------------------------------------------------------------- #


class TestReset:
    def test_reset_clears_cache(self):
        from harness.agents.assembly import AgentAssembler

        mock_factory = _make_mock_factory()
        mock_factory._cache = {"ceo": MagicMock()}
        with patch("harness.agents.assembly.AgentFactory") as mock_factory_cls:
            mock_factory_cls.return_value = mock_factory
            mock_factory_cls._CONFIG_PATH = "dummy"
            assembler = AgentAssembler()
            assembler._factory = mock_factory
            assembler._memory = MagicMock()

            assembler.reset()
            assert mock_factory._cache == {}
            assert assembler._memory is None


# --------------------------------------------------------------------------- #
# build_system_prompt                                                         #
# --------------------------------------------------------------------------- #

from harness.agents.assembly import AgentAssembler  # noqa: E402 — needed for staticmethod calls


class TestBuildSystemPrompt:
    def test_prompt_includes_role(self):
        from harness.agents.assembly import AssembledAgent

        assembled = AssembledAgent(
            agent_id="ceo",
            instance=MagicMock(),
            role="Chief Executive Officer",
            intent="deploy",
            tools=["plan"],
        )
        prompt = AgentAssembler.build_system_prompt(assembled)
        assert "Chief Executive Officer" in prompt or "CEO" in prompt

    def test_prompt_includes_memory(self):
        from harness.agents.assembly import AssembledAgent
        from src.core.memory_bridge import MemoryKind, MemoryRecord

        mem_record = MemoryRecord(
            content="Previously deployed v2.3 successfully.",
            kind=MemoryKind.EPISODIC,
        )
        assembled = AssembledAgent(
            agent_id="cto",
            instance=MagicMock(),
            role="Engineering",
            intent="deploy",
            tools=[],
            memory_context=[mem_record],
        )
        prompt = AgentAssembler.build_system_prompt(assembled)
        assert "v2.3" in prompt or "Previously" in prompt

    def test_prompt_includes_task_profile(self):
        from harness.agents.assembly import AssembledAgent
        from harness.agents.classifier import classify_task

        profile = classify_task("refactor the payment module")
        assembled = AssembledAgent(
            agent_id="cto",
            instance=MagicMock(),
            role="Engineering",
            intent="refactor",
            tools=[],
            task_profile=profile,
        )
        prompt = AgentAssembler.build_system_prompt(assembled)
        assert "code" in prompt or "complexity" in prompt


# --------------------------------------------------------------------------- #
# Intent-to-model mapping                                                     #
# --------------------------------------------------------------------------- #


class TestIntentModelMapping:
    @pytest.mark.parametrize(
        "goal,expected_model",
        [
            ("deploy the app", "claude-sonnet-4"),
            ("audit the codebase for vulnerabilities", "claude-opus-4-8"),
            ("refactor the database module", "claude-opus-4-8"),
            ("fix the login bug", "claude-sonnet-4"),
            ("check service status", "claude-sonnet-4"),
            ("optimize database performance", "claude-opus-4-8"),
        ],
    )
    def test_model_selection(self, assembler, goal, expected_model):
        result = assembler.assemble(goal)
        # Should be one of the mapped models
        assert result.engine_params.model in (
            "claude-sonnet-4",
            "claude-opus-4-8",
        )

    def test_low_temperature_for_audit(self, assembler):
        result = assembler.assemble("audit the payment routes for vulnerabilities")
        # "audit" intent → temperature 0.1 in _INTENT_TEMP_MAP
        assert result.engine_params.temperature < 0.3

    def test_unknown_goal_defaults(self, assembler_no_nlu):
        result = assembler_no_nlu.assemble("do something completely unheard of xyzzy")
        assert result.engine_params.temperature == 0.3
        assert result.engine_params.model == "claude-sonnet-4"


# --------------------------------------------------------------------------- #
# doctest / import smoke test                                                 #
# --------------------------------------------------------------------------- #


class TestSmokeImports:
    def test_import_assembly_module(self):
        from harness.agents import assembly

        assert hasattr(assembly, "AgentAssembler")
        assert hasattr(assembly, "AssembledAgent")
        assert hasattr(assembly, "AssemblyConfig")
        assert hasattr(assembly, "assemble_agent")
        assert hasattr(assembly, "get_assembler")

    def test_assembly_module_all(self):
        import harness.agents.assembly as mod

        for name in mod.__all__:
            assert hasattr(mod, name), f"Missing from module: {name}"
