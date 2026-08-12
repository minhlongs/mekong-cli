#!/usr/bin/env bash
#
# Backup KV Namespaces
# Exports all KV namespace keys and values for backup
#
# Usage:
#   ./scripts/backup-kv-namespaces.sh [backup-dir]
#
# Note: This can be rate-limited for large namespaces. Consider using
# wrangler kv:key list with --result=json for production backups.
#
# Exit codes:
#   0 - Success
#   1 - Error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

BACKUP_DIR="${1:-/tmp/backups/kv/$(date +%Y%m%d)}"
TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")

mkdir -p "$BACKUP_DIR"

echo "📦 KV Namespace Backup"
echo "====================="
echo "Backup directory: $BACKUP_DIR"
echo ""

cd "$REPO_ROOT"

# KV namespaces from wrangler.toml
NAMESPACES=(
    "RATE_LIMIT_KV"
    "CACHE_KV"
)

FAILED=0

for NS in "${NAMESPACES[@]}"; do
    echo "Backing up: $NS"

    # Get binding ID from wrangler.toml
    BINDING_ID=$(grep -A2 "binding = \"$NS\"" apps/api/wrangler.toml | grep 'id =' | head -1 | cut -d'"' -f2 || echo "")

    if [[ -z "$BINDING_ID" ]]; then
        echo "  ⚠️  Namespace ID not found in wrangler.toml (skipping)"
        continue
    fi

    # Export keys list
    KEYS_FILE="$BACKUP_DIR/${NS}-keys-${TIMESTAMP}.json"
    if wrangler kv:key list "$BINDING_ID" --format=json > "$KEYS_FILE" 2>/dev/null; then
        KEY_COUNT=$(jq 'length' "$KEYS_FILE" 2>/dev/null || echo "0")
        echo "  ✓ Keys exported: $KEY_COUNT"

        # Export full key-value pairs (rate-limited, so limit to first 1000 keys)
        FULL_FILE="$BACKUP_DIR/${NS}-full-${TIMESTAMP}.jsonl"
        jq -r '.[].name' "$KEYS_FILE" 2>/dev/null | head -1000 | while read -r key; do
            value=$(wrangler kv:key get "$BINDING_ID" "$key" --output=json 2>/dev/null || echo '""')
            printf '{"key":"%s","value":%s}\n' "$key" "$value" >> "$FULL_FILE"
        done

        PAIR_COUNT=$(wc -l < "$FULL_FILE" 2>/dev/null || echo "0")
        echo "  ✓ Values exported: $PAIR_COUNT key-value pairs"
    else
        echo "  ✗ Failed to list keys" >&2
        FAILED=1
    fi

    echo ""
done

if [[ $FAILED -eq 0 ]]; then
    echo "✅ KV backup completed"
    echo ""
    echo "Backup location: $BACKUP_DIR"
    echo "Files:"
    ls -lh "$BACKUP_DIR" 2>/dev/null | tail -n +2 || echo "  (no backup files)"
else
    echo "⚠️  Some backups failed" >&2
    exit 1
fi
