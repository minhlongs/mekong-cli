# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap DAG executor — walks chapter graph and dispatches agents."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from src.core.binh_phap.dag import CHAPTER_NODE_COUNT, DagDefinition, load_dag
from src.core.binh_phap.recovery import evaluate, should_retry

logger = logging.getLogger(__name__)
_SCHEMA_VERSION = "1.0"
_RETRY_POLICY_DEFAULT = {"max_consecutive_failures": 3, "backoff_base_seconds": 5}


def _new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ExecutionResult:
    """Outcome for a single chapter."""

    def __init__(self, chapter: int, status: str, started_at: Optional[str] = None, finished_at: Optional[str] = None, error: Optional[str] = None, fallback_chapters: Optional[List[int]] = None) -> None:
        self.chapter, self.status, self.started_at, self.finished_at, self.error, self.fallback_chapters = chapter, status, started_at, finished_at, error, fallback_chapters or []

    def to_dict(self) -> Dict[str, Any]:
        return {"chapter": self.chapter, "status": self.status, "started_at": self.started_at, "finished_at": self.finished_at, "error": self.error, "fallback_chapters": self.fallback_chapters}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecutionResult":
        return cls(chapter=d["chapter"], status=d["status"], started_at=d.get("started_at"), finished_at=d.get("finished_at"), error=d.get("error"), fallback_chapters=d.get("fallback_chapters", []))


class ExecutionState:
    """Mutable run state loaded from / saved to disk."""

    def __init__(self, state_path: Path = Path(".mekong/binh-phap-state.json")) -> None:
        self.path, self.dag, self.completed, self.failed = state_path, None, frozenset(), {}
        self.current, self.results, self.started_at, self.updated_at = None, {}, None, None
        self.run_id, self.schema_version, self.retry_policy = "", _SCHEMA_VERSION, dict(_RETRY_POLICY_DEFAULT)

    @classmethod
    def load(cls, state_path: Path, upgrade_legacy: bool = True) -> "ExecutionState":
        st = cls(state_path)
        if not state_path.exists():
            st.run_id = _new_run_id()
            return st
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            st.completed, st.failed = frozenset(raw.get("completed", [])), {int(k): v for k, v in raw.get("failed", {}).items()}
            st.current, st.started_at, st.updated_at = raw.get("current"), raw.get("started_at"), raw.get("updated_at")
            st.results = {int(k): ExecutionResult.from_dict(v) for k, v in raw.get("results", {}).items()}
            if (loaded_version := raw.get("schema_version", "")) and loaded_version != _SCHEMA_VERSION and upgrade_legacy:
                logger.info("Upgrading binh-phap state from schema %s → %s", loaded_version, _SCHEMA_VERSION)
            st.schema_version, st.run_id, st.retry_policy = _SCHEMA_VERSION, raw.get("run_id", _new_run_id()), raw.get("retry_policy", dict(_RETRY_POLICY_DEFAULT))
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Corrupted binh-phap state — starting fresh: %s", exc)
        return st

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": self.schema_version, "run_id": self.run_id, "completed": list(self.completed), "failed": self.failed, "current": self.current, "retry_policy": self.retry_policy, "started_at": self.started_at, "updated_at": self.updated_at or _now_iso(), "results": {k: v.to_dict() for k, v in self.results.items()}}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.path)

    def mark(self, result: ExecutionResult) -> None:
        self.results[result.chapter] = result
        if result.status == "success":
            self.completed = self.completed | {result.chapter}
        elif result.status == "failed":
            self.failed[result.chapter] = result.error or "unknown"
        self.updated_at = _now_iso()


