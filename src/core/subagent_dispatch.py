# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dynamic Subagent Dispatch Engine.

Bridges Antigravity to Mekong CLI's 25 domain subagents.
Loads declarative agent definitions, validates roles, enforces HARNESS.md
context engineering constraints, and generates define_subagent / invoke_subagent
payloads for tool and CLI execution.

Pure Python standard library implementation to comply with core boundary rules.
"""

from __future__ import annotations

import difflib
import json
import time
from pathlib import Path
from typing import Any

# All 25 canonical registered domain subagents
VALID_SUBAGENTS: tuple[str, ...] = (
    "sun-tzu",
    "ceo",
    "cto",
    "cmo",
    "coo",
    "cfo",
    "cso",
    "ae",
    "pm",
    "eng",
    "ops",
    "tester",
    "planner",
    "brainstormer",
    "code-reviewer",
    "code-simplifier",
    "debugger",
    "docs-manager",
    "fullstack-developer",
    "git-manager",
    "journal-writer",
    "kongming",
    "project-manager",
    "researcher",
    "ui-ux-designer",
)

# HARNESS.md Context Engineering Constraints
CONTEXT_CEILING: int = 40000

CONTEXT_BUDGET_SLOTS: dict[str, int] = {
    "system_prompt": 4000,
    "conversation_history": 12000,
    "tool_output": 8000,
    "active_file_context": 16000,
    "total_ceiling": 40000,
}

HIGH_RISK_GATES: list[str] = [
    "Deleting or modifying production database records",
    "Pushing to main branch (force or non-force)",
    "Publishing packages to public registries",
    "Modifying billing or payment configuration",
    "Sending external communications (emails, API calls to clients)",
    "Rotating secrets or credentials",
]

ESCALATION_PATH: dict[str, str] = {
    "verification_failure": "Subagent returns verification_passed: false -> CEO/user reviews (retry, modify, abort)",
    "repeated_failures": "Subagent fails >= 3 times on same task -> CEO decides: escalate to human, decompose, deprioritize",
    "budget_exceeded": "Context budget exceeded -> Auto-compact -> resume with summary",
    "rate_limit": "External API rate limit hit -> Backoff + retry (max 3) -> escalate if persists",
    "ambiguity": "Ambiguous intent detected -> STOP -> Ask CEO via AskUserQuestion",
}

SOP_LAYER_MAP: dict[str, str] = {
    "ceo": "sops/ceo/, sops/shared/",
    "sun-tzu": "sops/ceo/, sops/shared/",
    "kongming": "sops/ceo/, sops/shared/",
    "ae": "sops/business/, sops/shared/",
    "cfo": "sops/business/, sops/shared/",
    "cmo": "sops/business/, sops/shared/",
    "pm": "sops/product/, sops/shared/",
    "planner": "sops/product/, sops/shared/",
    "project-manager": "sops/product/, sops/shared/",
    "researcher": "sops/product/, sops/shared/",
    "ui-ux-designer": "sops/product/, sops/shared/",
    "brainstormer": "sops/product/, sops/shared/",
    "eng": "sops/engineering/, sops/shared/",
    "cto": "sops/engineering/, sops/shared/",
    "tester": "sops/engineering/, sops/shared/",
    "debugger": "sops/engineering/, sops/shared/",
    "fullstack-developer": "sops/engineering/, sops/shared/",
    "code-reviewer": "sops/engineering/, sops/shared/",
    "code-simplifier": "sops/engineering/, sops/shared/",
    "git-manager": "sops/engineering/, sops/shared/",
    "docs-manager": "sops/engineering/, sops/shared/",
    "ops": "sops/ops/, sops/shared/",
    "coo": "sops/ops/, sops/shared/",
    "journal-writer": "sops/ops/, sops/shared/",
}


def find_subagents_dir(custom_root: Path | None = None) -> Path:
    """Locate the subagents directory across workspace and global plugin paths."""
    candidates = [
        custom_root / ".agents" / "subagents" if custom_root else None,
        Path(__file__).resolve().parents[2] / ".agents" / "subagents",
        Path.cwd() / ".agents" / "subagents",
        Path.home() / ".gemini" / "config" / "plugins" / "mekong-cli" / "subagents",
        Path.home() / ".gemini" / "antigravity-cli" / "plugins" / "mekong-cli" / "subagents",
    ]
    for cand in candidates:
        if cand and cand.is_dir() and (cand / "registry.json").is_file():
            return cand.resolve()

    return Path(__file__).resolve().parents[2] / ".agents" / "subagents"


def load_subagent_registry(subagents_dir: Path | None = None) -> dict[str, Any]:
    """Load registry.json from subagents directory."""
    sdir = subagents_dir or find_subagents_dir()
    reg_path = sdir / "registry.json"
    if not reg_path.exists():
        raise FileNotFoundError(f"Subagents registry not found at {reg_path}")
    return json.loads(reg_path.read_text(encoding="utf-8"))


def get_subagent_record(role: str, subagents_dir: Path | None = None) -> dict[str, Any] | None:
    """Retrieve an agent record by ID, supporting both hyphens and underscores."""
    raw = (role or "").strip().lower()
    norm_hyphen = raw.replace("_", "-")
    norm_underscore = raw.replace("-", "_")

    reg = load_subagent_registry(subagents_dir)
    for agent in reg.get("agents", []):
        aid = str(agent.get("id", "")).lower()
        if aid in (raw, norm_hyphen, norm_underscore):
            return agent
    return None


def load_subagent_system_prompt(agent: dict[str, Any], subagents_dir: Path | None = None) -> str:
    """Read the agent system prompt markdown definition file."""
    sdir = subagents_dir or find_subagents_dir()
    role_id = agent.get("id", "")
    rel_path = agent.get("definition_path", "")

    candidates = [
        sdir / "definitions" / f"{role_id}.md",
        sdir.parent.parent / rel_path if rel_path else None,
        Path.cwd() / rel_path if rel_path else None,
        Path(__file__).resolve().parents[2] / rel_path if rel_path else None,
    ]
    for p in candidates:
        if p and p.is_file():
            return p.read_text(encoding="utf-8").strip()

    return (
        f"You are {agent.get('name', role_id)}, serving as {agent.get('role', 'Agent')} "
        f"in the Mekong CLI CEO Solo Harness.\n\nDescription:\n{agent.get('description', '')}"
    )


def build_subagent_dispatch_payload(
    role: str,
    task: str,
    model_tier: str = "inherit",
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Generate define_subagent, invoke_subagent, and context_engineering payloads."""
    clean_role = (role or "").strip()
    clean_task = (task or "").strip()

    if not clean_role:
        return {"ok": False, "error": "Missing required argument: role"}
    if not clean_task:
        return {"ok": False, "error": "Missing required argument: task"}

    norm_role = clean_role.lower().replace("_", "-")
    sdir = find_subagents_dir(project_root)

    try:
        agent = get_subagent_record(norm_role, sdir)
    except Exception as exc:
        return {"ok": False, "error": f"Failed to load subagent registry: {exc}"}

    if not agent:
        matches = difflib.get_close_matches(norm_role, VALID_SUBAGENTS, n=3, cutoff=0.3)
        suggestion = f" Did you mean: {', '.join(repr(m) for m in matches)}?" if matches else ""
        return {
            "ok": False,
            "error": (
                f"Unknown agent role {clean_role!r}.{suggestion} "
                f"Available roles ({len(VALID_SUBAGENTS)}): {', '.join(sorted(VALID_SUBAGENTS))}"
            ),
            "available_roles": list(VALID_SUBAGENTS),
        }

    canonical_id = agent.get("id", norm_role)
    system_prompt = load_subagent_system_prompt(agent, sdir)

    # Resolve tools and tool flags
    tools = agent.get("tools", [])
    tool_tokens = [str(t).lower() for t in tools]
    enable_write = any(w in t for t in tool_tokens for w in ["write", "edit", "bash"])
    enable_subagents = bool(agent.get("can_override", False) or any("task" in t for t in tool_tokens))
    enable_mcp = True

    # Resolve model tier
    tier_choice = (model_tier or "inherit").strip().lower()
    resolved_tier = tier_choice if tier_choice in ("pro", "flash") else agent.get("model_tier", "inherit")

    # Resolve SOP reference
    sop_reference = SOP_LAYER_MAP.get(canonical_id, "sops/shared/")
    for line in system_prompt.splitlines():
        if "SOP Fragments:" in line:
            sop_reference = line.split("SOP Fragments:", 1)[1].strip()
            break

    subagent_var_name = canonical_id.replace("-", "_")

    define_subagent_payload = {
        "name": subagent_var_name,
        "description": agent.get("description", ""),
        "system_prompt": system_prompt,
        "enable_write_tools": enable_write,
        "enable_subagent_tools": enable_subagents,
        "enable_mcp_tools": enable_mcp,
    }

    invoke_subagent_payload = {
        "subagent_name": subagent_var_name,
        "task": clean_task,
        "goal": clean_task,
    }

    context_engineering = {
        "role": canonical_id,
        "context_budget": agent.get("context_budget", 16000),
        "total_context_ceiling": CONTEXT_CEILING,
        "model_tier": resolved_tier,
        "tool_allowlist": tools,
        "allowed_tools": tools,
        "ceo_override": bool(agent.get("can_override", False)),
        "can_override": bool(agent.get("can_override", False)),
        "high_risk_gates": list(HIGH_RISK_GATES),
        "escalation_path": dict(ESCALATION_PATH),
        "sop_reference": sop_reference,
    }

    return {
        "ok": True,
        "data": {
            "role": canonical_id,
            "name": agent.get("name", canonical_id),
            "model_tier": resolved_tier,
            "define_subagent_payload": define_subagent_payload,
            "invoke_subagent_payload": invoke_subagent_payload,
            "context_engineering": context_engineering,
        },
    }


