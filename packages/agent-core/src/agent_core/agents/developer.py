"""DeveloperAgent — writes code against a CEO plan, persists files to ./outputs."""

from __future__ import annotations

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import LLMClient
from agent_core.memory import SeedMemory

DEVELOPER_ROLE_PROMPT = """Bạn là Kỹ sư phần mềm cao cấp cho một công ty AI một người.
Nhiệm vụ:
- Nhận kế hoạch hoặc task cụ thể từ CEO.
- Viết code sạch, có best-practice, kèm chú thích khi cần.
- Khi được yêu cầu tạo một file, trả lời ở định dạng JSON:
  {"file_path": "relative/path/under/outputs.ext", "content": "<toàn bộ nội dung file>"}
- Nếu task không sinh file, trả lời bằng text mô tả hành động đã thực hiện.
"""


class DeveloperAgent(BaseAgent):
    def __init__(
        self,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        super().__init__(
            name="Developer",
            role_prompt=DEVELOPER_ROLE_PROMPT,
            llm=llm,
            memory=memory,
        )

    def execute(self, task: str, plan_context: str | None = None) -> str:
        return self.run(task=task, extra_context=plan_context)
