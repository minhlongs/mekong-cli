"""BaseAgent: think → act → observe loop with persistent memory."""

from __future__ import annotations

import json
import logging
from typing import Any

from ..llm_client import LLMClient, get_llm_client
from ..memory import SeedMemory, get_memory

try:
    from observability.agent_metrics import timed as _timed
except ImportError:
    def _timed(name):  # graceful no-op if observability not installed
        def dec(fn):
            return fn
        return dec

logger = logging.getLogger(__name__)


class BaseAgent:
    """Foundation agent with LLM + memory."""

    def __init__(self, name: str, role_prompt: str, model: str | None = None) -> None:
        self.name = name
        self.role_prompt = role_prompt
        self.llm: LLMClient = get_llm_client()
        if model:
            self.llm.model = model
        self.memory: SeedMemory = get_memory()

    def _build_context(self, task: str) -> str:
        """Fetch relevant + recent memories to build context string."""
        relevant = self.memory.recall(self.name, task, n_results=5)
        recent = self.memory.get_recent(self.name, limit=3)
        parts: list[str] = []
        if relevant:
            parts.append("### Relevant memories:\n" + "\n".join(f"- {r}" for r in relevant))
        if recent:
            parts.append("### Recent activity:\n" + "\n".join(f"- {r['content']}" for r in recent))
        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> dict[str, Any]:
        """Try to parse JSON from response — try last block first, then first."""
        # Find all candidate {…} spans and try from last to first
        positions = []
        depth = 0
        start = None
        for i, ch in enumerate(response):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}" and depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    positions.append((start, i + 1))
        for s, e in reversed(positions):
            try:
                return json.loads(response[s:e])
            except Exception:
                continue
        return {"text": response}

    @_timed("agent.run")
    def run(self, task: str, extra_context: str | None = None) -> str:
        """Execute task: build context → call LLM → store memory → return response."""
        context = self._build_context(task)
        prompt = self.role_prompt
        if extra_context:
            prompt += f"\n\n{extra_context}"
        if context:
            prompt += f"\n\n{context}"
        prompt += f"\n\n## Current task:\n{task}\n\nRespond clearly and concisely."

        messages = [{"role": "user", "content": prompt}]
        response = self.llm.chat(messages)

        # Store memory
        self.memory.remember(
            self.name,
            f"Task: {task[:200]}...\nResponse: {response[:500]}...",
            {"task": task[:100], "response_preview": response[:200]},
        )
        return response
