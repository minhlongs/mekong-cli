"""Tests for A2UI Terminal Renderer.

Tests the renderer with various A2UI component types and protocol messages.

Run: python3 -m pytest tests/test_a2ui_renderer.py -v
"""

import os
import sys
from io import StringIO
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console

from src.a2ui import A2UIRenderer, COMPONENT_REGISTRY
from src.a2ui.components import (
    ICON_MAP,
    _render_button,
    _render_card,
    _render_checkbox,
    _render_divider,
    _render_image,
    _render_icon,
    _render_list,
    _render_text,
    _render_textfield,
    _render_tabs,
    _render_modal,
    _render_row,
    _render_column,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_renderer() -> tuple[A2UIRenderer, StringIO]:
    """Create renderer with captured output."""
    buf = StringIO()
    console = Console(file=buf, no_color=True, width=120)
    return A2UIRenderer(console=console), buf


# ---------------------------------------------------------------------------
# Component Registry
# ---------------------------------------------------------------------------

class TestComponentRegistry:
    def test_registry_has_all_required_types(self):
        required = [
            "Text", "Card", "Row", "Column", "List",
            "Button", "TextField", "CheckBox", "Divider",
            "Image", "Icon", "Tabs", "Modal",
        ]
        for ctype in required:
            assert ctype in COMPONENT_REGISTRY, f"Missing component: {ctype}"

    def test_registry_values_are_callable(self):
        for name, factory in COMPONENT_REGISTRY.items():
            assert callable(factory), f"Factory for {name} is not callable"

    def test_icon_map_not_empty(self):
        assert len(ICON_MAP) >= 10


# ---------------------------------------------------------------------------
# Text component
# ---------------------------------------------------------------------------

class TestTextComponent:
    def test_heading_variant(self):
        result = _render_text({"type": "Text", "text": "Hello", "variant": "heading"}, {})
        assert "Hello" in str(result)

    def test_body_variant(self):
        result = _render_text({"type": "Text", "text": "body text"}, {})
        assert "body text" in str(result)

    def test_data_binding(self):
        result = _render_text({"type": "Text", "text": "$data.name"}, {"name": "World"})
        assert "World" in str(result)

    def test_missing_binding_falls_back_to_key(self):
        result = _render_text({"type": "Text", "text": "$data.missing"}, {})
        assert "$data.missing" in str(result)

    def test_caption_variant(self):
        result = _render_text({"type": "Text", "text": "caption", "variant": "caption"}, {})
        assert "caption" in str(result)


# ---------------------------------------------------------------------------
# Card component
# ---------------------------------------------------------------------------

class TestCardComponent:
    def test_card_with_title(self):
        result = _render_card({"type": "Card", "title": "My Card", "children": []}, {})
        from rich.panel import Panel
        assert isinstance(result, Panel)

    def test_card_with_children(self):
        component = {
            "type": "Card",
            "title": "Parent",
            "children": [{"type": "Text", "text": "child text"}],
        }
        result = _render_card(component, {})
        from rich.panel import Panel
        assert isinstance(result, Panel)


# ---------------------------------------------------------------------------
# Button component
# ---------------------------------------------------------------------------

class TestButtonComponent:
    def test_button_label_present(self):
        result = _render_button({"type": "Button", "label": "Click Me"}, {})
        assert "Click Me" in str(result)

    def test_button_danger_variant(self):
        result = _render_button({"type": "Button", "label": "Delete", "variant": "danger"}, {})
        assert "Delete" in str(result)

    def test_button_arrow_prefix(self):
        result = _render_button({"type": "Button", "label": "Go"}, {})
        assert "▸" in str(result)


# ---------------------------------------------------------------------------
# List component
# ---------------------------------------------------------------------------

class TestListComponent:
    def test_list_renders_items(self):
        component = {
            "type": "List",
            "items": [{"label": "Item A"}, {"label": "Item B"}],
        }
        result = _render_list(component, {})
        from rich.table import Table
        assert isinstance(result, Table)

    def test_list_with_string_items(self):
        component = {"type": "List", "items": ["Apple", "Banana"]}
        result = _render_list(component, {})
        from rich.table import Table
        assert isinstance(result, Table)

    def test_list_data_binding(self):
        data = {"fruits": [{"label": "Mango"}, {"label": "Papaya"}]}
        component = {"type": "List", "items": "$data.fruits"}
        result = _render_list(component, data)
        from rich.table import Table
        assert isinstance(result, Table)

    def test_empty_list(self):
        result = _render_list({"type": "List", "items": []}, {})
        from rich.table import Table
        assert isinstance(result, Table)


# ---------------------------------------------------------------------------
# CheckBox component
# ---------------------------------------------------------------------------

class TestCheckBoxComponent:
    def test_unchecked_symbol(self):
        result = _render_checkbox({"type": "CheckBox", "label": "Accept", "checked": False}, {})
        assert "☐" in str(result)

    def test_checked_symbol(self):
        result = _render_checkbox({"type": "CheckBox", "label": "Done", "checked": True}, {})
        assert "☑" in str(result)


# ---------------------------------------------------------------------------
# TextField component
# ---------------------------------------------------------------------------

class TestTextFieldComponent:
    def test_placeholder_shown(self):
        result = _render_textfield({"type": "TextField", "placeholder": "Enter name"}, {})
        assert "Enter name" in str(result)

    def test_label_shown(self):
        result = _render_textfield(
            {"type": "TextField", "label": "Email", "placeholder": "you@example.com"}, {}
        )
        assert "Email" in str(result)

    def test_input_symbol(self):
        result = _render_textfield({"type": "TextField", "placeholder": "..."}, {})
        assert "⎕" in str(result)


# ---------------------------------------------------------------------------
# Divider component
# ---------------------------------------------------------------------------

class TestDividerComponent:
    def test_divider_returns_rule(self):
        from rich.rule import Rule
        result = _render_divider({"type": "Divider"}, {})
        assert isinstance(result, Rule)

    def test_divider_with_title(self):
        from rich.rule import Rule
        result = _render_divider({"type": "Divider", "title": "Section"}, {})
        assert isinstance(result, Rule)


# ---------------------------------------------------------------------------
# Image component
# ---------------------------------------------------------------------------

class TestImageComponent:
    def test_image_shows_alt(self):
        result = _render_image({"type": "Image", "alt": "A cat", "src": "/img/cat.png"}, {})
        assert "A cat" in str(result)

    def test_image_placeholder_format(self):
        result = _render_image({"type": "Image", "alt": "logo"}, {})
        text = str(result)
        assert "Image" in text
        assert "logo" in text


# ---------------------------------------------------------------------------
# Icon component
# ---------------------------------------------------------------------------

class TestIconComponent:
    def test_known_icon(self):
        result = _render_icon({"type": "Icon", "name": "home"}, {})
        assert "🏠" in str(result)

    def test_unknown_icon_fallback(self):
        result = _render_icon({"type": "Icon", "name": "nonexistent"}, {})
        assert "nonexistent" in str(result)

    def test_icon_with_label(self):
        result = _render_icon({"type": "Icon", "name": "star", "label": "Favorite"}, {})
        assert "Favorite" in str(result)


# ---------------------------------------------------------------------------
# Tabs component
# ---------------------------------------------------------------------------

class TestTabsComponent:
    def test_tabs_returns_table(self):
        from rich.table import Table
        component = {
            "type": "Tabs",
            "tabs": [{"label": "Home"}, {"label": "Settings"}],
            "activeIndex": 0,
        }
        result = _render_tabs(component, {})
        assert isinstance(result, Table)

    def test_empty_tabs(self):
        from rich.table import Table
        result = _render_tabs({"type": "Tabs", "tabs": []}, {})
        assert isinstance(result, Table)


# ---------------------------------------------------------------------------
# Modal component
# ---------------------------------------------------------------------------

class TestModalComponent:
    def test_modal_is_panel(self):
        from rich.panel import Panel
        result = _render_modal({"type": "Modal", "title": "Confirm", "children": []}, {})
        assert isinstance(result, Panel)


# ---------------------------------------------------------------------------
# Row / Column layout
# ---------------------------------------------------------------------------

class TestLayoutComponents:
    def test_row_with_children(self):
        component = {
            "type": "Row",
            "children": [
                {"type": "Text", "text": "Left"},
                {"type": "Text", "text": "Right"},
            ],
        }
        result = _render_row(component, {})
        from rich.columns import Columns
        assert isinstance(result, Columns)

    def test_row_empty_children(self):
        from rich.text import Text
        result = _render_row({"type": "Row", "children": []}, {})
        assert isinstance(result, Text)

    def test_column_with_children(self):
        component = {
            "type": "Column",
            "children": [
                {"type": "Text", "text": "Top"},
                {"type": "Button", "label": "Bottom"},
            ],
        }
        # Should not raise
        result = _render_column(component, {})
        assert result is not None


# ---------------------------------------------------------------------------
# A2UIRenderer — protocol message handling
# ---------------------------------------------------------------------------

class TestA2UIRendererMessages:
    def test_surface_update_stores_components(self):
        renderer, _ = make_renderer()
        renderer.process_message({
            "surfaceUpdate": {
                "surfaceId": "test",
                "components": [{"type": "Text", "text": "Hello"}],
            }
        })
        assert "test" in renderer.surface_ids
        assert len(renderer.surfaces["test"]) == 1

    def test_data_model_update_merges(self):
        renderer, _ = make_renderer()
        renderer.process_message({"dataModelUpdate": {"key1": "value1"}})
        renderer.process_message({"dataModelUpdate": {"key2": "value2"}})
        assert renderer.data["key1"] == "value1"
        assert renderer.data["key2"] == "value2"

    def test_delete_surface_removes_entry(self):
        renderer, _ = make_renderer()
        renderer.load_surface("to_delete", [{"type": "Text", "text": "bye"}])
        renderer.process_message({"deleteSurface": {"surfaceId": "to_delete"}})
        assert "to_delete" not in renderer.surface_ids

    def test_delete_nonexistent_surface_no_crash(self):
        renderer, _ = make_renderer()
        # Should not raise
        renderer.process_message({"deleteSurface": {"surfaceId": "ghost"}})

    def test_unknown_message_type_logs_warning(self):
        renderer, _ = make_renderer()
        # Should not raise
        renderer.process_message({"unknownKey": {}})

    def test_begin_rendering_unknown_surface_prints_error(self):
        renderer, buf = make_renderer()
        renderer.process_message({"beginRendering": {"surfaceId": "nope"}})
        output = buf.getvalue()
        assert "not found" in output or "nope" in output


# ---------------------------------------------------------------------------
# A2UIRenderer — render_surface integration
# ---------------------------------------------------------------------------

class TestA2UIRendererRender:
    def _render_and_capture(self, components: list, data: dict | None = None) -> str:
        renderer, buf = make_renderer()
        if data:
            renderer.process_message({"dataModelUpdate": data})
        renderer.load_surface("s", components)
        renderer.render_surface("s")
        return buf.getvalue()

    def test_renders_text_component(self):
        output = self._render_and_capture([{"type": "Text", "text": "Surface Text"}])
        assert "Surface Text" in output

    def test_renders_card_component(self):
        output = self._render_and_capture([{"type": "Card", "title": "My Card", "children": []}])
        assert "My Card" in output

    def test_renders_button_component(self):
        output = self._render_and_capture([{"type": "Button", "label": "Submit"}])
        assert "Submit" in output

    def test_renders_list_component(self):
        output = self._render_and_capture([
            {"type": "List", "items": [{"label": "Alpha"}, {"label": "Beta"}]}
        ])
        assert "Alpha" in output
        assert "Beta" in output

    def test_renders_data_bound_text(self):
        output = self._render_and_capture(
            [{"type": "Text", "text": "$data.greeting"}],
            data={"greeting": "Xin chào"},
        )
        assert "Xin chào" in output

    def test_renders_mixed_surface(self):
        """Render a realistic surface with multiple component types."""
        output = self._render_and_capture([
            {"type": "Text", "text": "Dashboard", "variant": "heading"},
            {"type": "Divider"},
            {"type": "Card", "title": "Stats", "children": [
                {"type": "Text", "text": "100 users"},
            ]},
            {"type": "Row", "children": [
                {"type": "Button", "label": "Refresh"},
                {"type": "Button", "label": "Export", "variant": "secondary"},
            ]},
            {"type": "CheckBox", "label": "Auto-refresh", "checked": True},
        ])
        assert "Dashboard" in output
        assert "Stats" in output
        assert "Refresh" in output
        assert "☑" in output

    def test_begin_rendering_message_triggers_render(self):
        renderer, buf = make_renderer()
        renderer.process_message({
            "surfaceUpdate": {
                "surfaceId": "live",
                "components": [{"type": "Text", "text": "Live Output"}],
            }
        })
        renderer.process_message({"beginRendering": {"surfaceId": "live"}})
        assert "Live Output" in buf.getvalue()

    def test_surface_ids_property(self):
        renderer, _ = make_renderer()
        renderer.load_surface("a", [])
        renderer.load_surface("b", [])
        ids = renderer.surface_ids
        assert "a" in ids
        assert "b" in ids

    def test_update_data_helper(self):
        renderer, buf = make_renderer()
        renderer.update_data("city", "Hà Nội")
        renderer.load_surface("city_view", [{"type": "Text", "text": "$data.city"}])
        renderer.render_surface("city_view")
        assert "Hà Nội" in buf.getvalue()
