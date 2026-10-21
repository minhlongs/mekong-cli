# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Vietnamese HTML email templates for Resend (welcome, magic-link, and Day 3/7/14 drip)."""
from __future__ import annotations

import logging
from typing import Any

_VN_MEKONG_HUB = "Mekong Hub — Nền tảng cho doanh nghiệp một người Việt Nam"
_VN_MAGIC_LINK_SENTENCE = (
    "Nếu bạn không yêu cầu liên kết này, hãy bỏ qua email này. "
    "Liên kết chỉ sử dụng được một lần."
)
_VN_SUPPORT_LINE = (
    'Cần hỗ trợ? Zalo <strong>0977.048.051</strong> · '
    '<a href="mailto:hello@mekongmind.com">hello@mekongmind.com</a>'
)


def _client():
    import src.services.resend_client as _rc

    return _rc


def send_welcome_email(
    to_email: str, user_name: str, user_id: str, credits: int, pilot_end_at: str
) -> dict[str, Any]:
    """Send Day-1 welcome email to a newly onboarded pilot."""
    rc = _client()
    try:
        rc._api_key()
    except RuntimeError:
        logging.warning("RESEND_API_KEY not set — skipping welcome email to %s", to_email)
        return {"id": "skipped"}

    subject = f"Chào mừng {user_name} đến Mekong Hub!"
    pilot_end_fmt = pilot_end_at[:10] if len(pilot_end_at) >= 10 else pilot_end_at
    html = (
        '<html>\n<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">\n'
        '<h2 style="color: #1a56db;">Chào mừng bạn đến Mekong Hub!</h2>\n'
        f"<p>Xin chào <strong>{user_name}</strong>,</p>\n"
        "<p>Cảm ơn bạn đã đăng ký dùng thử Mekong Hub! Tài khoản của bạn đã sẵn sàng.</p>\n\n"
        '<h3 style="color: #374151;">📋 Thông tin tài khoản</h3>\n<ul>\n'
        f'<li><strong>User ID:</strong> <code style="background:#f3f4f6;padding:2px 6px;border-radius:4px;">{user_id}</strong></li>\n'
        f"<li><strong>Credit miễn phí:</strong> <strong>{credits} credits</strong></li>\n"
        f"<li><strong>Thời gian dùng thử:</strong> đến <strong>{pilot_end_fmt}</strong> (8 tuần)</li>\n</ul>\n\n"
        '<h3 style="color: #374151;">🚀 Bắt đầu trong 3 bước</h3>\n<ol>\n'
        "<li><strong>Kết nối Zalo:</strong> Thêm bot Zalo Mekong Hub vào danh bạ + gửi tin nhắn thử</li>\n"
        "<li><strong>Chọn ngành & loại hình kinh doanh:</strong> AI sẽ tự học phong cách của bạn</li>\n"
        "<li><strong>Để AI vận hành:</strong> Trả lời khách, tạo content, báo cáo — tất cả tự động</li>\n</ol>\n\n"
        '<h3 style="color: #374151;">💬 Cần hỗ trợ?</h3>\n'
        "<p>Gọi / nhắn Zalo: <strong>0977.048.051</strong><br>\n"
        'Email: <a href="mailto:hello@mekongmind.com">hello@mekongmind.com</a></p>\n\n'
        f'<p style="color: #6b7280; font-size: 12px;">\n{_VN_MAGIC_LINK_SENTENCE}\n</p>\n'
        '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
        f'<p style="color: #9ca3af; font-size: 12px;">{_VN_MEKONG_HUB}</p>\n'
        "</body>\n</html>\n"
    )
    return rc.send_email(to_email, subject, html)