class BinhPhapExecutor:
    """Runs a Binh Phap DAG end-to-end (or resuming from persisted state)."""

    def __init__(self, dag: Optional[DagDefinition] = None, state_path: Path = Path(".mekong/binh-phap-state.json"), dry_run: bool = False) -> None:
        self.dag, self.state, self.dry_run = dag or load_dag(), ExecutionState.load(state_path), dry_run
        self.results: Dict[int, ExecutionResult] = dict(self.state.results)
        self._consecutive_failures: Dict[int, int] = {}

    def run(self, start_chapter: Optional[int] = None) -> Dict[int, ExecutionResult]:
        self.state.dag = self.dag
        if not self.state.started_at:
            self.state.started_at = _now_iso()
        order = self.dag.topological_order()
        if start_chapter and start_chapter not in order:
            raise ValueError(f"Chapter {start_chapter} not in DAG")
        start_idx = order.index(start_chapter) if start_chapter else 0

        for ch in order[start_idx:]:
            if ch not in self.dag.chapters or ch in self.state.completed or not self._deps_satisfied(ch):
                continue
            result = self._execute_chapter(ch)
            self.state.mark(result)
            self.state.save()
            decision = None
            while result.status == "failed":
                attempt = self._consecutive_failures.get(ch, 0) + 1
                decision = evaluate(ch, attempt, result.error or "unknown")
                if decision.action == "retry" and should_retry(ch, attempt, result.error or "unknown"):
                    self._handle_failure(result)
                    result = self._execute_chapter(ch)
                    self.state.mark(result)
                    self.state.save()
                else:
                    self._handle_failure(result)
                    break
            if result.status in ("success", "skipped") or (decision and decision.action == "fallback"):
                continue
            if ch not in self.dag.human_only:
                break
        return dict(self.state.results)

    def resume(self) -> Dict[int, ExecutionResult]:
        if not self.state.completed:
            return self.run()
        last = max(self.state.completed)
        return self.run(start_chapter=last + 1 if last < CHAPTER_NODE_COUNT else None)

    def _deps_satisfied(self, chapter: int) -> bool:
        return set(self.dag.predecessors(chapter)).issubset(self.state.completed)

    def _execute_chapter(self, chapter: int) -> ExecutionResult:
        node = self.dag.chapters.get(chapter)
        if node is None:
            return ExecutionResult(chapter=chapter, status="skipped", error="Chapter not in definition")
        started = _now_iso()
        if node.requires_human or chapter in self.dag.human_only:
            return ExecutionResult(chapter=chapter, status="skipped", started_at=started, error="Requires human approval — skipped in automated run")
        if not self.dry_run:
            time.sleep(0)
        return ExecutionResult(chapter=chapter, status="success", started_at=started, finished_at=_now_iso())

    def _handle_failure(self, result: ExecutionResult) -> bool:
        if result.chapter not in self.dag.chapters:
            return False
        attempt = self._consecutive_failures.get(result.chapter, 0) + 1
        self._consecutive_failures[result.chapter] = attempt
        decision = evaluate(result.chapter, attempt, result.error or "unknown")
        if decision.action == "abort":
            return False
        if decision.action == "escalate":
            from src.core.binh_phap.recovery import escalate
            escalate(result.chapter, result.error or "unknown")
            return False
        if decision.action == "retry" and should_retry(result.chapter, attempt, result.error or "unknown"):
            return True
        if decision.action == "fallback" and decision.fallback_chapters:
            self.state.failed[result.chapter] = result.error or "failed"
            for fb in (c for c in decision.fallback_chapters if c not in self.dag.human_only):
                fb_result = self._execute_chapter(fb)
                self.state.mark(fb_result)
                self.state.save()
                if fb_result.status == "success":
                    return True
        return False

    def status_report(self) -> Dict[str, Any]:
        rows = [{"chapter": ch, "name": n.name if (n := self.dag.chapters.get(ch)) else "?", "agent": n.primary_agent if n else "?", "status": r.status if (r := self.state.results.get(ch)) else "pending", "error": r.error if r else "", "human_only": ch in self.dag.human_only} for ch in self.dag.topological_order()]
        return {"started_at": self.state.started_at, "updated_at": self.state.updated_at, "completed_count": len(self.state.completed), "failed_count": len(self.state.failed), "total": CHAPTER_NODE_COUNT, "chapters": rows}


Executor = BinhPhapExecutor  # noqa: E305
