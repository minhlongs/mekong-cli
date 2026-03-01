"""A2UI Terminal Renderer — Core rendering engine.

Processes A2UI protocol messages and renders surfaces to Rich terminal output.
Supported message types:
- surfaceUpdate   → Store component tree for a surfaceId
- dataModelUpdate → Update data bindings (supports deep merge)
- beginRendering  → Render a surface to the console
- deleteSurface   → Remove a surface from the registry
"""

import logging
from typing import Any, Dict, Optional

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text

from .components import _dispatch

logger = logging.getLogger(__name__)


class A2UIRenderer:
    """Renders A2UI JSON surfaces to Rich terminal output.

    A2UI is Google's declarative JSON protocol for agent-generated UIs.
    This renderer maps the protocol to Rich widgets for terminal display.

    Usage:
        renderer = A2UIRenderer()
        renderer.process_message({"surfaceUpdate": {
            "surfaceId": "main",
            "components": [{"type": "Text", "text": "Hello A2UI"}]
        }})
        renderer.process_message({"beginRendering": {"surfaceId": "main"}})
    """

    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize the renderer.

        Args:
            console: Optional Rich Console instance. Creates a new one if not provided.
        """
        self.console: Console = console or Console()
        # surfaceId → list of component dicts
        self.surfaces: Dict[str, list[Dict[str, Any]]] = {}
        # data bindings used for $data.key resolution
        self.data: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Message processing
    # ------------------------------------------------------------------

    def process_message(self, message: Dict[str, Any]) -> None:
        """Process a single A2UI protocol message.

        Supported top-level keys:
            surfaceUpdate, dataModelUpdate, beginRendering, deleteSurface

        Args:
            message: A2UI message dict.
        """
        if "surfaceUpdate" in message:
            self._handle_surface_update(message["surfaceUpdate"])
        elif "dataModelUpdate" in message:
            self._handle_data_model_update(message["dataModelUpdate"])
        elif "beginRendering" in message:
            self._handle_begin_rendering(message["beginRendering"])
        elif "deleteSurface" in message:
            self._handle_delete_surface(message["deleteSurface"])
        else:
            logger.warning("[A2UI] Unknown message type: %s", list(message.keys()))

    def _handle_surface_update(self, payload: Dict[str, Any]) -> None:
        """Store or replace component tree for a surface.

        Args:
            payload: Dict with 'surfaceId' (str) and 'components' (list).
        """
        surface_id: str = payload.get("surfaceId", "")
        if not surface_id:
            logger.warning("[A2UI] surfaceUpdate missing surfaceId")
            return
        components: list[Dict[str, Any]] = payload.get("components", [])
        self.surfaces[surface_id] = components
        logger.debug("[A2UI] surfaceUpdate: %s (%d components)", surface_id, len(components))

    def _handle_data_model_update(self, payload: Dict[str, Any]) -> None:
        """Merge incoming data into the shared data context.

        Args:
            payload: Dict of key-value pairs to merge into self.data.
        """
        self.data.update(payload)
        logger.debug("[A2UI] dataModelUpdate: %d keys", len(payload))

    def _handle_begin_rendering(self, payload: Dict[str, Any]) -> None:
        """Render a surface by its ID.

        Args:
            payload: Dict with 'surfaceId' (str).
        """
        surface_id: str = payload.get("surfaceId", "")
        if not surface_id:
            logger.warning("[A2UI] beginRendering missing surfaceId")
            return
        self.render_surface(surface_id)

    def _handle_delete_surface(self, payload: Dict[str, Any]) -> None:
        """Remove a surface from the registry.

        Args:
            payload: Dict with 'surfaceId' (str).
        """
        surface_id: str = payload.get("surfaceId", "")
        if surface_id in self.surfaces:
            del self.surfaces[surface_id]
            logger.debug("[A2UI] deleteSurface: %s", surface_id)
        else:
            logger.warning("[A2UI] deleteSurface: surface '%s' not found", surface_id)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render_surface(self, surface_id: str) -> None:
        """Render a named surface to the console.

        Args:
            surface_id: The surface identifier to render.
        """
        if surface_id not in self.surfaces:
            self.console.print(
                f"[bold red][A2UI] Surface '{surface_id}' not found[/bold red]"
            )
            return

        components = self.surfaces[surface_id]
        title = Text(f"Surface: {surface_id}", style="bold blue")
        self.console.print(Panel(title, border_style="blue", expand=False))

        for component in components:
            try:
                renderable = self.render_component(component)
                self.console.print(renderable)
            except Exception as exc:  # noqa: BLE001
                logger.error("[A2UI] Failed to render component %s: %s", component, exc)
                self.console.print(
                    Text(f"[render error: {exc}]", style="bold red")
                )

    def render_component(self, component: Dict[str, Any]) -> RenderableType:
        """Render a single A2UI component dict.

        Looks up the component type in COMPONENT_REGISTRY and calls the
        corresponding factory with the current data context.

        Args:
            component: A2UI component dict with at minimum a 'type' key.

        Returns:
            A Rich RenderableType ready for console.print().
        """
        return _dispatch(component, self.data)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def load_surface(self, surface_id: str, components: list[Dict[str, Any]]) -> None:
        """Directly load components into a surface without a protocol message.

        Args:
            surface_id: Unique identifier for the surface.
            components: List of A2UI component dicts.
        """
        self.surfaces[surface_id] = components

    def update_data(self, key: str, value: Any) -> None:
        """Update a single key in the shared data context.

        Args:
            key: Data key (supports dot-notation in $data references).
            value: Value to store.
        """
        self.data[key] = value

    @property
    def surface_ids(self) -> list[str]:
        """Return list of registered surface IDs."""
        return list(self.surfaces.keys())


__all__ = ["A2UIRenderer"]
