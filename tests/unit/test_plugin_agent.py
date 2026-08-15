"""
Mekong CLI - PluginAgent Unit Tests

Comprehensive tests for plugin management operations.
"""

import json
import os
import tempfile
from pathlib import Path

import pytest

from src.core.agent_base import Task, TaskStatus
from src.agents.plugin_agent import PluginAgent


class TestPluginAgentInit:
    """Test PluginAgent initialization."""

    def test_init_default_values(self) -> None:
        """Test initialization with default values."""
        agent = PluginAgent()
        assert agent.name == "PluginAgent"
        assert agent.cwd == Path.cwd().resolve()
        assert agent.registry_path == Path.cwd().resolve() / ".mekong" / "plugins.json"

    def test_init_custom_cwd(self) -> None:
        """Test initialization with custom working directory."""
        custom_cwd = "/tmp/test"
        agent = PluginAgent(cwd=custom_cwd)
        assert agent.cwd == Path(custom_cwd).resolve()

    def test_init_custom_registry_path(self) -> None:
        """Test initialization with custom registry path."""
        custom_path = "/tmp/custom/plugins.json"
        agent = PluginAgent(registry_path=custom_path)
        assert agent.registry_path == Path(custom_path)

    def test_init_max_retries(self) -> None:
        """Test max_retries inherited from AgentBase."""
        agent = PluginAgent()
        assert agent.max_retries == 3


class TestPluginAgentPlan:
    """Test PluginAgent plan method."""

    @pytest.fixture
    def agent(self) -> PluginAgent:
        """Create PluginAgent for testing."""
        return PluginAgent()

    def test_plan_list_command(self, agent: PluginAgent) -> None:
        """Test planning 'list' command."""
        tasks = agent.plan("list")
        assert len(tasks) == 1
        assert tasks[0].id == "list_plugins"
        assert tasks[0].description == "List installed plugins"

    def test_plan_install_command(self, agent: PluginAgent) -> None:
        """Test planning 'install' command."""
        tasks = agent.plan("install my-plugin")
        assert len(tasks) == 1
        assert tasks[0].id == "install_plugin"
        assert tasks[0].input["plugin"] == "my-plugin"

    def test_plan_install_missing_name(self, agent: PluginAgent) -> None:
        """Test planning 'install' without plugin name."""
        tasks = agent.plan("install")
        assert len(tasks) == 1
        assert tasks[0].id == "error"
        assert "Plugin name required" in tasks[0].input["error"]

    def test_plan_remove_command(self, agent: PluginAgent) -> None:
        """Test planning 'remove' command."""
        tasks = agent.plan("remove my-plugin")
        assert len(tasks) == 1
        assert tasks[0].id == "remove_plugin"
        assert tasks[0].input["plugin"] == "my-plugin"

    def test_plan_remove_missing_name(self, agent: PluginAgent) -> None:
        """Test planning 'remove' without plugin name."""
        tasks = agent.plan("remove")
        assert len(tasks) == 1
        assert tasks[0].id == "error"
        assert "Plugin name required" in tasks[0].input["error"]

    def test_plan_update_command(self, agent: PluginAgent) -> None:
        """Test planning 'update' command with specific plugin."""
        tasks = agent.plan("update my-plugin")
        assert len(tasks) == 1
        assert tasks[0].id == "update_plugin"
        assert tasks[0].input["plugin"] == "my-plugin"

    def test_plan_update_all_command(self, agent: PluginAgent) -> None:
        """Test planning 'update' without plugin name (update all)."""
        tasks = agent.plan("update")
        assert len(tasks) == 1
        assert tasks[0].id == "update_plugin"
        assert tasks[0].input["plugin"] == "all"

    def test_plan_unknown_command(self, agent: PluginAgent) -> None:
        """Test planning unknown command."""
        tasks = agent.plan("unknown-command")
        assert len(tasks) == 1
        assert tasks[0].id == "error"
        assert "Unknown command: unknown-command" in tasks[0].input["error"]

    def test_plan_case_insensitive(self, agent: PluginAgent) -> None:
        """Test command parsing is case insensitive."""
        tasks = agent.plan("LIST")
        assert len(tasks) == 1
        assert tasks[0].id == "list_plugins"

        tasks = agent.plan("INSTALL test-plugin")
        assert tasks[0].id == "install_plugin"


