#!/bin/bash
# Check all open orders on Polymarket CLOB
# Usage: ./check-open-orders.sh
# Requires: POLYMARKET_API_KEY, POLYMARKET_API_SECRET env vars

set -e

API_BASE="${POLYMARKET_API_BASE:-https://clob.polymarket.com}"

if [ -z "$POLYMARKET_API_KEY" ]; then
    echo "[ERROR] POLYMARKET_API_KEY not set" >&2
    exit 1
fi

echo "[polymarket] Fetching open orders..."
curl -sf \
    -H "Authorization: Bearer $POLYMARKET_API_KEY" \
    "$API_BASE/orders?state=open" \
    | python3 -m json.tool

echo "[polymarket] Done. Review orders above before any engine restart."
