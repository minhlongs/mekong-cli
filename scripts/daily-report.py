#!/usr/bin/env python3
"""Daily performance report for CashClaw paper/live trading.

Runs at end of each day (cron or manual):
1. Query ai_decisions for today's resolved predictions
2. Calculate: Brier score, win rate, P&L, calibration
3. Compare against DNA targets
4. Write report to data/reports/daily-YYYY-MM-DD.md
"""

from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


DB_PATH = os.getenv("DATABASE_PATH", "data/algo-trade.db")
REPORTS_DIR = "data/reports"

# DNA targets
TARGET_BRIER = 0.20
TARGET_WIN_RATE = 0.55
TARGET_MIN_TRADES = 5
TARGET_MAX_TRADES = 20


def calculate_brier_score(predicted: list[float], actual: list[float]) -> float:
    """Calculate Brier score: mean squared error of probability predictions."""
    if not predicted:
        return 1.0
    return sum((p - a) ** 2 for p, a in zip(predicted, actual)) / len(predicted)


def generate_report(date_str: str | None = None) -> str:
    """Generate daily performance report."""
    if date_str is None:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    if not Path(DB_PATH).exists():
        return f"# Daily Report — {date_str}\n\nNo database found at {DB_PATH}.\n"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        # Get today's resolved decisions
        rows = conn.execute(
            """SELECT predicted_probability, actual_outcome, pnl, direction,
                      edge, market_id, question
               FROM ai_decisions
               WHERE date(timestamp) = ? AND resolved = 1""",
            (date_str,),
        ).fetchall()

        # Get all decisions (including unresolved) for trade count
        all_today = conn.execute(
            "SELECT COUNT(*) FROM ai_decisions WHERE date(timestamp) = ?",
            (date_str,),
        ).fetchone()

    total_trades = all_today[0] if all_today else 0
    resolved = len(rows)

    if resolved == 0:
        predicted, actual, pnls = [], [], []
    else:
        predicted = [r["predicted_probability"] for r in rows]
        actual = [r["actual_outcome"] for r in rows]
        pnls = [r["pnl"] or 0 for r in rows]

    brier = calculate_brier_score(predicted, actual)
    total_pnl = sum(pnls)
    winning = sum(1 for p in pnls if p > 0)
    win_rate = winning / resolved if resolved > 0 else 0.0
    avg_edge = sum(r["edge"] or 0 for r in rows) / resolved if resolved > 0 else 0.0

    # Status checks
    brier_ok = brier < TARGET_BRIER
    win_rate_ok = win_rate > TARGET_WIN_RATE
    pnl_ok = total_pnl > 0
    trades_ok = TARGET_MIN_TRADES <= total_trades <= TARGET_MAX_TRADES

    report = f"""# CashClaw Daily Report — {date_str}

## Performance Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total Trades | {total_trades} | {TARGET_MIN_TRADES}-{TARGET_MAX_TRADES} | {"PASS" if trades_ok else "WARN"} |
| Resolved | {resolved} | — | — |
| Brier Score | {brier:.4f} | < {TARGET_BRIER} | {"PASS" if brier_ok else "FAIL"} |
| Win Rate | {win_rate * 100:.1f}% | > {TARGET_WIN_RATE * 100}% | {"PASS" if win_rate_ok else "FAIL"} |
| P&L | ${total_pnl:+.2f} | > $0 | {"PASS" if pnl_ok else "FAIL"} |
| Avg Edge | {avg_edge * 100:.1f}% | — | — |

## Overall: {"ALL CLEAR" if all([brier_ok, win_rate_ok, pnl_ok]) else "NEEDS ATTENTION"}

"""

    if not brier_ok and resolved >= 10:
        report += "### WARNING: Calibration drift detected. Run CalibrationTuner.\n\n"

    if rows:
        report += "## Trade Log\n\n"
        report += "| Market | Direction | Edge | P&L |\n"
        report += "|--------|-----------|------|-----|\n"
        for r in rows:
            q = (r["question"] or "")[:40]
            report += f"| {q} | {r['direction']} | {(r['edge'] or 0) * 100:.1f}% | ${(r['pnl'] or 0):+.2f} |\n"

    return report


def main() -> None:
    """Generate and save daily report."""
    date_str = sys.argv[1] if len(sys.argv) > 1 else None
    report = generate_report(date_str)

    # Save to file
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    date_for_file = date_str or datetime.utcnow().strftime("%Y-%m-%d")
    report_path = f"{REPORTS_DIR}/daily-{date_for_file}.md"
    Path(report_path).write_text(report)

    print(report)
    print(f"\nReport saved to {report_path}")


if __name__ == "__main__":
    main()
