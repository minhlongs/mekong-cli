"""SQLite stats writer — track local vs cloud routing + $ saved."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Literal

log = logging.getLogger(__name__)

Destination = Literal["local", "cloud"]

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS routes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT    NOT NULL,
    method         TEXT    NOT NULL,
    tokens_in      INTEGER NOT NULL DEFAULT 0,
    tokens_out     INTEGER NOT NULL DEFAULT 0,
    destination    TEXT    NOT NULL,
    cost_saved_usd REAL    NOT NULL DEFAULT 0.0,
    model          TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_routes_ts ON routes (ts);
CREATE INDEX IF NOT EXISTS idx_routes_dest ON routes (destination);
"""


@dataclass
class StatsSummary:
    total_requests: int
    local_requests: int
    cloud_requests: int
    total_tokens_in: int
    total_tokens_out: int
    total_cost_saved_usd: float

    @property
    def local_pct(self) -> float:
        return (self.local_requests / self.total_requests * 100) if self.total_requests else 0.0


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA_SQL)
        conn.commit()


@contextmanager
def _connect(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
    finally:
        conn.close()


def record_route(
    db_path: Path,
    method: str,
    tokens_in: int,
    tokens_out: int,
    destination: Destination,
    cost_saved_usd: float = 0.0,
    model: str = "",
) -> bool:
    """Persist one routing decision. Swallows exceptions."""
    try:
        init_db(db_path)
        with _connect(db_path) as conn:
            conn.execute(
                "INSERT INTO routes (ts, method, tokens_in, tokens_out, destination, "
                "cost_saved_usd, model) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    method,
                    tokens_in,
                    tokens_out,
                    destination,
                    cost_saved_usd,
                    model,
                ),
            )
            conn.commit()
        return True
    except Exception as e:
        log.warning("stats.record_route failed: %s", e)
        return False


def aggregate_stats(db_path: Path) -> StatsSummary:
    if not db_path.exists():
        return StatsSummary(0, 0, 0, 0, 0, 0.0)
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COUNT(*), "
            "SUM(CASE WHEN destination='local' THEN 1 ELSE 0 END), "
            "SUM(CASE WHEN destination='cloud' THEN 1 ELSE 0 END), "
            "COALESCE(SUM(tokens_in),0), COALESCE(SUM(tokens_out),0), "
            "COALESCE(SUM(cost_saved_usd),0) FROM routes"
        ).fetchone()
    total, local, cloud, tin, tout, saved = row
    return StatsSummary(
        total_requests=total or 0,
        local_requests=local or 0,
        cloud_requests=cloud or 0,
        total_tokens_in=tin or 0,
        total_tokens_out=tout or 0,
        total_cost_saved_usd=float(saved or 0.0),
    )


def estimate_savings(
    tokens_in: int,
    tokens_out: int,
    input_usd_per_mtok: float,
    output_usd_per_mtok: float,
) -> float:
    """USD saved if this request hit local instead of cloud."""
    return (tokens_in * input_usd_per_mtok + tokens_out * output_usd_per_mtok) / 1_000_000
