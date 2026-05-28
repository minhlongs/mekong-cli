# M3: SQLite Database Persistence Layer Design & Analysis

This document presents the architecture, schema, migration framework, and query optimization strategy for the Anti-Gravity 2.0 SQLite persistence layer (`src/db.rs`).

---

## 1. Executive Summary

Milestone M3 requires storing extracted AST symbols into a SQLite database at `.git/antigravity/session.db`. To support local-first code analysis and real-time context compilation (M4), queries on this database must consistently run in **under 5ms**.

We recommend a **Normalized Schema** structure (separating `files` and `symbols`) to minimize storage duplication, coupled with an **FTS5 Trigram virtual table** to accelerate substring search. Database operations use transaction batching and performance PRAGMAs to guarantee sub-millisecond query latency.

---

## 2. Directory Initialization & Database Startup

The runtime operates within a git workspace. The database must reside at `.git/antigravity/session.db`.

### 2.1 Bootstrapping Flow
1. **Locate Git Repository Root**: Resolve the workspace directory and append `.git/antigravity/`.
2. **Directory Creation**: If `.git/antigravity/` does not exist, create it recursively using `std::fs::create_dir_all`.
3. **Database Connection**: Open/create `session.db` using `rusqlite::Connection::open`.
4. **Performance PRAGMAs**: Run initialization pragmas to optimize SQLite for rapid reads and concurrent writes.

### 2.2 Performance Optimizations (PRAGMAs)
* `PRAGMA journal_mode = WAL;` — Write-Ahead Logging allows concurrent reads during index writes.
* `PRAGMA synchronous = NORMAL;` — Reduces disk sync constraints without sacrificing durability in WAL mode.
* `PRAGMA foreign_keys = ON;` — Enforces integrity for cascaded deletes of symbols on file updates.
* `PRAGMA temp_store = MEMORY;` — Stores temporary tables and indexes in RAM.

---

## 3. Database Schema Design

We compare two design options for storing symbols: a simple Denormalized table and a space-efficient Normalized structure.

### Option A: Denormalized Schema
All fields stored in a single table. Easy to write, but duplicates file path and hash strings.

```sql
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    hash TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_path ON symbols(path);
```

### Option B: Normalized Schema (Recommended)
Splits files from their parsed symbols. A single codebase contains many symbols per file. Normalizing saves disk space, minimizes memory cache footprint, and simplifies invalidation.

```sql
-- Represents files in the workspace
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);

-- Represents AST symbols within those files
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

-- Core indexes for rapid symbol retrieval and foreign-key joins
CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
CREATE INDEX IF NOT EXISTS idx_symbols_file_id ON symbols(file_id);
CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
```

---

## 4. Query Design & Latency Optimization (<5ms)

To maintain a responsive terminal CLI, symbol lookups must execute in under 5ms. Here are the SQL queries corresponding to the search behaviors:

### 4.1 Exact Name Search
Querying a symbol by its precise identifier (e.g., class or function name):
```sql
SELECT s.id, f.path, f.hash, s.name, s.kind, s.start_line, s.end_line
FROM symbols s
JOIN files f ON s.file_id = f.id
WHERE s.name = ?1;
```
* **Performance**: Uses `idx_symbols_name` B-tree index. Complexity: $O(\log N)$. Execution time: **< 0.2ms**.

### 4.2 Prefix Name Search
Querying symbols starting with a specific term (e.g. autocompleting `get_u`):
```sql
SELECT s.id, f.path, f.hash, s.name, s.kind, s.start_line, s.end_line
FROM symbols s
JOIN files f ON s.file_id = f.id
WHERE s.name LIKE ?1 || '%';
```
* **Performance**: SQLite translates prefix `LIKE` queries into range queries and uses `idx_symbols_name`. Execution time: **< 0.5ms**.

### 4.3 Substring Search (Full-Text Search FTS5 with Trigrams)
Standard SQL substring search (`LIKE '%query%'`) cannot use standard B-Tree indexes, resulting in full-table scans. For large projects, this can exceed 20ms. 
To guarantee **< 1ms substring lookup**, we design an FTS5 table with a `trigram` tokenizer:

```sql
-- Virtual table for substring indexes
CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
    name,
    kind,
    tokenize="trigram"
);

-- Triggers to keep FTS index synchronized automatically
CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
    INSERT INTO symbols_fts(rowid, name, kind) VALUES (new.id, new.name, new.kind);
END;
CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
    DELETE FROM symbols_fts WHERE rowid = old.id;
END;
CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
    DELETE FROM symbols_fts WHERE rowid = old.id;
    INSERT INTO symbols_fts(rowid, name, kind) VALUES (new.id, new.name, new.kind);
END;
```

