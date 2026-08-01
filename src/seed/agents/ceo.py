"""CEOAgent — creates execution plans from goals."""
from __future__ import annotations

import json
import re
from typing import Any

from seed.agents.base import BaseAgent


class CEOAgent(BaseAgent):
    """Plans tasks into structured execution steps."""

    def create_plan(self, goal: str) -> dict[str, Any]:
        """Ask LLM for a plan, fall back if no JSON found."""
        content = (
            f"{self.role_prompt}\n"
            f"Goal: {goal}\n"
            f"Respond with JSON: {{'plan': [...], 'assigned_to': 'developer'}}"
        )
        messages = [{"role": "user", "content": content}]
        response = self.llm.chat(messages) if self.llm else ""

        parsed = self._parse_response(response)
        if "plan" not in parsed:
            parsed = {
                "plan": [response],
                "assigned_to": "developer",
            }
        return parsed
