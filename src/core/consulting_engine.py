"""Mekong Consulting Engine — AI Agent Building Service, Pricing & Outreach.

Client engagement and monetization engine for the Mekong RaaS Agency OS.
Strictly standard library only (tests/test_core_boundary.py compliant).
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional
import uuid

VND_PER_USD = 25400


class ConsultingPackage:
    """Standardized consulting service package."""

    def __init__(
        self,
        tier: str,
        title: str,
        price_usd: float,
        price_vnd: int,
        delivery_time: str,
        description: str,
        deliverables: List[str],
    ) -> None:
        self.tier = tier
        self.title = title
        self.price_usd = price_usd
        self.price_vnd = price_vnd
        self.delivery_time = delivery_time
        self.description = description
        self.deliverables = deliverables

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "title": self.title,
            "price_usd": self.price_usd,
            "price_vnd": self.price_vnd,
            "delivery_time": self.delivery_time,
            "description": self.description,
            "deliverables": self.deliverables,
        }


STANDARD_PACKAGES: Dict[str, Dict[str, Any]] = {
    "audit": {
        "tier": "audit",
        "title": "AI Agent Architecture & Automation Audit",
        "price_usd": 500.0,
        "delivery_time": "3 business days",
        "description": "Comprehensive evaluation of existing engineering pipelines and automation opportunities.",
        "deliverables": [
            "Codebase static AST boundary and vendor SDK audit",
            "Agent opportunity matrix & ROI impact projections",
            "Security posture & token budget compliance report",
            "Executive recommendation deck with implementation roadmap",
        ],
    },
    "custom_agent": {
        "tier": "custom_agent",
        "title": "Custom Domain Subagent Build",
        "price_usd": 2000.0,
        "delivery_time": "1 week",
        "description": "Bespoke production-grade autonomous agent tailored to company workflows.",
        "deliverables": [
            "Domain-specific subagent registry definition and system prompt",
            "Standard Operating Procedure (SOP) with acceptance gates",
            "Custom MCP tool integrations and data connectors",
            "Automated deterministic evaluation test battery",
            "Operational documentation and handoff walkthrough",
        ],
    },
    "full_stack": {
        "tier": "full_stack",
        "title": "Full Stack Agency OS Deployment",
        "price_usd": 5000.0,
        "delivery_time": "2 weeks",
        "description": "Complete multi-agent harness runtime configured and connected to production infrastructure.",
        "deliverables": [
            "Full 4-layer agent deployment (Business, Product, Engineering, Ops)",
            "Dual-streaming HTTP SSE & WebSocket event gateway",
            "Sliding-window token bucket rate limiter and tenant quota engine",
            "CI/CD regression battery and self-healing test automation",
            "Interactive Dash & TUI operations control center",
        ],
    },
    "retainer": {
        "tier": "retainer",
        "title": "Autonomous Operations Retainer",
        "price_usd": 2000.0,
        "delivery_time": "Ongoing (Monthly)",
        "description": "Continuous agent optimization, prompt engineering, model upgrades, and SLA support.",
        "deliverables": [
            "Priority incident response & agent debugging (4-hour SLA)",
            "Continuous model migrations and prompt fine-tuning",
            "1 new specialized agent or workflow implementation per month",
            "Weekly performance telemetry & token efficiency reviews",
        ],
    },
}


class ProposalReport:
    """Synthesized client consulting proposal."""

    def __init__(
        self,
        prospect_name: str,
        service_tier: str,
        title: str,
        price_usd: float,
        price_vnd: int,
        delivery_time: str,
        requirements: str,
        scope: List[str],
        milestones: List[Dict[str, str]],
        markdown_proposal: str,
        proposal_file: Optional[str] = None,
    ) -> None:
        self.prospect_name = prospect_name
        self.service_tier = service_tier
        self.title = title
        self.price_usd = price_usd
        self.price_vnd = price_vnd
        self.delivery_time = delivery_time
        self.requirements = requirements
        self.scope = scope
        self.milestones = milestones
        self.markdown_proposal = markdown_proposal
        self.proposal_file = proposal_file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prospect_name": self.prospect_name,
            "service_tier": self.service_tier,
            "title": self.title,
            "price_usd": self.price_usd,
            "price_vnd": self.price_vnd,
            "delivery_time": self.delivery_time,
            "requirements": self.requirements,
            "scope": self.scope,
            "milestones": self.milestones,
            "markdown_proposal": self.markdown_proposal,
            "proposal_file": self.proposal_file,
        }


class OutreachTemplate:
    """Multi-channel B2B consulting outreach copy."""

    def __init__(
        self,
        prospect_name: str,
        role: str,
        service_tier: str,
        subject: str,
        email_body: str,
        linkedin_body: str,
        zalo_body: str,
    ) -> None:
        self.prospect_name = prospect_name
        self.role = role
        self.service_tier = service_tier
        self.subject = subject
        self.email_body = email_body
        self.linkedin_body = linkedin_body
        self.zalo_body = zalo_body

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prospect_name": self.prospect_name,
            "role": self.role,
            "service_tier": self.service_tier,
            "subject": self.subject,
            "email_body": self.email_body,
            "linkedin_body": self.linkedin_body,
            "zalo_body": self.zalo_body,
        }


class EngagementRecord:
    """Tracked client engagement contract."""

    def __init__(
        self,
        id: str,
        client_name: str,
        service_tier: str,
        price_usd: float,
        status: str,  # PROPOSED, ACTIVE, DELIVERED, COMPLETED
        start_date: str,
        notes: str = "",
        created_at: str = "",
    ) -> None:
        self.id = id
        self.client_name = client_name
        self.service_tier = service_tier
        self.price_usd = price_usd
        self.status = status.upper()
        self.start_date = start_date
        self.notes = notes
        self.created_at = created_at or datetime.datetime.now(datetime.timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "client_name": self.client_name,
            "service_tier": self.service_tier,
            "price_usd": self.price_usd,
            "status": self.status,
            "start_date": self.start_date,
            "notes": self.notes,
            "created_at": self.created_at,
        }


class ConsultingEngine:
    """Autonomous AI Agent Consulting & Advisory Engine."""

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
            self.db_path = mekong_dir / "consulting.db"

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        """Initialize tables for client engagements and generated proposals."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS engagements (
                    id TEXT PRIMARY KEY,
                    client_name TEXT NOT NULL,
                    service_tier TEXT NOT NULL,
                    price_usd REAL NOT NULL,
                    status TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    notes TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    prospect_name TEXT NOT NULL,
                    service_tier TEXT NOT NULL,
                    price_usd REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    file_path TEXT
                )
                """
            )
            conn.commit()

    def get_service_catalog(self, currency: str = "USD") -> List[ConsultingPackage]:
        """Retrieve standardized consulting packages in specified currency."""
        packages: List[ConsultingPackage] = []
        for tier, data in STANDARD_PACKAGES.items():
            price_usd = data["price_usd"]
            price_vnd = int(price_usd * VND_PER_USD)
            packages.append(
                ConsultingPackage(
                    tier=tier,
                    title=data["title"],
                    price_usd=price_usd,
                    price_vnd=price_vnd,
                    delivery_time=data["delivery_time"],
                    description=data["description"],
                    deliverables=list(data["deliverables"]),
                )
            )
        return packages

    def generate_proposal(
        self,
        prospect_name: str,
        service_tier: str = "custom_agent",
        requirements: str = "",
        industry: str = "Technology",
        budget: Optional[float] = None,
        save_report: bool = False,
        output_dir: Optional[Path] = None,
    ) -> ProposalReport:
        """Synthesize tailored client engagement proposal."""
        tier = service_tier.lower()
        if tier not in STANDARD_PACKAGES:
            tier = "custom_agent"

        pkg = STANDARD_PACKAGES[tier]
        price_usd = budget if budget is not None else pkg["price_usd"]
        price_vnd = int(price_usd * VND_PER_USD)
        delivery_time = pkg["delivery_time"]
        req_text = requirements or f"Deploy production AI agentic infrastructure tailored to {industry} operations."

        milestones = [
            {"phase": "Phase 1: Architecture & Scoping", "timeline": "Day 1-2", "output": "Technical spec & SOP definition"},
            {"phase": "Phase 2: Agent Implementation", "timeline": "Day 3-5", "output": "Core engine, tools & boundary tests"},
            {"phase": "Phase 3: Verification & Handoff", "timeline": "Day 6-7", "output": "Eval benchmark run & operator training"},
        ]

        md_content = f"""# AI Agent Consulting Proposal: {prospect_name}

