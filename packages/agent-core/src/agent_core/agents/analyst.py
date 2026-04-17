"""AnalystAgent — produces insights + recommendations from a pipeline report."""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

ANALYST_ROLE_PROMPT = """Bạn là Product Analyst cho một công ty AI một người.
Nhiệm vụ:
- Đọc một pipeline report và (tuỳ chọn) lịch sử các lần chạy trước.
- Tóm tắt, tìm điểm yếu, đề xuất cải tiến hành động được.
- Trả lời ở định dạng JSON duy nhất:
  {"summary": "<1-2 câu>", "recommendations": ["r1", "r2"], "trend": "improving|flat|regressing"}
- "recommendations" phải hành động được — bắt đầu bằng động từ (ví dụ: "Thêm unit test cho...",
  "Rút gọn hàm X xuống dưới 50 dòng").
- Ngắn gọn, tiếng Việt, tối đa 5 recommendations.
"""


class AnalystAgent(BaseAgent):
    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="Analyst",
            role_prompt=ANALYST_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def analyze(self, report: dict, history: list[dict] | None = None) -> dict:
        """Return {summary, recommendations, trend} for a pipeline report + optional history."""
        history = history or []
        hist_block = ""
        if history:
            lines = []
            for i, h in enumerate(history[-3:], start=1):
                lines.append(
                    f"  Lần {i}: verdict={h.get('review', {}).get('verdict', '?')}, "
                    f"score={h.get('review', {}).get('score', 0)}, "
                    f"test={h.get('test', {}).get('status', '?')}"
                )
            hist_block = "\nLịch sử gần nhất:\n" + "\n".join(lines)
        task = (
            "Pipeline report cần phân tích:\n"
            f"- Goal: {report.get('goal', '')[:300]}\n"
            f"- Test: {report.get('test', {}).get('status', '?')} — "
            f"{report.get('test', {}).get('summary', '')[:200]}\n"
            f"- Review: {report.get('review', {}).get('verdict', '?')} "
            f"(score {report.get('review', {}).get('score', 0)}/10)\n"
            f"- Notes: {report.get('review', {}).get('notes', [])}"
            f"{hist_block}\n"
            "Trả lời JSON duy nhất."
        )
        raw = self.run(task=task)
        parsed = self.parse_json(raw)
        trend = parsed.get("trend")
        if trend not in ("improving", "flat", "regressing"):
            trend = "flat"
        return {
            "summary": parsed.get("summary", raw[:200]),
            "recommendations": parsed.get("recommendations", []) or [],
            "trend": trend,
        }
