"""The Signals Loop — tracks task events and surfaces improvement opportunities.

Events: task_submitted, task_completed, task_failed, user_satisfied
Output: weekly analysis via LLM → action items → A/B test candidates
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SIGNALS_FILE = Path(os.getenv("SIGNALS_FILE", "/tmp/mekong-signals.jsonl"))


def _append(event: dict) -> None:
    event["ts"] = datetime.now(timezone.utc).isoformat()
    with SIGNALS_FILE.open("a") as f:
        f.write(json.dumps(event) + "\n")


def track_submitted(user: str, task: str) -> None:
    _append({"event": "task_submitted", "user": user, "task": task[:200]})


def track_completed(user: str, task: str, score: int, outputs: list[str]) -> None:
    _append({
        "event": "task_completed",
        "user": user,
        "task": task[:200],
        "score": score,
        "output_count": len(outputs),
    })


def track_failed(user: str, task: str, error: str) -> None:
    _append({"event": "task_failed", "user": user, "task": task[:200], "error": error[:500]})


def track_satisfied(user: str, rating: int) -> None:
    _append({"event": "user_satisfied", "user": user, "rating": rating})


def load_signals(limit: int = 500) -> list[dict]:
    if not SIGNALS_FILE.exists():
        return []
    lines = SIGNALS_FILE.read_text().strip().split("\n")
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    return events


def analyze_weekly() -> str:
    """Use LLM to analyze recent signals and propose improvements."""
    events = load_signals(200)
    if not events:
        return "No signals to analyze yet."

    completed = [e for e in events if e["event"] == "task_completed"]
    failed = [e for e in events if e["event"] == "task_failed"]
    avg_score = sum(e.get("score", 7) for e in completed) / max(len(completed), 1)

    summary = (
        f"Last {len(events)} events: "
        f"{len(completed)} completed (avg score {avg_score:.1f}/10), "
        f"{len(failed)} failed.\n"
    )
    if failed:
        summary += "Top failures:\n"
        for e in failed[:3]:
            summary += f"  - {e.get('error', '')[:100]}\n"

    try:
        from seed.llm_client import get_llm_client
        llm = get_llm_client()
        prompt = (
            f"You are analyzing an AI agent platform's performance.\n{summary}\n"
            "Propose 3 concrete improvements to reduce failures and improve scores. "
            "Be specific and actionable."
        )
        response = llm.chat([{"role": "user", "content": prompt}])
        return f"{summary}\n📈 AI Analysis:\n{response}"
    except Exception as e:
        return f"{summary}\n[Analysis unavailable: {e}]"


if __name__ == "__main__":
    print(analyze_weekly())
