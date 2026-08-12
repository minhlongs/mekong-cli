#!/usr/bin/env bash
#
# Database Migration Rollback Script
# Rolls back migrations to a specific version with safety checks
#
# Usage:
#   DATABASE_URL=${DB_URL} scripts/db-rollback.sh 014  # Rollback to version 014
#   DATABASE_URL=${DB_URL} scripts/db-rollback.sh --last 1  # Rollback 1 migration
#
# Environment:
#   DATABASE_URL - PostgreSQL connection string (required)
#   SKIP_BACKUP - Set to 'true' to skip backup (DANGEROUS - not recommended)
#
# Exit codes:
#   0 - Success
#   1 - Error
#   2 - Validation failed

set -euo pipefail

# Parse arguments
TARGET_VERSION=""
ROLLBACK_COUNT=""

if [[ $# -eq 1 ]]; then
    TARGET_VERSION="$1"
elif [[ $# -eq 2 && "$1" == "--last" ]]; then
    ROLLBACK_COUNT="$2"
else
    echo "Usage: $0 [VERSION] | --last N"
    echo "  VERSION   - Rollback to this version (e.g., 014)"
    echo "  --last N  - Rollback N most recent migrations"
    exit 1
fi

# Validate
if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL environment variable is required" >&2
    exit 1
fi

# Parse database name for backup
PGDATABASE=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
BACKUP_DIR="${BACKUP_DIR:-/tmp/backups}"
BACKUP_PREFIX="rollback-${PGDATABASE}"

echo "🔄 Database Rollback"
echo "   Database: $PGDATABASE"
echo "   Target: ${TARGET_VERSION:-last $ROLLBACK_COUNT migration(s)}"

# Safety: Confirm production
if [[ "${DATABASE_URL}" == *".production"* ]] || [[ "$PGDATABASE" == *"prod"* ]]; then
    echo ""
    echo "⚠️  WARNING: This is a PRODUCTION database!"
    echo "   A backup will be created before rollback."
    echo ""
    read -p "Type 'YES I UNDERSTAND' to continue: " CONFIRM
    if [[ "$CONFIRM" != "YES I UNDERSTAND" ]]; then
        echo "Rollback cancelled."
        exit 0
    fi
fi

# Create backup unless skipped
if [[ "${SKIP_BACKUP:-false}" != "true" ]]; then
    echo "💾 Creating backup before rollback..."
    if DATABASE_URL="$DATABASE_URL" scripts/db-backup.sh "$BACKUP_DIR" "$BACKUP_PREFIX"; then
        echo "✅ Backup created"
    else
        echo "ERROR: Backup failed - aborting rollback for safety" >&2
        exit 1
    fi
else
    echo "⚠️  Skipping backup (SKIP_BACKUP=true)"
fi

# Execute rollback
echo ""
echo "🔙 Executing rollback..."

# Use Python to perform the rollback
python3 - "$TARGET_VERSION" "$ROLLBACK_COUNT" <<'PYTHON'
import sys
import os
import asyncio

target_version = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
rollback_count = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

# Add src to path
sys.path.insert(0, '/Users/macbook/mekong-cli')

from src.db.database import init_database, close_database
from src.db.migrate import MigrationRunner

async def do_rollback():
    db = await init_database()
    runner = MigrationRunner(db)

    # Get current status
    stat = await runner.get_status()
    print(f"Current applied: {', '.join(stat['applied'])}")
    print(f"Current version: {stat['current_version']}")

    if target_version:
        # Rollback to specific version
        print(f"\nRolling back to version {target_version}...")
        result = await runner.rollback(target_version)
        print(f"Rolled back {result['rolled_back_migrations']} migration(s)")

    elif rollback_count:
        # Rollback N migrations
        count = int(rollback_count)
        applied = sorted(stat['applied'], reverse=True)[:count]
        if not applied:
            print("No migrations to rollback")
            return

        target = applied[-1] if len(applied) < count else None
        print(f"\nRolling back {len(applied)} migration(s) to version {target or 'initial'}")
        for version in applied:
            print(f"  - {version}")
        result = await runner.rollback(target if target else "000")
        print(f"Rolled back {result['rolled_back_migrations']} migration(s)")

    else:
        print("ERROR: Must specify target version or rollback count")
        sys.exit(1)

    # Verify
    stat = await runner.get_status()
    print(f"\nNew applied: {', '.join(stat['applied'])}")
    print(f"New version: {stat['current_version']}")

    await close_database()

asyncio.run(do_rollback())
PYTHON

echo ""
echo "✅ Rollback complete"
echo ""
echo "Next steps:"
echo "  1. Verify application health: $GATEWAY_URL/health"
echo "  2. Review logs for errors"
echo "  3. If issues persist, consider full restore from backup"
