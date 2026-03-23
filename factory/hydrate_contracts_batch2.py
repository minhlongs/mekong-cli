#!/usr/bin/env python3
"""Hydrate factory contracts — Batch 2 (30 more commands).

Run: python3 factory/hydrate_contracts_batch2.py
"""

import json
from pathlib import Path

CONTRACTS_DIR = Path("factory/contracts/commands")

HYDRATIONS: dict[str, dict] = {
    # ═══ STUDIO / VC ═══
    "fundraise": {
        "display": {"description_en": "Fundraise preparation — pitch deck, financial model, investor targeting"},
        "execution": {"agents": ["strategist", "cfo"], "hub": "founder-hub", "credit_cost": 5, "requires_approval": True},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "round": {"type": "string", "enum": ["pre-seed", "seed", "series-a", "series-b"]}, "target_raise": {"type": "number"}}},
        "output": {"type": "object", "properties": {"pitch_deck_path": {"type": "string"}, "financial_model": {"type": "object"}, "investor_list": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "fit_score": {"type": "number"}}}}, "valuation_range": {"type": "object", "properties": {"low": {"type": "number"}, "high": {"type": "number"}}}}},
    },
    "pitch": {
        "display": {"description_en": "Create investor pitch deck with narrative and data"},
        "execution": {"agents": ["strategist", "editor"], "hub": "founder-hub", "credit_cost": 3},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "audience": {"type": "string", "enum": ["investors", "customers", "partners"]}, "duration_minutes": {"type": "integer", "default": 10}}},
        "output": {"type": "object", "properties": {"slides": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "content": {"type": "string"}, "notes": {"type": "string"}}}}, "talking_points": {"type": "array", "items": {"type": "string"}}}},
    },

    # ═══ ENGINEERING — DEEP ═══
    "refactor": {
        "display": {"description_en": "Refactor code — improve structure without changing behavior"},
        "execution": {"agents": ["fullstack-developer", "code-reviewer"], "hub": "engineering-hub", "credit_cost": 3},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "scope": {"type": "string", "enum": ["file", "module", "system"]}, "target_files": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"files_modified": {"type": "array", "items": {"type": "string"}}, "lines_removed": {"type": "integer"}, "complexity_reduction": {"type": "string"}, "tests_passing": {"type": "boolean"}}},
        "cascade": {"triggers": [{"pattern": ".*", "suggest": "test", "target_layer": "engineering"}]},
    },
    "migrate": {
        "display": {"description_en": "Database migration — schema changes, data transforms"},
        "execution": {"agents": ["fullstack-developer"], "hub": "engineering-hub", "credit_cost": 2, "requires_approval": True},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "database": {"type": "string", "enum": ["d1", "postgres", "supabase"]}, "direction": {"type": "string", "enum": ["up", "down"]}}},
        "output": {"type": "object", "properties": {"migration_file": {"type": "string"}, "tables_affected": {"type": "array", "items": {"type": "string"}}, "rollback_available": {"type": "boolean"}}},
    },

    # ═══ BUSINESS — OPERATIONS ═══
    "hr": {
        "display": {"description_en": "HR operations — hiring, onboarding, team management"},
        "execution": {"agents": ["coo"], "hub": "hr-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "action": {"type": "string", "enum": ["hire", "onboard", "review", "offboard"]}}},
        "output": {"type": "object", "properties": {"action_items": {"type": "array", "items": {"type": "string"}}, "documents": {"type": "array", "items": {"type": "string"}}, "timeline": {"type": "string"}}},
    },
    "budget": {
        "display": {"description_en": "Budget planning — allocation, forecasting, variance analysis"},
        "execution": {"agents": ["cfo"], "hub": "finance-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "period": {"type": "string", "enum": ["monthly", "quarterly", "annual"]}, "departments": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"total_budget": {"type": "number"}, "allocations": {"type": "array", "items": {"type": "object", "properties": {"department": {"type": "string"}, "amount": {"type": "number"}, "percent": {"type": "number"}}}}, "forecast": {"type": "object"}}},
    },
    "brand": {
        "display": {"description_en": "Brand strategy — identity, voice, positioning, guidelines"},
        "execution": {"agents": ["cmo", "editor"], "hub": "marketing-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "brand_type": {"type": "string", "enum": ["personal", "corporate", "product"]}}},
        "output": {"type": "object", "properties": {"brand_voice": {"type": "string"}, "positioning_statement": {"type": "string"}, "color_palette": {"type": "array", "items": {"type": "string"}}, "guidelines_path": {"type": "string"}}},
    },

    # ═══ PRODUCT ═══
    "scope": {
        "display": {"description_en": "Scope definition — boundaries, requirements, acceptance criteria"},
        "execution": {"agents": ["pm", "planner"], "hub": "product-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "scope_type": {"type": "string", "enum": ["feature", "sprint", "project"]}}},
        "output": {"type": "object", "properties": {"in_scope": {"type": "array", "items": {"type": "string"}}, "out_of_scope": {"type": "array", "items": {"type": "string"}}, "acceptance_criteria": {"type": "array", "items": {"type": "string"}}, "effort_estimate": {"type": "string"}}},
        "cascade": {"triggers": [{"pattern": ".*", "suggest": "plan", "target_layer": "product"}]},
    },
    "roadmap": {
        "display": {"description_en": "Product roadmap — quarters, milestones, feature timeline"},
        "execution": {"agents": ["pm", "strategist"], "hub": "product-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "horizon": {"type": "string", "enum": ["quarterly", "annual", "multi-year"]}}},
        "output": {"type": "object", "properties": {"quarters": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "themes": {"type": "array", "items": {"type": "string"}}, "features": {"type": "array", "items": {"type": "string"}}}}}, "milestones": {"type": "array", "items": {"type": "string"}}}},
    },
    "backlog": {
        "display": {"description_en": "Backlog management — prioritize, estimate, groom"},
        "execution": {"agents": ["pm"], "hub": "product-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "action": {"type": "string", "enum": ["groom", "prioritize", "estimate"]}}},
        "output": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {"title": {"type": "string"}, "priority": {"type": "string"}, "estimate": {"type": "string"}, "status": {"type": "string"}}}}, "total_points": {"type": "integer"}}},
    },

    # ═══ OPS — DEVOPS ═══
    "clean": {
        "display": {"description_en": "Clean project — remove build artifacts, caches, temp files"},
        "execution": {"agents": ["devops"], "hub": "ops-hub", "credit_cost": 0, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "targets": {"type": "array", "items": {"type": "string", "enum": ["build", "cache", "deps", "all"]}}}},
        "output": {"type": "object", "properties": {"files_removed": {"type": "integer"}, "space_freed_mb": {"type": "number"}, "paths_cleaned": {"type": "array", "items": {"type": "string"}}}},
    },

    # ═══ WRITER / CONTENT ═══
    "seo": {
        "display": {"description_en": "SEO analysis — keywords, rankings, optimization recommendations"},
        "execution": {"agents": ["researcher", "cmo"], "hub": "marketing-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "url": {"type": "string"}, "target_keywords": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"score": {"type": "number"}, "keywords": {"type": "array", "items": {"type": "object", "properties": {"keyword": {"type": "string"}, "volume": {"type": "integer"}, "difficulty": {"type": "number"}, "position": {"type": "integer"}}}}, "recommendations": {"type": "array", "items": {"type": "string"}}}},
    },
    "email": {
        "display": {"description_en": "Email sequences — drip campaigns, newsletters, transactional"},
        "execution": {"agents": ["editor", "cmo"], "hub": "marketing-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "email_type": {"type": "string", "enum": ["drip", "newsletter", "transactional", "cold"]}, "sequence_length": {"type": "integer"}}},
        "output": {"type": "object", "properties": {"emails": {"type": "array", "items": {"type": "object", "properties": {"subject": {"type": "string"}, "body": {"type": "string"}, "send_day": {"type": "integer"}, "cta": {"type": "string"}}}}}},
    },

    # ═══ SALES ═══
    "crm": {
        "display": {"description_en": "CRM operations — contacts, deals, pipeline management"},
        "execution": {"agents": ["sales"], "hub": "sales-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "action": {"type": "string", "enum": ["add-contact", "update-deal", "pipeline-report", "segment"]}}},
        "output": {"type": "object", "properties": {"contacts_affected": {"type": "integer"}, "deals_updated": {"type": "integer"}, "pipeline_value": {"type": "number"}, "next_actions": {"type": "array", "items": {"type": "string"}}}},
    },

    # ═══ SYNC / GIT OPS ═══
    "git-status": {
        "display": {"description_en": "Git status overview — branches, changes, PR status"},
        "execution": {"agents": ["devops"], "hub": "ops-hub", "credit_cost": 0, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "repo": {"type": "string"}}},
        "output": {"type": "object", "properties": {"branch": {"type": "string"}, "changes": {"type": "integer"}, "ahead": {"type": "integer"}, "behind": {"type": "integer"}, "open_prs": {"type": "integer"}}},
    },
    "git-pr": {
        "display": {"description_en": "Create or manage pull requests"},
        "execution": {"agents": ["devops"], "hub": "engineering-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "action": {"type": "string", "enum": ["create", "review", "merge", "close"]}, "branch": {"type": "string"}}},
        "output": {"type": "object", "properties": {"pr_url": {"type": "string"}, "pr_number": {"type": "integer"}, "status": {"type": "string"}, "reviewers": {"type": "array", "items": {"type": "string"}}}},
    },

    # ═══ DOCS ═══
    "docs-init": {
        "display": {"description_en": "Initialize project documentation structure"},
        "execution": {"agents": ["editor"], "hub": "ops-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "project_type": {"type": "string"}}},
        "output": {"type": "object", "properties": {"files_created": {"type": "array", "items": {"type": "string"}}, "structure": {"type": "string"}}},
    },
    "docs-update": {
        "display": {"description_en": "Update documentation based on code changes"},
        "execution": {"agents": ["editor"], "hub": "ops-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "scope": {"type": "string", "enum": ["api", "readme", "architecture", "all"]}}},
        "output": {"type": "object", "properties": {"files_updated": {"type": "array", "items": {"type": "string"}}, "sections_changed": {"type": "integer"}}},
    },

    # ═══ ANALYTICS / DATA ═══
    "analytics": {
        "display": {"description_en": "Analytics dashboard — metrics, trends, insights"},
        "execution": {"agents": ["data"], "hub": "ops-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "metric_type": {"type": "string", "enum": ["revenue", "usage", "engagement", "performance"]}, "period": {"type": "string"}}},
        "output": {"type": "object", "properties": {"metrics": {"type": "object"}, "trends": {"type": "array", "items": {"type": "object", "properties": {"metric": {"type": "string"}, "direction": {"type": "string"}, "change_percent": {"type": "number"}}}}, "insights": {"type": "array", "items": {"type": "string"}}}},
    },

    # ═══ REMAINING HIGH-USE ═══
    "campaign": {
        "display": {"description_en": "Marketing campaign — multi-channel execution plan"},
        "execution": {"agents": ["cmo", "editor"], "hub": "marketing-hub", "credit_cost": 3},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "channels": {"type": "array", "items": {"type": "string"}}, "budget": {"type": "number"}, "duration_days": {"type": "integer"}}},
        "output": {"type": "object", "properties": {"timeline": {"type": "array", "items": {"type": "object", "properties": {"day": {"type": "integer"}, "channel": {"type": "string"}, "action": {"type": "string"}}}}, "budget_breakdown": {"type": "object"}, "kpis": {"type": "array", "items": {"type": "string"}}}},
    },
    "tam": {
        "display": {"description_en": "Total Addressable Market analysis — market sizing and segmentation"},
        "execution": {"agents": ["researcher", "strategist"], "hub": "business-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "market": {"type": "string"}, "geography": {"type": "string"}}},
        "output": {"type": "object", "properties": {"tam": {"type": "number"}, "sam": {"type": "number"}, "som": {"type": "number"}, "growth_rate": {"type": "number"}, "segments": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "size": {"type": "number"}, "growth": {"type": "number"}}}}}},
    },
    "positioning": {
        "display": {"description_en": "Market positioning — differentiation, value proposition, messaging"},
        "execution": {"agents": ["strategist", "cmo"], "hub": "business-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "target_segment": {"type": "string"}, "competitors": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"positioning_statement": {"type": "string"}, "value_props": {"type": "array", "items": {"type": "string"}}, "messaging_pillars": {"type": "array", "items": {"type": "string"}}, "differentiation_map": {"type": "object"}}},
    },
    "market": {
        "display": {"description_en": "Market analysis — trends, opportunities, competitive landscape"},
        "execution": {"agents": ["researcher", "strategist"], "hub": "business-hub", "credit_cost": 2},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "industry": {"type": "string"}, "depth": {"type": "string", "enum": ["quick", "standard", "deep"]}}},
        "output": {"type": "object", "properties": {"market_size": {"type": "number"}, "growth_rate": {"type": "number"}, "key_players": {"type": "array", "items": {"type": "string"}}, "trends": {"type": "array", "items": {"type": "string"}}, "opportunities": {"type": "array", "items": {"type": "string"}}}},
    },

    # ═══ INFRA ═══
    "benchmark": {
        "display": {"description_en": "Performance benchmark — latency, throughput, resource usage"},
        "execution": {"agents": ["devops"], "hub": "ops-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "target": {"type": "string"}, "iterations": {"type": "integer", "default": 100}}},
        "output": {"type": "object", "properties": {"p50_ms": {"type": "number"}, "p95_ms": {"type": "number"}, "p99_ms": {"type": "number"}, "throughput_rps": {"type": "number"}, "memory_mb": {"type": "number"}, "cpu_percent": {"type": "number"}}},
    },
    "cost": {
        "display": {"description_en": "Cost analysis — infrastructure, LLM usage, burn rate"},
        "execution": {"agents": ["cfo", "devops"], "hub": "ops-hub", "credit_cost": 1},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]}}},
        "output": {"type": "object", "properties": {"total_cost": {"type": "number"}, "breakdown": {"type": "array", "items": {"type": "object", "properties": {"category": {"type": "string"}, "amount": {"type": "number"}, "trend": {"type": "string"}}}}, "savings_opportunities": {"type": "array", "items": {"type": "string"}}}},
    },
    "monitor": {
        "display": {"description_en": "System monitoring — alerts, metrics, dashboards"},
        "execution": {"agents": ["devops"], "hub": "ops-hub", "credit_cost": 0, "complexity": "simple"},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "services": {"type": "array", "items": {"type": "string"}}}},
        "output": {"type": "object", "properties": {"alerts": {"type": "array", "items": {"type": "object", "properties": {"severity": {"type": "string"}, "service": {"type": "string"}, "message": {"type": "string"}}}}, "uptime_percent": {"type": "number"}, "error_rate": {"type": "number"}}},
    },
    "incident": {
        "display": {"description_en": "Incident response — triage, mitigate, resolve, postmortem"},
        "execution": {"agents": ["devops", "fullstack-developer"], "hub": "ops-hub", "credit_cost": 3, "requires_approval": True},
        "input": {"type": "object", "required": ["goal"], "properties": {"goal": {"type": "string"}, "severity": {"type": "string", "enum": ["p0", "p1", "p2", "p3"]}, "service": {"type": "string"}}},
        "output": {"type": "object", "properties": {"root_cause": {"type": "string"}, "mitigation": {"type": "string"}, "resolution": {"type": "string"}, "duration_minutes": {"type": "integer"}, "postmortem_path": {"type": "string"}, "action_items": {"type": "array", "items": {"type": "string"}}}},
    },
}


def hydrate() -> None:
    """Apply typed schemas to existing contracts."""
    updated = 0
    skipped = 0
    for cmd_id, overrides in HYDRATIONS.items():
        path = CONTRACTS_DIR / f"{cmd_id}.json"
        if not path.exists():
            print(f"  SKIP {cmd_id}: not found")
            skipped += 1
            continue
        contract = json.loads(path.read_text())
        for key, value in overrides.items():
            if isinstance(value, dict) and key in contract and isinstance(contract[key], dict):
                contract[key].update(value)
            else:
                contract[key] = value
        path.write_text(json.dumps(contract, indent=2, ensure_ascii=False) + "\n")
        updated += 1
        print(f"  OK {cmd_id}")
    print(f"\nBatch 2: {updated} hydrated, {skipped} skipped")


if __name__ == "__main__":
    hydrate()
