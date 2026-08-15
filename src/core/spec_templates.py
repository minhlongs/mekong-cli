"""Template loader for SDD markdown artifacts.

Reads ``.specify/templates/*-template.md``, applies ``{key}`` substitution
via :func:`str.format`, and writes rendered artifacts to disk.

Gracefully handles missing templates by returning an empty string so callers
can always fall back without crashing.
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import UTC, datetime
from typing import Any

TEMPLATES_DIR = Path(".specify/templates")
_TEMPLATE_CACHE: dict[str, str] | None = None


def _load_all() -> dict[str, str]:
    """Load all ``*-template.md`` files into a name → content mapping.

    Keyed by the stem portion (``spec-template`` → ``spec``).
    Cached after first call so subsequent loads skip the filesystem.
    """
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE is not None:
        return _TEMPLATE_CACHE

    cache: dict[str, str] = {}
    if TEMPLATES_DIR.is_dir():
        for path in sorted(TEMPLATES_DIR.glob("*-template.md")):
            cache[path.stem.replace("-template", "")] = path.read_text(encoding="utf-8")

    _TEMPLATE_CACHE = cache
    return cache


def load_template(name: str) -> str:
    """Return raw template text for **name**, or ``""`` if not found."""
    return _load_all().get(name, "")


def render(template_name: str, context: dict[str, Any]) -> str:
    """Apply ``{key}`` substitution to the named template.

    Missing keys are silently left unreplaced (standard ``str.format``
    behaviour with ``MissingKeyError`` caught below).
    """
    template = load_template(template_name)
    if not template:
        return ""

    # Add a default timestamp so callers don't need to pass it manually
    context.setdefault("timestamp", datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"))

    try:
        return template.format_map(_SafeDict(context))
    except (KeyError, ValueError):
        # On substitution error, return the unrendered template so callers
        # can see what went wrong rather than silently producing empty output.
        return template


def write_artifact(
    path: str | Path,
    template_name: str,
    context: dict[str, Any],
) -> Path:
    """Render **template_name** with **context** and write to **path**.

    Creates parent directories automatically. Returns the resolved path.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render(template_name, context), encoding="utf-8")
    return target.resolve()


def write_json_artifact(
    path: str | Path,
    data: dict[str, Any],
    indent: int = 2,
) -> Path:
    """Serialise **data** to **path** as pretty-printed JSON.

    Creates parent directories automatically. Returns the resolved path.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")
    return target.resolve()


class _SafeDict(dict[str, Any]):
    """Dict subclass that returns the original placeholder on missing keys.

    Prevents ``str.format_map`` from raising ``KeyError`` so templates can
    contain optional placeholders without each call needing to supply every
    key.
    """

    def __missing__(self, key: str) -> str:  # noqa: D105
        return "{" + key + "}"
