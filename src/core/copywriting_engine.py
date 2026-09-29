# Mekong CLI — Pure Standard-Library Conversion Copywriting Engine
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Conversion copywriting and persuasion engine for Mekong CLI.

Provides proven direct-response formulas (PAS, AIDA, BAB, FAB, 4Us), landing page structural
frameworks, conversion email sequences, headline synthesis, and CTA optimization.
Enforces strict standard-library-only execution with zero vendor SDKs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

FORMULAS_CATALOG: Dict[str, Dict[str, Any]] = {
    "pas": {
        "name": "Problem - Agitation - Solution",
        "description": "Expose the painful problem, agitate the consequences, present the undeniable solution.",
        "best_for": "SaaS landing pages, cold emails, high-friction conversions",
        "steps": ["Problem", "Agitation", "Solution"],
    },
    "aida": {
        "name": "Attention - Interest - Desire - Action",
        "description": "Hook attention, build technical or commercial interest, fuel emotional desire, trigger immediate action.",
        "best_for": "Product launches, ad copy, sales pages",
        "steps": ["Attention", "Interest", "Desire", "Action"],
    },
    "bab": {
        "name": "Before - After - Bridge",
        "description": "Show the chaotic before-state, paint the dream after-state, and position your product as the bridge.",
        "best_for": "Case studies, social posts, onboarding emails",
        "steps": ["Before", "After", "Bridge"],
    },
    "fab": {
        "name": "Features - Advantages - Benefits",
        "description": "Translate architectural features into competitive advantages and high-value customer benefits.",
        "best_for": "Technical products, feature release announcements, documentation",
        "steps": ["Features", "Advantages", "Benefits"],
    },
    "4us": {
        "name": "Urgent - Unique - Useful - Ultra-specific",
        "description": "Score and craft copy that conveys immediate urgency, distinctive uniqueness, clear utility, and specificity.",
        "best_for": "Headlines, subject lines, notification microcopy",
        "steps": ["Urgent", "Unique", "Useful", "UltraSpecific"],
    },
}

STYLE_GUIDES: Dict[str, Dict[str, Any]] = {
    "direct_response": {
        "name": "Direct Response & High-Conversion",
        "tone": "Punchy, authoritative, benefit-first, crisp whitespace, zero fluff.",
        "rules": [
            "Use active voice and strong verbs.",
            "Break paragraphs every 1-2 sentences.",
            "Lead with quantifiable customer outcomes.",
        ],
    },
    "technical_founder": {
        "name": "Technical Founder / Pragmatic Engineer",
        "tone": "Substantive, no-nonsense, architecture-backed, honest tradeoffs.",
        "rules": [
            "Show code snippets or architectural facts.",
            "Avoid empty buzzwords like 'revolutionary' or 'disruptive'.",
            "Acknowledge edge cases and explain how the system handles them.",
        ],
    },
    "punchy_minimalist": {
        "name": "Punchy Minimalist",
        "tone": "Ultra-short sentences, bold statements, visceral clarity.",
        "rules": [
            "Keep sentences under 12 words.",
            "Use bullet points for readability.",
            "End with a single, clear, low-friction action.",
        ],
    },
    "storytelling": {
        "name": "Narrative Journey & Origin Story",
        "tone": "Vulnerable, authentic, relatable obstacle overcome.",
        "rules": [
            "Start in the middle of the conflict.",
            "Share the pivotal turning point.",
            "Invite the reader to share in the transformation.",
        ],
    },
}