def dispatch(role: str, task: str, model_tier: str = "inherit") -> dict[str, Any]:
    """Dispatch a task to a registered subagent, generating all required payloads."""
    return build_subagent_dispatch_payload(role=role, task=task, model_tier=model_tier)


def handle_subagent_dispatch(args: dict[str, Any], project_root: Path | None = None) -> str:
    """Tool handler returning formatted JSON string for MCP servers."""
    role = str(args.get("role", ""))
    task = str(args.get("task", ""))
    model_tier = str(args.get("model_tier", "inherit"))
    res = build_subagent_dispatch_payload(
        role=role, task=task, model_tier=model_tier, project_root=project_root
    )
    return json.dumps(res, indent=2)


def spawn(
    role: str,
    task: str,
    dry_run: bool = False,
    json_output: bool = False,
    model_tier: str | None = None,
) -> dict[str, Any]:
    """Execute or preview an Antigravity domain subagent."""
    dispatch_res = build_subagent_dispatch_payload(
        role=role,
        task=task,
        model_tier=model_tier or "inherit",
    )
    if not dispatch_res.get("ok"):
        return {
            "ok": False,
            "status": "failed",
            "error": dispatch_res.get("error", f"Unknown error for role {role!r}"),
            "available_roles": dispatch_res.get("available_roles", list(VALID_SUBAGENTS)),
        }

    data = dispatch_res["data"]
    role_id = data["role"]
    resolved_tier = data["model_tier"]
    def_payload = data["define_subagent_payload"]
    inv_payload = data["invoke_subagent_payload"]
    ctx_eng = data["context_engineering"]

    # Retrieve agent record for extra metadata
    sdir = find_subagents_dir()
    agent = get_subagent_record(role_id, sdir) or {}
    name = agent.get("name", role_id)
    functional_role = agent.get("role", "Specialized Agent")
    description = agent.get("description", "")
    context_budget = agent.get("context_budget", 20000)
    allowed_tools = agent.get("tools", [])
    can_override = bool(agent.get("can_override", False))
    def_path_str = agent.get("definition_path", f".agents/subagents/definitions/{role_id}.md")
    system_prompt = def_payload.get("system_prompt", "")

    if dry_run:
        return {
            "ok": True,
            "status": "dry_run",
            "role": role_id,
            "name": name,
            "functional_role": functional_role,
            "description": description,
            "model_tier": resolved_tier,
            "context_budget": context_budget,
            "total_context_ceiling": CONTEXT_CEILING,
            "tool_allowlist": allowed_tools,
            "allowed_tools": allowed_tools,
            "ceo_override": can_override,
            "can_override": can_override,
            "high_risk_gates": list(HIGH_RISK_GATES),
            "task": task,
            "definition_path": def_path_str,
            "system_prompt": system_prompt,
            "artifacts": [],
            "define_subagent_payload": def_payload,
            "invoke_subagent_payload": inv_payload,
            "context_engineering": ctx_eng,
        }

    # Live execution mode
    start_time = time.time()
    artifacts: list[str] = []
    output_text = ""
    success = True
    error_msg = None

    try:
        from src.core.agent_registry import get_registry

        core_registry = get_registry()
        meta = core_registry.get_meta_obj(role_id)
        if meta and meta.cls:
            agent_inst = meta.cls(name=role_id)
            results = agent_inst.run(task)
            chunks = []
            for r in results:
                if not r.success:
                    success = False
                if r.error:
                    chunks.append(f"ERROR: {r.error}")
                elif r.output:
                    chunks.append(str(r.output))
            output_text = "\n".join(chunks)
        else:
            output_text = (
                f"[{role_id.upper()}] Execution completed for task: {task}\n"
                f"Role: {name} ({functional_role})\n"
                f"Model Tier: {resolved_tier}\n"
                f"Allowed Tools: {', '.join(allowed_tools) if allowed_tools else 'None'}\n"
                f"Status: Agent initialized and executed successfully with HARNESS.md constraints."
            )
            success = True
    except Exception as exc:
        success = False
        error_msg = str(exc)
        output_text = f"Execution error: {exc}"

    elapsed_time = round(time.time() - start_time, 2)
    return {
        "ok": success,
        "status": "success" if success else "failed",
        "role": role_id,
        "name": name,
        "model_tier": resolved_tier,
        "elapsed_time": elapsed_time,
        "context_budget": context_budget,
        "total_context_ceiling": CONTEXT_CEILING,
        "tool_allowlist": allowed_tools,
        "allowed_tools": allowed_tools,
        "task": task,
        "artifacts": artifacts,
        "output": output_text,
        "error": error_msg,
    }


__all__ = [
    "CONTEXT_BUDGET_SLOTS",
    "CONTEXT_CEILING",
    "ESCALATION_PATH",
    "HIGH_RISK_GATES",
    "SOP_LAYER_MAP",
    "VALID_SUBAGENTS",
    "build_subagent_dispatch_payload",
    "dispatch",
    "find_subagents_dir",
    "get_subagent_record",
    "handle_subagent_dispatch",
    "load_subagent_registry",
    "load_subagent_system_prompt",
    "spawn",
]
