"""Chat TUI configuration: model registry, defaults, secrets resolution."""

from __future__ import annotations

import os
from pathlib import Path

# Model aliases → raw OmniRoute gateway ids.
# Default = zunef Claude (real, quality output).
# pmv text models may fall back to low-quality upstreams (e.g. nemotron) —
# the TUI renders markdown actively and banners the actual model.
MODELS: dict[str, str] = {
    "default": "anthropic-compatible-c33c2c9c-e3e4-47ae-b231-fda23ffef734/claude-sonnet-5-0",
    "minimax": "pmv/kimchi/minimax-m3",
    "kimi": "pmv/kimchi/kimi-k2.7",
}

DEFAULT_MODEL = MODELS["default"]

CHAT_PATH = "/v1/chat/completions"

_OMNI_KEY_FILE = Path.home() / "opc/secrets/omni.key"


def resolve_base_url() -> str:
    """Resolve OmniRoute base URL: env first, else LAN default."""
    return os.environ.get("OMNIROUTE_BASE_URL", "http://192.168.1.231:20128")


def resolve_token() -> str:
    """Resolve API token: OMNIROUTE_TOKEN env → ~/opc/secrets/omni.key → error."""
    token = os.environ.get("OMNIROUTE_TOKEN", "").strip()
    if token:
        return token
    try:
        lines = _OMNI_KEY_FILE.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    except OSError:
        pass
    raise RuntimeError(
        "Missing OmniRoute token. Set OMNIROUTE_TOKEN env var or create "
        f"{_OMNI_KEY_FILE} with the token on the first non-comment line."
    )


def resolve_model(model: str | None) -> str:
    """Resolve a model alias or raw id; unknown alias raises KeyError."""
    if not model:
        return DEFAULT_MODEL
    alias = model.strip()
    if alias in MODELS:
        return MODELS[alias]
    return alias  # assume raw gateway id
