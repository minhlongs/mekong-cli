# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""YAML frontmatter parsing and validation helpers for RecipeParser."""

from __future__ import annotations

import re
from typing import Callable, List

from .parser_models import Recipe
from .pev_types import EngineParams, ValidationConditions

FM_KEY_RE = re.compile(r"^(\w[\w_-]*)\s*:\s*(.*)$")
FM_BOOL_TRUE = re.compile(r"^(true|yes|1|on)$", re.IGNORECASE)
FM_BOOL_FALSE = re.compile(r"^(false|no|0|off|)$", re.IGNORECASE)


def cast_fm_value(
    raw: str,
    bool_true_re: re.Pattern[str] = FM_BOOL_TRUE,
    bool_false_re: re.Pattern[str] = FM_BOOL_FALSE,
) -> object:
    """Cast YAML scalar string to Python type (no PyYAML)."""
    stripped = raw.strip()
    if bool_true_re.match(stripped):
        return True
    if bool_false_re.match(stripped):
        return False
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    if (
        len(stripped) >= 2
        and stripped[0] == stripped[-1]
        and stripped[0] in ('"', "'")
    ):
        return stripped[1:-1]
    return stripped


def split_frontmatter(
    content: str,
    key_re: re.Pattern[str] = FM_KEY_RE,
    cast_fn: Callable[[str], object] = cast_fm_value,
) -> tuple[dict, str]:
    """Extract YAML frontmatter (--- delimited) and remaining body."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    fm_text = content[3:end].strip()
    body = content[end + 3 :].lstrip("\n")
    parsed: dict = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = key_re.match(line)
        if m:
            key = m.group(1).lower()
            raw = m.group(2).strip()
            if " #" in raw:
                raw = raw[: raw.index(" #")].strip()
            parsed[key] = cast_fn(raw)
    return parsed, body


def apply_frontmatter(recipe: Recipe, fm: dict) -> None:
    """Apply parsed frontmatter to recipe fields."""
    meta_keys = {
        "id",
        "name",
        "description",
        "version",
        "category",
        "max_retries",
        "timeout",
    }
    for key, value in fm.items():
        if key in meta_keys:
            recipe.metadata[key] = value

    recipe.intent = fm.get("intent", "")

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


def checks_to_validation(checks: List[str]) -> ValidationConditions:
    """Convert raw check strings into ValidationConditions (soft/hard split)."""
    soft: List[str] = []
    hard: List[str] = []
    hard_prefixes = (
        "output contains",
        "exit_code",
        "file_exists",
        "file_not_exists",
    )
    for check in checks:
        stripped = check.strip()
        if stripped.lower().startswith("soft:"):
            soft.append(stripped[5:].strip())
        elif stripped.lower().startswith("hard:"):
            hard.append(stripped[5:].strip())
        elif any(stripped.startswith(p) for p in hard_prefixes):
            hard.append(stripped)
        else:
            soft.append(stripped)
    return ValidationConditions(soft=soft, hard=hard)
