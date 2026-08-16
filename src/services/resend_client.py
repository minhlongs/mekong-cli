# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Resend.com REST API client — stdlib urllib.request only (no new pip deps).

Sends transactional email via POST https://api.resend.com/emails.
Auth: Bearer $RESEND_API_KEY (read at call time; raises RuntimeError if missing).
Sender domain: $MEKONG_MAGIC_LINK_FROM (default: noreply@mekong.dev).
Timeout: 10s. No retry loop — caller decides on failure policy.

Vietnamese email templates are defined inline (VN-only per V1 spec).
"""
from __future__ import annotations

import json
import logging
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
        to: Recipient email address.
        subject: Email subject line (Vietnamese OK).
        html: HTML body (Vietnamese OK — ensure_ascii=False).

    Returns:
        Parsed JSON response dict from Resend (contains 'id' on success).

    Raises:
        RuntimeError: RESEND_API_KEY not set.
        ResendError: Non-2xx HTTP response from Resend API.
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


_VN_MEKONG_HUB = "Mekong Hub — Nền tảng cho doanh nghiệp một người Việt Nam"
_VN_MAGIC_LINK_SENTENCE = (
    "Nếu bạn không yêu cầu liên kết này, hãy bỏ qua email này. "
    "Liên kết chỉ sử dụng được một lần."
)


def send_welcome_email(
    to_email: str, user_name: str, user_id: str, credits: int, pilot_end_at: str
) -> dict[str, Any]:
    """Send Day-1 welcome email to a newly onboarded pilot.

    Args:
        to_email: Recipient address.
        user_name: Display name from signup.
        user_id: Generated user ID (opc_NNN_xxxxxx).
        credits: Initial credit balance (usually 50 free credits).
        pilot_end_at: ISO date when 8-week pilot expires.

    Returns:
        Resend API response dict (contains 'id' on success).
        Silently returns {"id": "skipped"} if RESEND_API_KEY is unset
        (soft-fail — signup must not break without email infra).
    """
    try:
        _api_key()
    except RuntimeError:
        logging.warning(
            "RESEND_API_KEY not set — skipping welcome email to %s", to_email
        )
        return {"id": "skipped"}

    subject = f"Chào mừng {user_name} đến Mekong Hub!"
    pilot_end_fmt = pilot_end_at[:10] if len(pilot_end_at) >= 10 else pilot_end_at
    html = f"""\
<html>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
<h2 style="color: #1a56db;">Chào mừng bạn đến Mekong Hub!</h2>
<p>Xin chào <strong>{user_name}</strong>,</p>
<p>Cảm ơn bạn đã đăng ký dùng thử Mekong Hub! Tài khoản của bạn đã sẵn sàng.</p>

<h3 style="color: #374151;">📋 Thông tin tài khoản</h3>
<ul>
<li><strong>User ID:</strong> <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;">{user_id}</strong></li>
<li><strong>Credit miễn phí:</strong> <strong>{credits} credits</strong></li>
<li><strong>Thời gian dùng thử:</strong> đến <strong>{pilot_end_fmt}</strong> (8 tuần)</li>
</ul>

<h3 style="color: #374151;">🚀 Bắt đầu trong 3 bước</h3>
<ol>
<li><strong>Kết nối Zalo:</strong> Thêm bot Zalo Mekong Hub vào danh bạ + gửi tin nhắn thử</li>
<li><strong>Chọn ngành & loại hình kinh doanh:</strong> AI sẽ tự học phong cách của bạn</li>
<li><strong>Để AI vận hành:</strong> Trả lời khách, tạo content, báo cáo — tất cả tự động</li>
</ol>

<h3 style="color: #374151;">💬 Cần hỗ trợ?</h3>
<p>Gọi / nhắn Zalo: <strong>0977.048.051</strong><br>
Email: <a href="mailto:hello@mekongmind.com">hello@mekongmind.com</a></p>

