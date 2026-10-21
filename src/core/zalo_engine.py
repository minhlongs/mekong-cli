# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Zalo Official Account (OA) Customer Messaging, Broadcast Campaign & Social Marketing Engine."""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import sqlite3
import typing
import uuid

CANONICAL_FOLLOWERS = [
    {"user_id": "zalo-user-001", "name": "Nguyễn Văn An", "phone": "0901234567", "segment": "vip"},
    {"user_id": "zalo-user-002", "name": "Trần Thị Bích", "phone": "0912345678", "segment": "active"},
    {"user_id": "zalo-user-003", "name": "Lê Hoàng Long", "phone": "0987654321", "segment": "active"},
    {"user_id": "zalo-user-004", "name": "Phạm Thu Hương", "phone": "0934567890", "segment": "vip"},
    {"user_id": "zalo-user-005", "name": "Đỗ Minh Khang", "phone": "0976543210", "segment": "standard"},
]

TONE_TEMPLATES = {
    "vui_ve": {
        "prefix": "🎉 Chào cả nhà! Hôm nay có tin siêu hot về",
        "suffix": "👉 Nhắn tin ngay cho chúng mình để không bỏ lỡ nhé! Chúc mọi người một ngày tràn đầy năng lượng! ✨",
    },
    "chuyen_nghiep": {
        "prefix": "Kính gửi Quý đối tác và Khách hàng,\nChúng tôi trân trọng giới thiệu giải pháp tối ưu cho",
        "suffix": "Liên hệ bộ phận chuyên viên tư vấn để nhận tài liệu kỹ thuật và lộ trình triển khai chi tiết.",
    },
    "sang_tao": {
        "prefix": "✨ Có bao giờ bạn tự hỏi, điều gì tạo nên sự đột phá trong",
        "suffix": "💡 Khám phá câu chuyện đằng sau và đồng hành cùng chúng tôi trên hành trình kiến tạo giá trị mới.",
    },
    "khuyen_mai": {
        "prefix": "🔥 [SIÊU ƯU ĐÃI CÓ HẠN] Bùng nổ cơ hội sở hữu ngay",
        "suffix": "⚡ Giảm ngay 30% cho 50 khách hàng đầu tiên trong hôm nay! Đặt lịch ngay kẻo lỡ!",
    },
    "binh_phap": {
        "prefix": "⚔️ Binh Pháp Tôn Tử khởi sự: 'Biết mình biết ta, trăm trận không nguy.' Trong chiến trường",
        "suffix": "Chiếm lĩnh địa hình, nắm chắc tiên cơ, tối ưu hóa nguồn lực để bất khả chiến bại.",
    },
}


