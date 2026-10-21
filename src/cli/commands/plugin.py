# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin management Typer sub-app — E1c–E1f of Track E.

Registers the ``mekong plugin`` command group with sub-commands:
init, list, remove, install, update, search, publish.
"""

from __future__ import annotations

from typing import Optional

import typer

from src.cli.commands._plugin_lifecycle import (
    _register_install,
    _register_list,
    _register_remove,
    _register_update,
)
from src.cli.commands._plugin_marketplace import (
    DEFAULT_PUBLISH_DIR,
    _register_publish,
    _register_search,
    _search_local,
    _search_remote,
)
from src.cli.commands._plugin_scaffold import (
    _INIT_PY_TEMPLATE,
    _PLUGIN_JSON_TEMPLATE,
    _PLUGIN_TYPES,
    _README_TEMPLATE,
    INIT_TEST_TEMPLATE,
    _register_init,
    _scaffold_plugin,
    _title_to_kebab,
)
from src.core.plugin_publisher import PluginPublisher, PublishError
from src.core.plugin_runtime import PluginRuntime

_runtime: Optional[PluginRuntime] = None


def set_runtime(rt: PluginRuntime) -> None:
    """Allow app_setup.py to share its loaded PluginRuntime."""
    global _runtime
    _runtime = rt


def _get_runtime() -> PluginRuntime:
    """Return the shared runtime, or create a default one."""
    if _runtime is None:
        return PluginRuntime()
    return _runtime


def register(cli: typer.Typer) -> None:
    """Register ``mekong plugin`` sub-app."""
    app = typer.Typer(
        name="plugin",
        help="Plugin ecosystem: init / install / list / remove / update / search",
        no_args_is_help=True,
        add_completion=False,
        rich_markup_mode="rich",
    )

    _register_init(app)
    _register_list(app)
    _register_remove(app)
    _register_install(app)
    _register_update(app)
    _register_search(app)
    _register_publish(app)

    cli.add_typer(app, name="plugin", help="Plugin ecosystem management")


__all__ = [
    "DEFAULT_PUBLISH_DIR",
    "INIT_TEST_TEMPLATE",
    "PluginPublisher",
    "PluginRuntime",
    "PublishError",
    "_INIT_PY_TEMPLATE",
    "_PLUGIN_JSON_TEMPLATE",
    "_PLUGIN_TYPES",
    "_README_TEMPLATE",
    "_get_runtime",
    "_register_init",
    "_register_install",
    "_register_list",
    "_register_publish",
    "_register_remove",
    "_register_search",
    "_register_update",
    "_scaffold_plugin",
    "_search_local",
    "_search_remote",
    "_title_to_kebab",
    "register",
    "set_runtime",
]
