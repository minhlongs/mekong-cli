# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Typer wrappers for the Zalo OA funnel commands."""

from __future__ import annotations

import json
import os
from typing import Any

import typer

zalo_app = typer.Typer(
    name="zalo-oa",
    help="Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài",
    no_args_is_help=False, add_completion=False, rich_markup_mode="rich",
)


def _zalo_client() -> Any:
    """Lazy factory mirroring src/commands/zalo_oa.py::_get_client()."""
    from integrations.zalo import ZaloOAClient

    token = os.getenv("ZALO_OA_ACCESS_TOKEN")
    if not token:
        typer.echo("❌ Thiếu ZALO_OA_ACCESS_TOKEN. Đặt trong .env.", err=True)
        raise typer.Exit(code=1)
    return ZaloOAClient(access_token=token, app_id=os.getenv("ZALO_APP_ID", ""))


@zalo_app.callback(invoke_without_command=True)
def zalo_main(
    ctx: typer.Context,
    json_mode: bool = typer.Option(False, "--json", help="Xuất báo cáo tổng quan dạng JSON"),
) -> None:
    """Zalo OA — gửi tin nhắn, broadcast, followers, caption, đăng bài."""
    if ctx.invoked_subcommand is not None:
        return
    from rich.console import Console
    from rich.panel import Panel
    from src.core.zalo_engine import ZaloEngine

    status_data = ZaloEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(status_data, indent=2, ensure_ascii=False))
        return
    Console().print(
        Panel(
            f"[bold green]HỆ THỐNG ZALO OFFICIAL ACCOUNT (OA) & CSKH TỰ ĐỘNG[/]\n"
            f"  Trạng thái:            [bold cyan]{status_data['status'].upper()}[/]\n"
            f"  Tổng số người theo dõi:[bold]{status_data['total_followers']}[/]\n"
            f"  Tin nhắn đã gửi:       [yellow]{status_data['total_messages_sent']}[/]\n"
            f"  Chiến dịch broadcast:  [green]{status_data['total_broadcasts']}[/]\n"
            f"  Caption đã khởi tạo:   [bold magenta]{status_data['total_captions_generated']}[/]\n"
            f"  Chế độ tích hợp:       [bold]{status_data['integration_mode']}[/]",
            title="[bold blue]Zalo OA Marketing & CSKH[/]", border_style="green",
        )
    )


@zalo_app.command(name="send")
def zalo_send(
    user_id: str = typer.Argument(..., help="Zalo user ID"),
    message: str = typer.Argument(..., help="Nội dung tin nhắn"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Gửi tin nhắn cá nhân qua Zalo OA."""
    from src.core.zalo_engine import ZaloEngine

    if mock:
        typer.echo(json.dumps(ZaloEngine().send_message(user_id=user_id, text=message), ensure_ascii=False, indent=2))
        return
    result = _zalo_client().send_message(user_id, message)
    ZaloEngine().send_message(user_id=user_id, text=message)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="broadcast")
def zalo_broadcast(
    message: str = typer.Argument(..., help="Nội dung broadcast"),
    title: str = typer.Option("Thông báo Zalo OA", "--title", "-t", help="Tiêu đề thông báo"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Broadcast đến tất cả followers."""
    from src.core.zalo_engine import ZaloEngine

    if mock:
        typer.echo(json.dumps(ZaloEngine().broadcast_campaign(title=title, text=message), ensure_ascii=False, indent=2))
        return
    result = _zalo_client().broadcast(message)
    ZaloEngine().broadcast_campaign(title=title, text=message)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


@zalo_app.command(name="followers")
def zalo_followers(
    offset: int = typer.Option(0, "--offset", help="Vị trí bắt đầu"),
    count: int = typer.Option(50, "--count", help="Số lượng tối đa"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Xem danh sách followers."""
    if mock:
        from src.core.zalo_engine import ZaloEngine

        followers = ZaloEngine().list_followers(limit=count)
        if json_mode:
            typer.echo(json.dumps({"total": len(followers), "followers": followers}, ensure_ascii=False, indent=2))
            return
        typer.echo(f"Tổng followers: {len(followers):,}")
        for uid in followers:
            typer.echo(f"  - {uid.get('user_id', '')} | {uid.get('name', '')} ({uid.get('segment', '')})")
        return

    result = _zalo_client().get_followers(offset=offset, count=count)
    typer.echo(f"Tổng followers: {result.get('data', {}).get('total', 0):,}")
    for uid in result.get("data", {}).get("followers", []):
        typer.echo(f"  - {uid.get('user_id', '')} | {uid.get('display_name', '')}")


@zalo_app.command(name="caption")
def zalo_caption(
    product: str = typer.Argument(..., help="Tên sản phẩm/dịch vụ"),
    tone: str = typer.Option("than_thien", "--tone", help="Giọng văn: than_thien | chuyen_nghiep | vui_ve | sang_tao | khuyen_mai | binh_phap"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Tạo caption marketing tự động (offline, không cần token)."""
    from src.core.zalo_engine import ZaloEngine

    cap_data = ZaloEngine().generate_caption(topic=product, tone=tone)
    if json_mode:
        typer.echo(json.dumps(cap_data, ensure_ascii=False, indent=2))
        return
    from integrations.zalo import generate_vn_caption

    typer.echo(generate_vn_caption(product=product, tone=tone))


@zalo_app.command(name="post")
def zalo_post(
    title: str = typer.Argument(..., help="Tiêu đề bài viết"),
    content: str = typer.Argument(..., help="Nội dung bài viết"),
    cover: str = typer.Option("", "--cover", help="URL ảnh bìa"),
    mock: bool = typer.Option(False, "--mock", help="Chạy chế độ mô phỏng offline"),
    json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON"),
) -> None:
    """Đăng bài viết lên Zalo OA."""
    if mock:
        from src.core.zalo_engine import ZaloEngine

        typer.echo(json.dumps(ZaloEngine().create_post(title=title, content=content), ensure_ascii=False, indent=2))
        return
    typer.echo(json.dumps(_zalo_client().post_article(title=title, content=content, cover_image=cover), ensure_ascii=False, indent=2))


@zalo_app.command(name="status")
def zalo_status(json_mode: bool = typer.Option(False, "--json", help="Xuất dữ liệu JSON")) -> None:
    """Xem trạng thái hệ thống Zalo OA và số liệu marketing."""
    from rich.console import Console
    from rich.panel import Panel
    from src.core.zalo_engine import ZaloEngine

    data = ZaloEngine().get_status()
    if json_mode:
        typer.echo(json.dumps(data, indent=2, ensure_ascii=False))
        return
    Console().print(
        Panel(
            f"[bold green]TRẠNG THÁI ZALO OFFICIAL ACCOUNT[/]\n"
            f"Tổng followers:     [bold]{data['total_followers']}[/]\n"
            f"Tin nhắn CSKH:      [yellow]{data['total_messages_sent']}[/]\n"
            f"Broadcast đã gửi:   [green]{data['total_broadcasts']}[/]\n"
            f"Caption tiếp thị:   [bold magenta]{data['total_captions_generated']}[/]",
            title="[bold blue]Zalo OA Telemetry[/]", border_style="green",
        )
    )