**Target Offering**: `{pkg['title']}`
**Investment**: **${price_usd:,.2f} USD** (~{price_vnd:,.0f} VND) | **Timeline**: `{delivery_time}`
**Prepared By**: MekongMind Agency OS Solutions Group
**Date**: {datetime.datetime.now(datetime.timezone.utc).strftime('%B %d, %Y')}

---

## 1. Executive Summary & Objective
{prospect_name} is partnering with MekongMind to accelerate operational velocity through deterministic agentic harness engineering.
Primary focus: {req_text}

## 2. Scope of Deliverables
"""
        for d in pkg["deliverables"]:
            md_content += f"- ✅ **{d}**\n"

        md_content += """
## 3. Implementation Milestones
| Milestone | Timeline | Key Deliverable |
|---|---|---|
"""
        for m in milestones:
            md_content += f"| {m['phase']} | {m['timeline']} | {m['output']} |\n"

        md_content += f"""
## 4. Investment & Commercial Terms
- **Contract Price**: ${price_usd:,.2f} USD
- **Payment Structure**: 50% upon project kickoff, 50% upon final acceptance criteria validation.
- **Warranty**: 30 days post-launch warranty and bug fixes included.

## 5. Next Steps
1. Sign engagement agreement and designate technical liaison.
2. Schedule Day 1 kickoff and environment provisioning.
"""

        proposal_file: Optional[str] = None
        if save_report:
            p_dir = output_dir or (self.project_root / "proposals")
            p_dir.mkdir(parents=True, exist_ok=True)
            slug = prospect_name.lower().replace(" ", "_")
            dest = p_dir / f"proposal_{slug}_{tier}.md"
            dest.write_text(md_content, encoding="utf-8")
            proposal_file = str(dest)

        # Record in database
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO proposals (id, prospect_name, service_tier, price_usd, created_at, file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()),
                        prospect_name,
                        tier,
                        price_usd,
                        datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        proposal_file,
                    ),
                )
                conn.commit()
        except Exception:
            pass

        return ProposalReport(
            prospect_name=prospect_name,
            service_tier=tier,
            title=pkg["title"],
            price_usd=price_usd,
            price_vnd=price_vnd,
            delivery_time=delivery_time,
            requirements=req_text,
            scope=pkg["deliverables"],
            milestones=milestones,
            markdown_proposal=md_content,
            proposal_file=proposal_file,
        )

    def create_engagement(
        self,
        client_name: str,
        service_tier: str = "custom_agent",
        price_usd: float = 2000.0,
        start_date: Optional[str] = None,
        notes: str = "",
    ) -> EngagementRecord:
        """Create and track a client consulting engagement."""
        tier = service_tier.lower()
        if tier not in STANDARD_PACKAGES:
            tier = "custom_agent"

        eng_id = f"ENG-{uuid.uuid4().hex[:8].upper()}"
        st_date = start_date or datetime.date.today().isoformat()
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        status = "ACTIVE"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO engagements (id, client_name, service_tier, price_usd, status, start_date, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (eng_id, client_name, tier, price_usd, status, st_date, notes, ts),
            )
            conn.commit()

        return EngagementRecord(
            id=eng_id,
            client_name=client_name,
            service_tier=tier,
            price_usd=price_usd,
            status=status,
            start_date=st_date,
            notes=notes,
            created_at=ts,
        )

    def list_engagements(self, status: str = "ALL") -> List[EngagementRecord]:
        """List tracked consulting contracts filtered by status."""
        query = "SELECT * FROM engagements WHERE 1=1"
        params: List[Any] = []
        if status.upper() != "ALL":
            query += " AND status = ?"
            params.append(status.upper())
        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [
            EngagementRecord(
                id=r["id"],
                client_name=r["client_name"],
                service_tier=r["service_tier"],
                price_usd=r["price_usd"],
                status=r["status"],
                start_date=r["start_date"],
                notes=r["notes"] or "",
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def get_engagement(self, engagement_id: str) -> Optional[EngagementRecord]:
        """Retrieve a specific engagement contract by ID."""
        with self._get_connection() as conn:
            r = conn.execute("SELECT * FROM engagements WHERE id = ?", (engagement_id,)).fetchone()
            if not r:
                return None
            return EngagementRecord(
                id=r["id"],
                client_name=r["client_name"],
                service_tier=r["service_tier"],
                price_usd=r["price_usd"],
                status=r["status"],
                start_date=r["start_date"],
                notes=r["notes"] or "",
                created_at=r["created_at"],
            )

    def update_engagement(
        self,
        engagement_id: str,
        status: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Optional[EngagementRecord]:
        """Update status or notes for an engagement."""
        eng = self.get_engagement(engagement_id)
        if not eng:
            return None

        new_status = status.upper() if status else eng.status
        new_notes = notes if notes is not None else eng.notes

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE engagements
                SET status = ?, notes = ?
                WHERE id = ?
                """,
                (new_status, new_notes, engagement_id),
            )
            conn.commit()

        return self.get_engagement(engagement_id)

    def generate_outreach(
        self,
        prospect_name: str,
        service_tier: str = "custom_agent",
        role: str = "CTO",
    ) -> OutreachTemplate:
        """Synthesize tailored multi-channel B2B outreach templates."""
        tier = service_tier.lower()
        if tier not in STANDARD_PACKAGES:
            tier = "custom_agent"
        pkg = STANDARD_PACKAGES[tier]

        subject = f"Autonomous AI Agent Architecture for {prospect_name}"
        email_body = f"""Hi {prospect_name} Team,

I've been following your engineering milestones and noticed opportunities to accelerate feature delivery using deterministic AI agent harnesses.

At MekongMind, we specialize in building enterprise-grade autonomous agents on our RaaS platform. For teams like yours, our {pkg['title']} package ({pkg['delivery_time']}) provides:
• {pkg['deliverables'][0]}
• {pkg['deliverables'][1]}
• Zero vendor lock-in with standard-library deterministic runtime

Would you be open to a 15-minute architecture briefing this Thursday?

Best regards,
Mekong Advisory Solutions
"""

        linkedin_body = f"""Hi {role} at {prospect_name}, saw your latest updates. We build deterministic agentic pipelines for engineering teams — typically reducing implementation cycles by 40%. Happy to share a quick 1-page architecture audit if you're interested."""

        zalo_body = f"""Chào team {prospect_name}, MekongMind cung cấp giải pháp triển khai AI Agent chuyên nghiệp ({pkg['title']}, bàn giao trong {pkg['delivery_time']}). Mời anh/chị tham khảo quy trình tự động hóa tại mekongmind.com."""

        return OutreachTemplate(
            prospect_name=prospect_name,
            role=role,
            service_tier=tier,
            subject=subject,
            email_body=email_body,
            linkedin_body=linkedin_body,
            zalo_body=zalo_body,
        )

    def get_status(self) -> Dict[str, Any]:
        """Executive consulting pipeline status summary."""
        engs = self.list_engagements()
        active = [e for e in engs if e.status in {"ACTIVE", "PROPOSED"}]
        completed = [e for e in engs if e.status in {"DELIVERED", "COMPLETED"}]
        pipeline_usd = sum(e.price_usd for e in active)
        realized_usd = sum(e.price_usd for e in completed)

        return {
            "total_engagements": len(engs),
            "active_engagements": len(active),
            "completed_engagements": len(completed),
            "pipeline_value_usd": pipeline_usd,
            "realized_revenue_usd": realized_usd,
            "standard_offerings": list(STANDARD_PACKAGES.keys()),
        }


_default_engine: Optional[ConsultingEngine] = None


def get_consulting_engine(db_path: Optional[Path] = None, project_root: Optional[Path] = None) -> ConsultingEngine:
    """Singleton getter for ConsultingEngine."""
    global _default_engine
    if db_path is not None or project_root is not None:
        return ConsultingEngine(db_path=db_path, project_root=project_root)
    if _default_engine is None:
        _default_engine = ConsultingEngine()
    return _default_engine
