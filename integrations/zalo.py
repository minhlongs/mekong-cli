"""
Zalo OA API client — Broadcast, followers, article posting.
Docs: https://developers.zalo.me/docs/api/official-account-api
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

ZALO_OA_API = "https://openapi.zalo.me/v2.0/oa"
RATE_LIMIT_BROADCAST = 20  # req/min


@dataclass
class ZaloMessage:
    recipient_id: str
    text: str
    message_type: str = "text"  # text|template|image


class ZaloOAClient:
    """Client cho Zalo Official Account API."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> None:
        self.access_token = access_token or os.getenv("ZALO_OA_ACCESS_TOKEN", "")
        self.app_id = app_id or os.getenv("ZALO_APP_ID", "")
        self._session = None

    def _get_session(self):
        if requests is None:
            raise ImportError("requests not installed: pip install requests")
        if self._session is None:
            import requests as req
            self._session = req.Session()
            self._session.headers.update({
                "access_token": self.access_token,
                "Content-Type": "application/json",
            })
        return self._session

    def get_followers(self, offset: int = 0, count: int = 50) -> dict[str, Any]:
        """Lấy danh sách followers."""
        session = self._get_session()
        resp = session.get(
            f"{ZALO_OA_API}/getfollowers",
            params={"data": f'{{"offset":{offset},"count":{count}}}'},
        )
        resp.raise_for_status()
        return resp.json()

    def send_message(self, recipient_id: str, text: str) -> dict[str, Any]:
        """Gửi tin nhắn đến 1 follower."""
        session = self._get_session()
        payload = {
            "recipient": {"user_id": recipient_id},
            "message": {"text": text},
        }
        resp = session.post(f"{ZALO_OA_API}/message", json=payload)
        resp.raise_for_status()
        return resp.json()

    def broadcast(self, text: str) -> dict[str, Any]:
        """Broadcast tin nhắn đến tất cả followers (requires OA verified)."""
        session = self._get_session()
        payload = {"message": {"text": text}}
        resp = session.post(f"{ZALO_OA_API}/broadcast/message", json=payload)
        resp.raise_for_status()
        return resp.json()

    def post_article(self, title: str, content: str, cover_image: str = "") -> dict[str, Any]:
        """Đăng bài viết trên OA timeline."""
        session = self._get_session()
        payload = {
            "title": title,
            "description": content[:100],
            "content": content,
            "cover": cover_image,
        }
        resp = session.post(f"{ZALO_OA_API}/article", json=payload)
        resp.raise_for_status()
        return resp.json()

    def is_configured(self) -> bool:
        return bool(self.access_token and self.app_id)


def generate_vn_caption(product: str, tone: str = "than_thien") -> str:
    """Tạo caption Zalo OA cơ bản (offline, không cần AI call)."""
    tone_templates = {
        "than_thien": (
            f"🌟 Giới thiệu {product} — sản phẩm hot nhất hôm nay!\n\n"
            f"✅ Chất lượng đảm bảo\n"
            f"✅ Giao hàng nhanh toàn quốc\n"
            f"✅ Giá tốt nhất thị trường\n\n"
            f"📱 Nhắn tin ngay để được tư vấn miễn phí! 👇\n\n"
            f"#muasam #{product.replace(' ', '').lower()} #shopviet"
        ),
        "chuyen_nghiep": (
            f"Sản phẩm {product} — Giải pháp chuyên nghiệp cho nhu cầu của bạn.\n\n"
            f"• Chất lượng cam kết\n"
            f"• Hỗ trợ 24/7\n"
            f"• Bảo hành chính hãng\n\n"
            f"Liên hệ ngay để nhận báo giá. #{product.replace(' ', '').lower()}"
        ),
        "vui_ve": (
            f"Hey hey! 🎉 {product} đây nè!\n\n"
            f"Tại sao chọn mình? Vì mình XỊN! 😄\n"
            f"- Siêu ngon\n"
            f"- Siêu rẻ\n"
            f"- Ship siêu nhanh!\n\n"
            f"DM ngay nha! Đừng bỏ lỡ!! 🔥\n"
            f"#{product.replace(' ', '').lower()} #deal #hot"
        ),
    }
    return tone_templates.get(tone, tone_templates["than_thien"])
