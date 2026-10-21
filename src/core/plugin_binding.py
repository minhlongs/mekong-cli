# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin command binding — wires SDK commands into Typer CLI."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Set

import typer

if TYPE_CHECKING:
    from src.core.plugin_runtime import PluginRuntime

logger = logging.getLogger(__name__)


class PluginBinding:
    """Bridges PluginRuntime commands into a Typer root app."""

    def __init__(self, runtime: "PluginRuntime") -> None:
        self.runtime = runtime
        self._wired: Set[str] = set()

    def wire_commands(self, root: typer.Typer) -> None:
        """Register all loaded plugin commands as sub-apps under *root*."""
        if not self.runtime:
            return
        loaded: list[Any] = list(self.runtime.iter_loaded())
        if not loaded:
            logger.info("No plugins loaded — skipping wire_commands")
            return

        for loaded_plugin in loaded:
            pid = loaded_plugin.plugin_id
            if pid in self._wired:
                logger.debug("Plugin %s already wired — skipping", pid)
                continue

            sub_app = self._build_sub_app(
                plugin_id=pid,
                plugin_name=loaded_plugin.manifest.name or pid,
                commands=loaded_plugin.commands,
            )
            root.add_typer(sub_app, name=_plugin_slug(pid))
            self._wired.add(pid)
            logger.info("Wired %d commands for plugin '%s'", len(loaded_plugin.commands), pid)

    def unwire_commands(self, root: typer.Typer) -> None:
        """Remove previously wired plugin sub-apps from *root*."""
        self._wired.clear()

    def _build_sub_app(self, plugin_id: str, plugin_name: str, commands: list[Any]) -> typer.Typer:
        sub = typer.Typer(
            name=_plugin_slug(plugin_id),
            help=f"{plugin_name} ({plugin_id}) — plugin commands",
            no_args_is_help=True,
        )
        for cmd in commands:
            self._register_command(sub, plugin_id, cmd)
        return sub

    def _register_command(self, app: typer.Typer, plugin_id: str, cmd: Any) -> None:
        cmd_name: str = cmd.name
        cmd_desc: str = cmd.description or ""
        _: int = getattr(cmd, "mcu_cost", 1)

        @app.command(cmd_name, help=cmd_desc, context_settings={"obj": {}})
        def _handler(ctx: typer.Context, *args: Any, **kwargs: Any) -> None:
            result = self._invoke(plugin_id, cmd, ctx, *args, **kwargs)
            if result is None:
                return
            if not result.is_success():
                err = result.error_message or "Command failed"
                logger.error("[%s/%s] %s", plugin_id, cmd_name, err)
                raise typer.Exit(code=1)
            if result.output:
                logger.info("[%s/%s] %s", plugin_id, cmd_name, result.output)

        _handler.__name__ = f"_plugin_{plugin_id}_{cmd_name}"
        _handler.__doc__ = cmd_desc or f"Plugin command: {cmd_name}"

    def _invoke(self, plugin_id: str, cmd: Any, ctx: typer.Context, *args: Any, **kwargs: Any) -> Any:
        from packages.mekong_plugin_sdk.commands import CommandContext, CommandResult

        loaded = self.runtime.get_loaded(plugin_id)
        if loaded is None or loaded.instance is None:
            logger.error("Plugin '%s' is not loaded. Run `mekong plugin install <source>` first.", plugin_id)
            raise typer.Exit(code=1)

        sdk_arg_names = [a.name for a in getattr(cmd, "arguments", [])]
        arguments: dict[str, Any] = {
            (sdk_arg_names[i] if i < len(sdk_arg_names) else f"_arg_{i}"): value
            for i, value in enumerate(args)
        }
        sdk_ctx = CommandContext(
            plugin_id=plugin_id, command_name=cmd.name, arguments=arguments,
            options=dict(kwargs), stdin=None, metadata=None,
        )

        try:
            return cmd.handler(sdk_ctx)
        except SystemExit:
            raise
        except Exception as exc:
            logger.exception("Plugin command '%s/%s' crashed", plugin_id, cmd.name)
            return CommandResult(exit_code=1, output="", error_message=f"Unhandled error: {exc}")


def _plugin_slug(plugin_id: str) -> str:
    return plugin_id.lower().replace(".", "-").replace("_", "-")