class CopywritingEngine:
    """Core Conversion Copywriting & Persuasion Engine."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            base_dir = Path.cwd() / ".mekong"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "copywriting.db"
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
                CREATE TABLE IF NOT EXISTS copy_projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    formula TEXT NOT NULL,
                    type TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    target_audience TEXT NOT NULL,
                    copy_text TEXT NOT NULL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()

    @staticmethod
    def get_formulas() -> Dict[str, Any]:
        """Return registered conversion copywriting formulas."""
        return FORMULAS_CATALOG

    @staticmethod
    def get_styles() -> Dict[str, Any]:
        """Return registered writing style guides."""
        return STYLE_GUIDES

    def generate_copy(
        self,
        product_name: str,
        target_audience: str,
        formula: str = "pas",
        copy_type: str = "landing_page",
        key_benefit: str = "",
        style: str = "direct_response",
    ) -> Dict[str, Any]:
        """Synthesize high-converting copy using proven psychological frameworks."""
        formula_key = formula.lower().strip()
        f_info = FORMULAS_CATALOG.get(formula_key, FORMULAS_CATALOG["pas"])

        style_key = style.lower().strip()
        s_info = STYLE_GUIDES.get(style_key, STYLE_GUIDES["direct_response"])

        benefit = key_benefit.strip() or f"10x velocity and zero downtime for {target_audience}"
        prod = product_name.strip() or "Mekong Platform"
        aud = target_audience.strip() or "Founders & Engineers"

        copy_text, sections = self._render_copy(
            product_name=prod,
            audience=aud,
            formula_key=formula_key,
            copy_type=copy_type.lower().strip(),
            key_benefit=benefit,
            style_name=s_info["name"],
        )

        project_id = f"cpy_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        metadata = {
            "formula_name": f_info["name"],
            "style_name": s_info["name"],
            "key_benefit": benefit,
            "word_count": len(copy_text.split()),
            "sections": sections,
        }

        return {
            "id": project_id,
            "title": f"{prod} — {f_info['name']} ({copy_type.replace('_', ' ').capitalize()})",
            "formula": formula_key,
            "type": copy_type.lower().strip(),
            "product_name": prod,
            "target_audience": aud,
            "copy_text": copy_text,
            "metadata": metadata,
            "created_at": now,
        }

    def _render_copy(
        self,
        product_name: str,
        audience: str,
        formula_key: str,
        copy_type: str,
        key_benefit: str,
        style_name: str,
    ) -> Tuple[str, List[str]]:
        """Construct structured copy blocks based on formula and format."""
        sections = []

        if copy_type == "email":
            sections = ["Subject Line", "Hook", "Core Argument", "Call to Action"]
            if formula_key == "bab":
                body = (
                    f"Subject: Imagine never fixing a broken deployment at 2am again\n\n"
                    f"Hey [First Name],\n\n"
                    f"Remember when shipping a new feature meant babysitting CI scripts and praying nothing broke in production?\n\n"
                    f"Now imagine this: You describe the feature, an autonomous agent writes and audits the code, tests pass with 100% boundary compliance, and your release ships automatically.\n\n"
                    f"That is the bridge {product_name} builds for {audience}.\n\n"
                    f"With {key_benefit}, you stop acting as a human router and start running like an autonomous software studio.\n\n"
                    f"Want to see it in action? Click below to try the live demo:\n\n"
                    f"👉 [Explore {product_name} in 60 Seconds]\n\n"
                    f"Best,\n"
                    f"The {product_name} Team"
                )
            else:  # PAS default for email
                body = (
                    f"Subject: Is technical debt slowing down {product_name}?\n\n"
                    f"Hey [First Name],\n\n"
                    f"Most {audience} spend 60% of their week debugging boilerplate, wrestling dependencies, and patching broken integrations.\n\n"
                    f"Every hour lost to repetitive plumbing is an hour not spent shipping customer features or driving revenue. In today's market, slow shipping kills startups.\n\n"
                    f"{product_name} eliminates the friction. Built specifically for {audience}, it delivers {key_benefit} without the enterprise complexity.\n\n"
                    f"Ready to regain your engineering velocity?\n\n"
                    f"👉 [Start Building with {product_name} — Free 14-Day Trial]\n\n"
                    f"Cheers,\n"
                    f"The {product_name} Team"
                )

        elif copy_type == "headline":
            sections = ["Primary Headline", "Sub-headline", "Micro-copy"]
            body = (
                f"# Primary Headline:\n"
                f"The Sovereign Operating System for {audience}: Deliver {key_benefit}.\n\n"
                f"## Supporting Sub-headline:\n"
                f"Stop babysitting fragile prompts and bloated microservices. {product_name} automates your end-to-end workflows with deterministic reliability.\n\n"
                f"### Social Proof & Micro-copy:\n"
                f"★ Rated 4.9/5 by 500+ autonomous builders | Zero external dependencies | Local-first SQLite persistence"
            )

        elif copy_type == "cta":
            sections = ["Primary Button", "Secondary Action", "Risk Reversal"]
            body = (
                f"🔘 Primary CTA: [ Claim Your Autonomous Studio — Free 14-Day Trial ]\n"
                f"🔗 Secondary CTA: [ Read the Architecture Whitepaper → ]\n"
                f"🛡️ Risk Reversal: No credit card required. Pure Python standard library. Full right-to-fork sovereignty."
            )

        else:  # landing_page
            sections = ["Hero", "Problem", "Solution", "Features Grid", "Social Proof", "Final CTA"]
            body = (
                f"# {product_name}: The High-Velocity Engine for {audience}\n\n"
                f"## Hero Section\n"
                f"### Stop managing infrastructure. Start building {key_benefit}.\n"
                f"{product_name} combines autonomous agent orchestration, deterministic state rollback, and local SQLite persistence to give {audience} unfair leverage.\n\n"
                f"[ Start Free Trial — No Credit Card Required ]   [ View Live Demo ]\n\n"
                f"---\n\n"
                f"## The Problem Every {audience} Faces\n"
                f"Building software today is broken. Teams get trapped in prompt engineering loops, vendor API lock-ins, and brittle glue code that fails under pressure.\n\n"
                f"## The Solution: {product_name}\n"
                f"By replacing brittle prompts with architectural guardrails, {product_name} turns complex multi-agent workflows into predictable Plan-Execute-Verify pipelines.\n\n"
                f"## Why {audience} Choose {product_name}:\n"
                f"• **Zero External Dependencies**: Pure Python standard library ensures your core runtime never breaks on upstream CVEs.\n"
                f"• **Deterministic Checkpoints**: Atomic snapshots capture disk state so failed operations auto-heal in milliseconds.\n"
                f"• **Autonomous Financial Intelligence**: Built-in MRR waterfalls, payment reconciliation, and multi-currency billing (USD/VND).\n\n"
                f"## Don't Take Our Word For It\n"
                f"> \"{product_name} let us ship an entire agency platform with 1 engineer in under a month. It completely changed how we think about agent reliability.\"\n"
                f"> — VP of Engineering, Fintech Scale-up\n\n"
                f"## Ready to Transform Your Velocity?\n"
                f"Join hundreds of forward-thinking {audience} building sovereign agent systems today.\n\n"
                f"[ Get Started with {product_name} Now ]"
            )

        return body, sections

    def generate_headlines(
        self, product_name: str, value_prop: str, count: int = 5
    ) -> List[Dict[str, Any]]:
        """Generate high-impact headline variations categorized by psychological angle."""
        prod = product_name.strip() or "Mekong"
        vp = value_prop.strip() or "build autonomous agent systems"

        templates = [
            ("Direct / Benefit", f"How {prod} Helps You {vp} in Half the Time"),
            ("Loss Aversion", f"Stop Wasting 20 Hours a Week. Let {prod} {vp} Automatically."),
            ("How-To", f"How to {vp} Without Hiring an Entire Engineering Team"),
            ("Question / Intrigue", f"What if You Could {vp} with Zero Technical Debt?"),
            ("Social Proof", f"Join 1,000+ Engineers Using {prod} to {vp}"),
            ("Contrarian", f"Why Most Developers Fail to {vp} (And How {prod} Fixes It)"),
        ]

        results = []
        for i, (angle, headline) in enumerate(templates[:count]):
            results.append(
                {
                    "index": i + 1,
                    "angle": angle,
                    "headline": headline,
                    "subheadline": f"Discover how {prod} combines architectural guardrails with autonomous agent workflows.",
                }
            )
        return results

    def generate_cta(
        self, action_goal: str, risk_reversal: str = ""
    ) -> List[Dict[str, Any]]:
        """Generate optimized call-to-action button copy with risk-reversal microcopy."""
        goal = action_goal.strip() or "start free trial"
        reversal = risk_reversal.strip() or "No credit card required • Cancel anytime • 14-day free access"

        options = [
            {
                "type": "High Urgency",
                "button_text": f"Claim Your Access & {goal.title()}",
                "microcopy": reversal,
            },
            {
                "type": "Low Friction",
                "button_text": f"Get Started Free — {goal.title()}",
                "microcopy": "Instant setup in 60 seconds • Zero installation hassle",
            },
            {
                "type": "Value-Oriented",
                "button_text": f"Unlock {goal.title()} Today",
                "microcopy": "Backed by our 100% satisfaction guarantee",
            },
            {
                "type": "Social Proof",
                "button_text": f"Join 500+ Teams & {goal.title()}",
                "microcopy": f"Rated 4.9/5 by autonomous builders • {reversal}",
            },
            {
                "type": "Exclusive Access",
                "button_text": f"Get Priority Access: {goal.title()}",
                "microcopy": f"Limited onboarding cohort • {reversal}",
            },
        ]
        return options

    def save_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a generated copywriting project to the SQLite database."""
        pid = project_data["id"]
        title = project_data["title"]
        formula = project_data["formula"]
        ctype = project_data["type"]
        prod = project_data["product_name"]
        aud = project_data["target_audience"]
        text = project_data["copy_text"]
        meta_json = json.dumps(project_data.get("metadata", {}))
        now = datetime.now(timezone.utc).isoformat()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO copy_projects (
                    id, title, formula, type, product_name, target_audience, copy_text, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (pid, title, formula, ctype, prod, aud, text, meta_json, now),
            )
            conn.commit()

        res = dict(project_data)
        res["saved_to_db"] = True
        return res

    def list_projects(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List saved copywriting projects."""
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM copy_projects ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            projects = []
            for row in cur.fetchall():
                d = dict(row)
                if d.get("metadata_json"):
                    try:
                        d["metadata"] = json.loads(d["metadata_json"])
                    except Exception:
                        d["metadata"] = {}
                projects.append(d)
            return projects

    def get_status(self) -> Dict[str, Any]:
        """Return engine operational status and project counts."""
        with self._get_connection() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM copy_projects").fetchone()[
                0
            ]

        return {
            "status": "HEALTHY",
            "db_path": str(self.db_path),
            "saved_projects_count": cnt,
            "registered_formulas": len(FORMULAS_CATALOG),
            "registered_styles": len(STYLE_GUIDES),
        }


_default_copywriting_engine: Optional[CopywritingEngine] = None


def get_copywriting_engine(db_path: Optional[Path] = None) -> CopywritingEngine:
    """Return the global CopywritingEngine singleton or a newly initialized instance."""
    global _default_copywriting_engine
    if db_path is not None:
        return CopywritingEngine(db_path=db_path)
    if _default_copywriting_engine is None:
        _default_copywriting_engine = CopywritingEngine()
    return _default_copywriting_engine
