# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/core/sales_engine.py — Autonomous Sales & Revenue Dealflow Engine.

Manages pipeline opportunities, weighted revenue forecasts, deal preparation,
multi-channel outreach copy, and customer closing reports.
Backed by lightweight SQLite persistence in `.mekong/sales.db`.

Pure Python standard library implementation with zero external dependencies.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class DealStage(str, Enum):
    """Canonical sales pipeline stages."""

    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


STAGE_WEIGHTS: dict[str, float] = {
    DealStage.LEAD.value: 0.10,
    DealStage.QUALIFIED.value: 0.25,
    DealStage.PROPOSAL.value: 0.50,
    DealStage.NEGOTIATION.value: 0.75,
    DealStage.WON.value: 1.00,
    DealStage.LOST.value: 0.00,
}


@dataclass
class DealRecord:
    """Individual sales deal record in pipeline."""

    id: str
    name: str
    company: str
    value: float
    stage: str
    contact_email: str
    notes: str
    created_at: str
    updated_at: str

    @property
    def weighted_value(self) -> float:
        weight = STAGE_WEIGHTS.get(self.stage.lower(), 0.10)
        return round(self.value * weight, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "company": self.company,
            "value": self.value,
            "stage": self.stage,
            "weighted_value": self.weighted_value,
            "contact_email": self.contact_email,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class PipelineMetrics:
    """Consolidated pipeline performance and revenue forecast metrics."""

    total_deals: int
    total_pipeline_value: float
    weighted_pipeline_value: float
    won_value: float
    win_rate: float
    deals_by_stage: dict[str, int]
    top_deals: list[DealRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_deals": self.total_deals,
            "total_pipeline_value": round(self.total_pipeline_value, 2),
            "weighted_pipeline_value": round(self.weighted_pipeline_value, 2),
            "won_value": round(self.won_value, 2),
            "win_rate": round(self.win_rate, 2),
            "deals_by_stage": self.deals_by_stage,
            "top_deals": [d.to_dict() for d in self.top_deals],
        }


@dataclass
class OutreachTemplate:
    """Multi-channel personalized outreach copy and cadence."""

    company: str
    persona: str
    channel: str
    subject: str
    body: str
    follow_up_sequence: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DealPrepReport:
    """Structured prospect research, pain points, and objection handling."""

    company: str
    deal_value: float
    pain_points: list[str]
    solution_summary: str
    roi_multiplier: float
    objections_playbook: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CloseReport:
    """Deal close summary and customer onboarding receipt."""

    deal_id: str
    name: str
    company: str
    final_value: float
    closed_date: str
    onboarding_checklist: list[str]
    revenue_attribution: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SalesEngine:
    """Autonomous sales dealflow, outreach, and revenue pipeline engine."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path:
            self.db_path = Path(db_path)
        else:
            mekong_dir = Path(os.getcwd()) / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "sales.db"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS deals (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    company TEXT NOT NULL,
                    value REAL NOT NULL,
                    stage TEXT NOT NULL,
                    contact_email TEXT,
                    notes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Pipeline & Deal Management
    # -------------------------------------------------------------------------
    def add_deal(
        self,
        name: str,
        company: str,
        value: float,
        stage: str = "lead",
        contact_email: str = "",
        notes: str = "",
    ) -> DealRecord:
        """Add a new deal opportunity to the sales ledger."""
        deal_id = f"deal_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        valid_stage = stage.lower() if stage.lower() in [s.value for s in DealStage] else DealStage.LEAD.value

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO deals (id, name, company, value, stage, contact_email, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (deal_id, name, company, float(value), valid_stage, contact_email, notes, now, now),
            )
            conn.commit()

        return DealRecord(
            id=deal_id,
            name=name,
            company=company,
            value=float(value),
            stage=valid_stage,
            contact_email=contact_email,
            notes=notes,
            created_at=now,
            updated_at=now,
        )

    def update_deal(
        self,
        deal_id: str,
        stage: Optional[str] = None,
        value: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> Optional[DealRecord]:
        """Update an existing sales deal's stage, value, or notes."""
        existing = self.get_deal(deal_id)
        if not existing:
            return None

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_stage = stage.lower() if stage and stage.lower() in [s.value for s in DealStage] else existing.stage
        new_value = float(value) if value is not None else existing.value
        new_notes = notes if notes is not None else existing.notes

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE deals
                SET stage = ?, value = ?, notes = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_stage, new_value, new_notes, now, deal_id),
            )
            conn.commit()

        return self.get_deal(deal_id)

    def get_deal(self, deal_id: str) -> Optional[DealRecord]:
        """Fetch a single deal by its ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM deals WHERE id = ?", (deal_id,)).fetchone()
            if not row:
                return None
            return DealRecord(
                id=row["id"],
                name=row["name"],
                company=row["company"],
                value=float(row["value"]),
                stage=row["stage"],
                contact_email=row["contact_email"] or "",
                notes=row["notes"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_deals(self, stage: Optional[str] = None) -> list[DealRecord]:
        """List deals, optionally filtered by pipeline stage."""
        with self._get_connection() as conn:
            if stage:
                rows = conn.execute(
                    "SELECT * FROM deals WHERE stage = ? ORDER BY value DESC",
                    (stage.lower(),),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM deals ORDER BY value DESC").fetchall()

            return [
                DealRecord(
                    id=r["id"],
                    name=r["name"],
                    company=r["company"],
                    value=float(r["value"]),
                    stage=r["stage"],
                    contact_email=r["contact_email"] or "",
                    notes=r["notes"] or "",
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def get_pipeline_metrics(self) -> PipelineMetrics:
        """Calculate comprehensive sales pipeline metrics."""
        deals = self.list_deals()
        total_deals = len(deals)
        total_val = sum(d.value for d in deals)
        weighted_val = sum(d.weighted_value for d in deals)

        won_deals = [d for d in deals if d.stage == DealStage.WON.value]
        lost_deals = [d for d in deals if d.stage == DealStage.LOST.value]
        won_val = sum(d.value for d in won_deals)

        closed_count = len(won_deals) + len(lost_deals)
        win_rate = (len(won_deals) / closed_count * 100.0) if closed_count > 0 else 0.0

        by_stage: dict[str, int] = {s.value: 0 for s in DealStage}
        for d in deals:
            by_stage[d.stage] = by_stage.get(d.stage, 0) + 1

        top_deals = sorted(deals, key=lambda x: x.value, reverse=True)[:5]

        return PipelineMetrics(
            total_deals=total_deals,
            total_pipeline_value=total_val,
            weighted_pipeline_value=weighted_val,
            won_value=won_val,
            win_rate=win_rate,
            deals_by_stage=by_stage,
            top_deals=top_deals,
        )

    # -------------------------------------------------------------------------
    # Outreach Synthesis
    # -------------------------------------------------------------------------
    def generate_outreach(
        self,
        company: str,
        persona: str = "CTO",
        channel: str = "email",
    ) -> OutreachTemplate:
        """Synthesize tailored multi-channel outreach copy and cadence."""
        c = company.strip() or "Acme Corp"
        p = persona.strip() or "Engineering Leader"
        chan = channel.lower()

        if chan == "linkedin":
            subject = f"Connecting re: agentic automation at {c}"
            body = (
                f"Hi {p}, noticed {c}'s focus on engineering velocity. "
                "We built an autonomous harness engine that helps teams automate 80% of repetitive workflows "
                "with zero vendor lock-in. Would love to share how peers in your space are cutting sprint cycles in half."
            )
        elif chan == "zalo":
            subject = f"Mekong CLI giải pháp tự động hóa cho {c}"
            body = (
                f"Chào anh/chị {p} tại {c}, Mekong CLI cung cấp nền tảng AI harness engineering "
                "giúp tự động hóa quy trình nghiệp vụ, kế toán TT78 và CI/CD với chuẩn Binh Pháp. "
                "Rất mong có cơ hội demo ngắn 15 phút với đội ngũ {c}."
            )
        else:  # email
            subject = f"Accelerating engineering throughput at {c}"
            body = (
                f"Hi {p},\n\n"
                f"I've been following {c}'s recent growth. As engineering teams scale, context fragmentation "
                "and manual deployment checklists often create significant drag on release velocity.\n\n"
                "Mekong CLI provides a deterministic, standard-library agentic harness that unifies PRDs, "
                "code reviews, testing batteries, and production shipping into autonomous 5-step workflows.\n\n"
                "Do you have 10 minutes this Thursday to walk through how other technical teams deployed this "
                "with 100% test pass reliability?\n\n"
                "Best,\nMekong Solutions Team"
            )

        cadence = [
            f"Day 1: Initial outreach via {chan}",
            "Day 3: Value-add follow-up sharing case study and benchmark metrics",
            "Day 7: Quick question on current sprint bottleneck",
            "Day 14: Final check-in with self-serve demo sandbox link",
        ]

        return OutreachTemplate(
            company=c,
            persona=p,
            channel=chan,
            subject=subject,
            body=body,
            follow_up_sequence=cadence,
        )

    # -------------------------------------------------------------------------
    # Deal Preparation
    # -------------------------------------------------------------------------
    def generate_deal_prep(
        self,
        company: str,
        value: float = 12000.0,
        pain_points: str = "",
    ) -> DealPrepReport:
        """Generate deal preparation notes, objection handling, and ROI model."""
        c = company.strip() or "Target Prospect"
        pains = [p.strip() for p in pain_points.split(",") if p.strip()] if pain_points else [
            "High engineering cycle times on boilerplate scaffolding",
            "Fragile CI/CD pipelines lacking deterministic rollback",
            "Lack of unified visibility into codebase debt and team velocity",
        ]

        objections = [
            {
                "objection": "We already use standard CI/CD and open-source agent frameworks.",
                "rebuttal": "Mekong CLI operates as a pure standard-library harness with zero external vendor dependencies, reducing maintenance overhead while offering instant MCP and Typer CLI integration.",
            },
            {
                "objection": "Is the team ready for autonomous agent execution?",
                "rebuttal": "Mekong embeds strict CEO approval gates, pre-flight safety hooks, and automatic git checkpointing, ensuring humans retain 100% governance over high-risk mutations.",
            },
            {
                "objection": "What is the immediate ROI in the first 90 days?",
                "rebuttal": f"Based on a {value:,.0f} USD investment, teams recover 4-6x the contract value in reclaimed engineering hours within the first quarter.",
            },
        ]

        return DealPrepReport(
            company=c,
            deal_value=float(value),
            pain_points=pains,
            solution_summary=f"Custom Mekong Agentic Harness deployment for {c} with automated PEV workflows and executive dashboards.",
            roi_multiplier=4.8,
            objections_playbook=objections,
        )

    # -------------------------------------------------------------------------
    # Deal Close & Customer Receipt
    # -------------------------------------------------------------------------
    def generate_close_report(self, deal_id: str) -> Optional[CloseReport]:
        """Finalize deal closing, transition to WON, and create onboarding receipt."""
        deal = self.get_deal(deal_id)
        if not deal:
            return None

        # Transition stage to won
        updated = self.update_deal(deal_id, stage=DealStage.WON.value)
        today_str = datetime.date.today().strftime("%Y-%m-%d")

        checklist = [
            f"Execute contract terms and signature with {deal.company}",
            f"Generate tenant credentials and license keys for {deal.contact_email or deal.company}",
            "Deploy isolated agent workspace and git worktrees",
            "Schedule 30-minute technical onboarding with engineering leads",
        ]

        attr = {
            "source_deal": deal_id,
            "company": deal.company,
            "contract_value": deal.value,
            "revenue_model": "Annual Platform License",
            "mrr_contribution": round(deal.value / 12.0, 2),
        }

        return CloseReport(
            deal_id=deal_id,
            name=deal.name,
            company=deal.company,
            final_value=deal.value,
            closed_date=today_str,
            onboarding_checklist=checklist,
            revenue_attribution=attr,
        )


def get_sales_engine(db_path: str | Path | None = None) -> SalesEngine:
    """Factory helper returning SalesEngine instance."""
    return SalesEngine(db_path=db_path)
