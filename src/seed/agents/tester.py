# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""TesterAgent — verifies outputs against task requirements."""
from __future__ import annotations

from typing import Any

from seed.agents.base import BaseAgent


class TesterAgent(BaseAgent):
    """Verifies task outputs and returns structured verdict."""

    def verify(self, task: str, outputs: list[str]) -> dict[str, Any]:
        """Ask LLM to verify outputs, return structured verdict."""
        outputs_text = "\n".join(f"- {o}" for o in outputs)
        messages = [{"role": "user", "content": (
            f"{self.role_prompt}\n"
            f"Task: {task}\n"
            f"Outputs:\n{outputs_text}\n"
            "Respond with JSON: {'passed': bool, 'issues': [], 'score': int, 'notes': ''}"
        )}]
        response = self.llm.chat(messages) if self.llm else ""

        parsed = self._parse_response(response)
        return {
            "passed": parsed.get("passed", True),
            "issues": parsed.get("issues", []),
            "score": parsed.get("score", 7),
            "notes": parsed.get("notes", ""),
        }
