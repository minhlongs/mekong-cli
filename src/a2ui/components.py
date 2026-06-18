"""Rich renderers for A2UI component dictionaries."""

from __future__ import annotations

from typing import Any, Callable

from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text


ICON_MAP = {
    "home": "🏠",
    "star": "⭐",
    "search": "🔎",
    "settings": "⚙",
    "user": "👤",
    "check": "✓",
    "warning": "⚠",
    "info": "ℹ",
    "calendar": "📅",
    "mail": "✉",
}


def _resolve(value: Any, data: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$data."):
        key = value[len("$data.") :]
        return data.get(key, value)
    return value


def render_component(component: dict[str, Any], data: dict[str, Any]) -> Any:
    renderer = COMPONENT_REGISTRY.get(component.get("type", "Text"), _render_text)
    return renderer(component, data)


def _render_text(component: dict[str, Any], data: dict[str, Any]) -> Text:
    text = str(_resolve(component.get("text", ""), data))
    variant = component.get("variant", "body")
    style = {"heading": "bold", "caption": "dim"}.get(variant, "")
    return Text(text, style=style)


def _render_card(component: dict[str, Any], data: dict[str, Any]) -> Panel:
    children = [render_component(child, data) for child in component.get("children", [])]
    body = Group(*children) if children else Text("")
    return Panel(body, title=component.get("title"))


def _render_row(component: dict[str, Any], data: dict[str, Any]) -> Any:
    children = [render_component(child, data) for child in component.get("children", [])]
    return Columns(children) if children else Text("")


def _render_column(component: dict[str, Any], data: dict[str, Any]) -> Any:
    children = [render_component(child, data) for child in component.get("children", [])]
    return Group(*children) if children else Text("")


def _render_list(component: dict[str, Any], data: dict[str, Any]) -> Table:
    items = _resolve(component.get("items", []), data) or []
    table = Table(show_header=False)
    table.add_column("Item")
    for item in items:
        label = item.get("label", "") if isinstance(item, dict) else str(item)
        table.add_row(str(label))
    return table


def _render_button(component: dict[str, Any], data: dict[str, Any]) -> Text:
    label = str(_resolve(component.get("label", ""), data))
    return Text(f"▸ {label}")


def _render_textfield(component: dict[str, Any], data: dict[str, Any]) -> Text:
    label = component.get("label")
    placeholder = component.get("placeholder", "")
    prefix = f"{label}: " if label else ""
    return Text(f"{prefix}⎕ {placeholder}")


def _render_checkbox(component: dict[str, Any], data: dict[str, Any]) -> Text:
    mark = "☑" if component.get("checked") else "☐"
    return Text(f"{mark} {component.get('label', '')}")


def _render_divider(component: dict[str, Any], data: dict[str, Any]) -> Rule:
    return Rule(component.get("title", ""))


def _render_image(component: dict[str, Any], data: dict[str, Any]) -> Text:
    alt = component.get("alt", "")
    src = component.get("src", "")
    return Text(f"Image: {alt} {src}".strip())


def _render_icon(component: dict[str, Any], data: dict[str, Any]) -> Text:
    name = component.get("name", "")
    icon = ICON_MAP.get(name, str(name))
    label = component.get("label")
    return Text(f"{icon} {label}" if label else str(icon))


def _render_tabs(component: dict[str, Any], data: dict[str, Any]) -> Table:
    active = int(component.get("activeIndex", 0))
    table = Table(show_header=False)
    table.add_column("Tabs")
    labels = []
    for index, tab in enumerate(component.get("tabs", [])):
        label = tab.get("label", "") if isinstance(tab, dict) else str(tab)
        labels.append(f"[{label}]" if index == active else label)
    table.add_row(" | ".join(labels))
    return table


def _render_modal(component: dict[str, Any], data: dict[str, Any]) -> Panel:
    children = [render_component(child, data) for child in component.get("children", [])]
    return Panel(Group(*children) if children else Text(""), title=component.get("title"))


COMPONENT_REGISTRY: dict[str, Callable[[dict[str, Any], dict[str, Any]], Any]] = {
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
