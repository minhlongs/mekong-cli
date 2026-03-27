#!/bin/bash
# Emergency cancel ALL open orders on Polymarket CLOB
# Usage: ./cancel-all.sh [--confirm]
# Requires: POLYMARKET_API_KEY, POLYMARKET_API_SECRET env vars

set -e

if [ "$1" != "--confirm" ]; then
    echo "[SAFETY] This will cancel ALL open orders on Polymarket."
    echo "[SAFETY] Run with --confirm to execute."
    echo "[SAFETY] Usage: $0 --confirm"
    exit 1
fi

API_BASE="${POLYMARKET_API_BASE:-https://clob.polymarket.com}"

if [ -z "$POLYMARKET_API_KEY" ]; then
    echo "[ERROR] POLYMARKET_API_KEY not set" >&2
    exit 1
fi

echo "[polymarket] Cancelling all open orders..."
curl -sf -X DELETE \
    -H "Authorization: Bearer $POLYMARKET_API_KEY" \
    "$API_BASE/orders" \
    | python3 -m json.tool

echo "[polymarket] All orders cancelled."
