# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - Swarm Registry."""

from __future__ import annotations
import importlib.util
import logging
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
import requests  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from .verifier import ExecutionResult

logger = logging.getLogger(__name__)


@dataclass
class SwarmNode:
    id: str
    name: str
    host: str
    port: int
    token: str
    status: str = "unknown"
    last_heartbeat: float = 0.0


class SwarmRegistry:
    def __init__(self, config_path: str | None = None) -> None:
        self._nodes: dict[str, SwarmNode] = {}
        self._config_path = config_path or str(Path(".mekong") / "swarm.yaml")
        self._load()

    def register_node(self, name: str, host: str, port: int, token: str) -> SwarmNode:
        node = SwarmNode(id=uuid.uuid4().hex[:8], name=name, host=host, port=port, token=token)
        self._nodes[node.id] = node
        self._save()
        return node

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False
        del self._nodes[node_id]
        self._save()
        return True

    def list_nodes(self) -> list[SwarmNode]:
        return list(self._nodes.values())

    def get_node(self, node_id: str) -> SwarmNode | None:
        return self._nodes.get(node_id)

    def check_health(self, node: SwarmNode, timeout: float = 3.0) -> str:
        try:
            resp = requests.get(f"http://{node.host}:{node.port}/health", timeout=timeout)
            node.status = "healthy" if resp.status_code == 200 else "unhealthy"
        except requests.RequestException:
            node.status = "unreachable"
        node.last_heartbeat = time.time()
        return node.status

    def check_all_health(self, timeout: float = 3.0) -> dict[str, str]:
        results = {node.id: self.check_health(node, timeout) for node in self._nodes.values()}
        self._save()
        return results

    def dispatch_goal(self, node_id: str, goal: str, timeout: float = 60.0) -> dict[str, Any]:
        node = self.get_node(node_id)
        if not node:
            return {"error": f"Node {node_id} not found"}
        try:
            return dict(requests.post(f"http://{node.host}:{node.port}/cmd", json={"goal": goal, "token": node.token}, timeout=timeout).json())
        except requests.RequestException as e:
            return {"error": str(e)}

    def _save(self) -> None:
        path = Path(self._config_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Mekong Swarm Registry\nnodes:\n"] + [
            f"  - id: {n.id}\n    name: {n.name}\n    host: {n.host}\n    port: {n.port}\n    token: {n.token}\n    status: {n.status}\n    last_heartbeat: {n.last_heartbeat}\n"
            for n in self._nodes.values()
        ]
        path.write_text("".join(lines), encoding="utf-8")

    def _load(self) -> None:
        path = Path(self._config_path)
        if not path.exists():
            return
        try:
            import yaml  # type: ignore[import-untyped]
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.debug("Failed to load swarm config: %s", e)
            return
        for entry in raw.get("nodes") or []:
            node = SwarmNode(
                id=str(entry.get("id", "")), name=str(entry.get("name", "")), host=str(entry.get("host", "")),
                port=int(entry.get("port", 8000)), token=str(entry.get("token", "")),
                status=str(entry.get("status", "unknown")), last_heartbeat=float(entry.get("last_heartbeat", 0.0)),
            )
            if node.id:
                self._nodes[node.id] = node


class SwarmDispatcher:
    _AGENT_TYPE_MAP: dict[str, str] = {"git": "git", "file": "file", "shell": "shell"}

    def __init__(self, registry: SwarmRegistry) -> None:
        self.registry, self._local_agents = registry, {}
        self._init_local_agents()

    def _init_local_agents(self) -> None:
        base = Path(__file__).resolve().parent.parent / "agents"
        self._local_agents = {}
        for role in ("git", "file", "shell"):
            agent_path = base / f"{role}_agent.py"
            try:
                spec = importlib.util.spec_from_file_location(f"src.agents.{role}_agent", agent_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if agent_cls := getattr(module, role.capitalize() + "Agent", None):
                        self._local_agents[role] = agent_cls()
            except (FileNotFoundError, ImportError) as exc:
                logger.debug("Agent module unavailable (%s): %s", agent_path, exc)
            except SyntaxError as exc:
                logger.warning("Agent module has syntax error (%s): %s", agent_path, exc)

    def get_healthy_nodes(self) -> list[SwarmNode]:
        return [n for n in self.registry.list_nodes() if n.status == "healthy"]

    def _route_step(self, step: object) -> str:
        step_type = str((getattr(step, "params", None) or {}).get("type", "")).lower()
        if step_type in self._AGENT_TYPE_MAP:
            return self._AGENT_TYPE_MAP[step_type]
        desc = str(getattr(step, "description", "")).lower()
        if any(kw in desc for kw in ("git ", "commit", "branch", "diff", "status")):
            return "git"
        return "file" if any(kw in desc for kw in ("read file", "write file", "find file", "grep")) else "shell"

    def _dispatch_local(self, step: object, agent_type: str) -> "ExecutionResult":
        from .verifier import ExecutionResult
        agent = self._local_agents.get(agent_type) or self._local_agents.get("shell")
        if agent is None:
            return ExecutionResult(exit_code=1, stdout="", stderr="No local agent available")
        from .agent_base import Task
        description = getattr(step, "description", "")
        task_input = dict(getattr(step, "params", None) or {})
        task_input.setdefault("command", description)
        result = agent.execute(Task(id="swarm-dispatch", description=description, input=task_input))
        return ExecutionResult(exit_code=0 if result.success else 1, stdout=result.output or "", stderr=result.error or "")

    def _dispatch_remote(self, step: object, node: SwarmNode) -> "ExecutionResult":
        from .verifier import ExecutionResult
        try:
            data = requests.post(f"http://{node.host}:{node.port}/cmd", json={"goal": getattr(step, "description", ""), "token": node.token}, timeout=60.0).json()
            return ExecutionResult(exit_code=0 if data.get("status") == "success" else 1, stdout=str(data.get("result", "")), stderr=str(data.get("error", "")))
        except requests.RequestException as e:
            return ExecutionResult(exit_code=1, stdout="", stderr=str(e))

    def dispatch(self, step: object) -> "ExecutionResult":
        agent_type, healthy = self._route_step(step), self.get_healthy_nodes()
        return self._dispatch_remote(step, healthy[0]) if healthy else self._dispatch_local(step, agent_type)


__all__ = ["SwarmDispatcher", "SwarmNode", "SwarmRegistry"]
