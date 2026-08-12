"""Zalo OA Message Templates with VN/EN i18n using Jinja2."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from .models import ZaloCarouselElement, ZaloCarouselMessage, ZaloImageMessage, ZaloOutboundMessage, ZaloTextMessage


class ZaloTemplateEngine:
    """Template engine for Zalo messages with VN/EN i18n support."""

    def __init__(self, template_dir: str | None = None):
        """Initialize template engine.

        Args:
            template_dir: Directory containing template files. Defaults to src/seed/zalo/templates/
        """
        if template_dir is None:
            template_dir = str(Path(__file__).parent / "templates")

        self.template_dir = Path(template_dir)
        self.template_dir.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(["html", "xml", "jinja2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Default locale
        self.default_locale = "vi_VN"
        self.supported_locales = ["vi_VN", "en_US"]

        # Initialize default templates
        self._init_default_templates()

    def _init_default_templates(self) -> None:
        """Create default templates if they don't exist."""
        templates = {
            "welcome": {
                "vi_VN": "Chào {{ name }}, cảm ơn bạn đã theo dõi {{ oa_name }}! 🎉\n\n{{ oa_name }} sẽ gửi đến bạn những cập nhật mới nhất về {{ topic }}.\n\nGõ \"{{ help_keyword }}\" để xem hướng dẫn sử dụng.",
                "en_US": "Hi {{ name }}, thanks for following {{ oa_name }}! 🎉\n\n{{ oa_name }} will send you the latest updates about {{ topic }}.\n\nType \"{{ help_keyword }}\" to see usage guide.",
            },
            "help": {
                "vi_VN": "📋 *Hướng dẫn sử dụng {{ oa_name }}*\n\n{{ commands }}\n\nGõ từ khóa để tương tác:\n{{ keywords }}\n\nCần hỗ trợ? Liên hệ: {{ support_contact }}",
                "en_US": "📋 *{{ oa_name }} Usage Guide*\n\n{{ commands }}\n\nType keywords to interact:\n{{ keywords }}\n\nNeed help? Contact: {{ support_contact }}",
            },
            "fallback": {
                "vi_VN": "Xin lỗi, {{ name }}. Tôi không hiểu tin nhắn của bạn. 😔\n\nGõ \"{{ help_keyword }}\" để xem hướng dẫn hoặc chọn menu bên dưới.",
                "en_US": "Sorry {{ name }}, I didn't understand your message. 😔\n\nType \"{{ help_keyword }}\" for help or use the menu below.",
            },
            "promo": {
                "vi_VN": "🎁 *{{ title }}*\n\n{{ description }}\n\n💰 Giá: {{ price }}\n⏰ Hạn: {{ expiry }}\n\n👉 {{ cta_text }}: {{ cta_url }}",
                "en_US": "🎁 *{{ title }}*\n\n{{ description }}\n\n💰 Price: {{ price }}\n⏰ Expires: {{ expiry }}\n\n👉 {{ cta_text }}: {{ cta_url }}",
            },
            "order_confirmation": {
                "vi_VN": "✅ *Xác nhận đơn hàng #{{ order_id }}*\n\nChào {{ name }},\n\nĐơn hàng của bạn đã được xác nhận:\n{{ items }}\n\n💰 Tổng cộng: {{ total }}\n📦 Trạng thái: {{ status }}\n\nCảm ơn bạn đã mua hàng tại {{ oa_name }}!",
                "en_US": "✅ *Order Confirmation #{{ order_id }}*\n\nHi {{ name }},\n\nYour order has been confirmed:\n{{ items }}\n\n💰 Total: {{ total }}\n📦 Status: {{ status }}\n\nThank you for shopping at {{ oa_name }}!",
            },
            "shipping_update": {
                "vi_VN": "📦 *Cập nhật vận đơn #{{ tracking_id }}*\n\nChào {{ name }},\n\nĐơn hàng #{{ order_id }} đã được gửi:\n🚚 Đơn vị: {{ carrier }}\n📍 Trạng thái: {{ status }}\n🔗 Tra cứu: {{ tracking_url }}\n\nDự kiến giao: {{ estimated_delivery }}",
                "en_US": "📦 *Shipping Update #{{ tracking_id }}*\n\nHi {{ name }},\n\nOrder #{{ order_id }} has been shipped:\n🚚 Carrier: {{ carrier }}\n📍 Status: {{ status }}\n🔗 Track: {{ tracking_url }}\n\nEstimated delivery: {{ estimated_delivery }}",
            },
        }

        for name, locales in templates.items():
            for locale, content in locales.items():
                template_path = self.template_dir / locale / f"{name}.jinja2"
                template_path.parent.mkdir(parents=True, exist_ok=True)
                if not template_path.exists():
                    template_path.write_text(content, encoding="utf-8")

    def render(
        self,
        template_name: str,
        locale: str | None = None,
        **context: Any,
    ) -> str:
        """Render a template with given context.

        Args:
            template_name: Template name (without extension)
            locale: Locale code (vi_VN, en_US). Defaults to default_locale
            **context: Template variables

        Returns:
            Rendered template string
        """
        locale = locale or self.default_locale

        if locale not in self.supported_locales:
            locale = self.default_locale

        template_path = f"{locale}/{template_name}.jinja2"

        try:
            template = self.env.get_template(template_path)
        except TemplateNotFound:
            # Fallback to default locale
            if locale != self.default_locale:
                template_path = f"{self.default_locale}/{template_name}.jinja2"
                template = self.env.get_template(template_path)
            else:
                raise

        return template.render(**context)

    def render_message(
        self,
        template_name: str,
        recipient_id: str,
        locale: str | None = None,
        message_type: str = "text",
        **context: Any,
    ) -> ZaloOutboundMessage:
        """Render template and create Zalo message object.

        Args:
            template_name: Template name
            recipient_id: Zalo user ID
            locale: Locale code
            message_type: Message type (text, image, carousel)
            **context: Template variables

        Returns:
            ZaloOutboundMessage ready to send
        """
        content = self.render(template_name, locale, **context)

        if message_type == "text":
            return ZaloTextMessage(recipient_id=recipient_id, content=content)
        elif message_type == "image":
            image_url = context.get("image_url", "")
            return ZaloImageMessage(
                recipient_id=recipient_id,
                image_url=image_url,
                width=context.get("width"),
                height=context.get("height"),
            )
        elif message_type == "carousel":
            elements = context.get("elements", [])
            carousel_elements = [
                ZaloCarouselElement(**e) for e in elements
            ]
            return ZaloCarouselMessage(
                recipient_id=recipient_id,
                elements=carousel_elements,
            )
        else:
            return ZaloTextMessage(recipient_id=recipient_id, content=content)

    def get_available_templates(self, locale: str | None = None) -> list[str]:
        """List available template names for a locale."""
        locale = locale or self.default_locale
        locale_dir = self.template_dir / locale
        if not locale_dir.exists():
            return []
        return [f.stem for f in locale_dir.glob("*.jinja2")]

    def add_template(self, name: str, content: str, locale: str | None = None) -> None:
        """Add or update a template.

        Args:
            name: Template name
            content: Template content
            locale: Locale code (defaults to default_locale)
        """
        locale = locale or self.default_locale
        template_path = self.template_dir / locale / f"{name}.jinja2"
        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(content, encoding="utf-8")

    def get_template_source(self, name: str, locale: str | None = None) -> str:
        """Get raw template source."""
        locale = locale or self.default_locale
        template_path = self.template_dir / locale / f"{name}.jinja2"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"Template not found: {name} ({locale})")


# Default template engine instance
_default_engine: ZaloTemplateEngine | None = None


def get_template_engine(template_dir: str | None = None) -> ZaloTemplateEngine:
    """Get or create default template engine."""
    global _default_engine
    if _default_engine is None:
        _default_engine = ZaloTemplateEngine(template_dir)
    return _default_engine