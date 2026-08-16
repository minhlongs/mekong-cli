# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SQLite schema for the ZenOS behavior graph module.

Tables
------
entities
    Registered particles and external actors in the graph.
behaviors
    Directed, typed edges representing actions between entities.
trust_scores
    Computed trust values (0-100 integer) between entity pairs.
collusion_flags
    Detected collusion patterns with evidence blobs.
graph_meta
    Schema version tracking for migrations.
"""

from __future__ import annotations

import sqlite3

# ---------------------------------------------------------------------------
# Schema version — bump when adding migrations
# ---------------------------------------------------------------------------

SCHEMA_VERSION = 1

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------

CREATE_ENTITIES = """
CREATE TABLE IF NOT EXISTS entities (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    kind        TEXT NOT NULL DEFAULT 'particle',
    metadata    TEXT DEFAULT '{}',
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

CREATE_BEHAVIORS = """
CREATE TABLE IF NOT EXISTS behaviors (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   TEXT NOT NULL REFERENCES entities(id),
    target_id   TEXT NOT NULL REFERENCES entities(id),
    action      TEXT NOT NULL,
    payload     TEXT DEFAULT '{}',
    value       REAL DEFAULT 0.0,
    constitutional_review TEXT
        DEFAULT 'not_reviewed'
        CHECK(constitutional_review IN ('passed','failed','pending','not_reviewed')),
    constitutional_violation TEXT,
    timestamp   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
"""

# Indexes from day one — NOT added retroactively
INDEX_BEHAVIORS_ACTION_TIMESTAMP = """
CREATE INDEX IF NOT EXISTS idx_behaviors_action_timestamp
    ON behaviors(action, timestamp);
"""

INDEX_BEHAVIORS_SOURCE_ENTITY = """
CREATE INDEX IF NOT EXISTS idx_behaviors_source_entity
    ON behaviors(source_id, target_id);
"""

INDEX_BEHAVIORS_TARGET_ENTITY = """
CREATE INDEX IF NOT EXISTS idx_behaviors_target_entity
    ON behaviors(target_id, source_id);
"""

INDEX_BEHAVIORS_SOURCE_ACTION = """
CREATE INDEX IF NOT EXISTS idx_behaviors_source_action
    ON behaviors(source_id, action, timestamp);
"""

CREATE_TRUST_SCORES = """
CREATE TABLE IF NOT EXISTS trust_scores (
    source_id     TEXT NOT NULL REFERENCES entities(id),
    target_id     TEXT NOT NULL REFERENCES entities(id),
    score         INTEGER NOT NULL CHECK(score >= 0 AND score <= 100),
    confidence    INTEGER NOT NULL CHECK(confidence >= 0 AND confidence <= 100),
    raw_alpha     REAL NOT NULL DEFAULT 0.0,
    raw_beta      REAL NOT NULL DEFAULT 0.0,
    raw_gamma     REAL NOT NULL DEFAULT 0.0,
    raw_delta     REAL NOT NULL DEFAULT 0.0,
    raw_epsilon   REAL NOT NULL DEFAULT 0.0,
    raw_zeta      REAL NOT NULL DEFAULT 0.0,
    behavior_count INTEGER NOT NULL DEFAULT 0,
    updated_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (source_id, target_id)
);
"""

CREATE_COLLUSION_FLAGS = """
CREATE TABLE IF NOT EXISTS collusion_flags (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern       TEXT NOT NULL,
    entity_a_id   TEXT NOT NULL REFERENCES entities(id),
    entity_b_id   TEXT NOT NULL REFERENCES entities(id),
    evidence      TEXT NOT NULL DEFAULT '{}',
    severity      TEXT NOT NULL DEFAULT 'medium' CHECK(severity IN ('low', 'medium', 'high', 'critical')),
    detected_at   TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    cleared_at    TEXT
);
"""

CREATE_GRAPH_META = """
CREATE TABLE IF NOT EXISTS graph_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

SCHEMA_TABLES: list[str] = [
    CREATE_ENTITIES,
    CREATE_BEHAVIORS,
    INDEX_BEHAVIORS_ACTION_TIMESTAMP,
    INDEX_BEHAVIORS_SOURCE_ENTITY,
    INDEX_BEHAVIORS_TARGET_ENTITY,
    INDEX_BEHAVIORS_SOURCE_ACTION,
    CREATE_TRUST_SCORES,
    CREATE_COLLUSION_FLAGS,
    CREATE_GRAPH_META,
]


def init_db(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes if they do not exist.

    Migrations are tracked via the ``graph_meta`` table under the ``schema_version`` key.
    """
    for stmt in SCHEMA_TABLES:
        conn.execute(stmt)

    # Record / check schema version
    row = conn.execute(
        "SELECT value FROM graph_meta WHERE key = 'schema_version'"
    ).fetchone()

    if row is None:
        conn.execute(
            "INSERT INTO graph_meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
    else:
        existing = int(row[0])
        if existing < SCHEMA_VERSION:
            _run_migrations(conn, existing, SCHEMA_VERSION)
            conn.execute(
                "UPDATE graph_meta SET value = ? WHERE key = 'schema_version'",
                (str(SCHEMA_VERSION),),
            )

    conn.commit()


def _run_migrations(
    conn: sqlite3.Connection, from_version: int, to_version: int
) -> None:
    """Apply schema migrations between *from_version* and *to_version*."""
    # Future migrations go here as ``if from_version < N: ...`` blocks.
    _ = from_version, to_version  # placeholder for future migration blocks
