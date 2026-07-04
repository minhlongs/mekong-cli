"""Markdown constitution parser.

Reads a ZENOS.md constitution file and returns a structured ``Constitution``
object. All structural constants are imported from the shared ``format_schema``
module so that Phase 2 (producer) and Phase 5 (parser) stay in sync.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.mekong.constitution.format_schema import (
    AUTHORIZED_HEADERS,
    CONSTITUTION_HEADER_RE,
    MAX_LINES,
    MIN_ARTICLES,
    REQUIRED_ARTICLES,
    has_required_articles,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Article:
    """A single article parsed from a constitution document."""

    number: int
    title: str
    content: str
    category: str = ""


@dataclass
class Constitution:
    """Parsed representation of a ZENOS.md constitution file."""

    name: str
    articles: list[Article] = field(default_factory=list)
    lines: int = 0

    # --- derived helpers ---

    @property
    def article_titles(self) -> list[str]:
        return [a.title for a in self.articles]

    @property
    def categories(self) -> list[str]:
        return sorted({a.category for a in self.articles if a.category})

    def get_article_by_number(self, number: int) -> Optional[Article]:
        for a in self.articles:
            if a.number == number:
                return a
        return None

    def has_category(self, category: str) -> bool:
        return any(a.category == category for a in self.articles)

    def missing_required(self) -> list[str]:
        """Return required article titles that are not present."""
        return has_required_articles(self.article_titles)


# ---------------------------------------------------------------------------
# Category classifier
# ---------------------------------------------------------------------------


_CATEGORY_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"mission", re.IGNORECASE), "mission"),
    (re.compile(r"govern(ance|ed|or)", re.IGNORECASE), "governance"),
    (re.compile(r"capture|evolution", re.IGNORECASE), "governance"),
    (re.compile(r"ai\b|\bautomation", re.IGNORECASE), "ai_cells"),
    (re.compile(r"economic|token|reward|treasury", re.IGNORECASE), "economics"),
    (re.compile(r"exit|withdraw|leave", re.IGNORECASE), "exit"),
    (re.compile(r"common|open(ness| source)|shared|public good", re.IGNORECASE), "commons"),
]


def _classify_article(title: str) -> str:
    """Classify an article into one of the ``ARTICLE_CATEGORIES``."""
    for pattern, category in _CATEGORY_RULES:
        if pattern.search(title):
            return category
    return ""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def parse_constitution(path: str | Path) -> Constitution:
    """Parse a ZENOS.md constitution file and return a ``Constitution``.

    Raises
    ------
    ValueError
        If the file does not exist, exceeds ``MAX_LINES``, has fewer than
        ``MIN_ARTICLES``, or contains unauthorised single-hash headers
        (``# Heading`` — only ``##`` / ``###`` / ``####`` are allowed).
    """
    path = Path(path)
    if not path.exists():
        raise ValueError(f"Constitution not found: {path}")

    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    line_count = len(lines)

    if line_count > MAX_LINES:
        raise ValueError(
            f"Constitution has {line_count} lines, exceeds limit of {MAX_LINES}"
        )

    # Scan for unauthorised single-hash headers inside the constitution body.
    # A ``# Title`` preamble before the first ``## Article`` header is allowed.
    _check_header_depth(lines)

    # Find article headers and extract articles by position.
    articles: list[Article] = _extract_articles(lines)

    if len(articles) < MIN_ARTICLES:
        raise ValueError(
            f"Constitution has {len(articles)} articles, "
            f"minimum required is {MIN_ARTICLES}"
        )

    name = path.stem
    return Constitution(name=name, articles=articles, lines=line_count)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _check_header_depth(lines: list[str]) -> None:
    """Raise ``ValueError`` if a bare ``# `` header appears in the body.

    A ``# Title`` preamble before the first ``## Article`` header is allowed.
    Any ``# `` header that appears after the first article header is rejected.
    """
    seen_article = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line is an article header — once we see one, we are
        # inside the constitution body.
        if CONSTITUTION_HEADER_RE.match(stripped):
            seen_article = True
            continue

        # Reject bare ``# `` headers only when inside the body.
        if seen_article and (stripped.startswith("# ") or stripped == "#"):
            if not any(stripped.startswith(h) for h in AUTHORIZED_HEADERS):
                raise ValueError(
                    f"Line {i + 1}: unauthorised header '{stripped}'. "
                    f"Only {', '.join(AUTHORIZED_HEADERS)} headers are allowed."
                )


def _extract_articles(lines: list[str]) -> list[Article]:
    """Return all ``Article`` instances found in *lines*."""
    headers: list[tuple[int, int, str]] = []  # (line_index, number, title)

    for i, line in enumerate(lines):
        m = CONSTITUTION_HEADER_RE.match(line.strip())
        if m:
            num = int(m.group(1))
            title = m.group(2).strip()
            headers.append((i, num, title))

    articles: list[Article] = []
    for idx, (start, num, title) in enumerate(headers):
        end = headers[idx + 1][0] if idx + 1 < len(headers) else len(lines)
        content_lines = lines[start + 1 : end]
        content = "\n".join(line.rstrip() for line in content_lines).strip()
        category = _classify_article(title)
        articles.append(
            Article(number=num, title=title, content=content, category=category)
        )

    return articles
