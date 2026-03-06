---
title: "Phase 1 — Usage Queue Async Buffer"
description: "Create UsageQueue class with asyncio.Queue and SQLite fallback"
status: completed
priority: P2
effort: 1.5h
parent_plan: 260306-2301-usage-metering-phase4
---

# Phase 1 — Usage Queue Async Buffer

## Context Links

- Parent Plan: `plans/260306-2301-usage-metering-phase4/plan.md`
- Related: `src/lib/usage_meter.py`, `src/db/repository.py`
- Logging: `src/config/logging_config.py`

## Overview

Create async queue layer to buffer usage events before flushing to PostgreSQL.

**Why Queue?**
- Shell execution is sync; usage recording is async
- Prevent blocking command execution on DB latency/failure
- SQLite buffer as fallback if DB unavailable

## Architecture

```
┌──────────────────────────────────────────────┐
│  UsageQueue                                  │
│   ┌────────────┐     ┌──────────────────┐   │
│   │ asyncio    │────▶│ Background       │   │
│   │ Queue      │     │ Worker           │   │
│   └────────────┘     └──────────────────┘   │
│                              │                │
│                     ┌────────▼────────┐      │
│                     │ PostgreSQL      │      │
│                     │ (primary)       │      │
│                     └────────┬────────┘      │
│                              │                │
│                     ┌────────▼────────┐      │
│                     │ SQLite File     │      │
│                     │ (fallback)      │      │
│                     └─────────────────┘      │
└──────────────────────────────────────────────┘
```

## Requirements

1. Async queue with configurable max size
2. Background worker to flush events
3. SQLite fallback if PostgreSQL unavailable
4. Graceful shutdown (flush remaining events)
5. Structlog for all operations

## Implementation Steps

### Step 1: Create UsageQueue Class

```python
# src/lib/usage_queue.py
import asyncio
import sqlite3
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

import structlog

from src.config.logging_config import get_logger
from src.lib.usage_meter import UsageMeter
from src.db.repository import LicenseRepository


class UsageQueue:
    """Async queue for buffering usage events before PostgreSQL flush."""

    def __init__(
        self,
        max_size: int = 100,
        flush_interval: float = 5.0,
        sqlite_path: Optional[str] = None,
    ) -> None:
        """
        Initialize usage queue.

        Args:
            max_size: Maximum queue size before blocking
            flush_interval: Seconds between automatic flushes
            sqlite_path: Path to SQLite fallback database
        """
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self._flush_interval = flush_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._logger = get_logger(__name__)

        # SQLite fallback
        if sqlite_path is None:
            sqlite_path = ".mekong/usage_buffer.db"
        self._sqlite_path = Path(sqlite_path)
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._sqlite_conn: Optional[sqlite3.Connection] = None

        # Usage meter for recording
        self._meter = UsageMeter()

    async def start(self) -> None:
        """Start background worker."""
        self._running = True
        self._task = asyncio.create_task(self._process_queue())
        self._logger.info("usage.queue.started")

    async def stop(self) -> None:
        """Stop worker and flush remaining events."""
        self._running = False
        if self._task:
            # Flush remaining events
            await self._flush_batch()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._logger.info("usage.queue.stopped")

    async def enqueue(
        self,
        key_id: str,
        tier: str,
        command: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add usage event to queue.

        Args:
            key_id: License key ID
            tier: License tier
            command: Command that was executed
            metadata: Additional context (timestamp, exit_code, etc.)
        """
        event = {
            "key_id": key_id,
            "tier": tier,
            "command": command,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self._queue.put(event)
        self._logger.debug(
            "usage.queue.enqueued",
            key_id=key_id,
            queue_size=self._queue.qsize(),
        )

    async def _process_queue(self) -> None:
        """Background worker: flush queue periodically."""
        while self._running:
            try:
                # Wait for events or timeout
                try:
                    await asyncio.wait_for(
                        self._queue.join(),
                        timeout=self._flush_interval,
                    )
                except asyncio.TimeoutError:
                    pass

                # Flush batch
                await self._flush_batch()

            except Exception as e:
                self._logger.error(
                    "usage.queue.error",
                    error=str(e),
                )

    async def _flush_batch(self) -> None:
        """Flush all queued events to PostgreSQL."""
        batch = []
        while not self._queue.empty():
            try:
                event = self._queue.get_nowait()
                batch.append(event)
            except asyncio.QueueEmpty:
                break

        if not batch:
            return

        self._logger.info(
            "usage.queue.flushed",
            batch_size=len(batch),
        )

        # Record each event
        for event in batch:
            try:
                allowed, error = await self._meter.record_usage(
                    key_id=event["key_id"],
                    tier=event["tier"],
                    commands_count=1,
                )
                if allowed:
                    self._logger.info(
                        "usage.recorded",
                        key_id=event["key_id"],
                        tier=event["tier"],
                    )
                else:
                    self._logger.warning(
                        "usage.rejected",
                        key_id=event["key_id"],
                        reason=error,
                    )
            except Exception as e:
                # Fallback to SQLite
                await self._store_sqlite_fallback(event)
                self._logger.warning(
                    "usage.postgresql_failed",
                    key_id=event["key_id"],
                    fallback="sqlite",
                )

    def _store_sqlite_fallback(self, event: Dict[str, Any]) -> None:
        """Store event to SQLite if PostgreSQL unavailable."""
        if self._sqlite_conn is None:
            self._sqlite_conn = sqlite3.connect(self._sqlite_path)
            self._init_sqlite()

        query = """
            INSERT INTO usage_buffer (key_id, tier, command, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        self._sqlite_conn.execute(
            query,
            (
                event["key_id"],
                event["tier"],
                event["command"],
                str(event["metadata"]),
                event["timestamp"],
            ),
        )
        self._sqlite_conn.commit()

    def _init_sqlite(self) -> None:
        """Initialize SQLite schema."""
        self._sqlite_conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_buffer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT NOT NULL,
                tier TEXT NOT NULL,
                command TEXT NOT NULL,
                metadata TEXT,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._sqlite_conn.commit()
```

### Step 2: Add Global Instance

```python
# Global instance
_queue: Optional[UsageQueue] = None


def get_queue() -> UsageQueue:
    """Get global queue instance."""
    global _queue
    if _queue is None:
        _queue = UsageQueue()
    return _queue


async def init_queue() -> UsageQueue:
    """Initialize and start queue."""
    q = get_queue()
    await q.start()
    return q


__all__ = ["UsageQueue", "get_queue", "init_queue"]
```

### Step 3: Initialize on CLI Startup

Modify `src/main.py` to initialize queue on startup.

## Success Criteria

- [ ] `UsageQueue` class created with all methods
- [ ] Background worker runs without errors
- [ ] SQLite fallback works when PostgreSQL unavailable
- [ ] All operations logged with structlog
- [ ] Graceful shutdown flushes queue

## Todo List

- [ ] Create `src/lib/usage_queue.py` with full implementation
- [ ] Add global instance and helper functions
- [ ] Update `src/main.py` to initialize queue
- [ ] Test manually with sample events

## Risks

- **Queue overflow**: Max size 100 prevents memory issues
- **Worker crash**: Try-catch in loop, logs errors
- **SQLite lock**: Single-threaded, should be fine for fallback

## Next Steps

After Phase 1 complete, proceed to **Phase 6: License Key Parsing** to extract `key_id` from `RAAS_LICENSE_KEY`.
