"""Unit tests for Zalo OA Template Engine."""

# Test helpers conventionally skip full type annotations.
# mypy: disable-error-code="no-untyped-def,call-arg,union-attr,misc"

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.seed.zalo.templates import ZaloTemplateEngine, get_template_engine
from src.seed.zalo.models import ZaloCarouselMessage, ZaloImageMessage, ZaloTextMessage


@pytest.fixture
def temp_template_dir() -> Path:
    """Create temporary template directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def template_engine(temp_template_dir: Path) -> ZaloTemplateEngine:
    """Create template engine with temp directory."""
    return ZaloTemplateEngine(str(temp_template_dir))


class TestZaloTemplateEngine:
    """Tests for ZaloTemplateEngine."""

    def test_init_creates_directories(self, temp_template_dir: Path):
        """Test initialization creates locale directories."""
        ZaloTemplateEngine(str(temp_template_dir))

        assert (temp_template_dir / "vi_VN").exists()
        assert (temp_template_dir / "en_US").exists()

    def test_default_templates_created(self, temp_template_dir: Path):
        """Test default templates are created."""
        ZaloTemplateEngine(str(temp_template_dir))

        for locale in ["vi_VN", "en_US"]:
            locale_dir = temp_template_dir / locale
            assert (locale_dir / "welcome.jinja2").exists()
            assert (locale_dir / "help.jinja2").exists()
            assert (locale_dir / "fallback.jinja2").exists()
            assert (locale_dir / "promo.jinja2").exists()

    def test_render_simple_template(self, template_engine: ZaloTemplateEngine):
        """Test rendering a simple template."""
        # Add a test template
        template_engine.add_template("test", "Hello {{ name }}!", "vi_VN")

        result = template_engine.render("test", "vi_VN", name="World")
        assert result == "Hello World!"

    def test_render_with_locale_fallback(self, template_engine: ZaloTemplateEngine):
        """Test fallback to default locale."""
        template_engine.add_template("test", "VN: {{ name }}", "vi_VN")
        # Don't add English version

        result = template_engine.render("test", "en_US", name="Test")
        assert result == "VN: Test"

    def test_render_missing_template_raises(self, template_engine: ZaloTemplateEngine):
        """Test missing template raises error."""
        with pytest.raises(Exception):  # TemplateNotFound
            template_engine.render("nonexistent", "vi_VN")

    def test_render_text_message(self, template_engine: ZaloTemplateEngine):
        """Test rendering text message from template."""
        template_engine.add_template(
            "greeting", "Chào {{ name }}, chào mừng đến {{ place }}!", "vi_VN"
        )

        message = template_engine.render_message(
            "greeting", "user_123", "vi_VN", "text", name="An", place="Mekong"
        )

        assert isinstance(message, ZaloTextMessage)
        assert message.recipient_id == "user_123"
        assert message.content == "Chào An, chào mừng đến Mekong!"

    def test_render_image_message(self, template_engine: ZaloTemplateEngine):
        """Test rendering image message from template."""
        template_engine.add_template("promo_image", "Promo image", "vi_VN")

        message = template_engine.render_message(
            "promo_image",
            "user_123",
            "vi_VN",
            "image",
            image_url="https://example.com/promo.jpg",
            width=800,
            height=600,
        )

        assert isinstance(message, ZaloImageMessage)
        assert message.recipient_id == "user_123"
        assert message.image_url == "https://example.com/promo.jpg"
        assert message.width == 800
        assert message.height == 600

    def test_render_carousel_message(self, template_engine: ZaloTemplateEngine):
        """Test rendering carousel message from template."""
        template_engine.add_template("carousel", "Carousel", "vi_VN")

        elements = [
            {"title": "Item 1", "image_url": "https://example.com/1.jpg", "action_url": "https://example.com/1"},
            {"title": "Item 2", "image_url": "https://example.com/2.jpg", "action_url": "https://example.com/2"},
        ]

        message = template_engine.render_message(
            "carousel", "user_123", "vi_VN", "carousel", elements=elements
        )

        assert isinstance(message, ZaloCarouselMessage)
        assert message.recipient_id == "user_123"
        assert len(message.elements) == 2
        assert message.elements[0].title == "Item 1"
        assert message.elements[1].title == "Item 2"

    def test_get_available_templates(self, template_engine: ZaloTemplateEngine):
        """Test listing available templates."""
        template_engine.add_template("custom1", "Template 1", "vi_VN")
        template_engine.add_template("custom2", "Template 2", "vi_VN")

        templates = template_engine.get_available_templates("vi_VN")
        assert "welcome" in templates
        assert "help" in templates
        assert "custom1" in templates
        assert "custom2" in templates

    def test_add_template_updates_existing(self, template_engine: ZaloTemplateEngine):
        """Test adding template overwrites existing."""
        template_engine.add_template("welcome", "Original", "vi_VN")
        result1 = template_engine.render("welcome", "vi_VN")
        assert result1 == "Original"

        template_engine.add_template("welcome", "Updated", "vi_VN")
        result2 = template_engine.render("welcome", "vi_VN")
        assert result2 == "Updated"

    def test_get_template_source(self, template_engine: ZaloTemplateEngine):
        """Test getting raw template source."""
        template_engine.add_template("source_test", "Source: {{ value }}", "vi_VN")

        source = template_engine.get_template_source("source_test", "vi_VN")
        assert source == "Source: {{ value }}"

    def test_get_template_source_not_found(self, template_engine: ZaloTemplateEngine):
        """Test getting source for missing template."""
        with pytest.raises(FileNotFoundError):
            template_engine.get_template_source("missing", "vi_VN")

    def test_supported_locales(self, template_engine: ZaloTemplateEngine):
        """Test supported locales."""
        assert "vi_VN" in template_engine.supported_locales
        assert "en_US" in template_engine.supported_locales

    def test_default_locale(self, template_engine: ZaloTemplateEngine):
        """Test default locale."""
        assert template_engine.default_locale == "vi_VN"


class TestGetTemplateEngine:
    """Tests for get_template_engine singleton."""

    def test_singleton(self):
        """Test get_template_engine returns same instance."""
        engine1 = get_template_engine()
        engine2 = get_template_engine()
        assert engine1 is engine2