# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""i18n strings for plan CLI."""

from __future__ import annotations

_VI: dict[str, str] = {
    "no_company": "Không tìm thấy .mekong/company.json. Chạy `mekong company init` trước.",
    "already_setup": "Đã khởi tạo. Dùng --force để ghi đè.",
    "plan_generated": "Đã tạo kế hoạch.",
    "no_domains": "Không có outline lĩnh vực cho product_type này.",
    "missing_company": "Vui lòng chạy `mekong company init` trước.",
    "plans_conflict": "Thư mục plans/ đã có nội dung. Dùng --force để ghi đè.",
    "spec_overwrite_warn": "SPEC_OUTPUT.md đã tồn tại. Dùng --force để ghi đè.",
    "build_tasks_ready": "Đã tạo danh sách công việc build.",
}

_EN: dict[str, str] = {
    "no_company": ".mekong/company.json not found. Run `mekong company init` first.",
    "already_setup": "Already initialized. Use --force to overwrite.",
    "plan_generated": "Plan generated.",
    "no_domains": "No domain outline available for this product type.",
    "missing_company": "Run `mekong company init` first.",
    "plans_conflict": "plans/ already has content. Use --force to overwrite.",
    "spec_overwrite_warn": "SPEC_OUTPUT.md already exists. Use --force to overwrite.",
    "build_tasks_ready": "Build task list generated.",
}

MESSAGES = {"en": _EN, "vi": _VI}

_EXTRA_VI = {
    "invalid_lang": "Giá trị --lang không hợp lệ: {lang}. Dùng en | vi.",
    "no_domains_hint": "Không có outline cho product_type '{product_type}'. Dùng mặc định.",
    "spec_exists": "SPEC_OUTPUT.md đã tồn tại tại {path}. Dùng --force để ghi đè.",
    "plans_exist": "Thư mục plans/ đã có nội dung. Dùng --force để ghi đè.",
    "plan_generated_title": "Đã tạo kế hoạch / Plan Generated",
}
_EXTRA_EN = {
    "invalid_lang": "Invalid --lang: {lang}. Use en | vi.",
    "no_domains_hint": "No domain outline for product_type '{product_type}'. Using generic.",
    "spec_exists": "SPEC_OUTPUT.md already exists at {path}. Use --force to overwrite.",
    "plans_exist": "plans/ directory already has content. Use --force to overwrite.",
    "plan_generated_title": "Plan Generated",
}
for _k, _v in _EXTRA_VI.items():
    _VI.setdefault(_k, _v)
for _k, _v in _EXTRA_EN.items():
    _EN.setdefault(_k, _v)

def get_messages(locale: str) -> dict[str, str]:
    locale = locale if locale in ("en", "vi") else "en"
    return MESSAGES.get(locale, _EN)

DEFAULT_LOCALE = "en"

def t(locale: str, key: str, default: str = "") -> str:
    return get_messages(locale).get(key) or get_messages(DEFAULT_LOCALE).get(key) or default
