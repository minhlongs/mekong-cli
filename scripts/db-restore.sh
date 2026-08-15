#!/usr/bin/env bash
#
# Database Restore from Backup Script
# Restores a PostgreSQL database from a backup file
#
# Usage:
#   DATABASE_URL=${DB_URL} scripts/db-restore.sh /path/to/backup.sql.gz
#
# Environment:
#   DATABASE_URL - PostgreSQL connection string (required)
#   RESTORE_CONFIRM - Set to 'true' to skip confirmation prompt
#   DISABLE_CONNECTIONS - Set to 'true' to disconnect other sessions during restore
#
# Exit codes:
#   0 - Success
#   1 - Error

set -euo pipefail

BACKUP_FILE="${1:-}"

if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 /path/to/backup.sql.gz"
    echo ""
    echo "Backup files are typically found in:"
    echo "  /tmp/backups/mekong-*.sql.gz"
    echo "  /tmp/backups/rollback-*.sql.gz"
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

# Parse connection details
PGHOST=$(echo "$DATABASE_URL" | sed -n 's/.*@\([^:/]*\).*/\1/p')
PGPORT=$(echo "$DATABASE_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
PGDATABASE=$(echo "$DATABASE_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')
PGUSER=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')

if [[ -z "$PGDATABASE" ]]; then
    echo "ERROR: Could not parse database name from DATABASE_URL" >&2
    exit 1
fi

# Extract password if present
if [[ "$DATABASE_URL" == *":"*"@"* ]]; then
    PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    export PGPASSWORD
fi

echo "🔴 DATABASE RESTORE"
echo "=================="
echo "Database: $PGDATABASE"
echo "Backup:   $BACKUP_FILE"
echo "Size:     $(du -h "$BACKUP_FILE" | cut -f1)"
echo ""

# Safety checks
if [[ "${RESTORE_CONFIRM:-false}" != "true" ]]; then
    echo "⚠️  WARNING: This will OVERWRITE the current database!"
    echo ""
    read -p "Type the database name '$PGDATABASE' to confirm: " CONFIRM_DB
    if [[ "$CONFIRM_DB" != "$PGDATABASE" ]]; then
        echo "Restore cancelled."
        exit 0
    fi
fi

# Disable other connections if requested
if [[ "${DISABLE_CONNECTIONS:-false}" == "true" ]]; then
    echo "🔌 Disabling new connections..."
    psql "$DATABASE_URL" -c "UPDATE pg_database SET datallowconn = false WHERE datname = '$PGDATABASE';" 2>/dev/null || true
    echo "   Active connections:"
    psql "$DATABASE_URL" -c "SELECT pid, usename, application_name, client_addr FROM pg_stat_activity WHERE datname = '$PGDATABASE';" 2>/dev/null || true
    read -p "Press Enter after verifying connections are closed..."
fi

# Restore
echo ""
echo "📥 Restoring database..."
set -x

if [[ "$BACKUP_FILE" == *.gz ]]; then
    # Gzipped backup
    if ! gunzip -c "$BACKUP_FILE" | psql "$DATABASE_URL"; then
        echo "ERROR: Restore failed" >&2
        exit 1
    fi
else
    # Plain SQL
    if ! psql "$DATABASE_URL" < "$BACKUP_FILE"; then
        echo "ERROR: Restore failed" >&2
        exit 1
    fi
fi

set +x

echo ""
echo "✅ Restore complete"
echo ""
echo "Verifying..."
python3 -c "
import os, asyncio, sys
sys.path.insert(0, '/Users/macbook/mekong-cli')
from src.db.database import init_database, close_database
from src.db.migrate import MigrationRunner

async def verify():
    db = await init_database()
    runner = MigrationRunner(db)
    stat = await runner.get_status()
    print(f'Applied migrations: {len(stat[\"applied\"])}')
    print(f'Current version: {stat[\"current_version\"]}')
    await close_database()

asyncio.run(verify())
"

echo ""
echo "Next steps:"
echo "  1. Check application logs for any issues"
echo "  2. Run health check: $GATEWAY_URL/health"
echo "  3. Verify data integrity"
