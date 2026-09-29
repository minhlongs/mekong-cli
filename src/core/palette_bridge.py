# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/palette_bridge.py — Command Palette & TUI Dashboard Bridge.

Provides high-performance indexing, bilingual (Vietnamese + English) fuzzy matching,
category filtering, and real-time telemetry dashboard aggregation for Mekong CLI
and Google Antigravity.

Invariants:
- 100% provider-neutral: standard library only (difflib, unicodedata, json, sqlite3, pathlib, re, typing, dataclasses).
- Zero external vendor SDK imports (test_core_boundary.py compliant).
- Seamless indexing across:
  1. Antigravity Skills (.agents/skills/*/SKILL.md)
  2. Domain Subagents (.agents/subagents/registry.json)
  3. Mekong CLI Commands and Groups
- Accent-insensitive Vietnamese search normalization (kế hoạch ↔ ke hoach).
- Real-time telemetry & AGI health aggregation for the TUI dashboard.
"""

from __future__ import annotations

import difflib
import importlib
import json
import logging
import os
import re
import sqlite3
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def remove_accents(text: str) -> str:
    """Normalize and strip Vietnamese tone marks and accents for accent-insensitive search."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.lower()


@dataclass
class PaletteItem:
    """An indexed item in the Mekong command palette."""
    id: str
    name: str
    item_type: str  # "command" | "skill" | "agent" | "group"
    category: str   # "strategy" | "business" | "product" | "engineering" | "operations" | "vietnam" | "general"
    description: str
    command_syntax: str
    keywords: List[str] = field(default_factory=list)
    subagent_id: Optional[str] = None
    icon: str = "⚡"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SearchResult:
    """Result of a command palette search with scoring metadata."""
    item: PaletteItem
    score: float
    matched_by: str

    def to_dict(self) -> Dict[str, Any]:
        data = self.item.to_dict()
        data["score"] = round(self.score, 3)
        data["matched_by"] = self.matched_by
        return data


# Curated canonical Mekong CLI commands and groups with rich bilingual keywords
CANONICAL_CLI_COMMANDS: List[Dict[str, Any]] = [
    {
        "id": "cmd:cook",
        "name": "cook",
        "item_type": "command",
        "category": "engineering",
        "description": "Plan-Execute-Verify engine for autonomous feature development and coding",
        "command_syntax": "mekong cook [GOAL]",
        "keywords": ["cook", "code", "lập trình", "viết code", "triển khai tính năng", "build", "implement", "develop"],
        "subagent_id": "fullstack-developer",
        "icon": "🍳",
    },
    {
        "id": "cmd:cook-auto",
        "name": "cook-auto",
        "item_type": "command",
        "category": "engineering",
        "description": "Durable autonomous goal runner with checkpointing and atomic rollback",
        "command_syntax": "mekong cook-auto [GOAL]",
        "keywords": ["cook-auto", "autonomous", "tự động", "tự hành", "goal runner", "checkpoint"],
        "subagent_id": "fullstack-developer",
        "icon": "🤖",
    },
    {
        "id": "cmd:debug",
        "name": "debug",
        "item_type": "command",
        "category": "engineering",
        "description": "Interactive debugging, root cause analysis, and automated error fixing",
        "command_syntax": "mekong debug [TARGET]",
        "keywords": ["debug", "fix", "sửa lỗi", "sửa bug", "khắc phục", "lỗi", "error", "repair"],
        "subagent_id": "debugger",
        "icon": "🐛",
    },
    {
        "id": "cmd:plan",
        "name": "plan",
        "item_type": "group",
        "category": "product",
        "description": "Architecture and implementation plan generator with depth modes",
        "command_syntax": "mekong plan [GOAL]",
        "keywords": ["plan", "kế hoạch", "lập kế hoạch", "lên kế hoạch", "architecture", "thiết kế"],
        "subagent_id": "planner",
        "icon": "📋",
    },
    {
        "id": "cmd:specify",
        "name": "specify",
        "item_type": "command",
        "category": "product",
        "description": "SDD specification generator — translates feature requests into formal specs",
        "command_syntax": "mekong specify run [FEATURE]",
        "keywords": ["specify", "spec", "đặc tả", "yêu cầu", "sdd", "spec-kit", "requirements"],
        "subagent_id": "pm",
        "icon": "📝",
    },
    {
        "id": "cmd:tasks",
        "name": "tasks",
        "item_type": "command",
        "category": "product",
        "description": "Generate TDD-ordered implementation task breakdowns from specifications",
        "command_syntax": "mekong tasks new [SPEC]",
        "keywords": ["tasks", "task list", "danh sách công việc", "nhiệm vụ", "tdd", "chia task"],
        "subagent_id": "pm",
        "icon": "✅",
    },
    {
        "id": "cmd:implement",
        "name": "implement",
        "item_type": "command",
        "category": "engineering",
        "description": "Execute implementation tasks sequentially with automated verification",
        "command_syntax": "mekong implement [TASK_FILE]",
        "keywords": ["implement", "thực hiện", "triển khai task", "code tasks", "execute"],
        "subagent_id": "fullstack-developer",
        "icon": "🔨",
    },
    {
        "id": "cmd:ship",
        "name": "ship",
        "item_type": "command",
        "category": "engineering",
        "description": "Production release pipeline: Lint → Test → Commit → Push → Deploy",
        "command_syntax": "mekong ship",
        "keywords": ["ship", "deploy", "phát hành", "đẩy lên production", "release", "commit push"],
        "subagent_id": "eng",
        "icon": "🚀",
    },
    {
        "id": "cmd:binh-phap",
        "name": "binh-phap",
        "item_type": "group",
        "category": "strategy",
        "description": "Binh Pháp strategic execution framework (Art of War) with 13 tactical chapters",
        "command_syntax": "mekong binh-phap [ACTION]",
        "keywords": ["binh-phap", "binh pháp", "tôn tử", "sun tzu", "chiến lược", "strategy", "art of war"],
        "subagent_id": "sun-tzu",
        "icon": "⚔️",
    },
    {
        "id": "cmd:ke-toan",
        "name": "ke-toan",
        "item_type": "group",
        "category": "vietnam",
        "description": "VAS Vietnamese Accounting Standards, Circular TT78/2021 e-invoices, and journal entries",
        "command_syntax": "mekong ke-toan [SUBCOMMAND]",
        "keywords": ["ke-toan", "kế toán", "hóa đơn", "tt78", "vas", "bút toán", "tài chính", "accounting"],
        "subagent_id": "cfo",
        "icon": "🧾",
    },
    {
        "id": "cmd:thue",
        "name": "thue",
        "item_type": "group",
        "category": "vietnam",
        "description": "Vietnamese tax calculator: Personal Income Tax (TNCN), Corporate Tax (TNDN), and VAT (GTGT)",
        "command_syntax": "mekong thue [SUBCOMMAND]",
        "keywords": ["thue", "thuế", "tncn", "tndn", "gtgt", "vat", "tính thuế", "tax calculator"],
        "subagent_id": "cfo",
        "icon": "💰",
    },
    {
        "id": "cmd:zalo-oa",
        "name": "zalo-oa",
        "item_type": "group",
        "category": "vietnam",
        "description": "Zalo Official Account integration: customer messaging, broadcast, followers, and template posts",
        "command_syntax": "mekong zalo-oa [SUBCOMMAND]",
        "keywords": ["zalo-oa", "zalo", "nhắn tin zalo", "broadcast", "tin nhắn", "marketing zalo"],
        "subagent_id": "cmo",
        "icon": "💬",
    },
    {
        "id": "cmd:idea",
        "name": "idea",
        "item_type": "group",
        "category": "strategy",
        "description": "BizPlan OS Zero→IPO company generation and business model canvas validation",
        "command_syntax": "mekong idea [TOPIC]",
        "keywords": ["idea", "ý tưởng", "khởi nghiệp", "startup", "bmc", "prd", "business plan"],
        "subagent_id": "ceo",
        "icon": "💡",
    },
    {
        "id": "cmd:doctor",
        "name": "doctor",
        "item_type": "group",
        "category": "operations",
        "description": "System diagnostics, environment inspection, and requirement verification",
        "command_syntax": "mekong doctor",
        "keywords": ["doctor", "khám bệnh", "kiểm tra hệ thống", "chẩn đoán", "diagnostics", "health check"],
        "subagent_id": "ops",
        "icon": "🩺",
    },
    {
        "id": "cmd:eval-agent",
        "name": "eval-agent",
        "item_type": "command",
        "category": "operations",
        "description": "Query offline mission telemetry, success rates, p95 durations, and failure clusters",
        "command_syntax": "mekong eval-agent [--agent ID] [--days N]",
        "keywords": ["eval-agent", "đánh giá", "evals", "telemetry", "metrics", "failure cluster", "hiệu suất"],
        "subagent_id": "ops",
        "icon": "📊",
    },
    {
        "id": "cmd:evolve",
        "name": "evolve",
        "item_type": "command",
        "category": "operations",
        "description": "Continuous learning cycle: analyze execution patterns, generate recipes, deprecate bad ones",
        "command_syntax": "mekong evolve",
        "keywords": ["evolve", "tiến hóa", "tự học", "self improve", "học máy", "recipe evolution"],
        "subagent_id": "ops",
        "icon": "🧬",
    },
    {
        "id": "cmd:init",
        "name": "init",
        "item_type": "command",
        "category": "engineering",
        "description": "Scaffold and initialize Antigravity agent configurations, skills, and subagents",
        "command_syntax": "mekong init [PATH]",
        "keywords": ["init", "khởi tạo", "setup", "scaffold", "cài đặt dự án", "bootstrap"],
        "subagent_id": "cto",
        "icon": "🚀",
    },
    {
        "id": "cmd:gateway",
        "name": "gateway",
        "item_type": "command",
        "category": "operations",
        "description": "Start the OpenClaw Hybrid Commander HTTP gateway server",
        "command_syntax": "mekong gateway [--host HOST] [--port PORT] [--status] [--json]",
        "keywords": ["gateway", "cổng kết nối", "server", "http", "api", "openclaw"],
        "subagent_id": "ops",
        "icon": "🌐",
    },
    {
        "id": "cmd:halt",
        "name": "halt",
        "item_type": "command",
        "category": "operations",
        "description": "Emergency stop: immediately halt all autonomous agent operations and missions",
        "command_syntax": "mekong halt",
        "keywords": ["halt", "dừng khẩn cấp", "emergency stop", "ngừng hoạt động", "kill"],
        "subagent_id": "ceo",
        "icon": "🛑",
    },
    {
        "id": "cmd:dash",
        "name": "dash",
        "item_type": "command",
        "category": "operations",
        "description": "One-button action menu (The Washing Machine) for quick goal executions",
        "command_syntax": "mekong dash",
        "keywords": ["dash", "bảng điều khiển", "dashboard", "washing machine", "one button"],
        "subagent_id": "ceo",
        "icon": "🟢",
    },
    {
        "id": "cmd:palette",
        "name": "palette",
        "item_type": "command",
        "category": "general",
        "description": "Interactive command palette: fuzzy search Mekong commands, skills, and subagents",
        "command_syntax": "mekong palette [QUERY]",
        "keywords": ["palette", "tìm kiếm", "tìm lệnh", "search", "menu", "command palette", "lệnh"],
        "subagent_id": "ceo",
        "icon": "🔍",
    },
    {
        "id": "cmd:tui",
        "name": "tui",
        "item_type": "command",
        "category": "general",
        "description": "Warp-style interactive terminal UI with live telemetry streaming and palette",
        "command_syntax": "mekong tui [QUERY]",
        "keywords": ["tui", "giao diện terminal", "interactive", "warp", "streaming", "dashboard"],
        "subagent_id": "ceo",
        "icon": "🖥️",
    },
]


class PaletteBridge:
    """
    Central search, indexing, and TUI telemetry aggregator for Mekong CLI.
    """

    def __init__(self, root_dir: Optional[Path] = None) -> None:
        self.root_dir = root_dir or _PROJECT_ROOT
        self.skills_dir = self.root_dir / ".agents" / "skills"
        self.subagents_file = self.root_dir / ".agents" / "subagents" / "registry.json"
        self._items: Dict[str, PaletteItem] = {}
        self._indexed = False

    def ensure_indexed(self) -> None:
        """Lazily build or refresh the in-memory catalog index."""
        if not self._indexed:
            self.refresh_index()

    def refresh_index(self) -> int:
        """
        Build the unified search catalog from:
        1. Canonical CLI commands
        2. Antigravity Skills (.agents/skills/*/SKILL.md)
        3. Subagent registry (.agents/subagents/registry.json)
        """
        items: Dict[str, PaletteItem] = {}

        # 1. Index Canonical CLI Commands
        for cmd_def in CANONICAL_CLI_COMMANDS:
            item = PaletteItem(
                id=cmd_def["id"],
                name=cmd_def["name"],
                item_type=cmd_def["item_type"],
                category=cmd_def["category"],
                description=cmd_def["description"],
                command_syntax=cmd_def["command_syntax"],
                keywords=cmd_def.get("keywords", []),
                subagent_id=cmd_def.get("subagent_id"),
                icon=cmd_def.get("icon", "⚡"),
            )
            items[item.id] = item

        # 2. Index Antigravity Skills
        if self.skills_dir.is_dir():
            for skill_dir in sorted(self.skills_dir.iterdir()):
                if not skill_dir.is_dir():
                    continue
                skill_file = skill_dir / "SKILL.md"
                if not skill_file.is_file():
                    continue

                try:
                    content = skill_file.read_text(encoding="utf-8")
                    name = skill_dir.name
                    desc = ""
                    # Simple frontmatter parser
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            fm = parts[1]
                            for line in fm.splitlines():
                                line_s = line.strip()
                                if line_s.startswith("name:"):
                                    name = line_s.split(":", 1)[1].strip().strip('"\'')
                                elif line_s.startswith("description:"):
                                    desc = line_s.split(":", 1)[1].strip().strip('"\'')
                    if not desc:
                        # Extract first header or paragraph
                        for line in content.splitlines():
                            if line.startswith("#"):
                                desc = line.lstrip("#").strip()
                                break

                    category = self._infer_category(name, desc)
                    item_id = f"skill:{name}"
                    if item_id not in items:
                        kw = [name, name.replace("-", " ")]
                        items[item_id] = PaletteItem(
                            id=item_id,
                            name=name,
                            item_type="skill",
                            category=category,
                            description=desc[:160],
                            command_syntax=f"mekong {name}",
                            keywords=kw,
                            icon="🎯",
                        )
                except Exception as exc:
                    logger.debug("Failed to index skill %s: %s", skill_dir.name, exc)

        # 3. Index Domain Subagents
        if self.subagents_file.is_file():
            try:
                registry_data = json.loads(self.subagents_file.read_text(encoding="utf-8"))
                agents = registry_data.get("agents", [])
                for ag in agents:
                    ag_id = ag.get("id", "")
                    name = ag.get("name", ag_id)
                    role = ag.get("role", "")
                    desc = ag.get("description", "")
                    cat = self._infer_category(ag_id, f"{role} {desc}")
                    item_id = f"agent:{ag_id}"
                    kw = [ag_id, name, role]
                    items[item_id] = PaletteItem(
                        id=item_id,
                        name=ag_id,
                        item_type="agent",
                        category=cat,
                        description=f"{role}: {desc}"[:160],
                        command_syntax=f"mekong agent run {ag_id}",
                        keywords=kw,
                        subagent_id=ag_id,
                        icon="👤",
                    )
            except Exception as exc:
                logger.debug("Failed to index subagent registry: %s", exc)

        self._items = items
        self._indexed = True
        return len(items)

    def _infer_category(self, name: str, context: str) -> str:
        """Infer functional layer category from name and contextual text."""
        combined = f"{name} {context}".lower()

        if any(w in combined for w in ["ke-toan", "thue", "zalo", "bhxh", "ocop", "vietnam", "vas", "tt78"]):
            return "vietnam"
        if any(w in combined for w in ["binh-phap", "sun-tzu", "ceo", "cso", "venture", "strategy", "scenario", "founder"]):
            return "strategy"
        if any(w in combined for w in ["sales", "marketing", "ae", "cmo", "crm", "accounting", "invoice", "deal", "lead"]):
            return "business"
        if any(w in combined for w in ["plan", "spec", "specify", "tasks", "sdd", "pm", "product", "design", "backlog"]):
            return "product"
        if any(w in combined for w in ["cook", "code", "dev", "build", "ship", "deploy", "fix", "debug", "test", "eng", "cto", "particle"]):
            return "engineering"
        if any(w in combined for w in ["ops", "doctor", "health", "monitor", "metrics", "eval", "evolve", "halt", "gate", "guard"]):
            return "operations"
        return "general"

    def search(
        self,
        query: Optional[str] = None,
        category: str = "all",
        limit: int = 5,
    ) -> List[SearchResult]:
        """
        Bilingual fuzzy search with Vietnamese accent normalization.
        Returns top scored matches up to limit.
        """
        self.ensure_indexed()

        cat_filter = category.lower().strip() if category else "all"

        # If no query provided, return top items in category or top canonical items
        if not query or not query.strip():
            matches: List[SearchResult] = []
            for item in self._items.values():
                if cat_filter != "all" and item.category != cat_filter:
                    continue
                # Priority: canonical commands first, then agents, then skills
                base_score = 1.0 if item.item_type == "command" else 0.8 if item.item_type == "agent" else 0.6
                matches.append(SearchResult(item=item, score=base_score, matched_by="catalog_list"))
            matches.sort(key=lambda x: (x.score, x.item.name), reverse=True)
            return matches[:limit]

        q = query.strip()
        q_lower = q.lower()
        q_unaccent = remove_accents(q_lower)

        results: List[SearchResult] = []

        for item in self._items.values():
            if cat_filter != "all" and item.category != cat_filter:
                continue

            score = 0.0
            matched_by = ""

            item_name_lower = item.name.lower()
            item_name_unaccent = remove_accents(item_name_lower)
            desc_lower = item.description.lower()
            desc_unaccent = remove_accents(desc_lower)

            # 1. Exact match on name
            if q_lower == item_name_lower or q_unaccent == item_name_unaccent:
                score = 1.0
                matched_by = "exact_name"
            # 2. Exact match in keywords
            elif any(q_lower == kw.lower() or q_unaccent == remove_accents(kw) for kw in item.keywords):
                score = 0.95
                matched_by = "exact_keyword"
            # 3. Name starts with query
            elif item_name_lower.startswith(q_lower) or item_name_unaccent.startswith(q_unaccent):
                score = 0.88
                matched_by = "prefix_name"
            # 4. Keyword starts with query
            elif any(kw.lower().startswith(q_lower) or remove_accents(kw).startswith(q_unaccent) for kw in item.keywords):
                score = 0.82
                matched_by = "prefix_keyword"
            # 5. Query contained in name or keywords
            elif q_lower in item_name_lower or q_unaccent in item_name_unaccent:
                score = 0.78
                matched_by = "substring_name"
            elif any(q_lower in kw.lower() or q_unaccent in remove_accents(kw) for kw in item.keywords):
                score = 0.75
                matched_by = "substring_keyword"
            # 6. Description containment
            elif q_lower in desc_lower or q_unaccent in desc_unaccent:
                score = 0.65
                matched_by = "description_match"
            else:
                # 7. Fuzzy similarity ratio (difflib)
                ratio_name = difflib.SequenceMatcher(None, q_unaccent, item_name_unaccent).ratio()
                if ratio_name > 0.6:
                    score = 0.50 + (ratio_name * 0.25)
                    matched_by = "fuzzy_ratio"

            if score >= 0.40:
                results.append(SearchResult(item=item, score=score, matched_by=matched_by))

        results.sort(key=lambda x: (x.score, x.item.name), reverse=True)
        return results[:limit]

    def get_tui_dashboard_summary(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Aggregate real-time telemetry, checkpoints, goals, and AGI subsystem readiness
        for terminal UI display.
        """
        self.ensure_indexed()

        # 1. Telemetry / Evals stats
        evals_summary = {
            "total_missions": 0,
            "success_rate": 100.0,
            "p95_duration_ms": 0,
            "total_credits": 0.0,
            "failure_clusters": {},
        }
        evals_db = self.root_dir / ".mekong" / "evals.db"
        if evals_db.is_file():
            try:
                conn = sqlite3.connect(str(evals_db), timeout=2.0)
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                row = cur.execute(
                    "SELECT COUNT(*) as cnt, SUM(success) as ok_cnt, SUM(credits_used) as cr FROM mission_evals"
                ).fetchone()
                if row and row["cnt"]:
                    total = row["cnt"]
                    ok = row["ok_cnt"] or 0
                    evals_summary["total_missions"] = total
                    evals_summary["success_rate"] = round((ok / total) * 100, 1)
                    evals_summary["total_credits"] = round(row["cr"] or 0.0, 2)

                # p95 duration
                durs = [r[0] for r in cur.execute("SELECT duration_ms FROM mission_evals ORDER BY duration_ms ASC").fetchall()]
                if durs:
                    idx = int(len(durs) * 0.95)
                    evals_summary["p95_duration_ms"] = durs[min(idx, len(durs) - 1)]
                conn.close()
            except Exception as exc:
                logger.debug("Failed to read evals.db: %s", exc)

        # 2. Checkpoints count
        checkpoint_count = 0
        pev_db = self.root_dir / ".mekong" / "pev_checkpoints.db"
        if pev_db.is_file():
            try:
                conn = sqlite3.connect(str(pev_db), timeout=2.0)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='checkpoints'")
                if cur.fetchone():
                    c_row = cur.execute("SELECT COUNT(*) FROM checkpoints").fetchone()
                    if c_row:
                        checkpoint_count = c_row[0]
                conn.close()
            except Exception as exc:
                logger.debug("Failed to read pev_checkpoints.db: %s", exc)

        # 3. Goals count
        goal_stats = {"total_goals": 0, "active_goals": 0, "completed_goals": 0}
        goals_db = self.root_dir / ".mekong" / "goals.sqlite3"
        if goals_db.is_file():
            try:
                conn = sqlite3.connect(str(goals_db), timeout=2.0)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='goals'")
                if cur.fetchone():
                    g_rows = cur.execute("SELECT status, COUNT(*) FROM goals GROUP BY status").fetchall()
                    for status, count in g_rows:
                        goal_stats["total_goals"] += count
                        if str(status).lower() in ["active", "running", "in_progress"]:
                            goal_stats["active_goals"] += count
                        elif str(status).lower() in ["completed", "success", "done"]:
                            goal_stats["completed_goals"] += count
                conn.close()
            except Exception as exc:
                logger.debug("Failed to read goals.sqlite3: %s", exc)

        # 4. AGI Subsystems Readiness Check
        _subsystems_to_check = [
            ("NLU", "src.core.nlu", "IntentClassifier"),
            ("Memory", "src.core.memory_canonical", "MemoryStore"),
            ("Reflection", "src.core.reflection", "ReflectionEngine"),
            ("WorldModel", "src.core.world_model", "WorldModel"),
            ("ToolRegistry", "src.core.tool_registry", "ToolRegistry"),
            ("BrowserAgent", "src.core.browser_agent", "BrowserAgent"),
            ("Collaboration", "src.core.collaboration", "CollaborationProtocol"),
            ("CodeEvolution", "src.core.code_evolution", "CodeEvolutionEngine"),
            ("VectorMemory", "src.core.vector_memory_store", "VectorMemoryStore"),
        ]
        subsystem_status: Dict[str, bool] = {}
        for name, mod_name, cls_name in _subsystems_to_check:
            try:
                m = importlib.import_module(mod_name)
                getattr(m, cls_name)
                subsystem_status[name] = True
            except Exception:
                subsystem_status[name] = False

        online_count = sum(1 for v in subsystem_status.values() if v)
        total_subsystems = len(_subsystems_to_check)
        agi_health = "healthy" if online_count == total_subsystems else "degraded" if online_count >= 6 else "offline"

        # Catalog distribution
        types_breakdown: Dict[str, int] = {}
        categories_breakdown: Dict[str, int] = {}
        for it in self._items.values():
            types_breakdown[it.item_type] = types_breakdown.get(it.item_type, 0) + 1
            categories_breakdown[it.category] = categories_breakdown.get(it.category, 0) + 1

        summary = {
            "ok": True,
            "version": "v2.0.0-agi",
            "agi_health": agi_health,
            "subsystems_online": f"{online_count}/{total_subsystems}",
            "catalog": {
                "total_items": len(self._items),
                "types": types_breakdown,
                "categories": categories_breakdown,
            },
            "evals": evals_summary,
            "checkpoints_count": checkpoint_count,
            "goals": goal_stats,
        }

        if detailed:
            summary["subsystems_detail"] = subsystem_status

        return summary