def send_magic_link_email(to_email: str, magic_url: str, purpose: str) -> dict[str, Any]:
    """Send a magic-link email (Vietnamese content)."""
    rc = _client()
    purpose_label = {
        "login": "đăng nhập",
        "signup": "đăng ký",
        "join_invite": "tham gia tổ chức",
    }.get(purpose, purpose)

    subject = f"Liên kết {purpose_label} Mekong Hub của bạn"
    html = (
        '<html>\n<body style="font-family: Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 24px;">\n'
        '<h2 style="color: #1a56db;">Mekong Hub</h2>\n<p>Xin chào,</p>\n'
        f"<p>Nhấp vào liên kết bên dưới để {purpose_label}. Liên kết có hiệu lực trong <strong>15 phút</strong>:</p>\n"
        '<p style="margin: 24px 0;">\n'
        f'<a href="{magic_url}"\n'
        'style="background-color: #1a56db; color: white; padding: 12px 24px;\n'
        'text-decoration: none; border-radius: 6px; display: inline-block;">\n'
        f"{purpose_label.capitalize()}\n</a>\n</p>\n"
        '<p style="color: #6b7280; font-size: 14px;">\n'
        f'Hoặc copy URL: <code style="word-break: break-all;">{magic_url}</code>\n</p>\n'
        '<p style="color: #6b7280; font-size: 13px;">\n'
        "Nếu bạn không yêu cầu liên kết này, hãy bỏ qua email này.\n"
        "Liên kết chỉ sử dụng được một lần.\n</p>\n"
        '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
        '<p style="color: #9ca3af; font-size: 12px;">Mekong Hub — Nền tảng cho doanh nghiệp một người Việt Nam</p>\n'
        "</body>\n</html>"
    )
    return rc.send_email(to_email, subject, html)


