"""Tests for plugin command binding — E4d command binding integration."""
from __future__ import annotations

import json
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import typer

from src.core.plugin_binding import PluginBinding, _plugin_slug
from src.core.plugin_runtime import PluginRuntime

# ---------------------------------------------------------------------------
# Helpers — mock the SDK since it is not pip-installed
# ---------------------------------------------------------------------------


def _install_mock_sdk(plugin_id: str = "com.test.mock", version: str = "1.0.0") -> None:
    """Patch sys.modules with a fake packages.mekong_plugin_sdk package."""
    existing = sys.modules.get("packages.mekong_plugin_sdk")
    if (
        existing is not None
        and hasattr(existing, "plugin")
        and callable(getattr(existing.plugin, "create_plugin", None))
    ):
        return

    sdk_pkg = types.ModuleType("packages.mekong_plugin_sdk")

    plugin_mod = types.ModuleType("packages.mekong_plugin_sdk.plugin")
    plugin_mod.create_plugin = MagicMock()
    plugin_mod.MekongPlugin = object
    sdk_pkg.plugin = plugin_mod

    ctx_mod = types.ModuleType("packages.mekong_plugin_sdk.context")
    ctx_mod.PluginContext = MagicMock
    sdk_pkg.context = ctx_mod

    hooks_mod = types.ModuleType("packages.mekong_plugin_sdk.hooks")
    from dataclasses import dataclass, field
    from enum import Enum

    @dataclass
    class HookContext:
        plugin_id: str
        data: dict = field(default_factory=dict)

    class HookPoint(Enum):
        CLI_START = "cli_start"
        CLI_STOP = "cli_stop"
        COMMAND_BEFORE = "command_before"
        COMMAND_AFTER = "command_after"
        PLUGIN_LOADED = "plugin_loaded"
        PLUGIN_UNLOADED = "plugin_unloaded"

    @dataclass
    class HookDef:
        point: HookPoint
        handler: callable

    class HookRegistry:
        def initialize(self, plugin_id):
            pass

        def register(self, hook_def):
            pass

        def get_hooks(self, point):
            return [MagicMock()]

    hooks_mod.HookContext = HookContext
    hooks_mod.HookPoint = HookPoint
    hooks_mod.HookRegistry = HookRegistry
    sdk_pkg.hooks = hooks_mod

    commands_mod = types.ModuleType("packages.mekong_plugin_sdk.commands")

    class CommandContext:
        def __init__(
            self,
            plugin_id=None,
            command_name=None,
            arguments=None,
            options=None,
            stdin=None,
            metadata=None,
        ):
            self.plugin_id = plugin_id
            self.command_name = command_name
            self.arguments = arguments or {}
            self.options = options or {}
            self.stdin = stdin
            self.metadata = metadata

    class CommandResult:
        def __init__(self, exit_code=0, output="", error_message=None):
            self.exit_code = exit_code
            self.output = output
            self.error_message = error_message

        def is_success(self):
            return self.exit_code == 0

    commands_mod.CommandContext = CommandContext
    commands_mod.CommandResult = CommandResult
    sys.modules["packages.mekong_plugin_sdk.commands"] = commands_mod
    sdk_pkg.commands = commands_mod

    types_mod = types.ModuleType("packages.mekong_plugin_sdk.types")
    types_mod.CommandHandler = callable
    sdk_pkg.types = types_mod
    sys.modules["packages.mekong_plugin_sdk.types"] = types_mod
    if "packages" not in sys.modules:
        try:
            import importlib
            importlib.import_module("packages")
        except Exception:
            sys.modules["packages"] = types.ModuleType("packages")
    if "packages" in sys.modules:
        setattr(sys.modules["packages"], "mekong_plugin_sdk", sdk_pkg)
    sys.modules["packages.mekong_plugin_sdk"] = sdk_pkg
    sys.modules["packages.mekong_plugin_sdk.plugin"] = plugin_mod
    sys.modules["packages.mekong_plugin_sdk.context"] = ctx_mod
    sys.modules["packages.mekong_plugin_sdk.hooks"] = hooks_mod


def _uninstall_mock_sdk():
    for key in list(sys.modules):
        if key.startswith("packages.mekong_plugin_sdk") or key == "mekong_plugin_sdk.commands":
            del sys.modules[key]
    if "packages" in sys.modules and hasattr(sys.modules["packages"], "mekong_plugin_sdk"):
        try:
            delattr(sys.modules["packages"], "mekong_plugin_sdk")
        except AttributeError:
            pass


