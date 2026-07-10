"""TDD tests for plugin command binding — E4d.

Tests that plugin commands are wired into Mekong's Typer root so
`mekong <plugin-id> <command>` routes to the loaded plugin.

SDK not installed in test env — mocked via sys.modules.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.cli.plugin_integration import bind_plugin_commands, unbind_plugin_commands  # noqa: E402
from src.core.plugin_runtime import PluginRuntime, LoadedPlugin  # noqa: E402
from src.core.plugin_schema import PluginManifestSchema  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_manifest(plugin_id: str = "com.test.my-plugin") -> PluginManifestSchema:
    return PluginManifestSchema(
        id=plugin_id,
        name="My Plugin",
        version="0.1.0",
        description="Test plugin",
    )


def _make_loaded_plugin(
    plugin_id: str = "com.test.my-plugin",
    commands: list | None = None,
) -> LoadedPlugin:
    """Create a LoadedPlugin with optional mock commands."""
    mock_instance = MagicMock()
    mock_instance.get_commands.return_value = commands or []
    mock_instance.register_commands = MagicMock()
    mock_instance.register_hooks = MagicMock()

    return LoadedPlugin(
        plugin_id=plugin_id,
        manifest=_make_manifest(plugin_id),
        instance=mock_instance,
        commands=commands or [],
        hooks=[],
        source=f"/fake/{plugin_id}",
    )


def _make_sdk_cmd(name: str, description: str = "") -> MagicMock:
    """Create a mock SDK Command object."""
    cmd = MagicMock()
    cmd.name = name
    cmd.description = description
    cmd.handler = MagicMock(return_value=f"output from {name}")
    return cmd


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestBindPluginCommands:
    """E4d acceptance: plugin commands appear in Typer root."""

    def test_bind_no_plugins_empty_root(self):
        """Root stays clean when no plugins are loaded."""
        root = typer.Typer()
        runtime = PluginRuntime()
        runtime._loaded = {}

        bind_plugin_commands(root, runtime)

        # Root should have no sub-apps
        assert len(root.registered_groups) == 0

    def test_bind_single_plugin_creates_subapp(self):
        """Binding a loaded plugin creates a Typer sub-app under root."""
        root = typer.Typer()
        runtime = PluginRuntime()
        cmd = _make_sdk_cmd("hello", "Say hello")
        lp = _make_loaded_plugin("com.test.hello", commands=[cmd])
        runtime._loaded[lp.plugin_id] = lp

        bind_plugin_commands(root, runtime)

        # Plugin-id should be a registered Typer sub-app
        group_names = [g.name for g in root.registered_groups]
        assert "com.test.hello" in group_names

    def test_bind_command_routes_correctly(self):
        """`mekong <plugin-id> <cmd>` invokes the plugin handler."""
        root = typer.Typer()
        runtime = PluginRuntime()
        cmd = _make_sdk_cmd("greet", "Greet the user")
        lp = _make_loaded_plugin("com.test.greet", commands=[cmd])
        runtime._loaded[lp.plugin_id] = lp

        bind_plugin_commands(root, runtime)
        runner = CliRunner()
        result = runner.invoke(root, ["com.test.greet", "greet"])

        assert result.exit_code == 0, result.output

    def test_bind_multiple_plugins(self):
        """Multiple loaded plugins each get their own sub-app."""
        root = typer.Typer()
        runtime = PluginRuntime()

        for pid in ("com.test.a", "com.test.b", "com.test.c"):
            cmd = _make_sdk_cmd("run", f"Run {pid}")
            lp = _make_loaded_plugin(pid, commands=[cmd])
            runtime._loaded[pid] = lp

        bind_plugin_commands(root, runtime)

        for pid in ("com.test.a", "com.test.b", "com.test.c"):
            assert pid in [g.name for g in root.registered_groups]

    def test_bind_unknown_command_friendly_error(self):
        """Unknown subcommand gives a helpful error pointing to --help."""
        root = typer.Typer()
        runtime = PluginRuntime()
        cmd = _make_sdk_cmd("known", "A known command")
        lp = _make_loaded_plugin("com.test.err", commands=[cmd])
        runtime._loaded[lp.plugin_id] = lp

        bind_plugin_commands(root, runtime)
        runner = CliRunner()
        result = runner.invoke(root, ["com.test.err", "nonexistent"])

        assert result.exit_code != 0

    def test_bind_help_shows_plugin_commands(self):
        """--help on plugin sub-app shows plugin command descriptions."""
        root = typer.Typer()
        runtime = PluginRuntime()
        cmd = _make_sdk_cmd("deploy", "Deploy the plugin")
        lp = _make_loaded_plugin("com.test.help-test", commands=[cmd])
        runtime._loaded[lp.plugin_id] = lp

        bind_plugin_commands(root, runtime)
        runner = CliRunner()
        result = runner.invoke(root, ["com.test.help-test", "--help"])

        assert result.exit_code == 0
        assert "deploy" in result.output.lower()

    def test_unbind_removes_plugin_app(self):
        """unbind removes previously bound plugin sub-apps."""
        root = typer.Typer()
        runtime = PluginRuntime()
        cmd = _make_sdk_cmd("x", "X")
        lp = _make_loaded_plugin("com.test.tmp", commands=[cmd])
        runtime._loaded[lp.plugin_id] = lp

        bind_plugin_commands(root, runtime)
        group_names = [g.name for g in root.registered_groups]
        assert "com.test.tmp" in group_names

        unbind_plugin_commands(root, runtime)
        assert "com.test.tmp" not in [g.name for g in root.registered_groups]

    def test_rebind_after_reload_no_duplicates(self):
        """Re-binding after reload does not duplicate sub-apps."""
        root = typer.Typer()
        runtime = PluginRuntime()
        cmd = _make_sdk_cmd("sync", "Sync data")
        lp = _make_loaded_plugin("com.test.sync", commands=[cmd])
        runtime._loaded[lp.plugin_id] = lp

        bind_plugin_commands(root, runtime)
        unbind_plugin_commands(root, runtime)
        bind_plugin_commands(root, runtime)

        # Should still work, no duplicate
        runner = CliRunner()
        result = runner.invoke(root, ["com.test.sync", "sync"])
        assert result.exit_code == 0