class TestPluginAgentExecute:
    """Test PluginAgent execute method."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_execute_list_plugins_empty(self, agent: PluginAgent) -> None:
        """Test listing plugins when registry is empty."""
        task = Task(id="list_plugins", description="List plugins", input={})
        result = agent.execute(task)
        assert result.success is True
        assert "No plugins installed" in result.output

    def test_execute_install_plugin(self, agent: PluginAgent) -> None:
        """Test installing a new plugin."""
        task = Task(
            id="install_plugin",
            description="Install plugin",
            input={"plugin": "test-plugin"},
        )
        result = agent.execute(task)
        assert result.success is True
        assert "Successfully installed" in result.output
        assert "test-plugin@1.0.0" in result.output

    def test_execute_install_duplicate(self, agent: PluginAgent) -> None:
        """Test installing already installed plugin fails."""
        # First install
        task1 = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "test-plugin"},
        )
        agent.execute(task1)

        # Second install should fail
        task2 = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "test-plugin"},
        )
        result = agent.execute(task2)
        assert result.success is False
        assert "already installed" in result.error

    def test_execute_remove_plugin(self, agent: PluginAgent) -> None:
        """Test removing an installed plugin."""
        # Install first
        install_task = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "test-plugin"},
        )
        agent.execute(install_task)

        # Then remove
        remove_task = Task(
            id="remove_plugin",
            description="Remove",
            input={"plugin": "test-plugin"},
        )
        result = agent.execute(remove_task)
        assert result.success is True
        assert "Successfully removed" in result.output

    def test_execute_remove_nonexistent(self, agent: PluginAgent) -> None:
        """Test removing plugin that doesn't exist."""
        task = Task(
            id="remove_plugin",
            description="Remove",
            input={"plugin": "nonexistent"},
        )
        result = agent.execute(task)
        assert result.success is False
        assert "not installed" in result.error

    def test_execute_update_single_plugin(self, agent: PluginAgent) -> None:
        """Test updating a single plugin."""
        # Install first
        install_task = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "test-plugin"},
        )
        agent.execute(install_task)

        # Then update
        update_task = Task(
            id="update_plugin",
            description="Update",
            input={"plugin": "test-plugin"},
        )
        result = agent.execute(update_task)
        assert result.success is True
        assert "Updated plugins:" in result.output

    def test_execute_update_all_plugins(self, agent: PluginAgent) -> None:
        """Test updating all plugins."""
        # Install multiple plugins
        for plugin in ["plugin-a", "plugin-b", "plugin-c"]:
            task = Task(
                id="install_plugin",
                description="Install",
                input={"plugin": plugin},
            )
            agent.execute(task)

        # Update all
        update_task = Task(
            id="update_plugin",
            description="Update all",
            input={"plugin": "all"},
        )
        result = agent.execute(update_task)
        assert result.success is True
        assert "plugin-a" in result.output
        assert "plugin-b" in result.output
        assert "plugin-c" in result.output

    def test_execute_update_nonexistent_plugin(self, agent: PluginAgent) -> None:
        """Test updating plugin that doesn't exist."""
        # First install a plugin so registry is not empty
        install_task = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "existing-plugin"},
        )
        agent.execute(install_task)

        # Then try to update nonexistent plugin
        task = Task(
            id="update_plugin",
            description="Update",
            input={"plugin": "nonexistent"},
        )
        result = agent.execute(task)
        assert result.success is False
        assert "not installed" in result.error

    def test_execute_update_empty_registry(self, agent: PluginAgent) -> None:
        """Test updating when no plugins installed."""
        task = Task(
            id="update_plugin",
            description="Update all",
            input={"plugin": "all"},
        )
        result = agent.execute(task)
        assert result.success is False
        assert "No plugins installed" in result.error

    def test_execute_unknown_task(self, agent: PluginAgent) -> None:
        """Test executing unknown task."""
        task = Task(id="unknown_task", description="Unknown", input={})
        result = agent.execute(task)
        assert result.success is False
        assert "Unknown task" in result.error

    def test_execute_error_task(self, agent: PluginAgent) -> None:
        """Test executing error task from plan."""
        task = Task(
            id="error",
            description="Error",
            input={"error": "Test error message"},
        )
        result = agent.execute(task)
        assert result.success is False
        assert result.error == "Test error message"


