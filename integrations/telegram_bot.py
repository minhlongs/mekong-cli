"""Telegram webhook bot — bridges Telegram messages to seed agents.

Usage:
    TELEGRAM_TOKEN=xxx python integrations/telegram_bot.py

Commands:
    /task <description>  — Run a task through CEO→Developer→Tester pipeline
    /status              — Show last job result
    /help                — Show usage
"""

from __future__ import annotations

import json
import logging
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from threading import Thread

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from seed.main import run as seed_run

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

_last_result: dict = {}


def _tg_request(method: str, payload: dict) -> dict:
    url = f"{BASE_URL}/{method}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        logger.error("Telegram API error: %s", e)
        return {}


def send_message(chat_id: int, text: str) -> None:
    _tg_request("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})


def handle_task(chat_id: int, task: str) -> None:
    send_message(chat_id, f"⏳ Đang xử lý task...\n`{task[:80]}`")
    try:
        result = seed_run(task)
        global _last_result
        _last_result = result

        outputs = result.get("outputs", [])
        test_result = result.get("test_result", {})
        passed = test_result.get("passed", True)
        score = test_result.get("score", "?")

        lines = [f"✨ *Task hoàn thành!*\n"]
        lines.append(f"*Plan:* {len(result.get('plan', []))} bước")
        for out in outputs[:3]:
            lines.append(f"📁 `{out}`")
        lines.append(f"\n{'✅' if passed else '❌'} Test score: *{score}/10*")
        send_message(chat_id, "\n".join(lines))
    except Exception as e:
        send_message(chat_id, f"❌ Lỗi: {e}")


def process_update(update: dict) -> None:
    msg = update.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    text = msg.get("text", "").strip()
    if not chat_id or not text:
        return

    if text.startswith("/task "):
        task = text[6:].strip()
        if task:
            Thread(target=handle_task, args=(chat_id, task), daemon=True).start()
        else:
            send_message(chat_id, "Usage: `/task <mô tả task>`")
    elif text == "/status":
        if _last_result:
            outputs = _last_result.get("outputs", ["Chưa có output"])
            send_message(chat_id, f"Last outputs:\n" + "\n".join(f"• `{o}`" for o in outputs))
        else:
            send_message(chat_id, "Chưa có task nào được chạy.")
    elif text in ("/start", "/help"):
        send_message(
            chat_id,
            "🌱 *Mekong Seed Bot*\n\n"
            "Commands:\n"
            "`/task <mô tả>` — Chạy task qua AI agent\n"
            "`/status` — Xem kết quả lần cuối\n"
            "`/help` — Hướng dẫn này",
        )


def poll_updates() -> None:
    """Long-polling fallback (for local dev without webhook server)."""
    offset = 0
    logger.info("Telegram bot polling started...")
    while True:
        try:
            data = _tg_request("getUpdates", {"offset": offset, "timeout": 30})
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                process_update(upd)
        except Exception as e:
            logger.error("Poll error: %s", e)


if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("Set TELEGRAM_TOKEN env var first.")
        sys.exit(1)
    poll_updates()
