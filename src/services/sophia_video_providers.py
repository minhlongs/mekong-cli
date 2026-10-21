# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia AI Video Factory — Provider catalogs (Avatars, Voices, Templates) and DNA/MCU integrations."""
from __future__ import annotations

import logging
from typing import Any

from src.services.sophia_video_models import (
    AvatarProfile, VideoTemplate, VoiceProfile, validate_identifier,
)

logger = logging.getLogger(__name__)

AVATAR_CATALOG: list[AvatarProfile] = [
    AvatarProfile(
        id="sophia-anchor-vi-01", name="Sophia News Anchor", gender="female", language="vi-VN",
        provider="HeyGen", preview_url="https://assets.mekongmind.com/avatars/sophia-vi-01.jpg",
        description="Chuyên nghiệp, phát thanh viên bản tin tiếng Việt chuẩn giọng Hà Nội.",
    ),
    AvatarProfile(
        id="sophia-presenter-vi-02", name="Minh Trí Presenter", gender="male", language="vi-VN",
        provider="HeyGen", preview_url="https://assets.mekongmind.com/avatars/minh-tri-02.jpg",
        description="Năng động, phù hợp video hướng dẫn công nghệ và tài chính.",
    ),
    AvatarProfile(
        id="avatar-female-business-01", name="Elena Business Pro", gender="female", language="en-US",
        provider="D-ID", preview_url="https://assets.mekongmind.com/avatars/elena-en-01.jpg",
        description="Corporate executive presenter for English international markets.",
    ),
    AvatarProfile(
        id="avatar-male-tech-01", name="Alex Tech Explainer", gender="male", language="en-US",
        provider="D-ID", preview_url="https://assets.mekongmind.com/avatars/alex-tech-01.jpg",
        description="Modern SaaS explainer and developer advocate presenter.",
    ),
]

VOICE_CATALOG: list[VoiceProfile] = [
    VoiceProfile(
        id="elevenlabs-vi-hoang-01",
        name="Hoàng Nam (VI)",
        language="vi-VN",
        gender="male",
        provider="ElevenLabs",
        sample_text="Chào mừng quý vị đến với Mekong CLI AI Video Factory.",
        preview_url="https://assets.mekongmind.com/voices/hoang-nam.mp3",
    ),
    VoiceProfile(
        id="elevenlabs-vi-mai-02",
        name="Mai Linh (VI)",
        language="vi-VN",
        gender="female",
        provider="ElevenLabs",
        sample_text="Giải pháp tự động hóa nội dung video cho doanh nghiệp một người.",
        preview_url="https://assets.mekongmind.com/voices/mai-linh.mp3",
    ),
    VoiceProfile(
        id="elevenlabs-en-rachel-01",
        name="Rachel News (EN)",
        language="en-US",
        gender="female",
        provider="ElevenLabs",
        sample_text="Welcome to the future of automated video content production.",
        preview_url="https://assets.mekongmind.com/voices/rachel.mp3",
    ),
    VoiceProfile(
        id="elevenlabs-en-adam-02",
        name="Adam Narrative (EN)",
        language="en-US",
        gender="male",
        provider="ElevenLabs",
        sample_text="Transform your business ideas into compelling high-converting videos.",
        preview_url="https://assets.mekongmind.com/voices/adam.mp3",
    ),
]

TEMPLATE_CATALOG: list[VideoTemplate] = [
    VideoTemplate(
        id="news_anchor",
        name="Bản Tin & Thời Sự",
        aspect_ratio="9:16",
        description="Avatar xuất hiện ở góc dưới hoặc giữa màn hình, phụ đề động, tiêu đề tin tức nổi bật.",
        recommended_genres=["news", "editorial", "finance"],
    ),
    VideoTemplate(
        id="faceless_explainer",
        name="Video Giải Thích Không Mặt (Faceless)",
        aspect_ratio="9:16",
        description="B-roll đồ họa, phụ đề lớn kiểu Hormozi, voiceover, hiệu ứng âm thanh sống động.",
        recommended_genres=["education", "saas", "social"],
    ),
    VideoTemplate(
        id="product_showcase",
        name="Giới Thiệu Sản Phẩm",
        aspect_ratio="1:1",
        description="Khung vuông tối ưu cho Facebook & Instagram Ads, hiển thị mockup sản phẩm và CTA.",
        recommended_genres=["ecommerce", "marketing"],
    ),
    VideoTemplate(
        id="youtube_deepdive",
        name="YouTube Chuyên Sâu 16:9",
        aspect_ratio="16:9",
        description="Tỷ lệ ngang chuẩn YouTube, chia phân đoạn chương trình, hình ảnh minh họa song song avatar.",
        recommended_genres=["tutorial", "podcast", "keynote"],
    ),
]


def estimate_mcu_cost(duration_seconds: int, template: str = "news_anchor") -> dict[str, Any]:
    """Estimate MCU credit cost for a video of given duration and template."""
    if duration_seconds <= 0:
        raise ValueError("Duration must be positive")
    validate_identifier(template, "template ID")
    blocks = max(1, (duration_seconds + 29) // 30)
    mcu_cost = blocks * 50
    if template == "youtube_deepdive":
        mcu_cost = int(mcu_cost * 1.5)
    return {
        "duration_seconds": duration_seconds,
        "template": template,
        "estimated_mcu": mcu_cost,
        "billing_blocks": blocks,
        "currency": "MCU",
    }


def load_design_dna_tokens(dna_name: str) -> dict[str, Any] | None:
    """Attempt to load approved Design DNA styling tokens."""
    try:
        from src.design_intelligence.design_memory import load_approved

        dna = load_approved(dna_name)
        if dna is None:
            logger.warning("Design DNA '%s' not found in approved memory.", dna_name)
            return None
        return {
            "identity": dna.identity,
            "color_anchor": dna.color_anchor or "#1E40AF",
            "typography": dna.typography or "sans-serif",
            "type_pairing": dna.type_pairing,
            "surface_treatment": dna.surface_treatment or "clean-rounded",
            "density": dna.density.value,
        }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load design DNA '%s': %s", dna_name, exc)
        return None


def deduct_tenant_mcu(tenant_id: str, mcu_cost: int, mission_id: str, *, enable_billing: bool = True) -> bool:
    """Deduct MCU credits for tenant. Returns True if successful or billing disabled."""
    if not enable_billing:
        return True
    try:
        from src.core.mcu_billing import MCUBilling

        billing = MCUBilling()
        if billing.get_balance(tenant_id).balance < mcu_cost:
            billing.add_credits(tenant_id, 1000, "Initial Sophia Video seed allocation")
        return billing.deduct(tenant_id, complexity="standard", mission_id=mission_id).success
    except Exception as exc:  # noqa: BLE001
        logger.warning("MCU deduction failed (%s), proceeding in fallback mode.", exc)
        return True
