# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""core/daily_briefing.py — Autonomous Daily Executive Briefing & Standup Engine."""

from __future__ import annotations

import datetime
import logging
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CommitSummary:
    sha: str; message: str; author: str; date: str  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return {"sha": self.sha, "message": self.message, "author": self.author, "date": self.date}


@dataclass
class DebtItem:
    file: str; line: int; marker: str; text: str  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return {"file": self.file, "line": self.line, "marker": self.marker, "text": self.text}


@dataclass
class DailyBriefingReport:
    ok: bool; date: str; repo_name: str; current_branch: str; commits_count: int  # noqa: E702
    recent_commits: list[CommitSummary]; files_changed_stat: str; dirty_files_count: int  # noqa: E702
    dirty_files: list[str]; branches: list[str]; debt_items: list[DebtItem]  # noqa: E702
    queue_depth: int; dlq_count: int; focus_priorities: list[str]; error: Optional[str] = None  # noqa: E702

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok, "date": self.date, "repo_name": self.repo_name, "current_branch": self.current_branch,
            "commits_count": self.commits_count, "recent_commits": [c.to_dict() for c in self.recent_commits],
            "files_changed_stat": self.files_changed_stat, "dirty_files_count": self.dirty_files_count,
            "dirty_files": self.dirty_files, "branches": self.branches,
            "debt_items": [d.to_dict() for d in self.debt_items], "queue_depth": self.queue_depth,
            "dlq_count": self.dlq_count, "focus_priorities": self.focus_priorities, "error": self.error,
        }


