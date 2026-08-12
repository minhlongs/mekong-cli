"""Mekong CLI 7 — model registry.

Maps role -> gateway model id (resolved through OmniRoute combos).
Every id below is verified live against the gateway.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelEntry:
    id: str
    name: str
    role: str
    timeout_ms: int
    paid: bool = False


MODELS: dict[str, ModelEntry] = {
    "fable": ModelEntry("claude-fable-5", "Claude Fable 5 (1M)", "default/light", 45000, paid=False),
    "sonnet": ModelEntry("claude-opus-4-8[1m]", "Claude Opus 4.8 1M (sonnet-replacement)", "agent", 45000, paid=False),
    "opus": ModelEntry("claude-opus-4-8[1m]", "Claude Opus 4.8 1M", "heavy", 45000, paid=False),
    "haiku": ModelEntry("claude-haiku-4-5", "Claude Haiku 4.5", "fast", 45000, paid=False),
    "strategist": ModelEntry("strategist", "Qwen 3.8 Max (Stali)", "strategy", 120000, paid=True),
}

ROLE_TO_MODEL: dict[str, str] = {
    "default": "fable",
    "light": "fable",
    "agent": "sonnet",
    "sonnet": "sonnet",
    "heavy": "opus",
    "opus": "opus",
    "fast": "haiku",
    "haiku": "haiku",
    "strategy": "strategist",
    "strategist": "strategist",
}


# ── STRATEGIST-ONLY MODELS (user xác nhận 2026-08-12) ─────────
# claude-opus-5 + qwen3.8-max (xkiro & openrouter) CHỈ dùng bởi
# @kongming/@suntzu (Claude Code agents, model: strategist) qua combo
# strategist trên gateway: Opus 5 → xkiro/qwen/qwen3.8-max (free) →
# openrouter/qwen/qwen3.8-max (phí). MỌI đường gọi trong mk CLI
# (orchestrate/sop/omni/auto/dispatch) bị CẤM resolve ra 3 model này —
# buộc fallback claude-fable-5.
BANNED_MODEL_KEYS = {"strategist", "claude-opus-5", "claude/claude-opus-5",
                     "qwen3.8-max", "qwen/qwen3.8-max",
                     "xkiro/qwen/qwen3.8-max", "openrouter/qwen/qwen3.8-max"}
BANNED_FALLBACK_KEY = "fable"

# ── B4: Model-family fallback (OmniRoute) ─────────────────────
# Khi model gốc bị lock/banned → thử sibling cùng family theo thứ tự,
# rồi sang family khác (claude → deepseek → openrouter). qwen3.8-max KHÔNG
# bao giờ được chọn trong mk (BANNED_MODEL_KEYS guard — strategist-only).
MODEL_FAMILIES: dict[str, list[str]] = {
    "claude": ["claude-opus-5", "claude-sonnet-5", "claude-opus-4-6", "claude-fable-5"],
    "deepseek": ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4-flash2"],
    "openrouter": ["gpt-oss-20b:free", "nemotron-3-ultra-550b-a55b:free"],
}
FAMILY_ORDER = ("claude", "deepseek", "openrouter")


def family_of(model_id: str) -> str | None:
    """Family name cho một gateway model id (prefix match)."""
    low = model_id.strip().lower()
    if low.startswith("claude-"):
        return "claude"
    if low.startswith("deepseek-"):
        return "deepseek"
    if low.startswith(("qwen", "gpt-oss", "nemotron", "xkiro")):
        return "openrouter"
    return None


def fallback_chain(model_id: str) -> list[str]:
    """Sibling-first chain: family của model rồi các family khác (bỏ banned)."""
    low = model_id.strip().lower()
    fam = family_of(low)
    chain: list[str] = []
    order = [fam] + [f for f in FAMILY_ORDER if f != fam] if fam else list(FAMILY_ORDER)
    for f in order:
        for m in MODEL_FAMILIES[f]:
            if m == low or m in chain or m in BANNED_MODEL_KEYS:
                continue
            chain.append(m)
    return chain


def resolve(model_or_role: str) -> ModelEntry:
    """Resolve a role name or gateway id to a ModelEntry.

    Raises ModelBanned when the resolved target is a banned model key
    (strategist / openrouter qwen3.8-max — mk pipeline must never call it).
    """
    key = model_or_role.strip().lower()
    if key in BANNED_MODEL_KEYS:
        raise ModelBanned(key)
    if key in MODELS:
        return MODELS[key]
    if key in ROLE_TO_MODEL:
        resolved = ROLE_TO_MODEL[key]
        if resolved in BANNED_MODEL_KEYS:
            raise ModelBanned(key)
        return MODELS[resolved]
    # Assume it is a raw gateway model id (e.g. claude-sonnet-5-0).
    return ModelEntry(key, key, "custom", 45000, paid=False)


class ModelBanned(RuntimeError):
    """Raised when a banned model key (strategist / openrouter qwen3.8-max) is requested."""

    def __init__(self, key: str):
        super().__init__(f"model '{key}' is banned in mk pipeline (strategist only for @kongming/@suntzu; openrouter qwen3.8-max is paid)")


def resolve_or_fallback(model_or_role: str, locked=None) -> ModelEntry:
    """Resolve a model with fallbacks (banned → fable; locked → family chain).

    `locked` is an optional callable(model_id) -> bool. When the resolved model
    is locked (A1 breaker), walk the B4 family chain (siblings, then other
    families in claude → deepseek → xkiro → openrouter order) and return the
    first unlocked candidate. Banned keys are never returned.
    """
    try:
        entry = resolve(model_or_role)
    except ModelBanned:
        entry = MODELS[BANNED_FALLBACK_KEY]
    if locked is not None:
        for candidate in [entry.id, *fallback_chain(entry.id)]:
            if not locked(candidate):
                return _as_entry(candidate)
    return entry


def _as_entry(model_id: str) -> ModelEntry:
    if model_id in MODELS:
        return MODELS[model_id]
    return ModelEntry(model_id, model_id, "custom", 45000, paid=False)


def all_models() -> list[ModelEntry]:
    return list(MODELS.values())
