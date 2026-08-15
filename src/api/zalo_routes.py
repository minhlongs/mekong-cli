"""Zalo OA FastAPI Routes for Mekong CLI Gateway."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.seed.zalo import (
    ZaloAutomationEngine,
    ZaloOAClient,
    ZaloOAConfig,
    ZaloRateLimiter,
    ZaloTemplateEngine,
    ZaloCarouselElement,
    ZaloCarouselMessage,
    ZaloImageMessage,
    ZaloTextMessage,
    ZaloUserProfile,
    create_rate_limiter,
    get_template_engine,
)
from src.seed.zalo.automation import AutomationRule
from src.seed.zalo.models import ZaloEventType
from src.seed.zalo.rate_limiter import InMemoryKV, RateLimitInfo
from src.seed.zalo.webhook import create_zalo_webhook_router

router = APIRouter(prefix="/api/v1/zalo", tags=["Zalo OA"])

# Global instances (initialized on first use)
_zalo_client: ZaloOAClient | None = None
_zalo_config: ZaloOAConfig | None = None
_automation_engine: ZaloAutomationEngine | None = None
_rate_limiter: ZaloRateLimiter | None = None
_template_engine: ZaloTemplateEngine | None = None


def get_zalo_config() -> ZaloOAConfig:
    """Get Zalo OA configuration from environment."""
    global _zalo_config
    if _zalo_config is None:
        _zalo_config = ZaloOAConfig(
            oa_id=os.getenv("ZALO_OA_ID", ""),
            secret_key=os.getenv("ZALO_SECRET_KEY", ""),
            access_token=os.getenv("ZALO_ACCESS_TOKEN") or None,
            refresh_token=os.getenv("ZALO_REFRESH_TOKEN") or None,
            webhook_secret=os.getenv("ZALO_WEBHOOK_SECRET", ""),
            rate_limit_per_minute=int(os.getenv("ZALO_RATE_LIMIT", "100")),
        )
    return _zalo_config


async def get_zalo_client() -> ZaloOAClient:
    """Get or create Zalo OA client."""
    global _zalo_client
    if _zalo_client is None:
        config = get_zalo_config()
        _zalo_client = ZaloOAClient(config)
        await _zalo_client._ensure_token()
    return _zalo_client


def get_automation_engine() -> ZaloAutomationEngine:
    """Get or create automation engine."""
    global _automation_engine
    if _automation_engine is None:
        template_engine = get_template_engine()
        _automation_engine = ZaloAutomationEngine(template_engine=template_engine)
        # Add common rules
        from src.seed.zalo.automation import create_common_rules
        for rule in create_common_rules():
            _automation_engine.add_rule(rule)
    return _automation_engine


def get_rate_limiter() -> ZaloRateLimiter:
    """Get or create rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        kv = InMemoryKV()  # Use Cloudflare KV in production
        _rate_limiter = create_rate_limiter(kv, sliding=True)
    return _rate_limiter


def get_template_engine_instance() -> ZaloTemplateEngine:
    """Get template engine instance."""
    global _template_engine
    if _template_engine is None:
        _template_engine = get_template_engine()
    return _template_engine


# =============================================================================
# Request/Response Models
# =============================================================================

class SendTextRequest(BaseModel):
    user_id: str = Field(..., description="Zalo user ID")
    content: str = Field(..., max_length=5000, description="Message content")
    locale: str = Field("vi_VN", description="Locale for template rendering")


class SendImageRequest(BaseModel):
    user_id: str = Field(..., description="Zalo user ID")
    image_url: str = Field(..., description="HTTPS image URL")
    width: int | None = Field(None, description="Image width")
    height: int = Field(None, description="Image height")


class SendCarouselRequest(BaseModel):
    user_id: str = Field(..., description="Zalo user ID")
    elements: list[dict[str, Any]] = Field(..., min_length=1, max_length=10)


