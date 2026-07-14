"""Recipe parser — real Markdown → structured PEV output.

Wave B5 upgrade: replaces stub with production parser that produces
structured PEV tokens, engine params, and validation conditions.

Supported Markdown format:

---
id: recipe-id          # slug
name: "Readable Name"  # human title (overrides ## Goal heading)
intent: deploy         # NLU intent tag
model: claude-sonnet-4 # override default engine model
temperature: 0.2       # override default temperature
retries: 3             # per-step retry count
---

## Goal
Brief description of what to achieve

## Steps

1. **Step title** — description text
   multi-line description continued
2. **Another step** — description

## Verification

- soft: observed metric or probe text
- hard:exit_code == 0
- hard:output contains "deployed"
- hard:file_exists dist/
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .pev_types import (
    EngineParams,
    PromptToken,
    TokenRole,
    ValidationConditions,
)


@dataclass
class RecipeStep:
    """Single executable step in a PEV recipe."""

    order: int
    title: str
    description: str = ""
    params: dict = field(default_factory=dict)
    agent: str | None = None

    # PEV fields — populated by parser from step content / inline metadata
    validation: ValidationConditions = field(
        default_factory=ValidationConditions
    )

    # Dependencies on other steps (1-based order numbers). Set by planner
    # and consumed by DAGScheduler; not serialised into the Markdown format.
    dependencies: list[int] = field(default_factory=list)


@dataclass
class Recipe:
    """Full PEV recipe — backward-compatible superset of the original Recipe.

    All original fields (name, title, steps, verification) are preserved.
    New PEV fields provide structured tokens, engine params, per-step
    validation, and YAML frontmatter metadata.
    """

    name: str = ""
    title: str = ""
    steps: List[RecipeStep] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)

    # PEV structured format
    intent: str = ""
    prompt_tokens: List[PromptToken] = field(default_factory=list)
    engine_params: EngineParams = field(default_factory=EngineParams)
    validation: ValidationConditions = field(default_factory=ValidationConditions)
    metadata: dict = field(default_factory=dict)


class RecipeParser:
    """Parse Markdown recipe files into structured Recipe objects."""

    _SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    _STEP_RE = re.compile(r"^(\d+)\.\s+\*{0,2}(.+?)\*{0,2}(?:\s+[—–\-]\s*(.*))?$", re.MULTILINE)
    _CHECK_RE = re.compile(r"^-\s+(.+)$", re.MULTILINE)

    # YAML frontmatter patterns (lightweight — no PyYAML dependency)
    _FM_KEY_RE = re.compile(r"^(\w[\w_-]*)\s*:\s*(.*)$")
    _FM_BOOL_TRUE = re.compile(r"^(true|yes|1|on)$", re.IGNORECASE)
    _FM_BOOL_FALSE = re.compile(r"^(false|no|0|off|)$", re.IGNORECASE)

    def parse(self, filepath: Path) -> Recipe:
        """Parse a Markdown recipe file."""
        content = Path(filepath).read_text(encoding="utf-8")
        return self.parse_string(content, name=str(filepath))

    def parse_steps(self, content: str) -> List[RecipeStep]:
        """Extract steps from Markdown content string."""
        return self.parse_string(content).steps

    def parse_string(self, content: str, name: str = "inline") -> Recipe:
        """Parse Markdown string → Recipe with PEV structured fields."""
        recipe = Recipe(name=name)
        fm, body = self._split_frontmatter(content)

        # YAML frontmatter → metadata, engine_params, intent
        self._apply_frontmatter(recipe, fm)

        # Markdown body → title, steps, verification
        sections = self._split_sections(body)
        for heading, section_body in sections.items():
            heading_lower = heading.lower()
            if heading_lower == "goal":
                recipe.title = section_body.strip().split("\n")[0].strip()
            elif heading_lower == "steps":
                recipe.steps = self._parse_steps(section_body)
            elif heading_lower == "verification":
                checks = self._parse_checks(section_body)
                recipe.verification = checks
                recipe.validation = self._checks_to_validation(checks)

        # Build structured prompt tokens from goal + context
        recipe.prompt_tokens = self._build_prompt_tokens(recipe)
        return recipe

    # ------------------------------------------------------------------ #
    # Frontmatter
    # ------------------------------------------------------------------ #

    def _split_frontmatter(self, content: str) -> tuple[dict, str]:
        """Extract YAML frontmatter (--- delimited) and remaining body."""
        if not content.startswith("---"):
            return {}, content
        end = content.find("---", 3)
        if end == -1:
            return {}, content
        fm_text = content[3:end].strip()
        body = content[end + 3:].lstrip("\n")
        parsed: dict = {}
        for line in fm_text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = self._FM_KEY_RE.match(line)
            if m:
                key = m.group(1).lower()
                raw = m.group(2).strip()
                # Strip inline comment
                if " #" in raw:
                    raw = raw[: raw.index(" #")].strip()
                value = self._cast_fm_value(raw)
                parsed[key] = value
        return parsed, body

    @staticmethod
    def _cast_fm_value(raw: str) -> object:
        """Cast YAML scalar string to Python type (no PyYAML)."""
        stripped = raw.strip()
        if RecipeParser._FM_BOOL_TRUE.match(stripped):
            return True
        if RecipeParser._FM_BOOL_FALSE.match(stripped):
            return False
        try:
            return int(stripped)
        except ValueError:
            pass
        try:
            return float(stripped)
        except ValueError:
            pass
        # Strip surrounding quotes
        if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in ('"', "'"):
            return stripped[1:-1]
        return stripped

    def _apply_frontmatter(self, recipe: Recipe, fm: dict) -> None:
        """Apply parsed frontmatter to recipe fields."""
        # ---- metadata keys ----
        meta_keys = {
            "id", "name", "description", "version", "category",
            "max_retries", "timeout",
        }
        for key, value in fm.items():
            if key in meta_keys:
                recipe.metadata[key] = value

        # ---- intent ----
        recipe.intent = fm.get("intent", "")

        # ---- engine params ----
        ep = EngineParams()
        if "model" in fm:
            ep.model = str(fm["model"])
        if "temperature" in fm:
            try:
                ep.temperature = float(fm["temperature"])
            except (TypeError, ValueError):
                pass
        if "max_tokens" in fm:
            try:
                ep.max_tokens = int(fm["max_tokens"])
            except (TypeError, ValueError):
                pass
        if "retries" in fm:
            try:
                ep.retries = int(fm["retries"])
            except (TypeError, ValueError):
                pass
        if "timeout" in fm:
            try:
                ep.timeout_s = float(fm["timeout"])
            except (TypeError, ValueError):
                pass
        recipe.engine_params = ep

    # ------------------------------------------------------------------ #
    # Markdown body
    # ------------------------------------------------------------------ #

    def _split_sections(self, content: str) -> dict:
        parts = self._SECTION_RE.split(content)
        sections: dict = {}
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            sections[heading] = body
        return sections

    def _parse_steps(self, body: str) -> List[RecipeStep]:
        """Parse `## Steps` body → RecipeStep list with per-step validation."""
        steps: List[RecipeStep] = []
        matches = list(self._STEP_RE.finditer(body))
        for idx, m in enumerate(matches):
            order = int(m.group(1))
            title = m.group(2).strip()
            # m.group(3) is description after — separator (may be None)
            desc_oneline = m.group(3) or ""
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
            # Trailing body after the same line gives multi-line description
            block = body[start:end]
            first_line, *rest = block.split("\n", 1)
            rest_text = rest[0] if rest else ""
            # Combine: heading description + newline + rest
            desc = desc_oneline
            if rest_text.strip():
                desc = (desc + "\n" if desc else "") + rest_text.strip()

            # Extract inline step metadata
            params = self._detect_params(title, desc)
            # Split - prefixed lines from other step data (robust clean)
            step_text, checks = self._extract_inline_checks(desc)
            validation = self._checks_to_validation(checks)

            steps.append(
                RecipeStep(
                    order=order,
                    title=title,
                    description=step_text.strip().lstrip(": \t\n"),
                    params=params,
                    validation=validation,
                )
            )
        return steps

    @staticmethod
    def _extract_inline_checks(text: str) -> tuple[str, List[str]]:
        """Pull '- prefixed' lines from description, return (clean_text, checks)."""
        lines = text.split("\n")
        kept: List[str] = []
        checks: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                checks.append(stripped[2:].strip())
            else:
                kept.append(line)
        return "\n".join(kept).strip(), checks

    def _parse_checks(self, body: str) -> List[str]:
        """Parse `## Verification` body → list of condition strings."""
        return [m.group(1).strip() for m in self._CHECK_RE.finditer(body)]

    @staticmethod
    def _checks_to_validation(checks: List[str]) -> ValidationConditions:
        """Convert raw check strings into ValidationConditions (soft/hard split)."""
        soft: List[str] = []
        hard: List[str] = []
        for check in checks:
            stripped = check.strip()
            if stripped.lower().startswith("soft:"):
                soft.append(stripped[5:].strip())
            elif stripped.lower().startswith("hard:"):
                hard.append(stripped[5:].strip())
            elif any(stripped.startswith(p) for p in ("output contains", "exit_code", "file_exists", "file_not_exists")):
                hard.append(stripped)
            else:
                # Default: soft (advisory)
                soft.append(stripped)
        return ValidationConditions(soft=soft, hard=hard)

    @staticmethod
    def _detect_params(title: str, desc: str) -> dict:
        """Extract hint params from step text."""
        params: dict = {}
        text = f"{title} {desc}".lower()
        if "verify" in text or "check" in text:
            params["type"] = "verification"
        elif any(w in text for w in ("write", "create", "build", "deploy")):
            params["type"] = "creation"
        if "python" in text or ".py" in text:
            params["language"] = "python"
        elif "js" in text or "javascript" in text:
            params["language"] = "javascript"
        return params

    # ------------------------------------------------------------------ #
    # Intent detection (B3 NLU integration — delegation, not copy)
    # ------------------------------------------------------------------ #

    @staticmethod
    def detect_intent(recipe: "Recipe") -> str:
        """Detect recipe intent from title, frontmatter, or step keywords.

        Delegates to ``src.core.nlu.classify_intent`` when available,
        otherwise uses a lightweight keyword fallback. Never modifies B3.
        Returns upper-case intent tag string (e.g. "DEPLOY", "FIX").
        """
        # 1. Explicit intent from frontmatter takes priority
        if recipe.intent:
            return recipe.intent.upper()

        # 2. Try B3 NLU (delegation — no local copies)
        try:
            from src.core.nlu import classify_intent  # type: ignore[attr-defined]
            result = classify_intent(recipe.title)
            if hasattr(result, "intent") and hasattr(result.intent, "value"):
                return result.intent.value.upper()
        except Exception:
            pass

        # 3. Fallback: keyword scan on title
        _FALLBACK: dict[str, list[str]] = {
            "DEPLOY": ["deploy", "ship", "publish", "triển khai", "trien khai"],
            "FIX": ["fix", "repair", "debug", "patch", "sửa", "sua", "khắc phục"],
            "CREATE": ["create", "build", "generate", "init", "tạo", "tao", "xây"],
            "AUDIT": ["audit", "scan", "review", "kiểm tra", "kiem tra"],
            "REFACTOR": ["refactor", "clean", "restructure", "tái cấu trúc"],
            "OPTIMIZE": ["optimize", "performance", "tối ưu"],
        }
        title_lower = recipe.title.lower()
        for intent, keywords in _FALLBACK.items():
            if any(kw in title_lower for kw in keywords):
                return intent
        return "UNKNOWN"

    # ------------------------------------------------------------------ #
    # Prompt token composition
    # ------------------------------------------------------------------ #

    def _build_prompt_tokens(self, recipe: Recipe) -> List[PromptToken]:
        """Compose structured prompt tokens from goal + step context."""
        tokens: List[PromptToken] = []

        # SYSTEM: persona / role
        tokens.append(PromptToken(
            role=TokenRole.SYSTEM,
            content="You are the Mekong CLI execution engine. "
                    "Follow each step precisely, report results verbatim.",
            context="persona",
        ))

        # GOAL: the recipe title as the user's goal
        goal_text = recipe.title or recipe.name or "execute the plan"
        tokens.append(PromptToken(
            role=TokenRole.USER,
            content=goal_text,
            context="goal",
        ))

        # CONTEXT: metadata hints
        if recipe.metadata:
            ctx_parts = [f"{k}={v}" for k, v in recipe.metadata.items()]
            tokens.append(PromptToken(
                role=TokenRole.CONTEXT,
                content="Recipe metadata: " + ", ".join(ctx_parts),
                context="metadata",
            ))

        # PLAN: individual steps as references
        for step in recipe.steps:
            tokens.append(PromptToken(
                role=TokenRole.PLAN,
                content=f"Step {step.order}: {step.title}\n{step.description}",
                context=f"step-{step.order}",
            ))

        # GUARD: hard verification conditions
        hard_checks = recipe.validation.hard
        if hard_checks:
            tokens.append(PromptToken(
                role=TokenRole.GUARD,
                content="Hard requirements (must pass):\n  - " + "\n  - ".join(hard_checks),
                context="verification",
            ))

        # EXAMPLE: first step as illustrative pattern
        if recipe.steps:
            first = recipe.steps[0]
            tokens.append(PromptToken(
                role=TokenRole.EXAMPLE,
                content=f"Example: {first.title} → {first.description}",
                context="step-1",
            ))

        return tokens


__all__ = ["Recipe", "RecipeParser", "RecipeStep"]
