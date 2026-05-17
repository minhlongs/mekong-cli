"""
Zalo OA CLI — Wrapper gọi integrations/zalo.py từ command line.
Dùng: python -m src.commands.zalo_oa <subcommand> [args]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Lazy import để tránh lỗi nếu requests chưa cài
def _get_client():
    from integrations.zalo import ZaloOAClient
    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    app_id = os.getenv("ZALO_APP_ID", "")
    if not token:
        print("❌ Thiếu ZALO_OA_ACCESS_TOKEN. Đặt trong .env.", file=sys.stderr)
        sys.exit(1)
    return ZaloOAClient(access_token=token, app_id=app_id)


def cmd_send(args: argparse.Namespace) -> None:
    client = _get_client()
    result = client.send_message(args.user_id, args.message)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_broadcast(args: argparse.Namespace) -> None:
    client = _get_client()
    result = client.broadcast(args.message)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_followers(args: argparse.Namespace) -> None:
    client = _get_client()
    result = client.get_followers(offset=args.offset, count=args.count)
    total = result.get("data", {}).get("total", 0)
    print(f"Tổng followers: {total:,}")
    for uid in result.get("data", {}).get("followers", []):
        print(f"  - {uid.get('user_id', '')} | {uid.get('display_name', '')}")


def cmd_caption(args: argparse.Namespace) -> None:
    from integrations.zalo import generate_vn_caption
    caption = generate_vn_caption(product=args.product, tone=args.tone)
    print(caption)


def cmd_post(args: argparse.Namespace) -> None:
    client = _get_client()
    result = client.post_article(
        title=args.title,
        content=args.content,
        cover_image=args.cover or "",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="zalo-oa",
        description="Zalo OA CLI cho doanh nghiệp VN",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # send
    p_send = sub.add_parser("send", help="Gửi tin nhắn cá nhân")
    p_send.add_argument("user_id", help="Zalo user ID")
    p_send.add_argument("message", help="Nội dung tin nhắn")
    p_send.set_defaults(func=cmd_send)

    # broadcast
    p_bcast = sub.add_parser("broadcast", help="Broadcast đến tất cả followers")
    p_bcast.add_argument("message", help="Nội dung broadcast")
    p_bcast.set_defaults(func=cmd_broadcast)

    # followers
    p_fol = sub.add_parser("followers", help="Xem danh sách followers")
    p_fol.add_argument("--offset", type=int, default=0)
    p_fol.add_argument("--count", type=int, default=50)
    p_fol.set_defaults(func=cmd_followers)

    # caption
    p_cap = sub.add_parser("caption", help="Tạo caption marketing tự động")
    p_cap.add_argument("product", help="Tên sản phẩm/dịch vụ")
    p_cap.add_argument("--tone", default="than_thien", choices=["than_thien", "chuyen_nghiep", "vui_ve"])
    p_cap.set_defaults(func=cmd_caption)

    # post
    p_post = sub.add_parser("post", help="Đăng bài viết lên Zalo OA")
    p_post.add_argument("title", help="Tiêu đề bài viết")
    p_post.add_argument("content", help="Nội dung bài viết")
    p_post.add_argument("--cover", default="", help="URL ảnh bìa")
    p_post.set_defaults(func=cmd_post)

    args = parser.parse_args(argv)
    try:
        from src.core.usage_meter import Stopwatch
    except ImportError:
        args.func(args)
        return
    with Stopwatch("zalo-oa"):
        args.func(args)


if __name__ == "__main__":
    main()
