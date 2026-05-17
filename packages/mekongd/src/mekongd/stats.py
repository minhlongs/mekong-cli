"""SQLite stats writer — track local vs cloud routing + $ saved."""

from __future__ import annotations

import logging
import os
import sqlite3
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator, Literal

log = logging.getLogger(__name__)

Destination = Literal["local", "cloud"]
SignalKind = Literal["good", "bad"]

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS routes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    ts             TEXT    NOT NULL,
    method         TEXT    NOT NULL,
    tokens_in      INTEGER NOT NULL DEFAULT 0,
    tokens_out     INTEGER NOT NULL DEFAULT 0,
    destination    TEXT    NOT NULL,
    cost_saved_usd REAL    NOT NULL DEFAULT 0.0,
    cost_usd       REAL    NOT NULL DEFAULT 0.0,
    model          TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_routes_ts ON routes (ts);
CREATE INDEX IF NOT EXISTS idx_routes_dest ON routes (destination);

CREATE TABLE IF NOT EXISTS signals (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ts    TEXT    NOT NULL,
    kind  TEXT    NOT NULL,
    note  TEXT    NOT NULL DEFAULT '',
    model TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_signals_kind ON signals (kind);
"""


def _migrate_signals_model(conn: sqlite3.Connection) -> None:
    """Add `model` column to pre-existing signals tables (idempotent)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(signals)").fetchall()}
    if "model" not in cols:
        conn.execute("ALTER TABLE signals ADD COLUMN model TEXT NOT NULL DEFAULT ''")


def _migrate_routes_cost_usd(conn: sqlite3.Connection) -> None:
    """Add `cost_usd` column to pre-existing routes tables (idempotent)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(routes)").fetchall()}
    if "cost_usd" not in cols:
        conn.execute("ALTER TABLE routes ADD COLUMN cost_usd REAL NOT NULL DEFAULT 0.0")


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
        _migrate_signals_model(conn)
        _migrate_routes_cost_usd(conn)
        conn.commit()
    # Owner-only permissions to avoid leaking request metadata on shared hosts.
    try:
        os.chmod(str(db_path), stat.S_IRUSR | stat.S_IWUSR)
    except OSError as e:
        log.debug("chmod 0600 failed on %s: %s", db_path, e)


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
    cost_usd: float = 0.0,
) -> bool:
    """Persist one routing decision. Swallows exceptions.

    For local routes: cost_saved_usd=estimate, cost_usd=0.
    For cloud routes: cost_saved_usd=0, cost_usd=estimate (actual cloud bill).
    """
    try:
        init_db(db_path)
        with _connect(db_path) as conn:
            conn.execute(
                "INSERT INTO routes (ts, method, tokens_in, tokens_out, destination, "
                "cost_saved_usd, cost_usd, model) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(timezone.utc).isoformat(),
                    method,
                    tokens_in,
                    tokens_out,
                    destination,
                    cost_saved_usd,
                    cost_usd,
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


def record_signal(
    db_path: Path,
    kind: SignalKind,
    note: str = "",
    model: str = "",
) -> bool:
    """Persist one operator feedback signal. Swallows exceptions."""
    try:
        init_db(db_path)
        with _connect(db_path) as conn:
            conn.execute(
                "INSERT INTO signals (ts, kind, note, model) VALUES (?, ?, ?, ?)",
                (datetime.now(timezone.utc).isoformat(), kind, note, model),
            )
            conn.commit()
        return True
    except Exception as e:
        log.warning("stats.record_signal failed: %s", e)
        return False


def aggregate_signals(db_path: Path) -> dict[str, int]:
    """Return {kind: count} for all signals. Empty dict if db missing."""
    if not db_path.exists():
        return {}
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT kind, COUNT(*) FROM signals GROUP BY kind"
        ).fetchall()
    return {kind: int(count) for kind, count in rows}


def aggregate_user_signals(db_path: Path) -> dict[str, int]:
    """Return {kind: count} for user-originated signals only (note LIKE '%#user%').

    Pairs with ``aggregate_signals`` to let operators distinguish auto-emitted
    pipeline signals from explicit human feedback forwarded by agent-forest's
    POST /task/{id}/feedback endpoint.
    """
    if not db_path.exists():
        return {}
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT kind, COUNT(*) FROM signals "
            "WHERE note LIKE ? GROUP BY kind",
            ("%#user%",),
        ).fetchall()
    return {kind: int(count) for kind, count in rows}


def list_recent_signals(db_path: Path, limit: int = 20) -> list[dict]:
    """Return last N signal rows (newest first) as dicts. Empty list when db missing."""
    if not db_path.exists() or limit <= 0:
        return []
    limit = min(int(limit), 500)
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT ts, kind, COALESCE(note,''), COALESCE(model,'') "
            "FROM signals ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [{"ts": ts, "kind": kind, "note": note, "model": model} for ts, kind, note, model in rows]


def aggregate_signals_by_model(
    db_path: Path,
    since_hours: int | None = None,
    source: str | None = None,
) -> dict[str, dict[str, int]]:
    """Return {model: {good: n, bad: n}}. Legacy rows bucket under ''.

    since_hours: if provided, include only rows newer than now-since_hours UTC.
    source: ``user`` keeps only rows whose note contains ``#user`` (emitted
            by agent-forest POST /task/{id}/feedback); ``auto`` keeps
            everything else. ``None`` or ``all`` disables the filter.
    """
    if not db_path.exists():
        return {}
    sql = "SELECT COALESCE(model,''), kind, COUNT(*) FROM signals"
    where: list[str] = []
    params: list = []
    if since_hours is not None and since_hours > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        where.append("ts >= ?")
        params.append(cutoff.isoformat())
    if source == "user":
        where.append("note LIKE ?")
        params.append("%#user%")
    elif source == "auto":
        where.append("(note IS NULL OR note NOT LIKE ?)")
        params.append("%#user%")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " GROUP BY model, kind"
    with _connect(db_path) as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    out: dict[str, dict[str, int]] = {}
    for model, kind, count in rows:
        out.setdefault(model, {"good": 0, "bad": 0})[kind] = int(count)
    return out


def cloud_cost_by_model(db_path: Path, since_hours: int | None = None) -> dict[str, float]:
    """Return {model: total_cost_usd} for cloud routes. Legacy rows bucket under ''."""
    if not db_path.exists():
        return {}
    sql = "SELECT COALESCE(model,''), SUM(cost_usd) FROM routes WHERE destination='cloud'"
    params: tuple = ()
    if since_hours is not None and since_hours > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
        sql += " AND ts >= ?"
        params = (cutoff.isoformat(),)
    sql += " GROUP BY model"
    with _connect(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return {model: float(total or 0.0) for model, total in rows if (total or 0) > 0}


def today_cloud_spent_usd(db_path: Path) -> float:
    """Sum of cost_usd for cloud routes today (UTC midnight cutoff). 0 when empty."""
    if not db_path.exists():
        return 0.0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM routes "
            "WHERE destination='cloud' AND ts >= ?",
            (f"{today}T00:00:00+00:00",),
        ).fetchone()
    return float(row[0] if row else 0.0)


def estimate_savings(
    tokens_in: int,
    tokens_out: int,
    input_usd_per_mtok: float,
    output_usd_per_mtok: float,
) -> float:
    """USD saved if this request hit local instead of cloud."""
    return (tokens_in * input_usd_per_mtok + tokens_out * output_usd_per_mtok) / 1_000_000
