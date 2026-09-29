# Mekong CLI — Pure Standard-Library Content Marketing & Publishing Engine
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Content marketing and editorial publishing engine for Mekong CLI.

Provides multi-pillar content generation, structured format templates (blog, twitter,
linkedin, youtube script, newsletter), persistent editorial calendar tracking, channel
telemetry, and publication lifecycle workflows.
Enforces strict standard-library-only execution with zero vendor SDKs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

CONTENT_PILLARS: Dict[str, Dict[str, Any]] = {
    "one-person-company": {
        "name": "One-Person Company",
        "description": "Solo founder scaling, automation, AI leverage & lean operations",
        "frequency": "Weekly",
        "target_channels": ["blog", "indiehackers", "twitter"],
        "default_topics": [
            "How 1 Developer Out-builds an Agency with AI Swarms",
            "The Solo Founder's 10x Automation Stack",
            "Zero to $10k MRR without Hiring: The Autonomous Operator Guide",
        ],
    },
    "ai-agents": {
        "name": "AI Agents in Practice",
        "description": "Agent harness engineering, PEV execution, memory mesh & resilience",
        "frequency": "Weekly",
        "target_channels": ["blog", "twitter", "youtube"],
        "default_topics": [
            "Harness Engineering vs Prompt Engineering: Building Reliable AI",
            "Plan-Execute-Verify: Why Loops Fail and How to Checkpoint State",
            "Inside Mekong CLI: Building a Provider-Neutral AI Agent Architecture",
        ],
    },
    "solo-founder": {
        "name": "Solo Founder Life",
        "description": "Transparent bootstrapping, mental models, discipline & product-market fit",
        "frequency": "Biweekly",
        "target_channels": ["twitter", "indiehackers", "substack"],
        "default_topics": [
            "The Solopreneur Operating System: Daily Routines & Sprints",
            "Building in Public: Lessons from 100 Consecutive Production Deployments",
            "Mental Resilience for Solo Founders Facing Churn & Bugs",
        ],
    },
    "binh-phap": {
        "name": "Binh Pháp for Business",
        "description": "Sun Tzu Art of War applied to software business, strategy & positioning",
        "frequency": "Monthly",
        "target_channels": ["blog", "twitter", "substack"],
        "default_topics": [
            "Binh Pháp Chapter 1: Evaluating Ground & Competitor Asymmetry",
            "Winning Without Fighting: The Art of Strategic Niche Domination",
            "Chiến Tranh Nuôi Chiến Tranh: Self-Funding R&D from Customer Inflow",
        ],
    },
    "zenos": {
        "name": "ZenOS Philosophy",
        "description": "Decentralized organic commons, particle runtimes & autonomous governance",
        "frequency": "Monthly",
        "target_channels": ["blog", "indiehackers"],
        "default_topics": [
            "Beyond Monoliths: The Organic Architecture of ZenOS Particles",
            "Decentralized Governance for AI Agents: Ballots, Quorum & Charters",
            "The Right-to-Fork: True Sovereignty in Agent Ecosystems",
        ],
    },
}

SUPPORTED_FORMATS: List[str] = [
    "blog",
    "twitter",
    "linkedin",
    "youtube_script",
    "newsletter",
]

DEFAULT_CHANNELS: List[Dict[str, Any]] = [
    {"channel_id": "blog", "name": "Company Engineering Blog", "followers": 1250, "posts": 28},
    {"channel_id": "twitter", "name": "X / Twitter Community", "followers": 3400, "posts": 142},
    {"channel_id": "indiehackers", "name": "Indie Hackers Group", "followers": 890, "posts": 19},
    {"channel_id": "youtube", "name": "YouTube Tech Demos", "followers": 1560, "posts": 12},
    {"channel_id": "substack", "name": "Founder Dispatch Newsletter", "followers": 2100, "posts": 34},
    {"channel_id": "zalo", "name": "Zalo Official Account", "followers": 450, "posts": 16},
]


