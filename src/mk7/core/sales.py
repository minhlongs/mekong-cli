"""Mekong CLI 7 — Sales module (OPC Platform).

Leads (từ SignalInbox kind=lead) → proposal draft → close (human gate).
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from .opc_loop import SignalInbox, _load, _save


class SalesPipeline:
    STAGES = ("new", "contacted", "proposal", "closed")

    def __init__(self) -> None:
        self.leads: dict[str, dict[str, Any]] = _load("leads.json", {})

    def _save(self) -> None:
        _save("leads.json", self.leads)

    def create_from_signals(self) -> int:
        """Tự tạo lead từ SignalInbox kind=lead chưa được xử lý."""
        inbox = SignalInbox()
        created = 0
        for prod, s in inbox.list():
            if s["kind"] != "lead":
                continue
            lid = str(uuid.uuid4())[:8]
            self.leads[lid] = {
                "id": lid, "product": prod, "stage": "new",
                "note": s.get("note", ""), "ts": time.time(),
            }
            created += 1
        if created:
            self._save()
        return created

    def list(self, product: str | None = None) -> list[dict[str, Any]]:
        out = [l for l in self.leads.values()]
        if product:
            out = [l for l in out if l["product"] == product]
        return sorted(out, key=lambda l: l["ts"])

    def advance(self, lead_id: str, stage: str) -> dict[str, Any]:
        if stage not in self.STAGES:
            raise ValueError(f"stage must be one of {self.STAGES}")
        lead = self.leads.get(lead_id)
        if not lead:
            raise KeyError(f"lead {lead_id} not found")
        lead["stage"] = stage
        self._save()
        return lead

    def close(self, lead_id: str, amount: float, by: str) -> dict[str, Any]:
        """Close → ghi revenue (human gate qua RevenueLedger)."""
        from .opc_loop import RevenueLedger

        lead = self.advance(lead_id, "closed")
        if not by:
            raise ValueError("close requires human confirmation (by)")
        RevenueLedger().record(lead["product"], amount, confirmed_by=by)
        return lead

    def draft_proposal(self, lead_id: str) -> str:
        lead = self.leads.get(lead_id)
        if not lead:
            raise KeyError(f"lead {lead_id} not found")
        try:
            from .llm import LLMClient

            client = LLMClient(timeout=120)
            prompt = (
                f"Viết proposal draft tiếng Việt cho lead của product '{lead['product']}'.\n"
                f"Context khách: {lead.get('note', '')[:300]}\n"
                "Output: giá trị đề xuất, phạm vi, giá (đề xuất), bước tiếp theo. Ngắn gọn, thực dụng."
            )
            return client.text("claude-fable-5", prompt,
                               system="Bạn là AE của OPC Platform. Viết proposal thuyết phục, không phồng.", max_tokens=800)
        except Exception:
            pass
        return (
            f"Proposal draft — {lead['product']}\n"
            f"Context: {lead.get('note', '')[:200]}\n"
            f"Next: human review → send → close (ghi revenue bằng mk revenue-add)"
        )
