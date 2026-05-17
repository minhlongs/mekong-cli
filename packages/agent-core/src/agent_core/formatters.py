"""Text formatters for `agent-core report` output.

Extracted from cli.py so the command dispatcher stays lean and formatters
can be reused/tested independently.
"""

from __future__ import annotations


def format_breakdown(by_model: dict[str, dict[str, int]]) -> str:
    """Render signal breakdown dict as fixed-width table. Empty → friendly message."""
    if not by_model:
        return "Chưa có signal nào. Gửi feedback bằng `agent-core signal good|bad`."
    header = f"{'Model':<32}{'Good':>8}{'Bad':>8}{'Ratio':>10}"
    sep = "-" * len(header)
    rows = [header, sep]
    total_good = total_bad = 0
    for model, counts in sorted(by_model.items()):
        good, bad = int(counts.get("good", 0)), int(counts.get("bad", 0))
        total_good += good
        total_bad += bad
        ratio = good / (good + bad) if (good + bad) else 0.0
        display = model if model else "(unknown)"
        rows.append(f"{display:<32}{good:>8}{bad:>8}{ratio:>10.2f}")
    rows.append(sep)
    total = total_good + total_bad
    total_ratio = total_good / total if total else 0.0
    rows.append(f"{'TOTAL':<32}{total_good:>8}{total_bad:>8}{total_ratio:>10.2f}")
    return "\n".join(rows)


_USER_MARKER = "#user"


def classify_signal_source(note: str | None) -> str:
    """Return ``user`` when the signal note carries the ``#user`` marker, else ``auto``.

    Forest workers emit notes shaped ``forest/{user_id}/{job_id}``; the user
    feedback endpoint appends ``#user`` before any freeform text. Anything else
    (including empty) counts as an auto signal.
    """
    if note and _USER_MARKER in note:
        return "user"
    return "auto"


def breakdown_from_signals(
    signals: list[dict], source: str | None = None
) -> dict[str, dict[str, int]]:
    """Rebuild a ``{model: {good, bad}}`` breakdown from a raw signal list.

    ``source`` ∈ ``{None, "auto", "user", "all"}`` — ``None`` and ``"all"`` are
    equivalent.
    """
    want = source if source and source != "all" else None
    out: dict[str, dict[str, int]] = {}
    for s in signals:
        if want and classify_signal_source(s.get("note")) != want:
            continue
        model = s.get("model") or ""
        kind = s.get("kind")
        if kind not in ("good", "bad"):
            continue
        bucket = out.setdefault(model, {"good": 0, "bad": 0})
        bucket[kind] += 1
    return out


def format_recent_notes(signals: list[dict]) -> str:
    """Render recent signals as a timestamped note tail. Empty → friendly message."""
    if not signals:
        return "\nKhông có note gần đây."
    lines = ["", "Recent notes (newest first):"]
    for s in signals:
        ts = (s.get("ts") or "")[:19]
        kind = s.get("kind", "?")
        model = s.get("model") or "(unknown)"
        note = s.get("note") or "(no note)"
        lines.append(f"  {ts}  [{kind:<4}]  {model:<24}  {note}")
    return "\n".join(lines)


def format_history(rows: list[dict]) -> str:
    """Render persisted FeedbackSession rounds as fixed-width table, newest first."""
    if not rows:
        return (
            "Chưa có phiên feedback nào được ghi. "
            "Chạy `agent-core orchestrate --rounds 2 \"...\"` để tạo."
        )
    header = (
        f"{'When':<20}{'R':>3}{'Verdict':>10}{'Score':>7}"
        f"{'Trend':>12}  {'Goal':<60}"
    )
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        ts = (r.get("created_at") or "")[:19]
        lines.append(
            f"{ts:<20}{int(r.get('round', 0)):>3}"
            f"{r.get('verdict', '?'):>10}{int(r.get('score', 0)):>7}"
            f"{r.get('trend', '?'):>12}  {r.get('goal', ''):<60}"
        )
    return "\n".join(lines)


def format_status(
    agent_rows: dict[str, int],
    last_session_at: str | None,
    retention_env: str | None,
    memory_root: str,
) -> str:
    """Operator-facing snapshot: memory root, retention, row counts per agent_id."""
    retention_display = (
        f"{retention_env} (auto-prune on)"
        if retention_env and retention_env.isdigit() and int(retention_env) > 0
        else "unbounded"
    )
    last = last_session_at or "(never)"
    last_line = (
        f"  last feedback round : {last[:19]}"
        if last != "(never)"
        else "  last feedback round : (never)"
    )
    lines = [
        "agent-core status",
        f"  memory root         : {memory_root}",
        f"  retention env       : AGENT_CORE_SESSION_RETENTION={retention_env or '(unset)'}",
        f"  retention effective : {retention_display}",
        last_line,
        "",
        "Rows per agent_id (newest activity first):",
    ]
    if not agent_rows:
        lines.append("  (memory is empty)")
        return "\n".join(lines)
    header = f"  {'Agent':<28}{'Rows':>8}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for agent_id, count in agent_rows.items():
        display = agent_id if agent_id else "(unknown)"
        lines.append(f"  {display:<28}{count:>8}")
    return "\n".join(lines)


def format_forest_status(data: dict) -> str:
    """Render agent-forest gateway snapshot from fetch_forest_status() output."""
    lines = [f"agent-forest @ {data.get('base_url', '?')}"]
    err = data.get("error")
    if err:
        lines.append(f"  error: {err}")
        return "\n".join(lines)
    health = data.get("healthz") or {}
    code = health.get("status_code", "?")
    body = health.get("body") or {}
    lines.append(f"  /healthz            : HTTP {code}  service={body.get('service', '?')}")
    m = data.get("metrics") or {}
    up = int(m.get("agent_forest_up", 0))
    lines.append(f"  service up          : {'yes' if up == 1 else 'NO'}")
    lines.append(f"  queue depth         : {int(m.get('agent_forest_queue_depth', 0))}")
    lines.append(f"  workers alive       : {int(m.get('agent_forest_workers_alive', 0))}")
    last_seen = int(m.get("agent_forest_worker_last_seen_timestamp", 0))
    if last_seen > 0:
        from datetime import UTC, datetime

        ts = datetime.fromtimestamp(last_seen, tz=UTC).isoformat()[:19]
        lines.append(f"  last heartbeat utc  : {ts}")
    else:
        lines.append("  last heartbeat utc  : (none)")
    return "\n".join(lines)


def format_cost_by_model(by_model: dict[str, float], hours: int | None) -> str:
    """Render cloud cost dict as table sorted by spend desc. Empty → friendly."""
    if not by_model:
        return "\nKhông có cloud cost nào được ghi nhận."
    label = f" (last {hours}h)" if hours else ""
    lines = ["", f"Cloud cost by model{label}:"]
    total = 0.0
    for model, usd in sorted(by_model.items(), key=lambda kv: -kv[1]):
        display = model if model else "(unknown)"
        lines.append(f"  {display:<32}  ${usd:>10.4f}")
        total += usd
    lines.append(f"  {'TOTAL':<32}  ${total:>10.4f}")
    return "\n".join(lines)
