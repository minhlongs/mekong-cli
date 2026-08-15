"""Mekong CLI 7 — Intent router.

Natural-language request -> structured intent via a JSON-strict Haiku call.
Extracts: task_type, skill_hint, target_agent, danger_level, confidence.
Low confidence (<0.7) raises HitlGate so the operator can disambiguate.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .llm import LLMClient
from .models import resolve_or_fallback

CONFIDENCE_THRESHOLD = 0.7

TASK_TYPES = [
    "strategy",
    "approval",
    "client",
    "revenue",
    "product",
    "spec",
    "code",
    "deploy",
    "monitoring",
    "incident",
    "research",
    "docs",
    "other",
]

AGENTS = ["sun-tzu", "ceo", "ae", "pm", "eng", "ops"]

DANGER_LEVELS = ["low", "medium", "high", "critical"]


class HitlGate(RuntimeError):
    """Raised when intent confidence is too low; operator must disambiguate."""

    def __init__(self, raw: str, hint: str = ""):
        super().__init__(f"intent confidence too low — need operator input ({hint})")
        self.raw = raw
        self.hint = hint


@dataclass
class Intent:
    task_type: str
    skill_hint: str
    target_agent: str
    danger_level: str
    confidence: float
    raw_text: str = ""

    @property
    def is_dangerous(self) -> bool:
        return self.danger_level in ("high", "critical")


SYSTEM_PROMPT = (
    "You are an intent router for a solo-dev agent harness. Given one natural-language "
    "request, classify it into a JSON object with EXACTLY these fields:\n"
    '{"task_type": string, "skill_hint": string, "target_agent": string, '
    '"danger_level": string, "confidence": number}\n'
    f"task_type one of: {TASK_TYPES}\n"
    f"target_agent one of: {AGENTS}\n"
    f"danger_level one of: {DANGER_LEVELS} (low=read-only, medium=edits local, "
    "high=deploy/rm/git push --force, critical=spend money/delete data)\n"
    "skill_hint: short lowercase snake_case hint of the skill/slash-command to use "
    "(e.g. fix, cook, plan, debug, docs, strategist, binh-phap).\n"
    "confidence: 0.0-1.0 how sure you are of the classification.\n"
    "Return ONLY the JSON object, no prose, no code fence."
)


def _parse_intent(raw: str) -> dict[str, Any] | None:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except Exception:
        m = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not m:
            return None
        try:
            data = json.loads(m.group(0))
        except Exception:
            return None
    return data if isinstance(data, dict) else None


class IntentRouter:
    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    def classify(self, request: str, max_tokens: int = 256) -> Intent:
        """Classify a natural-language request into an Intent.

        Raises HitlGate when confidence < CONFIDENCE_THRESHOLD.
        Falls back across models (haiku -> openrouter free)
        when the primary model is unavailable. strategist is BANNED
        (qwen3.8-max only for @kongming/@suntzu) — never a candidate.
        """
        candidates = ["haiku", "openrouter-free"]
        last_err: Exception | None = None
        last_hitl: HitlGate | None = None
        for key in candidates:
            try:
                raw = self._classify_one(key, request, max_tokens)
                return self._build_intent(raw)
            except HitlGate as e:
                last_hitl = e
                continue  # try next model before giving up
            except Exception as e:
                last_err = e
                continue
        if last_hitl is not None:
            raise last_hitl
        raise last_err or HitlGate("all classifier models failed", "gateway unavailable")

    def _classify_one(self, key: str, request: str, max_tokens: int) -> str:
        from .models import resolve_or_fallback

        if key == "openrouter-free":
            return self.client.text(
                "openrouter/openai/gpt-oss-20b:free",
                request,
                system=SYSTEM_PROMPT,
                max_tokens=max_tokens,
            )
        entry = resolve_or_fallback(key)
        return self.client.text(entry.id, request, system=SYSTEM_PROMPT, max_tokens=max_tokens)

    def _build_intent(self, raw: str) -> Intent:
        data = _parse_intent(raw)

        if not data:
            # Fallback: unparseable reply -> treat as low confidence -> HITL.
            raise HitlGate(raw, "unparseable classifier reply")

        task_type = str(data.get("task_type", "other"))
        skill_hint = str(data.get("skill_hint", ""))
        target_agent = str(data.get("target_agent", "ceo"))
        danger_level = str(data.get("danger_level", "low"))
        try:
            confidence = float(data.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0

        # Normalize against known enums; unknown values drop to safe defaults.
        if task_type not in TASK_TYPES:
            task_type = "other"
        if target_agent not in AGENTS:
            target_agent = "ceo"
        if danger_level not in DANGER_LEVELS:
            danger_level = "low"

        intent = Intent(
            task_type=task_type,
            skill_hint=skill_hint,
            target_agent=target_agent,
            danger_level=danger_level,
            confidence=confidence,
            raw_text=raw,
        )

        if confidence < CONFIDENCE_THRESHOLD:
            raise HitlGate(raw, hint=f"confidence={confidence:.2f}")
        return intent