class ZaloEngine:
    """Autonomous Zalo Official Account Messaging & Campaign Engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        self.db_path = pathlib.Path(db_path) if db_path is not None else pathlib.Path(".mekong") / "zalo.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS messages (message_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, text TEXT NOT NULL, template TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, sent_at TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS broadcasts (broadcast_id TEXT PRIMARY KEY, title TEXT NOT NULL, text TEXT NOT NULL, target_segment TEXT NOT NULL, recipients_count INTEGER NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS followers (user_id TEXT PRIMARY KEY, name TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '', segment TEXT NOT NULL DEFAULT 'standard', followed_at TEXT NOT NULL)")
            conn.execute("CREATE TABLE IF NOT EXISTS captions (caption_id TEXT PRIMARY KEY, topic TEXT NOT NULL, tone TEXT NOT NULL, content TEXT NOT NULL, hashtags TEXT NOT NULL, created_at TEXT NOT NULL)")
            conn.commit()
            if conn.execute("SELECT COUNT(*) AS cnt FROM followers").fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for f in CANONICAL_FOLLOWERS:
                    conn.execute("INSERT INTO followers (user_id, name, phone, segment, followed_at) VALUES (?, ?, ?, ?, ?)", (f["user_id"], f["name"], f["phone"], f["segment"], now))
                conn.commit()

    def add_follower(self, user_id: str, name: str, phone: str = "", segment: str = "standard") -> dict[str, typing.Any]:
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO followers (user_id, name, phone, segment, followed_at) VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET name = excluded.name, phone = excluded.phone, segment = excluded.segment",
                (user_id, name, phone, segment, now),
            )
            conn.commit()
        return {"ok": True, "user_id": user_id, "name": name, "phone": phone, "segment": segment}

    def send_message(self, user_id: str, text: str, template: str = "", save: bool = True) -> dict[str, typing.Any]:
        msg_id = f"ZMSG-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if save:
            with self._get_connection() as conn:
                conn.execute("INSERT INTO messages (message_id, user_id, text, template, status, sent_at) VALUES (?, ?, ?, ?, ?, ?)", (msg_id, user_id, text, template, "delivered", now_iso))
                conn.commit()
        return {"ok": True, "message_id": msg_id, "user_id": user_id, "text": text, "template": template, "status": "delivered", "sent_at": now_iso, "simulated": True}

    def broadcast_campaign(self, title: str, text: str, target_segment: str = "all", save: bool = True) -> dict[str, typing.Any]:
        broadcast_id = f"ZBC-{str(uuid.uuid4())[:8].upper()}"
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        rc = len(self.list_followers(segment=target_segment))
        res = {
            "ok": True, "broadcast_id": broadcast_id, "title": title or "Thông báo Zalo OA", "text": text,
            "target_segment": target_segment, "recipients_count": rc, "sent_count": rc,
            "delivered_count": max(1, int(rc * 0.95)) if rc > 0 else 0, "read_count": max(1, int(rc * 0.70)) if rc > 0 else 0,
            "status": "completed", "created_at": now_iso, "simulated": True,
        }
        if save:
            with self._get_connection() as conn:
                conn.execute("INSERT INTO broadcasts (broadcast_id, title, text, target_segment, recipients_count, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)", (broadcast_id, res["title"], text, target_segment, rc, "completed", now_iso))
                conn.commit()
        return res

    def list_followers(self, segment: str = "all", limit: int = 50) -> list[dict[str, typing.Any]]:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM followers WHERE segment = ? ORDER BY followed_at DESC LIMIT ?", (segment, limit)) if segment != "all" else conn.execute("SELECT * FROM followers ORDER BY followed_at DESC LIMIT ?", (limit,))
            return [dict(r) for r in cur.fetchall()]

    def generate_caption(self, topic: str, tone: str = "vui_ve", save: bool = True) -> dict[str, typing.Any]:
        tone_key = tone.lower().strip() if tone.lower().strip() in TONE_TEMPLATES else "vui_ve"
        template, cleaned_topic = TONE_TEMPLATES[tone_key], topic.strip()
        slug = re.sub(r"[^\w\s]", "", cleaned_topic).replace(" ", "")
        tags = [f"#{slug}" if slug else "#Mekong", "#ZaloOA", "#MekongCLI", "#KinhDoanhVN"]
        full_content = f"{template['prefix']} {cleaned_topic}!\n\n{template['suffix']}\n\n{' '.join(tags)}"
        caption_id, now_iso = f"ZCAP-{str(uuid.uuid4())[:8].upper()}", datetime.datetime.now(datetime.timezone.utc).isoformat()
        if save:
            with self._get_connection() as conn:
                conn.execute("INSERT INTO captions (caption_id, topic, tone, content, hashtags, created_at) VALUES (?, ?, ?, ?, ?, ?)", (caption_id, cleaned_topic, tone_key, full_content, json.dumps(tags), now_iso))
                conn.commit()
        return {"ok": True, "caption_id": caption_id, "topic": cleaned_topic, "tone": tone_key, "caption": full_content, "content": full_content, "hashtags": tags, "created_at": now_iso}

    def create_post(self, title: str, content: str, save: bool = True) -> dict[str, typing.Any]:
        return {"ok": True, "post_id": f"ZPOST-{str(uuid.uuid4())[:8].upper()}", "title": title, "content": content, "status": "published", "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(), "simulated": True}

    def get_status(self) -> dict[str, typing.Any]:
        with self._get_connection() as conn:
            fc = conn.execute("SELECT COUNT(*) AS cnt FROM followers").fetchone()["cnt"]
            mc = conn.execute("SELECT COUNT(*) AS cnt FROM messages").fetchone()["cnt"]
            bc = conn.execute("SELECT COUNT(*) AS cnt FROM broadcasts").fetchone()["cnt"]
            cc = conn.execute("SELECT COUNT(*) AS cnt FROM captions").fetchone()["cnt"]
            segments = [r["segment"] for r in conn.execute("SELECT DISTINCT segment FROM followers").fetchall()]
            recent_msgs = [dict(r) for r in conn.execute("SELECT * FROM messages ORDER BY sent_at DESC LIMIT 5").fetchall()]
            recent_bcs = [dict(r) for r in conn.execute("SELECT * FROM broadcasts ORDER BY created_at DESC LIMIT 5").fetchall()]
        return {
            "ok": True, "status": "operational", "total_followers": fc, "total_messages": mc, "total_messages_sent": mc,
            "total_broadcasts": bc, "total_captions_generated": cc, "segments": segments, "supported_tones": list(TONE_TEMPLATES.keys()),
            "recent_messages": recent_msgs, "recent_broadcasts": recent_bcs, "integration_mode": "hybrid (offline simulation + openapi adapter)",
        }
