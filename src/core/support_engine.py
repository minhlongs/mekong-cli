"""Mekong Support Engine — Customer Success, Onboarding & NPS Feedback.

Part of Mekong's Agency OS customer success layer.
Strictly standard library only (tests/test_core_boundary.py compliant).
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

ONBOARDING_STEPS_DEFINITION = [
    {"index": 1, "title": "Configure environment variables and provider keys in HARNESS.md / .env"},
    {"index": 2, "title": "Inspect and verify agent registry definitions in agents/registry.yaml"},
    {"index": 3, "title": "Execute first autonomous PEV goal workflow via 'mekong cook'"},
    {"index": 4, "title": "Review system diagnostics and observability scorecards via 'mekong daily'"},
    {"index": 5, "title": "Deploy to production environment and configure webhook integrations"},
]


class OnboardingStatus:
    """Current onboarding milestones progress."""

    def __init__(
        self,
        completed_count: int,
        total_count: int,
        progress_pct: float,
        current_step: Optional[int],
        steps: List[Dict[str, Any]],
    ) -> None:
        self.completed_count = completed_count
        self.total_count = total_count
        self.progress_pct = progress_pct
        self.current_step = current_step
        self.steps = steps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completed_count": self.completed_count,
            "total_count": self.total_count,
            "progress_pct": self.progress_pct,
            "current_step": self.current_step,
            "steps": self.steps,
        }


class FeedbackRecord:
    """Customer satisfaction or feedback record."""

    def __init__(
        self,
        id: str,
        user_id: str,
        nps_score: Optional[int],
        feedback_text: str,
        category: str,
        created_at: str,
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.nps_score = nps_score
        self.feedback_text = feedback_text
        self.category = category
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "nps_score": self.nps_score,
            "feedback_text": self.feedback_text,
            "category": self.category,
            "created_at": self.created_at,
        }


class BugReport:
    """Submitted bug report."""

    def __init__(
        self,
        id: str,
        title: str,
        severity: str,
        description: str,
        steps: str,
        status: str,
        created_at: str,
    ) -> None:
        self.id = id
        self.title = title
        self.severity = severity.lower()
        self.description = description
        self.steps = steps
        self.status = status
        self.created_at = created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "description": self.description,
            "steps": self.steps,
            "status": self.status,
            "created_at": self.created_at,
        }


class NpsSummary:
    """Net Promoter Score statistical aggregate."""

    def __init__(
        self,
        total_responses: int,
        nps_score: float,
        promoters: int,
        passives: int,
        detractors: int,
        rating_distribution: Dict[int, int],
    ) -> None:
        self.total_responses = total_responses
        self.nps_score = nps_score
        self.promoters = promoters
        self.passives = passives
        self.detractors = detractors
        self.rating_distribution = rating_distribution

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_responses": self.total_responses,
            "nps_score": self.nps_score,
            "promoters": self.promoters,
            "passives": self.passives,
            "detractors": self.detractors,
            "rating_distribution": self.rating_distribution,
        }


class IssueTriage:
    """Smart triage recommendation for user issues."""

    def __init__(
        self,
        issue_text: str,
        category: str,
        urgency: str,
        recommended_action: str,
        escalation_channel: str,
    ) -> None:
        self.issue_text = issue_text
        self.category = category
        self.urgency = urgency
        self.recommended_action = recommended_action
        self.escalation_channel = escalation_channel

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issue_text": self.issue_text,
            "category": self.category,
            "urgency": self.urgency,
            "recommended_action": self.recommended_action,
            "escalation_channel": self.escalation_channel,
        }


class SupportEngine:
    """Autonomous Customer Success & Support Engine."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.project_root = project_root or Path.cwd()
        if db_path is not None:
            self.db_path = db_path
        else:
            mekong_dir = self.project_root / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "support.db"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        """Initialize tables for onboarding, feedback, and bug reports."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS onboarding_steps (
                    step_index INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    completed INTEGER NOT NULL DEFAULT 0,
                    completed_at TEXT,
                    notes TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    nps_score INTEGER,
                    feedback_text TEXT,
                    category TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bug_reports (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT,
                    steps TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Seed default onboarding steps if empty
            count = conn.execute("SELECT COUNT(*) FROM onboarding_steps").fetchone()[0]
            if count == 0:
                for s in ONBOARDING_STEPS_DEFINITION:
                    conn.execute(
                        "INSERT INTO onboarding_steps (step_index, title, completed, completed_at, notes) VALUES (?, ?, 0, NULL, '')",
                        (s["index"], s["title"]),
                    )
            conn.commit()

    def get_onboarding_status(self) -> OnboardingStatus:
        """Retrieve current onboarding progress."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM onboarding_steps ORDER BY step_index ASC").fetchall()

        steps: List[Dict[str, Any]] = []
        completed_count = 0
        current_step: Optional[int] = None

        for r in rows:
            is_comp = bool(r["completed"])
            if is_comp:
                completed_count += 1
            elif current_step is None:
                current_step = r["step_index"]

            steps.append({
                "step": r["step_index"],
                "title": r["title"],
                "completed": is_comp,
                "completed_at": r["completed_at"],
                "notes": r["notes"] or "",
            })

        total = len(steps)
        progress = round((completed_count / total) * 100, 1) if total > 0 else 0.0

        return OnboardingStatus(
            completed_count=completed_count,
            total_count=total,
            progress_pct=progress,
            current_step=current_step,
            steps=steps,
        )

    def complete_onboarding_step(self, step_index: int, notes: str = "") -> OnboardingStatus:
        """Mark an onboarding step as completed."""
        if not (1 <= step_index <= 5):
            raise ValueError(f"Step index must be between 1 and 5, got {step_index}")

        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE onboarding_steps
                SET completed = 1, completed_at = ?, notes = ?
                WHERE step_index = ?
                """,
                (ts, notes, step_index),
            )
            conn.commit()

        return self.get_onboarding_status()

    def reset_onboarding(self) -> OnboardingStatus:
        """Reset all onboarding steps to uncompleted."""
        with self._get_connection() as conn:
            conn.execute("UPDATE onboarding_steps SET completed = 0, completed_at = NULL, notes = ''")
            conn.commit()
        return self.get_onboarding_status()

    def submit_feedback(
        self,
        nps_score: Optional[int] = None,
        feedback_text: str = "",
        user_id: str = "default_user",
        category: str = "general",
    ) -> FeedbackRecord:
        """Record customer satisfaction or NPS rating."""
        if nps_score is not None:
            if not (0 <= nps_score <= 10):
                raise ValueError(f"NPS score must be between 0 and 10, got {nps_score}")

        fb_id = f"FB-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback (id, user_id, nps_score, feedback_text, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (fb_id, user_id, nps_score, feedback_text, category, ts),
            )
            conn.commit()

        return FeedbackRecord(
            id=fb_id,
            user_id=user_id,
            nps_score=nps_score,
            feedback_text=feedback_text,
            category=category,
            created_at=ts,
        )

    def submit_bug(
        self,
        title: str,
        severity: str = "medium",
        description: str = "",
        steps: str = "",
    ) -> BugReport:
        """File a new bug report in the customer success ledger."""
        sev = severity.lower()
        if sev not in {"low", "medium", "high", "critical"}:
            sev = "medium"

        bug_id = f"BUG-{uuid.uuid4().hex[:8].upper()}"
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO bug_reports (id, title, severity, description, steps, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (bug_id, title, sev, description, steps, "new", ts),
            )
            conn.commit()

        return BugReport(
            id=bug_id,
            title=title,
            severity=sev,
            description=description,
            steps=steps,
            status="new",
            created_at=ts,
        )

    def get_nps_summary(self) -> NpsSummary:
        """Calculate aggregated NPS score and rating distribution."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT nps_score FROM feedback WHERE nps_score IS NOT NULL").fetchall()

        scores = [r["nps_score"] for r in rows]
        total = len(scores)

        distribution: Dict[int, int] = {i: 0 for i in range(11)}
        for s in scores:
            distribution[s] = distribution.get(s, 0) + 1

        if total == 0:
            return NpsSummary(
                total_responses=0,
                nps_score=0.0,
                promoters=0,
                passives=0,
                detractors=0,
                rating_distribution=distribution,
            )

        promoters = sum(1 for s in scores if s in {9, 10})
        passives = sum(1 for s in scores if s in {7, 8})
        detractors = sum(1 for s in scores if s <= 6)

        nps = round(((promoters - detractors) / total) * 100, 1)

        return NpsSummary(
            total_responses=total,
            nps_score=nps,
            promoters=promoters,
            passives=passives,
            detractors=detractors,
            rating_distribution=distribution,
        )

    def list_feedback(self, limit: int = 50) -> List[FeedbackRecord]:
        """List recent customer feedback submissions."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()

        return [
            FeedbackRecord(
                id=r["id"],
                user_id=r["user_id"],
                nps_score=r["nps_score"],
                feedback_text=r["feedback_text"] or "",
                category=r["category"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def list_bugs(self, status: str = "ALL") -> List[BugReport]:
        """List submitted bug reports."""
        query = "SELECT * FROM bug_reports WHERE 1=1"
        params: List[Any] = []
        if status.upper() != "ALL":
            query += " AND status = ?"
            params.append(status.lower())
        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            BugReport(
                id=r["id"],
                title=r["title"],
                severity=r["severity"],
                description=r["description"] or "",
                steps=r["steps"] or "",
                status=r["status"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def triage_issue(self, issue_description: str) -> IssueTriage:
        """Analyze user description and provide triage & resolution guidance."""
        text = issue_description.lower()

        # Heuristic rules
        if any(w in text for w in ["api key", "token", "unauthorized", "401", "auth", "login", "credentials"]):
            category = "auth_setup"
            urgency = "high"
            action = "Run 'mekong config' to review API credentials and ensure keys are set in HARNESS.md or .env."
            channel = "Documentation: docs/core-contract.md & Setup Guide"
        elif any(w in text for w in ["billing", "invoice", "pricing", "payment", "stripe", "subscription", "charge"]):
            category = "billing"
            urgency = "high"
            action = "Check usage metering with 'mekong usage' or update subscription plan with 'mekong subscribe'."
            channel = "Billing Desk: billing@mekongmind.com"
        elif any(w in text for w in ["syntax", "traceback", "exception", "crash", "segmentation", "panic", "assertion"]):
            category = "bug_report"
            urgency = "critical" if "crash" in text or "panic" in text else "high"
            action = "Capture error logs with 'mekong debug' and file a reproducible bug report via 'mekong support bug'."
            channel = "GitHub Issues: https://github.com/minhlongs/mekong-cli/issues"
        elif any(w in text for w in ["slow", "timeout", "latency", "hang", "perf", "delay"]):
            category = "performance"
            urgency = "medium"
            action = "Execute 'mekong ops sweep' and 'mekong doctor' to inspect disk and resource constraints."
            channel = "SRE & Performance channel: support@mekongmind.com"
        else:
            category = "general_inquiry"
            urgency = "low"
            action = "Explore available workflows via 'mekong --help' or query agent guides in .agents/skills/."
            channel = "Community Forum & Discord / Zalo OA"

        return IssueTriage(
            issue_text=issue_description,
            category=category,
            urgency=urgency,
            recommended_action=action,
            escalation_channel=channel,
        )

    def get_support_channels(self) -> Dict[str, str]:
        """Return official support and contact links."""
        return {
            "github_issues": "https://github.com/minhlongs/mekong-cli/issues",
            "email_support": "support@mekongmind.com",
            "billing_support": "billing@mekongmind.com",
            "documentation": "https://github.com/minhlongs/mekong-cli",
            "zalo_oa": "https://zalo.me/mekongcli",
        }

    def get_status(self) -> Dict[str, Any]:
        """High-level customer success overview."""
        onboarding = self.get_onboarding_status()
        nps = self.get_nps_summary()
        bugs = self.list_bugs(status="ALL")
        open_bugs = [b for b in bugs if b.status != "resolved"]

        return {
            "onboarding_progress_pct": onboarding.progress_pct,
            "onboarding_step": onboarding.current_step,
            "onboarding_completed": onboarding.completed_count == onboarding.total_count,
            "nps_score": nps.nps_score,
            "nps_total_responses": nps.total_responses,
            "open_bugs_count": len(open_bugs),
            "channels": self.get_support_channels(),
        }


_default_engine: Optional[SupportEngine] = None


def get_support_engine(db_path: Optional[Path] = None, project_root: Optional[Path] = None) -> SupportEngine:
    """Singleton getter for SupportEngine."""
    global _default_engine
    if db_path is not None or project_root is not None:
        return SupportEngine(db_path=db_path, project_root=project_root)
    if _default_engine is None:
        _default_engine = SupportEngine()
    return _default_engine
