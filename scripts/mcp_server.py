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
