"""Mekong CLI 7 — Marketing module (OPC Platform).

Campaign draft generator — positioning + content per product.
"""

from __future__ import annotations

import time
from typing import Any

from .finance import Finance
from .opc_loop import MetricsStore, _load, _save


class Marketing:
    def __init__(self) -> None:
        self.campaigns: list[dict[str, Any]] = _load("campaigns.json", [])
        self.finance = Finance()
        self.metrics = MetricsStore()

    def draft(self, product: str, angle: str = "") -> str:
        m = self.metrics.get(product)
        rev = self.finance.revenue.total_for(product)
        cost = self.finance.costs.total_for(product)
        profit = round(rev - cost, 2)
        try:
            from .llm import LLMClient

            client = LLMClient(timeout=120)
            prompt = (
                f"Viết 1 campaign draft tiếng Việt cho product '{product}' của một solo-founder "
                f"dùng OPC Platform (công ty 1 người vận hành 24/7 bằng AI).\n"
                f"Thông tin thật: revenue={rev}$ profit={profit}$ cost={cost}$ "
                f"cycles={m.get('cycles', 0)} zero_revenue_streak={m.get('zero_revenue_streak', 0)}\n"
                f"Angle: {angle or 'chưa chọn — tự đề xuất'}\n"
                "Output: Positioning (1 câu) + Proof (từ số thật) + 3 kênh + CTA + hook 1 dòng."
            )
            return client.text("claude-fable-5", prompt,
                               system="Bạn là CMO của OPC Platform. Viết ngắn gọn, thực dụng, không phồng.", max_tokens=800)
        except Exception:
            pass
        angle_line = f"\nAngle: {angle}" if angle else ""
        return (
            f"Campaign draft — {product}\n"
            f"Positioning: giải quyết vấn đề X cho solo-founder\n"
            f"Proof: {rev}$ revenue · {profit}$ profit · {m.get('cycles', 0)} cycles vận hành{angle_line}\n"
            f"Channels: LinkedIn + X + newsletter\n"
            f"CTA: dùng thử 7 ngày — human review trước khi gửi"
        )

    def log(self, product: str, draft: str, by: str = "") -> dict[str, Any]:
        if not by:
            raise ValueError("campaign log requires human confirmation (by)")
        entry = {"product": product, "draft": draft, "by": by, "ts": time.time()}
        self.campaigns.append(entry)
        _save("campaigns.json", self.campaigns)
        return entry
