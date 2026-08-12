#!/usr/bin/env python3
"""
Database maintenance jobs for RaaS SQLite databases.

Task #69: Optimize database queries for scale

Run this script periodically (e.g., via cron) to:
- Clean up old processed_events records (> 90 days)
- Vacuum databases to reclaim space
- Update statistics for query planner
"""

import sqlite3
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List


# Database paths
TENANTS_DB = Path.home() / ".mekong" / "raas" / "tenants.db"
WORKSPACES_DB = Path.home() / ".mekong" / "raas" / "workspaces.db"


def cleanup_processed_events(conn: sqlite3.Connection, days_old: int = 90) -> int:
    """Delete processed_events older than specified days.

    Returns number of rows deleted.
    """
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()

    cursor = conn.execute(
        "DELETE FROM processed_events WHERE processed_at < ?",
        (cutoff_date,)
    )
    deleted = cursor.rowcount
    conn.commit()
    return deleted


def vacuum_database(conn: sqlite3.Connection) -> None:
    """Vacuum database to reclaim space and defragment."""
    conn.execute("VACUUM")


def update_stats(conn: sqlite3.Connection) -> None:
    """Update SQLite statistics for query planner."""
    conn.execute("ANALYZE")


def get_table_sizes(conn: sqlite3.Connection) -> List[dict]:
    """Get row counts for all tables."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    tables = [row[0] for row in cursor.fetchall()]

    sizes = []
    for table in tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        sizes.append({"table": table, "rows": count})

    return sizes


def maintain_database(db_path: Path, days_old: int = 90, vacuum: bool = False) -> None:
    """Run maintenance on a single database."""
    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    print(f"\nMaintaining: {db_path}")
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row

    try:
        # Show sizes before
        print("  Table sizes (before):")
        for size in get_table_sizes(conn):
            print(f"    {size['table']}: {size['rows']:,} rows")

        # Cleanup processed_events
        deleted = cleanup_processed_events(conn, days_old)
        if deleted > 0:
            print(f"  Deleted {deleted:,} old processed_events records")
        else:
            print("  No old processed_events to delete")

        # Update stats
        update_stats(conn)
        print("  Updated query planner statistics")

        # Vacuum if requested
        if vacuum:
            vacuum_database(conn)
            print("  Vacuumed database")

        # Show sizes after
        print("  Table sizes (after):")
        for size in get_table_sizes(conn):
            print(f"    {size['table']}: {size['rows']:,} rows")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Database maintenance for RaaS SQLite databases"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help="Delete processed_events older than this many days (default: 90)",
    )
    parser.add_argument(
        "--vacuum",
        action="store_true",
        help="Vacuum databases to reclaim space (slow on large DBs)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Maintain all databases (tenants.db, workspaces.db)",
    )

    args = parser.parse_args()

    print(f"Database Maintenance — Delete records older than {args.days} days")

    if args.all:
        databases = [TENANTS_DB, WORKSPACES_DB]
    else:
        databases = [TENANTS_DB]

    for db_path in databases:
        maintain_database(db_path, days_old=args.days, vacuum=args.vacuum)

    print("\nDone.")


if __name__ == "__main__":
    main()
