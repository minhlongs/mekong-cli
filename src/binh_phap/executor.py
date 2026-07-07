"""Binh Phap DAG executor — walks chapter graph and dispatches agents.

State persisted to .mekong/binh-phap-state.json between runs so interrupted
work resumes from last completed chapter rather than restarting.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.binh_phap.dag import DagDefinition, CHAPTER_NODE_COUNT, load_dag

logger = logging.getLogger(__name__)


class ExecutionResult:
    """Outcome for a single chapter."""

    def __init__(
        self,
        chapter: int,
        status: str,
        started_at: Optional[str] = None,
        finished_at: Optional[str] = None,
        error: Optional[str] = None,
        fallback_chapters: Optional[List[int]] = None,
    ) -> None:
        self.chapter = chapter
        self.status = status  # 'success' | 'failed' | 'skipped' | 'pending'
        self.started_at = started_at
        self.finished_at = finished_at
        self.error = error
        self.fallback_chapters = fallback_chapters or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "fallback_chapters": self.fallback_chapters,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExecutionResult":
        return cls(
            chapter=d["chapter"],
            status=d["status"],
            started_at=d.get("started_at"),
            finished_at=d.get("finished_at"),
            error=d.get("error"),
            fallback_chapters=d.get("fallback_chapters", []),
        )


class ExecutionState:
    """Mutable run state loaded from / saved to disk.

    High-water mark: records the last *successfully completed* chapter so
    the executor can resume without re-running finished nodes.
    """

    def __init__(self, state_path: Path = Path(".mekong/binh-phap-state.json")) -> None:
        self.path = state_path
        self.dag: Optional[DagDefinition] = None
        self.completed: frozenset[int] = frozenset()
        self.failed: Dict[int, str] = {}
        self.current: Optional[int] = None
        self.results: Dict[int, ExecutionResult] = {}
        self.started_at: Optional[str] = None
        self.updated_at: Optional[str] = None

    @classmethod
    def load(cls, state_path: Path) -> "ExecutionState":
        st = cls(state_path)
        if not state_path.exists():
            return st
        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            st.dag = None  # reloaded separately
            st.completed = frozenset(raw.get("completed", []))
            st.failed = {
                int(k): v for k, v in raw.get("failed", {}).items()
            }
            st.current = raw.get("current")
            st.started_at = raw.get("started_at")
            st.updated_at = raw.get("updated_at")
            st.results = {
                int(k): ExecutionResult.from_dict(v)
                for k, v in raw.get("results", {}).items()
            }
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning(
                "Corrupted binh-phap state — starting fresh: %s", exc
            )
            return st
        return st

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "completed": list(self.completed),
            "failed": self.failed,
            "current": self.current,
            "started_at": self.started_at,
            "updated_at": self.updated_at or _now_iso(),
            "results": {k: v.to_dict() for k, v in self.results.items()},
        }
        self.path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def mark(self, result: ExecutionResult) -> None:
        self.results[result.chapter] = result
        if result.status == "success":
            self.completed = self.completed | {result.chapter}
        elif result.status == "failed":
            self.failed[result.chapter] = result.error or "unknown"
        self.updated_at = _now_iso()


class Executor:
    """Runs a Binh Phap DAG end-to-end (or resuming from persisted state)."""

    def __init__(
        self,
        dag: Optional[DagDefinition] = None,
        state_path: Path = Path(".mekong/binh-phap-state.json"),
        dry_run: bool = False,
    ) -> None:
        self.dag = dag or load_dag()
        self.state = ExecutionState.load(state_path)
        self.dry_run = dry_run
        self.results: Dict[int, ExecutionResult] = dict(self.state.results)

    def run(self, start_chapter: Optional[int] = None) -> Dict[int, ExecutionResult]:
        """Execute the DAG from the beginning (or a specific chapter)."""
        self.state.dag = self.dag
        if not self.state.started_at:
            self.state.started_at = _now_iso()

        order = self.dag.topological_order()
        start_idx = 0
        if start_chapter:
            try:
                start_idx = order.index(start_chapter)
            except ValueError:
                raise ValueError(f"Chapter {start_chapter} not in DAG")

        for ch in order[:start_idx]:
            if ch in self.state.completed:
                logger.info(
                    "Chapter %d already completed — skipping", ch
                )

        for ch in order[start_idx:]:
            if ch not in self.dag.chapters:
                continue
            if ch in self.state.completed:
                logger.info("Chapter %d completed — skipping", ch)
                continue
            if not self._deps_satisfied(ch):
                logger.info(
                    "Chapter %d dependencies not met — skipping", ch
                )
                continue
            result = self._execute_chapter(ch)
            self.state.mark(result)
            self.state.save()
            if result.status == "failed" and self._handle_failure(result):
                continue
            if result.status in ("success", "skipped"):
                continue
            if ch not in self.dag.human_only:
                logger.warning("Stopping after failure at chapter %d", ch)
                break

        return dict(self.state.results)

    def resume(self) -> Dict[int, ExecutionResult]:
        """Resume from the last persisted completed chapter."""
        if not self.state.completed:
            return self.run()
        last = max(self.state.completed)
        logger.info("Resuming from chapter %d (last completed)", last)
        return self.run(
            start_chapter=last + 1 if last < CHAPTER_NODE_COUNT else None
        )

    def _deps_satisfied(self, chapter: int) -> bool:
        predecessors = set(self.dag.predecessors(chapter))
        return predecessors.issubset(self.state.completed)

    def _execute_chapter(self, chapter: int) -> ExecutionResult:
        node = self.dag.chapters.get(chapter)
        if node is None:
            return ExecutionResult(
                chapter=chapter, status="skipped", error="Chapter not in definition"
            )

        started = _now_iso()
        if node.requires_human or chapter in self.dag.human_only:
            return ExecutionResult(
                chapter=chapter,
                status="skipped",
                started_at=started,
                error="Requires human approval — skipped in automated run",
            )
        if self.dry_run:
            logger.info(
                "[DRY RUN] Would execute chapter %d (%s)", chapter, node.name
            )
            return ExecutionResult(
                chapter=chapter,
                status="success",
                started_at=started,
                finished_at=_now_iso(),
            )

        logger.info(
            "Executing chapter %d (%s) via %s",
            chapter,
            node.name,
            node.primary_agent,
        )
        finished = _now_iso()
        time.sleep(0)  # placeholder for subagent dispatch
        result = ExecutionResult(
            chapter=chapter,
            status="success",
            started_at=started,
            finished_at=finished,
        )
        logger.info("Chapter %d -> %s", chapter, result.status)
        return result

    def _handle_failure(self, result: ExecutionResult) -> bool:
        """Attempt recovery strategies. Returns True if fallback activated."""
        node = self.dag.chapters.get(result.chapter)
        if not node:
            return False
        fallbacks = node.fallback_chapters
        if not fallbacks:
            logger.info(
                "No fallback chapters for %d — flow stops", result.chapter
            )
            return False
        logger.info("Activating fallback chain %d -> %s", result.chapter, fallbacks)
        self.state.failed[result.chapter] = result.error or "failed"
        for fb in fallbacks:
            if fb in self.dag.human_only:
                logger.info(
                    "Fallback %d is human-only — flagging for operator", fb
                )
                continue
            logger.info("Running fallback chapter %d", fb)
            fb_result = self._execute_chapter(fb)
            self.state.mark(fb_result)
            self.state.save()
            if fb_result.status == "success":
                return True
        return False

    def status_report(self) -> Dict[str, Any]:
        """Return a serialisable dashboard of execution state."""
        order = self.dag.topological_order()
        rows = []
        for ch in order:
            node = self.dag.chapters.get(ch)
            res = self.state.results.get(ch)
            rows.append(
                {
                    "chapter": ch,
                    "name": node.name if node else "?",
                    "agent": node.primary_agent if node else "?",
                    "status": res.status if res else "pending",
                    "error": res.error if res else "",
                    "human_only": ch in self.dag.human_only,
                }
            )
        return {
            "started_at": self.state.started_at,
            "updated_at": self.state.updated_at,
            "completed_count": len(self.state.completed),
            "failed_count": len(self.state.failed),
            "total": CHAPTER_NODE_COUNT,
            "chapters": rows,
        }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
