# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Load tenant use-case configs from tenants/*.json."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

TENANTS_DIR = Path(__file__).resolve().parent.parent.parent / "tenants"


@lru_cache(maxsize=1)
def load_all_tenants() -> dict[str, dict]:
    """Load all tenant configs into {slug: config} dict. Cached."""
    configs: dict[str, dict] = {}
    if not TENANTS_DIR.is_dir():
        return configs
    for f in sorted(TENANTS_DIR.glob("*.json")):
        if f.name.startswith("_"):
            continue
        with open(f) as fh:
            cfg = json.load(fh)
            configs[cfg["slug"]] = cfg
    return configs


def get_tenant_config(slug: str) -> Optional[dict]:
    """Get single tenant config by slug. Returns None if not found."""
    return load_all_tenants().get(slug)


def list_tenant_slugs() -> list[str]:
    """Return sorted list of all tenant slugs."""
    return sorted(load_all_tenants().keys())
