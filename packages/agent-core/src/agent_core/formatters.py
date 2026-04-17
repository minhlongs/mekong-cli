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
