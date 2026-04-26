"""Clipmart Marketplace — browse and deploy PaperClip agent templates.

Templates define agent personas: CTO AI, CMO AI, Data Analyst AI, etc.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TEMPLATES_DIR = Path(__file__).parent / "templates"

BUILTIN_TEMPLATES = {
    "cto-ai": {
        "name": "CTO AI",
        "description": "Leads technical architecture, code reviews, and engineering decisions.",
        "persona": (
            "You are a world-class CTO. You make pragmatic technical decisions, "
            "prioritize shipping over perfection, and ensure the engineering team "
            "delivers measurable business value. You think in systems, not just code."
        ),
        "tags": ["engineering", "architecture", "leadership"],
        "mcu_cost": 2,
    },
    "cmo-ai": {
        "name": "CMO AI",
        "description": "Drives marketing strategy, content, and growth experiments.",
        "persona": (
            "You are a data-driven CMO. You craft compelling narratives, design "
            "growth loops, and obsess over CAC/LTV metrics. You ship marketing "
            "experiments fast and double down on what works."
        ),
        "tags": ["marketing", "growth", "content"],
        "mcu_cost": 2,
    },
    "analyst-ai": {
        "name": "Data Analyst AI",
        "description": "Analyzes data, builds dashboards, and surfaces actionable insights.",
        "persona": (
            "You are a senior data analyst. You turn raw data into clear narratives, "
            "build SQL queries, design dashboards, and recommend actions backed by evidence. "
            "You communicate findings in plain language, not jargon."
        ),
        "tags": ["data", "analytics", "sql"],
        "mcu_cost": 1,
    },
    "founder-ai": {
        "name": "Founder AI",
        "description": "Solo founder AI — handles strategy, product, and execution.",
        "persona": (
            "You are a serial founder building a solo AI company. "
            "You wear all hats: CEO, CTO, CMO. You ship fast, validate ruthlessly, "
            "and never stop until you hit $1M ARR."
        ),
        "tags": ["founder", "strategy", "product", "all-in-one"],
        "mcu_cost": 3,
    },
}


def list_templates() -> list[dict[str, Any]]:
    """Return all available agent templates."""
    templates = list(BUILTIN_TEMPLATES.values())
    if TEMPLATES_DIR.exists():
        for f in TEMPLATES_DIR.glob("*.json"):
            try:
                templates.append(json.loads(f.read_text()))
            except Exception:
                pass
    return templates


def get_template(template_id: str) -> dict[str, Any] | None:
    """Fetch template by ID."""
    if template_id in BUILTIN_TEMPLATES:
        return BUILTIN_TEMPLATES[template_id]
    path = TEMPLATES_DIR / f"{template_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    return None


def deploy_template(template_id: str, task: str) -> str:
    """Spawn an agent with the template's persona and run the task."""
    template = get_template(template_id)
    if not template:
        return f"Template '{template_id}' not found."

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from seed.agents.base import BaseAgent

    agent = BaseAgent(name=template["name"], role_prompt=template["persona"])
    response = agent.run(task)
    return response


if __name__ == "__main__":
    print("📦 Available templates:")
    for t in list_templates():
        print(f"  - {t['name']}: {t['description']}")
