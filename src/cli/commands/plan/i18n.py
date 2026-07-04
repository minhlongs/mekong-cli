"""i18n strings for plan CLI."""

from __future__ import annotations


def get_messages(locale: str) -> dict[str, str]:
    if locale == "vi":
        return {
            "no_company": "Không tìm thấy .mekong/company.json. Chạy `mekong company init` trước.",
            "already_setup": "Đã khởi tạo. Dùng --force để ghi đè.",
            "plan_generated": "Đã tạo kế hoạch.",
        }
    return {
        "no_company": ".mekong/company.json not found. Run `mekong company init` first.",
        "already_setup": "Already initialized. Use --force to overwrite.",
        "plan_generated": "Plan generated.",
    }
