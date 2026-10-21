"""Legacy watcher bridge dependency lookup helpers."""

from __future__ import annotations

import sys
from typing import Any

_BRIDGE_MODULE = "src.core.watcher_bridge"


def bridge_value(name: str, fallback: Any) -> Any:
    """Return a facade override when legacy callers monkeypatch it."""
    bridge = sys.modules.get(_BRIDGE_MODULE)
    if bridge is None:
        return fallback
    return getattr(bridge, name, fallback)
