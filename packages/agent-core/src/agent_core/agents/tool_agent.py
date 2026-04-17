"""ToolEnabledAgent — an agent that can call tools from REGISTRY.

Keeps the tool loop simple: one round-trip. The model responds with either a
JSON `{"tool": ..., "arguments": {...}}` to invoke a tool, or free text. A tool
call triggers a follow-up chat so the model can produce a final answer.
"""

from __future__ import annotations

from typing import Any

from agent_core.base_agent import BaseAgent
from agent_core.llm_client import ChatMessage, LLMClient
from agent_core.memory import SeedMemory
from agent_core.tools import REGISTRY


class ToolEnabledAgent(BaseAgent):
    def __init__(
        self,
        name: str,
        role_prompt: str,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
        tools: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(name=name, role_prompt=role_prompt, llm=llm, memory=memory)
        self.tools = tools if tools is not None else dict(REGISTRY)

    def _tool_catalog(self) -> str:
        lines = []
        for name, fn in self.tools.items():
            doc = (fn.__doc__ or "").strip().splitlines()
            summary = doc[0] if doc else ""
            lines.append(f"- {name}: {summary}")
        return "\n".join(lines)

    def _invoke_tool(self, name: str, arguments: dict) -> str:
        fn = self.tools.get(name)
        if fn is None:
            return f"Tool '{name}' không tồn tại."
        try:
            return str(fn(**arguments))
        except TypeError as e:
            return f"Tool '{name}' sai tham số: {e}"
        except Exception as e:  # noqa: BLE001
            return f"Tool '{name}' lỗi: {e}"

    def run(self, task: str, extra_context: str | None = None) -> str:
        context = self._build_context(task)
        prompt = (
            f"{extra_context or ''}\n\n{context}\n\n"
            f"Công cụ khả dụng:\n{self._tool_catalog()}\n\n"
            'Để dùng công cụ, trả về JSON: {"tool": "<name>", "arguments": {...}}\n'
            "Nếu không cần công cụ, trả lời bình thường.\n\n"
            f"## Nhiệm vụ:\n{task}"
        ).strip()
        first = self.llm.chat(
            messages=[ChatMessage(role="user", content=prompt)],
            system=self.role_prompt,
        )
        parsed = self.parse_json(first)
        if "tool" in parsed:
            tool_result = self._invoke_tool(parsed["tool"], parsed.get("arguments", {}))
            follow_up = (
                f"Kết quả từ công cụ {parsed['tool']}:\n{tool_result}\n\n"
                "Hãy hoàn thành nhiệm vụ dựa trên kết quả này."
            )
            final = self.llm.chat(
                messages=[
                    ChatMessage(role="user", content=prompt),
                    ChatMessage(role="assistant", content=first),
                    ChatMessage(role="user", content=follow_up),
                ],
                system=self.role_prompt,
            )
            self.memory.remember(
                self.name,
                f"Task: {task}\nTool: {parsed['tool']}\nResult: {tool_result[:300]}",
                {"task": task, "tool": parsed["tool"]},
            )
            return final
        self.memory.remember(
            self.name,
            f"Task: {task}\nResponse: {first[:500]}",
            {"task": task},
        )
        return first