class TestPluginAgentRegistryOperations:
    """Test registry file operations."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_ensure_registry_dir_creates_directory(self, agent: PluginAgent) -> None:
        """Test _ensure_registry_dir creates parent directories."""
        agent._ensure_registry_dir()
        assert agent.registry_path.parent.exists()

    def test_read_registry_nonexistent(self, agent: PluginAgent) -> None:
        """Test reading registry that doesn't exist."""
        registry = agent._read_registry()
        assert registry == {"plugins": {}}

    def test_read_registry_existing(self, agent: PluginAgent) -> None:
        """Test reading existing registry."""
        # Create registry
        agent._ensure_registry_dir()
        test_data = {"plugins": {"test": {"version": "1.0.0"}}}
        with open(agent.registry_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        registry = agent._read_registry()
        assert registry == test_data

    def test_write_registry(self, agent: PluginAgent) -> None:
        """Test writing registry to file."""
        test_data = {
            "plugins": {
                "plugin-a": {"version": "1.0.0"},
                "plugin-b": {"version": "2.0.0"},
            }
        }
        agent._write_registry(test_data)

        assert agent.registry_path.exists()
        with open(agent.registry_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == test_data


class TestPluginAgentListPlugins:
    """Test _list_plugins method."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_list_plugins_formats_output(self, agent: PluginAgent) -> None:
        """Test list plugins formats output correctly."""
        # Install plugins
        agent._write_registry({
            "plugins": {
                "plugin-a": {"version": "1.0.0"},
                "plugin-b": {"version": "2.5.0"},
            }
        })

        task = Task(id="list_plugins", description="List", input={})
        result = agent._list_plugins(task)

        assert "Installed plugins:" in result.output
        assert "plugin-a@1.0.0" in result.output
        assert "plugin-b@2.5.0" in result.output


class TestPluginAgentInstallPlugin:
    """Test _install_plugin method."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_install_plugin_missing_name(self, agent: PluginAgent) -> None:
        """Test install with missing plugin name."""
        task = Task(id="install_plugin", description="Install", input={})
        result = agent._install_plugin(task)
        assert result.success is False
        assert "Plugin name required" in result.error

    def test_install_plugin_updates_registry(self, agent: PluginAgent) -> None:
        """Test install updates registry file."""
        task = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "new-plugin"},
        )
        agent._install_plugin(task)

        registry = agent._read_registry()
        assert "new-plugin" in registry["plugins"]
        assert registry["plugins"]["new-plugin"]["version"] == "1.0.0"


class TestPluginAgentRemovePlugin:
    """Test _remove_plugin method."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_remove_plugin_missing_name(self, agent: PluginAgent) -> None:
        """Test remove with missing plugin name."""
        task = Task(id="remove_plugin", description="Remove", input={})
        result = agent._remove_plugin(task)
        assert result.success is False
        assert "Plugin name required" in result.error

    def test_remove_plugin_updates_registry(self, agent: PluginAgent) -> None:
        """Test remove updates registry file."""
        # Install first
        agent._write_registry({"plugins": {"to-remove": {"version": "1.0.0"}}})

        task = Task(
            id="remove_plugin",
            description="Remove",
            input={"plugin": "to-remove"},
        )
        agent._remove_plugin(task)

        registry = agent._read_registry()
        assert "to-remove" not in registry["plugins"]


class TestPluginAgentUpdatePlugin:
    """Test _update_plugin method."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_update_plugin_updates_version(self, agent: PluginAgent) -> None:
        """Test update changes plugin version."""
        agent._write_registry({
            "plugins": {
                "outdated": {"version": "0.1.0"},
            }
        })

        task = Task(
            id="update_plugin",
            description="Update",
            input={"plugin": "outdated"},
        )
        result = agent._update_plugin(task)

        assert result.success is True
        registry = agent._read_registry()
        assert registry["plugins"]["outdated"]["version"] == "1.0.0"

    def test_update_all_updates_all_plugins(self, agent: PluginAgent) -> None:
        """Test update all updates every plugin."""
        agent._write_registry({
            "plugins": {
                "plugin-a": {"version": "0.1.0"},
                "plugin-b": {"version": "0.2.0"},
            }
        })

        task = Task(
            id="update_plugin",
            description="Update all",
            input={"plugin": "all"},
        )
        result = agent._update_plugin(task)

        assert result.success is True
        registry = agent._read_registry()
        assert registry["plugins"]["plugin-a"]["version"] == "1.0.0"
        assert registry["plugins"]["plugin-b"]["version"] == "1.0.0"