class SendTemplateRequest(BaseModel):
    user_id: str = Field(..., description="Zalo user ID")
    template: str = Field(..., description="Template name")
    locale: str = Field("vi_VN", description="Locale code")
    message_type: str = Field("text", description="Message type: text, image, carousel")
    params: dict[str, Any] = Field(default_factory=dict, description="Template parameters")


class BroadcastRequest(BaseModel):
    message: dict[str, Any] = Field(..., description="Message payload (text, image, or carousel)")


class AutomationRuleRequest(BaseModel):
    id: str = Field(..., description="Rule ID")
    name: str = Field(..., description="Rule name")
    keywords: list[str] = Field(..., min_length=1)
    match_type: str = Field("contains", pattern="^(exact|contains|regex)$")
    priority: int = Field(0)
    enabled: bool = Field(True)
    actions: list[dict[str, Any]] = Field(..., min_length=1)
    conditions: list[dict[str, Any]] = Field(default_factory=list)


class OAuthCallbackRequest(BaseModel):
    code: str = Field(..., description="Authorization code")
    redirect_uri: str = Field(..., description="Redirect URI")


# =============================================================================
# Health & Config
# =============================================================================

@router.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "zalo-oa"}


@router.get("/config")
async def get_config() -> dict[str, Any]:
    """Get Zalo OA configuration (sanitized)."""
    config = get_zalo_config()
    return {
        "oa_id": config.oa_id,
        "has_access_token": bool(config.access_token),
        "has_refresh_token": bool(config.refresh_token),
        "rate_limit_per_minute": config.rate_limit_per_minute,
        "rate_limit_window_seconds": config.rate_limit_window_seconds,
    }


# =============================================================================
# OAuth
# =============================================================================

@router.get("/oauth/url")
async def get_oauth_url(
    redirect_uri: str = Query(..., description="OAuth redirect URI"),
    state: str | None = Query(None, description="CSRF state parameter"),
    client: ZaloOAClient = Depends(get_zalo_client),
) -> dict[str, str]:
    """Get Zalo OAuth authorization URL."""
    url = client.generate_oauth_url(redirect_uri, state)
    return {"authorization_url": url}


@router.post("/oauth/callback")
async def oauth_callback(
    request: OAuthCallbackRequest,
    client: ZaloOAClient = Depends(get_zalo_client),
) -> dict[str, Any]:
    """Exchange authorization code for access token."""
    token_response = await client.exchange_code_for_token(request.code, request.redirect_uri)

    # Update config with new tokens
    config = get_zalo_config()
    config.access_token = token_response.access_token
    config.refresh_token = token_response.refresh_token
    from datetime import datetime, timedelta
    config.token_expires_at = datetime.now() + timedelta(seconds=token_response.expires_in - 60)

    # Re-initialize client with new tokens
    global _zalo_client
    _zalo_client = ZaloOAClient(config)

    return {
        "access_token": token_response.access_token,
        "refresh_token": token_response.refresh_token,
        "expires_in": token_response.expires_in,
        "token_type": token_response.token_type,
    }


# =============================================================================
# Messaging
# =============================================================================

@router.post("/messages/text", status_code=status.HTTP_200_OK)
async def send_text_message(
    request: SendTextRequest,
    client: ZaloOAClient = Depends(get_zalo_client),
) -> dict[str, Any]:
    """Send a text message to a Zalo user."""
    response = await client.send_text(request.user_id, request.content)
    return response.model_dump()


@router.post("/messages/image", status_code=status.HTTP_200_OK)
async def send_image_message(
    request: SendImageRequest,
    client: ZaloOAClient = Depends(get_zalo_client),
) -> dict[str, Any]:
    """Send an image message to a Zalo user."""
    response = await client.send_image(
        request.user_id, request.image_url, request.width, request.height
    )
    return response.model_dump()


@router.post("/messages/carousel", status_code=status.HTTP_200_OK)
async def send_carousel_message(
    request: SendCarouselRequest,
    client: ZaloOAClient = Depends(get_zalo_client),
) -> dict[str, Any]:
    """Send a carousel message to a Zalo user."""
    response = await client.send_carousel(request.user_id, request.elements)
    return response.model_dump()


