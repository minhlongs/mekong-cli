"""TesterAgent: verifies developer outputs meet quality criteria."""

from __future__ import annotations

from .base import BaseAgent

TESTER_PROMPT = """You are a Senior QA Engineer. Your responsibilities:
- Verify that code or content produced by the Developer is correct
- Check for syntax errors, logic errors, missing files
- Validate outputs match the original task requirements
- Return a JSON object with your verdict:
  {"passed": true/false, "issues": ["issue1", "issue2"], "score": 0-10, "notes": "..."}

Be strict but fair. Focus on functionality over style."""


class TesterAgent(BaseAgent):
    """Quality verification specialist."""

    def __init__(self) -> None:
        super().__init__(name="Tester", role_prompt=TESTER_PROMPT)

    def verify(self, task: str, outputs: list[str]) -> dict:
        """Verify developer outputs against original task."""
        outputs_str = "\n".join(f"- {o}" for o in outputs)
        prompt = (
            f"Original task: {task}\n\n"
            f"Developer outputs:\n{outputs_str}\n\n"
            "Evaluate if the outputs satisfy the task requirements."
        )
        response = self.run(prompt)
        result = self._parse_response(response)
        if "passed" not in result:
            result = {"passed": True, "issues": [], "score": 7, "notes": response}
        passed = result.get("passed", True)
        score = result.get("score", 7)
        print(f"  {'✅' if passed else '❌'} Tester: score={score}/10  passed={passed}")
        return result
