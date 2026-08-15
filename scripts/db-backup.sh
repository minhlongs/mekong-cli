#!/usr/bin/env bash
#
# Database Backup Script for Migration CI/CD Pipeline
# Creates timestamped PostgreSQL backups before migrations
#
# Usage:
#   DATABASE_URL=${DB_URL} scripts/db-backup.sh /path/to/backup/dir
#   DATABASE_URL=${DB_URL} scripts/db-backup.sh /backups latest
#
# Environment:
#   DATABASE_URL - PostgreSQL connection string (required)
#   BACKUP_S3_BUCKET - Optional S3 bucket for offsite storage
#   BACKUP_RETENTION_DAYS - Days to keep local backups (default: 7)
#
# Outputs:
#   Backup file path on stdout on success

set -euo pipefail

# Configuration
BACKUP_RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
VERSION="${MEKONG_VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"

# Arguments
BACKUP_DIR="${1:-/backups}"
BACKUP_PREFIX="${2:-mekong}"

# Validate
if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: DATABASE_URL environment variable is required" >&2
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

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup filename
BACKUP_FILE="${BACKUP_DIR}/${BACKUP_PREFIX}-${PGDATABASE}-${TIMESTAMP}-${VERSION}.sql.gz"

echo "📦 Creating database backup..."
echo "   Database: $PGDATABASE"
echo "   Host: ${PGHOST:-localhost}"
echo "   Backup file: $BACKUP_FILE"

# Extract password if present
if [[ "$DATABASE_URL" == *":"*"@"* ]]; then
    PGPASSWORD=$(echo "$DATABASE_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
    export PGPASSWORD
fi

# Create backup
if pg_dump "$DATABASE_URL" 2>/dev/null | gzip > "$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "✅ Backup created successfully"
    echo "   Size: $BACKUP_SIZE"

    # Verify backup integrity
    if gzip -t "$BACKUP_FILE" 2>/dev/null; then
        echo "✅ Backup integrity verified"
    else
        echo "WARNING: Backup integrity check failed" >&2
    fi

    # Upload to S3 if configured
    if [[ -n "${BACKUP_S3_BUCKET:-}" ]]; then
        echo "📤 Uploading to S3: $BACKUP_S3_BUCKET"
        S3_KEY="backups/$(basename "$BACKUP_FILE")"
        if command -v aws &>/dev/null; then
            aws s3 cp "$BACKUP_FILE" "s3://${BACKUP_S3_BUCKET}/${S3_KEY}" \
                --storage-class STANDARD_IA \
                --only-show-errors
            echo "✅ Uploaded to S3"
        else
            echo "WARNING: aws CLI not installed, skipping S3 upload" >&2
        fi
    fi

    # Clean old backups
    echo "🧹 Cleaning backups older than $BACKUP_RETENTION_DAYS days..."
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}-*.sql.gz" -type f \
        -mtime "+$BACKUP_RETENTION_DAYS" -delete 2>/dev/null || true
    echo "✅ Cleanup complete"

    # Output backup path for downstream steps
    echo "backup_path=$BACKUP_FILE" >> "$GITHUB_OUTPUT" 2>/dev/null || true
    echo "$BACKUP_FILE"

else
    echo "ERROR: pg_dump failed" >&2
    rm -f "$BACKUP_FILE" 2>/dev/null || true
    exit 1
fi
