"""OmniRoute poller — quota, health, recent calls (via ssh on M1 Pro)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

SSH_HOST = "m1pro-home"
SSH_PORT = "2222"
BUDGET_SH = "bash $HOME/opc/scripts/budget.sh status"
HEALTHZ = "http://192.168.1.231:20128/healthz"
CALLS_QUERY = "bash $HOME/opc/scripts/omni-calls.sh 6"


@dataclass
class OmniPoll:
    health: str = "?"
    quota: str = "?"
    today_count: str = "?"
    recent: str = ""
    error: str = ""


def _ssh(cmd: str, timeout: int = 15) -> str:
    # wrap remote cmd in single quotes so the LOCAL shell does not expand
    # $PATH / ~ — only the remote shell sees them
    remote = f"export PATH=/opt/homebrew/bin:/usr/local/bin:$PATH; {cmd}"
    full = f"ssh -p {SSH_PORT} {SSH_HOST} -- '{remote}'"
    proc = subprocess.run(
        full, shell=True, capture_output=True, text=True, timeout=timeout,
    )
    return proc.stdout.strip()


def poll_all() -> OmniPoll:
    result = OmniPoll()
    try:
        result.health = _ssh(f"curl -sf --max-time 5 {HEALTHZ} || echo DOWN") or "?"
    except Exception as exc:
        result.error = str(exc)
    try:
        quota_raw = _ssh(BUDGET_SH)
        result.quota = quota_raw.splitlines()[0] if quota_raw else "?"
        for line in quota_raw.splitlines():
            if line.startswith("usage_today="):
                result.today_count = line.split("=")[1].split()[0]
    except Exception as exc:
        result.error = f"{result.error}; quota: {exc}"
    try:
        recent = _ssh(CALLS_QUERY)
        result.recent = "\n".join(recent.splitlines()[:6]) if recent else "(no calls)"
    except Exception as exc:
        result.error = f"{result.error}; calls: {exc}"
    return result
