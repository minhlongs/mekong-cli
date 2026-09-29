#!/usr/bin/env python3
# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI — Standalone Stdio Launch Bridge for Model Context Protocol (MCP).

Provides portable, dual-mode MCP servers for Google Antigravity and AI coding agents:
1. mekong-core (default): Exposes the 14 core Mekong AI OS tools:
   - Memory: mekong_memory_store, mekong_memory_recall, mekong_memory_search
   - Plans: mekong_plan_create, mekong_plan_update, mekong_plan_get
   - Tasks: mekong_task_create, mekong_task_update, mekong_task_list
   - Agents: mekong_agent_list, mekong_agent_info, mekong_agent_route
   - System: mekong_status, mekong_cost_estimate
2. mekong-fabric (--fabric): Exposes the 302 Command Fabric catalog tools.

Supports dual-execution engines:
- FastMCP Engine: Full FastMCP SDK integration if installed.
- Pure-Python JSON-RPC 2.0 Engine: Zero-dependency stdio server resilient to
  missing SDK or forced via MEKONG_FORCE_MCP_FALLBACK=1 or --fallback.
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import os
import sys
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Virtual Environment Auto-Detection and Re-Exec
# ---------------------------------------------------------------------------


def ensure_virtualenv() -> None:
    """If running under system Python and a project venv exists, re-exec under venv."""
    if (
        os.environ.get("MEKONG_VENV_ACTIVATED") == "1"
        or os.environ.get("MEKONG_NO_REEXEC") == "1"
        or "-c" in sys.argv
    ):
        return

    # If already running inside an active virtualenv, no re-exec needed
    if sys.prefix != sys.base_prefix:
        return

    # Discover project root
    project_root = Path(__file__).resolve().parent.parent
    if not (project_root / "src" / "core").is_dir():
        for cand in [Path.cwd(), Path(__file__).resolve().parents[2]]:
            if (cand / "src" / "core").is_dir():
                project_root = cand
                break

    candidate_venvs = [
        project_root / ".venv" / "bin" / "python",
        project_root / "venv" / "bin" / "python",
        project_root / ".venv" / "bin" / "python3",
        project_root / "venv" / "bin" / "python3",
        project_root / ".venv" / "Scripts" / "python.exe",
        project_root / "venv" / "Scripts" / "python.exe",
    ]

    current_exe = Path(sys.executable).resolve()
    for venv_py in candidate_venvs:
        if venv_py.is_file() and os.access(venv_py, os.X_OK):
            try:
                if current_exe == venv_py.resolve() or current_exe.parent.resolve() == venv_py.parent.resolve():
                    return
            except Exception:
                pass

            os.environ["MEKONG_VENV_ACTIVATED"] = "1"
            try:
                os.execv(str(venv_py), [str(venv_py)] + sys.argv)
            except Exception as exc:
                sys.stderr.write(f"Warning: Failed to re-exec in virtualenv {venv_py}: {exc}\n")
            return


# ---------------------------------------------------------------------------
# Workspace Root & sys.path Injection
# ---------------------------------------------------------------------------


def inject_sys_path() -> Path:
    """Locate Mekong project root and ensure it is at the head of sys.path."""
    candidates = [
        Path(os.environ.get("MEKONG_ROOT", "")),
        Path(__file__).resolve().parent.parent,
        Path(__file__).resolve().parents[2] if len(Path(__file__).resolve().parents) > 2 else Path.cwd(),
        Path.cwd(),
    ]
    for candidate in candidates:
        if candidate and (candidate / "src" / "core").is_dir():
            root_str = str(candidate.resolve())
            if root_str not in sys.path:
                sys.path.insert(0, root_str)
            return candidate.resolve()

    default_root = Path(__file__).resolve().parent.parent
    root_str = str(default_root.resolve())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return default_root.resolve()


# Initialise workspace root so imports resolve cleanly
PROJECT_ROOT = inject_sys_path()

# Configure logging strictly to stderr to prevent contaminating stdout
logger = logging.getLogger("mcp_server")
logging.basicConfig(
    stream=sys.stderr,
    level=os.getenv("LOG_LEVEL", "WARNING").upper(),
    format="%(levelname)s [%(name)s]: %(message)s",
)

# ---------------------------------------------------------------------------
# Detect FastMCP Availability
# ---------------------------------------------------------------------------

_HAS_FASTMCP = False
try:
    from mcp.server.fastmcp import FastMCP  # type: ignore[import-untyped]
    import mcp.types as mcp_types  # type: ignore[import-untyped]

    _HAS_FASTMCP = True

    # Monkeypatch types.JSONRPCMessage.model_validate_json to be permissive with initialize
    try:
        orig_mvj = mcp_types.JSONRPCMessage.model_validate_json

        def permissive_mvj(json_data: Any, *args: Any, **kwargs: Any) -> Any:
            if isinstance(json_data, (str, bytes)):
                try:
                    d = json.loads(json_data)
                    if isinstance(d, dict) and d.get("method") == "initialize":
                        params = d.setdefault("params", {})
                        params.setdefault("capabilities", {})
                        if "clientInfo" not in params or not isinstance(params["clientInfo"], dict):
                            params["clientInfo"] = {"name": "antigravity", "version": "1.0.0"}
                        else:
                            params["clientInfo"].setdefault("version", "1.0.0")
                        json_data = json.dumps(d)
                except Exception:
                    pass
            return orig_mvj(json_data, *args, **kwargs)

        mcp_types.JSONRPCMessage.model_validate_json = permissive_mvj  # type: ignore[assignment]
    except Exception:
        pass
except ImportError:
    FastMCP = None  # type: ignore[assignment]
    mcp_types = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Core 14 Tool Handlers
# ---------------------------------------------------------------------------


def handle_memory_store(args: dict[str, Any]) -> str:
    key = str(args.get("key", "")).strip()
    val = str(args.get("value", ""))
    ttl_raw = args.get("ttl")
    ttl = int(ttl_raw) if ttl_raw is not None and str(ttl_raw).isdigit() else None

    if not key or not val:
        return json.dumps({"ok": False, "error": "Missing required arguments: key, value"}, indent=2)

    try:
        from src.core.memory_canonical import MemoryStore

        store = MemoryStore()
        store.store(key=key, value=val.encode("utf-8"), ttl=ttl)
        return json.dumps({"ok": True, "data": {"key": key, "stored": True, "ttl": ttl}}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Memory store error: {exc}"}, indent=2)


def handle_memory_recall(args: dict[str, Any]) -> str:
    key = str(args.get("key", "")).strip()
    if not key:
        return json.dumps({"ok": False, "error": "Missing required argument: key"}, indent=2)

    try:
        from src.core.memory_canonical import MemoryStore

        store = MemoryStore()
        val_bytes = store.retrieve(key)
        if val_bytes is not None:
            return json.dumps(
                {"ok": True, "data": {"key": key, "value": val_bytes.decode("utf-8", errors="replace")}},
                indent=2,
            )

        # Fallback check directly in memory store entries
        for entry in reversed(getattr(store, "_entries", [])):
            if entry.goal == key and not store._is_entry_expired(entry):
                d = store._decode_entry_value(entry)
                if d is not None:
                    return json.dumps(
                        {"ok": True, "data": {"key": key, "value": d.decode("utf-8", errors="replace")}},
                        indent=2,
                    )
                return json.dumps({"ok": True, "data": {"key": key, "entry": asdict(entry)}}, indent=2)

        return json.dumps({"ok": False, "error": f"Memory key '{key}' not found"}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Memory recall error: {exc}"}, indent=2)


def handle_memory_search(args: dict[str, Any]) -> str:
    query = str(args.get("query", "")).strip()
    limit = int(args.get("limit", 10))
    if not query:
        return json.dumps({"ok": False, "error": "Missing required argument: query"}, indent=2)

    try:
        from src.core.memory_canonical import MemoryStore

        store = MemoryStore()
        hits = store.search(query=query, limit=limit)
        results = []
        for h in hits:
            results.append({
                "key": h.key,
                "score": getattr(h, "score", 1.0),
                "data": h.data.decode("utf-8", errors="replace") if hasattr(h, "data") and h.data else "",
                "metadata": getattr(h, "metadata", {}),
            })
        return json.dumps(
            {"ok": True, "data": {"query": query, "results": results, "count": len(results)}},
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Memory search error: {exc}"}, indent=2)


def handle_plan_create(args: dict[str, Any]) -> str:
    goal = str(args.get("goal", "")).strip()
    if not goal:
        return json.dumps({"ok": False, "error": "Missing required argument: goal"}, indent=2)

    try:
        from src.core.mcp_plan_store import get_plan_store

        store = get_plan_store()
        plan = store.create(goal=goal)
        return json.dumps({"ok": True, "data": plan.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Plan create error: {exc}"}, indent=2)


def handle_plan_update(args: dict[str, Any]) -> str:
    plan_id = str(args.get("plan_id", "")).strip()
    status = str(args.get("status", "")).strip()
    task_id = str(args.get("task_id", "")).strip()
    task_status = str(args.get("task_status", "")).strip()

    if not plan_id:
        return json.dumps({"ok": False, "error": "Missing required argument: plan_id"}, indent=2)

    try:
        from src.core.mcp_plan_store import get_plan_store

        store = get_plan_store()
        plan = None
        if status == "completed":
            plan = store.complete(plan_id)
        if task_id and task_status:
            plan = store.update_task_status(plan_id, task_id, task_status)
        if plan is None:
            plan = store.get(plan_id)
        if plan:
            return json.dumps({"ok": True, "data": plan.to_dict()}, indent=2)
        return json.dumps({"ok": False, "error": f"Plan '{plan_id}' not found"}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Plan update error: {exc}"}, indent=2)


def handle_plan_get(args: dict[str, Any]) -> str:
    plan_id = str(args.get("plan_id", "")).strip()
    status = str(args.get("status", "")).strip()

    try:
        from src.core.mcp_plan_store import get_plan_store

        store = get_plan_store()
        if plan_id:
            plan = store.get(plan_id)
            if plan:
                return json.dumps({"ok": True, "data": plan.to_dict()}, indent=2)
            return json.dumps({"ok": False, "error": f"Plan '{plan_id}' not found"}, indent=2)

        plans = store.list(status=status)
        return json.dumps(
            {"ok": True, "data": {"plans": [p.to_dict() for p in plans], "count": len(plans)}},
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Plan get error: {exc}"}, indent=2)


def handle_task_create(args: dict[str, Any]) -> str:
    subject = str(args.get("subject", "")).strip()
    if not subject:
        return json.dumps({"ok": False, "error": "Missing required argument: subject"}, indent=2)

    try:
        from src.core.mcp_task_store import get_task_store

        store = get_task_store()
        task = store.create(subject=subject)
        return json.dumps({"ok": True, "data": {"task": task.to_dict()}}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Task create error: {exc}"}, indent=2)


def handle_task_update(args: dict[str, Any]) -> str:
    task_id = str(args.get("task_id", "")).strip()
    status = str(args.get("status", "")).strip()

    if not task_id or not status:
        return json.dumps({"ok": False, "error": "Missing required arguments: task_id, status"}, indent=2)

    try:
        from src.core.mcp_task_store import get_task_store

        store = get_task_store()
        task = store.update_status(task_id, status)
        if task:
            return json.dumps({"ok": True, "data": {"task": task.to_dict()}}, indent=2)
        return json.dumps({"ok": False, "error": f"Task '{task_id}' not found or invalid status '{status}'"}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Task update error: {exc}"}, indent=2)


def handle_task_list(args: dict[str, Any]) -> str:
    status = str(args.get("status", "")).strip()
    try:
        from src.core.mcp_task_store import get_task_store

        store = get_task_store()
        tasks = store.list(status=status)
        return json.dumps(
            {"ok": True, "data": {"tasks": [t.to_dict() for t in tasks], "count": len(tasks)}},
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Task list error: {exc}"}, indent=2)


def handle_agent_list(args: dict[str, Any]) -> str:
    agents: list[dict[str, Any]] = []
    seen: set[str] = set()

    try:
        from src.core.agent_registry import get_registry

        reg = get_registry()
        for meta in reg.discover():
            seen.add(meta.name)
            agents.append({
                "name": meta.name,
                "description": meta.description,
                "risk_level": getattr(meta, "risk_level", "LOW"),
                "allowed_tools": list(getattr(meta, "allowed_tools", [])),
                "spawnable_agents": list(getattr(meta, "spawnable_agents", [])),
            })
    except Exception as exc:
        sys.stderr.write(f"Agent registry discovery error: {exc}\n")

    # Augment with agents from agents/registry.yaml if present
    yaml_path = PROJECT_ROOT / "agents" / "registry.yaml"
    if yaml_path.exists():
        try:
            import yaml  # type: ignore[import-untyped]

            raw_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(raw_yaml, dict) and "agents" in raw_yaml and isinstance(raw_yaml["agents"], list):
                for a in raw_yaml["agents"]:
                    aid = str(a.get("id") or a.get("name", ""))
                    if aid and aid not in seen:
                        seen.add(aid)
                        agents.append({
                            "name": aid,
                            "description": a.get("description", ""),
                            "risk_level": a.get("risk_level", "LOW"),
                            "allowed_tools": a.get("tools", []),
                            "spawnable_agents": a.get("spawnable_agents", []),
                        })
        except Exception as exc:
            sys.stderr.write(f"YAML agent load error: {exc}\n")

    return json.dumps({"ok": True, "data": {"agents": agents, "count": len(agents)}}, indent=2)


def handle_agent_info(args: dict[str, Any]) -> str:
    name = str(args.get("name", "")).strip()
    if not name:
        return json.dumps({"ok": False, "error": "Missing required argument: name"}, indent=2)

    try:
        from src.core.agent_registry import get_registry

        reg = get_registry()
        meta = reg.get_meta_obj(name)
        if meta:
            return json.dumps(
                {
                    "ok": True,
                    "data": {
                        "name": meta.name,
                        "description": meta.description,
                        "risk_level": getattr(meta, "risk_level", "LOW"),
                        "approval_policy": getattr(meta, "approval_policy", "AUTO"),
                        "allowed_tools": list(getattr(meta, "allowed_tools", [])),
                        "spawnable_agents": list(getattr(meta, "spawnable_agents", [])),
                    },
                },
                indent=2,
            )
    except Exception as exc:
        sys.stderr.write(f"Agent info lookup error: {exc}\n")

    yaml_path = PROJECT_ROOT / "agents" / "registry.yaml"
    if yaml_path.exists():
        try:
            import yaml

            raw_yaml = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if isinstance(raw_yaml, dict) and "agents" in raw_yaml and isinstance(raw_yaml["agents"], list):
                for a in raw_yaml["agents"]:
                    if a.get("id") == name or a.get("name") == name:
                        return json.dumps(
                            {
                                "ok": True,
                                "data": {
                                    "name": a.get("id", name),
                                    "description": a.get("description", ""),
                                    "risk_level": a.get("risk_level", "LOW"),
                                    "approval_policy": a.get("approval_policy", "AUTO"),
                                    "allowed_tools": a.get("tools", []),
                                    "spawnable_agents": a.get("spawnable_agents", []),
                                },
                            },
                            indent=2,
                        )
        except Exception:
            pass

    return json.dumps({"ok": False, "error": f"Agent '{name}' not found"}, indent=2)


def handle_agent_route(args: dict[str, Any]) -> str:
    goal = str(args.get("goal", "")).strip()
    if not goal:
        return json.dumps({"ok": False, "error": "Missing required argument: goal"}, indent=2)

    try:
        from src.core.task_classifier import classify_task, classify_multi_agent

        profile = classify_task(goal)
        multi = classify_multi_agent(goal)
        return json.dumps(
            {
                "ok": True,
                "data": {
                    "goal": goal,
                    "assigned_agent": profile.agent_role,
                    "collaborating_agents": multi,
                    "domain": profile.domain,
                    "complexity": profile.complexity,
                    "mcu_cost": profile.mcu_cost,
                    "preferred_tier": profile.preferred_tier,
                },
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Agent route error: {exc}"}, indent=2)


def handle_status(args: dict[str, Any]) -> str:
    data: dict[str, Any] = {
        "status": "HEALTHY",
        "python": sys.version,
        "platform": sys.platform,
    }
    try:
        from src.core.memory_canonical import MemoryStore

        mem = MemoryStore()
        data["memory_stats"] = mem.stats() if hasattr(mem, "stats") else "available"
    except Exception as e:
        data["memory_stats"] = f"unavailable: {e}"

    try:
        from src.core.mcp_task_store import get_task_store

        tasks = get_task_store()
        data["tasks_stats"] = tasks.stats()
    except Exception as e:
        data["tasks_stats"] = f"unavailable: {e}"

    try:
        from src.core.mcp_plan_store import get_plan_store

        plans = get_plan_store()
        data["plans_stats"] = plans.stats()
    except Exception as e:
        data["plans_stats"] = f"unavailable: {e}"

    try:
        from src.core.agent_registry import get_registry

        reg = get_registry()
        data["registered_agents"] = len(reg.list_agents())
    except Exception as e:
        data["registered_agents"] = f"unavailable: {e}"

    return json.dumps({"ok": True, "data": data}, indent=2)


def handle_cost_estimate(args: dict[str, Any]) -> str:
    goal = str(args.get("goal", "")).strip()
    model_id = str(args.get("model_id", "claude-sonnet-4-6")).strip()
    if not goal:
        return json.dumps({"ok": False, "error": "Missing required argument: goal"}, indent=2)

    try:
        from src.core.task_classifier import classify_task
        from src.core.cost_estimator import estimate_cost

        profile = classify_task(goal)
        est = estimate_cost(profile, model_id=model_id or "claude-sonnet-4-6")
        return json.dumps(
            {
                "ok": True,
                "data": {
                    "goal": goal,
                    "model_id": model_id,
                    "complexity": profile.complexity,
                    "mcu_required": est.mcu_required,
                    "usd_llm_cost": est.usd_llm_cost,
                    "usd_infra_cost": est.usd_infra_cost,
                    "total_usd": est.total_usd,
                    "margin_usd": est.margin_usd,
                    "margin_pct": est.margin_pct,
                },
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Cost estimate error: {exc}"}, indent=2)


def handle_subagent_dispatch(args: dict[str, Any]) -> str:
    """Tool handler for mekong_subagent_dispatch."""
    try:
        from src.core.subagent_dispatch import handle_subagent_dispatch as _dispatch

        return _dispatch(args, project_root=PROJECT_ROOT)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Subagent dispatch error: {exc}"}, indent=2)


def _clean_str(val: Any) -> str | None:
    """Extract stripped string, returning None if empty or not a string."""
    if isinstance(val, str):
        s = val.strip()
        return s if s else None
    return None


def handle_pev_plan(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pev_plan."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    goal = _clean_str(args.get("goal"))
    if not goal:
        return json.dumps({"ok": False, "error": "Goal parameter is required", "code": "EMPTY_GOAL"}, indent=2)
    mission_id = _clean_str(args.get("mission_id"))
    try:
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        bridge = PEVSwarmBridge()
        plan = bridge.plan(goal=goal, mission_id=mission_id)
        return json.dumps({"ok": True, "plan": plan.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"PEV plan generation error: {exc}"}, indent=2)


def handle_pev_checkpoint(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pev_checkpoint."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    mission_id = _clean_str(args.get("mission_id"))
    if not mission_id:
        return json.dumps({"ok": False, "error": "mission_id parameter is required", "code": "EMPTY_MISSION_ID"}, indent=2)
    label = _clean_str(args.get("label")) or "manual"

    raw_files = args.get("files")
    if raw_files is not None:
        if isinstance(raw_files, str):
            files = [raw_files]
        elif isinstance(raw_files, (list, tuple)):
            if not all(isinstance(f, str) for f in raw_files):
                return json.dumps(
                    {
                        "ok": False,
                        "error": "files parameter must be an array of strings",
                        "code": "INVALID_FILES_PARAMETER",
                    },
                    indent=2,
                )
            files = [str(f) for f in raw_files if f]
        else:
            return json.dumps(
                {
                    "ok": False,
                    "error": "files parameter must be an array of strings",
                    "code": "INVALID_FILES_PARAMETER",
                },
                indent=2,
            )
    else:
        files = None

    raw_tests = args.get("test_results")
    if raw_tests is not None and not isinstance(raw_tests, dict):
        return json.dumps(
            {
                "ok": False,
                "error": "test_results parameter must be an object (dictionary)",
                "code": "INVALID_TEST_RESULTS_PARAMETER",
            },
            indent=2,
        )
    test_results = raw_tests

    try:
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        bridge = PEVSwarmBridge()
        cp_id = bridge.store.capture_checkpoint(
            mission_id=mission_id,
            label=label,
            files=files,
            test_results=test_results,
        )
        cp_rec = bridge.store.get_checkpoint(cp_id)
        return json.dumps(
            {
                "ok": True,
                "checkpoint_id": cp_id,
                "mission_id": mission_id,
                "label": label,
                "file_count": len(cp_rec.file_snapshots) if cp_rec else 0,
                "status": "captured",
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Checkpoint capture error: {exc}"}, indent=2)


def handle_pev_rollback(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pev_rollback."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    checkpoint_id = _clean_str(args.get("checkpoint_id"))
    if not checkpoint_id:
        return json.dumps({"ok": False, "error": "checkpoint_id parameter is required", "code": "EMPTY_CHECKPOINT_ID"}, indent=2)
    try:
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        bridge = PEVSwarmBridge()
        res = bridge.store.rollback_to_checkpoint(checkpoint_id)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Checkpoint rollback error: {exc}"}, indent=2)


def handle_swarm_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_swarm_status."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    mission_id = _clean_str(args.get("mission_id"))
    try:
        from src.core.pev_swarm_bridge import PEVSwarmBridge

        bridge = PEVSwarmBridge()
        if mission_id:
            res = bridge.get_mission_status(mission_id)
        else:
            cps = bridge.store.list_checkpoints()
            res = {
                "ok": True,
                "active_missions_count": len(cps),
                "checkpoints": cps[:10],
                "status": "idle" if not cps else "active",
            }
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Swarm status error: {exc}"}, indent=2)


def handle_eval_query(args: dict[str, Any]) -> str:
    """Tool handler for mekong_eval_query."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    agent_id = _clean_str(args.get("agent_id")) or "all"
    days_val = args.get("days", 7)
    limit_val = args.get("limit", 50)
    try:
        days = int(days_val) if days_val is not None else 7
    except (ValueError, TypeError):
        return json.dumps({"ok": False, "error": "days must be an integer", "code": "INVALID_DAYS_PARAMETER"}, indent=2)
    try:
        limit = int(limit_val) if limit_val is not None else 50
    except (ValueError, TypeError):
        return json.dumps({"ok": False, "error": "limit must be an integer", "code": "INVALID_LIMIT_PARAMETER"}, indent=2)

    try:
        from src.core.evals_bridge import query_evals

        res = query_evals(agent_id=agent_id, window_days=days, limit=limit)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Eval query error: {exc}"}, indent=2)


def handle_recipe_evolve(args: dict[str, Any]) -> str:
    """Tool handler for mekong_recipe_evolve."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    recipe_name = _clean_str(args.get("recipe_name")) or ""
    goal = _clean_str(args.get("goal")) or ""
    force = bool(args.get("force", False))

    try:
        from src.core.memory_canonical import MemoryStore
        from src.core.recipe_gen import RecipeGenerator
        from src.core.self_improve import SelfImprover

        improver = SelfImprover(MemoryStore(), RecipeGenerator())
        if recipe_name:
            entry = improver.evolve_recipe(recipe_name=recipe_name, target_goal=goal, force=force)
            stats = improver.get_evolution_stats()
            return json.dumps(
                {
                    "ok": True,
                    "evolved": entry is not None,
                    "recipe_name": recipe_name,
                    "action": entry.action if entry else "skipped",
                    "reason": entry.reason if entry else "Already at latest version",
                    "details": entry.data if entry else {},
                    "stats": stats,
                },
                indent=2,
            )
        else:
            entries = improver.analyze_and_improve()
            stats = improver.get_evolution_stats()
            return json.dumps(
                {
                    "ok": True,
                    "evolved": len(entries) > 0,
                    "total_actions": len(entries),
                    "actions": [e.to_dict() for e in entries],
                    "stats": stats,
                },
                indent=2,
            )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Recipe evolution error: {exc}"}, indent=2)


def handle_mission_metrics(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mission_metrics."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    agent_id = _clean_str(args.get("agent_id")) or "all"
    days_val = args.get("days", 7)
    try:
        days = int(days_val) if days_val is not None else 7
    except (ValueError, TypeError):
        return json.dumps({"ok": False, "error": "days must be an integer", "code": "INVALID_DAYS_PARAMETER"}, indent=2)

    try:
        from src.core.evals_bridge import query_evals

        res = query_evals(agent_id=agent_id, window_days=days, limit=10)
        summary = {
            "ok": True,
            "agent_id": agent_id,
            "window_days": days,
            "total_missions": res.get("total_missions", 0),
            "successful_missions": res.get("successful_missions", 0),
            "failed_missions": res.get("failed_missions", 0),
            "success_rate_pct": res.get("success_rate_pct", 0.0),
            "p95_duration_ms": res.get("p95_duration_ms", 0),
            "avg_duration_ms": res.get("avg_duration_ms", 0.0),
            "avg_credits": res.get("avg_credits", 0.0),
            "total_credits": res.get("total_credits", 0.0),
            "failure_clusters_count": len(res.get("failure_clusters", [])),
            "top_cluster": res["failure_clusters"][0]["category"] if res.get("failure_clusters") else "None",
            "recommendations": res.get("recommendations", []),
        }
        return json.dumps(summary, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mission metrics error: {exc}"}, indent=2)


def handle_palette_search(args: dict[str, Any]) -> str:
    """Tool handler for mekong_palette_search."""
    if not isinstance(args, dict):
        return json.dumps({"ok": False, "error": "Invalid arguments object", "code": "INVALID_ARGUMENTS"}, indent=2)
    query = _clean_str(args.get("query"))
    category = _clean_str(args.get("category")) or "all"
    limit_val = args.get("limit", 5)
    try:
        limit = int(limit_val) if limit_val is not None else 5
    except (ValueError, TypeError):
        return json.dumps({"ok": False, "error": "limit must be an integer", "code": "INVALID_LIMIT_PARAMETER"}, indent=2)

    try:
        from src.core.palette_bridge import PaletteBridge

        bridge = PaletteBridge()
        matches = bridge.search(query=query, category=category, limit=limit)
        return json.dumps(
            {
                "ok": True,
                "query": query,
                "category": category,
                "total_matches": len(matches),
                "matches": [m.to_dict() for m in matches],
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Palette search error: {exc}"}, indent=2)


def handle_tui_dashboard_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tui_dashboard_status."""
    if not isinstance(args, dict):
        args = {}
    detailed = bool(args.get("detailed", False))
    try:
        from src.core.palette_bridge import PaletteBridge

        bridge = PaletteBridge()
        summary = bridge.get_tui_dashboard_summary(detailed=detailed)
        return json.dumps(summary, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"TUI dashboard error: {exc}"}, indent=2)


def handle_benchmark_run(args: dict[str, Any]) -> str:
    """Tool handler for mekong_benchmark_run."""
    if not isinstance(args, dict):
        args = {}
    suite = _clean_str(args.get("suite")) or "all"
    iterations_val = args.get("iterations", 1)
    try:
        iterations = int(iterations_val) if iterations_val is not None else 1
    except (ValueError, TypeError):
        iterations = 1
    chaos_level = _clean_str(args.get("chaos_level")) or "none"

    try:
        from src.core.benchmark_bridge import BenchmarkBridge

        bridge = BenchmarkBridge()
        report = bridge.run_benchmark(
            suite=suite,
            iterations=iterations,
            chaos_level=chaos_level,
        )
        res = report.to_dict()
        res["ok"] = (report.total_failed == 0)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Benchmark run error: {exc}"}, indent=2)


def handle_chaos_simulate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_chaos_simulate."""
    if not isinstance(args, dict):
        args = {}
    target = _clean_str(args.get("target")) or "checkpoint"
    error_type = _clean_str(args.get("error_type")) or "corrupt_file"

    try:
        from src.core.benchmark_bridge import BenchmarkBridge

        bridge = BenchmarkBridge()
        result = bridge.simulate_chaos(target=target, error_type=error_type)
        res = result.to_dict()
        res["ok"] = result.self_healed
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Chaos simulation error: {exc}"}, indent=2)


def handle_gateway_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_gateway_status."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.gateway.streaming import get_mission_streaming_broker
        from src.core.gateway.rate_limiter import get_rate_limiter, get_telemetry_hub

        broker = get_mission_streaming_broker()
        limiter = get_rate_limiter()
        telemetry = get_telemetry_hub()

        broker_stats = broker.get_stats() if hasattr(broker, "get_stats") else {}
        metrics = telemetry.get_metrics() if hasattr(telemetry, "get_metrics") else {}
        health = telemetry.get_health() if hasattr(telemetry, "get_health") else {}

        active_streams = broker_stats.get(
            "active_subscribers",
            metrics.get("active_subscribers", metrics.get("active_streams", 0)),
        )
        active_ws = broker_stats.get("active_ws_connections", 0)
        uptime = broker_stats.get("uptime_seconds", health.get("uptime_seconds", 0.0))
        status_val = broker_stats.get("status", health.get("status", "healthy"))

        res = {
            "ok": True,
            "status": status_val,
            "uptime_seconds": uptime,
            "active_streams": active_streams,
            "active_ws_connections": active_ws,
            "system_metrics": {
                "rate_limit_rejections": metrics.get("rate_limit_rejections", 0),
                "total_requests": metrics.get("total_requests", 0),
                "latency_percentiles": metrics.get(
                    "latency_percentiles",
                    {
                        "p50_ms": metrics.get("p50_ms", 0.0),
                        "p90_ms": metrics.get("p90_ms", 0.0),
                        "p99_ms": metrics.get("p99_ms", 0.0),
                    },
                ),
                "p50_latency_ms": metrics.get("p50_ms", 0.0),
                "p90_latency_ms": metrics.get("p90_ms", 0.0),
                "p99_latency_ms": metrics.get("p99_ms", 0.0),
                "total_events_emitted": broker_stats.get("total_events_emitted", 0),
                "active_missions": broker_stats.get("active_missions", 0),
            },
        }
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Gateway status error: {exc}"}, indent=2)


def handle_gateway_rate_limit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_gateway_rate_limit."""
    import time

    if not isinstance(args, dict):
        args = {}
    tenant_id = _clean_str(args.get("tenant_id")) or "default"

    try:
        from src.core.gateway.rate_limiter import get_rate_limiter

        limiter = get_rate_limiter()
        quota = limiter.get_quota(tenant_id)

        limit_val = quota.get("limit", quota.get("capacity", 60))
        remaining_val = quota.get("remaining", limit_val)
        reset_ts = quota.get("reset_timestamp", int(time.time()))
        now_ts = int(time.time())
        reset_in = max(0, reset_ts - now_ts)
        retry_after = 0 if remaining_val > 0 else max(1, reset_in)

        res = {
            "ok": True,
            "tenant_id": quota.get("tenant_id", tenant_id),
            "tier": quota.get("tier", "free"),
            "limit": limit_val,
            "quota_limit": limit_val,
            "remaining": remaining_val,
            "tokens_remaining": remaining_val,
            "reset_timestamp": reset_ts,
            "reset_in_seconds": reset_in,
            "retry_after": retry_after,
        }
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Gateway rate limit error: {exc}"}, indent=2)


def handle_watch_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_watch_status."""
    try:
        from src.core.watcher_bridge import get_watch_daemon
        daemon = get_watch_daemon()
        status_dict = daemon.get_status()
        res = {
            "ok": True,
            "status": "running" if daemon.is_running() else "idle",
            "data": status_dict,
        }
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Watch status error: {exc}"}, indent=2)


def handle_self_repair(args: dict[str, Any]) -> str:
    """Tool handler for mekong_self_repair."""
    if not isinstance(args, dict):
        args = {}
    file_path = _clean_str(args.get("file_path"))
    error_detail = _clean_str(args.get("error_detail")) or ""
    mode = _clean_str(args.get("mode")) or "auto"
    if not file_path:
        return json.dumps({"ok": False, "error": "Missing required argument: file_path"}, indent=2)

    try:
        from src.core.watcher_bridge import get_watch_daemon
        daemon = get_watch_daemon()
        res = daemon.trigger_self_repair(file_path, mode=mode)
        return json.dumps({"ok": True, "data": res}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Self repair error: {exc}"}, indent=2)


def handle_package_build(args: dict[str, Any]) -> str:
    """Tool handler for mekong_package_build."""
    if not isinstance(args, dict):
        args = {}
    target = _clean_str(args.get("target")) or "all"
    output_dir = _clean_str(args.get("output_dir")) or "dist"
    try:
        from pathlib import Path
        from src.core.packaging_bridge import PackagingBridge

        bridge = PackagingBridge()
        report = bridge.build_distribution_package(target=target, output_dir=Path(output_dir))
        return json.dumps({"ok": True, "data": report.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Package build error: {exc}"}, indent=2)


def handle_sandbox_exec(args: dict[str, Any]) -> str:
    """Tool handler for mekong_sandbox_exec."""
    if not isinstance(args, dict):
        args = {}
    command = _clean_str(args.get("command"))
    if not command:
        return json.dumps({"ok": False, "error": "Missing required argument: command"}, indent=2)

    timeout = int(args.get("timeout", 30))
    memory = int(args.get("memory_limit_mb", 512))
    image = _clean_str(args.get("image")) or "python:3.11-slim"

    try:
        from src.core.sandbox_bridge import SandboxConfig, get_sandbox_harness

        harness = get_sandbox_harness()
        cfg = SandboxConfig(
            image=image,
            timeout_seconds=timeout,
            memory_limit_mb=memory,
        )
        res = harness.execute(command, config=cfg)
        return json.dumps({"ok": True, "data": res.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Sandbox execution error: {exc}"}, indent=2)


def handle_consensus_vote(args: dict[str, Any]) -> str:
    """Tool handler for mekong_consensus_vote."""
    if not isinstance(args, dict):
        args = {}
    proposal = _clean_str(args.get("proposal"))
    if not proposal:
        return json.dumps({"ok": False, "error": "Missing required argument: proposal"}, indent=2)

    quorum = _clean_str(args.get("quorum")) or "majority"
    agents_raw = args.get("agents")
    agents = None
    if isinstance(agents_raw, list):
        agents = [str(a) for a in agents_raw]
    elif isinstance(agents_raw, str):
        agents = [a.strip() for a in agents_raw.split(",") if a.strip()]

    try:
        from src.core.consensus_bridge import get_consensus_bridge

        bridge = get_consensus_bridge()
        ballot = bridge.create_vote(proposal=proposal, agents=agents, quorum=quorum)
        return json.dumps({"ok": True, "data": ballot.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Consensus vote error: {exc}"}, indent=2)


def handle_consensus_debate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_consensus_debate."""
    if not isinstance(args, dict):
        args = {}
    topic = _clean_str(args.get("topic"))
    if not topic:
        return json.dumps({"ok": False, "error": "Missing required argument: topic"}, indent=2)

    proponent = _clean_str(args.get("proponent")) or "cto"
    opponent = _clean_str(args.get("opponent")) or "sre"
    moderator = _clean_str(args.get("moderator")) or "ceo"
    rounds = int(args.get("rounds", 2))

    try:
        from src.core.consensus_bridge import get_consensus_bridge

        bridge = get_consensus_bridge()
        session = bridge.conduct_debate(
            topic=topic,
            proponent=proponent,
            opponent=opponent,
            moderator=moderator,
            rounds=rounds,
        )
        return json.dumps({"ok": True, "data": session.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Consensus debate error: {exc}"}, indent=2)


def handle_semantic_recall(args: dict[str, Any]) -> str:
    """Tool handler for mekong_semantic_recall."""
    if not isinstance(args, dict):
        args = {}
    query = _clean_str(args.get("query"))
    if not query:
        return json.dumps({"ok": False, "error": "Missing required argument: query"}, indent=2)

    domain = _clean_str(args.get("domain")) or "all"
    limit = int(args.get("limit", 5))

    try:
        from src.core.memory_federation import get_memory_federation_engine

        engine = get_memory_federation_engine()
        items = engine.query(query_text=query, domain=domain, limit=limit)
        return json.dumps(
            {
                "ok": True,
                "data": {
                    "query": query,
                    "domain": domain,
                    "total_results": len(items),
                    "items": [item.to_dict() for item in items],
                },
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Semantic recall error: {exc}"}, indent=2)


def handle_knowledge_graph_query(args: dict[str, Any]) -> str:
    """Tool handler for mekong_knowledge_graph_query."""
    if not isinstance(args, dict):
        args = {}
    entity = _clean_str(args.get("entity"))
    if not entity:
        return json.dumps({"ok": False, "error": "Missing required argument: entity"}, indent=2)

    depth = int(args.get("depth", 2))

    try:
        from src.core.memory_federation import get_memory_federation_engine

        engine = get_memory_federation_engine()
        graph = engine.query_knowledge_graph(entity=entity, depth=depth)
        return json.dumps({"ok": True, "data": graph}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Knowledge graph query error: {exc}"}, indent=2)


def handle_telemetry_metrics(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telemetry_metrics."""
    if not isinstance(args, dict):
        args = {}
    fmt = _clean_str(args.get("format_type")) or _clean_str(args.get("format")) or "prometheus"
    try:
        from src.core.telemetry_bridge import get_telemetry_bridge

        bridge = get_telemetry_bridge()
        if fmt.lower() == "json":
            return json.dumps({"ok": True, "data": bridge.metrics.to_dict()}, indent=2)
        return bridge.metrics.to_prometheus_text()
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telemetry metrics error: {exc}"}, indent=2)


def handle_trace_query(args: dict[str, Any]) -> str:
    """Tool handler for mekong_trace_query."""
    if not isinstance(args, dict):
        args = {}
    trace_id = _clean_str(args.get("trace_id"))
    limit = int(args.get("limit", 20))
    try:
        from src.core.telemetry_bridge import get_telemetry_bridge

        bridge = get_telemetry_bridge()
        spans = bridge.query_spans(trace_id=trace_id, limit=limit)
        return json.dumps(
            {
                "ok": True,
                "data": {
                    "trace_id": trace_id,
                    "limit": limit,
                    "total_spans": len(spans),
                    "spans": [s.to_dict() for s in spans],
                },
            },
            indent=2,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Trace query error: {exc}"}, indent=2)


def handle_queue_enqueue(args: dict[str, Any]) -> str:
    """Tool handler for mekong_queue_enqueue."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or _clean_str(args.get("task_name"))
    if not name:
        return json.dumps({"ok": False, "error": "Missing required argument: name"}, indent=2)

    priority = _clean_str(args.get("priority")) or "normal"
    payload = args.get("payload")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {"raw": payload}
    elif not isinstance(payload, dict):
        payload = {}

    max_retries = int(args.get("max_retries", 3))
    delay_sec = float(args.get("delay_sec", 0.0))

    try:
        from src.core.task_queue import get_task_queue

        tq = get_task_queue()
        task = tq.enqueue(
            name=name,
            payload=payload,
            priority=priority,
            max_retries=max_retries,
            delay_sec=delay_sec,
        )
        return json.dumps({"ok": True, "data": task.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Queue enqueue error: {exc}"}, indent=2)


def handle_queue_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_queue_status."""
    try:
        from src.core.task_queue import get_task_queue

        tq = get_task_queue()
        status = tq.get_status()
        return json.dumps({"ok": True, "data": status}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Queue status error: {exc}"}, indent=2)


def handle_queue_dlq_action(args: dict[str, Any]) -> str:
    """Tool handler for mekong_queue_dlq_action."""
    if not isinstance(args, dict):
        args = {}
    action = (_clean_str(args.get("action")) or "list").lower()
    task_id = _clean_str(args.get("task_id"))

    try:
        from src.core.task_queue import get_task_queue

        tq = get_task_queue()
        if action == "clear":
            cleared = tq.clear_dlq()
            return json.dumps({"ok": True, "data": {"action": "clear", "cleared_tasks": cleared}}, indent=2)
        elif action in ("retry_all", "retry-all"):
            retried = tq.retry_all_dlq()
            return json.dumps({"ok": True, "data": {"action": "retry_all", "retried_tasks": retried}}, indent=2)
        elif action == "retry":
            if not task_id:
                return json.dumps({"ok": False, "error": "Missing required argument: task_id"}, indent=2)
            ok = tq.retry_dlq_task(task_id)
            return json.dumps({"ok": ok, "data": {"action": "retry", "task_id": task_id}}, indent=2)
        else:
            limit = int(args.get("limit", 50))
            tasks = tq.get_dlq_tasks(limit=limit)
            return json.dumps(
                {
                    "ok": True,
                    "data": {
                        "action": "list",
                        "total_dlq": len(tasks),
                        "tasks": [t.to_dict() for t in tasks],
                    },
                },
                indent=2,
            )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Queue DLQ action error: {exc}"}, indent=2)


def handle_pipeline_run(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pipeline_run."""
    if not isinstance(args, dict):
        args = {}
    goal = _clean_str(args.get("goal"))
    if not goal:
        return json.dumps({"ok": False, "error": "Missing required argument: goal"}, indent=2)

    stages_arg = args.get("stages")
    if isinstance(stages_arg, str):
        stages = [s.strip() for s in stages_arg.split(",") if s.strip()]
    elif isinstance(stages_arg, list):
        stages = [str(s).strip() for s in stages_arg if str(s).strip()]
    else:
        stages = ["file-picker", "editor", "reviewer"]

    try:
        from src.core.pipeline_manager import get_pipeline_manager

        pm = get_pipeline_manager()
        res = pm.run_multi_agent_pipeline(goal=goal, stages=stages)
        aggregated = pm.aggregate_results(res.pipeline_id)
        aggregated["goal"] = goal
        return json.dumps({"ok": res.status.value == "completed", "data": aggregated}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pipeline run error: {exc}"}, indent=2)


def handle_pipeline_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pipeline_status."""
    if not isinstance(args, dict):
        args = {}
    pipeline_id = _clean_str(args.get("pipeline_id"))

    try:
        from src.core.pipeline_manager import get_pipeline_manager

        pm = get_pipeline_manager()
        if pipeline_id:
            res = pm.get_pipeline(pipeline_id)
            if res is None:
                return json.dumps({"ok": False, "error": f"Pipeline not found: {pipeline_id}"}, indent=2)
            aggregated = pm.aggregate_results(pipeline_id)
            return json.dumps({"ok": True, "data": aggregated}, indent=2)
        else:
            all_pipelines = pm.list_pipelines()
            return json.dumps(
                {
                    "ok": True,
                    "data": {
                        "total_pipelines": len(all_pipelines),
                        "pipelines": [pm.aggregate_results(p.pipeline_id) for p in all_pipelines],
                    },
                },
                indent=2,
            )
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pipeline status error: {exc}"}, indent=2)


def handle_worktree_create(args: dict[str, Any]) -> str:
    """Tool handler for mekong_worktree_create."""
    if not isinstance(args, dict):
        args = {}
    feature = _clean_str(args.get("feature"))
    if not feature:
        return json.dumps({"ok": False, "error": "Missing required argument: feature"}, indent=2)
    prefix = _clean_str(args.get("prefix")) or None
    base_branch = _clean_str(args.get("base_branch") or args.get("base")) or None
    no_prefix = bool(args.get("no_prefix", False))
    root = _clean_str(args.get("root") or args.get("worktree_root")) or None
    dry_run = bool(args.get("dry_run", False))

    try:
        from src.core.worktree_manager import get_worktree_manager

        wm = get_worktree_manager()
        rec = wm.create_worktree(
            feature=feature,
            prefix=prefix,
            base_branch=base_branch,
            no_prefix=no_prefix,
            worktree_root=root,
            dry_run=dry_run,
        )
        return json.dumps({"ok": True, "dry_run": dry_run, "worktree": rec.to_dict()}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Worktree create error: {exc}"}, indent=2)


def handle_worktree_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_worktree_list."""
    try:
        from src.core.worktree_manager import get_worktree_manager

        wm = get_worktree_manager()
        recs = wm.list_worktrees()
        return json.dumps({"ok": True, "worktrees": [r.to_dict() for r in recs], "count": len(recs)}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Worktree list error: {exc}"}, indent=2)


def handle_worktree_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_worktree_status."""
    if not isinstance(args, dict):
        args = {}
    target = _clean_str(args.get("path_or_branch") or args.get("target")) or None
    try:
        from src.core.worktree_manager import get_worktree_manager

        wm = get_worktree_manager()
        stat = wm.status(path_or_branch=target)
        return json.dumps(stat, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Worktree status error: {exc}"}, indent=2)


def handle_worktree_remove(args: dict[str, Any]) -> str:
    """Tool handler for mekong_worktree_remove."""
    if not isinstance(args, dict):
        args = {}
    target = _clean_str(args.get("path_or_name") or args.get("target") or args.get("path"))
    if not target:
        return json.dumps({"ok": False, "error": "Missing required argument: path_or_name"}, indent=2)
    force = bool(args.get("force", False))
    try:
        from src.core.worktree_manager import get_worktree_manager

        wm = get_worktree_manager()
        success = wm.remove_worktree(path_or_name=target, force=force)
        return json.dumps({"ok": success, "target": target, "removed": True}, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Worktree remove error: {exc}"}, indent=2)


def handle_ship_preflight(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ship_preflight."""
    try:
        from src.core.shipping_engine import get_shipping_engine

        engine = get_shipping_engine()
        res = engine.preflight_check()
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Ship preflight error: {exc}"}, indent=2)


def handle_ship_run(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ship_run."""
    if not isinstance(args, dict):
        args = {}
    message = _clean_str(args.get("message")) or None
    run_lint = bool(args.get("run_lint", True)) if "run_lint" in args else not bool(args.get("skip_lint", False))
    run_tests = bool(args.get("run_tests", True)) if "run_tests" in args else not bool(args.get("skip_tests", False))
    push = bool(args.get("push", True)) if "push" in args else not bool(args.get("skip_push", False))
    dry_run = bool(args.get("dry_run", False))

    try:
        from src.core.shipping_engine import get_shipping_engine

        engine = get_shipping_engine()
        report = engine.ship(
            message=message,
            run_lint=run_lint,
            run_tests=run_tests,
            push=push,
            dry_run=dry_run,
        )
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Ship run error: {exc}"}, indent=2)


def handle_daily_report(args: dict[str, Any]) -> str:
    """Tool handler for mekong_daily_report."""
    if not isinstance(args, dict):
        args = {}
    since = _clean_str(args.get("since")) or "24 hours ago"
    include_todos = bool(args.get("include_todos", True))
    try:
        from src.core.daily_briefing import get_daily_briefing_engine

        engine = get_daily_briefing_engine()
        report = engine.generate_report(since=since, include_debt=include_todos)
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Daily report error: {exc}"}, indent=2)


def handle_daily_focus(args: dict[str, Any]) -> str:
    """Tool handler for mekong_daily_focus."""
    try:
        from src.core.daily_briefing import get_daily_briefing_engine

        engine = get_daily_briefing_engine()
        report = engine.generate_report(since="24 hours ago", include_debt=True)
        return json.dumps({
            "ok": True,
            "date": report.date,
            "focus_priorities": report.focus_priorities,
        }, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Daily focus error: {exc}"}, indent=2)


def handle_quick_start_plan(args: dict[str, Any]) -> str:
    """Tool handler for mekong_quick_start_plan."""
    if not isinstance(args, dict):
        args = {}
    project_name = _clean_str(args.get("project_name")) or "mekong-app"
    project_type = _clean_str(args.get("project_type")) or "agent"
    try:
        from src.core.quick_start_engine import get_quick_start_engine

        engine = get_quick_start_engine()
        report = engine.kickoff(
            project_name=project_name,
            project_type=project_type,
            dry_run=True,
            init_git=False,
        )
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Quick start plan error: {exc}"}, indent=2)


def handle_quick_start_create(args: dict[str, Any]) -> str:
    """Tool handler for mekong_quick_start_create."""
    if not isinstance(args, dict):
        args = {}
    project_name = _clean_str(args.get("project_name")) or "mekong-app"
    project_type = _clean_str(args.get("project_type")) or "agent"
    target_dir = _clean_str(args.get("target_dir"))
    dry_run = bool(args.get("dry_run", False))
    init_git = bool(args.get("init_git", True))
    try:
        from src.core.quick_start_engine import get_quick_start_engine

        engine = get_quick_start_engine()
        report = engine.kickoff(
            project_name=project_name,
            project_type=project_type,
            target_dir=target_dir if target_dir else None,
            dry_run=dry_run,
            init_git=init_git,
        )
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Quick start create error: {exc}"}, indent=2)


def handle_cto_scorecard(args: dict[str, Any]) -> str:
    """Tool handler for mekong_cto_scorecard."""
    try:
        from src.core.cto_engine import get_cto_engine

        engine = get_cto_engine()
        sc = engine.compute_scorecard()
        return json.dumps(sc.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"CTO scorecard error: {exc}"}, indent=2)


def handle_cto_review(args: dict[str, Any]) -> str:
    """Tool handler for mekong_cto_review."""
    if not isinstance(args, dict):
        args = {}
    target_path = _clean_str(args.get("target_path"))
    try:
        from src.core.cto_engine import get_cto_engine

        engine = get_cto_engine()
        report = engine.run_code_review(target_path=target_path if target_path else None)
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"CTO review error: {exc}"}, indent=2)


def handle_cto_architect(args: dict[str, Any]) -> str:
    """Tool handler for mekong_cto_architect."""
    if not isinstance(args, dict):
        args = {}
    title = _clean_str(args.get("title")) or "Architecture Decision"
    context = _clean_str(args.get("context")) or ""
    decision = _clean_str(args.get("decision")) or ""
    try:
        from src.core.cto_engine import get_cto_engine

        engine = get_cto_engine()
        adr = engine.generate_adr(title=title, context=context, decision=decision, export=False)
        return json.dumps(adr.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"CTO architect error: {exc}"}, indent=2)


def handle_sales_pipeline(args: dict[str, Any]) -> str:
    """Tool handler for mekong_sales_pipeline."""
    if not isinstance(args, dict):
        args = {}
    stage = _clean_str(args.get("stage")) or ""
    try:
        from src.core.sales_engine import get_sales_engine

        engine = get_sales_engine()
        metrics = engine.get_pipeline_metrics()
        return json.dumps(metrics.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Sales pipeline error: {exc}"}, indent=2)


def handle_sales_deal_add(args: dict[str, Any]) -> str:
    """Tool handler for mekong_sales_deal_add."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or "New Opportunity"
    company = _clean_str(args.get("company")) or "Prospective Account"
    value = float(args.get("value", 10000.0))
    stage = _clean_str(args.get("stage")) or "lead"
    email = _clean_str(args.get("email")) or ""
    try:
        from src.core.sales_engine import get_sales_engine

        engine = get_sales_engine()
        deal = engine.add_deal(name=name, company=company, value=value, stage=stage, contact_email=email)
        return json.dumps(deal.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Sales deal add error: {exc}"}, indent=2)


def handle_sales_outreach(args: dict[str, Any]) -> str:
    """Tool handler for mekong_sales_outreach."""
    if not isinstance(args, dict):
        args = {}
    company = _clean_str(args.get("company")) or "Acme Corp"
    persona = _clean_str(args.get("persona")) or "CTO"
    channel = _clean_str(args.get("channel")) or "email"
    try:
        from src.core.sales_engine import get_sales_engine

        engine = get_sales_engine()
        template = engine.generate_outreach(company=company, persona=persona, channel=channel)
        return json.dumps(template.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Sales outreach error: {exc}"}, indent=2)


def handle_marketing_metrics(args: dict[str, Any]) -> str:
    """Tool handler for mekong_marketing_metrics."""
    try:
        from src.core.marketing_engine import get_marketing_engine

        engine = get_marketing_engine()
        metrics = engine.get_marketing_metrics()
        return json.dumps(metrics.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Marketing metrics error: {exc}"}, indent=2)


def handle_marketing_campaign_create(args: dict[str, Any]) -> str:
    """Tool handler for mekong_marketing_campaign_create."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or "New Campaign"
    channel = _clean_str(args.get("channel")) or "social"
    budget = float(args.get("budget", 1000.0))
    audience = _clean_str(args.get("target_audience")) or "Tech Founders & Engineers"
    try:
        from src.core.marketing_engine import get_marketing_engine

        engine = get_marketing_engine()
        camp = engine.create_campaign(name=name, channel=channel, budget=budget, target_audience=audience)
        return json.dumps(camp.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Marketing campaign create error: {exc}"}, indent=2)


def handle_marketing_content_generate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_marketing_content_generate."""
    if not isinstance(args, dict):
        args = {}
    topic = _clean_str(args.get("topic")) or "Autonomous Agent Harnesses"
    channel = _clean_str(args.get("channel")) or "social"
    content_type = _clean_str(args.get("content_type")) or "post"
    try:
        from src.core.marketing_engine import get_marketing_engine

        engine = get_marketing_engine()
        item = engine.generate_content(topic=topic, channel=channel, content_type=content_type)
        return json.dumps(item.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Marketing content generate error: {exc}"}, indent=2)


def handle_dev_audit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_dev_audit."""
    if not isinstance(args, dict):
        args = {}
    path = _clean_str(args.get("path")) or ""
    try:
        from src.core.dev_engine import get_dev_engine

        engine = get_dev_engine()
        report = engine.audit_codebase(target_path=path if path else None)
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Dev audit error: {exc}"}, indent=2)


def handle_dev_scaffold(args: dict[str, Any]) -> str:
    """Tool handler for mekong_dev_scaffold."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or "sample_service"
    module_type = _clean_str(args.get("module_type")) or "service"
    dry_run = bool(args.get("dry_run", True))
    try:
        from src.core.dev_engine import get_dev_engine

        engine = get_dev_engine()
        res = engine.scaffold_module(name=name, module_type=module_type, dry_run=dry_run)
        return json.dumps(res.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Dev scaffold error: {exc}"}, indent=2)


def handle_dev_review(args: dict[str, Any]) -> str:
    """Tool handler for mekong_dev_review."""
    try:
        from src.core.dev_engine import get_dev_engine

        engine = get_dev_engine()
        report = engine.review_diff()
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Dev review error: {exc}"}, indent=2)


def handle_ops_health_sweep(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ops_health_sweep."""
    if not isinstance(args, dict):
        args = {}
    save_report = bool(args.get("save_report", False))
    try:
        from src.core.ops_engine import get_ops_engine

        engine = get_ops_engine()
        report = engine.health_sweep(save_report=save_report)
        return json.dumps(report.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Ops health sweep error: {exc}"}, indent=2)


def handle_ops_incident_create(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ops_incident_create."""
    if not isinstance(args, dict):
        args = {}
    title = _clean_str(args.get("title")) or "System degradation"
    severity = _clean_str(args.get("severity")) or "SEV3"
    service = _clean_str(args.get("service")) or "core"
    summary = _clean_str(args.get("summary")) or ""
    try:
        from src.core.ops_engine import get_ops_engine

        engine = get_ops_engine()
        rec = engine.create_incident(title=title, severity=severity, service=service, summary=summary)
        return json.dumps(rec.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Ops incident create error: {exc}"}, indent=2)


def handle_ops_incident_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ops_incident_list."""
    if not isinstance(args, dict):
        args = {}
    status = _clean_str(args.get("status")) or "ALL"
    try:
        from src.core.ops_engine import get_ops_engine

        engine = get_ops_engine()
        incidents = engine.list_incidents(status=status)
        return json.dumps([i.to_dict() for i in incidents], indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Ops incident list error: {exc}"}, indent=2)


def handle_support_onboard_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_support_onboard_status."""
    try:
        from src.core.support_engine import get_support_engine

        engine = get_support_engine()
        status = engine.get_onboarding_status()
        return json.dumps(status.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Support onboard status error: {exc}"}, indent=2)


def handle_support_feedback_submit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_support_feedback_submit."""
    if not isinstance(args, dict):
        args = {}
    nps_score = args.get("nps_score")
    if nps_score is not None:
        try:
            nps_score = int(nps_score)
        except (ValueError, TypeError):
            nps_score = None
    feedback_text = _clean_str(args.get("feedback_text")) or ""
    category = _clean_str(args.get("category")) or "general"
    try:
        from src.core.support_engine import get_support_engine

        engine = get_support_engine()
        rec = engine.submit_feedback(nps_score=nps_score, feedback_text=feedback_text, category=category)
        return json.dumps(rec.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Support feedback error: {exc}"}, indent=2)


def handle_support_triage(args: dict[str, Any]) -> str:
    """Tool handler for mekong_support_triage."""
    if not isinstance(args, dict):
        args = {}
    issue_text = _clean_str(args.get("issue_text")) or ""
    try:
        from src.core.support_engine import get_support_engine

        engine = get_support_engine()
        triage = engine.triage_issue(issue_description=issue_text)
        return json.dumps(triage.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Support triage error: {exc}"}, indent=2)


def handle_consulting_pricing(args: dict[str, Any]) -> str:
    """Tool handler for mekong_consulting_pricing."""
    if not isinstance(args, dict):
        args = {}
    currency = _clean_str(args.get("currency")) or "USD"
    try:
        from src.core.consulting_engine import get_consulting_engine

        engine = get_consulting_engine()
        packages = engine.get_service_catalog(currency=currency)
        return json.dumps([p.to_dict() for p in packages], indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Consulting pricing error: {exc}"}, indent=2)


def handle_consulting_proposal(args: dict[str, Any]) -> str:
    """Tool handler for mekong_consulting_proposal."""
    if not isinstance(args, dict):
        args = {}
    prospect = _clean_str(args.get("prospect_name")) or "Prospective Client"
    service_tier = _clean_str(args.get("service_tier")) or "custom_agent"
    requirements = _clean_str(args.get("requirements")) or ""
    try:
        from src.core.consulting_engine import get_consulting_engine

        engine = get_consulting_engine()
        prop = engine.generate_proposal(prospect_name=prospect, service_tier=service_tier, requirements=requirements)
        return json.dumps(prop.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Consulting proposal error: {exc}"}, indent=2)


def handle_consulting_outreach(args: dict[str, Any]) -> str:
    """Tool handler for mekong_consulting_outreach."""
    if not isinstance(args, dict):
        args = {}
    prospect = _clean_str(args.get("prospect_name")) or "Acme Corp"
    service_tier = _clean_str(args.get("service_tier")) or "custom_agent"
    role = _clean_str(args.get("role")) or "CTO"
    try:
        from src.core.consulting_engine import get_consulting_engine

        engine = get_consulting_engine()
        out = engine.generate_outreach(prospect_name=prospect, service_tier=service_tier, role=role)
        return json.dumps(out.to_dict(), indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Consulting outreach error: {exc}"}, indent=2)


def handle_revenue_metrics(args: dict[str, Any]) -> str:
    """Tool handler for mekong_revenue_metrics."""
    if not isinstance(args, dict):
        args = {}
    period = _clean_str(args.get("period")) or "month"
    try:
        from src.core.revenue_engine import get_revenue_engine

        engine = get_revenue_engine()
        metrics = engine.get_metrics(period=period)
        return json.dumps(metrics, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Revenue metrics error: {exc}"}, indent=2)


def handle_revenue_record(args: dict[str, Any]) -> str:
    """Tool handler for mekong_revenue_record."""
    if not isinstance(args, dict):
        args = {}
    customer_id = _clean_str(args.get("customer_id")) or "cust_default"
    amount = float(args.get("amount") or 0.0)
    customer_name = _clean_str(args.get("customer_name")) or ""
    currency = _clean_str(args.get("currency")) or "USD"
    tier = _clean_str(args.get("tier")) or "starter"
    txn_type = _clean_str(args.get("txn_type")) or "subscription"
    gateway = _clean_str(args.get("gateway")) or "stripe"
    status = _clean_str(args.get("status")) or "succeeded"
    notes = _clean_str(args.get("notes")) or ""
    try:
        from src.core.revenue_engine import get_revenue_engine

        engine = get_revenue_engine()
        res = engine.record_transaction(
            customer_id=customer_id,
            amount=amount,
            customer_name=customer_name,
            currency=currency,
            tier=tier,
            type=txn_type,
            gateway=gateway,
            status=status,
            notes=notes,
        )
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Revenue record error: {exc}"}, indent=2)


def handle_revenue_forecast(args: dict[str, Any]) -> str:
    """Tool handler for mekong_revenue_forecast."""
    if not isinstance(args, dict):
        args = {}
    months = int(args.get("months") or 6)
    scenario = _clean_str(args.get("scenario")) or "base"
    try:
        from src.core.revenue_engine import get_revenue_engine

        engine = get_revenue_engine()
        fc = engine.forecast_revenue(months=months, scenario=scenario)
        return json.dumps(fc, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Revenue forecast error: {exc}"}, indent=2)


def handle_content_generate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_content_generate."""
    if not isinstance(args, dict):
        args = {}
    pillar = _clean_str(args.get("pillar")) or "ai-agents"
    format_type = _clean_str(args.get("format_type")) or "blog"
    topic = _clean_str(args.get("topic")) or ""
    channel = _clean_str(args.get("channel")) or ""
    try:
        from src.core.content_engine import get_content_engine

        engine = get_content_engine()
        item = engine.generate_content(
            pillar=pillar,
            format_type=format_type,
            topic=topic,
            channel=channel,
        )
        return json.dumps(item, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Content generate error: {exc}"}, indent=2)


def handle_content_calendar(args: dict[str, Any]) -> str:
    """Tool handler for mekong_content_calendar."""
    try:
        from src.core.content_engine import get_content_engine

        engine = get_content_engine()
        cal = engine.get_calendar()
        return json.dumps(cal, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Content calendar error: {exc}"}, indent=2)


def handle_content_channels(args: dict[str, Any]) -> str:
    """Tool handler for mekong_content_channels."""
    try:
        from src.core.content_engine import get_content_engine

        engine = get_content_engine()
        channels = engine.get_channel_stats()
        return json.dumps(channels, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Content channels error: {exc}"}, indent=2)


def handle_copywriting_generate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_copywriting_generate."""
    if not isinstance(args, dict):
        args = {}
    prod = _clean_str(args.get("product_name")) or "Mekong CLI"
    aud = _clean_str(args.get("target_audience")) or "Founders & Engineers"
    formula = _clean_str(args.get("formula")) or "pas"
    copy_type = _clean_str(args.get("copy_type")) or "landing_page"
    benefit = _clean_str(args.get("key_benefit")) or ""
    style = _clean_str(args.get("style")) or "direct_response"
    try:
        from src.core.copywriting_engine import get_copywriting_engine

        engine = get_copywriting_engine()
        res = engine.generate_copy(
            product_name=prod,
            target_audience=aud,
            formula=formula,
            copy_type=copy_type,
            key_benefit=benefit,
            style=style,
        )
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Copywriting generate error: {exc}"}, indent=2)


def handle_copywriting_headline(args: dict[str, Any]) -> str:
    """Tool handler for mekong_copywriting_headline."""
    if not isinstance(args, dict):
        args = {}
    prod = _clean_str(args.get("product_name")) or "Mekong CLI"
    vp = _clean_str(args.get("value_prop")) or "automate engineering workflows"
    count = int(args.get("count") or 5)
    try:
        from src.core.copywriting_engine import get_copywriting_engine

        engine = get_copywriting_engine()
        headlines = engine.generate_headlines(
            product_name=prod,
            value_prop=vp,
            count=count,
        )
        return json.dumps(headlines, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Copywriting headline error: {exc}"}, indent=2)


def handle_copywriting_cta(args: dict[str, Any]) -> str:
    """Tool handler for mekong_copywriting_cta."""
    if not isinstance(args, dict):
        args = {}
    goal = _clean_str(args.get("action_goal")) or "start free trial"
    reversal = _clean_str(args.get("risk_reversal")) or ""
    try:
        from src.core.copywriting_engine import get_copywriting_engine

        engine = get_copywriting_engine()
        ctas = engine.generate_cta(action_goal=goal, risk_reversal=reversal)
        return json.dumps(ctas, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Copywriting CTA error: {exc}"}, indent=2)


def handle_billing_simulate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_billing_simulate."""
    if not isinstance(args, dict):
        args = {}
    lic = _clean_str(args.get("license_key")) or "mekong_lic_default"
    tier = _clean_str(args.get("tier")) or "pro"
    days = int(args.get("period_days") or 30)
    try:
        from src.core.billing_engine import get_billing_engine

        engine = get_billing_engine()
        invoice = engine.simulate_billing(license_key=lic, tier=tier, period_days=days)
        return json.dumps(invoice, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Billing simulate error: {exc}"}, indent=2)


def handle_billing_record_usage(args: dict[str, Any]) -> str:
    """Tool handler for mekong_billing_record_usage."""
    if not isinstance(args, dict):
        args = {}
    lic = _clean_str(args.get("license_key")) or "mekong_lic_default"
    etype = _clean_str(args.get("event_type")) or "llm_tokens"
    qty = float(args.get("quantity") or 1.0)
    key = _clean_str(args.get("idempotency_key")) or ""
    tier = _clean_str(args.get("tier")) or "pro"
    try:
        from src.core.billing_engine import get_billing_engine

        engine = get_billing_engine()
        res = engine.record_usage(
            license_key=lic,
            event_type=etype,
            quantity=qty,
            idempotency_key=key,
            tier=tier,
        )
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Billing record usage error: {exc}"}, indent=2)


def handle_billing_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_billing_status."""
    if not isinstance(args, dict):
        args = {}
    lic = _clean_str(args.get("license_key")) or "mekong_lic_default"
    try:
        from src.core.billing_engine import get_billing_engine

        engine = get_billing_engine()
        st = engine.get_billing_status(license_key=lic)
        return json.dumps(st, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Billing status error: {exc}"}, indent=2)


def handle_vendor_onboard(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vendor_onboard."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or ""
    vtype = _clean_str(args.get("vendor_type")) or "agent"
    desc = _clean_str(args.get("description")) or ""
    author = _clean_str(args.get("author")) or "Community Builder"
    ver = _clean_str(args.get("version")) or "1.0.0"
    trust = float(args.get("trust_score") or 85.0)
    try:
        from src.core.vendor_engine import get_vendor_engine

        engine = get_vendor_engine()
        vendor = engine.onboard_vendor(
            name=name,
            vendor_type=vtype,
            version=ver,
            description=desc,
            author=author,
            trust_score=trust,
        )
        return json.dumps(vendor, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Vendor onboard error: {exc}"}, indent=2)


def handle_vendor_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vendor_list."""
    if not isinstance(args, dict):
        args = {}
    vtype = _clean_str(args.get("vendor_type")) or "all"
    status = _clean_str(args.get("status")) or "all"
    limit = int(args.get("limit") or 50)
    try:
        from src.core.vendor_engine import get_vendor_engine

        engine = get_vendor_engine()
        vendors = engine.list_vendors(vendor_type=vtype, status=status, limit=limit)
        return json.dumps(vendors, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Vendor list error: {exc}"}, indent=2)


def handle_vendor_assess(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vendor_assess."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or ""
    atype = _clean_str(args.get("audit_type")) or "security"
    try:
        from src.core.vendor_engine import get_vendor_engine

        engine = get_vendor_engine()
        res = engine.audit_vendor(name_or_id=name, audit_type=atype)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Vendor assess error: {exc}"}, indent=2)


def handle_founder_assess(args: dict[str, Any]) -> str:
    """Tool handler for mekong_founder_assess."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name")) or ""
    mission = _clean_str(args.get("mission")) or ""
    tipi = args.get("tipi_responses")
    if not isinstance(tipi, dict):
        tipi = {}
    values = args.get("values")
    if not isinstance(values, list):
        values = []
    fears = args.get("fears")
    if not isinstance(fears, list):
        fears = []
    risk = args.get("risk_ratings")
    if not isinstance(risk, dict):
        risk = {}
    biases = args.get("bias_responses")
    if not isinstance(biases, dict):
        biases = {}
    particle_id = _clean_str(args.get("particle_id")) or None

    try:
        from src.core.founder_engine import get_founder_engine

        engine = get_founder_engine()
        genome = engine.assess_founder(
            name=name or (f"founder-{mission[:16].replace(' ', '-').lower()}" if mission else "founder-anonymous"),
            mission=mission,
            tipi_responses=tipi,
            values=values,
            fears=fears,
            risk_ratings=risk,
            bias_responses=biases,
            particle_id=particle_id,
        )
        return json.dumps(genome, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Founder assess error: {exc}"}, indent=2)


def handle_founder_review(args: dict[str, Any]) -> str:
    """Tool handler for mekong_founder_review."""
    if not isinstance(args, dict):
        args = {}
    fid = _clean_str(args.get("founder_id")) or ""
    try:
        from src.core.founder_engine import get_founder_engine

        engine = get_founder_engine()
        res = engine.get_founder(fid)
        if res is None:
            return json.dumps({"ok": False, "error": f"Founder '{fid}' not found"}, indent=2)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Founder review error: {exc}"}, indent=2)


def handle_founder_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_founder_list."""
    if not isinstance(args, dict):
        args = {}
    risk = _clean_str(args.get("risk_level")) or "all"
    limit = int(args.get("limit") or 50)
    try:
        from src.core.founder_engine import get_founder_engine

        engine = get_founder_engine()
        res = engine.list_founders(risk_level=risk, limit=limit)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Founder list error: {exc}"}, indent=2)


def handle_governance_propose(args: dict[str, Any]) -> str:
    """Tool handler for mekong_governance_propose."""
    if not isinstance(args, dict):
        args = {}
    title = _clean_str(args.get("title")) or ""
    desc = _clean_str(args.get("description")) or ""
    text = _clean_str(args.get("text")) or ""
    proposer = _clean_str(args.get("proposer")) or "founder"
    tier = _clean_str(args.get("tier")) or "soft"
    co_sponsors = args.get("co_sponsors")
    if not isinstance(co_sponsors, list):
        co_sponsors = []

    try:
        from src.core.governance_engine import get_governance_engine

        engine = get_governance_engine()
        res = engine.create_proposal(
            title=title,
            description=desc,
            text=text,
            proposer=proposer,
            tier=tier,
            co_sponsors=co_sponsors,
        )
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Governance propose error: {exc}"}, indent=2)


def handle_governance_vote(args: dict[str, Any]) -> str:
    """Tool handler for mekong_governance_vote."""
    if not isinstance(args, dict):
        args = {}
    pid = _clean_str(args.get("proposal_id")) or ""
    voter = _clean_str(args.get("voter")) or "founder"
    choice = _clean_str(args.get("choice")) or "yes"
    weight = float(args.get("weight") or 1.0)

    try:
        from src.core.governance_engine import get_governance_engine

        engine = get_governance_engine()
        res = engine.cast_vote(
            proposal_id=pid,
            voter=voter,
            choice=choice,
            weight=weight,
        )
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Governance vote error: {exc}"}, indent=2)


def handle_governance_tally(args: dict[str, Any]) -> str:
    """Tool handler for mekong_governance_tally."""
    if not isinstance(args, dict):
        args = {}
    pid = _clean_str(args.get("proposal_id")) or ""

    try:
        from src.core.governance_engine import get_governance_engine

        engine = get_governance_engine()
        res = engine.tally_votes(proposal_id=pid)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Governance tally error: {exc}"}, indent=2)


def handle_governance_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_governance_list."""
    if not isinstance(args, dict):
        args = {}
    status = _clean_str(args.get("status")) or "all"
    tier = _clean_str(args.get("tier")) or "all"
    limit = int(args.get("limit") or 50)

    try:
        from src.core.governance_engine import get_governance_engine

        engine = get_governance_engine()
        res = engine.list_proposals(status=status, tier=tier, limit=limit)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Governance list error: {exc}"}, indent=2)


def handle_particle_init(args: dict[str, Any]) -> str:
    """Tool handler for mekong_particle_init."""
    if not isinstance(args, dict):
        args = {}
    name = _clean_str(args.get("name"))
    if not name:
        return json.dumps({"ok": False, "error": "Missing required argument 'name'"}, indent=2)
    mission = _clean_str(args.get("mission"))
    template = _clean_str(args.get("template")) or "skel"

    try:
        from src.core.particle_engine import ParticleEngine

        engine = ParticleEngine()
        res = engine.init_particle(name=name, mission=mission, template=template)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Particle init error: {exc}"}, indent=2)


def handle_particle_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_particle_status."""
    if not isinstance(args, dict):
        args = {}
    particle_id = _clean_str(args.get("particle_id")) or "default"

    try:
        from src.core.particle_engine import ParticleEngine

        engine = ParticleEngine()
        if particle_id in ("default", ""):
            res = engine.get_status()
        else:
            res = engine.get_particle_status(particle_id)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Particle status error: {exc}"}, indent=2)


def handle_particle_connect(args: dict[str, Any]) -> str:
    """Tool handler for mekong_particle_connect."""
    if not isinstance(args, dict):
        args = {}
    particle_a = _clean_str(args.get("particle_a"))
    particle_b = _clean_str(args.get("particle_b"))
    if not particle_a or not particle_b:
        return json.dumps({"ok": False, "error": "Both 'particle_a' and 'particle_b' are required."}, indent=2)
    trust_score = float(args.get("trust_score") or 50.0)

    try:
        from src.core.particle_engine import ParticleEngine

        engine = ParticleEngine()
        res = engine.connect_particles(particle_a=particle_a, particle_b=particle_b, trust_score=trust_score)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Particle connect error: {exc}"}, indent=2)


def handle_particle_cell_run(args: dict[str, Any]) -> str:
    """Tool handler for mekong_particle_cell_run."""
    if not isinstance(args, dict):
        args = {}
    role = _clean_str(args.get("role"))
    prompt = _clean_str(args.get("prompt"))
    if not role or not prompt:
        return json.dumps({"ok": False, "error": "Both 'role' and 'prompt' are required."}, indent=2)
    particle_id = _clean_str(args.get("particle_id")) or "default"
    auto_compliance = bool(args.get("auto_compliance", False))

    try:
        from src.core.particle_engine import ParticleEngine

        engine = ParticleEngine()
        res = engine.run_cell(role=role, prompt=prompt, particle_id=particle_id, auto_compliance=auto_compliance)
        return json.dumps(res, indent=2)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Particle cell run error: {exc}"}, indent=2)


def handle_thue_tncn(args: dict[str, Any]) -> str:
    """Tool handler for mekong_thue_tncn."""
    if not isinstance(args, dict):
        args = {}
    income = float(args.get("monthly_income") or 0)
    dependents = int(args.get("dependents") or 0)

    try:
        from src.core.thue_engine import ThueEngine

        engine = ThueEngine()
        res = engine.calculate_tncn(monthly_income=income, dependents=dependents)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tax TNCN error: {exc}"}, indent=2)


def handle_thue_tndn(args: dict[str, Any]) -> str:
    """Tool handler for mekong_thue_tndn."""
    if not isinstance(args, dict):
        args = {}
    revenue = float(args.get("annual_revenue") or 0)
    profit = float(args.get("profit")) if args.get("profit") is not None else None
    is_sme = bool(args.get("is_sme", True))

    try:
        from src.core.thue_engine import ThueEngine

        engine = ThueEngine()
        res = engine.calculate_tndn(annual_revenue=revenue, profit=profit, is_sme=is_sme)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tax TNDN error: {exc}"}, indent=2)


def handle_thue_gtgt(args: dict[str, Any]) -> str:
    """Tool handler for mekong_thue_gtgt."""
    if not isinstance(args, dict):
        args = {}
    amount = float(args.get("amount") or 0)
    rate = int(args.get("rate") or 10)

    try:
        from src.core.thue_engine import ThueEngine

        engine = ThueEngine()
        res = engine.calculate_gtgt(amount=amount, rate=rate)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tax GTGT error: {exc}"}, indent=2)


def handle_thue_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_thue_status."""
    try:
        from src.core.thue_engine import ThueEngine

        engine = ThueEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tax status error: {exc}"}, indent=2)


def handle_ke_toan_create(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ke_toan_create."""
    if not isinstance(args, dict):
        args = {}
    amount = float(args.get("amount") or 0)
    vat_rate = int(args.get("vat_rate") or 10)
    buyer = str(args.get("buyer") or "Khách Hàng")
    seller = str(args.get("seller") or "Doanh Nghiệp")
    seller_tax_code = str(args.get("seller_tax_code") or "0000000000")
    buyer_tax_code = str(args.get("buyer_tax_code") or "")
    description = str(args.get("description") or "Hàng hóa/Dịch vụ")

    try:
        from src.core.ke_toan_engine import KeToanEngine

        engine = KeToanEngine()
        res = engine.create_invoice(
            amount=amount,
            buyer=buyer,
            vat_rate=vat_rate,
            seller=seller,
            seller_tax_code=seller_tax_code,
            buyer_tax_code=buyer_tax_code,
            description=description,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Accounting create error: {exc}"}, indent=2)


def handle_ke_toan_xml(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ke_toan_xml."""
    if not isinstance(args, dict):
        args = {}
    amount = float(args.get("amount") or 0)
    vat_rate = int(args.get("vat_rate") or 10)
    buyer = str(args.get("buyer") or "Khách Hàng")
    seller = str(args.get("seller") or "Doanh Nghiệp")
    seller_tax_code = str(args.get("seller_tax_code") or "0000000000")
    description = str(args.get("description") or "Hàng hóa/Dịch vụ")

    try:
        from src.core.ke_toan_engine import KeToanEngine

        engine = KeToanEngine()
        inv = engine.create_invoice(
            amount=amount,
            buyer=buyer,
            vat_rate=vat_rate,
            seller=seller,
            seller_tax_code=seller_tax_code,
            description=description,
            save=False,
        )
        return inv.get("xml_content", "")
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Accounting XML error: {exc}"}, indent=2)


def handle_ke_toan_journal(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ke_toan_journal."""
    if not isinstance(args, dict):
        args = {}
    amount = float(args.get("amount") or 0)
    vat_rate = int(args.get("vat_rate") or 10)
    buyer = str(args.get("buyer") or "Khách Hàng")
    seller = str(args.get("seller") or "Doanh Nghiệp")
    seller_tax_code = str(args.get("seller_tax_code") or "0000000000")
    description = str(args.get("description") or "Hàng hóa/Dịch vụ")

    try:
        from src.core.ke_toan_engine import KeToanEngine

        engine = KeToanEngine()
        inv = engine.create_invoice(
            amount=amount,
            buyer=buyer,
            vat_rate=vat_rate,
            seller=seller,
            seller_tax_code=seller_tax_code,
            description=description,
            save=False,
        )
        res = engine.create_vas_journal(inv, save=True)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Accounting journal error: {exc}"}, indent=2)


def handle_ke_toan_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ke_toan_status."""
    try:
        from src.core.ke_toan_engine import KeToanEngine

        engine = KeToanEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Accounting status error: {exc}"}, indent=2)


def handle_zalo_send(args: dict[str, Any]) -> str:
    """Tool handler for mekong_zalo_send."""
    if not isinstance(args, dict):
        args = {}
    user_id = str(args.get("user_id") or "")
    message = str(args.get("message") or "")
    template = str(args.get("template") or "")

    try:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        res = engine.send_message(user_id=user_id, text=message, template=template)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Zalo send error: {exc}"}, indent=2)


def handle_zalo_broadcast(args: dict[str, Any]) -> str:
    """Tool handler for mekong_zalo_broadcast."""
    if not isinstance(args, dict):
        args = {}
    message = str(args.get("message") or "")
    title = str(args.get("title") or "Thông báo Zalo OA")
    target_segment = str(args.get("target_segment") or "all")

    try:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        res = engine.broadcast_campaign(title=title, text=message, target_segment=target_segment)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Zalo broadcast error: {exc}"}, indent=2)


def handle_zalo_followers(args: dict[str, Any]) -> str:
    """Tool handler for mekong_zalo_followers."""
    if not isinstance(args, dict):
        args = {}
    segment = str(args.get("segment") or "all")
    limit = int(args.get("limit") or 50)

    try:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        followers = engine.list_followers(segment=segment, limit=limit)
        return json.dumps({"total": len(followers), "followers": followers}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Zalo followers error: {exc}"}, indent=2)


def handle_zalo_caption(args: dict[str, Any]) -> str:
    """Tool handler for mekong_zalo_caption."""
    if not isinstance(args, dict):
        args = {}
    topic = str(args.get("topic") or "Sản phẩm")
    tone = str(args.get("tone") or "vui_ve")

    try:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        res = engine.generate_caption(topic=topic, tone=tone)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Zalo caption error: {exc}"}, indent=2)


def handle_zalo_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_zalo_status."""
    try:
        from src.core.zalo_engine import ZaloEngine

        engine = ZaloEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Zalo status error: {exc}"}, indent=2)


def handle_bhxh_calc(args: dict[str, Any]) -> str:
    """Tool handler for mekong_bhxh_calc."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.bhxh_engine import BhxhEngine

        salary = float(args.get("salary") or 0.0)
        region = int(args.get("region") or 1)
        include_kpcd = bool(args.get("include_kpcd") or False)
        emp_id = str(args.get("employee_id") or "ADHOC")

        engine = BhxhEngine()
        res = engine.calculate_contribution(
            salary=salary,
            region=region,
            include_kpcd=include_kpcd,
            employee_id=emp_id,
            save=True,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"BHXH calculation error: {exc}"}, indent=2)


def handle_bhxh_employees(args: dict[str, Any]) -> str:
    """Tool handler for mekong_bhxh_employees."""
    if not isinstance(args, dict):
        args = {}
    status = str(args.get("status") or "all")
    try:
        from src.core.bhxh_engine import BhxhEngine

        engine = BhxhEngine()
        emps = engine.list_employees(status=status)
        return json.dumps({"total": len(emps), "employees": emps}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"BHXH employees error: {exc}"}, indent=2)


def handle_bhxh_declaration(args: dict[str, Any]) -> str:
    """Tool handler for mekong_bhxh_declaration."""
    if not isinstance(args, dict):
        args = {}
    change_type = str(args.get("change_type") or "dieu_chinh_luong")
    employee_id = str(args.get("employee_id") or "")
    effective_month = str(args.get("effective_month") or "")
    new_salary = float(args.get("new_salary") or 0.0)
    note = str(args.get("note") or "")

    try:
        from src.core.bhxh_engine import BhxhEngine

        engine = BhxhEngine()
        res = engine.create_declaration_d02lt(
            change_type=change_type,
            employee_id=employee_id,
            effective_month=effective_month,
            new_salary=new_salary,
            note=note,
            save=True,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"BHXH declaration error: {exc}"}, indent=2)


def handle_bhxh_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_bhxh_status."""
    try:
        from src.core.bhxh_engine import BhxhEngine

        engine = BhxhEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"BHXH status error: {exc}"}, indent=2)


def handle_ocop_eval(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ocop_eval."""
    try:
        from src.core.ocop_engine import OcopEngine

        engine = OcopEngine()
        product = str(args.get("product_name") or args.get("product") or "Sản Phẩm OCOP")
        part_a = float(args.get("part_a", 30.0))
        part_b = float(args.get("part_b", 22.0))
        part_c = float(args.get("part_c", 38.0))
        res = engine.evaluate_star_rating(
            product_name=product,
            part_a_community=part_a,
            part_b_marketing=part_b,
            part_c_quality=part_c,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"OCOP eval error: {exc}"}, indent=2)


def handle_ocop_products(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ocop_products."""
    try:
        from src.core.ocop_engine import OcopEngine

        engine = OcopEngine()
        min_stars = int(args.get("min_stars", 1))
        province = str(args.get("province", "all"))
        prods = engine.list_products(min_stars=min_stars, province=province)
        return json.dumps({"ok": True, "total": len(prods), "products": prods}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"OCOP products error: {exc}"}, indent=2)


def handle_ocop_listing(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ocop_listing."""
    try:
        from src.core.ocop_engine import OcopEngine

        engine = OcopEngine()
        product_id = str(args.get("product_id") or "OCOP-ST25")
        target_market = str(args.get("target_market") or args.get("market") or "EU")
        platform = str(args.get("platform") or "alibaba")
        res = engine.generate_b2b_listing(
            product_id=product_id,
            target_market=target_market,
            platform=platform,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"OCOP listing error: {exc}"}, indent=2)


def handle_ocop_compliance(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ocop_compliance."""
    try:
        from src.core.ocop_engine import OcopEngine

        engine = OcopEngine()
        market = str(args.get("market") or args.get("target_market") or "EU")
        res = engine.get_market_compliance(market)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"OCOP compliance error: {exc}"}, indent=2)


def handle_ocop_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ocop_status."""
    try:
        from src.core.ocop_engine import OcopEngine

        engine = OcopEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"OCOP status error: {exc}"}, indent=2)


def handle_vietqr_generate(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vietqr_generate."""
    try:
        from src.core.vietqr_engine import VietQrEngine

        engine = VietQrEngine()
        amount = int(args.get("amount") or args.get("amount_vnd") or 0)
        memo = str(args.get("memo") or "")
        bank = str(args.get("bank") or "MB")
        acc_num = str(args.get("account_number") or args.get("account") or "")
        acc_name = str(args.get("account_name") or args.get("name") or "")
        res = engine.generate_qr(
            bank=bank,
            account_number=acc_num,
            account_name=acc_name,
            amount_vnd=amount,
            memo=memo,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"VietQR generate error: {exc}"}, indent=2)


def handle_vietqr_banks(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vietqr_banks."""
    try:
        from src.core.vietqr_engine import VietQrEngine

        engine = VietQrEngine()
        banks = engine.list_banks()
        return json.dumps({"ok": True, "total": len(banks), "banks": banks}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"VietQR banks error: {exc}"}, indent=2)


def handle_vietqr_transactions(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vietqr_transactions."""
    try:
        from src.core.vietqr_engine import VietQrEngine

        engine = VietQrEngine()
        limit = int(args.get("limit", 20))
        txs = engine.list_transactions(limit=limit)
        return json.dumps({"ok": True, "total": len(txs), "transactions": txs}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"VietQR transactions error: {exc}"}, indent=2)


def handle_vietqr_record(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vietqr_record."""
    try:
        from src.core.vietqr_engine import VietQrEngine

        engine = VietQrEngine()
        tx_id = str(args.get("bank_tx_id") or args.get("tx_id") or "")
        amount = int(args.get("amount_vnd") or args.get("amount") or 0)
        memo = str(args.get("memo") or "")
        bin_code = str(args.get("bin_code") or "970422")
        order_id = str(args.get("matched_order_id") or args.get("order_id") or "")
        res = engine.record_transaction(
            bank_tx_id=tx_id,
            amount_vnd=amount,
            memo=memo,
            bin_code=bin_code,
            matched_order_id=order_id or None,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"VietQR record error: {exc}"}, indent=2)


def handle_vietqr_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_vietqr_status."""
    try:
        from src.core.vietqr_engine import VietQrEngine

        engine = VietQrEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"VietQR status error: {exc}"}, indent=2)


def handle_audit_run(args: dict[str, Any]) -> str:
    """Tool handler for mekong_audit_run."""
    if not isinstance(args, dict):
        args = {}
    framework = _clean_str(args.get("framework")) or "all"
    try:
        from src.core.sox_audit_engine import SoxAuditEngine

        engine = SoxAuditEngine()
        res = engine.run_audit(framework=framework)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Audit run error: {exc}"}, indent=2)


def handle_audit_controls(args: dict[str, Any]) -> str:
    """Tool handler for mekong_audit_controls."""
    if not isinstance(args, dict):
        args = {}
    domain = _clean_str(args.get("domain")) or "all"
    framework = _clean_str(args.get("framework")) or "all"
    try:
        from src.core.sox_audit_engine import SoxAuditEngine

        engine = SoxAuditEngine()
        res = engine.list_controls(domain=domain, framework=framework)
        return json.dumps({"ok": True, "controls": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Audit controls error: {exc}"}, indent=2)


def handle_audit_findings(args: dict[str, Any]) -> str:
    """Tool handler for mekong_audit_findings."""
    if not isinstance(args, dict):
        args = {}
    min_severity = _clean_str(args.get("min_severity") or args.get("severity")) or "all"
    try:
        from src.core.sox_audit_engine import SoxAuditEngine

        engine = SoxAuditEngine()
        res = engine.list_findings(min_severity=min_severity)
        return json.dumps({"ok": True, "findings": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Audit findings error: {exc}"}, indent=2)


def handle_audit_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_audit_status."""
    try:
        from src.core.sox_audit_engine import SoxAuditEngine

        engine = SoxAuditEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Audit status error: {exc}"}, indent=2)


def handle_payroll_gross_to_net(args: dict[str, Any]) -> str:
    """Tool handler for mekong_payroll_gross_to_net."""
    if not isinstance(args, dict):
        args = {}
    gross = float(args.get("gross", 0.0))
    dependents = int(args.get("dependents", 0))
    region = int(args.get("region", 1))
    lunch = float(args.get("lunch_allowance", 730000.0))
    try:
        from src.core.payroll_engine import PayrollEngine

        engine = PayrollEngine()
        res = engine.calculate_gross_to_net(
            gross=gross,
            dependents=dependents,
            region=region,
            lunch_allowance=lunch,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Payroll gross-to-net error: {exc}"}, indent=2)


def handle_payroll_net_to_gross(args: dict[str, Any]) -> str:
    """Tool handler for mekong_payroll_net_to_gross."""
    if not isinstance(args, dict):
        args = {}
    net = float(args.get("net", 0.0))
    dependents = int(args.get("dependents", 0))
    region = int(args.get("region", 1))
    lunch = float(args.get("lunch_allowance", 730000.0))
    try:
        from src.core.payroll_engine import PayrollEngine

        engine = PayrollEngine()
        res = engine.calculate_net_to_gross(
            net=net,
            dependents=dependents,
            region=region,
            lunch_allowance=lunch,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Payroll net-to-gross error: {exc}"}, indent=2)


def handle_payroll_payslip(args: dict[str, Any]) -> str:
    """Tool handler for mekong_payroll_payslip."""
    if not isinstance(args, dict):
        args = {}
    emp_name = _clean_str(args.get("employee_name")) or "Employee"
    gross = float(args.get("gross", 0.0))
    emp_id = _clean_str(args.get("employee_id")) or None
    month = _clean_str(args.get("month")) or None
    dependents = int(args.get("dependents", 0))
    region = int(args.get("region", 1))
    bonus = float(args.get("bonus", 0.0))
    try:
        from src.core.payroll_engine import PayrollEngine

        engine = PayrollEngine()
        res = engine.generate_payslip(
            employee_name=emp_name,
            gross=gross,
            employee_id=emp_id,
            month=month,
            dependents=dependents,
            region=region,
            bonus=bonus,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Payroll payslip error: {exc}"}, indent=2)


def handle_payroll_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_payroll_list."""
    if not isinstance(args, dict):
        args = {}
    month = _clean_str(args.get("month")) or ""
    limit = int(args.get("limit", 20))
    try:
        from src.core.payroll_engine import PayrollEngine

        engine = PayrollEngine()
        res = engine.list_payslips(month=month, limit=limit)
        return json.dumps({"ok": True, "payslips": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Payroll list error: {exc}"}, indent=2)


def handle_payroll_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_payroll_status."""
    try:
        from src.core.payroll_engine import PayrollEngine

        engine = PayrollEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Payroll status error: {exc}"}, indent=2)


def handle_corporate_charter(args: dict[str, Any]) -> str:
    """Tool handler for mekong_corporate_charter."""
    if not isinstance(args, dict):
        args = {}
    company_name = _clean_str(args.get("company_name")) or "CÔNG TY TNHH MEKONG"
    entity_type = _clean_str(args.get("entity_type")) or "TNHH_1TV"
    charter_capital = int(args.get("charter_capital", 1_000_000_000))
    legal_rep_name = _clean_str(args.get("legal_rep_name")) or "Nguyễn Văn A"
    address = _clean_str(args.get("address")) or "Hà Nội, Việt Nam"
    try:
        from src.core.corporate_engine import CorporateEngine

        engine = CorporateEngine()
        res = engine.generate_charter(
            company_name=company_name,
            entity_type=entity_type,
            charter_capital=charter_capital,
            legal_rep_name=legal_rep_name,
            address=address,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Corporate charter error: {exc}"}, indent=2)


def handle_corporate_resolution(args: dict[str, Any]) -> str:
    """Tool handler for mekong_corporate_resolution."""
    if not isinstance(args, dict):
        args = {}
    company_name = _clean_str(args.get("company_name")) or "CÔNG TY TNHH MEKONG"
    resolution_type = _clean_str(args.get("resolution_type")) or "APPOINTMENT"
    title = _clean_str(args.get("title")) or ""
    try:
        from src.core.corporate_engine import CorporateEngine

        engine = CorporateEngine()
        res = engine.generate_resolution(
            company_name=company_name,
            resolution_type=resolution_type,
            title=title,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Corporate resolution error: {exc}"}, indent=2)


def handle_corporate_dossier(args: dict[str, Any]) -> str:
    """Tool handler for mekong_corporate_dossier."""
    if not isinstance(args, dict):
        args = {}
    company_name = _clean_str(args.get("company_name")) or "CÔNG TY TNHH MEKONG"
    entity_type = _clean_str(args.get("entity_type")) or "TNHH_1TV"
    charter_capital = int(args.get("charter_capital", 1_000_000_000))
    legal_rep_name = _clean_str(args.get("legal_rep_name")) or "Nguyễn Văn A"
    address = _clean_str(args.get("address")) or "Hà Nội, Việt Nam"
    main_industry = _clean_str(args.get("main_industry")) or "6201"
    try:
        from src.core.corporate_engine import CorporateEngine

        engine = CorporateEngine()
        res = engine.create_filing_dossier(
            company_name=company_name,
            entity_type=entity_type,
            charter_capital=charter_capital,
            legal_rep_name=legal_rep_name,
            address=address,
            main_industry=main_industry,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Corporate dossier error: {exc}"}, indent=2)


def handle_corporate_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_corporate_list."""
    if not isinstance(args, dict):
        args = {}
    limit = int(args.get("limit", 20))
    try:
        from src.core.corporate_engine import CorporateEngine

        engine = CorporateEngine()
        res = engine.list_filings(limit=limit)
        return json.dumps({"ok": True, "filings": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Corporate list error: {exc}"}, indent=2)


def handle_corporate_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_corporate_status."""
    try:
        from src.core.corporate_engine import CorporateEngine

        engine = CorporateEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Corporate status error: {exc}"}, indent=2)


def handle_fdi_market_access(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fdi_market_access."""
    try:
        from src.core.fdi_engine import FDIEngine

        engine = FDIEngine()
        sector_code = str(args.get("sector_code", "6201"))
        investor_nationality = str(args.get("investor_nationality", "US"))
        ownership_pct = float(args.get("ownership_pct", 100.0))
        res = engine.evaluate_market_access(
            sector_code=sector_code,
            investor_nationality=investor_nationality,
            ownership_pct=ownership_pct,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"FDI market access error: {exc}"}, indent=2)


def handle_fdi_remittance(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fdi_remittance."""
    try:
        from src.core.fdi_engine import FDIEngine

        engine = FDIEngine()
        fiscal_year = int(args.get("fiscal_year", 2025))
        audited_profit_vnd = float(args.get("audited_profit_vnd", 0.0))
        tax_cleared = bool(args.get("tax_cleared", True))
        retained_reserve_pct = float(args.get("retained_reserve_pct", 5.0))
        dica_verified = bool(args.get("dica_verified", True))
        losses_carried_forward_vnd = float(args.get("losses_carried_forward_vnd", 0.0))
        res = engine.verify_profit_remittance(
            fiscal_year=fiscal_year,
            audited_profit_vnd=audited_profit_vnd,
            tax_cleared=tax_cleared,
            retained_reserve_pct=retained_reserve_pct,
            dica_verified=dica_verified,
            losses_carried_forward_vnd=losses_carried_forward_vnd,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"FDI remittance error: {exc}"}, indent=2)


def handle_fdi_foreign_loan(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fdi_foreign_loan."""
    try:
        from src.core.fdi_engine import FDIEngine

        engine = FDIEngine()
        loan_amount = float(args.get("loan_amount", 0.0))
        currency = str(args.get("currency", "USD"))
        tenure_months = int(args.get("tenure_months", 24))
        interest_rate_pct = float(args.get("interest_rate_pct", 6.5))
        project_capital_gap = float(args.get("project_capital_gap", 0.0))
        res = engine.evaluate_foreign_loan(
            loan_amount=loan_amount,
            currency=currency,
            tenure_months=tenure_months,
            interest_rate_pct=interest_rate_pct,
            project_capital_gap=project_capital_gap,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"FDI foreign loan error: {exc}"}, indent=2)


def handle_fdi_irc(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fdi_irc."""
    try:
        from src.core.fdi_engine import FDIEngine

        engine = FDIEngine()
        project_name = str(args.get("project_name", "FDI Tech Project"))
        sector_code = str(args.get("sector_code", "6201"))
        total_investment_vnd = float(args.get("total_investment_vnd", 2_500_000_000))
        investor_name = str(args.get("investor_name", "Foreign Investor Corp"))
        investor_country = str(args.get("investor_country", "US"))
        project_location = str(args.get("project_location", "TP. Hồ Chí Minh"))
        res = engine.generate_irc_dossier(
            project_name=project_name,
            sector_code=sector_code,
            total_investment_vnd=total_investment_vnd,
            investor_name=investor_name,
            investor_country=investor_country,
            project_location=project_location,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"FDI IRC dossier error: {exc}"}, indent=2)


def handle_fdi_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fdi_status."""
    try:
        from src.core.fdi_engine import FDIEngine

        engine = FDIEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"FDI status error: {exc}"}, indent=2)


def handle_ip_trademark(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ip_trademark."""
    try:
        from src.core.ip_engine import IPEngine

        engine = IPEngine()
        mark_name = str(args.get("mark_name", ""))
        nice_class = str(args.get("nice_class", "09"))
        applicant_name = str(args.get("applicant_name", "Công Ty Công Nghệ Mekong"))
        goods_services_spec = str(args.get("goods_services_spec", ""))
        res = engine.register_trademark(
            mark_name=mark_name,
            nice_class=nice_class,
            applicant_name=applicant_name,
            goods_services_spec=goods_services_spec,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"IP trademark error: {exc}"}, indent=2)


def handle_ip_search(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ip_search."""
    try:
        from src.core.ip_engine import IPEngine

        engine = IPEngine()
        mark_name = str(args.get("mark_name", ""))
        nice_class = str(args.get("nice_class", "09"))
        res = engine.search_trademark_similarity(
            mark_name=mark_name,
            nice_class=nice_class,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"IP search error: {exc}"}, indent=2)


def handle_ip_patent(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ip_patent."""
    try:
        from src.core.ip_engine import IPEngine

        engine = IPEngine()
        title = str(args.get("title", ""))
        technical_field = str(args.get("technical_field", ""))
        applicant_name = str(args.get("applicant_name", "Tổ chức Nghiên cứu Mekong"))
        independent_claims = int(args.get("independent_claims", 1))
        dependent_claims = int(args.get("dependent_claims", 2))
        res = engine.draft_patent_specification(
            title=title,
            technical_field=technical_field,
            applicant_name=applicant_name,
            independent_claims=independent_claims,
            dependent_claims=dependent_claims,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"IP patent error: {exc}"}, indent=2)


def handle_ip_copyright(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ip_copyright."""
    try:
        from src.core.ip_engine import IPEngine

        engine = IPEngine()
        software_name = str(args.get("software_name", ""))
        author_name = str(args.get("author_name", ""))
        version = str(args.get("version", "1.0.0"))
        repository_url = str(args.get("repository_url", ""))
        lines_of_code = int(args.get("lines_of_code", 10000))
        res = engine.register_software_copyright(
            software_name=software_name,
            author_name=author_name,
            version=version,
            repository_url=repository_url,
            lines_of_code=lines_of_code,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"IP copyright error: {exc}"}, indent=2)


def handle_ip_fees(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ip_fees."""
    try:
        from src.core.ip_engine import IPEngine

        engine = IPEngine()
        trademark_classes = int(args.get("trademark_classes", 1))
        patent_claims = int(args.get("patent_claims", 1))
        software_copyrights = int(args.get("software_copyrights", 1))
        res = engine.calculate_statutory_fees(
            trademark_classes=trademark_classes,
            patent_claims=patent_claims,
            software_copyrights=software_copyrights,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"IP fees error: {exc}"}, indent=2)


def handle_ip_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ip_status."""
    try:
        from src.core.ip_engine import IPEngine

        engine = IPEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"IP status error: {exc}"}, indent=2)


def handle_customs_hs_lookup(args: dict[str, Any]) -> str:
    """Tool handler for mekong_customs_hs_lookup."""
    try:
        from src.core.customs_engine import CustomsEngine

        engine = CustomsEngine()
        hs_code = str(args.get("hs_code", ""))
        fta = str(args.get("fta", "MFN"))
        res = engine.lookup_hs_code(hs_code=hs_code, fta=fta)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Customs HS lookup error: {exc}"}, indent=2)


def handle_customs_duty_calc(args: dict[str, Any]) -> str:
    """Tool handler for mekong_customs_duty_calc."""
    try:
        from src.core.customs_engine import CustomsEngine

        engine = CustomsEngine()
        invoice_value_usd = float(args.get("invoice_value_usd", 0.0))
        hs_code = str(args.get("hs_code", "8471.30.20"))
        freight_usd = float(args.get("freight_usd", 0.0))
        insurance_usd = float(args.get("insurance_usd", 0.0))
        fta = str(args.get("fta", "MFN"))
        res = engine.calculate_customs_duties(
            invoice_value_usd=invoice_value_usd,
            hs_code=hs_code,
            freight_usd=freight_usd,
            insurance_usd=insurance_usd,
            fta=fta,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Customs duty calculation error: {exc}"}, indent=2)


def handle_customs_channel(args: dict[str, Any]) -> str:
    """Tool handler for mekong_customs_channel."""
    try:
        from src.core.customs_engine import CustomsEngine

        engine = CustomsEngine()
        enterprise_tax_id = str(args.get("enterprise_tax_id", ""))
        hs_code = str(args.get("hs_code", ""))
        invoice_value_usd = float(args.get("invoice_value_usd", 0.0))
        origin_country = str(args.get("origin_country", "US"))
        compliance_tier = str(args.get("compliance_tier", "TIER_2_NORMAL"))
        has_valid_co = bool(args.get("has_valid_co", True))
        res = engine.evaluate_customs_channel(
            enterprise_tax_id=enterprise_tax_id,
            hs_code=hs_code,
            invoice_value_usd=invoice_value_usd,
            origin_country=origin_country,
            compliance_tier=compliance_tier,
            has_valid_co=has_valid_co,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Customs channel error: {exc}"}, indent=2)


def handle_customs_declare(args: dict[str, Any]) -> str:
    """Tool handler for mekong_customs_declare."""
    try:
        from src.core.customs_engine import CustomsEngine

        engine = CustomsEngine()
        enterprise_tax_id = str(args.get("enterprise_tax_id", ""))
        hs_code = str(args.get("hs_code", ""))
        commodity_name = str(args.get("commodity_name", ""))
        invoice_value_usd = float(args.get("invoice_value_usd", 0.0))
        origin_country = str(args.get("origin_country", "US"))
        declaration_type = str(args.get("declaration_type", "IMPORT_BUSINESS"))
        compliance_tier = str(args.get("compliance_tier", "TIER_2_NORMAL"))
        has_valid_co = bool(args.get("has_valid_co", True))
        res = engine.create_declaration(
            enterprise_tax_id=enterprise_tax_id,
            hs_code=hs_code,
            commodity_name=commodity_name,
            invoice_value_usd=invoice_value_usd,
            origin_country=origin_country,
            declaration_type=declaration_type,
            compliance_tier=compliance_tier,
            has_valid_co=has_valid_co,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Customs declaration error: {exc}"}, indent=2)


def handle_customs_origin(args: dict[str, Any]) -> str:
    """Tool handler for mekong_customs_origin."""
    try:
        from src.core.customs_engine import CustomsEngine

        engine = CustomsEngine()
        form_type = str(args.get("form_type", "EUR.1"))
        hs_code = str(args.get("hs_code", ""))
        fob_value_usd = float(args.get("fob_value_usd", 0.0))
        non_originating_value_usd = float(args.get("non_originating_value_usd", 0.0))
        exporter_name = str(args.get("exporter_name", "Doanh Nghiệp Xuất Khẩu Việt Nam"))
        importer_country = str(args.get("importer_country", "DE"))
        res = engine.verify_rules_of_origin(
            form_type=form_type,
            hs_code=hs_code,
            fob_value_usd=fob_value_usd,
            non_originating_value_usd=non_originating_value_usd,
            exporter_name=exporter_name,
            importer_country=importer_country,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Customs origin error: {exc}"}, indent=2)


def handle_customs_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_customs_status."""
    try:
        from src.core.customs_engine import CustomsEngine

        engine = CustomsEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Customs status error: {exc}"}, indent=2)


def handle_contract_draft(args: dict[str, Any]) -> str:
    """Tool handler for mekong_contract_draft."""
    try:
        from src.core.contract_engine import ContractEngine

        engine = ContractEngine()
        template_type = str(args.get("template_type", "SOFTWARE_DEV"))
        party_a_name = str(args.get("party_a_name", "Bên A"))
        party_b_name = str(args.get("party_b_name", "Bên B"))
        contract_value_vnd = float(args.get("contract_value_vnd", 0.0))
        party_a_tax_id = str(args.get("party_a_tax_id", "0100000001"))
        party_b_tax_id = str(args.get("party_b_tax_id", "0300000002"))
        scope_summary = str(args.get("scope_summary", ""))
        penalty_rate_pct = float(args.get("penalty_rate_pct", 8.0))
        dispute_forum = str(args.get("dispute_forum", "VIAC"))
        res = engine.draft_contract(
            template_type=template_type,
            party_a_name=party_a_name,
            party_b_name=party_b_name,
            contract_value_vnd=contract_value_vnd,
            party_a_tax_id=party_a_tax_id,
            party_b_tax_id=party_b_tax_id,
            scope_summary=scope_summary,
            penalty_rate_pct=penalty_rate_pct,
            dispute_forum=dispute_forum,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Contract drafting error: {exc}"}, indent=2)


def handle_contract_risk_check(args: dict[str, Any]) -> str:
    """Tool handler for mekong_contract_risk_check."""
    try:
        from src.core.contract_engine import ContractEngine

        engine = ContractEngine()
        contract_text = str(args.get("contract_text", ""))
        penalty_pct = args.get("penalty_pct")
        p_val = float(penalty_pct) if penalty_pct is not None else None
        res = engine.assess_contract_risk(contract_text=contract_text, penalty_pct=p_val)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Contract risk assessment error: {exc}"}, indent=2)


def handle_contract_sign(args: dict[str, Any]) -> str:
    """Tool handler for mekong_contract_sign."""
    try:
        from src.core.contract_engine import ContractEngine

        engine = ContractEngine()
        contract_id = str(args.get("contract_id", ""))
        signer_name = str(args.get("signer_name", ""))
        signer_title = str(args.get("signer_title", "Giám đốc điều hành"))
        signer_tax_id = str(args.get("signer_tax_id", "0100000001"))
        organization_name = str(args.get("organization_name", ""))
        res = engine.sign_contract(
            contract_id=contract_id,
            signer_name=signer_name,
            signer_title=signer_title,
            signer_tax_id=signer_tax_id,
            organization_name=organization_name,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Contract e-signing error: {exc}"}, indent=2)


def handle_contract_verify(args: dict[str, Any]) -> str:
    """Tool handler for mekong_contract_verify."""
    try:
        from src.core.contract_engine import ContractEngine

        engine = ContractEngine()
        signature_id = str(args.get("signature_id", ""))
        res = engine.verify_signature(signature_id=signature_id)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Contract signature verification error: {exc}"}, indent=2)


def handle_contract_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_contract_list."""
    try:
        from src.core.contract_engine import ContractEngine

        engine = ContractEngine()
        status = str(args.get("status", "ALL"))
        limit = int(args.get("limit", 20))
        res = engine.list_contracts(status=status, limit=limit)
        return json.dumps({"ok": True, "contracts": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Contract list error: {exc}"}, indent=2)


def handle_contract_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_contract_status."""
    try:
        from src.core.contract_engine import ContractEngine

        engine = ContractEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Contract status error: {exc}"}, indent=2)


def handle_tender_method(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tender_method."""
    try:
        from src.core.tender_engine import TenderEngine

        engine = TenderEngine()
        package_type = str(args.get("package_type", "GOODS"))
        budget_vnd = float(args.get("budget_vnd", 0.0))
        urgent = bool(args.get("urgent", False))
        proprietary = bool(args.get("proprietary", False))
        res = engine.evaluate_procurement_method(
            package_type=package_type,
            budget_vnd=budget_vnd,
            is_urgent=urgent,
            is_proprietary_tech=proprietary,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tender method evaluation error: {exc}"}, indent=2)


def handle_tender_create(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tender_create."""
    try:
        from src.core.tender_engine import TenderEngine

        engine = TenderEngine()
        package_name = str(args.get("package_name", ""))
        procuring_entity = str(args.get("procuring_entity", ""))
        budget_vnd = float(args.get("budget_vnd", 0.0))
        package_type = str(args.get("package_type", "GOODS"))
        procurement_method = args.get("procurement_method")
        p_method = str(procurement_method) if procurement_method else None
        submission_days = int(args.get("submission_days", 15))
        res = engine.create_tender(
            package_name=package_name,
            procuring_entity=procuring_entity,
            budget_vnd=budget_vnd,
            package_type=package_type,
            procurement_method=p_method,
            submission_days=submission_days,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tender creation error: {exc}"}, indent=2)


def handle_tender_eval(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tender_eval."""
    try:
        from src.core.tender_engine import TenderEngine

        engine = TenderEngine()
        tender_id = str(args.get("tender_id", ""))
        bidder_name = str(args.get("bidder_name", ""))
        bid_price_vnd = float(args.get("bid_price_vnd", 0.0))
        bidder_tax_id = str(args.get("bidder_tax_id", "0101234567"))
        revenue_3yr_avg_vnd = float(args.get("revenue_3yr_avg_vnd", 0.0))
        similar_contract_val_vnd = float(args.get("similar_contract_val_vnd", 0.0))
        tech_score = float(args.get("tech_score", 85.0))
        has_valid_security = bool(args.get("has_valid_security", True))
        res = engine.evaluate_bid(
            tender_id=tender_id,
            bidder_name=bidder_name,
            bid_price_vnd=bid_price_vnd,
            bidder_tax_id=bidder_tax_id,
            revenue_3yr_avg_vnd=revenue_3yr_avg_vnd,
            similar_contract_val_vnd=similar_contract_val_vnd,
            tech_score=tech_score,
            has_valid_security=has_valid_security,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Bid evaluation error: {exc}"}, indent=2)


def handle_tender_collusion_scan(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tender_collusion_scan."""
    try:
        from src.core.tender_engine import TenderEngine

        engine = TenderEngine()
        tender_id = str(args.get("tender_id", ""))
        res = engine.detect_bid_collusion(tender_id=tender_id)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Bid collusion scan error: {exc}"}, indent=2)


def handle_tender_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tender_list."""
    try:
        from src.core.tender_engine import TenderEngine

        engine = TenderEngine()
        status = str(args.get("status", "ALL"))
        limit = int(args.get("limit", 20))
        res = engine.list_tenders(status=status, limit=limit)
        return json.dumps({"ok": True, "tenders": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tender list error: {exc}"}, indent=2)


def handle_tender_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_tender_status."""
    try:
        from src.core.tender_engine import TenderEngine

        engine = TenderEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Tender status error: {exc}"}, indent=2)


def handle_realestate_finance(args: dict[str, Any]) -> str:
    """Tool handler for mekong_realestate_finance."""
    try:
        from src.core.realestate_engine import RealEstateEngine

        engine = RealEstateEngine()
        category = str(args.get("category", "COMMERCIAL_OFFICE"))
        area_sqm = float(args.get("area_sqm", 0.0))
        unit_rent_usd = float(args.get("unit_rent_usd", 0.0))
        lease_term_months = int(args.get("lease_term_months", 36))
        maintenance_fee_usd = float(args.get("maintenance_fee_usd", 0.5))
        deposit_months = int(args.get("deposit_months", 3))
        annual_escalation_pct = float(args.get("annual_escalation_pct", 3.0))
        res = engine.calculate_lease_financials(
            category=category,
            area_sqm=area_sqm,
            unit_rent_usd=unit_rent_usd,
            lease_term_months=lease_term_months,
            maintenance_fee_usd=maintenance_fee_usd,
            deposit_months=deposit_months,
            annual_escalation_pct=annual_escalation_pct,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Real estate financial calculation error: {exc}"}, indent=2)


def handle_realestate_density(args: dict[str, Any]) -> str:
    """Tool handler for mekong_realestate_density."""
    try:
        from src.core.realestate_engine import RealEstateEngine

        engine = RealEstateEngine()
        lot_area_sqm = float(args.get("lot_area_sqm", 0.0))
        building_footprint_sqm = float(args.get("building_footprint_sqm", 0.0))
        green_space_sqm = float(args.get("green_space_sqm", 0.0))
        building_height_tier = str(args.get("building_height_tier", "UP_TO_20M"))
        res = engine.validate_construction_density(
            lot_area_sqm=lot_area_sqm,
            building_footprint_sqm=building_footprint_sqm,
            green_space_sqm=green_space_sqm,
            building_height_tier=building_height_tier,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Density validation error: {exc}"}, indent=2)


def handle_realestate_audit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_realestate_audit."""
    try:
        from src.core.realestate_engine import RealEstateEngine

        engine = RealEstateEngine()
        project_name = str(args.get("project_name", ""))
        category = str(args.get("category", "INDUSTRIAL_LAND"))
        land_area_sqm = float(args.get("land_area_sqm", 0.0))
        has_land_cert = bool(args.get("has_land_cert", True))
        has_construction_permit = bool(args.get("has_construction_permit", True))
        has_fire_safety_cert = bool(args.get("has_fire_safety_cert", True))
        tenure_remaining_years = float(args.get("tenure_remaining_years", 35.0))
        payment_term = str(args.get("payment_term", "ANNUAL_RENT"))
        has_disputes = bool(args.get("has_disputes", False))
        is_mortgaged_to_bank = bool(args.get("is_mortgaged_to_bank", False))
        res = engine.perform_due_diligence(
            project_name=project_name,
            category=category,
            land_area_sqm=land_area_sqm,
            has_land_cert=has_land_cert,
            has_construction_permit=has_construction_permit,
            has_fire_safety_cert=has_fire_safety_cert,
            tenure_remaining_years=tenure_remaining_years,
            payment_term=payment_term,
            has_disputes=has_disputes,
            is_mortgaged_to_bank=is_mortgaged_to_bank,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Real estate due diligence error: {exc}"}, indent=2)


def handle_realestate_draft(args: dict[str, Any]) -> str:
    """Tool handler for mekong_realestate_draft."""
    try:
        from src.core.realestate_engine import RealEstateEngine

        engine = RealEstateEngine()
        property_id = str(args.get("property_id", ""))
        lessor_name = str(args.get("lessor_name", ""))
        lessee_name = str(args.get("lessee_name", ""))
        leased_area_sqm = float(args.get("leased_area_sqm", 0.0))
        unit_rent_usd = float(args.get("unit_rent_usd", 0.0))
        lease_term_months = int(args.get("lease_term_months", 36))
        maintenance_fee_usd = float(args.get("maintenance_fee_usd", 0.5))
        deposit_months = int(args.get("deposit_months", 3))
        dispute_resolution = str(args.get("dispute_resolution", "VIAC"))
        res = engine.draft_lease_agreement(
            property_id=property_id,
            lessor_name=lessor_name,
            lessee_name=lessee_name,
            leased_area_sqm=leased_area_sqm,
            unit_rent_usd=unit_rent_usd,
            lease_term_months=lease_term_months,
            maintenance_fee_usd=maintenance_fee_usd,
            deposit_months=deposit_months,
            dispute_resolution=dispute_resolution,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Lease agreement drafting error: {exc}"}, indent=2)


def handle_realestate_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_realestate_list."""
    try:
        from src.core.realestate_engine import RealEstateEngine

        engine = RealEstateEngine()
        category = str(args.get("category", "ALL"))
        limit = int(args.get("limit", 20))
        res = engine.list_properties(category=category, limit=limit)
        return json.dumps({"ok": True, "properties": res, "total": len(res)}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Real estate list error: {exc}"}, indent=2)


def handle_realestate_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_realestate_status."""
    try:
        from src.core.realestate_engine import RealEstateEngine

        engine = RealEstateEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Real estate status error: {exc}"}, indent=2)


def handle_esg_ghg(args: dict[str, Any]) -> str:
    """Tool handler for mekong_esg_ghg."""
    try:
        from src.core.esg_engine import EsgEngine

        engine = EsgEngine()
        enterprise_name = str(args.get("enterprise_name", ""))
        reporting_year = int(args.get("reporting_year", datetime.datetime.now().year))
        fuel_diesel_liters = float(args.get("fuel_diesel_liters", 0.0))
        fuel_gasoline_liters = float(args.get("fuel_gasoline_liters", 0.0))
        coal_tons = float(args.get("coal_tons", 0.0))
        lpg_kg = float(args.get("lpg_kg", 0.0))
        electricity_kwh = float(args.get("electricity_kwh", 0.0))
        scope3_logistics_tco2e = float(args.get("scope3_logistics_tco2e", 0.0))

        res = engine.calculate_ghg_inventory(
            enterprise_name=enterprise_name,
            reporting_year=reporting_year,
            fuel_diesel_liters=fuel_diesel_liters,
            fuel_gasoline_liters=fuel_gasoline_liters,
            coal_tons=coal_tons,
            lpg_kg=lpg_kg,
            electricity_kwh=electricity_kwh,
            scope3_logistics_tco2e=scope3_logistics_tco2e,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"ESG GHG inventory error: {exc}"}, indent=2)


def handle_esg_cbam(args: dict[str, Any]) -> str:
    """Tool handler for mekong_esg_cbam."""
    try:
        from src.core.esg_engine import EsgEngine

        engine = EsgEngine()
        product_type = str(args.get("product_type", "STEEL"))
        export_volume_tons = float(args.get("export_volume_tons", 0.0))
        direct_emissions_tco2 = float(args.get("direct_emissions_tco2", 0.0))
        indirect_emissions_tco2 = float(args.get("indirect_emissions_tco2", 0.0))
        cbam_carbon_price_eur_per_ton = float(args.get("cbam_carbon_price_eur_per_ton", 75.0))

        res = engine.evaluate_cbam_liability(
            product_type=product_type,
            export_volume_tons=export_volume_tons,
            direct_emissions_tco2=direct_emissions_tco2,
            indirect_emissions_tco2=indirect_emissions_tco2,
            cbam_carbon_price_eur_per_ton=cbam_carbon_price_eur_per_ton,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"ESG CBAM liability error: {exc}"}, indent=2)


def handle_esg_audit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_esg_audit."""
    try:
        from src.core.esg_engine import EsgEngine

        engine = EsgEngine()
        enterprise_name = str(args.get("enterprise_name", ""))
        has_iso_14001 = bool(args.get("has_iso_14001", True))
        renewable_energy_ratio_pct = float(args.get("renewable_energy_ratio_pct", 20.0))
        has_waste_treatment_license = bool(args.get("has_waste_treatment_license", True))
        full_social_insurance_compliance = bool(args.get("full_social_insurance_compliance", True))
        workplace_accident_rate = float(args.get("workplace_accident_rate", 0.0))
        female_leadership_ratio_pct = float(args.get("female_leadership_ratio_pct", 30.0))
        independent_board_members_ratio_pct = float(args.get("independent_board_members_ratio_pct", 33.3))
        has_anti_corruption_policy = bool(args.get("has_anti_corruption_policy", True))
        has_audited_financial_report = bool(args.get("has_audited_financial_report", True))

        res = engine.audit_esg_score(
            enterprise_name=enterprise_name,
            has_iso_14001=has_iso_14001,
            renewable_energy_ratio_pct=renewable_energy_ratio_pct,
            has_waste_treatment_license=has_waste_treatment_license,
            full_social_insurance_compliance=full_social_insurance_compliance,
            workplace_accident_rate=workplace_accident_rate,
            female_leadership_ratio_pct=female_leadership_ratio_pct,
            independent_board_members_ratio_pct=independent_board_members_ratio_pct,
            has_anti_corruption_policy=has_anti_corruption_policy,
            has_audited_financial_report=has_audited_financial_report,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"ESG audit error: {exc}"}, indent=2)


def handle_esg_carbon_trade(args: dict[str, Any]) -> str:
    """Tool handler for mekong_esg_carbon_trade."""
    try:
        from src.core.esg_engine import EsgEngine

        engine = EsgEngine()
        project_name = str(args.get("project_name", ""))
        credit_type = str(args.get("credit_type", "VCS"))
        quantity_tco2e = float(args.get("quantity_tco2e", 0.0))
        unit_price_usd = float(args.get("unit_price_usd", 0.0))
        action = str(args.get("action", "BUY"))
        counterparty = str(args.get("counterparty", "Sàn giao dịch Carbon Quốc gia"))

        res = engine.trade_carbon_credits(
            project_name=project_name,
            credit_type=credit_type,
            quantity_tco2e=quantity_tco2e,
            unit_price_usd=unit_price_usd,
            action=action,
            counterparty=counterparty,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"ESG carbon trade error: {exc}"}, indent=2)


def handle_esg_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_esg_list."""
    try:
        from src.core.esg_engine import EsgEngine

        engine = EsgEngine()
        limit = int(args.get("limit", 20))
        invs = engine.list_inventories(limit=limit)
        txs = engine.list_transactions(limit=limit)
        return json.dumps({"ok": True, "ghg_inventories": invs, "carbon_transactions": txs}, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"ESG list error: {exc}"}, indent=2)


def handle_esg_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_esg_status."""
    try:
        from src.core.esg_engine import EsgEngine

        engine = EsgEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"ESG status error: {exc}"}, indent=2)


def handle_supplychain_plot(args: dict[str, Any]) -> str:
    """Tool handler for mekong_supplychain_plot."""
    try:
        from src.core.supplychain_engine import SupplyChainEngine

        engine = SupplyChainEngine()
        farmer_name = str(args.get("farmer_name", ""))
        province = str(args.get("province", ""))
        commodity = str(args.get("commodity", "COFFEE"))
        latitude = float(args.get("latitude", 0.0))
        longitude = float(args.get("longitude", 0.0))
        area_hectares = float(args.get("area_hectares", 1.0))
        district = str(args.get("district", "Tây Nguyên"))
        deforestation_free_post_2020 = bool(args.get("deforestation_free_post_2020", True))
        legal_land_cert = str(args.get("legal_land_cert", "Sổ đỏ nông nghiệp / Giấy chứng nhận QSDĐ"))

        res = engine.register_plot(
            farmer_name=farmer_name,
            province=province,
            commodity=commodity,
            latitude=latitude,
            longitude=longitude,
            area_hectares=area_hectares,
            district=district,
            deforestation_free_post_2020=deforestation_free_post_2020,
            legal_land_cert=legal_land_cert,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Supply chain plot registration error: {exc}"}, indent=2)


def handle_supplychain_batch(args: dict[str, Any]) -> str:
    """Tool handler for mekong_supplychain_batch."""
    try:
        from src.core.supplychain_engine import SupplyChainEngine

        engine = SupplyChainEngine()
        batch_code = str(args.get("batch_code", ""))
        commodity = str(args.get("commodity", "COFFEE"))
        quantity_kg = float(args.get("quantity_kg", 0.0))
        processor_name = str(args.get("processor_name", ""))
        plot_ids = args.get("plot_ids")
        certifications = args.get("certifications")

        res = engine.create_batch(
            batch_code=batch_code,
            commodity=commodity,
            quantity_kg=quantity_kg,
            processor_name=processor_name,
            plot_ids=plot_ids if isinstance(plot_ids, list) else None,
            certifications=certifications if isinstance(certifications, list) else None,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Supply chain batch creation error: {exc}"}, indent=2)


def handle_supplychain_event(args: dict[str, Any]) -> str:
    """Tool handler for mekong_supplychain_event."""
    try:
        from src.core.supplychain_engine import SupplyChainEngine

        engine = SupplyChainEngine()
        batch_code = str(args.get("batch_code", ""))
        event_type = str(args.get("event_type", "PROCESS"))
        location = str(args.get("location", ""))
        actor_name = str(args.get("actor_name", ""))
        notes = str(args.get("notes", ""))

        res = engine.record_custody_event(
            batch_code=batch_code,
            event_type=event_type,
            location=location,
            actor_name=actor_name,
            notes=notes,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Supply chain custody event error: {exc}"}, indent=2)


def handle_supplychain_eudr(args: dict[str, Any]) -> str:
    """Tool handler for mekong_supplychain_eudr."""
    try:
        from src.core.supplychain_engine import SupplyChainEngine

        engine = SupplyChainEngine()
        batch_code = str(args.get("batch_code", ""))
        exporter_name = str(args.get("exporter_name", ""))
        importer_name = str(args.get("importer_name", ""))
        destination_country = str(args.get("destination_country", "Germany"))

        res = engine.generate_eudr_statement(
            batch_code=batch_code,
            exporter_name=exporter_name,
            importer_name=importer_name,
            destination_country=destination_country,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Supply chain EUDR statement error: {exc}"}, indent=2)


def handle_supplychain_trace(args: dict[str, Any]) -> str:
    """Tool handler for mekong_supplychain_trace."""
    try:
        from src.core.supplychain_engine import SupplyChainEngine

        engine = SupplyChainEngine()
        batch_code = str(args.get("batch_code", ""))
        res = engine.get_batch_trace(batch_code=batch_code)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Supply chain trace error: {exc}"}, indent=2)


def handle_supplychain_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_supplychain_status."""
    try:
        from src.core.supplychain_engine import SupplyChainEngine

        engine = SupplyChainEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Supply chain status error: {exc}"}, indent=2)


def handle_labor_permit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_permit."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        res = engine.evaluate_work_permit_eligibility(
            worker_name=_clean_str(args.get("worker_name")) or "Foreign Employee",
            nationality=_clean_str(args.get("nationality")) or "Foreign",
            position_category=_clean_str(args.get("position")) or "EXPERT",
            job_title=_clean_str(args.get("job_title")) or "Specialist",
            education_degree=_clean_str(args.get("degree")) or "BACHELOR",
            experience_years=float(args.get("exp", 3.0)),
            capital_contribution_vnd=float(args.get("capital", 0.0)),
            is_wto_internal_transfer=bool(args.get("wto", False)),
            married_to_vietnamese=bool(args.get("married_vn", False)),
            passport_number=_clean_str(args.get("passport")) or "PASS-DEFAULT",
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor permit error: {exc}"}, indent=2)


def handle_labor_overtime(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_overtime."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        res = engine.calculate_overtime_pay(
            hourly_rate_vnd=float(args.get("hourly_rate", 100000.0)),
            normal_day_ot_hours=float(args.get("weekday_ot", 0.0)),
            weekend_ot_hours=float(args.get("weekend_ot", 0.0)),
            holiday_ot_hours=float(args.get("holiday_ot", 0.0)),
            night_shift_regular_hours=float(args.get("night_regular", 0.0)),
            night_shift_ot_hours=float(args.get("night_ot", 0.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor overtime error: {exc}"}, indent=2)


def handle_labor_caps(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_caps."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        monthly = float(args.get("monthly_ot_hours", 0.0))
        yearly = float(args.get("yearly_cumulative_hours", 0.0))
        exceptional = bool(args.get("exceptional", False))
        res = engine.validate_overtime_caps(
            monthly_overtime_hours=monthly,
            yearly_cumulative_hours=yearly,
            is_extended_industry=exceptional,
        )
        res["employee_id"] = _clean_str(args.get("employee_id")) or "EMP-001"
        res["employee_name"] = _clean_str(args.get("employee_name")) or "Employee"
        res["industry"] = _clean_str(args.get("industry")) or "GENERAL"
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor caps error: {exc}"}, indent=2)


def handle_labor_severance(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_severance."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        avg_sal = float(args.get("average_salary", 15000000.0))
        total_yrs = float(args.get("total_years", 3.0))
        bhtn_yrs = float(args.get("bhtn_years", 0.0))
        allowance_type = _clean_str(args.get("allowance_type")) or "SEVERANCE"
        res = engine.calculate_termination_allowance(
            average_salary_vnd=avg_sal,
            total_working_months=round(total_yrs * 12),
            bhtn_working_months=round(bhtn_yrs * 12),
            termination_type=allowance_type,
        )
        res["employee_name"] = _clean_str(args.get("employee_name")) or "Employee"
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor severance error: {exc}"}, indent=2)


def handle_labor_regulations(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_regulations."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        res = engine.audit_internal_regulations(
            enterprise_name=_clean_str(args.get("enterprise_name")) or "Enterprise",
            total_employees=int(args.get("total_employees", 25)),
            has_written_regulations=bool(args.get("has_written_regulations", True)),
            is_registered_with_dolab=bool(args.get("is_registered", True)),
            has_dialogue_mechanism=bool(args.get("dialogue", True)),
            has_safety_council=bool(args.get("safety_council", True)),
            dolab_filing_number=_clean_str(args.get("docket")) or "NQLD-2026-DOLAB",
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor regulations error: {exc}"}, indent=2)


def handle_labor_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_list."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        res = engine.list_workers(
            position=_clean_str(args.get("category")) or "ALL",
            limit=int(args.get("limit", 50)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor list error: {exc}"}, indent=2)


def handle_labor_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_labor_status."""
    try:
        from src.core.labor_engine import LaborEngine

        engine = LaborEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Labor status error: {exc}"}, indent=2)


def handle_maritime_vessel(args: dict[str, Any]) -> str:
    """Tool handler for mekong_maritime_vessel."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.maritime_engine import MaritimeEngine

        engine = MaritimeEngine()
        res = engine.register_vessel_call(
            vessel_name=_clean_str(args.get("name")) or "Commercial Vessel",
            imo_number=_clean_str(args.get("imo")) or "IMO9811000",
            flag_state=_clean_str(args.get("flag")) or "Panama",
            dwt=float(args.get("dwt", 50000.0)),
            grt=float(args.get("grt", 40000.0)),
            loa_meters=float(args.get("loa", 250.0)),
            draft_meters=float(args.get("draft", 12.0)),
            port_code=_clean_str(args.get("port_code")) or "VNVUT",
            terminal_name=_clean_str(args.get("terminal")) or "Cái Mép Terminal",
            eta=_clean_str(args.get("eta")) or "2026-10-01 08:00",
            etd=_clean_str(args.get("etd")) or "2026-10-02 20:00",
            call_sign=_clean_str(args.get("call_sign")) or "3XYZ",
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Maritime vessel error: {exc}"}, indent=2)


def handle_maritime_container(args: dict[str, Any]) -> str:
    """Tool handler for mekong_maritime_container."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.maritime_engine import MaritimeEngine

        engine = MaritimeEngine()
        res = engine.register_container(
            container_no=_clean_str(args.get("container_no")) or "MSCU1234567",
            container_type=_clean_str(args.get("container_type")) or "40HC",
            gross_weight_kg=float(args.get("gross_weight", 25000.0)),
            seal_number=_clean_str(args.get("seal")) or "VN-SEAL-001",
            booking_or_bl=_clean_str(args.get("booking_or_bl")) or "BL-DEFAULT",
            yard_slot=_clean_str(args.get("slot")) or "YARD-B01-R03-T2",
            tare_weight_kg=float(args.get("tare", 2300.0)),
            is_reefer=bool(args.get("reefer", False)),
            is_dangerous=bool(args.get("dg", False)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Maritime container error: {exc}"}, indent=2)


def handle_maritime_tariff(args: dict[str, Any]) -> str:
    """Tool handler for mekong_maritime_tariff."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.maritime_engine import MaritimeEngine

        engine = MaritimeEngine()
        res = engine.calculate_port_tariffs(
            vessel_call_id=_clean_str(args.get("vessel_call")) or "CALL-001",
            port_group=_clean_str(args.get("group")) or "GROUP_4",
            grt=float(args.get("grt", 40000.0)),
            berth_hours=float(args.get("berth_hours", 24.0)),
            pilotage_distance_nm=float(args.get("distance", 18.0)),
            full_20ft_count=int(args.get("f20", 0)),
            full_40ft_count=int(args.get("f40", 0)),
            empty_20ft_count=int(args.get("e20", 0)),
            empty_40ft_count=int(args.get("e40", 0)),
            reefer_power_hours=float(args.get("reefer_hrs", 0.0)),
            reefer_count=int(args.get("reefer_cnt", 0)),
            terminal_name=_clean_str(args.get("terminal")) or "Tân Cảng Cát Lái",
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Maritime tariff error: {exc}"}, indent=2)


def handle_maritime_manifest(args: dict[str, Any]) -> str:
    """Tool handler for mekong_maritime_manifest."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.maritime_engine import MaritimeEngine

        engine = MaritimeEngine()
        res = engine.declare_customs_manifest(
            vessel_call_id=_clean_str(args.get("vessel_call")) or "CALL-001",
            bill_of_lading=_clean_str(args.get("bl")) or "BL-001",
            shipper_name=_clean_str(args.get("shipper")) or "Shipper Corp",
            consignee_name=_clean_str(args.get("consignee")) or "Consignee Inc",
            cargo_description=_clean_str(args.get("cargo")) or "General Cargo",
            container_count=int(args.get("containers", 1)),
            total_gross_kg=float(args.get("gross_kg", 20000.0)),
            declaration_no=_clean_str(args.get("decl_no")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Maritime manifest error: {exc}"}, indent=2)


def handle_maritime_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_maritime_list."""
    if not isinstance(args, dict):
        args = {}
    try:
        from src.core.maritime_engine import MaritimeEngine

        engine = MaritimeEngine()
        item_type = _clean_str(args.get("item_type")) or "vessels"
        if item_type in ("containers", "container"):
            res = engine.list_containers(
                yard=_clean_str(args.get("yard")) or "ALL",
                limit=int(args.get("limit", 50)),
            )
        else:
            res = engine.list_vessel_calls(limit=int(args.get("limit", 50)))
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Maritime list error: {exc}"}, indent=2)


def handle_maritime_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_maritime_status."""
    try:
        from src.core.maritime_engine import MaritimeEngine

        engine = MaritimeEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Maritime status error: {exc}"}, indent=2)


def handle_energy_solar(args: dict[str, Any]) -> str:
    """Tool handler for mekong_energy_solar."""
    try:
        from src.core.energy_engine import EnergyEngine

        engine = EnergyEngine()
        res = engine.evaluate_rooftop_solar(
            project_id=str(args.get("project_id", "")),
            capacity_kwp=float(args.get("capacity_kwp", 0.0)),
            location=str(args.get("location", "Binh Thuan")),
            self_consumption_pct=float(args.get("self_consumption_pct", 80.0)),
            grid_connection=str(args.get("grid_connection", "connected")),
            battery_storage_kwh=float(args.get("battery_storage_kwh", 0.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Energy solar error: {exc}"}, indent=2)


def handle_energy_dppa(args: dict[str, Any]) -> str:
    """Tool handler for mekong_energy_dppa."""
    try:
        from src.core.energy_engine import EnergyEngine

        engine = EnergyEngine()
        res = engine.evaluate_dppa_contract(
            contract_id=str(args.get("contract_id", "")),
            buyer_id=str(args.get("buyer_id", "")),
            seller_id=str(args.get("seller_id", "")),
            mechanism=str(args.get("mechanism", "direct")),
            contract_kwh_month=float(args.get("contract_kwh_month", 500000.0)),
            strike_price_vnd_kwh=float(args.get("strike_price_vnd_kwh", 1800.0)),
            spot_price_vnd_kwh=float(args.get("spot_price_vnd_kwh", 1650.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Energy DPPA error: {exc}"}, indent=2)


def handle_energy_ev(args: dict[str, Any]) -> str:
    """Tool handler for mekong_energy_ev."""
    try:
        from src.core.energy_engine import EnergyEngine

        engine = EnergyEngine()
        res = engine.simulate_ev_charging_session(
            session_id=str(args.get("session_id", "")),
            station_id=str(args.get("station_id", "")),
            charger_type=str(args.get("charger_type", "DC_120kW")),
            energy_kwh=float(args.get("energy_kwh", 45.0)),
            tou_period=str(args.get("tou_period", "normal")),
            ev_model=str(args.get("ev_model", "VF8")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Energy EV error: {exc}"}, indent=2)


def handle_energy_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_energy_list."""
    try:
        from src.core.energy_engine import EnergyEngine

        engine = EnergyEngine()
        item_type = str(args.get("item_type", "solar")).lower()
        limit = int(args.get("limit", 50))
        if item_type in ("dppa", "contracts"):
            res = engine.list_dppa_contracts(limit=limit)
        elif item_type in ("ev", "sessions", "charging"):
            res = engine.list_ev_sessions(limit=limit)
        else:
            res = engine.list_solar_projects(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Energy list error: {exc}"}, indent=2)


def handle_energy_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_energy_status."""
    try:
        from src.core.energy_engine import EnergyEngine

        engine = EnergyEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Energy status error: {exc}"}, indent=2)


def handle_privacy_audit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_audit."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        res = engine.audit_enterprise_compliance(
            enterprise_name=str(args.get("enterprise_name", "")),
            controller_type=str(args.get("controller_type", "CONTROLLER_AND_PROCESSOR")),
            has_sensitive_data=bool(args.get("has_sensitive_data", False)),
            has_dpo=bool(args.get("has_dpo", False)),
            has_cross_border=bool(args.get("has_cross_border", False)),
            has_dpia_dossier=bool(args.get("has_dpia_dossier", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy audit error: {exc}"}, indent=2)


def handle_privacy_dpia(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_dpia."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        raw_cats = args.get("data_categories", [])
        if isinstance(raw_cats, str):
            cats = [c.strip().upper() for c in raw_cats.split(",") if c.strip()]
        else:
            cats = [str(c).strip().upper() for c in raw_cats]

        res = engine.create_dpia_assessment(
            activity_name=str(args.get("activity_name", "")),
            processing_purpose=str(args.get("processing_purpose", "")),
            data_categories=cats,
            legal_basis=str(args.get("legal_basis", "CONSENT")),
            security_measures=str(args.get("security_measures", "AES-256 Encryption, RBAC, TLS 1.3")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy DPIA error: {exc}"}, indent=2)


def handle_privacy_transfer(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_transfer."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        raw_types = args.get("data_types", [])
        if isinstance(raw_types, str):
            types_list = [t.strip().upper() for t in raw_types.split(",") if t.strip()]
        else:
            types_list = [str(t).strip().upper() for t in raw_types]

        res = engine.evaluate_cross_border_transfer(
            transfer_name=str(args.get("transfer_name", "")),
            recipient_entity=str(args.get("recipient_entity", "")),
            destination_country=str(args.get("destination_country", "")),
            data_types=types_list,
            record_count=int(args.get("record_count", 1000)),
            has_scc=bool(args.get("has_scc", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy transfer error: {exc}"}, indent=2)


def handle_privacy_breach(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_breach."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        res = engine.report_data_breach(
            incident_name=str(args.get("incident_name", "")),
            severity=str(args.get("severity", "HIGH")),
            affected_count=int(args.get("affected_count", 0)),
            breach_type=str(args.get("breach_type", "UNAUTHORIZED_ACCESS")),
            hours_elapsed=float(args.get("hours_elapsed", 2.0)),
            mitigation_plan=str(args.get("mitigation_plan", "Revoked compromised tokens, enabled network isolation, activated incident team")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy breach error: {exc}"}, indent=2)


def handle_privacy_dsar(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_dsar."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        res = engine.handle_dsar_request(
            request_type=str(args.get("request_type", "RIGHT_TO_ACCESS")),
            subject_id=str(args.get("subject_id", "")),
            details=str(args.get("details", "Request under Article 9 PDPD")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy DSAR error: {exc}"}, indent=2)


def handle_privacy_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_list."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        item_type = str(args.get("item_type", "dpia")).lower().strip()
        limit = int(args.get("limit", 50))
        if item_type in ("transfer", "transfers", "cross_border"):
            res = engine.list_cross_border_transfers(limit=limit)
        elif item_type in ("breach", "breaches", "incident", "incidents"):
            res = engine.list_breach_incidents(limit=limit)
        elif item_type in ("dsar", "requests"):
            res = engine.list_dsar_requests(limit=limit)
        else:
            res = engine.list_dpia_assessments(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy list error: {exc}"}, indent=2)


def handle_privacy_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_privacy_status."""
    try:
        from src.core.privacy_engine import PrivacyEngine

        engine = PrivacyEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Privacy status error: {exc}"}, indent=2)


def handle_aviation_flight(args: dict[str, Any]) -> str:
    """Tool handler for mekong_aviation_flight."""
    try:
        from src.core.aviation_engine import AviationEngine

        engine = AviationEngine()
        res = engine.register_flight_schedule(
            flight_no=args.get("flight_no", "VN216"),
            aircraft_type=args.get("aircraft_type", "A321"),
            origin_airport=args.get("origin_airport", "SGN"),
            dest_airport=args.get("dest_airport", "HAN"),
            mtow_tons=float(args.get("mtow_tons", 90.0)),
            parking_hours=float(args.get("parking_hours", 2.0)),
            is_international=bool(args.get("is_international", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Aviation flight error: {exc}"}, indent=2)


def handle_aviation_cargo(args: dict[str, Any]) -> str:
    """Tool handler for mekong_aviation_cargo."""
    try:
        from src.core.aviation_engine import AviationEngine

        engine = AviationEngine()
        res = engine.calculate_air_cargo_chargeable_weight(
            mawb_no=args.get("mawb_no", "738-12345675"),
            origin_airport=args.get("origin_airport", "SGN"),
            dest_airport=args.get("dest_airport", "HAN"),
            piece_count=int(args.get("piece_count", 10)),
            gross_weight_kg=float(args.get("gross_weight_kg", 500.0)),
            volume_cbm=float(args.get("volume_cbm", 4.5)),
            cargo_type=args.get("cargo_type", "GENERAL"),
            temperature_regime=args.get("temperature_regime", "AMBIENT"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Aviation cargo error: {exc}"}, indent=2)


def handle_aviation_tariff(args: dict[str, Any]) -> str:
    """Tool handler for mekong_aviation_tariff."""
    try:
        from src.core.aviation_engine import AviationEngine

        engine = AviationEngine()
        res = engine.calculate_airport_tariffs(
            flight_no=args.get("flight_no", "VN216"),
            airport_code=args.get("airport_code", "HAN"),
            mtow_tons=float(args.get("mtow_tons", 90.0)),
            parking_hours=float(args.get("parking_hours", 2.0)),
            cargo_tons=float(args.get("cargo_tons", 10.0)),
            is_international=bool(args.get("is_international", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Aviation tariff error: {exc}"}, indent=2)


def handle_aviation_dg(args: dict[str, Any]) -> str:
    """Tool handler for mekong_aviation_dg."""
    try:
        from src.core.aviation_engine import AviationEngine

        engine = AviationEngine()
        res = engine.evaluate_dangerous_goods_declaration(
            un_number=args.get("un_number", "UN3480"),
            proper_shipping_name=args.get("proper_shipping_name", "Lithium Ion Batteries"),
            hazard_class=args.get("hazard_class", "CLASS_9"),
            packing_group=args.get("packing_group", "II"),
            quantity_kg=float(args.get("quantity_kg", 10.0)),
            aircraft_type=args.get("aircraft_type", "PAX_AND_CARGO"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Aviation DG error: {exc}"}, indent=2)


def handle_aviation_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_aviation_list."""
    try:
        from src.core.aviation_engine import AviationEngine

        engine = AviationEngine()
        item_type = str(args.get("item_type", "flights")).lower().strip()
        limit = int(args.get("limit", 50))
        if item_type in ("cargo", "shipment", "shipments", "awb"):
            res = engine.list_air_cargo_shipments(limit=limit)
        elif item_type in ("dg", "dangerous_goods", "hazmat", "declarations"):
            res = engine.list_dangerous_goods(limit=limit)
        else:
            res = engine.list_flight_schedules(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Aviation list error: {exc}"}, indent=2)


def handle_aviation_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_aviation_status."""
    try:
        from src.core.aviation_engine import AviationEngine

        engine = AviationEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Aviation status error: {exc}"}, indent=2)


def handle_ecom_fct(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ecom_fct."""
    try:
        from src.core.ecommerce_engine import EcommerceEngine

        engine = EcommerceEngine()
        res = engine.calculate_foreign_contractor_tax(
            foreign_supplier_name=args.get("foreign_supplier_name", "Google Asia Pacific"),
            supplier_etax_code=args.get("supplier_etax_code", "0109998877"),
            service_category=args.get("service_category", "ONLINE_ADVERTISING"),
            revenue_usd=float(args.get("revenue_usd", 0.0)),
            revenue_vnd=float(args.get("revenue_vnd", 0.0)),
            quarter=args.get("quarter", "Q1-2026"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"E-Commerce FCT error: {exc}"}, indent=2)


def handle_ecom_audit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ecom_audit."""
    try:
        from src.core.ecommerce_engine import EcommerceEngine

        engine = EcommerceEngine()
        res = engine.audit_platform_compliance(
            platform_name=args.get("platform_name", "Shopee Vietnam"),
            domain_url=args.get("domain_url", "https://shopee.vn"),
            platform_type=args.get("platform_type", "MARKETPLACE"),
            enterprise_tax_id=args.get("enterprise_tax_id", "0106773786"),
            has_operating_regulations=bool(args.get("has_operating_regulations", True)),
            has_dispute_mechanism=bool(args.get("has_dispute_mechanism", True)),
            has_seller_kyc=bool(args.get("has_seller_kyc", True)),
            has_data_retention_3yr=bool(args.get("has_data_retention_3yr", True)),
            has_tax_reporting_system=bool(args.get("has_tax_reporting_system", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"E-Commerce audit error: {exc}"}, indent=2)


def handle_ecom_order(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ecom_order."""
    try:
        from src.core.ecommerce_engine import EcommerceEngine

        engine = EcommerceEngine()
        res = engine.process_marketplace_order_settlement(
            order_code=args.get("order_code", "ORD-2026-9999"),
            platform_id=args.get("platform_id", "SHOPEE_VN"),
            seller_id=args.get("seller_id", "SHOP-123"),
            buyer_id=args.get("buyer_id", "USER-456"),
            gmv_gross_vnd=float(args.get("gmv_gross_vnd", 500000.0)),
            platform_commission_pct=float(args.get("platform_commission_pct", 6.0)),
            payment_fee_pct=float(args.get("payment_fee_pct", 2.5)),
            shop_voucher_vnd=float(args.get("shop_voucher_vnd", 0.0)),
            platform_voucher_vnd=float(args.get("platform_voucher_vnd", 0.0)),
            shipping_fee_vnd=float(args.get("shipping_fee_vnd", 30000.0)),
            vat_rate_pct=int(args.get("vat_rate_pct", 10)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"E-Commerce order settlement error: {exc}"}, indent=2)


def handle_ecom_parcel(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ecom_parcel."""
    try:
        from src.core.ecommerce_engine import EcommerceEngine

        engine = EcommerceEngine()
        res = engine.evaluate_cross_border_parcel(
            tracking_no=args.get("tracking_no", "VN123456789HK"),
            shipper_country=args.get("shipper_country", "China"),
            consignee_name=args.get("consignee_name", "Nguyen Van A"),
            item_description=args.get("item_description", "Wireless Earbuds"),
            customs_value_usd=float(args.get("customs_value_usd", 0.0)),
            customs_value_vnd=float(args.get("customs_value_vnd", 0.0)),
            import_duty_pct=float(args.get("import_duty_pct", 10.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"E-Commerce parcel error: {exc}"}, indent=2)


def handle_ecom_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ecom_list."""
    try:
        from src.core.ecommerce_engine import EcommerceEngine

        engine = EcommerceEngine()
        item_type = str(args.get("item_type", "platforms")).lower().strip()
        limit = int(args.get("limit", 50))
        if item_type in ("fct", "tax", "declarations"):
            res = engine.list_fct_declarations(limit=limit)
        elif item_type in ("order", "orders", "settlements"):
            res = engine.list_marketplace_orders(limit=limit)
        elif item_type in ("parcel", "parcels", "express"):
            res = engine.list_cross_border_parcels(limit=limit)
        else:
            res = engine.list_platform_registrations(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"E-Commerce list error: {exc}"}, indent=2)


def handle_ecom_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_ecom_status."""
    try:
        from src.core.ecommerce_engine import EcommerceEngine

        engine = EcommerceEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"E-Commerce status error: {exc}"}, indent=2)


def handle_telecom_spectrum(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telecom_spectrum."""
    try:
        from src.core.telecom_engine import TelecomEngine

        engine = TelecomEngine()
        res = engine.calculate_spectrum_auction_valuation(
            band_code=args.get("band_code", "B7_2600"),
            license_years=int(args.get("license_years", 15)),
            deposit_pct=float(args.get("deposit_pct", 10.0)),
            custom_reserve_price_vnd=float(args.get("custom_reserve_price_vnd", 0.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telecom spectrum error: {exc}"}, indent=2)


def handle_telecom_ott(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telecom_ott."""
    try:
        from src.core.telecom_engine import TelecomEngine

        engine = TelecomEngine()
        res = engine.audit_ott_service_compliance(
            service_name=args.get("service_name", "OTT Service"),
            provider_name=args.get("provider_name", "Provider"),
            service_category=args.get("service_category", "OTT_MESSAGING_VOICE"),
            registered_users=int(args.get("registered_users", 1000000)),
            has_kyc_verification=bool(args.get("has_kyc_verification", True)),
            has_encryption_e2ee=bool(args.get("has_encryption_e2ee", True)),
            has_local_data_storage=bool(args.get("has_local_data_storage", True)),
            has_vnta_notification=bool(args.get("has_vnta_notification", True)),
            has_consumer_dispute_system=bool(args.get("has_consumer_dispute_system", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telecom OTT error: {exc}"}, indent=2)


def handle_telecom_bts(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telecom_bts."""
    try:
        from src.core.telecom_engine import TelecomEngine

        engine = TelecomEngine()
        res = engine.evaluate_bts_emf_safety(
            station_id=args.get("station_id", "BTS-01"),
            location=args.get("location", "Vietnam"),
            antenna_height_m=float(args.get("antenna_height_m", 30.0)),
            transmit_power_watts=float(args.get("transmit_power_watts", 80.0)),
            frequency_mhz=float(args.get("frequency_mhz", 2600.0)),
            antenna_gain_dbi=float(args.get("antenna_gain_dbi", 18.0)),
            distance_residential_m=float(args.get("distance_residential_m", 25.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telecom BTS error: {exc}"}, indent=2)


def handle_telecom_number(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telecom_number."""
    try:
        from src.core.telecom_engine import TelecomEngine

        engine = TelecomEngine()
        res = engine.allocate_numbering_resource(
            number_prefix=args.get("number_prefix", "1900"),
            assigned_operator=args.get("assigned_operator", "Operator"),
            block_size=int(args.get("block_size", 10000)),
            service_purpose=args.get("service_purpose", "MOBILE_SUBSCRIBER"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telecom number error: {exc}"}, indent=2)


def handle_telecom_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telecom_list."""
    try:
        from src.core.telecom_engine import TelecomEngine

        engine = TelecomEngine()
        item_type = args.get("item_type", "spectrum")
        limit = int(args.get("limit", 50))
        clean_type = item_type.lower().strip()
        if clean_type in ("ott", "audits", "services"):
            res = engine.list_ott_audits(limit=limit)
        elif clean_type in ("bts", "stations", "emf"):
            res = engine.list_bts_evaluations(limit=limit)
        elif clean_type in ("number", "numbers", "resources"):
            res = engine.list_numbering_resources(limit=limit)
        else:
            res = engine.list_spectrum_auctions(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telecom list error: {exc}"}, indent=2)


def handle_telecom_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_telecom_status."""
    try:
        from src.core.telecom_engine import TelecomEngine

        engine = TelecomEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Telecom status error: {exc}"}, indent=2)


def handle_pharma_drug(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pharma_drug."""
    try:
        from src.core.pharma_engine import PharmaEngine

        engine = PharmaEngine()
        res = engine.register_drug_marketing_authorization(
            visa_number=args.get("visa_number", "VN-00000-00"),
            drug_name=args.get("drug_name", "Drug"),
            active_ingredient=args.get("active_ingredient", "API"),
            strength=args.get("strength", "500mg"),
            dosage_form=args.get("dosage_form", "Tablet"),
            classification=args.get("classification", "RX_PRESCRIPTION"),
            manufacturer_name=args.get("manufacturer_name", "DHG Pharma"),
            country_of_origin=args.get("country_of_origin", "Vietnam"),
            tenure_years=int(args.get("tenure_years", 5)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pharma drug error: {exc}"}, indent=2)


def handle_pharma_gsp(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pharma_gsp."""
    try:
        from src.core.pharma_engine import PharmaEngine

        engine = PharmaEngine()
        res = engine.audit_gsp_storage_condition(
            warehouse_id=args.get("warehouse_id", "WH-01"),
            warehouse_name=args.get("warehouse_name", "Warehouse"),
            storage_condition=args.get("storage_condition", "COLD_CHAIN"),
            recorded_temp_c=float(args.get("recorded_temp_c", 4.5)),
            recorded_humidity_pct=float(args.get("recorded_humidity_pct", 55.0)),
            sensor_id=args.get("sensor_id", "SENSOR-01"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pharma GSP error: {exc}"}, indent=2)


def handle_pharma_batch(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pharma_batch."""
    try:
        from src.core.pharma_engine import PharmaEngine

        engine = PharmaEngine()
        res = engine.track_batch_traceability(
            batch_number=args.get("batch_number", "BATCH-01"),
            visa_number=args.get("visa_number", "VN-00000-00"),
            drug_name=args.get("drug_name", "Drug"),
            gtin_14=args.get("gtin_14", "08935000000018"),
            serial_number=args.get("serial_number", "SN1234567890"),
            manufacturing_date=args.get("manufacturing_date", "2026-01-15"),
            expiry_date=args.get("expiry_date", "2028-01-15"),
            quantity_units=int(args.get("quantity_units", 10000)),
            recall_action=args.get("recall_action", "NONE"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pharma batch error: {exc}"}, indent=2)


def handle_pharma_price(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pharma_price."""
    try:
        from src.core.pharma_engine import PharmaEngine

        engine = PharmaEngine()
        res = engine.declare_drug_pricing(
            visa_number=args.get("visa_number", "VN-00000-00"),
            drug_name=args.get("drug_name", "Drug"),
            wholesale_price_vnd=float(args.get("wholesale_price_vnd", 0.0)),
            hospital_retail_price_vnd=float(args.get("hospital_retail_price_vnd", 0.0)),
            declared_by=args.get("declared_by", "DHG Pharma"),
            classification=args.get("classification", "RX_PRESCRIPTION"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pharma price error: {exc}"}, indent=2)


def handle_pharma_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pharma_list."""
    try:
        from src.core.pharma_engine import PharmaEngine

        engine = PharmaEngine()
        item_type = args.get("item_type", "drugs")
        limit = int(args.get("limit", 50))
        clean_type = item_type.lower().strip()
        if clean_type in ("gsp", "warehouse", "storage", "coldchain"):
            res = engine.list_gsp_logs(limit=limit)
        elif clean_type in ("batch", "batches", "traceability", "gs1"):
            res = engine.list_batch_traceability(limit=limit)
        elif clean_type in ("price", "prices", "margins"):
            res = engine.list_price_declarations(limit=limit)
        else:
            res = engine.list_drug_registrations(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pharma list error: {exc}"}, indent=2)


def handle_pharma_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_pharma_status."""
    try:
        from src.core.pharma_engine import PharmaEngine

        engine = PharmaEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Pharma status error: {exc}"}, indent=2)


def handle_petrol_price(args: dict[str, Any]) -> str:
    """Tool handler for mekong_petrol_price."""
    try:
        from src.core.petrol_engine import PetrolEngine

        engine = PetrolEngine()
        res = engine.calculate_fuel_base_and_retail_price(
            product_code=args.get("product_code", "RON95_III"),
            mops_platts_usd_per_barrel=float(args.get("mops_platts_usd_per_barrel", 92.50)),
            import_duty_pct=float(args.get("import_duty_pct", 10.0)),
            bog_fund_deduction_vnd=float(args.get("bog_fund_deduction_vnd", 0.0)),
            bog_fund_expenditure_vnd=float(args.get("bog_fund_expenditure_vnd", 0.0)),
            cycle_date=args.get("cycle_date"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Petrol price error: {exc}"}, indent=2)


def handle_petrol_reserve(args: dict[str, Any]) -> str:
    """Tool handler for mekong_petrol_reserve."""
    try:
        from src.core.petrol_engine import PetrolEngine

        engine = PetrolEngine()
        res = engine.audit_national_fuel_reserves(
            enterprise_name=str(args["enterprise_name"]),
            enterprise_type=str(args.get("enterprise_type", "KEY_IMPORTER")),
            storage_capacity_m3=float(args.get("storage_capacity_m3", 100000.0)),
            current_stock_m3=float(args.get("current_stock_m3", 75000.0)),
            daily_consumption_m3=float(args.get("daily_consumption_m3", 3000.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Petrol reserve error: {exc}"}, indent=2)


def handle_petrol_quality(args: dict[str, Any]) -> str:
    """Tool handler for mekong_petrol_quality."""
    try:
        from src.core.petrol_engine import PetrolEngine

        engine = PetrolEngine()
        res = engine.inspect_fuel_quality(
            gas_station_id=str(args["gas_station_id"]),
            gas_station_name=str(args["gas_station_name"]),
            product_code=str(args.get("product_code", "RON95_III")),
            sulfur_content_ppm=float(args.get("sulfur_content_ppm", 35.0)),
            lead_content_g_l=float(args.get("lead_content_g_l", 0.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Petrol quality error: {exc}"}, indent=2)


def handle_petrol_pump(args: dict[str, Any]) -> str:
    """Tool handler for mekong_petrol_pump."""
    try:
        from src.core.petrol_engine import PetrolEngine

        engine = PetrolEngine()
        res = engine.report_pump_einvoice_telemetry(
            station_id=str(args["station_id"]),
            pump_count=int(args.get("pump_count", 8)),
            daily_transactions=int(args.get("daily_transactions", 1500)),
            daily_volume_liters=float(args.get("daily_volume_liters", 12000.0)),
            daily_revenue_vnd=float(args.get("daily_revenue_vnd", 285000000.0)),
            e_invoices_issued=int(args.get("e_invoices_issued", 1500)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Petrol pump error: {exc}"}, indent=2)


def handle_petrol_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_petrol_list."""
    try:
        from src.core.petrol_engine import PetrolEngine

        engine = PetrolEngine()
        item_type = str(args.get("item_type", "prices")).lower().strip()
        limit = int(args.get("limit", 50))
        if item_type in ("reserve", "reserves", "stock", "storage"):
            res = engine.list_fuel_reserves(limit=limit)
        elif item_type in ("quality", "inspections", "lab", "euro"):
            res = engine.list_quality_inspections(limit=limit)
        elif item_type in ("pump", "telemetry", "invoices", "dispenser"):
            res = engine.list_pump_telemetry(limit=limit)
        else:
            res = engine.list_price_adjustments(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Petrol list error: {exc}"}, indent=2)


def handle_petrol_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_petrol_status."""
    try:
        from src.core.petrol_engine import PetrolEngine

        engine = PetrolEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Petrol status error: {exc}"}, indent=2)


def handle_fishery_vessel(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fishery_vessel."""
    try:
        from src.core.fishery_engine import FisheryEngine

        engine = FisheryEngine()
        res = engine.register_fishing_vessel(
            vessel_plate=str(args["vessel_plate"]),
            owner_name=str(args["owner_name"]),
            home_port=str(args.get("home_port", "PORT_TAC_CAU")),
            length_meters=float(args.get("length_meters", 18.5)),
            engine_power_hp=float(args.get("engine_power_hp", 450.0)),
            vms_device_id=args.get("vms_device_id"),
            assigned_zone=str(args.get("assigned_zone", "SOUTHWEST_GULF")),
            license_valid_years=int(args.get("license_valid_years", 5)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Fishery vessel error: {exc}"}, indent=2)


def handle_fishery_vms(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fishery_vms."""
    try:
        from src.core.fishery_engine import FisheryEngine

        engine = FisheryEngine()
        res = engine.track_vms_telemetry(
            vessel_plate=str(args["vessel_plate"]),
            latitude=float(args["latitude"]),
            longitude=float(args["longitude"]),
            speed_knots=float(args.get("speed_knots", 8.5)),
            heading_degrees=float(args.get("heading_degrees", 135.0)),
            is_signal_active=bool(args.get("is_signal_active", True)),
            disconnection_hours=float(args.get("disconnection_hours", 0.0)),
            assigned_zone=str(args.get("assigned_zone", "SOUTHWEST_GULF")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Fishery VMS error: {exc}"}, indent=2)


def handle_fishery_cert(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fishery_cert."""
    try:
        from src.core.fishery_engine import FisheryEngine

        engine = FisheryEngine()
        res = engine.issue_catch_certificate(
            vessel_plate=str(args["vessel_plate"]),
            species_code=str(args.get("species_code", "YELLOWFIN_TUNA")),
            catch_volume_kg=float(args.get("catch_volume_kg", 12500.0)),
            landing_port=str(args.get("landing_port", "PORT_QUY_NHON")),
            destination_market=str(args.get("destination_market", "EU_MARKET")),
            certificate_type=str(args.get("certificate_type", "CATCH_CERTIFICATE_CC")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Fishery cert error: {exc}"}, indent=2)


def handle_fishery_quality(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fishery_quality."""
    try:
        from src.core.fishery_engine import FisheryEngine

        engine = FisheryEngine()
        res = engine.audit_seafood_quality(
            facility_eu_code=str(args["facility_eu_code"]),
            facility_name=str(args["facility_name"]),
            lot_number=str(args["lot_number"]),
            species_code=str(args.get("species_code", "WHITELEG_SHRIMP")),
            haccp_score=float(args.get("haccp_score", 95.0)),
            chloramphenicol_ppb=float(args.get("chloramphenicol_ppb", 0.0)),
            nitrofurans_ppb=float(args.get("nitrofurans_ppb", 0.0)),
            heavy_metal_pass=bool(args.get("heavy_metal_pass", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Fishery quality error: {exc}"}, indent=2)


def handle_fishery_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fishery_list."""
    try:
        from src.core.fishery_engine import FisheryEngine

        engine = FisheryEngine()
        item_type = str(args.get("item_type", "vessels")).lower().strip()
        limit = int(args.get("limit", 50))
        if item_type in ("vms", "telemetry", "tracking", "gps"):
            res = engine.list_vms_telemetry(limit=limit)
        elif item_type in ("cert", "certs", "ecdt", "catch", "certificates"):
            res = engine.list_catch_certificates(limit=limit)
        elif item_type in ("quality", "audits", "haccp", "lab"):
            res = engine.list_seafood_quality_audits(limit=limit)
        else:
            res = engine.list_fishing_vessels(limit=limit)
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Fishery list error: {exc}"}, indent=2)


def handle_fishery_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_fishery_status."""
    try:
        from src.core.fishery_engine import FisheryEngine

        engine = FisheryEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Fishery status error: {exc}"}, indent=2)


def handle_construction_project(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_project."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        res = engine.register_construction_project(
            project_name=str(args.get("project_name", "")),
            project_type=str(args.get("project_type", "CIVIL_COMMERCIAL")),
            total_investment_vnd=float(args.get("total_investment_vnd", 250000000000.0)),
            gross_floor_area_m2=float(args.get("gross_floor_area_m2", 35000.0)),
            height_meters=float(args.get("height_meters", 85.0)),
            floors_count=int(args.get("floors_count", 26)),
            location_province=str(args.get("location_province", "TP. Hồ Chí Minh")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction project error: {exc}"}, indent=2)


def handle_construction_permit(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_permit."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        res = engine.evaluate_building_permit(
            project_id=str(args.get("project_id", "")),
            is_secret_defense_project=bool(args.get("is_secret_defense_project", False)),
            is_rural_detached_house=bool(args.get("is_rural_detached_house", False)),
            is_industrial_park_approved_1_500=bool(args.get("is_industrial_park_approved_1_500", False)),
            is_fire_safety_approved=bool(args.get("is_fire_safety_approved", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction permit error: {exc}"}, indent=2)


def handle_construction_fidic(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_fidic."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        adv = float(args["custom_advance_pct"]) if args.get("custom_advance_pct") is not None else None
        res = engine.structure_fidic_contract(
            project_id=str(args.get("project_id", "")),
            contract_name=str(args.get("contract_name", "")),
            fidic_type=str(args.get("fidic_type", "FIDIC_YELLOW_BOOK")),
            employer_name=str(args.get("employer_name", "Vinhomes Joint Stock Company")),
            contractor_name=str(args.get("contractor_name", "Coteccons Construction Corporation")),
            contract_value_vnd=float(args.get("contract_value_vnd", 180000000000.0)),
            custom_advance_pct=adv,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction FIDIC error: {exc}"}, indent=2)


def handle_construction_pccc(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_pccc."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        res = engine.audit_fire_safety_qcvn06(
            project_id=str(args.get("project_id", "")),
            fire_tier=str(args.get("fire_tier", "TIER_I")),
            tested_column_rei_min=int(args.get("tested_column_rei_min", 150)),
            tested_floor_rei_min=int(args.get("tested_floor_rei_min", 90)),
            measured_evacuation_dist_m=float(args.get("measured_evacuation_dist_m", 32.5)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction PCCC error: {exc}"}, indent=2)


def handle_construction_accept(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_accept."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        res = engine.accept_construction_stage(
            project_id=str(args.get("project_id", "")),
            acceptance_stage=str(args.get("acceptance_stage", "FINAL_COMMISSIONING")),
            inspector_name=str(args.get("inspector_name", "Tư vấn Giám sát Apave Vietnam")),
            structural_soundness_pct=float(args.get("structural_soundness_pct", 98.5)),
            as_built_compliance=bool(args.get("as_built_compliance", True)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction acceptance error: {exc}"}, indent=2)


def handle_construction_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_list."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        cat = str(args.get("category", "projects")).lower().strip()
        limit = int(args.get("limit", 50))
        if cat in ("permits", "permit"):
            res = engine.list_permits(limit=limit)
        elif cat in ("fidic", "contracts", "contract"):
            res = engine.list_fidic_contracts(limit=limit)
        elif cat in ("pccc", "fire"):
            res = engine.list_fire_safety_audits(limit=limit)
        elif cat in ("acceptances", "accept", "quality"):
            res = engine.list_acceptances(limit=limit)
        else:
            res = engine.list_projects(limit=limit)
        return json.dumps(res.data, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction list error: {exc}"}, indent=2)


def handle_construction_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_construction_status."""
    try:
        from src.core.construction_engine import ConstructionEngine

        engine = ConstructionEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Construction status error: {exc}"}, indent=2)


def handle_mining_license(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_license."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        res = engine.register_mining_license(
            mine_name=str(args.get("mine_name", "")),
            mineral_type=str(args.get("mineral_type", "RARE_EARTH")),
            enterprise_name=str(args.get("enterprise_name", "Vietnam Rare Earth Joint Stock Company")),
            approved_reserve=float(args.get("approved_reserve", 2500000.0)),
            annual_capacity=float(args.get("annual_capacity", 120000.0)),
            mining_method=str(args.get("mining_method", "OPEN_PIT")),
            mine_area_hectares=float(args.get("mine_area_hectares", 85.5)),
            location_province=str(args.get("location_province", "Lai Châu")),
            duration_years=int(args.get("duration_years", 25)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining license error: {exc}"}, indent=2)


def handle_mining_rights_fee(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_rights_fee."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        res = engine.calculate_mineral_rights_fee(
            license_id=str(args.get("license_id", "")),
            reserve_volume=float(args["reserve_volume"]) if args.get("reserve_volume") is not None else None,
            custom_unit_price_vnd=float(args["custom_unit_price_vnd"]) if args.get("custom_unit_price_vnd") is not None else None,
            mining_method=str(args.get("mining_method", "OPEN_PIT")),
            mineral_type=str(args.get("mineral_type", "RARE_EARTH")),
            payment_years=int(args.get("payment_years", 10)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining rights fee error: {exc}"}, indent=2)


def handle_mining_royalty(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_royalty."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        res = engine.calculate_resource_royalty_tax(
            license_id=str(args.get("license_id", "")),
            tax_period=str(args.get("tax_period", "2026-Q1")),
            actual_mined_volume=float(args.get("actual_mined_volume", 30000.0)),
            mineral_type=str(args.get("mineral_type", "RARE_EARTH")),
            taxable_unit_price_vnd=float(args["taxable_unit_price_vnd"]) if args.get("taxable_unit_price_vnd") is not None else None,
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining royalty tax error: {exc}"}, indent=2)


def handle_mining_rehab(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_rehab."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        res = engine.audit_environmental_rehabilitation(
            license_id=str(args.get("license_id", "")),
            total_rehab_estimate_vnd=float(args.get("total_rehab_estimate_vnd", 12000000000.0)),
            initial_deposit_pct=float(args.get("initial_deposit_pct", 25.0)),
            replanted_trees_count=int(args.get("replanted_trees_count", 15000)),
            wastewater_ph=float(args.get("wastewater_ph", 7.2)),
            wastewater_tss_mg_l=float(args.get("wastewater_tss_mg_l", 38.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining rehabilitation error: {exc}"}, indent=2)


def handle_mining_sand(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_sand."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        res = engine.inspect_river_sand_gravel(
            license_id=str(args.get("license_id", "")),
            vessel_plate=str(args.get("vessel_plate", "")),
            operation_time_hh_mm=str(args.get("operation_time_hh_mm", "10:30")),
            is_gps_installed=bool(args.get("is_gps_installed", True)),
            is_dock_camera_installed=bool(args.get("is_dock_camera_installed", True)),
            measured_cargo_m3=float(args.get("measured_cargo_m3", 240.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining sand inspection error: {exc}"}, indent=2)


def handle_mining_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_list."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        cat = str(args.get("category", "licenses")).lower().strip()
        limit = int(args.get("limit", 50))
        if cat in ("fees", "fee", "rights"):
            res = engine.list_mineral_rights_fees(limit=limit)
        elif cat in ("taxes", "tax", "royalty"):
            res = engine.list_resource_royalty_taxes(limit=limit)
        elif cat in ("rehab", "rehabilitations", "environment"):
            res = engine.list_environmental_rehabilitations(limit=limit)
        elif cat in ("sand", "gravel", "inspections"):
            res = engine.list_river_sand_inspections(limit=limit)
        else:
            res = engine.list_mining_licenses(limit=limit)
        return json.dumps(res.data, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining list error: {exc}"}, indent=2)


def handle_mining_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_mining_status."""
    try:
        from src.core.mining_engine import MiningEngine

        engine = MiningEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Mining status error: {exc}"}, indent=2)


def handle_forestry_plot(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_plot."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        res = engine.register_forest_plot(
            plot_name=str(args.get("plot_name", "Khu Rừng Thử Nghiệm")),
            forest_type=str(args.get("forest_type", "PRODUCTION_PLANTATION")),
            province=str(args.get("province", "Quảng Nam")),
            area_hectares=float(args.get("area_hectares", 150.0)),
            canopy_cover_pct=float(args.get("canopy_cover_pct", 65.0)),
            trees_per_hectare=float(args.get("trees_per_hectare", 1600.0)),
            main_species=str(args.get("main_species", "Acacia auriculiformis (Keo lá tràm)")),
            is_fsc_certified=bool(args.get("is_fsc_certified", True)),
            fsc_code=args.get("fsc_code", "FSC-C123456"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Forestry plot error: {exc}"}, indent=2)


def handle_forestry_timber(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_timber."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        res = engine.verify_timber_vntlas(
            enterprise_name=str(args.get("enterprise_name", "Công Ty Chế Biến Gỗ")),
            product_type=str(args.get("product_type", "FURNITURE")),
            volume_m3=float(args.get("volume_m3", 120.0)),
            species=str(args.get("species", "Tectona grandis (Gỗ Teak) / Keo tràm")),
            origin_province=str(args.get("origin_province", "Bình Dương")),
            enterprise_tier=str(args.get("enterprise_tier", "TIER_1")),
            flegt_cites_license=args.get("flegt_cites_license", "FLEGT-VN-2026-00892"),
            export_market=str(args.get("export_market", "EU")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Timber VNTLAS error: {exc}"}, indent=2)


def handle_forestry_afforestation(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_afforestation."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        res = engine.calculate_alternative_afforestation(
            project_name=str(args.get("project_name", "Dự Án Hạ Tầng")),
            converted_forest_type=str(args.get("converted_forest_type", "PRODUCTION_NATURAL")),
            converted_area_ha=float(args.get("converted_area_ha", 25.0)),
            payment_rate_vnd_per_ha=float(args.get("payment_rate_vnd_per_ha", 95000000.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Alternative afforestation error: {exc}"}, indent=2)


def handle_forestry_pfes(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_pfes."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        res = engine.calculate_pfes_and_carbon(
            facility_name=str(args.get("facility_name", "Nhà Máy Nước / Thủy Điện")),
            facility_type=str(args.get("facility_type", "HYDROPOWER")),
            production_volume=float(args.get("production_volume", 250000000.0)),
            forest_area_ha=float(args.get("forest_area_ha", 12000.0)),
            carbon_sequestration_rate=float(args.get("carbon_sequestration_rate", 4.2)),
            erpa_price_usd_per_ton=float(args.get("erpa_price_usd_per_ton", 5.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"PFES calculation error: {exc}"}, indent=2)


def handle_forestry_fire(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_fire."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        res = engine.assess_forest_fire_danger(
            plot_id=str(args.get("plot_id", "PLT-001")),
            temperature_c=float(args.get("temperature_c", 37.5)),
            humidity_pct=float(args.get("humidity_pct", 38.0)),
            wind_speed_kmh=float(args.get("wind_speed_kmh", 24.0)),
            consecutive_dry_days=int(args.get("consecutive_dry_days", 14)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Forest fire assessment error: {exc}"}, indent=2)


def handle_forestry_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_list."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        cat = str(args.get("category", "plots")).lower().strip()
        limit = int(args.get("limit", 50))
        if cat in ("plots", "plot"):
            res = engine.list_forest_plots(limit=limit)
        elif cat in ("timber", "consignments"):
            res = engine.list_timber_consignments(limit=limit)
        elif cat in ("afforestation", "afforestations"):
            res = engine.list_afforestation_projects(limit=limit)
        elif cat in ("pfes", "carbon"):
            res = engine.list_pfes_records(limit=limit)
        elif cat in ("fire", "fire_assessments"):
            res = engine.list_fire_danger_assessments(limit=limit)
        else:
            res = engine.list_forest_plots(limit=limit)
        return json.dumps(res.data, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Forestry list error: {exc}"}, indent=2)


def handle_forestry_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_forestry_status."""
    try:
        from src.core.forestry_engine import ForestryEngine

        engine = ForestryEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Forestry status error: {exc}"}, indent=2)


def handle_water_plant(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_plant."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        res = engine.register_water_plant(
            plant_name=args.get("name", args.get("plant_name", "Nhà máy Nước Tân Hiệp")),
            capacity_m3_day=float(args.get("capacity", args.get("capacity_m3_day", 50000.0))),
            water_source=args.get("source", args.get("water_source", "Sông Đồng Nai (Nguồn nước mặt)")),
            province=args.get("province", "Bình Dương"),
            technology=args.get("technology", args.get("tech", "Lắng lamen + Lọc cát + Khử trùng Clo")),
            operator_name=args.get("operator", args.get("operator_name", "BIWASE")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Water plant registration error: {exc}"}, indent=2)


def handle_water_test(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_test."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        res = engine.audit_water_quality_qcvn01(
            plant_id=args.get("plant_id", "PLT-001"),
            sample_location=args.get("location", args.get("sample_location", "Bể chứa nước sạch trạm bơm cấp 2")),
            ph_level=float(args.get("ph", args.get("ph_level", 7.2))),
            turbidity_ntu=float(args.get("turbidity", args.get("turbidity_ntu", 0.85))),
            residual_chlorine_mg_l=float(args.get("chlorine", args.get("residual_chlorine_mg_l", 0.5))),
            coliform_cfu=float(args.get("coliform", args.get("coliform_cfu", 0.0))),
            e_coli_cfu=float(args.get("ecoli", args.get("e_coli_cfu", 0.0))),
            heavy_metal_pass=bool(args.get("metal_pass", args.get("heavy_metal_pass", True))),
            tested_by=args.get("tester", args.get("tested_by", "Trung tâm Kiểm soát Bệnh tật (CDC)")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Water quality audit error: {exc}"}, indent=2)


def handle_water_bill(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_bill."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        res = engine.calculate_water_bill(
            customer_code=args.get("code", args.get("customer_code", "KH-001")),
            customer_name=args.get("name", args.get("customer_name", "Hộ Gia Đình Nguyễn Văn A")),
            consumption_m3=float(args.get("volume", args.get("consumption_m3", 22.5))),
            customer_category=args.get("category", args.get("customer_category", "DOMESTIC")),
            billing_month=args.get("month", args.get("billing_month", None)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Water bill calculation error: {exc}"}, indent=2)


def handle_water_nrw(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_nrw."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        res = engine.audit_nrw_loss(
            plant_id=args.get("plant_id", "PLT-001"),
            produced_volume_m3=float(args.get("produced", args.get("produced_volume_m3", 1500000.0))),
            billed_volume_m3=float(args.get("billed", args.get("billed_volume_m3", 1320000.0))),
            audit_period=args.get("period", args.get("audit_period", "2026-Q1")),
            target_max_pct=float(args.get("target", args.get("target_max_pct", 15.0))),
            notes=args.get("notes", None),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"NRW audit error: {exc}"}, indent=2)


def handle_water_discharge(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_discharge."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        res = engine.inspect_wastewater_discharge(
            facility_name=args.get("facility", args.get("facility_name", "Nhà máy Dệt Nhuộm VSIP")),
            industrial_park=args.get("park", args.get("industrial_park", "KCN VSIP II - Bình Dương")),
            daily_flow_m3=float(args.get("flow", args.get("daily_flow_m3", args.get("daily_flow_m3_day", 1200.0)))),
            standard_column=args.get("column", args.get("standard_column", "COLUMN_A")),
            bod5_mg_l=float(args.get("bod5", args.get("bod5_mg_l", 24.5))),
            cod_mg_l=float(args.get("cod", args.get("cod_mg_l", 62.0))),
            tss_mg_l=float(args.get("tss", args.get("tss_mg_l", 38.0))),
            ammonium_mg_l=float(args.get("nh4", args.get("ammonium_mg_l", 3.5))),
            ph_level=float(args.get("ph", args.get("ph_level", 7.4))),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Wastewater discharge inspection error: {exc}"}, indent=2)


def handle_water_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_list."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        cat = args.get("category", "plants").lower().strip()
        limit = int(args.get("limit", 50))
        if cat in ("plants", "plant"):
            res = engine.list_water_plants(limit=limit)
        elif cat in ("tests", "quality", "test"):
            res = engine.list_water_quality_tests(limit=limit)
        elif cat in ("bills", "bill", "tariffs"):
            res = engine.list_tariff_bills(limit=limit)
        elif cat in ("nrw", "loss", "leakage"):
            res = engine.list_nrw_audits(limit=limit)
        elif cat in ("discharges", "wastewater", "discharge"):
            res = engine.list_wastewater_discharges(limit=limit)
        else:
            res = engine.list_water_plants(limit=limit)
        return json.dumps(res.data, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Water list error: {exc}"}, indent=2)


def handle_water_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_water_status."""
    try:
        from src.core.water_engine import WaterEngine

        engine = WaterEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Water status error: {exc}"}, indent=2)


def handle_medtech_device(args: dict[str, Any]) -> str:
    """Tool handler for mekong_medtech_device."""
    try:
        from src.core.medtech_engine import MedtechEngine

        engine = MedtechEngine()
        res = engine.register_medical_device(
            device_name=args.get("name", args.get("device_name", "Thiết bị Y tế Mẫu")),
            risk_class=args.get("risk_class", args.get("class", "CLASS_B")),
            manufacturer=args.get("maker", args.get("manufacturer", "MedTech Global Instruments Inc.")),
            country_of_origin=args.get("origin", args.get("country_of_origin", "Germany")),
            importer_name=args.get("importer", args.get("importer_name", "Công ty TNHH Thiết Bị Y Tế Sài Gòn")),
            intended_use=args.get("use", args.get("intended_use", "Theo dõi huyết áp và chỉ số sinh tồn điện tử")),
            reference_cfs=args.get("cfs", args.get("reference_cfs", "CE")),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Medical device registration error: {exc}"}, indent=2)


def handle_medtech_price(args: dict[str, Any]) -> str:
    """Tool handler for mekong_medtech_price."""
    try:
        from src.core.medtech_engine import MedtechEngine

        engine = MedtechEngine()
        res = engine.declare_device_price(
            device_id=args.get("device_id", "DEV-001"),
            device_name=args.get("name", args.get("device_name", "Thiết bị Y tế Mẫu")),
            cif_cost_vnd=float(args.get("cif", args.get("cif_cost_vnd", 10000000.0))),
            wholesale_price_vnd=float(args.get("wholesale", args.get("wholesale_price_vnd", 13000000.0))),
            retail_price_vnd=float(args.get("retail", args.get("retail_price_vnd", 15000000.0))),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Device price declaration error: {exc}"}, indent=2)


def handle_medtech_facility(args: dict[str, Any]) -> str:
    """Tool handler for mekong_medtech_facility."""
    try:
        from src.core.medtech_engine import MedtechEngine

        engine = MedtechEngine()
        res = engine.evaluate_facility_license(
            facility_name=args.get("name", args.get("facility_name", "Bệnh viện Đa khoa Quốc tế")),
            facility_type=args.get("fac_type", args.get("type", args.get("facility_type", "GENERAL_HOSPITAL"))),
            province=args.get("province", "Hà Nội"),
            bed_capacity=int(args.get("beds", args.get("bed_capacity", 100))),
            total_floor_area_m2=float(args.get("area", args.get("total_floor_area_m2", 6000.0))),
            chief_medical_officer=args.get("cmo", args.get("chief_medical_officer", "PGS.TS. Trần Quốc Tuấn")),
            cmo_practice_months=int(args.get("months", args.get("cmo_practice_months", 60))),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Healthcare facility licensing error: {exc}"}, indent=2)


def handle_medtech_trial(args: dict[str, Any]) -> str:
    """Tool handler for mekong_medtech_trial."""
    try:
        from src.core.medtech_engine import MedtechEngine

        engine = MedtechEngine()
        res = engine.submit_clinical_trial_protocol(
            device_id=args.get("device_id", "DEV-001"),
            trial_title=args.get("title", args.get("trial_title", "Đề cương thử nghiệm lâm sàng")),
            trial_phase=int(args.get("phase", args.get("trial_phase", 2))),
            principal_investigator=args.get("pi", args.get("principal_investigator", "GS.TS. Phạm Nhật An")),
            study_site=args.get("site", args.get("study_site", "Bệnh viện Đại học Y Dược TP.HCM")),
            target_subjects=int(args.get("subjects", args.get("target_subjects", 120))),
            irb_approved=bool(args.get("irb", args.get("irb_approved", True))),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Clinical trial protocol error: {exc}"}, indent=2)


def handle_medtech_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_medtech_list."""
    try:
        from src.core.medtech_engine import MedtechEngine

        engine = MedtechEngine()
        cat = args.get("category", "devices").lower().strip()
        limit = int(args.get("limit", 50))
        if cat in ("devices", "device"):
            res = engine.list_medical_devices(limit=limit)
        elif cat in ("prices", "price"):
            res = engine.list_price_declarations(limit=limit)
        elif cat in ("facilities", "facility"):
            res = engine.list_healthcare_facilities(limit=limit)
        elif cat in ("trials", "trial"):
            res = engine.list_clinical_trials(limit=limit)
        else:
            res = engine.list_medical_devices(limit=limit)
        return json.dumps(res.data, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"MedTech list error: {exc}"}, indent=2)


def handle_medtech_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_medtech_status."""
    try:
        from src.core.medtech_engine import MedtechEngine

        engine = MedtechEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"MedTech status error: {exc}"}, indent=2)


def handle_livestock_farm(args: dict[str, Any]) -> str:
    """Tool handler for mekong_livestock_farm."""
    try:
        from src.core.livestock_engine import LivestockEngine

        engine = LivestockEngine()
        res = engine.register_livestock_farm(
            farm_name=args["farm_name"],
            owner_name=args.get("owner_name", "Tập Đoàn Chăn Nuôi CP Việt Nam"),
            province=args.get("province", "Đồng Nai"),
            animal_type=args.get("animal_type", "PIG_FATTENER"),
            head_count=int(args.get("head_count", 2000)),
            agricultural_land_ha=float(args.get("agricultural_land_ha", 30.0)),
            region=args.get("region", "SOUTHEAST"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Livestock farm error: {exc}"}, indent=2)


def handle_livestock_distance(args: dict[str, Any]) -> str:
    """Tool handler for mekong_livestock_distance."""
    try:
        from src.core.livestock_engine import LivestockEngine

        engine = LivestockEngine()
        res = engine.audit_biosecurity_distance(
            farm_id=args["farm_id"],
            farm_scale=args.get("farm_scale", "LARGE_SCALE"),
            residential_distance_m=float(args.get("residential_distance_m", 450.0)),
            water_source_distance_m=float(args.get("water_source_distance_m", 120.0)),
            farm_to_farm_distance_m=float(args.get("farm_to_farm_distance_m", 1200.0)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Livestock distance error: {exc}"}, indent=2)


def handle_livestock_feed(args: dict[str, Any]) -> str:
    """Tool handler for mekong_livestock_feed."""
    try:
        from src.core.livestock_engine import LivestockEngine

        engine = LivestockEngine()
        res = engine.inspect_feed_quality(
            product_name=args["product_name"],
            feed_type=args.get("feed_type", "PIG_FEED_COMPLETE"),
            manufacturer=args.get("manufacturer", "C.P. Vietnam Corporation"),
            crude_protein_pct=float(args.get("crude_protein_pct", 18.5)),
            aflatoxin_b1_ppb=float(args.get("aflatoxin_b1_ppb", 8.5)),
            lead_pb_ppm=float(args.get("lead_pb_ppm", 1.2)),
            banned_substance=args.get("banned_substance"),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Livestock feed error: {exc}"}, indent=2)


def handle_livestock_waste(args: dict[str, Any]) -> str:
    """Tool handler for mekong_livestock_waste."""
    try:
        from src.core.livestock_engine import LivestockEngine

        engine = LivestockEngine()
        res = engine.audit_waste_treatment(
            farm_id=args["farm_id"],
            livestock_units=float(args.get("livestock_units", 400.0)),
            treatment_method=args.get("treatment_method", "BIOGAS_DIGESTER"),
            biogas_volume_m3=float(args.get("biogas_volume_m3", 350.0)),
            is_cattle=bool(args.get("is_cattle", False)),
        )
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Livestock waste error: {exc}"}, indent=2)


def handle_livestock_list(args: dict[str, Any]) -> str:
    """Tool handler for mekong_livestock_list."""
    try:
        from src.core.livestock_engine import LivestockEngine

        engine = LivestockEngine()
        category = args.get("category", "farms").lower().strip()
        limit = int(args.get("limit", 50))
        if category in ("farms", "farm"):
            res = engine.list_livestock_farms(limit=limit)
        elif category in ("biosecurity", "bio", "distance"):
            res = engine.list_biosecurity_audits(limit=limit)
        elif category in ("feed", "feeds", "quality"):
            res = engine.list_feed_inspections(limit=limit)
        elif category in ("waste", "biogas"):
            res = engine.list_waste_audits(limit=limit)
        else:
            res = engine.list_livestock_farms(limit=limit)
        return json.dumps(res.data, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Livestock list error: {exc}"}, indent=2)


def handle_livestock_status(args: dict[str, Any]) -> str:
    """Tool handler for mekong_livestock_status."""
    try:
        from src.core.livestock_engine import LivestockEngine

        engine = LivestockEngine()
        res = engine.get_status()
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": f"Livestock status error: {exc}"}, indent=2)


# ---------------------------------------------------------------------------
# Canonical Core Tools Specification
# ---------------------------------------------------------------------------



CORE_TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "name": "mekong_memory_store",
        "description": "Store a key-value or execution memory in Mekong canonical memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key, subject, or goal identifier"},
                "value": {"type": "string", "description": "Content, value, or fact to persist"},
                "ttl": {"type": "integer", "description": "Optional time-to-live in seconds"},
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "mekong_memory_recall",
        "description": "Retrieve an exact key-value or execution record by key from memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Memory key to retrieve"},
            },
            "required": ["key"],
        },
    },
    {
        "name": "mekong_memory_search",
        "description": "Search memories using vector semantic similarity with keyword substring fallback.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query or natural language phrase"},
                "limit": {"type": "integer", "description": "Maximum number of results to return (default: 10)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "mekong_plan_create",
        "description": "Decompose a goal into sequential/parallel tasks and persist the plan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "Goal or objective to decompose into an actionable plan"},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "mekong_plan_update",
        "description": "Update plan status ('active', 'completed') or a specific subtask status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Target plan identifier"},
                "status": {"type": "string", "description": "New plan status ('active', 'completed')"},
                "task_id": {"type": "string", "description": "Optional subtask ID within the plan"},
                "task_status": {
                    "type": "string",
                    "description": "New status for the subtask ('todo', 'in-progress', 'done')",
                },
            },
            "required": ["plan_id"],
        },
    },
    {
        "name": "mekong_plan_get",
        "description": "Fetch a plan by ID or list plans filtered by status ('active', 'completed').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string", "description": "Optional plan ID. If omitted, returns plan list"},
                "status": {"type": "string", "description": "Status filter when listing plans"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_task_create",
        "description": "Create a new task in the task backlog.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string", "description": "Subject or description of the task"},
            },
            "required": ["subject"],
        },
    },
    {
        "name": "mekong_task_update",
        "description": "Transition task status ('todo' -> 'in-progress' -> 'done').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "Task identifier"},
                "status": {"type": "string", "description": "Updated task status ('todo', 'in-progress', 'done')"},
            },
            "required": ["task_id", "status"],
        },
    },
    {
        "name": "mekong_task_list",
        "description": "List backlog tasks filtered by status ('todo', 'in-progress', 'done').",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional status filter"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_agent_list",
        "description": "List registered autonomous agents, roles, and allowed tools.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_agent_info",
        "description": "Fetch detailed policy, tools, context budget, and prompt info for a specific agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent identifier (e.g. 'cfo', 'cto', 'sun-tzu', 'ceo')"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_agent_route",
        "description": "Route a natural language goal to the optimal agent or multi-agent swarm team.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "Natural language task or objective description"},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "mekong_status",
        "description": "System health diagnostic across Python runtime, LLM providers, memory store, tasks, and plans.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_cost_estimate",
        "description": "Pre-execution LLM token usage and MCU cost prediction.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "Goal description for complexity classification"},
                "model_id": {"type": "string", "description": "Model ID to estimate (default: 'claude-sonnet-4-6')"},
            },
            "required": ["goal"],
        },
    },
    {
        "name": "mekong_subagent_dispatch",
        "description": "Dynamic subagent bridge: generates define_subagent and invoke_subagent payloads for Antigravity with HARNESS.md guardrails.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Subagent role identifier (one of 25 registered domain agents)",
                    "enum": [
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
                    ],
                },
                "task": {
                    "type": "string",
                    "description": "Task description, goal, or assignment for the subagent",
                },
                "model_tier": {
                    "type": "string",
                    "description": "Optional model tier override ('pro', 'flash', 'inherit')",
                    "enum": ["pro", "flash", "inherit"],
                    "default": "inherit",
                },
            },
            "required": ["role", "task"],
        },
    },
    {
        "name": "mekong_pev_plan",
        "description": "Generate structured PEV execution plan, tasks, and subagent assignments from a goal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "Goal statement to decompose into PEV tasks",
                },
                "mission_id": {
                    "type": "string",
                    "description": "Optional mission identifier to associate or resume",
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "mekong_pev_checkpoint",
        "description": "Capture atomic SQLite checkpoint of workspace files and task states.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mission_id": {
                    "type": "string",
                    "description": "Mission ID to checkpoint",
                },
                "label": {
                    "type": "string",
                    "description": "Checkpoint label (default: manual)",
                    "default": "manual",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of file paths to snapshot",
                },
                "test_results": {
                    "type": "object",
                    "description": "Optional test execution results",
                },
            },
            "required": ["mission_id"],
        },
    },
    {
        "name": "mekong_pev_rollback",
        "description": "Atomically restore workspace files and task states to a specific checkpoint.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "checkpoint_id": {
                    "type": "string",
                    "description": "Checkpoint ID to restore",
                },
            },
            "required": ["checkpoint_id"],
        },
    },
    {
        "name": "mekong_swarm_status",
        "description": "Inspect active multi-agent PEV mission progress, cycles, and health.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mission_id": {
                    "type": "string",
                    "description": "Optional mission ID to inspect",
                },
            },
        },
    },
    {
        "name": "mekong_eval_query",
        "description": "Query offline mission evaluations, p95 durations, failure clusters, and continuous learning recommendations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier filter, or 'all' for all agents",
                    "default": "all",
                },
                "days": {
                    "type": "integer",
                    "description": "Lookback window in days (default: 7)",
                    "default": 7,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max recent missions to return (default: 50)",
                    "default": 50,
                },
            },
        },
    },
    {
        "name": "mekong_recipe_evolve",
        "description": "Trigger self-improvement and recipe evolution for a goal or recipe based on failure clusters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe_name": {
                    "type": "string",
                    "description": "Recipe slug or name to evolve (leave empty to evolve across all recent missions)",
                    "default": "",
                },
                "goal": {
                    "type": "string",
                    "description": "Optional goal description for synthesized recipe",
                    "default": "",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force evolution even if already evolved to latest version",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "mekong_mission_metrics",
        "description": "Retrieve aggregated telemetry metrics, credit usage, and failure breakdowns across agents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_id": {
                    "type": "string",
                    "description": "Agent identifier filter, or 'all' for all agents",
                    "default": "all",
                },
                "days": {
                    "type": "integer",
                    "description": "Lookback window in days (default: 7)",
                    "default": 7,
                },
            },
        },
    },
    {
        "name": "mekong_palette_search",
        "description": "Fuzzy search across Mekong CLI commands, Antigravity skills, and domain subagents using Vietnamese or English natural language.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query in Vietnamese or English (e.g. 'sửa lỗi', 'kế hoạch', 'cook', 'tax')",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter: strategy, business, product, engineering, operations, vietnam, or all",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5,
                },
            },
        },
    },
    {
        "name": "mekong_tui_dashboard_status",
        "description": "Retrieve real-time telemetry, AGI subsystem health, checkpoints, and system performance summary for the Mekong TUI dashboard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Whether to return detailed subsystem breakdown and metric percentiles",
                    "default": False,
                },
            },
        },
    },
    {
        "name": "mekong_benchmark_run",
        "description": "Run autonomous benchmark suites across PEV, checkpoints, subagents, and chaos scenarios.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "suite": {
                    "type": "string",
                    "description": "Benchmark suite to run: pev, checkpoints, subagents, chaos, or all (default: all)",
                    "default": "all",
                },
                "iterations": {
                    "type": "integer",
                    "description": "Number of iterations per test (default: 1)",
                    "default": 1,
                },
                "chaos_level": {
                    "type": "string",
                    "description": "Chaos intensity: none, low, medium, or high (default: none)",
                    "default": "none",
                },
            },
        },
    },
    {
        "name": "mekong_chaos_simulate",
        "description": "Simulate chaos fault injection against checkpoints, tools, or payloads to test self-healing resilience.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Chaos fault target: checkpoint, timeout, or payload (default: checkpoint)",
                    "default": "checkpoint",
                },
                "error_type": {
                    "type": "string",
                    "description": "Specific error scenario type (default: corrupt_file)",
                    "default": "corrupt_file",
                },
            },
        },
    },
    {
        "name": "mekong_gateway_status",
        "description": "Query Mekong Gateway server health, uptime, active SSE streams, and system metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_gateway_rate_limit",
        "description": "Query tenant rate limit quota, tokens remaining, and reset timestamp.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {
                    "type": "string",
                    "description": "Tenant identifier",
                    "default": "default",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_watch_status",
        "description": "Query active Mekong file watcher daemon state, monitored directories, recent change events, and repair metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_self_repair",
        "description": "Perform AST syntax diagnostics and automated self-healing repair (or checkpoint rollback) on a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the Python file requiring diagnostic evaluation and repair",
                },
                "error_detail": {
                    "type": "string",
                    "description": "Optional known error message or diagnostic text",
                    "default": "",
                },
                "mode": {
                    "type": "string",
                    "description": "Repair strategy: auto, syntax_fix, or rollback",
                    "enum": ["auto", "syntax_fix", "rollback"],
                    "default": "auto",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "mekong_package_build",
        "description": "Build multi-platform distribution packages, Homebrew formulas, and Docker assets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Packaging target: pypi, homebrew, docker, or all",
                    "default": "all",
                },
                "output_dir": {
                    "type": "string",
                    "description": "Destination directory for generated artifacts",
                    "default": "dist",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_sandbox_exec",
        "description": "Execute a shell command inside an isolated container or secure subprocess sandbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to run in the isolated sandbox",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Execution timeout in seconds",
                    "default": 30,
                },
                "memory_limit_mb": {
                    "type": "integer",
                    "description": "Memory limit in megabytes",
                    "default": 512,
                },
                "image": {
                    "type": "string",
                    "description": "Container image to use",
                    "default": "python:3.11-slim",
                },
            },
            "required": ["command"],
        },
    },
    {
        "name": "mekong_consensus_vote",
        "description": "Execute a multi-agent quorum vote on a proposal (majority, supermajority, unanimous, weighted).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposal": {
                    "type": "string",
                    "description": "The proposal to vote upon",
                },
                "quorum": {
                    "type": "string",
                    "description": "Quorum rule: majority, supermajority, unanimous, or weighted",
                    "default": "majority",
                },
                "agents": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of participating agent roles",
                },
            },
            "required": ["proposal"],
        },
    },
    {
        "name": "mekong_consensus_debate",
        "description": "Conduct a structured multi-round debate between domain roles with synthetic consensus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The technical or strategic topic to debate",
                },
                "proponent": {
                    "type": "string",
                    "description": "Proponent agent role (e.g. cto)",
                    "default": "cto",
                },
                "opponent": {
                    "type": "string",
                    "description": "Opponent agent role (e.g. sre)",
                    "default": "sre",
                },
                "moderator": {
                    "type": "string",
                    "description": "Moderator agent role (default: ceo)",
                    "default": "ceo",
                },
                "rounds": {
                    "type": "integer",
                    "description": "Number of debate rounds",
                    "default": 2,
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "mekong_semantic_recall",
        "description": "Perform associative semantic and BM25 search across federated memory domains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text for associative recall",
                },
                "domain": {
                    "type": "string",
                    "description": "Target domain: episodic, decisions, entities, patterns, or all",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "mekong_knowledge_graph_query",
        "description": "Traverse relational codebase and architectural knowledge graph around an entity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "entity": {
                    "type": "string",
                    "description": "Entity name, symbol, or file path to query",
                },
                "depth": {
                    "type": "integer",
                    "description": "Graph traversal depth (1-4)",
                    "default": 2,
                },
            },
            "required": ["entity"],
        },
    },
    {
        "name": "mekong_telemetry_metrics",
        "description": "Export or inspect standard Prometheus exposition metrics or structured JSON.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format_type": {
                    "type": "string",
                    "description": "Exposition format: prometheus or json (default: prometheus)",
                    "default": "prometheus",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_trace_query",
        "description": "Query distributed tracing spans, latency timings, and W3C traceparent headers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "trace_id": {
                    "type": "string",
                    "description": "Optional 32-hex W3C trace identifier to filter spans",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of spans to return (default: 20)",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_queue_enqueue",
        "description": "Schedule a new task for prioritized execution in the distributed task queue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name or operation identifier for the queued task",
                },
                "priority": {
                    "type": "string",
                    "description": "Priority: critical, high, normal, or low (default: normal)",
                    "default": "normal",
                },
                "payload": {
                    "type": "object",
                    "description": "Optional JSON payload dictionary passed to task worker",
                },
                "max_retries": {
                    "type": "integer",
                    "description": "Maximum retry attempts before routing to DLQ (default: 3)",
                    "default": 3,
                },
                "delay_sec": {
                    "type": "number",
                    "description": "Delay execution by N seconds (default: 0)",
                    "default": 0,
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_queue_status",
        "description": "Inspect queue depth, active worker leases, and dead-letter counts.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_queue_dlq_action",
        "description": "Inspect, retry, or clear tasks residing in the dead-letter queue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: list, retry, retry_all, or clear (default: list)",
                    "default": "list",
                },
                "task_id": {
                    "type": "string",
                    "description": "Specific task ID (required when action is retry)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_pipeline_run",
        "description": "Run multi-agent sequential pipeline (FilePicker -> Editor -> Reviewer) for software engineering tasks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "Goal or task description for the multi-agent pipeline to execute",
                },
                "stages": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of stage names (default: ['file-picker', 'editor', 'reviewer'])",
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "mekong_pipeline_status",
        "description": "Inspect status, stage outcomes, and timings for a pipeline execution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pipeline_id": {
                    "type": "string",
                    "description": "Optional pipeline ID to inspect. If omitted, returns all tracked pipelines.",
                    "default": "",
                },
            },
        },
    },
    {
        "name": "mekong_worktree_create",
        "description": "Create a new isolated git worktree branching from the base branch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "feature": {
                    "type": "string",
                    "description": "Feature description, ticket ID, or branch name to isolate",
                },
                "prefix": {
                    "type": "string",
                    "description": "Branch prefix override (feat, fix, refactor, docs, test, perf, chore)",
                },
                "base_branch": {
                    "type": "string",
                    "description": "Base branch to branch from (defaults to main/master)",
                },
                "no_prefix": {
                    "type": "boolean",
                    "description": "Do not prepend prefix; use feature string directly",
                    "default": False,
                },
                "root": {
                    "type": "string",
                    "description": "Custom root directory to host the isolated worktree directory",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate branch and worktree path calculation without executing git mutations",
                    "default": False,
                },
            },
            "required": ["feature"],
        },
    },
    {
        "name": "mekong_worktree_list",
        "description": "List all registered git worktrees in the repository.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_worktree_status",
        "description": "Inspect status, uncommitted changes, and divergence against base branch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path_or_branch": {
                    "type": "string",
                    "description": "Optional worktree path or branch name to inspect",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_worktree_remove",
        "description": "Remove an isolated git worktree workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path_or_name": {
                    "type": "string",
                    "description": "Worktree path, directory basename, or branch name to remove",
                },
                "force": {
                    "type": "boolean",
                    "description": "Force removal even if untracked files or uncommitted changes exist",
                    "default": False,
                },
            },
            "required": ["path_or_name"],
        },
    },
    {
        "name": "mekong_ship_preflight",
        "description": "Inspect repository topology, branch, remote, and dirty files before shipping.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_ship_run",
        "description": "Run the production shipping pipeline: lint, test, stage, commit, and push.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Optional commit message description (auto-synthesized if omitted)",
                },
                "run_lint": {
                    "type": "boolean",
                    "description": "Run linters before staging (default: true)",
                    "default": True,
                },
                "run_tests": {
                    "type": "boolean",
                    "description": "Run automated tests before staging (default: true)",
                    "default": True,
                },
                "push": {
                    "type": "boolean",
                    "description": "Push branch to remote upstream (default: true)",
                    "default": True,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate shipping without mutating git history or remote (default: false)",
                    "default": False,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_daily_report",
        "description": "Produce an executive daily standup report: git commit velocity, uncommitted files, codebase debt, and mesh queue depth.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since": {
                    "type": "string",
                    "description": "Time window for git commit velocity (default: '24 hours ago')",
                    "default": "24 hours ago",
                },
                "include_todos": {
                    "type": "boolean",
                    "description": "Scan codebase for open action markers (default: true)",
                    "default": True,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_daily_focus",
        "description": "Retrieve prioritized strategic daily focus recommendations synthesized from repository and queue signals.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_quick_start_plan",
        "description": "Simulate and retrieve the 5-step project kickoff blueprint, architecture PRD, and milestone checklist without writing files.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name or slug of the new project to simulate (default: mekong-app)",
                    "default": "mekong-app",
                },
                "project_type": {
                    "type": "string",
                    "description": "Project archetype: cli, web, agent, fullstack (default: agent)",
                    "enum": ["cli", "web", "agent", "fullstack"],
                    "default": "agent",
                },
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "mekong_quick_start_create",
        "description": "Execute the end-to-end 5-step project kickoff: brainstorm, plan, scaffold, verify & git commit, and monetization roadmap.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Name or slug of the project to initialize",
                },
                "project_type": {
                    "type": "string",
                    "description": "Project archetype: cli, web, agent, fullstack (default: agent)",
                    "enum": ["cli", "web", "agent", "fullstack"],
                    "default": "agent",
                },
                "target_dir": {
                    "type": "string",
                    "description": "Optional destination directory (defaults to ./<project_name>)",
                    "default": "",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate kickoff execution without disk mutations",
                    "default": False,
                },
                "init_git": {
                    "type": "boolean",
                    "description": "Initialize git repository and create initial commit (default: true)",
                    "default": True,
                },
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "mekong_cto_scorecard",
        "description": "Calculate composite engineering health score, grade, test coverage, and security posture.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_cto_review",
        "description": "Conduct automated code quality, anti-pattern, dynamic execution, and security review.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_path": {
                    "type": "string",
                    "description": "Optional path to directory or file to review",
                    "default": "",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_cto_architect",
        "description": "Generate an Architecture Decision Record (ADR) with context, decision, consequences, and alternatives.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the architectural decision",
                },
                "context": {
                    "type": "string",
                    "description": "Background context and problem rationale",
                    "default": "",
                },
                "decision": {
                    "type": "string",
                    "description": "Chosen design pattern or implementation decision",
                    "default": "",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "mekong_sales_pipeline",
        "description": "Query sales pipeline metrics, weighted revenue forecasts, and opportunities by stage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stage": {
                    "type": "string",
                    "description": "Optional stage filter (lead, qualified, proposal, negotiation, won, lost)",
                    "default": "",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_sales_deal_add",
        "description": "Add a new deal opportunity to the sales pipeline ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Opportunity name",
                },
                "company": {
                    "type": "string",
                    "description": "Target company name",
                },
                "value": {
                    "type": "number",
                    "description": "Estimated deal value in USD",
                },
                "stage": {
                    "type": "string",
                    "description": "Pipeline stage (default 'lead')",
                    "default": "lead",
                },
                "email": {
                    "type": "string",
                    "description": "Contact email address",
                    "default": "",
                },
            },
            "required": ["name", "company", "value"],
        },
    },
    {
        "name": "mekong_sales_outreach",
        "description": "Generate tailored multi-channel outreach copy and cadence (email, linkedin, zalo).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company": {
                    "type": "string",
                    "description": "Target company name",
                },
                "persona": {
                    "type": "string",
                    "description": "Target persona (e.g. CTO, VP of Engineering)",
                    "default": "CTO",
                },
                "channel": {
                    "type": "string",
                    "description": "Channel: email, linkedin, zalo",
                    "default": "email",
                },
            },
            "required": ["company"],
        },
    },
    {
        "name": "mekong_marketing_metrics",
        "description": "Query aggregated marketing metrics, active campaigns, total spend, and conversions.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_marketing_campaign_create",
        "description": "Create and register a promotional or growth marketing campaign.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Campaign name",
                },
                "channel": {
                    "type": "string",
                    "description": "Channel (social, search, content, email, local, zalo)",
                    "default": "social",
                },
                "budget": {
                    "type": "number",
                    "description": "Allocated budget in USD",
                    "default": 1000.0,
                },
                "target_audience": {
                    "type": "string",
                    "description": "Target audience persona description",
                    "default": "",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_marketing_content_generate",
        "description": "Synthesize ready-to-use marketing copy and creative with hashtags and call-to-action.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic or product feature to create copy for",
                },
                "channel": {
                    "type": "string",
                    "description": "Destination channel (social, linkedin, zalo, blog)",
                    "default": "social",
                },
                "content_type": {
                    "type": "string",
                    "description": "Content format (post, article, thread)",
                    "default": "post",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "mekong_dev_audit",
        "description": "Perform static AST and security audit across the codebase or specific module.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Optional path to directory or file to audit",
                    "default": "",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_dev_scaffold",
        "description": "Scaffold a new structured Python module, service, API, or agent with unit tests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Component or module name",
                },
                "module_type": {
                    "type": "string",
                    "description": "Type of module (service, api, agent, util)",
                    "default": "service",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Simulate file creation without writing to disk",
                    "default": True,
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_dev_review",
        "description": "Review working tree git diff for safety, technical debt, and quality hazards.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_ops_health_sweep",
        "description": "Run comprehensive system health audit across runtime, storage, databases, git & configs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "save_report": {
                    "type": "boolean",
                    "description": "Whether to save markdown report to reports/health-sweep/",
                    "default": False,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_ops_incident_create",
        "description": "Create and track a new SRE incident in the operations ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Incident title / brief summary",
                },
                "severity": {
                    "type": "string",
                    "description": "Severity level (SEV1, SEV2, SEV3, SEV4)",
                    "default": "SEV3",
                },
                "service": {
                    "type": "string",
                    "description": "Affected subsystem or service",
                    "default": "core",
                },
                "summary": {
                    "type": "string",
                    "description": "Detailed incident description",
                    "default": "",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "mekong_ops_incident_list",
        "description": "List tracked SRE incidents filtered by status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status (OPEN, RESOLVED, ALL)",
                    "default": "ALL",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_support_onboard_status",
        "description": "Query current project onboarding milestones, completed steps, and progress percentage.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_support_feedback_submit",
        "description": "Record customer satisfaction, feedback comments, or Net Promoter Score (NPS).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "nps_score": {
                    "type": "integer",
                    "description": "NPS rating from 0 to 10",
                },
                "feedback_text": {
                    "type": "string",
                    "description": "Customer comments or suggestion",
                    "default": "",
                },
                "category": {
                    "type": "string",
                    "description": "Category (product, pricing, performance, support)",
                    "default": "general",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_support_triage",
        "description": "Perform smart AI/heuristic triage for user issues, error traces, and operational bugs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "issue_text": {
                    "type": "string",
                    "description": "Error description or problem statement",
                },
            },
            "required": ["issue_text"],
        },
    },
    {
        "name": "mekong_consulting_pricing",
        "description": "Show standardized AI agent consulting packages, pricing, and deliverables.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "currency": {
                    "type": "string",
                    "description": "Currency code (USD or VND)",
                    "default": "USD",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_consulting_proposal",
        "description": "Synthesize a customized commercial consulting proposal for a prospect.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prospect_name": {
                    "type": "string",
                    "description": "Client or prospect company name",
                },
                "service_tier": {
                    "type": "string",
                    "description": "Service tier (audit, custom_agent, full_stack, retainer)",
                    "default": "custom_agent",
                },
                "requirements": {
                    "type": "string",
                    "description": "Custom requirements or client problem statement",
                    "default": "",
                },
            },
            "required": ["prospect_name"],
        },
    },
    {
        "name": "mekong_consulting_outreach",
        "description": "Generate multi-channel B2B cold/warm outreach templates (Email, LinkedIn, Zalo).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prospect_name": {
                    "type": "string",
                    "description": "Client or prospect company name",
                },
                "service_tier": {
                    "type": "string",
                    "description": "Service tier (audit, custom_agent, full_stack, retainer)",
                    "default": "custom_agent",
                },
                "role": {
                    "type": "string",
                    "description": "Recipient role/title (CTO, Founder, Head of Product)",
                    "default": "CTO",
                },
            },
            "required": ["prospect_name"],
        },
    },
    {
        "name": "mekong_revenue_metrics",
        "description": "Calculate current MRR, ARR, ARPU, LTV, churn rate, and MRR waterfall economics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Reporting period (month, quarter, year)",
                    "default": "month",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_revenue_record",
        "description": "Record a payment transaction into the revenue ledger and update active subscriptions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "customer_id": {
                    "type": "string",
                    "description": "Customer identifier",
                },
                "amount": {
                    "type": "number",
                    "description": "Transaction payment amount",
                },
                "customer_name": {
                    "type": "string",
                    "description": "Customer display name",
                    "default": "",
                },
                "currency": {
                    "type": "string",
                    "description": "Payment currency (USD or VND)",
                    "default": "USD",
                },
                "tier": {
                    "type": "string",
                    "description": "Subscription tier (free, starter, growth, scale, pro, enterprise)",
                    "default": "starter",
                },
                "txn_type": {
                    "type": "string",
                    "description": "Transaction type (subscription, one_time, addon, refund)",
                    "default": "subscription",
                },
                "gateway": {
                    "type": "string",
                    "description": "Payment gateway (stripe, polar, bank_transfer, manual)",
                    "default": "stripe",
                },
            },
            "required": ["customer_id", "amount"],
        },
    },
    {
        "name": "mekong_revenue_forecast",
        "description": "Project future MRR, ARR, and cumulative cash flows across growth scenarios.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "months": {
                    "type": "integer",
                    "description": "Forecast horizon in months",
                    "default": 6,
                },
                "scenario": {
                    "type": "string",
                    "description": "Growth scenario (conservative, base, aggressive)",
                    "default": "base",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_content_generate",
        "description": "Generate structured, ready-to-publish content for any pillar and format.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pillar": {
                    "type": "string",
                    "description": "Content pillar (one-person-company, ai-agents, solo-founder, binh-phap, zenos)",
                },
                "format_type": {
                    "type": "string",
                    "description": "Content format (blog, twitter, linkedin, youtube_script, newsletter)",
                    "default": "blog",
                },
                "topic": {
                    "type": "string",
                    "description": "Article or post topic",
                    "default": "",
                },
                "channel": {
                    "type": "string",
                    "description": "Target distribution channel (blog, twitter, indiehackers, youtube, substack)",
                    "default": "",
                },
            },
            "required": ["pillar"],
        },
    },
    {
        "name": "mekong_content_calendar",
        "description": "Query editorial publication calendar, frequencies, and upcoming deadlines.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_content_channels",
        "description": "Query distribution channels, audience reach, and publication metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_copywriting_generate",
        "description": "Generate high-converting marketing and product copy using proven psychological frameworks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Product or feature name",
                    "default": "Mekong CLI",
                },
                "target_audience": {
                    "type": "string",
                    "description": "Target audience persona",
                    "default": "Founders & Engineers",
                },
                "formula": {
                    "type": "string",
                    "description": "Copywriting formula (pas, aida, bab, fab, 4us)",
                    "default": "pas",
                },
                "copy_type": {
                    "type": "string",
                    "description": "Copy format (landing_page, email, headline, cta)",
                    "default": "landing_page",
                },
                "key_benefit": {
                    "type": "string",
                    "description": "Core value proposition or transformation",
                    "default": "",
                },
                "style": {
                    "type": "string",
                    "description": "Brand tone and style (direct_response, technical_founder, punchy_minimalist, storytelling)",
                    "default": "direct_response",
                },
            },
            "required": ["product_name"],
        },
    },
    {
        "name": "mekong_copywriting_headline",
        "description": "Generate high-conversion headline variations across psychological angles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Product or feature name",
                    "default": "Mekong CLI",
                },
                "value_prop": {
                    "type": "string",
                    "description": "Core value proposition",
                    "default": "automate engineering workflows",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of headline variations",
                    "default": 5,
                },
            },
            "required": ["product_name"],
        },
    },
    {
        "name": "mekong_copywriting_cta",
        "description": "Generate conversion call-to-action button variations with risk reversals.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action_goal": {
                    "type": "string",
                    "description": "Desired user conversion action",
                    "default": "start free trial",
                },
                "risk_reversal": {
                    "type": "string",
                    "description": "Guarantee or risk reduction statement",
                    "default": "",
                },
            },
            "required": ["action_goal"],
        },
    },
    {
        "name": "mekong_billing_simulate",
        "description": "Simulate an itemized billing invoice based on accrued usage events and pricing tiers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_key": {
                    "type": "string",
                    "description": "License key or tenant identifier",
                    "default": "mekong_lic_default",
                },
                "tier": {
                    "type": "string",
                    "description": "Pricing tier (free, developer, pro, enterprise)",
                    "default": "pro",
                },
                "period_days": {
                    "type": "integer",
                    "description": "Simulation lookback window in days",
                    "default": 30,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_billing_record_usage",
        "description": "Ingest and meter a billable usage event with idempotent deduplication and pricing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_key": {
                    "type": "string",
                    "description": "License key or tenant identifier",
                    "default": "mekong_lic_default",
                },
                "event_type": {
                    "type": "string",
                    "description": "Billable event type (llm_tokens, agent_minutes, api_calls, storage_mb, mcu_credits)",
                    "default": "llm_tokens",
                },
                "quantity": {
                    "type": "number",
                    "description": "Consumed metric quantity",
                    "default": 1.0,
                },
                "idempotency_key": {
                    "type": "string",
                    "description": "Unique key to prevent duplicate billing",
                    "default": "",
                },
                "tier": {
                    "type": "string",
                    "description": "Pricing tier",
                    "default": "pro",
                },
            },
            "required": ["event_type", "quantity"],
        },
    },
    {
        "name": "mekong_billing_status",
        "description": "Retrieve real-time billing quotas, consumption, unbilled charges, and health status for a license.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_key": {
                    "type": "string",
                    "description": "License key to inspect",
                    "default": "mekong_lic_default",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_vendor_onboard",
        "description": "Register and onboard a third-party vendor or provider into the sovereign marketplace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Vendor name / extension identifier",
                },
                "vendor_type": {
                    "type": "string",
                    "description": "Vendor type (agent, provider, hook, recipe, model_router)",
                    "default": "agent",
                },
                "description": {
                    "type": "string",
                    "description": "Short description of the extension",
                    "default": "",
                },
                "author": {
                    "type": "string",
                    "description": "Author or organization",
                    "default": "Community Builder",
                },
                "version": {
                    "type": "string",
                    "description": "Semantic version",
                    "default": "1.0.0",
                },
                "trust_score": {
                    "type": "number",
                    "description": "Initial trust score (0-100)",
                    "default": 85.0,
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_vendor_list",
        "description": "List registered marketplace vendors and providers filtered by type and status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vendor_type": {
                    "type": "string",
                    "description": "Filter by vendor type (all, agent, provider, hook, recipe)",
                    "default": "all",
                },
                "status": {
                    "type": "string",
                    "description": "Filter by status (all, active, pending_audit, delisted)",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum vendors to return",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_vendor_assess",
        "description": "Perform automated compliance, security, and boundary assessment on a vendor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Vendor name or ID to assess",
                },
                "audit_type": {
                    "type": "string",
                    "description": "Audit type (security, compliance, performance, boundary)",
                    "default": "security",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_founder_assess",
        "description": "Assess a founder genome with personality, core values, fears, risk tolerance, and cognitive biases.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Founder name or handle",
                },
                "mission": {
                    "type": "string",
                    "description": "Founder mission or purpose statement",
                    "default": "",
                },
                "tipi_responses": {
                    "type": "object",
                    "description": "TIPI-10 item responses (1-7 Likert scale)",
                },
                "values": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Selected Schwartz value IDs",
                },
                "fears": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Fear triggers, predicted behaviors, and mitigations",
                },
                "risk_ratings": {
                    "type": "object",
                    "description": "Risk dimension ratings (1-10 scale)",
                },
                "bias_responses": {
                    "type": "object",
                    "description": "Cognitive bias responses (boolean per bias)",
                },
                "particle_id": {
                    "type": "string",
                    "description": "Optional ZenOS particle ID for identity linkage",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_founder_review",
        "description": "Load and inspect a complete founder genome profile from the registry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "founder_id": {
                    "type": "string",
                    "description": "Founder name or entity ID to review",
                },
            },
            "required": ["founder_id"],
        },
    },
    {
        "name": "mekong_founder_list",
        "description": "List assessed founder genome profiles with optional risk level filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "risk_level": {
                    "type": "string",
                    "description": "Filter by risk level (all, conservative, moderate, aggressive)",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of founders to return",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_governance_propose",
        "description": "Draft and submit a new constitutional amendment proposal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Proposal title",
                },
                "description": {
                    "type": "string",
                    "description": "Description or rationale for the amendment",
                },
                "text": {
                    "type": "string",
                    "description": "Exact proposed amendment text",
                },
                "proposer": {
                    "type": "string",
                    "description": "Proposer member ID",
                    "default": "founder",
                },
                "tier": {
                    "type": "string",
                    "description": "Amendment tier (soft, operational, foundational)",
                    "default": "soft",
                },
                "co_sponsors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of co-sponsor member IDs",
                },
            },
            "required": ["title", "description", "text"],
        },
    },
    {
        "name": "mekong_governance_vote",
        "description": "Cast a weighted cryptographic ballot on an active governance proposal.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposal_id": {
                    "type": "string",
                    "description": "Proposal ID to vote on",
                },
                "voter": {
                    "type": "string",
                    "description": "Voter member ID",
                    "default": "founder",
                },
                "choice": {
                    "type": "string",
                    "description": "Vote choice (yes, no, abstain, recuse)",
                    "default": "yes",
                },
                "weight": {
                    "type": "number",
                    "description": "Voting weight or reputation multiplier",
                    "default": 1.0,
                },
            },
            "required": ["proposal_id", "choice"],
        },
    },
    {
        "name": "mekong_governance_tally",
        "description": "Tally ballots, compute quorum satisfaction, and finalize proposal outcome.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "proposal_id": {
                    "type": "string",
                    "description": "Proposal ID to tally",
                },
            },
            "required": ["proposal_id"],
        },
    },
    {
        "name": "mekong_governance_list",
        "description": "List constitutional governance proposals filtered by status and tier.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status (all, voting, passed, rejected, enacted)",
                    "default": "all",
                },
                "tier": {
                    "type": "string",
                    "description": "Filter by tier (all, soft, operational, foundational)",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of proposals to return",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_particle_init",
        "description": "Create and register a new ZenOS particle with constitutional mission.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Unique name of the ZenOS particle",
                },
                "mission": {
                    "type": "string",
                    "description": "Mission statement for the particle constitution",
                    "default": "",
                },
                "template": {
                    "type": "string",
                    "description": "Template scaffold name (default: skel)",
                    "default": "skel",
                },
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_particle_status",
        "description": "Show a ZenOS particle's network status, connections, trust score, and collusion check.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "particle_id": {
                    "type": "string",
                    "description": "Particle ID or name (default returns overview status)",
                    "default": "default",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_particle_connect",
        "description": "Establish a bidirectional trust relationship between two ZenOS particles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "particle_a": {
                    "type": "string",
                    "description": "First particle name or ID",
                },
                "particle_b": {
                    "type": "string",
                    "description": "Second particle name or ID",
                },
                "trust_score": {
                    "type": "number",
                    "description": "Initial trust score (default: 50.0)",
                    "default": 50.0,
                },
            },
            "required": ["particle_a", "particle_b"],
        },
    },
    {
        "name": "mekong_particle_cell_run",
        "description": "Execute an autonomous AI cell role within particle constitutional context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Cell role identifier (strategist, compliance, executor, evaluator)",
                },
                "prompt": {
                    "type": "string",
                    "description": "Task prompt for the AI cell",
                },
                "particle_id": {
                    "type": "string",
                    "description": "Particle ID or name",
                    "default": "default",
                },
                "auto_compliance": {
                    "type": "boolean",
                    "description": "Run constitutional compliance check after execution",
                    "default": False,
                },
            },
            "required": ["role", "prompt"],
        },
    },
    {
        "name": "mekong_thue_tncn",
        "description": "Calculate progressive Personal Income Tax (TNCN) under Vietnamese tax regulations (Điều 22).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "monthly_income": {
                    "type": "number",
                    "description": "Monthly gross income in VND",
                },
                "dependents": {
                    "type": "integer",
                    "description": "Number of qualified dependents (4.4M VND deduction each)",
                    "default": 0,
                },
            },
            "required": ["monthly_income"],
        },
    },
    {
        "name": "mekong_thue_tndn",
        "description": "Calculate Corporate Income Tax (TNDN) with standard 20% or SME 17% preferential rate.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "annual_revenue": {
                    "type": "number",
                    "description": "Annual enterprise gross revenue in VND",
                },
                "profit": {
                    "type": "number",
                    "description": "Optional taxable profit in VND (estimated at 15% if omitted)",
                },
                "is_sme": {
                    "type": "boolean",
                    "description": "Apply SME preferential rate (17%) if revenue <= 3B VND",
                    "default": True,
                },
            },
            "required": ["annual_revenue"],
        },
    },
    {
        "name": "mekong_thue_gtgt",
        "description": "Calculate Value Added Tax (GTGT / VAT 0%, 5%, 8%, 10%) under Decree 123 & Circular 78.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Base subtotal amount in VND before VAT",
                },
                "rate": {
                    "type": "integer",
                    "description": "VAT tax rate percentage (0, 5, 8, 10)",
                    "default": 10,
                },
            },
            "required": ["amount"],
        },
    },
    {
        "name": "mekong_thue_status",
        "description": "Retrieve Vietnamese tax engine status, statutory deduction rates, and historical simulation summaries.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_ke_toan_create",
        "description": "Create an electronic invoice compliant with Decree 123 & Circular 78 and save to accounting database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Subtotal invoice amount before VAT (VND)",
                },
                "buyer": {
                    "type": "string",
                    "description": "Buyer name or purchasing company entity",
                },
                "vat_rate": {
                    "type": "integer",
                    "description": "VAT tax rate percentage (0, 5, 8, 10)",
                    "default": 10,
                },
                "seller": {
                    "type": "string",
                    "description": "Seller company name",
                    "default": "Doanh Nghiệp",
                },
                "seller_tax_code": {
                    "type": "string",
                    "description": "Seller tax identification code (Mã số thuế)",
                    "default": "0000000000",
                },
                "buyer_tax_code": {
                    "type": "string",
                    "description": "Buyer tax identification code",
                    "default": "",
                },
                "description": {
                    "type": "string",
                    "description": "Product or service description",
                    "default": "Hàng hóa/Dịch vụ",
                },
            },
            "required": ["amount", "buyer"],
        },
    },
    {
        "name": "mekong_ke_toan_xml",
        "description": "Generate electronic invoice XML complying with Circular 78/2021/TT-BTC schema.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Subtotal invoice amount before VAT (VND)",
                },
                "buyer": {
                    "type": "string",
                    "description": "Buyer name or purchasing company entity",
                },
                "vat_rate": {
                    "type": "integer",
                    "description": "VAT tax rate percentage (0, 5, 8, 10)",
                    "default": 10,
                },
                "seller": {
                    "type": "string",
                    "description": "Seller company name",
                    "default": "Doanh Nghiệp",
                },
                "seller_tax_code": {
                    "type": "string",
                    "description": "Seller tax identification code",
                    "default": "0000000000",
                },
                "description": {
                    "type": "string",
                    "description": "Product or service description",
                    "default": "Hàng hóa/Dịch vụ",
                },
            },
            "required": ["amount", "buyer"],
        },
    },
    {
        "name": "mekong_ke_toan_journal",
        "description": "Generate balanced VAS double-entry journal entry (Nợ 131 / Có 511, Có 3331) for sales revenue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Subtotal invoice amount before VAT (VND)",
                },
                "buyer": {
                    "type": "string",
                    "description": "Buyer name or purchasing company entity",
                },
                "vat_rate": {
                    "type": "integer",
                    "description": "VAT tax rate percentage (0, 5, 8, 10)",
                    "default": 10,
                },
                "seller": {
                    "type": "string",
                    "description": "Seller company name",
                    "default": "Doanh Nghiệp",
                },
                "seller_tax_code": {
                    "type": "string",
                    "description": "Seller tax identification code",
                    "default": "0000000000",
                },
                "description": {
                    "type": "string",
                    "description": "Product or service description",
                    "default": "Hàng hóa/Dịch vụ",
                },
            },
            "required": ["amount", "buyer"],
        },
    },
    {
        "name": "mekong_ke_toan_status",
        "description": "Retrieve Vietnamese accounting system status, invoice totals, VAT output, and general ledger statistics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_zalo_send",
        "description": "Send a customer care or transactional message to a Zalo user ID via Zalo OA.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "Zalo User ID (UID)",
                },
                "message": {
                    "type": "string",
                    "description": "Message body content",
                },
                "template": {
                    "type": "string",
                    "description": "Optional message template identifier",
                    "default": "",
                },
            },
            "required": ["user_id", "message"],
        },
    },
    {
        "name": "mekong_zalo_broadcast",
        "description": "Broadcast an announcement or promotion to subscribers via Zalo OA.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Broadcast message content",
                },
                "title": {
                    "type": "string",
                    "description": "Broadcast notification title",
                    "default": "Thông báo Zalo OA",
                },
                "target_segment": {
                    "type": "string",
                    "description": "Follower target segment (all, vip, active, standard)",
                    "default": "all",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "mekong_zalo_followers",
        "description": "Query Zalo OA follower roster, tiers, and engagement status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "segment": {
                    "type": "string",
                    "description": "Filter by follower segment (all, vip, active, standard)",
                    "default": "all",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of followers to return",
                    "default": 50,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_zalo_caption",
        "description": "Generate high-engagement social media captions across 5 tones (vui_ve, chuyen_nghiep, sang_tao, khuyen_mai, binh_phap).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Product name or campaign topic",
                },
                "tone": {
                    "type": "string",
                    "description": "Caption tone: vui_ve | chuyen_nghiep | sang_tao | khuyen_mai | binh_phap",
                    "default": "vui_ve",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "mekong_zalo_status",
        "description": "Retrieve Zalo OA customer messaging, broadcast, and engagement metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_bhxh_calc",
        "description": "Calculate statutory Vietnamese social insurance (BHXH 8%/17.5%, BHYT 1.5%/3%, BHTN 1%/1%) with salary ceilings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "salary": {
                    "type": "number",
                    "description": "Gross monthly salary in VND",
                },
                "region": {
                    "type": "integer",
                    "description": "Region minimum wage tier (1, 2, 3, 4)",
                    "default": 1,
                },
                "include_kpcd": {
                    "type": "boolean",
                    "description": "Include trade union fee (2% employer contribution)",
                    "default": False,
                },
                "employee_id": {
                    "type": "string",
                    "description": "Optional employee identifier",
                    "default": "ADHOC",
                },
            },
            "required": ["salary"],
        },
    },
    {
        "name": "mekong_bhxh_employees",
        "description": "List registered employees for social insurance reporting and declarations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by employee status (active, all)",
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_bhxh_declaration",
        "description": "Generate statutory electronic declaration D02-LT (bao_tang, bao_giam, dieu_chinh_luong).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "change_type": {
                    "type": "string",
                    "description": "Declaration type (bao_tang, bao_giam, dieu_chinh_luong)",
                },
                "employee_id": {
                    "type": "string",
                    "description": "Employee ID (e.g. EMP-001)",
                },
                "effective_month": {
                    "type": "string",
                    "description": "Effective month (MM/YYYY)",
                    "default": "",
                },
                "new_salary": {
                    "type": "number",
                    "description": "Updated insurance salary if adjust salary",
                    "default": 0.0,
                },
                "note": {
                    "type": "string",
                    "description": "Optional declaration note",
                    "default": "",
                },
            },
            "required": ["change_type", "employee_id"],
        },
    },
    {
        "name": "mekong_bhxh_status",
        "description": "Retrieve Vietnamese social insurance regulatory status, contribution totals, and active employee metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_ocop_eval",
        "description": "Evaluate Vietnamese agricultural product OCOP star classification (1 to 5 stars) under Decision 148/QĐ-TTg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type": "string",
                    "description": "Name of agricultural product to evaluate",
                },
                "part_a": {
                    "type": "number",
                    "description": "Part A community & production score (max 35.0)",
                    "default": 30.0,
                },
                "part_b": {
                    "type": "number",
                    "description": "Part B marketing & commercialization score (max 25.0)",
                    "default": 22.0,
                },
                "part_c": {
                    "type": "number",
                    "description": "Part C quality & certification score (max 40.0)",
                    "default": 38.0,
                },
            },
            "required": ["product_name"],
        },
    },
    {
        "name": "mekong_ocop_products",
        "description": "Browse registered Vietnamese OCOP products, HS code classifications, and international certifications.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_stars": {
                    "type": "integer",
                    "description": "Filter by minimum star rating (1 to 5)",
                    "default": 1,
                },
                "province": {
                    "type": "string",
                    "description": "Filter by origin province (e.g. Sóc Trăng, Đắk Lắk, all)",
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_ocop_listing",
        "description": "Synthesize international B2B export marketplace listing and trade compliance audit (Alibaba, Amazon, Shopee).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "string",
                    "description": "Product ID (e.g. OCOP-ST25) or product name",
                },
                "target_market": {
                    "type": "string",
                    "description": "Target export market (EU, US, Japan, China, Middle East)",
                    "default": "EU",
                },
                "platform": {
                    "type": "string",
                    "description": "Target B2B e-commerce platform (alibaba, amazon, shopee)",
                    "default": "alibaba",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "mekong_ocop_compliance",
        "description": "Inspect technical trade barriers, tariff preferences under FTAs (EVFTA, CPTPP, RCEP), and required food safety certs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "description": "Destination market (EU, US, Japan, China, Middle East)",
                    "default": "EU",
                },
            },
            "required": ["market"],
        },
    },
    {
        "name": "mekong_ocop_status",
        "description": "Retrieve national OCOP program telemetry, star breakdown, and registered export listings.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_vietqr_generate",
        "description": "Construct EMVCo VietQR string and Napas 247 QuickLink for instant interbank fund transfers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "integer",
                    "description": "Transfer amount in VND (0 for dynamic/payer-entered)",
                    "default": 0,
                },
                "memo": {
                    "type": "string",
                    "description": "Transfer memo / reference content (e.g. MK-INV-1001)",
                    "default": "",
                },
                "bank": {
                    "type": "string",
                    "description": "Bank short code (MB, VCB, CTG, BIDV, TCB, ACB, TPB) or BIN",
                    "default": "MB",
                },
                "account_number": {
                    "type": "string",
                    "description": "Beneficiary account number (defaults to corporate configured account)",
                    "default": "",
                },
                "account_name": {
                    "type": "string",
                    "description": "Beneficiary account holder name",
                    "default": "",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_vietqr_banks",
        "description": "Lookup Vietnamese Napas 247 participant banks, BIN codes, and short names.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_vietqr_transactions",
        "description": "List recent incoming bank transfer transactions and payment reconciliation records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_vietqr_record",
        "description": "Record and reconcile an incoming bank payment transaction idempotently.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "bank_tx_id": {
                    "type": "string",
                    "description": "Unique bank transaction reference code",
                },
                "amount_vnd": {
                    "type": "integer",
                    "description": "Payment amount received in VND",
                },
                "memo": {
                    "type": "string",
                    "description": "Payment reference memo",
                    "default": "",
                },
                "bin_code": {
                    "type": "string",
                    "description": "Bank BIN code (defaults to 970422)",
                    "default": "970422",
                },
                "matched_order_id": {
                    "type": "string",
                    "description": "Associated internal invoice or order ID",
                    "default": "",
                },
            },
            "required": ["bank_tx_id", "amount_vnd"],
        },
    },
    {
        "name": "mekong_vietqr_status",
        "description": "Retrieve VietQR payment gateway status, default account, and volume metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_audit_run",
        "description": "Execute automated SOX 404, ITGC, and internal controls testing across all control domains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "framework": {
                    "type": "string",
                    "description": "Controls framework to test ('all', 'sox', 'itgc').",
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_audit_controls",
        "description": "Browse internal controls catalog, risk ratings, and validation procedures across AC, CM, CO, and SD domains.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Control domain filter ('all', 'AC', 'CM', 'CO', 'SD').",
                    "default": "all",
                },
                "framework": {
                    "type": "string",
                    "description": "Controls framework filter ('all', 'sox', 'itgc').",
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_audit_findings",
        "description": "Inspect open audit deficiencies, material weaknesses, and remediation action plans.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "min_severity": {
                    "type": "string",
                    "description": "Minimum severity level filter ('all', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW').",
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_audit_status",
        "description": "Retrieve executive internal controls audit posture, latest compliance score, and audit opinion.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_payroll_gross_to_net",
        "description": "Calculate Vietnamese Net take-home pay, employee insurance, PIT tax, and employer burden from Gross salary.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "gross": {
                    "type": "number",
                    "description": "Gross contractual salary in VND.",
                },
                "dependents": {
                    "type": "integer",
                    "description": "Number of dependents for family circumstance relief.",
                    "default": 0,
                },
                "region": {
                    "type": "integer",
                    "description": "Statutory minimum wage region (1, 2, 3, or 4).",
                    "default": 1,
                },
                "lunch_allowance": {
                    "type": "number",
                    "description": "Lunch allowance in VND (tax-exempt up to 730,000 VND).",
                    "default": 730000.0,
                },
            },
            "required": ["gross"],
        },
    },
    {
        "name": "mekong_payroll_net_to_gross",
        "description": "Convert desired Net take-home salary to required contractual Gross salary and employer cost.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "net": {
                    "type": "number",
                    "description": "Desired Net take-home pay in VND.",
                },
                "dependents": {
                    "type": "integer",
                    "description": "Number of dependents for family circumstance relief.",
                    "default": 0,
                },
                "region": {
                    "type": "integer",
                    "description": "Statutory minimum wage region (1, 2, 3, or 4).",
                    "default": 1,
                },
                "lunch_allowance": {
                    "type": "number",
                    "description": "Lunch allowance in VND (tax-exempt up to 730,000 VND).",
                    "default": 730000.0,
                },
            },
            "required": ["net"],
        },
    },
    {
        "name": "mekong_payroll_payslip",
        "description": "Generate and persist an itemized electronic payslip for an employee.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "employee_name": {
                    "type": "string",
                    "description": "Full legal name of the employee.",
                },
                "gross": {
                    "type": "number",
                    "description": "Gross contractual salary in VND.",
                },
                "employee_id": {
                    "type": "string",
                    "description": "Employee ID code.",
                    "default": "",
                },
                "month": {
                    "type": "string",
                    "description": "Pay period in YYYY-MM format.",
                    "default": "",
                },
                "dependents": {
                    "type": "integer",
                    "description": "Number of dependents for relief.",
                    "default": 0,
                },
                "region": {
                    "type": "integer",
                    "description": "Statutory minimum wage region (1-4).",
                    "default": 1,
                },
                "bonus": {
                    "type": "number",
                    "description": "Performance bonus or additional compensation.",
                    "default": 0.0,
                },
            },
            "required": ["employee_name", "gross"],
        },
    },
    {
        "name": "mekong_payroll_list",
        "description": "Query historical electronic payslips and compensation disbursement records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "month": {
                    "type": "string",
                    "description": "Filter by pay period (YYYY-MM).",
                    "default": "",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return.",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_payroll_status",
        "description": "Retrieve Vietnamese payroll system status, statutory parameters, and total disburse metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_corporate_charter",
        "description": "Synthesize a complete 10-chapter Corporate Charter (Điều lệ công ty) complying with Article 24 Law on Enterprises 2020.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Full registered company name.",
                },
                "entity_type": {
                    "type": "string",
                    "description": "Corporate form ('TNHH_1TV', 'TNHH_2TV', 'JSC').",
                    "default": "TNHH_1TV",
                },
                "charter_capital": {
                    "type": "integer",
                    "description": "Charter capital in VND.",
                    "default": 1000000000,
                },
                "legal_rep_name": {
                    "type": "string",
                    "description": "Full name of legal representative.",
                    "default": "Nguyễn Văn A",
                },
                "address": {
                    "type": "string",
                    "description": "Headquarters address.",
                    "default": "Hà Nội, Việt Nam",
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "mekong_corporate_resolution",
        "description": "Draft statutory Board / Member Council resolution and meeting minutes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Company name.",
                },
                "resolution_type": {
                    "type": "string",
                    "description": "Type of resolution ('APPOINTMENT', 'CAPITAL_INCREASE', 'BRANCH').",
                    "default": "APPOINTMENT",
                },
                "title": {
                    "type": "string",
                    "description": "Optional custom resolution title.",
                    "default": "",
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "mekong_corporate_dossier",
        "description": "Synthesize complete statutory business incorporation dossier under Decree 01/2021/NĐ-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Company name to incorporate.",
                },
                "entity_type": {
                    "type": "string",
                    "description": "Corporate entity form ('TNHH_1TV', 'TNHH_2TV', 'JSC').",
                    "default": "TNHH_1TV",
                },
                "charter_capital": {
                    "type": "integer",
                    "description": "Charter capital in VND.",
                    "default": 1000000000,
                },
                "legal_rep_name": {
                    "type": "string",
                    "description": "Legal representative full name.",
                    "default": "Nguyễn Văn A",
                },
                "address": {
                    "type": "string",
                    "description": "Headquarters address.",
                    "default": "Hà Nội, Việt Nam",
                },
                "main_industry": {
                    "type": "string",
                    "description": "Primary VSIC economic industry code.",
                    "default": "6201",
                },
            },
            "required": ["company_name"],
        },
    },
    {
        "name": "mekong_corporate_list",
        "description": "Query historical corporate filings, charters, and statutory governance documents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum records to return.",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_corporate_status",
        "description": "Retrieve corporate governance engine metrics, registered entity counts, and legal framework.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_fdi_market_access",
        "description": "Evaluate foreign ownership limits, market access conditions, and international treaties (WTO/CPTPP/EVFTA).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sector_code": {
                    "type": "string",
                    "description": "VSIC or CPC sector code (e.g. 6201, 6202, 6311, 4651, 6810, 8411).",
                },
                "investor_nationality": {
                    "type": "string",
                    "description": "Investor country of origin ISO code (default: US).",
                },
                "ownership_pct": {
                    "type": "number",
                    "description": "Desired foreign equity ownership percentage (default: 100.0).",
                },
            },
            "required": ["sector_code"],
        },
    },
    {
        "name": "mekong_fdi_remittance",
        "description": "Verify offshore profit remittance eligibility, statutory DICA account, tax clearance, and legal reserve rules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fiscal_year": {
                    "type": "integer",
                    "description": "Fiscal year of audited profits.",
                },
                "audited_profit_vnd": {
                    "type": "number",
                    "description": "Audited net profit after tax in VND.",
                },
                "tax_cleared": {
                    "type": "boolean",
                    "description": "Whether corporate income tax and obligations are fully cleared.",
                },
                "retained_reserve_pct": {
                    "type": "number",
                    "description": "Percentage allocated to statutory reserve fund (default: 5.0).",
                },
                "dica_verified": {
                    "type": "boolean",
                    "description": "Whether Direct Investment Capital Account (DICA) is verified at authorized bank.",
                },
                "losses_carried_forward_vnd": {
                    "type": "number",
                    "description": "Accumulated losses carried forward in VND.",
                },
            },
            "required": ["fiscal_year", "audited_profit_vnd"],
        },
    },
    {
        "name": "mekong_fdi_foreign_loan",
        "description": "Evaluate offshore foreign loan compliance, SBV registration triggers, and foreign debt ceiling limit.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "loan_amount": {
                    "type": "number",
                    "description": "Foreign loan principal amount.",
                },
                "currency": {
                    "type": "string",
                    "description": "Foreign currency ISO code (default: USD).",
                },
                "tenure_months": {
                    "type": "integer",
                    "description": "Loan duration in months (tenure > 12 requires SBV registration).",
                },
                "interest_rate_pct": {
                    "type": "number",
                    "description": "Annual interest rate percentage.",
                },
                "project_capital_gap": {
                    "type": "number",
                    "description": "Project investment gap (Total Investment - Charter Capital).",
                },
            },
            "required": ["loan_amount"],
        },
    },
    {
        "name": "mekong_fdi_irc",
        "description": "Synthesize statutory Investment Registration Certificate (IRC) application dossier under Law on Investment 2020.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "FDI Project name.",
                },
                "sector_code": {
                    "type": "string",
                    "description": "VSIC industry code (e.g. 6201).",
                },
                "total_investment_vnd": {
                    "type": "number",
                    "description": "Total investment capital in VND.",
                },
                "investor_name": {
                    "type": "string",
                    "description": "Foreign corporate or individual investor legal name.",
                },
                "investor_country": {
                    "type": "string",
                    "description": "Investor country of origin (default: US).",
                },
                "project_location": {
                    "type": "string",
                    "description": "Project registered execution location in Vietnam.",
                },
            },
            "required": ["project_name", "sector_code", "total_investment_vnd", "investor_name"],
        },
    },
    {
        "name": "mekong_fdi_status",
        "description": "Retrieve FDI & SBV capital compliance engine metrics, registered projects, and legal framework.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_ip_trademark",
        "description": "Register a trademark application conforming to Nice Classification 12-2024 and Law on Intellectual Property.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mark_name": {
                    "type": "string",
                    "description": "Name of trademark to register.",
                },
                "nice_class": {
                    "type": "string",
                    "description": "Nice classification code (e.g. 09, 35, 36, 38, 41, 42, 45).",
                },
                "applicant_name": {
                    "type": "string",
                    "description": "Applicant / owner name.",
                },
                "goods_services_spec": {
                    "type": "string",
                    "description": "Itemized list of goods and services covered.",
                },
            },
            "required": ["mark_name"],
        },
    },
    {
        "name": "mekong_ip_search",
        "description": "Search phonetical and orthographical trademark conflicts and assess likelihood of confusion under Article 74.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mark_name": {
                    "type": "string",
                    "description": "Query trademark name to evaluate.",
                },
                "nice_class": {
                    "type": "string",
                    "description": "Target Nice class (default: 09).",
                },
            },
            "required": ["mark_name"],
        },
    },
    {
        "name": "mekong_ip_patent",
        "description": "Draft statutory patent specification and independent/dependent claims under Article 102 Law on IP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Invention / technical title.",
                },
                "technical_field": {
                    "type": "string",
                    "description": "Technical domain of the invention.",
                },
                "applicant_name": {
                    "type": "string",
                    "description": "Patent applicant organization or individual.",
                },
                "independent_claims": {
                    "type": "integer",
                    "description": "Number of independent claims to draft (default: 1).",
                },
                "dependent_claims": {
                    "type": "integer",
                    "description": "Number of dependent claims to draft (default: 2).",
                },
            },
            "required": ["title", "technical_field"],
        },
    },
    {
        "name": "mekong_ip_copyright",
        "description": "Synthesize software computer program copyright registration dossier under Decree 17/2023/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "software_name": {
                    "type": "string",
                    "description": "Name of computer software / program.",
                },
                "author_name": {
                    "type": "string",
                    "description": "Author / software creator legal name.",
                },
                "version": {
                    "type": "string",
                    "description": "Software version (default: 1.0.0).",
                },
                "repository_url": {
                    "type": "string",
                    "description": "VCS repository URL (optional).",
                },
                "lines_of_code": {
                    "type": "integer",
                    "description": "Lines of source code (default: 10000).",
                },
            },
            "required": ["software_name", "author_name"],
        },
    },
    {
        "name": "mekong_ip_fees",
        "description": "Calculate itemized state official IP registration fees under Circular 263/2016/TT-BTC.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "trademark_classes": {
                    "type": "integer",
                    "description": "Number of trademark Nice classes (default: 1).",
                },
                "patent_claims": {
                    "type": "integer",
                    "description": "Number of independent patent claims (default: 1).",
                },
                "software_copyrights": {
                    "type": "integer",
                    "description": "Number of software copyright certificates (default: 1).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_ip_status",
        "description": "Retrieve IP engine telemetry, Nice classification support, and registered asset counts.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_customs_hs_lookup",
        "description": "Look up 8-digit AHTN HS code tariff rates, MFN duty, import VAT, and preferential FTA rates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hs_code": {
                    "type": "string",
                    "description": "8-digit AHTN HS code (e.g. 8471.30.20).",
                },
                "fta": {
                    "type": "string",
                    "description": "Applicable FTA or tariff framework (MFN, EVFTA, CPTPP, ATIGA, ACFTA, VKFTA).",
                },
            },
            "required": ["hs_code"],
        },
    },
    {
        "name": "mekong_customs_duty_calc",
        "description": "Calculate itemized CIF valuation, import duty, and import VAT obligations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "invoice_value_usd": {
                    "type": "number",
                    "description": "Invoice commercial value in USD.",
                },
                "hs_code": {
                    "type": "string",
                    "description": "8-digit AHTN HS code (default: 8471.30.20).",
                },
                "freight_usd": {
                    "type": "number",
                    "description": "International freight cost in USD.",
                },
                "insurance_usd": {
                    "type": "number",
                    "description": "Marine/cargo insurance cost in USD.",
                },
                "fta": {
                    "type": "string",
                    "description": "Applicable FTA tariff schedule (MFN, EVFTA, CPTPP, ATIGA).",
                },
            },
            "required": ["invoice_value_usd"],
        },
    },
    {
        "name": "mekong_customs_channel",
        "description": "Evaluate VNACCS automated risk criteria and determine Green, Yellow, or Red customs channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_tax_id": {
                    "type": "string",
                    "description": "10-digit Vietnamese Enterprise Tax Identification Number (MST).",
                },
                "hs_code": {
                    "type": "string",
                    "description": "8-digit AHTN HS code.",
                },
                "invoice_value_usd": {
                    "type": "number",
                    "description": "Commercial invoice value in USD.",
                },
                "origin_country": {
                    "type": "string",
                    "description": "Country of origin ISO code (default: US).",
                },
                "compliance_tier": {
                    "type": "string",
                    "description": "Customs compliance rating (TIER_1_PRIORITY, TIER_2_NORMAL, TIER_3_WATCHLIST).",
                },
                "has_valid_co": {
                    "type": "boolean",
                    "description": "Whether a valid Certificate of Origin is provided.",
                },
            },
            "required": ["enterprise_tax_id", "hs_code", "invoice_value_usd"],
        },
    },
    {
        "name": "mekong_customs_declare",
        "description": "Synthesize and submit a formal VNACCS/VCIS electronic customs declaration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_tax_id": {
                    "type": "string",
                    "description": "10-digit Vietnamese Enterprise Tax Identification Number (MST).",
                },
                "hs_code": {
                    "type": "string",
                    "description": "8-digit AHTN HS code.",
                },
                "commodity_name": {
                    "type": "string",
                    "description": "Commercial description of commodity.",
                },
                "invoice_value_usd": {
                    "type": "number",
                    "description": "Commercial invoice value in USD.",
                },
                "origin_country": {
                    "type": "string",
                    "description": "Country of origin ISO code (default: US).",
                },
                "declaration_type": {
                    "type": "string",
                    "description": "Customs declaration type (IMPORT_BUSINESS, EXPORT_BUSINESS).",
                },
                "compliance_tier": {
                    "type": "string",
                    "description": "Customs compliance rating.",
                },
                "has_valid_co": {
                    "type": "boolean",
                    "description": "Whether a valid Certificate of Origin is provided.",
                },
            },
            "required": ["enterprise_tax_id", "hs_code", "commodity_name", "invoice_value_usd"],
        },
    },
    {
        "name": "mekong_customs_origin",
        "description": "Verify Rules of Origin (RVC >= 40% and CTC criteria) for preferential C/O certification.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "form_type": {
                    "type": "string",
                    "description": "Certificate of Origin Form (EUR.1, CPTPP, D, E, B).",
                },
                "hs_code": {
                    "type": "string",
                    "description": "8-digit AHTN HS code of finished product.",
                },
                "fob_value_usd": {
                    "type": "number",
                    "description": "FOB export transaction price in USD.",
                },
                "non_originating_value_usd": {
                    "type": "number",
                    "description": "Value of non-originating / imported raw materials in USD.",
                },
                "exporter_name": {
                    "type": "string",
                    "description": "Vietnamese exporter registered name.",
                },
                "importer_country": {
                    "type": "string",
                    "description": "Destination country ISO code (default: DE).",
                },
            },
            "required": ["form_type", "hs_code", "fob_value_usd"],
        },
    },
    {
        "name": "mekong_customs_status",
        "description": "Retrieve customs engine telemetry, VNACCS channel distribution, and total duty collected.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_contract_draft",
        "description": "Synthesize standard commercial contract complying with Vietnamese law (SOFTWARE_DEV, COMMERCIAL_SALE, NDA, DISTRIBUTION).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "description": "Template key (SOFTWARE_DEV, COMMERCIAL_SALE, NDA, DISTRIBUTION).",
                },
                "party_a_name": {
                    "type": "string",
                    "description": "Name of Party A (Client / Buyer).",
                },
                "party_b_name": {
                    "type": "string",
                    "description": "Name of Party B (Vendor / Seller).",
                },
                "contract_value_vnd": {
                    "type": "number",
                    "description": "Total contract value in VND.",
                },
                "party_a_tax_id": {
                    "type": "string",
                    "description": "Tax Identification Number of Party A.",
                },
                "party_b_tax_id": {
                    "type": "string",
                    "description": "Tax Identification Number of Party B.",
                },
                "scope_summary": {
                    "type": "string",
                    "description": "Summary scope of work or deliverables.",
                },
                "penalty_rate_pct": {
                    "type": "number",
                    "description": "Breach penalty percentage (statutory cap: 8.0%).",
                },
                "dispute_forum": {
                    "type": "string",
                    "description": "Dispute resolution forum (VIAC or Court).",
                },
            },
            "required": ["template_type", "party_a_name", "party_b_name"],
        },
    },
    {
        "name": "mekong_contract_risk_check",
        "description": "Scan contract clauses for legal risks, penalty breach (>8%), missing force majeure, and redline recommendations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_text": {
                    "type": "string",
                    "description": "Full contract text or clause excerpt to evaluate.",
                },
                "penalty_pct": {
                    "type": "number",
                    "description": "Agreed penalty rate percentage to verify against statutory 8% cap.",
                },
            },
            "required": ["contract_text"],
        },
    },
    {
        "name": "mekong_contract_sign",
        "description": "Sign a commercial contract electronically with cryptographic SHA-256 digest and TSA timestamp under Law on Electronic Transactions 2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "Contract identifier or contract number.",
                },
                "signer_name": {
                    "type": "string",
                    "description": "Legal representative full name.",
                },
                "signer_title": {
                    "type": "string",
                    "description": "Title/position of signer (default: Giám đốc điều hành).",
                },
                "signer_tax_id": {
                    "type": "string",
                    "description": "Tax ID of signing enterprise.",
                },
                "organization_name": {
                    "type": "string",
                    "description": "Signing enterprise registered name.",
                },
            },
            "required": ["contract_id", "signer_name"],
        },
    },
    {
        "name": "mekong_contract_verify",
        "description": "Verify authenticity, integrity, and timestamp of an electronic contract signature.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "signature_id": {
                    "type": "string",
                    "description": "Electronic signature ID or signature hash.",
                },
            },
            "required": ["signature_id"],
        },
    },
    {
        "name": "mekong_contract_list",
        "description": "Query historical commercial contracts and execution/signing status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Status filter (ALL, DRAFTED, SIGNED).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 20).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_contract_status",
        "description": "Retrieve contract engine telemetry, active e-signatures, template catalog, and risk metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_tender_method",
        "description": "Evaluate and advise statutory procurement method (Open Bidding, Direct Contracting, Competitive Quotation) under Bidding Law 2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package_type": {
                    "type": "string",
                    "description": "Procurement category (GOODS, CONSULTING, WORKS, NON_CONSULTING).",
                },
                "budget_vnd": {
                    "type": "number",
                    "description": "Approved budget / package estimate in VND.",
                },
                "urgent": {
                    "type": "boolean",
                    "description": "Whether package is urgent disaster relief / disease prevention.",
                },
                "proprietary": {
                    "type": "boolean",
                    "description": "Whether package requires proprietary tech or unique IP.",
                },
            },
            "required": ["package_type", "budget_vnd"],
        },
    },
    {
        "name": "mekong_tender_create",
        "description": "Synthesize and publish an electronic tender dossier (E-HSMT) on National E-GP under Decree 24/2024/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package_name": {
                    "type": "string",
                    "description": "Official bidding package name.",
                },
                "procuring_entity": {
                    "type": "string",
                    "description": "Procuring agency, ministry, or state enterprise name.",
                },
                "budget_vnd": {
                    "type": "number",
                    "description": "Approved procurement budget in VND.",
                },
                "package_type": {
                    "type": "string",
                    "description": "Package type (GOODS, CONSULTING, WORKS, NON_CONSULTING).",
                },
                "procurement_method": {
                    "type": "string",
                    "description": "Procurement method (OPEN_BIDDING, DIRECT_CONTRACTING, COMPETITIVE_QUOTATION).",
                },
                "submission_days": {
                    "type": "integer",
                    "description": "Bid submission period in calendar days (default: 15).",
                },
            },
            "required": ["package_name", "procuring_entity", "budget_vnd"],
        },
    },
    {
        "name": "mekong_tender_eval",
        "description": "Execute statutory 4-step E-HSDT bid evaluation (eligibility, capacity/experience, technical floor, financial/savings).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tender_id": {
                    "type": "string",
                    "description": "Tender package ID or package number.",
                },
                "bidder_name": {
                    "type": "string",
                    "description": "Name of bidding enterprise or consortium.",
                },
                "bid_price_vnd": {
                    "type": "number",
                    "description": "Bid submission price in VND.",
                },
                "bidder_tax_id": {
                    "type": "string",
                    "description": "Enterprise tax identification number (MST).",
                },
                "revenue_3yr_avg_vnd": {
                    "type": "number",
                    "description": "3-year average annual revenue in VND.",
                },
                "similar_contract_val_vnd": {
                    "type": "number",
                    "description": "Value of highest executed similar contract in VND.",
                },
                "tech_score": {
                    "type": "number",
                    "description": "Technical evaluation score (0-100, floor: 70).",
                },
                "has_valid_security": {
                    "type": "boolean",
                    "description": "Whether bidder submitted valid bank bid guarantee/bond.",
                },
            },
            "required": ["tender_id", "bidder_name", "bid_price_vnd"],
        },
    },
    {
        "name": "mekong_tender_collusion_scan",
        "description": "Scan submitted tender bids for anti-competitive collusion, abnormal price clustering, and affiliate conflicts under Article 16 Bidding Law 2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tender_id": {
                    "type": "string",
                    "description": "Tender package identifier to scan.",
                },
            },
            "required": ["tender_id"],
        },
    },
    {
        "name": "mekong_tender_list",
        "description": "Query registered tender packages and active biddings on National E-GP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Status filter (ALL, PUBLISHED, EVALUATED, CLOSED).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of packages to return (default: 20).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_tender_status",
        "description": "Retrieve public procurement telemetry, budget, savings rate, and E-GP bidding metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_realestate_finance",
        "description": "Calculate complete commercial/industrial leasing cash flow schedule, security deposit, and total value.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Property type (COMMERCIAL_OFFICE, INDUSTRIAL_LAND, READY_BUILT_FACTORY, BUILT_TO_SUIT).",
                },
                "area_sqm": {
                    "type": "number",
                    "description": "Leased area in square meters.",
                },
                "unit_rent_usd": {
                    "type": "number",
                    "description": "Base rent in USD per sqm per month.",
                },
                "lease_term_months": {
                    "type": "integer",
                    "description": "Lease term in months (default: 36).",
                },
                "maintenance_fee_usd": {
                    "type": "number",
                    "description": "Management fee in USD per sqm per month (default: 0.5).",
                },
                "deposit_months": {
                    "type": "integer",
                    "description": "Security deposit in months of rent (default: 3).",
                },
                "annual_escalation_pct": {
                    "type": "number",
                    "description": "Annual rent escalation percentage (default: 3.0).",
                },
            },
            "required": ["category", "area_sqm", "unit_rent_usd"],
        },
    },
    {
        "name": "mekong_realestate_density",
        "description": "Validate industrial/commercial site density (<=70%) and green space ratio (>=10%) against QCVN 01:2021/BXD.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lot_area_sqm": {
                    "type": "number",
                    "description": "Total lot area in square meters.",
                },
                "building_footprint_sqm": {
                    "type": "number",
                    "description": "Total building footprint / ground floor area in sqm.",
                },
                "green_space_sqm": {
                    "type": "number",
                    "description": "Landscaped green space area in sqm.",
                },
                "building_height_tier": {
                    "type": "string",
                    "description": "Building height tier (UP_TO_12M, UP_TO_20M, UP_TO_30M, UP_TO_40M, OVER_40M).",
                },
            },
            "required": ["lot_area_sqm", "building_footprint_sqm", "green_space_sqm"],
        },
    },
    {
        "name": "mekong_realestate_audit",
        "description": "Audit legal title, construction readiness, fire safety cert, and statutory conditions for real estate leasing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Project name or industrial park lot identifier.",
                },
                "category": {
                    "type": "string",
                    "description": "Property category (INDUSTRIAL_LAND, READY_BUILT_FACTORY, COMMERCIAL_OFFICE, BUILT_TO_SUIT).",
                },
                "land_area_sqm": {
                    "type": "number",
                    "description": "Total land / property area in sqm.",
                },
                "has_land_cert": {
                    "type": "boolean",
                    "description": "Whether property has valid Land Use Right Certificate (So Hong).",
                },
                "has_construction_permit": {
                    "type": "boolean",
                    "description": "Whether property has valid construction permit / as-built approval.",
                },
                "has_fire_safety_cert": {
                    "type": "boolean",
                    "description": "Whether building has statutory fire safety certificate.",
                },
                "tenure_remaining_years": {
                    "type": "number",
                    "description": "Remaining land lease term in years.",
                },
                "payment_term": {
                    "type": "string",
                    "description": "Payment term (ANNUAL_RENT, LUMP_SUM_RENT).",
                },
                "has_disputes": {
                    "type": "boolean",
                    "description": "Whether property is under active legal dispute.",
                },
                "is_mortgaged_to_bank": {
                    "type": "boolean",
                    "description": "Whether property is mortgaged to a credit institution.",
                },
            },
            "required": ["project_name", "category", "land_area_sqm"],
        },
    },
    {
        "name": "mekong_realestate_draft",
        "description": "Synthesize a complete commercial/industrial lease agreement complying with Decree 96/2024/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "property_id": {
                    "type": "string",
                    "description": "Property identifier or cadastral parcel ID.",
                },
                "lessor_name": {
                    "type": "string",
                    "description": "Lessor / landlord organization name.",
                },
                "lessee_name": {
                    "type": "string",
                    "description": "Lessee / tenant organization name.",
                },
                "leased_area_sqm": {
                    "type": "number",
                    "description": "Contractual leased area in sqm.",
                },
                "unit_rent_usd": {
                    "type": "number",
                    "description": "Base unit rent in USD per sqm per month.",
                },
                "lease_term_months": {
                    "type": "integer",
                    "description": "Lease term in months (default: 36).",
                },
                "maintenance_fee_usd": {
                    "type": "number",
                    "description": "Management fee in USD per sqm per month (default: 0.5).",
                },
                "deposit_months": {
                    "type": "integer",
                    "description": "Security deposit in months (default: 3).",
                },
                "dispute_resolution": {
                    "type": "string",
                    "description": "Arbitration or court forum (VIAC, COURT).",
                },
            },
            "required": ["property_id", "lessor_name", "lessee_name", "leased_area_sqm", "unit_rent_usd"],
        },
    },
    {
        "name": "mekong_realestate_list",
        "description": "Query registered real estate properties and industrial parks.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category filter (ALL, INDUSTRIAL_LAND, COMMERCIAL_OFFICE, etc.).",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 20).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_realestate_status",
        "description": "Retrieve commercial real estate engine telemetry, total managed area, active leases, and metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_esg_ghg",
        "description": "Compute enterprise greenhouse gas (GHG) emissions inventory across Scope 1, 2, 3 under ISO 14064-1 & Decision 13/2024/QD-TTg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_name": {
                    "type": "string",
                    "description": "Name of enterprise or manufacturing facility.",
                },
                "reporting_year": {
                    "type": "integer",
                    "description": "Reporting calendar year (e.g. 2026).",
                },
                "fuel_diesel_liters": {
                    "type": "number",
                    "description": "Liters of diesel consumed (Scope 1).",
                },
                "fuel_gasoline_liters": {
                    "type": "number",
                    "description": "Liters of gasoline consumed (Scope 1).",
                },
                "coal_tons": {
                    "type": "number",
                    "description": "Tons of coal consumed (Scope 1).",
                },
                "lpg_kg": {
                    "type": "number",
                    "description": "Kilograms of LPG consumed (Scope 1).",
                },
                "electricity_kwh": {
                    "type": "number",
                    "description": "Kilowatt-hours of national grid electricity consumed (Scope 2).",
                },
                "scope3_logistics_tco2e": {
                    "type": "number",
                    "description": "Tons of CO2e from value chain, logistics, and supply chain (Scope 3).",
                },
            },
            "required": ["enterprise_name", "reporting_year"],
        },
    },
    {
        "name": "mekong_esg_cbam",
        "description": "Evaluate EU CBAM embedded emissions and financial certificate liability for Vietnam exports (Regulation EU 2023/956).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "description": "CBAM covered product (STEEL, ALUMINUM, CEMENT, FERTILIZER, HYDROGEN).",
                },
                "export_volume_tons": {
                    "type": "number",
                    "description": "Metric tons of product exported to the European Union.",
                },
                "direct_emissions_tco2": {
                    "type": "number",
                    "description": "Direct production emissions (Scope 1) in tCO2e.",
                },
                "indirect_emissions_tco2": {
                    "type": "number",
                    "description": "Indirect emissions from electricity consumption in tCO2e.",
                },
                "cbam_carbon_price_eur_per_ton": {
                    "type": "number",
                    "description": "Projected EU ETS carbon allowance price in EUR/ton (default: 75.0).",
                },
            },
            "required": ["product_type", "export_volume_tons", "direct_emissions_tco2"],
        },
    },
    {
        "name": "mekong_esg_audit",
        "description": "Audit and synthesize corporate ESG composite score and rating under Circular 96/2020/TT-BTC & GRI standards.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_name": {
                    "type": "string",
                    "description": "Name of audited corporation or listed enterprise.",
                },
                "has_iso_14001": {
                    "type": "boolean",
                    "description": "Has certified ISO 14001 environmental management system (default: True).",
                },
                "renewable_energy_ratio_pct": {
                    "type": "number",
                    "description": "Percentage of energy sourced from renewables (default: 20.0).",
                },
                "has_waste_treatment_license": {
                    "type": "boolean",
                    "description": "Possesses valid environmental discharge/waste treatment permit (default: True).",
                },
                "full_social_insurance_compliance": {
                    "type": "boolean",
                    "description": "100% compliance with statutory BHXH, BHYT, BHTN for workforce (default: True).",
                },
                "workplace_accident_rate": {
                    "type": "number",
                    "description": "Occupational accident frequency rate per million hours worked (default: 0.0).",
                },
                "female_leadership_ratio_pct": {
                    "type": "number",
                    "description": "Percentage of women in managerial / board positions (default: 30.0).",
                },
                "independent_board_members_ratio_pct": {
                    "type": "number",
                    "description": "Percentage of independent non-executive board directors (default: 33.3).",
                },
                "has_anti_corruption_policy": {
                    "type": "boolean",
                    "description": "Established anti-bribery, ethics, and whistleblower protections (default: True).",
                },
                "has_audited_financial_report": {
                    "type": "boolean",
                    "description": "Annual financial statements audited by accredited auditing firm (default: True).",
                },
            },
            "required": ["enterprise_name"],
        },
    },
    {
        "name": "mekong_esg_carbon_trade",
        "description": "Execute carbon credit transaction or offset surrender under Articles 93 & 94 Environmental Law 2020.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Originating green mitigation project name (e.g. Mangrove Reforestation Ca Mau).",
                },
                "credit_type": {
                    "type": "string",
                    "description": "Carbon standard / credit classification (VCS, GS, CDM, I-REC).",
                },
                "quantity_tco2e": {
                    "type": "number",
                    "description": "Quantity of carbon credits in metric tons of CO2 equivalent.",
                },
                "unit_price_usd": {
                    "type": "number",
                    "description": "Price per carbon credit unit in USD.",
                },
                "action": {
                    "type": "string",
                    "description": "Trade action (BUY, SELL, OFFSET). Default: BUY.",
                },
                "counterparty": {
                    "type": "string",
                    "description": "Trading exchange or counterparty enterprise.",
                },
            },
            "required": ["project_name", "credit_type", "quantity_tco2e", "unit_price_usd"],
        },
    },
    {
        "name": "mekong_esg_list",
        "description": "Query registered enterprise GHG inventories and carbon transaction ledger.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of records to return (default: 20).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "mekong_esg_status",
        "description": "Retrieve ESG compliance telemetry, tracked emissions, carbon trades, and green metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_supplychain_plot",
        "description": "Register agricultural or forestry production plot with EUDR coordinates (Regulation EU 2023/1115).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "farmer_name": {
                    "type": "string",
                    "description": "Name of farmer, plantation owner, or forestry holder.",
                },
                "province": {
                    "type": "string",
                    "description": "Vietnamese province (e.g. Đắk Lắk, Lâm Đồng, Gia Lai).",
                },
                "commodity": {
                    "type": "string",
                    "description": "Covered commodity (COFFEE, RUBBER, TIMBER_WOOD, COCOA, PALM_OIL, SOYA, CATTLE).",
                },
                "latitude": {
                    "type": "number",
                    "description": "GPS latitude in decimal degrees (e.g. 12.6667).",
                },
                "longitude": {
                    "type": "number",
                    "description": "GPS longitude in decimal degrees (e.g. 108.0333).",
                },
                "area_hectares": {
                    "type": "number",
                    "description": "Total plot area in hectares.",
                },
                "district": {
                    "type": "string",
                    "description": "District or administrative ward.",
                },
                "deforestation_free_post_2020": {
                    "type": "boolean",
                    "description": "Certified zero deforestation after 31/12/2020 cut-off date (default: True).",
                },
                "legal_land_cert": {
                    "type": "string",
                    "description": "Land tenure certificate or statutory forestry permit reference.",
                },
            },
            "required": ["farmer_name", "province", "commodity", "latitude", "longitude", "area_hectares"],
        },
    },
    {
        "name": "mekong_supplychain_batch",
        "description": "Initialize export traceability batch with plot linkage and SHA-256 fingerprint.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_code": {
                    "type": "string",
                    "description": "Unique export batch or lot number.",
                },
                "commodity": {
                    "type": "string",
                    "description": "Commodity classification (COFFEE, RUBBER, TIMBER_WOOD, ...).",
                },
                "quantity_kg": {
                    "type": "number",
                    "description": "Total net volume/weight in kilograms.",
                },
                "processor_name": {
                    "type": "string",
                    "description": "Processing facility or exporter name.",
                },
                "plot_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of origin production plot IDs.",
                },
                "certifications": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of sustainability/quality certifications (VIETGAP, 4C, FSC, PEFC, VFCS).",
                },
            },
            "required": ["batch_code", "commodity", "quantity_kg", "processor_name"],
        },
    },
    {
        "name": "mekong_supplychain_event",
        "description": "Record EPCIS custody transfer event with cryptographic hash chaining (GS1 EPCIS 2.0).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_code": {
                    "type": "string",
                    "description": "Traceability batch code.",
                },
                "event_type": {
                    "type": "string",
                    "description": "EPCIS event type (HARVEST, COLLECT, PROCESS, AGGREGATE, QUALITY_INSPECT, PACK, CUSTOMS_CLEAR, SHIP).",
                },
                "location": {
                    "type": "string",
                    "description": "Physical facility or port location.",
                },
                "actor_name": {
                    "type": "string",
                    "description": "Entity or inspector performing the custody action.",
                },
                "notes": {
                    "type": "string",
                    "description": "Operational notes, moisture readings, or container numbers.",
                },
            },
            "required": ["batch_code", "event_type", "location", "actor_name"],
        },
    },
    {
        "name": "mekong_supplychain_eudr",
        "description": "Synthesize official EUDR Due Diligence Statement (DDS) dossier for EU export customs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_code": {
                    "type": "string",
                    "description": "Export batch code to certify.",
                },
                "exporter_name": {
                    "type": "string",
                    "description": "Vietnamese exporter operator name.",
                },
                "importer_name": {
                    "type": "string",
                    "description": "EU importer enterprise name.",
                },
                "destination_country": {
                    "type": "string",
                    "description": "Destination EU member state (default: Germany).",
                },
            },
            "required": ["batch_code", "exporter_name", "importer_name"],
        },
    },
    {
        "name": "mekong_supplychain_trace",
        "description": "Retrieve complete end-to-end provenance timeline and custody chain for an export batch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_code": {
                    "type": "string",
                    "description": "Traceability batch code to query.",
                },
            },
            "required": ["batch_code"],
        },
    },
    {
        "name": "mekong_supplychain_status",
        "description": "Retrieve supply chain engine telemetry, monitored area, and volume metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_labor_permit",
        "description": "Assess foreign worker eligibility for work permit or statutory exemption under Decree 152/2020 & 70/2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "worker_name": {"type": "string", "description": "Foreign employee full name."},
                "nationality": {"type": "string", "description": "Country of citizenship."},
                "position": {"type": "string", "description": "Job category: EXPERT, EXECUTIVE_DIRECTOR, MANAGING_DIRECTOR, TECHNICAL_WORKER."},
                "job_title": {"type": "string", "description": "Specific job appointment title."},
                "degree": {"type": "string", "description": "Educational degree qualification.", "default": "BACHELOR"},
                "exp": {"type": "number", "description": "Relevant professional experience in years.", "default": 3.0},
                "capital": {"type": "number", "description": "Capital contribution in VND.", "default": 0.0},
                "wto": {"type": "boolean", "description": "Internal transfer in 11 WTO committed service sectors.", "default": False},
                "married_vn": {"type": "boolean", "description": "Married to a Vietnamese citizen.", "default": False},
                "passport": {"type": "string", "description": "Passport number.", "default": "PASS-DEFAULT"},
            },
            "required": ["worker_name", "nationality", "position", "job_title"],
        },
    },
    {
        "name": "mekong_labor_overtime",
        "description": "Calculate statutory overtime pay and night shift rates under Labor Code 2019 Article 98.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "hourly_rate": {"type": "number", "description": "Base hourly wage rate in VND."},
                "weekday_ot": {"type": "number", "description": "Normal weekday overtime hours (150%).", "default": 0.0},
                "weekend_ot": {"type": "number", "description": "Weekend rest day overtime hours (200%).", "default": 0.0},
                "holiday_ot": {"type": "number", "description": "Public holiday / Tet overtime hours (300%).", "default": 0.0},
                "night_regular": {"type": "number", "description": "Night shift regular hours (+30%).", "default": 0.0},
                "night_ot": {"type": "number", "description": "Night shift overtime hours (200%).", "default": 0.0},
            },
            "required": ["hourly_rate"],
        },
    },
    {
        "name": "mekong_labor_caps",
        "description": "Audit monthly and annual overtime working hours against Article 107 statutory limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "Employee identifier code."},
                "employee_name": {"type": "string", "description": "Employee full name."},
                "monthly_ot_hours": {"type": "number", "description": "Overtime hours worked in current month."},
                "yearly_cumulative_hours": {"type": "number", "description": "Cumulative overtime hours in current calendar year."},
                "industry": {"type": "string", "description": "Industry classification.", "default": "GENERAL"},
                "exceptional": {"type": "boolean", "description": "Eligible for 300h extended overtime category.", "default": False},
            },
            "required": ["employee_id", "employee_name", "monthly_ot_hours", "yearly_cumulative_hours"],
        },
    },
    {
        "name": "mekong_labor_severance",
        "description": "Calculate statutory severance pay (Article 46) or job loss allowance (Article 47).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "employee_name": {"type": "string", "description": "Employee full name."},
                "average_salary": {"type": "number", "description": "Average salary of 6 consecutive months before termination in VND."},
                "total_years": {"type": "number", "description": "Total length of employment service in years."},
                "bhtn_years": {"type": "number", "description": "Length of time participating in unemployment insurance (BHTN) in years.", "default": 0.0},
                "allowance_type": {"type": "string", "description": "SEVERANCE (0.5 mo/yr) or JOB_LOSS (1.0 mo/yr, min 2 mos).", "default": "SEVERANCE"},
            },
            "required": ["employee_name", "average_salary", "total_years"],
        },
    },
    {
        "name": "mekong_labor_regulations",
        "description": "Audit Internal Labor Regulations (NQLD) compliance under Article 118 for enterprises with 10+ employees.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_name": {"type": "string", "description": "Enterprise legal name."},
                "total_employees": {"type": "integer", "description": "Total head count of employees."},
                "has_written_regulations": {"type": "boolean", "description": "Has written internal labor regulations document.", "default": True},
                "is_registered": {"type": "boolean", "description": "Registered and filed with DOLISA.", "default": True},
                "dialogue": {"type": "boolean", "description": "Has workplace dialogue regulation.", "default": True},
                "safety_council": {"type": "boolean", "description": "Has occupational safety & health council.", "default": True},
                "docket": {"type": "string", "description": "DOLISA registration filing docket number.", "default": "NQLD-2026-DOLAB"},
            },
            "required": ["enterprise_name", "total_employees"],
        },
    },
    {
        "name": "mekong_labor_list",
        "description": "Query registered foreign worker permit dossiers and audit records.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by position category or 'ALL'.", "default": "ALL"},
                "limit": {"type": "integer", "description": "Maximum records to return.", "default": 50},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_labor_status",
        "description": "Retrieve Vietnamese labor compliance engine metrics, telemetry, and statutory threshold status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_maritime_vessel",
        "description": "Register commercial vessel call, schedule berthing, and audit channel draft requirements.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Commercial vessel name."},
                "imo": {"type": "string", "description": "IMO vessel number."},
                "flag": {"type": "string", "description": "Vessel flag state."},
                "dwt": {"type": "number", "description": "Deadweight tonnage in metric tons."},
                "grt": {"type": "number", "description": "Gross registered tonnage."},
                "loa": {"type": "number", "description": "Length overall in meters."},
                "draft": {"type": "number", "description": "Design vessel draft in meters."},
                "port_code": {"type": "string", "description": "Seaport UN/LOCODE (e.g. VNVUT, VNSGN, VNHPH)."},
                "terminal": {"type": "string", "description": "Terminal berth or dock facility name."},
                "eta": {"type": "string", "description": "Estimated time of arrival."},
                "etd": {"type": "string", "description": "Estimated time of departure."},
                "call_sign": {"type": "string", "description": "Vessel radio call sign.", "default": "3XYZ"},
            },
            "required": ["name", "imo", "flag", "dwt", "grt", "loa", "draft", "port_code", "terminal", "eta", "etd"],
        },
    },
    {
        "name": "mekong_maritime_container",
        "description": "Record container inventory, 3D yard slot location, and SOLAS VGM gross mass compliance.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "container_no": {"type": "string", "description": "Standard container ISO number (e.g. MSCU1234567)."},
                "container_type": {"type": "string", "description": "Container size and category (20GP, 40GP, 40HC, 20RF, 40RF)."},
                "gross_weight": {"type": "number", "description": "Gross weight including cargo and tare in kg."},
                "seal": {"type": "string", "description": "Shipping line seal number."},
                "booking_or_bl": {"type": "string", "description": "Booking reference or Bill of Lading number."},
                "slot": {"type": "string", "description": "Yard location coordinate (Bay-Row-Tier).", "default": "YARD-B01-R03-T2"},
                "tare": {"type": "number", "description": "Tare weight of empty container in kg.", "default": 2300.0},
                "reefer": {"type": "boolean", "description": "Is active refrigerated container.", "default": False},
                "dg": {"type": "boolean", "description": "Is IMO dangerous goods cargo.", "default": False},
            },
            "required": ["container_no", "container_type", "gross_weight", "seal", "booking_or_bl"],
        },
    },
    {
        "name": "mekong_maritime_tariff",
        "description": "Compute statutory berth dues, pilotage fees, and container LoLo stevedoring tariffs (Circular 39/2023).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_call": {"type": "string", "description": "Vessel call identifier."},
                "group": {"type": "string", "description": "Seaport tariff group (GROUP_1 to GROUP_5)."},
                "grt": {"type": "number", "description": "Vessel Gross Registered Tonnage."},
                "berth_hours": {"type": "number", "description": "Duration alongside berth in hours."},
                "distance": {"type": "number", "description": "Pilotage distance in nautical miles.", "default": 18.0},
                "f20": {"type": "integer", "description": "Loaded 20ft containers handled.", "default": 0},
                "f40": {"type": "integer", "description": "Loaded 40ft containers handled.", "default": 0},
                "e20": {"type": "integer", "description": "Empty 20ft containers handled.", "default": 0},
                "e40": {"type": "integer", "description": "Empty 40ft containers handled.", "default": 0},
                "reefer_hrs": {"type": "number", "description": "Reefer power hours.", "default": 0.0},
                "reefer_cnt": {"type": "integer", "description": "Reefer container count.", "default": 0},
                "terminal": {"type": "string", "description": "Terminal facility name.", "default": "Tân Cảng Cát Lái"},
            },
            "required": ["vessel_call", "group", "grt", "berth_hours"],
        },
    },
    {
        "name": "mekong_maritime_manifest",
        "description": "Submit electronic sea cargo e-Manifest to VNACCS / National Single Window.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_call": {"type": "string", "description": "Vessel call identifier."},
                "bl": {"type": "string", "description": "Bill of Lading number."},
                "shipper": {"type": "string", "description": "Shipper company name."},
                "consignee": {"type": "string", "description": "Consignee company name."},
                "cargo": {"type": "string", "description": "Commodity description."},
                "containers": {"type": "integer", "description": "Total container count."},
                "gross_kg": {"type": "number", "description": "Total gross weight in kg."},
                "decl_no": {"type": "string", "description": "Customs declaration receipt number."},
            },
            "required": ["vessel_call", "bl", "shipper", "consignee", "cargo", "containers", "gross_kg"],
        },
    },
    {
        "name": "mekong_maritime_list",
        "description": "Query scheduled vessel calls or container inventory in terminal yards and ICD depots.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "'vessels' or 'containers'.", "default": "vessels"},
                "yard": {"type": "string", "description": "Yard filter string.", "default": "ALL"},
                "limit": {"type": "integer", "description": "Maximum records to return.", "default": 50},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_maritime_status",
        "description": "Retrieve Vietnamese maritime logistics, vessel schedule, and terminal yard metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_energy_solar",
        "description": "Evaluate rooftop solar (ĐMTMN) self-consumption, Decree 135/2024 surplus caps, and carbon offsets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Unique solar project ID"},
                "capacity_kwp": {"type": "number", "description": "Installed peak capacity in kWp"},
                "location": {"type": "string", "description": "Province/location in Vietnam"},
                "self_consumption_pct": {"type": "number", "description": "Percentage self-consumed on-site (0-100)"},
                "grid_connection": {"type": "string", "description": "Grid connection status (connected/off-grid)"},
                "battery_storage_kwh": {"type": "number", "description": "BESS battery capacity in kWh"},
            },
            "required": ["project_id", "capacity_kwp"],
        },
    },
    {
        "name": "mekong_energy_dppa",
        "description": "Evaluate Direct Power Purchase Agreement (DPPA) under Decree 80/2024, private wire vs national grid CfD settlement.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Unique DPPA contract ID"},
                "buyer_id": {"type": "string", "description": "Large consumer / buyer entity name"},
                "seller_id": {"type": "string", "description": "Renewable generation developer entity name"},
                "mechanism": {"type": "string", "description": "DPPA mechanism: 'direct' (private wire) or 'grid' (VWEM + CfD)"},
                "contract_kwh_month": {"type": "number", "description": "Contracted monthly energy volume in kWh"},
                "strike_price_vnd_kwh": {"type": "number", "description": "Agreed strike price in VND/kWh"},
                "spot_price_vnd_kwh": {"type": "number", "description": "Wholesale market spot price in VND/kWh"},
            },
            "required": ["contract_id", "buyer_id", "seller_id"],
        },
    },
    {
        "name": "mekong_energy_ev",
        "description": "Simulate EV charging station session, TCVN 13078 / IEC 61851 charger specs, Decision 2699 TOU billing, and CO2 offset.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Unique charging session ID"},
                "station_id": {"type": "string", "description": "Charging station identifier"},
                "charger_type": {"type": "string", "description": "Charger specification: AC_7kW, AC_22kW, DC_60kW, DC_120kW, DC_180kW"},
                "energy_kwh": {"type": "number", "description": "Energy delivered in kWh"},
                "tou_period": {"type": "string", "description": "Time-of-Use period: off_peak, normal, peak"},
                "ev_model": {"type": "string", "description": "Electric vehicle model"},
            },
            "required": ["session_id", "station_id"],
        },
    },
    {
        "name": "mekong_energy_list",
        "description": "Query registered rooftop solar projects, DPPA bilateral contracts, or EV charging stations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Item category: 'solar', 'dppa', or 'ev'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_energy_status",
        "description": "Retrieve Vietnamese renewable energy grid metrics, DPPA settlements, and EV charging network summary.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_privacy_audit",
        "description": "Audit enterprise compliance against Decree 13/2023/ND-CP (PDPD), identify gaps, and recommend DPO / DPIA actions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_name": {"type": "string", "description": "Enterprise name undergoing compliance audit"},
                "controller_type": {"type": "string", "description": "Controller role: CONTROLLER, PROCESSOR, CONTROLLER_AND_PROCESSOR"},
                "has_sensitive_data": {"type": "boolean", "description": "Whether enterprise processes sensitive personal data"},
                "has_dpo": {"type": "boolean", "description": "Whether enterprise has appointed a DPO"},
                "has_cross_border": {"type": "boolean", "description": "Whether enterprise transfers personal data overseas"},
                "has_dpia_dossier": {"type": "boolean", "description": "Whether enterprise has compiled DPIA dossier"},
            },
            "required": ["enterprise_name"],
        },
    },
    {
        "name": "mekong_privacy_dpia",
        "description": "Create Personal Data Processing Impact Assessment (DPIA Form 04) under Article 24 Decree 13/2023/ND-CP for A05 filing.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "activity_name": {"type": "string", "description": "Data processing activity title"},
                "processing_purpose": {"type": "string", "description": "Purpose of personal data processing"},
                "data_categories": {"type": "array", "items": {"type": "string"}, "description": "List of personal data categories"},
                "legal_basis": {"type": "string", "description": "Statutory legal basis (e.g. CONSENT, CONTRACT)"},
                "security_measures": {"type": "string", "description": "Technical and organizational security measures"},
            },
            "required": ["activity_name", "processing_purpose", "data_categories"],
        },
    },
    {
        "name": "mekong_privacy_transfer",
        "description": "Evaluate overseas cross-border data transfer compliance and SCC agreement under Article 25 Decree 13/2023/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "transfer_name": {"type": "string", "description": "Data transfer flow title"},
                "recipient_entity": {"type": "string", "description": "Foreign recipient organization/corporation"},
                "destination_country": {"type": "string", "description": "Receiving country/territory"},
                "data_types": {"type": "array", "items": {"type": "string"}, "description": "List of data types transferred"},
                "record_count": {"type": "integer", "description": "Number of transferred records/subjects"},
                "has_scc": {"type": "boolean", "description": "Whether binding data protection agreement/SCC is signed"},
            },
            "required": ["transfer_name", "recipient_entity", "destination_country", "data_types"],
        },
    },
    {
        "name": "mekong_privacy_breach",
        "description": "Report personal data breach incident, track mitigation, and enforce 72-hour statutory notification to A05 (Article 26).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "incident_name": {"type": "string", "description": "Data breach incident title"},
                "severity": {"type": "string", "description": "Severity level: LOW, MEDIUM, HIGH, CRITICAL"},
                "affected_count": {"type": "integer", "description": "Number of affected data subjects"},
                "breach_type": {"type": "string", "description": "Type/nature of security incident"},
                "hours_elapsed": {"type": "number", "description": "Hours elapsed since breach discovery"},
                "mitigation_plan": {"type": "string", "description": "Containment and mitigation plan"},
            },
            "required": ["incident_name", "severity", "affected_count", "breach_type"],
        },
    },
    {
        "name": "mekong_privacy_dsar",
        "description": "Process Article 9 Data Subject Access Request (access, delete, withdraw consent, restrict processing).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "request_type": {"type": "string", "description": "Right invoked under Article 9 (e.g. RIGHT_TO_ACCESS, RIGHT_TO_DELETE)"},
                "subject_id": {"type": "string", "description": "Data subject identifier (CCCD / citizen ID or user ID)"},
                "details": {"type": "string", "description": "Detailed description of DSAR request"},
            },
            "required": ["request_type", "subject_id"],
        },
    },
    {
        "name": "mekong_privacy_list",
        "description": "Query registered DPIA assessments, cross-border transfers, data breach incidents, or DSAR requests.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'dpia', 'transfer', 'breach', or 'dsar'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_privacy_status",
        "description": "Retrieve Vietnamese Personal Data Protection Decree (PDPD Decree 13/2023) compliance metrics and telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_aviation_flight",
        "description": "Register commercial flight movement, aircraft specs (MTOW), and apron/gate parking allocation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "flight_no": {"type": "string", "description": "Flight number (e.g. VN216, VJ123)"},
                "aircraft_type": {"type": "string", "description": "Aircraft model (A321, A321NEO, B787-9, A350-900, B777F, ATR72)"},
                "origin_airport": {"type": "string", "description": "IATA origin airport code (SGN, HAN, DAD, CXR, PQC, etc.)"},
                "dest_airport": {"type": "string", "description": "IATA destination airport code"},
                "mtow_tons": {"type": "number", "description": "Maximum Takeoff Weight in metric tons"},
                "parking_hours": {"type": "number", "description": "Scheduled apron parking duration in hours"},
                "is_international": {"type": "boolean", "description": "Whether flight operates internationally"},
            },
            "required": ["flight_no", "aircraft_type", "origin_airport", "dest_airport"],
        },
    },
    {
        "name": "mekong_aviation_cargo",
        "description": "Calculate IATA volumetric chargeable weight (1 CBM = 166.67 kg) and air freight density rating.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mawb_no": {"type": "string", "description": "11-digit Master Air Waybill number (e.g. 738-12345675)"},
                "origin_airport": {"type": "string", "description": "Origin airport code (HAN, SGN)"},
                "dest_airport": {"type": "string", "description": "Destination airport code"},
                "piece_count": {"type": "integer", "description": "Total package piece count"},
                "gross_weight_kg": {"type": "number", "description": "Actual physical weight in kg"},
                "volume_cbm": {"type": "number", "description": "Total cargo volume in cubic meters (CBM)"},
                "cargo_type": {"type": "string", "description": "Cargo type: GENERAL, PERISHABLE, PHARMA, VALUABLE, DG"},
                "temperature_regime": {"type": "string", "description": "Temperature condition: AMBIENT, CRT (15-25C), COOL (2-8C), FROZEN (-20C)"},
            },
            "required": ["mawb_no", "origin_airport", "dest_airport", "piece_count", "gross_weight_kg", "volume_cbm"],
        },
    },
    {
        "name": "mekong_aviation_tariff",
        "description": "Calculate statutory landing/takeoff, aircraft parking, security screening, and ramp handling fees (Circular 53/2019).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "flight_no": {"type": "string", "description": "Flight number"},
                "airport_code": {"type": "string", "description": "Vietnam airport code (HAN, SGN, DAD, CXR, PQC, etc.)"},
                "mtow_tons": {"type": "number", "description": "Aircraft MTOW in metric tons"},
                "parking_hours": {"type": "number", "description": "Total parking hours at apron/stand"},
                "cargo_tons": {"type": "number", "description": "Loaded/unloaded cargo payload in tons"},
                "is_international": {"type": "boolean", "description": "Whether flight is international"},
            },
            "required": ["flight_no", "airport_code", "mtow_tons"],
        },
    },
    {
        "name": "mekong_aviation_dg",
        "description": "Evaluate Dangerous Goods declaration under IATA DGR and enforce passenger aircraft prohibitions (PAX vs CAO).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "un_number": {"type": "string", "description": "UN 4-digit code (e.g. UN3480, UN1203, UN1805)"},
                "proper_shipping_name": {"type": "string", "description": "Official IATA chemical/commodity shipping name"},
                "hazard_class": {"type": "string", "description": "Hazard class: CLASS_1, CLASS_2.1, CLASS_3, CLASS_8, CLASS_9, etc."},
                "packing_group": {"type": "string", "description": "Packing group: I (high danger), II (medium), III (low)"},
                "quantity_kg": {"type": "number", "description": "Net explosive/chemical quantity in kg"},
                "aircraft_type": {"type": "string", "description": "Intended aircraft: PAX_AND_CARGO or CARGO_AIRCRAFT_ONLY"},
            },
            "required": ["un_number", "proper_shipping_name", "hazard_class"],
        },
    },
    {
        "name": "mekong_aviation_list",
        "description": "Query registered flight schedules, air cargo shipments, or Dangerous Goods declarations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'flights', 'cargo', or 'dg'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_aviation_status",
        "description": "Retrieve Vietnamese civil aviation network metrics, airport revenue, and air freight telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_ecom_fct",
        "description": "Calculate digital services Foreign Contractor Tax (FCT - VAT & CIT) under Decree 126/2020 & Circular 80/2021.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "foreign_supplier_name": {"type": "string", "description": "Foreign supplier name (e.g. Google, Meta, Netflix, TikTok)"},
                "supplier_etax_code": {"type": "string", "description": "Vietnam supplier tax code issued via etaxvn.gdt.gov.vn"},
                "service_category": {"type": "string", "description": "Service category: DIGITAL_SERVICES, ONLINE_ADVERTISING, CLOUD_SAAS, STREAMING_MEDIA"},
                "revenue_usd": {"type": "number", "description": "Declared digital service revenue in USD"},
                "revenue_vnd": {"type": "number", "description": "Declared digital service revenue in VND"},
                "quarter": {"type": "string", "description": "Tax filing period (e.g. Q1-2026)"},
            },
            "required": ["foreign_supplier_name", "supplier_etax_code", "service_category"],
        },
    },
    {
        "name": "mekong_ecom_audit",
        "description": "Audit e-commerce platform compliance and statutory licensing under Decree 52/2013 & Decree 85/2021.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "platform_name": {"type": "string", "description": "Platform or e-commerce website name"},
                "domain_url": {"type": "string", "description": "Website or app URL"},
                "platform_type": {"type": "string", "description": "Platform type: SALES_WEBSITE, MARKETPLACE, SOCIAL_COMMERCE, PROMOTION_APP"},
                "enterprise_tax_id": {"type": "string", "description": "Operating enterprise tax ID"},
                "has_operating_regulations": {"type": "boolean", "description": "Whether operating regulations are approved"},
                "has_dispute_mechanism": {"type": "boolean", "description": "Whether consumer dispute handling mechanism exists"},
                "has_seller_kyc": {"type": "boolean", "description": "Whether seller identity KYC is collected"},
                "has_data_retention_3yr": {"type": "boolean", "description": "Whether 3-year transaction audit log retention is active"},
                "has_tax_reporting_system": {"type": "boolean", "description": "Whether quarterly tax portal reporting module is ready"},
            },
            "required": ["platform_name", "domain_url"],
        },
    },
    {
        "name": "mekong_ecom_order",
        "description": "Settle marketplace order finances, compute seller net payout, and generate electronic invoice under Decree 123/2020.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "order_code": {"type": "string", "description": "Marketplace transaction order code"},
                "platform_id": {"type": "string", "description": "Marketplace identifier (e.g. SHOPEE_VN, LAZADA_VN)"},
                "seller_id": {"type": "string", "description": "Seller or shop account ID"},
                "buyer_id": {"type": "string", "description": "Buyer account ID"},
                "gmv_gross_vnd": {"type": "number", "description": "Gross merchandise value of products in VND"},
                "platform_commission_pct": {"type": "number", "description": "Marketplace take-rate commission percentage"},
                "payment_fee_pct": {"type": "number", "description": "Payment gateway processing fee percentage"},
                "shop_voucher_vnd": {"type": "number", "description": "Seller funded voucher discount in VND"},
                "platform_voucher_vnd": {"type": "number", "description": "Platform subsidized voucher discount in VND"},
                "shipping_fee_vnd": {"type": "number", "description": "Delivery shipping fee in VND"},
                "vat_rate_pct": {"type": "integer", "description": "Invoice VAT rate (0, 5, 8, 10)"},
            },
            "required": ["order_code", "platform_id", "seller_id", "buyer_id", "gmv_gross_vnd"],
        },
    },
    {
        "name": "mekong_ecom_parcel",
        "description": "Evaluate cross-border express parcel customs duty & VAT exemption threshold under statutory de minimis rules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tracking_no": {"type": "string", "description": "International express waybill tracking number"},
                "shipper_country": {"type": "string", "description": "Country of origin/dispatch"},
                "consignee_name": {"type": "string", "description": "Consignee recipient full name in Vietnam"},
                "item_description": {"type": "string", "description": "Commodity goods description"},
                "customs_value_usd": {"type": "number", "description": "Customs valuation in USD"},
                "customs_value_vnd": {"type": "number", "description": "Customs valuation in VND"},
                "import_duty_pct": {"type": "number", "description": "Applicable import tariff percentage"},
            },
            "required": ["tracking_no", "shipper_country", "consignee_name", "item_description"],
        },
    },
    {
        "name": "mekong_ecom_list",
        "description": "Query registered e-commerce platforms, FCT tax declarations, marketplace orders, or cross-border parcels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'platforms', 'fct', 'orders', or 'parcels'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_ecom_status",
        "description": "Retrieve Vietnamese e-commerce compliance telemetry, digital tax metrics, and order settlement statistics.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_telecom_spectrum",
        "description": "Calculate spectrum auction reserve valuation, deposit, and network rollout obligations under Decree 63/2023/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "band_code": {"type": "string", "description": "Spectrum band code (e.g. B7_2600, C2_3700, C3_3800, N28_700, B3_1800)"},
                "license_years": {"type": "integer", "description": "License tenure in years (max 15)"},
                "deposit_pct": {"type": "number", "description": "Bid deposit percentage (5% to 20%)"},
                "custom_reserve_price_vnd": {"type": "number", "description": "Custom starting reserve price in VND"},
            },
            "required": ["band_code"],
        },
    },
    {
        "name": "mekong_telecom_ott",
        "description": "Audit OTT messaging, VoIP & digital communication service compliance under Telecommunications Law 2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "description": "Name of the OTT communication application/service"},
                "provider_name": {"type": "string", "description": "Operating enterprise / legal entity"},
                "service_category": {"type": "string", "description": "Category: 'OTT_MESSAGING_VOICE', 'DATA_CENTER', 'CLOUD_COMPUTING'"},
                "registered_users": {"type": "integer", "description": "Registered subscriber base"},
                "has_kyc_verification": {"type": "boolean", "description": "User mobile OTP/identity verification enabled"},
                "has_encryption_e2ee": {"type": "boolean", "description": "End-to-end encryption or TLS 1.3 enabled"},
                "has_local_data_storage": {"type": "boolean", "description": "Domestic data storage under Cybersecurity Law 2018"},
                "has_vnta_notification": {"type": "boolean", "description": "Service notification filed with VNTA / MIC"},
                "has_consumer_dispute_system": {"type": "boolean", "description": "Customer dispute resolution system available"},
            },
            "required": ["service_name", "provider_name"],
        },
    },
    {
        "name": "mekong_telecom_bts",
        "description": "Evaluate base transceiver station (BTS) electromagnetic field (EMF) exposure safety against QCVN 08:2020/BTTTT.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string", "description": "Unique BTS station identifier"},
                "location": {"type": "string", "description": "Geographical address / ward / district"},
                "antenna_height_m": {"type": "number", "description": "Antenna elevation above ground level in meters"},
                "transmit_power_watts": {"type": "number", "description": "RF transmitter output power in Watts"},
                "frequency_mhz": {"type": "number", "description": "Carrier operating frequency in MHz"},
                "antenna_gain_dbi": {"type": "number", "description": "Antenna directional gain in dBi"},
                "distance_residential_m": {"type": "number", "description": "Distance to nearest residential boundary in meters"},
            },
            "required": ["station_id", "location"],
        },
    },
    {
        "name": "mekong_telecom_number",
        "description": "Allocate national telecom numbering resources (1900, 1800, Mobile) and compute maintenance fees under Circular 25/2015.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number_prefix": {"type": "string", "description": "Number prefix or block (e.g. 1900, 1800, 098, 090)"},
                "assigned_operator": {"type": "string", "description": "Licensed telco or enterprise assignee"},
                "block_size": {"type": "integer", "description": "Quantity of numbers in block"},
                "service_purpose": {"type": "string", "description": "Usage purpose: 'MOBILE_SUBSCRIBER', 'HOTLINE', 'EMERGENCY'"},
            },
            "required": ["number_prefix", "assigned_operator"],
        },
    },
    {
        "name": "mekong_telecom_list",
        "description": "Query registered spectrum auctions, OTT compliance audits, BTS safety evals, or numbering resources.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'spectrum', 'ott', 'bts', or 'numbers'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_telecom_status",
        "description": "Retrieve Vietnamese telecommunications telemetry, spectrum auctions, and OTT compliance status.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_pharma_drug",
        "description": "Register or verify drug marketing authorization (Visa MA) under Drug Law 2016.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "visa_number": {"type": "string", "description": "Statutory marketing authorization visa (e.g. VN-22019-19, VD-35124-21)"},
                "drug_name": {"type": "string", "description": "Commercial drug brand name"},
                "active_ingredient": {"type": "string", "description": "Active Pharmaceutical Ingredient (API)"},
                "strength": {"type": "string", "description": "Concentration/dosage strength (e.g. 500mg, 10mg/ml)"},
                "dosage_form": {"type": "string", "description": "Pharmaceutical form (e.g. Film-coated tablet, Injection)"},
                "classification": {"type": "string", "description": "Category: 'RX_PRESCRIPTION', 'OTC_NON_PRESCRIPTION', 'SPECIAL_CONTROL_NARCOTIC', 'VACCINE_BIOLOGICAL'"},
                "manufacturer_name": {"type": "string", "description": "Pharmaceutical manufacturing establishment"},
                "country_of_origin": {"type": "string", "description": "Manufacturing origin country"},
                "tenure_years": {"type": "integer", "description": "Validity period in years (default 5)"},
            },
            "required": ["visa_number", "drug_name", "active_ingredient", "strength", "dosage_form"],
        },
    },
    {
        "name": "mekong_pharma_gsp",
        "description": "Audit warehouse environmental storage conditions and cold chain against GSP standards (Circular 36/2018).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "warehouse_id": {"type": "string", "description": "Warehouse facility identifier"},
                "warehouse_name": {"type": "string", "description": "Facility name/location"},
                "storage_condition": {"type": "string", "description": "Regime: 'STANDARD_ROOM', 'COOL_STORAGE', 'COLD_CHAIN', 'DEEP_FREEZE'"},
                "recorded_temp_c": {"type": "number", "description": "Current recorded temperature in Celsius"},
                "recorded_humidity_pct": {"type": "number", "description": "Current relative humidity percentage"},
                "sensor_id": {"type": "string", "description": "IoT data logger identifier"},
            },
            "required": ["warehouse_id", "warehouse_name"],
        },
    },
    {
        "name": "mekong_pharma_batch",
        "description": "Track drug batch with GS1 DataMatrix identifiers and manage national recall alerts under Decision 412/QD-BYT.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "batch_number": {"type": "string", "description": "Production batch / lot number"},
                "visa_number": {"type": "string", "description": "Registered drug visa number"},
                "drug_name": {"type": "string", "description": "Commercial drug brand name"},
                "gtin_14": {"type": "string", "description": "GS1 GTIN-14 package identifier"},
                "serial_number": {"type": "string", "description": "Unique unit serial number S/N"},
                "manufacturing_date": {"type": "string", "description": "Production date (YYYY-MM-DD)"},
                "expiry_date": {"type": "string", "description": "Expiry date (YYYY-MM-DD)"},
                "quantity_units": {"type": "integer", "description": "Total batch size in units"},
                "recall_action": {"type": "string", "description": "Recall status: 'NONE', 'LEVEL_1', 'LEVEL_2', 'LEVEL_3'"},
            },
            "required": ["batch_number", "visa_number", "drug_name"],
        },
    },
    {
        "name": "mekong_pharma_price",
        "description": "Verify statutory drug wholesale and hospital retail margin limits under Decree 54/2017/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "visa_number": {"type": "string", "description": "Registered drug visa number"},
                "drug_name": {"type": "string", "description": "Commercial drug brand name"},
                "wholesale_price_vnd": {"type": "number", "description": "Declared wholesale price in VND"},
                "hospital_retail_price_vnd": {"type": "number", "description": "Proposed hospital pharmacy retail price in VND"},
                "declared_by": {"type": "string", "description": "Declaring pharmaceutical distributor/manufacturer"},
                "classification": {"type": "string", "description": "Drug classification"},
            },
            "required": ["visa_number", "drug_name", "wholesale_price_vnd", "hospital_retail_price_vnd"],
        },
    },
    {
        "name": "mekong_pharma_list",
        "description": "Query registered drug marketing authorizations, GSP logs, batch traceability, or price declarations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'drugs', 'gsp', 'batches', or 'prices'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_pharma_status",
        "description": "Retrieve Vietnamese pharmaceutical regulatory, GSP cold chain, and batch traceability telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_petrol_price",
        "description": "Calculate statutory petroleum base price and retail ceilings under Decree 80/2023/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_code": {"type": "string", "description": "Petroleum product code: RON95_III, E5_RON92, DIESEL_005S, KEROSENE, MAZUT_180CST"},
                "mops_platts_usd_per_barrel": {"type": "number", "description": "Platts Singapore MOPS benchmark in USD/bbl"},
                "import_duty_pct": {"type": "number", "description": "Preferential import tariff MFN/FTA percentage"},
                "bog_fund_deduction_vnd": {"type": "number", "description": "Stabilization fund BOG deduction in VND/liter"},
                "bog_fund_expenditure_vnd": {"type": "number", "description": "Stabilization fund BOG expenditure in VND/liter"},
                "cycle_date": {"type": "string", "description": "Adjustment date in YYYY-MM-DD"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_petrol_reserve",
        "description": "Audit statutory mandatory fuel reserves against Decree 83/2014 & Decision 242/QD-TTg thresholds.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_name": {"type": "string", "description": "Name of petroleum trading enterprise"},
                "enterprise_type": {"type": "string", "description": "Enterprise type: KEY_IMPORTER (20 days), DISTRIBUTOR (5 days), DOMESTIC_REFINERY (30 days)"},
                "storage_capacity_m3": {"type": "number", "description": "Tank storage capacity in m3"},
                "current_stock_m3": {"type": "number", "description": "Current physical stock in m3"},
                "daily_consumption_m3": {"type": "number", "description": "Average daily sales/consumption in m3/day"},
            },
            "required": ["enterprise_name"],
        },
    },
    {
        "name": "mekong_petrol_quality",
        "description": "Inspect petroleum quality and Euro 4/5 emission tier compliance under QCVN 01:2015/BKHCN.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "gas_station_id": {"type": "string", "description": "Retail fuel station ID"},
                "gas_station_name": {"type": "string", "description": "Retail fuel station name"},
                "product_code": {"type": "string", "description": "Petroleum product code"},
                "sulfur_content_ppm": {"type": "number", "description": "Measured sulfur content in ppm"},
                "lead_content_g_l": {"type": "number", "description": "Measured lead content in g/l"},
            },
            "required": ["gas_station_id", "gas_station_name"],
        },
    },
    {
        "name": "mekong_petrol_pump",
        "description": "Monitor dispenser pump e-invoice issuance telemetry under Official Telegram 1284/CD-TTg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station_id": {"type": "string", "description": "Retail fuel station ID"},
                "pump_count": {"type": "integer", "description": "Number of active fuel dispenser nozzles/pumps"},
                "daily_transactions": {"type": "integer", "description": "Total daily retail transactions"},
                "daily_volume_liters": {"type": "number", "description": "Total dispensed volume in liters"},
                "daily_revenue_vnd": {"type": "number", "description": "Total retail revenue in VND"},
                "e_invoices_issued": {"type": "integer", "description": "Number of e-invoices issued per pump transaction"},
            },
            "required": ["station_id"],
        },
    },
    {
        "name": "mekong_petrol_list",
        "description": "Query petroleum price adjustments, national reserves, quality inspections, or pump telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'prices', 'reserves', 'quality', or 'pump'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_petrol_status",
        "description": "Retrieve Vietnamese petroleum regulatory, price adjustments, national reserves, and e-invoice telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_fishery_vessel",
        "description": "Register fishing vessel into VNFishbase and audit statutory VMS mandate under Decree 26/2019/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_plate": {"type": "string", "description": "Fishing vessel registration plate"},
                "owner_name": {"type": "string", "description": "Vessel owner or captain name"},
                "home_port": {"type": "string", "description": "Designated landing port"},
                "length_meters": {"type": "number", "description": "Maximum vessel length Lmax in meters"},
                "engine_power_hp": {"type": "number", "description": "Main engine horsepower CV"},
                "vms_device_id": {"type": "string", "description": "VMS device serial ID"},
                "assigned_zone": {"type": "string", "description": "Permitted sea zone"},
                "license_valid_years": {"type": "integer", "description": "Fishing license validity period in years"},
            },
            "required": ["vessel_plate", "owner_name"],
        },
    },
    {
        "name": "mekong_fishery_vms",
        "description": "Track vessel GPS telemetry, detect EEZ maritime border violations, and assess EC IUU Yellow Card risk.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_plate": {"type": "string", "description": "Fishing vessel registration plate"},
                "latitude": {"type": "number", "description": "Vessel latitude coordinate"},
                "longitude": {"type": "number", "description": "Vessel longitude coordinate"},
                "speed_knots": {"type": "number", "description": "Vessel speed in knots"},
                "heading_degrees": {"type": "number", "description": "Compass heading degrees"},
                "is_signal_active": {"type": "boolean", "description": "Whether VMS signal is active"},
                "disconnection_hours": {"type": "number", "description": "Continuous signal disconnection duration in hours"},
                "assigned_zone": {"type": "string", "description": "Permitted fishing sea zone"},
            },
            "required": ["vessel_plate", "latitude", "longitude"],
        },
    },
    {
        "name": "mekong_fishery_cert",
        "description": "Issue electronic Catch Certificate (CC) or Statement of Catch (SC) under eCDT VN system.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "vessel_plate": {"type": "string", "description": "Fishing vessel registration plate"},
                "species_code": {"type": "string", "description": "Marine species code"},
                "catch_volume_kg": {"type": "number", "description": "Landed volume in kilograms"},
                "landing_port": {"type": "string", "description": "Designated port of landing"},
                "destination_market": {"type": "string", "description": "Target export destination market"},
                "certificate_type": {"type": "string", "description": "CATCH_CERTIFICATE_CC or STATEMENT_OF_CATCH_SC"},
            },
            "required": ["vessel_plate"],
        },
    },
    {
        "name": "mekong_fishery_quality",
        "description": "Audit seafood factory HACCP compliance and banned antibiotic residue limits under Circular 48/2013.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "facility_eu_code": {"type": "string", "description": "EU approved plant code DL-xxx"},
                "facility_name": {"type": "string", "description": "Name of seafood processing facility"},
                "lot_number": {"type": "string", "description": "Finished product batch lot number"},
                "species_code": {"type": "string", "description": "Seafood species code"},
                "haccp_score": {"type": "number", "description": "HACCP audit score (0-100)"},
                "chloramphenicol_ppb": {"type": "number", "description": "Chloramphenicol residue in ppb (<=0.1)"},
                "nitrofurans_ppb": {"type": "number", "description": "Nitrofuran metabolites in ppb (<=0.5)"},
                "heavy_metal_pass": {"type": "boolean", "description": "Heavy metal compliance pass/fail"},
            },
            "required": ["facility_eu_code", "facility_name", "lot_number"],
        },
    },
    {
        "name": "mekong_fishery_list",
        "description": "Query registered fishing vessels, VMS logs, eCDT catch certificates, or seafood quality audits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "item_type": {"type": "string", "description": "Category: 'vessels', 'vms', 'certs', or 'quality'"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_fishery_status",
        "description": "Retrieve Vietnamese fisheries, VMS fleet tracking, eCDT catch certs, and EC IUU Yellow Card telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_construction_project",
        "description": "Register construction project and evaluate statutory building grade under Decree 06/2021/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Construction project name"},
                "project_type": {"type": "string", "description": "Project classification"},
                "total_investment_vnd": {"type": "number", "description": "Total investment capital in VND"},
                "gross_floor_area_m2": {"type": "number", "description": "Gross floor area in m2"},
                "height_meters": {"type": "number", "description": "Building height in meters"},
                "floors_count": {"type": "integer", "description": "Number of above-ground floors"},
                "location_province": {"type": "string", "description": "Province or city"},
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "mekong_construction_permit",
        "description": "Evaluate building permit eligibility and statutory exemptions under Article 89 Law on Construction 2020.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier PRJ-xxxx"},
                "is_secret_defense_project": {"type": "boolean", "description": "State secret or defense project"},
                "is_rural_detached_house": {"type": "boolean", "description": "Rural detached house under 7 floors"},
                "is_industrial_park_approved_1_500": {"type": "boolean", "description": "Industrial park with approved 1/500 zoning"},
                "is_fire_safety_approved": {"type": "boolean", "description": "PCCC fire safety approval status"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "mekong_construction_fidic",
        "description": "Structure FIDIC construction contract (Red/Yellow/Silver Book) with advance payment, performance bond and retention terms.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "contract_name": {"type": "string", "description": "Contract package title"},
                "fidic_type": {"type": "string", "description": "FIDIC_RED_BOOK, FIDIC_YELLOW_BOOK, or FIDIC_SILVER_BOOK"},
                "employer_name": {"type": "string", "description": "Employer name"},
                "contractor_name": {"type": "string", "description": "Contractor name"},
                "contract_value_vnd": {"type": "number", "description": "Contract value in VND"},
                "custom_advance_pct": {"type": "number", "description": "Custom advance payment percentage"},
            },
            "required": ["project_id", "contract_name"],
        },
    },
    {
        "name": "mekong_construction_pccc",
        "description": "Audit building fire safety rating, REI resistance and evacuation distances under QCVN 06:2022/BXD.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "fire_tier": {"type": "string", "description": "Fire resistance tier (TIER_I to TIER_V)"},
                "tested_column_rei_min": {"type": "integer", "description": "Tested columns REI fire resistance (minutes)"},
                "tested_floor_rei_min": {"type": "integer", "description": "Tested floors REI fire resistance (minutes)"},
                "measured_evacuation_dist_m": {"type": "number", "description": "Measured evacuation travel distance (meters)"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "mekong_construction_accept",
        "description": "Perform construction quality acceptance inspection for commissioning under Decree 06/2021/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "acceptance_stage": {"type": "string", "description": "Acceptance stage"},
                "inspector_name": {"type": "string", "description": "Supervising consultant name"},
                "structural_soundness_pct": {"type": "number", "description": "Structural soundness score (>=90%)"},
                "as_built_compliance": {"type": "boolean", "description": "As-built compliance"},
            },
            "required": ["project_id"],
        },
    },
    {
        "name": "mekong_construction_list",
        "description": "Query registered projects, building permits, FIDIC contracts, PCCC audits, or quality acceptances.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: projects, permits, fidic, pccc, acceptances"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_construction_status",
        "description": "Retrieve Vietnamese construction engineering, FIDIC contracts, and building permits telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_mining_license",
        "description": "Register mineral mining concession and determine statutory licensing authority under Mineral Law 2010.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mine_name": {"type": "string", "description": "Name of mine concession"},
                "mineral_type": {"type": "string", "description": "Mineral code: RARE_EARTH, BAUXITE, GOLD_ORE, COAL_ENERGY, TITANIUM, etc."},
                "enterprise_name": {"type": "string", "description": "Mining enterprise name"},
                "approved_reserve": {"type": "number", "description": "Approved geological reserve volume"},
                "annual_capacity": {"type": "number", "description": "Annual exploitation capacity"},
                "mining_method": {"type": "string", "description": "OPEN_PIT or UNDERGROUND"},
                "mine_area_hectares": {"type": "number", "description": "Concession area in hectares"},
                "location_province": {"type": "string", "description": "Province/city location"},
                "duration_years": {"type": "integer", "description": "License tenure in years (<= 30)"},
            },
            "required": ["mine_name"],
        },
    },
    {
        "name": "mekong_mining_rights_fee",
        "description": "Calculate statutory concession mineral rights fee T = Q * G * K * R under Decree 67/2019/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_id": {"type": "string", "description": "Concession license ID"},
                "reserve_volume": {"type": "number", "description": "Chargeable reserve Q"},
                "custom_unit_price_vnd": {"type": "number", "description": "Statutory unit price G in VND"},
                "mining_method": {"type": "string", "description": "Mining method coefficient K (OPEN_PIT=1.0, UNDERGROUND=0.9)"},
                "mineral_type": {"type": "string", "description": "Mineral type for rate R"},
                "payment_years": {"type": "integer", "description": "Payment installment years"},
            },
            "required": ["license_id"],
        },
    },
    {
        "name": "mekong_mining_royalty",
        "description": "Compute natural resources royalty tax declaration under Law on Natural Resources Tax 2009.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_id": {"type": "string", "description": "License ID"},
                "tax_period": {"type": "string", "description": "Tax declaration period (e.g. 2026-Q1)"},
                "actual_mined_volume": {"type": "number", "description": "Actual volume extracted"},
                "mineral_type": {"type": "string", "description": "Mineral code for statutory tax rate"},
                "taxable_unit_price_vnd": {"type": "number", "description": "Taxable unit price in VND"},
            },
            "required": ["license_id"],
        },
    },
    {
        "name": "mekong_mining_rehab",
        "description": "Audit environmental rehabilitation escrow deposit and wastewater effluent against QCVN 40:2011/BTNMT.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_id": {"type": "string", "description": "License ID"},
                "total_rehab_estimate_vnd": {"type": "number", "description": "Approved environmental rehabilitation budget"},
                "initial_deposit_pct": {"type": "number", "description": "Initial deposit percentage (min 25%)"},
                "replanted_trees_count": {"type": "integer", "description": "Replanted trees count"},
                "wastewater_ph": {"type": "number", "description": "Effluent pH reading (6.0 - 9.0)"},
                "wastewater_tss_mg_l": {"type": "number", "description": "Effluent TSS in mg/L (<= 50)"},
            },
            "required": ["license_id"],
        },
    },
    {
        "name": "mekong_mining_sand",
        "description": "Inspect river sand & gravel dredging vessel compliance against Decree 23/2020/ND-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "license_id": {"type": "string", "description": "License ID"},
                "vessel_plate": {"type": "string", "description": "Dredging vessel / barge plate number"},
                "operation_time_hh_mm": {"type": "string", "description": "Operation time HH:MM (allowed 07:00-17:00)"},
                "is_gps_installed": {"type": "boolean", "description": "GPS tracking installed"},
                "is_dock_camera_installed": {"type": "boolean", "description": "Dock camera surveillance installed"},
                "measured_cargo_m3": {"type": "number", "description": "Measured cargo volume in m3"},
            },
            "required": ["license_id", "vessel_plate"],
        },
    },
    {
        "name": "mekong_mining_list",
        "description": "Query registered mining licenses, rights fees, royalty taxes, environmental rehabs, or sand inspections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: licenses, fees, taxes, rehab, sand"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_mining_status",
        "description": "Retrieve Vietnamese mining regulatory, mineral rights fees, royalties, and environmental telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_forestry_plot",
        "description": "Register forest plot with canopy coverage, species, and FSC/PEFC certification under Law on Forestry 2017.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plot_name": {"type": "string", "description": "Name of forest plot"},
                "forest_type": {"type": "string", "description": "Forest type: SPECIAL_USE, PROTECTION, PRODUCTION_NATURAL, PRODUCTION_PLANTATION"},
                "province": {"type": "string", "description": "Province location"},
                "area_hectares": {"type": "number", "description": "Area in hectares"},
                "canopy_cover_pct": {"type": "number", "description": "Canopy cover percentage"},
                "trees_per_hectare": {"type": "number", "description": "Average trees per hectare"},
                "main_species": {"type": "string", "description": "Dominant tree species"},
                "is_fsc_certified": {"type": "boolean", "description": "Whether certified by FSC/PEFC"},
                "fsc_code": {"type": "string", "description": "FSC/PEFC certificate code"},
            },
            "required": ["plot_name"],
        },
    },
    {
        "name": "mekong_forestry_timber",
        "description": "Verify timber consignment legality under VNTLAS (Decree 102/2020) and issue export manifest.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "enterprise_name": {"type": "string", "description": "Name of timber processing/export enterprise"},
                "product_type": {"type": "string", "description": "Product type: FURNITURE, PLYWOOD, SAWN_TIMBER, PELLET"},
                "volume_m3": {"type": "number", "description": "Consignment volume in m3"},
                "species": {"type": "string", "description": "Timber species"},
                "origin_province": {"type": "string", "description": "Processing/origin province"},
                "enterprise_tier": {"type": "string", "description": "VNTLAS classification: TIER_1 or TIER_2"},
                "flegt_cites_license": {"type": "string", "description": "FLEGT or CITES export license number"},
                "export_market": {"type": "string", "description": "Destination market: EU, US, JAPAN, UK"},
            },
            "required": ["enterprise_name"],
        },
    },
    {
        "name": "mekong_forestry_afforestation",
        "description": "Calculate mandatory alternative afforestation area or Vietnam Forest Protection Fund (VNFF) deposit under Article 21.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Infrastructure or conversion project name"},
                "converted_forest_type": {"type": "string", "description": "Converted forest type: SPECIAL_USE, PROTECTION, PRODUCTION_NATURAL, PRODUCTION_PLANTATION"},
                "converted_area_ha": {"type": "number", "description": "Converted forest area in hectares"},
                "payment_rate_vnd_per_ha": {"type": "number", "description": "VNFF approved planting rate in VND/ha"},
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "mekong_forestry_pfes",
        "description": "Compute PFES obligation (Decree 156/2018) and World Bank ERPA forest carbon sequestration revenue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "facility_name": {"type": "string", "description": "Name of payer facility"},
                "facility_type": {"type": "string", "description": "Facility type: HYDROPOWER, CLEAN_WATER, INDUSTRIAL_WATER, ECO_TOURISM"},
                "production_volume": {"type": "number", "description": "Production volume or revenue"},
                "forest_area_ha": {"type": "number", "description": "Basin forest area in hectares"},
                "carbon_sequestration_rate": {"type": "number", "description": "Carbon absorption rate (tCO2e/ha/yr)"},
                "erpa_price_usd_per_ton": {"type": "number", "description": "ERPA carbon transfer price in USD/ton"},
            },
            "required": ["facility_name"],
        },
    },
    {
        "name": "mekong_forestry_fire",
        "description": "Assess forest fire danger level (Tier I to V) based on meteorological index under Decree 156/2018.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plot_id": {"type": "string", "description": "Forest plot identifier"},
                "temperature_c": {"type": "number", "description": "Air temperature in Celsius"},
                "humidity_pct": {"type": "number", "description": "Relative humidity percentage"},
                "wind_speed_kmh": {"type": "number", "description": "Wind speed in km/h"},
                "consecutive_dry_days": {"type": "integer", "description": "Consecutive days without rain"},
            },
            "required": ["plot_id"],
        },
    },
    {
        "name": "mekong_forestry_list",
        "description": "Query registered forest plots, timber consignments, alternative afforestations, PFES records, or fire danger assessments.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: plots, timber, afforestation, pfes, fire"},
                "limit": {"type": "integer", "description": "Maximum records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_forestry_status",
        "description": "Retrieve Vietnamese forestry, VNTLAS timber, PFES, and forest carbon telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_water_plant",
        "description": "Register clean water treatment plant with capacity, source, and operator.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Plant name"},
                "capacity": {"type": "number", "description": "Design capacity in m3/day"},
                "source": {"type": "string", "description": "Raw water intake source"},
                "province": {"type": "string", "description": "Province / City"},
                "technology": {"type": "string", "description": "Water treatment technology"},
                "operator": {"type": "string", "description": "Operating water supply utility"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_water_test",
        "description": "Audit drinking water quality against QCVN 01-1:2018/BYT statutory standards.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plant_id": {"type": "string", "description": "Water plant ID"},
                "location": {"type": "string", "description": "Sample location"},
                "ph": {"type": "number", "description": "pH level (6.0 - 8.5)"},
                "turbidity": {"type": "number", "description": "Turbidity NTU (<= 2.0)"},
                "chlorine": {"type": "number", "description": "Free residual chlorine mg/L (0.2 - 1.0)"},
                "coliform": {"type": "number", "description": "Coliform count CFU/100mL (< 3)"},
                "ecoli": {"type": "number", "description": "E. coli count CFU/100mL (= 0)"},
                "metal_pass": {"type": "boolean", "description": "Whether heavy metal thresholds are safe"},
                "tester": {"type": "string", "description": "Testing laboratory"},
            },
            "required": ["plant_id"],
        },
    },
    {
        "name": "mekong_water_bill",
        "description": "Calculate statutory progressive water consumption bill, wastewater fee & VAT (Circular 44/2021/TT-BTC).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Customer code"},
                "name": {"type": "string", "description": "Customer name"},
                "volume": {"type": "number", "description": "Water consumption in m3"},
                "category": {"type": "string", "description": "Customer category: DOMESTIC, ADMINISTRATIVE, PUBLIC_SERVICE, MANUFACTURING, COMMERCIAL"},
                "month": {"type": "string", "description": "Billing month (YYYY-MM)"},
            },
            "required": ["code", "name", "volume"],
        },
    },
    {
        "name": "mekong_water_nrw",
        "description": "Audit non-revenue water (NRW) leakage rate under Decision 2147/QĐ-TTg (target <= 15%).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "plant_id": {"type": "string", "description": "Plant or network ID"},
                "produced": {"type": "number", "description": "Total produced volume in m3"},
                "billed": {"type": "number", "description": "Total billed consumption volume in m3"},
                "period": {"type": "string", "description": "Audit period (e.g. 2026-Q1)"},
                "target": {"type": "number", "description": "Statutory maximum loss target % (default: 15.0)"},
                "notes": {"type": "string", "description": "Auditor notes"},
            },
            "required": ["plant_id", "produced", "billed"],
        },
    },
    {
        "name": "mekong_water_discharge",
        "description": "Inspect industrial wastewater discharge against QCVN 40:2011/BTNMT (Column A & B limits).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "facility": {"type": "string", "description": "Discharging facility name"},
                "park": {"type": "string", "description": "Industrial zone or location"},
                "flow": {"type": "number", "description": "Discharge flow rate in m3/day"},
                "column": {"type": "string", "description": "Standard column: COLUMN_A or COLUMN_B"},
                "bod5": {"type": "number", "description": "BOD5 mg/L"},
                "cod": {"type": "number", "description": "COD mg/L"},
                "tss": {"type": "number", "description": "Total suspended solids mg/L"},
                "nh4": {"type": "number", "description": "Ammonium mg/L"},
                "ph": {"type": "number", "description": "pH level"},
            },
            "required": ["facility"],
        },
    },
    {
        "name": "mekong_water_list",
        "description": "Query registered water plants, quality tests, tariff bills, NRW audits, or wastewater inspections.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: plants, tests, bills, nrw, discharges"},
                "limit": {"type": "integer", "description": "Max records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_water_status",
        "description": "Retrieve Vietnamese clean water utilities, drainage, and wastewater treatment telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_medtech_device",
        "description": "Classify medical device risk class (A/B/C/D) and register market authorization under Decree 98/2021 & 07/2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Medical device commercial name"},
                "risk_class": {"type": "string", "description": "Risk class: CLASS_A, CLASS_B, CLASS_C, CLASS_D"},
                "maker": {"type": "string", "description": "Manufacturer name"},
                "origin": {"type": "string", "description": "Country of origin"},
                "importer": {"type": "string", "description": "Importing or distributing entity"},
                "use": {"type": "string", "description": "Intended medical purpose"},
                "cfs": {"type": "string", "description": "Reference foreign regulatory agency: FDA, CE, PMDA, TGA, HEALTH_CANADA"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_medtech_price",
        "description": "Declare medical device wholesale and retail prices and verify markup cap (<= 35%) under Decree 07/2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Medical device ID (DEV-xxxx)"},
                "name": {"type": "string", "description": "Medical device commercial name"},
                "cif": {"type": "number", "description": "CIF import cost or production cost in VND"},
                "wholesale": {"type": "number", "description": "Declared wholesale price in VND"},
                "retail": {"type": "number", "description": "Declared maximum retail price in VND"},
            },
            "required": ["device_id", "name", "cif", "wholesale", "retail"],
        },
    },
    {
        "name": "mekong_medtech_facility",
        "description": "Evaluate healthcare facility operating license conditions under Law on Medical Examination 2023.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Healthcare facility name"},
                "fac_type": {"type": "string", "description": "Facility type: GENERAL_HOSPITAL, SPECIALIZED_HOSPITAL, POLYCLINIC, SPECIALIZED_CLINIC"},
                "province": {"type": "string", "description": "Province / City"},
                "beds": {"type": "integer", "description": "Inpatient bed capacity"},
                "area": {"type": "number", "description": "Total floor area in m2"},
                "cmo": {"type": "string", "description": "Chief medical officer name"},
                "months": {"type": "integer", "description": "Months of continuous clinical practice with medical certificate"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "mekong_medtech_trial",
        "description": "Register medical device clinical evaluation trial protocol and ethics approval under Circular 29/2023/TT-BYT.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "device_id": {"type": "string", "description": "Medical device ID"},
                "title": {"type": "string", "description": "Clinical trial protocol title"},
                "phase": {"type": "integer", "description": "Trial phase (1, 2, or 3)"},
                "pi": {"type": "string", "description": "Principal investigator name"},
                "site": {"type": "string", "description": "Study site hospital name"},
                "subjects": {"type": "integer", "description": "Target subject count"},
                "irb": {"type": "boolean", "description": "Whether ethics IRB committee has approved protocol"},
            },
            "required": ["device_id", "title"],
        },
    },
    {
        "name": "mekong_medtech_list",
        "description": "Query registered medical devices, price declarations, healthcare facilities, or clinical trials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: devices, prices, facilities, trials"},
                "limit": {"type": "integer", "description": "Max records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_medtech_status",
        "description": "Retrieve Vietnamese medical devices, healthcare facility licensing, and clinical evaluation telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "mekong_livestock_farm",
        "description": "Register livestock farm, compute statutory Livestock Units (ĐVN), scale, and regional density.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "farm_name": {"type": "string", "description": "Farm name"},
                "owner_name": {"type": "string", "description": "Farm owner"},
                "province": {"type": "string", "description": "Province"},
                "animal_type": {"type": "string", "description": "Animal type (e.g. PIG_FATTENER, CATTLE_BEEF)"},
                "head_count": {"type": "integer", "description": "Number of animals"},
                "agricultural_land_ha": {"type": "number", "description": "Agricultural land area in hectares"},
                "region": {"type": "string", "description": "Ecological region"},
            },
            "required": ["farm_name"],
        },
    },
    {
        "name": "mekong_livestock_distance",
        "description": "Audit farm biosecurity buffer distances against residential areas, water sources, and other farms under Article 5 Decree 13/2020/NĐ-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string", "description": "Farm ID (LVF-xxxx)"},
                "farm_scale": {"type": "string", "description": "Farm scale (LARGE_SCALE, MEDIUM_SCALE, SMALL_SCALE, HOUSEHOLD)"},
                "residential_distance_m": {"type": "number", "description": "Distance to residential areas in meters"},
                "water_source_distance_m": {"type": "number", "description": "Distance to domestic water source in meters"},
                "farm_to_farm_distance_m": {"type": "number", "description": "Distance to nearest livestock farm in meters"},
            },
            "required": ["farm_id"],
        },
    },
    {
        "name": "mekong_livestock_feed",
        "description": "Inspect animal feed quality, mycotoxins (Aflatoxin B1), heavy metals, and prohibited beta-agonists under QCVN 01-183.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "Feed product name"},
                "feed_type": {"type": "string", "description": "Feed type"},
                "manufacturer": {"type": "string", "description": "Manufacturer"},
                "crude_protein_pct": {"type": "number", "description": "Crude protein percentage"},
                "aflatoxin_b1_ppb": {"type": "number", "description": "Aflatoxin B1 concentration in ppb"},
                "lead_pb_ppm": {"type": "number", "description": "Lead Pb concentration in ppm"},
                "banned_substance": {"type": "string", "description": "Banned substance detected (Salbutamol, Clenbuterol, Ractopamine)"},
            },
            "required": ["product_name"],
        },
    },
    {
        "name": "mekong_livestock_waste",
        "description": "Audit livestock waste management and Biogas digester volume adequacy under Decree 46/2022/NĐ-CP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "farm_id": {"type": "string", "description": "Farm ID (LVF-xxxx)"},
                "livestock_units": {"type": "number", "description": "Total Livestock Units (ĐVN)"},
                "treatment_method": {"type": "string", "description": "Waste treatment method"},
                "biogas_volume_m3": {"type": "number", "description": "Actual biogas digester volume in m3"},
                "is_cattle": {"type": "boolean", "description": "True if cattle/buffalo (1.2 m3/ĐVN), False if pig/poultry (0.8 m3/ĐVN)"},
            },
            "required": ["farm_id"],
        },
    },
    {
        "name": "mekong_livestock_list",
        "description": "Query registered livestock farms, biosecurity audits, feed tests, or waste/biogas projects.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Category: farms, biosecurity, feed, waste"},
                "limit": {"type": "integer", "description": "Max records to return"},
            },
            "required": [],
        },
    },
    {
        "name": "mekong_livestock_status",
        "description": "Retrieve Vietnamese animal husbandry, biosecurity, feed standards, and waste telemetry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

CORE_HANDLERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "mekong_memory_store": handle_memory_store,
    "mekong_memory_recall": handle_memory_recall,
    "mekong_memory_search": handle_memory_search,
    "mekong_plan_create": handle_plan_create,
    "mekong_plan_update": handle_plan_update,
    "mekong_plan_get": handle_plan_get,
    "mekong_task_create": handle_task_create,
    "mekong_task_update": handle_task_update,
    "mekong_task_list": handle_task_list,
    "mekong_agent_list": handle_agent_list,
    "mekong_agent_info": handle_agent_info,
    "mekong_agent_route": handle_agent_route,
    "mekong_status": handle_status,
    "mekong_cost_estimate": handle_cost_estimate,
    "mekong_subagent_dispatch": handle_subagent_dispatch,
    "mekong_pev_plan": handle_pev_plan,
    "mekong_pev_checkpoint": handle_pev_checkpoint,
    "mekong_pev_rollback": handle_pev_rollback,
    "mekong_swarm_status": handle_swarm_status,
    "mekong_eval_query": handle_eval_query,
    "mekong_recipe_evolve": handle_recipe_evolve,
    "mekong_mission_metrics": handle_mission_metrics,
    "mekong_palette_search": handle_palette_search,
    "mekong_tui_dashboard_status": handle_tui_dashboard_status,
    "mekong_benchmark_run": handle_benchmark_run,
    "mekong_chaos_simulate": handle_chaos_simulate,
    "mekong_gateway_status": handle_gateway_status,
    "mekong_gateway_rate_limit": handle_gateway_rate_limit,
    "gateway_status": handle_gateway_status,
    "mekong_watch_status": handle_watch_status,
    "mekong_self_repair": handle_self_repair,
    "watch_status": handle_watch_status,
    "self_repair": handle_self_repair,
    "mekong_package_build": handle_package_build,
    "mekong_sandbox_exec": handle_sandbox_exec,
    "package_build": handle_package_build,
    "sandbox_exec": handle_sandbox_exec,
    "mekong_consensus_vote": handle_consensus_vote,
    "mekong_consensus_debate": handle_consensus_debate,
    "consensus_vote": handle_consensus_vote,
    "consensus_debate": handle_consensus_debate,
    "mekong_semantic_recall": handle_semantic_recall,
    "mekong_knowledge_graph_query": handle_knowledge_graph_query,
    "semantic_recall": handle_semantic_recall,
    "knowledge_graph_query": handle_knowledge_graph_query,
    "mekong_telemetry_metrics": handle_telemetry_metrics,
    "mekong_trace_query": handle_trace_query,
    "telemetry_metrics": handle_telemetry_metrics,
    "trace_query": handle_trace_query,
    "mekong_queue_enqueue": handle_queue_enqueue,
    "mekong_queue_status": handle_queue_status,
    "mekong_queue_dlq_action": handle_queue_dlq_action,
    "queue_enqueue": handle_queue_enqueue,
    "queue_status": handle_queue_status,
    "queue_dlq_action": handle_queue_dlq_action,
    "mekong_pipeline_run": handle_pipeline_run,
    "mekong_pipeline_status": handle_pipeline_status,
    "pipeline_run": handle_pipeline_run,
    "pipeline_status": handle_pipeline_status,
    "mekong_worktree_create": handle_worktree_create,
    "mekong_worktree_list": handle_worktree_list,
    "mekong_worktree_status": handle_worktree_status,
    "mekong_worktree_remove": handle_worktree_remove,
    "worktree_create": handle_worktree_create,
    "worktree_list": handle_worktree_list,
    "worktree_status": handle_worktree_status,
    "worktree_remove": handle_worktree_remove,
    "mekong_ship_preflight": handle_ship_preflight,
    "mekong_ship_run": handle_ship_run,
    "ship_preflight": handle_ship_preflight,
    "ship_run": handle_ship_run,
    "mekong_daily_report": handle_daily_report,
    "mekong_daily_focus": handle_daily_focus,
    "daily_report": handle_daily_report,
    "daily_focus": handle_daily_focus,
    "mekong_quick_start_plan": handle_quick_start_plan,
    "mekong_quick_start_create": handle_quick_start_create,
    "quick_start_plan": handle_quick_start_plan,
    "quick_start_create": handle_quick_start_create,
    "mekong_cto_scorecard": handle_cto_scorecard,
    "mekong_cto_review": handle_cto_review,
    "mekong_cto_architect": handle_cto_architect,
    "cto_scorecard": handle_cto_scorecard,
    "cto_review": handle_cto_review,
    "cto_architect": handle_cto_architect,
    "mekong_sales_pipeline": handle_sales_pipeline,
    "mekong_sales_deal_add": handle_sales_deal_add,
    "mekong_sales_outreach": handle_sales_outreach,
    "sales_pipeline": handle_sales_pipeline,
    "sales_deal_add": handle_sales_deal_add,
    "sales_outreach": handle_sales_outreach,
    "mekong_marketing_metrics": handle_marketing_metrics,
    "mekong_marketing_campaign_create": handle_marketing_campaign_create,
    "mekong_marketing_content_generate": handle_marketing_content_generate,
    "marketing_metrics": handle_marketing_metrics,
    "marketing_campaign_create": handle_marketing_campaign_create,
    "marketing_content_generate": handle_marketing_content_generate,
    "mekong_dev_audit": handle_dev_audit,
    "mekong_dev_scaffold": handle_dev_scaffold,
    "mekong_dev_review": handle_dev_review,
    "dev_audit": handle_dev_audit,
    "dev_scaffold": handle_dev_scaffold,
    "dev_review": handle_dev_review,
    "mekong_ops_health_sweep": handle_ops_health_sweep,
    "mekong_ops_incident_create": handle_ops_incident_create,
    "mekong_ops_incident_list": handle_ops_incident_list,
    "ops_health_sweep": handle_ops_health_sweep,
    "ops_incident_create": handle_ops_incident_create,
    "ops_incident_list": handle_ops_incident_list,
    "mekong_support_onboard_status": handle_support_onboard_status,
    "mekong_support_feedback_submit": handle_support_feedback_submit,
    "mekong_support_triage": handle_support_triage,
    "support_onboard_status": handle_support_onboard_status,
    "support_feedback_submit": handle_support_feedback_submit,
    "support_triage": handle_support_triage,
    "mekong_consulting_pricing": handle_consulting_pricing,
    "mekong_consulting_proposal": handle_consulting_proposal,
    "mekong_consulting_outreach": handle_consulting_outreach,
    "consulting_pricing": handle_consulting_pricing,
    "consulting_proposal": handle_consulting_proposal,
    "consulting_outreach": handle_consulting_outreach,
    "mekong_revenue_metrics": handle_revenue_metrics,
    "mekong_revenue_record": handle_revenue_record,
    "mekong_revenue_forecast": handle_revenue_forecast,
    "revenue_metrics": handle_revenue_metrics,
    "revenue_record": handle_revenue_record,
    "revenue_forecast": handle_revenue_forecast,
    "mekong_content_generate": handle_content_generate,
    "mekong_content_calendar": handle_content_calendar,
    "mekong_content_channels": handle_content_channels,
    "content_generate": handle_content_generate,
    "content_calendar": handle_content_calendar,
    "content_channels": handle_content_channels,
    "mekong_copywriting_generate": handle_copywriting_generate,
    "mekong_copywriting_headline": handle_copywriting_headline,
    "mekong_copywriting_cta": handle_copywriting_cta,
    "copywriting_generate": handle_copywriting_generate,
    "copywriting_headline": handle_copywriting_headline,
    "copywriting_cta": handle_copywriting_cta,
    "mekong_billing_simulate": handle_billing_simulate,
    "mekong_billing_record_usage": handle_billing_record_usage,
    "mekong_billing_status": handle_billing_status,
    "billing_simulate": handle_billing_simulate,
    "billing_record_usage": handle_billing_record_usage,
    "billing_status": handle_billing_status,
    "mekong_vendor_onboard": handle_vendor_onboard,
    "mekong_vendor_list": handle_vendor_list,
    "mekong_vendor_assess": handle_vendor_assess,
    "vendor_onboard": handle_vendor_onboard,
    "vendor_list": handle_vendor_list,
    "vendor_assess": handle_vendor_assess,
    "mekong_founder_assess": handle_founder_assess,
    "mekong_founder_review": handle_founder_review,
    "mekong_founder_list": handle_founder_list,
    "founder_assess": handle_founder_assess,
    "founder_review": handle_founder_review,
    "founder_list": handle_founder_list,
    "mekong_governance_propose": handle_governance_propose,
    "mekong_governance_vote": handle_governance_vote,
    "mekong_governance_tally": handle_governance_tally,
    "mekong_governance_list": handle_governance_list,
    "governance_propose": handle_governance_propose,
    "governance_vote": handle_governance_vote,
    "governance_tally": handle_governance_tally,
    "governance_list": handle_governance_list,
    "mekong_particle_init": handle_particle_init,
    "mekong_particle_status": handle_particle_status,
    "mekong_particle_connect": handle_particle_connect,
    "mekong_particle_cell_run": handle_particle_cell_run,
    "particle_init": handle_particle_init,
    "particle_status": handle_particle_status,
    "particle_connect": handle_particle_connect,
    "particle_cell_run": handle_particle_cell_run,
    "mekong_thue_tncn": handle_thue_tncn,
    "mekong_thue_tndn": handle_thue_tndn,
    "mekong_thue_gtgt": handle_thue_gtgt,
    "mekong_thue_status": handle_thue_status,
    "thue_tncn": handle_thue_tncn,
    "thue_tndn": handle_thue_tndn,
    "thue_gtgt": handle_thue_gtgt,
    "thue_status": handle_thue_status,
    "mekong_ke_toan_create": handle_ke_toan_create,
    "mekong_ke_toan_xml": handle_ke_toan_xml,
    "mekong_ke_toan_journal": handle_ke_toan_journal,
    "mekong_ke_toan_status": handle_ke_toan_status,
    "ke_toan_create": handle_ke_toan_create,
    "ke_toan_xml": handle_ke_toan_xml,
    "ke_toan_journal": handle_ke_toan_journal,
    "ke_toan_status": handle_ke_toan_status,
    "mekong_zalo_send": handle_zalo_send,
    "mekong_zalo_broadcast": handle_zalo_broadcast,
    "mekong_zalo_followers": handle_zalo_followers,
    "mekong_zalo_caption": handle_zalo_caption,
    "mekong_zalo_status": handle_zalo_status,
    "zalo_send": handle_zalo_send,
    "zalo_broadcast": handle_zalo_broadcast,
    "zalo_followers": handle_zalo_followers,
    "zalo_caption": handle_zalo_caption,
    "zalo_status": handle_zalo_status,
    "mekong_bhxh_calc": handle_bhxh_calc,
    "mekong_bhxh_employees": handle_bhxh_employees,
    "mekong_bhxh_declaration": handle_bhxh_declaration,
    "mekong_bhxh_status": handle_bhxh_status,
    "bhxh_calc": handle_bhxh_calc,
    "bhxh_employees": handle_bhxh_employees,
    "bhxh_declaration": handle_bhxh_declaration,
    "bhxh_status": handle_bhxh_status,
    "mekong_ocop_eval": handle_ocop_eval,
    "mekong_ocop_products": handle_ocop_products,
    "mekong_ocop_listing": handle_ocop_listing,
    "mekong_ocop_compliance": handle_ocop_compliance,
    "mekong_ocop_status": handle_ocop_status,
    "ocop_eval": handle_ocop_eval,
    "ocop_products": handle_ocop_products,
    "ocop_listing": handle_ocop_listing,
    "ocop_compliance": handle_ocop_compliance,
    "ocop_status": handle_ocop_status,
    "mekong_vietqr_generate": handle_vietqr_generate,
    "mekong_vietqr_banks": handle_vietqr_banks,
    "mekong_vietqr_transactions": handle_vietqr_transactions,
    "mekong_vietqr_record": handle_vietqr_record,
    "mekong_vietqr_status": handle_vietqr_status,
    "vietqr_generate": handle_vietqr_generate,
    "vietqr_banks": handle_vietqr_banks,
    "vietqr_transactions": handle_vietqr_transactions,
    "vietqr_record": handle_vietqr_record,
    "vietqr_status": handle_vietqr_status,
    "mekong_audit_run": handle_audit_run,
    "mekong_audit_controls": handle_audit_controls,
    "mekong_audit_findings": handle_audit_findings,
    "mekong_audit_status": handle_audit_status,
    "audit_run": handle_audit_run,
    "audit_controls": handle_audit_controls,
    "audit_findings": handle_audit_findings,
    "audit_status": handle_audit_status,
    "mekong_payroll_gross_to_net": handle_payroll_gross_to_net,
    "mekong_payroll_net_to_gross": handle_payroll_net_to_gross,
    "mekong_payroll_payslip": handle_payroll_payslip,
    "mekong_payroll_list": handle_payroll_list,
    "mekong_payroll_status": handle_payroll_status,
    "payroll_gross_to_net": handle_payroll_gross_to_net,
    "payroll_net_to_gross": handle_payroll_net_to_gross,
    "payroll_payslip": handle_payroll_payslip,
    "payroll_list": handle_payroll_list,
    "payroll_status": handle_payroll_status,
    "mekong_corporate_charter": handle_corporate_charter,
    "mekong_corporate_resolution": handle_corporate_resolution,
    "mekong_corporate_dossier": handle_corporate_dossier,
    "mekong_corporate_list": handle_corporate_list,
    "mekong_corporate_status": handle_corporate_status,
    "corporate_charter": handle_corporate_charter,
    "corporate_resolution": handle_corporate_resolution,
    "corporate_dossier": handle_corporate_dossier,
    "corporate_list": handle_corporate_list,
    "corporate_status": handle_corporate_status,
    "mekong_fdi_market_access": handle_fdi_market_access,
    "mekong_fdi_remittance": handle_fdi_remittance,
    "mekong_fdi_foreign_loan": handle_fdi_foreign_loan,
    "mekong_fdi_irc": handle_fdi_irc,
    "mekong_fdi_status": handle_fdi_status,
    "fdi_market_access": handle_fdi_market_access,
    "fdi_remittance": handle_fdi_remittance,
    "fdi_foreign_loan": handle_fdi_foreign_loan,
    "fdi_irc": handle_fdi_irc,
    "fdi_status": handle_fdi_status,
    "mekong_ip_trademark": handle_ip_trademark,
    "mekong_ip_search": handle_ip_search,
    "mekong_ip_patent": handle_ip_patent,
    "mekong_ip_copyright": handle_ip_copyright,
    "mekong_ip_fees": handle_ip_fees,
    "mekong_ip_status": handle_ip_status,
    "ip_trademark": handle_ip_trademark,
    "ip_search": handle_ip_search,
    "ip_patent": handle_ip_patent,
    "ip_copyright": handle_ip_copyright,
    "ip_fees": handle_ip_fees,
    "ip_status": handle_ip_status,
    "mekong_customs_hs_lookup": handle_customs_hs_lookup,
    "mekong_customs_duty_calc": handle_customs_duty_calc,
    "mekong_customs_channel": handle_customs_channel,
    "mekong_customs_declare": handle_customs_declare,
    "mekong_customs_origin": handle_customs_origin,
    "mekong_customs_status": handle_customs_status,
    "customs_hs_lookup": handle_customs_hs_lookup,
    "customs_duty_calc": handle_customs_duty_calc,
    "customs_channel": handle_customs_channel,
    "customs_declare": handle_customs_declare,
    "customs_origin": handle_customs_origin,
    "customs_status": handle_customs_status,
    "mekong_contract_draft": handle_contract_draft,
    "mekong_contract_risk_check": handle_contract_risk_check,
    "mekong_contract_sign": handle_contract_sign,
    "mekong_contract_verify": handle_contract_verify,
    "mekong_contract_list": handle_contract_list,
    "mekong_contract_status": handle_contract_status,
    "contract_draft": handle_contract_draft,
    "contract_risk_check": handle_contract_risk_check,
    "contract_sign": handle_contract_sign,
    "contract_verify": handle_contract_verify,
    "contract_list": handle_contract_list,
    "contract_status": handle_contract_status,
    "mekong_tender_method": handle_tender_method,
    "mekong_tender_create": handle_tender_create,
    "mekong_tender_eval": handle_tender_eval,
    "mekong_tender_collusion_scan": handle_tender_collusion_scan,
    "mekong_tender_list": handle_tender_list,
    "mekong_tender_status": handle_tender_status,
    "tender_method": handle_tender_method,
    "tender_create": handle_tender_create,
    "tender_eval": handle_tender_eval,
    "tender_collusion_scan": handle_tender_collusion_scan,
    "tender_list": handle_tender_list,
    "tender_status": handle_tender_status,
    "mekong_realestate_finance": handle_realestate_finance,
    "mekong_realestate_density": handle_realestate_density,
    "mekong_realestate_audit": handle_realestate_audit,
    "mekong_realestate_draft": handle_realestate_draft,
    "mekong_realestate_list": handle_realestate_list,
    "mekong_realestate_status": handle_realestate_status,
    "realestate_finance": handle_realestate_finance,
    "realestate_density": handle_realestate_density,
    "realestate_audit": handle_realestate_audit,
    "realestate_draft": handle_realestate_draft,
    "realestate_list": handle_realestate_list,
    "realestate_status": handle_realestate_status,
    "mekong_esg_ghg": handle_esg_ghg,
    "mekong_esg_cbam": handle_esg_cbam,
    "mekong_esg_audit": handle_esg_audit,
    "mekong_esg_carbon_trade": handle_esg_carbon_trade,
    "mekong_esg_list": handle_esg_list,
    "mekong_esg_status": handle_esg_status,
    "esg_ghg": handle_esg_ghg,
    "esg_cbam": handle_esg_cbam,
    "esg_audit": handle_esg_audit,
    "esg_carbon_trade": handle_esg_carbon_trade,
    "esg_list": handle_esg_list,
    "esg_status": handle_esg_status,
    "mekong_supplychain_plot": handle_supplychain_plot,
    "mekong_supplychain_batch": handle_supplychain_batch,
    "mekong_supplychain_event": handle_supplychain_event,
    "mekong_supplychain_eudr": handle_supplychain_eudr,
    "mekong_supplychain_trace": handle_supplychain_trace,
    "mekong_supplychain_status": handle_supplychain_status,
    "supplychain_plot": handle_supplychain_plot,
    "supplychain_batch": handle_supplychain_batch,
    "supplychain_event": handle_supplychain_event,
    "supplychain_eudr": handle_supplychain_eudr,
    "supplychain_trace": handle_supplychain_trace,
    "supplychain_status": handle_supplychain_status,
    "mekong_labor_permit": handle_labor_permit,
    "mekong_labor_overtime": handle_labor_overtime,
    "mekong_labor_caps": handle_labor_caps,
    "mekong_labor_severance": handle_labor_severance,
    "mekong_labor_regulations": handle_labor_regulations,
    "mekong_labor_list": handle_labor_list,
    "mekong_labor_status": handle_labor_status,
    "labor_permit": handle_labor_permit,
    "labor_overtime": handle_labor_overtime,
    "labor_caps": handle_labor_caps,
    "labor_severance": handle_labor_severance,
    "labor_regulations": handle_labor_regulations,
    "labor_list": handle_labor_list,
    "labor_status": handle_labor_status,
    "mekong_maritime_vessel": handle_maritime_vessel,
    "mekong_maritime_container": handle_maritime_container,
    "mekong_maritime_tariff": handle_maritime_tariff,
    "mekong_maritime_manifest": handle_maritime_manifest,
    "mekong_maritime_list": handle_maritime_list,
    "mekong_maritime_status": handle_maritime_status,
    "maritime_vessel": handle_maritime_vessel,
    "maritime_container": handle_maritime_container,
    "maritime_tariff": handle_maritime_tariff,
    "maritime_manifest": handle_maritime_manifest,
    "maritime_list": handle_maritime_list,
    "maritime_status": handle_maritime_status,
    "mekong_energy_solar": handle_energy_solar,
    "mekong_energy_dppa": handle_energy_dppa,
    "mekong_energy_ev": handle_energy_ev,
    "mekong_energy_list": handle_energy_list,
    "mekong_energy_status": handle_energy_status,
    "energy_solar": handle_energy_solar,
    "energy_dppa": handle_energy_dppa,
    "energy_ev": handle_energy_ev,
    "energy_list": handle_energy_list,
    "energy_status": handle_energy_status,
    "mekong_privacy_audit": handle_privacy_audit,
    "mekong_privacy_dpia": handle_privacy_dpia,
    "mekong_privacy_transfer": handle_privacy_transfer,
    "mekong_privacy_breach": handle_privacy_breach,
    "mekong_privacy_dsar": handle_privacy_dsar,
    "mekong_privacy_list": handle_privacy_list,
    "mekong_privacy_status": handle_privacy_status,
    "privacy_audit": handle_privacy_audit,
    "privacy_dpia": handle_privacy_dpia,
    "privacy_transfer": handle_privacy_transfer,
    "privacy_breach": handle_privacy_breach,
    "privacy_dsar": handle_privacy_dsar,
    "privacy_list": handle_privacy_list,
    "privacy_status": handle_privacy_status,
    "mekong_aviation_flight": handle_aviation_flight,
    "mekong_aviation_cargo": handle_aviation_cargo,
    "mekong_aviation_tariff": handle_aviation_tariff,
    "mekong_aviation_dg": handle_aviation_dg,
    "mekong_aviation_list": handle_aviation_list,
    "mekong_aviation_status": handle_aviation_status,
    "aviation_flight": handle_aviation_flight,
    "aviation_cargo": handle_aviation_cargo,
    "aviation_tariff": handle_aviation_tariff,
    "aviation_dg": handle_aviation_dg,
    "aviation_list": handle_aviation_list,
    "aviation_status": handle_aviation_status,
    "mekong_ecom_fct": handle_ecom_fct,
    "mekong_ecom_audit": handle_ecom_audit,
    "mekong_ecom_order": handle_ecom_order,
    "mekong_ecom_parcel": handle_ecom_parcel,
    "mekong_ecom_list": handle_ecom_list,
    "mekong_ecom_status": handle_ecom_status,
    "ecom_fct": handle_ecom_fct,
    "ecom_audit": handle_ecom_audit,
    "ecom_order": handle_ecom_order,
    "ecom_parcel": handle_ecom_parcel,
    "ecom_list": handle_ecom_list,
    "ecom_status": handle_ecom_status,
    "mekong_telecom_spectrum": handle_telecom_spectrum,
    "mekong_telecom_ott": handle_telecom_ott,
    "mekong_telecom_bts": handle_telecom_bts,
    "mekong_telecom_number": handle_telecom_number,
    "mekong_telecom_list": handle_telecom_list,
    "mekong_telecom_status": handle_telecom_status,
    "telecom_spectrum": handle_telecom_spectrum,
    "telecom_ott": handle_telecom_ott,
    "telecom_bts": handle_telecom_bts,
    "telecom_number": handle_telecom_number,
    "telecom_list": handle_telecom_list,
    "telecom_status": handle_telecom_status,
    "mekong_pharma_drug": handle_pharma_drug,
    "mekong_pharma_gsp": handle_pharma_gsp,
    "mekong_pharma_batch": handle_pharma_batch,
    "mekong_pharma_price": handle_pharma_price,
    "mekong_pharma_list": handle_pharma_list,
    "mekong_pharma_status": handle_pharma_status,
    "pharma_drug": handle_pharma_drug,
    "pharma_gsp": handle_pharma_gsp,
    "pharma_batch": handle_pharma_batch,
    "pharma_price": handle_pharma_price,
    "pharma_list": handle_pharma_list,
    "pharma_status": handle_pharma_status,
    "mekong_petrol_price": handle_petrol_price,
    "mekong_petrol_reserve": handle_petrol_reserve,
    "mekong_petrol_quality": handle_petrol_quality,
    "mekong_petrol_pump": handle_petrol_pump,
    "mekong_petrol_list": handle_petrol_list,
    "mekong_petrol_status": handle_petrol_status,
    "petrol_price": handle_petrol_price,
    "petrol_reserve": handle_petrol_reserve,
    "petrol_quality": handle_petrol_quality,
    "petrol_pump": handle_petrol_pump,
    "petrol_list": handle_petrol_list,
    "petrol_status": handle_petrol_status,
    "mekong_fishery_vessel": handle_fishery_vessel,
    "mekong_fishery_vms": handle_fishery_vms,
    "mekong_fishery_cert": handle_fishery_cert,
    "mekong_fishery_quality": handle_fishery_quality,
    "mekong_fishery_list": handle_fishery_list,
    "mekong_fishery_status": handle_fishery_status,
    "fishery_vessel": handle_fishery_vessel,
    "fishery_vms": handle_fishery_vms,
    "fishery_cert": handle_fishery_cert,
    "fishery_quality": handle_fishery_quality,
    "fishery_list": handle_fishery_list,
    "fishery_status": handle_fishery_status,
    "mekong_construction_project": handle_construction_project,
    "mekong_construction_permit": handle_construction_permit,
    "mekong_construction_fidic": handle_construction_fidic,
    "mekong_construction_pccc": handle_construction_pccc,
    "mekong_construction_accept": handle_construction_accept,
    "mekong_construction_list": handle_construction_list,
    "mekong_construction_status": handle_construction_status,
    "construction_project": handle_construction_project,
    "construction_permit": handle_construction_permit,
    "construction_fidic": handle_construction_fidic,
    "construction_pccc": handle_construction_pccc,
    "construction_accept": handle_construction_accept,
    "construction_list": handle_construction_list,
    "construction_status": handle_construction_status,
    "mekong_mining_license": handle_mining_license,
    "mekong_mining_rights_fee": handle_mining_rights_fee,
    "mekong_mining_royalty": handle_mining_royalty,
    "mekong_mining_rehab": handle_mining_rehab,
    "mekong_mining_sand": handle_mining_sand,
    "mekong_mining_list": handle_mining_list,
    "mekong_mining_status": handle_mining_status,
    "mining_license": handle_mining_license,
    "mining_rights_fee": handle_mining_rights_fee,
    "mining_royalty": handle_mining_royalty,
    "mining_rehab": handle_mining_rehab,
    "mining_sand": handle_mining_sand,
    "mining_list": handle_mining_list,
    "mining_status": handle_mining_status,
    "mekong_forestry_plot": handle_forestry_plot,
    "mekong_forestry_timber": handle_forestry_timber,
    "mekong_forestry_afforestation": handle_forestry_afforestation,
    "mekong_forestry_pfes": handle_forestry_pfes,
    "mekong_forestry_fire": handle_forestry_fire,
    "mekong_forestry_list": handle_forestry_list,
    "mekong_forestry_status": handle_forestry_status,
    "forestry_plot": handle_forestry_plot,
    "forestry_timber": handle_forestry_timber,
    "forestry_afforestation": handle_forestry_afforestation,
    "forestry_pfes": handle_forestry_pfes,
    "forestry_fire": handle_forestry_fire,
    "forestry_list": handle_forestry_list,
    "forestry_status": handle_forestry_status,
    "mekong_water_plant": handle_water_plant,
    "mekong_water_test": handle_water_test,
    "mekong_water_bill": handle_water_bill,
    "mekong_water_nrw": handle_water_nrw,
    "mekong_water_discharge": handle_water_discharge,
    "mekong_water_list": handle_water_list,
    "mekong_water_status": handle_water_status,
    "water_plant": handle_water_plant,
    "water_test": handle_water_test,
    "water_bill": handle_water_bill,
    "water_nrw": handle_water_nrw,
    "water_discharge": handle_water_discharge,
    "water_list": handle_water_list,
    "water_status": handle_water_status,
    "mekong_medtech_device": handle_medtech_device,
    "mekong_medtech_price": handle_medtech_price,
    "mekong_medtech_facility": handle_medtech_facility,
    "mekong_medtech_trial": handle_medtech_trial,
    "mekong_medtech_list": handle_medtech_list,
    "mekong_medtech_status": handle_medtech_status,
    "medtech_device": handle_medtech_device,
    "medtech_price": handle_medtech_price,
    "medtech_facility": handle_medtech_facility,
    "medtech_trial": handle_medtech_trial,
    "medtech_list": handle_medtech_list,
    "medtech_status": handle_medtech_status,
    "mekong_livestock_farm": handle_livestock_farm,
    "mekong_livestock_distance": handle_livestock_distance,
    "mekong_livestock_feed": handle_livestock_feed,
    "mekong_livestock_waste": handle_livestock_waste,
    "mekong_livestock_list": handle_livestock_list,
    "mekong_livestock_status": handle_livestock_status,
    "livestock_farm": handle_livestock_farm,
    "livestock_distance": handle_livestock_distance,
    "livestock_feed": handle_livestock_feed,
    "livestock_waste": handle_livestock_waste,
    "livestock_list": handle_livestock_list,
    "livestock_status": handle_livestock_status,
}

# ---------------------------------------------------------------------------
# Command Fabric Tools Loader
# ---------------------------------------------------------------------------


def load_command_fabric_tools() -> tuple[list[dict[str, Any]], dict[str, Callable[[dict[str, Any]], str]]]:
    """Load Command Fabric MCP tools manifest and build invocation handlers."""
    try:
        from src.command_fabric.adapters import export_adapter_manifest
        from src.command_fabric.runtime import invoke_command_fabric

        manifest = export_adapter_manifest("mcp")
        tools = manifest.get("tools", [])
        handlers: dict[str, Callable[[dict[str, Any]], str]] = {}

        for item in tools:
            tool_name = item["name"]
            cmd_name = (
                item.get("metadata", {}).get("command")
                or tool_name.removeprefix("mekong_").replace("_", "-")
            )

            def make_handler(c_name: str) -> Callable[[dict[str, Any]], str]:
                def handler(args: dict[str, Any]) -> str:
                    args_val = args.get("arguments", "")
                    if isinstance(args_val, dict):
                        args_str = " ".join(f"--{k} {v}" for k, v in args_val.items())
                    else:
                        args_str = str(args_val or "")
                    res = invoke_command_fabric(command=c_name, args=args_str)
                    return json.dumps(
                        {"ok": res.exit_code == 0, "data": res.to_dict()},
                        indent=2,
                        default=str,
                    )

                return handler

            handlers[tool_name] = make_handler(cmd_name)

        return tools, handlers
    except Exception as exc:
        sys.stderr.write(f"Failed to load Command Fabric catalog: {exc}\n")
        return [], {}


# ---------------------------------------------------------------------------
# Pure-Python Stdio JSON-RPC 2.0 Engine (Zero-Dependency Fallback)
# ---------------------------------------------------------------------------


class PureJsonRpcServer:
    """Zero-dependency line-delimited JSON-RPC 2.0 stdio server.

    Complies with MCP 2024-11-05 handshake, tools/list, and tools/call.
    Tolerates HTTP-style Content-Length framing, routes all logs to stderr,
    and terminates cleanly on stdin EOF.
    """

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        tools: list[dict[str, Any]] | None = None,
        handlers: dict[str, Callable[[dict[str, Any]], str]] | None = None,
    ) -> None:
        self.name = name
        self.version = version
        self.tools = tools or []
        self.handlers = handlers or {}

    def _read_message(self, stream: Any) -> dict[str, Any] | None:
        while True:
            line = stream.readline()
            if not line:
                return None  # EOF
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.lower().startswith("content-length:"):
                try:
                    length = int(stripped.split(":", 1)[1].strip())
                except ValueError:
                    continue
                while True:
                    h = stream.readline()
                    if not h or not h.strip():
                        break
                body = stream.read(length)
                if not body:
                    return None
                try:
                    return json.loads(body)
                except Exception as exc:
                    sys.stderr.write(f"JSON decode error: {exc}\n")
                    continue
            else:
                try:
                    return json.loads(stripped)
                except Exception as exc:
                    sys.stderr.write(f"JSON decode error: {exc}\n")
                    continue

    def _write_message(self, stream: Any, message: dict[str, Any]) -> None:
        payload = json.dumps(message, separators=(",", ":"), ensure_ascii=False)
        stream.write(payload + "\n")
        stream.flush()

    def handle_request(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        req_id = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params") or {}

        # Handle notifications
        if req_id is None:
            if method == "notifications/initialized":
                sys.stderr.write(f"[{self.name}] Client session initialized.\n")
            return None

        # 1. initialize
        if method == "initialize":
            proto = params.get("protocolVersion") if isinstance(params, dict) else None
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": proto or "2024-11-05",
                    "capabilities": {
                        "tools": {},
                    },
                    "serverInfo": {
                        "name": self.name,
                        "version": self.version,
                    },
                },
            }

        # 2. ping
        if method == "ping":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {},
            }

        # 3. tools/list
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": self.tools,
                },
            }

        # 4. tools/call
        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments") or {}
            handler = self.handlers.get(tool_name)
            if not handler:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                        "isError": True,
                    },
                }

            try:
                res = handler(arguments)
                text_res = res if isinstance(res, str) else json.dumps(res, indent=2, default=str)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": text_res}],
                        "isError": False,
                    },
                }
            except Exception as exc:
                sys.stderr.write(f"Exception during tool call '{tool_name}': {exc}\n")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps({"ok": False, "error": str(exc)}, indent=2)}],
                        "isError": True,
                    },
                }

        # Unhandled / unknown method
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found",
            },
        }

    def serve(self, in_stream: Any = None, out_stream: Any = None) -> None:
        in_stream = in_stream or sys.stdin
        out_stream = out_stream or sys.stdout

        while True:
            try:
                msg = self._read_message(in_stream)
                if msg is None:
                    break
                resp = self.handle_request(msg)
                if resp is not None:
                    self._write_message(out_stream, resp)
            except (KeyboardInterrupt, BrokenPipeError):
                break
            except Exception as exc:
                sys.stderr.write(f"Unexpected error in serve loop: {exc}\n")
                traceback.print_exc(file=sys.stderr)


# ---------------------------------------------------------------------------
# FastMCP Engine Setup
# ---------------------------------------------------------------------------


def run_fastmcp_server(
    mode: str,
    name: str,
    transport: str = "stdio",
    port: int = 8000,
) -> None:
    """Launch FastMCP server instance."""
    if not _HAS_FASTMCP or FastMCP is None:
        raise RuntimeError("FastMCP SDK is not available.")

    app = FastMCP(name, log_level="ERROR")

    if mode == "fabric":
        tools, _ = load_command_fabric_tools()
        from src.command_fabric.runtime import invoke_command_fabric

        for item in tools:
            tool_name = item["name"]
            desc = item.get("description", "")
            cmd_name = (
                item.get("metadata", {}).get("command")
                or tool_name.removeprefix("mekong_").replace("_", "-")
            )

            def make_fabric_fn(c_name: str, c_desc: str) -> Callable[[str], str]:
                def fabric_handler(arguments: str = "") -> str:
                    res = invoke_command_fabric(command=c_name, args=arguments)
                    return json.dumps(
                        {"ok": res.exit_code == 0, "data": res.to_dict()},
                        indent=2,
                        default=str,
                    )

                fabric_handler.__name__ = f"handler_{c_name.replace('-', '_')}"
                fabric_handler.__doc__ = c_desc
                return fabric_handler

            app.add_tool(
                make_fabric_fn(cmd_name, desc),
                name=tool_name,
                description=desc,
            )
    else:
        # Register Core 14 Tools
        @app.tool(name="mekong_memory_store", description="Store a key-value or execution memory in Mekong canonical memory.")
        def mekong_memory_store(key: str, value: str, ttl: int | None = None) -> str:
            return handle_memory_store({"key": key, "value": value, "ttl": ttl})

        @app.tool(name="mekong_memory_recall", description="Retrieve an exact key-value or execution record by key from memory.")
        def mekong_memory_recall(key: str) -> str:
            return handle_memory_recall({"key": key})

        @app.tool(name="mekong_memory_search", description="Search memories using vector semantic similarity with keyword substring fallback.")
        def mekong_memory_search(query: str, limit: int = 10) -> str:
            return handle_memory_search({"query": query, "limit": limit})

        @app.tool(name="mekong_plan_create", description="Decompose a goal into sequential/parallel tasks and persist the plan.")
        def mekong_plan_create(goal: str) -> str:
            return handle_plan_create({"goal": goal})

        @app.tool(name="mekong_plan_update", description="Update plan status ('active', 'completed') or a specific subtask status.")
        def mekong_plan_update(plan_id: str, status: str = "", task_id: str = "", task_status: str = "") -> str:
            return handle_plan_update({"plan_id": plan_id, "status": status, "task_id": task_id, "task_status": task_status})

        @app.tool(name="mekong_plan_get", description="Fetch a plan by ID or list plans filtered by status ('active', 'completed').")
        def mekong_plan_get(plan_id: str = "", status: str = "") -> str:
            return handle_plan_get({"plan_id": plan_id, "status": status})

        @app.tool(name="mekong_task_create", description="Create a new task in the task backlog.")
        def mekong_task_create(subject: str) -> str:
            return handle_task_create({"subject": subject})

        @app.tool(name="mekong_task_update", description="Update task status ('todo', 'in-progress', 'done').")
        def mekong_task_update(task_id: str, status: str) -> str:
            return handle_task_update({"task_id": task_id, "status": status})

        @app.tool(name="mekong_task_list", description="List backlog tasks filtered by status ('todo', 'in-progress', 'done').")
        def mekong_task_list(status: str = "") -> str:
            return handle_task_list({"status": status})

        @app.tool(name="mekong_agent_list", description="List registered autonomous agents, roles, and allowed tools.")
        def mekong_agent_list() -> str:
            return handle_agent_list({})

        @app.tool(name="mekong_agent_info", description="Fetch detailed policy, tools, context budget, and prompt info for a specific agent.")
        def mekong_agent_info(name: str) -> str:
            return handle_agent_info({"name": name})

        @app.tool(name="mekong_agent_route", description="Route a natural language goal to the optimal agent or multi-agent swarm team.")
        def mekong_agent_route(goal: str) -> str:
            return handle_agent_route({"goal": goal})

        @app.tool(name="mekong_status", description="System health diagnostic across Python runtime, LLM providers, memory store, tasks, and plans.")
        def mekong_status() -> str:
            return handle_status({})

        @app.tool(name="mekong_cost_estimate", description="Pre-execution LLM token usage and MCU cost prediction.")
        def mekong_cost_estimate(goal: str, model_id: str = "claude-sonnet-4-6") -> str:
            return handle_cost_estimate({"goal": goal, "model_id": model_id})

        @app.tool(
            name="mekong_subagent_dispatch",
            description="Dynamic subagent bridge: generates define_subagent and invoke_subagent payloads for Antigravity with HARNESS.md guardrails.",
        )
        def mekong_subagent_dispatch(role: str, task: str, model_tier: str = "inherit") -> str:
            return handle_subagent_dispatch({"role": role, "task": task, "model_tier": model_tier})

        @app.tool(
            name="mekong_pev_plan",
            description="Generate structured PEV execution plan, tasks, and subagent assignments from a goal.",
        )
        def mekong_pev_plan(goal: str, mission_id: str = "") -> str:
            return handle_pev_plan({"goal": goal, "mission_id": mission_id})

        @app.tool(
            name="mekong_pev_checkpoint",
            description="Capture atomic SQLite checkpoint of workspace files and task states.",
        )
        def mekong_pev_checkpoint(
            mission_id: str,
            label: str = "manual",
            files: list[str] | None = None,
            test_results: dict[str, Any] | None = None,
        ) -> str:
            return handle_pev_checkpoint(
                {"mission_id": mission_id, "label": label, "files": files, "test_results": test_results}
            )

        @app.tool(
            name="mekong_pev_rollback",
            description="Atomically restore workspace files and task states to a specific checkpoint.",
        )
        def mekong_pev_rollback(checkpoint_id: str) -> str:
            return handle_pev_rollback({"checkpoint_id": checkpoint_id})

        @app.tool(
            name="mekong_swarm_status",
            description="Inspect active multi-agent PEV mission progress, cycles, and health.",
        )
        def mekong_swarm_status(mission_id: str = "") -> str:
            return handle_swarm_status({"mission_id": mission_id})

        @app.tool(
            name="mekong_eval_query",
            description="Query offline mission evaluations, p95 durations, failure clusters, and continuous learning recommendations.",
        )
        def mekong_eval_query(agent_id: str = "all", days: int = 7, limit: int = 50) -> str:
            return handle_eval_query({"agent_id": agent_id, "days": days, "limit": limit})

        @app.tool(
            name="mekong_recipe_evolve",
            description="Trigger self-improvement and recipe evolution for a goal or recipe based on failure clusters.",
        )
        def mekong_recipe_evolve(recipe_name: str = "", goal: str = "", force: bool = False) -> str:
            return handle_recipe_evolve({"recipe_name": recipe_name, "goal": goal, "force": force})

        @app.tool(
            name="mekong_mission_metrics",
            description="Retrieve aggregated telemetry metrics, credit usage, and failure breakdowns across agents.",
        )
        def mekong_mission_metrics(agent_id: str = "all", days: int = 7) -> str:
            return handle_mission_metrics({"agent_id": agent_id, "days": days})

        @app.tool(
            name="mekong_palette_search",
            description="Fuzzy search across Mekong CLI commands, Antigravity skills, and domain subagents using Vietnamese or English natural language.",
        )
        def mekong_palette_search(query: str, category: str = "all", limit: int = 5) -> str:
            return handle_palette_search({"query": query, "category": category, "limit": limit})

        @app.tool(
            name="mekong_tui_dashboard_status",
            description="Retrieve real-time telemetry, AGI subsystem health, checkpoints, and system performance summary for the Mekong TUI dashboard.",
        )
        def mekong_tui_dashboard_status(detailed: bool = False) -> str:
            return handle_tui_dashboard_status({"detailed": detailed})

        @app.tool(
            name="mekong_benchmark_run",
            description="Run autonomous benchmark suites across PEV, checkpoints, subagents, and chaos scenarios.",
        )
        def mekong_benchmark_run(suite: str = "all", iterations: int = 1, chaos_level: str = "none") -> str:
            return handle_benchmark_run({"suite": suite, "iterations": iterations, "chaos_level": chaos_level})

        @app.tool(
            name="mekong_chaos_simulate",
            description="Simulate chaos fault injection against checkpoints, tools, or payloads to test self-healing resilience.",
        )
        def mekong_chaos_simulate(target: str = "checkpoint", error_type: str = "corrupt_file") -> str:
            return handle_chaos_simulate({"target": target, "error_type": error_type})

        @app.tool(
            name="mekong_gateway_status",
            description="Query Mekong Gateway server health, uptime, active SSE streams, and system metrics.",
        )
        def mekong_gateway_status() -> str:
            return handle_gateway_status({})

        @app.tool(
            name="mekong_gateway_rate_limit",
            description="Query tenant rate limit quota, tokens remaining, and reset timestamp.",
        )
        def mekong_gateway_rate_limit(tenant_id: str = "default") -> str:
            return handle_gateway_rate_limit({"tenant_id": tenant_id})

        @app.tool(
            name="mekong_watch_status",
            description="Query active Mekong file watcher daemon state, monitored directories, recent change events, and repair metrics.",
        )
        def mekong_watch_status() -> str:
            return handle_watch_status({})

        @app.tool(
            name="mekong_self_repair",
            description="Perform AST syntax diagnostics and automated self-healing repair (or checkpoint rollback) on a file.",
        )
        def mekong_self_repair(file_path: str, error_detail: str = "", mode: str = "auto") -> str:
            return handle_self_repair({"file_path": file_path, "error_detail": error_detail, "mode": mode})

        @app.tool(
            name="mekong_package_build",
            description="Build multi-platform distribution packages, Homebrew formulas, and Docker assets.",
        )
        def mekong_package_build(target: str = "all", output_dir: str = "dist") -> str:
            return handle_package_build({"target": target, "output_dir": output_dir})

        @app.tool(
            name="mekong_sandbox_exec",
            description="Execute a shell command inside an isolated container or secure subprocess sandbox.",
        )
        def mekong_sandbox_exec(command: str, timeout: int = 30, memory_limit_mb: int = 512, image: str = "python:3.11-slim") -> str:
            return handle_sandbox_exec({"command": command, "timeout": timeout, "memory_limit_mb": memory_limit_mb, "image": image})

        @app.tool(
            name="mekong_consensus_vote",
            description="Execute a multi-agent quorum vote on a proposal (majority, supermajority, unanimous, weighted).",
        )
        def mekong_consensus_vote(proposal: str, quorum: str = "majority", agents: list[str] | None = None) -> str:
            return handle_consensus_vote({"proposal": proposal, "quorum": quorum, "agents": agents})

        @app.tool(
            name="mekong_consensus_debate",
            description="Conduct a structured multi-round debate between domain roles with synthetic consensus.",
        )
        def mekong_consensus_debate(topic: str, proponent: str = "cto", opponent: str = "sre", moderator: str = "ceo", rounds: int = 2) -> str:
            return handle_consensus_debate({"topic": topic, "proponent": proponent, "opponent": opponent, "moderator": moderator, "rounds": rounds})

        @app.tool(
            name="mekong_semantic_recall",
            description="Perform associative semantic and BM25 search across federated memory domains.",
        )
        def mekong_semantic_recall(query: str, domain: str = "all", limit: int = 5) -> str:
            return handle_semantic_recall({"query": query, "domain": domain, "limit": limit})

        @app.tool(
            name="mekong_knowledge_graph_query",
            description="Traverse relational codebase and architectural knowledge graph around an entity.",
        )
        def mekong_knowledge_graph_query(entity: str, depth: int = 2) -> str:
            return handle_knowledge_graph_query({"entity": entity, "depth": depth})

        @app.tool(
            name="mekong_telemetry_metrics",
            description="Export or inspect standard Prometheus exposition metrics or structured JSON.",
        )
        def mekong_telemetry_metrics(format_type: str = "prometheus") -> str:
            return handle_telemetry_metrics({"format_type": format_type})

        @app.tool(
            name="mekong_trace_query",
            description="Query distributed tracing spans, latency timings, and W3C traceparent headers.",
        )
        def mekong_trace_query(trace_id: str | None = None, limit: int = 20) -> str:
            return handle_trace_query({"trace_id": trace_id, "limit": limit})

        @app.tool(
            name="mekong_queue_enqueue",
            description="Schedule a new task for prioritized execution in the distributed task queue.",
        )
        def mekong_queue_enqueue(name: str, priority: str = "normal", payload: dict | None = None, max_retries: int = 3, delay_sec: float = 0.0) -> str:
            return handle_queue_enqueue({"name": name, "priority": priority, "payload": payload, "max_retries": max_retries, "delay_sec": delay_sec})

        @app.tool(
            name="mekong_queue_status",
            description="Inspect queue depth, active worker leases, and dead-letter counts.",
        )
        def mekong_queue_status() -> str:
            return handle_queue_status({})

        @app.tool(
            name="mekong_queue_dlq_action",
            description="Inspect, retry, or clear tasks residing in the dead-letter queue.",
        )
        def mekong_queue_dlq_action(action: str = "list", task_id: str | None = None) -> str:
            return handle_queue_dlq_action({"action": action, "task_id": task_id})

        @app.tool(
            name="mekong_pipeline_run",
            description="Run multi-agent sequential pipeline (FilePicker -> Editor -> Reviewer) for software engineering tasks.",
        )
        def mekong_pipeline_run(goal: str, stages: list[str] | None = None) -> str:
            return handle_pipeline_run({"goal": goal, "stages": stages})

        @app.tool(
            name="mekong_pipeline_status",
            description="Inspect status, stage outcomes, and timings for a pipeline execution.",
        )
        def mekong_pipeline_status(pipeline_id: str = "") -> str:
            return handle_pipeline_status({"pipeline_id": pipeline_id})

        @app.tool(
            name="mekong_worktree_create",
            description="Create a new isolated git worktree branching from the base branch.",
        )
        def mekong_worktree_create(feature: str, prefix: str | None = None, base_branch: str | None = None, no_prefix: bool = False, root: str | None = None, dry_run: bool = False) -> str:
            return handle_worktree_create({"feature": feature, "prefix": prefix, "base_branch": base_branch, "no_prefix": no_prefix, "root": root, "dry_run": dry_run})

        @app.tool(
            name="mekong_worktree_list",
            description="List all registered git worktrees in the repository.",
        )
        def mekong_worktree_list() -> str:
            return handle_worktree_list({})

        @app.tool(
            name="mekong_worktree_status",
            description="Inspect status, uncommitted changes, and divergence against base branch.",
        )
        def mekong_worktree_status(path_or_branch: str | None = None) -> str:
            return handle_worktree_status({"path_or_branch": path_or_branch})

        @app.tool(
            name="mekong_worktree_remove",
            description="Remove an isolated git worktree workspace.",
        )
        def mekong_worktree_remove(path_or_name: str, force: bool = False) -> str:
            return handle_worktree_remove({"path_or_name": path_or_name, "force": force})

        @app.tool(
            name="mekong_ship_preflight",
            description="Inspect repository topology, branch, remote, and dirty files before shipping.",
        )
        def mekong_ship_preflight() -> str:
            return handle_ship_preflight({})

        @app.tool(
            name="mekong_ship_run",
            description="Run the production shipping pipeline: lint, test, stage, commit, and push.",
        )
        def mekong_ship_run(message: str = "", run_lint: bool = True, run_tests: bool = True, push: bool = True, dry_run: bool = False) -> str:
            return handle_ship_run({"message": message, "run_lint": run_lint, "run_tests": run_tests, "push": push, "dry_run": dry_run})

        @app.tool(
            name="mekong_daily_report",
            description="Produce an executive daily standup report: git commit velocity, uncommitted files, codebase debt, and mesh queue depth.",
        )
        def mekong_daily_report(since: str = "24 hours ago", include_todos: bool = True) -> str:
            return handle_daily_report({"since": since, "include_todos": include_todos})

        @app.tool(
            name="mekong_daily_focus",
            description="Retrieve prioritized strategic daily focus recommendations synthesized from repository and queue signals.",
        )
        def mekong_daily_focus() -> str:
            return handle_daily_focus({})

        @app.tool(
            name="mekong_quick_start_plan",
            description="Simulate and retrieve the 5-step project kickoff blueprint, architecture PRD, and milestone checklist without writing files.",
        )
        def mekong_quick_start_plan(project_name: str = "mekong-app", project_type: str = "agent") -> str:
            return handle_quick_start_plan({"project_name": project_name, "project_type": project_type})

        @app.tool(
            name="mekong_quick_start_create",
            description="Execute the end-to-end 5-step project kickoff: brainstorm, plan, scaffold, verify & git commit, and monetization roadmap.",
        )
        def mekong_quick_start_create(project_name: str = "mekong-app", project_type: str = "agent", target_dir: str = "", dry_run: bool = False, init_git: bool = True) -> str:
            return handle_quick_start_create({"project_name": project_name, "project_type": project_type, "target_dir": target_dir, "dry_run": dry_run, "init_git": init_git})

        @app.tool(
            name="mekong_cto_scorecard",
            description="Calculate composite engineering health score, grade, test coverage, and security posture.",
        )
        def mekong_cto_scorecard() -> str:
            return handle_cto_scorecard({})

        @app.tool(
            name="mekong_cto_review",
            description="Conduct automated code quality, anti-pattern, dynamic execution, and security review.",
        )
        def mekong_cto_review(target_path: str = "") -> str:
            return handle_cto_review({"target_path": target_path})

        @app.tool(
            name="mekong_cto_architect",
            description="Generate an Architecture Decision Record (ADR) with context, decision, consequences, and alternatives.",
        )
        def mekong_cto_architect(title: str, context: str = "", decision: str = "") -> str:
            return handle_cto_architect({"title": title, "context": context, "decision": decision})

        @app.tool(
            name="mekong_sales_pipeline",
            description="Query sales pipeline metrics, weighted revenue forecasts, and opportunities by stage.",
        )
        def mekong_sales_pipeline(stage: str = "") -> str:
            return handle_sales_pipeline({"stage": stage})

        @app.tool(
            name="mekong_sales_deal_add",
            description="Add a new deal opportunity to the sales pipeline ledger.",
        )
        def mekong_sales_deal_add(name: str, company: str, value: float, stage: str = "lead", email: str = "") -> str:
            return handle_sales_deal_add({"name": name, "company": company, "value": value, "stage": stage, "email": email})

        @app.tool(
            name="mekong_sales_outreach",
            description="Generate tailored multi-channel outreach copy and cadence (email, linkedin, zalo).",
        )
        def mekong_sales_outreach(company: str, persona: str = "CTO", channel: str = "email") -> str:
            return handle_sales_outreach({"company": company, "persona": persona, "channel": channel})

        @app.tool(
            name="mekong_marketing_metrics",
            description="Query aggregated marketing metrics, active campaigns, total spend, and conversions.",
        )
        def mekong_marketing_metrics() -> str:
            return handle_marketing_metrics({})

        @app.tool(
            name="mekong_marketing_campaign_create",
            description="Create and register a promotional or growth marketing campaign.",
        )
        def mekong_marketing_campaign_create(name: str, channel: str = "social", budget: float = 1000.0, target_audience: str = "") -> str:
            return handle_marketing_campaign_create({"name": name, "channel": channel, "budget": budget, "target_audience": target_audience})

        @app.tool(
            name="mekong_marketing_content_generate",
            description="Synthesize ready-to-use marketing copy and creative with hashtags and call-to-action.",
        )
        def mekong_marketing_content_generate(topic: str, channel: str = "social", content_type: str = "post") -> str:
            return handle_marketing_content_generate({"topic": topic, "channel": channel, "content_type": content_type})

        @app.tool(
            name="mekong_dev_audit",
            description="Perform static AST and security audit across the codebase or specific module.",
        )
        def mekong_dev_audit(path: str = "") -> str:
            return handle_dev_audit({"path": path})

        @app.tool(
            name="mekong_dev_scaffold",
            description="Scaffold a new structured Python module, service, API, or agent with unit tests.",
        )
        def mekong_dev_scaffold(name: str, module_type: str = "service", dry_run: bool = True) -> str:
            return handle_dev_scaffold({"name": name, "module_type": module_type, "dry_run": dry_run})

        @app.tool(
            name="mekong_dev_review",
            description="Review working tree git diff for safety, technical debt, and quality hazards.",
        )
        def mekong_dev_review() -> str:
            return handle_dev_review({})

        @app.tool(
            name="mekong_ops_health_sweep",
            description="Run comprehensive system health audit across runtime, storage, databases, git & configs.",
        )
        def mekong_ops_health_sweep(save_report: bool = False) -> str:
            return handle_ops_health_sweep({"save_report": save_report})

        @app.tool(
            name="mekong_ops_incident_create",
            description="Create and track a new SRE incident in the operations ledger.",
        )
        def mekong_ops_incident_create(title: str, severity: str = "SEV3", service: str = "core", summary: str = "") -> str:
            return handle_ops_incident_create({"title": title, "severity": severity, "service": service, "summary": summary})

        @app.tool(
            name="mekong_ops_incident_list",
            description="List tracked SRE incidents filtered by status.",
        )
        def mekong_ops_incident_list(status: str = "ALL") -> str:
            return handle_ops_incident_list({"status": status})

        @app.tool(
            name="mekong_support_onboard_status",
            description="Query current project onboarding milestones, completed steps, and progress percentage.",
        )
        def mekong_support_onboard_status() -> str:
            return handle_support_onboard_status({})

        @app.tool(
            name="mekong_support_feedback_submit",
            description="Record customer satisfaction, feedback comments, or Net Promoter Score (NPS).",
        )
        def mekong_support_feedback_submit(nps_score: Optional[int] = None, feedback_text: str = "", category: str = "general") -> str:
            return handle_support_feedback_submit({"nps_score": nps_score, "feedback_text": feedback_text, "category": category})

        @app.tool(
            name="mekong_support_triage",
            description="Perform smart AI/heuristic triage for user issues, error traces, and operational bugs.",
        )
        def mekong_support_triage(issue_text: str) -> str:
            return handle_support_triage({"issue_text": issue_text})

        @app.tool(
            name="mekong_consulting_pricing",
            description="Show standardized AI agent consulting packages, pricing, and deliverables.",
        )
        def mekong_consulting_pricing(currency: str = "USD") -> str:
            return handle_consulting_pricing({"currency": currency})

        @app.tool(
            name="mekong_consulting_proposal",
            description="Synthesize a customized commercial consulting proposal for a prospect.",
        )
        def mekong_consulting_proposal(prospect_name: str, service_tier: str = "custom_agent", requirements: str = "") -> str:
            return handle_consulting_proposal({"prospect_name": prospect_name, "service_tier": service_tier, "requirements": requirements})

        @app.tool(
            name="mekong_consulting_outreach",
            description="Generate multi-channel B2B cold/warm outreach templates (Email, LinkedIn, Zalo).",
        )
        def mekong_consulting_outreach(prospect_name: str, service_tier: str = "custom_agent", role: str = "CTO") -> str:
            return handle_consulting_outreach({"prospect_name": prospect_name, "service_tier": service_tier, "role": role})

        @app.tool(
            name="mekong_revenue_metrics",
            description="Calculate current MRR, ARR, ARPU, LTV, churn rate, and MRR waterfall economics.",
        )
        def mekong_revenue_metrics(period: str = "month") -> str:
            return handle_revenue_metrics({"period": period})

        @app.tool(
            name="mekong_revenue_record",
            description="Record a payment transaction into the revenue ledger and update active subscriptions.",
        )
        def mekong_revenue_record(
            customer_id: str,
            amount: float,
            customer_name: str = "",
            currency: str = "USD",
            tier: str = "starter",
            txn_type: str = "subscription",
            gateway: str = "stripe",
        ) -> str:
            return handle_revenue_record({
                "customer_id": customer_id,
                "amount": amount,
                "customer_name": customer_name,
                "currency": currency,
                "tier": tier,
                "txn_type": txn_type,
                "gateway": gateway,
            })

        @app.tool(
            name="mekong_revenue_forecast",
            description="Project future MRR, ARR, and cumulative cash flows across growth scenarios.",
        )
        def mekong_revenue_forecast(months: int = 6, scenario: str = "base") -> str:
            return handle_revenue_forecast({"months": months, "scenario": scenario})

        @app.tool(
            name="mekong_content_generate",
            description="Generate structured, ready-to-publish content for any pillar and format.",
        )
        def mekong_content_generate(pillar: str, format_type: str = "blog", topic: str = "", channel: str = "") -> str:
            return handle_content_generate({"pillar": pillar, "format_type": format_type, "topic": topic, "channel": channel})

        @app.tool(
            name="mekong_content_calendar",
            description="Query editorial publication calendar, frequencies, and upcoming deadlines.",
        )
        def mekong_content_calendar() -> str:
            return handle_content_calendar({})

        @app.tool(
            name="mekong_content_channels",
            description="Query distribution channels, audience reach, and publication metrics.",
        )
        def mekong_content_channels() -> str:
            return handle_content_channels({})

        @app.tool(
            name="mekong_copywriting_generate",
            description="Generate high-converting marketing and product copy using proven psychological frameworks.",
        )
        def mekong_copywriting_generate(
            product_name: str = "Mekong CLI",
            target_audience: str = "Founders & Engineers",
            formula: str = "pas",
            copy_type: str = "landing_page",
            key_benefit: str = "",
            style: str = "direct_response",
        ) -> str:
            return handle_copywriting_generate({
                "product_name": product_name,
                "target_audience": target_audience,
                "formula": formula,
                "copy_type": copy_type,
                "key_benefit": key_benefit,
                "style": style,
            })

        @app.tool(
            name="mekong_copywriting_headline",
            description="Generate high-conversion headline variations across psychological angles.",
        )
        def mekong_copywriting_headline(
            product_name: str = "Mekong CLI",
            value_prop: str = "automate engineering workflows",
            count: int = 5,
        ) -> str:
            return handle_copywriting_headline({
                "product_name": product_name,
                "value_prop": value_prop,
                "count": count,
            })

        @app.tool(
            name="mekong_copywriting_cta",
            description="Generate conversion call-to-action button variations with risk reversals.",
        )
        def mekong_copywriting_cta(
            action_goal: str = "start free trial",
            risk_reversal: str = "",
        ) -> str:
            return handle_copywriting_cta({
                "action_goal": action_goal,
                "risk_reversal": risk_reversal,
            })

        @app.tool(
            name="mekong_billing_simulate",
            description="Simulate an itemized billing invoice based on accrued usage events and pricing tiers.",
        )
        def mekong_billing_simulate(
            license_key: str = "mekong_lic_default",
            tier: str = "pro",
            period_days: int = 30,
        ) -> str:
            return handle_billing_simulate({
                "license_key": license_key,
                "tier": tier,
                "period_days": period_days,
            })

        @app.tool(
            name="mekong_billing_record_usage",
            description="Ingest and meter a billable usage event with idempotent deduplication and pricing.",
        )
        def mekong_billing_record_usage(
            license_key: str = "mekong_lic_default",
            event_type: str = "llm_tokens",
            quantity: float = 1.0,
            idempotency_key: str = "",
            tier: str = "pro",
        ) -> str:
            return handle_billing_record_usage({
                "license_key": license_key,
                "event_type": event_type,
                "quantity": quantity,
                "idempotency_key": idempotency_key,
                "tier": tier,
            })

        @app.tool(
            name="mekong_billing_status",
            description="Retrieve real-time billing quotas, consumption, unbilled charges, and health status for a license.",
        )
        def mekong_billing_status(
            license_key: str = "mekong_lic_default",
        ) -> str:
            return handle_billing_status({
                "license_key": license_key,
            })

        @app.tool(
            name="mekong_vendor_onboard",
            description="Register and onboard a third-party vendor, plugin, model, or tool provider.",
        )
        def mekong_vendor_onboard(
            name: str,
            vendor_type: str = "agent",
            version: str = "1.0.0",
            description: str = "",
            author: str = "Community Builder",
            trust_score: float = 85.0,
        ) -> str:
            return handle_vendor_onboard({
                "name": name,
                "vendor_type": vendor_type,
                "version": version,
                "description": description,
                "author": author,
                "trust_score": trust_score,
            })

        @app.tool(
            name="mekong_vendor_list",
            description="List registered vendors with optional filtering by type and operational status.",
        )
        def mekong_vendor_list(
            vendor_type: str = "all",
            status: str = "all",
            limit: int = 50,
        ) -> str:
            return handle_vendor_list({
                "vendor_type": vendor_type,
                "status": status,
                "limit": limit,
            })

        @app.tool(
            name="mekong_vendor_assess",
            description="Run an automated security, compliance, or performance audit on a vendor provider.",
        )
        def mekong_vendor_assess(
            name: str,
            audit_type: str = "security",
        ) -> str:
            return handle_vendor_assess({
                "name": name,
                "audit_type": audit_type,
            })

        @app.tool(
            name="mekong_founder_assess",
            description="Assess a founder genome with personality, core values, fears, risk tolerance, and cognitive biases.",
        )
        def mekong_founder_assess(
            name: str = "",
            mission: str = "",
            tipi_responses: Optional[dict[str, int]] = None,
            values: Optional[list[str]] = None,
            fears: Optional[list[dict[str, Any]]] = None,
            risk_ratings: Optional[dict[str, int]] = None,
            bias_responses: Optional[dict[str, bool]] = None,
            particle_id: Optional[str] = None,
        ) -> str:
            return handle_founder_assess({
                "name": name,
                "mission": mission,
                "tipi_responses": tipi_responses or {},
                "values": values or [],
                "fears": fears or [],
                "risk_ratings": risk_ratings or {},
                "bias_responses": bias_responses or {},
                "particle_id": particle_id,
            })

        @app.tool(
            name="mekong_founder_review",
            description="Load and inspect a complete founder genome profile from the registry.",
        )
        def mekong_founder_review(
            founder_id: str,
        ) -> str:
            return handle_founder_review({
                "founder_id": founder_id,
            })

        @app.tool(
            name="mekong_founder_list",
            description="List assessed founder genome profiles with optional risk level filtering.",
        )
        def mekong_founder_list(
            risk_level: str = "all",
            limit: int = 50,
        ) -> str:
            return handle_founder_list({
                "risk_level": risk_level,
                "limit": limit,
            })

        @app.tool(
            name="mekong_governance_propose",
            description="Draft and submit a new constitutional amendment proposal.",
        )
        def mekong_governance_propose(
            title: str,
            description: str,
            text: str,
            proposer: str = "founder",
            tier: str = "soft",
            co_sponsors: Optional[list[str]] = None,
        ) -> str:
            return handle_governance_propose({
                "title": title,
                "description": description,
                "text": text,
                "proposer": proposer,
                "tier": tier,
                "co_sponsors": co_sponsors or [],
            })

        @app.tool(
            name="mekong_governance_vote",
            description="Cast a weighted cryptographic ballot on an active governance proposal.",
        )
        def mekong_governance_vote(
            proposal_id: str,
            choice: str = "yes",
            voter: str = "founder",
            weight: float = 1.0,
        ) -> str:
            return handle_governance_vote({
                "proposal_id": proposal_id,
                "choice": choice,
                "voter": voter,
                "weight": weight,
            })

        @app.tool(
            name="mekong_governance_tally",
            description="Tally ballots, compute quorum satisfaction, and finalize proposal outcome.",
        )
        def mekong_governance_tally(
            proposal_id: str,
        ) -> str:
            return handle_governance_tally({
                "proposal_id": proposal_id,
            })

        @app.tool(
            name="mekong_governance_list",
            description="List constitutional governance proposals filtered by status and tier.",
        )
        def mekong_governance_list(
            status: str = "all",
            tier: str = "all",
            limit: int = 50,
        ) -> str:
            return handle_governance_list({
                "status": status,
                "tier": tier,
                "limit": limit,
            })

        @app.tool(
            name="mekong_particle_init",
            description="Create and register a new ZenOS particle with constitutional mission.",
        )
        def mekong_particle_init(
            name: str,
            mission: str = "",
            template: str = "skel",
        ) -> str:
            return handle_particle_init({
                "name": name,
                "mission": mission,
                "template": template,
            })

        @app.tool(
            name="mekong_particle_status",
            description="Show a ZenOS particle's network status, connections, trust score, and collusion check.",
        )
        def mekong_particle_status(
            particle_id: str = "default",
        ) -> str:
            return handle_particle_status({
                "particle_id": particle_id,
            })

        @app.tool(
            name="mekong_particle_connect",
            description="Establish a bidirectional trust relationship between two ZenOS particles.",
        )
        def mekong_particle_connect(
            particle_a: str,
            particle_b: str,
            trust_score: float = 50.0,
        ) -> str:
            return handle_particle_connect({
                "particle_a": particle_a,
                "particle_b": particle_b,
                "trust_score": trust_score,
            })

        @app.tool(
            name="mekong_particle_cell_run",
            description="Execute an autonomous AI cell role within particle constitutional context.",
        )
        def mekong_particle_cell_run(
            role: str,
            prompt: str,
            particle_id: str = "default",
            auto_compliance: bool = False,
        ) -> str:
            return handle_particle_cell_run({
                "role": role,
                "prompt": prompt,
                "particle_id": particle_id,
                "auto_compliance": auto_compliance,
            })

        @app.tool(
            name="mekong_thue_tncn",
            description="Calculate progressive Personal Income Tax (TNCN) under Vietnamese tax regulations (Điều 22).",
        )
        def mekong_thue_tncn(
            monthly_income: float,
            dependents: int = 0,
        ) -> str:
            return handle_thue_tncn({
                "monthly_income": monthly_income,
                "dependents": dependents,
            })

        @app.tool(
            name="mekong_thue_tndn",
            description="Calculate Corporate Income Tax (TNDN) with standard 20% or SME 17% preferential rate.",
        )
        def mekong_thue_tndn(
            annual_revenue: float,
            profit: float = 0.0,
            is_sme: bool = True,
        ) -> str:
            return handle_thue_tndn({
                "annual_revenue": annual_revenue,
                "profit": profit if profit > 0 else None,
                "is_sme": is_sme,
            })

        @app.tool(
            name="mekong_thue_gtgt",
            description="Calculate Value Added Tax (GTGT / VAT 0%, 5%, 8%, 10%) under Decree 123 & Circular 78.",
        )
        def mekong_thue_gtgt(
            amount: float,
            rate: int = 10,
        ) -> str:
            return handle_thue_gtgt({
                "amount": amount,
                "rate": rate,
            })

        @app.tool(
            name="mekong_thue_status",
            description="Retrieve Vietnamese tax engine status, statutory deduction rates, and historical simulation summaries.",
        )
        def mekong_thue_status() -> str:
            return handle_thue_status({})

        @app.tool(
            name="mekong_ke_toan_create",
            description="Create an electronic invoice compliant with Decree 123 & Circular 78 and save to accounting database.",
        )
        def mekong_ke_toan_create(
            amount: float,
            buyer: str,
            vat_rate: int = 10,
            seller: str = "Doanh Nghiệp",
            seller_tax_code: str = "0000000000",
            buyer_tax_code: str = "",
            description: str = "Hàng hóa/Dịch vụ",
        ) -> str:
            return handle_ke_toan_create({
                "amount": amount,
                "buyer": buyer,
                "vat_rate": vat_rate,
                "seller": seller,
                "seller_tax_code": seller_tax_code,
                "buyer_tax_code": buyer_tax_code,
                "description": description,
            })

        @app.tool(
            name="mekong_ke_toan_xml",
            description="Generate electronic invoice XML complying with Circular 78/2021/TT-BTC schema.",
        )
        def mekong_ke_toan_xml(
            amount: float,
            buyer: str,
            vat_rate: int = 10,
            seller: str = "Doanh Nghiệp",
            seller_tax_code: str = "0000000000",
            description: str = "Hàng hóa/Dịch vụ",
        ) -> str:
            return handle_ke_toan_xml({
                "amount": amount,
                "buyer": buyer,
                "vat_rate": vat_rate,
                "seller": seller,
                "seller_tax_code": seller_tax_code,
                "description": description,
            })

        @app.tool(
            name="mekong_ke_toan_journal",
            description="Generate balanced VAS double-entry journal entry (Nợ 131 / Có 511, Có 3331) for sales revenue.",
        )
        def mekong_ke_toan_journal(
            amount: float,
            buyer: str,
            vat_rate: int = 10,
            seller: str = "Doanh Nghiệp",
            seller_tax_code: str = "0000000000",
            description: str = "Hàng hóa/Dịch vụ",
        ) -> str:
            return handle_ke_toan_journal({
                "amount": amount,
                "buyer": buyer,
                "vat_rate": vat_rate,
                "seller": seller,
                "seller_tax_code": seller_tax_code,
                "description": description,
            })

        @app.tool(
            name="mekong_ke_toan_status",
            description="Retrieve Vietnamese accounting system status, invoice totals, VAT output, and general ledger statistics.",
        )
        def mekong_ke_toan_status() -> str:
            return handle_ke_toan_status({})

        @app.tool(
            name="mekong_zalo_send",
            description="Send a customer care or transactional message to a Zalo user ID via Zalo OA.",
        )
        def mekong_zalo_send(
            user_id: str,
            message: str,
            template: str = "",
        ) -> str:
            return handle_zalo_send({
                "user_id": user_id,
                "message": message,
                "template": template,
            })

        @app.tool(
            name="mekong_zalo_broadcast",
            description="Broadcast an announcement or promotion to subscribers via Zalo OA.",
        )
        def mekong_zalo_broadcast(
            message: str,
            title: str = "Thông báo Zalo OA",
            target_segment: str = "all",
        ) -> str:
            return handle_zalo_broadcast({
                "message": message,
                "title": title,
                "target_segment": target_segment,
            })

        @app.tool(
            name="mekong_zalo_followers",
            description="Query Zalo OA follower roster, tiers, and engagement status.",
        )
        def mekong_zalo_followers(
            segment: str = "all",
            limit: int = 50,
        ) -> str:
            return handle_zalo_followers({
                "segment": segment,
                "limit": limit,
            })

        @app.tool(
            name="mekong_zalo_caption",
            description="Generate high-engagement social media captions across 5 tones (vui_ve, chuyen_nghiep, sang_tao, khuyen_mai, binh_phap).",
        )
        def mekong_zalo_caption(
            topic: str,
            tone: str = "vui_ve",
        ) -> str:
            return handle_zalo_caption({
                "topic": topic,
                "tone": tone,
            })

        @app.tool(
            name="mekong_zalo_status",
            description="Retrieve Zalo OA customer messaging, broadcast, and engagement metrics.",
        )
        def mekong_zalo_status() -> str:
            return handle_zalo_status({})

        @app.tool(
            name="mekong_bhxh_calc",
            description="Calculate statutory Vietnamese social insurance (BHXH 8%/17.5%, BHYT 1.5%/3%, BHTN 1%/1%) with salary ceilings.",
        )
        def mekong_bhxh_calc(
            salary: float,
            region: int = 1,
            include_kpcd: bool = False,
            employee_id: str = "ADHOC",
        ) -> str:
            return handle_bhxh_calc({
                "salary": salary,
                "region": region,
                "include_kpcd": include_kpcd,
                "employee_id": employee_id,
            })

        @app.tool(
            name="mekong_bhxh_employees",
            description="List registered employees for social insurance reporting and declarations.",
        )
        def mekong_bhxh_employees(status: str = "all") -> str:
            return handle_bhxh_employees({"status": status})

        @app.tool(
            name="mekong_bhxh_declaration",
            description="Generate statutory electronic declaration D02-LT (bao_tang, bao_giam, dieu_chinh_luong).",
        )
        def mekong_bhxh_declaration(
            change_type: str,
            employee_id: str,
            effective_month: str = "",
            new_salary: float = 0.0,
            note: str = "",
        ) -> str:
            return handle_bhxh_declaration({
                "change_type": change_type,
                "employee_id": employee_id,
                "effective_month": effective_month,
                "new_salary": new_salary,
                "note": note,
            })

        @app.tool(
            name="mekong_bhxh_status",
            description="Retrieve Vietnamese social insurance regulatory status, contribution totals, and active employee metrics.",
        )
        def mekong_bhxh_status() -> str:
            return handle_bhxh_status({})

        @app.tool(
            name="mekong_ocop_eval",
            description="Evaluate Vietnamese agricultural product OCOP star classification (1 to 5 stars) under Decision 148/QĐ-TTg.",
        )
        def mekong_ocop_eval(
            product_name: str,
            part_a: float = 30.0,
            part_b: float = 22.0,
            part_c: float = 38.0,
        ) -> str:
            return handle_ocop_eval({
                "product_name": product_name,
                "part_a": part_a,
                "part_b": part_b,
                "part_c": part_c,
            })

        @app.tool(
            name="mekong_ocop_products",
            description="Browse registered Vietnamese OCOP products, HS code classifications, and international certifications.",
        )
        def mekong_ocop_products(min_stars: int = 1, province: str = "all") -> str:
            return handle_ocop_products({
                "min_stars": min_stars,
                "province": province,
            })

        @app.tool(
            name="mekong_ocop_listing",
            description="Synthesize international B2B export marketplace listing and trade compliance audit (Alibaba, Amazon, Shopee).",
        )
        def mekong_ocop_listing(
            product_id: str,
            target_market: str = "EU",
            platform: str = "alibaba",
        ) -> str:
            return handle_ocop_listing({
                "product_id": product_id,
                "target_market": target_market,
                "platform": platform,
            })

        @app.tool(
            name="mekong_ocop_compliance",
            description="Inspect technical trade barriers, tariff preferences under FTAs (EVFTA, CPTPP, RCEP), and required food safety certs.",
        )
        def mekong_ocop_compliance(market: str = "EU") -> str:
            return handle_ocop_compliance({
                "market": market,
            })

        @app.tool(
            name="mekong_ocop_status",
            description="Retrieve national OCOP program telemetry, star breakdown, and registered export listings.",
        )
        def mekong_ocop_status() -> str:
            return handle_ocop_status({})

        @app.tool(
            name="mekong_vietqr_generate",
            description="Construct EMVCo VietQR string and Napas 247 QuickLink for instant interbank fund transfers.",
        )
        def mekong_vietqr_generate(
            amount: int = 0,
            memo: str = "",
            bank: str = "MB",
            account_number: str = "",
            account_name: str = "",
        ) -> str:
            return handle_vietqr_generate({
                "amount": amount,
                "memo": memo,
                "bank": bank,
                "account_number": account_number,
                "account_name": account_name,
            })

        @app.tool(
            name="mekong_vietqr_banks",
            description="Lookup Vietnamese Napas 247 participant banks, BIN codes, and short names.",
        )
        def mekong_vietqr_banks() -> str:
            return handle_vietqr_banks({})

        @app.tool(
            name="mekong_vietqr_transactions",
            description="List recent incoming bank transfer transactions and payment reconciliation records.",
        )
        def mekong_vietqr_transactions(limit: int = 20) -> str:
            return handle_vietqr_transactions({"limit": limit})

        @app.tool(
            name="mekong_vietqr_record",
            description="Record and reconcile an incoming bank payment transaction idempotently.",
        )
        def mekong_vietqr_record(
            bank_tx_id: str,
            amount_vnd: int,
            memo: str = "",
            bin_code: str = "970422",
            matched_order_id: str = "",
        ) -> str:
            return handle_vietqr_record({
                "bank_tx_id": bank_tx_id,
                "amount_vnd": amount_vnd,
                "memo": memo,
                "bin_code": bin_code,
                "matched_order_id": matched_order_id,
            })

        @app.tool(
            name="mekong_vietqr_status",
            description="Retrieve VietQR payment gateway status, default account, and volume metrics.",
        )
        def mekong_vietqr_status() -> str:
            return handle_vietqr_status({})

        @app.tool(
            name="mekong_audit_run",
            description="Execute automated SOX 404, ITGC, and internal controls testing across all control domains.",
        )
        def mekong_audit_run(framework: str = "all") -> str:
            return handle_audit_run({"framework": framework})

        @app.tool(
            name="mekong_audit_controls",
            description="Browse internal controls catalog, risk ratings, and validation procedures across AC, CM, CO, and SD domains.",
        )
        def mekong_audit_controls(domain: str = "all", framework: str = "all") -> str:
            return handle_audit_controls({"domain": domain, "framework": framework})

        @app.tool(
            name="mekong_audit_findings",
            description="Inspect open audit deficiencies, material weaknesses, and remediation action plans.",
        )
        def mekong_audit_findings(min_severity: str = "all") -> str:
            return handle_audit_findings({"min_severity": min_severity})

        @app.tool(
            name="mekong_audit_status",
            description="Retrieve executive internal controls audit posture, latest compliance score, and audit opinion.",
        )
        def mekong_audit_status() -> str:
            return handle_audit_status({})

        @app.tool(
            name="mekong_payroll_gross_to_net",
            description="Calculate Vietnamese Net take-home pay, employee insurance, PIT tax, and employer burden from Gross salary.",
        )
        def mekong_payroll_gross_to_net(
            gross: float,
            dependents: int = 0,
            region: int = 1,
            lunch_allowance: float = 730000.0,
        ) -> str:
            return handle_payroll_gross_to_net({
                "gross": gross,
                "dependents": dependents,
                "region": region,
                "lunch_allowance": lunch_allowance,
            })

        @app.tool(
            name="mekong_payroll_net_to_gross",
            description="Convert desired Net take-home salary to required contractual Gross salary and employer cost.",
        )
        def mekong_payroll_net_to_gross(
            net: float,
            dependents: int = 0,
            region: int = 1,
            lunch_allowance: float = 730000.0,
        ) -> str:
            return handle_payroll_net_to_gross({
                "net": net,
                "dependents": dependents,
                "region": region,
                "lunch_allowance": lunch_allowance,
            })

        @app.tool(
            name="mekong_payroll_payslip",
            description="Generate and persist an itemized electronic payslip for an employee.",
        )
        def mekong_payroll_payslip(
            employee_name: str,
            gross: float,
            employee_id: str = "",
            month: str = "",
            dependents: int = 0,
            region: int = 1,
            bonus: float = 0.0,
        ) -> str:
            return handle_payroll_payslip({
                "employee_name": employee_name,
                "gross": gross,
                "employee_id": employee_id,
                "month": month,
                "dependents": dependents,
                "region": region,
                "bonus": bonus,
            })

        @app.tool(
            name="mekong_payroll_list",
            description="Query historical electronic payslips and compensation disbursement records.",
        )
        def mekong_payroll_list(month: str = "", limit: int = 20) -> str:
            return handle_payroll_list({"month": month, "limit": limit})

        @app.tool(
            name="mekong_payroll_status",
            description="Retrieve Vietnamese payroll system status, statutory parameters, and total disburse metrics.",
        )
        def mekong_payroll_status() -> str:
            return handle_payroll_status({})

        @app.tool(
            name="mekong_corporate_charter",
            description="Synthesize a complete 10-chapter Corporate Charter (Điều lệ công ty) complying with Article 24 Law on Enterprises 2020.",
        )
        def mekong_corporate_charter(
            company_name: str,
            entity_type: str = "TNHH_1TV",
            charter_capital: int = 1000000000,
            legal_rep_name: str = "Nguyễn Văn A",
            address: str = "Hà Nội, Việt Nam",
        ) -> str:
            return handle_corporate_charter({
                "company_name": company_name,
                "entity_type": entity_type,
                "charter_capital": charter_capital,
                "legal_rep_name": legal_rep_name,
                "address": address,
            })

        @app.tool(
            name="mekong_corporate_resolution",
            description="Draft statutory Board / Member Council resolution and meeting minutes.",
        )
        def mekong_corporate_resolution(
            company_name: str,
            resolution_type: str = "APPOINTMENT",
            title: str = "",
        ) -> str:
            return handle_corporate_resolution({
                "company_name": company_name,
                "resolution_type": resolution_type,
                "title": title,
            })

        @app.tool(
            name="mekong_corporate_dossier",
            description="Synthesize complete statutory business incorporation dossier under Decree 01/2021/NĐ-CP.",
        )
        def mekong_corporate_dossier(
            company_name: str,
            entity_type: str = "TNHH_1TV",
            charter_capital: int = 1000000000,
            legal_rep_name: str = "Nguyễn Văn A",
            address: str = "Hà Nội, Việt Nam",
            main_industry: str = "6201",
        ) -> str:
            return handle_corporate_dossier({
                "company_name": company_name,
                "entity_type": entity_type,
                "charter_capital": charter_capital,
                "legal_rep_name": legal_rep_name,
                "address": address,
                "main_industry": main_industry,
            })

        @app.tool(
            name="mekong_corporate_list",
            description="Query historical corporate filings, charters, and statutory governance documents.",
        )
        def mekong_corporate_list(limit: int = 20) -> str:
            return handle_corporate_list({"limit": limit})

        @app.tool(
            name="mekong_corporate_status",
            description="Retrieve corporate governance engine metrics, registered entity counts, and legal framework.",
        )
        def mekong_corporate_status() -> str:
            return handle_corporate_status({})

        @app.tool(
            name="mekong_fdi_market_access",
            description="Evaluate foreign ownership limits, market access conditions, and international treaties (WTO/CPTPP/EVFTA).",
        )
        def mekong_fdi_market_access(
            sector_code: str,
            investor_nationality: str = "US",
            ownership_pct: float = 100.0,
        ) -> str:
            return handle_fdi_market_access({
                "sector_code": sector_code,
                "investor_nationality": investor_nationality,
                "ownership_pct": ownership_pct,
            })

        @app.tool(
            name="mekong_fdi_remittance",
            description="Verify offshore profit remittance eligibility, statutory DICA account, tax clearance, and legal reserve rules.",
        )
        def mekong_fdi_remittance(
            fiscal_year: int,
            audited_profit_vnd: float,
            tax_cleared: bool = True,
            retained_reserve_pct: float = 5.0,
            dica_verified: bool = True,
            losses_carried_forward_vnd: float = 0.0,
        ) -> str:
            return handle_fdi_remittance({
                "fiscal_year": fiscal_year,
                "audited_profit_vnd": audited_profit_vnd,
                "tax_cleared": tax_cleared,
                "retained_reserve_pct": retained_reserve_pct,
                "dica_verified": dica_verified,
                "losses_carried_forward_vnd": losses_carried_forward_vnd,
            })

        @app.tool(
            name="mekong_fdi_foreign_loan",
            description="Evaluate offshore foreign loan compliance, SBV registration triggers, and foreign debt ceiling limit.",
        )
        def mekong_fdi_foreign_loan(
            loan_amount: float,
            currency: str = "USD",
            tenure_months: int = 24,
            interest_rate_pct: float = 6.5,
            project_capital_gap: float = 0.0,
        ) -> str:
            return handle_fdi_foreign_loan({
                "loan_amount": loan_amount,
                "currency": currency,
                "tenure_months": tenure_months,
                "interest_rate_pct": interest_rate_pct,
                "project_capital_gap": project_capital_gap,
            })

        @app.tool(
            name="mekong_fdi_irc",
            description="Synthesize statutory Investment Registration Certificate (IRC) application dossier under Law on Investment 2020.",
        )
        def mekong_fdi_irc(
            project_name: str,
            sector_code: str,
            total_investment_vnd: float,
            investor_name: str,
            investor_country: str = "US",
            project_location: str = "TP. Hồ Chí Minh",
        ) -> str:
            return handle_fdi_irc({
                "project_name": project_name,
                "sector_code": sector_code,
                "total_investment_vnd": total_investment_vnd,
                "investor_name": investor_name,
                "investor_country": investor_country,
                "project_location": project_location,
            })

        @app.tool(
            name="mekong_fdi_status",
            description="Retrieve FDI & SBV capital compliance engine metrics, registered projects, and legal framework.",
        )
        def mekong_fdi_status() -> str:
            return handle_fdi_status({})

        @app.tool(
            name="mekong_ip_trademark",
            description="Register a trademark application conforming to Nice Classification 12-2024 and Law on Intellectual Property.",
        )
        def mekong_ip_trademark(
            mark_name: str,
            nice_class: str = "09",
            applicant_name: str = "Công Ty Công Nghệ Mekong",
            goods_services_spec: str = "",
        ) -> str:
            return handle_ip_trademark({
                "mark_name": mark_name,
                "nice_class": nice_class,
                "applicant_name": applicant_name,
                "goods_services_spec": goods_services_spec,
            })

        @app.tool(
            name="mekong_ip_search",
            description="Search phonetical and orthographical trademark conflicts and assess likelihood of confusion under Article 74.",
        )
        def mekong_ip_search(
            mark_name: str,
            nice_class: str = "09",
        ) -> str:
            return handle_ip_search({
                "mark_name": mark_name,
                "nice_class": nice_class,
            })

        @app.tool(
            name="mekong_ip_patent",
            description="Draft statutory patent specification and independent/dependent claims under Article 102 Law on IP.",
        )
        def mekong_ip_patent(
            title: str,
            technical_field: str,
            applicant_name: str = "Tổ chức Nghiên cứu Mekong",
            independent_claims: int = 1,
            dependent_claims: int = 2,
        ) -> str:
            return handle_ip_patent({
                "title": title,
                "technical_field": technical_field,
                "applicant_name": applicant_name,
                "independent_claims": independent_claims,
                "dependent_claims": dependent_claims,
            })

        @app.tool(
            name="mekong_ip_copyright",
            description="Synthesize software computer program copyright registration dossier under Decree 17/2023/ND-CP.",
        )
        def mekong_ip_copyright(
            software_name: str,
            author_name: str,
            version: str = "1.0.0",
            repository_url: str = "",
            lines_of_code: int = 10000,
        ) -> str:
            return handle_ip_copyright({
                "software_name": software_name,
                "author_name": author_name,
                "version": version,
                "repository_url": repository_url,
                "lines_of_code": lines_of_code,
            })

        @app.tool(
            name="mekong_ip_fees",
            description="Calculate itemized state official IP registration fees under Circular 263/2016/TT-BTC.",
        )
        def mekong_ip_fees(
            trademark_classes: int = 1,
            patent_claims: int = 1,
            software_copyrights: int = 1,
        ) -> str:
            return handle_ip_fees({
                "trademark_classes": trademark_classes,
                "patent_claims": patent_claims,
                "software_copyrights": software_copyrights,
            })

        @app.tool(
            name="mekong_ip_status",
            description="Retrieve IP engine telemetry, Nice classification support, and registered asset counts.",
        )
        def mekong_ip_status() -> str:
            return handle_ip_status({})

        @app.tool(
            name="mekong_customs_hs_lookup",
            description="Look up 8-digit AHTN HS code tariff rates, MFN duty, import VAT, and preferential FTA rates.",
        )
        def mekong_customs_hs_lookup(
            hs_code: str,
            fta: str = "MFN",
        ) -> str:
            return handle_customs_hs_lookup({
                "hs_code": hs_code,
                "fta": fta,
            })

        @app.tool(
            name="mekong_customs_duty_calc",
            description="Calculate itemized CIF valuation, import duty, and import VAT obligations.",
        )
        def mekong_customs_duty_calc(
            invoice_value_usd: float,
            hs_code: str = "8471.30.20",
            freight_usd: float = 0.0,
            insurance_usd: float = 0.0,
            fta: str = "MFN",
        ) -> str:
            return handle_customs_duty_calc({
                "invoice_value_usd": invoice_value_usd,
                "hs_code": hs_code,
                "freight_usd": freight_usd,
                "insurance_usd": insurance_usd,
                "fta": fta,
            })

        @app.tool(
            name="mekong_customs_channel",
            description="Evaluate VNACCS automated risk criteria and determine Green, Yellow, or Red customs channel.",
        )
        def mekong_customs_channel(
            enterprise_tax_id: str,
            hs_code: str,
            invoice_value_usd: float,
            origin_country: str = "US",
            compliance_tier: str = "TIER_2_NORMAL",
            has_valid_co: bool = True,
        ) -> str:
            return handle_customs_channel({
                "enterprise_tax_id": enterprise_tax_id,
                "hs_code": hs_code,
                "invoice_value_usd": invoice_value_usd,
                "origin_country": origin_country,
                "compliance_tier": compliance_tier,
                "has_valid_co": has_valid_co,
            })

        @app.tool(
            name="mekong_customs_declare",
            description="Synthesize and submit a formal VNACCS/VCIS electronic customs declaration.",
        )
        def mekong_customs_declare(
            enterprise_tax_id: str,
            hs_code: str,
            commodity_name: str,
            invoice_value_usd: float,
            origin_country: str = "US",
            declaration_type: str = "IMPORT_BUSINESS",
            compliance_tier: str = "TIER_2_NORMAL",
            has_valid_co: bool = True,
        ) -> str:
            return handle_customs_declare({
                "enterprise_tax_id": enterprise_tax_id,
                "hs_code": hs_code,
                "commodity_name": commodity_name,
                "invoice_value_usd": invoice_value_usd,
                "origin_country": origin_country,
                "declaration_type": declaration_type,
                "compliance_tier": compliance_tier,
                "has_valid_co": has_valid_co,
            })

        @app.tool(
            name="mekong_customs_origin",
            description="Verify Rules of Origin (RVC >= 40% and CTC criteria) for preferential C/O certification.",
        )
        def mekong_customs_origin(
            form_type: str,
            hs_code: str,
            fob_value_usd: float,
            non_originating_value_usd: float,
            exporter_name: str = "Doanh Nghiệp Xuất Khẩu Việt Nam",
            importer_country: str = "DE",
        ) -> str:
            return handle_customs_origin({
                "form_type": form_type,
                "hs_code": hs_code,
                "fob_value_usd": fob_value_usd,
                "non_originating_value_usd": non_originating_value_usd,
                "exporter_name": exporter_name,
                "importer_country": importer_country,
            })

        @app.tool(
            name="mekong_customs_status",
            description="Retrieve customs engine telemetry, VNACCS channel distribution, and total duty collected.",
        )
        def mekong_customs_status() -> str:
            return handle_customs_status({})

        @app.tool(
            name="mekong_contract_draft",
            description="Synthesize standard commercial contract complying with Vietnamese law (SOFTWARE_DEV, COMMERCIAL_SALE, NDA, DISTRIBUTION).",
        )
        def mekong_contract_draft(
            template_type: str,
            party_a_name: str,
            party_b_name: str,
            contract_value_vnd: float = 0.0,
            party_a_tax_id: str = "0100000001",
            party_b_tax_id: str = "0300000002",
            scope_summary: str = "",
            penalty_rate_pct: float = 8.0,
            dispute_forum: str = "VIAC",
        ) -> str:
            return handle_contract_draft({
                "template_type": template_type,
                "party_a_name": party_a_name,
                "party_b_name": party_b_name,
                "contract_value_vnd": contract_value_vnd,
                "party_a_tax_id": party_a_tax_id,
                "party_b_tax_id": party_b_tax_id,
                "scope_summary": scope_summary,
                "penalty_rate_pct": penalty_rate_pct,
                "dispute_forum": dispute_forum,
            })

        @app.tool(
            name="mekong_contract_risk_check",
            description="Scan contract clauses for legal risks, penalty breach (>8%), missing force majeure, and redline recommendations.",
        )
        def mekong_contract_risk_check(
            contract_text: str,
            penalty_pct: float = 8.0,
        ) -> str:
            return handle_contract_risk_check({
                "contract_text": contract_text,
                "penalty_pct": penalty_pct,
            })

        @app.tool(
            name="mekong_contract_sign",
            description="Sign a commercial contract electronically with cryptographic SHA-256 digest and TSA timestamp under Law on Electronic Transactions 2023.",
        )
        def mekong_contract_sign(
            contract_id: str,
            signer_name: str,
            signer_title: str = "Giám đốc điều hành",
            signer_tax_id: str = "0100000001",
            organization_name: str = "",
        ) -> str:
            return handle_contract_sign({
                "contract_id": contract_id,
                "signer_name": signer_name,
                "signer_title": signer_title,
                "signer_tax_id": signer_tax_id,
                "organization_name": organization_name,
            })

        @app.tool(
            name="mekong_contract_verify",
            description="Verify authenticity, integrity, and timestamp of an electronic contract signature.",
        )
        def mekong_contract_verify(
            signature_id: str,
        ) -> str:
            return handle_contract_verify({
                "signature_id": signature_id,
            })

        @app.tool(
            name="mekong_contract_list",
            description="Query historical commercial contracts and execution/signing status.",
        )
        def mekong_contract_list(
            status: str = "ALL",
            limit: int = 20,
        ) -> str:
            return handle_contract_list({
                "status": status,
                "limit": limit,
            })

        @app.tool(
            name="mekong_contract_status",
            description="Retrieve contract engine telemetry, active e-signatures, template catalog, and risk metrics.",
        )
        def mekong_contract_status() -> str:
            return handle_contract_status({})

        @app.tool(
            name="mekong_tender_method",
            description="Evaluate and advise statutory procurement method (Open Bidding, Direct Contracting, Competitive Quotation) under Bidding Law 2023.",
        )
        def mekong_tender_method(
            package_type: str,
            budget_vnd: float,
            urgent: bool = False,
            proprietary: bool = False,
        ) -> str:
            return handle_tender_method({
                "package_type": package_type,
                "budget_vnd": budget_vnd,
                "urgent": urgent,
                "proprietary": proprietary,
            })

        @app.tool(
            name="mekong_tender_create",
            description="Synthesize and publish an electronic tender dossier (E-HSMT) on National E-GP under Decree 24/2024/ND-CP.",
        )
        def mekong_tender_create(
            package_name: str,
            procuring_entity: str,
            budget_vnd: float,
            package_type: str = "GOODS",
            procurement_method: str = "",
            submission_days: int = 15,
        ) -> str:
            return handle_tender_create({
                "package_name": package_name,
                "procuring_entity": procuring_entity,
                "budget_vnd": budget_vnd,
                "package_type": package_type,
                "procurement_method": procurement_method,
                "submission_days": submission_days,
            })

        @app.tool(
            name="mekong_tender_eval",
            description="Execute statutory 4-step E-HSDT bid evaluation (eligibility, capacity/experience, technical floor, financial/savings).",
        )
        def mekong_tender_eval(
            tender_id: str,
            bidder_name: str,
            bid_price_vnd: float,
            bidder_tax_id: str = "0101234567",
            revenue_3yr_avg_vnd: float = 0.0,
            similar_contract_val_vnd: float = 0.0,
            tech_score: float = 85.0,
            has_valid_security: bool = True,
        ) -> str:
            return handle_tender_eval({
                "tender_id": tender_id,
                "bidder_name": bidder_name,
                "bid_price_vnd": bid_price_vnd,
                "bidder_tax_id": bidder_tax_id,
                "revenue_3yr_avg_vnd": revenue_3yr_avg_vnd,
                "similar_contract_val_vnd": similar_contract_val_vnd,
                "tech_score": tech_score,
                "has_valid_security": has_valid_security,
            })

        @app.tool(
            name="mekong_tender_collusion_scan",
            description="Scan submitted tender bids for anti-competitive collusion, abnormal price clustering, and affiliate conflicts under Article 16 Bidding Law 2023.",
        )
        def mekong_tender_collusion_scan(
            tender_id: str,
        ) -> str:
            return handle_tender_collusion_scan({
                "tender_id": tender_id,
            })

        @app.tool(
            name="mekong_tender_list",
            description="Query registered tender packages and active biddings on National E-GP.",
        )
        def mekong_tender_list(
            status: str = "ALL",
            limit: int = 20,
        ) -> str:
            return handle_tender_list({
                "status": status,
                "limit": limit,
            })

        @app.tool(
            name="mekong_tender_status",
            description="Retrieve public procurement telemetry, budget, savings rate, and E-GP bidding metrics.",
        )
        def mekong_tender_status() -> str:
            return handle_tender_status({})

        @app.tool(
            name="mekong_realestate_finance",
            description="Calculate complete commercial/industrial leasing cash flow schedule, security deposit, and total value.",
        )
        def mekong_realestate_finance(
            category: str,
            area_sqm: float,
            unit_rent_usd: float,
            lease_term_months: int = 36,
            maintenance_fee_usd: float = 0.5,
            deposit_months: int = 3,
            annual_escalation_pct: float = 3.0,
        ) -> str:
            return handle_realestate_finance({
                "category": category,
                "area_sqm": area_sqm,
                "unit_rent_usd": unit_rent_usd,
                "lease_term_months": lease_term_months,
                "maintenance_fee_usd": maintenance_fee_usd,
                "deposit_months": deposit_months,
                "annual_escalation_pct": annual_escalation_pct,
            })

        @app.tool(
            name="mekong_realestate_density",
            description="Validate industrial/commercial site density (<=70%) and green space ratio (>=10%) against QCVN 01:2021/BXD.",
        )
        def mekong_realestate_density(
            lot_area_sqm: float,
            building_footprint_sqm: float,
            green_space_sqm: float,
            building_height_tier: str = "UP_TO_20M",
        ) -> str:
            return handle_realestate_density({
                "lot_area_sqm": lot_area_sqm,
                "building_footprint_sqm": building_footprint_sqm,
                "green_space_sqm": green_space_sqm,
                "building_height_tier": building_height_tier,
            })

        @app.tool(
            name="mekong_realestate_audit",
            description="Audit legal title, construction readiness, fire safety cert, and statutory conditions for real estate leasing.",
        )
        def mekong_realestate_audit(
            project_name: str,
            category: str,
            land_area_sqm: float,
            has_land_cert: bool = True,
            has_construction_permit: bool = True,
            has_fire_safety_cert: bool = True,
            tenure_remaining_years: float = 35.0,
            payment_term: str = "ANNUAL_RENT",
            has_disputes: bool = False,
            is_mortgaged_to_bank: bool = False,
        ) -> str:
            return handle_realestate_audit({
                "project_name": project_name,
                "category": category,
                "land_area_sqm": land_area_sqm,
                "has_land_cert": has_land_cert,
                "has_construction_permit": has_construction_permit,
                "has_fire_safety_cert": has_fire_safety_cert,
                "tenure_remaining_years": tenure_remaining_years,
                "payment_term": payment_term,
                "has_disputes": has_disputes,
                "is_mortgaged_to_bank": is_mortgaged_to_bank,
            })

        @app.tool(
            name="mekong_realestate_draft",
            description="Synthesize a complete commercial/industrial lease agreement complying with Decree 96/2024/ND-CP.",
        )
        def mekong_realestate_draft(
            property_id: str,
            lessor_name: str,
            lessee_name: str,
            leased_area_sqm: float,
            unit_rent_usd: float,
            lease_term_months: int = 36,
            maintenance_fee_usd: float = 0.5,
            deposit_months: int = 3,
            dispute_resolution: str = "VIAC",
        ) -> str:
            return handle_realestate_draft({
                "property_id": property_id,
                "lessor_name": lessor_name,
                "lessee_name": lessee_name,
                "leased_area_sqm": leased_area_sqm,
                "unit_rent_usd": unit_rent_usd,
                "lease_term_months": lease_term_months,
                "maintenance_fee_usd": maintenance_fee_usd,
                "deposit_months": deposit_months,
                "dispute_resolution": dispute_resolution,
            })

        @app.tool(
            name="mekong_realestate_list",
            description="Query registered real estate properties and industrial parks.",
        )
        def mekong_realestate_list(
            category: str = "ALL",
            limit: int = 20,
        ) -> str:
            return handle_realestate_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_realestate_status",
            description="Retrieve commercial real estate engine telemetry, total managed area, active leases, and metrics.",
        )
        def mekong_realestate_status() -> str:
            return handle_realestate_status({})

        @app.tool(
            name="mekong_esg_ghg",
            description="Compute enterprise greenhouse gas (GHG) emissions inventory across Scope 1, 2, 3 under ISO 14064-1 & Decision 13/2024/QD-TTg.",
        )
        def mekong_esg_ghg(
            enterprise_name: str,
            reporting_year: int,
            fuel_diesel_liters: float = 0.0,
            fuel_gasoline_liters: float = 0.0,
            coal_tons: float = 0.0,
            lpg_kg: float = 0.0,
            electricity_kwh: float = 0.0,
            scope3_logistics_tco2e: float = 0.0,
        ) -> str:
            return handle_esg_ghg({
                "enterprise_name": enterprise_name,
                "reporting_year": reporting_year,
                "fuel_diesel_liters": fuel_diesel_liters,
                "fuel_gasoline_liters": fuel_gasoline_liters,
                "coal_tons": coal_tons,
                "lpg_kg": lpg_kg,
                "electricity_kwh": electricity_kwh,
                "scope3_logistics_tco2e": scope3_logistics_tco2e,
            })

        @app.tool(
            name="mekong_esg_cbam",
            description="Evaluate EU CBAM embedded emissions and financial certificate liability for Vietnam exports (Regulation EU 2023/956).",
        )
        def mekong_esg_cbam(
            product_type: str,
            export_volume_tons: float,
            direct_emissions_tco2: float,
            indirect_emissions_tco2: float = 0.0,
            cbam_carbon_price_eur_per_ton: float = 75.0,
        ) -> str:
            return handle_esg_cbam({
                "product_type": product_type,
                "export_volume_tons": export_volume_tons,
                "direct_emissions_tco2": direct_emissions_tco2,
                "indirect_emissions_tco2": indirect_emissions_tco2,
                "cbam_carbon_price_eur_per_ton": cbam_carbon_price_eur_per_ton,
            })

        @app.tool(
            name="mekong_esg_audit",
            description="Audit and synthesize corporate ESG composite score and rating under Circular 96/2020/TT-BTC & GRI standards.",
        )
        def mekong_esg_audit(
            enterprise_name: str,
            has_iso_14001: bool = True,
            renewable_energy_ratio_pct: float = 20.0,
            has_waste_treatment_license: bool = True,
            full_social_insurance_compliance: bool = True,
            workplace_accident_rate: float = 0.0,
            female_leadership_ratio_pct: float = 30.0,
            independent_board_members_ratio_pct: float = 33.3,
            has_anti_corruption_policy: bool = True,
            has_audited_financial_report: bool = True,
        ) -> str:
            return handle_esg_audit({
                "enterprise_name": enterprise_name,
                "has_iso_14001": has_iso_14001,
                "renewable_energy_ratio_pct": renewable_energy_ratio_pct,
                "has_waste_treatment_license": has_waste_treatment_license,
                "full_social_insurance_compliance": full_social_insurance_compliance,
                "workplace_accident_rate": workplace_accident_rate,
                "female_leadership_ratio_pct": female_leadership_ratio_pct,
                "independent_board_members_ratio_pct": independent_board_members_ratio_pct,
                "has_anti_corruption_policy": has_anti_corruption_policy,
                "has_audited_financial_report": has_audited_financial_report,
            })

        @app.tool(
            name="mekong_esg_carbon_trade",
            description="Execute carbon credit transaction or offset surrender under Articles 93 & 94 Environmental Law 2020.",
        )
        def mekong_esg_carbon_trade(
            project_name: str,
            credit_type: str,
            quantity_tco2e: float,
            unit_price_usd: float,
            action: str = "BUY",
            counterparty: str = "Sàn giao dịch Carbon Quốc gia",
        ) -> str:
            return handle_esg_carbon_trade({
                "project_name": project_name,
                "credit_type": credit_type,
                "quantity_tco2e": quantity_tco2e,
                "unit_price_usd": unit_price_usd,
                "action": action,
                "counterparty": counterparty,
            })

        @app.tool(
            name="mekong_esg_list",
            description="Query registered enterprise GHG inventories and carbon transaction ledger.",
        )
        def mekong_esg_list(
            limit: int = 20,
        ) -> str:
            return handle_esg_list({
                "limit": limit,
            })

        @app.tool(
            name="mekong_esg_status",
            description="Retrieve ESG compliance telemetry, tracked emissions, carbon trades, and green metrics.",
        )
        def mekong_esg_status() -> str:
            return handle_esg_status({})

        @app.tool(
            name="mekong_supplychain_plot",
            description="Register agricultural or forestry production plot with EUDR coordinates (Regulation EU 2023/1115).",
        )
        def mekong_supplychain_plot(
            farmer_name: str,
            province: str,
            commodity: str,
            latitude: float,
            longitude: float,
            area_hectares: float,
            district: str = "Tây Nguyên",
            deforestation_free_post_2020: bool = True,
            legal_land_cert: str = "Sổ đỏ nông nghiệp / Giấy chứng nhận QSDĐ",
        ) -> str:
            return handle_supplychain_plot({
                "farmer_name": farmer_name,
                "province": province,
                "commodity": commodity,
                "latitude": latitude,
                "longitude": longitude,
                "area_hectares": area_hectares,
                "district": district,
                "deforestation_free_post_2020": deforestation_free_post_2020,
                "legal_land_cert": legal_land_cert,
            })

        @app.tool(
            name="mekong_supplychain_batch",
            description="Initialize export traceability batch with plot linkage and SHA-256 fingerprint.",
        )
        def mekong_supplychain_batch(
            batch_code: str,
            commodity: str,
            quantity_kg: float,
            processor_name: str,
            plot_ids: list[str] = None,
            certifications: list[str] = None,
        ) -> str:
            return handle_supplychain_batch({
                "batch_code": batch_code,
                "commodity": commodity,
                "quantity_kg": quantity_kg,
                "processor_name": processor_name,
                "plot_ids": plot_ids,
                "certifications": certifications,
            })

        @app.tool(
            name="mekong_supplychain_event",
            description="Record EPCIS custody transfer event with cryptographic hash chaining (GS1 EPCIS 2.0).",
        )
        def mekong_supplychain_event(
            batch_code: str,
            event_type: str,
            location: str,
            actor_name: str,
            notes: str = "",
        ) -> str:
            return handle_supplychain_event({
                "batch_code": batch_code,
                "event_type": event_type,
                "location": location,
                "actor_name": actor_name,
                "notes": notes,
            })

        @app.tool(
            name="mekong_supplychain_eudr",
            description="Synthesize official EUDR Due Diligence Statement (DDS) dossier for EU export customs.",
        )
        def mekong_supplychain_eudr(
            batch_code: str,
            exporter_name: str,
            importer_name: str,
            destination_country: str = "Germany",
        ) -> str:
            return handle_supplychain_eudr({
                "batch_code": batch_code,
                "exporter_name": exporter_name,
                "importer_name": importer_name,
                "destination_country": destination_country,
            })

        @app.tool(
            name="mekong_supplychain_trace",
            description="Retrieve complete end-to-end provenance timeline and custody chain for an export batch.",
        )
        def mekong_supplychain_trace(
            batch_code: str,
        ) -> str:
            return handle_supplychain_trace({
                "batch_code": batch_code,
            })

        @app.tool(
            name="mekong_supplychain_status",
            description="Retrieve supply chain engine telemetry, monitored area, and volume metrics.",
        )
        def mekong_supplychain_status() -> str:
            return handle_supplychain_status({})

        @app.tool(
            name="mekong_labor_permit",
            description="Assess foreign worker eligibility for work permit or statutory exemption under Decree 152/2020 & 70/2023.",
        )
        def mekong_labor_permit(
            worker_name: str,
            nationality: str,
            position: str,
            job_title: str,
            degree: str = "BACHELOR",
            exp: float = 3.0,
            capital: float = 0.0,
            wto: bool = False,
            married_vn: bool = False,
            passport: str = "PASS-DEFAULT",
        ) -> str:
            return handle_labor_permit({
                "worker_name": worker_name,
                "nationality": nationality,
                "position": position,
                "job_title": job_title,
                "degree": degree,
                "exp": exp,
                "capital": capital,
                "wto": wto,
                "married_vn": married_vn,
                "passport": passport,
            })

        @app.tool(
            name="mekong_labor_overtime",
            description="Calculate statutory overtime pay and night shift rates under Labor Code 2019 Article 98.",
        )
        def mekong_labor_overtime(
            hourly_rate: float,
            weekday_ot: float = 0.0,
            weekend_ot: float = 0.0,
            holiday_ot: float = 0.0,
            night_regular: float = 0.0,
            night_ot: float = 0.0,
        ) -> str:
            return handle_labor_overtime({
                "hourly_rate": hourly_rate,
                "weekday_ot": weekday_ot,
                "weekend_ot": weekend_ot,
                "holiday_ot": holiday_ot,
                "night_regular": night_regular,
                "night_ot": night_ot,
            })

        @app.tool(
            name="mekong_labor_caps",
            description="Audit monthly and annual overtime working hours against Article 107 statutory limits.",
        )
        def mekong_labor_caps(
            employee_id: str,
            employee_name: str,
            monthly_ot_hours: float,
            yearly_cumulative_hours: float,
            industry: str = "GENERAL",
            exceptional: bool = False,
        ) -> str:
            return handle_labor_caps({
                "employee_id": employee_id,
                "employee_name": employee_name,
                "monthly_ot_hours": monthly_ot_hours,
                "yearly_cumulative_hours": yearly_cumulative_hours,
                "industry": industry,
                "exceptional": exceptional,
            })

        @app.tool(
            name="mekong_labor_severance",
            description="Calculate statutory severance pay (Article 46) or job loss allowance (Article 47).",
        )
        def mekong_labor_severance(
            employee_name: str,
            average_salary: float,
            total_years: float,
            bhtn_years: float = 0.0,
            allowance_type: str = "SEVERANCE",
        ) -> str:
            return handle_labor_severance({
                "employee_name": employee_name,
                "average_salary": average_salary,
                "total_years": total_years,
                "bhtn_years": bhtn_years,
                "allowance_type": allowance_type,
            })

        @app.tool(
            name="mekong_labor_regulations",
            description="Audit Internal Labor Regulations (NQLD) compliance under Article 118 for enterprises with 10+ employees.",
        )
        def mekong_labor_regulations(
            enterprise_name: str,
            total_employees: int,
            has_written_regulations: bool = True,
            is_registered: bool = True,
            dialogue: bool = True,
            safety_council: bool = True,
            docket: str = "NQLD-2026-DOLAB",
        ) -> str:
            return handle_labor_regulations({
                "enterprise_name": enterprise_name,
                "total_employees": total_employees,
                "has_written_regulations": has_written_regulations,
                "is_registered": is_registered,
                "dialogue": dialogue,
                "safety_council": safety_council,
                "docket": docket,
            })

        @app.tool(
            name="mekong_labor_list",
            description="Query registered foreign worker permit dossiers and audit records.",
        )
        def mekong_labor_list(
            category: str = "ALL",
            limit: int = 50,
        ) -> str:
            return handle_labor_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_labor_status",
            description="Retrieve Vietnamese labor compliance engine metrics, telemetry, and statutory threshold status.",
        )
        def mekong_labor_status() -> str:
            return handle_labor_status({})

        @app.tool(
            name="mekong_maritime_vessel",
            description="Register commercial vessel call, schedule berthing, and audit channel draft requirements.",
        )
        def mekong_maritime_vessel(
            name: str,
            imo: str,
            flag: str,
            dwt: float,
            grt: float,
            loa: float,
            draft: float,
            port_code: str,
            terminal: str,
            eta: str,
            etd: str,
            call_sign: str = "3XYZ",
        ) -> str:
            return handle_maritime_vessel({
                "name": name,
                "imo": imo,
                "flag": flag,
                "dwt": dwt,
                "grt": grt,
                "loa": loa,
                "draft": draft,
                "port_code": port_code,
                "terminal": terminal,
                "eta": eta,
                "etd": etd,
                "call_sign": call_sign,
            })

        @app.tool(
            name="mekong_maritime_container",
            description="Record container inventory, 3D yard slot location, and SOLAS VGM gross mass compliance.",
        )
        def mekong_maritime_container(
            container_no: str,
            container_type: str,
            gross_weight: float,
            seal: str,
            booking_or_bl: str,
            slot: str = "YARD-B01-R03-T2",
            tare: float = 2300.0,
            reefer: bool = False,
            dg: bool = False,
        ) -> str:
            return handle_maritime_container({
                "container_no": container_no,
                "container_type": container_type,
                "gross_weight": gross_weight,
                "seal": seal,
                "booking_or_bl": booking_or_bl,
                "slot": slot,
                "tare": tare,
                "reefer": reefer,
                "dg": dg,
            })

        @app.tool(
            name="mekong_maritime_tariff",
            description="Compute statutory berth dues, pilotage fees, and container LoLo stevedoring tariffs (Circular 39/2023).",
        )
        def mekong_maritime_tariff(
            vessel_call: str,
            group: str,
            grt: float,
            berth_hours: float,
            distance: float = 18.0,
            f20: int = 0,
            f40: int = 0,
            e20: int = 0,
            e40: int = 0,
            reefer_hrs: float = 0.0,
            reefer_cnt: int = 0,
            terminal: str = "Tân Cảng Cát Lái",
        ) -> str:
            return handle_maritime_tariff({
                "vessel_call": vessel_call,
                "group": group,
                "grt": grt,
                "berth_hours": berth_hours,
                "distance": distance,
                "f20": f20,
                "f40": f40,
                "e20": e20,
                "e40": e40,
                "reefer_hrs": reefer_hrs,
                "reefer_cnt": reefer_cnt,
                "terminal": terminal,
            })

        @app.tool(
            name="mekong_maritime_manifest",
            description="Submit electronic sea cargo e-Manifest to VNACCS / National Single Window.",
        )
        def mekong_maritime_manifest(
            vessel_call: str,
            bl: str,
            shipper: str,
            consignee: str,
            cargo: str,
            containers: int,
            gross_kg: float,
            decl_no: typing.Optional[str] = None,
        ) -> str:
            return handle_maritime_manifest({
                "vessel_call": vessel_call,
                "bl": bl,
                "shipper": shipper,
                "consignee": consignee,
                "cargo": cargo,
                "containers": containers,
                "gross_kg": gross_kg,
                "decl_no": decl_no,
            })

        @app.tool(
            name="mekong_maritime_list",
            description="Query scheduled vessel calls or container inventory in terminal yards and ICD depots.",
        )
        def mekong_maritime_list(
            item_type: str = "vessels",
            yard: str = "ALL",
            limit: int = 50,
        ) -> str:
            return handle_maritime_list({
                "item_type": item_type,
                "yard": yard,
                "limit": limit,
            })

        @app.tool(
            name="mekong_maritime_status",
            description="Retrieve Vietnamese maritime logistics, vessel schedule, and terminal yard metrics.",
        )
        def mekong_maritime_status() -> str:
            return handle_maritime_status({})

        @app.tool(
            name="mekong_energy_solar",
            description="Evaluate rooftop solar (ĐMTMN) self-consumption, Decree 135/2024 surplus caps, and carbon offsets.",
        )
        def mekong_energy_solar(
            project_id: str,
            capacity_kwp: float,
            location: str = "Binh Thuan",
            self_consumption_pct: float = 80.0,
            grid_connection: str = "connected",
            battery_storage_kwh: float = 0.0,
        ) -> str:
            return handle_energy_solar({
                "project_id": project_id,
                "capacity_kwp": capacity_kwp,
                "location": location,
                "self_consumption_pct": self_consumption_pct,
                "grid_connection": grid_connection,
                "battery_storage_kwh": battery_storage_kwh,
            })

        @app.tool(
            name="mekong_energy_dppa",
            description="Evaluate Direct Power Purchase Agreement (DPPA) under Decree 80/2024, private wire vs national grid CfD settlement.",
        )
        def mekong_energy_dppa(
            contract_id: str,
            buyer_id: str,
            seller_id: str,
            mechanism: str = "direct",
            contract_kwh_month: float = 500000.0,
            strike_price_vnd_kwh: float = 1800.0,
            spot_price_vnd_kwh: float = 1650.0,
        ) -> str:
            return handle_energy_dppa({
                "contract_id": contract_id,
                "buyer_id": buyer_id,
                "seller_id": seller_id,
                "mechanism": mechanism,
                "contract_kwh_month": contract_kwh_month,
                "strike_price_vnd_kwh": strike_price_vnd_kwh,
                "spot_price_vnd_kwh": spot_price_vnd_kwh,
            })

        @app.tool(
            name="mekong_energy_ev",
            description="Simulate EV charging station session, TCVN 13078 / IEC 61851 charger specs, Decision 2699 TOU billing, and CO2 offset.",
        )
        def mekong_energy_ev(
            session_id: str,
            station_id: str,
            charger_type: str = "DC_120kW",
            energy_kwh: float = 45.0,
            tou_period: str = "normal",
            ev_model: str = "VF8",
        ) -> str:
            return handle_energy_ev({
                "session_id": session_id,
                "station_id": station_id,
                "charger_type": charger_type,
                "energy_kwh": energy_kwh,
                "tou_period": tou_period,
                "ev_model": ev_model,
            })

        @app.tool(
            name="mekong_energy_list",
            description="Query registered rooftop solar projects, DPPA bilateral contracts, or EV charging stations.",
        )
        def mekong_energy_list(
            item_type: str = "solar",
            limit: int = 50,
        ) -> str:
            return handle_energy_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_energy_status",
            description="Retrieve Vietnamese renewable energy grid metrics, DPPA settlements, and EV charging network summary.",
        )
        def mekong_energy_status() -> str:
            return handle_energy_status({})

        @app.tool(
            name="mekong_privacy_audit",
            description="Audit enterprise compliance against Decree 13/2023/ND-CP (PDPD), identify gaps, and recommend DPO / DPIA actions.",
        )
        def mekong_privacy_audit(
            enterprise_name: str,
            controller_type: str = "CONTROLLER_AND_PROCESSOR",
            has_sensitive_data: bool = False,
            has_dpo: bool = False,
            has_cross_border: bool = False,
            has_dpia_dossier: bool = True,
        ) -> str:
            return handle_privacy_audit({
                "enterprise_name": enterprise_name,
                "controller_type": controller_type,
                "has_sensitive_data": has_sensitive_data,
                "has_dpo": has_dpo,
                "has_cross_border": has_cross_border,
                "has_dpia_dossier": has_dpia_dossier,
            })

        @app.tool(
            name="mekong_privacy_dpia",
            description="Create Personal Data Processing Impact Assessment (DPIA Form 04) under Article 24 Decree 13/2023/ND-CP for A05 filing.",
        )
        def mekong_privacy_dpia(
            activity_name: str,
            processing_purpose: str,
            data_categories: list[str],
            legal_basis: str = "CONSENT",
            security_measures: str = "AES-256 Encryption, RBAC, TLS 1.3",
        ) -> str:
            return handle_privacy_dpia({
                "activity_name": activity_name,
                "processing_purpose": processing_purpose,
                "data_categories": data_categories,
                "legal_basis": legal_basis,
                "security_measures": security_measures,
            })

        @app.tool(
            name="mekong_privacy_transfer",
            description="Evaluate overseas cross-border data transfer compliance and SCC agreement under Article 25 Decree 13/2023/ND-CP.",
        )
        def mekong_privacy_transfer(
            transfer_name: str,
            recipient_entity: str,
            destination_country: str,
            data_types: list[str],
            record_count: int = 1000,
            has_scc: bool = True,
        ) -> str:
            return handle_privacy_transfer({
                "transfer_name": transfer_name,
                "recipient_entity": recipient_entity,
                "destination_country": destination_country,
                "data_types": data_types,
                "record_count": record_count,
                "has_scc": has_scc,
            })

        @app.tool(
            name="mekong_privacy_breach",
            description="Report personal data breach incident, track mitigation, and enforce 72-hour statutory notification to A05 (Article 26).",
        )
        def mekong_privacy_breach(
            incident_name: str,
            severity: str,
            affected_count: int,
            breach_type: str,
            hours_elapsed: float = 2.0,
            mitigation_plan: str = "Revoked compromised tokens, enabled network isolation, activated incident team",
        ) -> str:
            return handle_privacy_breach({
                "incident_name": incident_name,
                "severity": severity,
                "affected_count": affected_count,
                "breach_type": breach_type,
                "hours_elapsed": hours_elapsed,
                "mitigation_plan": mitigation_plan,
            })

        @app.tool(
            name="mekong_privacy_dsar",
            description="Process Article 9 Data Subject Access Request (access, delete, withdraw consent, restrict processing).",
        )
        def mekong_privacy_dsar(
            request_type: str,
            subject_id: str,
            details: str = "Request under Article 9 PDPD",
        ) -> str:
            return handle_privacy_dsar({
                "request_type": request_type,
                "subject_id": subject_id,
                "details": details,
            })

        @app.tool(
            name="mekong_privacy_list",
            description="Query registered DPIA assessments, cross-border transfers, data breach incidents, or DSAR requests.",
        )
        def mekong_privacy_list(
            item_type: str = "dpia",
            limit: int = 50,
        ) -> str:
            return handle_privacy_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_privacy_status",
            description="Retrieve Vietnamese Personal Data Protection Decree (PDPD Decree 13/2023) compliance metrics and telemetry.",
        )
        def mekong_privacy_status() -> str:
            return handle_privacy_status({})

        @app.tool(
            name="mekong_aviation_flight",
            description="Register commercial flight movement, aircraft specs (MTOW), and apron/gate parking allocation.",
        )
        def mekong_aviation_flight(
            flight_no: str,
            aircraft_type: str,
            origin_airport: str,
            dest_airport: str,
            mtow_tons: float = 90.0,
            parking_hours: float = 2.0,
            is_international: bool = True,
        ) -> str:
            return handle_aviation_flight({
                "flight_no": flight_no,
                "aircraft_type": aircraft_type,
                "origin_airport": origin_airport,
                "dest_airport": dest_airport,
                "mtow_tons": mtow_tons,
                "parking_hours": parking_hours,
                "is_international": is_international,
            })

        @app.tool(
            name="mekong_aviation_cargo",
            description="Calculate IATA volumetric chargeable weight (1 CBM = 166.67 kg) and air freight density rating.",
        )
        def mekong_aviation_cargo(
            mawb_no: str,
            origin_airport: str,
            dest_airport: str,
            piece_count: int,
            gross_weight_kg: float,
            volume_cbm: float,
            cargo_type: str = "GENERAL",
            temperature_regime: str = "AMBIENT",
        ) -> str:
            return handle_aviation_cargo({
                "mawb_no": mawb_no,
                "origin_airport": origin_airport,
                "dest_airport": dest_airport,
                "piece_count": piece_count,
                "gross_weight_kg": gross_weight_kg,
                "volume_cbm": volume_cbm,
                "cargo_type": cargo_type,
                "temperature_regime": temperature_regime,
            })

        @app.tool(
            name="mekong_aviation_tariff",
            description="Calculate statutory landing/takeoff, aircraft parking, security screening, and ramp handling fees (Circular 53/2019).",
        )
        def mekong_aviation_tariff(
            flight_no: str,
            airport_code: str,
            mtow_tons: float,
            parking_hours: float = 2.0,
            cargo_tons: float = 10.0,
            is_international: bool = True,
        ) -> str:
            return handle_aviation_tariff({
                "flight_no": flight_no,
                "airport_code": airport_code,
                "mtow_tons": mtow_tons,
                "parking_hours": parking_hours,
                "cargo_tons": cargo_tons,
                "is_international": is_international,
            })

        @app.tool(
            name="mekong_aviation_dg",
            description="Evaluate Dangerous Goods declaration under IATA DGR and enforce passenger aircraft prohibitions (PAX vs CAO).",
        )
        def mekong_aviation_dg(
            un_number: str,
            proper_shipping_name: str,
            hazard_class: str,
            packing_group: str = "II",
            quantity_kg: float = 10.0,
            aircraft_type: str = "PAX_AND_CARGO",
        ) -> str:
            return handle_aviation_dg({
                "un_number": un_number,
                "proper_shipping_name": proper_shipping_name,
                "hazard_class": hazard_class,
                "packing_group": packing_group,
                "quantity_kg": quantity_kg,
                "aircraft_type": aircraft_type,
            })

        @app.tool(
            name="mekong_aviation_list",
            description="Query registered flight schedules, air cargo shipments, or Dangerous Goods declarations.",
        )
        def mekong_aviation_list(
            item_type: str = "flights",
            limit: int = 50,
        ) -> str:
            return handle_aviation_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_aviation_status",
            description="Retrieve Vietnamese civil aviation network metrics, airport revenue, and air freight telemetry.",
        )
        def mekong_aviation_status() -> str:
            return handle_aviation_status({})

        @app.tool(
            name="mekong_ecom_fct",
            description="Calculate digital services Foreign Contractor Tax (FCT - VAT & CIT) under Decree 126/2020 & Circular 80/2021.",
        )
        def mekong_ecom_fct(
            foreign_supplier_name: str,
            supplier_etax_code: str,
            service_category: str,
            revenue_usd: float = 0.0,
            revenue_vnd: float = 0.0,
            quarter: str = "Q1-2026",
        ) -> str:
            return handle_ecom_fct({
                "foreign_supplier_name": foreign_supplier_name,
                "supplier_etax_code": supplier_etax_code,
                "service_category": service_category,
                "revenue_usd": revenue_usd,
                "revenue_vnd": revenue_vnd,
                "quarter": quarter,
            })

        @app.tool(
            name="mekong_ecom_audit",
            description="Audit e-commerce platform compliance and statutory licensing under Decree 52/2013 & Decree 85/2021.",
        )
        def mekong_ecom_audit(
            platform_name: str,
            domain_url: str,
            platform_type: str = "MARKETPLACE",
            enterprise_tax_id: str = "0109999999",
            has_operating_regulations: bool = True,
            has_dispute_mechanism: bool = True,
            has_seller_kyc: bool = True,
            has_data_retention_3yr: bool = True,
            has_tax_reporting_system: bool = True,
        ) -> str:
            return handle_ecom_audit({
                "platform_name": platform_name,
                "domain_url": domain_url,
                "platform_type": platform_type,
                "enterprise_tax_id": enterprise_tax_id,
                "has_operating_regulations": has_operating_regulations,
                "has_dispute_mechanism": has_dispute_mechanism,
                "has_seller_kyc": has_seller_kyc,
                "has_data_retention_3yr": has_data_retention_3yr,
                "has_tax_reporting_system": has_tax_reporting_system,
            })

        @app.tool(
            name="mekong_ecom_order",
            description="Settle marketplace order finances, compute seller net payout, and generate electronic invoice under Decree 123/2020.",
        )
        def mekong_ecom_order(
            order_code: str,
            platform_id: str,
            seller_id: str,
            buyer_id: str,
            gmv_gross_vnd: float,
            platform_commission_pct: float = 6.0,
            payment_fee_pct: float = 2.5,
            shop_voucher_vnd: float = 0.0,
            platform_voucher_vnd: float = 0.0,
            shipping_fee_vnd: float = 30000.0,
            vat_rate_pct: int = 10,
        ) -> str:
            return handle_ecom_order({
                "order_code": order_code,
                "platform_id": platform_id,
                "seller_id": seller_id,
                "buyer_id": buyer_id,
                "gmv_gross_vnd": gmv_gross_vnd,
                "platform_commission_pct": platform_commission_pct,
                "payment_fee_pct": payment_fee_pct,
                "shop_voucher_vnd": shop_voucher_vnd,
                "platform_voucher_vnd": platform_voucher_vnd,
                "shipping_fee_vnd": shipping_fee_vnd,
                "vat_rate_pct": vat_rate_pct,
            })

        @app.tool(
            name="mekong_ecom_parcel",
            description="Evaluate cross-border express parcel customs duty & VAT exemption threshold under statutory de minimis rules.",
        )
        def mekong_ecom_parcel(
            tracking_no: str,
            shipper_country: str,
            consignee_name: str,
            item_description: str,
            customs_value_usd: float = 0.0,
            customs_value_vnd: float = 0.0,
            import_duty_pct: float = 10.0,
        ) -> str:
            return handle_ecom_parcel({
                "tracking_no": tracking_no,
                "shipper_country": shipper_country,
                "consignee_name": consignee_name,
                "item_description": item_description,
                "customs_value_usd": customs_value_usd,
                "customs_value_vnd": customs_value_vnd,
                "import_duty_pct": import_duty_pct,
            })

        @app.tool(
            name="mekong_ecom_list",
            description="Query registered e-commerce platforms, FCT tax declarations, marketplace orders, or cross-border parcels.",
        )
        def mekong_ecom_list(
            item_type: str = "platforms",
            limit: int = 50,
        ) -> str:
            return handle_ecom_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_ecom_status",
            description="Retrieve Vietnamese e-commerce compliance telemetry, digital tax metrics, and order settlement statistics.",
        )
        def mekong_ecom_status() -> str:
            return handle_ecom_status({})

        @app.tool(
            name="mekong_telecom_spectrum",
            description="Calculate spectrum auction reserve valuation, deposit, and network rollout obligations under Decree 63/2023/ND-CP.",
        )
        def mekong_telecom_spectrum(
            band_code: str,
            license_years: int = 15,
            deposit_pct: float = 10.0,
            custom_reserve_price_vnd: float = 0.0,
        ) -> str:
            return handle_telecom_spectrum({
                "band_code": band_code,
                "license_years": license_years,
                "deposit_pct": deposit_pct,
                "custom_reserve_price_vnd": custom_reserve_price_vnd,
            })

        @app.tool(
            name="mekong_telecom_ott",
            description="Audit OTT messaging, VoIP & digital communication service compliance under Telecommunications Law 2023.",
        )
        def mekong_telecom_ott(
            service_name: str,
            provider_name: str,
            service_category: str = "OTT_MESSAGING_VOICE",
            registered_users: int = 1000000,
            has_kyc_verification: bool = True,
            has_encryption_e2ee: bool = True,
            has_local_data_storage: bool = True,
            has_vnta_notification: bool = True,
            has_consumer_dispute_system: bool = True,
        ) -> str:
            return handle_telecom_ott({
                "service_name": service_name,
                "provider_name": provider_name,
                "service_category": service_category,
                "registered_users": registered_users,
                "has_kyc_verification": has_kyc_verification,
                "has_encryption_e2ee": has_encryption_e2ee,
                "has_local_data_storage": has_local_data_storage,
                "has_vnta_notification": has_vnta_notification,
                "has_consumer_dispute_system": has_consumer_dispute_system,
            })

        @app.tool(
            name="mekong_telecom_bts",
            description="Evaluate base transceiver station (BTS) electromagnetic field (EMF) exposure safety against QCVN 08:2020/BTTTT.",
        )
        def mekong_telecom_bts(
            station_id: str,
            location: str,
            antenna_height_m: float = 30.0,
            transmit_power_watts: float = 80.0,
            frequency_mhz: float = 2600.0,
            antenna_gain_dbi: float = 18.0,
            distance_residential_m: float = 25.0,
        ) -> str:
            return handle_telecom_bts({
                "station_id": station_id,
                "location": location,
                "antenna_height_m": antenna_height_m,
                "transmit_power_watts": transmit_power_watts,
                "frequency_mhz": frequency_mhz,
                "antenna_gain_dbi": antenna_gain_dbi,
                "distance_residential_m": distance_residential_m,
            })

        @app.tool(
            name="mekong_telecom_number",
            description="Allocate national telecom numbering resources (1900, 1800, Mobile) and compute maintenance fees under Circular 25/2015.",
        )
        def mekong_telecom_number(
            number_prefix: str,
            assigned_operator: str,
            block_size: int = 10000,
            service_purpose: str = "MOBILE_SUBSCRIBER",
        ) -> str:
            return handle_telecom_number({
                "number_prefix": number_prefix,
                "assigned_operator": assigned_operator,
                "block_size": block_size,
                "service_purpose": service_purpose,
            })

        @app.tool(
            name="mekong_telecom_list",
            description="Query registered spectrum auctions, OTT compliance audits, BTS safety evals, or numbering resources.",
        )
        def mekong_telecom_list(
            item_type: str = "spectrum",
            limit: int = 50,
        ) -> str:
            return handle_telecom_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_telecom_status",
            description="Retrieve Vietnamese telecommunications telemetry, spectrum auctions, and OTT compliance status.",
        )
        def mekong_telecom_status() -> str:
            return handle_telecom_status({})

        @app.tool(
            name="mekong_pharma_drug",
            description="Register or verify drug marketing authorization (Visa MA) under Drug Law 2016.",
        )
        def mekong_pharma_drug(
            visa_number: str,
            drug_name: str,
            active_ingredient: str,
            strength: str,
            dosage_form: str,
            classification: str = "RX_PRESCRIPTION",
            manufacturer_name: str = "DHG Pharma",
            country_of_origin: str = "Vietnam",
            tenure_years: int = 5,
        ) -> str:
            return handle_pharma_drug({
                "visa_number": visa_number,
                "drug_name": drug_name,
                "active_ingredient": active_ingredient,
                "strength": strength,
                "dosage_form": dosage_form,
                "classification": classification,
                "manufacturer_name": manufacturer_name,
                "country_of_origin": country_of_origin,
                "tenure_years": tenure_years,
            })

        @app.tool(
            name="mekong_pharma_gsp",
            description="Audit warehouse environmental storage conditions and cold chain against GSP standards (Circular 36/2018).",
        )
        def mekong_pharma_gsp(
            warehouse_id: str,
            warehouse_name: str,
            storage_condition: str = "COLD_CHAIN",
            recorded_temp_c: float = 4.5,
            recorded_humidity_pct: float = 55.0,
            sensor_id: str = "SENSOR-TMP-01",
        ) -> str:
            return handle_pharma_gsp({
                "warehouse_id": warehouse_id,
                "warehouse_name": warehouse_name,
                "storage_condition": storage_condition,
                "recorded_temp_c": recorded_temp_c,
                "recorded_humidity_pct": recorded_humidity_pct,
                "sensor_id": sensor_id,
            })

        @app.tool(
            name="mekong_pharma_batch",
            description="Track drug batch with GS1 DataMatrix identifiers and manage national recall alerts under Decision 412/QD-BYT.",
        )
        def mekong_pharma_batch(
            batch_number: str,
            visa_number: str,
            drug_name: str,
            gtin_14: str = "08935000000018",
            serial_number: str = "SN1234567890",
            manufacturing_date: str = "2026-01-15",
            expiry_date: str = "2028-01-15",
            quantity_units: int = 10000,
            recall_action: str = "NONE",
        ) -> str:
            return handle_pharma_batch({
                "batch_number": batch_number,
                "visa_number": visa_number,
                "drug_name": drug_name,
                "gtin_14": gtin_14,
                "serial_number": serial_number,
                "manufacturing_date": manufacturing_date,
                "expiry_date": expiry_date,
                "quantity_units": quantity_units,
                "recall_action": recall_action,
            })

        @app.tool(
            name="mekong_pharma_price",
            description="Verify statutory drug wholesale and hospital retail margin limits under Decree 54/2017/ND-CP.",
        )
        def mekong_pharma_price(
            visa_number: str,
            drug_name: str,
            wholesale_price_vnd: float,
            hospital_retail_price_vnd: float,
            declared_by: str = "DHG Pharma",
            classification: str = "RX_PRESCRIPTION",
        ) -> str:
            return handle_pharma_price({
                "visa_number": visa_number,
                "drug_name": drug_name,
                "wholesale_price_vnd": wholesale_price_vnd,
                "hospital_retail_price_vnd": hospital_retail_price_vnd,
                "declared_by": declared_by,
                "classification": classification,
            })

        @app.tool(
            name="mekong_pharma_list",
            description="Query registered drug marketing authorizations, GSP logs, batch traceability, or price declarations.",
        )
        def mekong_pharma_list(
            item_type: str = "drugs",
            limit: int = 50,
        ) -> str:
            return handle_pharma_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_pharma_status",
            description="Retrieve Vietnamese pharmaceutical regulatory, GSP cold chain, and batch traceability telemetry.",
        )
        def mekong_pharma_status() -> str:
            return handle_pharma_status({})

        @app.tool(
            name="mekong_petrol_price",
            description="Calculate statutory petroleum base price and retail ceilings under Decree 80/2023/ND-CP.",
        )
        def mekong_petrol_price(
            product_code: str = "RON95_III",
            mops_platts_usd_per_barrel: float = 92.50,
            import_duty_pct: float = 10.0,
            bog_fund_deduction_vnd: float = 0.0,
            bog_fund_expenditure_vnd: float = 0.0,
            cycle_date: typing.Optional[str] = None,
        ) -> str:
            return handle_petrol_price({
                "product_code": product_code,
                "mops_platts_usd_per_barrel": mops_platts_usd_per_barrel,
                "import_duty_pct": import_duty_pct,
                "bog_fund_deduction_vnd": bog_fund_deduction_vnd,
                "bog_fund_expenditure_vnd": bog_fund_expenditure_vnd,
                "cycle_date": cycle_date,
            })

        @app.tool(
            name="mekong_petrol_reserve",
            description="Audit statutory mandatory fuel reserves against Decree 83/2014 & Decision 242/QD-TTg thresholds.",
        )
        def mekong_petrol_reserve(
            enterprise_name: str,
            enterprise_type: str = "KEY_IMPORTER",
            storage_capacity_m3: float = 100000.0,
            current_stock_m3: float = 75000.0,
            daily_consumption_m3: float = 3000.0,
        ) -> str:
            return handle_petrol_reserve({
                "enterprise_name": enterprise_name,
                "enterprise_type": enterprise_type,
                "storage_capacity_m3": storage_capacity_m3,
                "current_stock_m3": current_stock_m3,
                "daily_consumption_m3": daily_consumption_m3,
            })

        @app.tool(
            name="mekong_petrol_quality",
            description="Inspect petroleum quality and Euro 4/5 emission tier compliance under QCVN 01:2015/BKHCN.",
        )
        def mekong_petrol_quality(
            gas_station_id: str,
            gas_station_name: str,
            product_code: str = "RON95_III",
            sulfur_content_ppm: float = 35.0,
            lead_content_g_l: float = 0.0,
        ) -> str:
            return handle_petrol_quality({
                "gas_station_id": gas_station_id,
                "gas_station_name": gas_station_name,
                "product_code": product_code,
                "sulfur_content_ppm": sulfur_content_ppm,
                "lead_content_g_l": lead_content_g_l,
            })

        @app.tool(
            name="mekong_petrol_pump",
            description="Monitor dispenser pump e-invoice issuance telemetry under Official Telegram 1284/CD-TTg.",
        )
        def mekong_petrol_pump(
            station_id: str,
            pump_count: int = 8,
            daily_transactions: int = 1500,
            daily_volume_liters: float = 12000.0,
            daily_revenue_vnd: float = 285000000.0,
            e_invoices_issued: int = 1500,
        ) -> str:
            return handle_petrol_pump({
                "station_id": station_id,
                "pump_count": pump_count,
                "daily_transactions": daily_transactions,
                "daily_volume_liters": daily_volume_liters,
                "daily_revenue_vnd": daily_revenue_vnd,
                "e_invoices_issued": e_invoices_issued,
            })

        @app.tool(
            name="mekong_petrol_list",
            description="Query petroleum price adjustments, national reserves, quality inspections, or pump telemetry.",
        )
        def mekong_petrol_list(
            item_type: str = "prices",
            limit: int = 50,
        ) -> str:
            return handle_petrol_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_petrol_status",
            description="Retrieve Vietnamese petroleum regulatory, price adjustments, national reserves, and e-invoice telemetry.",
        )
        def mekong_petrol_status() -> str:
            return handle_petrol_status({})

        @app.tool(
            name="mekong_fishery_vessel",
            description="Register fishing vessel into VNFishbase and audit statutory VMS mandate under Decree 26/2019/ND-CP.",
        )
        def mekong_fishery_vessel(
            vessel_plate: str,
            owner_name: str,
            home_port: str = "PORT_TAC_CAU",
            length_meters: float = 18.5,
            engine_power_hp: float = 450.0,
            vms_device_id: typing.Optional[str] = None,
            assigned_zone: str = "SOUTHWEST_GULF",
            license_valid_years: int = 5,
        ) -> str:
            return handle_fishery_vessel({
                "vessel_plate": vessel_plate,
                "owner_name": owner_name,
                "home_port": home_port,
                "length_meters": length_meters,
                "engine_power_hp": engine_power_hp,
                "vms_device_id": vms_device_id,
                "assigned_zone": assigned_zone,
                "license_valid_years": license_valid_years,
            })

        @app.tool(
            name="mekong_fishery_vms",
            description="Track vessel GPS telemetry, detect EEZ maritime border violations, and assess EC IUU Yellow Card risk.",
        )
        def mekong_fishery_vms(
            vessel_plate: str,
            latitude: float,
            longitude: float,
            speed_knots: float = 8.5,
            heading_degrees: float = 135.0,
            is_signal_active: bool = True,
            disconnection_hours: float = 0.0,
            assigned_zone: str = "SOUTHWEST_GULF",
        ) -> str:
            return handle_fishery_vms({
                "vessel_plate": vessel_plate,
                "latitude": latitude,
                "longitude": longitude,
                "speed_knots": speed_knots,
                "heading_degrees": heading_degrees,
                "is_signal_active": is_signal_active,
                "disconnection_hours": disconnection_hours,
                "assigned_zone": assigned_zone,
            })

        @app.tool(
            name="mekong_fishery_cert",
            description="Issue electronic Catch Certificate (CC) or Statement of Catch (SC) under eCDT VN system.",
        )
        def mekong_fishery_cert(
            vessel_plate: str,
            species_code: str = "YELLOWFIN_TUNA",
            catch_volume_kg: float = 12500.0,
            landing_port: str = "PORT_QUY_NHON",
            destination_market: str = "EU_MARKET",
            certificate_type: str = "CATCH_CERTIFICATE_CC",
        ) -> str:
            return handle_fishery_cert({
                "vessel_plate": vessel_plate,
                "species_code": species_code,
                "catch_volume_kg": catch_volume_kg,
                "landing_port": landing_port,
                "destination_market": destination_market,
                "certificate_type": certificate_type,
            })

        @app.tool(
            name="mekong_fishery_quality",
            description="Audit seafood factory HACCP compliance and banned antibiotic residue limits under Circular 48/2013.",
        )
        def mekong_fishery_quality(
            facility_eu_code: str,
            facility_name: str,
            lot_number: str,
            species_code: str = "WHITELEG_SHRIMP",
            haccp_score: float = 95.0,
            chloramphenicol_ppb: float = 0.0,
            nitrofurans_ppb: float = 0.0,
            heavy_metal_pass: bool = True,
        ) -> str:
            return handle_fishery_quality({
                "facility_eu_code": facility_eu_code,
                "facility_name": facility_name,
                "lot_number": lot_number,
                "species_code": species_code,
                "haccp_score": haccp_score,
                "chloramphenicol_ppb": chloramphenicol_ppb,
                "nitrofurans_ppb": nitrofurans_ppb,
                "heavy_metal_pass": heavy_metal_pass,
            })

        @app.tool(
            name="mekong_fishery_list",
            description="Query registered fishing vessels, VMS logs, eCDT catch certificates, or seafood quality audits.",
        )
        def mekong_fishery_list(
            item_type: str = "vessels",
            limit: int = 50,
        ) -> str:
            return handle_fishery_list({
                "item_type": item_type,
                "limit": limit,
            })

        @app.tool(
            name="mekong_fishery_status",
            description="Retrieve Vietnamese fisheries, VMS fleet tracking, eCDT catch certs, and EC IUU Yellow Card telemetry.",
        )
        def mekong_fishery_status() -> str:
            return handle_fishery_status({})

        @app.tool(
            name="mekong_construction_project",
            description="Register construction project and evaluate statutory building grade under Decree 06/2021/ND-CP.",
        )
        def mekong_construction_project(
            project_name: str,
            project_type: str = "CIVIL_COMMERCIAL",
            total_investment_vnd: float = 250000000000.0,
            gross_floor_area_m2: float = 35000.0,
            height_meters: float = 85.0,
            floors_count: int = 26,
            location_province: str = "TP. Hồ Chí Minh",
        ) -> str:
            return handle_construction_project({
                "project_name": project_name,
                "project_type": project_type,
                "total_investment_vnd": total_investment_vnd,
                "gross_floor_area_m2": gross_floor_area_m2,
                "height_meters": height_meters,
                "floors_count": floors_count,
                "location_province": location_province,
            })

        @app.tool(
            name="mekong_construction_permit",
            description="Evaluate building permit eligibility and statutory exemptions under Article 89 Law on Construction 2020.",
        )
        def mekong_construction_permit(
            project_id: str,
            is_secret_defense_project: bool = False,
            is_rural_detached_house: bool = False,
            is_industrial_park_approved_1_500: bool = False,
            is_fire_safety_approved: bool = True,
        ) -> str:
            return handle_construction_permit({
                "project_id": project_id,
                "is_secret_defense_project": is_secret_defense_project,
                "is_rural_detached_house": is_rural_detached_house,
                "is_industrial_park_approved_1_500": is_industrial_park_approved_1_500,
                "is_fire_safety_approved": is_fire_safety_approved,
            })

        @app.tool(
            name="mekong_construction_fidic",
            description="Structure FIDIC construction contract (Red/Yellow/Silver Book) with advance payment, performance bond and retention terms.",
        )
        def mekong_construction_fidic(
            project_id: str,
            contract_name: str,
            fidic_type: str = "FIDIC_YELLOW_BOOK",
            employer_name: str = "Vinhomes Joint Stock Company",
            contractor_name: str = "Coteccons Construction Corporation",
            contract_value_vnd: float = 180000000000.0,
            custom_advance_pct: float | None = None,
        ) -> str:
            return handle_construction_fidic({
                "project_id": project_id,
                "contract_name": contract_name,
                "fidic_type": fidic_type,
                "employer_name": employer_name,
                "contractor_name": contractor_name,
                "contract_value_vnd": contract_value_vnd,
                "custom_advance_pct": custom_advance_pct,
            })

        @app.tool(
            name="mekong_construction_pccc",
            description="Audit building fire safety rating, REI resistance and evacuation distances under QCVN 06:2022/BXD.",
        )
        def mekong_construction_pccc(
            project_id: str,
            fire_tier: str = "TIER_I",
            tested_column_rei_min: int = 150,
            tested_floor_rei_min: int = 90,
            measured_evacuation_dist_m: float = 32.5,
        ) -> str:
            return handle_construction_pccc({
                "project_id": project_id,
                "fire_tier": fire_tier,
                "tested_column_rei_min": tested_column_rei_min,
                "tested_floor_rei_min": tested_floor_rei_min,
                "measured_evacuation_dist_m": measured_evacuation_dist_m,
            })

        @app.tool(
            name="mekong_construction_accept",
            description="Perform construction quality acceptance inspection for commissioning under Decree 06/2021/ND-CP.",
        )
        def mekong_construction_accept(
            project_id: str,
            acceptance_stage: str = "FINAL_COMMISSIONING",
            inspector_name: str = "Tư vấn Giám sát Apave Vietnam",
            structural_soundness_pct: float = 98.5,
            as_built_compliance: bool = True,
        ) -> str:
            return handle_construction_accept({
                "project_id": project_id,
                "acceptance_stage": acceptance_stage,
                "inspector_name": inspector_name,
                "structural_soundness_pct": structural_soundness_pct,
                "as_built_compliance": as_built_compliance,
            })

        @app.tool(
            name="mekong_construction_list",
            description="Query registered projects, building permits, FIDIC contracts, PCCC audits, or quality acceptances.",
        )
        def mekong_construction_list(
            category: str = "projects",
            limit: int = 50,
        ) -> str:
            return handle_construction_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_construction_status",
            description="Retrieve Vietnamese construction engineering, FIDIC contracts, and building permits telemetry.",
        )
        def mekong_construction_status() -> str:
            return handle_construction_status({})

        @app.tool(
            name="mekong_mining_license",
            description="Register mineral mining concession and determine statutory licensing authority under Mineral Law 2010.",
        )
        def mekong_mining_license(
            mine_name: str,
            mineral_type: str = "RARE_EARTH",
            enterprise_name: str = "Vietnam Rare Earth Joint Stock Company",
            approved_reserve: float = 2500000.0,
            annual_capacity: float = 120000.0,
            mining_method: str = "OPEN_PIT",
            mine_area_hectares: float = 85.5,
            location_province: str = "Lai Châu",
            duration_years: int = 25,
        ) -> str:
            return handle_mining_license({
                "mine_name": mine_name,
                "mineral_type": mineral_type,
                "enterprise_name": enterprise_name,
                "approved_reserve": approved_reserve,
                "annual_capacity": annual_capacity,
                "mining_method": mining_method,
                "mine_area_hectares": mine_area_hectares,
                "location_province": location_province,
                "duration_years": duration_years,
            })

        @app.tool(
            name="mekong_mining_rights_fee",
            description="Calculate statutory concession mineral rights fee T = Q * G * K * R under Decree 67/2019/ND-CP.",
        )
        def mekong_mining_rights_fee(
            license_id: str,
            reserve_volume: float | None = None,
            custom_unit_price_vnd: float | None = None,
            mining_method: str = "OPEN_PIT",
            mineral_type: str = "RARE_EARTH",
            payment_years: int = 10,
        ) -> str:
            return handle_mining_rights_fee({
                "license_id": license_id,
                "reserve_volume": reserve_volume,
                "custom_unit_price_vnd": custom_unit_price_vnd,
                "mining_method": mining_method,
                "mineral_type": mineral_type,
                "payment_years": payment_years,
            })

        @app.tool(
            name="mekong_mining_royalty",
            description="Compute natural resources royalty tax declaration under Law on Natural Resources Tax 2009.",
        )
        def mekong_mining_royalty(
            license_id: str,
            tax_period: str = "2026-Q1",
            actual_mined_volume: float = 30000.0,
            mineral_type: str = "RARE_EARTH",
            taxable_unit_price_vnd: float | None = None,
        ) -> str:
            return handle_mining_royalty({
                "license_id": license_id,
                "tax_period": tax_period,
                "actual_mined_volume": actual_mined_volume,
                "mineral_type": mineral_type,
                "taxable_unit_price_vnd": taxable_unit_price_vnd,
            })

        @app.tool(
            name="mekong_mining_rehab",
            description="Audit environmental rehabilitation escrow deposit and wastewater effluent against QCVN 40:2011/BTNMT.",
        )
        def mekong_mining_rehab(
            license_id: str,
            total_rehab_estimate_vnd: float = 12000000000.0,
            initial_deposit_pct: float = 25.0,
            replanted_trees_count: int = 15000,
            wastewater_ph: float = 7.2,
            wastewater_tss_mg_l: float = 38.0,
        ) -> str:
            return handle_mining_rehab({
                "license_id": license_id,
                "total_rehab_estimate_vnd": total_rehab_estimate_vnd,
                "initial_deposit_pct": initial_deposit_pct,
                "replanted_trees_count": replanted_trees_count,
                "wastewater_ph": wastewater_ph,
                "wastewater_tss_mg_l": wastewater_tss_mg_l,
            })

        @app.tool(
            name="mekong_mining_sand",
            description="Inspect river sand & gravel dredging vessel compliance against Decree 23/2020/ND-CP.",
        )
        def mekong_mining_sand(
            license_id: str,
            vessel_plate: str,
            operation_time_hh_mm: str = "10:30",
            is_gps_installed: bool = True,
            is_dock_camera_installed: bool = True,
            measured_cargo_m3: float = 240.0,
        ) -> str:
            return handle_mining_sand({
                "license_id": license_id,
                "vessel_plate": vessel_plate,
                "operation_time_hh_mm": operation_time_hh_mm,
                "is_gps_installed": is_gps_installed,
                "is_dock_camera_installed": is_dock_camera_installed,
                "measured_cargo_m3": measured_cargo_m3,
            })

        @app.tool(
            name="mekong_mining_list",
            description="Query registered mining licenses, rights fees, royalty taxes, environmental rehabs, or sand inspections.",
        )
        def mekong_mining_list(
            category: str = "licenses",
            limit: int = 50,
        ) -> str:
            return handle_mining_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_mining_status",
            description="Retrieve Vietnamese mining regulatory, mineral rights fees, royalties, and environmental telemetry.",
        )
        def mekong_mining_status() -> str:
            return handle_mining_status({})

        @app.tool(
            name="mekong_forestry_plot",
            description="Register forest plot with canopy coverage, species, and FSC/PEFC certification under Law on Forestry 2017.",
        )
        def mekong_forestry_plot(
            plot_name: str,
            forest_type: str = "PRODUCTION_PLANTATION",
            province: str = "Quảng Nam",
            area_hectares: float = 150.0,
            canopy_cover_pct: float = 65.0,
            trees_per_hectare: float = 1600.0,
            main_species: str = "Acacia auriculiformis (Keo lá tràm)",
            is_fsc_certified: bool = True,
            fsc_code: str | None = "FSC-C123456",
        ) -> str:
            return handle_forestry_plot({
                "plot_name": plot_name,
                "forest_type": forest_type,
                "province": province,
                "area_hectares": area_hectares,
                "canopy_cover_pct": canopy_cover_pct,
                "trees_per_hectare": trees_per_hectare,
                "main_species": main_species,
                "is_fsc_certified": is_fsc_certified,
                "fsc_code": fsc_code,
            })

        @app.tool(
            name="mekong_forestry_timber",
            description="Verify timber consignment legality under VNTLAS (Decree 102/2020) and issue export manifest.",
        )
        def mekong_forestry_timber(
            enterprise_name: str,
            product_type: str = "FURNITURE",
            volume_m3: float = 120.0,
            species: str = "Tectona grandis (Gỗ Teak) / Keo tràm",
            origin_province: str = "Bình Dương",
            enterprise_tier: str = "TIER_1",
            flegt_cites_license: str | None = "FLEGT-VN-2026-00892",
            export_market: str = "EU",
        ) -> str:
            return handle_forestry_timber({
                "enterprise_name": enterprise_name,
                "product_type": product_type,
                "volume_m3": volume_m3,
                "species": species,
                "origin_province": origin_province,
                "enterprise_tier": enterprise_tier,
                "flegt_cites_license": flegt_cites_license,
                "export_market": export_market,
            })

        @app.tool(
            name="mekong_forestry_afforestation",
            description="Calculate mandatory alternative afforestation area or Vietnam Forest Protection Fund (VNFF) deposit under Article 21.",
        )
        def mekong_forestry_afforestation(
            project_name: str,
            converted_forest_type: str = "PRODUCTION_NATURAL",
            converted_area_ha: float = 25.0,
            payment_rate_vnd_per_ha: float = 95000000.0,
        ) -> str:
            return handle_forestry_afforestation({
                "project_name": project_name,
                "converted_forest_type": converted_forest_type,
                "converted_area_ha": converted_area_ha,
                "payment_rate_vnd_per_ha": payment_rate_vnd_per_ha,
            })

        @app.tool(
            name="mekong_forestry_pfes",
            description="Compute PFES obligation (Decree 156/2018) and World Bank ERPA forest carbon sequestration revenue.",
        )
        def mekong_forestry_pfes(
            facility_name: str,
            facility_type: str = "HYDROPOWER",
            production_volume: float = 250000000.0,
            forest_area_ha: float = 12000.0,
            carbon_sequestration_rate: float = 4.2,
            erpa_price_usd_per_ton: float = 5.0,
        ) -> str:
            return handle_forestry_pfes({
                "facility_name": facility_name,
                "facility_type": facility_type,
                "production_volume": production_volume,
                "forest_area_ha": forest_area_ha,
                "carbon_sequestration_rate": carbon_sequestration_rate,
                "erpa_price_usd_per_ton": erpa_price_usd_per_ton,
            })

        @app.tool(
            name="mekong_forestry_fire",
            description="Assess forest fire danger level (Tier I to V) based on meteorological index under Decree 156/2018.",
        )
        def mekong_forestry_fire(
            plot_id: str,
            temperature_c: float = 37.5,
            humidity_pct: float = 38.0,
            wind_speed_kmh: float = 24.0,
            consecutive_dry_days: int = 14,
        ) -> str:
            return handle_forestry_fire({
                "plot_id": plot_id,
                "temperature_c": temperature_c,
                "humidity_pct": humidity_pct,
                "wind_speed_kmh": wind_speed_kmh,
                "consecutive_dry_days": consecutive_dry_days,
            })

        @app.tool(
            name="mekong_forestry_list",
            description="Query registered forest plots, timber consignments, alternative afforestations, PFES records, or fire danger assessments.",
        )
        def mekong_forestry_list(
            category: str = "plots",
            limit: int = 50,
        ) -> str:
            return handle_forestry_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_forestry_status",
            description="Retrieve Vietnamese forestry, VNTLAS timber, PFES, and forest carbon telemetry.",
        )
        def mekong_forestry_status() -> str:
            return handle_forestry_status({})

        @app.tool(
            name="mekong_water_plant",
            description="Register clean water treatment plant with capacity, source, and operator.",
        )
        def mekong_water_plant(
            name: str,
            capacity: float = 50000.0,
            source: str = "Sông Đồng Nai (Nguồn nước mặt)",
            province: str = "Bình Dương",
            technology: str = "Lắng lamen + Lọc cát + Khử trùng Clo",
            operator: str = "BIWASE",
        ) -> str:
            return handle_water_plant({
                "name": name,
                "capacity": capacity,
                "source": source,
                "province": province,
                "technology": technology,
                "operator": operator,
            })

        @app.tool(
            name="mekong_water_test",
            description="Audit drinking water quality against QCVN 01-1:2018/BYT statutory standards.",
        )
        def mekong_water_test(
            plant_id: str,
            location: str = "Bể chứa nước sạch trạm bơm cấp 2",
            ph: float = 7.2,
            turbidity: float = 0.85,
            chlorine: float = 0.5,
            coliform: float = 0.0,
            ecoli: float = 0.0,
            metal_pass: bool = True,
            tester: str = "Trung tâm Kiểm soát Bệnh tật (CDC)",
        ) -> str:
            return handle_water_test({
                "plant_id": plant_id,
                "location": location,
                "ph": ph,
                "turbidity": turbidity,
                "chlorine": chlorine,
                "coliform": coliform,
                "ecoli": ecoli,
                "metal_pass": metal_pass,
                "tester": tester,
            })

        @app.tool(
            name="mekong_water_bill",
            description="Calculate statutory progressive water consumption bill, wastewater fee & VAT (Circular 44/2021/TT-BTC).",
        )
        def mekong_water_bill(
            code: str,
            name: str,
            volume: float,
            category: str = "DOMESTIC",
            month: str | None = None,
        ) -> str:
            return handle_water_bill({
                "code": code,
                "name": name,
                "volume": volume,
                "category": category,
                "month": month,
            })

        @app.tool(
            name="mekong_water_nrw",
            description="Audit non-revenue water (NRW) leakage rate under Decision 2147/QĐ-TTg (target <= 15%).",
        )
        def mekong_water_nrw(
            plant_id: str,
            produced: float,
            billed: float,
            period: str = "2026-Q1",
            target: float = 15.0,
            notes: str | None = None,
        ) -> str:
            return handle_water_nrw({
                "plant_id": plant_id,
                "produced": produced,
                "billed": billed,
                "period": period,
                "target": target,
                "notes": notes,
            })

        @app.tool(
            name="mekong_water_discharge",
            description="Inspect industrial wastewater discharge against QCVN 40:2011/BTNMT (Column A & B limits).",
        )
        def mekong_water_discharge(
            facility: str,
            park: str = "KCN VSIP II - Bình Dương",
            flow: float = 1200.0,
            column: str = "COLUMN_A",
            bod5: float = 24.5,
            cod: float = 62.0,
            tss: float = 38.0,
            nh4: float = 3.5,
            ph: float = 7.4,
        ) -> str:
            return handle_water_discharge({
                "facility": facility,
                "park": park,
                "flow": flow,
                "column": column,
                "bod5": bod5,
                "cod": cod,
                "tss": tss,
                "nh4": nh4,
                "ph": ph,
            })

        @app.tool(
            name="mekong_water_list",
            description="Query registered water plants, quality tests, tariff bills, NRW audits, or wastewater inspections.",
        )
        def mekong_water_list(
            category: str = "plants",
            limit: int = 50,
        ) -> str:
            return handle_water_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_water_status",
            description="Retrieve Vietnamese clean water utilities, drainage, and wastewater treatment telemetry.",
        )
        def mekong_water_status() -> str:
            return handle_water_status({})

        @app.tool(
            name="mekong_medtech_device",
            description="Classify medical device risk class (A/B/C/D) and register market authorization under Decree 98/2021 & 07/2023.",
        )
        def mekong_medtech_device(
            name: str,
            risk_class: str = "CLASS_B",
            maker: str = "MedTech Global Instruments Inc.",
            origin: str = "Germany",
            importer: str = "Công ty TNHH Thiết Bị Y Tế Sài Gòn",
            use: str = "Theo dõi huyết áp và chỉ số sinh tồn điện tử",
            cfs: str | None = "CE",
        ) -> str:
            return handle_medtech_device({
                "name": name,
                "risk_class": risk_class,
                "maker": maker,
                "origin": origin,
                "importer": importer,
                "use": use,
                "cfs": cfs,
            })

        @app.tool(
            name="mekong_medtech_price",
            description="Declare medical device wholesale and retail prices and verify markup cap (<= 35%) under Decree 07/2023.",
        )
        def mekong_medtech_price(
            device_id: str,
            name: str,
            cif: float,
            wholesale: float,
            retail: float,
        ) -> str:
            return handle_medtech_price({
                "device_id": device_id,
                "name": name,
                "cif": cif,
                "wholesale": wholesale,
                "retail": retail,
            })

        @app.tool(
            name="mekong_medtech_facility",
            description="Evaluate healthcare facility operating license conditions under Law on Medical Examination 2023.",
        )
        def mekong_medtech_facility(
            name: str,
            fac_type: str = "GENERAL_HOSPITAL",
            province: str = "Hà Nội",
            beds: int = 100,
            area: float = 6000.0,
            cmo: str = "PGS.TS. Trần Quốc Tuấn",
            months: int = 60,
        ) -> str:
            return handle_medtech_facility({
                "name": name,
                "fac_type": fac_type,
                "province": province,
                "beds": beds,
                "area": area,
                "cmo": cmo,
                "months": months,
            })

        @app.tool(
            name="mekong_medtech_trial",
            description="Register medical device clinical evaluation trial protocol and ethics approval under Circular 29/2023/TT-BYT.",
        )
        def mekong_medtech_trial(
            device_id: str,
            title: str,
            phase: int = 2,
            pi: str = "GS.TS. Phạm Nhật An",
            site: str = "Bệnh viện Đại học Y Dược TP.HCM",
            subjects: int = 120,
            irb: bool = True,
        ) -> str:
            return handle_medtech_trial({
                "device_id": device_id,
                "title": title,
                "phase": phase,
                "pi": pi,
                "site": site,
                "subjects": subjects,
                "irb": irb,
            })

        @app.tool(
            name="mekong_medtech_list",
            description="Query registered medical devices, price declarations, healthcare facilities, or clinical trials.",
        )
        def mekong_medtech_list(
            category: str = "devices",
            limit: int = 50,
        ) -> str:
            return handle_medtech_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_medtech_status",
            description="Retrieve Vietnamese medical devices, healthcare facility licensing, and clinical evaluation telemetry.",
        )
        def mekong_medtech_status() -> str:
            return handle_medtech_status({})

        @app.tool(
            name="mekong_livestock_farm",
            description="Register livestock farm, compute statutory Livestock Units (ĐVN), scale, and regional density.",
        )
        def mekong_livestock_farm(
            farm_name: str,
            owner_name: str = "Tập Đoàn Chăn Nuôi CP Việt Nam",
            province: str = "Đồng Nai",
            animal_type: str = "PIG_FATTENER",
            head_count: int = 2000,
            agricultural_land_ha: float = 30.0,
            region: str = "SOUTHEAST",
        ) -> str:
            return handle_livestock_farm({
                "farm_name": farm_name,
                "owner_name": owner_name,
                "province": province,
                "animal_type": animal_type,
                "head_count": head_count,
                "agricultural_land_ha": agricultural_land_ha,
                "region": region,
            })

        @app.tool(
            name="mekong_livestock_distance",
            description="Audit farm biosecurity buffer distances against residential areas, water sources, and other farms under Article 5 Decree 13/2020/NĐ-CP.",
        )
        def mekong_livestock_distance(
            farm_id: str,
            farm_scale: str = "LARGE_SCALE",
            residential_distance_m: float = 450.0,
            water_source_distance_m: float = 120.0,
            farm_to_farm_distance_m: float = 1200.0,
        ) -> str:
            return handle_livestock_distance({
                "farm_id": farm_id,
                "farm_scale": farm_scale,
                "residential_distance_m": residential_distance_m,
                "water_source_distance_m": water_source_distance_m,
                "farm_to_farm_distance_m": farm_to_farm_distance_m,
            })

        @app.tool(
            name="mekong_livestock_feed",
            description="Inspect animal feed quality, mycotoxins (Aflatoxin B1), heavy metals, and prohibited beta-agonists under QCVN 01-183.",
        )
        def mekong_livestock_feed(
            product_name: str,
            feed_type: str = "PIG_FEED_COMPLETE",
            manufacturer: str = "C.P. Vietnam Corporation",
            crude_protein_pct: float = 18.5,
            aflatoxin_b1_ppb: float = 8.5,
            lead_pb_ppm: float = 1.2,
            banned_substance: str | None = None,
        ) -> str:
            return handle_livestock_feed({
                "product_name": product_name,
                "feed_type": feed_type,
                "manufacturer": manufacturer,
                "crude_protein_pct": crude_protein_pct,
                "aflatoxin_b1_ppb": aflatoxin_b1_ppb,
                "lead_pb_ppm": lead_pb_ppm,
                "banned_substance": banned_substance,
            })

        @app.tool(
            name="mekong_livestock_waste",
            description="Audit livestock waste management and Biogas digester volume adequacy under Decree 46/2022/NĐ-CP.",
        )
        def mekong_livestock_waste(
            farm_id: str,
            livestock_units: float = 400.0,
            treatment_method: str = "BIOGAS_DIGESTER",
            biogas_volume_m3: float = 350.0,
            is_cattle: bool = False,
        ) -> str:
            return handle_livestock_waste({
                "farm_id": farm_id,
                "livestock_units": livestock_units,
                "treatment_method": treatment_method,
                "biogas_volume_m3": biogas_volume_m3,
                "is_cattle": is_cattle,
            })

        @app.tool(
            name="mekong_livestock_list",
            description="Query registered livestock farms, biosecurity audits, feed tests, or waste/biogas projects.",
        )
        def mekong_livestock_list(
            category: str = "farms",
            limit: int = 50,
        ) -> str:
            return handle_livestock_list({
                "category": category,
                "limit": limit,
            })

        @app.tool(
            name="mekong_livestock_status",
            description="Retrieve Vietnamese animal husbandry, biosecurity, feed standards, and waste telemetry.",
        )
        def mekong_livestock_status() -> str:
            return handle_livestock_status({})
















    if transport == "sse":
        os.environ["MCP_SSE_PORT"] = str(port)
        app.run(transport="sse")
    else:
        app.run(transport="stdio")


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def main() -> None:
    ensure_virtualenv()
    parser = argparse.ArgumentParser(description="Mekong MCP Stdio Server Bridge")
    parser.add_argument(
        "--fabric",
        action="store_true",
        help="Run in Command Fabric mode (exposing all 302 command fabric tools)",
    )
    parser.add_argument(
        "--mode",
        choices=["core", "fabric"],
        default="core",
        help="Server mode: 'core' (14 core tools) or 'fabric' (command fabric tools)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="",
        help="MCP server name (default: mekong-core or mekong-fabric)",
    )
    parser.add_argument(
        "--fallback",
        action="store_true",
        help="Force pure-Python zero-dependency JSON-RPC stdio engine",
    )
    parser.add_argument(
        "--engine",
        choices=["auto", "fastmcp", "pure"],
        default="auto",
        help="Execution engine: 'auto', 'fastmcp', or 'pure'",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport type (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE transport (default: 8000)",
    )

    args = parser.parse_args()

    mode = "fabric" if (args.fabric or args.mode == "fabric") else "core"
    default_name = "mekong-fabric" if mode == "fabric" else "mekong-core"
    server_name = args.name or default_name
    server_version = "1.0.0" if mode == "fabric" else "0.1.0"

    force_fallback = (
        args.fallback
        or args.engine == "pure"
        or os.environ.get("MEKONG_FORCE_MCP_FALLBACK") in {"1", "true", "True"}
    )

    if not force_fallback and _HAS_FASTMCP and args.engine != "pure":
        try:
            run_fastmcp_server(
                mode=mode,
                name=server_name,
                transport=args.transport,
                port=args.port,
            )
            return
        except Exception as exc:
            sys.stderr.write(f"FastMCP server exited or failed ({exc}), falling back to pure JSON-RPC server.\n")

    # Pure-Python Stdio JSON-RPC 2.0 Engine Fallback
    if mode == "fabric":
        tools, handlers = load_command_fabric_tools()
    else:
        tools, handlers = CORE_TOOLS_SPEC, CORE_HANDLERS

    server = PureJsonRpcServer(
        name=server_name,
        version=server_version,
        tools=tools,
        handlers=handlers,
    )
    server.serve()


if __name__ == "__main__":
    main()
