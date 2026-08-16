# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
format_schema.py — Shared format contract for ZENOS.md.

Used by:
- Phase 2 producer (this task): creates ZENOS.md conforming to this schema.
- Phase 5 parser: reads and validates ZENOS.md using the same constants.

Any change to header patterns, required articles, or categories must be
reflected here so both producer and parser stay in sync.
"""

import re

# Regex matching constitution article headers: "## Article N: Title"
# Captures the article number and title text.
CONSTITUTION_HEADER_PATTERN: str = r"^## Article (\d+): (.+)$"
CONSTITUTION_HEADER_RE: re.Pattern = re.compile(CONSTITUTION_HEADER_PATTERN, re.MULTILINE)

# Articles that MUST appear in the constitution for it to be valid.
REQUIRED_ARTICLES: list[str] = [
    "Mission Integrity",
    "Right to Exit",
    "Anti-Capture and Evolution",
]

# Top-level categories an article can belong to.
ARTICLE_CATEGORIES: list[str] = [
    "mission",
    "governance",
    "ai_cells",
    "economics",
    "exit",
    "commons",
]

# Hard limits enforced by both producer and parser.
MAX_LINES: int = 200           # Total constitution length (excl. preamble/footer)
MIN_ARTICLES: int = 3          # Minimum number of articles required

# Markdown headers that are authorised inside the constitution body.
AUTHORIZED_HEADERS: list[str] = [
    "##",
    "###",
    "####",
]


def parse_article_header(line: str) -> tuple[int, str] | None:
    """Parse a line into (article_number, title) or None if it is not a header."""
    m = CONSTITUTION_HEADER_RE.match(line.strip())
    if m:
        return int(m.group(1)), m.group(2).strip()
    return None


def is_authorized_header(line: str) -> bool:
    """Return True if the line starts with an authorised header prefix."""
    stripped = line.strip()
    return any(stripped.startswith(h) for h in AUTHORIZED_HEADERS)


def has_required_articles(article_titles: list[str]) -> list[str]:
    """Return a list of required articles missing from *article_titles*."""
    found = {t.strip().lower() for t in article_titles}
    missing: list[str] = []
    for req in REQUIRED_ARTICLES:
        if req.lower() not in found:
            missing.append(req)
    return missing
