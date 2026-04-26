"""CEOAgent: phân tích task → tạo action plan."""

from __future__ import annotations

from .base import BaseAgent

CEO_PROMPT = """You are the CEO of a solo AI company. Your responsibilities:
- Analyze user requests and break them into clear, actionable steps
- Assign tasks to specialists (Developer, Designer, Analyst)
- Ensure quality and coherence of the final output

When given a task:
1. Analyze what needs to be done
2. Create a concise step-by-step plan (max 5 steps)
3. Return the plan as a JSON object:
   {"plan": ["step 1", "step 2", ...], "assigned_to": "developer|analyst|designer"}

Keep plans practical and implementable."""


class CEOAgent(BaseAgent):
    """Strategic orchestrator — turns goals into plans."""

    def __init__(self) -> None:
        super().__init__(name="CEO", role_prompt=CEO_PROMPT)

    def create_plan(self, task: str) -> dict:
        """Analyze task and return structured plan."""
        print(f"  🤖 CEO analyzing: {task[:80]}...")
        response = self.run(task)
        parsed = self._parse_response(response)
        if "plan" not in parsed:
            parsed = {"plan": [response], "assigned_to": "developer"}
        print(f"  📋 Plan ({len(parsed['plan'])} steps): {parsed['plan'][0][:60]}...")
        return parsed
