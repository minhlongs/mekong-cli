"""Resend.com REST API client — stdlib urllib.request only (no new pip deps).

Sends transactional email via POST https://api.resend.com/emails.
Auth: Bearer $RESEND_API_KEY (read at call time; raises RuntimeError if missing).
Sender domain: $MEKONG_MAGIC_LINK_FROM (default: noreply@mekong.dev).
Timeout: 10s. No retry loop — caller decides on failure policy.

Vietnamese email templates are defined inline (VN-only per V1 spec).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

_RESEND_API_URL = "https://api.resend.com/emails"
_DEFAULT_FROM = "noreply@mekong.dev"
_TIMEOUT_SECONDS = 10


class ResendError(Exception):
    """Raised on non-2xx Resend API response."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Resend API error {status_code}: {body}")


def _api_key() -> str:
    """Read RESEND_API_KEY at call time. Raises RuntimeError if unset."""
    key = os.getenv("RESEND_API_KEY")
    if not key:
        raise RuntimeError(
            "RESEND_API_KEY env var is required to send email. "
            "Set it in your launchd plist EnvironmentVariables."
        )
    return key


def _from_address() -> str:
    return os.getenv("MEKONG_MAGIC_LINK_FROM", _DEFAULT_FROM)


def send_email(to: str, subject: str, html: str) -> dict[str, Any]:
    """POST one email to Resend REST API.

    Args:
        to:      Recipient email address.
        subject: Email subject line (Vietnamese OK).
        html:    HTML body (Vietnamese OK — ensure_ascii=False).

    Returns:
        Parsed JSON response dict from Resend (contains 'id' on success).

    Raises:
        RuntimeError: RESEND_API_KEY not set.
        ResendError:  Non-2xx HTTP response from Resend API.
        urllib.error.URLError: Network/timeout failure.
    """
    api_key = _api_key()
    payload = {
        "from": _from_address(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=_RESEND_API_URL,
        data=body_bytes,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else ""
        raise ResendError(exc.code, error_body) from exc


def send_magic_link_email(to_email: str, magic_url: str, purpose: str) -> dict[str, Any]:
    """Send a magic-link email (Vietnamese content).

    Args:
        to_email:  Recipient address.
        magic_url: Full verify URL (https://api.mekong.dev/v1/auth/verify?token=...).
        purpose:   Token purpose string ("login", "signup", "join_invite").

    Returns:
        Resend API response dict.
    """
    purpose_label = {
        "login": "đăng nhập",
        "signup": "đăng ký",
        "join_invite": "tham gia tổ chức",
    }.get(purpose, purpose)

    subject = f"Liên kết {purpose_label} Mekong Hub của bạn"
    html = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #1a56db;">Mekong Hub</h2>
  <p>Xin chào,</p>
  <p>Nhấp vào liên kết bên dưới để {purpose_label}. Liên kết có hiệu lực trong <strong>15 phút</strong>:</p>
  <p style="margin: 24px 0;">
    <a href="{magic_url}"
       style="background-color: #1a56db; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 6px; display: inline-block;">
      {purpose_label.capitalize()}
    </a>
  </p>
  <p style="color: #6b7280; font-size: 14px;">
    Hoặc copy URL: <code style="word-break: break-all;">{magic_url}</code>
  </p>
  <p style="color: #6b7280; font-size: 13px;">
    Nếu bạn không yêu cầu liên kết này, hãy bỏ qua email này.
    Liên kết chỉ sử dụng được một lần.
  </p>
  <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
  <p style="color: #9ca3af; font-size: 12px;">Mekong Hub — Nền tảng cho doanh nghiệp một người Việt Nam</p>
</body>
</html>
""".strip()
    return send_email(to_email, subject, html)
