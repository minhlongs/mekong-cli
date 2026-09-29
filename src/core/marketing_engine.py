# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/core/marketing_engine.py — Autonomous Marketing, Content Engine & Growth Campaign Suite.

Manages marketing campaigns, multi-channel content generation, SEO keyword gap analysis,
growth A/B experiment design, and universal bootstrap marketing strategies.
Backed by persistent SQLite storage in `.mekong/marketing.db`.

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


class CampaignStatus(str, Enum):
    """Canonical campaign states."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CampaignChannel(str, Enum):
    """Supported promotional and marketing channels."""

    SOCIAL = "social"
    SEARCH = "search"
    CONTENT = "content"
    EMAIL = "email"
    LOCAL = "local"
    ZALO = "zalo"


@dataclass
class CampaignRecord:
    """Individual marketing campaign record in the ledger."""

    id: str
    name: str
    channel: str
    budget: float
    status: str
    target_audience: str
    impressions: int
    conversions: int
    created_at: str
    updated_at: str

    @property
    def cpa(self) -> float:
        """Cost per acquisition (conversion)."""
        if self.conversions > 0:
            return round(self.budget / self.conversions, 2)
        return 0.0

    @property
    def conversion_rate(self) -> float:
        """Conversion rate percentage."""
        if self.impressions > 0:
            return round((self.conversions / self.impressions) * 100.0, 2)
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "channel": self.channel,
            "budget": self.budget,
            "status": self.status,
            "target_audience": self.target_audience,
            "impressions": self.impressions,
            "conversions": self.conversions,
            "cpa": self.cpa,
            "conversion_rate": self.conversion_rate,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ContentItem:
    """Synthesized, publish-ready marketing copy."""

    id: str
    topic: str
    channel: str
    content_type: str
    headline: str
    body: str
    hashtags: list[str]
    call_to_action: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SeoAuditReport:
    """Technical SEO keyword recommendations and content gap analysis."""

    keyword: str
    domain: str
    recommended_title: str
    recommended_meta_description: str
    target_keyword_density: str
    heading_structure: list[str]
    content_gap_topics: list[str]
    backlink_opportunities: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GrowthExperiment:
    """Structured growth experiment framework."""

    id: str
    hypothesis: str
    target_metric: str
    target_lift: str
    sample_size_per_variant: int
    duration_days: int
    variant_a: str
    variant_b: str
    decision_rule: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MarketingMetrics:
    """Consolidated marketing performance metrics across all campaigns."""

    total_campaigns: int
    active_campaigns: int
    total_budget: float
    total_impressions: int
    total_conversions: int
    blended_cpa: float
    campaigns_by_channel: dict[str, int]
    top_campaigns: list[CampaignRecord]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_campaigns": self.total_campaigns,
            "active_campaigns": self.active_campaigns,
            "total_budget": round(self.total_budget, 2),
            "total_impressions": self.total_impressions,
            "total_conversions": self.total_conversions,
            "blended_cpa": round(self.blended_cpa, 2),
            "campaigns_by_channel": self.campaigns_by_channel,
            "top_campaigns": [c.to_dict() for c in self.top_campaigns],
        }


@dataclass
class MarketingPlan:
    """Complete bootstrap marketing strategy and 30-day editorial schedule."""

    business_name: str
    industry: str
    strategy_summary: str
    channel_mix: dict[str, str]
    content_calendar_30d: list[dict[str, str]]
    key_kpis: dict[str, str]
    exported_path: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MarketingEngine:
    """Autonomous marketing campaign ledger, content engine, and growth lab."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path:
            self.db_path = Path(db_path)
        else:
            mekong_dir = Path(os.getcwd()) / ".mekong"
            mekong_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = mekong_dir / "marketing.db"

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
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    budget REAL NOT NULL,
                    status TEXT NOT NULL,
                    target_audience TEXT,
                    impressions INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_items (
                    id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    body TEXT NOT NULL,
                    hashtags TEXT,
                    call_to_action TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    # -------------------------------------------------------------------------
    # Campaign Management
    # -------------------------------------------------------------------------
    def create_campaign(
        self,
        name: str,
        channel: str = "social",
        budget: float = 1000.0,
        target_audience: str = "Tech Founders & Engineers",
        status: str = "active",
    ) -> CampaignRecord:
        """Create and register a marketing campaign."""
        cid = f"camp_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        valid_channel = channel.lower() if channel.lower() in [c.value for c in CampaignChannel] else CampaignChannel.SOCIAL.value
        valid_status = status.lower() if status.lower() in [s.value for s in CampaignStatus] else CampaignStatus.ACTIVE.value

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO campaigns (id, name, channel, budget, status, target_audience, impressions, conversions, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)
                """,
                (cid, name, valid_channel, float(budget), valid_status, target_audience, now, now),
            )
            conn.commit()

        return CampaignRecord(
            id=cid,
            name=name,
            channel=valid_channel,
            budget=float(budget),
            status=valid_status,
            target_audience=target_audience,
            impressions=0,
            conversions=0,
            created_at=now,
            updated_at=now,
        )

    def update_campaign(
        self,
        campaign_id: str,
        status: Optional[str] = None,
        budget: Optional[float] = None,
        impressions: Optional[int] = None,
        conversions: Optional[int] = None,
    ) -> Optional[CampaignRecord]:
        """Update campaign status, budget, or performance metrics."""
        existing = self.get_campaign(campaign_id)
        if not existing:
            return None

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_status = status.lower() if status and status.lower() in [s.value for s in CampaignStatus] else existing.status
        new_budget = float(budget) if budget is not None else existing.budget
        new_impressions = int(impressions) if impressions is not None else existing.impressions
        new_conversions = int(conversions) if conversions is not None else existing.conversions

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE campaigns
                SET status = ?, budget = ?, impressions = ?, conversions = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_status, new_budget, new_impressions, new_conversions, now, campaign_id),
            )
            conn.commit()

        return self.get_campaign(campaign_id)

    def get_campaign(self, campaign_id: str) -> Optional[CampaignRecord]:
        """Retrieve a campaign by ID."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
            if not row:
                return None
            return CampaignRecord(
                id=row["id"],
                name=row["name"],
                channel=row["channel"],
                budget=float(row["budget"]),
                status=row["status"],
                target_audience=row["target_audience"] or "",
                impressions=int(row["impressions"]),
                conversions=int(row["conversions"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def list_campaigns(
        self,
        status: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> list[CampaignRecord]:
        """List campaigns with optional status and channel filters."""
        query = "SELECT * FROM campaigns WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status.lower())
        if channel:
            query += " AND channel = ?"
            params.append(channel.lower())

        query += " ORDER BY budget DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [
                CampaignRecord(
                    id=r["id"],
                    name=r["name"],
                    channel=r["channel"],
                    budget=float(r["budget"]),
                    status=r["status"],
                    target_audience=r["target_audience"] or "",
                    impressions=int(r["impressions"]),
                    conversions=int(r["conversions"]),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
                for r in rows
            ]

    def get_marketing_metrics(self) -> MarketingMetrics:
        """Calculate consolidated marketing performance analytics."""
        campaigns = self.list_campaigns()
        total_count = len(campaigns)
        active_count = sum(1 for c in campaigns if c.status == CampaignStatus.ACTIVE.value)
        total_budget = sum(c.budget for c in campaigns)
        total_impressions = sum(c.impressions for c in campaigns)
        total_conversions = sum(c.conversions for c in campaigns)

        blended_cpa = (total_budget / total_conversions) if total_conversions > 0 else 0.0

        by_channel: dict[str, int] = {ch.value: 0 for ch in CampaignChannel}
        for c in campaigns:
            by_channel[c.channel] = by_channel.get(c.channel, 0) + 1

        top_campaigns = sorted(campaigns, key=lambda x: x.conversions, reverse=True)[:5]

        return MarketingMetrics(
            total_campaigns=total_count,
            active_campaigns=active_count,
            total_budget=total_budget,
            total_impressions=total_impressions,
            total_conversions=total_conversions,
            blended_cpa=blended_cpa,
            campaigns_by_channel=by_channel,
            top_campaigns=top_campaigns,
        )

    # -------------------------------------------------------------------------
    # Content Engine
    # -------------------------------------------------------------------------
    def generate_content(
        self,
        topic: str,
        channel: str = "social",
        content_type: str = "post",
    ) -> ContentItem:
        """Synthesize ready-to-use marketing copy and creative."""
        t = topic.strip() or "Autonomous AI Harness Engineering"
        ch = channel.lower()
        cid = f"cnt_{uuid.uuid4().hex[:8]}"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if ch == "linkedin":
            headline = f"Why Engineering Teams Are Rethinking Workflows for {t}"
            body = (
                f"Modern software velocity isn't limited by how fast we write code—it's bottlenecked "
                f"by context loss, fragmented tooling, and manual deployment checklists.\n\n"
                f"When addressing {t}, high-performing teams apply deterministic harness engineering: "
                "verifiable plans, automated pre-flight gates, and rollback-ready checkpoints.\n\n"
                "Here are 3 lessons from running autonomous agent swarms in production:\n"
                "1. Treat specs as executable contracts, not documentation.\n"
                "2. Standard-library boundaries minimize dependency debt.\n"
                "3. Continuous observability turns flaky steps into deterministic self-healing.\n\n"
                "How is your team approaching automation this quarter?"
            )
            hashtags = ["#EngineeringVelocity", "#DevOps", "#AIAutomation", "#HarnessEngineering"]
            cta = "Drop your thoughts below or reach out to see the benchmark comparison."

        elif ch == "zalo":
            headline = f"Giải Pháp Đột Phá: Tự Động Hóa Với {t}"
            body = (
                f"Kính gửi Quý Doanh Nghiệp,\n\n"
                f"Trong bối cảnh tối ưu chi phí và tăng tốc độ vận hành, việc áp dụng công nghệ vào {t} "
                "đang giúp các doanh nghiệp Việt Nam cắt giảm 70% thời gian xử lý thủ công.\n\n"
                "Mekong CLI mang đến nền tảng AI Agentic chuẩn Binh Pháp:\n"
                "✓ Tích hợp hóa đơn điện tử TT78 và chuẩn kế toán VAS\n"
                "✓ Quy trình kiểm thử và triển khai tự động an toàn 100%\n"
                "✓ Báo cáo điều hành thông minh gửi trực tiếp qua Zalo OA\n\n"
                "Đăng ký trải nghiệm demo trực tiếp ngay hôm nay!"
            )
            hashtags = ["#MekongCLI", "#ChuyenDoiSo", "#TuDongHoa", "#DoanhNghiepViet"]
            cta = "Nhắn tin qua Zalo OA để nhận tài liệu tư vấn miễn phí."

        elif ch in ("blog", "content"):
            headline = f"The Comprehensive Guide to {t}: Architecture & Strategy"
            body = (
                f"# Mastering {t} with Deterministic Harness Engineering\n\n"
                f"As organizations scale, engineering complexity compounds exponentially. Implementing {t} "
                "requires moving beyond prompt wrappers to robust system architectures.\n\n"
                "## 1. The Core Architecture\n"
                "A resilient agent harness consists of 3 foundational layers: a declarative specification engine, "
                "an immutable state ledger, and an automated verification gate.\n\n"
                "## 2. Eliminating Fragility with Standard Library Invariants\n"
                "By constraining runtime components to the Python standard library, teams avoid dependency drift "
                "and ensure sub-second startup times across any containerized or edge environment.\n\n"
                "## 3. Production Deployment & Verification\n"
                "Zero-defect delivery is achieved through deterministic test batteries and automated rollbacks."
            )
            hashtags = ["#SoftwareEngineering", "#Architecture", "#Automation", "#BestPractices"]
            cta = "Read the complete documentation and start the 5-step quickstart."

        else:  # social / facebook / x
            headline = f"🚀 Supercharge your workflow with {t}"
            body = (
                f"Tired of manual bottlenecks in {t}?\n\n"
                "Meet Mekong CLI: the autonomous harness engineering platform built for reliability.\n\n"
                "⚡ 100% test-backed execution\n"
                "🛡️ Built-in rollback and safe autonomy\n"
                "📊 Real-time pipeline metrics\n\n"
                "Stop wrestling with boilerplate and start shipping with confidence."
            )
            hashtags = ["#TechInnovation", "#BuildInPublic", "#Developers", "#MekongCLI"]
            cta = "Get started in 5 minutes with `mekong quick-start`."

        item = ContentItem(
            id=cid,
            topic=t,
            channel=ch,
            content_type=content_type,
            headline=headline,
            body=body,
            hashtags=hashtags,
            call_to_action=cta,
            created_at=now,
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO content_items (id, topic, channel, content_type, headline, body, hashtags, call_to_action, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item.id, item.topic, item.channel, item.content_type, item.headline, item.body, json.dumps(item.hashtags), item.call_to_action, item.created_at),
            )
            conn.commit()

        return item

    # -------------------------------------------------------------------------
    # SEO & Keyword Gap Analysis
    # -------------------------------------------------------------------------
    def generate_seo_audit(self, keyword: str, domain: str = "") -> SeoAuditReport:
        """Generate SEO recommendations, on-page checklist, and keyword gap analysis."""
        kw = keyword.strip() or "agentic harness engineering"
        dom = domain.strip() or "mekongcli.dev"

        title = f"{kw.title()} — Complete Architectural Guide | {dom}"
        meta_desc = (
            f"Learn how to build and scale {kw} with deterministic harnesses, automated testing, "
            f"and zero vendor lock-in. Explore production blueprints and benchmarks on {dom}."
        )

        headings = [
            f"H1: What is {kw.title()} and Why Does It Matter?",
            "H2: Key Architecture Principles: Plan, Execute, Verify",
            "H2: Avoiding Common Pitfalls & Context Fragmentation",
            "H2: Benchmarks, Latency, and Cost Optimization",
            "H3: Step-by-Step Implementation Guide",
            "H3: Production Readiness Checklist",
        ]

        gaps = [
            f"{kw} vs traditional CI/CD pipelines",
            f"Open-source alternatives for {kw}",
            f"Security and governance compliance for {kw}",
            f"Real-world enterprise case studies and ROI figures",
        ]

        backlinks = [
            "GitHub awesome-lists (awesome-ai, awesome-harness-engineering)",
            "Hacker News Show HN launch post",
            "Dev.to technical deep-dive tutorial series",
            "Vietnamese Tech Communities (Groovin Technology, Tinh Tế, Vietnam AI Hub)",
        ]

        return SeoAuditReport(
            keyword=kw,
            domain=dom,
            recommended_title=title,
            recommended_meta_description=meta_desc,
            target_keyword_density="1.5% - 2.5%",
            heading_structure=headings,
            content_gap_topics=gaps,
            backlink_opportunities=backlinks,
        )

    # -------------------------------------------------------------------------
    # Growth Experimentation Lab
    # -------------------------------------------------------------------------
    def create_growth_experiment(
        self,
        hypothesis: str,
        target_metric: str = "Signup Conversion Rate",
        target_lift: str = "+25%",
    ) -> GrowthExperiment:
        """Formulate a scientifically structured growth experiment."""
        eid = f"exp_{uuid.uuid4().hex[:8]}"
        hyp = hypothesis.strip() or "Adding interactive terminal previews will increase trial signups"

        return GrowthExperiment(
            id=eid,
            hypothesis=hyp,
            target_metric=target_metric,
            target_lift=target_lift,
            sample_size_per_variant=1200,
            duration_days=14,
            variant_a="Control: Static feature bullet points with CTA button",
            variant_b="Variant: Embedded interactive Rich terminal recording demonstrating 5-step quickstart",
            decision_rule="Adopt Variant B if p-value < 0.05 and observed lift >= 15% with zero degradation in retention.",
        )

    # -------------------------------------------------------------------------
    # Universal Marketing Bootstrap Wizard
    # -------------------------------------------------------------------------
    def bootstrap_plan(
        self,
        business_name: str,
        industry: str = "B2B SaaS",
        export: bool = True,
    ) -> MarketingPlan:
        """Generate a complete 30-day marketing plan and editorial schedule."""
        bname = business_name.strip() or "Mekong Venture"
        ind = industry.strip() or "AI Platform"

        mix = {
            "Content & SEO": "40% budget — High-intent technical articles and architectural blueprints",
            "Social & Community": "30% budget — LinkedIn thought leadership and technical community outreach",
            "Paid & Search Ads": "20% budget — Targeted Google/LinkedIn search for developer keywords",
            "Direct Outreach / Zalo": "10% budget — Direct messaging and personalized executive demos",
        }

        calendar = [
            {"day": "Day 1", "platform": "Blog", "action": f"Publish cornerstone announcement: Introducing {bname}"},
            {"day": "Day 3", "platform": "LinkedIn", "action": "Share founder narrative and technical problem statement"},
            {"day": "Day 7", "platform": "Zalo / Email", "action": "Send first bi-weekly customer newsletter with benchmark ROI"},
            {"day": "Day 12", "platform": "Social", "action": "Post interactive code snippet and developer showcase"},
            {"day": "Day 18", "platform": "Blog", "action": "Deep-dive case study with customer success metrics"},
            {"day": "Day 24", "platform": "LinkedIn", "action": "Host virtual AMA / Technical Walkthrough"},
            {"day": "Day 30", "platform": "Review", "action": "Review CAC, conversions, and reallocate budget to top channels"},
        ]

        kpis = {
            "Month 1 Target Leads": "100 qualified prospects",
            "Blended CAC Target": "< $45.00 per activation",
            "Organic Traffic Growth": "+40% MoM",
            "Trial-to-Paid Conversion": ">= 18%",
        }

        plan = MarketingPlan(
            business_name=bname,
            industry=ind,
            strategy_summary=f"High-velocity inbound and technical proof-of-work marketing engine tailored for {bname} ({ind}).",
            channel_mix=mix,
            content_calendar_30d=calendar,
            key_kpis=kpis,
        )

        if export:
            out_dir = Path(os.getcwd()) / "plans" / "marketing"
            out_dir.mkdir(parents=True, exist_ok=True)
            export_file = out_dir / "MARKETING_STRATEGY.md"
            md_lines = [
                f"# Marketing Strategy & Growth Blueprint: {bname}",
                f"**Industry:** {ind}  ",
                f"**Generated:** {datetime.date.today().strftime('%Y-%m-%d')}\n",
                "## 1. Executive Strategy",
                plan.strategy_summary,
                "\n## 2. Channel Allocation",
            ]
            for ch, desc in mix.items():
                md_lines.append(f"- **{ch}:** {desc}")
            md_lines.append("\n## 3. 30-Day Editorial Calendar")
            for item in calendar:
                md_lines.append(f"- **{item['day']} ({item['platform']}):** {item['action']}")
            md_lines.append("\n## 4. Key Performance Indicators (KPIs)")
            for k, v in kpis.items():
                md_lines.append(f"- **{k}:** `{v}`")

            export_file.write_text("\n".join(md_lines), encoding="utf-8")
            plan.exported_path = str(export_file)

        return plan


def get_marketing_engine(db_path: str | Path | None = None) -> MarketingEngine:
    """Factory helper returning MarketingEngine instance."""
    return MarketingEngine(db_path=db_path)
