"""
Pipeline Executor — Runs scheduled solo-ops pipelines via agent_loop.run_agent_sync().

Reads `solo_ops_loops` from .mekong/solo-ops-config.json, checks each pipeline's
cron schedule against current time, and fires run_agent_sync() for due pipelines.

Usage:
    python3 -m src.daemon.pipeline_executor
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
MEKONG_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = MEKONG_ROOT / ".mekong" / "solo-ops-config.json"
LOG_DIR = MEKONG_ROOT / ".mekong" / "logs"

# ── System prompts per pipeline ────────────────────────────────────────────────
PIPELINE_PROMPTS: dict[str, str] = {
    "lead_scan": "Scan .mekong/leads/ for new opportunities. Summarize findings.",
    "content_batch": "Generate 3 social media posts about AI automation for business.",
    "support_triage": "Check .mekong/support/ for new tickets. Triage by priority.",
    "sales_ops": "Review .mekong/sales/ pipeline. Update status of active deals.",
    "monitor": "Check system health. Report any issues in .mekong/logs/.",
}

# Tier label → model_tier arg accepted by run_agent_sync
TIER_MAP: dict[str, str] = {
    "fast": "fast",
    "deep": "deep",
}


# ── Cron matching ──────────────────────────────────────────────────────────────

def _field_matches(field: str, value: int) -> bool:
    """Return True if cron field string matches integer value."""
    if field == "*":
        return True
    # Step syntax: */N
    if field.startswith("*/"):
        step = int(field[2:])
        return value % step == 0
    # List syntax: 1,3,5
    if "," in field:
        return value in {int(v) for v in field.split(",")}
    # Range syntax: 1-5
    if "-" in field:
        lo, hi = field.split("-")
        return int(lo) <= value <= int(hi)
    # Literal
    return value == int(field)


def is_due(schedule: str, now: datetime | None = None) -> bool:
    """
    Simple 5-field cron check: minute hour dom month dow.
    DOM and month always match (not implemented — overkill for ops loops).
    """
    if now is None:
        now = datetime.now()
    try:
        minute, hour, _dom, _month, dow = schedule.split()
    except ValueError:
        logger.warning(f"[PipelineExec] Malformed schedule: {schedule!r}")
        return False

    # Cron DOW: 0=Sun…6=Sat. Python weekday(): 0=Mon…6=Sun.
    # Convert Python weekday → cron DOW: (weekday + 1) % 7
    cron_dow = (now.weekday() + 1) % 7
    return (
        _field_matches(minute, now.minute)
        and _field_matches(hour, now.hour)
        and _field_matches(dow, cron_dow)
    )


# ── Logging helper ─────────────────────────────────────────────────────────────

def _log_result(name: str, output: str, error: str | None) -> None:
    """Append run result to .mekong/logs/pipeline-{name}.log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"pipeline-{name}.log"
    ts = datetime.now().isoformat(timespec="seconds")
    entry = f"[{ts}] {'ERROR: ' + error if error else 'OK'}\n{output}\n{'─' * 60}\n"
    log_path.open("a").write(entry)


# ── Core runner ────────────────────────────────────────────────────────────────

def run_due_pipelines(now: datetime | None = None) -> list[dict]:
    """
    Check all pipelines and run those whose schedule matches `now`.

    Returns a list of result dicts: {name, ran, success, output, error}.
    """
    if now is None:
        now = datetime.now()

    if not CONFIG_FILE.exists():
        logger.error(f"[PipelineExec] Config not found: {CONFIG_FILE}")
        return []

    try:
        config = json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError as exc:
        logger.error(f"[PipelineExec] Config parse error: {exc}")
        return []

    loops: dict = config.get("solo_ops_loops", {})
    results: list[dict] = []

    # Lazy import — only available on M1 Max where agent_loop exists
    try:
        from .agent_loop import run_agent_sync
    except ImportError as exc:
        logger.error(f"[PipelineExec] Cannot import agent_loop: {exc}")
        return []

    for name, cfg in loops.items():
        schedule: str = cfg.get("schedule", "")
        tier: str = TIER_MAP.get(cfg.get("tier", "fast"), "fast")
        prompt: str = PIPELINE_PROMPTS.get(name, f"Run {name} pipeline.")

        if not is_due(schedule, now):
            results.append({"name": name, "ran": False})
            continue

        logger.info(f"[PipelineExec] Running pipeline: {name} (tier={tier})")
        error: str | None = None
        output: str = ""

        try:
            output = run_agent_sync(prompt, model_tier=tier)
            success = True
        except Exception as exc:
            error = str(exc)
            success = False
            logger.error(f"[PipelineExec] Pipeline {name} failed: {exc}")

        _log_result(name, output, error)
        results.append({"name": name, "ran": True, "success": success, "output": output, "error": error})
        logger.info(f"[PipelineExec] {name} → {'OK' if success else 'FAIL'}")

    return results


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    results = run_due_pipelines()
    ran = [r for r in results if r.get("ran")]
    skipped = len(results) - len(ran)
    print(f"Ran {len(ran)} pipeline(s), skipped {skipped} (not due).")
    for r in ran:
        status = "OK" if r.get("success") else f"FAIL: {r.get('error', '')}"
        print(f"  {r['name']}: {status}")
    sys.exit(0 if all(r.get("success", True) for r in ran) else 1)