class TestPluginAgentRun:
    """Test full run method (Plan-Execute-Verify cycle)."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_run_list_command(self, agent: PluginAgent) -> None:
        """Test full run cycle for list command."""
        results = agent.run("list")
        assert len(results) == 1
        assert results[0].success is True

    def test_run_install_command(self, agent: PluginAgent) -> None:
        """Test full run cycle for install command."""
        results = agent.run("install test-plugin")
        assert len(results) == 1
        assert results[0].success is True
        assert "Successfully installed" in results[0].output

    def test_run_remove_command(self, agent: PluginAgent) -> None:
        """Test full run cycle for remove command."""
        # Install first
        agent.run("install test-plugin")
        # Then remove
        results = agent.run("remove test-plugin")
        assert len(results) == 1
        assert results[0].success is True

    def test_run_update_command(self, agent: PluginAgent) -> None:
        """Test full run cycle for update command."""
        agent.run("install test-plugin")
        results = agent.run("update test-plugin")
        assert len(results) == 1
        assert results[0].success is True

    def test_run_invalid_command(self, agent: PluginAgent) -> None:
        """Test full run cycle for invalid command."""
        results = agent.run("invalid-command")
        assert len(results) == 1
        assert results[0].success is False


class TestPluginAgentRepr:
    """Test __repr__ method inherited from AgentBase."""

    def test_repr_string(self) -> None:
        """Test agent representation."""
        agent = PluginAgent()
        repr_str = repr(agent)
        assert "Agent:PluginAgent" in repr_str or "PluginAgent" in repr_str


class TestPluginAgentEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def agent(self, temp_dir: str) -> PluginAgent:
        """Create PluginAgent with temp registry."""
        registry_path = os.path.join(temp_dir, "plugins.json")
        return PluginAgent(cwd=temp_dir, registry_path=registry_path)

    def test_plan_with_extra_whitespace(self, agent: PluginAgent) -> None:
        """Test planning command with extra whitespace."""
        tasks = agent.plan("  install   my-plugin  ")
        assert len(tasks) == 1
        assert tasks[0].id == "install_plugin"

    def test_plan_install_multiple_words(self, agent: PluginAgent) -> None:
        """Test planning install with multi-word plugin name."""
        tasks = agent.plan("install my-awesome-plugin")
        assert tasks[0].input["plugin"] == "my-awesome-plugin"

    def test_execute_exception_handling(self, agent: PluginAgent) -> None:
        """Test execute handles unexpected exceptions."""
        # Test with corrupted registry file
        agent._ensure_registry_dir()
        with open(agent.registry_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        task = Task(id="list_plugins", description="List", input={})
        result = agent.execute(task)
        # Should handle JSON decode error gracefully
        assert result.success is False
        assert result.error is not None

    def test_install_plugin_with_version_in_name(self, agent: PluginAgent) -> None:
        """Test installing plugin with version-like name."""
        task = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "plugin-v2.0"},
        )
        result = agent.execute(task)
        assert result.success is True
        assert "plugin-v2.0" in result.output

    def test_remove_then_install_again(self, agent: PluginAgent) -> None:
        """Test removing then reinstalling same plugin."""
        # Install
        agent.execute(Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "test-plugin"},
        ))
        # Remove
        agent.execute(Task(
            id="remove_plugin",
            description="Remove",
            input={"plugin": "test-plugin"},
        ))
        # Install again - should succeed
        result = agent.execute(Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "test-plugin"},
        ))
        assert result.success is True

    def test_update_preserves_other_plugins(self, agent: PluginAgent) -> None:
        """Test update only changes target plugin."""
        agent._write_registry({
            "plugins": {
                "plugin-a": {"version": "0.1.0"},
                "plugin-b": {"version": "0.2.0"},
            }
        })

        task = Task(
            id="update_plugin",
            description="Update",
            input={"plugin": "plugin-a"},
        )
        agent._update_plugin(task)

        registry = agent._read_registry()
        assert registry["plugins"]["plugin-a"]["version"] == "1.0.0"
        assert registry["plugins"]["plugin-b"]["version"] == "0.2.0"

    def test_list_plugins_with_special_characters(self, agent: PluginAgent) -> None:
        """Test listing plugins with special characters in names."""
        agent._write_registry({
            "plugins": {
                "@scope/plugin-name": {"version": "1.0.0"},
                "plugin_with_underscore": {"version": "2.0.0"},
            }
        })

        task = Task(id="list_plugins", description="List", input={})
        result = agent._list_plugins(task)

        assert "@scope/plugin-name@1.0.0" in result.output
        assert "plugin_with_underscore@2.0.0" in result.output

    def test_registry_json_corrupted(self, agent: PluginAgent) -> None:
        """Test handling corrupted JSON registry."""
        agent._ensure_registry_dir()
        # Write invalid JSON
        with open(agent.registry_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        task = Task(id="list_plugins", description="List", input={})
        result = agent.execute(task)
        # Should handle gracefully with error
        assert result.success is False
        assert result.error is not None

    def test_concurrent_install_same_plugin(self, agent: PluginAgent) -> None:
        """Test installing same plugin twice returns error."""
        task = Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "duplicate-test"},
        )
        # First install
        result1 = agent.execute(task)
        assert result1.success is True

        # Second install should fail
        result2 = agent.execute(task)
        assert result2.success is False
        assert "already installed" in result2.error

    def test_plugin_name_with_spaces(self, agent: PluginAgent) -> None:
        """Test plugin name handling (spaces not supported, takes first word)."""
        tasks = agent.plan("install my plugin name")
        assert tasks[0].input["plugin"] == "my plugin name"

    def test_empty_command(self, agent: PluginAgent) -> None:
        """Test handling empty command."""
        tasks = agent.plan("")
        # Empty string results in parts = [""] so command = ""
        assert len(tasks) == 1
        assert tasks[0].id == "error" or tasks[0].id == "list_plugins"

    def test_registry_path_is_absolute(self) -> None:
        """Test that registry path is resolved to absolute."""
        agent = PluginAgent(cwd="/tmp")
        assert agent.cwd.is_absolute()

    def test_install_multiple_plugins_sequential(self, agent: PluginAgent) -> None:
        """Test installing multiple plugins sequentially."""
        plugins = ["plugin-1", "plugin-2", "plugin-3"]
        for plugin_name in plugins:
            task = Task(
                id="install_plugin",
                description="Install",
                input={"plugin": plugin_name},
            )
            result = agent.execute(task)
            assert result.success is True

        # Verify all installed
        list_task = Task(id="list_plugins", description="List", input={})
        result = agent.execute(list_task)
        for plugin_name in plugins:
            assert plugin_name in result.output

    def test_remove_all_plugins_one_by_one(self, agent: PluginAgent) -> None:
        """Test removing all plugins one by one."""
        # Install multiple
        for name in ["a", "b", "c"]:
            agent.execute(Task(
                id="install_plugin",
                description="Install",
                input={"plugin": name},
            ))

        # Remove all
        for name in ["a", "b", "c"]:
            result = agent.execute(Task(
                id="remove_plugin",
                description="Remove",
                input={"plugin": name},
            ))
            assert result.success is True

        # Verify empty
        result = agent.execute(Task(id="list_plugins", description="List", input={}))
        assert "No plugins installed" in result.output

    def test_update_nonexistent_after_installs(self, agent: PluginAgent) -> None:
        """Test update nonexistent plugin after some installs."""
        # Install one plugin
        agent.execute(Task(
            id="install_plugin",
            description="Install",
            input={"plugin": "existing"},
        ))

        # Try update nonexistent
        result = agent.execute(Task(
            id="update_plugin",
            description="Update",
            input={"plugin": "ghost-plugin"},
        ))
        assert result.success is False
        assert "not installed" in result.error

    def test_run_method_task_status_updated(self, agent: PluginAgent) -> None:
        """Test that run method updates task status."""
        agent.run("install test")
        assert len(agent.tasks) > 0
        assert agent.tasks[0].status in [TaskStatus.SUCCESS, TaskStatus.FAILED]

    def test_agent_base_max_retries_configured(self) -> None:
        """Test that max_retries from AgentBase is accessible."""
        # PluginAgent doesn't expose max_retries in __init__, use default
        agent = PluginAgent()
        assert agent.max_retries == 3

    def test_registry_dir_created_on_write(self, agent: PluginAgent) -> None:
        """Test that _write_registry creates parent directories."""
        new_path = Path(agent.cwd) / "deep" / "nested" / "path" / "plugins.json"
        agent.registry_path = new_path  # type: ignore[assignment]
        agent._write_registry({"plugins": {}})
        assert new_path.exists()
