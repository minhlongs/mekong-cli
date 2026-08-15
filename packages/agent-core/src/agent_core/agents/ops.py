"""OpsAgent — monitors a pipeline run, emits alerts if something looks unhealthy."""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

OPS_ROLE_PROMPT = """Bạn là Ops Engineer cho một công ty AI một người.
Nhiệm vụ:
- Nhận một pipeline report gồm plan, artifact, test, review.
- Đánh giá SỨC KHOẺ tổng thể của lần chạy (độ tin cậy, rủi ro vận hành, tín hiệu lỗi).
- Trả lời ở định dạng JSON duy nhất:
  {"healthy": true|false, "severity": "info|warn|critical", "alerts": ["alert 1", "alert 2"]}
- "critical" khi có rủi ro vận hành nghiêm trọng (ví dụ: test fail + review block).
- "warn" khi có dấu hiệu xuống cấp nhưng không chặn.
- "info" khi mọi thứ ổn.
- Ngắn gọn, tiếng Việt, tối đa 5 alerts.
"""


class OpsAgent(BaseAgent):
    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="Ops",
            role_prompt=OPS_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def monitor(self, report: dict) -> dict:
        """Return {healthy, severity, alerts} for a pipeline report."""
        task = (
            "Pipeline report cần đánh giá sức khoẻ:\n"
            f"- Goal: {report.get('goal', '')[:300]}\n"
            f"- Test status: {report.get('test', {}).get('status', 'unknown')}\n"
            f"- Test issues: {report.get('test', {}).get('issues', [])}\n"
            f"- Review verdict: {report.get('review', {}).get('verdict', 'unknown')} "
            f"(score {report.get('review', {}).get('score', 0)}/10)\n"
            f"- Review notes: {report.get('review', {}).get('notes', [])}\n"
            "Trả lời JSON duy nhất."
        )
        raw = self.run(task=task)
        parsed = self.parse_json(raw)
        severity = parsed.get("severity")
        if severity not in ("info", "warn", "critical"):
            severity = "warn"
        healthy = parsed.get("healthy")
        if not isinstance(healthy, bool):
            healthy = severity == "info"
        return {
            "healthy": healthy,
            "severity": severity,
            "alerts": parsed.get("alerts", []) or [],
        }
