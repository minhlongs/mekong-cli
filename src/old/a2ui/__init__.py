"""A2UI Terminal Renderer — First CLI renderer for Google A2UI protocol.

Maps Google's A2UI declarative JSON protocol to Rich terminal widgets,
enabling agent-generated UIs to render natively in the terminal.

Usage:
    from src.a2ui import A2UIRenderer
    renderer = A2UIRenderer()
    renderer.process_message({"surfaceUpdate": {"surfaceId": "main", "components": [...]}})
    renderer.process_message({"beginRendering": {"surfaceId": "main"}})
"""

from .renderer import A2UIRenderer
from .components import COMPONENT_REGISTRY

__all__ = ["A2UIRenderer", "COMPONENT_REGISTRY"]