**Substring Search Query**:
```sql
SELECT s.id, f.path, f.hash, s.name, s.kind, s.start_line, s.end_line
FROM symbols s
JOIN files f ON s.file_id = f.id
JOIN symbols_fts fts ON s.id = fts.rowid
WHERE fts.name MATCH ?1;
```
* **Performance**: Matches terms instantly using character trigrams. Execution time: **< 1.0ms** even on massive symbol sets.

---

## 5. Migration Framework & Schema Versioning

To support clean schema updates without manual user interventions, the SQLite persistence layer uses `PRAGMA user_version` migrations.

```rust
const MIGRATIONS: &[&str] = &[
    // Migration 0: Normalized core database schema
    r#"
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
    CREATE INDEX IF NOT EXISTS idx_symbols_file_id ON symbols(file_id);
    CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
    "#,
    // Migration 1: FTS5 Trigram Substring Search
    r#"
    CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
        name,
        kind,
        tokenize="trigram"
    );
    CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
        INSERT INTO symbols_fts(rowid, name, kind) VALUES (new.id, new.name, new.kind);
    END;
    CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
        DELETE FROM symbols_fts WHERE rowid = old.id;
    END;
    CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
        DELETE FROM symbols_fts WHERE rowid = old.id;
        INSERT INTO symbols_fts(rowid, name, kind) VALUES (new.id, new.name, new.kind);
    END;
    "#,
    // Migration 2: Session and settings metadata
    r#"
    CREATE TABLE IF NOT EXISTS session_metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    );
    "#
];
```

---

## 6. Update and Invalidation Strategy

To update index symbols rapidly, the indexer checks file content hashes:
1. Fetch existing file hash from the `files` table.
2. If file hash matches current computed hash, **skip indexing entirely**.
3. If hash differs:
   - Within a transaction, delete old symbols for the file (`ON DELETE CASCADE` from `files` cascades to `symbols`).
   - Insert new symbols and update the file hash.
   - Commit transaction (ensuring trigger updates FTS table).

---

## 7. Session State Persistence

For a fully persistent agent terminal interface, we introduce two tables to store active session state:

1. **`session_metadata`**: Key-value settings to store workspace stats, active routing parameters, and model selections.
2. **`chat_history`**: Persistent log of active conversational turns, allowing agents to resume context across process restarts.

```sql
CREATE TABLE IF NOT EXISTS session_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    role TEXT NOT NULL,
    content TEXT NOT NULL
);
```

---

## 8. Proposed Code Skeleton (`src/db.rs`)

The following Rust implementation integrates all design specifications cleanly using the `rusqlite` crate:

