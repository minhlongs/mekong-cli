"""Recipe parser — real Markdown → structured Recipe implementation.

Wave B5: replaces stub with production parser. Supported format:

    ## Goal
    Brief description of what to achieve

    ## Steps
    1. Step title
       Step description (optional indented block)

    2. Another step
       Description

    ## Verification
    - Check that file exists
    - Run `python test.py`
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class RecipeStep:
    order: int
    title: str
    description: str = ""
    params: dict = field(default_factory=dict)


@dataclass
class Recipe:
    name: str = ""
    title: str = ""
    steps: List[RecipeStep] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)


class RecipeParser:
    """Parse Markdown recipe files into structured Recipe objects."""

    _SECTION_RE = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    _STEP_RE = re.compile(r"^(\d+)\.\s+(.+)$", re.MULTILINE)
    _CHECK_RE = re.compile(r"^-\s+(.+)$", re.MULTILINE)

    def parse(self, filepath: Path) -> Recipe:
        """Parse a Markdown recipe file."""
        content = Path(filepath).read_text(encoding="utf-8")
        return self.parse_string(content, name=str(filepath))

    def parse_steps(self, content: str) -> List[RecipeStep]:
        """Extract steps from Markdown content string."""
        return self.parse_string(content).steps

    def parse_string(self, content: str, name: str = "inline") -> Recipe:
        recipe = Recipe(name=name)
        sections = self._split_sections(content)

        for heading, body in sections.items():
            heading_lower = heading.lower()
            if heading_lower == "goal":
                recipe.title = body.strip().split("\n")[0].strip()
            elif heading_lower == "steps":
                recipe.steps = self._parse_steps(body)
            elif heading_lower == "verification":
                recipe.verification = self._parse_checks(body)

        return recipe

    def _split_sections(self, content: str) -> dict[str, str]:
        """Split Markdown content into {heading: body} dict."""
        parts = self._SECTION_RE.split(content)
        sections: dict[str, str] = {}
        for i in range(1, len(parts), 2):
            heading = parts[i].strip()
            body = parts[i + 1] if i + 1 < len(parts) else ""
            sections[heading] = body
        return sections

    def _parse_steps(self, body: str) -> List[RecipeStep]:
        """Parse `## Steps` body into RecipeStep list."""
        steps: List[RecipeStep] = []
        matches = list(self._STEP_RE.finditer(body))
        for idx, m in enumerate(matches):
            order = int(m.group(1))
            title = m.group(2).strip()
            start = m.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
            desc = body[start:end].strip().lstrip(": \t\n")
            params = self._detect_params(title, desc)
            steps.append(RecipeStep(order=order, title=title, description=desc, params=params))
        return steps

    def _parse_checks(self, body: str) -> List[str]:
        return [m.group(1).strip() for m in self._CHECK_RE.finditer(body)]

    def _detect_params(self, title: str, desc: str) -> dict:
        """Extract hints from step title/description."""
        params: dict = {}
        text = f"{title} {desc}".lower()
        if "verify" in text or "check" in text:
            params["type"] = "verification"
        elif "write" in text or "create" in text or "build" in text:
            params["type"] = "creation"
        if "python" in text or ".py" in text:
            params["language"] = "python"
        elif "js" in text or "javascript" in text:
            params["language"] = "javascript"
        return params


__all__ = ["Recipe", "RecipeParser", "RecipeStep"]
