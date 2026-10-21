# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Catalog scanning and frontmatter parsing for RaaS Marketplace."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SKILLS = _DEFAULT_REPO_ROOT / ".claude" / "skills"
_DEFAULT_COMMANDS = _DEFAULT_REPO_ROOT / ".claude" / "commands"


def _mod() -> Any:
    return sys.modules.get("src.raas.marketplace_router")


@dataclass
class MarketplaceItem:
    """Single skill or command entry."""

    name: str
    item_type: str  # "skill" or "command"
    description: str = ""
    category: str = ""
    tags: List[str] = field(default_factory=list)
    path: str = ""
    cost: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.item_type,
            "description": self.description,
            "category": self.category,
            "tags": self.tags,
            "path": self.path,
            "cost": self.cost,
        }


def _parse_frontmatter(text: str) -> Dict[str, str]:
    """Extract YAML-like frontmatter from markdown text."""
    meta: Dict[str, str] = {}
    if not text.startswith("---"):
        return meta
    end = text.find("---", 3)
    if end < 0:
        return meta
    block = text[3:end].strip()
    for line in block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip().strip('"').strip("'")
            if key:
                meta[key] = val
    return meta


def _extract_description(text: str, fm: Dict[str, str]) -> str:
    desc = fm.get("description", "")
    if not desc:
        end = text.find("---", 3)
        if end >= 0:
            remainder = text[end + 3 :].strip()
            desc = remainder.splitlines()[0].lstrip("# ").strip() if remainder else ""
    return desc[:200]


def _scan_skills() -> List[MarketplaceItem]:
    """Scan .claude/skills/ for all SKILL.md entries."""
    mod = _mod()
    skills_dir = getattr(mod, "_MARKETPLACE_SKILLS", _DEFAULT_SKILLS)
    repo_root = getattr(mod, "_REPO_ROOT", _DEFAULT_REPO_ROOT)
    skill_cost = getattr(mod, "SKILL_INSTALL_COST", 1)

    items: List[MarketplaceItem] = []
    if not skills_dir.exists():
        return items

    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_dir() or entry.name.startswith("_"):
            continue
        skill_file = entry / "SKILL.md"
        if not skill_file.exists():
            continue

        text = skill_file.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(text)
        desc = _extract_description(text, fm)
        tags: List[str] = []
        if "tags" in fm:
            tags = [t.strip() for t in fm["tags"].split(",") if t.strip()]

        items.append(
            MarketplaceItem(
                name=entry.name,
                item_type="skill",
                description=desc,
                category=fm.get("category", ""),
                tags=tags,
                path=os.path.relpath(str(skill_file), str(repo_root)),
                cost=skill_cost,
            )
        )
    return items


def _scan_commands() -> List[MarketplaceItem]:
    """Scan .claude/commands/ for all .md entries."""
    mod = _mod()
    commands_dir = getattr(mod, "_MARKETPLACE_COMMANDS", _DEFAULT_COMMANDS)
    repo_root = getattr(mod, "_REPO_ROOT", _DEFAULT_REPO_ROOT)
    cmd_cost = getattr(mod, "COMMAND_INSTALL_COST", 1)

    items: List[MarketplaceItem] = []
    if not commands_dir.exists():
        return items

    for entry in sorted(commands_dir.iterdir()):
        if entry.is_file() and entry.suffix == ".md" and not entry.name.startswith("_"):
            text = entry.read_text(encoding="utf-8", errors="replace")
            fm = _parse_frontmatter(text)
            items.append(
                MarketplaceItem(
                    name=entry.stem,
                    item_type="command",
                    description=_extract_description(text, fm),
                    category="",
                    tags=[],
                    path=os.path.relpath(str(entry), str(repo_root)),
                    cost=cmd_cost,
                )
            )
        elif entry.is_dir() and not entry.name.startswith("_"):
            for sub in sorted(entry.iterdir()):
                if sub.is_file() and sub.suffix == ".md":
                    text = sub.read_text(encoding="utf-8", errors="replace")
                    fm = _parse_frontmatter(text)
                    items.append(
                        MarketplaceItem(
                            name=f"{entry.name}/{sub.stem}",
                            item_type="command",
                            description=_extract_description(text, fm),
                            category=entry.name,
                            tags=[],
                            path=os.path.relpath(str(sub), str(repo_root)),
                            cost=cmd_cost,
                        )
                    )
    return items


def _get_catalog() -> Dict[str, List[MarketplaceItem]]:
    """Return {skills: [...], commands: [...]}."""
    mod = _mod()
    scan_skills = getattr(mod, "_scan_skills", _scan_skills)
    scan_commands = getattr(mod, "_scan_commands", _scan_commands)
    return {
        "skills": scan_skills(),
        "commands": scan_commands(),
    }
