# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Recipe parser — real Markdown -> structured PEV output."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .parser_frontmatter import (
    FM_BOOL_FALSE,
    FM_BOOL_TRUE,
    FM_KEY_RE,
    apply_frontmatter,
    cast_fm_value,
    checks_to_validation,
    split_frontmatter,
)
from .parser_models import (
    Recipe,
    RecipeStep,
    build_prompt_tokens,
    detect_recipe_intent,
)
from .pev_types import (  # noqa: F401
    EngineParams,
    PromptToken,
    TokenRole,
    ValidationConditions,
)


class RecipeParser:
    """Parse Markdown recipe files into structured Recipe objects."""

    _SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    _STEP_RE = re.compile(
        r"^(\d+)\.\s+\*{0,2}(.+?)\*{0,2}(?:\s+[—–\-]\s*(.*))?$", re.MULTILINE
    )
    _CHECK_RE = re.compile(r"^-\s+(.+)$", re.MULTILINE)

    _FM_KEY_RE = FM_KEY_RE
    _FM_BOOL_TRUE = FM_BOOL_TRUE
    _FM_BOOL_FALSE = FM_BOOL_FALSE

    def parse(self, filepath: Path) -> Recipe:
        """Parse a Markdown recipe file."""
        content = Path(filepath).read_text(encoding="utf-8")
        return self.parse_string(content, name=str(filepath))

    def parse_steps(self, content: str) -> List[RecipeStep]:
        """Extract steps from Markdown content string."""
        return self.parse_string(content).steps

    def parse_string(self, content: str, name: str = "inline") -> Recipe:
        """Parse Markdown string -> Recipe with PEV structured fields."""
        recipe = Recipe(name=name)
        fm, body = self._split_frontmatter(content)
        self._apply_frontmatter(recipe, fm)

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

        recipe.prompt_tokens = self._build_prompt_tokens(recipe)
        return recipe

    def _split_frontmatter(self, content: str) -> tuple[dict, str]:
        return split_frontmatter(content, self._FM_KEY_RE, self._cast_fm_value)

    @staticmethod
    def _cast_fm_value(raw: str) -> object:
        return cast_fm_value(raw, RecipeParser._FM_BOOL_TRUE, RecipeParser._FM_BOOL_FALSE)

    def _apply_frontmatter(self, recipe: Recipe, fm: dict) -> None:
        apply_frontmatter(recipe, fm)

    def _split_sections(self, content: str) -> dict:
        parts = self._SECTION_RE.split(content)
        sections: dict = {}
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            sections[heading] = body
        return sections

    def _parse_steps(self, body: str) -> List[RecipeStep]:
        """Parse `## Steps` body -> RecipeStep list with per-step validation."""
        steps: List[RecipeStep] = []
        matches = list(self._STEP_RE.finditer(body))
        for idx, m in enumerate(matches):
            order = int(m.group(1))
            title = m.group(2).strip()
            desc_oneline = m.group(3) or ""
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
            block = body[start:end]
            _, *rest = block.split("\n", 1)
            rest_text = rest[0] if rest else ""
            desc = desc_oneline
            if rest_text.strip():
                desc = (desc + "\n" if desc else "") + rest_text.strip()

            params = self._detect_params(title, desc)
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
        return [m.group(1).strip() for m in self._CHECK_RE.finditer(body)]

    @staticmethod
    def _checks_to_validation(checks: List[str]) -> ValidationConditions:
        return checks_to_validation(checks)

    @staticmethod
    def _detect_params(title: str, desc: str) -> dict:
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

    @staticmethod
    def detect_intent(recipe: Recipe) -> str:
        return detect_recipe_intent(recipe)

    def _build_prompt_tokens(self, recipe: Recipe) -> List[PromptToken]:
        return build_prompt_tokens(recipe)


__all__ = ["Recipe", "RecipeParser", "RecipeStep"]
