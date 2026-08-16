# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin command binding — wires SDK commands into Typer CLI.

After PluginRuntime loads plugins (their commands are stored as
``LoadedPlugin.commands``), this module produces Typer sub-apps so:

    mekong <plugin-id> <command> [args...]

runs the handler declared in ``.plugin.json`` via the SDK ``Command`` model.

Lifecycle
---------
    create PluginBinding(runtime) -> wire_commands(root_typer) -> done

Re-wiring is idempotent (skips plugins already wired on the same root).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Set

import typer

if TYPE_CHECKING:
    from src.core.plugin_runtime import PluginRuntime

logger = logging.getLogger(__name__)


class PluginBinding:
    """Bridges PluginRuntime commands into a Typer root app.

    Parameters
    ----------
    runtime: PluginRuntime — the already-initialised runtime (plugins loaded).
    """

    def __init__(self, runtime: "PluginRuntime") -> None:
        self.runtime = runtime
        self._wired: Set[str] = set()  # plugin_ids already wired to a root

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def wire_commands(self, root: typer.Typer) -> None:
        """Register all loaded plugin commands as sub-apps under *root*.

        Each plugin gets its own ``typer.Typer`` sub-app named after the
        slugified plugin id. Individual SDK ``Command`` objects become
        Typer commands inside that sub-app.

        Re-wiring the same plugin id is a no-op.
        """
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
            logger.info(
                "Wired %d commands for plugin '%s'",
                len(loaded_plugin.commands),
                pid,
            )

    def unwire_commands(self, root: typer.Typer) -> None:
        """Remove previously wired plugin sub-apps from *root*.

        Typer does not expose a built-in remove, so this is a best-effort
        clear — callers that need true removal should recreate the root app.
        """
        self._wired.clear()

    # ------------------------------------------------------------------
    # internal
    # ------------------------------------------------------------------

    def _build_sub_app(
        self,
        plugin_id: str,
        plugin_name: str,
        commands: list[Any],  # SDK Command objects — no typed stub available
    ) -> typer.Typer:
        """Return a Typer sub-app populated with *commands*."""
        sub = typer.Typer(
            name=_plugin_slug(plugin_id),
            help=f"{plugin_name} ({plugin_id}) — plugin commands",
            no_args_is_help=True,
        )
        for cmd in commands:
            self._register_command(sub, plugin_id, cmd)
        return sub

    def _register_command(
        self,
        app: typer.Typer,
        plugin_id: str,
        cmd: Any,
    ) -> None:
        """Register a single SDK *cmd* as a Typer command on *app*."""
        cmd_name: str = cmd.name
        cmd_desc: str = cmd.description or ""
        _: int = getattr(cmd, "mcu_cost", 1)

        @app.command(cmd_name, help=cmd_desc, context_settings={"obj": {}})
        def _handler(ctx: typer.Context, *args: Any, **kwargs: Any) -> None:
            """Invoke the SDK command handler and surface result."""
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

    def _invoke(
        self,
        plugin_id: str,
        cmd: Any,
        ctx: typer.Context,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Call the SDK handler, catching unexpected errors."""
        # type: ignore — SDK has no published .pyi stubs; silence guards
        # against silent signature drift in packages.mekong_plugin_sdk.commands
        from packages.mekong_plugin_sdk.commands import (
            CommandContext,
            CommandResult,
        )

        loaded = self.runtime.get_loaded(plugin_id)
        if loaded is None or loaded.instance is None:
            logger.error(
                "Plugin '%s' is not loaded. Run `mekong plugin install <source>` first.",
                plugin_id,
            )
            raise typer.Exit(code=1)

        # Map CLI positional args to SDK arguments by name (by position if
        # names are unknown), keyword flags become options.
        sdk_arg_names = [a.name for a in getattr(cmd, "arguments", [])]
        arguments: dict[str, Any] = {}
        for i, value in enumerate(args):
            if i < len(sdk_arg_names):
                arguments[sdk_arg_names[i]] = value
            else:
                arguments[f"_arg_{i}"] = value
        options: dict[str, Any] = dict(kwargs)

        sdk_ctx = CommandContext(
            plugin_id=plugin_id,
            command_name=cmd.name,
            arguments=arguments,
            options=options,
            stdin=None,
            metadata=None,
        )

        try:
            return cmd.handler(sdk_ctx)
        except SystemExit:
            raise
        except Exception as exc:
            logger.exception("Plugin command '%s/%s' crashed", plugin_id, cmd.name)
            return CommandResult(
                exit_code=1,
                output="",
                error_message=f"Unhandled error: {exc}",
            )


# ------------------------------------------------------------------
# private helpers
# ------------------------------------------------------------------

def _plugin_slug(plugin_id: str) -> str:
    """Collapse a plugin id to a CLI-safe slug (kebab-case)."""
    return plugin_id.lower().replace(".", "-").replace("_", "-")
