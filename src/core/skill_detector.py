"""Mekong CLI - Skill Detector.

Scans workspace for technology markers and injects relevant
skill context into LLM prompts. Part of the PEV pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class DetectedSkill:
    """A detected technology skill with confidence score."""

    name: str
    confidence: float
    markers: list[str] = field(default_factory=list)
    recipe_path: str = ""

    def __repr__(self) -> str:
        return f"<Skill:{self.name} conf={self.confidence:.1f}>"


@dataclass
class _DetectorRule:
    """Internal rule for a single technology detector."""

    name: str
    files: list[str]
    patterns: list[tuple[str, str]]  # (glob, search_string)
    recipe: str = ""


def _build_rules() -> list[_DetectorRule]:
    """Build the 17+ detector rules."""
    return [
        _DetectorRule("python", ["pyproject.toml", "setup.py", "requirements.txt"],
                      [("*.py", "import ")], "python.md"),
        _DetectorRule("fastapi", ["requirements.txt"],
                      [("*.py", "from fastapi"), ("pyproject.toml", "fastapi")], "fastapi.md"),
        _DetectorRule("flask", ["requirements.txt"],
                      [("*.py", "from flask"), ("pyproject.toml", "flask")]),
        _DetectorRule("nextjs", ["next.config.js", "next.config.mjs", "next.config.ts"],
                      [("package.json", '"next"')]),
        _DetectorRule("react", [],
                      [("package.json", '"react"'), ("*.tsx", "import React")]),
        _DetectorRule("typescript", ["tsconfig.json"],
                      [("package.json", '"typescript"')]),
        _DetectorRule("tailwind", ["tailwind.config.js", "tailwind.config.ts"],
                      [("package.json", '"tailwindcss"')]),
        _DetectorRule("docker", ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
                      [], "docker.md"),
        _DetectorRule("cloudflare", ["wrangler.toml", "wrangler.jsonc"],
                      [("package.json", '"wrangler"')], "cloudflare.md"),
        _DetectorRule("postgresql", [],
                      [("*.py", "psycopg"), ("*.py", "asyncpg"),
                       ("docker-compose.yml", "postgres")]),
        _DetectorRule("sqlite", [],
                      [("*.py", "sqlite3"), ("*.py", "aiosqlite")]),
        _DetectorRule("supabase", [],
                      [("package.json", '"@supabase"'), ("*.py", "supabase")]),
        _DetectorRule("terraform", ["main.tf", "terraform.tfvars"],
                      [("*.tf", "resource ")]),
        _DetectorRule("kubernetes", ["k8s/", "kubernetes/"],
                      [("*.yaml", "apiVersion:"), ("*.yml", "kind: Deployment")]),
        _DetectorRule("github_actions", [".github/workflows/"],
                      [(".github/workflows/*.yml", "on:")]),
        _DetectorRule("pytest", ["conftest.py", "pytest.ini"],
                      [("pyproject.toml", "[tool.pytest")], "testing.md"),
        _DetectorRule("poetry", ["poetry.lock"],
                      [("pyproject.toml", "[tool.poetry")]),
        _DetectorRule("polar", [],
                      [("*.py", "polar"), ("package.json", '"polar"')]),
    ]


class SkillDetector:
    """Scan workspace for technology markers.

    Detects technologies present in a workspace by checking
    for marker files and grep patterns, then provides skill
    context for LLM prompt injection.
    """

    def __init__(self, workspace: str = ".") -> None:
        self._workspace = Path(workspace).resolve()
        self._rules = _build_rules()
        self._cache: Optional[list[DetectedSkill]] = None
        self._cache_time: float = 0.0
        self._cache_ttl: float = 300.0

    @property
    def workspace(self) -> Path:
        """Return the resolved workspace path."""
        return self._workspace

    def detect(self, force: bool = False) -> list[DetectedSkill]:
        """Scan workspace and return detected skills sorted by confidence.

        Args:
            force: Bypass cache and rescan.

        Returns:
            List of DetectedSkill sorted by confidence descending.
        """
        now = time.monotonic()
        if not force and self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        skills: list[DetectedSkill] = []
        for rule in self._rules:
            skill = self._evaluate_rule(rule)
            if skill and skill.confidence > 0:
                skills.append(skill)

        skills.sort(key=lambda s: s.confidence, reverse=True)
        self._cache = skills
        self._cache_time = now
        return skills

    def _evaluate_rule(self, rule: _DetectorRule) -> Optional[DetectedSkill]:
        """Evaluate a single detector rule against the workspace."""
        markers: list[str] = []
        score = 0.0

        # Check marker files
        for f in rule.files:
            target = self._workspace / f
            if target.exists():
                markers.append(f"file:{f}")
                score += 0.5

        # Check grep patterns
        for glob_pat, search_str in rule.patterns:
            if self._grep_workspace(glob_pat, search_str):
                markers.append(f"pattern:{glob_pat}~{search_str}")
                score += 0.3

        if score == 0:
            return None

        confidence = min(score, 1.0)
        recipe = f"recipes/skills/{rule.recipe}" if rule.recipe else ""
        return DetectedSkill(
            name=rule.name,
            confidence=confidence,
            markers=markers,
            recipe_path=recipe,
        )

    def _grep_workspace(self, glob_pattern: str, search: str) -> bool:
        """Check if search string exists in files matching glob."""
        try:
            for path in self._workspace.glob(glob_pattern):
                if path.is_file():
                    try:
                        text = path.read_text(errors="ignore")[:50000]
                        if search in text:
                            return True
                    except OSError:
                        continue
        except OSError:
            pass
        return False

    def inject_context(self) -> str:
        """Return combined skill text for LLM prompt injection.

        Reads recipe files for detected skills and returns
        concatenated context string.
        """
        skills = self.detect()
        if not skills:
            return ""

        parts: list[str] = []
        parts.append(f"## Detected Skills ({len(skills)})\n")

        for skill in skills:
            parts.append(f"- **{skill.name}** (confidence: {skill.confidence:.1f})")
            if skill.recipe_path:
                recipe_file = self._workspace / skill.recipe_path
                if recipe_file.is_file():
                    try:
                        content = recipe_file.read_text(errors="ignore")
                        parts.append(f"\n### {skill.name} Best Practices\n{content}")
                    except OSError:
                        pass

        return "\n".join(parts)

    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self._cache = None
        self._cache_time = 0.0


__all__ = ["DetectedSkill", "SkillDetector"]
