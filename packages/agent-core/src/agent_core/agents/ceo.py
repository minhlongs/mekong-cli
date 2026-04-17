"""CEOAgent — breaks down user goals into an action plan."""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

CEO_ROLE_PROMPT = """Bạn là CEO của một công ty khởi nghiệp AI một người (solo company).
Nhiệm vụ của bạn:
- Phân tích yêu cầu từ người sáng lập.
- Chia mục tiêu lớn thành các nhiệm vụ cụ thể, có thể giao cho Developer / Tester / Marketer.
- Trả về một kế hoạch hành động dạng danh sách số thứ tự, mỗi mục là một task độc lập.
- Luôn trả lời bằng tiếng Việt, ngắn gọn và thi hành được.
"""


class CEOAgent(BaseAgent):
    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="CEO",
            role_prompt=CEO_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def plan(self, goal: str) -> str:
        """Return a multi-step plan for the given goal."""
        return self.run(
            task=f"Lập kế hoạch chi tiết cho yêu cầu sau: {goal}",
            extra_context="Giao diện đầu ra: danh sách các bước đánh số, rõ chủ thể thực thi.",
        )