class DailyBriefingEngine:
    """Collects repository telemetry, technical debt, and synthesizes daily standups."""

    EXCLUDED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", "dist", "build", ".egg-info", ".archive"}
    SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".go", ".rs", ".json", ".yaml", ".yml"}

    def __init__(self, repo_dir: str | Path | None = None) -> None:
        self.repo_dir = Path(repo_dir or os.getcwd()).resolve()

    def _run_git(self, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
        try:
            res = subprocess.run(["git"] + args, cwd=self.repo_dir, capture_output=True, text=True, timeout=timeout)
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except Exception as exc:
            return 1, "", str(exc)

    def collect_git_activity(self, since: str = "24 hours ago") -> dict[str, Any]:
        code, _, _ = self._run_git(["rev-parse", "--show-toplevel"])
        if code != 0:
            return {"ok": False, "error": f"Not a git repository: {self.repo_dir}", "commits_count": 0, "recent_commits": [], "files_changed_stat": "", "dirty_files": [], "branches": [], "current_branch": ""}
        _, curr_branch, _ = self._run_git(["branch", "--show-current"])
        code, count_out, _ = self._run_git(["rev-list", "--count", f"--since={since}", "HEAD"])
        commits_count = int(count_out) if code == 0 and count_out.isdigit() else 0
        _, log_out, _ = self._run_git(["log", f"--since={since}", "--pretty=format:%h|%an|%cr|%s", "-n", "10"])
        commits: list[CommitSummary] = []
        for line in (log_out.split("\n") if log_out else []):
            parts = line.strip().split("|", 3)
            if len(parts) == 4:
                commits.append(CommitSummary(sha=parts[0].strip(), author=parts[1].strip(), date=parts[2].strip(), message=parts[3].strip()))
        stat_summary = self._run_git(["diff", "--stat", f"HEAD~{min(commits_count, 10)}..HEAD"])[1] if commits_count > 0 else ""
        dirty_files = [ln.strip().split()[-1] for ln in self._run_git(["status", "--porcelain"])[1].split("\n") if ln.strip()]
        branches = [b.strip().lstrip("* ").strip() for b in self._run_git(["branch", "--list"])[1].split("\n") if b.strip()]
        return {
            "ok": True, "repo_name": self.repo_dir.name, "current_branch": curr_branch or "main",
            "commits_count": commits_count, "recent_commits": commits, "files_changed_stat": stat_summary,
            "dirty_files": dirty_files, "dirty_count": len(dirty_files), "branches": branches,
        }

    def scan_codebase_debt(self, max_items: int = 15) -> list[DebtItem]:
        items: list[DebtItem] = []
        pattern = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b(?:\(([^)]+)\))?:?\s*(.*)", re.IGNORECASE)
        for root, dirs, files in os.walk(self.repo_dir):
            dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS and not d.startswith(".")]
            for file_name in sorted(files):
                if len(items) >= max_items:
                    return items
                if Path(file_name).suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                    continue
                full_path = Path(root) / file_name
                rel_path = full_path.relative_to(self.repo_dir)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, start=1):
                            if len(items) >= max_items:
                                break
                            if match := pattern.search(line):
                                items.append(DebtItem(file=str(rel_path), line=line_num, marker=match.group(1).upper(), text=(match.group(3).strip() or line.strip())[:100]))
                except Exception:
                    continue
        return items

    def check_system_health(self) -> dict[str, Any]:
        try:
            from src.core.task_queue import get_task_queue
            stat = get_task_queue().status()
            return {"queue_depth": stat.get("pending_tasks", 0) + stat.get("active_leases", 0), "dlq_count": stat.get("dlq_tasks", 0)}
        except Exception:
            return {"queue_depth": 0, "dlq_count": 0}

    def synthesize_today_focus(self, git_act: dict[str, Any], debt_items: list[DebtItem], health: dict[str, Any]) -> list[str]:
        priorities: list[str] = []
        if git_act.get("dirty_count", 0) > 0:
            priorities.append(f"Review and ship {git_act['dirty_count']} uncommitted file changes (`mekong ship`)")
        if health.get("dlq_count", 0) > 0:
            priorities.append(f"Inspect and recover {health['dlq_count']} failed tasks in dead-letter queue (`mekong queue dlq`)")
        fixmes = [d for d in debt_items if d.marker in ("FIXME", "XXX")]
        if fixmes:
            priorities.append(f"Resolve {fixmes[0].marker} in {fixmes[0].file}:{fixmes[0].line} ('{fixmes[0].text[:50]}')")
        elif debt_items:
            priorities.append(f"Address {debt_items[0].marker} in {debt_items[0].file}:{debt_items[0].line} ('{debt_items[0].text[:50]}')")
        commits = git_act.get("commits_count", 0)
        priorities.append(f"Kick off daily feature development cycle on '{git_act.get('current_branch', 'main')}' (`mekong cook`)" if commits == 0 else f"Run test and verification battery on recent {commits} commits (`mekong test`)")
        if len(priorities) < 3:
            priorities.append("Review project architecture and technical graph (`mekong tech-graph`)")
        return priorities[:4]

    def generate_report(self, since: str = "24 hours ago", include_debt: bool = True) -> DailyBriefingReport:
        today_str = datetime.date.today().strftime("%b %d, %Y")
        git_act = self.collect_git_activity(since=since)
        if not git_act.get("ok"):
            return DailyBriefingReport(False, today_str, self.repo_dir.name, "", 0, [], "", 0, [], [], [], 0, 0, [], git_act.get("error", "Failed to collect git activity"))
        debt_items = self.scan_codebase_debt(max_items=10) if include_debt else []
        health = self.check_system_health()
        focus = self.synthesize_today_focus(git_act=git_act, debt_items=debt_items, health=health)
        return DailyBriefingReport(
            True, today_str, git_act["repo_name"], git_act["current_branch"], git_act["commits_count"],
            git_act["recent_commits"], git_act["files_changed_stat"], git_act["dirty_count"],
            git_act["dirty_files"], git_act["branches"], debt_items, health["queue_depth"], health["dlq_count"], focus,
        )


_daily_briefing_instance: DailyBriefingEngine | None = None


def get_daily_briefing_engine(repo_dir: str | Path | None = None) -> DailyBriefingEngine:
    global _daily_briefing_instance
    if _daily_briefing_instance is None or repo_dir is not None:
        _daily_briefing_instance = DailyBriefingEngine(repo_dir=repo_dir)
    return _daily_briefing_instance


__all__ = ["CommitSummary", "DailyBriefingEngine", "DailyBriefingReport", "DebtItem", "get_daily_briefing_engine"]
