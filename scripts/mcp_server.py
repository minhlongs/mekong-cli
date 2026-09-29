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
