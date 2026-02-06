#!/bin/bash

# 🛡️ MACOOK Guardian v1.0
# Optimized for MacBook M1 16GB VibeCoding Hub
# Author: Antigravity

# --- Configuration ---
LOG_DIR="/Users/macbookprom1/mekong-cli/logs"
LOG_FILE="$LOG_DIR/macook-guardian.log"
mkdir -p "$LOG_DIR"

# Thresholds (Based on M1_VIBECODING_HUB_OPTIMIZATION.md)
RAM_WARNING=500     # MB
RAM_CRITICAL=200    # MB
LOAD_CRITICAL=6.0
COMPRESSOR_RED=5    # GB

# --- Functions ---
SUDO_CMD="echo 1234 | sudo -S"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

get_unused_ram() {
    # Pages free + Pages inactive + Pages speculative
    # Page size 16384 on M1
    FREE=$(vm_stat | grep "Pages free" | awk '{print $3}' | tr -d '.')
    INACTIVE=$(vm_stat | grep "Pages inactive" | awk '{print $3}' | tr -d '.')
    SPECULATIVE=$(vm_stat | grep "Pages speculative" | awk '{print $3}' | tr -d '.')
    echo $(((FREE + INACTIVE + SPECULATIVE) * 16384 / 1024 / 1024))
}

get_load_avg() {
    sysctl -n vm.loadavg | awk '{print $2}'
}

get_compressor_gb() {
    PAGES=$(vm_stat | grep "Pages occupied by compressor" | awk '{print $5}' | tr -d '.')
    if [ -z "$PAGES" ]; then PAGES=0; fi
    # Integer GB
    echo $((PAGES * 16384 / 1024 / 1024 / 1024))
}

prioritize_processes() {
    log "🚀 Prioritizing CC CLI and Dev Servers..."
    # renice: lower value = higher priority. -20 is max.
    PIDS=$(pgrep -f "claude")
    if [ -n "$PIDS" ]; then
        echo "$PIDS" | xargs $SUDO_CMD renice -n -10 >/dev/null 2>&1
    fi
    DEV_PIDS=$(pgrep -f "npm run dev")
    if [ -n "$DEV_PIDS" ]; then
        echo "$DEV_PIDS" | xargs $SUDO_CMD renice -n -5 >/dev/null 2>&1
    fi
}

intervention_level_1() {
    log "🟡 Level 1 Intervention: Purging RAM..."
    eval "$SUDO_CMD purge"
    prioritize_processes
}

intervention_level_2() {
    log "🔴 Level 2 Intervention: Clearing Browser Caches..."
    intervention_level_1
    rm -rf ~/Library/Caches/Google/Chrome/Default/Cache/* 2>/dev/null
    rm -rf ~/Library/Caches/com.apple.Safari/Cache.db* 2>/dev/null
    pgrep -f "esbuild" | xargs kill -9 >/dev/null 2>&1
}

intervention_level_3() {
    log "💀 Level 3 Intervention: Deep Cleanup..."
    intervention_level_2
    npm cache clean --force 2>/dev/null
    rm -rf ~/Library/Logs/* 2>/dev/null
    # Clean non-active .next caches
    find /Users/macbookprom1/mekong-cli -path "*/.next/cache" -type d -mmin +60 -exec rm -rf {} + 2>/dev/null
}

# --- Main Logic ---
log "🛡️ MACOOK Guardian Started"

while true; do
    UNUSED=$(get_unused_ram)
    LOAD_RAW=$(get_load_avg)
    LOAD=${LOAD_RAW%.*} # Integer part
    COMPRESSOR=$(get_compressor_gb)

    log "📊 Status: RAM: ${UNUSED}MB | Load: ${LOAD_RAW} | Comp: ${COMPRESSOR}GB"

    # Check Thresholds (Integer checks only)
    if [ "$COMPRESSOR" -ge "$COMPRESSOR_RED" ] || [ "$LOAD" -ge "${LOAD_CRITICAL%.*}" ] || [ "$UNUSED" -lt "$RAM_CRITICAL" ]; then
        intervention_level_2
    elif [ "$UNUSED" -lt "$RAM_WARNING" ]; then
        intervention_level_1
    fi

    # Every 4 hours (approx 480 cycles of 30s)
    ((COUNTER++))
    if [ "$COUNTER" -ge 480 ]; then
        intervention_level_3
        COUNTER=0
    fi

    sleep 30
done
