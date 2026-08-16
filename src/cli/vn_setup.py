# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
VN Onboarding Wizard — interactive setup cho 10 OPC pilot users.
Hỏi 4 câu, ghi config vào ~/.mekong/vn_config.json, gợi ý command packs theo ngành.

Usage:
    python -m src.cli.vn_setup
    mekong setup-vn         # (after wrapper integration)
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

CONFIG_DIR = Path.home() / ".mekong"
CONFIG_FILE = CONFIG_DIR / "vn_config.json"

BUSINESS_TYPES = {
    "1": ("shop_online", "Shop online (Shopee/TikTok/Lazada/Facebook)"),
    "2": ("freelancer", "Freelancer (thiết kế, content, IT)"),
    "3": ("cafe_fnb", "Quán cà phê / F&B nhỏ"),
    "4": ("giao_vien", "Gia sư / Giáo viên tự do"),
    "5": ("dich_vu", "Dịch vụ sửa chữa / Tư vấn"),
    "6": ("ho_kinh_doanh", "Hộ kinh doanh truyền thống"),
    "7": ("opc", "Công ty 1 thành viên (OPC)"),
}

CITIES = {
    "1": ("HCM", "TP. Hồ Chí Minh"),
    "2": ("HN", "Hà Nội"),
    "3": ("DN", "Đà Nẵng"),
    "4": ("CT", "Cần Thơ"),
    "5": ("HP", "Hải Phòng"),
    "6": ("OTHER", "Tỉnh/thành khác"),
}

BANKS = {
    "1": ("VCB", "Vietcombank"),
    "2": ("TCB", "Techcombank"),
    "3": ("ACB", "ACB"),
    "4": ("MB", "MB Bank"),
    "5": ("VTB", "VietinBank"),
    "6": ("BIDV", "BIDV"),
    "7": ("VPB", "VPBank"),
    "8": ("OTHER", "Ngân hàng khác"),
}

RECOMMENDED_PACKS = {
    "shop_online": ["ke-toan", "zalo-oa", "vietqr", "marketing-vn"],
    "freelancer": ["ke-toan", "thue-dnvn", "phap-ly-vn"],
    "cafe_fnb": ["ke-toan", "vietqr", "van-hanh-vn", "marketing-vn"],
    "giao_vien": ["ke-toan", "vietqr", "kinh-doanh-vn"],
    "dich_vu": ["ke-toan", "thue-dnvn", "bhxh"],
    "ho_kinh_doanh": ["ke-toan", "thue-dnvn", "vietqr"],
    "opc": ["ke-toan", "thue-dnvn", "phap-ly-vn", "bhxh", "tai-chinh-vn"],
}


@dataclass
class VNConfig:
    business_type: str
    business_type_label: str
    city: str
    city_label: str
    bank: str
    bank_label: str
    industry: Optional[str] = None
    recommended_commands: Optional[list[str]] = None
    onboarded_at: Optional[str] = None
    lang: str = "vi"

    def to_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


def _print_menu(title: str, options: dict[str, tuple[str, str]]) -> None:
    print(f"\n{title}")
    for key, (_, label) in options.items():
        print(f"  [{key}] {label}")


def _prompt_choice(
    title: str,
    options: dict[str, tuple[str, str]],
    default: str = "1",
) -> tuple[str, str]:
    _print_menu(title, options)
    while True:
        raw = input(f"Chọn [{default}]: ").strip() or default
        if raw in options:
            return options[raw]
        print(f"⚠️  Lựa chọn không hợp lệ: {raw}. Vui lòng nhập 1-{len(options)}.")


def _prompt_text(title: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{title}{suffix}: ").strip()
    return raw or default


def run_wizard(interactive: bool = True) -> VNConfig:
    """Chạy wizard. Trả về VNConfig đã ghi đĩa."""
    print("=" * 60)
    print("  🇻🇳  MEKONG AI — Cài Đặt Tiếng Việt")
    print("  Dành cho 1 triệu doanh nghiệp 1 người Việt Nam")
    print("=" * 60)

    if not interactive:
        # Default config for CI / non-tty runs
        biz = BUSINESS_TYPES["1"]
        city = CITIES["1"]
        bank = BANKS["1"]
        industry = "default"
    else:
        biz = _prompt_choice("Loại hình kinh doanh của bạn?", BUSINESS_TYPES)
        city = _prompt_choice("Tỉnh/Thành phố?", CITIES)
        bank = _prompt_choice("Ngân hàng chính?", BANKS)
        industry = _prompt_text("Ngành cụ thể (vd: thời trang, IT, F&B)", default="")

    from datetime import datetime, timezone

    config = VNConfig(
        business_type=biz[0],
        business_type_label=biz[1],
        city=city[0],
        city_label=city[1],
        bank=bank[0],
        bank_label=bank[1],
        industry=industry or None,
        recommended_commands=RECOMMENDED_PACKS.get(biz[0], ["ke-toan", "thue-dnvn"]),
        onboarded_at=datetime.now(timezone.utc).isoformat(),
    )

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(config.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print("=" * 60)
    print("✅ Cài đặt thành công!")
    print(f"   Loại hình:    {config.business_type_label}")
    print(f"   Thành phố:    {config.city_label}")
    print(f"   Ngân hàng:    {config.bank_label}")
    if config.industry:
        print(f"   Ngành:        {config.industry}")
    print(f"   Lưu tại:      {CONFIG_FILE}")
    print()
    print("📦 Command packs được khuyến nghị cho bạn:")
    for cmd in config.recommended_commands or []:
        print(f"   • mekong {cmd}")
    print()
    print("🚀 Thử ngay lệnh đầu tiên:")
    print('   mekong ke-toan invoice --amount 5000000 --vat 10 --buyer "Khách thử"')
    print()
    print("📞 Cần hỗ trợ? Zalo OA: https://zalo.me/mekongmind")
    print("=" * 60)

    return config


def load_config() -> Optional[VNConfig]:
    """Đọc config đã lưu. Trả None nếu chưa onboard."""
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return VNConfig(**data)
    except (json.JSONDecodeError, TypeError):
        return None


def main(argv: Optional[list[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if "--non-interactive" in args or not sys.stdin.isatty():
        run_wizard(interactive=False)
    else:
        run_wizard(interactive=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
