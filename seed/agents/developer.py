"""DeveloperAgent: thực thi plan → viết code → lưu file."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .base import BaseAgent
from ..config import OUTPUTS_DIR

DEV_PROMPT = """You are a Senior Software Engineer. Your responsibilities:
- Implement tasks given to you with clean, working code
- Write complete, runnable files (not pseudocode or stubs)
- When asked to create a file, return a JSON object:
  {"file_path": "filename.ext", "content": "...full file content..."}
- For non-code tasks, return {"text": "...your response..."}
- Always verify your code is syntactically correct before responding

Write production-quality code. No placeholders. No TODOs."""


class DeveloperAgent(BaseAgent):
    """Execution specialist — implements plans and writes files."""

    def __init__(self) -> None:
        super().__init__(name="Developer", role_prompt=DEV_PROMPT)

    def execute_plan(self, plan: list[str], original_task: str) -> list[str]:
        """Execute each plan step, write output files."""
        outputs: list[str] = []
        plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))

        print(f"  💻 Developer executing {len(plan)} steps...")
        task_prompt = (
            f"Execute this plan for: {original_task}\n\n"
            f"Plan:\n{plan_str}\n\n"
            "Implement step by step and produce the final output."
        )
        response = self.run(task_prompt)
        parsed = self._parse_response(response)

        if "file_path" in parsed and "content" in parsed:
            saved = self._save_file(parsed["file_path"], parsed["content"])
            outputs.append(saved)
        elif "text" in parsed:
            outputs.append(parsed["text"])
        else:
            outputs.append(response)

        return outputs

    def _save_file(self, file_path: str, content: str) -> str:
        """Save content to outputs directory."""
        out_dir = Path(OUTPUTS_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        # Strip leading / or ..
        safe_name = Path(file_path).name
        full_path = out_dir / safe_name
        full_path.write_text(content, encoding="utf-8")
        print(f"  💾 Saved: {full_path}")
        return str(full_path)
