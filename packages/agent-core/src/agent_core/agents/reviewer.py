"""ReviewerAgent — audits security, readability, maintainability of an artifact."""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

REVIEWER_ROLE_PROMPT = """Bạn là Senior Code Reviewer cho một công ty AI một người.
Nhiệm vụ:
- Đánh giá một artifact về ba trục: bảo mật, dễ đọc, dễ bảo trì.
- Trả lời ở định dạng JSON duy nhất:
  {"score": 0-10, "verdict": "ship|revise|block", "notes": ["note 1", "note 2"]}
- "ship"  (score >= 8): sẵn sàng triển khai.
- "revise" (5-7): cần chỉnh vài điểm.
- "block"  (<5): có rủi ro nghiêm trọng.
- Ngắn gọn, tiếng Việt, tối đa 5 notes.
"""


class ReviewerAgent(BaseAgent):
    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="Reviewer",
            role_prompt=REVIEWER_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def review(self, goal: str, artifact: str) -> dict:
        """Return {score, verdict, notes} for artifact."""
        task = (
            f"Mục tiêu dự án: {goal}\n\n"
            f"Artifact cần review:\n```\n{artifact[:4000]}\n```\n"
            "Trả lời JSON duy nhất."
        )
        raw = self.run(task=task)
        parsed = self.parse_json(raw)
        score = parsed.get("score", 0)
        try:
            score = max(0, min(10, int(score)))
        except (TypeError, ValueError):
            score = 0
        verdict = parsed.get("verdict")
        if verdict not in ("ship", "revise", "block"):
            verdict = "revise" if score >= 5 else "block"
        elif verdict == "ship" and score < 5:
            verdict = "block"
        return {
            "score": score,
            "verdict": verdict,
            "notes": parsed.get("notes", []) or [],
        }
