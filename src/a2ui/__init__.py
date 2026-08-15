"""A2UI terminal renderer."""

from __future__ import annotations

from typing import Any

from rich.console import Console

from src.a2ui.components import COMPONENT_REGISTRY, render_component


class A2UIRenderer:
    """Render A2UI protocol surfaces to a Rich console."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.surfaces: dict[str, list[dict[str, Any]]] = {}
        self.data: dict[str, Any] = {}

    @property
    def surface_ids(self) -> list[str]:
        return list(self.surfaces.keys())

    def load_surface(self, surface_id: str, components: list[dict[str, Any]]) -> None:
        self.surfaces[surface_id] = components

    def update_data(self, key: str, value: Any) -> None:
        self.data[key] = value

    def process_message(self, message: dict[str, Any]) -> None:
        if "surfaceUpdate" in message:
            payload = message["surfaceUpdate"]
            self.load_surface(payload["surfaceId"], payload.get("components", []))
            return
        if "dataModelUpdate" in message:
            self.data.update(message["dataModelUpdate"])
            return
        if "deleteSurface" in message:
            self.surfaces.pop(message["deleteSurface"].get("surfaceId", ""), None)
            return
        if "beginRendering" in message:
            self.render_surface(message["beginRendering"].get("surfaceId", ""))
            return
        self.console.print("[yellow]Unknown A2UI message[/yellow]")

    def render_surface(self, surface_id: str) -> None:
        components = self.surfaces.get(surface_id)
        if components is None:
            self.console.print(f"Surface not found: {surface_id}")
            return
        for component in components:
            self.console.print(render_component(component, self.data))


__all__ = ["A2UIRenderer", "COMPONENT_REGISTRY"]
