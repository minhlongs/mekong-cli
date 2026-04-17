"""BaseAgent — think → act → observe loop, backed by LLMClient + SeedMemory."""

from __future__ import annotations

import json
import logging
from typing import Any

from agent_core.llm_client import ChatMessage, LLMClient
from agent_core.memory import SeedMemory

log = logging.getLogger(__name__)


class BaseAgent:
    def __init__(
        self,
        name: str,
        role_prompt: str,
        llm: LLMClient | None = None,
        memory: SeedMemory | None = None,
    ) -> None:
        self.name = name
        self.role_prompt = role_prompt
        self.llm = llm or LLMClient()
        self.memory = memory or SeedMemory()

    def _build_context(self, task: str) -> str:
        relevant = self.memory.recall(self.name, task, n_results=5)
        recent = self.memory.get_recent(self.name, limit=3)
        parts: list[str] = []
        if relevant:
            parts.append("### Ký ức liên quan:\n" + "\n".join(f"- {r}" for r in relevant))
        if recent:
            parts.append(
                "### Hoạt động gần đây:\n"
                + "\n".join(f"- {r.content[:200]}" for r in recent)
            )
        return "\n\n".join(parts)

    @staticmethod
    def parse_json(response: str) -> dict[str, Any]:
        """Best-effort JSON extraction from an LLM response."""
        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {"text": response}
        try:
            return json.loads(response[start : end + 1])
        except json.JSONDecodeError:
            return {"text": response}

    def run(self, task: str, extra_context: str | None = None) -> str:
        context = self._build_context(task)
        user_body = (
            f"{extra_context or ''}\n\n{context}\n\n## Nhiệm vụ hiện tại:\n{task}"
        ).strip()
        response = self.llm.chat(
            messages=[ChatMessage(role="user", content=user_body)],
            system=self.role_prompt,
        )
        self.memory.remember(
            self.name,
            f"Task: {task}\nResponse: {response[:500]}",
            {"task": task, "response_preview": response[:200]},
        )
        return response
