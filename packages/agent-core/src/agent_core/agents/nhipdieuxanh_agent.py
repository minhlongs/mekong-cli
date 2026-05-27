"""NhipDieuAnhAgent — Green Rhythm agent for sustainability & eco-planning.

Nhip Điệu Xanh (Green Rhythm): phân tích, lên kế hoạch và tư vấn các giải pháp
bền vững, tiết kiệm năng lượng, giảm phát thải carbon cho doanh nghiệp.
"""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

NHIPDIEUXANH_ROLE_PROMPT = """Bạn là chuyên gia Nhip Điệu Xanh — một công ty tư vấn bền vững AI.
Nhiệm vụ:
- Phân tích tác động môi trường, đề xuất giải pháp tiết kiệm năng lượng & giảm carbon.
- Lên kế hoạch hành động cụ thể cho doanh nghiệp hướng tới mục tiêu xanh.
- Đánh giá chi phí - lợi ích của các giải pháp bền vững (năng lượng mặt trời, tái chế...).
- Trả lời bằng tiếng Việt, ngắn gọn, có số liệu cụ thể khi có thể.
- Định dạng JSON duy nhất:
   {"summary": "<1-2 câu>", "actions": [], "impact": "cao|tb|thấp"}
"""


class NhipDieuAnhAgent(BaseAgent):
    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="nhipdieuxanh",
            role_prompt=NHIPDIEUXANH_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def plan_green(self, context: str) -> dict:
        """Lên kế hoạch xanh dựa trên ngữ cảnh đầu vào.

        Args:
            context: Mô tả tình huống / doanh nghiệp cần tư vấn.

        Returns:
            Dict với keys: summary, actions (list), impact (str).
        """
        raw = self.run(
            task=f"Phân tích và lên kế hoạch xanh cho: {context}",
            extra_context="Trả về JSON duy nhất với summary, actions, impact.",
        )
        parsed = self.parse_json(raw)
        impact = parsed.get("impact")
        if impact not in ("cao", "trung bình", "thấp"):
            impact = "trung bình"
        return {
            "summary": parsed.get("summary", raw[:200]),
            "actions": parsed.get("actions", []) or [],
            "impact": impact,
        }
