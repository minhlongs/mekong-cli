"""Migration: normalize raw_model_ids and model_aliases to API/local prefixed ids.

This is an additive, idempotent SQLite migration:
- creates model_aliases if missing
- backfills normalized_id for unknown/unprefixed ids
- inserts normalized aliases for raw ids that match CONTEXT_WINDOW_MAP keys

Run once: python3 migrations/fix_model_ids.py
Supports --dry-run / --batch-size.
"""

from __future__ import annotations

import argparse
import logging
import sqlite3
import sys
from pathlib import Path
from typing import NamedTuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_DB = "data/engine.db"
DEFAULT_BATCH = 500

# Source of truth for prefixes available in this codebase.
KNOWN_PREFIXES = ("ollama:", "openai:", "gemini:", "mlx:", "deepseek:", "qwen:", "llama:", "mistral:")
CHAIN_MODEL_RE = r"^(gemini|openai|ollama|mlx|deepseek|qwen|llama|mistral):([\w.\-]+)$"


class Row(NamedTuple):
    id: int
    raw_model_id: str
    normalized_id: str | None


class Migration(NamedTuple):
    batch_size: int
    dry_run: bool


def has_prefix(value: str) -> bool:
    return any(value.startswith(p) for p in KNOWN_PREFIXES)


def prefixed(value: str, default: str = "ollama:") -> str:
    return value if has_prefix(value) else f"{default}{value}"


def open_connection(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"database not found: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def ensure_alias_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS model_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT UNIQUE NOT NULL,
            normalized_id TEXT NOT NULL,
            provider TEXT,
            is_local INTEGER NOT NULL DEFAULT 0,
            model_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def candidates_without_normalized(conn: sqlite3.Connection, batch_size: int) -> list[Row]:
    rows: list[sqlite3.Row] = conn.execute(
        """
        SELECT id, raw_model_id, normalized_id
        FROM model_aliases
        WHERE normalized_id IS NULL
           OR TRIM(normalized_id) = ''
        ORDER BY id
        LIMIT ?
        """,
        (batch_size,),
    ).fetchall()
    return [Row(r["id"], r["raw_model_id"], r["normalized_id"]) for r in rows]


def backfill_normalized(conn: sqlite3.Connection, rows: list[Row]) -> int:
    updated = 0
    for row in rows:
        normalized = prefixed(row.raw_model_id)
        conn.execute(
            "UPDATE model_aliases SET normalized_id = ? WHERE id = ?",
            (normalized, row.id),
        )
        logger.info("backfill id=%s %s -> %s", row.id, row.raw_model_id, normalized)
        updated += 1
    return updated


def ids_that_are_local(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT normalized_id FROM model_aliases WHERE is_local = 1 AND prefixed(normalized_id) = normalized_id"
    ).fetchall()
    return {r["normalized_id"] for r in rows if r["normalized_id"]}


def insert_aliases(conn: sqlite3.Connection, batch_size: int) -> int:
    rows = conn.execute(
        "SELECT raw_model_id, normalized_id FROM model_aliases ORDER BY id"
    ).fetchall()
    logger.info("existing alias rows: %s", len(rows))

    local_models: set[str] = {r["normalized_id"] for r in rows if r["normalized_id"] and r["normalized_id"].startswith("ollama:")}

    aliases: list[tuple[str, str, str, int, str]] = []
    for row in rows:
        source = row["raw_model_id"]
        normalized = row["normalized_id"]
        if not normalized:
            continue
        if not has_prefix(source):
            aliases.append((source, normalized, "fallback", 1 if normalized in local_models else 0, f"{source} -> {normalized}"))
    if not aliases:
        return 0
    conn.executemany(
        """
        INSERT OR IGNORE INTO model_aliases (model_id, normalized_id, provider, is_local, model_name)
        VALUES (?, ?, ?, ?, ?)
        """,
        aliases,
    )
    logger.info("inserted %s alias rows", len(aliases))
    return len(aliases)


def run(migration: Migration, db_path: str) -> int:
    path = Path(db_path)
    conn = open_connection(path)
    try:
        ensure_alias_table(conn)
        rows = candidates_without_normalized(conn, migration.batch_size)
        if not rows:
            logger.info("no rows missing normalized_id")
            return 0
        if migration.dry_run:
            logger.info("dry-run mode; would update %s rows", len(rows))
            for row in rows:
                logger.info("  id=%s %s", row.id, prefixed(row.raw_model_id))
            return len(rows)
        updated = backfill_normalized(conn, rows)
        conn.commit()
        inserted = insert_aliases(conn, migration.batch_size)
        conn.commit()
        logger.info("migrated %s rows", updated)
        return updated + inserted
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="normalize model_id values to prefixed ids")
    parser.add_argument("--db", default=DEFAULT_DB)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    migration = Migration(batch_size=max(1, args.batch_size), dry_run=args.dry_run)
    try:
        updated = run(migration, args.db)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 2
    logger.info("done; updated+inserted=%s", updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())