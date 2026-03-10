"""
Vibe Coding Factory — Entry Point Router.

Loads the layer pyramid from layers.yaml and provides role-based
command menus for the `mekong start` command.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

_FACTORY_DIR = Path(__file__).parent


def _load_layers(layers_path: Path) -> dict:
    """Load and return the full layers configuration."""
    try:
        with layers_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            return data.get("layers", {})
    except FileNotFoundError:
        logger.error("layers.yaml not found at %s", layers_path)
        return {}
    except yaml.YAMLError as exc:
        logger.error("Failed to parse layers.yaml: %s", exc)
        return {}


class EntryPointRouter:
    """
    Routes users to the correct factory layer based on their role.

    Provides menus and command lists loaded from layers.yaml so the
    `mekong start` command can present role-specific options.
    """

    def __init__(self, layers_path: Path | None = None) -> None:
        path = layers_path or (_FACTORY_DIR / "layers.yaml")
        self._layers = _load_layers(path)

    def get_role_menu(self) -> dict:
        """
        Return a display menu mapping role names to layer metadata.

        Returns:
            Dict keyed by layer name with role, description, entry_prompt.
        """
        menu: dict = {}
        for layer_name, cfg in self._layers.items():
            menu[layer_name] = {
                "role": cfg.get("role", layer_name.title()),
                "description": cfg.get("description", ""),
                "entry_prompt": cfg.get("entry_prompt", ""),
                "chapter": cfg.get("chapter", ""),
            }
        return menu

    def get_commands_for_role(self, role: str) -> list[str]:
        """
        Return the command list for a given layer/role name.

        Args:
            role: Layer name (founder, business, product, engineering, ops).

        Returns:
            List of command strings, empty list if role not found.
        """
        role_lower = role.lower().strip()
        layer_cfg = self._layers.get(role_lower)
        if layer_cfg is None:
            logger.warning("Role not found in layers.yaml: %s", role)
            return []
        return list(layer_cfg.get("commands", []))

    def get_entry_prompt(self, role: str) -> str:
        """Return the entry prompt string for a given role."""
        layer_cfg = self._layers.get(role.lower().strip(), {})
        return layer_cfg.get("entry_prompt", f"Chào mừng đến layer {role}.")

    def list_roles(self) -> list[str]:
        """Return ordered list of all layer/role names."""
        return list(self._layers.keys())
