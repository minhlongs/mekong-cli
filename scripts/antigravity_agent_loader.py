#!/usr/bin/env python3
# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Antigravity Subagent Loader and Dispatch Helper.

Provides utilities to:
- List registered Antigravity subagents from .agents/subagents/registry.json
- Generate payload for Antigravity's `define_subagent` tool
- Validate agent system prompts and tool bindings
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = PROJECT_ROOT / ".agents" / "subagents" / "registry.json"


def load_registry() -> Dict[str, Any]:
    """Load the subagents registry JSON."""
    if not REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Registry file not found at {REGISTRY_PATH}. Run scripts/sync_antigravity.py first.")
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an agent record by ID."""
    registry = load_registry()
    for agent in registry.get("agents", []):
        if agent.get("id") == agent_id:
            return agent
    return None


def get_define_subagent_payload(agent_id: str) -> Dict[str, Any]:
    """Build the exact payload required by Antigravity's `define_subagent` tool."""
    agent = get_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent '{agent_id}' not found in registry.")

    def_path = PROJECT_ROOT / agent.get("definition_path", "")
    if not def_path.exists():
        raise FileNotFoundError(f"Definition file not found: {def_path}")

    system_prompt = def_path.read_text(encoding="utf-8")
    tools = [t.lower() for t in agent.get("tools", [])]

    # Map Mekong tool permissions to Antigravity flags
    enable_write = any(w in tools for w in ["write", "edit", "bash"])
    enable_subagents = agent.get("can_override", False) or "task" in tools
    enable_mcp = True

    return {
        "name": agent["id"].replace("-", "_"),
        "description": agent["description"],
        "system_prompt": system_prompt,
        "enable_write_tools": enable_write,
        "enable_subagent_tools": enable_subagents,
        "enable_mcp_tools": enable_mcp,
    }


def list_agents() -> None:
    """Print a formatted table of all registered subagents."""
    registry = load_registry()
    agents: List[Dict[str, Any]] = registry.get("agents", [])

    print(f"\nRegistered Antigravity Subagents ({len(agents)} total):")
    print(f"{'ID':<18} | {'Role':<24} | {'Model Tier':<10} | {'Override':<8} | {'Context'}")
    print("-" * 75)
    for a in agents:
        agent_id = a.get("id", "")
        role = a.get("role", "")[:24]
        model = a.get("model_tier", "inherit")
        override = "YES" if a.get("can_override") else "NO"
        ctx = f"{a.get('context_budget', 0):,} tok"
        print(f"{agent_id:<18} | {role:<24} | {model:<10} | {override:<8} | {ctx}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Antigravity Subagent Loader")
    parser.add_argument("--list", action="store_true", help="List all registered subagents")
    parser.add_argument("--get", type=str, metavar="AGENT_ID", help="Get define_subagent JSON payload for agent")
    parser.add_argument("--all-payloads", action="store_true", help="Export all define_subagent payloads as JSON")

    args = parser.parse_args()

    if args.list or len(sys.argv) == 1:
        list_agents()
        return

    if args.get:
        payload = get_define_subagent_payload(args.get)
        print(json.dumps(payload, indent=2))
        return

    if args.all_payloads:
        registry = load_registry()
        payloads = [get_define_subagent_payload(a["id"]) for a in registry.get("agents", [])]
        print(json.dumps(payloads, indent=2))
        return


if __name__ == "__main__":
    main()
