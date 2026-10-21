# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain outlines and phase definitions for `mekong plan from-init`."""

from __future__ import annotations

_DOMAIN_OUTLINES: dict[str, dict[str, list[str]]] = {
    "saas": {
        "en": [
            "User authentication & authorization (SSO, RBAC)",
            "Subscription billing & invoicing (Stripe / NOWPayments / PayOS)",
            "REST / GraphQL API layer with rate limiting",
            "Usage analytics & quota enforcement",
            "Admin dashboard & team management",
            "Email notification pipeline",
            "Audit log & compliance reporting",
        ],
        "vi": [
            "Xác thực & ủy quyền người dùng (SSO, RBAC)",
            "Thanh toán đăng ký & hóa đơn (Stripe / NOWPayments / PayOS)",
            "API REST / GraphQL với giới hạn tần suất",
            "Phân tích sử dụng & kiểm tra hạn mức",
            "Bảng điều khiển quản trị & quản lý nhóm",
            "Pipeline thông báo email",
            "Nhật ký kiểm toán & báo cáo tuân thủ",
        ],
    },
    "ecommerce": {
        "en": [
            "Product catalog & inventory management",
            "Shopping cart & checkout flow",
            "Payment gateway integration (multiple providers)",
            "Order management & fulfillment tracking",
            "Customer accounts & order history",
            "Discount / coupon system",
            "Shipping rate calculation & tracking",
            "SEO & product feed",
        ],
        "vi": [
            "Danh mục sản phẩm & quản lý tồn kho",
            "Giỏ hàng & luồng thanh toán",
            "Tích hợp cổng thanh toán (nhiều nhà cung cấp)",
            "Quản lý đơn hàng & theo dõi thực hiện",
            "Tài khoản khách hàng & lịch sử đơn hàng",
            "Hệ thống giảm giá / mã coupon",
            "Tính toán & theo dõi cước vận chuyển",
            "SEO & nguồn cấp sản phẩm",
        ],
    },
    "digital": {
        "en": [
            "Content management (CRUD for digital assets)",
            "File storage & delivery (CDN / R2)",
            "Subscription access control (tier gating)",
            "Download & streaming serving",
            "User library / collection management",
            "Payment & license key delivery",
            "Content versioning & updates",
        ],
        "vi": [
            "Quản lý nội dung (CRUD cho tài sản số)",
            "Lưu trữ & phân phối tệp (CDN / R2)",
            "Kiểm soát truy cập đăng ký (tier gating)",
            "Dịch vụ tải xuống & phát trực tuyến",
            "Thư viện / quản lý bộ sưu tập người dùng",
            "Giao hàng thanh toán & khóa bản quyền",
            "Phiên bản & cập nhật nội dung",
        ],
    },
    "api_service": {
        "en": [
            "OpenAPI / AsyncAPI spec design",
            "API gateway & rate limiting",
            "SDK generation (Python, Node, Go)",
            "Usage metering & billing per call",
            "Webhook delivery system",
            "Developer portal & API key management",
            "SLA monitoring & uptime reporting",
        ],
        "vi": [
            "Thiết kế spec OpenAPI / AsyncAPI",
            "Cổng API & giới hạn tần suất",
            "Tạo SDK (Python, Node, Go)",
            "Đo lường sử dụng & thanh toán theo lời gọi",
            "Hệ thống giao webhook",
            "Cổng nhà phát triển & quản lý API key",
            "Giám sát SLA & báo cáo thời gian hoạt động",
        ],
    },
    "consulting": {
        "en": [
            "Client profile & engagement management",
            "Proposal generation & e-signature",
            "Scheduling & calendar integration",
            "Project tracking & milestone reporting",
            "Time tracking & invoicing",
            "Knowledge base & resource library",
            "Client portal & progress dashboard",
        ],
        "vi": [
            "Hồ sơ khách hàng & quản lý hợp tác",
            "Tạo đề xuất & chữ ký điện tử",
            "Lên lịch & tích hợp lịch",
            "Theo dõi dự án & báo cáo cột mốc",
            "Theo dõi thời gian & hóa đơn",
            "Cơ sở tri thức & thư viện tài nguyên",
            "Cổng khách hàng & bảng theo dõi tiến độ",
        ],
    },
}

_PHASES: dict[str, dict[str, dict[str, str]]] = {
    "research": {
        "en": {"title": "Research", "acceptance": "Requirements documented; tech stack chosen"},
        "vi": {"title": "Nghiên cứu", "acceptance": "Yêu cầu được lưu; stack công nghệ đã chọn"},
    },
    "implement": {
        "en": {"title": "Implement", "acceptance": "All features pass lint, type-check, unit tests"},
        "vi": {"title": "Triển khai", "acceptance": "Tính năng pass lint, type-check, unit test"},
    },
    "test": {
        "en": {"title": "Test", "acceptance": "Test coverage >= 80%; CI green"},
        "vi": {"title": "Kiểm thử", "acceptance": "Độ phủ test >= 80%; CI xanh"},
    },
    "review": {
        "en": {"title": "Review", "acceptance": "Code reviewed; security audit passed"},
        "vi": {"title": "Đánh giá", "acceptance": "Code đã review; kiểm tra bảo mật pass"},
    },
    "deploy": {
        "en": {"title": "Deploy", "acceptance": "Production deploy green; SHA verified"},
        "vi": {"title": "Triển khai", "acceptance": "Triển khai production xanh; SHA đã xác minh"},
    },
}


def _domain_outlines(product_type: str, lang: str) -> list[str]:
    return _DOMAIN_OUTLINES.get(product_type, {}).get(
        lang, _DOMAIN_OUTLINES.get(product_type, {}).get("en", [])
    )
