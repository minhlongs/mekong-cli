"""Zalo Official Account Integration for Mekong CLI."""

from .client import ZaloOAClient, create_zalo_client_from_env
from .webhook import ZaloWebhookHandler
from .templates import ZaloTemplateEngine, get_template_engine
from .automation import ZaloAutomationEngine
from .rate_limiter import ZaloRateLimiter, create_rate_limiter
from .models import (
    ZaloWebhookPayload,
    ZaloMessage,
    ZaloTextMessage,
    ZaloImageMessage,
    ZaloCarouselMessage,
    ZaloCarouselElement,
    ZaloOutboundMessage,
    ZaloUserProfile,
    ZaloOAConfig,
)

__all__ = [
    "ZaloOAClient",
    "create_zalo_client_from_env",
    "ZaloWebhookHandler",
    "ZaloTemplateEngine",
    "get_template_engine",
    "ZaloAutomationEngine",
    "ZaloRateLimiter",
    "create_rate_limiter",
    "ZaloWebhookPayload",
    "ZaloMessage",
    "ZaloTextMessage",
    "ZaloImageMessage",
    "ZaloCarouselMessage",
    "ZaloCarouselElement",
    "ZaloOutboundMessage",
    "ZaloUserProfile",
    "ZaloOAConfig",
]