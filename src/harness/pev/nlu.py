# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""PEV orchestrator NLU — delegates to core/nlu.py.

PEV-specific intents (RECIPE_PARSE / STEP_EXECUTE / VERIFY) are promoted into
core/nlu.py so the harness sees no special cases in the fast path. This
module adds only the compatibility shim required by the harness orchestrator:

- Re-export `IntentClassifier` for callers that do `from ..nlu import
  IntentClassifier`.
- Expose `classify_intent_pev`, the PEV entry point requested by Wave B3.
- Publish `PEV_INTENTS`, the PEV-specific intent strings (mirroring the
  enum values in core/nlu.py so nothing hard-codes magic strings).
"""

from __future__ import annotations

from src.core.nlu import (
    IntentClassifier as IntentClassifier,
    IntentResult,
    Intent as IntentBase,
)

LEGACY_PEV_ALIAS_MAP: dict[str, str] = {
    "build": IntentBase.CREATE.value,
    "fix": IntentBase.FIX.value,
    "refactor": IntentBase.REFACTOR.value,
    "deploy": IntentBase.DEPLOY.value,
    "review": IntentBase.AUDIT.value,
}

PEV_ALIAS_KEYWORDS: dict[str, list[str]] = {
    "build": ["build", "build this", "build the"],
    "refactor": ["refactor", "refactor this", "restructure"],
    "review": ["review", "review this", "review code", "code review", "review the"],
}


def classify_intent(text: str) -> str | IntentResult:
    """Return the PEV-specific classification for ``text``.

    This is a thin wrapper around ``src.core.nlu.classify_intent`` that
    preserves the historical caller contract used in
    ``src/harness/pev/orchestrator/runner.py``: callers expect the result to
    be comparable with the PEV legacy alias strings. Core returns a string
    lower-case enum value; this wrapper uppercases it so callers can compare
    against ``"UNKNOWN"`` etc. without case sensitivity bugs.
    """
    raw: str | IntentResult = _core_classify(text)
    if isinstance(raw, IntentResult):
        raw = raw.intent.value if hasattr(raw.intent, "value") else str(raw.intent)
    return str(raw).upper()


def classify_intent_pev(text: str) -> str:
    """Classify with PEV-specific intents, fallback to core.

    Matching semantics (bind: rule 2):
    - Only the legacy PEV intents (BUILD/FIX/REFACTOR/DEPLOY/REVIEW) may be
      produced via alias mapping. All other results must come from core/nlu.py
      unchanged.
    - If every path produces more than one best-alias with equal score, the
      function returns ``"UNKNOWN"`` rather than choosing arbitrarily.
    """
    if not isinstance(text, str) or not text.strip():
        return "UNKNOWN"

    raw = _core_classify(text)
    if isinstance(raw, IntentResult):
        core_str = raw.intent.value if hasattr(raw.intent, "value") else str(raw.intent)
    else:
        core_str = str(raw)

    core_str = (core_str or "unknown").strip().lower()
    if core_str != "unknown":
        return core_str.upper()

    # PEV-specific fallback via legacy alias keyword matching.
    aliases: dict[str, float] = {}
    text_lower = text.lower()
    for alias, keywords in PEV_ALIAS_KEYWORDS.items():
        score = 0.0
        for keyword in keywords:
            if keyword in text_lower:
                score += 0.9 if " " in keyword else 0.7
        if score > 0:
            aliases[alias] = score

    if aliases:
        unique_best = _unique_best(aliases)
        if unique_best is not None:
            return LEGACY_PEV_ALIAS_MAP[unique_best].upper()

    return "UNKNOWN"


def _core_classify(text: str) -> str | IntentResult:
    try:
        from src.core.nlu import classify_intent as _classify_intent  # type: ignore[attr-defined]
        return _classify_intent(text)
    except Exception:
        return "UNKNOWN"


def _unique_best(aliases: dict[str, float]) -> str | None:
    if not aliases:
        return None
    best = max(aliases, key=lambda key: aliases[key])
    best_score = aliases[best]
    if sum(1 for score in aliases.values() if score == best_score) > 1:
        return None
    return best


PEV_INTENTS: tuple[str, str, str] = (
    "RECIPE_PARSE",
    "STEP_EXECUTE",
    "VERIFY",
)

__all__ = [
    "IntentClassifier",
    "IntentResult",
    "classify_intent",
    "classify_intent_pev",
    "PEV_INTENTS",
    "PEV_ALIAS_KEYWORDS",
    "LEGACY_PEV_ALIAS_MAP",
]
