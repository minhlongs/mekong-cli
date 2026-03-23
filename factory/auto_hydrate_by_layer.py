#!/usr/bin/env python3
"""Auto-hydrate remaining generic contracts using layer-based templates.

Each layer gets a sensible default I/O schema that's better than {goal: string}.
Commands keep their existing metadata (chapter, display, etc.) — only input/output
and execution.agents are upgraded.

Run: python3 factory/auto_hydrate_by_layer.py
"""

import json
from pathlib import Path

CONTRACTS_DIR = Path("factory/contracts/commands")

# Layer → default typed schema templates
LAYER_TEMPLATES: dict[str, dict] = {
    "founder": {
        "execution_agents": ["strategist", "researcher"],
        "hub": "founder-hub",
        "input_extra": {
            "context": {"type": "string", "description": "Business context or background"},
            "urgency": {"type": "string", "enum": ["low", "medium", "high"], "description": "Priority level"},
        },
        "output_template": {
            "summary": {"type": "string", "description": "Executive summary"},
            "recommendations": {"type": "array", "items": {"type": "string"}},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        },
    },
    "business": {
        "execution_agents": ["cmo", "sales"],
        "hub": "business-hub",
        "input_extra": {
            "target_audience": {"type": "string", "description": "Target customer segment"},
            "budget": {"type": "number", "description": "Budget allocation"},
        },
        "output_template": {
            "summary": {"type": "string"},
            "action_items": {"type": "array", "items": {"type": "string"}},
            "metrics": {"type": "object", "description": "Key metrics and KPIs"},
            "roi_estimate": {"type": "number", "description": "Expected ROI"},
        },
    },
    "product": {
        "execution_agents": ["pm", "planner"],
        "hub": "product-hub",
        "input_extra": {
            "scope": {"type": "string", "enum": ["feature", "module", "system"], "description": "Scope level"},
            "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]},
        },
        "output_template": {
            "summary": {"type": "string"},
            "requirements": {"type": "array", "items": {"type": "string"}},
            "effort_estimate": {"type": "string", "description": "Effort in hours/days"},
            "dependencies": {"type": "array", "items": {"type": "string"}},
        },
    },
    "engineering": {
        "execution_agents": ["fullstack-developer", "code-reviewer"],
        "hub": "engineering-hub",
        "input_extra": {
            "file_paths": {"type": "array", "items": {"type": "string"}, "description": "Target files"},
            "language": {"type": "string", "description": "Programming language"},
        },
        "output_template": {
            "summary": {"type": "string"},
            "files_modified": {"type": "array", "items": {"type": "string"}},
            "tests_status": {"type": "string", "enum": ["passing", "failing", "skipped"]},
            "lines_changed": {"type": "integer"},
        },
    },
    "ops": {
        "execution_agents": ["devops"],
        "hub": "ops-hub",
        "input_extra": {
            "services": {"type": "array", "items": {"type": "string"}, "description": "Target services"},
            "environment": {"type": "string", "enum": ["local", "staging", "production"]},
        },
        "output_template": {
            "summary": {"type": "string"},
            "status": {"type": "string", "enum": ["healthy", "degraded", "down", "completed"]},
            "findings": {"type": "array", "items": {"type": "string"}},
            "actions_taken": {"type": "array", "items": {"type": "string"}},
        },
    },
}


def hydrate_generic() -> None:
    """Upgrade all generic {goal, project} contracts with layer-appropriate schemas."""
    updated = 0

    for f in sorted(CONTRACTS_DIR.glob("*.json")):
        c = json.loads(f.read_text())
        props = c.get("input", {}).get("properties", {})

        # Skip already-hydrated
        if set(props.keys()) != {"goal", "project"}:
            continue

        layer = c.get("layer", "ops")
        template = LAYER_TEMPLATES.get(layer, LAYER_TEMPLATES["ops"])

        # Upgrade input: keep goal, add layer-specific fields
        c["input"] = {
            "type": "object",
            "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "description": "Natural language task description"},
                **template["input_extra"],
            },
        }

        # Upgrade output
        c["output"] = {
            "type": "object",
            "properties": template["output_template"],
        }

        # Upgrade agents (only if still generic planner+fullstack-developer)
        current_agents = c.get("execution", {}).get("agents", [])
        if current_agents == ["planner", "fullstack-developer"]:
            c["execution"]["agents"] = template["execution_agents"]
            c["execution"]["hub"] = template["hub"]

        f.write_text(json.dumps(c, indent=2, ensure_ascii=False) + "\n")
        updated += 1

    print(f"Auto-hydrated {updated} contracts (layer templates)")
    print(f"Total hydrated: {updated + 37} (manual 37 + auto {updated})")


if __name__ == "__main__":
    hydrate_generic()