@router.post("/messages/template", status_code=status.HTTP_200_OK)
async def send_template_message(
    request: SendTemplateRequest,
    client: ZaloOAClient = Depends(get_zalo_client),
    template_engine: ZaloTemplateEngine = Depends(get_template_engine_instance),
) -> dict[str, Any]:
    """Send a templated message."""
    message = template_engine.render_message(
        template_name=request.template,
        recipient_id=request.user_id,
        locale=request.locale,
        message_type=request.message_type,
        **request.params,
    )
    response = await client.send_message(message)
    return response.model_dump()


@router.post("/messages/broadcast", status_code=status.HTTP_200_OK)
async def broadcast_message(
    request: BroadcastRequest,
    client: ZaloOAClient = Depends(get_zalo_client),
) -> dict[str, Any]:
    """Broadcast a message to all followers."""
    # Determine message type and create appropriate message object
    msg_data = request.message
    msg_type = msg_data.get("message_type", "text")

    if msg_type == "text":
        message = ZaloTextMessage(
            recipient_id="",  # Ignored for broadcast
            content=msg_data.get("content", ""),
        )
    elif msg_type == "image":
        message = ZaloImageMessage(
            recipient_id="",
            image_url=msg_data.get("image_url", ""),
            width=msg_data.get("width"),
            height=msg_data.get("height"),
        )
    elif msg_type == "carousel":
        elements = [
            ZaloCarouselElement(**e) for e in msg_data.get("elements", [])
        ]
        message = ZaloCarouselMessage(recipient_id="", elements=elements)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown message type: {msg_type}",
        )

    response = await client.broadcast_message(message)
    return response.model_dump()


# =============================================================================
# User Management
# =============================================================================

@router.get("/users/{user_id}", response_model=ZaloUserProfile)
async def get_user_profile(
    user_id: str,
    client: ZaloOAClient = Depends(get_zalo_client),
) -> ZaloUserProfile:
    """Get Zalo user profile."""
    return await client.get_user_profile(user_id)


@router.get("/followers")
async def get_followers(
    offset: int = Query(0, ge=0),
    count: int = Query(50, ge=1, le=50),
    client: ZaloOAClient = Depends(get_zalo_client),
) -> list[ZaloUserProfile]:
    """Get list of OA followers."""
    return await client.get_followers(offset, count)


# =============================================================================
# Automation Rules
# =============================================================================

@router.get("/automation/rules")
async def list_automation_rules(
    enabled_only: bool = Query(True),
    engine: ZaloAutomationEngine = Depends(get_automation_engine),
) -> list[dict[str, Any]]:
    """List all automation rules."""
    rules = engine.list_rules(enabled_only)
    return [rule.model_dump() for rule in rules]


@router.get("/automation/rules/{rule_id}")
async def get_automation_rule(
    rule_id: str,
    engine: ZaloAutomationEngine = Depends(get_automation_engine),
) -> dict[str, Any]:
    """Get a specific automation rule."""
    rule = engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule.model_dump()


@router.post("/automation/rules", status_code=status.HTTP_201_CREATED)
async def create_automation_rule(
    request: AutomationRuleRequest,
    engine: ZaloAutomationEngine = Depends(get_automation_engine),
) -> dict[str, Any]:
    """Create or update an automation rule."""
    rule = AutomationRule(**request.model_dump())
    engine.add_rule(rule)
    return rule.model_dump()


@router.delete("/automation/rules/{rule_id}")
async def delete_automation_rule(
    rule_id: str,
    engine: ZaloAutomationEngine = Depends(get_automation_engine),
) -> dict[str, str]:
    """Delete an automation rule."""
    removed = engine.remove_rule(rule_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "deleted", "rule_id": rule_id}


