"""Mekong CLI 7 — Plan-Execute-Verify engine.

Durable goal runner with checkpoint/resume. Each step:
  1. PLAN: strategist or sonnet drafts a step list
  2. EXECUTE: eng agent implements (code edits via instructed CLI usage)
  3. VERIFY: agent runs checks (typecheck/lint/test) and reports

State persists to ~/.mekong/state/<goal-slug>.json for resume.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from .config import CONFIG_DIR
from .llm import LLMClient
from .models import resolve

STATE_DIR = CONFIG_DIR / "state"


@dataclass
class Step:
    name: str
    task: str
    status: str = "pending"  # pending | running | done | failed
    result: str = ""
    error: str = ""


@dataclass
class Goal:
    title: str
    steps: list[Step] = field(default_factory=list)
    status: str = "created"  # created | planned | running | done | failed
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def slug(self) -> str:
        s = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        return s[:60] or "goal"


def load_goal(slug: str) -> Goal | None:
    path = STATE_DIR / f"{slug}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    goal = Goal(title=data["title"])
    goal.steps = [Step(**s) for s in data.get("steps", [])]
    goal.status = data.get("status", "created")
    goal.created_at = data.get("created_at", 0)
    goal.updated_at = data.get("updated_at", 0)
    return goal


def save_goal(goal: Goal) -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    goal.updated_at = time.time()
    path = STATE_DIR / f"{goal.slug}.json"
    path.write_text(
        json.dumps(
            {
                "title": goal.title,
                "status": goal.status,
                "steps": [s.__dict__ for s in goal.steps],
                "created_at": goal.created_at,
                "updated_at": goal.updated_at,
            },
            indent=2,
        )
    )
    return path


def plan_goal(title: str, client: LLMClient | None = None) -> list[Step]:
    """Use sonnet to decompose a goal into executable steps."""
    client = client or LLMClient()
    entry = resolve("sonnet")
    prompt = (
        f"Decompose this goal into 2-5 concrete implementation steps:\n\n{title}\n\n"
        "Working directory context: the operator's repo. Each step must be a single "
        "self-contained task an engineer agent can execute (create files, edit code, "
        "run checks).\n\n"
        'Return ONLY a JSON array, no prose: [{"name": "...", "task": "..."}]'
    )
    raw = client.text(entry.id, prompt, max_tokens=2048)
    steps: list[Step] = []
    try:
        data = json.loads(raw)
        for item in data:
            steps.append(Step(name=item.get("name", "step"), task=item.get("task", "")))
    except Exception:
        # Fallback: one big step with the raw plan text.
        steps.append(Step(name="implement", task=title))
    if not steps:
        steps.append(Step(name="implement", task=title))
    return steps
