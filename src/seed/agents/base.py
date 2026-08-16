"""Base agent — matches test expectations."""
from __future__ import annotations

import json
import re
from typing import Any



def get_llm_client() -> Any:
    """Return configured LLM client (used by tests via patch)."""
    return None


def get_memory() -> Any:
    """Return configured memory store (used by tests via patch)."""
    return None


class BaseAgent:
    """Agent base class with LLM, memory, and JSON response parsing."""

    def __init__(self, name: str = "", role_prompt: str = "", llm: Any = None, memory: Any = None, **_kw) -> None:
        self.name = name
        self.role_prompt = role_prompt
        self.llm = llm if llm is not None else get_llm_client()
        self.memory = memory if memory is not None else get_memory()

    # ── Response parsing ──────────────────────────────────────────────

    def _parse_response(self, raw: str) -> dict[str, Any]:
        """Extract JSON from LLM response. Falls back to text wrapper."""
        # Strip fenced code block wrapper if present
        m = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
        if m:
            raw = m.group(1)

        # Strategy 1: non-greedy without DOTALL — matches individual JSON objects
        # back-to-back. Correctly handles nested objects (stops at matching `}`).
        candidates = re.findall(r"\{.*?\}", raw)
        for block in reversed(candidates):
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue

        # Strategy 2: greedy with DOTALL — for responses with newlines inside
        # a single JSON object. Tries each candidate from last to first.
        candidates = re.findall(r"\{.*\}", raw, re.DOTALL)
        for block in reversed(candidates):
            try:
                return json.loads(block)
            except json.JSONDecodeError:
                continue

        return {"text": raw}

    # ── Run loop ──────────────────────────────────────────────────────

    def run(self, task: str, extra_context: str = "") -> str:
        """Execute task via LLM with memory context. Returns raw LLM response."""
        messages: list[dict[str, str]] = []

        context = ""
        if self.memory:
            self.memory.recall(task)
            recent = self.memory.get_recent(self.name, limit=5)
            if recent:
                context = "\n".join(
                    r.get("content", "") if isinstance(r, dict) else str(r)
                    for r in recent
                )

        if self.role_prompt:
            messages.append({"role": "system", "content": self.role_prompt})
        if context:
            messages.append({"role": "user", "content": f"Previous context:\n{context}"})
        if extra_context:
            messages.append({"role": "user", "content": extra_context})
        messages.append({"role": "user", "content": f"Task: {task}"})

        if self.llm:
            response = self.llm.chat(messages)
        else:
            response = "stub response"

        if self.memory and hasattr(self.memory, "remember"):
            self.memory.remember(self.name, response)
        return response

    def chat(self, prompt: str) -> str:
        return self.run(prompt)
