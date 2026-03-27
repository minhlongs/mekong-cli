#!/bin/bash
# ==============================================================================
# Mekong CLI — Pre-startup coexistence check
# Verifies LLM servers + sibling container status before full startup
# ==============================================================================

set -e

echo "[coexist] Checking M1 Max dual-system status..."

# Check LLM servers
DEEPSEEK_OK=false
NEMOTRON_OK=false

if curl -sf http://host.docker.internal:11435/v1/models > /dev/null 2>&1; then
    DEEPSEEK_OK=true
    echo "[coexist] DeepSeek R1 (:11435) — healthy"
else
    echo "[coexist] WARNING: DeepSeek R1 (:11435) — unreachable"
fi

if curl -sf http://host.docker.internal:11436/v1/models > /dev/null 2>&1; then
    NEMOTRON_OK=true
    echo "[coexist] Nemotron Nano (:11436) — healthy"
else
    echo "[coexist] WARNING: Nemotron Nano (:11436) — unreachable"
fi

# Check CashClaw sibling (informational only, don't block startup)
if docker ps --filter name=cashclaw-bot --format "{{.Status}}" 2>/dev/null | grep -q "Up"; then
    echo "[coexist] CashClaw sibling — running (LIVE TRADING)"
    echo "[coexist] DO NOT restart Docker engine without stopping CashClaw first"
else
    echo "[coexist] CashClaw sibling — not running"
fi

# Summary
if $DEEPSEEK_OK && $NEMOTRON_OK; then
    echo "[coexist] All systems nominal. Proceeding."
else
    echo "[coexist] WARNING: Some LLM servers unreachable. Mekong will start but PEV planning may fail."
fi