def send_drip_email(
    to_email: str,
    user_name: str,
    user_id: str,
    credits: int,
    drip_day: int,
    business_type: str = "",
    has_outreach_contact: bool = False,
) -> dict[str, Any]:
    """Send a Day-3, Day-7, or Day-14 nurture email to a pilot user."""
    rc = _client()
    try:
        rc._api_key()
    except RuntimeError:
        logging.warning("RESEND_API_KEY not set — skipping drip email day=%d to %s", drip_day, to_email)
        return {"id": "skipped"}

    if drip_day == 3:
        subject = f"3 ngày đầu với Mekong Hub — tips hay lắm, {user_name}!"
        html = (
            '<html>\n<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">\n'
            f'<h2 style="color: #1a56db;">Sử dụng tốt lắm, {user_name}!</h2>\n'
            "<p>Đây là ngày thứ <strong>3</strong> bạn dùng Mekong Hub — và chúng tôi có vài tips siêu hữu ích:</p>\n"
            '<h3 style="color: #374151;">💡 Mẹo cho ngày thứ 3</h3>\n<ol>\n'
            "<li><strong>Tự động hóa Zalo:</strong> Đặt câu trả lời tự động cho 3 câu hỏi khách hỏi nhiều nhất (giá, địa chỉ, giờ mở cửa).</li>\n"
            "<li><strong>Content calendar:</strong> Dùng AI tạo 1 tuần content trong 5 phút — chỉ việc duyệt và đăng.</li>\n"
            '<li><strong>CRM tagging:</strong> Đánh dấu "Hot lead" cho khách quan tâm — AI sẽ nhắc bạn follow-up sau 24h.</li>\n</ol>\n'
            '<h3 style="color: #374151;">📊 Theo dõi tiến độ</h3>\n'
            "<p>Kiểm tra bao nhiêu credit bạn đã dùng tại <code>Zalo Bot → /status</code>.</p>\n"
            f'<p style="color: #6b7280; font-size: 13px;">Còn {credits} credits — bạn dùng được khoảng <strong>{credits // 5} câu hỏi AI</strong> nữa.</p>\n'
            f"<p>{_VN_SUPPORT_LINE}</p>\n"
            '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
            f'<p style="color: #9ca3af; font-size: 12px;">{_VN_MEKONG_HUB}</p>\n</body>\n</html>\n'
        )
    elif drip_day == 7:
        subject = "Tuần 1 với Mekong Hub — bạn đã làm được gì?"
        html = (
            '<html>\n<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">\n'
            f'<h2 style="color: #1a56db;">Báo cáo tuần 1 — {user_name}</h2>\n'
            "<p>Chúc mừng! Bạn đã dùng Mekong Hub được <strong>1 tuần</strong>. Hãy cùng xem lại:</p>\n"
            '<h3 style="color: #374151;">📈 Bạn đã đạt được gì?</h3>\n<ul>\n'
            "<li>Khách được AI trả lời tự động: <strong>_____</strong> lần</li>\n"
            "<li>Content được AI tạo: <strong>_____</strong> bài</li>\n"
            "<li>Lead được CRM ghi nhận: <strong>_____</strong> khách</li>\n</ul>\n"
            '<p style="color: #6b7280; font-size: 13px;">Điền số vào chỗ trống, gửi lại email này cho chúng tôi — chúng tôi sẽ đưa ra feedback cá nhân hóa.</p>\n'
            '<h3 style="color: #374151;">🎯 Muốn nâng cấp?</h3>\n'
            "<p>Sau 8 tuần dùng thử, bạn sẽ có thể chuyển sang gói trả phí từ <strong>199K VND/tháng</strong>. Liên hệ để được tư vấn gói phù hợp.</p>\n"
            f'<p style="color: #6b7280; font-size: 13px;">Credits còn lại: <strong>{credits}</strong></p>\n'
            f"<p>{_VN_SUPPORT_LINE}</p>\n"
            '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
            f'<p style="color: #9ca3af; font-size: 12px;">{_VN_MEKONG_HUB}</p>\n</body>\n</html>\n'
        )
    elif drip_day == 14:
        subject = "Đã gặp khó khăn gì không? Hỗ trợ 1:1 luôn sẵn"
        outreach_section = (
            '\n<h3 style="color: #374151;">📱 Bạn muốn tư vấn trực tiếp?</h3>\n'
            "<p>Nhắn Zalo <strong>0977.048.051</strong> — team Mekong Hub sẽ setup 1:1 cùng bạn, miễn phí trong 15 phút.</p>\n"
            if not has_outreach_contact
            else ""
        )
        html = (
            '<html>\n<body style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px;">\n'
            '<h2 style="color: #1a56db;">Hai tuần với Mekong Hub — chúng ta cải thiện gì?</h2>\n'
            f"<p>Xin chào <strong>{user_name}</strong>,</p>\n"
            "<p>Bạn đã dùng Mekong Hub được <strong>2 tuần</strong>. Chúng tôi muốn hỏi:</p>\n"
            '<h3 style="color: #374151;">⭐ Trải nghiệm của bạn thế nào?</h3>\n'
            "<p>Đánh giá 1-5 sao và gửi phản hồi — giúp chúng tôi cải thiện sản phẩm:</p>\n"
            '<p style="margin: 16px 0;">\n<a href="https://api.mekongmind.com/v1/pilot/response"\n'
            'style="background-color: #16a34a; color: white; padding: 10px 20px;\n'
            'text-decoration: none; border-radius: 6px; display: inline-block;">\nĐánh giá ngay\n</a>\n</p>\n'
            f"{outreach_section}\n"
            '<h3 style="color: #374151;">🙋 Hỗ trợ 1:1 miễn phí</h3>\n'
            "<p>Nếu bạn gặp khó khăn — nhắn Zalo <strong>0977.048.051</strong>, chúng tôi sẽ setup cùng bạn trong 15 phút.</p>\n"
            f'<p style="color: #6b7280; font-size: 13px;">Credits: <strong>{credits}</strong> · Thời gian dùng thử còn: ~<strong>6 tuần</strong></p>\n'
            f"<p>{_VN_SUPPORT_LINE}</p>\n"
            '<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;" />\n'
            f'<p style="color: #9ca3af; font-size: 12px;">{_VN_MEKONG_HUB}</p>\n</body>\n</html>\n'
        )
    else:
        raise ValueError(f"drip_day must be 3, 7, or 14 — got {drip_day}")

    return rc.send_email(to_email, subject, html)