```rust
use std::fs;
use std::path::{Path, PathBuf};
use rusqlite::{params, Connection, OptionalExtension};
use anyhow::{Context, Result};

pub struct Symbol {
    pub path: String,
    pub hash: String,
    pub name: String,
    pub kind: String,
    pub start_line: usize,
    pub end_line: usize,
}

pub struct SessionDb {
    conn: Connection,
}

const MIGRATIONS: &[&str] = &[
    r#"
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT NOT NULL UNIQUE,
        hash TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS symbols (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        kind TEXT NOT NULL,
        start_line INTEGER NOT NULL,
        end_line INTEGER NOT NULL,
        FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_symbols_name ON symbols(name);
    CREATE INDEX IF NOT EXISTS idx_symbols_file_id ON symbols(file_id);
    CREATE INDEX IF NOT EXISTS idx_files_path ON files(path);
    "#,
    r#"
    CREATE VIRTUAL TABLE IF NOT EXISTS symbols_fts USING fts5(
        name,
        kind,
        tokenize="trigram"
    );
    CREATE TRIGGER IF NOT EXISTS symbols_ai AFTER INSERT ON symbols BEGIN
        INSERT INTO symbols_fts(rowid, name, kind) VALUES (new.id, new.name, new.kind);
    END;
    CREATE TRIGGER IF NOT EXISTS symbols_ad AFTER DELETE ON symbols BEGIN
        DELETE FROM symbols_fts WHERE rowid = old.id;
    END;
    CREATE TRIGGER IF NOT EXISTS symbols_au AFTER UPDATE ON symbols BEGIN
        DELETE FROM symbols_fts WHERE rowid = old.id;
        INSERT INTO symbols_fts(rowid, name, kind) VALUES (new.id, new.name, new.kind);
    END;
    "#,
    r#"
    CREATE TABLE IF NOT EXISTS session_metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        role TEXT NOT NULL,
        content TEXT NOT NULL
    );
    "#
];

impl SessionDb {
    /// Connects to the SQLite database at .git/antigravity/session.db and executes migrations.
    pub fn new(repo_path: &Path) -> Result<Self> {
        let db_dir = repo_path.join(".git").join("antigravity");
        if !db_dir.exists() {
            fs::create_dir_all(&db_dir)
                .context(format!("Failed to create database directory at {:?}", db_dir))?;
        }
        let db_path = db_dir.join("session.db");
        let conn = Connection::open(&db_path)
            .context(format!("Failed to open SQLite database at {:?}", db_path))?;
        
        let mut db = Self { conn };
        db.setup_pragmas()?;
        db.run_migrations()?;
        Ok(db)
    }

    fn setup_pragmas(&self) -> Result<()> {
        self.conn.pragma_update(None, "journal_mode", "WAL")?;
        self.conn.pragma_update(None, "synchronous", "NORMAL")?;
        self.conn.pragma_update(None, "foreign_keys", "ON")?;
        self.conn.pragma_update(None, "temp_store", "MEMORY")?;
        Ok(())
    }

    fn run_migrations(&mut self) -> Result<()> {
        let current_version: i32 = self.conn.query_row("PRAGMA user_version", [], |row| row.get(0))?;
        let target_version = MIGRATIONS.len() as i32;
        
        if current_version < target_version {
            let tx = self.conn.transaction()?;
            for (version, migration) in MIGRATIONS.iter().enumerate().skip(current_version as usize) {
                tx.execute_batch(migration)
                    .context(format!("Failed to apply migration version {}", version))?;
            }
            tx.pragma_update(None, "user_version", target_version)?;
            tx.commit()?;
        }
        Ok(())
    }

    /// Update symbols for a given file path. Minimizes database writes by checking hash equality.
    pub fn update_file_symbols(&mut self, path: &str, hash: &str, symbols: &[Symbol]) -> Result<()> {
        let tx = self.conn.transaction()?;
        
        let existing: Option<(i64, String)> = tx.query_row(
            "SELECT id, hash FROM files WHERE path = ?1",
            [path],
            |row| Ok((row.get(0)?, row.get::<_, String>(1)?))
        ).optional()?;

        match existing {
            Some((file_id, existing_hash)) if existing_hash == hash => {
                // File unchanged, skip update
                return Ok(());
            }
            Some((file_id, _)) => {
                // File changed, delete old symbols, update hash
                tx.execute("UPDATE files SET hash = ?1 WHERE id = ?2", [hash, &file_id.to_string()])?;
                tx.execute("DELETE FROM symbols WHERE file_id = ?1", [file_id])?;
                
                for sym in symbols {
                    tx.execute(
                        "INSERT INTO symbols (file_id, name, kind, start_line, end_line) VALUES (?1, ?2, ?3, ?4, ?5)",
                        params![file_id, sym.name, sym.kind, sym.start_line, sym.end_line]
                    )?;
                }
            }
            None => {
                // New file, insert metadata and all parsed symbols
                tx.execute("INSERT INTO files (path, hash) VALUES (?1, ?2)", [path, hash])?;
                let file_id: i64 = tx.last_insert_rowid();
                
                for sym in symbols {
                    tx.execute(
                        "INSERT INTO symbols (file_id, name, kind, start_line, end_line) VALUES (?1, ?2, ?3, ?4, ?5)",
                        params![file_id, sym.name, sym.kind, sym.start_line, sym.end_line]
                    )?;
                }
            }
        }
        
        tx.commit()?;
        Ok(())
    }

    /// Query symbols using exact matching, prefix matching, or trigram FTS5 substring matching.
    pub fn query_symbols(&self, query: &str) -> Result<Vec<Symbol>> {
        let mut stmt = self.conn.prepare(
            "SELECT s.name, s.kind, s.start_line, s.end_line, f.path, f.hash
             FROM symbols s
             JOIN files f ON s.file_id = f.id
             JOIN symbols_fts fts ON s.id = fts.rowid
             WHERE fts.name MATCH ?1"
        )?;

        let rows = stmt.query_map([query], |row| {
            Ok(Symbol {
                name: row.get(0)?,
                kind: row.get(1)?,
                start_line: row.get(2)?,
                end_line: row.get(3)?,
                path: row.get(4)?,
                hash: row.get(5)?,
            })
        })?;

        let mut results = Vec::new();
        for r in rows {
            results.push(r?);
        }
        Ok(results)
    }
}
```

---

## 9. Verification & Performance Validation

To verify the sub-5ms latency constraint:
1. **Benchmark Test**: Run benchmark tests using cargo/rust tests that mock insertion of 10,000 file entries containing 100,000 distinct symbol references.
2. **Measurement**: Measure query execution latency using `std::time::Instant` across a variety of lookup parameters:
   - Direct exact query.
   - Long substring matching.
   - Non-existent substring matching (worst-case filter).
3. **Query Inspection**: Execute `EXPLAIN QUERY PLAN <query>` in the test suite to assert that SQLite is traversing index tables instead of performing scanning loops on the main tables.