@router.post("/automation/rules/{rule_id}/test")
async def test_automation_rule(
    rule_id: str,
    message: str = Query(..., description="Test message"),
    user_id: str = Query("test_user", description="Test user ID"),
    engine: ZaloAutomationEngine = Depends(get_automation_engine),
) -> dict[str, Any]:
    """Test an automation rule with a sample message."""
    from src.seed.zalo.models import ZaloWebhookPayload, ZaloTextMessage, ZaloUserProfile

    rule = engine.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    # Create mock payload
    payload = ZaloWebhookPayload(
        event_name=ZaloEventType.MESSAGE,
        timestamp=int(__import__("time").time() * 1000),
        sender=ZaloUserProfile(user_id=user_id, name="Test User", locale="vi_VN"),
        message=ZaloTextMessage(recipient_id=user_id, content=message),
    )

    executed = await engine.execute_rules(user_id, message, payload)
    return {
        "rule_id": rule_id,
        "matched": rule_id in executed,
        "executed_rules": executed,
    }


# =============================================================================
# Templates
# =============================================================================

@router.get("/templates")
async def list_templates(
    locale: str = Query("vi_VN"),
    engine: ZaloTemplateEngine = Depends(get_template_engine_instance),
) -> list[str]:
    """List available templates for a locale."""
    return engine.get_available_templates(locale)


@router.get("/templates/{template_name}")
async def get_template(
    template_name: str,
    locale: str = Query("vi_VN"),
    engine: ZaloTemplateEngine = Depends(get_template_engine_instance),
) -> dict[str, str]:
    """Get template source."""
    try:
        source = engine.get_template_source(template_name, locale)
        return {"name": template_name, "locale": locale, "source": source}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")


@router.post("/templates/{template_name}/render")
async def render_template(
    template_name: str,
    locale: str = Query("vi_VN"),
    params: dict[str, Any] = None,
    engine: ZaloTemplateEngine = Depends(get_template_engine_instance),
) -> dict[str, str]:
    """Render a template with parameters."""
    params = params or {}
    try:
        rendered = engine.render(template_name, locale, **params)
        return {"rendered": rendered}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Rate Limiting
# =============================================================================

@router.get("/rate-limit/{oa_id}")
async def get_rate_limit_status(
    oa_id: str,
    limiter: ZaloRateLimiter = Depends(get_rate_limiter),
) -> RateLimitInfo:
    """Get current rate limit status for an OA."""
    return await limiter.get_status(oa_id)


@router.post("/rate-limit/{oa_id}/reset")
async def reset_rate_limit(
    oa_id: str,
    limiter: ZaloRateLimiter = Depends(get_rate_limiter),
) -> dict[str, str]:
    """Reset rate limit for an OA (admin)."""
    await limiter.reset_limit(oa_id)
    return {"status": "reset", "oa_id": oa_id}


@router.post("/rate-limit/{oa_id}/config")
async def set_rate_limit_config(
    oa_id: str,
    limit: int = Query(..., ge=1, le=10000),
    window_seconds: int = Query(..., ge=1, le=3600),
    limiter: ZaloRateLimiter = Depends(get_rate_limiter),
) -> dict[str, Any]:
    """Set custom rate limit for an OA."""
    await limiter.set_custom_limit(oa_id, limit, window_seconds)
    return {"status": "updated", "oa_id": oa_id, "limit": limit, "window_seconds": window_seconds}


# =============================================================================
# Webhook Router (mounted separately)
# =============================================================================

def get_zalo_webhook_router() -> APIRouter:
    """Get the webhook router for mounting in gateway."""
    config = get_zalo_config()
    client = ZaloOAClient(config)  # Create new client for webhook
    automation = get_automation_engine()
    rate_limiter = get_rate_limiter()
    return create_zalo_webhook_router(config, client, automation, rate_limiter)


# Export for gateway integration
__all__ = [
    "router",
    "get_zalo_webhook_router",
    "get_zalo_client",
    "get_automation_engine",
    "get_rate_limiter",
    "get_template_engine_instance",
]