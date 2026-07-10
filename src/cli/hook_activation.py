"""Hook system activation — wraps Typer command dispatch with BEFORE_COMMAND / AFTER_COMMAND hooks.

Installs a Typer rich callback on the root app that fires plugin hooks
around every command invocation. Hook failures are silently swallowed
(HookpointRouter.fire_safe) so a broken plugin never crashes user commands.

Usage::

    from src.cli.hook_activation import HookCommandWrapper
    wrapper = HookCommandWrapper(_hookpoint_router)
    wrapper.install(root_app)  # call once after build_app()
"""
from __future__ import annotations

import logging

import typer

from packages.mekong_plugin_sdk.hooks import HookContext, HookPoint

logger = logging.getLogger(__name__)


class HookCommandWrapper:
    """Wraps a Typer app so every command pass through plugin hooks.

    Parameters
    ----------
    router : HookpointRouter — shared router (already populated from runtime).
    """

    def __init__(self, router: object) -> None:
        self._router = router

    # ------------------------------------------------------------------
    # public
    # ------------------------------------------------------------------

    def install(self, app: typer.Typer) -> None:
        """Install the hook callback on *app*.

        Safe to call multiple times (no-op after first install).
        """
        if getattr(app, "_hook_wrapper_installed", False):
            return

        @app.callback(invoke_without_command=True)
        def _hook_wrap(ctx: typer.Context) -> None:
            """Fire BEFORE_COMMAND / AFTER_COMMAND around every invocation."""
            if ctx.invoked_subcommand is None:
                # Typer shows help when no subcommand given — still fire events
                pass

            invoked = ctx.invoked_subcommand or "<help>"
            command_name = invoked.lstrip("-")

            router = self._router
            has_before = (
                router is not None
                and getattr(router, "has_hooks", lambda p: False)(
                    HookPoint.BEFORE_COMMAND
                )
            )
            if not has_before:
                # Fast path: no before hooks — skip context build
                pass
            else:
                context = HookContext(
                    plugin_id="*",
                    command_name=command_name,
                    data={
                        "command": command_name,
                        "args": ctx.args,
                        "kwargs": {},
                    },
                )
                router.fire_safe(HookPoint.BEFORE_COMMAND, context)
                router.fire_safe(HookPoint.AFTER_COMMAND, context)

        app._hook_wrapper_installed = True  # type: ignore[attr-defined]
        logger.info("Hook command wrapper installed on Typer app")
