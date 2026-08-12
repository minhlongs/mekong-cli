"""Mekong CLI 7 — Support module (OPC Platform).

Tickets (từ SignalInbox kind=support) → auto-response draft → resolve (human).
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from .opc_loop import SignalInbox, _load, _save


class SupportDesk:
    def __init__(self) -> None:
        self.tickets: dict[str, dict[str, Any]] = _load("tickets.json", {})

    def _save(self) -> None:
        _save("tickets.json", self.tickets)

    def create_from_signals(self) -> int:
        inbox = SignalInbox()
        created = 0
        for prod, s in inbox.list():
            if s["kind"] != "support":
                continue
            tid = str(uuid.uuid4())[:8]
            self.tickets[tid] = {
                "id": tid, "product": prod, "status": "open",
                "note": s.get("note", ""), "ts": time.time(),
            }
            created += 1
        if created:
            self._save()
        return created

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        out = [t for t in self.tickets.values()]
        if status:
            out = [t for t in out if t["status"] == status]
        return sorted(out, key=lambda t: t["ts"])

    def draft_response(self, ticket_id: str) -> str:
        t = self.tickets.get(ticket_id)
        if not t:
            raise KeyError(f"ticket {ticket_id} not found")
        try:
            from .llm import LLMClient

            client = LLMClient(timeout=120)
            prompt = (
                f"Viết response draft tiếng Việt cho ticket của product '{t['product']}'.\n"
                f"Vấn đề khách: {t.get('note', '')[:300]}\n"
                "Output: xác nhận đã nhận, hướng xử lý, thời gian dự kiến. Lịch sự, ngắn gọn."
            )
            return client.text("claude-fable-5", prompt,
                               system="Bạn là support của OPC Platform. Viết response chuyên nghiệp.", max_tokens=600)
        except Exception:
            pass
        return (
            f"Response draft — {t['product']} ticket\n"
            f"Customer: {t.get('note', '')[:200]}\n"
            f"Next: human review → send → resolve (mk support-resolve {ticket_id} --by ...)"
        )

    def resolve(self, ticket_id: str, by: str) -> dict[str, Any]:
        t = self.tickets.get(ticket_id)
        if not t:
            raise KeyError(f"ticket {ticket_id} not found")
        if not by:
            raise ValueError("resolve requires human confirmation (by)")
        t["status"] = "resolved"
        t["resolved_by"] = by
        t["resolved_at"] = time.time()
        self._save()
        return t
