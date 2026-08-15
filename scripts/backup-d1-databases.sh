#!/usr/bin/env bash
#
# Backup D1 Databases
# Exports all D1 databases to local/R2 storage
#
# Usage:
#   ./scripts/backup-d1-databases.sh [backup-dir]
#
# Environment:
#   WRANGLER_BACKEND=auto  # Use local or remote
#   R2_BACKUP_BUCKET       # Optional: R2 bucket for offsite storage
#
# Exit codes:
#   0 - Success
#   1 - Error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_DIR="${1:-/tmp/backups/d1/$(date +%Y%m%d)}"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
VERSION="${MEKONG_VERSION:-$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')}"

mkdir -p "$BACKUP_DIR"

echo "📦 D1 Database Backup"
echo "====================="
echo "Backup directory: $BACKUP_DIR"
echo "Timestamp: $TIMESTAMP"
echo "Version: $VERSION"
echo ""

cd "$REPO_ROOT"

# List of databases from wrangler.toml
DATABASES=(
    "mekong-sessions"
    "mekong-audit"
)

FAILED=0

for DB in "${DATABASES[@]}"; do
    echo "Backing up: $DB"

    # Check if database exists
    if ! wrangler d1 list | grep -q "$DB"; then
        echo "  ⚠️  Database not found: $DB (skipping)"
        continue
    fi

    BACKUP_FILE="$BACKUP_DIR/${DB}-${TIMESTAMP}-${VERSION}.sql"

    # Export database
    if wrangler d1 export "$DB" --output="$BACKUP_FILE" 2>/dev/null; then
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "  ✓ Backup created: $SIZE"

        # Verify integrity
        if [[ -s "$BACKUP_FILE" ]]; then
            echo "  ✓ Verified: $(wc -l < "$BACKUP_FILE") lines"
        else
            echo "  ✗ Empty backup file!" >&2
            FAILED=1
        fi
    else
        echo "  ✗ Export failed" >&2
        FAILED=1
    fi

    echo ""
done

# Upload to R2 if configured
if [[ -n "${R2_BACKUP_BUCKET:-}" ]] && command -v wrangler &>/dev/null; then
    echo "Uploading to R2: $R2_BACKUP_BUCKET"
    for file in "$BACKUP_DIR"/*.sql; do
        [[ -f "$file" ]] || continue
        R2_KEY="d1-backups/$(basename "$file")"
        if wrangler r2 object put "$R2_BACKUP_BUCKET/$R2_KEY" --file="$file" 2>/dev/null; then
            echo "  ✓ Uploaded: $(basename "$file")"
        else
            echo "  ⚠️  Upload failed: $(basename "$file")" >&2
        fi
    done
    echo ""
fi

# Cleanup old backups (keep 30 days)
echo "Cleaning backups older than 30 days..."
find "$(dirname "$BACKUP_DIR")" -type d -name "$(basename "$BACKUP_DIR" | cut -d- -f1)-*" -mtime +30 -exec rm -rf {} + 2>/dev/null || true
echo ""

if [[ $FAILED -eq 0 ]]; then
    echo "✅ All backups completed"
    echo ""
    echo "Backup location: $BACKUP_DIR"
    echo "Files:"
    ls -lh "$BACKUP_DIR"/*.sql 2>/dev/null || echo "  (no backup files)"
else
    echo "⚠️  Some backups failed" >&2
    exit 1
fi