def _make_mock_plugin(commands: list):
    plugin = MagicMock()
    plugin.get_commands.return_value = commands
    plugin.register_hooks = MagicMock()
    plugin.initialize = MagicMock()
    plugin.start = MagicMock()
    plugin.stop = MagicMock()
    plugin.dispose = MagicMock()
    return plugin


def _make_runtime_with_mock(plugin_dirs, commands=None, manifest_overrides=None):
    runtime = PluginRuntime(plugin_dirs=plugin_dirs)
    if commands is None:
        commands = [
            MagicMock(
                name="greet",
                description="Say hello",
                mcu_cost=1,
                permission=None,
                arguments=[],
                options=[],
                handler=MagicMock(return_value=MagicMock(exit_code=0, output="hi", is_success=lambda: True)),
            )
        ]
    if manifest_overrides is None:
        manifest_overrides = {"id": "com.test.plugin", "name": "Test Plugin"}
    mock_plugin = _make_mock_plugin(commands)

    plugin_id = manifest_overrides["id"]
    slug = _plugin_slug(plugin_id)
    pdir = plugin_dirs[0] / slug
    pdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "id": plugin_id,
        "name": manifest_overrides["name"],
        "version": "0.1.0",
        "description": "test",
        "license": "MIT",
        "engines": {"mekong": "^6.0.0"},
        "permissions": [],
        "mcu_cost": 1,
        "dependencies": [],
        "hooks": [],
        "entry_point": None,
        "isolation": "none",
    }
    (pdir / ".plugin.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pdir / "src").mkdir(exist_ok=True)
    (pdir / "src" / "__init__.py").write_text("", encoding="utf-8")

    sdk_plugin_mod = sys.modules.get("packages.mekong_plugin_sdk.plugin")
    old_create = None
    if sdk_plugin_mod is not None:
        old_create = sdk_plugin_mod.create_plugin
        sdk_plugin_mod.create_plugin = MagicMock(return_value=mock_plugin)
    try:
        runtime.load_plugin(pdir / ".plugin.json")
    finally:
        if sdk_plugin_mod is not None and old_create is not None:
            sdk_plugin_mod.create_plugin = old_create
    return runtime, mock_plugin


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPluginBindingSetup:
    def test_plugin_binding_module_exists(self):
        assert hasattr(PluginBinding, "wire_commands")

    def test_plugin_slug(self):
        assert _plugin_slug("com.example.my_plugin") == "com-example-my-plugin"

    def test_type_checking_block(self):
        import importlib
        import typing
        import src.core.plugin_binding as mod

        orig = typing.TYPE_CHECKING
        try:
            typing.TYPE_CHECKING = True
            importlib.reload(mod)
        finally:
            typing.TYPE_CHECKING = orig
            importlib.reload(mod)


class TestWireCommandsIntoApp:
    def test_loaded_plugin_commands_appear_in_typer(self):
        _install_mock_sdk()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                runtime, _ = _make_runtime_with_mock(
                    plugin_dirs=[Path(tmp) / "plugins"],
                )
                assert len(runtime.loaded_plugins) > 0

                root = typer.Typer()
                binding = PluginBinding(runtime)
                binding.wire_commands(root)

                group_names = [g.name for g in root.registered_groups]
                assert "com-test-plugin" in group_names
        finally:
            _uninstall_mock_sdk()

    def test_wire_no_runtime(self):
        binding = PluginBinding(runtime=None)
        root = typer.Typer()
        binding.wire_commands(root)
        assert len(binding._wired) == 0

    def test_wire_no_plugins_does_not_crash(self):
        runtime = PluginRuntime(plugin_dirs=[])
        binding = PluginBinding(runtime)
        root = typer.Typer()
        binding.wire_commands(root)
        assert len(binding._wired) == 0

    def test_wire_commands_already_wired_skips(self):
        _install_mock_sdk()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                runtime, _ = _make_runtime_with_mock(
                    plugin_dirs=[Path(tmp) / "plugins"],
                )
                root = typer.Typer()
                binding = PluginBinding(runtime)
                binding.wire_commands(root)
                assert len(binding._wired) == 1
                # Call wire_commands again to hit the already wired branch
                binding.wire_commands(root)
                assert len(binding._wired) == 1
        finally:
            _uninstall_mock_sdk()

    def test_wire_commands_plugin_name_fallback_to_id(self):
        runtime = MagicMock()
        loaded_plugin = MagicMock()
        loaded_plugin.plugin_id = "com.anonymous.plugin"
        loaded_plugin.manifest.name = ""
        loaded_plugin.commands = []
        runtime.iter_loaded.return_value = [loaded_plugin]

        root = typer.Typer()
        binding = PluginBinding(runtime)
        binding.wire_commands(root)
        assert "com.anonymous.plugin" in binding._wired

    def test_unwire_commands(self):
        runtime = PluginRuntime(plugin_dirs=[])
        binding = PluginBinding(runtime)
        binding._wired.add("some.plugin")
        root = typer.Typer()
        binding.unwire_commands(root)
        assert len(binding._wired) == 0


class TestRegisterCommandAndHandler:
    def test_register_command_no_description_fallback(self):
        runtime = MagicMock()
        binding = PluginBinding(runtime)
        app = typer.Typer()
        cmd = MagicMock()
        cmd.name = "bare-cmd"
        cmd.description = None
        cmd.mcu_cost = 2

        binding._register_command(app, "com.test.bare", cmd)
        cb = app.registered_commands[0].callback
        assert cb.__name__ == "_plugin_com.test.bare_bare-cmd"
        assert cb.__doc__ == "Plugin command: bare-cmd"

    def test_handler_invocation_returns_none(self):
        runtime = MagicMock()
        binding = PluginBinding(runtime)
        binding._invoke = MagicMock(return_value=None)
        app = typer.Typer()
        cmd = MagicMock(name="none-cmd", description="Desc")
        binding._register_command(app, "com.test", cmd)
        cb = app.registered_commands[0].callback

        ctx = MagicMock()
        # Returns None without raising
        cb(ctx)
        binding._invoke.assert_called_once_with("com.test", cmd, ctx)

    def test_handler_invocation_failure_with_error_message(self):
        runtime = MagicMock()
        binding = PluginBinding(runtime)
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.error_message = "Exploded"
        binding._invoke = MagicMock(return_value=mock_result)

        app = typer.Typer()
        cmd = MagicMock(name="fail-cmd", description="Desc")
        binding._register_command(app, "com.test", cmd)
        cb = app.registered_commands[0].callback

        ctx = MagicMock()
        with pytest.raises(typer.Exit) as exc_info:
            cb(ctx)
        assert exc_info.value.exit_code == 1

    def test_handler_invocation_failure_without_error_message(self):
        runtime = MagicMock()
        binding = PluginBinding(runtime)
        mock_result = MagicMock()
        mock_result.is_success.return_value = False
        mock_result.error_message = None
        binding._invoke = MagicMock(return_value=mock_result)

        app = typer.Typer()
        cmd = MagicMock(name="fail-silent-cmd", description="Desc")
        binding._register_command(app, "com.test", cmd)
        cb = app.registered_commands[0].callback

        ctx = MagicMock()
        with pytest.raises(typer.Exit) as exc_info:
            cb(ctx)
        assert exc_info.value.exit_code == 1

    def test_handler_invocation_success_with_output(self):
        runtime = MagicMock()
        binding = PluginBinding(runtime)
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.output = "All good"
        binding._invoke = MagicMock(return_value=mock_result)

        app = typer.Typer()
        cmd = MagicMock(name="success-cmd", description="Desc")
        binding._register_command(app, "com.test", cmd)
        cb = app.registered_commands[0].callback

        ctx = MagicMock()
        cb(ctx)
        binding._invoke.assert_called_once()

    def test_handler_invocation_success_empty_output(self):
        runtime = MagicMock()
        binding = PluginBinding(runtime)
        mock_result = MagicMock()
        mock_result.is_success.return_value = True
        mock_result.output = ""
        binding._invoke = MagicMock(return_value=mock_result)

        app = typer.Typer()
        cmd = MagicMock(name="empty-cmd", description="Desc")
        binding._register_command(app, "com.test", cmd)
        cb = app.registered_commands[0].callback

        ctx = MagicMock()
        cb(ctx)
        binding._invoke.assert_called_once()


class TestPluginCommandInvoke:
    def test_invoke_plugin_not_loaded_none(self):
        _install_mock_sdk()
        try:
            runtime = MagicMock()
            runtime.get_loaded.return_value = None
            binding = PluginBinding(runtime)
            cmd = MagicMock(name="any-cmd")
            ctx = MagicMock()

            with pytest.raises(typer.Exit) as exc_info:
                binding._invoke("not.loaded", cmd, ctx)
            assert exc_info.value.exit_code == 1
        finally:
            _uninstall_mock_sdk()

    def test_invoke_plugin_instance_is_none(self):
        _install_mock_sdk()
        try:
            runtime = MagicMock()
            loaded_plugin = MagicMock(instance=None)
            runtime.get_loaded.return_value = loaded_plugin
            binding = PluginBinding(runtime)
            cmd = MagicMock(name="any-cmd")
            ctx = MagicMock()

            with pytest.raises(typer.Exit) as exc_info:
                binding._invoke("broken.plugin", cmd, ctx)
            assert exc_info.value.exit_code == 1
        finally:
            _uninstall_mock_sdk()

    def test_invoke_arguments_and_options_mapping(self):
        _install_mock_sdk()
        try:
            from packages.mekong_plugin_sdk.commands import CommandResult

            runtime = MagicMock()
            loaded_plugin = MagicMock(instance=MagicMock())
            runtime.get_loaded.return_value = loaded_plugin

            captured_ctx = []

            def handler(ctx):
                captured_ctx.append(ctx)
                return CommandResult(exit_code=0)

            arg1 = MagicMock()
            arg1.name = "first"
            cmd = MagicMock(
                name="complex-cmd",
                arguments=[arg1],
                handler=handler,
            )
            binding = PluginBinding(runtime)
            ctx = MagicMock()

            res = binding._invoke("com.test.plugin", cmd, ctx, "arg_val_1", "extra_val_2", option_flag="active")
            assert res.is_success()
            assert len(captured_ctx) == 1
            assert captured_ctx[0].arguments["first"] == "arg_val_1"
            assert captured_ctx[0].arguments["_arg_1"] == "extra_val_2"
            assert captured_ctx[0].options["option_flag"] == "active"
        finally:
            _uninstall_mock_sdk()

    def test_invoke_cmd_without_arguments_attribute(self):
        _install_mock_sdk()
        try:
            from packages.mekong_plugin_sdk.commands import CommandResult

            runtime = MagicMock()
            loaded_plugin = MagicMock(instance=MagicMock())
            runtime.get_loaded.return_value = loaded_plugin

            captured_ctx = []

            def handler(ctx):
                captured_ctx.append(ctx)
                return CommandResult(exit_code=0)

            # cmd object without arguments attribute
            cmd = types.SimpleNamespace(name="no-args-cmd", handler=handler)
            binding = PluginBinding(runtime)
            ctx = MagicMock()

            res = binding._invoke("com.test.plugin", cmd, ctx, "val1")
            assert res.is_success()
            assert len(captured_ctx) == 1
            assert captured_ctx[0].arguments["_arg_0"] == "val1"
        finally:
            _uninstall_mock_sdk()

    def test_invoke_handler_raises_system_exit(self):
        _install_mock_sdk()
        try:
            runtime = MagicMock()
            loaded_plugin = MagicMock(instance=MagicMock())
            runtime.get_loaded.return_value = loaded_plugin

            def handler(ctx):
                raise SystemExit(3)

            cmd = MagicMock(name="exit-cmd", arguments=[], handler=handler)
            binding = PluginBinding(runtime)
            ctx = MagicMock()

            with pytest.raises(SystemExit) as exc_info:
                binding._invoke("com.test.plugin", cmd, ctx)
            assert exc_info.value.code == 3
        finally:
            _uninstall_mock_sdk()

    def test_invoke_handler_raises_exception(self):
        _install_mock_sdk()
        try:
            runtime = MagicMock()
            loaded_plugin = MagicMock(instance=MagicMock())
            runtime.get_loaded.return_value = loaded_plugin

            def handler(ctx):
                raise ValueError("unexpected crash inside handler")

            cmd = MagicMock(name="crash-cmd", arguments=[], handler=handler)
            binding = PluginBinding(runtime)
            ctx = MagicMock()

            result = binding._invoke("com.test.plugin", cmd, ctx)
            assert result.exit_code == 1
            assert "unexpected crash inside handler" in result.error_message
        finally:
            _uninstall_mock_sdk()
