"""Mekong CLI 7 — Skill loader (port of opencode skill tool).

Discovers SKILL.md files (claude skills dir + project .claude/skills +
~/.config/opencode/skills), parses frontmatter, and injects skill
instructions into node prompts based on intent.skill_hint.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

SKILL_DIRS = (
    Path.home() / ".claude" / "skills",
    Path.home() / ".config" / "opencode" / "skills",
)


class SkillNotFound(KeyError):
    pass


@dataclass
class Skill:
    name: str
    description: str
    body: str
    source: str = ""

    @property
    def frontmatter(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description}


def _parse_frontmatter(text: str) -> tuple[dict[str, Any] | None, str]:
    """Split SKILL.md frontmatter (---\n...\n---) from body."""
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, text
    fm_text = "\n".join(lines[1:end])
    body = "\n".join(lines[end + 1 :]).strip()
    if yaml is None:
        return None, body
    try:
        fm = yaml.safe_load(fm_text)
        return (fm if isinstance(fm, dict) else None), body
    except Exception:
        return None, body


class SkillRegistry:
    """In-memory index of all discoverable skills."""

    def __init__(self, extra_dirs: list[Path] | None = None):
        self.skills: dict[str, Skill] = {}
        dirs = list(SKILL_DIRS) + (extra_dirs or [])
        for base in dirs:
            if not base.is_dir():
                continue
            for sk in sorted(base.iterdir()):
                md = sk / "SKILL.md"
                if not md.is_file():
                    continue
                text = md.read_text(errors="replace")
                fm, body = _parse_frontmatter(text)
                name = str((fm or {}).get("name") or sk.name)
                description = str((fm or {}).get("description") or "")
                # normalize ak:brainstorm -> ak-brainstorm (claude-safe)
                name = name.replace(":", "-")
                self.skills[name] = Skill(name=name, description=description, body=body, source=str(md))

    def find(self, name: str) -> Skill | None:
        key = name.strip().lower().replace(":", "-")
        if key in self.skills:
            return self.skills[key]
        for sk in self.skills.values():
            if sk.name.lower() == key or sk.name.lower().replace("-", "") == key.replace("-", ""):
                return sk
        return None

    def search(self, query: str, limit: int = 5) -> list[Skill]:
        q = query.lower()
        scored: list[tuple[int, Skill]] = []
        for sk in self.skills.values():
            score = 0
            if q in sk.name.lower():
                score += 10
            if q in sk.description.lower():
                score += 5
            if q in sk.body.lower()[:2000]:
                score += 1
            if score:
                scored.append((score, sk))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [sk for _, sk in scored[:limit]]

    def list(self) -> list[Skill]:
        return sorted(self.skills.values(), key=lambda s: s.name)


def load_skill(name: str, registry: SkillRegistry | None = None) -> Skill:
    """Load a skill by name, raising SkillNotFound if missing."""
    reg = registry or SkillRegistry()
    skill = reg.find(name)
    if skill is None:
        raise SkillNotFound(name)
    return skill


def skill_prompt_for_hint(hint: str, registry: SkillRegistry | None = None, max_chars: int = 4000) -> str:
    """Return skill instructions for an intent skill_hint ('' if not found)."""
    if not hint:
        return ""
    reg = registry or SkillRegistry()
    skill = reg.find(hint)
    if skill is None:
        matches = reg.search(hint, limit=1)
        if not matches:
            return ""
        skill = matches[0]
    body = skill.body[:max_chars]
    return f"Skill: {skill.name}\n{skill.description}\n\n{body}"
