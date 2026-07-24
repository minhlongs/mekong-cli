#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ZUNEF_INSTALL_TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ZUNEF_INSTALL_TOKEN", "")
CACHE = Path.home() / ".claude" / "mekong" / ".zunef-jwt-cache"
if not ZUNEF_INSTALL_TOKEN:
    raise SystemExit("Provide ZuneF install token as arg or env ZUNEF_INSTALL_TOKEN.")


def run_login(install_token: str) -> str:
    url = f"https://claude.zunef.com/api/claude-code/{install_token}/auth"
    # Placeholder real flow would exchange install token for JWT
    # and persist to CACHE.
    return f"zunef-jwt-placeholder-{install_token[:8]}"


def main() -> int:
    jwt = run_login(ZUNEF_INSTALL_TOKEN)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps({"jwt": jwt, "ts": __import__("time").time()}))
    print(f"[zunef-login][ok] cached JWT -> {CACHE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