class ContentEngine:
    """Core Content Marketing, Publishing & Editorial Calendar Engine."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            base_dir = Path.cwd() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "content.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    pillar TEXT NOT NULL,
                    format TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    status TEXT NOT NULL,
                    body TEXT NOT NULL,
                    metadata_json TEXT,
                    scheduled_at TEXT,
                    published_at TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    followers INTEGER DEFAULT 0,
                    posts_published INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 4.2,
                    notes TEXT
                );
                """
            )
            # Seed default channels if empty
            cur = conn.execute("SELECT COUNT(*) FROM channels")
            if cur.fetchone()[0] == 0:
                for ch in DEFAULT_CHANNELS:
                    conn.execute(
                        """
                        INSERT INTO channels (channel_id, name, status, followers, posts_published, engagement_rate, notes)
                        VALUES (?, ?, 'active', ?, ?, 4.2, 'Default distribution channel')
                        """,
                        (ch["channel_id"], ch["name"], ch["followers"], ch["posts"]),
                    )
            conn.commit()

    @staticmethod
    def get_pillars() -> Dict[str, Any]:
        """Return registered content pillars with target channels and frequencies."""
        return CONTENT_PILLARS

    def generate_content(
        self,
        pillar: str,
        format_type: str = "blog",
        topic: str = "",
        channel: str = "",
    ) -> Dict[str, Any]:
        """Generate structured, ready-to-publish content for a specific pillar and format."""
        pillar_key = pillar.lower().strip()
        pillar_info = CONTENT_PILLARS.get(
            pillar_key,
            {
                "name": pillar.capitalize(),
                "description": "General technology & business operations",
                "target_channels": ["blog", "twitter"],
                "default_topics": [f"Deep Dive: {pillar}"],
            },
        )

        fmt = format_type.lower().strip()
        if fmt not in SUPPORTED_FORMATS:
            fmt = "blog"

        chosen_topic = topic.strip()
        if not chosen_topic:
            defaults = pillar_info.get("default_topics", ["Autonomous Systems"])
            chosen_topic = defaults[0]

        target_ch = channel.strip()
        if not target_ch:
            target_ch = pillar_info.get("target_channels", ["blog"])[0]

        title = f"{chosen_topic}"
        body, hook, cta, tags = self._render_format_template(
            pillar_name=pillar_info["name"],
            topic=chosen_topic,
            fmt=fmt,
            channel=target_ch,
        )

        content_id = f"cnt_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "hook": hook,
            "cta": cta,
            "tags": tags,
            "estimated_read_time": "3 min" if fmt == "blog" else "1 min",
            "word_count": len(body.split()),
        }

        return {
            "id": content_id,
            "title": title,
            "pillar": pillar_key,
            "format": fmt,
            "channel": target_ch,
            "status": "draft",
            "body": body,
            "metadata": metadata,
            "created_at": now,
        }

    def _render_format_template(
        self, pillar_name: str, topic: str, fmt: str, channel: str
    ) -> Tuple[str, str, str, List[str]]:
        """Synthesize format-tailored content with hook, body, and CTA."""
        tags = [f"#{pillar_name.replace(' ', '')}", "#AI", "#SoloFounder", "#MekongCLI"]

        if fmt == "twitter":
            hook = f"🧵 Most founders burn $200k/year on team overhead. Here is how to run the entire operation with AI agents:"
            body = (
                f"{hook}\n\n"
                f"1/5 🎯 Topic: {topic}\n"
                f"When you replace rigid handoffs with autonomous Plan-Execute-Verify loops, velocity increases 10x.\n\n"
                f"2/5 ⚡ Architecture beats raw LLM intelligence.\n"
                f"Instead of asking an LLM to do everything in one prompt, decouple tasks into specialized roles (Product, Dev, Ops).\n\n"
                f"3/5 🛡️ Invariant guardrails are non-negotiable.\n"
                f"Zero external vendor lock-in. Deterministic SQLite checkpoints. Auto-rollback when tests fail.\n\n"
                f"4/5 📊 Financial discipline:\n"
                f"Track MRR waterfalls and payment reconciliation automatically so you stay cashflow positive from day 1.\n\n"
                f"5/5 🚀 Want the full architectural playbook? Check out Mekong CLI."
            )
            cta = "Follow for daily engineering insights on building solo agentic startups."

        elif fmt == "linkedin":
            hook = f"The era of the 50-person early-stage engineering team is ending. Here is what comes next."
            body = (
                f"{hook}\n\n"
                f"We just published our deep-dive into: **{topic}** ({pillar_name}).\n\n"
                f"Key Takeaways for CTOs & Solopreneurs:\n"
                f"• **Single-Process Autonomy**: Local SQLite persistence with WAL mode out-performs bloated distributed microservices for lean teams.\n"
                f"• **Standard-Library Purity**: Zero unnecessary runtime dependencies means zero security CVE fire-drills.\n"
                f"• **Deterministic Recovery**: When an agent task fails, atomic state snapshots restore the system in <100ms.\n\n"
                f"Are you experimenting with autonomous AI harnesses in production yet?\n\n"
                f"Drop your thoughts below 👇"
            )
            cta = "Connect and share your thoughts on sovereign agent systems."

        elif fmt == "youtube_script":
            hook = f"[HOOK - 0:00]\nHey everyone! Today we're breaking down {topic} and showing you how to build it step-by-step."
            body = (
                f"{hook}\n\n"
                f"[INTRO - 0:30]\nWelcome back to the channel. In this video from our {pillar_name} series, we explore how modern developers run full-stack operations without technical debt.\n\n"
                f"[THE PROBLEM - 1:15]\nTraditional SaaS workflows break down when multiple AI agents hallucinate or lose execution context.\n\n"
                f"[THE SOLUTION & DEMO - 3:00]\nLet's open Mekong CLI and run `mekong cook` to see how the PEV engine handles automated planning, execution, and verification.\n\n"
                f"[KEY TAKEAWAYS - 6:30]\n1. Always checkpoint file states.\n2. Keep your core provider-neutral.\n3. Measure throughput with deterministic evals.\n\n"
                f"[OUTRO & CTA - 7:45]\nHit like, subscribe, and grab the open-source code linked in the description below!"
            )
            cta = "Subscribe for weekly fullstack agent tutorials."

        elif fmt == "newsletter":
            hook = f"Founder Dispatch: {topic}"
            body = (
                f"# {hook}\n\n"
                f"Hey Builders,\n\n"
                f"Welcome to this week's dispatch covering **{pillar_name}**.\n\n"
                f"### The Focus This Week: {topic}\n"
                f"Running a solo software company requires ruthless prioritization. In software development, that means shaping the environment around agents rather than endlessly tweaking prompts.\n\n"
                f"### 3 Insights You Can Use Today:\n"
                f"1. **Audit your dependencies**: How many external API keys are in your critical path?\n"
                f"2. **Automate your MRR waterfall**: Know your expansion vs churn rates before hiring.\n"
                f"3. **Run daily health sweeps**: Don't wait for users to report broken database connections.\n\n"
                f"Until next week,\n"
                f"— The Mekong Team"
            )
            cta = "Reply to this email with your biggest agent engineering roadblock."

        else:  # blog
            hook = f"In this article, we examine {topic} through the lens of {pillar_name} and explore production patterns for sovereign software systems."
            body = (
                f"# {topic}\n\n"
                f"*{pillar_name} Series | Published by Mekong CLI Engineering*\n\n"
                f"## Executive Summary\n"
                f"{hook}\n\n"
                f"## 1. The Core Architecture\n"
                f"Modern software engineering requires systems that self-heal, self-audit, and self-improve. By adopting a strict standard-library foundation and local-first SQLite persistence, developers eliminate external point-of-failure risks.\n\n"
                f"```bash\n"
                f"# Run autonomous verification\n"
                f"mekong dev audit --strict\n"
                f"mekong revenue metrics --period month\n"
                f"```\n\n"
                f"## 2. Practical Implementation Patterns\n"
                f"When designing agentic workflows for {pillar_name}, adhere to three primary constraints:\n"
                f"- **Context Engineering**: Observe budget caps per role to prevent prompt degradation.\n"
                f"- **Atomic Rollbacks**: Checkpoint disk states before executing high-risk mutations.\n"
                f"- **Bilingual Multi-Currency Support**: Support global markets with automatic USD/VND conversion.\n\n"
                f"## 3. Summary & Next Steps\n"
                f"Building high-leverage software is no longer about team size—it is about architectural purity and execution discipline.\n\n"
                f"Ready to deploy? Run `mekong quick-start` or check the official repository."
            )
            cta = "Read the full Mekong CLI documentation and join the solo founder community."

        return body, hook, cta, tags

    def save_content(
        self,
        content_item: Dict[str, Any],
        output_dir: Optional[Path] = None,
        save_file: bool = False,
    ) -> Dict[str, Any]:
        """Save a generated content item into SQLite database and optional markdown file."""
        cid = content_item["id"]
        title = content_item["title"]
        pillar = content_item["pillar"]
        fmt = content_item["format"]
        channel = content_item["channel"]
        status = content_item.get("status", "draft")
        body = content_item["body"]
        meta_json = json.dumps(content_item.get("metadata", {}))
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO content_items (
                    id, title, pillar, format, channel, status, body, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cid, title, pillar, fmt, channel, status, body, meta_json, now),
            )
            conn.commit()

        file_path = None
        if save_file:
            target_dir = output_dir or (Path.cwd() / "content" / pillar)
            target_dir.mkdir(parents=True, exist_ok=True)
            slug = re.sub(r"[^a-zA-Z0-9_\-]+", "_", title.lower())[:40]
            target_file = target_dir / f"{slug}_{fmt}.md"
            target_file.write_text(body, encoding="utf-8")
            file_path = str(target_file)

        res = dict(content_item)
        res["saved_to_db"] = True
        res["file_path"] = file_path
        return res

    def list_content(
        self,
        status: str = "all",
        pillar: str = "",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List content items filtered by status and pillar."""
        conditions = []
        params: List[Any] = []
        if status.lower() != "all":
            conditions.append("status = ?")
            params.append(status.lower())
        if pillar.strip():
            conditions.append("pillar = ?")
            params.append(pillar.lower().strip())

        query = "SELECT * FROM content_items"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cur = conn.execute(query, params)
            items = []
            for row in cur.fetchall():
                d = dict(row)
                if d.get("metadata_json"):
                    try:
                        d["metadata"] = json.loads(d["metadata_json"])
                    except Exception:
                        d["metadata"] = {}
                items.append(d)
            return items

    def update_status(
        self, content_id: str, new_status: str, channel: str = ""
    ) -> Dict[str, Any]:
        """Update content publication status (draft -> scheduled -> published)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM content_items WHERE id = ?", (content_id,)
            )
            row = cur.fetchone()
            if not row:
                return {
                    "success": False,
                    "error": f"Content item {content_id} not found",
                }

            published_at = row["published_at"]
            if new_status.lower() == "published" and not published_at:
                published_at = now

            conn.execute(
                """
                UPDATE content_items
                SET status = ?, published_at = ?
                WHERE id = ?
                """,
                (new_status.lower(), published_at, content_id),
            )

            # If published, bump posts_published on the channel
            target_ch = channel or row["channel"]
            conn.execute(
                """
                UPDATE channels
                SET posts_published = posts_published + 1
                WHERE channel_id = ?
                """,
                (target_ch,),
            )
            conn.commit()

        return {
            "success": True,
            "id": content_id,
            "status": new_status.lower(),
            "published_at": published_at,
            "channel": target_ch,
        }

    def get_calendar(self) -> Dict[str, Any]:
        """Calculate publication schedule, upcoming cadence, and pillar coverage."""
        all_items = self.list_content(limit=100)
        published_items = [i for i in all_items if i["status"] == "published"]
        scheduled_items = [i for i in all_items if i["status"] == "scheduled"]
        draft_items = [i for i in all_items if i["status"] == "draft"]

        pillar_summary: Dict[str, Dict[str, Any]] = {}
        now = datetime.now(timezone.utc)

        for p_key, p_info in CONTENT_PILLARS.items():
            p_published = [i for i in published_items if i["pillar"] == p_key]
            p_drafts = [i for i in draft_items if i["pillar"] == p_key]

            # Calculate next due date heuristic based on frequency
            freq = p_info["frequency"].lower()
            if "week" in freq:
                due = (now + timedelta(days=3)).strftime("%Y-%m-%d")
            elif "biweek" in freq:
                due = (now + timedelta(days=7)).strftime("%Y-%m-%d")
            else:
                due = (now + timedelta(days=14)).strftime("%Y-%m-%d")

            pillar_summary[p_key] = {
                "name": p_info["name"],
                "frequency": p_info["frequency"],
                "target_channels": p_info["target_channels"],
                "published_count": len(p_published),
                "drafts_count": len(p_drafts),
                "next_due_date": due,
            }

        return {
            "total_items": len(all_items),
            "published_count": len(published_items),
            "scheduled_count": len(scheduled_items),
            "drafts_count": len(draft_items),
            "pillars": pillar_summary,
            "recent_drafts": draft_items[:5],
            "upcoming_scheduled": scheduled_items[:5],
        }

    def get_channel_stats(self) -> List[Dict[str, Any]]:
        """Return distribution channel stats and audience reach."""
        with self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM channels ORDER BY followers DESC")
            return [dict(r) for r in cur.fetchall()]

    def get_status(self) -> Dict[str, Any]:
        """Return engine operational status and database metrics."""
        with self._get_connection() as conn:
            item_count = conn.execute(
                "SELECT COUNT(*) FROM content_items"
            ).fetchone()[0]
            pub_count = conn.execute(
                "SELECT COUNT(*) FROM content_items WHERE status = 'published'"
            ).fetchone()[0]
            ch_count = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[
                0
            ]

        return {
            "status": "HEALTHY",
            "db_path": str(self.db_path),
            "total_content_items": item_count,
            "published_items": pub_count,
            "active_channels": ch_count,
            "registered_pillars": len(CONTENT_PILLARS),
        }


_default_content_engine: Optional[ContentEngine] = None


def get_content_engine(db_path: Optional[Path] = None) -> ContentEngine:
    """Return the global ContentEngine singleton or a newly initialized instance."""
    global _default_content_engine
    if db_path is not None:
        return ContentEngine(db_path=db_path)
    if _default_content_engine is None:
        _default_content_engine = ContentEngine()
    return _default_content_engine
