# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Plugin management commands — `mekong plugin {init|install|list|uninstall}`."""

from __future__ import annotations

import shutil
import subprocess

import typer
from rich.console import Console

from src.cli.commands._plugin_install_cmds import (
    plugin_init,
    plugin_install,
    plugin_list,
    plugin_uninstall,
)
from src.cli.commands._plugin_install_scaffold import (
    _DEFAULT_MANIFEST_TEMPLATE,
    _INIT_PY_TEMPLATE,
    _ISOLATION_MAP,
    _README_TEMPLATE,
    _default_isolation,
    _human_name_from_id,
    _plugin_id_from_name,
    _render_manfiest_info,
    _scaffold,
)
from src.cli.commands._plugin_install_source import (
    _clone_git,
    _detect_source,
    _fetch_zip,
    _get_plugins_dir,
    _get_runtime,
    _install_source,
)
from src.core.plugin_runtime import PluginRuntime
from src.core.plugin_schema import PluginManifestSchema

app = typer.Typer(
    name="plugin",
    help="Plugin management — init | install | list | uninstall | publish",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()

app.command("init")(plugin_init)
app.command("install")(plugin_install)
app.command("list")(plugin_list)
app.command("uninstall")(plugin_uninstall)


def register_plugin_commands(root: typer.Typer) -> None:
    """Add the ``plugin`` sub-app to the root Typer app."""
    if getattr(root, "_mekong_plugin_wired", False):
        return
    root._mekong_plugin_wired = True  # type: ignore[attr-defined]
    root.add_typer(
        app,
        name="plugin",
        help="Plugin management — init | install | list | uninstall | publish",
    )


__all__ = [
    "PluginManifestSchema",
    "PluginRuntime",
    "_DEFAULT_MANIFEST_TEMPLATE",
    "_INIT_PY_TEMPLATE",
    "_ISOLATION_MAP",
    "_README_TEMPLATE",
    "_clone_git",
    "_default_isolation",
    "_detect_source",
    "_fetch_zip",
    "_get_plugins_dir",
    "_get_runtime",
    "_human_name_from_id",
    "_install_source",
    "_plugin_id_from_name",
    "_render_manfiest_info",
    "_scaffold",
    "app",
    "console",
    "plugin_init",
    "plugin_install",
    "plugin_list",
    "plugin_uninstall",
    "register_plugin_commands",
    "shutil",
    "subprocess",
]
