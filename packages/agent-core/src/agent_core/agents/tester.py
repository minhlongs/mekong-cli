"""TesterAgent — reviews an artifact + asserts it meets acceptance criteria."""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

TESTER_ROLE_PROMPT = """Bạn là Kỹ sư QA cao cấp cho một công ty AI một người.
Nhiệm vụ:
- Nhận một artifact (đoạn code hoặc file đã được Developer tạo ra) kèm mục tiêu ban đầu.
- Trả lời ở định dạng JSON duy nhất:
  {"status": "pass|fail", "summary": "<mô tả ngắn>", "issues": ["issue 1", "issue 2"]}
- "pass" nếu artifact đáp ứng mục tiêu và không có lỗi rõ ràng.
- "fail" nếu có lỗi cú pháp, thiếu yêu cầu, hoặc logic sai.
- Ngắn gọn, tiếng Việt.
"""


class TesterAgent(BaseAgent):
    __test__ = False  # pytest: class is not a test collector target

    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="Tester",
            role_prompt=TESTER_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def evaluate(self, goal: str, artifact: str) -> dict:
        """Return {status, summary, issues} for artifact vs goal."""
        task = (
            f"Mục tiêu: {goal}\n\n"
            f"Artifact cần đánh giá:\n```\n{artifact[:4000]}\n```\n"
            "Trả lời JSON duy nhất."
        )
        raw = self.run(task=task)
        parsed = self.parse_json(raw)
        status = parsed.get("status")
        if status not in ("pass", "fail"):
            status = "fail"
        return {
            "status": status,
            "summary": parsed.get("summary", raw[:200]),
            "issues": parsed.get("issues", []) or [],
        }
