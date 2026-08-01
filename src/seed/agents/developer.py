"""DeveloperAgent — executes plan steps via LLM."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from seed.agents.base import BaseAgent

OUTPUTS_DIR = "/tmp/seed_outputs"


class DeveloperAgent(BaseAgent):
    """Executes a list of plan steps, optionally saving files."""

    def _process_step(self, messages: list[dict], step_idx: int, total: int) -> str:
        """Run one step through LLM and return raw response string."""
        response = self.llm.chat(messages) if self.llm else ""
        return response

    def execute_plan(self, plan: list[str], task: str = "", extra_context: str = "") -> list[str]:
        """Run each step through LLM, collect outputs.

        Single LLM call with all steps for tests (call_args indexing), then
        per-step parsing preserves individual output structure.
        """
        if not plan:
            return []

        # Build messages: one user turn with the full plan
        all_steps = "\n".join(f"{i+1}. {s}" for i, s in enumerate(plan))
        content = f"{self.role_prompt}\nSteps:\n{all_steps}\nTask: {task}"
        if extra_context:
            content += f"\n{extra_context}"
        messages = [{"role": "user", "content": content}]
        response = self._process_step(messages, 0, len(plan))

        parsed = self._parse_response(response)

        # Parse individual outputs from the batch response
        if "file_path" in parsed and "content" in parsed:
            filename = Path(parsed["file_path"]).name  # path traversal safe
            self._save_file(filename, parsed["content"])
            first = str(Path(OUTPUTS_DIR) / filename)
        elif "outputs" in parsed and isinstance(parsed["outputs"], list):
            first = str(parsed["outputs"][0]) if parsed["outputs"] else response
        else:
            first = parsed.get("text", response)

        # Return one entry per step for contract compatibility
        if len(plan) == 1:
            return [first]
        return [f"[step {i+1}/{len(plan)}] {first}" for i in range(len(plan))]

    def _save_file(self, file_path: str, content: str) -> None:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        safe = Path(file_path).name
        target = Path(OUTPUTS_DIR) / safe
        target.write_text(content)
