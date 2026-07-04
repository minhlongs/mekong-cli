"""Tests for Codebuff port: agent schema, tool restriction, pipeline stages."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.agent_base import AgentBase, Result, Task
from src.core.agent_registry import AgentRegistry
from src.core.agent_schema import (
    merge_definition_defaults,
    validate_agent_definition,
)
from src.core.tool_names import ALL_TOOL_NAMES, ALIASES, resolve_tool_name
from src.core.tool_registry import ToolRegistry
from src.core.pipeline_stages import (
    ALL_STAGES,
    EDITOR_STAGE,
    FILE_PICKER_STAGE,
    REVIEWER_STAGE,
    compose_pipeline,
    get_stage,
    stages_by_phase,
)
from src.agents.file_picker_agent import FilePickerAgent
from src.agents.editor_agent import EditorAgent
from src.agents.reviewer_agent import ReviewerAgent


# ─── AgentBase backward compat ────────────────────────────────────────────────

class MinimalAgent(AgentBase):
    """Minimal agent for testing backward compat."""

    def plan(self, input_data: str) -> list[Task]:
        return [Task(id="t1", description="test", input={})]

    def execute(self, task: Task) -> Result:
        return Result(task_id=task.id, success=True, output="done")


def test_agent_base_backward_compat():
    """Existing agents with just name and max_retries still work."""
    agent = MinimalAgent(name="test", max_retries=2)
    assert agent.name == "test"
    assert agent.max_retries == 2
    # New fields have safe defaults
    assert agent.allowed_tools == []
    assert agent.spawnable_agents == []
    assert agent.output_mode == "last_message"
    assert agent.step_hooks == {}


def test_agent_base_new_fields():
    """New fields are accepted and stored correctly."""
    hooks = {"on_step_start": lambda **kw: None}
    agent = MinimalAgent(
        name="test",
        allowed_tools=["read_files", "write_file"],
        spawnable_agents=["git-agent"],
        output_mode="structured",
        step_hooks=hooks,
    )
    assert agent.allowed_tools == ["read_files", "write_file"]
    assert agent.spawnable_agents == ["git-agent"]
    assert agent.output_mode == "structured"
    assert agent.step_hooks == hooks


def test_agent_base_run():
    """run() executes plan + execute + verify loop."""
    agent = MinimalAgent(name="runner")
    results = agent.run("test input")
    assert len(results) == 1
    assert results[0].success is True


def test_agent_base_repr():
    """__repr__ includes name and task count."""
    agent = MinimalAgent(name="repr-test")
    r = repr(agent)
    assert "repr-test" in r
    assert "tasks=" in r


# ─── Step hooks ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fire_hook_sync():
    """Sync hooks are called without error."""
    agent = MinimalAgent(name="hook-test")
    called = []
    agent.step_hooks = {"on_step_start": lambda **kw: called.append(kw)}
    await agent._fire_hook("on_step_start", step=1)
    assert len(called) == 1
    assert called[0]["step"] == 1


@pytest.mark.asyncio
async def test_fire_hook_async():
    """Async hooks are awaited."""
    agent = MinimalAgent(name="hook-test-async")

    async def async_hook(**kw):
        pass

    agent.step_hooks = {"on_step_end": async_hook}
    # Should not raise
    await agent._fire_hook("on_step_end", step=1)


@pytest.mark.asyncio
async def test_fire_hook_missing():
    """Missing hooks are silently skipped."""
    agent = MinimalAgent(name="hook-test")
    # No hooks registered - should not raise
    await agent._fire_hook("nonexistent_hook")


@pytest.mark.asyncio
async def test_fire_hook_error_non_fatal():
    """Hook errors are caught and logged, not raised."""
    agent = MinimalAgent(name="hook-test")

    def bad_hook(**kw):
        raise RuntimeError("hook failed")

    agent.step_hooks = {"on_error": bad_hook}
    # Should not raise
    await agent._fire_hook("on_error")


# ─── AgentRegistry ────────────────────────────────────────────────────────────

def test_registry_register_and_get():
    """Basic register/get works."""
    reg = AgentRegistry()
    reg.register("minimal", MinimalAgent)
    assert reg.get("minimal") is MinimalAgent


def test_registry_warns_non_agent(caplog):
    """Registering non-AgentBase logs warning but does not raise (plugin compat)."""
    import logging
    caplog.set_level(logging.WARNING)
    reg = AgentRegistry()
    reg.register("bad", str)
    assert "bad" in reg
    assert any("not an AgentBase subclass" in r.message for r in caplog.records)


def test_registry_get_unknown():
    """Getting unknown agent raises KeyError with available list."""
    reg = AgentRegistry()
    with pytest.raises(KeyError, match="Available agents"):
        reg.get("nonexistent")


def test_registry_list_agents():
    """list_agents returns sorted names."""
    reg = AgentRegistry()
    reg.register("z-agent", MinimalAgent)
    reg.register("a-agent", MinimalAgent)
    assert reg.list_agents() == ["a-agent", "z-agent"]


def test_registry_contains():
    """'in' operator works."""
    reg = AgentRegistry()
    reg.register("test", MinimalAgent)
    assert "test" in reg
    assert "missing" not in reg


def test_registry_len():
    """len() returns agent count."""
    reg = AgentRegistry()
    assert len(reg) == 0
    reg.register("a", MinimalAgent)
    assert len(reg) == 1


def test_registry_with_allowed_tools():
    """Registry accepts allowed_tools metadata."""
    reg = AgentRegistry()
    reg.register("editor", EditorAgent, allowed_tools=["read_files", "write_file"])
    meta = reg.get_meta("editor")
    assert "read_files" in meta["allowed_tools"]


def test_registry_warns_unknown_tools(caplog):
    """Registry warns (not raises) for unknown tool names."""
    import logging
    caplog.set_level(logging.WARNING)
    reg = AgentRegistry()
    # Should log warning but still register (softened per M1)
    reg.register("bad", MinimalAgent, allowed_tools=["nonexistent_tool"])
    assert "bad" in reg
    assert any("nonexistent_tool" in r.message for r in caplog.records)


def test_registry_accepts_wildcard():
    """Wildcard '*' in allowed_tools is accepted."""
    reg = AgentRegistry()
    reg.register("wild", MinimalAgent, allowed_tools=["*"])
    meta = reg.get_meta("wild")
    assert "*" in meta["allowed_tools"]


# ─── Tool names ───────────────────────────────────────────────────────────────

def test_resolve_tool_name_canonical():
    """Canonical names pass through unchanged."""
    assert resolve_tool_name("read_files") == "read_files"
    assert resolve_tool_name("code_search") == "code_search"


def test_resolve_tool_name_alias():
    """Aliases are resolved to canonical names."""
    assert resolve_tool_name("git_status") == "git:status"
    assert resolve_tool_name("shell_run") == "shell:run"
    assert resolve_tool_name("read_file") == "read_files"


def test_all_tool_names_no_duplicates():
    """ALL_TOOL_NAMES has no duplicates."""
    assert len(ALL_TOOL_NAMES) == len(set(ALL_TOOL_NAMES))


def test_aliases_resolve_to_canonical():
    """Every alias maps to a name in ALL_TOOL_NAMES."""
    for alias, canonical in ALIASES.items():
        assert canonical in ALL_TOOL_NAMES, f"Alias {alias} -> {canonical} not in ALL_TOOL_NAMES"


# ─── ToolRegistry restriction ─────────────────────────────────────────────────

@pytest.fixture
def registry() -> ToolRegistry:
    reg = ToolRegistry(persist_path=None)
    # Clear builtins for clean test
    reg._tools.clear()
    return reg


def test_list_for_agent_empty_allowed(registry: ToolRegistry):
    """Empty allowed_tools returns all tools."""
    registry.register("t1", "tool one", handler=lambda: "one")
    registry.register("t2", "tool two", handler=lambda: "two")

    class EmptyAgent:
        allowed_tools = []

    result = registry.list_for_agent(EmptyAgent())
    assert len(result) == 2


def test_list_for_agent_wildcard(registry: ToolRegistry):
    """Wildcard '*' returns all tools."""
    registry.register("t1", "tool one", handler=lambda: "one")

    class WildAgent:
        allowed_tools = ["*"]

    result = registry.list_for_agent(WildAgent())
    assert len(result) == 1


def test_list_for_agent_restricted(registry: ToolRegistry):
    """Restricted agent gets only allowed tools."""
    registry.register("read", "read tool", handler=lambda: "r")
    registry.register("write", "write tool", handler=lambda: "w")
    registry.register("exec", "exec tool", handler=lambda: "e")

    class RestrictedAgent:
        allowed_tools = ["read", "write"]

    result = registry.list_for_agent(RestrictedAgent())
    assert len(result) == 2
    names = [t.name for t in result]
    assert "read" in names
    assert "write" in names
    assert "exec" not in names


def test_validate_call_allowed(registry: ToolRegistry):
    """validate_call returns True for allowed tools."""

    class Agent:
        allowed_tools = ["read"]

    assert registry.validate_call(Agent(), "read") is True


def test_validate_call_denied(registry: ToolRegistry):
    """validate_call returns False for denied tools."""

    class Agent:
        allowed_tools = ["read"]

    assert registry.validate_call(Agent(), "write") is False


def test_validate_call_empty_allowed(registry: ToolRegistry):
    """Empty allowed_tools allows everything."""

    class Agent:
        allowed_tools = []

    assert registry.validate_call(Agent(), "anything") is True


# ─── Agent schema validation ──────────────────────────────────────────────────

def test_validate_valid_definition():
    """Valid definition passes."""
    errors = validate_agent_definition({
        "id": "test-agent",
        "displayName": "Test Agent",
        "allowedTools": ["read_files"],
        "spawnableAgents": ["git"],
        "outputMode": "last_message",
        "stepHooks": {"on_step_start": lambda: None},
    })
    assert errors == []


def test_validate_missing_id():
    """Missing id is caught."""
    errors = validate_agent_definition({"displayName": "Test"})
    assert any("id" in e for e in errors)


def test_validate_missing_display_name():
    """Missing displayName is caught."""
    errors = validate_agent_definition({"id": "test"})
    assert any("displayName" in e for e in errors)


def test_validate_invalid_output_mode():
    """Invalid outputMode is caught."""
    errors = validate_agent_definition({
        "id": "test",
        "displayName": "Test",
        "outputMode": "invalid_mode",
    })
    assert any("outputMode" in e for e in errors)


def test_validate_invalid_step_hook():
    """Unknown stepHook name is caught."""
    errors = validate_agent_definition({
        "id": "test",
        "displayName": "Test",
        "stepHooks": {"unknown_hook": lambda: None},
    })
    assert any("stepHook" in e for e in errors)


def test_merge_defaults():
    """merge_definition_defaults fills in safe defaults."""
    result = merge_definition_defaults({"id": "test"})
    assert result["allowedTools"] == ["*"]
    assert result["spawnableAgents"] == []
    assert result["outputMode"] == "last_message"
    assert result["stepHooks"] == {}


# ─── Pipeline stages ──────────────────────────────────────────────────────────

def test_get_stage():
    """get_stage returns correct stage."""
    stage = get_stage("file-picker")
    assert stage.name == "file-picker"
    assert stage.phase == "plan"


def test_get_stage_unknown():
    """get_stage raises KeyError for unknown stage."""
    with pytest.raises(KeyError, match="Unknown pipeline stage"):
        get_stage("nonexistent")


def test_all_stages_defined():
    """All expected stages exist."""
    assert "file-picker" in ALL_STAGES
    assert "editor" in ALL_STAGES
    assert "reviewer" in ALL_STAGES


def test_stage_phases():
    """Each stage has correct PEV phase."""
    assert FILE_PICKER_STAGE.phase == "plan"
    assert EDITOR_STAGE.phase == "execute"
    assert REVIEWER_STAGE.phase == "verify"


def test_stages_by_phase():
    """stages_by_phase returns correct stages."""
    plan_stages = stages_by_phase("plan")
    assert len(plan_stages) == 1
    assert plan_stages[0].name == "file-picker"

    verify_stages = stages_by_phase("verify")
    assert len(verify_stages) == 1
    assert verify_stages[0].name == "reviewer"


def test_compose_pipeline_default():
    """compose_pipeline with no args returns DEFAULT_PIPELINE (all 3 stages)."""
    stages = compose_pipeline()
    assert len(stages) == 3
    assert [s.name for s in stages] == ["file-picker", "editor", "reviewer"]


def test_compose_pipeline_explicit():
    """compose_pipeline with explicit names."""
    stages = compose_pipeline(["file-picker", "editor"])
    assert len(stages) == 2
    assert stages[0].name == "file-picker"
    assert stages[1].name == "editor"


def test_compose_pipeline_with_phase_filter():
    """compose_pipeline filters by phase."""
    stages = compose_pipeline(["file-picker", "editor", "reviewer"], enabled_phases=["plan"])
    assert len(stages) == 1
    assert stages[0].name == "file-picker"


# ─── Specialized agents ───────────────────────────────────────────────────────

def test_file_picker_agent():
    """FilePickerAgent has correct tool restriction."""
    agent = FilePickerAgent()
    assert agent.name == "FilePickerAgent"
    assert "read_files" in agent.allowed_tools
    assert "write_file" not in agent.allowed_tools


def test_file_picker_find_relevant(tmp_path):
    """FilePickerAgent finds relevant files."""
    # Create test files
    (tmp_path / "auth.py").write_text("# auth module")
    (tmp_path / "user_service.py").write_text("# user service")
    (tmp_path / "random.txt").write_text("irrelevant")

    agent = FilePickerAgent(root=str(tmp_path), max_files=10)
    task = Task(id="scan", description="find auth files", input={})
    result = agent.execute(task)
    assert result.success is True
    assert "auth.py" in result.output


def test_file_picker_skips_symlinks(tmp_path):
    """Symlinks are not followed — prevents symlink DoS."""
    # Create a real file and a symlink pointing outside the tree
    (tmp_path / "real.py").write_text("# real module")
    outside = tmp_path / "outside.py"
    outside.write_text("# outside file")
    symlink = tmp_path / "link_to_outside.py"
    symlink.symlink_to(outside)

    agent = FilePickerAgent(root=str(tmp_path), max_files=10)
    task = Task(id="scan", description="find files", input={})
    result = agent.execute(task)

    assert result.success is True
    # The symlinked path must NOT appear in results
    assert "link_to_outside.py" not in result.output
    # The real file should still be found
    assert "real.py" in result.output




def test_editor_agent():
    """EditorAgent has correct tool restriction."""
    agent = EditorAgent()
    assert agent.name == "EditorAgent"
    assert "write_file" in agent.allowed_tools
    assert "code_search" not in agent.allowed_tools


def test_reviewer_agent():
    """ReviewerAgent has correct tool restriction."""
    agent = ReviewerAgent()
    assert agent.name == "ReviewerAgent"
    assert "code_search" in agent.allowed_tools
    assert "write_file" not in agent.allowed_tools


def test_specialized_agents_backward_compat():
    """Specialized agents work with base AgentBase interface."""
    picker = FilePickerAgent()
    editor = EditorAgent()
    reviewer = ReviewerAgent()

    # All have standard AgentBase interface
    for agent in [picker, editor, reviewer]:
        assert hasattr(agent, "plan")
        assert hasattr(agent, "execute")
        assert hasattr(agent, "verify")
        assert hasattr(agent, "run")


# ─── build_message_chain tool restriction ──────────────────────────────────────

@pytest.fixture
def registry_with_tools() -> ToolRegistry:
    reg = ToolRegistry(persist_path=None)
    reg._tools.clear()
    reg.register("read_files", "Read files", handler=lambda: None)
    reg.register("write_file", "Write file", handler=lambda: None)
    reg.register("code_search", "Search code", handler=lambda: None)
    reg.register("shell_run", "Run shell", handler=lambda: None)
    return reg


def test_build_message_chain_with_tool_restriction(
    registry_with_tools: ToolRegistry,
) -> None:
    """build_message_chain returns filtered available_tools when agent has allowed_tools."""
    from src.core.agent_dispatcher import build_message_chain

    class RestrictedAgent:
        allowed_tools = ["read_files", "code_search"]

    agent = RestrictedAgent()

    messages, system_prompt, available_tools = build_message_chain(
        goal="find auth files",
        agent_role="file-picker",
        domain="code",
        agent=agent,
        tool_registry=registry_with_tools,
    )

    assert len(available_tools) == 2
    assert "read_files" in available_tools
    assert "code_search" in available_tools
    assert "write_file" not in available_tools
    assert "shell_run" not in available_tools


def test_build_message_chain_no_agent_no_filter(
    registry_with_tools: ToolRegistry,
) -> None:
    """Without agent, available_tools is empty (no restriction applied)."""
    from src.core.agent_dispatcher import build_message_chain

    messages, system_prompt, available_tools = build_message_chain(
        goal="test",
        agent_role="test",
        domain="code",
        tool_registry=registry_with_tools,
    )

    assert available_tools == []


def test_build_message_chain_wildcard_agent(
    registry_with_tools: ToolRegistry,
) -> None:
    """Agent with wildcard '*' gets all registered tools."""
    from src.core.agent_dispatcher import build_message_chain

    class WildAgent:
        allowed_tools = ["*"]

    messages, system_prompt, available_tools = build_message_chain(
        goal="test",
        agent_role="test",
        domain="code",
        agent=WildAgent(),
        tool_registry=registry_with_tools,
    )

    assert len(available_tools) == 4


# ─── FilePickerAgent depth limit ────────────────────────────────────────────────

def test_file_picker_depth_limit(tmp_path: Path) -> None:
    """FilePickerAgent respects max_depth and does not crash on deep trees."""
    # Build a nested directory structure deeper than the default max_depth of 10
    deep_dir = tmp_path
    for i in range(12):
        deep_dir = deep_dir / f"level_{i}"
    deep_dir.mkdir(parents=True)
    (deep_dir / "deep_file.py").write_text("# deep file")

    # Also place a file at a shallow depth so the agent has something to find
    (tmp_path / "shallow.py").write_text("# shallow file")

    agent = FilePickerAgent(root=str(tmp_path), max_depth=10, max_files=20)
    # Use a goal that matches the filenames (keyword matching checks path strings)
    task = Task(id="scan", description="find shallow deep file", input={})
    result = agent.execute(task)

    assert result.success is True
    # shallow.py should be found; the deep file at depth 12 should be excluded
    assert "shallow.py" in result.output
    assert "deep_file.py" not in result.output


# ─── FilePickerAgent hidden directory skipping ──────────────────────────────────

def test_file_picker_skips_hidden_dirs(tmp_path: Path) -> None:
    """FilePickerAgent skips files inside directories starting with '.'."""
    hidden_dir = tmp_path / ".hidden"
    hidden_dir.mkdir()
    (hidden_dir / "secret.py").write_text("# secret code")
    (hidden_dir / "config.yaml").write_text("key: value")

    visible_dir = tmp_path / "src"
    visible_dir.mkdir()
    (visible_dir / "main.py").write_text("# main code")

    agent = FilePickerAgent(root=str(tmp_path), max_depth=10, max_files=20)
    task = Task(id="scan", description="find source files", input={})
    result = agent.execute(task)

    assert result.success is True
    assert "main.py" in result.output
    assert "secret.py" not in result.output
    assert ".hidden" not in result.output
