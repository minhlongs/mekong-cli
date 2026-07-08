"""Plugin command binding — wires SDK commands into Typer CLI.

After PluginRuntime loads plugins (their commands are stored as
``LoadedPlugin.commands``), this module produces Typer sub-apps so::

    mekong <plugin-id> <command> [args...]

runs the handler declared in ``.plugin.json`` via the SDK ``Command`` model.

Lifecycle
---------
create PluginBinding(runtime) → wire_commands(root_typer) → done

Re-wiring is idempotent (skips plugins already wired on the same root).
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Set

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
        slugified plugin id.  Individual SDK ``Command`` objects become
        Typer commands inside that sub-app.

        Re-wiring the same plugin id is a no-op.
        """
        if not self.runtime:
            return

        loaded: List[Any] = list(self.runtime.iter_loaded())
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
            logger.info("Wired %d commands for plugin '%s'",
                        len(loaded_plugin.commands), pid)

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
        commands: List[Any],
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
        mcu_cost: int = getattr(cmd, "mcu_cost", 1)

        @app.command(cmd_name, help=cmd_desc, context_settings={"obj": {}})
        def _handler(ctx: typer.Context, *args: Any, **kwargs: Any) -> None:
            """Invoke the SDK command handler and surface result."""

            result = self._invoke(plugin_id, cmd, ctx)
            if result is None:
                return

            if not result.is_success():
                err = result.error_message or "Command failed"
                typer.echo(err, err=True)
                raise typer.Exit(code=1)

            if result.output:
                typer.echo(result.output)

        # preserve a useful name for introspection / testing
        _handler.__name__ = f"_plugin_{plugin_id}_{cmd_name}"
        _handler.__doc__ = cmd_desc or f"Plugin command: {cmd_name}"

    def _invoke(
        self,
        plugin_id: str,
        cmd: Any,
        ctx: typer.Context,
    ) -> Any:
        """Call the SDK handler, catching unexpected errors."""
        from mekong_plugin_sdk.commands import (  # type: ignore
            CommandContext,
            CommandResult,
        )

        loaded = self.runtime.get_loaded(plugin_id)
        if loaded is None or loaded.instance is None:
            typer.echo(
                f"Error: plugin '{plugin_id}' is not loaded. "
                f"Run `mekong plugin install <source>` first.",
                err=True,
            )
            raise typer.Exit(code=1)

        # build a minimal CommandContext
        sdk_ctx = CommandContext(
            plugin_id=plugin_id,
            command_name=cmd.name,
            arguments={},
            options={},
            stdin=None,
            metadata=None,
        )

        try:
            return cmd.handler(sdk_ctx)
        except SystemExit:
            raise
        except Exception as exc:
            logger.exception("Plugin command '%s/%s' crashed",
                             plugin_id, cmd.name)
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

