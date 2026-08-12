"""Pydantic models for Zalo OA integration."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ZaloMessageType(str, Enum):
    """Zalo OA message types."""

    TEXT = "text"
    IMAGE = "image"
    CAROUSEL = "carousel"
    FILE = "file"
    LOCATION = "location"


class ZaloEventType(str, Enum):
    """Zalo OA webhook event types."""

    MESSAGE = "message"
    FOLLOW = "follow"
    UNFOLLOW = "unfollow"
    USER_INFO = "user_info"
    CLICK_MENU = "click_menu"
    SCAN_QR = "scan_qr"


class ZaloOAConfig(BaseModel):
    """Zalo Official Account configuration."""

    oa_id: str = Field(..., description="Zalo OA ID")
    secret_key: str = Field(..., description="Zalo OA Secret Key")
    access_token: str | None = Field(None, description="Current access token")
    refresh_token: str | None = Field(None, description="Refresh token for token renewal")
    token_expires_at: datetime | None = Field(None, description="Access token expiry")
    webhook_secret: str = Field(..., description="Webhook HMAC secret")
    rate_limit_per_minute: int = Field(100, description="Rate limit per minute")
    rate_limit_window_seconds: int = Field(60, description="Rate limit window in seconds")

    # Note: env vars are read explicitly via os.getenv (see client.py), so no env_prefix.
    model_config = ConfigDict(
        extra="forbid",
    )

    @field_validator("rate_limit_per_minute", mode="before")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Rate limit must be positive")
        return v


class ZaloUserProfile(BaseModel):
    """Zalo user profile from webhook or API."""

    user_id: str = Field(..., description="Zalo user ID")
    name: str | None = Field(None, description="User display name")
    gender: int | None = Field(None, description="Gender: 1=male, 2=female, 0=unknown")
    birthday: str | None = Field(None, description="Birthday in DD/MM/YYYY format")
    phone: str | None = Field(None, description="Phone number")
    avatar: str | None = Field(None, description="Avatar URL")
    locale: str = Field("vi_VN", description="User locale")

    model_config = ConfigDict(
        extra="allow",
    )


class ZaloMessage(BaseModel):
    """Base Zalo message model."""

    message_type: str
    recipient_id: str = Field(..., description="Recipient user ID")

    model_config = ConfigDict(
        extra="forbid",
    )


class ZaloTextMessage(ZaloMessage):
    """Zalo text message."""

    message_type: Literal["text"] = "text"
    content: str = Field(..., max_length=5000, description="Text content")


class ZaloImageMessage(ZaloMessage):
    """Zalo image message."""

    message_type: Literal["image"] = "image"
    image_url: str = Field(..., description="Image URL (must be HTTPS)")
    width: int | None = Field(None, description="Image width")
    height: int | None = Field(None, description="Image height")


class ZaloCarouselElement(BaseModel):
    """Carousel element for Zalo carousel message."""

    title: str = Field(..., max_length=80, description="Element title")
    subtitle: str | None = Field(None, max_length=80, description="Element subtitle")
    image_url: str = Field(..., description="Image URL (HTTPS)")
    action_url: str | None = Field(None, description="Action URL on click")
    action_type: str = Field("open_url", description="Action type: open_url, phone_call, etc.")


class ZaloCarouselMessage(ZaloMessage):
    """Zalo carousel message."""

    message_type: Literal["carousel"] = "carousel"
    elements: list[ZaloCarouselElement] = Field(
        ..., min_length=1, max_length=10, description="Carousel elements (1-10)"
    )


class ZaloWebhookPayload(BaseModel):
    """Zalo OA webhook payload."""

    event_name: ZaloEventType
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    follower: ZaloUserProfile | None = Field(None, description="Follower info for follow/unfollow")
    message: ZaloOutboundMessage | None = Field(None, description="Message content for message events")
    sender: ZaloUserProfile | None = Field(None, description="Message sender")
    menu_id: str | None = Field(None, description="Menu ID for click_menu events")
    qr_code_id: str | None = Field(None, description="QR code ID for scan_qr events")

    model_config = ConfigDict(
        use_enum_values=True,
        extra="allow",
    )


class ZaloAPIResponse(BaseModel):
    """Standard Zalo API response."""

    error: int = Field(0, description="Error code (0 = success)")
    message: str = Field("", description="Error message")
    data: dict[str, Any] | None = Field(None, description="Response data")


class ZaloTokenResponse(BaseModel):
    """Zalo OAuth token response."""

    access_token: str
    refresh_token: str
    expires_in: int = Field(..., description="Token lifetime in seconds")
    token_type: str = Field("Bearer")


class ZaloSendMessageResponse(BaseModel):
    """Zalo send message response."""

    error: int
    message: str
    msg_id: str | None = None
    timestamp: int | None = None


class AutomationRule(BaseModel):
    """Automation rule for keyword-based responses."""

    id: str = Field(..., description="Unique rule ID")
    name: str = Field(..., description="Rule name")
    keywords: list[str] = Field(..., min_length=1, description="Trigger keywords (case-insensitive)")
    match_type: Literal["exact", "contains", "regex"] = Field("contains", description="Match type")
    priority: int = Field(0, description="Higher priority executes first")
    enabled: bool = Field(True, description="Whether rule is active")
    actions: list[AutomationAction] = Field(..., min_length=1, description="Actions to execute")
    conditions: list[AutomationCondition] = Field(default_factory=list, description="Additional conditions")

    model_config = ConfigDict(
        extra="forbid",
    )


class AutomationAction(BaseModel):
    """Automation action to execute.

    `type` may be one of the built-in actions
    (``send_message``, ``send_template``, ``tag_user``, ``call_webhook``, ``delay``)
    or a custom action name registered via ``ZaloAutomationEngine.register_custom_action``.
    """

    type: str = Field(..., max_length=64, description="Action type (built-in or custom)")
    params: dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class AutomationCondition(BaseModel):
    """Automation condition for rule execution.

    `type` may be one of the built-in conditions
    (``user_tag``, ``time_range``, ``user_locale``, ``message_count``)
    or a custom condition name registered via ``ZaloAutomationEngine.register_custom_condition``.
    """

    type: str = Field(..., max_length=64, description="Condition type (built-in or custom)")
    params: dict[str, Any] = Field(default_factory=dict, description="Condition parameters")


class RateLimitInfo(BaseModel):
    """Rate limit status information."""

    limit: int = Field(..., description="Maximum requests allowed")
    remaining: int = Field(..., description="Remaining requests in window")
    reset_at: int = Field(..., description="Unix timestamp when limit resets")
    exceeded: bool = Field(False, description="Whether limit is exceeded")


# Type alias for union of message types
ZaloOutboundMessage = Annotated[
    ZaloTextMessage | ZaloImageMessage | ZaloCarouselMessage,
    Field(discriminator="message_type"),
]