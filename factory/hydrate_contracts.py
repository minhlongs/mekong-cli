#!/usr/bin/env python3
"""Hydrate factory contracts with typed I/O schemas.

Replaces generic {goal: string} stubs with command-specific
input/output schemas, correct agents, cascade triggers, and validation.

Run: python3 factory/hydrate_contracts.py
"""

import json
from pathlib import Path

CONTRACTS_DIR = Path("factory/contracts/commands")

# ── Typed contract definitions for top 30 commands ──
# Format: id → {overrides to merge into existing contract}

HYDRATIONS: dict[str, dict] = {
    # ═══ VERTICAL CHAIN (swot→plan→cook→test→deploy→audit) ═══
    "swot": {
        "display": {"description_en": "SWOT analysis — strengths, weaknesses, opportunities, threats"},
        "execution": {"agents": ["strategist", "researcher"], "hub": "founder-hub", "credit_cost": 2, "complexity": "standard"},
        "input": {
            "type": "object", "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "description": "Company/product/market to analyze"},
                "focus": {"type": "string", "enum": ["product", "market", "team", "financial"], "description": "Analysis focus area"},
                "competitors": {"type": "array", "items": {"type": "string"}, "description": "Known competitors to compare"},
            },
        },
        "output": {
            "type": "object",
            "properties": {
                "strengths": {"type": "array", "items": {"type": "string"}},
                "weaknesses": {"type": "array", "items": {"type": "string"}},
                "opportunities": {"type": "array", "items": {"type": "string"}},
                "threats": {"type": "array", "items": {"type": "string"}},
                "recommendation": {"type": "string"},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            },
        },
        "cascade": {"triggers": ["plan"]},
        "validation": {"output_must_contain": ["strengths", "weaknesses"], "min_output_length": 200},
    },
    "plan": {
        "display": {"description_en": "Create implementation plan with phases, dependencies, and estimates"},
        "execution": {"agents": ["planner", "researcher"], "hub": "product-hub", "credit_cost": 2, "complexity": "standard"},
        "input": {
            "type": "object", "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "description": "Feature or system to plan"},
                "constraints": {"type": "array", "items": {"type": "string"}, "description": "Technical/business constraints"},
                "deadline": {"type": "string", "format": "date", "description": "Target completion date"},
            },
        },
        "output": {
            "type": "object",
            "properties": {
                "plan_path": {"type": "string", "description": "Path to plan.md file"},
                "phases": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "effort_hours": {"type": "number"}, "dependencies": {"type": "array", "items": {"type": "string"}}}}},
                "total_effort_hours": {"type": "number"},
                "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            },
        },
        "cascade": {"triggers": ["cook"]},
        "validation": {"output_must_contain": ["plan_path", "phases"], "min_output_length": 100},
    },
    "test": {
        "display": {"description_en": "Run test suite with coverage analysis and failure diagnosis"},
        "execution": {"agents": ["tester"], "hub": "engineering-hub", "credit_cost": 1, "complexity": "simple"},
        "input": {
            "type": "object", "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "description": "Test scope or specific file"},
                "test_type": {"type": "string", "enum": ["unit", "integration", "e2e", "all"]},
                "coverage_threshold": {"type": "number", "default": 80},
            },
        },
        "output": {
            "type": "object",
            "properties": {
                "total_tests": {"type": "integer"},
                "passed": {"type": "integer"},
                "failed": {"type": "integer"},
                "skipped": {"type": "integer"},
                "coverage_percent": {"type": "number"},
                "failures": {"type": "array", "items": {"type": "object", "properties": {"test": {"type": "string"}, "error": {"type": "string"}}}},
            },
        },
        "cascade": {"triggers": ["deploy"]},
        "validation": {"output_must_contain": ["total_tests", "passed"], "min_output_length": 50},
    },
    "deploy": {
        "display": {"description_en": "Deploy to production — build, push, verify CI/CD, confirm green"},
        "execution": {"agents": ["devops"], "hub": "engineering-hub", "credit_cost": 3, "complexity": "standard", "requires_approval": True},
        "input": {
            "type": "object", "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "description": "Deployment target or description"},
                "environment": {"type": "string", "enum": ["staging", "production"], "default": "production"},
                "platform": {"type": "string", "enum": ["cloudflare", "vercel", "docker"]},
            },
        },
        "output": {
            "type": "object",
            "properties": {
                "deploy_url": {"type": "string", "format": "uri"},
                "commit_sha": {"type": "string"},
                "ci_status": {"type": "string", "enum": ["success", "failure", "pending"]},
                "http_status": {"type": "integer"},
                "deploy_time_seconds": {"type": "number"},
            },
        },
        "cascade": {"triggers": ["audit"]},
        "validation": {"output_must_contain": ["deploy_url", "ci_status"], "min_output_length": 50},
    },
    "audit": {
        "display": {"description_en": "Security and code quality audit — deps, secrets, OWASP checks"},
        "execution": {"agents": ["security-reviewer", "code-reviewer"], "hub": "ops-hub", "credit_cost": 2, "complexity": "standard"},
        "input": {
            "type": "object", "required": ["goal"],
            "properties": {
                "goal": {"type": "string", "description": "Audit scope"},
                "audit_type": {"type": "string", "enum": ["security", "code", "dependency", "full"]},
                "severity_threshold": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            },
        },
        "output": {
            "type": "object",
            "properties": {
                "score": {"type": "number", "minimum": 0, "maximum": 10},
                "findings": {"type": "array", "items": {"type": "object", "properties": {"severity": {"type": "string"}, "category": {"type": "string"}, "description": {"type": "string"}, "fix": {"type": "string"}}}},
                "critical_count": {"type": "integer"},
                "high_count": {"type": "integer"},
                "recommendations": {"type": "array", "items": {"type": "string"}},
            },
        },
        "cascade": {"triggers": []},
        "validation": {"output_must_contain": ["score", "findings"], "min_output_length": 100},
    },

    # ═══ FOUNDER LAYER ═══
    "annual": {
        "display": {"description_en": "Annual business plan — vision, goals, financials, milestones"},
        "execution": {"agents": ["strategist", "cfo"], "hub": "founder-hub", "credit_cost": 3},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "year": {"type": "integer"}, "current_mrr": {"type": "number"}}},
        "output": {"type": "object", "properties": {"vision": {"type": "string"}, "goals": {"type": "array", "items": {"type": "string"}}, "revenue_target": {"type": "number"}, "milestones": {"type": "array", "items": {"type": "object", "properties": {"quarter": {"type": "string"}, "target": {"type": "string"}}}}}},
        "cascade": {"triggers": ["okr"]},
    },
    "okr": {
        "display": {"description_en": "Set OKRs — objectives with measurable key results"},
        "execution": {"agents": ["strategist"], "hub": "founder-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "quarter": {"type": "string"}, "focus_areas": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"objectives": {"type": "array", "items": {"type": "object", "properties": {"objective": {"type": "string"}, "key_results": {"type": "array", "items": {"type": "object", "properties": {"metric": {"type": "string"}, "target": {"type": "number"}, "current": {"type": "number"}}}}}}}}},
        "cascade": {"triggers": ["sprint"]},
    },

    # ═══ BUSINESS LAYER ═══
    "finance": {
        "display": {"description_en": "Financial analysis — P&L, cash flow, unit economics"},
        "execution": {"agents": ["cfo", "data"], "hub": "finance-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "period": {"type": "string", "enum": ["monthly", "quarterly", "annual"]}, "metrics": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"mrr": {"type": "number"}, "arr": {"type": "number"}, "burn_rate": {"type": "number"}, "runway_months": {"type": "number"}, "unit_economics": {"type": "object", "properties": {"ltv": {"type": "number"}, "cac": {"type": "number"}, "ltv_cac_ratio": {"type": "number"}}}}},
        "cascade": {"triggers": []},
    },
    "pricing": {
        "display": {"description_en": "Pricing strategy — competitive analysis, tier design, revenue modeling"},
        "execution": {"agents": ["strategist", "cfo"], "hub": "business-hub", "credit_cost": 3, "requires_approval": True},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "current_pricing": {"type": "object"}, "competitors": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"tiers": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "price": {"type": "number"}, "features": {"type": "array", "items": {"type": "string"}}}}}, "revenue_projection": {"type": "object", "properties": {"monthly": {"type": "number"}, "annual": {"type": "number"}}}}},
        "cascade": {"triggers": []},
    },
    "marketing": {
        "display": {"description_en": "Marketing strategy — channels, content, campaigns"},
        "execution": {"agents": ["cmo", "editor"], "hub": "marketing-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "channel": {"type": "string", "enum": ["seo", "social", "email", "ads", "content", "all"]}, "budget": {"type": "number"}}},
        "output": {"type": "object", "properties": {"strategy": {"type": "string"}, "channels": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "action": {"type": "string"}, "expected_roi": {"type": "number"}}}}, "content_plan": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": ["content", "launch"]},
    },
    "sales": {
        "display": {"description_en": "Sales strategy — pipeline, outreach, closing"},
        "execution": {"agents": ["sales", "cmo"], "hub": "sales-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "target_segment": {"type": "string"}, "deal_size": {"type": "number"}}},
        "output": {"type": "object", "properties": {"icp": {"type": "object", "properties": {"industry": {"type": "string"}, "company_size": {"type": "string"}, "pain_points": {"type": "array", "items": {"type": "string"}}}}, "pipeline_stages": {"type": "array", "items": {"type": "string"}}, "outreach_templates": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": []},
    },

    # ═══ PRODUCT LAYER ═══
    "brainstorm": {
        "display": {"description_en": "Brainstorm solutions with trade-off analysis"},
        "execution": {"agents": ["planner", "researcher"], "hub": "product-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "constraints": {"type": "array", "items": {"type": "string"}}, "max_options": {"type": "integer", "default": 5}}},
        "output": {"type": "object", "properties": {"options": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "description": {"type": "string"}, "pros": {"type": "array", "items": {"type": "string"}}, "cons": {"type": "array", "items": {"type": "string"}}, "effort": {"type": "string", "enum": ["low", "medium", "high"]}}}}, "recommendation": {"type": "string"}}},
        "cascade": {"triggers": ["plan"]},
    },
    "sprint": {
        "display": {"description_en": "Sprint planning — backlog grooming, task breakdown, assignments"},
        "execution": {"agents": ["pm", "planner"], "hub": "product-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "sprint_duration_days": {"type": "integer", "default": 14}, "team_capacity_hours": {"type": "number"}}},
        "output": {"type": "object", "properties": {"sprint_goal": {"type": "string"}, "tasks": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "assignee": {"type": "string"}, "estimate_hours": {"type": "number"}, "priority": {"type": "string", "enum": ["critical", "high", "medium", "low"]}}}}, "total_points": {"type": "integer"}}},
        "cascade": {"triggers": ["cook"]},
    },

    # ═══ ENGINEERING LAYER ═══
    "fix": {
        "display": {"description_en": "Debug and fix bugs with root cause analysis"},
        "execution": {"agents": ["debugger", "fullstack-developer"], "hub": "engineering-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string", "description": "Bug description or error message"}, "logs": {"type": "string"}, "file_path": {"type": "string"}}},
        "output": {"type": "object", "properties": {"root_cause": {"type": "string"}, "fix_description": {"type": "string"}, "files_modified": {"type": "array", "items": {"type": "string"}}, "tests_added": {"type": "integer"}, "verified": {"type": "boolean"}}},
        "cascade": {"triggers": ["test"]},
        "validation": {"output_must_contain": ["root_cause", "fix_description"], "min_output_length": 50},
    },
    "review": {
        "display": {"description_en": "Code review with security, quality, and performance checks"},
        "execution": {"agents": ["code-reviewer"], "hub": "engineering-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "files": {"type": "array", "items": {"type": "string"}}, "review_type": {"type": "string", "enum": ["security", "quality", "performance", "full"]}}},
        "output": {"type": "object", "properties": {"score": {"type": "number", "minimum": 0, "maximum": 10}, "issues": {"type": "array", "items": {"type": "object", "properties": {"severity": {"type": "string"}, "file": {"type": "string"}, "line": {"type": "integer"}, "message": {"type": "string"}}}}, "approved": {"type": "boolean"}}},
        "cascade": {"triggers": []},
    },
    "code": {
        "display": {"description_en": "Write code for a specific task — focused implementation"},
        "execution": {"agents": ["fullstack-developer"], "hub": "engineering-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "language": {"type": "string"}, "file_path": {"type": "string"}}},
        "output": {"type": "object", "properties": {"files_created": {"type": "array", "items": {"type": "string"}}, "files_modified": {"type": "array", "items": {"type": "string"}}, "lines_added": {"type": "integer"}, "lines_removed": {"type": "integer"}}},
        "cascade": {"triggers": ["test", "review"]},
    },

    # ═══ OPS LAYER ═══
    "health": {
        "display": {"description_en": "System health check — services, endpoints, dependencies"},
        "execution": {"agents": ["devops"], "hub": "ops-hub", "credit_cost": 0, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "services": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"overall_status": {"type": "string", "enum": ["healthy", "degraded", "down"]}, "services": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "status": {"type": "string"}, "latency_ms": {"type": "number"}, "uptime_percent": {"type": "number"}}}}}},
        "cascade": {"triggers": []},
    },
    "status": {
        "display": {"description_en": "Project status report — progress, blockers, metrics"},
        "execution": {"agents": ["pm"], "hub": "ops-hub", "credit_cost": 0, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "project": {"type": "string"}}},
        "output": {"type": "object", "properties": {"status": {"type": "string", "enum": ["on_track", "at_risk", "blocked", "completed"]}, "progress_percent": {"type": "number"}, "blockers": {"type": "array", "items": {"type": "string"}}, "next_milestone": {"type": "string"}}},
        "cascade": {"triggers": []},
    },
    "debug": {
        "display": {"description_en": "Systematic debugging with log analysis and root cause identification"},
        "execution": {"agents": ["debugger"], "hub": "ops-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string", "description": "Error or symptom description"}, "logs": {"type": "string"}, "stack_trace": {"type": "string"}}},
        "output": {"type": "object", "properties": {"root_cause": {"type": "string"}, "affected_files": {"type": "array", "items": {"type": "string"}}, "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]}, "fix_suggestion": {"type": "string"}, "related_issues": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": ["fix"]},
    },
    "security": {
        "display": {"description_en": "Security scan — vulnerabilities, secrets, OWASP compliance"},
        "execution": {"agents": ["security-reviewer"], "hub": "ops-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "scan_type": {"type": "string", "enum": ["dependency", "code", "config", "full"]}}},
        "output": {"type": "object", "properties": {"vulnerabilities": {"type": "array", "items": {"type": "object", "properties": {"severity": {"type": "string"}, "package": {"type": "string"}, "description": {"type": "string"}, "fix": {"type": "string"}}}}, "secrets_found": {"type": "integer"}, "owasp_score": {"type": "number"}}},
        "cascade": {"triggers": []},
    },

    # ═══ BUSINESS — REVENUE ═══
    "launch": {
        "display": {"description_en": "Product launch — checklist, channels, announcements"},
        "execution": {"agents": ["cmo", "pm"], "hub": "business-hub", "credit_cost": 3, "requires_approval": True},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "channels": {"type": "array", "items": {"type": "string"}}, "launch_date": {"type": "string", "format": "date"}}},
        "output": {"type": "object", "properties": {"checklist": {"type": "array", "items": {"type": "object", "properties": {"task": {"type": "string"}, "status": {"type": "string"}, "owner": {"type": "string"}}}}, "announcements": {"type": "array", "items": {"type": "string"}}, "metrics_to_track": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": ["marketing"]},
    },
    "content": {
        "display": {"description_en": "Content creation — blog posts, social media, email sequences"},
        "execution": {"agents": ["editor", "cmo"], "hub": "marketing-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "content_type": {"type": "string", "enum": ["blog", "social", "email", "docs", "newsletter"]}, "tone": {"type": "string", "enum": ["professional", "casual", "technical"]}}},
        "output": {"type": "object", "properties": {"content": {"type": "string"}, "word_count": {"type": "integer"}, "seo_keywords": {"type": "array", "items": {"type": "string"}}, "cta": {"type": "string"}}},
        "cascade": {"triggers": []},
    },
    "competitive": {
        "display": {"description_en": "Competitive analysis — market positioning, feature comparison, battlecards"},
        "execution": {"agents": ["researcher", "strategist"], "hub": "business-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "competitors": {"type": "array", "items": {"type": "string"}}, "dimensions": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"competitors": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "strengths": {"type": "array", "items": {"type": "string"}}, "weaknesses": {"type": "array", "items": {"type": "string"}}, "pricing": {"type": "string"}}}}, "our_advantages": {"type": "array", "items": {"type": "string"}}, "battlecard": {"type": "string"}}},
        "cascade": {"triggers": []},
    },
    "research": {
        "display": {"description_en": "Technical research — architecture evaluation, best practices, trade-offs"},
        "execution": {"agents": ["researcher"], "hub": "product-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "depth": {"type": "string", "enum": ["quick", "standard", "deep"]}}},
        "output": {"type": "object", "properties": {"findings": {"type": "array", "items": {"type": "object", "properties": {"topic": {"type": "string"}, "summary": {"type": "string"}, "sources": {"type": "array", "items": {"type": "string"}}}}}, "recommendation": {"type": "string"}, "trade_offs": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": ["plan"]},
    },

    # ═══ STUDIO LAYER ═══
    "standup": {
        "display": {"description_en": "Daily standup — yesterday, today, blockers"},
        "execution": {"agents": ["pm"], "hub": "ops-hub", "credit_cost": 0, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "project": {"type": "string"}}},
        "output": {"type": "object", "properties": {"yesterday": {"type": "array", "items": {"type": "string"}}, "today": {"type": "array", "items": {"type": "string"}}, "blockers": {"type": "array", "items": {"type": "string"}}, "metrics": {"type": "object"}}},
        "cascade": {"triggers": []},
    },
    "milestone": {
        "display": {"description_en": "Milestone tracking — progress against targets"},
        "execution": {"agents": ["pm"], "hub": "product-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "milestone_name": {"type": "string"}}},
        "output": {"type": "object", "properties": {"name": {"type": "string"}, "progress_percent": {"type": "number"}, "tasks_completed": {"type": "integer"}, "tasks_remaining": {"type": "integer"}, "estimated_completion": {"type": "string"}, "risks": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": []},
    },
    "outreach": {
        "display": {"description_en": "Sales outreach — cold emails, LinkedIn, follow-ups"},
        "execution": {"agents": ["sales", "editor"], "hub": "sales-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "channel": {"type": "string", "enum": ["email", "linkedin", "twitter", "phone"]}, "target_count": {"type": "integer"}}},
        "output": {"type": "object", "properties": {"templates": {"type": "array", "items": {"type": "object", "properties": {"subject": {"type": "string"}, "body": {"type": "string"}, "channel": {"type": "string"}}}}, "targets_contacted": {"type": "integer"}, "follow_up_schedule": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": []},
    },
    "scout": {
        "display": {"description_en": "Codebase scouting — file discovery, task context, architecture analysis"},
        "execution": {"agents": ["researcher"], "hub": "ops-hub", "credit_cost": 1, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "scope": {"type": "string", "enum": ["file", "module", "full"]}, "pattern": {"type": "string"}}},
        "output": {"type": "object", "properties": {"files_found": {"type": "array", "items": {"type": "string"}}, "architecture_summary": {"type": "string"}, "key_patterns": {"type": "array", "items": {"type": "string"}}, "dependencies": {"type": "array", "items": {"type": "string"}}}},
        "cascade": {"triggers": ["plan"]},
    },
}


def hydrate() -> None:
    """Apply typed schemas to existing contracts."""
    updated = 0
    skipped = 0

    for cmd_id, overrides in HYDRATIONS.items():
        path = CONTRACTS_DIR / f"{cmd_id}.json"
        if not path.exists():
            print(f"  SKIP {cmd_id}: contract file not found")
            skipped += 1
            continue

        contract = json.loads(path.read_text())

        # Deep merge overrides
        for key, value in overrides.items():
            if isinstance(value, dict) and key in contract and isinstance(contract[key], dict):
                contract[key].update(value)
            else:
                contract[key] = value

        path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n")
        updated += 1
        print(f"  OK {cmd_id}")

    print(f"\nHydrated {updated} contracts, skipped {skipped}")
    print(f"Remaining generic: {len(list(CONTRACTS_DIR.glob('*.json'))) - updated}")


if __name__ == "__main__":
    hydrate()
