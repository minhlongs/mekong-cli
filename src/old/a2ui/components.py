"""A2UI Component Registry — Maps A2UI component types to Rich widget factories.

Each factory takes (component_data: dict, data_context: dict) and returns
a Rich RenderableType. Components follow Google's A2UI declarative schema.
"""

from typing import Any, Callable, Dict

from rich.columns import Columns
from rich.console import RenderableType
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from .component_helpers import _resolve_binding, _render_group, ICON_MAP

# Type alias
ComponentFactory = Callable[[Dict[str, Any], Dict[str, Any]], RenderableType]


# ---------------------------------------------------------------------------
# Forward declaration (allows _dispatch to be called from within factories)
# ---------------------------------------------------------------------------

def _dispatch(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    """Dispatch a component dict to its factory.

    Supports two formats:
    1. Flat: {"type": "Text", "text": "hello"}
    2. A2UI spec: {"id": "x", "component": {"Text": {"text": "hello"}}}
    """
    # Format 2: A2UI spec {"id": ..., "component": {"Text": {...}}}
    if "component" in component:
        comp_dict = component["component"]
        for ctype, props in comp_dict.items():
            factory = COMPONENT_REGISTRY.get(ctype, _render_unknown)
            merged = {"type": ctype}
            if isinstance(props, dict):
                merged.update(props)
            return factory(merged, data)
        return _render_unknown(component, data)
    # Format 1: flat {"type": "Text", ...}
    ctype = component.get("type", "")
    factory = COMPONENT_REGISTRY.get(ctype, _render_unknown)
    return factory(component, data)


# ---------------------------------------------------------------------------
# Component factories
# ---------------------------------------------------------------------------

def _render_text(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    text_val = component.get("text", "")
    # A2UI spec: {"text": {"literalString": "..."}} or {"text": {"dataRef": "$data.x"}}
    if isinstance(text_val, dict):
        text_val = text_val.get("literalString", text_val.get("dataRef", str(text_val)))
    raw = _resolve_binding(text_val, data)
    style_map = {
        "heading": "bold", "subheading": "bold dim",
        "caption": "dim italic", "body": "", "label": "dim",
    }
    variant = component.get("variant", "body")
    color = component.get("color", "")
    style = f"{style_map.get(variant, '')} {color}".strip()
    return Text(str(raw), style=style)


def _render_card(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    title = str(_resolve_binding(component.get("title", ""), data))
    subtitle = component.get("subtitle", "")
    border_style = component.get("borderColor", "blue")
    children = component.get("children", [])
    parts: list[RenderableType] = []
    if subtitle:
        parts.append(Text(str(_resolve_binding(subtitle, data)), style="dim"))
    parts.extend(_dispatch(c, data) for c in children)
    content: RenderableType = (
        parts[0] if len(parts) == 1 else (_render_group(parts) if parts else Text(""))
    )
    return Panel(
        content,
        title=f"[bold]{title}[/bold]" if title else None,
        border_style=border_style,
        expand=False,
    )


def _render_row(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    children = component.get("children", [])
    renderables = [_dispatch(c, data) for c in children]
    return Columns(renderables, equal=False, expand=False) if renderables else Text("")


def _render_column(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    parts = [_dispatch(c, data) for c in component.get("children", [])]
    return _render_group(parts) if parts else Text("")


def _render_list(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    items = _resolve_binding(component.get("items", []), data)
    if not isinstance(items, list):
        items = []
    label_key = component.get("labelKey", "label")
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("item")
    for item in items:
        cell = str(item.get(label_key, item)) if isinstance(item, dict) else str(item)
        table.add_row(f"• {cell}")
    return table


def _render_button(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    label = str(_resolve_binding(component.get("label", "Button"), data))
    style_map = {
        "primary": "bold cyan", "secondary": "bold white",
        "danger": "bold red", "ghost": "dim",
    }
    style = style_map.get(component.get("variant", "primary"), "bold cyan")
    return Text(f"▸ {label}", style=style)


def _render_textfield(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    placeholder = str(_resolve_binding(component.get("placeholder", "Enter text..."), data))
    label = component.get("label", "")
    value = _resolve_binding(component.get("value", ""), data)
    display = str(value) if value else f"[dim]{placeholder}[/dim]"
    prefix = f"[bold]{label}:[/bold] " if label else ""
    return Text.from_markup(f"{prefix}⎕ {display}")


def _render_checkbox(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    label = str(_resolve_binding(component.get("label", ""), data))
    checked = bool(_resolve_binding(component.get("checked", False), data))
    return Text(f"{'☑' if checked else '☐'} {label}", style="green" if checked else "white")


def _render_divider(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    title = str(_resolve_binding(component.get("title", ""), data))
    return Rule(title=title or None, style=component.get("style", "dim"))


def _render_image(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    alt = str(_resolve_binding(component.get("alt", "image"), data))
    src = str(_resolve_binding(component.get("src", ""), data))
    hint = f" ({src})" if src else ""
    return Text(f"[Image: {alt}{hint}]", style="dim italic")


def _render_icon(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    name = str(_resolve_binding(component.get("name", ""), data)).lower()
    emoji = ICON_MAP.get(name, f"[{name}]")
    label = component.get("label", "")
    return Text(f"{emoji} {label}" if label else emoji)


def _render_tabs(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    tabs = component.get("tabs", [])
    active_index = int(component.get("activeIndex", 0))
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    for i, tab in enumerate(tabs):
        tab_label = str(_resolve_binding(tab.get("label", f"Tab {i}"), data))
        style = "bold cyan underline" if i == active_index else "dim"
        table.add_column(tab_label, style=style)
    if tabs:
        table.add_row(*["" for _ in tabs])
    return table


def _render_modal(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    title = str(_resolve_binding(component.get("title", "Modal"), data))
    parts = [_dispatch(c, data) for c in component.get("children", [])]
    content: RenderableType = _render_group(parts) if parts else Text("")
    return Panel(
        content,
        title=f"[bold magenta]{title}[/bold magenta]",
        border_style="bright_magenta",
        expand=False,
        subtitle="[dim]ESC to close[/dim]",
    )


def _render_unknown(component: Dict[str, Any], data: Dict[str, Any]) -> RenderableType:
    return Text(f"[?{component.get('type', 'unknown')}]", style="dim red")


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

COMPONENT_REGISTRY: Dict[str, ComponentFactory] = {
    "Text": _render_text,
    "Card": _render_card,
    "Row": _render_row,
    "Column": _render_column,
    "List": _render_list,
    "Button": _render_button,
    "TextField": _render_textfield,
    "CheckBox": _render_checkbox,
    "Divider": _render_divider,
    "Image": _render_image,
    "Icon": _render_icon,
    "Tabs": _render_tabs,
    "Modal": _render_modal,
}

__all__ = ["COMPONENT_REGISTRY", "ICON_MAP", "ComponentFactory", "_dispatch"]