<p style="color: #6b7280; font-size: 12px;">
{_VN_MAGIC_LINK_SENTENCE}
</p>
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
<p style="color: #9ca3af; font-size: 12px;">{_VN_MEKONG_HUB}</p>
</body>
</html>
"""

    return send_email(to_email, subject, html)


def send_magic_link_email(
    to_email: str, magic_url: str, purpose: str
) -> dict[str, Any]:
    """Send a magic-link email (Vietnamese content).

    Args:
        to_email: Recipient address.
        magic_url: Full verify URL (https://api.mekong.dev/v1/auth/verify?token=...).
        purpose: Token purpose string ("login", "signup", "join_invite").

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


# =============================================================================
# DRIP EMAIL TEMPLATES — Day 3, 7, 14
# =============================================================================
# Each function soft-fails (returns {"id": "skipped"}) if RESEND_API_KEY is unset.
# Vietnamese HTML only (per V1 spec). Stdlib urllib only — no new pip deps.

_VN_SUPPORT_LINE = (
    'Cần hỗ trợ? Zalo <strong>0977.048.051</strong> · '
    '<a href="mailto:hello@mekongmind.com">hello@mekongmind.com</a>'
)


def send_drip_email(
    to_email: str,
    user_name: str,
    user_id: str,
    credits: int,
    drip_day: int,
    business_type: str = "",
    has_outreach_contact: bool = False,
) -> dict[str, Any]:
    """Send a Day-3, Day-7, or Day-14 nurture email to a pilot user.

    drip_day: 3, 7, or 14 — selects the matching template.
    has_outreach_contact: if True, Day-14 email drops the outreach
    CTA section (user has already been contacted by founder).
    Returns Resend API response dict, or {"id": "skipped"} on missing API key.
    Soft-fails — drip triggers never break if email infra is down.
    """
    try:
        _api_key()
    except RuntimeError:
        logging.warning(
            "RESEND_API_KEY not set — skipping drip email day=%d to %s",
            drip_day,
            to_email,
        )
        return {"id": "skipped"}

    if drip_day == 3:
        subject = f"3 ngày đầu với Mekong Hub — tips hay lắm, {user_name}!"
        html = """<html>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
<h2 style="color: #1a56db;">Sử dụng tốt lắm, {name}!</h2>
<p>Đây là ngày thứ <strong>3</strong> bạn dùng Mekong Hub — và chúng tôi có vài tips siêu hữu ích:</p>
<h3 style="color: #374151;">💡 Mẹo cho ngày thứ 3</h3>
<ol>
<li><strong>Tự động hóa Zalo:</strong> Đặt câu trả lời tự động cho 3 câu hỏi khách hỏi nhiều nhất (giá, địa chỉ, giờ mở cửa).</li>
<li><strong>Content calendar:</strong> Dùng AI tạo 1 tuần content trong 5 phút — chỉ việc duyệt và đăng.</li>
<li><strong>CRM tagging:</strong> Đánh dấu "Hot lead" cho khách quan tâm — AI sẽ nhắc bạn follow-up sau 24h.</li>
</ol>
<h3 style="color: #374151;">📊 Theo dõi tiến độ</h3>
<p>Kiểm tra bao nhiêu credit bạn đã dùng tại <code>Zalo Bot → /status</code>.</p>
<p style="color: #6b7280; font-size: 13px;">Còn {credits} credits — bạn dùng được khoảng <strong>{uses} câu hỏi AI</strong> nữa.</p>
<p>{support}</p>
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
<p style="color: #9ca3af; font-size: 12px;">{hub_tag}</p>
</body>
</html>
""".format(
            name=user_name,
            credits=credits,
            uses=credits // 5,
            support=_VN_SUPPORT_LINE,
            hub_tag=_VN_MEKONG_HUB,
        )

    elif drip_day == 7:
        subject = "Tuần 1 với Mekong Hub — bạn đã làm được gì?"
        html = """<html>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
<h2 style="color: #1a56db;">Báo cáo tuần 1 — {name}</h2>
<p>Chúc mừng! Bạn đã dùng Mekong Hub được <strong>1 tuần</strong>. Hãy cùng xem lại:</p>
<h3 style="color: #374151;">📈 Bạn đã đạt được gì?</h3>
<ul>
<li>Khách được AI trả lời tự động: <strong>_____</strong> lần</li>
<li>Content được AI tạo: <strong>_____</strong> bài</li>
<li>Lead được CRM ghi nhận: <strong>_____</strong> khách</li>
</ul>
<p style="color: #6b7280; font-size: 13px;">Điền số vào chỗ trống, gửi lại email này cho chúng tôi — chúng tôi sẽ đưa ra feedback cá nhân hóa.</p>
<h3 style="color: #374151;">🎯 Muốn nâng cấp?</h3>
<p>Sau 8 tuần dùng thử, bạn sẽ có thể chuyển sang gói trả phí từ <strong>199K VND/tháng</strong>. Liên hệ để được tư vấn gói phù hợp.</p>
<p style="color: #6b7280; font-size: 13px;">Credits còn lại: <strong>{credits}</strong></p>
<p>{support}</p>
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
<p style="color: #9ca3af; font-size: 12px;">{hub_tag}</p>
</body>
</html>
""".format(
            name=user_name,
            credits=credits,
            support=_VN_SUPPORT_LINE,
            hub_tag=_VN_MEKONG_HUB,
        )

    elif drip_day == 14:
        subject = "Đã gặp khó khăn gì không? Hỗ trợ 1:1 luôn sẵn"

        outreach_section = ""
        if not has_outreach_contact:
            outreach_section = """
<h3 style="color: #374151;">📱 Bạn muốn tư vấn trực tiếp?</h3>
<p>Nhắn Zalo <strong>0977.048.051</strong> — team Mekong Hub sẽ setup 1:1 cùng bạn, miễn phí trong 15 phút.</p>
"""

        html = """<html>
<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">
<h2 style="color: #1a56db;">Hai tuần với Mekong Hub — chúng ta cải thiện gì?</h2>
<p>Xin chào <strong>{name}</strong>,</p>
<p>Bạn đã dùng Mekong Hub được <strong>2 tuần</strong>. Chúng tôi muốn hỏi:</p>
<h3 style="color: #374151;">⭐ Trải nghiệm của bạn thế nào?</h3>
<p>Đánh giá 1-5 sao và gửi phản hồi — giúp chúng tôi cải thiện sản phẩm:</p>
<p style="margin: 16px 0;">
<a href="https://api.mekongmind.com/v1/pilot/response"
style="background-color: #16a34a; color: white; padding: 10px 20px;
text-decoration: none; border-radius: 6px; display: inline-block;">
Đánh giá ngay
</a>
</p>
""" + outreach_section + """
<h3 style="color: #374151;">🙋 Hỗ trợ 1:1 miễn phí</h3>
<p>Nếu bạn gặp khó khăn — nhắn Zalo <strong>0977.048.051</strong>, chúng tôi sẽ setup cùng bạn trong 15 phút.</p>
<p style="color: #6b7280; font-size: 13px;">Credits: <strong>{credits}</strong> · Thời gian dùng thử còn: ~<strong>6 tuần</strong></p>
<p>{support}</p>
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />
<p style="color: #9ca3af; font-size: 12px;">{hub_tag}</p>
</body>
</html>
""".format(
            credits=credits,
            support=_VN_SUPPORT_LINE,
            hub_tag=_VN_MEKONG_HUB,
        )

    else:
        raise ValueError(f"drip_day must be 3, 7, or 14 — got {drip_day}")

    return send_email(to_email, subject, html)
